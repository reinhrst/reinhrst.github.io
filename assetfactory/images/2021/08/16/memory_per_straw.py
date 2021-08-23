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

    graphstartexp = 10
    fzf_types = tuple({r.fzf_type: "" for r in runDatas}.keys())
    nrlines = 2**np.arange(graphstartexp, 25)
    data = {key: {nr: 0 for nr in nrlines} for key in fzf_types}
    print("Haystack size|", end="")
    for fzf_type in fzf_types:
        print(fzf_type +"|", end="")
    print("")
    print("--" + "|".join(["--" for _ in fzf_type]))

    for nr in nrlines:
        exp = len(f"{nr:b}") - 1
        print(f"2<sup>{exp}</sup> = {nr}|", end="")
        for fzf_type in fzf_types:
            memory = []
            for runData in runDatas:
                if runData.nrlines == nr and runData.fzf_type == fzf_type:
                    if runData.memory_used_mib:
                        memory.append(runData.memory_used_mib)
            if memory:
                mean_memory = np.mean(memory)
                data[fzf_type][nr] = mean_memory
                print(f"{mean_memory:.1f} ({mean_memory * 1024 / nr:.1f})|", end="")
            else:
                data[fzf_type][nr] = np.nan
                print("--|", end="")
        print("")

    xaxis = np.arange(len(nrlines))
    ax.set_xticks(xaxis)
    ax.set_xticklabels([f"$2^{{{x+graphstartexp}}}$" for x in xaxis], rotation=45)
    for i, label in enumerate(fzf_types):
        width = 0.8 / len(fzf_types)
        pos = (i - len(fzf_types) / 2) * width
        itemdata = np.array(list(data[label].values())) / nrlines * 1024
        ax.bar(xaxis + pos, itemdata, width=width, label=label)

    ax.set_title("Memory use divided by size of the haystack")
    ax.set_xlabel("Haystack size")
    ax.set_ylabel("Memory per straw (kiB)")
    ax.set_ylim([0, 10])
    ax.legend()
