"""The COIP's amending acts, replayed in order of entry into force on the Code as enacted (RO Supl. 180, 2014).

Every act with a text layer in the Registro Oficial is a function that edits a copy of the previous version's units
(civil/replay.py's Units). New wording is never typed here as such: it is cut out of the act's own cached gazette PDF
(civil/replay.py's Src) after an anchor phrase, and every short phrase an act inserts is checked to occur, word for
word, in that act's PDF. Changed units are credited to the act automatically.

Acts whose gazette edition has no text layer are NOT applied (no OCR, by the user's decision): they get a version of
their own that changes no words, credited to the provisions an editorial index names, with a note saying so.

Anachronism rule: a version in force on day D may only carry wording from acts published on or before D, and every
act is applied on its own in-force day, never earlier. `check_anachronism` enforces it on the finished versions.
"""
from __future__ import annotations

import datetime as dt
import json
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "civil"))
import fetch  # noqa: E402
import rotext  # noqa: E402
from replay import Src, Units, unquote  # noqa: E402  (civil/replay.py: gazette cutting and unit edits)

H = "http://esacc.corteconstitucional.gob.ec/storage/api/v1/10_DWL_FL/"


def ro(b64: str) -> str:
    return H + b64


_EDITIONS = json.loads((HERE / "editions.json").read_text(encoding="utf-8"))


def ed(name: str, title: str) -> str:
    """PDF URL of one edition found by coip/find_editions.py ('s598-2015', 'Tercer Suplemento')."""
    hits = [e["pdf"] for e in _EDITIONS[name] if e["title"] == title]
    if len(hits) != 1:
        raise SystemExit(f"edition {name} {title!r}: {len(hits)} matches")
    return hits[0]


S180_2014 = ro("eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiMjkwYzMxODUtNTY0OC00MzNjLTk1ZDEtZDg0NjY1NDc5NWI0LnBkZiJ9")
S2_332_2014 = ro("eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiNDIwM2NhZGUtMzY2Yy00ZWIzLTgzZmQtZDI5Yzg3NGY3ZjU0LnBkZiJ9")
S3_598_2015 = ed("s598-2015", "Tercer Suplemento")
S615_2015 = ed("s615-2015", "Primer Suplemento")
S711_2016 = ed("s711-2016", "Primer Suplemento")
S2_802_2016 = ed("s802-2016", "Segundo Suplemento")
S2_150_2017 = ed("s150-2017", "Segundo Suplemento")
S133_2017 = ro("eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiYTg1ZGM4YzMtM2U4ZS00OGI5LWI1YjEtZGJmZWQzZGJhNWE0LnBkZiJ9")
S180_2018 = ro("eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiOGMwNTA4ZmMtYTQ0NS00MWRlLTk3OWEtZmZiMjY5NGMyNWQ0LnBkZiJ9")
S175_2018 = ed("s175-2018", "Primer Suplemento")
S478_2019 = ed("s478-2019", "Primer Suplemento")
S481_2019 = ed("s481-2019", "Primer Suplemento")
EC90_2019 = ed("ec90-2019", "Ediciones Constitucionales")
EC6_2019 = ed("ec6-2019", "Ediciones Constitucionales")
EC21_2019 = _EDITIONS["ec21-2019"][0]["pdf"]
S107_2019 = ed("s107-2019", "Primer Suplemento")


def plazo_days(published: str, days: int) -> str:
    """In force after a plazo of `days` days counted from publication: Código Civil art. 33 (plazos are complete days
    and run to midnight of the last day), the publication day not counted, so the act binds from the next day."""
    return (dt.date.fromisoformat(published) + dt.timedelta(days=days + 1)).isoformat()


def plazo_months(published: str, months: int) -> str:
    """Código Civil art. 33: a plazo of months ends on the same date of the later month."""
    d = dt.date.fromisoformat(published)
    m = d.month - 1 + months
    return dt.date(d.year + m // 12, m % 12 + 1, d.day).isoformat()


# ---------------------------------------------------------------- cutting quoted text out of a gazette edition

def qfrom(src: Src, anchor: str, after: str | None = None) -> list[str]:
    """The quotation that opens right after `anchor` (in the same paragraph or the next one), as paragraphs.

    The quotation closes at the first double quote that leaves an even count of quotes and is followed by the end
    of a paragraph, a stop/comma/semicolon, or the act's next lettered or numbered item ('" b) Agregar ...')."""
    i = src.index(anchor, after)
    p = src.paras[i]
    head = p[p.index(anchor) + len(anchor):]
    text = "\n".join([head] + src.paras[i + 1:i + 80])
    start = text.find('"')
    if start < 0 or text[:start].strip():
        raise SystemExit(f"no quotation right after {anchor!r}: {text[:60]!r}")
    count = 0
    for m in re.finditer('"', text):
        if m.start() < start:
            continue
        count += 1
        if count % 2 or m.start() == start:
            continue
        rest = text[m.end():]
        if re.match(r"[.,;]?\s*(\n|$|[a-z]\)\s|\d+\.-?\s|[A-ZÁÉÍÓÚ])", rest):
            stop = rest[:1] if rest[:1] in ".,;" else ""
            inner = text[start:m.end()] + stop
            return unquote(inner.split("\n"))
    raise SystemExit(f"quotation after {anchor!r} does not close")


def paras_between(src: Src, first: str, last: str, after: str | None = None) -> list[str]:
    """Whole paragraphs from the one starting with `first` to the one containing `last` (unquoted text an act adds)."""
    i = src.index(first, after)
    if not src.paras[i].startswith(first):
        raise SystemExit(f"{first!r} does not start its paragraph")
    j = src.index(last, src.paras[i]) if last not in src.paras[i] else i
    return src.paras[i:j + 1]


def phrase(src: Src, text: str) -> str:
    """A short phrase an act inserts, checked to occur word for word in the act's PDF."""
    src.check(text)
    return text


# ---------------------------------------------------------------- the acts (text layer available)

def comf_2014(u: Units) -> None:
    """Código Orgánico Monetario y Financiero (Segundo Supl. 332, 12-IX-2014), Disposición reformatoria trigésima
    séptima: art. 278, fourth inciso replaced (by two paragraphs); art. 557 num. 3, a sentence added after 'para el
    efecto.'."""
    s = Src(S2_332_2014)
    new = qfrom(s, "sustitúyase el cuarto inciso por el siguiente:")
    if len(new) != 2:
        raise SystemExit(f"COMF 278: {len(new)} paragraphs")
    u.set_para("art-278", 3, new)
    add = qfrom(s, 'numeral 3, después de "para el efecto." agréguese:')[0]
    u.sub("art-557", "para el efecto.", "para el efecto. " + add, para="3. ")


def reformatoria_coip_2015(u: Units) -> None:
    """Ley Orgánica Reformatoria del Código Orgánico Integral Penal (Tercer Supl. 598, 30-IX-2015), arts. 1-13; in
    force on publication (its Disposición final)."""
    s = Src(S3_598_2015)
    # 1. art. 19: second and third paragraphs removed
    s.check("En el artículo 19, elimínense los párrafos segundo y tercero.")
    ps = u.paras("art-019")
    u.put("art-019", ps[:1] + ps[3:])
    # 2. art. 186, fourth paragraph (numerals are not counted as paragraphs): 'privados,' after 'fondos'
    s.check('En el párrafo cuarto del artículo 186, después de la palabra "fondos", poner la palabra "privados,".')
    u.sub("art-186", "fondos públicos", "fondos privados, públicos", para="La estafa cometida")
    # 3. new article 208 A after art. 208
    new = qfrom(s, "luego del artículo 208, agréguese el siguiente artículo:")
    u.set_unit("art-208-a", new, label="Art. 208 A")
    # 4. art. 278, fourth paragraph: 'y vigilancia' after 'consejo de administración' (the paragraph, as replaced by
    #    the COMF in 2014, reads 'consejos de administración'; see decisions)
    s.check('En el párrafo cuarto del artículo 278, después de la frase "consejo de administración", agregar las '
            'palabras "y vigilancia".')
    u.sub("art-278", "consejos de administración", "consejos de administración y vigilancia", para=3)
    # 5. art. 298, penultimate paragraph: 'prejuicio' -> 'perjuicio'
    s.check('En el párrafo penúltimo del artículo 298, sustituir la palabra "prejuicio" por "perjuicio".')
    n = len(u.paras("art-298"))
    u.sub("art-298", "prejuicio", "perjuicio", para=n - 2)
    # 6. art. 380: a paragraph after the fourth
    new = paras_between(s, "Si la persona se encontrare en estado de embriaguez", "de treinta a cuarenta y cinco días.")
    u.insert("art-380", 4, new)
    # 7. art. 415, numeral 4 replaced
    u.set_para("art-415", u.find("art-415", "4. "), qfrom(s, "En el artículo 415, sustitúyase el numeral 4 por el siguiente:"))
    # 8. art. 473, second paragraph replaced
    u.set_para("art-473", 1, qfrom(s, "En el artículo 473, sustitúyase el párrafo segundo por:"))
    # 9. art. 581, last paragraph: the final stop becomes ', cuando el objeto de la infracción sea recursos públicos.'
    add = phrase(s, ", cuando el objeto de la infracción sea recursos públicos.")
    ps = u.paras("art-581")
    if not ps[-1].endswith("."):
        raise SystemExit("581: last paragraph has no final stop")
    ps[-1] = ps[-1][:-1] + add
    u.put("art-581", ps)
    # 10. art. 640, numeral 2, second paragraph replaced
    u.set_para("art-640", u.find("art-640", "2. ") + 1,
               qfrom(s, "Sustitúyase el párrafo segundo del numeral 2 del artículo 640 por el siguiente texto:"))
    # 11. art. 643, numeral 14 removed
    s.check("Elimínese el numeral 14 del artículo 643.")
    u.delete_para("art-643", "14. ")
    # 12. art. 663, numeral 2 replaced
    u.set_para("art-663", u.find("art-663", "2. "),
               qfrom(s, "Sustitúyase el numeral 2 del artículo 663 por el siguiente texto:"))
    # 13. Disposición reformatoria duodécima: 'plazo' -> 'término'
    s.check('En la Disposición Reformatoria Décimo Segunda, sustitúyase la palabra "plazo" por "término".')
    u.sub("disp-reformatoria-12", "plazo", "término")


def drogas_2015_a(u: Units) -> None:
    """Ley Orgánica de Prevención Integral del Fenómeno Socio Económico de las Drogas (Supl. 615, 26-X-2015),
    Disposición reformatoria primera, which its Disposición final applies from publication: arts. 220, 474, 557."""
    s = Src(S615_2015)
    p = s.paras[s.index("1.- En el número 1 del artículo 220, sustitúyanse los literales a) y b) por los siguientes:")]
    rest = p.split("por los siguientes: ", 1)[1]
    a, b = rest.split(" b) ", 1)
    if not a.startswith("a) "):
        raise SystemExit("220: literals not found")
    u.set_para("art-220", u.find("art-220", "a) "), [a.strip()], count=2)
    u.insert("art-220", u.find("art-220", "a) ") + 1, ["b) " + b.strip()])
    old = "al organismo competente en materia de sustancias catalogadas sujetas a fiscalización"
    new = phrase(s, "a la institución encargada de la administración y gestión inmobiliaria del Estado")
    s.check("En el número seis del artículo 474, sustitúyase la expresión")
    u.sub("art-474", old, new, para="6. ")
    s.check("En el inciso segundo, del número uno del artículo 557, sustitúyase la expresión")
    u.sub("art-557", old, new, para=u.find("art-557", "1. ") + 1)


def drogas_2015_b(u: Units) -> None:
    """The same law, Disposición derogatoria cuarta, in force with the rest of the law ninety days after publication:
    the Code's Disposición reformatoria décimo primera is repealed."""
    s = Src(S615_2015)
    s.check("Derógase la disposición reformatoria décimo primera del Código Orgánico Integral Penal")
    u.remove("disp-reformatoria-11")


def tierras_2016(u: Units) -> None:
    """Ley Orgánica de Tierras Rurales y Territorios Ancestrales (Supl. 711, 14-III-2016), Disposición reformatoria
    quinta: a numeral 7 after numeral 6 of art. 557. The law sets no vigencia, so it binds from publication."""
    s = Src(S711_2016)
    new = qfrom(s, "En el artículo 557 del Código Orgánico Integral Penal, incorpórese después del numeral sexto uno "
                   "que diga:")
    u.insert("art-557", u.find("art-557", "6. ") + 1, new)


def lavado_2016(u: Units) -> None:
    """Ley Orgánica de Prevención, Detección y Erradicación del Delito de Lavado de Activos y del Financiamiento de
    Delitos (Segundo Supl. 802, 21-VII-2016), Disposición reformatoria 1: art. 298. In force on publication."""
    s = Src(S2_802_2016)
    a = "Refórmese el artículo 298 del Código Orgánico Integral Penal de la siguiente manera: a) Sustituir el primer inciso por el siguiente:"
    first = qfrom(s, a)
    ps = u.paras("art-298")
    head = re.match(r"(Artículo 298\.- Defraudación tributaria\.- )", ps[0]).group(1)
    ps[0] = head + first[0]
    u.put("art-298", ps)
    num20 = qfrom(s, "b) Agregar el siguiente numeral a continuación del numeral 19:")
    u.insert("art-298", u.find("art-298", "19. ") + 1, num20)
    s.check('c) En el quinto inciso posterior al numeral 19, sustitúyase "18 y 19" por lo siguiente "18, 19 y 20".')
    u.sub("art-298", "18 y 19", "18, 19 y 20", para="En el caso de los numerales 18 y 19")
    new = qfrom(s, "d) Sustitúyase el antepenúltimo inciso por el siguiente:")
    n = len(u.paras("art-298"))
    u.set_para("art-298", n - 3, new)


def clean_src(url: str) -> Src:
    """Like Src, but skipping stray text fragments laid over the real text blocks (rotext drop_overlaps); used only
    for the editions whose pages carry them (see decisions)."""
    s = object.__new__(Src)
    s.url = url
    s.paras = rotext.paragraphs(fetch.cached(url), drop_overlaps=True)
    s.flat = re.sub(r"\s+", " ", "\n".join(s.paras))
    return s


def open_quote(src: Src, anchor: str, until: str) -> list[str]:
    """A quotation the act opens after `anchor` and never closes: it runs to the paragraph before the one starting
    with `until` (the act's next provision). A closing quote, if printed at the end, is dropped."""
    i = src.index(anchor)
    p = src.paras[i]
    head = p[p.index(anchor) + len(anchor):].strip()
    j = src.index(until, src.paras[i])
    if not src.paras[j].startswith(until):
        raise SystemExit(f"{until!r} does not start its paragraph")
    block = ([head] if head else []) + src.paras[i + 1:j]
    if not block or not block[0].startswith('"'):
        raise SystemExit(f"no opening quote after {anchor!r}")
    block[0] = block[0][1:].strip()
    block[-1] = re.sub(r'"\s*([.,;]?)$', r"\1", block[-1]).rstrip()
    return block


def quoted_para(src: Src, start: str, after: str | None = None) -> list[str]:
    """The single quoted paragraph beginning with '"' + start (the first one after the paragraph holding `after`)."""
    i0 = src.index(after) + 1 if after else 0
    hits = [p for p in src.paras[i0:] if p.startswith('"' + start)]
    if after and hits:
        hits = hits[:1]
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} quoted paragraphs start with {start!r}")
    return unquote([hits[0]])


def violencia_mujeres_2018(u: Units) -> None:
    """Ley Orgánica Integral para Prevenir y Erradicar la Violencia contra las Mujeres (Supl. 175, 5-II-2018),
    Disposiciones reformatorias cuarta to séptima and décima; in force on publication (its Disposición final). Its
    quotations open and are never closed; each runs to the next disposición."""
    s = clean_src(S175_2018)
    u.set_unit("art-558-1", open_quote(s, "Agrégase, a continuación del artículo 558 del Código Orgánico Integral Penal, "
                                          "el siguiente artículo:", "QUINTA.-"), label="Art. 558.1")
    u.set_unit("art-078-1", open_quote(s, "A continuación del artículo 78 del Código Orgánico Integral Penal, "
                                          "incorpórase el siguiente artículo:", "SEXTA.-"), label="Art. 78.1")
    u.set_unit("art-157", open_quote(s, "Sustitúyase el artículo 157 del Código Orgánico Integral Penal, por el "
                                        "siguiente:", "SÉPTIMA.-"))
    u.set_unit("art-159", open_quote(s, "Refórmase el artículo 159 del Código Orgánico Integral Penal por el "
                                        "siguiente texto:", "OCTAVA.-"))
    u.set_unit("art-570", open_quote(s, "Refórmase el artículo 570 del Código Orgánico Integral Penal por el "
                                        "siguiente:", "DÉCIMA PRIMERA.-"))


def referendo_2018(u: Units) -> None:
    """Referéndum y consulta popular of 4 February 2018, questions 1 and 4: the annexes' reforms of the COIP, as put
    to the vote by Decreto Ejecutivo 229 (Supl. 133, 4-XII-2017); in force on the publication of the CNE's results
    (Supl. 180, 14-II-2018), as for the Constitution's amendments of the same vote."""
    s = clean_src(S133_2017)
    s.check("Agréguese el número 14 al artículo 60 del Código Orgánico Integral Penal, que disponga:")
    u.insert("art-060", u.find("art-060", "13. ") + 1, quoted_para(s, "14. Inhabilitación para contratar"))
    s.check("Agréguese como segundo inciso en el artículo 68 del Código Orgánico Integral Penal, el siguiente:")
    u.insert("art-068", 1, quoted_para(s, "En el caso de los delitos de peculado"))
    s.check("En el artículo 77 del Código Orgánico Integral Penal incorpórese el siguiente inciso final:")
    u.insert("art-077", u.count("art-077"), quoted_para(s, "Las personas condenadas con sentencia ejecutoriada"))
    pj = "En caso de determinarse responsabilidad de la persona jurídica será sancionada"
    a280 = "En el artículo 280 del Código Orgánico Integral Penal añádase el siguiente inciso final:"
    u.insert("art-280", u.count("art-280"), quoted_para(s, pj, after=a280))
    a285 = "En el artículo 285 del Código Orgánico Integral Penal incorpórese como tercer inciso, el siguiente:"
    u.insert("art-285", 2, quoted_para(s, pj, after=a285))
    s.check("En el artículo 289 del Código Orgánico Integral Penal incorpórese como segundo inciso, el siguiente:")
    u.insert("art-289", 1, quoted_para(s, "En caso de establecerse responsabilidad de personas jurídicas"))
    s.check("Sustitúyase el numeral 4 del artículo 16 del Código Orgánico Integral Penal por el siguiente texto:")
    u.set_para("art-016", u.find("art-016", "4. "), ["4. " + quoted_para(s, "Las infracciones de agresión a un Estado")[0]])
    s.check("Sustitúyase el inciso final del artículo 75 del Código Orgánico Integral Penal por el siguiente texto:")
    u.set_para("art-075", u.count("art-075") - 1, quoted_para(s, "No prescriben las penas determinadas"))


def deporte_2019(u: Units) -> None:
    """Ley Orgánica de Prevención y Sanción de la Violencia en el Deporte (Supl. 478, 30-IV-2019), Disposición
    reformatoria primera: art. 397 replaced (unquoted, up to the next disposición). No vigencia clause: in force on
    publication (Código Civil art. 6)."""
    s = Src(S478_2019)
    i = s.index("PRIMERA.- Sustitúyase el artículo 397 por el siguiente texto:")
    j = s.index("DISPOSICIONES TRANSITORIAS", s.paras[i])
    new = s.paras[i + 1:j]
    if not new[0].startswith("Artículo 397.-"):
        raise SystemExit("397: replacement not found")
    u.set_unit("art-397", new)


def defensoria_2019(u: Units) -> None:
    """Ley Orgánica de la Defensoría del Pueblo (Supl. 481, 6-V-2019), Disposiciones reformatorias séptima (art. 675,
    first inciso) and octava (a new Disposición general); in force on publication (its Disposición final)."""
    s = Src(S481_2019)
    new = open_quote(s, "Refórmese el inciso primero del artículo 675 del Código Integral Penal de la siguiente manera:",
                     "OCTAVA.-")
    if len(new) != 1 or not new[0].startswith("Art. 675.- Directorio.-"):
        raise SystemExit("675: unexpected replacement")
    ps = u.paras("art-675")
    ps[0] = new[0]
    u.put("art-675", ps)
    i = s.index("Agrégase una Disposición General al Código Orgánico Integral Penal, que dicte:")
    j = s.index("Durante las visitas, el Mecanismo Nacional", s.paras[i])
    block = s.paras[i + 1:j + 1]
    u.set_unit("disp-general-05", unquote(block), label="Disposición general (quinta)")
    u.u["disp-general-05"]["kind"] = "general"


class Heads:
    """The 'titulos' unit as [heading, first unit after it] pairs, so a heading can be inserted before an article."""

    def __init__(self) -> None:
        import coip_base
        self.lines = [list(h) for h in coip_base.HEAD_NEXT]

    def _write(self, u: Units) -> None:
        u.u["titulos"]["text"] = "".join(h[0] + "\n" for h in self.lines)

    def rename(self, u: Units, old: str, new: str) -> None:
        hits = [h for h in self.lines if h[0] == old]
        if len(hits) != 1:
            raise SystemExit(f"heading {old!r}: {len(hits)} matches")
        hits[0][0] = new
        self._write(u)

    def insert(self, u: Units, text: str, before: str) -> None:
        pos = next((i for i, h in enumerate(self.lines) if order(h[1]) > order(before)), len(self.lines))
        self.lines.insert(pos, [text, before])
        self._write(u)


HEADS: Heads | None = None


def reformatoria_coip_2019(u: Units) -> None:
    """Ley Orgánica Reformatoria al Código Orgánico Integral Penal (Supl. 107, 24-XII-2019), arts. 1-121; in force
    180 days after publication (its Disposición final). See coip/s107_2019.py."""
    import s107_2019
    s107_2019.apply(u, clean_src(S107_2019), HEADS)


def order(key: str) -> tuple:
    m = re.match(r"art-(\d{3})(?:-(\w+))?$", key)
    if m:
        return (1, int(m.group(1)), m.group(2) or "")
    for i, p in enumerate(("disp-general", "disp-transitoria", "disp-reformatoria", "disp-derogatoria", "disp-final",
                           "titulos")):
        if key.startswith(p):
            return (2 + i, 0, key)
    return (9, 0, key)


def sha_of(url: str) -> str:
    return hashlib.sha256(fetch.cached(url).read_bytes()).hexdigest()


IMAGE_ONLY = ("NOT APPLIED here: the Registro Oficial edition that publishes it is page images without a text layer, "
              "and this repository does not OCR. Its wording is missing from the files named in this commit; they "
              "keep the earlier text (provisions named from the editorial indexes: Ediciones Legales 2021, Lexis 2023).")

LAWS: dict[str, dict] = {
    "comf-2014": dict(label="Código Orgánico Monetario y Financiero (2014)", kind="law", enacted="2014-07-24",
                      published="2014-09-12", url=S2_332_2014,
                      title="Código Orgánico Monetario y Financiero, Disposición reformatoria trigésima séptima "
                            "(Registro Oficial, Segundo Suplemento 332, 12-IX-2014)"),
    "reformatoria-coip-2015": dict(label="Ley Orgánica Reformatoria del COIP (2015)", kind="law",
                                   enacted="2015-09-24", published="2015-09-30", url=S3_598_2015,
                                   title="Ley Orgánica Reformatoria del Código Orgánico Integral Penal (Registro "
                                         "Oficial, Tercer Suplemento 598, 30-IX-2015)"),
    "ley-drogas-2015": dict(label="Ley Orgánica de Drogas (2015)", kind="law", enacted="2015-10-01",
                            published="2015-10-26", url=S615_2015,
                            title="Ley Orgánica de Prevención Integral del Fenómeno Socio Económico de las Drogas y de "
                                  "Regulación y Control del Uso de Sustancias Catalogadas Sujetas a Fiscalización "
                                  "(Registro Oficial, Suplemento 615, 26-X-2015)"),
    "ley-tierras-2016": dict(label="Ley Orgánica de Tierras Rurales (2016)", kind="law", enacted="2016-03-03",
                             published="2016-03-14", url=S711_2016,
                             title="Ley Orgánica de Tierras Rurales y Territorios Ancestrales (Registro Oficial, "
                                   "Suplemento 711, 14-III-2016)"),
    "ley-lavado-2016": dict(label="Ley Orgánica contra el Lavado de Activos (2016)", kind="law", enacted="2016-07-13",
                            published="2016-07-21", url=S2_802_2016,
                            title="Ley Orgánica de Prevención, Detección y Erradicación del Delito de Lavado de Activos "
                                  "y del Financiamiento de Delitos (Registro Oficial, Segundo Suplemento 802, "
                                  "21-VII-2016)"),
    "ley-reactivacion-2017": dict(label="Ley Orgánica para la Reactivación de la Economía (2017)", kind="law",
                                  published="2017-12-29", url=S2_150_2017, note=IMAGE_ONLY,
                                  title="Ley Orgánica para la Reactivación de la Economía, Fortalecimiento de la "
                                        "Dolarización y Modernización de la Gestión Financiera (Registro Oficial, "
                                        "Segundo Suplemento 150, 29-XII-2017): art. 299, first inciso. NOT APPLIED "
                                        "(image-only edition)"),
    "ley-violencia-mujeres-2018": dict(label="Ley Orgánica contra la Violencia hacia las Mujeres (2018)", kind="law",
                                       enacted="2018-01-23", published="2018-02-05", url=S175_2018,
                                       title="Ley Orgánica Integral para Prevenir y Erradicar la Violencia contra las "
                                             "Mujeres (Registro Oficial, Suplemento 175, 5-II-2018)"),
    "referendo-2018": dict(label="Referéndum de 2018", kind="referendum", enacted="2018-02-04", published="2018-02-14",
                           url=S180_2018,
                           title="Referéndum y consulta popular de 4 de febrero de 2018, preguntas 1 y 4 (anexos del "
                                 "Decreto Ejecutivo 229, RO Supl. 133 de 4-XII-2017; resultados del CNE, RO Supl. 180 "
                                 "de 14-II-2018)"),
    "ley-deporte-2019": dict(label="Ley Orgánica contra la Violencia en el Deporte (2019)", kind="law",
                             enacted="2019-03-27", published="2019-04-30", url=S478_2019,
                             title="Ley Orgánica de Prevención y Sanción de la Violencia en el Deporte (Registro "
                                   "Oficial, Suplemento 478, 30-IV-2019)"),
    "ley-defensoria-2019": dict(label="Ley Orgánica de la Defensoría del Pueblo (2019)", kind="law",
                                published="2019-05-06", url=S481_2019,
                                title="Ley Orgánica de la Defensoría del Pueblo (Registro Oficial, Suplemento 481, "
                                      "6-V-2019)"),
    "cc-ec90-2019": dict(label="Corte Constitucional, Edición Constitucional 90 (2019)", kind="court",
                         published="2019-06-03", url=EC90_2019, note=IMAGE_ONLY,
                         title="Corte Constitucional, sentencia publicada en la Edición Constitucional 90 (3-VI-2019) "
                               "que declara la inconstitucionalidad parcial del art. 202. NOT APPLIED (image-only "
                               "edition)"),
    "cc-ec6-2019": dict(label="Corte Constitucional, sentencia 5-13-IN/19", kind="court", published="2019-08-15",
                        url=EC6_2019, note=IMAGE_ONLY,
                        title="Corte Constitucional, sentencia 5-13-IN/19 (Edición Constitucional 6, 15-VIII-2019): "
                              "inconstitucionalidad del último inciso del art. 581. NOT APPLIED (image-only edition)"),
    "cc-ec21-2019": dict(label="Corte Constitucional, Edición Constitucional 21 (2019)", kind="court",
                         published="2019-11-13", url=EC21_2019, note=IMAGE_ONLY,
                         title="Corte Constitucional, sentencia publicada en la Edición Constitucional 21 (13-XI-2019): "
                               "constitucionalidad condicionada aditiva del art. 653. NOT APPLIED (image-only edition)"),
    "reformatoria-coip-2019": dict(label="Ley Orgánica Reformatoria del COIP (2019)", kind="law", enacted="2019-12-17",
                                   published="2019-12-24", url=S107_2019,
                                   title="Ley Orgánica Reformatoria al Código Orgánico Integral Penal (Registro "
                                         "Oficial, Suplemento 107, 24-XII-2019)"),
}

# (law, in-force day, edit function, or the list of provisions a not-applied act concerns)
STEPS: list[tuple] = [
    ("comf-2014", "2014-09-12", comf_2014),
    ("reformatoria-coip-2015", "2015-09-30", reformatoria_coip_2015),
    ("ley-drogas-2015", "2015-10-26", drogas_2015_a),
    ("ley-drogas-2015", plazo_days("2015-10-26", 90), drogas_2015_b),
    ("ley-tierras-2016", "2016-03-14", tierras_2016),
    ("ley-lavado-2016", "2016-07-21", lavado_2016),
    ("ley-reactivacion-2017", "2017-12-29", ["art-299"]),
    ("ley-violencia-mujeres-2018", "2018-02-05", violencia_mujeres_2018),
    ("referendo-2018", "2018-02-14", referendo_2018),
    ("ley-deporte-2019", "2019-04-30", deporte_2019),
    ("ley-defensoria-2019", "2019-05-06", defensoria_2019),
    ("cc-ec90-2019", "2019-06-03", ["art-202"]),
    ("cc-ec6-2019", "2019-08-15", ["art-581"]),
    ("cc-ec21-2019", "2019-11-13", ["art-653"]),
    ("reformatoria-coip-2019", plazo_days("2019-12-24", 180), reformatoria_coip_2019),
]


def replay(first: dict) -> list[dict]:
    global HEADS
    HEADS = Heads()
    out = []
    units = first
    for law, day, edit in STEPS:
        url = LAWS[law]["url"]
        if isinstance(edit, list):
            for k in edit:
                if k not in units:
                    raise SystemExit(f"{law}: no unit {k}")
            v = {"from": day, "source_url": url, "sha256": sha_of(url), "changes": {},
                 "credits": {k: [law] for k in sorted(edit, key=order)}}
            if LAWS[law].get("note"):
                v["note"] = LAWS[law]["note"]
            if out and out[-1]["from"] == day:
                v["same_day"] = True
            out.append(v)
            continue
        u = Units(units)
        edit(u)
        new = u.u
        changed = sorted((k for k in set(units) | set(new) if units.get(k) != new.get(k)), key=order)
        if not changed:
            raise SystemExit(f"{law}: no change")
        v = {"from": day, "source_url": url, "sha256": sha_of(url),
             "changes": {k: new.get(k) for k in changed}, "credits": {k: [law] for k in changed}}
        if out and out[-1]["from"] == day:
            v["same_day"] = True
        out.append(v)
        units = new
    return out


def check_anachronism(versions: list[dict], laws: dict) -> list[str]:
    """No version may carry a law published after its own in-force day; versions are in order of in-force day."""
    errs = []
    prev = ""
    for v in versions:
        if v["from"] < prev:
            errs.append(f"version {v['from']} comes after {prev}")
        prev = v["from"]
        for k, ls in v.get("credits", {}).items():
            for law in ls:
                pub = laws[law]["published"]
                if pub > v["from"]:
                    errs.append(f"{v['from']}: {k} credited to {law}, published {pub}")
    return errs


DECISIONS: list[str] = []
