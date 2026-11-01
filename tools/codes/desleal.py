"""Write corpus.d/98-competencia-desleal.json: the Ley Orgánica de Regulación contra la Competencia Desleal (2025).

Reads only the cache. Deterministic: the same cache gives the same bytes. The part is written atomically (.tmp, then
rename).

    python -X utf8 codes/desleal.py      (DESLEAL_OUT=... to write elsewhere)

Base: Registro Oficial Tercer Suplemento 113, 29-VIII-2025 (text layer), in force on publication (its Disposición
final única). No later change found (DECISIONS).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import discapacidad as D  # noqa: E402  (shared parser and helpers)

OUT = Path(os.environ.get("DESLEAL_OUT", HERE.parent / "corpus.d" / "98-competencia-desleal.json"))
RETRIEVED = "2026-11-01"
S3_113_2025 = "https://www.asambleanacional.gob.ec/es/system/files/ro_17.pdf"
LAW = "ley-competencia-desleal-2025"
TITLE = "LEY ORGÁNICA DE REGULACIÓN CONTRA LA COMPETENCIA DESLEAL"
# literals the text layer sets inside one paragraph ("... podrán ser reclamadas por: a. Cualquier persona ...; b. ...")
# go one per line; text quoted from another law (the reformatory dispositions) stays as printed
ITEM = re.compile(r"(?:(?<=[:;.])|(?<=; y,)|(?<=; o,))(?<!^\d\.) (?=(?:[a-z][.)]|\d{1,2}\.) [A-ZÁÉÍÓÚÑ])")


def split_items(p: str) -> list[str]:
    if p.startswith('"'):
        return [p]
    return ITEM.split(p)


def base_units() -> dict:
    return D.law_units(D.paras(S3_113_2025), TITLE, 73, "Títulos, capítulos y secciones", split=split_items,
                       end=("Dado y suscrito, en la sede de la Asamblea Nacional",
                            "Dada en la sede de la Asamblea Nacional"))


LAWS = {
    LAW: dict(label="Ley Orgánica de Regulación contra la Competencia Desleal (2025)", kind="law",
              enacted="2025-08-20", published="2025-08-29", url=S3_113_2025,
              title="Ley Orgánica de Regulación contra la Competencia Desleal (Registro Oficial, Tercer Suplemento "
                    "113, 29-VIII-2025)"),
}

DECISIONS = [
    "Ley Orgánica de Regulación contra la Competencia Desleal (2025): the first and only version is the law as enacted (Registro Oficial Tercer Suplemento 113, 29-VIII-2025), in force on publication (its Disposición final única). The Asamblea approved it on 6-V-2025 and, after the President's objection, approved the changes on 20-VIII-2025; the published text is that final text. Units are art-NNN for arts. 1-73, disp-general-NN (1-3), disp-reformatoria-NN (1-2: its reforms of the Ley Orgánica de Regulación y Control del Poder de Mercado, kept as printed with the quoted text), disp-derogatoria-NN (1-2), disp-final; 'titulos' holds the Título, Capítulo and Sección headings in order, as printed ('TÍTULO 1', 'TITULO II'). The oficio, certification and considerandos are not units.",
    "Ley Orgánica de Regulación contra la Competencia Desleal (2025), text: literals and numerals set inside one paragraph ('... podrán ser reclamadas por: a. Cualquier persona ...') are split one per line, except inside quoted reform text.",
    "Ley Orgánica de Regulación contra la Competencia Desleal (2025), later amendments: none found to 1-XI-2026. The Registro Oficial's own search of edition summaries for 'Competencia Desleal' returns only the law's publication (no reform, no Corte Constitucional ruling naming it); the laws the Asamblea lists as published 2025-2026 were searched in their text layers and none amends it. Laws of that period printed only as page images could not be read; an amendment inside one of them would be missing here.",
    "Ley Orgánica de Regulación contra la Competencia Desleal (2025), reconciliation: no consolidation posted by a public body was found. The text in force today is therefore the gazette text; every line of every unit was checked to occur in the gazette's text layer, and every paragraph of the law in the gazette to be covered by a unit.",
]
AI_USE = [
    "Ley Orgánica de Regulación contra la Competencia Desleal (2025): no generative model wrote legal text. The parser (codes/desleal.py, with codes/discapacidad.py's shared functions) was written by an AI agent (Claude); every word is cut from the gazette PDF's text layer. No OCR was used.",
]


def build_act() -> dict:
    units = base_units()
    versions = [{"from": "2025-08-29", "source_url": S3_113_2025, "sha256": D.sha_of(S3_113_2025), "units": units,
                 "credits": {}}]
    return {"slug": "ley-competencia-desleal", "short": "LORCCD",
            "title": "Ley Orgánica de Regulación contra la Competencia Desleal", "url": S3_113_2025,
            "first_law": LAW, "earlier_laws": [], "versions": versions}


def laws() -> dict:
    return {k: {"label": v["label"], "title": v["title"], "kind": v["kind"], "enacted": v.get("enacted"),
                "published": v["published"], "url": v["url"], "temporary_until": None, "restores": None,
                "note": v.get("note")} for k, v in LAWS.items()}


def sources() -> list[dict]:
    return [
        {"name": "Registro Oficial del Ecuador (Ley Orgánica de Regulación contra la Competencia Desleal)",
         "url": "https://www.registroficial.gob.ec", "retrieved": RETRIEVED, "requests": 1,
         "licence": "No licence stated on the site; official gazette text.",
         "notes": "Tercer Suplemento 113, 29-VIII-2025 (the edition PDF as published on the Asamblea Nacional's list of approved laws); the text is cut from its text layer."},
    ]


def main() -> None:
    act = build_act()
    part = {"laws": laws(), "acts": [act], "sources": sources(), "applies": [], "decisions": DECISIONS,
            "ai_use": AI_USE}
    data = D.write(part, OUT)
    print(f"{OUT.name}: {len(act['versions'])} versions, {len(act['versions'][0]['units'])} units, {len(data)} bytes")


if __name__ == "__main__":
    main()
