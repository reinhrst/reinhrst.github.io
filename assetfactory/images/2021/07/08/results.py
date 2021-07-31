import numpy as np
from matplotlib.ticker import FuncFormatter


def formatter(nr, _pos):
    mapping = [
        (9, "T"),
        (6, "M"),
        (3, "k"),
        (0, ""),
        (-3, "m"),
        (-6, "µ"),
        (-9, "n"),
    ]

    for (exp, modifier) in mapping:
        if nr >= 10**exp:
            return "%.1f%s" % (nr / 10**exp, modifier)
    return "%.1f" % nr

data = [
    (1024, 0.7, 0),
    (2048, 1.1, 10),
    (4096, 2.5, 10),
    (8192, 4.8, 20),
    (16384, 6.8, 30),
    (32768, 12.9, 50),
    (65536, 24.9, 100),
    (131072, 48.9, 210),
    (262144, 95.7, 430),
    (524288, 190.9, 860),
    (1048576, 380.1, 1730),
    (2097152, 767.5, 3490),
    (4194304, 1577.7, 6960),
    (8388608, 3173.6, 14290),
    (16777216, 6588.1, 28500),
    (33554432, 33097.6, 58230),
]
x, y1, y2 = map(lambda d: np.array(d, dtype=float), zip(*data))


def create_plot(ax):
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.bar(x-x/8, y1, width=x/4, label="time fzf-lib")
    ax.bar(x+x/8, y2, width=x/4, label="time fzf cmdline")
    ax.xaxis.set_major_formatter(FuncFormatter(formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(formatter))
    ax.set_xlabel("Size of the haystack")
    ax.set_ylabel("Time (ms)")
    ax.legend(facecolor=ax.get_facecolor())
    ax.set_title("""Fzf-lib — time to search for "hello world" in list of quotes""")
