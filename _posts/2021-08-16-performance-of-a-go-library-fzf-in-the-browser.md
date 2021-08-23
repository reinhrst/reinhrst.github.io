---
title: 'Performance of a Go library (fzf-lib) in the browser'
categories:
    - tech
tags:
    - fzf
    - go
    - wasm
    - javascript
series: Making fzf available in the browser
toc: true
---

In past posts in this series, I looked at how to convert a Go library in order for it to work in the browser.
We used both the standard go compiler and TinyGo to compile Go code to WebAssembly, and we used GopherJS to compile Go code to JavaScript.
If you did not read that post, I [very much advice you to do so now](./2021-08-10-using-a-go-library-fzf-lib-in-the-browser.md); this post builds on that one, and readers are assumed to know the information in that post 

In this post we'll dive deeper into performance:
- We admit a new contender: [`fzf-for-js`](https://github.com/ajitid/fzf-for-js), a (manual) JavaScript port of `fzf`.
- In the last test we did one simple performance test; this time we'll test with different amounts of data to search in, and different access patterns.
- Some compilers allow different compile flags that influence performance, we'll play with those a bit.
- Before we simply tested in node; this time we'll extend the test to different platforms (i.e. browsers).
- As a bonus: We will make an active effort to enhance performance a bit more

# `fzf-for-js`, a manual JavaScript port of `fzf`
As I mentioned in the previous post, there are generally 4 ways to get some Go code to run in the browser: compile it to WebAssembly, compile it to JavaScript, manually write it in WebAssembly (or possibly in C and compile that) and manually write it in JavaScript.
In the last post I showed 2 solutions based on a Go -> WebAssembly compiler (Go & TinyGo), and a single solution based on a Go -> JavaScript compiler (GopherJS).
When I first started looking at compiling the Go code a couple of months ago, I did have in the back of my mind that I wanted to manually port it to JavaScript as well, if only to see how much better (or worse) I would be compared to the automatic tools.

Back then I had obviously checked if someone had already done this, and nobody had. So I was very surprised when a couple of weeks ago I ran into [`fzf-for-js` by `ajitid`](https://github.com/ajitid/fzf-for-js).
This project aims to port the `fzf` code (or at least the same part that I called the core, when deciding what to include in `fzf-lib`) -- so unlike some of the other efforts out there (including my own ill-conceived-now-discontinued one), he didn't try to reverse engineer the `fzf` code from example inputs and outputs, and then rebuild it in JavaScript (trust me, getting 95% to work, is no problem. The last 5% is hell!), but rather tries to port the Go code file by file.

In order to be accurate, I have to clarify something.
`fzf-for-js` is, like many large JavaScript projects, not actually written in JavaScript, but in TypeScript.
So technically it could look as if we're comparing a Go --> JavaScript compiler with a TypeScript to JavaScript compiler.
This is not the right way to look at it though; Go and JavaScript are hugely different languages and compiling from one to the other is far from trivial.
TypeScript on the other hand is just a wrapper around JavaScript; one writes JavaScript, with JavaScript standard libraries, just with types and some additional syntax to make the programmer's life easier.
So, from performance point of view it makes no difference if something is written in JavaScript or TypeScript, and I will treat them as similar in this post.
{: .notice}

The project is very new, and being actively developed (there were a dozen commits in just the last week).
Not everything is possible yet (for instance, at the time of writing caching is not yet included; I wouldn't be surprised if it is by the time you read this), however the hard part, getting the exact same behaviour as Fzf algorithm v2, is working.
I am running the tests here with [version v0.4.1 (revision 5c18f85)](https://github.com/ajitid/fzf-for-js/releases/tag/v0.4.1).

The author of this project asked me not to include this port yet in any performance-metric, since most of the work in the past couple of months has gone into getting the features to work, and not focus has been put yet on performance improvements 
I do think it's fair though to include it--with this disclaimer that no special focus has been put on performance yet.
I think that for others who contemplate different ways to get their Go code to run in the browser, it is extremely valuable to see as many options as possible, even if they are not yet fully developed, luckily the author agreed, and so I can include this now.

As we saw in the last post, one of the potential drawbacks of compiling code from Go to WebAssembly/JavaScript is the size of the output file.
In my last post I explained more about how we measure this for the different projects.
It's obvious that `fzf-for-js` takes home the crown for smallest library size (even if we take into account that maybe a small code increase is needed to gain full feature parity).


<figure markdown="1">

| |Go | TinyGo | GopherJs | GopherJs (minified) | `fzf-for-js` (es) | `fzf-for-js` (umd)
|-|---|--------|----------|---------------------|-------------------|-------------------
| Uncompressed| 2.5 MB | 698 kB | 1.7 MB | 1.1 MB | 13.7 kB | 14.7 kB |
| Brotli compression | 535 kB | 216 kB | 181 kB | 148 kB | 4.9 kB | 5.2 kB |

<figcaption markdown="1">`fzf-for-js` comes is two flavours, as es module, or as umd module. Either of them is in compressed form around 5kB, or about a factor 30(!) smaller than the smallest compiled Go version. (uncompressed the difference is even larger)
</figcaption>
</figure>

# Differences in results between versions
Obviously the expectation was that all four versions would give exactly the same results -- the same hay straws in the same order, with the same scores, and the same positions where the match was made.

During the tests I found that this was not 100% true; the first issue is that `fzf-for-js` sorts matches by length of the hay straw if requested (same as default behaviour for `lib-fzf`), however where `fzf` sorts on the trimmed length, `fzf-for-js` sorts on the non-trimmed length (a [pull request to fix this](https://github.com/ajitid/fzf-for-js/pull/72) was rejected by the author of `fzf-for-js`).
However `fzf-for-js` has an amazing option where one provides their own tiebreaker function; this way `fzf-for-js` can be made to behave the same as `fzf-lib`.

Another minute difference occured in positions reported by the compiled Go library and `fzf-for-js`; both were correct, but different. So for instance (a much simplified example, that doesn't actually result in a difference) if searching for `a` in `baa`, one method reports a match at positions `[1]`, the other at positions `[2]`.
The interesting thing is that `fzf-lib` reports the same positions if this is the forst search done; however if there were previous searches, sometimes a position is different.
I therefore consider this to be a bug in `fzf-lib`, probably to do with caching; it only happens very rarely, and not something I consider worth looking into more.

Finally, there is a small issue where there is a difference between the WebAssembly code (both through Go and TinyGo compilers) and the GopherJS code.
t seems to happen when calculating the length of a string with a non-ascii character in it.
Interesting difference, but not essential (for English speakers/Latin writers at least).

The conclusions needs to be that all 4 version (when using the custom tiebreaker for `fzf-for-js`) have (essentially) the same results for all practical purposes.

# Testing other kinds of data and access
I mentioned in the last post that the performance test we did then was a bit artificial.
We generated list of random sentences, and then looked for "hello world".
Obviously `fzf` in a browser could be used in any number of situations, however I expect in many case the search to be incremental, a user typing one letter at a time, and the browser showing results from each action.

Each test consists of searching for the fuzzy string "h", then "he" then "hel", until we search for "hello world" (needle) in a number of lines (the haystack).
The haystack will consist of the top `X` lines from the linux kernel source code (gotten by running `rg --line-number --no-heading . | head -n X` in the linux 5.14 rc 6 code tree.

<details markdown="1">
<summary>See an example of the lines we search in.</summary>
```
sound/last.c:22:		}
sound/last.c:23:	}
sound/last.c:24:	if (ok == 0)
sound/last.c:25:		printk(KERN_INFO "  No soundcards found.\n");
sound/last.c:26:	return 0;
sound/last.c:27:}
sound/last.c:29:late_initcall_sync(alsa_sound_last_init);
kernel/configs.c:1:// SPDX-License-Identifier: GPL-2.0-or-later
kernel/configs.c:2:/*
kernel/configs.c:3: * kernel/configs.c
kernel/configs.c:4: * Echo the kernel .config file used to build the kernel
kernel/configs.c:5: *
kernel/configs.c:6: * Copyright (C) 2002 Khalid Aziz <khalid_aziz@hp.com>
kernel/configs.c:7: * Copyright (C) 2002 Randy Dunlap <rdunlap@xenotime.net>
kernel/configs.c:8: * Copyright (C) 2002 Al Stone <ahs3@fc.hp.com>
kernel/configs.c:9: * Copyright (C) 2002 Hewlett-Packard Company
kernel/configs.c:10: */
kernel/configs.c:12:#include <linux/kernel.h>
kernel/configs.c:13:#include <linux/module.h>
kernel/configs.c:14:#include <linux/proc_fs.h>
kernel/configs.c:15:#include <linux/seq_file.h>
kernel/configs.c:16:#include <linux/init.h>
kernel/configs.c:17:#include <linux/uaccess.h>
kernel/configs.c:19:/*
kernel/configs.c:20: * "IKCFG_ST" and "IKCFG_ED" are used to extract the config data from
kernel/configs.c:21: * a binary kernel image or a module. See scripts/extract-ikconfig.
kernel/configs.c:22: */
kernel/configs.c:23:asm (
kernel/configs.c:24:"	.pushsection .rodata, \"a\"		\n"
kernel/configs.c:25:"	.ascii \"IKCFG_ST\"			\n"
kernel/configs.c:26:"	.global kernel_config_data		\n"
kernel/configs.c:27:"kernel_config_data:				\n"
kernel/configs.c:28:"	.incbin \"kernel/config_data.gz\"	\n"
kernel/configs.c:29:"	.global kernel_config_data_end		\n"
kernel/configs.c:30:"kernel_config_data_end:			\n"
kernel/configs.c:31:"	.ascii \"IKCFG_ED\"			\n"
kernel/configs.c:32:"	.popsection				\n"
kernel/configs.c:33:);
kernel/configs.c:35:#ifdef CONFIG_IKCONFIG_PROC
kernel/configs.c:37:extern char kernel_config_data;
kernel/configs.c:38:extern char kernel_config_data_end;
kernel/configs.c:40:static ssize_t
kernel/configs.c:41:ikconfig_read_current(struct file *file, char __user *buf,
kernel/configs.c:42:		      size_t len, loff_t * offset)
kernel/configs.c:43:{
kernel/configs.c:44:	return simple_read_from_buffer(buf, len, offset,
kernel/configs.c:45:				       &kernel_config_data,
kernel/configs.c:46:				       &kernel_config_data_end -
kernel/configs.c:47:				       &kernel_config_data);
kernel/configs.c:48:}
kernel/configs.c:50:static const struct proc_ops config_gz_proc_ops = {
kernel/configs.c:51:	.proc_read	= ikconfig_read_current,
kernel/configs.c:52:	.proc_lseek	= default_llseek,
kernel/configs.c:53:};
kernel/configs.c:55:static int __init ikconfig_init(void)
kernel/configs.c:56:{
kernel/configs.c:57:	struct proc_dir_entry *entry;
kernel/configs.c:59:	/* create the current config file */
kernel/configs.c:60:	entry = proc_create("config.gz", S_IFREG | S_IRUGO, NULL,
kernel/configs.c:61:			    &config_gz_proc_ops);
kernel/configs.c:62:	if (!entry)
kernel/configs.c:63:		return -ENOMEM;
kernel/configs.c:65:	proc_set_size(entry, &kernel_config_data_end - &kernel_config_data);
kernel/configs.c:67:	return 0;
kernel/configs.c:68:}
kernel/configs.c:70:static void __exit ikconfig_cleanup(void)
kernel/configs.c:71:{
kernel/configs.c:72:	remove_proc_entry("config.gz", NULL);
kernel/configs.c:73:}
kernel/configs.c:75:module_init(ikconfig_init);
kernel/configs.c:76:module_exit(ikconfig_cleanup);
kernel/configs.c:78:#endif /* CONFIG_IKCONFIG_PROC */
kernel/configs.c:80:MODULE_LICENSE("GPL");
kernel/configs.c:81:MODULE_AUTHOR("Randy Dunlap");
kernel/configs.c:82:MODULE_DESCRIPTION("Echo the kernel .config file used to build the kernel");
block/blk-core.c:1:// SPDX-License-Identifier: GPL-2.0
block/blk-core.c:2:/*
block/blk-core.c:3: * Copyright (C) 1991, 1992 Linus Torvalds
block/blk-core.c:4: * Copyright (C) 1994,      Karl Keyte: Added support for disk statistics
block/blk-core.c:5: * Elevator latency, (C) 2000  Andrea Arcangeli <andrea@suse.de> SuSE
block/blk-core.c:6: * Queue request tables / lock, selectable elevator, Jens Axboe <axboe@suse.de>
block/blk-core.c:7: * kernel-doc documentation started by NeilBrown <neilb@cse.unsw.edu.au>
block/blk-core.c:8: *	-  July2000
block/blk-core.c:9: * bio rewrite, highmem i/o, etc, Jens Axboe <axboe@suse.de> - may 2001
block/blk-core.c:10: */
block/blk-core.c:12:/*
block/blk-core.c:13: * This handles all read/write requests to block devices
block/blk-core.c:14: */
block/blk-core.c:15:#include <linux/kernel.h>
block/blk-core.c:16:#include <linux/module.h>
block/blk-core.c:17:#include <linux/backing-dev.h>
block/blk-core.c:18:#include <linux/bio.h>
block/blk-core.c:19:#include <linux/blkdev.h>
block/blk-core.c:20:#include <linux/blk-mq.h>
block/blk-core.c:21:#include <linux/blk-pm.h>
block/blk-core.c:22:#include <linux/highmem.h>
block/blk-core.c:23:#include <linux/mm.h>
block/blk-core.c:24:#include <linux/pagemap.h>
block/blk-core.c:25:#include <linux/kernel_stat.h>
block/blk-core.c:26:#include <linux/string.h>
```
</details>

All tests are run in node (v16.4.2).
We increase the haystack in steps of factor 2 from 1024 until 16.4M lines.
Between runs with different haystack sizes, node is restarted.
I run the use the code used in the last post ([tag `performance-testing` of the `fzf-js` repo](https://github.com/reinhrst/fzf-js/releases/tag/performance-testing)).

The `main.mjs` file is pretty much the same as in the last post, however with some small changes to do multiple searches, and output the output that we need.

<details markdown="1">
<summary>See the main.mjs file</summary>
The version compatible with the Go interface
```javascript
import {createReadStream} from "fs"
import {Writable} from "stream"


function memoryUsageInMiB() {
  const memUsage = process.memoryUsage()
  let memUsageMiB = {}
  for (let key in memUsage) {
    memUsageMiB[key] = memUsage[key] / 1024 / 1024
  }
  return memUsageMiB
}

function increase(s, start) {
  let items = []
  for (let i=start; i <= s.length; i++) {
    items.push(s.slice(0, i));
  }
  return items
}

const filename = process.argv[2]

let startTime = Date.now()

function logTime(message) {
  const now = Date.now()
  console.log(message, now, now - startTime)
}

async function readLinesFromFile(filename) {
  const p = new Promise((resolve, _reject) => {

    let buffer = ""
    const lines = []
    const writableStream = new Writable({
      write: (chunk, _encoding, next) => {
        buffer += chunk.toString()
        let index
        while ((index = buffer.indexOf("\n")) != -1) {
          lines.push(buffer.slice(0, index))
          buffer = buffer.slice(index + 1)
        }
        next()
      },
      final: (callback) => {
        if (buffer.length > 0) {
          lines.push(buffer)
        }
        callback()
        resolve(lines)
      }
    })
    createReadStream(filename, "utf-8").pipe(writableStream)
  })
  return p
}

console.log("fzf-type:", process.argv[1].split("/").slice(-2, -1)[0])
logTime("start")
import {Fzf} from "./index.mjs"
logTime("js/wasm loaded")
const lines = await readLinesFromFile(filename)
logTime(`lines.txt loaded: ${lines.length} lines`)

SetStartTime("" + startTime)
logTime("startTimeSet")

const needles = [
  ...increase("hello world", 1)
]

const myFzf = new Fzf(lines)
logTime("Fzf initialized")
let searchStartTime = Date.now()
let searchTotalTime = 0
let i = 0

myFzf.addResultListener((result) => {
  logTime("Search done")
  console.log("Searching for '" + result.needle + "' resulted in " + result.matches.length + " results.")
  const timePassed = Date.now() - searchStartTime
  searchTotalTime += timePassed
  console.log("---", filename, timePassed, searchTotalTime, result.needle)
  setTimeout(searchNext, 0)
})

function searchNext() {
  if (i < needles.length) {
    searchStartTime = Date.now()
    myFzf.search(needles[i++]);
  } else {
    console.log(memoryUsageInMiB())
  }
}

searchNext()
```

The `fzf-for-js` has a slightly different ending:
```javascript
const myFzf = new Fzf(lines, {match: extendedMatch, tiebreakers: [ byLengthAsc ]})
logTime("Fzf initialized")
let searchStartTime
let searchTotalTime = 0

for (const needle of needles) {
  searchStartTime = Date.now()
  console.log("Search start: ", needle)
  let result = myFzf.find(needle)
  console.log("done")
  logTime("Search done")
  console.log("Searching for '" + needle + "' resulted in " + result.length + " results.")
  const timePassed = Date.now() - searchStartTime
  searchTotalTime += timePassed
  console.log("---", filename, timePassed, searchTotalTime, needle)
}
console.log(memoryUsageInMiB())
```
</details>

There's also a version that used `fzf-lib` in Go, which will be compiled directly to native code.
This serves as base-line; no matter what optimizations we do, it's unlikely that we will ever be faster than this.

## Memory
Let's start by seeing how much memory each process uses.

I use `time -v` to print memory information after a process has ended, and record the `	Maximum resident set size (kbytes):` line.
In the table below are the results.

Obviously memory increases with haystack size; it's probably nicer to plot the memory divided by haystack size.

<details markdown="1">
<summary>See memory usage table</summary>
<figure markdown="1">

{% include_relative 2021-08-16/memory_per_straw.table.md %}

<figcaption>Memory in MiB (Memory divided by haystack size in kiB)</figcaption>
</figure>
</details>

{%include figure
    image_path="/assets/images/2021/08/16/memory_per_straw.svg"
    alt="graph of memory usage"
    caption="Memory divided by haystack size (obviously) decreases with increasing haystack (since overhead is smaller percentage). Therefore only results for larger haystack are shown. Relative differences are interesting."
%}
![]()

Note that I'm pushing the system to the limit, and not all compilation methods deal well with large input files, hence the gaps.
Most methods crash with an out-of-memory error; the exception is TinyGo.
TinyGo keeps running, (node process 100%) without showing any progress.

## Execution time

The runtime is the time from the moment we have finished reading the haystack into JavaScript, until the last search finishes.

<details markdown="1">
<summary>See execution time table</summary>
<figure markdown="1">
{% include_relative 2021-08-16/performance.table.md %}

<figcaption>Total time in seconds (time divided by haystack size in microseconds). Note that this is the time for the init plus 11 searches combined, not the time for a single search.</figcaption>
</figure>
</details>

In the graph I show how the time is used: the lowest (darker) block is the time spent in `new Fzf()`, basically loading the haystack into fzf.
The blocks above are each for 1 extra typed letter; so the second block from the bottom is for searching "h", the third is for "he", the fourth for "hel", etc.
The lighter blocks on top are for when the needle starts to be 2 words, so "hello ", "hello w", "hello wo", etc.

{%include figure
    image_path="/assets/images/2021/08/16/performance.svg"
    alt="graph of execution time"
    caption="Execution time divided by haystack size."
%}

There are a number of interesting observations in this graph.

First (and I think it will not surprise anyone) is that native Go code is the fastest.
It does help that Native Go is the only one that is able to use multiple cores (see also my previous post), but also, `fzf` was optimised to run super fast, on native Go.

Next, for relatively small haystack sizes (until <katex-inline>2^{12}</katex-inline> = 4096), Go and TinyGo seem to offer the fastest solutions -- although total runtime for the full iteration is around 100ms at this numbers, so it's questionable that it actually matters much which is faster here.
For larger sizes, `fzf-for-js` is about twice as fast as Go and TinyGo.
GopherJS always is the slowest solution.

At larger haystack sizes, performance starts to suffer a lot.
Especially TinyGo suffers here; at a haystack of 1M, total runtime goes from 23 seconds (for 512k straws) to over 600 seconds.
At haystack size of 2M, searching for "h" takes more than 1 hour, and "he" at least another hour (after which I killed the process).

Something else that can be seen is that for all methods except `fzf-for-js`, contributions of the light-coloured searches (search for "hello " + something) is very small.
This is because `fzf-lib` uses its cache to quickly limit the search-set to only those straws that matched "hello", meaning that any additional search is relatively fast.
As mentioned, `fzf-for-js` does not have caching yet, so the contribution of the light-coloured items is much larger.

`fzf-for-js` is clearly the winner here, since it performs fastest (of all web-based solutions), and does not crash for large haystacks.

## Execution time: Search algorithm only
We saw [in the last post on the subject ](./2021-08-10-using-a-go-library-fzf-lib-in-the-browser.md), that a large part of execution time for the WebAssembly based solutions is spent on copying/encoding/decoding data between Go/WebAssembly and JavaScript.
In that post I showed a quick speedup using JSON, and proposed some solutions to further speed up this interface.
True enough, a large part of the execution time seen in the previous section, is spent on transferring data between the two layers.

Rather than looking for specific speedups now, it may be interesting to take the idea to its extreme: measure only the clean running time of of the algorithm, not caring about the setup  (`new Fzf()`) cost or the time it takes to send the search request from JavaScript to Go, or the result back.
This will obvioulsy not influence the go-native timings, or `fzf-for-js`.
GopherJS may see a very small speedup, but the WebAssembly code should benefit a lot from this.

<details markdown="1">
<summary>See algorithm execution time table</summary>
<figure markdown="1">

{% include_relative 2021-08-16/performance-per-straw-no-interface.table.md %}

<figcaption>Total time in seconds (time divided by haystack size in microseconds)</figcaption>
</figure>
</details>

{%include figure
    image_path="/assets/images/2021/08/16/performance-per-straw-no-interface.svg"
    alt="graph of execution time for the core algorithm"
    caption="Execution time divided by haystack size (only the algorithm)"
%}

Both Go and TinyGo now perform better than `fzf-for-js` up until 2<sup>18</sup> = 250k items in the haystack; however at closer inspection one can see that searching the first five strings ("h", "he", "hel", "hell", and "hello") the three methods are pretty similar.
Only in the light part of the bar does `fzf-for-js` spend much more time than the WebAssembly methods.
This is due to the fact that `lib-fzf` relies heavily on caching here; it only searches in the (cached) subset of lines that match "hello".
As I mentioned before, caching is on the roadmap for `fzf-for-js`, which should make it just as fast as the two WebAssembly based methods.

I should stress again that this test is only on the pure algorithm, without returning the data to JavaScript; returning data to JavaScript is instantaneous for `fzf-for-js`, where for the other 2 methods there is overhead, no matter how many smart tricks one uses there.

From careful inspection of the graph, another interesting thing can be observed.
(Especially) TinyGo sometimes has long delays in places where one would not expect them; for instance at 2<sup>17</sup> and 2<sup>18</sup> we see green blocks that are much taller than the ones below them, meaning that a search for a longer string too much longer (there are even long light-green blocks, for searches that should have been near instantaneous.

Obviously the system is doing more work than it needs to during that time, so there is possibility for further optimisation.
I have a strong hunch that this is due to the garbage collector ([also due to Surma's experience with this](https://surma.dev/things/js-to-asc/index.html)); we'll look at this in the next section.

## Play with the Garbage Collection
Both Go and JavaScript have 
