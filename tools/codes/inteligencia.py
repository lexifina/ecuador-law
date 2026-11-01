"""Write corpus.d/99-inteligencia.json: the Ley Orgánica de Inteligencia (2025).

Reads only the cache. Deterministic: the same cache gives the same bytes. The part is written atomically (.tmp, then
rename).

    python -X utf8 codes/inteligencia.py      (INTELIGENCIA_OUT=... to write elsewhere)

Base: Registro Oficial Cuarto Suplemento 57, 11-VI-2025 (text layer), in force on publication (its Disposición
final). Later change: Ley Orgánica Reformatoria para el Fortalecimiento del Sistema Penitenciario (Cuarto Suplemento
275, 29-IV-2026), art. 28, adds a final inciso to art. 30; in force on publication (its Disposición final única).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import discapacidad as D  # noqa: E402  (shared parser and helpers)

OUT = Path(os.environ.get("INTELIGENCIA_OUT", HERE.parent / "corpus.d" / "99-inteligencia.json"))
RETRIEVED = "2026-11-01"
S4_57_2025 = "https://www.asambleanacional.gob.ec/es/system/files/ro_6.pdf"
S4_275_2026 = "https://www.asambleanacional.gob.ec/es/system/files/ro_27.pdf"  # same edition as the COIP part's copy
LAW = "ley-inteligencia-2025"
PENIT = "ley-penitenciaria-2026"  # key and label shared with the COIP part (60-coip), which loads first
TITLE = "LEY ORGÁNICA DE INTELIGENCIA"
END = ("Dada y suscrita en la sede de la Asamblea Nacional", "Dada en la sede de la Asamblea Nacional",
       "Dado en la sede de la Asamblea Nacional")


def base_units() -> dict:
    return D.law_units(D.paras(S4_57_2025), TITLE, 58, "Títulos y capítulos", end=END)


LAWS = {
    LAW: dict(label="Ley Orgánica de Inteligencia (2025)", kind="law", enacted="2025-06-10", published="2025-06-11",
              url=S4_57_2025,
              title="Ley Orgánica de Inteligencia (Registro Oficial, Cuarto Suplemento 57, 11-VI-2025)"),
    PENIT: dict(label="Ley Reformatoria del Sistema Penitenciario (2026)", kind="law", enacted=None,
                published="2026-04-29", url=S4_275_2026,
                title="Ley Orgánica Reformatoria para el Fortalecimiento del Sistema Penitenciario (Registro Oficial, "
                      "Cuarto Suplemento 275, 29-IV-2026)"),
}


def penitenciaria_2026(units: dict) -> dict:
    """Art. 28 of the 2026 penitentiary reform: 'En el artículo 30, agréguese el siguiente inciso final: "..."'."""
    ps = D.paras(S4_275_2026)
    i = [n for n, p in enumerate(ps) if p == "Artículo 28.- En el artículo 30, agréguese el siguiente inciso final:"]
    if len(i) != 1 or ps[i[0] - 1] != "DE LAS REFORMAS A LA LEY ORGÁNICA DE INTELIGENCIA":
        raise SystemExit("penitenciaria 2026: art. 28 anchor")
    q = ps[i[0] + 1]
    if not (q.startswith('"') and q.endswith('"') and ps[i[0] + 2] == "Capítulo VI"):
        raise SystemExit("penitenciaria 2026: art. 28 is not one quoted paragraph")
    t = units["art-030"]["text"]
    if not t.startswith("Artículo 30. Subsistema de Inteligencia Penitenciaria"):
        raise SystemExit("penitenciaria 2026: art. 30")
    new = dict(units)
    new["art-030"] = dict(units["art-030"], text=t + q[1:-1] + "\n")
    return new


STEPS = [(PENIT, "2026-04-29", penitenciaria_2026)]

DECISIONS = [
    "Ley Orgánica de Inteligencia (2025): the first version is the law as enacted (Registro Oficial Cuarto Suplemento 57, 11-VI-2025), in force on publication (its Disposición final). Units are art-NNN for arts. 1-58, disp-general-NN, disp-transitoria (única), disp-derogatoria-NN, disp-final; 'titulos' holds the Título and Capítulo headings in order. The oficio, certification and considerandos are not units.",
    "Ley Orgánica de Inteligencia (2025): the Ley Orgánica Reformatoria para el Fortalecimiento del Sistema Penitenciario (Cuarto Suplemento 275, 29-IV-2026), Capítulo V, art. 28, adds a final inciso to art. 30; the act is in force on publication (its Disposición final única), so the inciso applies from 29-IV-2026. The law key and label are shared with the COIP part, which records the same act as a reform of the COIP.",
    "Ley Orgánica de Inteligencia (2025), later amendments and rulings: the Registro Oficial's own search of edition summaries for the law's full name returns only its publication and its Reglamento General (Decreto Ejecutivo 52, Cuarto Suplemento 81, 15-VII-2025), no reform and no Corte Constitucional ruling naming it; the laws the Asamblea lists as published 2025-2026 were searched in their text layers and only the 2026 penitentiary reform amends it. A provisional suspension of articles by the Corte Constitucional changes no words and is not a version. Laws of that period printed only as page images could not be read; an amendment inside one of them would be missing here.",
    "Ley Orgánica de Inteligencia (2025), reconciliation: no consolidation posted by a public body was found. The text in force today is therefore the gazette text with the 2026 inciso added; every line of every unit was checked to occur in the gazette's text layer (the added inciso in the 2026 act's), and every paragraph of the law in the gazette to be covered by a unit.",
]
AI_USE = [
    "Ley Orgánica de Inteligencia (2025): no generative model wrote legal text. The parser (codes/inteligencia.py, with codes/discapacidad.py's shared functions) was written by an AI agent (Claude); every word is cut from the gazette PDFs' text layers. No OCR was used.",
]


def build_act() -> dict:
    units = base_units()
    versions = [{"from": "2025-06-11", "source_url": S4_57_2025, "sha256": D.sha_of(S4_57_2025), "units": units,
                 "credits": {}}]
    for law, day, edit in STEPS:
        new = edit(units)
        changed = sorted((k for k in set(units) | set(new) if units.get(k) != new.get(k)), key=D.order)
        url = LAWS[law]["url"]
        versions.append({"from": day, "source_url": url, "sha256": D.sha_of(url),
                         "changes": {k: new.get(k) for k in changed}, "credits": {k: [law] for k in changed}})
        units = new
    return {"slug": "ley-inteligencia", "short": "LOI", "title": "Ley Orgánica de Inteligencia", "url": S4_57_2025,
            "first_law": LAW, "earlier_laws": [], "versions": versions}


def laws() -> dict:
    return {k: {"label": v["label"], "title": v["title"], "kind": v["kind"], "enacted": v.get("enacted"),
                "published": v["published"], "url": v["url"], "temporary_until": None, "restores": None,
                "note": v.get("note")} for k, v in LAWS.items()}


def sources() -> list[dict]:
    return [
        {"name": "Registro Oficial del Ecuador (Ley Orgánica de Inteligencia)",
         "url": "https://www.registroficial.gob.ec", "retrieved": RETRIEVED, "requests": 1,
         "licence": "No licence stated on the site; official gazette text.",
         "notes": "Cuarto Suplemento 57, 11-VI-2025, and Cuarto Suplemento 275, 29-IV-2026 (the edition PDFs as published on the Asamblea Nacional's list of approved laws); the text is cut from their text layers."},
    ]


def main() -> None:
    act = build_act()
    part = {"laws": laws(), "acts": [act], "sources": sources(), "applies": [], "decisions": DECISIONS,
            "ai_use": AI_USE}
    data = D.write(part, OUT)
    print(f"{OUT.name}: {len(act['versions'])} versions, {len(act['versions'][0]['units'])} units, {len(data)} bytes")


if __name__ == "__main__":
    main()
