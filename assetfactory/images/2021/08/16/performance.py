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
        lambda runData: np.array([
            runData.fzf_init_time_ms,
            *[i[0] for i in runData.search_times_ms_nr_results.values()]
        ]) / 1000,
        to_show = (
            "Go (native)",
            "Go (WebAssembly)",
            "TinyGo",
            "fzf-for-js",
            "GopherJS",
        ),
        colourmap = [2] + [0] * len("hello") + [1] * len(" world"),
        ylim=(0, 100)
    )

    ax.set_title("Runtime use divided by size of the haystack")
    ax.set_xlabel("Haystack size")
    ax.set_ylabel("Time per straw (µs)")
    ax.legend()
    return tabledata
