"""The Constitution's amending acts, applied in order to the 2008 text.

Every act is a function that edits a copy of the previous version's units. New
wording is never typed here as such: whole provisions and paragraphs are cut out
of the act's own cached Registro Oficial PDF between two anchors (Src.grab), and
every short phrase an act inserts is checked to occur, word for word, in that
act's PDF (Src.check). Changed units are credited to the act automatically.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import fetch
import rotext

HERE = Path(__file__).resolve().parent
H = "http://esacc.corteconstitucional.gob.ec/storage/api/v1/10_DWL_FL/"
HS = "https://esacc.corteconstitucional.gob.ec/storage/api/v1/10_DWL_FL/"
RO_490_2011 = H + "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiY2M1YTUwMjYtZTcyMS00NTExLWFlMmEtZGE2MjZlMDllYjUzLnBkZiJ9"
RO_653_2015 = H + "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiYzFhZWNmOTgtMjczYS00MDRmLThmYmEtZTg4N2ZjZTE5NTZmLnBkZiJ9"
RO_133_2017 = H + "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiYTg1ZGM4YzMtM2U4ZS00OGI5LWI1YjEtZGJmZWQzZGJhNWE0LnBkZiJ9"
RO_180_2018 = H + "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiOGMwNTA4ZmMtYTQ0NS00MWRlLTk3OWEtZmZiMjY5NGMyNWQ0LnBkZiJ9"
RO_EC79_2019 = HS + "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiYjQzZGNhZWEtY2ZjYy00MDU3LTk3ZjctMDY3MGE1ODJjODczLnBkZiJ9"
RO_377_2021 = H + "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiY2NiNDhjMmUtYjIwNy00YTBhLWFkZTEtMDczNTA2OGEyYzI3LnBkZiJ9"
RO_568_2024 = H + "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiYmE0MDA2ZDgtYThkZi00YzUzLTg0NTItZWFmYzc1NDZjODRhLnBkZiJ9"


# ---------------------------------------------------------------- sources

class Src:
    """One cached gazette edition as normalised text (paragraphs joined by newlines)."""
    _cache: dict[str, "Src"] = {}

    def __new__(cls, url: str):
        if url in cls._cache:
            return cls._cache[url]
        self = super().__new__(cls)
        path = fetch.cached(url)
        if path is None:
            raise SystemExit(f"not in cache: {url}")
        self.url, self.path = url, path
        self.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        self.text = "\n".join(rotext.paragraphs(path))
        self.flat = re.sub(r"\s+", " ", self.text)
        cls._cache[url] = self
        return self

    def check(self, *phrases: str) -> None:
        for p in phrases:
            if re.sub(r"\s+", " ", p) not in self.flat:
                raise SystemExit(f"phrase not in {self.url[-20:]}: {p!r}")

    def grab(self, start: str, end: str, after: str | None = None) -> list[str]:
        """The paragraphs from `start` through `end` (both anchors included), quotes trimmed."""
        t = self.text
        base = t.index(after) if after else 0
        i = t.find(start, base)
        if i < 0:
            raise SystemExit(f"start anchor not found: {start!r}")
        j = t.find(end, i)
        if j < 0:
            raise SystemExit(f"end anchor not found: {end!r}")
        j += len(end)
        tail = t[j:j + 3]
        chunk = t[i:j]
        # a quotation that closes without a final stop, followed by the act's own "." or "," (Spanish
        # puts the full stop outside the closing quote): the stop belongs to the quoted sentence.
        if re.match(r'\s*"\s*[.,]', tail) and not re.search(r"[.:;]$", chunk):
            chunk += "."
        paras = [p.strip() for p in chunk.split("\n") if p.strip()]
        paras = [p.strip('"').strip() if k == 0 else p for k, p in enumerate(paras)]
        paras[-1] = re.sub(r'"\s*[.,]?$', "", paras[-1]).strip()
        if paras[0].startswith('"'):
            paras[0] = paras[0][1:]
        for p in paras:
            if '"' in p and p.count('"') % 2:
                raise SystemExit(f"unbalanced quote in grabbed text: {p[:80]!r}")
        return paras


# ---------------------------------------------------------------- unit edits

class Units:
    def __init__(self, units: dict):
        self.u = copy.deepcopy(units)

    def paras(self, key: str) -> list[str]:
        return self.u[key]["text"].rstrip("\n").split("\n")

    def put(self, key: str, paras: list[str]) -> None:
        self.u[key]["text"] = "".join(p + "\n" for p in paras)

    def find(self, key: str, prefix: str) -> int:
        hits = [i for i, p in enumerate(self.paras(key)) if p.startswith(prefix)]
        if len(hits) != 1:
            raise SystemExit(f"{key}: {len(hits)} paragraphs start with {prefix!r}")
        return hits[0]

    def sub(self, key: str, old: str, new: str, src: Src | None = None, para: str | None = None) -> None:
        """Replace one exact phrase (once) in a unit, or in its paragraph starting with `para`."""
        ps = self.paras(key)
        idx = range(len(ps)) if para is None else [self.find(key, para)]
        hits = [(i, ps[i].count(old)) for i in idx if old in ps[i]]
        if len(hits) != 1 or hits[0][1] != 1:
            raise SystemExit(f"{key}: phrase {old!r} found {hits}")
        i = hits[0][0]
        ps[i] = ps[i].replace(old, new)
        self.put(key, ps)

    def set_para(self, key: str, prefix: str, new: list[str], keep_prefix: str = "") -> None:
        ps = self.paras(key)
        i = self.find(key, prefix)
        new = list(new)
        new[0] = keep_prefix + new[0]
        ps[i:i + 1] = new
        self.put(key, ps)

    def insert_after(self, key: str, prefix: str | None, new: list[str]) -> None:
        ps = self.paras(key)
        i = len(ps) - 1 if prefix is None else self.find(key, prefix)
        ps[i + 1:i + 1] = new
        self.put(key, ps)

    def delete_para(self, key: str, prefix: str) -> None:
        ps = self.paras(key)
        del ps[self.find(key, prefix)]
        self.put(key, ps)

    def set_unit(self, key: str, new: list[str], label: str | None = None, kind: str | None = None) -> None:
        if key not in self.u:
            self.u[key] = {"label": label, "kind": kind, "text": ""}
        self.put(key, new)


def art_head(n: int) -> str:
    return f"Art. {n}.- "


# ---------------------------------------------------------------- the acts

def referendo_2011(u: Units) -> None:
    s = Src(RO_490_2011)
    s.check("Incorpórese a continuación del primer inciso al numeral 9 del artículo 77",
            "El artículo 77 numeral 1 dirá:", "El artículo 77 numeral 11 dirá:",
            "En el primer inciso del artículo 312 de la Constitución dirá:",
            "En el primer inciso de la DISPOSICIÓN TRANSITORIA VIGÉSIMO NOVENA, dirá:",
            "El artículo 20 del Régimen de Transición dirá:",
            "Los artículos 179 y 181 de la Constitución de la República dirán:",
            "Suprímase el último inciso del artículo 180 de la Constitución.")
    u.set_para("art-077", "1. ", s.grab("La privación de la libertad no será la regla general",
                                        "condiciones y requisitos establecidos en la ley."), keep_prefix="1. ")
    u.insert_after("art-077", "9. ", s.grab("La orden de prisión preventiva se mantendrá vigente",
                                            "sancionados de conformidad con la ley."))
    u.set_para("art-077", "11. ", s.grab("La jueza o juez aplicará las medidas cautelares alternativas",
                                         "plazos, condiciones y requisitos establecidos en la ley."), keep_prefix="11. ")
    u.set_para("art-312", "Art. 312.-", s.grab("Las instituciones del sistema financiero privado, así como las empresas "
                                               "privadas de comunicación", "marco constitucional y normativo vigente."),
               keep_prefix=art_head(312))
    u.set_para("disp-transitoria-29", "VIGESIMONOVENA.-",
               s.grab("Las acciones y participaciones que posean las instituciones",
                      "aprobación de esta reforma en referendo."), keep_prefix="VIGESIMONOVENA.- ")
    u.set_unit("regimen-transicion-art-20", s.grab("Art. 20.- Se disuelve el actual Pleno",
                                                   "Disposición Transitoria Primera del Código Orgánico de la Función Judicial."))
    u.set_unit("art-179", s.grab("Art. 179.- El Consejo de la Judicatura se integrará por 5 delegados",
                                 "que podrá fiscalizar y juzgar a sus miembros"))
    u.set_unit("art-181", s.grab("Art. 181.- Serán funciones del Consejo de la Judicatura",
                                 "se tomarán por mayoría simple."))
    u.delete_para("art-180", "La designación de las vocales y los vocales del Consejo de la Judicatura")


def enmiendas_2015(u: Units, part: str) -> None:
    """part 'a': everything in force on publication; part 'b': arts. 114 and 144 (in force 24 May 2017)."""
    s = Src(RO_653_2015)
    if part == "b":
        s.check('En el artículo 114, suprímase la frase "por una sola vez, consecutiva o no, para el mismo cargo". '
                'Añádase luego de la palabra "podrán" la frase: "postularse para".',
                'En el artículo 144, en el inciso segundo suprímase la frase "por una sola vez". Añádase luego de la '
                'palabra "podrá" la frase: "postularse para".',
                "Las Enmiendas Constitucionales a los artículos 114 y 144 segundo inciso de la Constitución de la "
                "República del Ecuador, referidas a los derechos de participación política, entrarán en vigencia "
                "desde el 24 de mayo de 2017.")
        u.sub("art-114", " por una sola vez, consecutiva o no, para el mismo cargo", "")
        u.sub("art-114", "podrán reelegirse", "podrán postularse para reelegirse")
        u.sub("art-144", " por una sola vez", "", para="La Presidenta o Presidente de la República permanecerá")
        u.sub("art-144", "y podrá ser reelecto", "y podrá postularse para ser reelecto",
              para="La Presidenta o Presidente de la República permanecerá")
        return
    s.check('Al final del inciso tercero, suprímase el signo gramatical punto (.) y a continuación añádase la '
            'siguiente frase: "que sean de competencia del correspondiente nivel de gobierno."',
            'En el inciso cuarto suprímase la frase "sobre cualquier asunto".',
            'En el artículo 142, sustitúyanse las palabras "treinta y cinco" por "treinta".',
            'En el artículo 158, sustitúyase el segundo inciso por el siguiente:',
            'En el artículo 211, suprímase la frase ", y la consecución de los objetivos de las instituciones del Estado".',
            'En el artículo 212 numeral 2, suprímanse las palabras "y gestiones" y sustitúyase la palabra "sujetas" por "sujetos".',
            "En el artículo 229, suprímase el tercer inciso.",
            'En el artículo 326 numeral 16, luego de las palabras "o profesionales" inclúyanse las palabras "y demás '
            'servidores públicos" y sustitúyase la frase: "Aquellos que no se incluyen en esta categorización estarán '
            'amparados por el Código del Trabajo." por el siguiente texto:',
            'En el artículo 261 numeral 6, a continuación del punto (.) inclúyase la siguiente frase: "Planificar, '
            'construir y mantener la infraestructura física y los equipamientos correspondientes en educación y salud."',
            "En el artículo 264 sustitúyase el numeral 7, por el siguiente texto:",
            "En el artículo 370, agréguese al final un inciso con el siguiente texto:",
            'En el artículo 372, al inicio del segundo inciso, sustitúyase la palabra "provisionales" por la palabra '
            '"previsionales".',
            "En el artículo 384, agréguese como primer inciso el siguiente texto:",
            'En la Disposición Transitoria PRIMERA, numeral 9, a continuación de la frase "regiones autónomas", '
            'sustitúyase el signo de puntuación coma (,) por el signo de punto (.) y suprímase la frase "que en ningún '
            'caso excederá de ocho años."')
    u.sub("art-104", "sobre temas de interés para su jurisdicción.",
          "sobre temas de interés para su jurisdicción que sean de competencia del correspondiente nivel de gobierno.")
    u.sub("art-104", "consulta popular sobre cualquier asunto.", "consulta popular.")
    u.sub("art-142", "treinta y cinco años", "treinta años")
    u.set_para("art-158", "Las Fuerzas Armadas tienen como misión fundamental",
               s.grab("Las Fuerzas Armadas tienen como misión fundamental la defensa de la soberanía e integridad",
                      "seguridad integral del Estado de conformidad con la ley."))
    u.sub("art-211", ", y la consecución de los objetivos de las instituciones del Estado", "")
    u.sub("art-212", "con los aspectos y gestiones sujetas a su control", "con los aspectos sujetos a su control", para="2. ")
    u.delete_para("art-229", "Las obreras y obreros del sector público estarán sujetos al Código de Trabajo.")
    new16 = s.grab("Bajo este régimen, los servidores públicos tendrán derecho",
                   "sólo habrá contratación colectiva para el sector privado.")
    assert len(new16) == 1
    u.sub("art-326", "o profesionales,", "o profesionales y demás servidores públicos,", para="16. ")
    u.sub("art-326", "Aquellos que no se incluyen en esta categorización estarán amparados por el Código del Trabajo.",
          new16[0], para="16. ")
    u.sub("art-261", "6. Las políticas de educación, salud, seguridad social, vivienda.",
          "6. Las políticas de educación, salud, seguridad social, vivienda. Planificar, construir y mantener la "
          "infraestructura física y los equipamientos correspondientes en educación y salud.")
    u.set_para("art-264", "7. ", s.grab("7. Planificar, construir y mantener la infraestructura física y los "
                                        "equipamientos de los espacios públicos", "de salud y educación."))
    u.insert_after("art-370", None, s.grab("El Estado garantiza el pago de las pensiones de retiro",
                                           "las Fuerzas Armadas y la Policía Nacional."))
    u.sub("art-372", "Los fondos provisionales", "Los fondos previsionales")
    first = s.grab("La comunicación como un servicio público se prestará",
                   "a través de medios públicos, privados y comunitarios.")
    u.sub("art-384", "Art. 384.- El sistema de comunicación social", "El sistema de comunicación social")
    ps = u.paras("art-384")
    u.put("art-384", [art_head(384) + first[0]] + ps)
    u.sub("disp-transitoria-01", "regiones autónomas, que en ningún caso excederá de ocho años.",
          "regiones autónomas.", para="9. ")


def referendo_2018(u: Units) -> None:
    s = Src(RO_133_2017)  # the annexes, printed with Decreto Ejecutivo 229 (RO Supl. 133, 4-XII-2017)
    s.check("Sustitúyase el artículo 233 de la Constitución de la República del Ecuador por el siguiente texto:",
            "Sustitúyase el texto del art. 114 de la Constitución por el siguiente:",
            "Sustitúyase el segundo inciso del artículo 144 por el siguiente:",
            "Incorpórese una Disposición General Primera, con el siguiente texto:",
            "Incorpórese una Disposición General Segunda, con el siguiente texto:",
            "Agréguese un inciso tercero al artículo 112 de la Constitución que disponga:",
            "Sustitúyase el inciso primero del artículo 205 de la Constitución por el siguiente texto:",
            "Sustitúyase el inciso tercero del artículo 207 de la Constitución por el siguiente texto:",
            "Agréguese un cuarto inciso al artículo 207 de la Constitución que disponga:",
            "Añádase al numeral 4 del artículo 46 de la Constitución un segundo inciso con el siguiente texto:",
            "Agréguese un segundo inciso al artículo 407 de la Constitución de la República del Ecuador con el "
            "siguiente texto:")
    new = s.grab("Ninguna servidora ni servidor público estará exento", "establecidos en la presente Constitución.")
    u.set_unit("art-233", [art_head(233) + new[0]] + new[1:])
    new = s.grab("Las autoridades de elección popular podrán reelegirse por una sola vez", "al que desempeñan")
    u.set_unit("art-114", [art_head(114) + new[0]] + new[1:])
    u.set_para("art-144", "La Presidenta o Presidente de la República permanecerá",
               s.grab("La Presidenta o Presidente de la República permanecerá cuatro años en sus funciones y podrá ser "
                      "reelecto", "por una sola vez"))
    u.set_unit("disp-general-01", s.grab("Disposición General Primera: Déjense sin efecto",
                                         "de 2015 por la Asamblea Nacional."),
               label="Disposición general primera", kind="general")
    u.set_unit("disp-general-02", s.grab("Disposición General Segunda: Las autoridades de elección popular",
                                         "no podrán postularse para el mismo cargo."),
               label="Disposición general segunda", kind="general")
    u.insert_after("art-112", None, s.grab("Los partidos y movimientos políticos o sus alianzas no podrán postular",
                                           "Consejo de Participación Ciudadana y Control Social."))
    new = s.grab("Los representantes de las entidades que forman parte de la Función de Transparencia y Control Social "
                 "tendrán fuero", "la Función Legislativa podrá designar al reemplazo.")
    u.set_para("art-205", "Art. 205.-", new, keep_prefix=art_head(205))
    u.set_para("art-207", "La selección de las consejeras y los consejeros",
               s.grab("Las consejeras y consejeros serán elegidos por sufragio universal",
                      "que regule su organización y funcionamiento."))
    u.insert_after("art-207", "Las consejeras y consejeros serán elegidos por sufragio universal",
                   s.grab("Las consejeras y consejeros deberán ser ciudadanas y ciudadanos con trayectoria",
                          "de partidos o movimientos políticos, durante los últimos cinco años."))
    u.insert_after("art-046", "4. ", s.grab("Las acciones y las penas por delitos contra la integridad sexual",
                                            "serán imprescriptibles"))
    u.insert_after("art-407", None, s.grab("Se prohíbe todo tipo de minería metálica", "centros urbanos y zonas intangibles"))


# ---------------------------------------------------------------- laws and order

LAWS = {
    "referendo-2011": {
        "label": "Referéndum de 2011",
        "title": ("Enmiendas aprobadas en el referéndum del 7 de mayo de 2011 (preguntas 1 a 5); resultados proclamados "
                  "por el Consejo Nacional Electoral"),
        "kind": "referendum", "enacted": "2011-05-07", "published": "2011-07-13", "url": RO_490_2011,
    },
    "enmiendas-2015": {
        "label": "Enmiendas de 2015",
        "title": "Enmiendas a la Constitución de la República del Ecuador (Asamblea Nacional, 3 de diciembre de 2015)",
        "kind": "law", "enacted": "2015-12-03", "published": "2015-12-21", "url": RO_653_2015,
    },
    "referendo-2018": {
        "label": "Referéndum de 2018",
        "title": ("Enmiendas aprobadas en el referéndum del 4 de febrero de 2018 (preguntas 1 a 5; textos en los anexos "
                  "del Decreto Ejecutivo 229, RO Supl. 133 de 4-XII-2017); Resolución PLE-CNE-1-8-2-2018-R"),
        "kind": "referendum", "enacted": "2018-02-04", "published": "2018-02-14", "url": RO_180_2018,
    },
    "cc-018-18-sin-cc": {
        "label": "Sentencia 018-18-SIN-CC",
        "title": ("Corte Constitucional, sentencia 018-18-SIN-CC (casos 0099-15-IN y acumulados): inconstitucionalidad "
                  "por la forma de las enmiendas de 3 de diciembre de 2015; auto de aclaración de 17 de abril de 2019"),
        "kind": "court", "enacted": "2018-08-01", "published": "2019-04-30", "url": RO_EC79_2019,
        "restores": "enmiendas-2015",
    },
}

# (law, in-force day, edit, text source)
STEPS = [
    ("referendo-2011", "2011-07-13", referendo_2011, RO_490_2011),
    ("enmiendas-2015", "2015-12-21", lambda u: enmiendas_2015(u, "a"), RO_653_2015),
    ("enmiendas-2015", "2017-05-24", lambda u: enmiendas_2015(u, "b"), RO_653_2015),
    ("referendo-2018", "2018-02-14", referendo_2018, RO_133_2017),
    ("cc-018-18-sin-cc", "2018-08-02", None, None),
]

NOTES = {
    "2011-07-13": "Registro Oficial, Suplemento 490, 13 de julio de 2011: resultados del referéndum de 7 de mayo de 2011.",
    "2015-12-21": "Registro Oficial, Suplemento 653, 21 de diciembre de 2015 (in force on publication, by its Disposición final).",
    "2017-05-24": ("Enmiendas de 2015, arts. 2 and 4 (arts. 114 and 144 of the Constitution), in force from 24 May 2017 "
                   "by the enmiendas' Disposición transitoria segunda."),
    "2018-02-14": ("Registro Oficial, Suplemento 180, 14 de febrero de 2018 (results); the wording is that of the annexes "
                   "to Decreto Ejecutivo 229, Registro Oficial, Suplemento 133, 4 de diciembre de 2017."),
    "2018-08-02": ("Sentencia 018-18-SIN-CC (1 August 2018, notified 2 August 2018; Registro Oficial, Edición "
                   "Constitucional 79, 30 April 2019). The court's auto of 17 April 2019 says the declaration took effect "
                   "on notification, so the 2015 wording fell and the earlier text came back, except arts. 114 and 144, "
                   "already replaced by the 2018 referendum."),
}

DECISIONS = [
    "Amendments are replayed: each act's own Registro Oficial text says which provision, paragraph (inciso) or numeral "
    "it replaces, adds or removes; parse.py makes exactly that edit. Replacement wording is cut from the act's PDF "
    "between two anchors, and every shorter inserted phrase is checked to occur word for word in the act's PDF.",
    "When an act replaces the first paragraph of an article, or a numeral, it quotes only the words; the printed "
    "label of the provision ('Art. 312.- ', '1. ', 'VIGESIMONOVENA.- ') is kept in front of the new words.",
    "When a quoted replacement closes without a full stop and the act's sentence continues with '.' or ',' after the "
    "closing quote, the full stop is kept with the provision (for example art. 179 in 2011, arts. 114 and 144 in 2018).",
    "Referendum amendments take effect on the publication of the Consejo Nacional Electoral's results in the "
    "Registro Oficial (2011: Supl. 490, 13 July 2011; 2018: Supl. 180, 14 February 2018), which is the day the "
    "commercial consolidations also use. The 2018 annexes are not reprinted with the results; their wording is read "
    "from Decreto Ejecutivo 229 (Supl. 133, 4 December 2017), which put the questions with their annexes to the vote.",
    "The 2015 enmiendas took effect on publication (21 December 2015), except arts. 114 and 144 (second inciso), "
    "which their Disposición transitoria segunda put in force on 24 May 2017; that part is a second commit of the "
    "same law. The enmiendas' own transitional, general and final provisions are part of the amending act, not of "
    "the Constitution, and are not added to it (one commercial consolidation prints them at the end of the text).",
    "Sentencia 018-18-SIN-CC is a court law that restores the pre-2015 text of every provision the 2015 enmiendas "
    "changed and the 2018 referendum did not replace (arts. 104, 142, 158, 211, 212, 229, 261, 264, 326, 370, 372, "
    "384 and transitional provision 1). It takes effect on 2 August 2018, the day of notification, as the court's "
    "auto of 17 April 2019 says; it was published on 30 April 2019. The ruling is printed only as page images in "
    "Edición Constitucional 79; those pages were read (machine OCR, see ai_use) to fix the date and scope, and no "
    "wording is taken from them.",
    "The 2018 referendum's annex 3 also set a transitional regime for the Consejo de Participación Ciudadana y "
    "Control Social; it is not inserted into the Constitution's text and is not added.",
    "Interpretative rulings of the Corte Constitucional (which change no words) and a commercial consolidation's "
    "editorial replacement of 'imputado' by 'procesado' (from the Código Orgánico Integral Penal, which cannot amend "
    "the Constitution) are not commits.",
]


def restore_from(versions: list[dict], law_key: str, units: dict) -> dict:
    """Units the law changed, reset to their text before the law's first version (unless replaced since)."""
    first = next(i for i, v in enumerate(versions) if any(law_key in c for c in v["credits"].values()))
    before = versions[first - 1]["units"]
    touched = {k for v in versions if any(law_key in c for c in v["credits"].values())
               for k, c in v["credits"].items() if law_key in c}
    out = copy.deepcopy(units)
    for k in sorted(touched):
        later = [v for v in versions[first:] if k in v["credits"] and law_key not in v["credits"][k]]
        if later:
            continue  # replaced by a later act (arts. 114 and 144: the 2018 referendum)
        if k in before:
            out[k] = copy.deepcopy(before[k])
        else:
            out.pop(k, None)
    return out


def apply_all(versions: list[dict], laws: dict) -> None:
    for key, law in LAWS.items():
        laws[key] = {"label": law["label"], "title": law["title"], "kind": law["kind"], "enacted": law["enacted"],
                     "published": law["published"], "url": law["url"], "temporary_until": None,
                     "restores": law.get("restores"), "note": law.get("note")}
    for law, day, edit, src in STEPS:
        prev = versions[-1]
        if edit is None:
            new_units = restore_from(versions, LAWS[law]["restores"], prev["units"])
            src_url = LAWS[law]["url"]
        else:
            u = Units(prev["units"])
            edit(u)
            new_units = u.u
            src_url = src
        changed = sorted(k for k in set(prev["units"]) | set(new_units)
                         if prev["units"].get(k) != new_units.get(k))
        if not changed:
            raise SystemExit(f"{law} {day}: no change")
        versions.append({
            "from": day,
            "source_url": src_url,
            "sha256": Src(src_url).sha256 if src_url != RO_EC79_2019 else _sha(src_url),
            "units": dict(sorted(new_units.items(), key=lambda kv: _order(kv[0]))),
            "credits": {k: [law] for k in changed},
            "note": NOTES.get(day),
        })


def _sha(url: str) -> str:
    return hashlib.sha256(fetch.cached(url).read_bytes()).hexdigest()


def _order(key: str) -> tuple:
    groups = ["preambulo", "art-", "disp-general-", "disp-transitoria-", "disp-derogatoria", "regimen-transicion-",
              "disp-final", "titulos"]
    for i, g in enumerate(groups):
        if key.startswith(g):
            return (i, key)
    return (len(groups), key)
