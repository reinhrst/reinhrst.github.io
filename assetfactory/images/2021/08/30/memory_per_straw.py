import importlib
import pathlib

import numpy as np

basefilename = pathlib.Path(__file__).parent / "base.py"
spec = importlib.util.spec_from_file_location("base", basefilename)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def create_plot(ax):
    tabledata = base.do_create_table_and_plot(
        ax,
        np.arange(10, 25),
        lambda runData: np.array([runData.memory_used_mib]),
        to_show = (
            "Go (native)",
            "Go (WebAssembly)",
            "TinyGo",
            "fzf-for-js",
            "GopherJS",
        ),
        colourmap = [0],
        ylim=(0, 10),
        large_small_multiplier=1024,
    )

    ax.set_title("Memory use divided by size of the haystack")
    ax.set_xlabel("Haystack size")
    ax.set_ylabel("Memory per straw (kiB)")
    ax.legend(loc="upper right")
    return tabledata
