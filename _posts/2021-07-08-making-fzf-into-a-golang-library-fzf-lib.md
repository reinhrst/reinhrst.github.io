---
title: 'Creating Fzf into a library: fzf-lib'
description: Why and how of creating Fzf into a library
categories:
    - tech
tags:
    - fzf
    - go
toc: true
---
Over the past coupe of weeks I converted fzf into a go library, to be used in other projects.

[See fzf-lib on <i class="fab fa-fw fa-github" aria-hidden="true"></i> Github][1]{: .btn .btn--success}

# Introduction

Ever since I discovered [Junegunn Choi's fzf](https://github.com/junegunn/fzf) I've been a huge fan.
It has all the properties of a great product: extremely low learning curve, intuitive usage (just start typing, and pick your result), intuitive result order (the thing that you most likely wanted is on top), and extremely fast, even when searching through millions of lines of text.
Plus, once you get the hang of things, it _does_ have the power to use smartly chosen meta-characters that make your search so much easier.
It does all this through a highly configurable terminal interface, with helpful previews, and a vim plugin.
I think I use fzf hundreds of times a day, both during work and free time!

<figure>
  <script src="https://asciinema.org/a/RFPICdImQuLFkBDOEWnL2k1v3.js" id="asciicast-RFPICdImQuLFkBDOEWnL2k1v3" async data-autoplay="true" data-loop="1"></script>
  <figcaption>Let's search for some magic and strange animals in the fzf source code, using fzf in neovim.</figcaption>
</figure>

I have used fzf in multiple small projects I worked on.
Every time I somehow have a long (or even short) list of items, and I want to quickly use the keyboard to find the one I need, fzf is the way to go.
For commandline scripts, running in the terminal, this works great.
However there are moments when I wanted to integrate the functionality into some other program (specifically, I was working on a native macOS app that allowed logging in to AWS (using SAML/SSO), and then picking a role to assume, giving it to the terminal -- more on this in a later blog post).
The [fzf suggested way](https://junegunn.kr/2016/02/using-fzf-in-your-program) to do this, is to spawn an fzf process, using `--filter`, and then piping in the input and getting back the result.
There have been [multiple](https://github.com/junegunn/fzf/issues/2097) [github](https://github.com/junegunn/fzf/issues/1270) [requests](https://github.com/junegunn/fzf/pull/1053) to make fzf into a library, however the [main repository owner](https://github.com/junegunn) has declared no interest in this (mostly for the, _in my opinion completely valid_, reason that this is not the direction in which he wants to take the product, and it _would_ result in extra maintenance for him).

<hr>

Over the past years, whenever I wanted to use fzf in one of my own projects, I tended to alternate between 2 solutions:
- Rewrite the parts of fzf as a library
- Use fzf in [the suggested shell-spawn-option](https://junegunn.kr/2016/02/using-fzf-in-your-program)

I tended to start with writing a real simple fuzzy finder in whatever language I needed, then after a couple of hours realise that this is not so easy (or: only easy as long as you don't care too much about the details), then use the shell-spawn-option, right to the point where I ran into the limitations of that, after which I would spend a couple of more hours on the first option 😐.
Sigh.

Note that I call this second option the "shell-spawn-option".
It is actually not necessary to spawn a shell, it's enough to spawn an fzf-process without a shell.
So while not technically correct, I do feel that shell-spawn intuitively gives a better feeling for what's happening.
If you disagree, please read "fzf-process-spawning" where ever it says "shell-spawning".
{: .notice}

## Limitations of the shell-spawn-option
For most simple use cases, the shell spawn option works just fine.
There are a number of reasons though why this is not an ideal solution.

### Depends on fzf being installed and findable on the system
The shell spawn option only works if fzf can be found on the system that you're currently running on.
This means that for a non-tech-savvy end user, this may lead to a more complex installation method (i.e. install my tool, now do `brew install fzf`, etc...), and more error handling is needed in case the tool can not be found (or is the wrong version).

Shipping fzf with your tool could be a solution, but may be overkill, or not something you're happy to do.

### Fzf does not expose certain information using the shell-spawn-option
The shell-spawn-option (piping input into `fzf --filter`) is very powerfull, especially if combined with options like `--read0`, `--print0`, `--nth`, etc.
However there are two pieces of information that are not being exposed by this method: the score, and the positions where the characters match.
Every match in fzf has a score, something that says how good the match is. For instance, if you type `app` in the search window, then the string `apple grape pear` will have a high matching score (since `app` matches the start of the string).
Likewise, `avocado pear papaya` will get a high score as well, since the first letter of each word is matched.
The string `pear grape apricot` will still match, but at a much lower score, since the three letters matches are all through the words "pe**a**r gra**p**e a**p**ricot" (note that the letters need to appear in the string in the order that they are in the search term).
There is more information on the score, and what results in a higher score, in the fzf source code ([`src/algo/algo.go`](https://github.com/junegunn/fzf/blob/master/src/algo/algo.go)).

Fzf will sort the results by score (this can be controlled by commandline options), so it's questionable how useful the score is for the tool that uses fzf through a shell spawn, but it may still be interesting in some cases.

Another piece of information that gets lost when using fzf through a shell spawn, is _which_ letters of the matched string actually resulted in the matches.
When using fzf as an interactive process (see screencast above), one can see that parts of the matched strings are green.
These are the exact letters that the system matched in order to decide that the string is a match for your search (and to calculate the score).
If you're building a tool where a user can type in a search window, and see a list in realtime with the matching results, this sort of highlighting can make a lot of difference in understanding the results (and maybe seeing a typo in their search query).

Unfortunately there is no way to get this information when using fzf as a shell spawn.
It may be possible (and maybe even relatively easy) to modify fzf to expose this data in the output, but it's not available as-is.

### Shell spawning is slow; restarting fzf is slow
Depending on your programming language, starting a separate process and piping in all data to match, is slow-ish.
If you have a lot of data coming in (and coming out), it may easily take multiple hundreds of milliseconds; good enough for a one-time-operation, but resulting in a slugisch experience if trying to make a real-time-search-box.

In addition, when running fzf in a terminal, caching is used extensively.
To start off with, the input is read only once.
In addition, there are multiple places in the code where results are cached so that subsequent searches may be faster.
This way, fzf can search in near-realtime through the whole linux kernel source code (23M lines of code) on my macbook, when used interactively.

The shell-spawn method demands that you create a new fzf process for each subsequent search, meaning that you have to pipe in the input again, and all cache is empty.

In my experience, trying to make a realtime search with fzf in shell-spawn-mode (to search through a list of a couple of hundred items, and display the results in an macOS NSTableView), would result in a workable-but-not-quite-nice-experience.
I think that if there are more than 1000 items to search through, it would start to get too slow for comfort.

### Shell spawning is not always available
There might be situations where the shell-spawn option is not available.
One that comes to mind is in clientside code on a webpage.
Whereas it's possible to compile Go code to Web Assembly, you cannot compile an executable and then run it through some sort of commandline interface.

There may be other situations as well where executing programs from the file system is not allowed for security reasons, or just not supported (think of iOS, or embedded devices).

## Write it yourself option
As I mentioned, I have had at least a couple of moments in the past years where I decided to write an fzf clone that _would_ be available as a library.
Every time I would be full of enthusiasm at the start of the weekend, convinced I could do it in a couple of hours, and I always ended up defeated, at 4am on Monday morning, having created something that would work in some easy cases, some more complex cases, but would not get even _close_ to fzf in feature support, results being sorted in a useful way, or speed.

I'm not at all saying that it's impossble to write (all algorithms, and of course also the code to fzf, are open source); I'm just saying that it will take _a lot_ of time.

# Fzf-lib

## Parts of fzf
Above I described that neither shell spawning, nor writing one's own fzf seemed like a good solution to incorporate fzf into another program.
Over the past weeks I've instead focussed on seeing if I could not build a library based on the existing fzf code.

### The core of fzf
For me, the part of fzf that I always wanted to integrate into other systems is the part where the finding happens, basically the method that you give a whole bunch of strings, and a search string, and it returns all matches, with scores and match positions.
This is exactly the functionality that an `fzf --filter` gives you, without the downsides mentioned above.
For better or worse, I will call this the "core of fzf" in the rest of the post.

### The non-core of fzf
I never realised until I dove into the code, that fzf is so much more than just a fuzzy finder.
I would say that about <katex-inline class="keepfont">\frac{2}{3}</katex-inline> of the code (and maybe 80% of the commandline options) deals with other things than what I consider "the core fzf".
In addition to the core, there is code for:
- commandline interface, including options parsing, reading and parsing from `stdin`.
- An ncurses/terminal integration, that allows real-time searching, selecting one of the options, showing (customizable) previews and allowing one to define hotkeys for special operations.
- An ansi module that helps with filtering out ansi colour codes in the input strings, and then putting these codes back in the output.
- A VIM plugin for integration with (neo)vim
- *probably missing some things here....*

In making fzf-lib, I stripped out everything that is non-core.

### Stripping of options
Most of the commandline options/flags that fzf has, have to do with the non-core parts of fzf.
Obviously these options were stripped, since they only affect parts that I stripped from the library anyways.

In addition, some options have to do with input/output.
Things like `--nth` and `--with-nth` come to mind.
I made the choice _not_ to include these options in the library; they make sense in a commandline-world where everything is a string.
For fzf as a library however, I expect the containing program to keep a list of objects, send a list of strings (created from this objects) to the fzf library, together with a search word.
The results can then be matched back (by index) to the original objects, where the decision can be made of what to show to the user.

In the end, the only options that remain are:
- `Extended`: (set to false to get algorithm to perform as in fzf < 0.10.9; on commandline: `--extended`)
- `Fuzzy`: If Fuzzy == true, search without apostrophe prefix is fuzzy search word, with prefix is exact search. If Fuzzy == false, this is exactly the other way around. Opposite of commandline `--exact`.
- `--casemode`: Either match case insensitive, case sensitive or case smart (meaning insensitive, unless there is a capital letter in search word). On commandline controlled with `-i, +i, <nothing>`.
- `Normalize`: Normalizes unicode characters into their base-form. Opposite of `--literal` on commandline.
- `Sort`: Defines what to sort the results on.

Note that `--toc` which reverses search result is not supported; reversing a list should be trivial in the tool that makes the interface.

### Other things that got stripped
There are some other things that the library doesn't support (but should not be impossible to build in, should need arrise). Probably this is not an exhaustive list.
- Fzf can define a hotkey that switches sorting on and off (while searching).
In the library you make a choice for sorting on or off when you start searching.
This can not be changed halfway (although it should be easy to start a new search with the same words and sorting off).
- Fzf can search a stream, meaning that while you type it can listen for new lines coming in, which will be searched as well.
The library does not support this; if you have new lines that need to be searched as well, you have to restart your search.

## Result
I produced a working version of fzf as a library, which can be found [on <i class="fab fa-fw fa-github" aria-hidden="true"></i> Github][1].
It removes all the non-core parts, and leaves us with a very consise API (note, this is for version 0.8.7; for current version, please see the github page):

```go
func DefaultOptions() Options;  // get the default options struct
func New(hayStack []string, opts Options) *Fzf;  // create a new Fzf
func (fzf *Fzf) Search(needle string);  // start a search
func (fzf *Fzf) GetResultCannel() <-chan SearchResult;  // get the channel to listen on for results
func (fzf *Fzf) End();  // cleanup
func RunBasicBenchmark();  // run a quick benchmark
```

The idea is that you make a new `Fzf` object, fill it with hay (the stuff you search in) at startup time, and then call `Search`.
The results will come back through the result channel.
If you send a new search request before the old one finishes, the old one gets cancelled.
In the end, make sure to call `End()`, in order to clean up the resources used.

<figure markdown="1">
```go
package main

import (
    "fmt"
    "github.com/reinhrst/fzf-lib"
    "time"
    "sync"
)

func main() {
    var options = fzf.DefaultOptions()
    // update any options here
    var hayStack = []string{`hello world`, `hyo world`}
    var myFzf = fzf.New(hayStack, options)
    var result fzf.SearchResult
    myFzf.Search(`^hel owo`)
    result = <- myFzf.GetResultCannel()
    fmt.Printf("%#v", result)
    time.Sleep(200 * time.Millisecond)
    myFzf.Search(`^hy owo`)
    result = <- myFzf.GetResultCannel()
    fmt.Printf("%#v", result)
    myFzf.End()
}
```
<figcaption>Small example, showing lib-fzf in action</figcaption>
</figure>

The original fzf code has an assumption that only one search is running in the process, and that the process will end when the search ends.
In the library it should be possible to make multiple `Fzf` objects, each with different options and different hay, and do the searches in parallel, or interleaved.

## Performance
One of the reasons to fork-and-strip the original fzf code (as opposed to writing something from scratch) is the amazing performance of the original fzf code.

It is hard to say something about the "typical performance" of fuzzy search code.
This is because there are so many variables influencing how long a search takes, especially since fzf has a lot of "smart tricks" to cache intermediate results.
The following therefore is not a scientific result, but it should give a feel for the performance.

The library contains two benchmarks.
The first is a Go Test benchmark.
It takes a list of quotes (as in: famous quotes from famous people), concats this list to itself many times to get a bunch of hay (stuff to search in) of a certain size, and then (fuzzy) searches for the string `hello world`.
The benchmark measures the time it takes to create an Fzf object, do the search, retrieve the results and destruct the object.
Since only a single search is done, cache cannot be used; the results therefore are a lower bound.

This benchmark can be run by typing `go test --bench=.`.

There is a second benchmark, which is exposed as a Go function `RunBasicBenchmark()`.
The raison d'etre of this benchmark is that it's exported when the library is transpiled to different environments (something that I will be doing in a next blog post).
It is then easy to compare performance of the code in different environments.
(There is probably a better way to do this; I'm open to suggestions!)
{: .notice}

In this article we will compare the data of the first benchmark with performance data we get by running the following code (the `quotes.txt` file is the file from the testdata directory in the [fzf-lib repository][1]).

```bash
(for i in $(seq 20000); do cat quotes.txt; done) > quotes2.txt
wc -l quotes2.txt
#> 33280000 quotes2.txt
for i in $(seq 10 25); do echo $((2 ** i)); head -n $((2**i)) quotes2.txt | time fzf --filter "hello world" > /dev/null;  done
```

As you can see, we add 20000 copies of the `quotes.txt` file together, into `quotes2.txt` (so that the file has enough data when we ask for <katex-inline class="keepfont">2^{25}</katex-inline> lines of data).
We then pipe the first X lines of this file to `fzf --filter "hello world"`, and time how long it takes.

All tests were done on my MacBook Pro M1 (all binaries are compiled for Apple Silicon).
Because of the limitations of the `time` command, we only get 10ms resolution for the commandline runs.
I want to stress that I don't consider this to be a fair test of which code is better or faster (the original fzf, or fzf-lib).
Commandline fzf is spending extra time on piping in the data, reading and parsing it, and possibly other things.
However it does give a good idea of the ballpark performance we can expect from these systems.

items|time fzf-lib (ms)|time fzf cmdline (ms)
----:|------:|-----:|
1024|0.7|0
2048|1.1|10
4096|2.5|10
8192|4.8|20
16384|6.8|30
32768|12.9|50
65536|24.9|100
131072|48.9|210
262144|95.7|430
524288|190.9|860
1048576|380.1|1730
2097152|767.5|3490
4194304|1577.7|6960
8388608|3173.6|14,290
16777216|6588.1|28,500
33554432|33,097.6|58,230

{%include figure
    image_path="/assets/images/2021/07/08/results.png"
    alt="results chart"
    caption="Results in double-log chart. Clear to see that time taken scales as power-series"
%}

In the table and chart above, one can easily see that fzf-lib is faster than piping data into a spawned fzf process; usually by a factor 4.
Again I like to stress that it's not a fair comparison of raw performance and many factors may influence the result, however it does show that lib-fzf should not be slower than the suggested way to include fzf in third party software by piping into a spawned process.

Also remember this test cannot take advantage of caching, so I expect that as soon as 2 searches are done on the same haystack, fzf-lib's performance will increase a lot (I feel I should do a post on that in the future).

All in all, the numbers above show that, real-time searching through 50k items should not be a problem at all, even if we want to keep a large margin for slower hardware / other unexpected slowness.

## Version numbers
The library is currently (at moment of writing of this article) at v0.8.7.
The idea is to finish some api-breaking changes before soming to v1.0, which should be production ready.

The code was cloned from the fzf master branch on 8 June 2021, latest commit being `7191ebb615f5d6ebbf51d598d8ec853a65e2274d`.
This means that it's basically version `0.27.2`, with some bug fixes.
The git tags from the forked repository (with fzf releases numbers) have been removed from the fzf-lib github repository to avoid confusion.

# TODO for version 1.0
The wishlist for v1.0 is (in addition to extra (stress)tests):

- Send SearchProgess messages on the result channel if the search takes more than 200ms, so that a progress bar can be shown
- See if we can automatically call `myFzf.End()` when the item goes out of scope.
- Allow selection of algorithm v1, in case someone would want that.
- Probably some work to make this act nicely in the Go ecosystem.


[1]: https://github.com/reinhrst/fzf-lib
