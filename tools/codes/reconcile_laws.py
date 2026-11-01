"""Reading-only reconciliation of the LOTAIP and the Ley de Transformación Digital with Lexis consolidations (Lexis
'última reforma' 2024-05-29 and 2025-06-13, as posted by a public body). Nothing is
copied: per unit, the record's words are compared, letters and digits only, with the consolidation's text.

    python -X utf8 codes/reconcile_laws.py <part.json> <consolidation.pdf> <date> [--show]
"""
from __future__ import annotations

import json
import re
import sys

import fitz


def letters(s: str) -> str:
    """Letters and digits only; Lexis sets each article's label ('Art. 2') in a margin column that lands inside the
    running text, so 'art' + number is dropped on both sides."""
    return re.sub(r"art\d+", "", re.sub(r"[^0-9a-záéíóúñü]", "", s.lower()))


HEAD = re.compile(r"^(?:Artículo|Art\.)\s*[\d-]+[A-Z]*\s*\.?-\s*|^(?:PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|OCTAVA|NOVENA|ÚNICA)\.-\s*")


def body(line: str) -> str:
    """A line without its article or disposition heading (Lexis writes 'Art. 1.-' where the gazette has 'Artículo 1.-')."""
    return letters(HEAD.sub("", line))


def state(part: dict, day: str) -> dict:
    units: dict = {}
    for v in part["acts"][0]["versions"]:
        if v["from"] > day:
            break
        if "units" in v:
            units = dict(v["units"])
        for k, u in (v.get("changes") or {}).items():
            if u is None:
                units.pop(k, None)
            else:
                units[k] = u
    return units


def consolidation(path: str) -> str:
    d = fitz.open(path)
    text = "\n".join(d[i].get_text() for i in range(len(d)))
    title = next(x.strip() for x in text.splitlines() if x.strip())  # the running title on every page
    text = "\n".join(x for x in text.splitlines() if x.strip() != title)
    # the publisher's running heads, page footers and notes are not law text
    text = re.sub(r"(?m)^.*Página \d+ de \d+.*$", " ", text)
    text = re.sub(r"(?m)^.*(descargado de las bases de datos de LEXIS|comercialización o divulgación|"
                  r"estrictamente prohibida).*$", " ", text)
    return letters(text)


def main(argv: list[str]) -> None:
    part = json.load(open(argv[0], encoding="utf-8"))
    flat = consolidation(argv[1])
    units = state(part, argv[2])
    agree, differ = 0, []
    for k, u in units.items():
        if k == "titulos":
            continue
        lines = u["text"].splitlines()
        if all(body(x) in flat for x in lines):
            agree += 1
        else:
            differ.append((k, [x for x in lines if body(x) not in flat]))
    print(f"{argv[0]} on {argv[2]}: {agree} units agree, {len(differ)} differ")
    for k, xs in differ:
        print(" ", k, len(xs), "line(s)")
        if "--show" in argv:
            for x in xs:
                print("     ", x[:220])


if __name__ == "__main__":
    main(sys.argv[1:])
