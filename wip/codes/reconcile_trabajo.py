"""Reading-only comparison of the Código del Trabajo as rebuilt here (version in force on 1-II-2023) with the Lexis-style
consolidation of that date (LegalCloud DOCX, 'Última modificación: 01-02-2023', codes/index_docx.py). Nothing here
becomes legal text: it lists the numbered articles whose words differ after normalising spacing, quotes, dashes and
the article heading, with the differing words. Articles innumerados ('Art. ...', 'Art. (...)') are cut off the
numbered article they follow in the DOCX and compared by hand (codes/trabajo.py decisions).

    python -X utf8 codes/reconcile_trabajo.py [part.json]      -> codes/reconcile_trabajo.json
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import index_docx  # noqa: E402

DAY = "2023-02-01"


def norm(s: str) -> str:
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("–", "-").replace("—", "-").replace(" ", " ")
    s = re.sub(r"^\s*Art(?:ículo|\.)?\s*\d+(?:\.\d+)?\s*\.?-?\s*", "", s)
    s = re.sub(r"\s+([.,;:)])", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def lexis() -> dict[str, str]:
    t = "\n".join(index_docx.paras("trabajo"))
    t = re.split(r"\nDISPOSICIONES TRANSITORIAS\n", t)[0]
    out: dict[str, str] = {}
    marks = list(re.finditer(r"(?:^|\s)Art\.\s*(\d+)(?:\.(\d+))?\s*\.-", t, re.M))
    for i, m in enumerate(marks):
        body = t[m.start():marks[i + 1].start() if i + 1 < len(marks) else len(t)]
        body = re.split(r"\s(?:Nota:|Concordancias:|Jurisprudencia:)", body)[0]
        body = re.split(r"\sArt\.\s*(?:\.\.\.|\(\.\.\.\)|innumerado)", body)[0]
        body = re.sub(r"(?:\n|\s{2,})(?:TÍTULO|TITULO|Capítulo|CAPÍTULO|CAPITULO|Parágrafo|PARÁGRAFO)\s.*", "", body,
                      flags=re.S)
        n = int(m.group(1))
        key = f"art-{n:04d}" + (f"-{int(m.group(2))}" if m.group(2) else "")
        out.setdefault(key, body)
    return out


def ours(path: Path) -> dict[str, str]:
    act = json.loads(path.read_text(encoding="utf-8"))["acts"][0]
    units = dict(act["versions"][0]["units"])
    for v in act["versions"][1:]:
        if v["from"] > DAY:
            break
        for k, x in (v.get("changes") or {}).items():
            if x is None:
                units.pop(k, None)
            else:
                units[k] = x
    return {k: u["text"] for k, u in units.items() if k.startswith("art-")}


def main(argv: list[str]) -> None:
    path = Path(argv[0]) if argv else HERE.parent / "corpus.d" / "90-trabajo.json"
    a, b = ours(path), lexis()
    rows = {}
    same = 0
    for k in sorted(set(a) | set(b)):
        x, y = norm(a.get(k, "")), norm(b.get(k, ""))
        if x == y:
            same += 1
            continue
        sm = difflib.SequenceMatcher(None, x.split(), y.split(), autojunk=False)
        d = [f"{' '.join(x.split()[i1:i2])!r} -> {' '.join(y.split()[j1:j2])!r}"
             for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
        rows[k] = d[:8] if k in a and k in b else ["only here" if k in a else "only in Lexis"]
    out = HERE / "reconcile_trabajo.json"
    out.write_text(json.dumps({"day": DAY, "agree": same, "differ": rows}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"{same} agree, {len(rows)} differ -> {out.name}")
    for k, d in rows.items():
        print(k, "|", " ; ".join(d)[:300])


if __name__ == "__main__":
    main(sys.argv[1:])
