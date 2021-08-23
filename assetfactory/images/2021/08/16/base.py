from __future__ import annotations
import pathlib
import typing as t


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
    "go-debugnogc": "Go (no GC)",
    "tinygo-leakinggc": "TinyGo (no GC)",
    "go-native-nogc": "Go (native; no GC)",
}


class RunData:
    fzf_type: str = None
    nrlines: int = None
    lines_load_time_ms: int = None
    fzf_init_time_ms: int = None
    memory_used_mib: float = None
    search_times_ms_nr_results: t.MutableMapping[str, t.Tuple[int, int]] = None
    aborted: bool

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
        self.fzf_type = TYPE_MAP[line.split()[1]]
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
        pathlib.Path(__file__).parent / "results-native.txt",
        pathlib.Path(__file__).parent / "results-native-nogc.txt",
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
        else:
            hashes[key] = (myhashes, runData.fzf_type)


    return t.cast(t.Sequence[RunData], runDatas)
