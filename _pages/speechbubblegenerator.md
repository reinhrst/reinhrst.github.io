---
title: "SVG speech bubble generator"
permalink: /speechbubblegenerator/
layout: single
---
<style>
svg#generator {
    border: 1px solid grey;
}
span.value {
    width: 50px;
    display: inline-block;
}
code#generatorcode {
    white-space: break-spaces;
}
button {
    margin: 7px;
}
</style>
This generator is based on the methods described in [this blog post](../_posts/2021-08-05-making-speech-bubbles-in-svg.md).

See the generated SVG code at the bottom.

<svg id="generator" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 500" width="1000" height="500">
    <defs>
        <ellipse id="bubble" cx="300" cy="75" rx="150" ry="70" />
    </defs>

    <use href="#bubble" style="stroke: black; stroke-width: 6px; fill: none;" />
    <path style="stroke: black; stroke-width: 3px; fill: white;" d="
        M 200,100
        q -20,80 -100,100
        q 90,-20 120,-100
    " />
    <use href="#bubble" style="stroke: none; fill: white;" />
</svg>
<label for="strokewidth">Stroke width: <span class="value"></span>
    <input type="range" id="strokewidth" min="1" max="12" value="3">
</label>
<label for="bubblewidth">Bubble width: <span class="value"></span>
    <input type="range" id="bubblewidth" min="10" max="950" value="300">
</label>
<label for="bubbleheight">Bubble height: <span class="value"></span>
    <input type="range" id="bubbleheight" min="10" max="450" value="140">
</label>
<div>
    <button id="bubblemidpoint">Move bubble</button>
    <button id="arrowmove">Move arrow</button>
    <button id="arrowpoint">Move arrow point</button>
</div>
<div>
    <button id="arrowend1">Move arrow end 1</button>
    <button id="arrowcurve1">Change arrow curve 1</button>
</div>
<div>
    <button id="arrowend2">Move arrow end 2</button>
    <button id="arrowcurve2">Change arrow curve 2</button>
</div>
<div class="language-xml highlighter-rouge">
    <code id="generatorcode"></code>
</div>

<script>
    function updateCode() {
        document.querySelector("#generatorcode").innerText =
                            document.querySelector("#generator").outerHTML

    }
    updateCode()
    function bubbleChange() {
        for (const [dim, att] of [["width", "rx"], ["height", "ry"]]){
            const value = document.querySelector(`#bubble${dim}`).value;
            document.querySelector(`label[for=bubble${dim}] span.value`).innerText = value;
            document.querySelector("svg#generator #bubble").setAttribute(att, value / 2);
        }
        updateCode()
    }
    document.querySelector("#bubblewidth").addEventListener("input", bubbleChange)
    document.querySelector("#bubbleheight").addEventListener("input", bubbleChange)
    bubbleChange()

    function strokeChange() {
        const width = document.querySelector("#strokewidth").value;
        document.querySelector(`label[for=strokewidth] span.value`).innerText = width + "px";
        document.querySelector("svg#generator use").style.strokeWidth = (width * 2) + "px"
        document.querySelector("svg#generator path").style.strokeWidth = width + "px"
        updateCode();
    }
    strokeChange()
    document.querySelector("#strokewidth").addEventListener("input", strokeChange)

    function bubbleFollowPointer(event) {
        const rect = this.getBoundingClientRect();
        const x = Math.round(event.clientX - rect.left);
        const y = Math.round(event.clientY - rect.top);
        document.querySelector("svg#generator #bubble").setAttribute("cx", x);
        document.querySelector("svg#generator #bubble").setAttribute("cy", y);
        updateCode()
    }

    function getPath() {
        const pathd = document.querySelector("#generator path").getAttribute("d")
        const values = pathd.match(/^\W+M[\W]*?(-?\d+)[\W,]+?(-?\d+)[\W,]*q[\W,]*?(-?\d+)[\W,]+?(-?\d+)[\W,]+?(-?\d+)[\W,]+?(-?\d+)[\W,]*q[\W,]*?(-?\d+)[\W,]+?(-?\d+)[\W,]+?(-?\d+)[\W,]+?(-?\d+)[\W,]*$/).slice(1);
        return values.map(parseFloat)
    }

    function getPathAbsolute() {
        // get path as absolute values
        const values = getPath()
        values[2] += values[0]
        values[4] += values[0]
        values[3] += values[1]
        values[5] += values[1]
        values[6] += values[4]
        values[8] += values[4]
        values[7] += values[5]
        values[9] += values[5]
        return values;
    }

    function setPathAbsolute(values) {
        values[6] -= values[4]
        values[8] -= values[4]
        values[7] -= values[5]
        values[9] -= values[5]
        values[2] -= values[0]
        values[4] -= values[0]
        values[3] -= values[1]
        values[5] -= values[1]
        setPath(values)
    }
    function setPath(values) {
        values = values.map(Math.round);
        const indent = "                "
        const pathd = `\n${indent}M ${values[0]},${values[1]}\n${indent}q ${values[2]},${values[3]} ${values[4]},${values[5]}\n${indent}q ${values[6]},${values[7]} ${values[8]},${values[9]}\n              `
        document.querySelector("#generator path").setAttribute("d", pathd)
    }

    function moveWholeArrow(event) {
        const rect = this.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const values = getPath();
        values[0] = x - values[4]
        values[1] = y - values[5]
        setPath(values)
        updateCode()
    }
    function pathPointFollowPointer(pointindex) {
        return function (event) {
            const rect = this.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            const values = getPathAbsolute();
            values[pointindex] = x
            values[pointindex + 1] = y
            setPathAbsolute(values)
            updateCode()
        }
    }

    const end1PointFollowPointer = pathPointFollowPointer(0);
    const end1CurveFollowPointer = pathPointFollowPointer(2);
    const arrowPointFollowPointer = pathPointFollowPointer(4);
    const end2CurveFollowPointer = pathPointFollowPointer(6);
    const end2PointFollowPointer = pathPointFollowPointer(8);

    function removeAllListeners() {
        document.querySelector("#generator").removeEventListener("pointermove", bubbleFollowPointer)
        document.querySelector("#generator").removeEventListener("pointermove", moveWholeArrow)
        document.querySelector("#generator").removeEventListener("pointermove", end1PointFollowPointer)
        document.querySelector("#generator").removeEventListener("pointermove", end1CurveFollowPointer)
        document.querySelector("#generator").removeEventListener("pointermove", arrowPointFollowPointer)
        document.querySelector("#generator").removeEventListener("pointermove", end2CurveFollowPointer)
        document.querySelector("#generator").removeEventListener("pointermove", end2PointFollowPointer)
    }

    document.querySelector("#generator").addEventListener("click", removeAllListeners)

    for (const [selector, listener] of [
                            ["#bubblemidpoint", bubbleFollowPointer],
                            ["#arrowmove", moveWholeArrow],
                            ["#arrowend1", end1PointFollowPointer],
                            ["#arrowcurve1", end1CurveFollowPointer],
                            ["#arrowpoint", arrowPointFollowPointer],
                            ["#arrowcurve2", end2CurveFollowPointer],
                            ["#arrowend2", end2PointFollowPointer]]) {
        document.querySelector(selector).addEventListener("click", () => {
            removeAllListeners();
            document.querySelector("#generator").addEventListener("pointermove", listener);
        })
    }
</script>
