DATA = [
    ("Load JS/WebAssembly", 2, 2, 2, 2, 2),
    ("Load /tmp/lines.txt", 225, 222, 218, 209, 202),
    ("From JS new Fzf() until ready to ....",
     7825, 8548, 1579, 2592, 15069),
    ("Calling fzf-lib's fzf.New()", 1255, 3121, 963, 612, 899),
    ("return from fzfNew() function", 358, 7, 0, 18, 1),
    ("search() until library has result", 4235, 1394, 12132, 4069, 11805),
    ("Returning search result to JS callback", 1908, 1378, 416, 1173, 6400),
]



def create_plot(ax):
    labels = ["Go", "TinyGo", "GopherJS", "Go with JSON", "GopherJS with JSON"]
    bottoms = [0, 0, 0, 0, 0]
    for row in DATA:
        ax.bar(labels, row[1:], label=row[0], bottom=bottoms)
        bottoms = [bottoms[i] + row[1:][i] for i in range(len(bottoms))]
    ax.set_ylabel("Time (ms)")
    ax.set_ylim([0, 45000])
    ax.legend(ncol=2)
