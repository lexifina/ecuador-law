"""The Constitution's amending acts, applied in order to the 2008 text.

Each entry names the act (a key in LAWS), its Registro Oficial PDF, its in-force
day and, per provision, where the new text is printed in that PDF. New text is
always taken from the cached PDF itself, never typed here.
"""
from __future__ import annotations

DECISIONS: list[str] = []


def apply_all(versions: list[dict], laws: dict) -> None:
    return None
