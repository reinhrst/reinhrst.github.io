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
It assumed that you're familiar with the [previous post in this series](g2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md), as well have at least a basic understanding of Go, JavaScript and TypeScript.

I'm going to expose [`fzf-lib`](https://github.com/reinhrst/fzf-lib), so that we can make calls to it from JavaScript.
`fzf-lib` is a library-port [I made earlier](g2021-07-08-making-fzf-into-a-golang-library-fzf-lib.md) from Junegunn Choi's amazing command line program [fzf](https://github.com/junegunn/fzf).

The following items are discussed in this post:
- Create a JavaScript interface for `fzf-lib`
- Compile `fzf-lib` and the interface into browser runnable code in three different ways (using Go, TinyGo and GopherJS)
- Create a JavaScript/TypeScript wrapper for `fzf-lib`
- Do some basic performance testing on the different solutions
- Bonus: do a performance optimisation

[Accompanying code for this post is available on <i class="fab fa-fw fa-github" aria-hidden="true"></i> GitHub](https://github.com/reinhrst/fzf-js){: .btn .btn--success}

<div markdown="1" class="notice">
In this post I will compile Go code to WebAssembly (with two different tools) and to JavaScript code.
We will look at performance later, but it's important to dispel some prejudices here (in as far as they exist).

WebAssembly is (as the name suggests) assembly code, compiled code, whereas JavaScript is an interpreted language.
"Traditional wisdom" is that compiled programs run many times faster than interpreted programs.
Therefore it's tempting to assume that if you want something to be fast, you should look at WebAssembly.

There are blog posts out there trying to determine how much faster WebAssembly is; then there are plenty of blogs saying that these other blogs do it wrong, and don't get realistic results (mostly because they take trivial programs in tight loops, which is almost never what you encounter in real cyberlife).
Just a couple of months ago, a Surma, a Web Advocate at Google, did some tests and wrote a [very interesting article](https://surma.dev/things/js-to-asc/index.html) on this subject.

A long read (but very much worth it!); but if you don't have the time, just read the first two lines:

> Add WebAssembly, get performance. Is that how it really works?
>
> The incredibly unsatisfying answer is: It depends. It depends on oh-so-many factors, and I’ll be touching on some of them here.
</div>


## Step 0: Set up the environment
In order to follow the steps in this post, you need to have the following tools installed (If you need help installing any of these, Google is your friend :) :
- node/npm -- We use npm to orchestrate our build steps, and node/npm to transpile TypeScript into JavaScript. I have versions node (v16.4.2) and npm (7.18.1), but any recent version should do.
- Go -- to compile the library to WebAssembly using Go. I use version 1.16.5.
- TinyGo -- to compile the library to WebAssembly using TinyGo. I use version 0.19.0.
- GopherJS -- to compile the library to JavaScript. I use version 1.16.3+go1.16.5. GopherJS executable is installed under `~/go/bin/gopherjs` in my system; you may need to change some things in the example repo if it's different in your system.

This post describes in broad strokes how to recreate the [`fzf-js` repo](https://github.com/reinhrst/fzf-js) (for MacOs/Linux; you may have to improvise a bit if you're on Windows).
At the same time, it's not a list of commands you can copy and paste, and get to the same result -- most of the commands are printed verbatim, but sometimes I just write things like "create a new directory".

It's advised that you keep the `fzf-js` repo at hand for reference while you do these steps; or just clone this repo and `npm install` :).

The repo uses tags to get you the code for different sections of this article:

- [Tag `first-version`](https://github.com/reinhrst/fzf-js/releases/tag/first-version) is the code we're making in step 1 and 2.
- [Tag `performance-testing`](https://github.com/reinhrst/fzf-js/releases/tag/performance-testing) is the code we use (surprise!) in the performance testing section.
- Finally [tag `bonus-speedup`](https://github.com/reinhrst/fzf-js/releases/tag/bonus-speedup) is used in the Bonus section.

It's not impossible that at some point in the future, I will continue work on the `fzf-js` repo for a new post, so there may be more stuff in this repo.
Just use these three tags here, and you'll be fine!

If you want to build everything by hand, this is how you get started:

- Create a new directory `fzf-js`
- In this directory run `npm init`
- Now install `@types/golang-wasm-exec` and `typescript`: `npm install @types/golang-wasm-exec typescript`

## Step 1: Create an interface (the Go part)
As I discussed in [my previous post](g2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md), one needs to create an interface for a Go library to be used in JavaScript.
The interface exposes functions (and other things, like constants) to JavaScript.

As a side note: just today I ran into [this StackOverflow question/answer](https://stackoverflow.com/questions/68656435/how-to-get-all-headers-cookies-with-go-wasm) that suggests that at least in TinyGo it's possible to export Go functions to WebAssembly without the interface as described here.
I have not looked into this any further, since it doesn't seem to be a portable method (that would be usable across Go/TinyGo/GopherJS.
It would be interesting for a future post to look into this method.
{: .notice}

We'll create all the source-code in a `src` directory.
Create this, and run `go mod init github.com/reinhrst/fzf-js` (or however you want to call your project).
Next install `fzf-lib`: `go get github.com/reinhrst/fzf-lib@v1.0.0-beta1`.

We now need to create an interface (the Go-side of the interface; later we will focus on the JavaScript side): a `main` package that registers functions that we can call from JavaScript.
Let's see what [the library gives us](https://github.com/reinhrst/fzf-lib/blob/main/core.go) (only the public fields):

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

If something about the format above is unclear, make sure to read my [previous post in the series](g2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md).

For the Fzf `New()` function (which we'll export as `fzfNew`), we need to do something slightly more complex.
We want a function that returns something that feels like an Fzf object (with an `search()` and `end()` method).
JavaScript has no concept of Channels; asynchronous results are usually returned through callback functions, so that's what we'll do to.
We'll allow registering callback functions through `addResultListener()` (I don't see any reason to build a `removeResultListener()`, but this shouldn't be too hard).

<div markdown="1" class="notice">
It may seem like a bit of over-engineering to have the `Search()` method return the result asynchronously via a `Channel()`, but there is a good reason for this.
The original `fzf` is meant to be used interactively: the results update while you type.
It's fully possible that someone types `hello wor`, and that before `fzf` is done searching the next letter `l` is typed.
In this case a new search command is given, automatically cancelling the old search -- this is how `fzf`, and `fzf-lib`, work.

We probably want to have similar behaviour in our JavaScript.
It feels very tempting to make `search()` an asynchronous function that `await`s the result; this would fit better with the tests we want to run later on.
However in real life it's more likely that you just want to always update the result list when the latest search result comes in, so a callback function makes more sense in my opinion.
</div>

The way to make the `fzfNew` function return something that looks like an object instance, is by defining the returned methods as closures within the constructor.
The constructor then returns a map (which is a JavaScript object) with the "methods" present.
It should be noted that technically these things are not really like what we thing of as JavaScript instance variables, but they behave like them in all normal operations.

<div markdown="1" class="notice">
A quick note on naming used in this blog: we'll end up with 3 fzf-type constructors soon, and this may lead to confusion...: 
- `fzf.New` -- this refers to the `New` function in the `fzf-lib` package.
- `fzfNew` (without dot) -- this is the `New` function in the `fzf-js.go` file that we're introducing below. We'll export this to JavaScript as `fzfNew`.
- `Fzf` -- this is the name of the class in our TypeScript interface that we'll make in the next section. This has a `constructor()` function which we call with `new Fzf()`.

Later, when we create the TypeScript interface, we also need a name (in `declarations.d.ts`) for the return type of the `fzfNew` function. We call this `GoFzf`, as to not interfere with the `Fzf` type, which is the class mentioned as the third point above.

Sorry for all the naming confusion, where possible, I will try to be clear on what I mean.
</div>


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
    if !jsOptions.Get("extended").IsUndefined() {
        opts.Extended = jsOptions.Get("extended").Bool()
    }
    if !jsOptions.Get("fuzzy").IsUndefined() {
        opts.Fuzzy = jsOptions.Get("fuzzy").Bool()
    }
    if !jsOptions.Get("caseMode").IsUndefined() {
        opts.CaseMode = fzf.Case(jsOptions.Get("caseMode").Int())
    }
    if !jsOptions.Get("sort").IsUndefined() {
        sort := jsOptions.Get("sort")
        opts.Sort = nil
        for i := 0; i < sort.Length(); i++ {
            opts.Sort = append(opts.Sort, fzf.Criterion(sort.Index(i).Int()))
        }
    }
    if !jsOptions.Get("normalize").IsUndefined() {
        opts.Normalize = jsOptions.Get("normalize").Bool()
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

And finally we register the functions in the global scope (note that we only register the `fzfExposeConstants` and `fzfNew` functions; `addResultListener`, `search` and `end` are exposed on the return value of the `fzfNew` function):

```go
func main() {
    c := make(chan struct{}, 0)
    js.Global().Set("fzfNew", js.FuncOf(New))
    js.Global().Set("fzfExposeConstants", js.FuncOf(ExposeConstants))
    <-c
}
```

Now we have something that, if we were to compile it (see next step), gives us a nice JavaScript interface.
I will still want to wrap this into a proper interface on the JavaScript/TypeScript side, but for now, we have something that works!

## Step 2: Compile, and create a HelloWorld

In this step we will compile the code using three different methods: with Go to WebAssembly, with TinyGo to WebAssembly and with GopherJS to JavaScript.

We will compile the code into `lib/go`, `lib/tinygo` and `lib/gopherjs` respectively.

After compilation, we will run the result in node, using the following small program (you see a bit of fiddling to make sue that the next search only starts after the previous one finishes):
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
Since Go has a lot of standard library that gets added, the size of even a simple Hello World program (as we saw in the [previous post](g2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md)) is between 1 and 2 MB large.
It is possible to compress the result (using [Brotli](https://en.wikipedia.org/wiki/Brotli); a compression algorithm that performs better than GZIP and is supported by all major browsers; also see [here; at the bottom the section about Reducing Size](https://zchee.github.io/golang-wiki/WebAssembly/)).
For each compilation method, I will report the file size, both uncompressed and compressed.

### Compile with Go to WebAssembly
Compiling Go to WebAssembly is easy using the built-in Go compiler. I use version 1.16.

In the `src` directory, run:
```bash
mkdir -p ../lib/go/
GOOS=js GOARCH=wasm go build -o ../lib/go/main.wasm
```

Now we have a WebAssembly (`.wasm`) file in the target directory.
This WebAssembly file needs a Go-specific JavaScript file for support, we will copy this from the Go directory to the target dir:

```bash
cp $(go env GOROOT)/misc/wasm/wasm_exec.js ../lib/go/wasm_exec.js
```

Now we're ready to create a file that:
1. Loads the `wasm_exec.js`
2. Creates a new `Go()` object
3. Load the WebAssembly into Node, then instantiate it and import into the Go object
4. Run the "hello world" code we described above

Create a file `main.mjs` in `lib/go` (the `.mjs` extension tells node that this file is a [JavaScript module](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules), meaning that `import ...` and top-level `await`s are supported):

```javascript
import {promises} from "fs"
import "./wasm_exec.js"

const go = new Go();
const wasmcode = await promises.readFile("main.wasm")
const webass = await WebAssembly.instantiate(wasmcode, go.importObject)
go.run(webass.instance)

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
```

And run `node main.mjs` should result in

```
Searching for 'a ny' resulted in a bright new day
Searching for 'oo' resulted in goodbye nothingness,hello world
Searching for ''oo' resulted in goodbye nothingness
Searching for '!oo' resulted in hello world,a bright new day
```

Success! If you want, you can try other hay and needles; it's proper `fzf-lib` running here!

<figure markdown="1">

|  |WebAssembly code|JavaScript code|Total
--|---|---|---
uncompressed|2'501'415|18'147|2'519'562
compressed|531'134|4'205|535'339

<figcaption>File sizes for WebAssembly and the supporting JavaScript (excluding `main.mjs`).</figcaption>
</figure>

As can be seen, this solution does lead to a minimal transfer-size of 500kB for the library.

### Compile with TinyGo to WebAssembly
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

It seems that TinyGo wants its Go modules in different spots than Go. Unfortunately my experience with Go and TinyGo is not big enough to comment on what exactly is going on; worst case you may need to copy around the `fzf-lib` code a bit.
{: .notice}

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

As you can see, the result is almost the same; it just has a bunch of `syscall/js.finalizeRef not implemented` messages; these are warnings are [a known issue](https://github.com/tinygo-org/tinygo/issues/1140), and for now we ignore them (they look terrible here; in the browser they will go to the JavaScript console, and nobody but developers will see them. On node, we can get rid of them by redirecting `stderr` to `/dev/null`, but this also suppresses other errors (and some other output in some programs). So to run `main.mjs` and filter out only these errors: `node main.mjs 2> >(grep -v 'syscall/js.finalizeRef not implemented')`, which redirects `stderr` (file descriptor `2`) to an anonymous pipe that greps for everything *except* this error).

<figure markdown="1">

|  |WebAssembly code|JavaScript code|Total
--|---|---|---
uncompressed|682'781|15'670|698'451
compressed|212'423|3'768|216'191

<figcaption>File sizes for WebAssembly and the supporting JavaScript (excluding `main.mjs`).</figcaption>
</figure>

As you can see, TinyGo code is uncompressed about 4 times smaller than Go WebAssembly code, and compressed about 40% of the size.

### Compile with GopherJS to JavaScript
GopherJS differs from the other two methods, in that it compiles the Go code directly to JavaScript.
It's been doing this since 2013, longer than the WebAssembly outputs of the other two.
As mentioned on its [GitHub page](https://github.com/gopherjs/gopherjs), *[i]ts main purpose is to give you the opportunity to write front-end code in Go which will still run in all browsers.*
So even though exposing Go libraries to JavaScript is not its main purpose, it does so just fine, as I will show here.

We assume in this post that you have the GopherJS executable at `~/go/bin/gopherjs`; if not, make sure to update the commands below.
Unlike when we compile to WebAssembly, we don't need any supporting JavaScript files; once we compile, we're done.
Run the commands below once again from the `src` directory.

```bash
mkdir -p ../lib/gopherjs/
~/go/bin/gopherjs build . -o ../lib/gopherjs/fzf-js.js
```

Note that this not only makes `fzf-js.js`, but also an `fzf-js.js.map` file, which should help you debugging the compiled Go code (see [this StackOverflow question](https://stackoverflow.com/questions/21719562/how-to-use-javascript-source-maps-map-files) on how `.map` files are used). The map file is for debugging *only*, you can safely remove it in production, and therefore doesn't count towards the code size we report here.

Because we don't have to worry about loading and starting WebAssembly, we can make our `main.mjs` file a bit simpler as well:

```javascript
import "./fzf-js.js"

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
```

Done! Running `node main.mjs` gives exactly the same results it should!

<figure markdown="1">

|  |WebAssembly code|JavaScript code|Total
--|---|---|---
uncompressed||1'687'108|1'687'108|
compressed||180'831|180'831|
minified (javascript-minifier.com)||904'499|904'499
minified (javascript-minifier.com) & compressed||159'598|159'598
minified (gopherjs built in)||1'095'605| 1'095'605
minified (gopherjs built in) & compressed||148'069 | 148'069

<figcaption>File sizes for JavaScript (excluding `main.mjs`). Note that GopherJS does not produce any WebAssembly code.</figcaption>
</figure>


The resulting JavaScript is 1.7 MB, which is between Go and TinyGo in, however it's very compressible, and when compressed it's only 181 kB.
This is 35% of Go's WebAssembly size, and also 15% smaller than TinyGo's WebAssembly.

Because the result is JavaScript rather than WebAssembly, we can make the size even smaller by first minifying the JavaScript. I used [the first DuckDuckGo result for "javascript minifier"](https://javascript-minifier.com); the result is even smaller, 160 kB when compressed!

Update: after writing this, I became aware that GopherJS actually contains a built-in minifier. If you compile with `-m` you get minified code.
This code is 1.1 MB bytes uncompressed (so larger than the minified code generated by the DuckDuckGo's result), but it compresses down to less than 150 kB, the absolute winner.
{: .notice--info}

## JavaScript (TypeScript) interface
As mentioned in [the previous post in this series](g2021-08-05-interface-between-go-1.16-and-javascript-syscall-js.md), I like to create a TypeScript/JavaScript interface for a Go library.
The advantages of this is that I can guarantee a consistent interface, even if changes in Go mean that the current interface is not possible anymore, or if there is a better (faster) interface.
In addition, because the interface then uses proper JavaScript objects, functions and methods, we expose items that a JavaScript developer is familiar with.
Finally, we expose methods with a signature that means something, not just `(this js.Value, args []js.Value) interface{}`.

Since I like to write my code in TypeScript rather than JavaScript, we have to start by setting some configuration for TypeScript: easiest is just to download [the `tsconfig.json` from the accompanying repo](https://github.com/reinhrst/fzf-js/blob/first-version/tsconfig.json) and save it to the directory root.

Before we can start to write anything in TypeScript, we need to make sure that TypeScript knows about the functions that we export in WebAssembly / GopherJS JavaScript (note that TypeScript already knows about the stuff in `wasm_exec.js`, because we npm-installed `@types/golang-wasm-exec` before).

We do this by adding a `declarations.d.ts` file to the `src` directory.

```typescript
declare function fzfExposeConstants(): FzfConstants
declare function fzfNew(hayStack: string[],
                        options: Partial<FzfOptions>): GoFzf

declare type Case = { readonly __tag: unique symbol }
declare type SortCriterion = { readonly __tag: unique symbol }

declare type FzfConstants = {
  CaseSmart: Case
  CaseIgnore: Case
  CaseRespect: Case
  ByScore: SortCriterion
  ByBegin: SortCriterion
  ByEnd: SortCriterion
  ByLength: SortCriterion
}

declare type FzfOptions = {
  Extended: boolean
  Fuzzy: boolean
  CaseMode: Case
  Normalize: boolean
  Sort: SortCriterion[]
}

declare type GoFzf = {
  addResultListener: (listener: (result: SearchResult) => void) => void,
  search: (string: string) => void,
  end: () => void,
}

declare type SearchResult = {
  needle: string
  matches: MatchResult[]
}

declare type MatchResult = {
  key: string
  hayIndex: number
  score: number
  positions: number[]
}
```

First we declare the two functions that we exposed in the `main()` function in Go.
These (obviously) have parameter and return types that need to be `declare`d in turn, and so we fill the file.
For the `Case` and `SortCriterion` constants, I create [a unique type](https://kubyshkin.name/posts/newtype-in-typescript/), so that I cannot accidentally use the wrong one.

The interface itself ([the `index.ts` file](https://github.com/reinhrst/fzf-js/blob/first-version/src/index.ts)) starts with a block loading the compiled JavaScript (`fzf-js.js`), or the WebAssembly helper (`wasm_exec.js`) and the WebAssembly (`main.wasm`) -- normally you could save yourself some code here since you either have WebAssembly *or* a GopherJS JavaScript file.

Since we want the code to run both on Node and on the browser, we need some extra code.
Because this file is a JavaScript module, we're allowed to put `await`s in there.
The `// @tsignore` lines are necessary because the modules that we're importing don't exist in the source directory, so TypeScript will complain about that.
```typescript
try {
  // @ts-ignore -- it will complain it cannot find this module at compile time
  await import("./fzf-js.js")
} catch (e) {
  console.log("No fzf-js.js file, assuming WebAssembly module")
  // @ts-ignore -- it will complain it cannot find this module at compile time
  await import("./wasm_exec.js")
  let fetchAsArrayBuffer: (filename: string) => Promise<ArrayBuffer>
  if (globalThis.fetch === undefined) {
    // node
  // @ts-ignore -- it will complain it cannot find this module at compile time
    var fs = await import('fs');
    fetchAsArrayBuffer = fs.promises.readFile
  } else {
    // browser
    fetchAsArrayBuffer = async (url: string) => await (await fetch(url)).arrayBuffer()
  }
  const go = new Go();
  const result = await WebAssembly.instantiate(
    await fetchAsArrayBuffer("main.wasm"), go.importObject)
  go.run(result.instance)
}
```

The second part of the file is just a wrapper around the Go methods (with some error checking to give a nice error message if the object is used after `end()` is called), and an `export {}` of the `Fzf()` class:
```typescript
class Fzf {
  static optionConstants = fzfExposeConstants()
  _fzf: GoFzf | undefined

  constructor(hayStack: string[], options?: Partial<FzfOptions>) {
    this._fzf = fzfNew(
      hayStack,
      options || {}
    )
  }

  addResultListener(listener: (result: SearchResult) => void): void {
    if (this._fzf == undefined) {
      throw new Error("Fzf object already ended")
    }
    this._fzf.addResultListener(listener)
  }

  search(needle: string): void {
    if (this._fzf == undefined) {
      throw new Error("Fzf object already ended")
    }
    this._fzf.search(needle)
  }

  end() {
    if (this._fzf == undefined) {
      throw new Error("Fzf object already ended")
    }
    this._fzf.end()
    this._fzf = undefined
  }
}


export {Fzf}
```

In order to build all this, it's probably best to add some build-commands to `package.json`:

```json
  "scripts": {
    "build-go": "TARGETDIR=lib/go; mkdir -p ${TARGETDIR} && (cd src && GOOS=js GOARCH=wasm go build -o ../${TARGETDIR}/main.wasm) && tsc --outDir ${TARGETDIR}/ && cp ${TARGETDIR}/index.js ${TARGETDIR}/index.mjs && cp $(go env GOROOT)/misc/wasm/wasm_exec.js ${TARGETDIR}/",
    "build-tinygo": "export TARGETDIR=lib/tinygo; mkdir -p ${TARGETDIR} && (cd src && tinygo build -target=wasm -opt 2 -o ../${TARGETDIR}/main.wasm) && tsc --outDir ${TARGETDIR}/ && cp ${TARGETDIR}/index.js ${TARGETDIR}/index.mjs && cp $(tinygo env TINYGOROOT)/targets/wasm_exec.js ${TARGETDIR}/",
    "build-gopherjs": "export TARGETDIR=lib/gopherjs; mkdir -p ${TARGETDIR} && (cd src && ~/go/bin/gopherjs build . -o ../${TARGETDIR}/fzf-js.js) && tsc --outDir ${TARGETDIR}/ && cp ${TARGETDIR}/index.js ${TARGETDIR}/index.mjs",
    "build-all": "npm run build-go && npm run build-tinygo && npm run build-gopherjs"
  }
```

Now you just type `npm run build-all` to build.

<div markdown="1" class="notice">
One small thing you may see in the build commands, is that we copy the `index.js` file, which contains our interface, to `index.mjs`.
An `.mjs` file is interpreted by Node as a JavaScript module, meaning that things like `import {...} from ...`, `export {...}` and (in our case very importantly) top level `await ...` statements are possible.
There is a [long running TypeScript issue](https://github.com/Microsoft/TypeScript/issues/18442) (which occasionally turns into a flame war about whether Node is JavaScript, etc....) whether TypeScript should be able to emit `.mjs` files directly. Four years into the ticket, there seems to be no agreement....

In our case, the easiest thing is just to copy the `index.js` file to `index.mjs` -- we leave the `index.js` file so that we serve that in the browser later on (in the next article).
</div>

Let's see if it works!

Create the following `main.mjs` (which is basically the same as before, without the loading of WebAssembly, and with `new Fzf()`, our JavaScript interface, rather than `fzfNew()`. Ow, and just for fun, I used one of the options to sort the result by length of the match:
```javascript
import {Fzf} from "./index.mjs"

const myFzf = new Fzf(["hello world", "goodbye nothingness", "a bright new day"], {
  sort: [Fzf.optionConstants.ByLength]
});
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
```

Unsurprisingly, it does the same thing as before, with the small difference thanks to sorting `ByLength`.

```
> node main.mjs
Searching for 'a ny' resulted in a bright new day
Searching for 'oo' resulted in hello world,goodbye nothingness
Searching for ''oo' resulted in goodbye nothingness
Searching for '!oo' resulted in hello world,a bright new day
```

## Performance
As promised, we will do a small performance test on the code.
I intend to write another blog later where we go into performance in detail.
There are many different variables that would be interesting to consider; for instance different browsers, different optimisation and garbage collection settings, whether we allow the code to "warm up". Way too much to go into detail now; today we do a simple test.

The code for this section is in the same repository, but has the [`performance-testing` tag](https://github.com/reinhrst/fzf-js/releases/tag/performance-testing).

To test performance, we need a lot of lines of text to search in; here is a small program that creates lots of lines of text (let's save it under `testdata/generator.go`):
```go
package main

import (
    "os"
    "fmt"
    "flag"
    "math/rand"
    "strings"
)

var fruits = []string{`Abiu`, `Açaí`, `Acerola`, `Ackee`, `African cucumber`, `Apple`, `Apricot`, `Avocado`, `Banana`, `Bilberry`, `Blackberry`, `Blackcurrant`, `Black sapote`, `Blueberry`, `Boysenberry`, `Breadfruit`, `Buddha's hand (fingered citron)`, `Cactus pear`, `Canistel`, `Cempedak`, `Cherimoya (Custard Apple)`, `Cherry`, `Chico fruit`, `Cloudberry`, `Coco De Mer`, `Coconut`, `Crab apple`, `Cranberry`, `Currant`, `Damson`, `Date`, `Dragonfruit (or Pitaya)`, `Durian`, `Egg Fruit`, `Elderberry`, `Feijoa`, `Fig`, `Finger Lime (or Caviar Lime)`, `Goji berry`, `Gooseberry`, `Grape`, `Raisin`, `Grapefruit`, `Grewia asiatica (phalsa or falsa)`, `Guava`, `Hala Fruit`, `Honeyberry`, `Huckleberry`, `Jabuticaba`, `Jackfruit`, `Jambul`, `Japanese plum`, `Jostaberry`, `Jujube`, `Juniper berry`, `Kaffir Lime`, `Kiwano (horned melon)`, `Kiwifruit`, `Kumquat`, `Lemon`, `Lime`, `Loganberry`, `Longan`, `Loquat`, `Lulo`, `Lychee`, `Magellan Barberry`, `Mamey Apple`, `Mamey Sapote`, `Mango`, `Mangosteen`, `Marionberry`, `Melon`, `Cantaloupe`, `Galia melon`, `Honeydew`, `Mouse melon`, `Musk melon`, `Watermelon`, `Miracle fruit`, `Monstera deliciosa`, `Mulberry`, `Nance`, `Nectarine`, `Orange`, `Blood orange`, `Clementine`, `Mandarine`, `Tangerine`, `Papaya`, `Passionfruit`, `Peach`, `Pear`, `Persimmon`, `Plantain`, `Plum`, `Prune (dried plum)`, `Pineapple`, `Pineberry`, `Plumcot (or Pluot)`, `Pomegranate`, `Pomelo`, `Purple mangosteen`, `Quince`, `Raspberry`, `Salmonberry`, `Rambutan (or Mamin Chino)`, `Redcurrant`, `Rose apple`, `Salal berry`, `Salak`, `Satsuma`, `Shine Muscat or Vitis Vinifera`, `Sloe or Hawthorn Berry`, `Soursop`, `Star apple`, `Star fruit`, `Strawberry`, `Surinam cherry`, `Tamarillo`, `Tamarind`, `Tangelo`, `Tayberry`, `Tomato`, `Ugli fruit`, `White currant`, `White sapote`, `Yuzu`}

func main() {
    randomizer := rand.New(rand.NewSource(12345))
    var nrlines int
    flag.IntVar(&nrlines, "n", 1 << 20, "Number of lines to produce")
    flag.Parse()
    fmt.Fprintf(os.Stderr, "Now creating %d lines of fruit\n", nrlines)

    for i := 0; i < nrlines; i++ {
        nrwords := 3 + randomizer.Intn(10)
        var words []string
        for j := 0; j < nrwords; j++ {
            words = append(words, fruits[randomizer.Intn(len(fruits))])
        }
        fmt.Fprintln(os.Stdout, strings.Join(words, " "))
    }
}
```

If we run it without any parameters, it generates <katex-inline>2^{20}</katex-inline> = 1'048'576 lines.
Since we seed the `randomizer`, there is a guarantee that every time we generate the same list, ideal for testing.

For our performance test, I run this code and save the output: `go run main.go > /tmp/lines.txt`.

To avoid things getting too complex now, I run the performance tests in node (rather than going to the browser); we will load the 1M lines of text, and do a fuzzy-search for "hello world".
In both the JavaScript and the Go code I will put some timers, and at the end we can read them out.
Since the search will take (much) more than a couple of milliseconds, I'm not worried that the timers will influence execution time too much.

All tests are done on my M1 MacBook Pro (late 2020); all code is arm64.

Let's first get some base-line data, by just running `fzf --filter`:
```bash
cat /tmp/lines.txt | time fzf --filter "hello world" | wc -l
```

This command finishes in 460ms (using 309% CPU), reporting 74779 matching lines -- your timings may vary, the number of matching lines should be the same.
As can be seen from the 309% CPU, `fzf` makes proper use of the multiple cores of the M1 CPU.

WebAssembly and JavaScript can not take advantage of multiple cores (technically it's more complex than this; I intend to write a post about multi-threaded JavaScript later; however, the code that we generated in this post does not take advantage of multiple cores (there is an [old issue](https://github.com/golang/go/issues/28631) to make Go WebAssembly multi-threaded; it's still open).

When I run the `fzf --filter` command in a Docker container that has been limited to a single core, it runs in 1390ms (which is almost exactly 3.09 x 460ms :)).
This gives us a "native Go" baseline -- I don't expect the Node code to come anywhere close to that, but it will be interesting to see how it compares.

In order to log times in JavaScript, we add some code to our `main.mjs`:
```javascript
let startTime = Date.now()
function logTime(message) {
  const now = Date.now()
  console.log(message, now, now - startTime)
}
```
This prints lines with a message, the absolute time, and time since start.
In order to get the same in Go, we expose a function to receive the startTime (so that Go and JavaScript have the same start time) and then print the same values.
I ran into a small issue here, that `args[0].Int()` in TinyGo seems to be limited to 32 bits (and the JavaScript timestamp in milliseconds is much larger than a 32 bit int), so we send the time as a string, and then parse to an `int64`.

```go
var startTime int64
func SetStartTime(this js.Value, args []js.Value) interface{} {
    startTime, _ = strconv.ParseInt(args[0].String(), 10, 64)
    return nil
}

func logTime(message string) {
    t := int64(time.Now().UnixNano() / 1e6)
    println(message, strconv.FormatInt(t, 10), strconv.FormatInt(t - startTime, 10))
}
```

See the exact code changes [on GitHub](https://github.com/reinhrst/fzf-js/compare/first-version...performance-testing).

Now we're ready to run the following `main.mjs`:
```javascript
let startTime = Date.now()
function logTime(message) {
  const now = Date.now()
  console.log(message, now, now - startTime)
}
logTime("start")

import {Fzf} from "./index.mjs"
logTime("js/wasm loaded")
import {promises} from "fs"
const lines = (await promises.readFile("/tmp/lines.txt", "utf-8")).split("\n")
logTime("lines.txt loaded")

SetStartTime("" + startTime)
logTime("startTimeSet")

const myFzf = new Fzf(lines)
logTime("Fzf initialized")
myFzf.addResultListener((result) => {
  logTime("Search done")
  console.log("Searching for '" + result.needle + "' resulted in " + result.matches.length + " results.")
})
myFzf.search("hello world")
```

A typical run will give us the following output (Note that for TinyGo you have to run `node main.mjs 2> >(grep -v 'syscall/js.finalizeRef not implemented')`):
```
start 1628507038082 0
js/wasm loaded 1628507038084 2
lines.txt loaded 1628507038302 220
startTimeSet 1628507038302 220
newStart 1628507038302 220
newFinishedParse 1628507039862 1780
newDone 1628507040813 2731
Fzf initialized 1628507040814 2732
Result ready to send 1628507053034 14952
Search done 1628507053470 15388
Searching for 'hello world' resulted in 74779 results.
Result sent 1628507053470 15388
```

I ran this for Go, TinyGo and GopherJS, 20 times in a row and took the mean (there are no large outliers, so mean is representative).
Let's first see what timings we get from our JavaScript code (all numbers are in milliseconds):

| | Go | TinyGo | GopherJS |
--|---|---|---
Load JS/WebAssembly | 2 | 2 | 2
Load `/tmp/lines.txt` | 225 | 222 | 218
`new Fzf()` | 9'438 | 11'677 | 2'543
`search()` until callback | 6'144 | 2'772 | 12'547
Total | 15'809 | 14'673 | 15'310

{%include figure
    image_path="/assets/images/2021/08/10/results-from-javascript.svg"
    alt="results chart"
    caption="It's clear to see that each method uses time in different parts of the code."
%}

So interestingly, all three methods need about 15 seconds from cold start to a result (this is about 10 times as much as native Go on a single core).
There is however a huge difference in *where* they spend their time.
TinyGo has a very long startup time, after which the search is relatively fast, whereas GopherJS is the opposite story. Go is in between the two.

Since we also have some timing data in the Go code, we can split this out a bit further (all numbers in milliseconds):

| | Go | TinyGo | GopherJS |
--|---|---|---
Load JS/WebAssembly | 2 | 2 | 2
Load `/tmp/lines.txt` | 225 | 222 | 218
From JS `new Fzf()` until ready to call `fzf-lib`'s `fzf.New()` | 7'825 | 8'548 | 1'579
Calling `fzf-lib`'s `fzf.New()` | 1'255 | 3'121 | 963
return from `fzfNew()` function | 358 | 7 | 0
`search()` until library has result | 4'235 | 1'394 | 12'132
Returning search result to JS callback | 1'908 | 1'378 | 416


{%include figure
    image_path="/assets/images/2021/08/10/results-js-and-go.svg"
    alt="results chart"
%}

In this second figure, it's clear to see that for Go and TinyGo, a large amount of time is spent in moving data from JavaScript to Go (the green block) and from Go back to JavaScript (the pink block).
In the Bonus section we will see if we can do something to improve this.

## Conclusion
It's quite possible these days to take a Go library and compile it so that it will run on the browser.
The resulting code will be quite large, although with compression it can be slimmed down to between 150-600 kB, depending on your method.
There is a standard way to build an interface in Go, that works for Go, TinyGo and GopherJS.

I'm hesitant to jump to conclusions about performance; there is a reason that I feel that performance deserves a whole post on its own.
What we saw in this example, is that without any manual optimisation, we seem to be getting performances that are 10 times slower than native Go on a single CPU core.
I actually am very impressed by this, considering that the `fzf` code has been optimised to run as fast as possible (when compiled to native code).
For now there is no clear winner between the methods--all three perform similar in this very simple test case.

It should also be noted that for instance GopherJS has some [tips and tricks to improve performance](https://github.com/gopherjs/gopherjs#performance-tips); these were not applied in this test; again I refer to a future post for this.
Also, the interface that we're using, `syscall.js`, is in EXPERIMENTAL state, and may still get considerable (speed) updates.

## Bonus: see if we can get a speedup
If you're still here, you deserve a treat: see if we can speed things up a bit using some small tricks.

Looking at the performance graphs, it seems that the Go and TinyGo methods are spending a very long time in unpacking and packing JavaScript variables.
This makes sense, if you consider that `hayStack = append(hayStack, jsHayStack.Index(i).String())` is called over 1 million times, once for each line in the `hayStack`.
It would be interesting to see if we can come up with a quick speedup for this.

An obvious and easy thing to do is to send everything as one JSON string, and get the result back as a single JSON string.
Thanks to our JavaScript/TypeScript interface, we can do this without any change to our outside interface (this is exactly a major reason why I like having a TypeScript interface!).
We just make some small changes; in `declarations.d.ts`, specify that the `fzfNew()` and callback functions have string parameters, in `index.ts` put some `JSON.stringify` and `JSON.parse` calls, and put JSON code in `fzf.js.go` (see the [`bonus-speedup` tag on GitHub](https://github.com/reinhrst/fzf-js/releases/tag/bonus-speedup), or [only the diff](https://github.com/reinhrst/fzf-js/compare/performance-testing...bonus-speedup)).

As soon as we try to run this, we run into a problem: [TinyGo does not support json serialization](https://github.com/tinygo-org/tinygo/issues/447).
This results in a `panic: unimplemented` error when trying to run it.

For Go and GopherJS, the result is unexpected (again, all timings in ms; between brackets the timings before this change):

| | Go | TinyGo | GopherJS
--|---|---|---
Load JS/WebAssembly | 2 (2) | - | 2 (2)
Load `/tmp/lines.txt` | 209 (225) | - | 202 (218)
From JS `new Fzf()` until ready to call `fzf-lib`'s `fzf.New()`| 2'592 (7'825) | - | 15'069 (1'579)
Calling `fzf-lib`'s `fzf.New()` | 621 (1'255) | - | 899 (963)
return from `fzfNew()` function | 18 (358) | - | 1 (0)
`search()` until library has result | 4'069 (4'235) | - | 11'805 (12'132)
Returning search result to JS callback | 1'173 (1'908) | - | 6'400 (416)
Total | 8'685 (15'809) | - | 34'371 (15'310)


{%include figure
    image_path="/assets/images/2021/08/10/results-js-and-go-speedup.svg"
    alt="results chart"
    caption="Go WebAssembly performs much better with the JSON patch, but GopherJS is much worse."
%}

I did expect Go WebAssembly to perform a lot better, and I'm happy to see that it did.
We managed with a small change to almost half the end-to-end execution time.
It's not impossible to imagine that we might be able to optimise this even further; JSON is not the most efficient encoding, and possibly there are more efficient ways to send data across the boundary between JavaScript and Go.

Interestingly, this method also sees speedups in other steps that we didn't change.
Calling `fzf.New()` is twice as fast, and returning from the `fzfNew()` function went from 358ms to 18ms.
I expect that this is due to there being less need to do cleanup, memory recovery.

The unexpected result is how much worse GopherJS does; it takes more than twice as long this way.
My gut feeling is that, since the compiled code is JavaScript, it used to be able to just take the JavaScript strings and reuse them as Go strings.
Now however we encode everything in JSON, so there now need to be three copies of each string: one in JavaScript, one in the JSON string and one as the decoded string in the Go code.
All this however is speculation; I did use node's `process.memoryUsage().heapUsed` to see how much memory each of the methods used, but I do feel more research would be needed to draw any conclusions (for reference: the haystack in `lines.txt` is 83 MB).

Value for `process.memoryUsage().heapUsed` at the end of the script, in MB:

| | Go | TinyGo | GopherJS
--|--|--|--
Before "speedup" | 195 MB | 506 MB | 910 MB
After "speedup" | 235 MB | - | 1'170 MB

<div markdown="1" class="notice">
I would *love* to dive deeper into this, see how much more performance we can get from this code.
Speeding up code is a bit of a hobby, and there is a serious challenge here.
I will probably have to leave that to a future post, if I ever want to get this post "to press"....

Some ideas that I have:
- Send the hayStack as one big string delimited by `0x00` (or `\n`); this should be faster than JSON and compatible with TinyGo
- Send the hayStack as a ByteArray which is moved to Go by [`CopyBytesToGo`](https://pkg.go.dev/syscall/js#CopyBytesToGo) and a list of start/end indices
- Converting []byte into string in Go makes a copy of the underlying memory, however there are some "hacky/unsafe" workarounds to do this without a copy (see [this issue](https://github.com/golang/go/issues/25484) for more info); that should be able to save a lot.
- For the result, first thing one can wonder is if it makes sense to return the `key` (the hay straw that got matched) in the result; the index of the hay straw is already returned and one can assume that JavaScript still has the hay array lying around somewhere.
- It's very unlikely anyone will find it useful to get all 74779 results returned. If we're showing a real time search box, we're probably interested in how many results fit on our screen; and after we scroll, we want to know about one more screen, etc. So we could return the results only when they're needed, although this would require a bit more effort.
- See if we can speed up GopherJS's actual search performance; it's quite slow, the actual search takes 12 seconds for GopherJS, whereas Go WebAssembly does it in 4 seconds (and TinyGo even faster).
</div>
