---
title: AWS Lambda (python) with packages through pip (in CloudFormation)
description: An easy way to use CloudFormation to AWS Lambda python functions with packages through pip.
date: '2021-02-10T18:30:03Z'
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
original_post_medium_url: https://claude-e-e.medium.com/aws-lambda-python-with-packages-through-pip-in-cloudformation-e8d92bba17b9
header:
  image: /assets/images/2021/02/10/layers-header.jpg
  teaser: /assets/images/2021/02/10/layers.jpg
---
I absolutely love CloudFormation as a tool for creating small and large items on AWS. Having code-based infrastructure, of easily maintaining your system in git, seeing differences, etc is pure joy. There are however (many) times when CloudFormation (or AWS in general) seems to miss some things. In such cases, blogs like this one should help you :).

This document is here mostly for historical reference.
There is a new and better method, that doesn't have [some of the security implications](./2021-02-15-aws-custom-resources-security--trap----or-why-it-s-bad-to-give-lambda-execute-rights-to-non-admin.md) present in this post.
{: .notice--danger}

**TL;DR** scroll down to find a CloudFormation custom resource that builds Lambda Layers based on a list of pip packages.

If one wants to create a lambda function (in python — the lambda environment by now supports lots of languages, this blogpost deals with python only) there are 2 ways to do this in CloudFormation; either write the code directly into the CloudFormation yaml file, or upload a zipped archive to an S3 bucket and reference that. The first method is very nice, in that it’s self-contained; you don’t need any external tools to upload the code you just wrote to an S3 bucket, and you don’t need an S3 bucket (which supposedly you would need to make in another, previous, CloudFormation stack) — it does help to have a small tool to insert an external python file into the yaml, more on this on another blog post. The second method however has some major advantages, in that it supports up to 250MB of python code (whereas the first method is limited to 4096 bytes), and it supports multiple files (whereas the first method is limited to a single file). 4096 bytes is a serious limitation when writing a (readable and failure-resistant) python program, however it is doable for smaller functions (and these are exactly the lambdas for which you don’t want to be bothered to set up a system to upload them to S3, etc:)); actually, there seems to be a workaround for this, but we’ll get to that in a later post (update: [later post is live](./2021-02-15-better-lambdas-with-pip-packages-in-cloudformation.md)). The second limitation, only allowing a single file, is also a large restriction, especially in those cases when we would like to include some library for pypi (or another repository).

In the python universe, most libraries are downloaded from pypi.org (PYthon Package Index), through the pip command. If you type `pip install numpy`, pip will contact pypi.org to find and download the numpy package, and then install it (build it if necessary). Python ships with a large standard library, but quite often the tools in there are _just_ suboptimal for the job (as an example, the `urllib` package in the standard library is less robust than the `requests` package. The different `xml.*` packages are not protected against DOS attacks, whereas pypi provides `defusedxml`). In addition, tools like `numpy`, `pillow`, etc provide functionality that is hard to build yourself on the python runtime. In short, if you cannot use pypi packages, you’re very limited in what programs you can write. As a side note: The default AWS Lambda environment always contains the `boto3` package, as well as (if you install your lambda through method 1) something called `cfnresponse`. It used to also include the `requests` package somewhere under `boto3.vendored`; [this will be removed in some weeks though](https://aws.amazon.com/blogs/compute/upcoming-changes-to-the-python-sdk-in-aws-lambda/).

For years the only solution for using pypi packages on lambda was to install them locally, then zip them together with the lambda function, and upload them (for CloudFormation this means: adding them to S3, etc) — hoping that (for packages that compile) your compiled code is actually compatible with whatever AWS Lambda runs on. Two years ago AWS released [Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html). You can make a lambda layer with whatever data, code, libraries you want, and include this in your lambda. It’s great that you could just write your simple, method 1, small lambda, and import a layer with, say, `numpy`, `pillow`, `requests` and [`abstractcp`](https://pypi.org/project/abstractcp/) (shameless plug for my only pypi package :)). All you need is to create this layer…. Below a [CloudFormation Custom Resource](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html) to do just that.

#### Solution

We create a Custom Resource that runs a lambda that calls `pip` (which luckily nowadays is available in the lambda environment). This will download and build packages for _exactly_ the system and python version that the lambda runs on. It will then save the result as a lambda layer.

Packages can be specified using whatever syntax pip understands, so specifying specific versions, or ranges, all is (should be) allowed.

The example below produces a layer called `mylayer` with the required pypi packages installed. A lambda created later can use this layer by adding a property `Layers: [!Ref MyLayer]`.

The `!Ref MyLayer` is actually the ARN of the layer version. Any change to the MyLayer resource (e.g. a new package is added, or the description is changed) will result in a new layerversion. CloudFormation notes that the ARN has changed, and will therefore also update any lambda using this layer to use the new layerversion (and afterwards call the PipLayer custom Resource with a `Delete` request for the old layer version).

{% gist 6478d80aeb88f5014e89ad1d915931dd %}
