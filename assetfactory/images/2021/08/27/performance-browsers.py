import importlib
import pathlib

import numpy as np

basefilename = pathlib.Path(__file__).parent / "base.py"
spec = importlib.util.spec_from_file_location("base", basefilename)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def create_plot(ax):
    to_show = [None if ts is None or browser is None
               else f"{ts} - {browser}" if browser else ts
               for ts in ("Go (WebAssembly)", "TinyGo", "fzf-for-js", "GopherJS",)
               for browser in ("", "Firefox", "Chrome", "Safari", "Edge", None)]
    tabledata = base.do_create_table_and_plot(
        ax,
        np.arange(17, 22),
        lambda runData: np.array([
            runData.fzf_init_time_ms,
            *[i[0] for i in runData.search_times_ms_nr_results.values()]
        ]) / 1000,
        to_show = to_show,
        colourmap = [2] * (len("hello world") + 1),
        ylim=(0, 200)
    )

    ax.set_title("Runtime use divided by size of the haystack")
    ax.set_xlabel("Haystack size (bars for Node, Firefox, Chrome, Safari, Edge)")
    ax.set_ylabel("Time per straw (µs)")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles[3::5],
              labels=[l.rsplit(" - ", 1)[0] for l in labels[3::5]],
              loc="upper left")
    return tabledata
