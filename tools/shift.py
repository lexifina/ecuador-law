"""Shifted-font text layers: some Registro Oficial editions (2025 on) set a few literal markers ("a)", "1.") and
spaces in a font whose text layer holds each character 29 code points lower ("D\\x0c" for "a)", "\\x14\\x11" for
"1.", "\\x03" for a space). Such a span is set wholly in that font and always holds a control character; adding 29 to
each of its characters gives the printed text back. This is a fixed character offset of the PDF's own text layer,
not OCR: nothing is read off page images. Spans of other fonts are untouched, so pages without such spans read
exactly as rotext/pua read them.

    shift.paragraphs(path)      pua.paragraphs(path) with shifted spans decoded first
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pua  # noqa: E402

CTRL = re.compile(r"[\x01-\x1f]")
OK = re.compile(r"^[\x01-\x5f]+$")  # every character of a shifted span lies below '`' (+29 stays within ASCII)


def decode_span(t: str) -> str:
    return "".join(chr(ord(c) + 29) for c in t)


def _fixed_blocks(page, get_text) -> list:
    """page.get_text('blocks') with every shifted span decoded (blocks without one are returned unchanged)."""
    blocks = get_text(page, "blocks", sort=False)
    if not any(CTRL.search(b[4]) for b in blocks if b[6] == 0):
        return blocks
    lines: list[tuple[str, str]] = []
    for b in get_text(page, "dict", sort=False)["blocks"]:
        for ln in b.get("lines", []):
            spans = [s["text"] for s in ln["spans"]]
            if any(CTRL.search(s) and OK.match(s.replace("\n", "")) for s in spans):
                raw = "".join(spans)
                fixed = "".join(decode_span(s) if CTRL.search(s) and OK.match(s) else s for s in spans)
                lines.append((raw, fixed))
    out = []
    for b in blocks:
        text = b[4]
        if b[6] == 0 and CTRL.search(text):
            for raw, fixed in lines:
                if raw and raw in text:
                    text = text.replace(raw, fixed)
        out.append((*b[:4], text, *b[5:]))
    return out


def paragraphs(path, **kw) -> list[str]:
    """pua.paragraphs with shifted-font spans decoded at the span level."""
    import fitz
    orig = fitz.Page.get_text

    def get_text(self, option="text", *a, **k):
        if option == "blocks":
            return _fixed_blocks(self, orig)
        return orig(self, option, *a, **k)
    fitz.Page.get_text = get_text
    try:
        return pua.paragraphs(path, **kw)
    finally:
        fitz.Page.get_text = orig
