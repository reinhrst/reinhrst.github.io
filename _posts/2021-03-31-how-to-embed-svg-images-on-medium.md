---
title: How to embed SVG images on Medium
description: Guide how to embed SVG imaged on Medium
date: '2021-03-31T11:03:40Z'
categories:
  - tech
  - manual
tags:
  - howto
  - svg
  - medium
series: Scalar Vector Graphics (SVG)
original_post_medium_url: https://claude-e-e.medium.com/how-to-embed-svg-images-on-medium-eb2aaaca69ad
header:
  image: /assets/images/2021/03/31/header.png
  teaser: /assets/images/2021/03/31/teaser.svg
---

As you may know, [I am a great fan of SVG](./2021-02-25-ways-to-use-svg-in-your-html-page.md). I don’t think that SVG gets enough credit on the web, as a small file size, infinite resolution, declarative, next gen image format. A reason why SVG is not so popular, may be that may places that allow image upload, don’t allow SVG; such is the case here at Medium as well. There may be good reasons for this (cross browser compatibility, security, SVGs [acting different based on how you embed them](./2021-02-25-ways-to-use-svg-in-your-html-page.md)). However, in the end, I would love to embed some SVGs in Medium.

Note: This post was originally written on Medium, when my blog still lived there.
It makes more sense on Medium; it's just here for historical purposes.
Note that on jekyll, SVGs can just be embedded the same as (other) images.
The place in this text that supposedly shows an SVG embed is actually just an SVG image.
{: .notice}

Now obviously the foolproof way is to convert your SVG into a PNG image (you can even use just the OS level screenshot tool for this), however I’ve noticed multiple times that I was working on an article and I didn’t like having to repeatedly convert my SVG into PNG, and reupload the image. So time for a plan B. Also, any animation or interaction would get lost this way.

#### So tell me already: how to embed an SVG in medium

{% include figure
    image_path="/assets/images/2021/03/31/heatpump.svg"
    alt="Air air heatpump schematic (svg)"
    caption="Example: in SVG it’s easy to create an animation. This example of how a (very simple) air/water heat pump works, is only 20k in size. Note: SVG is licensed under CC BY-NC 4.0; Attribution-NonCommercial 4.0 International"
%}

It’s a simple 2 step approach:

1.  Create a public [GIST](https://gist.github.com/) (note: private GISTs won’t work — how do you expect Medium to read your private gist?) with 1 file in it. The 1 file needs to have extension `.svg` and should be a valid SVG file (notably: it needs to have either a `width` and `height` defined in the `<svg` tag, or a `viewBox`). You should see the SVG displayed on overview page of the gist.
2.  Copy the gist ID, and then create a url `https://www.richembeds.org/gistembed?gist-id=XXXXXX` (where `XXXXXX` is your gist id). If you paste this URL into a medium post (on it’s own line), after a couple of seconds you should see your SVG appear. If you want to try, the url to use for the example above is `https://www.richembeds.org/gistembed?gist-id=cbc33f2325d548ace4e375a02b3d5233`.

If somehow you encounter problems, send me a private message and I’ll look into it.

Note: at the moment the SVG is put in the page in an `<img` tag. This has some consequences for [the types of SVG features that are supported](./2021-02-25-ways-to-use-svg-in-your-html-page.md). I am considering in the future to allow more interactive embed, but I haven’t decided yet.

Note2: Upon first embedding an SVG, Medium (or embedly) caches the height of the embedded item for a while. If you change the viewBox (or width/height) of the item), it may take a while until the thing "fits" again into it’s box.

Note3: You can actually also directly use the gist embed system:

<figure>
  {% gist cbc33f2325d548ace4e375a02b3d5233 %}
  <figcaption>This is what happens if you just embed https://gist.github.com/reinhrst/cbc33f2325d548ace4e375a02b3d5233. This works better for some SVGs, and is less nice for others.</figcaption>
</figure>

#### How did you create this functionality

I intend to do a full write-up on how I built this functionality, by making an oEmbed / embed.ly plugin; let me know if you’d be interested in this, if there is enough interest I can prioritise it a bit :).
