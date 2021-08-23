import importlib
import pathlib
import typing as t

import numpy as np

basefilename = pathlib.Path(__file__).parent / "base.py"
spec = importlib.util.spec_from_file_location("base", basefilename)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def create_plot(ax):
    runDatas = base.loadRunData()

    fzf_types = tuple({r.fzf_type: "" for r in runDatas}.keys())
    nrlines = 2**np.arange(10, 25)
    data = {key: {nr: None for nr in nrlines} for key in fzf_types}
    print("Haystack size|", end="")
    for fzf_type in fzf_types:
        print(fzf_type +"|", end="")
    print("")
    print("--" + "|".join(["--" for _ in fzf_type]))
    for nr in nrlines:
        exp = len(f"{nr:b}") - 1
        print(f"2<sup>{exp}</sup> = {nr}|", end="")
        for fzf_type in fzf_types:
            runtimes = []
            for runData in runDatas:
                if runData.nrlines == nr and runData.fzf_type == fzf_type:
                    if "hello world" in runData.search_times_ms_nr_results:
                        runtimes.append(np.array([
                            i[0] if i[1] is None else i[1]
                            for i in runData.search_times_ms_nr_results.values()
                        ]))
            if runtimes:
                mean_runtime = np.mean(runtimes, axis=0)
                data[fzf_type][nr] = mean_runtime
                total = sum(mean_runtime)
                print(f"{total / 1000:.2f} ({total * 1000 / nr:.1f})|", end="")
            else:
                print("--|", end="")
        print("")
    xaxis = np.arange(len(nrlines))
    ax.set_xticks(xaxis)
    ax.set_xticklabels([f"$2^{{{x+10}}}$" for x in xaxis], rotation=45)
    colours = {
        "Go (native)": ["#008", "#00c", "#77e"],
        "Go (WebAssembly)": ["#730", "#e80", "#fa5"],
        "TinyGo": ["#080", "#0c0", "#7d7"],
        "fzf-for-js": ["#800", "#e00", "#f77"],
        "GopherJS": ["#627", "#84a", "#a7f"],
    }
    colourindex = ([1] * len("hello ")) + ([2] * len("world"))
    GAP = 0.1
    for i, label in enumerate(colours):
        width = 0.8 / len(fzf_types)
        pos = (i - len(fzf_types) / 2) * width
        bottom = np.zeros((len(xaxis), ))
        for a in range(len("hello world")):
            itemdata = np.array(
                [np.nan if stnr is None else stnr[a] for stnr in data[label].values()]
            ) / nrlines * 1000
            color = colours[label][colourindex[a]]
            ax.bar(xaxis[:] + pos,
                   itemdata - (0 if a == len("hello world") else GAP),
                   bottom=bottom,
                   width=width,
                   color=color,
                   label = label if a == 1 else None)
            bottom += itemdata

    ax.set_title("Runtime use divided by size of the haystack")
    ax.set_xlabel("Haystack size")
    ax.set_ylabel("Time per straw (µs)")
    ax.set_ylim([0, 50])
    ax.legend(loc="upper left")
