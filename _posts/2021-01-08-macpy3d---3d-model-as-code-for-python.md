---
title: MacPy3D — 3D Model As Code for Python
description: 'Announcment of my new project: a python library to create 3d models as code'
date: '2021-01-08T17:58:05'
categories:
    - tech
    - macpy3d
tags:
    - python
    - 3d
original_post_medium_url: https://claude-e-e.medium.com/macpy3d-3d-model-as-code-for-python-58df4557036
header:
  image: /assets/images/2021/01/08/macpy3d-header.jpg
  teaser: /assets/images/2021/01/08/macpy3d-mascotte.jpg
---

I’ve always been the kind of person who cannot resist a good challenge, especially in programming. In addition, I’m one who likes to know what is going on, not just one to accept magic, accept bugs, accept that the computer knows better than me.

People who grew up with WordPerfect on DOS remember the days that in a word processor, you could look “under water” and see exactly what was going on. I remember “programming” logos and icons in javascript + canvas, rather than using photoshop — these days I try to exclusively use SVG. All so that my products are human-readable code, that I can check in, see diffs between versions, etc.

In the early days of 3D printers, I fired up [Blender](https://www.blender.org) to make 3D models, trying, [without success](https://blender.stackexchange.com/questions/18930/reset-blender-environment-on-each-script-run), to script the whole process. A couple of years later I got introduced to [OpenSCAD](http://openscad.org/), which solved most of my problems. [SolidPython](https://github.com/SolidCode/SolidPython) then made life easier, allowing writing code and doing debugging in Python rather than having to learn a new language (and a custom editor). Still, there was something missing. SolidPython just creates OpenSCAD code, so never has access to the raw data. OpenSCAD itself too often gave me obscure error message that only appear upon final rendering (meaning that I have to revert many many many iterations in order to find the exact spot where the error was introduced).

Don’t get me wrong — I very much appreciate all the work put into OpenSCAD and SolidPython, and for the time being I will probably keep using them for most of my 3D modelling needs. At the same time, why not try to get my hands dirty on something new. At the very least, I will get a better understanding of the complexities of 3d modelling software!

{% include figure
    image_path="/assets/images/2021/01/08/macpy3d-mascotte.jpg"
    alt="3d render of macpy3d mascotte on desk"
    caption="The MacPy3D mascotte “sitting” on my desk (note: this was made in Shapr3D on my iPad — it will be a goal of the project to design this in MacPy3D)"
%}

## MacPy3D

The goal of MacPy3D is to make a python library that allows one to create 3D models from code. This means that python → 3D objects rendering is separate from the viewing of the object (which allows you to bring your own viewing device, be it iPad, VR set, or just a good viewer on your platform), as well as separate from the editor. For a complete list of goals:

*   Create basic objects (cube / sphere / pyramid / etc)
*   Create objects by boolean combining of other objects
*   Import objects from file
*   Be fast! It should not be slower than OpenSCAD.
*   Clear, consise, stable, documented API
*   Good debugging — no more obscure CGAL errors. Every error message should lead you directly to the problem (e.g. it will tell you _which_ object is not properly closed, or _why_ a certain operation on two objects is not allowed).
*   [Boundary Representation](https://en.wikipedia.org/wiki/Boundary_representation): everything in MacPy3D are meshes. This means it’s trivial to introspect them, and for instance place something “3mm to the right of that other object”.
*   Allow full interaction with the models from python
*   Modular setup: Bring your own editor
*   Modular setup: Default viewer will be provided, but Bring Your Own Viewer is certainly supported
*   Modular setup: API for creating your own functions
*   Bonus goal: No external dependencies beyond Python + numpy (and possibly something like “pyopencl”). Mostly this means: no CGAL.
*   Bonus goal: Easy viewer on MacOS and iOS, with native gesture support.

## Next steps

Over the past weeks I have been spending some time hacking away at these problems. Most of all this has given me a greater understanding of the complexities of what I’m trying to do. I also found out that there is very little documentation out there on how to do these kind of things. Since I would like to both document what I did (for my own reference later), as well as contribute to the general knowledge out there, I now decided to start this series. Hopefully over the coming weeks, I’ll be able to post regular updates, explaining some concepts, explaining the complexities, and how to deal with them. Stand by….
