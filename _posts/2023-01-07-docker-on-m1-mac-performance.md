---
title: "Docker on M1/M2 macbook performance"
categories:
    - tech
tags:
    - docker
    - performance
    - apple silicon
toc: true
header:
    image: /assets/images/2023/01/07/header.jpg
---

Just a quick note to describe what [some others had already found before][1].
I was running [a compiler (the Nordic Semi Chip Compiler) under docker][2].
The docker image is available only for `x86_64/amd64` architecture, which was fine while I was giving it all a first spin.
However when I started to do more and more compilations, I started to get frustrated by the compilation times, and I was wondering how much could be saved by using an `arm64` docker image.

The [compiler docker image][2] needs some tweaking in order to compile to `arm64` (I will write another post about that soon, and open a PR to this repo with my changes), but once that is done, things are considerably faster.

Doing a clean build, took 30 minutes on the `x86_64/amd64` image, takes 13 minutes on the `arm64` image (meaning 2.3 times as fast).
The incremental build used to take 13 minutes, now takes a bit over 5 minutes, meaning a 2.5x speedup!

So, conclusion is, it's worth spending some time on obtaining / creating an `arm64` container if at all possible.

**Update**: I checked in the code to generate the docker image in [this fork][4], (posted it [as pull request][5] to the orginal repo, but not sure what will happen to it (it's not really a PR, it needs more work).

(TODO is obviously figuring out how fast the compilation would be without docker; I might do that at some time in the future).

Header photo credits: [https://www.circe.info/][3]

[1]: https://dev.to/oben/apple-silicon-mac-m1m2-how-to-deal-with-slow-docker-performance-58n0
[2]: https://github.com/NordicPlayground/nrfconnect-chip-docker
[3]: https://www.circe.info/
[4]: https://github.com/reinhrst/nrfconnect-chip-docker/tree/arm64
[5]: https://github.com/NordicPlayground/nrfconnect-chip-docker/pulls
