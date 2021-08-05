---
title: 'Interface between Go 1.16 (compiled to WebAssembly) and JavaScript (syscall/js)'
description: A howto (with lots of examples) for making Go code available in the browser and how to have it interface with JavaScript.
categories:
    - tech
    - howto
tags:
    - fzf
    - go
    - wasm
    - javascript
toc: true
---
Last month I [posted a story](../_posts/2021-07-08-making-fzf-into-a-golang-library-fzf-lib.md) about creating a stand-alone library from [Junegunn Choi's fzf](https://github.com/junegunn/fzf).
This was the first step in an effort to produce a version of fzf that runs in the browser.
A second step would be to compile [fzf-lib](https://github.com/reinhrst/fzf-lib) to run in the browser.
Doing exactly that will be the content of a next post (after which there will be a couple more, looking at performance, looking at whether it's the smart thing to do, packaging the whole thing into an npm package).
In today's post I will focus on how to make an interface between Go and JavaScript code.
There is some documentation out there, but it's few are far between (and some outdated); hopefully the explanations and examples here will help others (among which future me).

This describes the situation for the current (August 2021) version of Go (1.16).
It looks from the documentation that Go 1.17 will be the same, but no guarantees.

This document focusses on how to build the *interface*, the connection between JavaScript and Go.
There are multiple ways to get your Go code to run in the browser; you can compile to WebAssembly using Go or [TinyGo](https://tinygo.org), or use [GopherJs](https://github.com/gopherjs/gopherjs) to compile Go to JavaScript -- I will dive deeper into these options in a later post.
Luckily, the interface described below is supported by all three methods.

Because examples work best when you can actually do them yourself, I will quickly describe how to compile from Go to WebAssembly, and integrate this in a javascript program; in a later post I will dive into this in more detail, and show multiple methods of doing this.
This post comes with a [GitHub repository with examples](https://github.com/reinhrst/go-js-interface) containing all the code that is described in this post.

[Accompanying code on <i class="fab fa-fw fa-github" aria-hidden="true"></i> Github](https://github.com/reinhrst/go-js-interface){: .btn .btn--success}


<div markdown="1" class="notice">
In this article I will consistently talk about Go code and JavaScript code as the two parts that we care about.
Technically, no Go code is called from JavaScript; it's actually WebAssembly code being called from JavaScript (or, if we use a Go --> JavaScript compiler, it would even be JavaScript code being called from JavaScript).
I do think however that it's clear what I mean.

Things get even a little more complex towards the end of this example.
Rather than write JavaScript, we will write that part of the code in TypeScript.
TypeScript gets compiled into JavaScript, however there is a huge difference between a Go --> JavaScript compiler and a TypeScript --> JavaScript compiler.
TypeScript is very close to JavaScript; it uses the same standard library, the same variable types, the same object structure.
Therefore we consider TypeScript to be similar to JavaScript (we just need to take some extra care to expose some type declarations).
</div>

# How to compile and run
Ideally this post would only talk about the interface, however it's unrewarding to not be able to play with things yourself.
If you just want to quickly get started, I would advice cloning [the accompanying GitHub repo](https://github.com/reinhrst/go-js-interface), and [skip right to the next section](#interface).
If you want to start from scratch, keep reading.
Be aware that I will write a whole post on this topic; in here I will just scratch the surface to get you up and running.

In this post, we will use the standard Go 1.16 compiler to compile our Go code to WebAssembly (`.wasm` file).
There are other methods to do this which I will describe in aforementioned follow-up post.

A WebAssembly (`.wasm`) file cannot be run by itself; you need to write a JavaScript file to load and start the WebAssembly.
In addition, the Go code needs a Go-provided JavaScript file (called `wasm_exec.js`) to be loaded.

If we want to see all this in the browser (as opposed to running in node), we also need an HTML file.

## Walkthrough: Compiling Go "Hello World" into WebAssembly and running it

All commands below were tested in MacOs.
They should work in Linux.
On Windows, you probably need to make some small adjustments.
{: .notice}

Create a new directory; in the new directory init a new Go module:

```bash
> go mod init hello
```

Let's create a small program (`hello.go`)
```go
package main

func main() {
    println("Hello, world!");
}
```

Compiling the Go program is the easy step
```bash
> GOOS=js GOARCH=wasm go build -o main.wasm
```
Note that even for a trivial Go program, this file will be between 1 and 2MB -- this is normal, and something we will discuss in aforementioned follow-up post.

Getting the `wasm_exec.js` file is also easy (make sure you get the one that corresponds to the go version you used to compile):
```bash
> cp "$(go env GOROOT)/misc/wasm/wasm_exec.js" .
```

Finally we create a module file (`main.mjs`; a javascript file with the extension `.mjs` tells node that this file is a module, and we can do things like `import ...`)
```javascript
import {promises} from "fs"
import "./wasm_exec.js"

const go = new Go();
promises.readFile("main.wasm")
  .then(wasmcode => WebAssembly.instantiate(wasmcode, go.importObject))
  .then((result) => go.run(result.instance))
```

In this file, we import the `wasm_exec.js` file create a new `Go()` object, read the WebAssembly code, and import it into the `Go` object. Finally we call `go.run()` on the WebAssembly.

Your directory should now contain 4 files:
```
go.mod
hello.go
main.mjs
main.wasm
wasm_exec.js
```

Now run the whole thing in node (I use v16.4.2):
```bash
> node main.mjs
Hello, world!
```

Congratulations, you have run your first Go WebAssembly.

If you want to run this in the browser, you will need a simple HTML page, and use `fetch()` rather than `readFile()`.
I've only managed to run this in the browser using a local webserver; `fetch()` doesn't work from the file system.
See [the accompanying GitHub repo](https://github.com/reinhrst/go-js-interface) for an example.

Note that in a browser, the output will appear in the JavaScript console, not on the page itself!

# Interface
Go and JavaScript are different types of languages; an important difference in this case is that Go is statically typed, whereas JavaScript is dynamically typed.
This means that "stuff" has to happen on the boundary (and we cannot just call an exposed Go function from JavaScript).

## A simple example
The workhorse of the boundary is the [`syscall/js`](https://pkg.go.dev/syscall/js) module, part of the Go standard library.

The `syscall/js` package (in Go 1.16) is labelled EXPERIMENTAL, with the additional text *[this package] is exempt from the Go compatibility promise*.
In good English: use at your own risk and we will not guarantee that it keeps working when we upgrade Go to a new version.
It might be good to keep this in mind when writing production code that is meant to survive a long time.
{: .notice}

Let's create a small example to see how this package works:
```go
package main

import (
    "syscall/js"
)

func AddInts(this js.Value, args []js.Value) interface{} {
    a := args[0].Int()
    b := args[1].Int()

    return a + b
}

func main() {
    js.Global().Set("mylibAddInts", js.FuncOf(AddInts))
    c := make(chan struct{}, 0)
    <-c
}
```

Let's walk though what's going on here:

So we define a funcion `AddInts` that we want to expose to JavaScript.
Any function that we want to expose, needs this *exact* signature: `func FuncName(this js.Value, args []js.Value) interface{}`, nothing else is allowed.
Even if you have a function that you don't want to return anything, you should still give it `interface{}` as return type, and return `nil` (or anything else you would like).

The two parameters are the value of `this` (as in javascript `this`), and a slice (list) of arguments.

In order to make Go usable values of `js.Value`s, we need to call a method on them to convert them to a specific type.
`args[0].Int()` tells the system to convert the value to an `int`; this method will panic if the value is not an `int`.
Likewise, there is a `jsValue.String()` method, a `jsValue.Bool()`, `jsValue.Float()`.

More complex types, such as Objects or Arrays are supported, but you need a call for each item; see below for an example.

The `AddInts` function returns an `int` (`return a + b`).
Since Go type `int` is an `interface{}`, this is allowed.
As we will see later, Go will automatically call `js.ValueOf()` on this returnvalue to make it a JavaScript value.

Next we need to register the function so that it can be called from JavaScript.
The `js.FuncOf` creates a JavaScript function from the Go function.
Via `js.Global().Set()`, we set this function somewhere in the global scope.
It should be noted that nothing special is going on here, we can also set the function on some object:

```go
js.Global().Set("mylib", js.ValueOf(map[string]interface{} {
    "AddInts": js.FuncOf(AddInts),
}))
```
or if the global `mylib` object already exists, we can set to it
```go
js.Global().Get("mylib").Set("AddInts", js.FuncOf(AddInts))
```

Finally, we need 2 lines of "magic".
```go
    c := make(chan struct{}, 0)
    <-c
```

These lines make Go listen for something on a channel that we just created (and where nothing will come), so basically an infinite sleep.
This is to make sure that the `main()` function doesn't end; when `main()` ends, the program ends, and all the functions that we just registered become useless.

## Passing stuff through the boundary

### Simple stuff
Passing `int`, `float`, `string`, `bool` between JavaScript and Go is easily done as described in the example above.
JavaScript `null` and `undefined` can be passed to Go, but has to be inspected through `isNull()` and `isUndefined()`; it doesn't map to a Go type.
When Go returns `nil`, it will be transformed into a JavaScript `null`.

### Arrays/Slices
We are able to pass Arrays/Slices along, but things quickly get complex.
Here we have a function that takes a list of ints, and calculates the Sum and the Product of them.
It then returns a list of length 2, with these two values.
```go
func SumAndProdInts(this js.Value, args []js.Value) interface{} {
    var numbers []int
    for i :=0; i < args[0].Length(); i++ {
        numbers = append(numbers, args[0].Index(i).Int())
    }
    sum := 0
    prod := 1
    for _, number := range numbers {
        sum += number
        prod *= number
    }
    return []interface{} {sum, prod}
}
```
As you can see, we have to call `Int()` on each number separately to convert it.

Take special note of the last line.
One might be very tempted to write (as I did initially while writing this post): `return []int {sum, prod}`.
Doing this leads to the very helpful (not!) error message `panic: ValueOf: invalid value`.

What's going on is that Go knows that the return value of this function is sent to JavaScript, and therefore `js.ValueOf()` is called on the returnvalue.
Even though technically I see no reason why `js.ValueOf()` could not convert an `[]int`, it panics when it receives an `[]int`.
Returning the `[]int` as an `[]interface{}` solves this problem.

Note that `args` is a Go slice of `js.Value`s.
This means that we can loop through `args` and access it's members in the normal, Go-way (`for _, arg := range args {...}` and `args[i]`).
`args[i]` is a `js.Value`; therefore if we know that a *certain* arg is a list, we have to loop through it and access it the `js.Value` way: `for i :=0; i < args[0].Length(); i++ {...}` and `args[0].Index(i)`.

### Objects/Maps
JavaScript Objects can be sent to Go, and a `map[string]interface{}` can be sent from Go to JavaScript.
```go
func CombineName(this js.Value, args []js.Value) interface{} {
    var name string
    if args[0].Get("first").IsUndefined() {
        if args[0].Get("last").IsUndefined() {
            name = "<anonymous>"
        } else {
            name = "Mr/Mrs/Ms. " + args[0].Get("last").String()
        }
    } else {
        if args[0].Get("last").IsUndefined() {
            name = args[0].Get("first").String() + " X."
        } else {
            name = args[0].Get("first").String() + " " + args[0].Get("last").String()
        }
    }
    return map[string]interface{} {
        "full name": name,
    }
}
```

The same rules apply as above: call `String()` on each element after `Get()`.
A `return map[string]string {"full name": name}` is perfectly good Go, will compile just fine, but will result again in a `panic: ValueOf: invalid value`.
One *must* use a `map[string]interface{}`.

As far as I know, there is no easy way to loop over all "keys" in an object received in Go from JavaScript.

### Functions
Functions can be sent from Go to JavaScript, as long as they use the correct signature: `func FuncName(this js.Value, args []js.Value) interface{}`.
One should use the `js.FuncOf()` method to create a JavaScript function.
This can then be assigned to a variable, or be a return value from a function:

```go
func GetAddIntsFunction(this js.Value, args []js.Value) interface{} {
    return js.FuncOf(AddInts)
}
```

The other way around, a JavaScript function can be sent to Go, and then be `Invoke()`d from Go.
This is mostly useful as a callback function for some long-running process:

```go
func Fib(x int) int {
    if x == 1 || x == 2 {
        return 1
    }
    return Fib(x - 1) + Fib(x - 2)
}

func AsyncFib(this js.Value, args []js.Value) interface{} {
    fibnr := args[0].Int()
    callback := args[1]

    go func() {
        result := Fib(fibnr)
        callback.Invoke(result)
    }()
    return nil
}
```

Note that in the case above, it doesn't really make sense to use a callback, but with some changes it will (see more below when we talk about `go routines / threads`.


Finally, there is a way for Go to directly call a JavaScript method.
We could for instance add the following line to our `main()` function
```go
    js.Global().Get("console").Call(
        "log", "hello", "from", runtime.Version())
```

### Other types
There are (as far as I know) 2 JavaScript "normal" data types that are not supported in this interface: BigInt and Symbol (using them will result in a `panic: bad type flag` message).
Since they are used very rarely in JavaScript programs, it's doubtful this will be a practical limitation.

In case of `TypedArray`, one can use the `js.CopyBytesToGo()` and `js.CopyBytesToJS()` functions for `Uint8Array` and `Uint8ClampedArray` -- other `TypedArray`s don't seem to be supported.

Going the other direction, from Go to JavaScript, lots of types are not supported.
It might technically be possible to transfer things like pointers, and store them in JavaScript, but this is outside of the scope of this post (and even it's possible, you likely shouldn't :)).

The fact that one can not store arbitrary Go data in JavaScript does mean that it's far from trivial to offer an Object-oriented interface from Go to JavaScript.
I don't think this is a huge problem; when creating a JavaScript interface for your Go library, I would always choose to create a proper JavaScript (TypeScript) interface (see the [bonus section](#bonus-wrap-your-go-library-in-a-layer-of-javascript-or-better-even-typescript)).

## Tips and tricks
### println
One nice thing that should help you along the way (and during debugging) is that you can use the standard Go `println()` (and `Printf()`) functionality, and it will do a `console.log()`.

### panic: ValueOf: invalid value
Over the course of getting the code examples in this post to work, I've seen above error message way too many times, so often that I want to give it a separate section.

Whenever something is sent to JavaScript (either because of a `Set()` or a `return` in a function, or as arguments in a function or method call (`Invoke()` and `Call()`), it has to be a `js.Value()`.
You as developer can do this explicitly (by calling `js.ValueOf()` in your code), or Go does this for you implicitly.
The error above appears when the argument to `js.ValueOf()` is not one of the following (the list is probably not exhaustive, but will give you a good idea):
- `int`
- `float`
- `string`
- `bool`
- `nil`
- `[]interface{}`
- `map[string]interface{}`

Specifically I got bitten a couple of times when returning an `[]int` (which is an `[]interface{}`, but not allowed) or an `map[string]int`.
See the examples above on how it should be done.

### Goroutines / multi-threading
Goroutines lie at the basis of Go, so I should at least quickly discuss how they are supported in Go -- a following blog post will dig much deeper into this.
At the moment, the WebAssembly code generated by Go (as well as the JavaScript generated from Go) is all single threaded, and runs on the main thread.

If however something is done in a goroutine that does not need the processor (waiting for a channel, or just a simple `time.sleep()`), execution is continued in a spot where there *is* something to do (either a different Goroutine, or in JavaScript), as you can see in [the example at the bottom of this post](#bonus-of-the-bonus-a-proper-async-go-function).

As I said, there is much more to say about this, and I fully intend to write about this in an upcoming post on this blog.

### Promises and async functions
As far as I've been able to attain, there is no support for Promises and async programming models "through" the interface (which would possibly be hard, since Go doesn't know this programming model).
Obvously, one could wrap the interface (see [the example at the bottom of this post](#bonus-of-the-bonus-a-proper-async-go-function)) in order to make proper async functions.

### Program defensively / add asserts
[Defensive programming](https://en.wikipedia.org/wiki/Defensive_design) is always a good idea, but as a Go developer, one gets used to Go doing a lot of these things for you.
For instance, when writing `func add(a int, b int)[] {...}`, it's instantly clear that this is a function that takes 2 ints, and returns an int.
You don't need to write code to handle a case when someone puts in a `float`, or if someone tries to call this function with 3 arguments; the Go compiler has you covered there.
Also it's less necessary to use the word Int in the function name; if someone assumed that it will work with floats, they will instantly see the compiler error.

All this is not true for `func AddInts(this js.Value, args []js.Value) interface{}`.
Here I *do* like to add the expected type to the function name.
In addition, in normal code (I didn't in this post, since it would obscure the points I was trying to make), I would add extra asserts / panics in case the function is used the wrong way:

```go
func AddInts(this js.Value, args []js.Value) interface{} {
    if !this.isUndefined() {
        panic(`Expect this to be undefined`)
    }
    if len(args) != 2 {
        panic(`Expect two arguments: the numbers to be added`)
    }
    a := args[0].Int()
    b := args[1].Int()
    return mylib.AddInts(a, b)
}
```

Note that `a := args[0].Int()` already panics when it's not an int, so no need to do so explicitly.


# Bonus: Wrap your Go library in a layer of JavaScript, or (better even) TypeScript
Exactly because it's hard to read the signatures of the functions that Go exposes to JavaScript, you should always wrap them in a proper JavaScript/TypeScript interface.

Let's expose the Go functions in a location with a name that shows that we don't expect others to access it.

```go
js.Global().Set("mylib__private__AddInts", js.FuncOf(AddInts))
```

Now we create a JavaScript module (with proper documentation and exports) that exposes this functionality:

```javascript
/**
 * Adds two integers together though mylib
 * @param  {Number} a First integer to add
 * @param  {Number} b Second integer to add
 * @return {Number}   Sum of the two integers
 */
function addInts(a, b) {
    mylib__private__AddInts(a, b)
}

...

export {addInts}
```

The proper function signature and documentation means that it's instantly clear for a JavaScript developer (including future-you) how to use this function.
Also a JavaScript editor may show the documentation and type-hints when the function is used.

Note that since JavaScript only has type "Number" (not Int or Float), I prefer to still call the function `addInts`.

We can make things even more explicit in TypeScript
```typescript
function addInts(a: number, b: number): number {
    mylib__private__AddInts(a, b)
}

export {addInts}
```

The code above will lead to an error though, because TypeScript cannot determine the type of `mylib__private__.AddInts`.
In order to fix this, we will need to add a `declarations.d.ts` file:

```typescript
declare function mylib__private__AddInts(a: number, b: number): number
```

One could argue that only this `declarations.d.ts` is already enough, without the wrapper.
TypeScript will complain if the function is used any other way.
Although this is correct, I still like to use the wrapper function; it's a nice single entrance point for this function, if we want we could add logging here, or further JavaScriptfy the function (see next example).
It also takes the Go function out of the global context and into a nice JavaScript module.
{: .notice}

## Bonus of the bonus: a proper async Go function
Before I mentioned that there is no built-in way to make a Go function behave like an async/Promise JavaScript function.
Let's see how we can fix this using wrapping.
In order to illustrate a function that could be async, we put a `sleep` in the `Fib()` function; very artificial, but does the job!

```go
func Fib(x int) int {
	time.Sleep(1 * time.Microsecond)
	if x == 1 || x == 2 {
		return 1
	}
	return Fib(x-1) + Fib(x-2)
}

func AsyncFib(this js.Value, args []js.Value) interface{} {
	fibnr := args[0].Int()
	callback := args[1]

	go func() {
		result := Fib(fibnr)
		callback.Invoke(result)
	}()
	return nil
}

func main() {
	js.Global().Set("mylib__private__AsyncFib", js.FuncOf(AsyncFib))
	c := make(chan struct{}, 0)
	<-c
}
```

We wrap this as follows (TypeScript):
```typescript
function fib(n: number): Promise<number> {
    return new Promise((resolve, _reject) => {
        mylib__private__AsyncFib(n, resolve)
    })
}

export {fib}
```

(or JavaScript)
```typescript
function fib(n) {
    return new Promise((resolve, _reject) => {
        mylib__private__AsyncFib(n, resolve)
    })
}

export {fib}
```

Now you can call this either as `fib(5).then(result => console.log("fib(5)=", result))` or within an `async` function:

```javascript
async function log_fibs() {
  const response1 = await fib(7);
  console.log({response1})
  const response2 = await fib(9);
  console.log({response2})
}
```
