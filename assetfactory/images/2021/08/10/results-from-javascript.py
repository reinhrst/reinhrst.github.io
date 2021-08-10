DATA = [
    ("Load JS/WebAssembly", 2, 2, 2),
    ("Load /tmp/lines.txt", 225, 222, 218),
    ("new Fzf()", 9438, 11677, 2543),
    ("search() until callback", 6144, 2772, 12547),
]



def create_plot(ax):
    labels = ["Go", "TinyGo", "GopherJS"]
    bottoms = [0, 0, 0]
    for row in DATA:
        ax.bar(labels, row[1:], label=row[0], bottom=bottoms)
        bottoms = [bottoms[i] + row[1:][i] for i in range(len(bottoms))]
    ax.set_ylabel("Time (ms)")
    ax.set_ylim([0, 20000])
    ax.legend()
