"""Turn a cached Registro Oficial PDF into paragraphs.

The Registro Oficial is set in two justified columns. pymupdf gives one text
block per column, in reading order. Paragraphs are separated by whitespace-only
lines; a paragraph that runs over a column or page break is joined back when the
earlier part has no closing punctuation. Page headers ("Registro Oficial Nº 449
-- Lunes 20 de Octubre del 2008 -- 8") are dropped.
"""
from __future__ import annotations

import re
import unicodedata

import fitz  # pymupdf

HEADER = re.compile(
    r"^\s*(\d+\s*-+\s*)?(Tercer\s+|Segundo\s+|Cuarto\s+|Quinto\s+)?(Suplemento\s+(del\s+)?|Edici[oó]n\s+\w+\s+(del\s+)?)?"
    r"Registro\s+Oficial\s+(N[º°o]\.?|No\.?)\s*\d+.*\d{4}\s*(-+\s*\d+\s*)?$",
    re.I,
)
STRUCT = re.compile(
    r"^(Art\.\s*\d+|Art[ií]culo\s+\d+|\d+\.\s|[A-ZÁÉÍÓÚ]{4,}[A-ZÁÉÍÓÚ]*\.-|T[IÍ]TULO\s|Cap[ií]tulo\s|CAP[IÍ]TULO\s|Secci[oó]n\s|SECCI[OÓ]N\s|DISPOSICI)"
)
HEADING = re.compile(r"^(T[IÍ]TULO\s|Cap[ií]tulo\s|CAP[IÍ]TULO\s|Secci[oó]n\s|SECCI[OÓ]N\s|DISPOSICI|R[EÉ]GIMEN DE TRANSICI|PRE[AÁ]MBULO)")
ART_START = re.compile(r"^Art\.\s*-?\s*\d+\s*\.?\s*-")
HEAD_LINE = re.compile(r"^(T[IÍ]TULO\s+[IVXL]+|Cap[ií]tulo\s+\w+|CAP[IÍ]TULO\s+[IVXL]+|Secci[oó]n\s+\w+)$")
ITEM_START = re.compile(r"^\d{1,2}\.\s+\S")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u00a0", " ").replace("\u00ad", "")
    for a in "\u201c\u201d\u201e\u00ab\u00bb\u2033":
        s = s.replace(a, '"')
    for a in "\u2018\u2019\u201a\u2032\u00b4":
        s = s.replace(a, "'")
    for a in "\u2013\u2014\u2012\u2212":
        s = s.replace(a, "-")
    s = s.replace("\u2026", "...")
    return re.sub(r"[ \t]+", " ", s).strip()


def join_lines(lines: list[str]) -> str:
    out = ""
    for ln in lines:
        ln = norm(ln)
        if not ln:
            continue
        if not out:
            out = ln
        elif re.search(r"[A-Za-zñÑáéíóúÁÉÍÓÚ]-$", out) and re.match(r"[a-zñáéíóú]", ln):
            out += ln  # word broken at a line end: keep the printed hyphen, no space
        else:
            out += " " + ln
    return re.sub(r" {2,}", " ", out).strip()


def chunks(pdf_path, first_page: int = 0, last_page: int | None = None) -> list[list[list[str]]]:
    """Per text block (column), the list of paragraphs (each a list of raw lines)."""
    doc = fitz.open(pdf_path)
    out = []
    last = len(doc) if last_page is None else last_page
    for pn in range(first_page, last):
        for b in doc[pn].get_text("blocks", sort=False):
            if b[6] != 0:
                continue
            paras: list[list[str]] = []
            cur: list[str] = []
            for raw in b[4].split("\n"):
                if HEADER.match(norm(raw)):
                    continue
                if not raw.strip():
                    if cur:
                        paras.append(cur)
                        cur = []
                    continue
                n = norm(raw)
                prev = norm(cur[-1]) if cur else ""
                if cur and (ART_START.match(n) or HEAD_LINE.match(n) or (ITEM_START.match(n) and re.search(r"[.;:]$", prev))):
                    paras.append(cur)
                    cur = []
                cur.append(raw)
            if cur:
                paras.append(cur)
            if paras:
                out.append(paras)
    return out


def paragraphs(pdf_path, first_page: int = 0, last_page: int | None = None) -> list[str]:
    """Paragraph strings in reading order, with paragraphs re-joined across column/page breaks."""
    out: list[str] = []
    for paras in chunks(pdf_path, first_page, last_page):
        for i, p in enumerate(paras):
            text = join_lines(p)
            if not text:
                continue
            if i == 0 and out:
                prev = out[-1]
                cont = not re.search(r"[.:;]\"?$", prev) and not STRUCT.match(text) and not HEADING.match(prev)
                if re.match(r"[a-zñáéíóú]", text) and not HEADING.match(prev):
                    cont = True
                if cont:
                    out[-1] = join_lines([prev, text])
                    continue
            out.append(text)
    return out
