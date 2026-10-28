"""The COIP's amending acts of 2023 to 2026 whose Registro Oficial edition has a text layer, as edit functions for
coip_replay.py (which holds their LAWS entries, in-force days and STEPS).

Each act's amending items are cut out of its own gazette edition: an item is the instruction paragraph ("Artículo 41.-
Sustitúyase el artículo 154 ...", "5. Sustitúyase el artículo 268 ...") and the payload paragraphs up to the next item.
Whole articles an act substitutes or adds are taken exactly as it prints them. A partial amendment (a numeral, an
inciso, a phrase) is applied only to a provision whose text in this record is the law (coip_replay.editable); one an
earlier, image-only reform had already amended is credited to the act as not applied.
"""
from __future__ import annotations

import re

from replay import Units  # civil/replay.py
from s107_2019 import span, unq  # coip/s107_2019.py

import coip_replay as R


# ---------------------------------------------------------------- cutting an act into items

def items(src, start: str, stop: str, item: str, numbers: range, inline: bool = False) -> dict[int, tuple[str, list[str]]]:
    """{n: (instruction, payload)} for the items numbered `numbers` between the paragraph holding `start` and the one
    holding `stop`. `item` is a regex with one group, the item's number, matched at the start of a paragraph. With
    `inline`, the payload begins inside the instruction paragraph, at its first double quote."""
    i0 = src.index(start)
    i1 = src.index(stop, src.paras[i0])
    want = list(numbers)
    pos: dict[int, int] = {}
    for i in range(i0 + 1, i1):
        m = re.match(item, src.paras[i])
        if m and want and int(m.group(1)) == want[0]:
            pos[want.pop(0)] = i
    if want:
        raise SystemExit(f"{src.url[-24:]}: items not found from {want[0]}")
    out = {}
    keys = list(pos)
    for j, n in enumerate(keys):
        a = pos[n]
        b = pos[keys[j + 1]] if j + 1 < len(keys) else i1
        ins = src.paras[a]
        payload = src.paras[a + 1:b]
        if inline and '"' in ins:
            q = ins.index('"')
            ins, payload = ins[:q].rstrip(), [ins[q:]] + payload
        out[n] = (ins, payload)
    return out


def check(ins: str, *phrases: str) -> None:
    for ph in phrases:
        if ph not in ins:
            raise SystemExit(f"instruction lacks {ph!r}: {ins[:140]!r}")


def num_key(n: str) -> str:
    """'477.10' -> 'art-477-10'; '678-A' -> 'art-678-a'; '4' -> 'art-004'."""
    m = re.fullmatch(r"(\d+)(?:[.-](\w+))?", n)
    if not m:
        raise SystemExit(f"article number {n!r}")
    return f"art-{int(m.group(1)):03d}" + (f"-{m.group(2).lower()}" if m.group(2) else "")


HEAD = re.compile(r"(?:Art\.|Artículo\.?)\s*(\d+(?:[.-]\w+)?)\s*\.?\s*-")


def whole(u: Units, n: str, payload: list[str], printed: str | None = None) -> None:
    """Article n substituted entirely by the payload (which must begin with its own heading, numbered `printed` when
    the act misprints it)."""
    new = unq(payload)
    m = HEAD.match(new[0])
    if not m or m.group(1) != (printed or n):
        raise SystemExit(f"art. {n}: payload starts {new[0][:50]!r}")
    key = num_key(n)
    u.set_unit(key, new, label=f"Art. {n}")
    R.fresh(u, key)


def add(u: Units, payload: list[str], expect: str | None = None) -> str:
    """A new article, numbered by its own heading."""
    new = unq(payload)
    m = HEAD.match(new[0])
    if not m:
        raise SystemExit(f"new article: payload starts {new[0][:50]!r}")
    n = m.group(1)
    if expect and n != expect:
        raise SystemExit(f"new article {n}, expected {expect}")
    key = num_key(n)
    if key in u.u:
        raise SystemExit(f"new article {n}: {key} exists")
    u.set_unit(key, new, label=f"Art. {n}")
    R.fresh(u, key)
    return key


def numeral(u: Units, key: str, n: int) -> tuple[int, int]:
    """Paragraph range of numeral n up to the next numeral (or the first later paragraph that is not part of it:
    an unnumbered paragraph after the last numeral is the article's next inciso)."""
    a, b = span(u, key, n)
    ps = u.paras(key)
    if b == len(ps):
        b = a + 1
    return a, b


WHOLE = re.compile(r"(?:Sustitúyase|Sustitúyese) (?:el texto del |el contenido del )?(?:el )?artículo (\d+(?:\.\d+)?)"
                   r"(?: del Código Orgánico Integral(?: Penal)?)?,? por el siguiente(?: texto)?:?$")
AFTER = re.compile(r"(?:Agréguese|Agréguense|Agrégase) (?:el siguiente artículo [\d.]+ )?a continuación del (?:nuevo )?"
                   r"artículo (\d+(?:\.\d+)?)(?: supra)?(?: del Código Orgánico Integral Penal)?(?: añadido)?(?:,| la)? "
                   r"(?:el siguiente|los siguientes artículos|el siguiente artículo)?:?$")


# ---------------------------------------------------------------- 2023: Supl. 279

def seguridad_integral_2023(u: Units) -> None:
    """Ley Orgánica Reformatoria a Varios Cuerpos Legales para el Fortalecimiento de las Capacidades Institucionales y
    la Seguridad Integral (Registro Oficial, Suplemento 279, 29-III-2023), Capítulo III, arts. 38 to 126."""
    s = R.csrc(R.S279_2023)
    P = items(s, "Capítulo III REFORMAS AL CÓDIGO ORGÁNICO INTEGRAL PENAL", "Capítulo IV REFORMAS",
              r"Artículo (\d+)\.- ", range(38, 127))
    special = {39, 40, 45, 46, 48, 59, 60, 61, 62, 63, 64, 65, 66, 67, 78, 81, 82, 84, 96, 109, 125, 126}
    for k, (ins, pay) in P.items():
        body = re.sub(r"^Artículo \d+\.- ", "", ins)
        if k in special:
            continue
        m = WHOLE.match(body)
        if m:
            whole(u, m.group(1), pay)
            continue
        m = AFTER.match(body) or re.match(r"A continuación de artículo (616) .* agréguese un artículo 616\.1 con el "
                                           r"siguiente texto:$", body) or re.match(
            r"Agréguese el siguiente artículo 552\.1 a continuación del artículo (552) del Código Orgánico Integral "
            r"Penal:$", body)
        if m:
            add(u, pay)
            continue
        raise SystemExit(f"S279 art. {k}: unhandled {body[:100]!r}")

    def ins_(k: int) -> str:
        return P[k][0]

    def pay(k: int) -> list[str]:
        return unq(P[k][1])

    # 39. art. 48 numeral 8: a phrase
    check(ins_(39), 'En el número 8 del artículo 48', 'sustitúyase la frase: "funcionaria o funcionario público" por: '
                    '"servidora o servidor público"')
    if R.editable(u, "art-048"):
        u.sub("art-048", "funcionaria o funcionario público", "servidora o servidor público", para="8. ")
    # 40. art. 47: numeral 24 after numeral 23
    check(ins_(40), "a continuación del número 23 del artículo 47")
    if R.editable(u, "art-047"):
        raise SystemExit("S279 art. 40: art. 47 is current")
    # 45. art. 219 numeral 2
    check(ins_(45), "Sustitúyase el número 2 del artículo 219")
    if R.editable(u, "art-219"):
        a, b = numeral(u, "art-219", 2)
        u.set_para("art-219", a, pay(45), count=b - a)
    # 46. art. 220 first paragraph
    check(ins_(46), "Sustitúyase el párrafo primero del artículo 220")
    if R.editable(u, "art-220"):
        new = pay(46)
        if len(new) != 1 or not new[0].startswith("Art. 220.-"):
            raise SystemExit("S279 art. 46: payload")
        u.set_para("art-220", 0, new)
    # 48. art. 260: a final paragraph
    check(ins_(48), "Agréguese un párrafo final al artículo 260")
    if R.editable(u, "art-260"):
        u.insert("art-260", u.count("art-260"), pay(48))
    # 59. art. 430.1: an inciso
    check(ins_(59), "Agréguese como inciso del artículo 430.1")
    if R.editable(u, "art-430-1"):
        raise SystemExit("S279 art. 59: art. 430.1 is current")
    # 60. art. 444 numerals 8 and 9
    check(ins_(60), "Sustitúyase los numerales 8 y 9 del artículo 444")
    if R.editable(u, "art-444"):
        new = pay(60)
        if len(new) != 2 or not (new[0].startswith("8. ") and new[1].startswith("9. ")):
            raise SystemExit("S279 art. 60: payload")
        a = u.find("art-444", "8. ")
        if not u.paras("art-444")[a + 1].startswith("9. ") or not u.paras("art-444")[a + 2].startswith("10. "):
            raise SystemExit("S279 art. 60: numerals 8, 9 are not one paragraph each")
        u.set_para("art-444", a, new, count=2)
    # 61. art. 444: numerals 15 to 17 after numeral 14
    check(ins_(61), "a continuación del numeral 14 del artículo 444")
    if R.editable(u, "art-444"):
        u.insert("art-444", u.find("art-444", "14. ") + 1, pay(61))
    # 62. art. 459 numeral 1
    check(ins_(62), "Sustitúyase el número 1 del artículo 459")
    if R.editable(u, "art-459"):
        a, b = numeral(u, "art-459", 1)
        u.set_para("art-459", a, pay(62), count=b - a)
    # 63. art. 471 first paragraph
    check(ins_(63), "Sustitúyase el párrafo primero del artículo 471")
    if R.editable(u, "art-471"):
        new = pay(63)
        if len(new) != 1 or not new[0].startswith("Art. 471.-"):
            raise SystemExit("S279 art. 63: payload")
        u.set_para("art-471", 0, new)
    # 64. art. 474 numerals 2 and 4 (the act quotes each numeral apart)
    check(ins_(64), "Sustitúyase los numerales 2 y 4 del artículo 474")
    if R.editable(u, "art-474"):
        raw = P[64][1]
        two, four = unq(raw[:1]), unq(raw[1:])
        if not (two[0].startswith("2. ") and four[0].startswith("4. ")):
            raise SystemExit("S279 art. 64: payload")
        a, b = numeral(u, "art-474", 4)
        u.set_para("art-474", a, four, count=b - a)
        a, b = numeral(u, "art-474", 2)
        u.set_para("art-474", a, two, count=b - a)
    # 65. art. 474: numeral 7 after numeral 6
    check(ins_(65), "Agréguese a continuación del texto del número 6 del artículo 474")
    if R.editable(u, "art-474"):
        a, b = numeral(u, "art-474", 6)
        u.insert("art-474", b, pay(65))
    # 66, 67. a heading after art. 477, and art. 477.1 (which the act heads 'Art. 471.1')
    check(ins_(66), "Agréguese a continuación del artículo 477", "la siguiente sección innumerada")
    check(ins_(67), "Sustitúyase el artículo 477.1")
    whole(u, "477.1", P[67][1], printed="471.1")
    R.HEADS.insert(u, pay(66)[0], before="art-477-1")
    # 78. art. 484 numerals 3 and 4
    check(ins_(78), "Sustitúyase el contenido de los números 3 y 4 del artículo 484")
    if R.editable(u, "art-484"):
        new = pay(78)
        if len(new) != 2 or not (new[0].startswith("3. ") and new[1].startswith("4. ")):
            raise SystemExit("S279 art. 78: payload")
        a = u.find("art-484", "3. ")
        if not u.paras("art-484")[a + 1].startswith("4. ") or not u.paras("art-484")[a + 2].startswith("5. "):
            raise SystemExit("S279 art. 78: numerals 3, 4")
        u.set_para("art-484", a, new, count=2)
    # 81. art. 500 first paragraph: a phrase
    check(ins_(81), 'En el primer párrafo del artículo 500', 'sustitúyase la frase: "acto informático", por la '
                    'siguiente: "dato informático"')
    if R.editable(u, "art-500"):
        u.sub("art-500", "acto informático", "dato informático", para=0)
    # 82. art. 520 numeral 3
    check(ins_(82), "Sustitúyase el número 3 del artículo 520")
    if R.editable(u, "art-520"):
        a, b = numeral(u, "art-520", 3)
        u.set_para("art-520", a, pay(82), count=b - a)
    # 84. art. 529: paragraphs added
    check(ins_(84), "Agréguese al artículo 529", "los siguientes párrafos")
    if R.editable(u, "art-529"):
        u.insert("art-529", u.count("art-529"), pay(84))
    # 96. art. 635 numeral 1
    check(ins_(96), "Sustitúyase el número 1 del artículo 635")
    if R.editable(u, "art-635"):
        a, b = numeral(u, "art-635", 1)
        u.set_para("art-635", a, pay(96), count=b - a)
    # 109. art. 718: text added
    check(ins_(109), "Agréguese en el artículo 718", "el siguiente texto")
    if R.editable(u, "art-718"):
        u.insert("art-718", u.count("art-718"), pay(109))
    # 125. art. 726 repealed
    check(ins_(125), "Deróguese el artículo 726")
    u.remove("art-726")
    # 126. Disposición general novena
    check(ins_(126), "Agréguese como DISPOSICIÓN GENERAL NOVENA")
    new = pay(126)
    if not new[0].startswith("DISPOSICIÓN GENERAL NOVENA.-"):
        raise SystemExit("S279 art. 126: payload")
    u.set_unit("disp-general-09", new, label="Disposición general novena")
    u.u["disp-general-09"]["kind"] = "general"
    R.fresh(u, "disp-general-09")
