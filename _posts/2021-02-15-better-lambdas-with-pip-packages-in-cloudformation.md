---
title: Better Lambdas with pip packages in CloudFormation
description: An easy way to use CloudFormation to AWS Lambda python functions with packages through pip.
date: '2021-02-15T18:37:36Z'
categories:
  - tech
  - howto
keywords:
  - aws
  - cloudformation
  - lambda
  - layers
  - python
  - pip
original_post_medium_url: https://claude-e-e.medium.com/better-lambdas-with-pip-packages-in-cloudformation-7ef92b2c793c
---

After writing about how to [create AWS Lambda Layers based on pip packages](/tech/howto/2021/02/10/aws-lambda-python-with-packages-through-pip-in-cloudformation.html), I set out to make writing lambda functions in CloudFormation a bit easier. In the official CloudFormation `AWS::Lambda::Function` you either must upload your functions as zipfile to S3 and reference them from there, or, if you want them inline, you run into 3 large issues

*   You’re limited to 4096 bytes of code (meaning in my experience that as the code gets more complex, you start saving on comments, function names, error checking, etc, making the whole thing even harder to read and maintain).
*   You’re limited to a single file. Maybe not so bad if you only have 4096 bytes, but still not good for readability
*   You are limited to the builtin packages cfnresponse and boto3; installing packages from pip is not that easy. This limitation is mitigated by [the pip layers](https://claude-e-e.medium.com/aws-lambda-python-with-packages-through-pip-in-cloudformation-e8d92bba17b9) mentioned before.

Now, let me lead of by saying that for more complex environments (production environments), I definitely recommend having uploading packages through the S3 way. At this time you should also have multiple stacks (or even multiple accounts), and your own tooling for doing stack stuff. However for someone who just experiments a bit on their own account with a small project now and then, it’s nice to have self-contained stacks, that do the job from start to end.

So in this article I introduce a way to use Custom Resources to create a function from inline python code, of arbitrary size (note: there is a limit of 51200 bytes for the template as a whole, after which you will still need an S3 spot to upload your template to CF, but this at least gives a bit of leeway).

To start off, I use a small python tool to build my stack. It allows me to do something like:

```yaml
stack.yaml:
===========

Resources:
  __INCLUDE__0: baseresources.yaml
  __INCLUDE__1: lambdas.yaml
etc...


lambdas.yaml:
=============
MyLambda:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: testlambda
    Code:
      ZipFile: |
        __INCLUDE__: testlambda.py
```

Note that this tool is far from perfect, however it allows me to reuse code and write the python in `.py` files, which means that the editor helps me:

{% capture code %}
```python
# Run as "python getstack.py #filename#", it prints a filename on stdout that contains
# the stack in #filename# with some edits
# Useful in a commandline such as:
# aws cloudformation update-stack --stack-name MyStack --template-body file://$(python getstack.py stack/stack.yaml) --parameters ParameterKey=XXXX,ParameterValue=YYYY --capabilities CAPABILITY_IAM


# The following tags are supported
# Note that all filenames used are relative to the location of the file that contains
# the filename
# All files are expected to have utf-8 encoding
#
# ---- __INCLUDE__: #includefilename# ----
# Should appear on a line by itself
# the #includefilename# will be included in this script (recursively processed itself)
# and indented by the number of spaces before the __INCLUDE__:
# Note that a number may follow the __INCLUDE__ in order to make the tags unique
# This is not a requirement but some YAML editors will complain if you have two
# __INCLUDE__ keys at the same level, so you can use __INCLUDE__1, __INCLUDE__2, etc
#
# --- !!TIMESTAMP!! --
# This string is replaced by an identifierfriendly timestamp (e.g. 20210103T120354Z)
# There is a guarantee that the same timestamp is used everywhere in the file
from __future__ import annotations

import datetime
import logging
import pathlib
import re
import tempfile

logger = logging.getLogger()

IMPORT_RE = re.compile(
    r"^(?P<indent> +)__INCLUDE__\d*: (?P<filename>.+)$", re.MULTILINE)


def importfile(indent: int, filename: pathlib.Path) -> str:
    assert filename.is_absolute()
    data = process_file(filename)
    lines = [(" " * indent) + line if line else "" for line in data.split("\n")]
    return "\n".join(lines)


def process_file(filename: pathlib.Path) -> str:
    logger.info('Processing %s', filename)

    assert filename.is_absolute()
    filepath = filename.parent
    data = filename.read_text(encoding="utf-8")
    return IMPORT_RE.sub(
        lambda match: importfile(
            len(match.group("indent")),
            (filepath / match.group("filename")).resolve()),
        data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    absolute_filename = pathlib.Path(args.filename).resolve()
    processed_stack = process_file(absolute_filename)
    processed_stack = processed_stack.replace(
        "!!TIMESTAMP!!", datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
    tmpfile = tempfile.NamedTemporaryFile(
        mode="wt", encoding="utf-8", suffix="-" + absolute_filename.name, delete=False)
    tmpfile.write(processed_stack)
    logger.info("Wrote %s", tmpfile.name)
    print(tmpfile.name)
```
{% endcapture %}
{% include details
  summary="Expand to see code"
  body=code
%}


Now, using the example before, as soon as `testlambda.py` gets larger than 4096 bytes (which is about 2 pages of code, not that much), the stack update will fail.

It seems that the 4096 bytes limit is arbitrary; it’s totally possible to send larger documents to Custom Resources, so we could actually make a custom resource that receives this code, and then creates a lambda function out of it. For the past days I’ve been trying to do just that, however both having the custom resource create the lambda directly, and having the custom resource update the code of some existing lambda failed, because of [my uneasiness with lambdas that can potentially escalate privileges](tech/howto/2021/02/15/aws-custom-resources-security-trap-or-why-it-s-bad-to-give-lambda-execute-rights-to-non-admin.html). After some more experimentation, the (more secure) solution seems to be to put all the code in a Lambda Layer. Since lambda layers are versioned (as far as I know, it’s not possible to tell a function to always run the latest layer version) an attacker would need to gain access to more than just the Custom Resource lambda in order to mount an attack.

So the result is a Custom Resource that creates a lambda layer. The lambda layer contains both the packages and the code. The lambda function itself contains no code at all — we can use the `Handler` property of a function to directly call code in the layer. So to get a (very uninteresting) lambda — note that we give it so few rights that it cannot even log execution:

```yaml
TestLambdaRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: 2012-10-17
      Statement:
        - Action:
            - sts:AssumeRole
          Effect: Allow
          Principal:
            Service:
              - lambda.amazonaws.com

TestLambda:
  Type: AWS::Lambda::Function
  Properties:
    Code:
      ZipFile: '# NOTE: this file is not used, all code is in layer'
    Description: Test Function
    FunctionName: testlambda
    Handler: testlambda.handler
    MemorySize: 128
    Role: !GetAtt TestLambdaRole.Arn
    Runtime: python3.8
    Layers:
      - !Ref TestLambdaLayer

TestLambdaLayer:
  Type: Custom::CodeLayer
  Properties:
    ServiceToken: !GetAtt CodeLayerLambda.Arn
    LayerName: TestLambdaLayer
    Packages:
      - numpy==1.20
    Files:
      testlambda.py: |
        import numpy as np

        def handler(event, context):
            print(np.arange(10) \*\* 2)
```

It creates a lambda function with an index.py with the string `# NOTE: this file is not used, all code is in layer`. Obviously you can put here whatever you want, I usually opt for just `...` although this text is better in case I forget later what I did. The `TestLambdaLayer` is where the magic happens; the custom resource builds a layer with the `testlambda.py` file, with the `numpy` package installed, and the `TestLambda` function runs directly the `handler()` function from the `testlambda.py` file.

Note that any update to the code will result in a new layer version being created, then the `TestLambda` function being updated to use the new layer version. In case of a single application consisting of 4 of 5 lambda functions, one could create a single layer with all the code, and each lambda function just pointing to a different entry point (`Handler`).

The CloudFormation code to create the custom function is below (note that it uses the `__INCLUDE__:` syntax from the `getstack.py` file above; this is just for readability, and things will work just as well if you manually copy the `codelayer.py` code into the `codelayer.yaml` file (and indent it far enough). The code has the following features:

*   Fits in 4096 bytes (so can be used inline in a CF template)
*   Uses a 300 second timeout and 1024MB of memory limit. Feel free to expand/shrink these limits to your use. At today’s pricing, a 300 second run for a 1024MB lambda function costs about $0.005, or half a cent.
*   Installs packages from pip (you should be able to use any syntax that is valid for `python -m pip ...`. Note, packages have to be given as array, with multiple packages in multiple array items. It will auto-install the packages for the python version that the lambda runs in (python 3.8 for the code below). In almost all cases this will install a version for all recent 3.x python versions; if it’s important, you can change the runtime on the `CodeLayerLambda`.
*   Installs files as given through key-value in the `Files` section. Creates directories where necessary, so you can do something like `{"Files": {"test/unittest.py": "import unittest\n..."}}` .
*   Allows creation of python and non-python files. Python files are syntax-checked, and deploy fails if `python -m py_compile #filename#` fails for a file with extension `.py`. Obviously it’s easy to remove this check below. Non-python files are limited to text-files for now.
*   Note: Security was not a big design requirement here; it’s assumed that only admins can run this function. I don’t see any obvious ways how a bad actor can do something bad within the lambda environment while running this, but sanity checking all the code in a way that I would like to do, makes the lambda (much) bigger than 4096 bytes.

{% gist 0d0db326631e509fa8ba31b78b98dc9b %}
