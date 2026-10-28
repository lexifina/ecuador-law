"""Prints the law of Ecuador as it stood on a given day, read from this repository's history.

    python tools/vigente_el.py 2024-05-29 constitucion art-138   # art. 138 the day before the 2024 enmienda
    python tools/vigente_el.py 2024-05-30 constitucion 138       # the same article, by number, as amended
    python tools/vigente_el.py 2010-01-01 constitucion           # the whole Constitution on 1 January 2010
    python tools/vigente_el.py --law 2020-01-01 constitucion 158 # also name the law behind that wording

A thin wrapper around tools/on.py: the version is chosen by each commit's `In-force:` trailer, never by its commit
date, and branches named wip* are ignored. Standard library only.
"""
import runpy
import sys
from pathlib import Path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.argv[0] = str(Path(__file__).with_name('on.py'))
    runpy.run_path(sys.argv[0], run_name='__main__')
