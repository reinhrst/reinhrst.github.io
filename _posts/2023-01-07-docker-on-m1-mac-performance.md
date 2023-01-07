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

Doing a clean build, took 30 minutes on the `x86_64/amd64` image, takes 13 minutes on the `arm64` image (meaning 2.3 times as fast). It can be a little bit faster by compiling to the `/tmp/` dir: 11:20.
The incremental build used to take 13 minutes, now takes a bit over 5 minutes, meaning a 2.5x speedup!

So, conclusion is, it's worth spending some time on obtaining / creating an `arm64` container if at all possible.

The terms `x86_64` and `amd64` are used interchangeably in this post. The same technology is also known as `x64`. The alternative `arm64` architecture is also known as `aarch64`. Personally I like the names `amd64` and `arm64` the most, if it wasn't for the fact that they are *so* similar (and I made mistakes by misreading them many times).
{: .notice--info}

**Update**: I checked in the code to generate the docker image in [this branch in my fork][4], (posted it [as pull request][5] to the orginal repo, but not sure what will happen to it (it's not really a PR, it needs more work).

Header photo credits: [https://www.circe.info/][3]

## Update 2: So what without docker

In order to give a good comparison, I also wanted to check how fast things were without Docker (so just running the compilation toolchain natively on MacOS).
It's a bit of a mess to set up (I still don't know how I did it exactly....) but after I managed to set it up, I couldn't believe by eyes:
The first clean compile I did took 2 minutes; the second and additional times, it was 40 seconds (I guess something gets cached somewhere, which doesn't get removed by removing the `/build/` dir. An incremental build takes 30 seconds.

This means that using an `arm64` docker container is about 20 times slower than native build, and an `amd64` container 40 times.
Now to be honest, most of the times I don't really care about docker container speeds, but it's very useful to know that when serious workloads are concerned, Docker on Apple Silicon is slow (as opposed to [docker on linux][6]).

To be honest, all results here are just from experience with this single toolchain, and it's not impossible that there is something else to blame for the difference in speed (it's probably worth one day to do a proper comparison) but for now: be aware with Docker on MacOS.

|   | full rebuild | incremental build |
|---|:-:|:-:|
|Native MacOS (first build ever)| 2:00 |  - |
|Native MacOS (subsequent build)| 0:40 |  0:30 |
|`arm64` docker container (use /tmp) | 11:20 | 4:10 |
|`arm64` docker container (use mounted host volume) | 13:00 | 5:20 |
|`x86_64` docker container (use mounted host volume) | 30:00 | 13:00 |

[1]: https://dev.to/oben/apple-silicon-mac-m1m2-how-to-deal-with-slow-docker-performance-58n0
[2]: https://github.com/NordicPlayground/nrfconnect-chip-docker
[3]: https://www.circe.info/
[4]: https://github.com/reinhrst/nrfconnect-chip-docker/tree/arm64
[5]: https://github.com/NordicPlayground/nrfconnect-chip-docker/pull/12
[6]: https://stackoverflow.com/questions/21889053/what-is-the-runtime-performance-cost-of-a-docker-container
