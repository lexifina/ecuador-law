"""Write corpus.d/90-trabajo.json: the Código del Trabajo (Codificación 2005-017) and its amending acts.

Reads only the cache (editions located and fetched with `python -X utf8 codes/editions_trabajo.py`). Deterministic:
the same cache gives the same bytes. The part is written atomically (.tmp, then rename).

    python -X utf8 codes/trabajo.py            (TRABAJO_OUT=... to write elsewhere)

Base: Registro Oficial Suplemento 167, 16-XII-2005 (text layer). Amending acts from the 'Nota:' lines of a Lexis-style
consolidation to 1-II-2023 (codes/index_docx.py trabajo, reading only) and the Asamblea's law list screened by text
layer for 2023-2026 (codes/screen.py -> codes/screen_trabajo.json, reading only). Every word is cut from the text layer
of a gazette edition; editions that are page images only are NOT applied (no OCR).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "civil"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import rotext  # noqa: E402
import replay as civil_replay  # noqa: E402
from replay import Src, Units, unquote  # noqa: E402,F401
import strict  # noqa: E402

OUT = Path(os.environ.get("TRABAJO_OUT", HERE.parent / "corpus.d" / "90-trabajo.json"))
RETRIEVED = "2026-10-29"
EDITIONS = json.loads((HERE / "editions_trabajo.json").read_text(encoding="utf-8"))


def ed(name: str, title: str) -> str:
    return next(e["pdf"] for e in EDITIONS[name] if e["title"] == title)


S167_2005 = ed("s167-2005", "Primer Suplemento")

ORD = ["PRIMERA", "SEGUNDA", "TERCERA", "CUARTA", "QUINTA", "SEXTA", "SÉPTIMA", "OCTAVA", "NOVENA", "DECIMA"]
ORD_LOW = ["primera", "segunda", "tercera", "cuarta", "quinta", "sexta", "séptima", "octava", "novena", "décima"]
HEAD = re.compile(r"^(T[ÍI]TULO|Cap[íi]tulo|CAP[ÍI]TULO|Par[áa]grafo|PAR[ÁA]GRAFO|Secci[óo]n|SECCI[ÓO]N)\b")
ART = re.compile(r"^Art\.\s*(\d+)\s*\.?\s*-")
# literals the text layer sets in one paragraph ("...; f) Los contratos a prueba;") go one per line, in the base and in
# the amending acts' quoted text alike
ITEM = re.compile(r"(?<=[:;,.]) (?=[a-z]\) [A-ZÁÉÍÓÚÑ¿\"])")


def split_items(ps: list[str]) -> list[str]:
    out: list[str] = []
    for p in ps:
        out.extend(ITEM.split(p))
    return out


def art_key(n: int, extra: str = "") -> str:
    return f"art-{n:04d}" + (f"-{extra}" if extra else "")


def order(key: str) -> tuple:
    m = re.match(r"art-(\d{4})(?:-(\d+))?$", key)
    if m:
        return (1, int(m.group(1)), int(m.group(2) or 0), "")
    rank = {"disp-general": 2, "disp-transitoria": 3, "disp-final": 5, "titulos": 6}
    base = re.sub(r"-\d+$", "", key)
    return (rank.get(base, 7), 0, 0, key)


def sha_of(url: str) -> str:
    return hashlib.sha256(fetch.cached(url).read_bytes()).hexdigest()


class SSrc(Src):
    """A gazette edition read through codes/strict.py (stray overlay fragments dropped)."""
    _cache: dict[str, "SSrc"] = {}

    def __new__(cls, url: str):
        if url in cls._cache:
            return cls._cache[url]
        self = object.__new__(cls)
        path = fetch.cached(url)
        if path is None:
            raise SystemExit(f"not in cache: {url}")
        self.url = url
        self.paras = [civil_replay.fix_layer(p) for p in strict.paragraphs(path)]
        self.flat = re.sub(r"\s+", " ", "\n".join(self.paras))
        cls._cache[url] = self
        return self


# ---------------------------------------------------------------- base

def base_units() -> dict:
    path = fetch.cached(S167_2005)
    if path is None:
        raise SystemExit(f"not in cache: {S167_2005}")
    ps = rotext.paragraphs(path)
    start = ps.index("TÍTULO PRELIMINAR DISPOSICIONES FUNDAMENTALES")
    units: dict[str, dict] = {}
    heads: list[str] = []
    cur: str | None = None
    pending: list[str] = []  # "De la Ley 133, ...:" lines that head the next transitoria
    expect = 1
    trans = False
    in_head = False
    for p in ps[start:]:
        if p.startswith("Esta Codificación fue elaborada"):
            break
        m = ART.match(p)
        if not trans and m:
            n = int(m.group(1))
            if n != expect:
                raise SystemExit(f"article {n} where {expect} was expected")
            expect += 1
            cur = art_key(n)
            units[cur] = {"label": f"Art. {n}", "kind": "art", "text": ""}
        elif p == "DISPOSICIONES TRANSITORIAS" and expect == 638:
            trans = True
            heads.append(p)
            cur = None
            continue
        elif trans and re.match(r"^De la Ley [\d-]+", p):
            pending.append(p)
            continue
        elif trans and re.match(r"^(%s)\.-" % "|".join(ORD), p):
            i = ORD.index(p.split(".-")[0])
            cur = f"disp-transitoria-{i + 1:02d}"
            units[cur] = {"label": f"Disposición transitoria {ORD_LOW[i]}", "kind": "transitional",
                          "text": "".join(x + "\n" for x in pending)}
            pending = []
        elif trans and p.startswith("ARTÍCULO FINAL.-"):
            cur = "disp-final"
            units[cur] = {"label": "Artículo final", "kind": "final", "text": ""}
        elif not trans and (HEAD.match(p) or cur is None):
            heads.append(p)
            in_head = True
            continue
        elif in_head and not trans:
            # a heading set on two lines ("Capítulo XI Del fondo de reserva, de su disponibilidad y de la" +
            # "jubilación Parágrafo 1ro. Del fondo de reserva"): joined, then split before a following heading
            heads[-1:] = re.split(r" (?=Par[áa]grafo \d)", heads[-1] + " " + p)
            continue
        in_head = False
        if cur is None:
            raise SystemExit(f"text outside a unit: {p[:60]!r}")
        units[cur]["text"] += "".join(x + "\n" for x in split_items([p]))
    if expect != 638 or pending:
        raise SystemExit(f"stopped at article {expect - 1}")
    units["titulos"] = {"label": "Títulos, capítulos y parágrafos", "kind": "headings",
                        "text": "".join(h + "\n" for h in heads)}
    return dict(sorted(units.items(), key=lambda kv: order(kv[0])))


# ---------------------------------------------------------------- helpers for the amending acts

def q(s: Src, anchor: str, count: int = 1, after: str | None = None) -> list[list[str]]:
    return [split_items(b) for b in s.quoted(anchor, count=count, after=after)]


def whole(u: Units, s: Src, n: int, anchor: str, after: str | None = None, key: str | None = None) -> None:
    (b,) = q(s, anchor, after=after)
    if not re.match(rf"Art\.?\s*{n}\s*\.?\s*-", b[0]):
        raise SystemExit(f"art. {n}: quoted text starts {b[0][:30]!r}")
    u.set_unit(key or art_key(n), b)


def innominate(u: Units, after_n: int, block: list[str], start: int = 1) -> list[str]:
    """Split a quoted block of 'Art. ...-' articles into units art-NNNN-1, -2 ... placed after art. after_n."""
    arts: list[list[str]] = []
    for p in block:
        if re.match(r"^Art\.\s*\.{3}|^Art\.\s*\(\.\.\.\)|^Art\.\s*innumerado", p):
            arts.append([p])
        elif arts:
            arts[-1].append(p)
        else:
            raise SystemExit(f"text before the first article: {p[:40]!r}")
    keys = []
    for i, a in enumerate(arts, start):
        k = art_key(after_n, str(i))
        u.set_unit(k, a, label=f"Art. innumerado {i} (tras el art. {after_n})")
        keys.append(k)
    return keys


def paras_after(s: Src, anchor: str, n: int, after: str | None = None, tail: str = '"') -> list[str]:
    """The n paragraphs after the one holding `anchor`, for quotations Src.quoted cannot close (the act ends the
    quotation with '"; y,' or similar): the opening quote and the closing `tail` are stripped and must be there."""
    i = s.index(anchor, after) + 1
    b = list(s.paras[i:i + n])
    if not (b[0].startswith('"') and b[-1].endswith(tail)):
        raise SystemExit(f"quotation after {anchor!r} not as expected: {b[0][:30]!r} ... {b[-1][-30:]!r}")
    b[0] = b[0][1:]
    b[-1] = b[-1][:-len(tail)]
    for x in b:
        if x.count('"') % 2:
            raise SystemExit(f"unbalanced quote: {x[:80]!r}")
    return split_items(b)


def heading_before(u: Units, before: str, lines: list[str]) -> None:
    ps = u.paras("titulos")
    i = ps.index(before)
    u.put("titulos", ps[:i] + lines + ps[i:])


def literal(u: Units, key: str, prefix: str) -> int:
    return u.find(key, prefix)


# ---------------------------------------------------------------- the amending acts (text layer)

RO198_2006 = ed("ro198-2006", "Registro Oficial")
RO223_2006 = ed("ro223-2006", "Registro Oficial")
RO250_2006 = ed("ro250-2006", "Registro Oficial")


def ley_2006_28(u: Units) -> None:
    """Ley 2006-28 Reformatoria al Código del Trabajo (RO 198, 30-I-2006), numerals 1 and 2 of its art. 1: the parts
    that fit the codified text as published (the rest waits for the fe de erratas of RO 223)."""
    s = Src(RO198_2006)
    s.check("Artículo Final.- La presente Ley Reformatoria, entrará en vigencia a partir de su publicación en el Registro Oficial.")
    (b,) = q(s, "1. Sustitúyese el numeral 2, por el siguiente:")
    u.set_para("art-0042", u.find("art-0042", "2. Instalar"), b)
    (b,) = q(s, "2. Sustitúyase el numeral 33, por el siguiente:")
    u.set_para("art-0042", u.find("art-0042", "33. Contratar"), b)


def erratas_2006_28(u: Units) -> None:
    """Fe de erratas (RO 223, 7-III-2006) of Ley 2006-28: its art. 1 num. 3 adds numeral 35 after numeral 34, its
    art. 2 adds the Título after art. 346 and its art. 3 substitutes art. 403 (the published text named numeral 35,
    art. 352 and art. 409, the numbering before the 2005 codification)."""
    e = Src(RO223_2006)
    e.check('En el numeral 3 del artículo 1, donde dice: "Sustitúyase el numeral 35, por el siguiente:", debe decir: '
            '"A continuación del numeral 34, agrégase el siguiente:"',
            'debe decir: "A continuación del artículo 346, añádase el siguiente Título:"',
            'debe decir: "Sustitúyase el artículo 403, por el siguiente: ".')
    s = Src(RO198_2006)
    (b,) = q(s, "3. Sustitúyase el numeral 35, por el siguiente:")
    ps = u.paras("art-0042")
    i = u.find("art-0042", "34. Contratar")
    u.insert("art-0042", i + 1, b)
    (b,) = q(s, "Art. 2.- A continuación del artículo 352, añádase el siguiente Título:")
    if not (b[0] == "TITULO ...." and b[1] == "DEL TRABAJO PARA PERSONAS CON DISCAPACIDAD"):
        raise SystemExit(f"Ley 2006-28 art. 2: {b[:2]}")
    heading_before(u, "TÍTULO IV DE LOS RIESGOS DEL TRABAJO", [b[0] + " " + b[1]])
    innominate(u, 346, b[2:])
    (b,) = q(s, "Art. 3.- Sustitúyase el artículo 409, por el siguiente:")
    b[0] = re.sub(r"^Art\. 409\.-", "Art. 403.-", b[0])  # the fe de erratas corrects the article's number
    whole_ = b
    if not whole_[0].startswith("Art. 403.- Prescripción de las acciones.-"):
        raise SystemExit("Ley 2006-28 art. 3")
    u.set_unit("art-0403", whole_)
    del ps


def comma_end(b: list[str]) -> list[str]:
    """unquote() adds the act's full stop to a quoted text that ends without one; a literal that ends '; y,' keeps
    its comma (the stop after the closing quote ends the act's sentence)."""
    b = list(b)
    if b[-1].endswith(",."):
        b[-1] = b[-1][:-1]
    return b


def ley_2006_39(u: Units) -> None:
    """Ley 2006-39 Reformatoria al Código del Trabajo (RO 250, 13-IV-2006), in force on publication (its Artículo
    final). Edits whose target words do not occur once in the codified text are not applied (decisions)."""
    s = Src(RO250_2006)
    s.check("Artículo Final.- La presente Ley entrará en vigencia a partir de su publicación en el Registro Oficial.")
    # art. 1: a new literal k) in art. 19; the former k) becomes l)
    (b,) = q(s, 'Art. 1.- En el artículo 19, inclúyese como literal k), el siguiente:')
    s.check("El actual literal k) pasa a ser literal l), con el mismo contenido.")
    i = u.find("art-0019", "k) En general")
    u.sub("art-0019", "k) En general", "l) En general", para=i)
    u.insert("art-0019", i, comma_end(b))
    (b,) = q(s, "Art. 2.- En el artículo 20, añádanse los siguientes incisos:")
    u.insert("art-0020", u.count("art-0020"), b)
    whole(u, s, 35, "Art. 3.- Sustitúyese el artículo 35, por el siguiente:")
    whole(u, s, 134, "Art. 4.- Sustitúyese el artículo 134, por el siguiente:")
    s.check('a) Luego de la palabra: "...contrataren", añádese: "mayores de quince años y"; además, sustitúyese: '
            '"...instrucción primaria", por: "instrucción básica"')
    u.sub("art-0135", "contrataren menores", "contrataren mayores de quince años y menores")
    u.sub("art-0135", "instrucción primaria", "instrucción básica")
    (b,) = q(s, "b) Agréguense los siguientes incisos:", after="Art. 5.- En el artículo 135")
    u.insert("art-0135", u.count("art-0135"), b)
    whole(u, s, 136, "Art. 6.- Sustitúyese el artículo 136, por el siguiente:")
    whole(u, s, 138, "Art. 7.- Sustitúyese el artículo 138, por el siguiente:")
    # art. 8 b): the scale of art. 139 (letter a), 'menores' -> 'adolescentes de quince años', names a word that occurs
    # twice in the article and is not applied)
    i = s.index("b) Sustitúyese los límites máximos de carga de acuerdo a la siguiente escala:",
                after="Art. 8.- En el artículo 139")
    scale = s.paras[i + 1]
    if not scale.startswith("Varones de 15 a 18 años 25 libras"):
        raise SystemExit(f"Ley 2006-39 art. 8: {scale[:40]!r}")
    u.set_para("art-0139", u.find("art-0139", "LÍMITES MÁXIMOS DE CARGA"), [scale])
    s.check('Art. 9.- En el artículo 141, luego de la palabra: "... trabajadores", añádese: "... mayores de dieciocho años y".',
            'Art. 10.- En el artículo 144, luego de la palabra: "...personas", añádese: "...mayores de dieciocho años y".',
            "Art. 11.- Derógase el artículo 146 del Código del Trabajo.")
    u.sub("art-0141", "trabajadores menores", "trabajadores mayores de dieciocho años y menores")
    u.sub("art-0144", "personas menores", "personas mayores de dieciocho años y menores")
    u.remove("art-0146")
    whole(u, s, 147, "Art. 12.- Sustitúyese el artículo 147, por el siguiente:")
    (b,) = q(s, "Art. 13.- En el artículo 148, añádese el siguiente inciso:")
    u.insert("art-0148", u.count("art-0148"), b)
    s.check('Art. 14.- En el título del artículo 149, reemplácese: "... menores", por: "adolescentes"; y, luego de: '
            '"...reglamento aprobado", añádese la siguiente frase: "... o lo prescrito en el TITULO V del LIBRO I del '
            'Código de la Niñez y Adolescencia".')
    u.sub("art-0149", "enfermedades de menores atribuidos", "enfermedades de adolescentes atribuidos")
    u.sub("art-0149", "reglamento aprobado", "reglamento aprobado o lo prescrito en el TITULO V del LIBRO I del Código "
          "de la Niñez y Adolescencia")
    s.check('a) En lugar de: "Consejo Nacional de la Niñez y Adolescencia", deberá decir: "... los jueces de la niñez y '
            'adolescencia y las juntas cantonales de protección de derechos";',
            'b) Sustitúyese: "menores de edad", por: "adolescentes menores de quince años"; y,')
    # 'el Consejo Nacional ...' -> 'los jueces ...': the article 'el' goes with the name it introduced
    u.sub("art-0151", "el Consejo Nacional de la Niñez y Adolescencia",
          "los jueces de la niñez y adolescencia y las juntas cantonales de protección de derechos")
    u.sub("art-0151", "menores de edad", "adolescentes menores de quince años")
    (b,) = q(s, "c) Añádase los siguientes incisos:", after="Art. 15.- En el artículo 151")
    u.insert("art-0151", u.count("art-0151"), b)
    (b,) = q(s, "Art. 16.- Sustitúyese el primer inciso del artículo 156, por el siguiente:")
    u.set_para("art-0156", 0, b)
    # art. 17 a) (numeral 1 of art. 158) names a semicolon and words the codified numeral already holds in other
    # words: not applied; b) 'Agréguese como numeral 4': the article already has a numeral 4, so the new one follows it
    (b,) = q(s, "b) Agréguese como numeral 4, el siguiente:", after="Art. 17.- En el artículo 158")
    u.insert("art-0158", u.count("art-0158"), b)
    whole(u, s, 168, "Art. 18.- Sustitúyese el artículo 168, por el siguiente:")
    (b,) = q(s, "Art. 19.- Al artículo 262, agréguese como tercer inciso, el siguiente:")
    u.insert("art-0262", 2, b)
    s.check('Art. 20.- En el artículo 268, en lugar de la última frase: "Si es menor impúber estará el empleador obligado '
            'a darle instrucción primaria", deberá decir:')
    new = s.inline('Art. 20.- En el artículo 268, en lugar de la última frase: "Si es menor impúber estará el empleador '
                   'obligado a darle instrucción primaria", deberá decir:') or None
    if not new:
        (nb,) = s.quoted('Art. 20.- En el artículo 268, en lugar de la última frase:')
        new = nb[0]
    u.sub("art-0268", "Si es menor impúber estará el empleador obligado a darle instrucción primaria", new.rstrip("."))
    b = paras_after(s, "a) Sustitúyese los incisos segundo y tercero, por los siguientes:", 2,
                    after="Art. 21.- En el artículo 616", tail='"; y,')
    u.set_para("art-0616", 1, b, count=2)
    (b,) = q(s, "b) Añádese como inciso final, el siguiente:", after="Art. 21.- En el artículo 616")
    u.insert("art-0616", u.count("art-0616"), b)
    # art. 22 ('menores de edad' occurs twice in art. 381) and art. 23 ('Tribunal de Menores', in neither art. 381 nor
    # art. 402) are not applied


RO259_2006 = ed("ro259-2006", "Registro Oficial")
S298_2006 = ed("s298-2006", "Primer Suplemento")
RO340_2006 = ed("ro340-2006", "Registro Oficial")
S387_2006 = ed("s387-2006", "Primer Suplemento")
RO75_2007 = ed("ro75-2007", "Registro Oficial")
S330_2008 = ed("s330-2008", "Primer Suplemento")
S528_2009 = ed("s528-2009", "Primer Suplemento")
S351_2010 = ed("s351-2010", "Primer Suplemento")
S372_2011 = ed("s372-2011", "Primer Suplemento")
S797_2012 = ed("s797-2012", "Segundo Suplemento")
S332_2014 = ed("s332-2014", "Segundo Suplemento")


def ley_2006_40(u: Units) -> None:
    """Ley 2006-40 Reformatoria del Código del Trabajo (RO 259, 27-IV-2006): five articles innumerados after art. 156
    (medical examination of minors) and a numeral 10 in art. 542. No vigencia clause: in force on publication."""
    s = Src(RO259_2006)
    (b,) = q(s, "Art. 1.- A continuación del artículo 156, agréguense los siguientes artículos innumerados:")
    innominate(u, 156, b)
    (b,) = q(s, "Art. 2.- El numeral 10 del artículo 542 del Código del Trabajo, pasa a ser 11 y agréguese como numeral 10,")
    i = u.find("art-0542", "10. Las demás atribuciones")
    u.sub("art-0542", "10. Las demás atribuciones", "11. Las demás atribuciones", para=i)
    u.insert("art-0542", i, b)


def ley_2006_48(u: Units) -> None:
    """Ley 2006-48 Reformatoria al Código del Trabajo (Suplemento 298, 23-VI-2006): a Capítulo on intermediación
    laboral and tercerización after art. 346, at the end of Título III, and an article after art. 557; in force on
    publication (its Disposición final segunda)."""
    s = Src(S298_2006)
    s.check("SEGUNDA.- La presente Ley Reformatoria entrará en vigencia a partir de su publicación en el Registro Oficial.")
    (b,) = q(s, "Art. 1.- Al final del TITULO III y luego del artículo 346 del Código del Trabajo, incorpórese el siguiente Capítulo:")
    if not (b[0] == "CAPITULO ..." and b[1].startswith("DE LA INTERMEDIACION LABORAL")):
        raise SystemExit(f"Ley 2006-48 art. 1: {b[:2]}")
    heading_before(u, "TITULO .... DEL TRABAJO PARA PERSONAS CON DISCAPACIDAD", [b[0] + " " + b[1]])
    keys = innominate(u, 346, b[2:], start=4)
    if len(keys) != 20:
        raise SystemExit(f"Ley 2006-48: {len(keys)} articles")
    (b,) = q(s, "Art. 2.- A continuación del artículo 557, agréguese el siguiente artículo innumerado:")
    innominate(u, 557, b)


def erratas_2006_216(u: Units) -> None:
    """Fe de erratas of the codification (RO 340, 23-VIII-2006), Comisión de Legislación y Codificación: art. 216
    num. 2, first inciso."""
    s = Src(RO340_2006)
    s.check('1.- En el primer inciso del numeral 2 del artículo 216, se dice: "remuneración básica mínima unificada '
            'medio", debiendo corregirse por la siguiente expresión: "remuneración básica unificada media".')
    u.sub("art-0216", "remuneración básica mínima unificada medio", "remuneración básica unificada media", para="2. ")


def ley_2006_60(u: Units) -> None:
    """Ley 2006-60 Reformatoria al Código del Trabajo (Suplemento 387, 30-X-2006): an article after art. 304 (mining
    workers). No vigencia clause: in force on publication."""
    s = Src(S387_2006)
    (b,) = q(s, "Art. 1.- A continuación del artículo 304, incorpórese el siguiente:")
    innominate(u, 304, b)


def ley_2007_77(u: Units) -> None:
    """Ley Reformatoria al Código del Trabajo (RO 75, 2-V-2007): first inciso of art. 113 (decimocuarta
    remuneración); in force on publication (its art. 2)."""
    s = Src(RO75_2007)
    s.check("Art. 2.- La presente Ley reformatoria entrará en vigencia desde la fecha de su publicación en el Registro Oficial.")
    (b,) = q(s, "Art. 1.- Sustitúyese el primer inciso del artículo 113, por el siguiente:")
    u.set_para("art-0113", 0, b)


def mandato_8(u: Units) -> None:
    """Mandato Constituyente No. 8 (Asamblea Constituyente, 30-III-2008; Suplemento 330, 6-V-2008), Disposición final
    primera: repeals Ley 2006-48 and, in the Code, art. 11 literal h), 14 literal g), the phrase 'por horas' and the
    sixth to thirteenth incisos of art. 17, 19 literal j), 41 second inciso and the words 'o intermediarios' of art.
    100. In force 'en forma inmediata, sin perjuicio de su publicación' (Disposición final tercera)."""
    s = Src(S330_2008)
    s.check('PRIMERA: Deróguese la Ley Reformatoria al Código de Trabajo, mediante la cual se reguló la actividad de '
            'intermediación laboral y la de tercerización de servicios complementarios, publicada en el Suplemento del '
            'Registro Oficial 298 de 23 de junio del 2006; los artículos 11 literal h), 14 literal g), 17 la frase: '
            '"por horas" incisos sexto al décimotercero, 19 literal j), 41 inciso 2º y las palabras "o intermediarios" '
            'del artículo 100 de la Codificación del Código del Trabajo;',
            "entrará en vigencia en forma inmediata, sin perjuicio de su publicación en la Gaceta Constituyente y/o en "
            "el Registro Oficial.")
    for k in [k for k in u.u if re.fullmatch(r"art-0346-(\d+)", k) and int(k.rsplit("-", 1)[1]) >= 4] + ["art-0557-1"]:
        u.remove(k)
    ps = u.paras("titulos")
    ps.remove("CAPITULO ... DE LA INTERMEDIACION LABORAL Y DE LA TERCERIZACION DE SERVICIOS COMPLEMENTARIOS")
    u.put("titulos", ps)
    # art. 11 h) 'Por horas.' is the last literal: g) keeps its '; y,' as printed
    u.delete_para("art-0011", "h) Por horas.")
    u.delete_para("art-0014", "g) Los que se pacten por horas")
    ps = u.paras("art-0017")
    if len(ps) != 13 or not ps[5].startswith("Son contratos por hora aquellos"):
        raise SystemExit("art. 17: incisos not as expected")
    u.put("art-0017", ps[:5])
    u.drop("art-0017", "por horas")
    u.delete_para("art-0019", "j) Los que se pacten por horas")
    ps = u.paras("art-0041")
    if len(ps) != 2:
        raise SystemExit("art. 41: expected two incisos")
    u.put("art-0041", ps[:1])
    ps = u.paras("art-0100")
    if sum(p.count(" o intermediarios") for p in ps) != 3:
        raise SystemExit("art. 100: 'o intermediarios' not found three times")
    u.put("art-0100", [p.replace(" o intermediarios", "") for p in ps])


def ley_2009_licencias(u: Units) -> None:
    """Ley Orgánica Reformatoria a la LOSCCA y al Código del Trabajo (Suplemento 528, 13-II-2009): art. 152
    substituted (maternity and paternity leave) and two articles innumerados after it; in force on publication."""
    s = Src(S528_2009)
    s.check("La presente Ley entrará en vigencia a partir de su publicación en el Registro Oficial.")
    i = s.index("Art. 4.- Sustitúyase el artículo 152 del Código del Trabajo por el siguiente:")
    j = s.index("Art. 5.- A continuación del artículo 152 agréguese los siguientes artículos innumerados:")
    k = s.index("DISPOSICION GENERAL UNICA.-")
    if j - i != 5 or k - j != 4:
        raise SystemExit("Suplemento 528: layout not as expected")
    # printed without quotation marks and without the article's number and heading
    u.set_unit("art-0152", s.paras[i + 1:j])
    innominate(u, 152, s.paras[j + 1:k])


def copci_2010(u: Units) -> None:
    """Código Orgánico de la Producción, Comercio e Inversiones (Suplemento 351, 29-XII-2010), Disposición
    reformatoria quinta; in force on publication. Its numeral 5 (art. 95) names words the codified inciso words
    otherwise ('la decimotercera, decimocuarta remuneraciones,'): not applied."""
    s = Src(S351_2010)
    s.check("Las disposiciones de este Código y sus derogatorias entrarán en vigencia desde la fecha de su promulgación en el Registro Oficial.")
    top = "QUINTA.- Refórmese el Código de Trabajo en las siguientes disposiciones:"
    (b,) = q(s, "1. En el Artículo 81, agréguense los siguientes incisos:", after=top)
    u.insert("art-0081", u.count("art-0081"), b)
    (b,) = q(s, "2. A continuación del Art. 105, incorpórese el siguiente artículo innumerado:", after=top)
    u.set_unit("art-0105-1", b, label="Art. 105.1")
    s.check('3. En el segundo inciso del Art. 17 del Código del Trabajo, luego de la palabra "continuos", agréguese la '
            'frase "o discontinuos", y al final del mismo inciso agréguese lo siguiente: "El sueldo o salario que se '
            'pague en los contratos eventuales, tendrá un incremento del 35% del valor hora del salario básico del '
            'sector al que corresponda el trabajador.".',
            'Al final del tercer inciso agréguese lo siguiente: "El sueldo o salario que se pague en los contratos '
            'ocasionales, tendrá un incremento del 35% del valor hora del salario básico del sector al que corresponda '
            'el trabajador."')
    u.sub("art-0017", "ciento ochenta días continuos", "ciento ochenta días continuos o discontinuos", para=1)
    ps = u.paras("art-0017")
    ps[1] += (" El sueldo o salario que se pague en los contratos eventuales, tendrá un incremento del 35% del valor "
              "hora del salario básico del sector al que corresponda el trabajador.")
    ps[2] += (" El sueldo o salario que se pague en los contratos ocasionales, tendrá un incremento del 35% del valor "
              "hora del salario básico del sector al que corresponda el trabajador.")
    u.put("art-0017", ps)
    (b,) = q(s, "4. A continuación del Artículo 23 agréguese el siguiente artículo:", after=top)
    u.set_unit("art-0023-1", b, label="Art. 23.1")


def cc_031_10_scn_cc(u: Units) -> None:
    """Corte Constitucional, sentencia 031-10-SCN-CC (Suplemento 372, 27-I-2011): the second inciso of art. 581 is
    unconstitutional and expelled from the legal order."""
    s = Src(S372_2011)
    s.check('1. Declarar que el contenido del inciso segundo del artículo 581 del Código del Trabajo, que señala "Si una '
            'de las partes ha obtenido directamente documentos no adjuntados en la diligencia preliminar, necesarios '
            'para justificar sus afirmaciones o excepciones, podrá entregarlos al juez antes de los alegatos", '
            'contraviene')
    u.delete_para("art-0581", "Si una de las partes ha obtenido directamente documentos no adjuntados")


def ley_derechos_laborales_2012(u: Units) -> None:
    """Ley Orgánica para la Defensa de los Derechos Laborales (Segundo Suplemento 797, 26-IX-2012), arts. 3-6. No
    vigencia clause: in force on publication."""
    s = Src(S797_2012)
    (b,) = q(s, "Artículo 3.- En el Artículo 104 del Código del Trabajo, añádase el inciso siguiente:")
    u.insert("art-0104", u.count("art-0104"), b)
    (b,) = q(s, "Artículo 4.- Sustitúyase el tercer inciso del Artículo 155 del Código del Trabajo, por el siguiente:")
    u.set_para("art-0155", 2, b)
    s.check("Artículo 5.- Derógase el Artículo 269 del Código del Trabajo.")
    u.remove("art-0269")
    (b,) = q(s, "Artículo 6.- Añádase el siguiente artículo innumerado después del Artículo 268 del Código de Trabajo:")
    u.set_unit("art-0268-1", b, label="Art. innumerado 1 (tras el art. 268)")


def comf_2014(u: Units) -> None:
    """Código Orgánico Monetario y Financiero (Segundo Suplemento 332, 12-IX-2014), Disposición reformatoria sexta:
    a last inciso of art. 36; in force on publication (its Disposición final)."""
    s = Src(S332_2014)
    s.check("DISPOSICIÓN FINAL.- El presente Código entrará en vigencia desde la fecha de su publicación en el Registro Oficial.")
    p = s.paras[s.index("Sexta.- En el Código del Trabajo, en el artículo 36, incorpórese como último inciso, lo siguiente:")]
    rest = p.split("lo siguiente: ", 1)[1]
    (new,) = unquote([rest])
    u.insert("art-0036", u.count("art-0036"), [new])


# ---------------------------------------------------------------- laws, steps, part

BASE_LAW = "codificacion-ct-2005-017"
IMAGE_ONLY = ("NOT APPLIED here: the Registro Oficial edition that publishes it is page images without a text layer, "
              "and this repository does not OCR. Its wording is missing: the files named in this commit keep the "
              "earlier text (provisions named from the Lexis index).")

LAWS = {
    BASE_LAW: dict(label="Codificación 2005-017 del Código del Trabajo", kind="law", enacted="2005-10-18",
                   published="2005-12-16", url=S167_2005,
                   title="Codificación del Código del Trabajo (Comisión de Legislación y Codificación del Congreso "
                         "Nacional)"),
    "ley-2006-28": dict(label="Ley 2006-28 Reformatoria al Código del Trabajo", kind="law", enacted="2006-01-18",
                        published="2006-01-30", url=RO198_2006,
                        title="Ley 2006-28 Reformatoria al Código del Trabajo (personas con discapacidad)"),
    "fe-erratas-ley-2006-28": dict(label="Fe de erratas de la Ley 2006-28", kind="law", enacted="2006-02-24",
                                   published="2006-03-07", url=RO223_2006,
                                   title="Fe de erratas a la Ley 2006-28 Reformatoria al Código del Trabajo (Congreso "
                                         "Nacional, Registro Oficial 223)"),
    "ley-2006-39": dict(label="Ley 2006-39 Reformatoria al Código del Trabajo", kind="law", enacted="2006-03-28",
                        published="2006-04-13", url=RO250_2006,
                        title="Ley 2006-39 Reformatoria al Código del Trabajo (trabajo de adolescentes)"),
}

# (law key(s), in-force day, edit function or list of provisions for an act that is not applied); a tuple of law keys
# credits every changed unit to all of them
STEPS = [
    ("ley-2006-28", "2006-01-30", ley_2006_28),
    (("ley-2006-28", "fe-erratas-ley-2006-28"), "2006-03-07", erratas_2006_28),
    ("ley-2006-39", "2006-04-13", ley_2006_39),
]

DECISIONS = [
    "Código del Trabajo: the oldest version is the Codificación 2005-017 (Registro Oficial Suplemento 167, 16-XII-2005), in force from its publication (its Artículo final: the Code, its reforms and repeals are in force from their publication). The Code dates from 1938; older texts are not part of this history, so the first version is credited to the publisher as the oldest version available.",
    "Código del Trabajo units: art-NNNN for each article; articles added later keep their place (art-0346-1, art-0346-2 ... for the articles innumerados after art. 346); disp-transitoria-NN (each with the 'De la Ley ...' line that heads it in the codification), disp-final for the Artículo final; 'titulos' holds the Título, Capítulo and Parágrafo headings in order (headings the text layer sets on two lines are joined). The codification's introduction, its concordance table and its list of sources are not units. Repealed articles are removed.",
    "Código del Trabajo text: literals the text layer sets in one paragraph ('...; f) Los contratos a prueba;') are split one per line, in the base and in the amending acts' quoted text alike; tables keep the run-together text the gazette's text layer gives (arts. 131, 139, 218, 438).",
    "Código del Trabajo: every later version replays an amending act's own Registro Oficial text on the version before it, in order of entry into force: whole articles and paragraphs are cut from the act's PDF after an anchor phrase, and every short phrase an act inserts or replaces is checked to occur word for word in the act's PDF.",
    "Código del Trabajo: Ley 2006-28 (RO 198, 30-I-2006) was written against the numbering before the 2005 codification; the Congress's fe de erratas (RO 223, 7-III-2006) moved three of its provisions: numeral 35 of art. 42 is added after numeral 34 (not 'substituted'), the Título on work of persons with disabilities goes after art. 346 (not 352) and the new text on prescription replaces art. 403 (not 409). Its numerals 2 and 33 of art. 42 fit the codified text as published and are dated 30-I-2006; the three corrected provisions are dated 7-III-2006 and credited to both the law and the fe de erratas. The substituted article, printed 'Art. 409.-', is numbered 'Art. 403.-' as the fe de erratas directs.",
    "Código del Trabajo: Ley 2006-39 (RO 250, 13-IV-2006) is applied as worded where the words it names occur once in the codified text. Not applied, because the codification already worded the provision otherwise or the words occur more than once or not at all: art. 8 a) ('menores' -> 'adolescentes de quince años' in art. 139: twice), art. 17 a) (art. 158 num. 1: the codified numeral already speaks of 'los mecanismos de transferencia de los conocimientos'), art. 22 ('menores de edad' in art. 381: twice) and art. 23 ('Tribunal de Menores': in neither art. 381 nor art. 402). Its art. 17 b) adds a numeral '4.' after the existing numeral 4 of art. 158, and art. 19 inserts the new text as the third inciso of art. 262, before the inciso that was third. In art. 151 'el Consejo Nacional de la Niñez y Adolescencia' becomes 'los jueces de la niñez y adolescencia ...' (the article 'el' goes with the name it introduced). Art. 20 replaces the last phrase of art. 268 without the full stop the act sets inside its quotation marks.",
]

AI_USE = [
    "Código del Trabajo: no generative model wrote legal text. The amendment map in codes/trabajo.py (which provision each act changes, and the anchor phrases before its new text in the act's PDF) was written by an AI agent (Claude) from reading each act; the words are cut from the gazette PDFs' text layers. No OCR was used.",
]


def replay(first: dict) -> list[dict]:
    out = []
    units = first
    for law, day, edit in STEPS:
        laws_ = list(law) if isinstance(law, tuple) else [law]
        url = LAWS[laws_[-1]]["url"]
        if isinstance(edit, list):
            for k in edit:
                if k not in units:
                    raise SystemExit(f"{law}: no unit {k}")
            out.append({"from": day, "source_url": url, "sha256": sha_of(url), "changes": {},
                        "credits": {k: laws_ for k in sorted(edit, key=order)}})
            continue
        u = Units(units)
        edit(u)
        new = dict(sorted(u.u.items(), key=lambda kv: order(kv[0])))
        changed = sorted((k for k in set(units) | set(new) if units.get(k) != new.get(k)), key=order)
        if not changed:
            raise SystemExit(f"{law}: no change")
        v = {"from": day, "source_url": url, "sha256": sha_of(url),
             "changes": {k: new.get(k) for k in changed}, "credits": {k: laws_ for k in changed}}
        if out and out[-1]["from"] == day:
            v["same_day"] = True
        out.append(v)
        units = new
    return out


def build_act() -> dict:
    units = base_units()
    first = {"from": "2005-12-16", "source_url": S167_2005, "sha256": sha_of(S167_2005), "units": units, "credits": {}}
    return {"slug": "codigo-trabajo", "short": "CT", "title": "Código del Trabajo", "url": S167_2005,
            "first_law": None, "earlier_laws": [BASE_LAW], "versions": [first] + replay(units)}


def laws() -> dict:
    return {k: {"label": v["label"], "title": v["title"], "kind": v["kind"], "enacted": v.get("enacted"),
                "published": v["published"], "url": v["url"], "temporary_until": None,
                "restores": v.get("restores"), "note": v.get("note")} for k, v in LAWS.items()}


def sources() -> list[dict]:
    n = sum(len(v) for v in EDITIONS.values())
    return [
        {"name": "Registro Oficial del Ecuador (Código del Trabajo and its amending acts)",
         "url": "https://www.registroficial.gob.ec", "retrieved": RETRIEVED, "requests": n,
         "licence": "No licence stated on the site; official gazette text.",
         "notes": "One PDF per gazette edition, served by esacc.corteconstitucional.gob.ec, found through the site's month listings (codes/editions_trabajo.py -> codes/editions_trabajo.json). Every version's wording is cut from the text layer of the 2005 codification or of the amending act; editions without a text layer are listed in decisions and not applied."},
        {"name": "Lexis-style consolidation of the Código del Trabajo, 'Última modificación: 01-02-2023' (LegalCloud download)",
         "url": "https://legalcloud.ec/download/codigo-del-trabajo/", "retrieved": RETRIEVED, "requests": 1,
         "licence": "Publisher's copyright; read only, nothing copied.",
         "notes": "Index of amending acts ('Nota:' lines, codes/index_docx.py trabajo). Reading only."},
    ]


def main() -> None:
    act = build_act()
    part = {"laws": laws(), "acts": [act], "sources": sources(), "applies": [], "decisions": DECISIONS, "ai_use": AI_USE}
    OUT.parent.mkdir(exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    data = json.dumps(part, ensure_ascii=False, indent=1) + "\n"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)
    os.replace(tmp, OUT)
    n = sum(len(v.get("changes", {})) for v in act["versions"][1:])
    print(f"{OUT.name}: {len(act['versions'])} versions, {len(part['laws'])} laws, {n} unit changes, {len(data)} bytes")


if __name__ == "__main__" and "--base" not in sys.argv:
    main()

if __name__ == "__main__" and "--base" in sys.argv:
    u = base_units()
    print(len(u))
    print(u["titulos"]["text"])
    for k in ["art-0011", "art-0014", "art-0131", "disp-transitoria-03", "disp-final"]:
        print(k, u[k]["text"])
