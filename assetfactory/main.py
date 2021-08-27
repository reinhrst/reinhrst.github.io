import argparse
import importlib
import logging
import pathlib
import typing

import matplotlib.pyplot as plt

logger = logging.getLogger()

def process_file(filename: pathlib.Path):
    if not filename.is_file():
        raise Exception("File does not exist: %s" % filename)
    spec = importlib.util.spec_from_file_location("module", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _fig, ax = plt.subplots(figsize=(8,6), facecolor="#f3f3f3")
    ax.set_facecolor("#f3f3f3")
    tabledata = module.create_plot(ax)

    here = pathlib.Path(__file__).resolve().parent
    relative = filename.relative_to(here)
    assets = here.parent / "assets"
    target = (assets / relative).parent / f"{relative.stem}.svg"
    if not target.parent.exists():
        target.parent.mkdir(parents=True)
        logger.info("Created directory %s", target.parent)
    plt.tight_layout(pad=.2)
    plt.savefig(target)
    logger.info("Wrote %s", target)

    if tabledata:
        tables = here.parent / "_posts" / "tables"
        target = (tables / relative).parent / f"{relative.stem}.md"
        if not target.parent.exists():
            target.parent.mkdir(parents=True)
            logger.info("Created directory %s", target.parent)
        target.write_text(tabledata)
        logger.info("Wrote %s", target)


def run():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="+")
    args = parser.parse_args()

    filenames = [pathlib.Path(filename).resolve() for filename in args.filename]
    completed_filenames: typing.Sequence[pathlib.Path] = []
    for filename in filenames:
        try:
            process_file(filename)
        except Exception:
            logger.exception("Problem with %r", filename)
        else:
            completed_filenames.append(filename)

    logger.info("Done, handled %d / %d files successfully",
                len(completed_filenames), len(filenames))


if __name__ == "__main__":
    run()
