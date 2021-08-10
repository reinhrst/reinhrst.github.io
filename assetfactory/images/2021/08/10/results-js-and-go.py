DATA = [
    ("Load JS/WebAssembly", 2, 2, 2),
    ("Load /tmp/lines.txt", 225, 222, 218),
    ("From JS new Fzf() until ready to ....",
     7825, 8548, 1579),
    ("Calling fzf-lib's fzf.New()", 1255, 3121, 963),
    ("return from fzfNew() function", 358, 7, 0),
    ("search() until library has result", 4235, 1394, 12132),
    ("Returning search result to JS callback", 1908, 1378, 416),
]



def create_plot(ax):
    labels = ["Go", "TinyGo", "GopherJS"]
    bottoms = [0, 0, 0]
    for row in DATA:
        ax.bar(labels, row[1:], label=row[0], bottom=bottoms)
        bottoms = [bottoms[i] + row[1:][i] for i in range(len(bottoms))]
    ax.set_ylabel("Time (ms)")
    ax.set_ylim([0, 20000])
    ax.legend(ncol=2)
