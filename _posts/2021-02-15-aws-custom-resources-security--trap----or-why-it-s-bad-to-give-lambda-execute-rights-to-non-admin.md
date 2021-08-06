---
title: AWS Custom Resources security "trap" — or why it’s bad to give lambda execute rights to non-admin
description: Quick description of the security problems you run into if non-admins have lambda execution rights.
date: '2021-02-15T11:58:17Z'
categories:
  - tech
  - howto
tags:
  - aws
  - cloudformation
  - lambda
  - python
  - pip
  - security
original_post_medium_url: https://claude-e-e.medium.com/aws-custom-resources-security-trap-or-why-its-bad-to-give-lambda-execute-rights-to-non-admin-10f3fd2ddbe7
header:
  teaser: /assets/images/2021/02/15/stop.svg
---

AWS CloudFormation allows the use of Custom Resources. These are great if one has to do some things outside AWS (say you create a stack and you want as part of the stack also create a github repository with a bunch of access rights). In practice however I have mostly used them to do things inside AWS that either do not have a CloudFormation interface (yet), or where the CloudFormation interface does not do what I need (for example, build a [lambda layer based on pip packages](/tech/howto/2021/02/10/aws-lambda-python-with-packages-through-pip-in-cloudformation.html)). It takes quite some hassle to set it all up, but once it works, it works like a breeze!

There is however something that one needs to take into account in these cases. Custom Resources (in these cases) are lambda functions. And lambda functions run in their own IAM role. In many setups that I have seen (and, to my shame, have built), most users have execute lambda permissions (without any restrictions). This means that whatever your custom resource is capable of doing, now all of a sudden all lambda users can do. As far as I have been able to tell, there is no easy way to restrict from a lambda execution role who can actually execute that function (so that it could be limited to e.g. admin only). There also is no obvious way inside the lambda itself to find if it was called as part of a CloudFormation Stack Custom Resource or through the CLI/console (note: I mean no _secure_ way; one can look at the data in the `event` dict, but someone could send the exact same event when calling from the console) — if someone knows of a way, please let me know!

Depending on what rights you give to your Custom Resource lambda, this may or may not be a serious security risk. For instance imagine the custom resource that [builds a lambda layer](./2021-02-10-aws-lambda--python--with-packages-through-pip--in-cloudformation.md). Anyone with (unrestricted) lambda execute rights could use this to replace any layer with whatever code they wanted (by uploading a package `evilpackage` to pypi and then calling the Custom Resource lambda to update the layer with this new package). For layers the problems seem to be limited, since a new layer would have a new layer version number, and existing lambdas (that possibly have execution roles with even more rights) will not use the new layers unless told to do so (which supposedly is something the attacker will not be able to do).

I was however in the process last week to build a Custom Resource that allows creation of lambdas with multiple files, pip packages, etc, all from within CloudFormation. Creating a new lambda however means that one needs the `iam:PassRole` right; this means that an attacker could use this lambda to create a new lambda with any (existing) role it wants and any code it wants; just because it can execute this one lambda! And it is possible to limit the roles that the `iam:PassRole` allows, however this would invalidate the flexibility of the Custom Resource. So, even though I would love to have a custom resource like this, I feel the risk is too great (I like to have at least 2 layers of defence for attacks like this; not just assume that nobody will accidentally give a non-admin user lambda execute rights on `*`, because they assume that all lambdas have to do with running our application.

Considering where the root of the problem lies (besides the fact that meat-and-bones are lazy and like to create `*` access too often), it seems to me that it would be great if AWS allowed for lambdas to run either in the execution role that calls them, or in that role restricted by further policies. That way if it’s called from CloudFormation, it will not be able to do anything that the role doing the stack update would not be able to do. If called by the attacker, it would not grant any extra permissions. Note that in some (many) cases it’s great that lambda elevates permissions (e.g. it may be able to get a password from a store and use the password to make a web call, while hiding the password from the caller), however this should not be default (or at least, should not be the _only_ way to do things). Note also that permission elevation is especially problematic for general / reusable Custom Resources. We often want to make the Custom Resource so that it can create _any_ function, assign _any_ execution role, etc, so that we’re not limited in what we can specify in our CloudFormation template.

Lambdas get their amazing startup speed and scalability probably exactly _because_ they don’t have to do too many difficult IAM things. It’s obviously easier if every lambda invocation has exactly the same role. The main usecase for lambda is for a small piece of code that scales to millions of calls per second, without much delay, capable of running the biggest websites without any limits. However Custom Resources don’t need this — they might be called once a month, and it’s ok if they take a second of even 10 to startup. It’s understandable that AWS reused the lambda environment for Custom Resources, but it does feel that for security (and possibly maintenance/performance) reasons, another choice could have been made.

There are obviously solutions to this all (of which in my mind at least 2 need to be applied just to be sure — and obviously in addition to applying minimal privilege everywhere anyways):

*   Making sure that no non-admin user/role ever has `lambda:InvokeFunction` (or `lambda:InvokeAsync`) rights on anything with a wildcard, unless it’s something like `arn:aws:lambda:REGION:ACCOUNTID:function:junior-lamdas-*` . There is some alert / regular test / check that this is true (I know I certainly have changed `Resource` to `*` sometimes to debug some invocation issue, and then forgot to put it back).  
    Using ResourceTags on lambdas would be perfect (you could then do something like by default add `Effect: Deny, Resource: *, Condition: StringEquals: aws:ResourceTag/AdminFunction: true`, but [lambdas do not support tag-based access](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-services-that-work-with-iam.html) (at least at 2021–02–15).
*   Whenever developing a Custom Resource, explicitly consider that an attacker may be able to run the lambda with any input they desire. Consider if this would lead to them being able to be destructive (either directly, or possibly through rights elevation; i.e. that they can create and control another item with additional rights).
*   Put all your Custom Resources into a separate AWS account that is accessible only to those roles that run stack updates. This is probably what you want anyways, however it does have some overhead, and e.g. for smaller projects it’s not feasible (it’s nice for a small project to have the custom resource creation in the same stack as where it’s used)

### Things I tried to make sure that a lambda function could only be run by specific people

Below some ideas I had to make sure that a random attacker either could not run the lambda function. They fall in 3 categories:

*   Make sure that starting of the lambda function does not work (unless started by an admin), either because lambda.InvokeFunction gives an AccessDenied (did not find a way to control this from the lambda), or because the AssumeRole for the lambda execution role would fail
*   Use `Condition`s in the PolicyDocument of the Execution Role so that if it was started by anyone but an admin the function would not have any rights
*   Put something in the lambda code that terminates execution if started by a non-admin (or e.g. not from CloudFormation)

#### Disallow assuming the execution role (failed)

```yaml
AssumeRolePolicyDocument:  
      Version: 2012-10-17  
      Statement:  
        - Action:  
            - sts:AssumeRole  
          Effect: Allow  
          Principal:  
            Service:  
              - lambda.amazonaws.com  
          Condition:  
            StringEquals:  
              aws:PrincipalTag/PolicyUpdater: "true"
```

The idea is only a principal with a certain tag (PolicyUpdater=true) can assume this role. This fails, most likely because the principal is actually `lambda.amazonaws.com`. If you think about it, it makes sense: lambda starts the program, and whenever someone invokes the function it just calls a (python/javascript) function, so the assumerole is not being done by the person invoking the function.

#### Revoking permissions based on principal (failed)

```yaml
Statement:  
  - Action:  
    - lambda:UpdateFunctionCode  
    - lambda:GetFunction  
    Effect: Allow  
    Resource:  
    - "*"  
    Condition:  
      StringEquals:  
        aws:PrincipalTag/PolicyUpdater: "true"
```

The idea is that even if the person gets the execution role, it will limit what the role can do. This fails for the same reason as above (plus, I expect, the principal by now probably is the execution role itself).

#### Having the lambda check who called it (failed in easy ways)

The idea is that somehow within the lambda we can find out how it was called. If it’s called by CloudFormation, we can continue execution (or even better, try to intersect our execution role with the CloudFormation Stack Update role). There does not seem to be an easy way to do this. Things like `sts.GetCallerIdentity` don’t give any info of the real caller, and anything that the `event` object contains can be faked by a caller. I did not see any other way to do this through the API (which makes sense since I expect that subsequent invocations of a lambda all use the same access key) or any other way. However, see below.

### Suggestions for further research on how this could be done

When thinking about how the lambda could check who called it, I did find several directions that might provide some direction.

#### Use the aws\_request\_id from the context object

A lambda function receives in the invocation a [_context_ variable](https://docs.aws.amazon.com/lambda/latest/dg/python-context.html) that contains an `aws_request_id`. The AWS Request ID seems mostly to be useful when talking to AWS support, however I could imagine that this ID for instance also gets logged into CloudTrail when making a call. A lambda could then inspect CloudTrail to see where the call came from, and fail to execute if it didn’t come from CloudFormation. Some things have to be kept in mind:

*   Can an attacker fake the `context.aws_request_id` in a call from the CLI?
*   Could an attacker somehow enter a fake record into whatever store is being used to check the request\_id?
*   Knowing that the call came from CloudFormation is not (necessarily) enough — maybe there is a user with very limited CloudFormation rights; this would need more research.

#### Providing access key/secret through event object

What if the lambda runs with an execution role that only allows writing to logs, and any real calls happen with an access key / secret that is sent through the event object (so through CloudFormation template). This means that an attacker that has invoke access to the lambda could never give more rights to the lambda than that he already has. There are some things to take into account:

*   Make sure the access key/secret are not being logged, neither in CloudFormation or in the lambda. If this is not possible / secure enough, there are some mitigations (digitally sign the event object so that a replay would fail if anything was changed; combine this with a token that the lambda exchanges for another token, for instance in the ParameterStore; something like this).
*   Using sts.AssumeRole it’s actually possible to create a token for a role that is the intersection of the role that the CloudFormation Stack update runs as, and a certain lambda role, exactly what we would need and want.
*   Never use this with permanent credentials. Temporary credentials have a minimum lifetime of 15 minutes — still plenty of time for a hacker to act, but much much better than infinite time.

Work in progress (maybe a next blogpost)
