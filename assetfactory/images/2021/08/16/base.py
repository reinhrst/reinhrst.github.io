from __future__ import annotations
import pathlib
import typing as t

import numpy as np

import math

def rgb_to_hsv(r, g, b):
    r = float(r)
    g = float(g)
    b = float(b)
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, v = high, high, high

    d = high - low
    s = 0 if high == 0 else d/high

    if high == low:
        h = 0.0
    else:
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return h, s, v

def hsv_to_rgb(h, s, v):
    i = math.floor(h*6)
    f = h*6 - i
    p = v * (1-s)
    q = v * (1-f*s)
    t = v * (1-(1-f)*s)

    r, g, b = [
        (v, t, p),
        (q, v, p),
        (p, v, t),
        (p, q, v),
        (t, p, v),
        (v, p, q),
    ][int(i%6)]

    return r, g, b

def rgb_to_hsl(r, g, b):
    r = float(r)
    g = float(g)
    b = float(b)
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, l = ((high + low) / 2,)*3

    if high == low:
        h = 0.0
        s = 0.0
    else:
        d = high - low
        s = d / (2 - high - low) if l > 0.5 else d / (high + low)
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return h, s, l

def hsl_to_rgb(h, s, l):
    def hue_to_rgb(p, q, t):
        t += 1 if t < 0 else 0
        t -= 1 if t > 1 else 0
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        r, g, b = l, l, l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

    return r, g, b


def hex_to_rgb(rgb: str) -> t.Tuple[float, float, float]:
    assert rgb[0] == "#"
    if len(rgb) == len("#rgb"):
        elementlength = 1
    else:
        assert len(rgb) == len("#rrggbb")
        elementlength = 2
    return [int(rgb[i:i + elementlength], 16) / (16 ** elementlength - 1)
            for i in range(1, len(rgb), elementlength)]

def rgb_to_hex(r: float, g: float, b: float) -> str:
    assert 0 <= r <= 1
    assert 0 <= g <= 1
    assert 0 <= b <= 1
    return "#" + "".join(
        "%02x" % int(round(c * 255)) for c in (r, g, b))

def lighter(rgb: str, pct: float):
    assert 0 < pct <= 100
    r, g, b = hex_to_rgb(rgb)
    h, s, l = rgb_to_hsl(r, g, b)
    l = 1 - (1 - l) / (1 + pct / 100)
    return rgb_to_hex(*hsl_to_rgb(h, s, l))

class RunDataNoMatchException(Exception):
    def __init__(self, runData: RunData):
        self.runData = runData
        super().__init__("Ran out of data to match")

class RunDataOutOfLinesException(Exception):
    def __init__(self):
        super().__init__("No more lines")

TYPE_MAP = {
    "go-native": "Go (native)",
    "go": "Go (WebAssembly)",
    "tinygo": "TinyGo",
    "fzf-for-js": "fzf-for-js",
    "gopherjs": "GopherJS",
    "go-debugnogc": "Go (WebAssembly; no GC)",
    "tinygo-leakinggc": "TinyGo (no GC)",
    "go-native-nogc": "Go (native; no GC)",
}

COLOUR_MAP = {
    "Go (native)": ["#003f5c", "#668eaa", "#002633"],
    "Go (native; no GC)": ["#ffa600", "#ffcc33"],
    "Go (WebAssembly)": ["#58508d", "#9e94c5", "#262145"],
    "Go (WebAssembly; no GC)": ["#9e94ff", "#b7b2ff"],
    "TinyGo": ["#bc5090", "#df94be", "#8F2464"],
    "TinyGo (no GC)": ["#00c786", "#33ffa0"],
    "fzf-for-js": ["#ff6361", "#ffa097", "#cc2020"],
    "GopherJS": ["#ffa600", "#ffc171", "#cc5000"],
}

COLOUR_MAP = {
    **COLOUR_MAP,
    **{f"{key} - {browser}": [lighter(v, pct) for v in value]
       for key, value in COLOUR_MAP.items()
       for browser, pct in [
           ("Firefox", 20),
           ("Chrome", 40),
           ("Safari", 60),
           ("Edge", 80),
       ]}
}

LOG2_MAP = {2**i: i for i in range(40)}


class RunData:
    fzf_type: str = None
    nrlines: int = None
    lines_load_time_ms: int = None
    fzf_init_time_ms: int = None
    memory_used_mib: float = None
    search_times_ms_nr_results: t.MutableMapping[str, t.Tuple[int, int]] = None
    aborted: bool
    browser: bool

    def popuntilstartmatch(self, lines: t.MutableSequence[str], start: str) -> str:
        try:
            while not (line := lines.pop()).startswith(start):
                if line.startswith("******"):
                    self.aborted = True
                    lines.append(line)
                    raise RunDataNoMatchException(self)
        except IndexError:
            self.aborted = True
            raise RunDataNoMatchException(self)
        return line

    def __init__(self, lines: t.MutableSequence[str]):
        self.aborted = False
        self.search_times_ms_nr_results = {}
        try:
            while not (line := lines.pop()).startswith("******"):
                pass
        except IndexError:
            raise RunDataOutOfLinesException()
        line = self.popuntilstartmatch(lines, "fzf-type: ")
        raw_fzf_type = line.split()[1]
        if any(raw_fzf_type.endswith(f"-{x}")
               for x in ("edge", "safari", "firefox", "chrome")):
            base, browser = raw_fzf_type.rsplit("-", 1)
            self.fzf_type = TYPE_MAP[base] + f" - {browser.capitalize()}"
            self.browser = True
        else:
            self.fzf_type = TYPE_MAP[raw_fzf_type]
            self.browser = False
        line = self.popuntilstartmatch(lines, "lines.txt loaded:")
        _, _, nrlines, _, _, lines_load_time_ms = line.split()
        self.nrlines = int(nrlines)
        self.lines_load_time_ms = int(lines_load_time_ms)

        line = self.popuntilstartmatch(lines, "Fzf initialized ")
        self.fzf_init_time_ms = int(line.split()[-1]) - self.lines_load_time_ms
        while "hello world" not in self.search_times_ms_nr_results:
            line = self.popuntilstartmatch(lines, "Searching for '")
            nrresults = int(line.split()[-2])
            line = lines.pop()
            assert line.startswith(f"--- ../{self.nrlines}.txt "), line
            searchtime = int(line.split()[2])
            searchterm = line.split(" ", 4)[-1]
            if lines[-1].startswith("hash: "):
                line = lines.pop()
                assert line.startswith("hash: ")
                hash = line.split()[1][:5]
            else:
                hash = None
            if lines[-1].startswith("+++ filename "):
                line = lines.pop()
                gosearchtime = int(line.split()[2])
            else:
                gosearchtime = None

            self.search_times_ms_nr_results[searchterm] = (searchtime, gosearchtime, hash, nrresults)
        if self.browser:
            self.memory_used_mib = None
        else:
            line = self.popuntilstartmatch(lines, "	Maximum resident set size (kbytes):")
            self.memory_used_mib = float(line.split()[-1]) / 1024

    def __repr__(self):
        aborted = "<aborted>" if self.aborted else ""
        memused = self.memory_used_mib and round(self.memory_used_mib, 1)
        return (
            f"RunData{aborted}: {self.fzf_type}({self.nrlines}). "
            f"load {self.lines_load_time_ms} ms; "
            f"fzf init {self.fzf_init_time_ms} ms; "
            f"search results: {self.search_times_ms_nr_results}; "
            f"memory used results: {memused} MiB; "
        )


def loadRunData() -> t.Sequence[RunData]:
    runDatas: t.MutableSequence[RunData] = []
    for filename in (
        pathlib.Path(__file__).parent / "results-native-2.txt",
        pathlib.Path(__file__).parent / "results-native-nogc-2.txt",
        pathlib.Path(__file__).parent / "results.browsers.txt",
        pathlib.Path(__file__).parent / "results-new.txt",
        pathlib.Path(__file__).parent / "results-debugnogc.txt",
                     ):
        data = pathlib.Path(filename).read_text()
        lines = list(reversed(data.splitlines()))
        while True:
            try:
                runData = RunData(lines)
                runDatas.append(runData)
            except RunDataNoMatchException as e:
                runDatas.append(e.runData)
            except RunDataOutOfLinesException:
                break
    hashes = {}
    for runData in runDatas:
        if runData.aborted:
            continue
        key = runData.nrlines
        myhashes = tuple([i[2] for i in runData.search_times_ms_nr_results.values()])
        if key in hashes:
            if hashes[key][0] != myhashes:
                print(f"For {key}:\n    {hashes[key][0]} ({hashes[key][1]}) !=\n    {myhashes} {runData.fzf_type}")
                breakpoint()
        else:
            hashes[key] = (myhashes, runData.fzf_type)


    return t.cast(t.Sequence[RunData], runDatas)

def markdown_table(data, large_small_multiplier) -> str:
    totaldata = {
        key: {
            nr: np.sum(data[key][nr]) for nr in data[key]
        } for key in data
    }
    return "\n".join(
        [
            "|".join(["Haystack size", *[key for key in data]]),
            "|".join(["---"] * (len(data) + 1)),
            *[
                "|".join([
                    f"2<sup>{LOG2_MAP[nr]}</sup> = {nr}",
                    *["---" if np.isnan(dfk[nr])
                      else
                      f"{dfk[nr]:.2f} ({dfk[nr] * large_small_multiplier / nr:.1f})"
                      for key, dfk in totaldata.items()],
                ])
                for nr in list(data.values())[0]
            ]
        ]
    )


def do_create_table_and_plot(
        ax,
        nrlinesexp: t.Sequence[int],
        data_element_getter: t.Callable[[RunData], t.Sequence[float]],
        to_show: t.Sequence[t.Optional[str]],
        colourmap: t.Sequence[int],
        ylim: t.Tuple[float, float],
        large_small_multiplier: float=1e6,
    ):
    runDatas = loadRunData()
    fzf_types = {r.fzf_type for r in runDatas}
    assert all(key in fzf_types for key in to_show if key is not None)
    data = {key: {2**nr: [] for nr in nrlinesexp}
            for key in to_show if key is not None}
    runData: RunData
    datalength = len(colourmap)
    for runData in runDatas:
        if (
                runData.aborted
                or (key := runData.fzf_type) not in data
                or (nrlines := runData.nrlines) not in data[key]):
            continue
        data[key][nrlines].append(data_element_getter(runData))
        assert datalength == len(data[key][nrlines][-1])

    # calculate averages
    for key in data:
        for nr in data[key]:
            if data[key][nr]:
                data[key][nr] = np.mean(data[key][nr], axis=0)
            else:
                data[key][nr] = np.full((datalength, ), np.nan)

    xaxis = nrlinesexp - nrlinesexp[0]
    ax.set_xticks(xaxis)
    ax.set_xticklabels([f"$2^{{{exp}}}$" for exp in nrlinesexp], rotation=45)
    gap = (ylim[1] - ylim[0]) / 500

    bargap = "".join(" " if k is None else "b" for k in to_show)
    nrbars = bargap.count("b")
    nrgaps = len(bargap.strip()) - nrbars
    width = 0.9 / (nrbars + nrgaps / 2)
    x_offset = -0.45
    for label in to_show:
        if label is None:
            x_offset += width / 2
            continue
        bottom = np.zeros((len(xaxis), ))
        for a in range(datalength):
            itemdata = np.array([data[label][2**exp][a] for exp in nrlinesexp]
                                ) / 2**nrlinesexp * large_small_multiplier
            colour = COLOUR_MAP[label][colourmap[a]]

            ax.bar(xaxis[:] + x_offset,
                   itemdata - (gap if a < datalength - 1 else 0),
                   bottom=bottom,
                   width=width,
                   color=colour,
                   label = label if a == min(1, datalength - 1) else None)
            bottom += itemdata
        x_offset += width

    ax.set_ylim(*ylim)
    return markdown_table(data, large_small_multiplier)
