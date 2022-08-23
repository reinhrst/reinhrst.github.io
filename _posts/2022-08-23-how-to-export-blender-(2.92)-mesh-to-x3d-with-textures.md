---
title: "How to export from Blender to X3D with textures"
categories:
    - how-to
tags:
    - blender
    - 3D
toc: false
---
This document is to describe the 3D Scanner App -> Blender -> X3D conversion. 3D Scanner App is a great app for making 3d scans. It can scan large areas, however on my iPhone 13 Pro it crashes when a single scan is more than 4GB large (note: this is not a hard limit; sometimes it crashes with 3.5GB, sometimes I have seen it succeed with 4.5GB scans). In the best case the scan is retained, however in my experience you should consider the scan lost in this case. It seems to hit the 4GB mark after 15 minutes of scanning. In order to be on the safe side, and have a bit of leeway, I like to plan the scans so that they take 10 minutes each. In theory you could make two scans with only 10cm overlap, and still align them later, however it depends on how distinct and changing the scene is; you will need to find the same object in both scans in order to align. I was scanning a rocky field, and I certainly needed 5 meter overlap in order to match different scans. After doing all this, the scans need to be stiched back together, this is what we use Blender for (and obviously, while we're here, we might do any number of things; simplifying meshes, adding things, etc). Finally I want to export the scan to a X3D file, so I may use it on the web.
It took me a good amount of time to get the textures correctly included in the final result, so I'm writing myself this little note on how to do this :).

In order to export something from 3D Scanner App to Blender we have several choices; they might give different results, but for me `obj` worked well.
When you export the scan `scan_1` from 3D Scanner App to a `obj` format, you end up with a `.zip` file with three files inside: `textured_output.obj`, `textured_output.jpg` and `textured_output.mtl`.
For now, just import the `.obj` file into a new Blender document (remove the default cube); later we'll see that it might be better to first do some work.
You'll see the prefectly textured scan in Blender and can play with it, or import a second (and third, etc) one that you want to align with the first.

## Aligning the scans

Let's first quickly discuss how to align the scans in Blender.
When scanning on an iPhone 13 Pro (and probably any other phone with an accelerometer), your scans will be correct in horizontal vs vertical orientation.
This means that to align two scans, you only need to move them (in X, Y and Z directions) and rotate around the Z axis.
You do *not* need to rotate around the X and Y axes.
I like to align them by finding a point that is in both scans, and moving one scan so that this point overlaps.
Then make the point the origin point of the mesh, and rotate in the Z direction until another point (ideally one that is far away in the X/Y direction) also lines up.
Now it should be fully aligned.

It should be noted that one could also use the 3 point align extension (which costs $6); and possibly there are automatic ways to align stuff (MeshLab seems to say on the webpage that it can do alignments, but I'm not sure how will it will work.

Now save the result as a `.blend` file (Blender's native format) and you feel that you're almost there, but no, there is a problem!

I have found that most 3D object files do NOT contain the texture(-image) in them. The `.blend` file only contains *links* to the textures, so if you move / delete the `textured_output.jpg` files that we saw earlier and open the `.blend` file again, you'll see that all textures are gone (so better not lose those original `.jpg`s!
There might be an option to include the textures in the `.blend` file, but this was not the case by default, for me.

## Exporting from Blender, first try
When exporting from Blender to `X3D`, it seems (in Blender 2.92) that the textures are completely ignored; an export is made with some default grayish material.
You can at this time edit the `.x3d` file by hand to get the right textures back (although we may also use MeshLab to make things a bit faster for us).
To do so, look for the `<Shape>` tag.
There should be one `<Shape>` tag for each of the imported scans (even if you *join* them into a single object in Blender; although depending on what other operations you do, your mileage may vary.
The `<Shape>` tag should have a child called `<Appearance>`; this is the tag that describes the material or texture.
In the default Blender X3D export it will have a `<Materal>` tag describing the mentioned graying colour.
Replace this `<Material>` tag by `<ImageTexture url="&quot;my_texture.jpg&quot;"/>` -- note the double quotes (`"`'s and `&quot;`'s) around the filename.
The filename should point to a valid URL (so the same directory or a subdirectory seems a good bet; if you go to another server, think about Cross Origin headers); don't use an absolute path to a filename, unless you intend to only use the X3D file locally (not in a browser).

So from something like
```
<Shape>
    <Appearance>
        <Material DEF="MA_material_0_002"
                  diffuseColor="1.000 1.000 1.000"
                  specularColor="0.001 0.001 0.001"
                  emissiveColor="0.000 0.000 0.000"
                  ambientIntensity="0.000"
                  shininess="0.000"
                  transparency="0.0"
                  />
    </Appearance>
    <IndexedFaceSet solid="false" ..... (etc) />
</Shape>
```
We go to
```
<Shape>
    <Appearance>
        <ImageTexture url="&quot;my_texture.jpg&quot;"/>
    </Appearance>
    <IndexedFaceSet solid="false" ..... (etc) />
</Shape>
```

There is some trial and error to find which `<Shape>` corresponds to which scan (and so needs which texture).
Either do them one at a time and check the result, or point them to different obvious textures (e.g. one points to a fully white texture, one to a fully blue one, etc).

## Exporting from Blender via MeshLab
There is a slightly simpler way to do the export with textures.
You can export from Blender to an `.obj` file, and then use MeshLab (2022.02) to import the `.obj` file and export to `.x3d`, with textures.
Use "Export Mesh As... (Shift-Cmd-E)" and select `.x3d` as export format.
On the next page you even have an option to export the texture files themselves, into the same directory.
In theroy this should all work great, but as soon as we have more than one scan, we run into a snatch: all texture files are called `textured_output.jpg` and they will all overwrite one another -- there seems to be an interface to rename the textures before saving, but I had only limited success with this.
We could fix this by manually copying the texture files and giving them unique names and then updating the `.x3d` file by hand, but there is a slightly easier solution.

Remember that before we said that an `obj` export actually creates three files: `textured_output.obj`, `textured_output.jpg` and `textured_output.mtl`.
This is actually the file discribing the 3D structure (`.obj`), the texture itself (`.jpg`) and a file linking the two (`.mtl`); MTL stands for (WaveFront) Materal Template Library.
These `.mtl` files can be opened with a text editor; the file accomanpying the export from 3D Scanner App contains:

```
newmtl material_0
Ka 0.100000 0.100000 0.100000
Kd 1.000000 1.000000 1.000000
Ks 0.000000 0.000000 0.000000
Tr 0.000000
illum 1
Ns 1.000000
map_Kd textured_output.jpg
```

The last line (obviously) points to the texture file.
It would probably have been great if, before we did any alignment in Blender, we had renamed all the `textured_output.jpg` files to something like `scan_1.jpg`, `scan_2.jpg` and change the accomanpying `.mtl` files; this way there would not have been any collisions in naming when exporting from MeshLab.
However if you don't want to start all over again, you can also do the renaming later; the `.obj` file exported from Blender has an accompanying `.mtl` file that points to all the textures (by absolute path):

```
# Blender MTL File: 'combined.blend'
# Material Count: 10

newmtl material_0
Ns 1.000002
Ka 1.000000 1.000000 1.000000
Kd 1.000000 1.000000 1.000000
Ks 0.000000 0.000000 0.000000
Ke 0.000000 0.000000 0.000000
Ni 1.450000
d 1.000000
illum 1
map_Kd /Users/XXXXXX/Downloads/scan_1_14_12_18/textured_output.jpg

newmtl material_0.001
Ns 1.000002
Ka 1.000000 1.000000 1.000000
Kd 1.000000 1.000000 1.000000
Ks 0.000000 0.000000 0.000000
Ke 0.000000 0.000000 0.000000
Ni 1.450000
d 1.000000
illum 1
map_Kd /Users/XXXXXX/Downloads/scan_2_14_23_03/textured_output.jpg

...
```

Within this file we can rename the textures (e.g. `/Users/XXXXXX/Downloads/scan_1_14_12_18/textured_output.jpg` -> `textures/scan_1.jpg`).
Now when we import to MeshLab it will use these (relative) paths -- do make sure the files exist on these paths, else MeshLab will replace them with dummy path.
Now the export to X3D will work as we want it.


