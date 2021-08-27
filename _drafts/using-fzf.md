---
title: 'Using a Go library (fzf-lib) in the browser'
description: I'm compiling the fzf-lib go library for use in the browser
categories:
    - tech
tags:
    - fzf
    - go
    - wasm
    - javascript
    - series Making fzf available in the browser
series: Making fzf available in the browser
toc: true
---

In this post I will describe how to compile a Go library for use in the browser.
It assumed that you're familiar with the [previous post in this series](../_posts/2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md).

In this post we will expose [`fzf-lib`](https://github.com/reinhrst/fzf-lib), so that we can make calls to it from JavaScript.
`fzf-lib` is a library-port [I made earlier](../_posts/2021-07-08-making-fzf-into-a-golang-library-fzf-lib.md) from Junegunn Choi's amazing commanline program [fzf](https://github.com/junegunn/fzf).

The following items are discussed in this post:
- Create a JavaScript interface for `fzf-lib`
- Compile `fzf-lib` and the interface into browser runnable code in three different ways (using Go, TinyGo and GopherJS)
- Create a JavaScript/TypeScript wrapper for `fzf-lib`
- Do some basic performance testing on the different solutions
- Bonus: do a performance optimisation

[Accompanying code for this post is available on <i class="fab fa-fw fa-github" aria-hidden="true"></i> Github](https://github.com/reinhrst/fzf-js){: .btn .btn--success}

# Step 0: Set up the environment
In order to follow the steps in this post, you need to have the following tools installed (If you need help installing any of these, Google is your friend :) :
- node/npm -- We use npm to orchestrate our buildsteps, and node/npm to transpile TypeScript into JavaScript. I have versions node (v16.4.2) and npm (7.18.1), but any recent version should do.
- Go -- to compile the library to WebAssembly using Go. I use version 1.16.5.
- TinyGo -- to compile the library to WebAssembly using TinyGo. I use version 0.19.0.
- GopherJS -- to compile the library to JavaScript. I use version 1.16.3+go1.16.5. GopherJS executable is installed under `~/go/bin/gopherjs` in my system; you may need to change some things in the example repo if it's different in your system.

This post described in broad strokes how to recreate the [`fzf-js` repo](https://github.com/reinhrst/fzf-js) (for MacOs/Linux; it probably needs some work to run it on Windows).
At the same time, it's not a list of commands you can copy and paste, and get to the same result -- most of the commands are printed verbatim, but sometimes I just write things like "create a new directory".

It's advised that you keep the `fzf-js` repo at hand for reference while you do these steps; or just clone this repo and `npm install` :).
The repo already contains the performance optimisation from the Bonus section; to access the version without the optimisation, get the `first-version` tag: [weblink](https://github.com/reinhrst/fzf-js/releases/tag/first-version), or in your cloned repo: `git co first-version`.

- Create a new directory `fzf-js`
- In this directory run `npm init`
- Now install `@types/golang-wasm-exec` and `typescript`: `npm install @types/golang-wasm-exec typescript`

# Step 1: Create an interface (the Go part)
As I discussed in [my previous post](../_posts/2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md), one needs to create an interface for a Go library to be used in JavaScript.
The interface exposes functions (and other things, like constants) to JavaScript.

As a side note: just today I ran into [this stackoverflow question/answer](https://stackoverflow.com/questions/68656435/how-to-get-all-headers-cookies-with-go-wasm) that suggests that at least in TinyGo it's possible to export Go functions to WebAssembly without the interface as described here.
I have not looked into this any further, since it doesn't seem to be a portable method (that would be usable across Go/TinyGo/GopherJS.
It would be interesting for a future post to look into this method.
{: .notice}

We'll create all the source-code in a `src` directory.
Create this, and run `go mod init github.com/reinhrst/fzf-js` (or however you want to call your 
Now we'll install `fzf-lib`: `go get github.com/reinhrst/fzf-lib@v1.0.0-beta1`.

Next we need to create an interface (the Go-side of the interface; later we will focus on the JavaScript side), a `main` package that registers functions that we can call from JavaScript.
Let's see what the library gives us (only the public fields):

```go
type Options struct {
    Extended bool
    Fuzzy bool
    // CaseRespect, CaseIgnore or CaseSmart
    CaseMode Case
    Normalize bool
    // Array with options from {ByScore, ByLength, ByBegin, ByEnd}.
    Sort []Criterion
}

type SearchResult struct {
    Needle        string
    SearchOptions Options
    Matches       []MatchResult
}

type MatchResult struct {
    Key       string
    HayIndex  int32
    Score     int
    Positions []int
}

type Fzf struct {}

func DefaultOptions() Options {}
func New(hayStack []string, opts Options) *Fzf {}
func (fzf *Fzf) GetResultChannel() <-chan SearchResult {}
func (fzf *Fzf) Search(needle string) {}
func (fzf *Fzf) End() {}
```

`fzf-lib` has an object-oriented-like interface.
One can create a new `Fzf` object, and run searches against it.
The search result comes back on a Go Channel.
At the end we need to call `End()` to free the object again.
In addition, there are a number of constants that we would need to export for the options.

Let's start with the easy bit: have a function that export the constants, so we can refer to them in JavaScript:

```go
func ExposeConstants(this js.Value, args []js.Value) interface{} {
    if !this.IsUndefined() {
        panic(`Expect "this" to be undefined`)
    }
    if len(args) != 0 {
        panic(`Expect no arguments`)
    }
    return map[string]interface{}{
        "ByScore": int(fzf.ByScore),
        "ByLength": int(fzf.ByLength),
        "ByBegin": int(fzf.ByBegin),
        "ByEnd": int(fzf.ByEnd),
        "CaseSmart": int(fzf.CaseSmart),
        "CaseIgnore": int(fzf.CaseIgnore),
        "CaseRespect": int(fzf.CaseRespect),
    }
}
```

If something about the format above is unclear, make sure to read my [previous post in the series](../_posts/2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md).

Now for the Fzf type, we want to do something special.
We want a function that returns something that feels like an Fzf object (with an `search()` and `end()` method).
JavaScript has no concept of Channels; asynchronous results are usually returned through callback functions, so that's what we'll do to.
We'll allow registering callback functions through `addResultListener()`.

The way to make the `New` function return something that looks like an object instance, is by defining the returned methods as closures within the constructor.
The constructor then returns a map (which is a JavaScript object) with the "methods" present.
It should be noted that technically these things are not really like what we thing of as JavaScript instance variables, but they behave like them in all normal operations.

```go
func New(this js.Value, args []js.Value) interface{} {
    if !this.IsUndefined() {
        panic(`Expect "this" to be undefined`)
    }
    if len(args) != 2 {
        panic(`Expect three arguments: hayStack, options`)
    }
    jsHayStack := args[0]
    jsOptions := args[1]
    var jsCallbacks []js.Value

    length := args[0].Length()
    if (length < 1) {
        panic(`Call fzf with at least one word in the hayStack`)
    }
    var hayStack []string
    for i :=0; i < jsHayStack.Length(); i++ {
        hayStack = append(hayStack, jsHayStack.Index(i).String())
    }

    opts := parseOptions(jsOptions)

    myFzf := fzf.New(hayStack, opts)

    go func() {
        for {
            result, more := <- myFzf.GetResultChannel()
            if !more {
                break;
            }
            for _, jsCallback := range jsCallbacks {
                jsCallback.Invoke(searchResultToJs(result))
            }
        }
    }()

    addResultListener := func (this js.Value, args []js.Value) interface{} {
        if len(args) != 1 {
            panic(`Expect 1 arguments: result listener`)
        }
        jsCallbacks = append(jsCallbacks, args[0])
        return nil
    }

    search := func (this js.Value, args []js.Value) interface{} {
        if len(args) != 1 {
            panic(`Expect 1 arguments: needle`)
        }
        needle := args[0].String()
        myFzf.Search(needle)
        return nil
    }

    end := func (this js.Value, args []js.Value) interface{} {
        if len(args) != 0 {
            panic(`Expect no arguments`)
        }
        myFzf.End()
        return nil
    }

    return map[string]interface{} {
        "addResultListener": js.FuncOf(addResultListener),
        "search": js.FuncOf(search),
        "end": js.FuncOf(end),
    }
}
```

Then the two (pretty straight-forward) helper functions, which map between Go and JavaScript formats:

```go
func parseOptions(jsOptions js.Value) fzf.Options {
    opts := fzf.DefaultOptions()
    if !jsOptions.Get("Extended").IsUndefined() {
        opts.Extended = jsOptions.Get("Extended").Bool()
    }
    if !jsOptions.Get("Fuzzy").IsUndefined() {
        opts.Fuzzy = jsOptions.Get("Fuzzy").Bool()
    }
    if !jsOptions.Get("CaseMode").IsUndefined() {
        opts.CaseMode = fzf.Case(jsOptions.Get("CaseMode").Int())
    }
    if !jsOptions.Get("Sort").IsUndefined() {
        sort := jsOptions.Get("Sort")
        opts.Sort = nil
        for i := 0; i < sort.Length(); i++ {
            opts.Sort = append(opts.Sort, fzf.Criterion(sort.Index(i).Int()))
        }
    }
    if !jsOptions.Get("Normalize").IsUndefined() {
        opts.Normalize = jsOptions.Get("Normalize").Bool()
    }
    return opts
}

func searchResultToJs(result fzf.SearchResult) map[string]interface{} {
    var matchResults []interface{}
    for _, match := range result.Matches {
        var positions []interface{}
        for _, pos :=  range match.Positions {
            positions = append(positions, pos)
        }
        matchResults = append(matchResults, map[string]interface{} {
            "key": match.Key,
            "hayIndex": match.HayIndex,
            "score": match.Score,
            "positions": positions,
        })
    }
    var searchResult = map[string]interface{}{
        "needle": result.Needle,
        "matches": matchResults,
    }
    return searchResult
}
```

And finally we register the functions in the global scope:

```go
func main() {
    c := make(chan struct{}, 0)
    js.Global().Set("fzfNew", js.FuncOf(New))
    js.Global().Set("fzfExposeConstants", js.FuncOf(ExposeConstants))
    <-c
}
```

Now we have something that, if we were to compile it (see next step), gives us a nice Javascript interface.
I will still want to wrap this into a proper interface on the JavaScript/TypeScript side, but for now, we have something that works!

# Step 2: Compile, and create a "hello world"

In this step we will compile the code using three different methods: with Go to WebAssembly, with TinyGo to WebAssembly and with GopherJS to JavaScript.

We will compile the code into `lib/go`, `lib/tinygo` and `lib/gopherjs` respectively.

After compilation, we will run the result in node, using the following small program:
```javascript
const myFzf = fzfNew(["hello world", "goodbye nothingness", "a bright new day"], {});
const needles = ["a ny", "oo", "'oo", "!oo"]
let i = 0
myFzf.addResultListener((result) => {
  console.log("Searching for '" + result.needle + "' resulted in " + 
    result.matches.map(match => match.key))
    i++
    if (needles[i] != undefined) {
      myFzf.search(needles[i])
    }
})
myFzf.search(needles[0])
})
```

One thing that is important when compiling Go to the browser, especially if you plan to serve it over the internet, is the size of the code.
Since Go has a lot of standard library that gets added, the size of even a simple Hello World program (as we saw in the previous post) is between 1 and 2 MB large.
It is possible to compress the result (using [Brotli](https://en.wikipedia.org/wiki/Brotli); a compression algorithm that performs better than GZIP and is supported by all major browsers; also see [here; at the bottom the section about Reducing Size](https://zchee.github.io/golang-wiki/WebAssembly/)).
For each compilation method, I will report the file size, both uncompressed and compressed.

## Compile Go to WebAssembly
Compiling Go to WebAssembly is easy using the built-in Go compiler. I use version 1.16.

In the `src` directory, run:
```bash
mkdir -p ../lib/go/
GOOS=js GOARCH=wasm go build -o ../lib/go/main.wasm
```

Now we have a WebAssembly (`.wasm`) file in the target directory.
This WebAssembly file needs a Go-specific javascript file for support, we will copy this from the Go directory to the target dir:

```bash
cp $(go env GOROOT)/misc/wasm/wasm_exec.js ../lib/go/wasm_exec.js
```

Now we're ready to create a file that:
1. Loads the `wasm_exec.js`
2. Creates a new `Go()` object
3. Load the WebAssembly into Node, then instntiate it and import into the Go object
4. Run the "hello world" code we described above

Create a file `main.mjs` in `lib/go` (the `.mjs` extension tells node that this file is a [JavaScript module]()https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules, meaning that `import ...` is supported.

```javascript
import {promises} from "fs"
import "./wasm_exec.js"

const go = new Go();
promises.readFile("main.wasm")
  .then(wasmcode => WebAssembly.instantiate(wasmcode, go.importObject))
  .then((result) => {
    go.run(result.instance)
    const myFzf = fzfNew(["hello world", "goodbye nothingness", "a bright new day"], {});
    const needles = ["a ny", "oo", "'oo", "!oo"]
    let i = 0
    myFzf.addResultListener((result) => {
      console.log("Searching for '" + result.needle + "' resulted in " + 
        result.matches.map(match => match.key))
        i++
        if (needles[i] != undefined) {
          myFzf.search(needles[i])
        }
    })
    myFzf.search(needles[0])
  })
```

And run `node main.mjs` should result in

```
Searching for 'a ny' resulted in a bright new day
Searching for 'oo' resulted in goodbye nothingness,hello world
Searching for ''oo' resulted in goodbye nothingness
Searching for '!oo' resulted in hello world,a bright new day
```

Success! If you want, you can try other hay and needles; it's proper `fzf-lib` runnig here!

<figure markdown="1">

|  |WebAssembly code|JavaScript code|Total
--|---|---|---
uncompressed|2'500'890|18'147|2'519'037
compressed|531'302|4'205|535'507

<figcaption>File sizes for WebAssembly and the supporting JavaScript (excluding `main.mjs`).</figcaption>
</figure>

As can be seen, this solution does lead to a minimal transfer-size of 500kB for the library.

## Compile TinyGo to WebAssembly
TinyGo was developed specifically to compile Go to run on constrained devices.
This could be a microcontroller (which has constrained storage), or a WebAssembly target (which has a constrained bandwidth to download the code).

TinyGo doesn't support the full Go standard library, and has some bugs, so I did have to make a couple of small changes to get `fzf-lib` to compile on TinyGo (they have been included in `fzf-lib` now); specifically I needed to remove all Regular Expressions (because of a bug), and remove `runtime.NumCPU()` (since it's not supported in TinyGo).

In addition, TinyGo has [an issue](https://github.com/tinygo-org/tinygo/issues/1790) that prevents the library to compile at the standard optimisation settings (`-opt=z`); we will compile with `-opt=2`. Supposedly `opt=z` should give a slightly smaller WebAssembly result, but I've been unable to test this (`-opt=s` should also give better file size compared to `-opt=2`, but in my tests the resulting files were exactly the same).

When compiling with TinyGo, we can also choose which Garbage Collection method should be used. By default it compiles with `-gc=conservative`; the only viable alternative is `-gc=leaking`, which switches off garbage collection completely.
In a next post we will look into this more closely, and see the influence that garbage collection has on performance; for now we choose the default option.

As with Go, we will compile TinyGo to its own target directory. The commands are very similar to Go (note that we have to get the `wasm_exec.js` from TinyGo now, it's not the same one as the Go one):


```bash
mkdir -p ../lib/tinygo/
tinygo build -target=wasm -opt 2 -o ../lib/tinygo/main.wasm
cp $(tinygo env TINYGOROOT)/targets/wasm_exec.js ../lib/tinygo/wasm_exec.js
```

Now create exactly the same `main.mjs` file that we created in the previous section (or copy it from the `lib/go` directory), and we're ready to run `node main.mjs`:

```
syscall/js.finalizeRef not implemented
syscall/js.finalizeRef not implemented
syscall/js.finalizeRef not implemented
syscall/js.finalizeRef not implemented
Searching for 'a ny' resulted in a bright new day
syscall/js.finalizeRef not implemented
Searching for 'oo' resulted in goodbye nothingness,hello world
syscall/js.finalizeRef not implemented
Searching for ''oo' resulted in goodbye nothingness
syscall/js.finalizeRef not implemented
Searching for '!oo' resulted in hello world,a bright new day
```

As you can see, the result is almost the same; it just has a bunch of `syscall/js.finalizeRef not implemented` messages; these are warnings are [a known issue](https://github.com/tinygo-org/tinygo/issues/1140), and for now we ignore them (they look terrible here; in the browser they will go to the JavaScript console, and nobody but developers will see them.

<figure markdown="1">

|  |WebAssembly code|JavaScript code|Total
--|---|---|---
uncompressed|2'500'890|18'147|2'519'037
compressed|531'302|4'205|535'507

<figcaption>File sizes for WebAssembly and the supporting JavaScript (excluding `main.mjs`).</figcaption>
</figure>















## Go WASM target

# Introduction
[The Go programming language is a statically typed, compiled programming language designed at Google][1].
One of the interesting features of Go is the [built-in concurreny][1], which lends itself to writing highly performing scripts.
One of those scripts, one that I use on a daily basis, is [Junegunn Choi's fzf](https://github.com/junegunn/fzf), an interactive tool that allows blazing fast searching for text in enourmous lists.
Last month I wrote about [my efforts to build a stand-alone library from the fzf project](../_posts/2021-07-08-making-fzf-into-a-golang-library-fzf-lib.md).

When there is a desire to interface with a commandline tool such as fzf, the "easy" way is to have your program run the fzf commandline program, send it data and read the result.
This works in most other programs, and I have used this successfully in Swift, in Python and in Bash.
If however we want to use fzf's functionality on a web page, we cannot run an external program.
In such a case, we need a version of the fzf library that runs in a web browser.

In order to run a code in a webbrowser, there are (globally speaking) 2 choices.
Since the early 1990s browsers ship with JavaScript, an interpreted language.
Over yime there have been many improvements to JavaScript, both in language features and in running speed.
In the last couple of years another method of running code in the browser has appeared: WebAssembly.
WebAssembly is a format that is much closer to the language that programs like Go are compiled into.
As such, we see more and more compilers over time that are able to compile code into WebAssembly.

Globally speaking we have 4 ways to get [fzf-lib](https://github.com/reinhrst/fzf-lib) to work in our browser:
- Automatically convert the Go code into JavaScript code
- Manually rewrite the Go code to (something that produces) JavaScript code
- Automatically covert the Go code to WebAssembly
- Manually rewrite the Go code to (something that produces) WebAssembly

<div markdown="1" class="notice">
Two remarks should be made about this list:

It should be noted first of all that although people do write JavaScript directly, larger projects tend to be written in other languages (such as TypeScript) which easily convert to JavaScript. The difference between compiling Go code to JavaScript and compiling something like TypeScript to JavaScript is that the latter is a much easier process. typeScript can be thought of as syntactic sugar on top as JavaScript; it for instance uses the same APIs and data structures. Therefore it's more likely that a TypeScript -> JavaScript compiler will produce (close to) optimal code, than a Go -> JavaScript compiler.

WebAssembly is another story.
WebAssembly is not human-friendly, and there are probably very few people programming WebAssembly by hand.
The reason why it may be more efficient to re-write the code into another language, and then compile to to WebAssembly, is that some compilers are more mature than others, some languages will allow more control over what WebAssembly is produced.

Secondly, there is a fifth option that should be described for completeness sake.
In order to get fzf like behaviour in a browser, the browser could make use of a backend.
In this case it would send the list of items to search in to the backend (a web address) together with a search query, and get the results back.
The backend could run any language (including Go), and even make use of the commandline fzf program.
There are however large disadvantages to this option:
- It would require someone to build (and pay for) a backend server to do this work
- It would send large lists of data to search in over the internet, resulting in relatively large delays
- There may be privacy/security implications related to sending all this data to another server (unless you run your own server).
</div>

In this post I will look at the viability of all four options, and look at the preformance of them, as well as things like code size, ease of use, stability, etc.
It should be kept in mind that I'm only testing one specific program.
In addition, the different methods that I'm testing were not all developed for the exact purpose that I have in mind.
In no way should this post be considered a definite answer to the question which method or project is "better".
At the same time, when I started out on this problem, I could not find *any* information on what methods were available, and what would be the upsides and downsides of all of them.

# The projects to test

We will be looking at four methods/projects.
Two of these are compilers from Go to WebAssembly; one is a compiler from Go to JavaScript.
As I was about to test these, I started to get interested in how these methods would perform against a version that was written directly in JavaScript; just as I was about to start work on that, I ran into [fzf-for-js][3], a project started literally a week after I has searched the whole Internet for just that :).
Fzf-for-js's author managed to rewrite fzf in TypeScript, trying to stay as close to the original Go code as possible.

This means that (for now) we cover 3 of the 4 categories to get Go programs to run in the browser.
It might be interesting to also have an WebAssembly optimised version (for instance, written in C, compiled to WebAssembly), although it remains to be seen what kind of extra speedup such a version would give us.

<div markdown="1" class="notice">
It's important to have a small side-panel on WebAssembly.
"Traditional wisdom" is that compiled programs run many times faster than interpreted programs.
Therefore it's tempting to assume that if you want something to be fast, you should look at WebAssembly.
There are blogposts out there trying to determine how much faster WebAssembly is; then there are plenty of blogs saying that these other blogs do it wrong, and don't get realistic results (mostly because they take trivial programs in tight loops, which is almost never what you encounter in real cyberlife).
Just a couple of months ago, a Surma, a Web Advocate at Google, did some tests and wrote a [very interesting article][4] on this subject.

A long read, but the first 2 lines say it all:

> Add WebAssembly, get performance. Is that how it really works?
> The incredibly unsatisfying answer is: It depends. It depends on oh-so-many factors, and I’ll be touching on some of them here.
</div>


## Go WebAssembly target
The standard Go compiler (we use Go version 1.16 here, the newest at the time of writing) can generate WebAssembly code, using `GOOS=js GOARCH=wasm go build -o main.wasm`.
Whereas Go is by now a mature language, powering products such as Docker and Kubernetes, the WebAssembly target feels a bit inmature as of yet.
While trying to get this all to work, in ran into a lot of small issues that did not seem to be documented anywhere.
[This page](https://github.com/golang/go/wiki/WebAssembly) describes WebAssembly in Go.

## TinyGo WebAssembly target
[Tinygo](https://tinygo.org) is meant to compile Go for embedded devices (where space considerations are more important) and WebAssembly.
Whereas the Go WebAssembly target for fzf-lib is around 2.5MB (this is uncompressed; WebAssembly code can be compressed to about 25% size for more efficient transfer), Tinygo produces files that are between 0.5 and 1MB in size (depending on what compile options are chosen).

The price for this reduction in size, is that not all Go library functionality is supported (in fzf-lib there is one function, runtime.NumCPU(), which is not supported in Tinygo at the moment).
I also ran into some differences between Go and Tinygo when converting between `int64` and `int`, but I'm not 100% sure that wasn't just my fault.
All in all it's amazing that the Tinygo developers manage to compile to a WebAssembly that is about 30% of the size of the one that Go produces.

TinyGo WebAssembly target also does not give me the feeling of a mature implementation.
For instance, compiling fzf-lib with default options leads to a very cryptic error message;
searching on this message showed [this issue](https://github.com/tinygo-org/tinygo/issues/1790) which has been open for almost 4 months now.
Again, I think the Tinygo developers do amazing work, however I do feel that some more work has to be done for this to become a stable feature.

It should be noted that TinyGo has compile-flags that allow one to set an optimisation level, and a garbage collector.
Those that have managed to work their way through [Surma's article][4] that I mentioned before, will remember that garbage collection can have a huge influence on performance.
[Available values](https://tinygo.org/docs/reference/usage/important-options/) for `-opt` are `0`, `1`, `2`, `s` and `z` (the default).
`0`, `1` and `2` here mean more optimisation, while `s` and `z` are supposed to mean "optimisation like `2`, but while reducing output size".
In my tests, `2` and `s` give exactly the same output, and `z` gives the error mentioned above; for that reason, I compiled with `2` for this test (where necessary, a quick mention is made of the differences between different optimisations).

There are 2 garbage collection strategies that can be used; the standard one (called `conservative`), and `leaking`, which means that never any garbagecollection is done.
Where possible I test both, although it should be very clear that `leaking` should only be used in production after very conserate thought and testing, since it's asking for your webpage being killed because of out-of-memory problems.

## GopherJS
GopherJS is a compiler from Go to Javascript (rather than WebAssembly).
As mentioned on its [github page](https://github.com/gopherjs/gopherjs), *[i]ts main purpose is to give you the opportunity to write front-end code in Go which will still run in all browsers.*

It is in active development, up to date (supports Go 1.16), and has been around for a while (first commits are in 2013), much longer than that Go and Tinygo has WASM compile targets.
The description however shows that the main goal is not necessarily performance, so it will be interesting to see how it performs.

## Fzf-for-js
Just 2 months ago, an effort was started to create a JavaScript (TypeScript) clone of fzf: [fzf-for-js][3].
The author first tried the GopherJS approach to compile directly to JavaScript, however found out that the Gopher generated code was 27k lines.
He therefore decided to "transcribe" the go code to TypeScript himself.
At this point most of the actual fzf searching (including fzf algorthm v2) is implemented.
Caching is not yet implemented at the time of writing; this should not influence our first round of performance tests, since we will actively avoid tests that can be cached.
It does mean that at this time it may not be usable yet for production use, however considering the speed with which development has progressed over the past few months, I would expect caching to be implemented soon.

Fzf-lib, which is the basis for the go compilers, has a slight extension over standard fzf, namely that it returns both the *score* of a hit, as well as the exact *positions* in the input string that the hit was made on.
Fzf-for-js returns at this moment only the *score*.
In order to come to a clean comparison, I will patch fzf-for-js so that it also returns the positions.


# Testing
I have thought for a long time on what would be the best, and fairest, way to compare the methods.
Even if all we care about is performance, it's unclear what performance is actually the most interesting, especially when considering this post is hoping to be useful beyond fzf-lib, for other go libraries.

## Considerations

### Which flow to test
First one has to decide what "flow" to test.
In this case, I generated 524288 (<katex-inline>2^{19}</katex-inline>) random lines of text (see repo for code, TODO).
In these lines, we fzf-search for the string "hello world" (the full operation is similar to `cat lines_524288.txt | fzf --filter "hello world"`).
We time how long it takes to load lines into fzf, and then how long it takes from the search command, until we have our result back.

There may certainly be other intersting things to measure; for instance, how long does a second search for the same string ("hello world") take.
Or, try a more realistic scenario where someone is typing into the search box and we want to show live results.
In this case we would search first for "h", then "he", then "hel", etc, until we get to "hello world".

TODO: write something on whether we also tested other flows, and if the results are the same.

### Test start and endpoint
A full run will start with loading the javascript and the lines to search in into the javascript process.
For the WebAssembly based systems, the `.wasm` also has to be loaded and setup in the javascript engine.

TODO: will later show test start and endpoints

In certain cases it may make sense to run the test in such a way that the start point and endpoint are in WebAssembly.

### Test runs / warm up time
Modern day JavaScript runs as a sort of multi-stage rocket (for an in-depth article about the trade-offs, see [here](https://mathiasbynens.be/notes/prototypes#tradeoffs)).
When JavaScript is run the first time, it's done so in a relatively slow interpreter.
As soon as the system notices that a certain bit of JavaScript is run more often, this part is sent off to a compiler.
The compiler actually makes the system a bit slower *while compiling*, but as soon as it's done, that part of JavaScript is now orders of magnitude faster.
In modern JavaScript engines, there may be even another stage, when even more compiling happens, and the code is even faster at the end.

Usually when I read articles comparing JavaScript to WebAssembly, the speed is compared only after a couple of runs.
This means that all code has been compiled by that time.

What the more usable metric is, is debatable.
A single-page web-app may be ok with a small slowdown at the start, whereas in some other cases every millisecond may count.
I will not allow javascript to warm-up / compile before the start of the main tests, however I will look at how much difference it would make if I did allow warm up.

### Where to run the tests
Both JavaScript and WebAssembly are being run within a JavaScript engine.
There are at least three major JavaScript engines out there (more depending on where you draw the line of what is "major").
Google Chrome and Node (and Microsoft Edge) run [v8][5].
Firefox runs [SpiderMonkey](https://en.wikipedia.org/wiki/SpiderMonkey), and Safari runs [JavaScriptCore](https://en.wikipedia.org/wiki/WebKit#JavaScriptCore).
There are stand-alone versions of these engines (which can be installed through [jsvu](https://github.com/GoogleChromeLabs/jsvu), which should make testing a lot easier.

TODO: where do we actually test.

### Versions to test
In order to make the tests not more complicated than necessary, I tested with the latest stable versions of all browsers, Node, Go, TinyGo and Gopher.
Considering the speed of development of fzf-for-js, I tested the latest dev version of this.

### Hardware to test on
All tests were done on a MacBook M1. All code ran in darwin-arm64/Apple Silicon mode; Rosetta was not used.

## Preparations
We decided to do a proper end-to-end test, where the data, where we start with the data to search in (the Hay) and the data to search for (the Needle) in JavaScript, and want our result back in JavaScript.
Since 3 of the 4 projects we're looking at, are automatic compilations from Go, we need to create an interface so that our JavaScript can talk to our Go code (which will be either WebAssembly or JavaScript itself).

TODO: damn this is a post by itself!










Links:
- https://github.com/golang/go/issues/28631 -- threading in go wasm compiler
- Web workers shared buffer: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer
- WASM threading (Rust repo): https://rustwasm.github.io/2018/10/24/multithreading-rust-and-wasm.html
- Rust multithreading
- TinyGo build options: https://tinygo.org/docs/reference/usage/important-options/


What would be a good thing to measure:
- init time
- search time (first time)
- search time (after a number of loops, without cache)
- incremental search time (with cache)

- Max search time (see tiny_wasm_slow)


We do the following:
- Start browser with http://localhost:8000/mypage.html?itemcount=....
- This loads the page, the javascipt and (if applicable) the wasm
- It loads haystack_#itemcount#
- settle() (sleep)
- logts
- init fzf with the haystack
- repeat 10 times:
    - logts
    - search "hello world"
    - logts
    - search "quick sting"
    - logts
    - search "walks weird"
    - logts
- make call to http://localhost:8000/log.html?test=safari,gopherjs,1024,ts1,ts2,.... (or print this data)


Running on the pure javascript engines would take more work; golang wasm file expects some polyfills which are not available

{%include figure
    image_path="/assets/images/2021/08/02/results.svg"
    alt="results chart"
    caption="Results"
%}

[1]: https://en.wikipedia.org/wiki/Go_(programming_language)
[2]: https://en.wikipedia.org/wiki/Go_(programming_language)#Concurrency:_goroutines_and_channels
[3]: https://github.com/ajitid/fzf-for-js
[4]: https://surma.dev/things/js-to-asc/index.html
[5]: https://en.wikipedia.org/wiki/V8_(JavaScript_engine)
