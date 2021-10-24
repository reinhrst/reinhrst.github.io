---
title: 'Create a static HTTPS site on your custom domain using Cloud Formation'
categories:
    - tech
    - manual
tags:
    - howto
    - aws
    - cloudformation
---

Every now and then I find myself with the need to quickly create a small website, for instance as a static backend or a help page to [one](https://sks.claude-apps.com/) of my apps.
I have a couple of requirements for this:

- I want a custom (sub)domain. For now I host everything on claude-apps.com, but this could change.
- I want to serve my website on HTTPS (obviously).
- I want the website to be securely setup, in a minimal number of clicks.
- I want to be able to access the log files.
- I don't want anything I didn't ask for (in the form of trackers, or advertisements, or pay walls, etc).

This howto assumes that you know your way around AWS.
It will talk about CloudFormation, CloudFront and S3, and assume you know what they are (or are willing to find out by reading up on them).
This is NOT a howto for people without any AWS experience.
{: .notice--warning}

The last option means that AWS is the target of choice (Note: I'm contrasting it here to "free" webhosting services; I'm sure that Azure and Google Cloud offer similar privacy, but this article is about AWS).
It should be noted that AWS is not free; in my experience however, the only real cost I have is $12 a year for the domain name registration, and another $0.50 a month for the hosted-zone (the DNS).
This gives me an unlimited number of websites on the claude-apps.com domain; the additional costs (so far) for traffic and hosting is literally less than 2 cents/month for 3 websites (however do see the warning/disclaimer at the bottom).

There are multiple ways to set up a secure static website on AWS; here I choose to have an S3 bucket.
The S3 bucket has 2 directories (one log directory, one directory with the website).
The website will only serve HTTP requests to CloudFront; CloudFront serves the HTTPS requests to the rest of the world.

Setting this all up "just right" is fiddly every time, so I made a CloudFormation Stack to do all the heavy lifting.

Before you start, you need to set up a hosted "parent" zone on Route53; this is a one time operation, after which you can create unlimited websites on subdomains.
In my case, I have a `claude-apps.com` hosted zone, with zoneId `Z0XXXXXXXXXXXX`.
You don't need to have the domain name registered at AWS, however you must make sure that the Route53 zone is actually being used by DNS.
This is because later we ask Amazon to create a certificate for your zone, and it will only do so if DNS for this domain points to Route53.

Afterwards it's as simple as downloading the following stack template and creating a stack from it.

NOTE: make sure to create the stack in the us-east-1 region.
Since CloudFront only looks in the us-east-1 region to find the HTTPS certificate, that certificate needs to be created in that region.
It does mean that your S3 buckets are in us-east-1 as well; if you really care about performance of your website that much, you probably should not be using this tutorial at all, and dive deeper into what you really want.
{: .notice--warning}

Security warning: NEVER just download templates from the internet and run them in your AWS account, always check that they indeed do what you expect, and what they claim to do.
Doing otherwise is a security risk, and may even rake up huge bills.
So: download the template, read through it until you understand, and then run it.
{: .notice--danger}

{% gist 6c10b2da47bda52d7ced4e87c0f00681 %}

If you run this from the command line, use the following format; obviously adjust the parameter values to your needs; my parameters below will not work for you since you don't have access to this parent zone (if you use the console, just upload the template and fill in the parameters there).

```bash
aws cloudformation create-stack \
    --region us-east-1 \
    --stack-name sks-claude-apps-com \
    --template-body file://stack.yaml \
    --parameters ParameterKey=HostedZoneId,ParameterValue=Z0XXXXXXXXXXXX ParameterKey=HostedZoneName,ParameterValue=claude-apps.com ParameterKey=Hostname,ParameterValue=sks ParameterKey=PriceClass,ParameterValue=PriceClass_100
```

(Note that one has to give both the `HostedZoneId` and `HostedZoneName` for the parent zone; this is technically overkill, since both point to the same object, but is necessary because of a limitation of CloudFormation; at least it was last year when I created this stack. You could fix this with a `CustomResource` but that just adds a whole lot of complexity for little gain).

If you want a website on `www.claude-apps.com`, just use `www` as hostname (or omit the parameter, `www` is the default).
You will need to manually make a redirect somehow if you then want `claude-apps.com` to redirect to `www.claude-apps.com`.

This creates the following resources for you (assuming `claude-apps.com` for parent zone and `sks` for hostname):

- A Bucket with the name sks.claude-apps.com (if you cannot find this bucket, remember it's in us-east-1). The bucket is setup in a secure way (no public access, default encryption on, etc).
- A Bucket policy that allows access to CloudFront to read the `/website/` "directory".
- A certificate for `https://sks.claude-apps.com/`
- A CloudFront distribution that gets data from the S3 bucket and serves it on `https://sks.claude-apps.com/` (with the valid certificate). It will write its logs to a `/cloudfront-logs/` "directory" in the bucket.
- A DNS entry that points `sks.claude-apps.com` to CloudFront

If you go to your newly created website now (you may need to wait a couple of minutes (actually up to 24 hours max) for DNS to propagate), you should see an AccessDenied XML document.
This is a CloudFront error message, because it's looking for the `website/index.html` file (which is not there).
If you wait a couple of minutes, you should see a `cloudfront-logs/` directory appear in the S3 bucket, which should contain the log of your recent request.

Next, create a `/website/` directory in your bucket and add 2 files `index.html` and `404.html`.
Now if you reload your browser, you should see the index.html page.
If you request another (non existent) page, you will see the 404.html page.

<div markdown="1" class="notice">
A note on CloudFront and caching.
CloudFront is a CDN that allows one to easily serve content very fast from local locations around the globe.
In that, it's just a huge distributed reverse proxy.
In our setup we tell CloudFront not to cache anything; the only thing that CloudFront actually does for us is being the HTTPS endpoint.

In my simple usage (this is a static page, with some images and some css) this is fine; the page loads fast enough, and I'm not ever billed more than a couple of cents a year for traffic.
The upside of no caching is that you never have to worry about how long it takes before a change you made to the HTML files is visible to your users.
However once your website is stable, and you are starting to get more traffic, you might want to enable caching; I might write a post later on how to do that, for now it's outside the scope of this document.
If you start getting a (real) lot of traffic, you may also consider not storing all log files on S3, forever.
S3 is cheap, but if your logfiles start to grow to terrabyte size, probably you want to (re)move them.

As always, be aware that AWS is post-paid, and you could rake up enormous costs (allowing people to download files many gigabytes large from your website comes to mind); obviously, do things at your own risk, I can only share my experiences.
AWS has tools to "lock" your account if you start raking up unexpected costs; I would advice you to look into them if you're unsure of what you're doing.
</div>
