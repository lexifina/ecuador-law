# Ecuador: law history in git

The law of Ecuador as a git history: one file per provision, one commit per law on the day it took effect, and the law that made each change as the commit's author. `git blame` names the law behind every paragraph; `git log` lists every change to an article; checking out a date gives the text in force that day.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `ec/`.

**What is in it now**

| Folder | Act | Versions | History |
| --- | --- | ---: | --- |
| `constitucion/` | Constitución de la República del Ecuador (2008) | 12 | As published on 20 October 2008, then every amendment, court ruling and referendum to 16 November 2025 |
| `codigo-civil/` | Código Civil (Codificación 2005-010) | 22 | From the 2005 codification to 27 June 2024 (see "Código Civil" below) |
| `coip/` | Código Orgánico Integral Penal (2014) | 50 | From the Code as published on 10 February 2014 to 7 August 2026 (see "COIP" below) |
| `codigo-comercio/` | Código de Comercio (2019) | 3 | As published on 29 May 2019, then its amendments to 7 February 2023 (see "Código de Comercio" below) |
| `cogep/` | Código Orgánico General de Procesos (2015) | 18 | From the Code as enacted (in force 22 May 2016) to 7 October 2025; **preview only, not today's text** (see "COGEP" below) |
| `codigo-trabajo/` | Código del Trabajo (Codificación 2005-017) | 38 | From the 2005 codification to 1 August 2025, text-layer reforms only; **preview only, not the law in force** (image-only reforms of 2018-2025 missing; see "Código del Trabajo" below) |
| `lotaip/` | Ley Orgánica de Transparencia y Acceso a la Información Pública (2023) | 2 | As published on 7 February 2023, then sentencia 21-23-IN/24 (29 May 2024) (see "LOTAIP" below) |
| `ley-transformacion-digital/` | Ley Orgánica para la Transformación Digital y Audiovisual (2023) | 3 | As published on 7 February 2023, then the 2025 telecommunications reform (no words changed) and the Ley de Ciberseguridad of 22 May 2026 (see "Transformación Digital" below) |

The Constitution is complete: 444 articles, the preamble, the 30 transitional provisions, the Disposición derogatoria, the 30 articles of the Régimen de transición, the Disposición final, the general provisions added since 2018, and the headings of its titles, chapters and sections (`constitucion/titulos.md`).

Its history, all read from the Registro Oficial:

| In force | Law | What it did |
| --- | --- | --- |
| 2008-10-20 | Constitución de 2008 | Approved by referendum on 28 September 2008; in force on publication (RO 449) |
| 2011-07-13 | Referéndum de 2011 | Arts. 77, 179, 180, 181, 312, transitional provision 29, Régimen de transición art. 20 |
| 2015-12-21 | Enmiendas de 2015 | Arts. 104, 142, 158, 211, 212, 229, 261, 264, 326, 370, 372, 384, transitional provision 1 |
| 2017-05-24 | Enmiendas de 2015 | Arts. 114 and 144 (indefinite re-election), deferred to this day by the enmiendas themselves |
| 2018-02-14 | Referéndum de 2018 | Arts. 46, 112, 114, 144, 205, 207, 233, 407; general provisions 1 and 2 |
| 2018-08-02 | Sentencia 018-18-SIN-CC | Struck down the 2015 enmiendas for their procedure: the earlier text returns (court ruling, `Restores:`) |
| 2023-02-05 | Referéndum de 2023 | All eight proposals rejected: no words changed |
| 2024-04-21 | Referéndum de 2024, questions D and E | Rejected: no words changed (arts. 327, 422) |
| 2024-05-09 | Reforma parcial and Referéndum de 2024 | Arts. 79, 86, 158; general provision 3; the reform's own transitional and final provisions |
| 2025-11-16 | Referéndum y consulta popular de 2025 | All four questions rejected: no words changed (arts. 5, 110, 118, 444) |

More acts follow as their history can be shown from official text; see "What it does not show".

## A lawyer's questions as git commands

| Question | Command |
| --- | --- |
| What did art. 158 say on 1 January 2017? | `python tools/vigente_el.py 2017-01-01 constitucion 158` |
| The same, and which law wrote it | `python tools/vigente_el.py --law 2017-01-01 constitucion 158` |
| The same, with raw git (bash) | `git show $(git rev-list -1 --before="2017-01-01T23:59:59Z" main -- constitucion/art-158.md):constitucion/art-158.md` |
| The same, in PowerShell | `$r = git rev-list -1 --before="2017-01-01T23:59:59Z" main -- constitucion/art-158.md; git show "$($r):constitucion/art-158.md"` |
| Which law wrote each paragraph of art. 77? | `git blame constitucion/art-077.md` |
| Every change to art. 114 (re-election), word by word | `git log -p --word-diff constitucion/art-114.md` |
| Every law in the record, in order | `git log --reverse --format="%ad %an" --date=short main` |
| Everything one law changed | `git show law/referendo-2018` (tags `law/<key>` mark each law's commit) |
| The whole Constitution on a date | `python tools/vigente_el.py 2016-01-01 constitucion` |
| Laws passed but not yet in force | `git log main..futuro` (the branch exists only when there are any) |

After a rebuild, refresh tags with `git fetch --force --tags`: a plain fetch keeps stale tags.

## Dates

- Each commit is dated at **noon, America/Guayaquil, on the day the change took effect** (the in-force date). Enactment and publication dates are trailers (`Enacted:`, `Published:`), and the in-force day is in `In-force:`, which the tools read.
- **Default rule.** A law binds from its promulgation in the Registro Oficial unless it sets another day (Código Civil art. 6). The Constitution's own Disposición final put it in force on its publication, 20 October 2008; each enmienda since 2015 says the same of itself.
- **Referendums** take effect when the Consejo Nacional Electoral's results are published in the Registro Oficial (13 July 2011, 14 February 2018, 9 May 2024).
- **The 2015 enmiendas** took effect on 21 December 2015, except the re-election articles (114 and 144), which they themselves deferred to 24 May 2017.
- **Sentencia 018-18-SIN-CC** (1 August 2018) took effect on its notification, 2 August 2018, as the Court's auto of 17 April 2019 explains; it was published on 30 April 2019. The 2015 wording fell and the earlier text came back, except arts. 114 and 144, which the 2018 referendum had already replaced.
- **Rejected referendums** change no words; they are commits with `Words-changed: no`, dated on the day of the vote and credited to the provisions their annexes would have changed.
- `--before="YYYY-MM-DD"` alone uses your clock's time of day, so a law that took effect that day may be missed before noon. Use `T23:59:59Z` as above, or the tool.

## How it is checked

- Every version is read back from git on the day it took effect and on the day before (`tools/check_repo.py`); both must match `corpus.json`. Results are in `REPRODUCE.md`.
- Health checks: no merge commits on `main`, commit dates never go backwards, nothing dated in the future, and every commit's trailers parse with `git interpret-trailers --parse`.
- **No official consolidated text exists.** The Registro Oficial publishes the gazette editions only. The history is a replay: the 2008 text from Registro Oficial No. 449, then each amending act, ruling and referendum read from its own edition, applying exactly the edits it states. Replacement wording is cut from the act's PDF between two anchors, and every shorter inserted phrase is checked to occur word for word in that PDF.
- The replay was reconciled, for reading only, with a commercial consolidation (Lexis Finder, last amendment 25 January 2021, as republished by the Ministerio de Defensa): on that day 430 of the 444 articles have exactly the same words. The 14 others differ only where the consolidation corrected the gazette's spelling ("ei" for "el" in arts. 11 and 73, "étnia", "periodo", "unicamente", "unica", "valida"), which this record keeps as the gazette printed it, or where the consolidation's notes break its article boundaries (arts. 146, 148, 208, 313, 379, whose words match in full). No text was copied from it.
- Two enmiendas (2021, art. 272; 2024, art. 138) are printed in the Registro Oficial only as page images and are not in this record; see "What it does not show".

## What "author" means

The author of a commit is the law that made the change, with an e-mail address that cannot exist (`referendo-2018@registroficial.invalid`), so `git blame` and `git log --author` name laws. The committer is always `Lexifina <ecuador-law@lexifina.com>`. A change that no act explains would be committed by the publisher, the Registro Oficial, and labelled "unexplained"; there are none.

Blame credits whole lines (one paragraph per line). Use `git log -p --word-diff` to see exactly which words a law changed.

## What it does not show

- **Not possible: two enmiendas in force are missing.** The enmienda of 2021 (art. 272, new numeral 4 on rural roads; Registro Oficial, Tercer Suplemento 377, 25 January 2021) and the enmienda of 2024 (art. 138, partial veto, ratification by absolute majority; Tercer Suplemento 568, 30 May 2024) are printed in the Registro Oficial only as page images, and no machine-readable official copy was found. Their words are never transcribed by OCR or by a model, so this record does not carry them: **from 25 January 2021 art. 272 and from 30 May 2024 art. 138 here show the earlier wording, which is not the law in force.** Read those two articles in the Registro Oficial editions named above.
- **Published acts so far:** the Constitution, the Código Civil, the Código Orgánico Integral Penal (COIP), the LOTAIP (2023) and the Ley Orgánica para la Transformación Digital y Audiovisual (2023); the Código de Comercio, the COGEP and the Código del Trabajo are built on the `preview` branch only. The data protection law of 2021 is printed only as page images, so it cannot be built from the gazette's text.
- **Spelling is the gazette's.** Where the Registro Oficial printed a typo ("ei", "Ileva"), the record keeps it.
- **Court rulings that interpret** the Constitution without striking words (several since 2009) are not commits.
- **The 2015 enmiendas' own transitional and final provisions**, and the 2018 transitional regime for the Consejo de Participación Ciudadana y Control Social, belong to the amending acts, not to the Constitution's text, and are not added. The 2024 reform did add its own transitional and final provisions to the Constitution, and they are here as `reforma-2024-*`.
- **Proposals still in progress** (the Corte Constitucional's 2025–2026 rulings on the route for further amendments) are not in force and are not recorded.
- The Kichwa and Shuar versions are not included.

## Código Civil (codificación 2005)

`codigo-civil/` holds the Civil Code as codified in 2005 (Codificación 2005-010, Registro Oficial Suplemento 46, 24 June 2005), with 22 versions to 27 June 2024. Each later version replays one amending act, cut from the text layer of that act's own Registro Oficial edition, in order of entry into force (Código Civil art. 6, unless the act sets a later date: COGEP 22 May 2016, Código Orgánico del Ambiente 12 April 2018).

No official consolidated text of the Code exists after 2005. Today's text was compared, for reading only, with the Ediciones Legales consolidation published on gob.ec (last reform 17 June 2025). 2,362 of 2,428 articles agree. Each of the 66 that disagree is explained in REPRODUCE.md (decisions).

### Changes that are missing (not applied)

These acts are published only as page images, with no text layer, and this repository does not OCR. Each one has a commit on its date that changes no words and says "NOT APPLIED". From that date on, the articles listed keep their earlier wording, which is no longer the law:

| In force | Act | Articles whose current wording is missing |
| --- | --- | --- |
| 2019-07-08 | Sentencia 10-18-CN/19 (Edición Constitucional 96) | 81 |
| 2021-05-14 | Ley Orgánica de Extinción de Dominio (Quinto Supl. 452) | 603 |
| 2021-10-19 | Ley Reformatoria al Código Civil, CONVEMAR (Quinto Supl. 561) | 606, 609, 610, 613 |
| 2024-01-05 | Ley Orgánica de Salud Mental (Supl. 471) | heading of Título XXII; 192, 478-482, 484-487, 489, 496, 518, 738, 1012, 1463, 2219, 2409 |
| 2024-02-09 | Ley Orgánica para el Ahorro y la Monetización de Recursos (Segundo Supl. 496) | 603 |
| 2024-03-13 | Ley Orgánica Reformatoria de la LOGIDAC (Supl. 517) | 21 |
| 2024-06-27 | Ley Orgánica de reparación a familiares de víctimas de femicidio (Tercer Supl. 588) | 1010 |

Two rulings could not be read because the portal's links for their suplementos serve another edition: Resolución TC 002-06-DI (19 May 2006, art. 260) and Sentencia 025-10-SCN-CC (23 September 2010, art. 257). Both articles were repealed on 19 June 2015, which is applied.

The article lists come from the editorial indexes (Ediciones Legales 2025, Lexis 2017). No wording is taken from them.

### En español

`codigo-civil/` contiene la Codificación 2005-010 del Código Civil y 22 versiones hasta el 27 de junio de 2024, cada una tomada del texto del Registro Oficial que publicó la reforma. No existe una codificación oficial posterior a 2005. Las reformas publicadas solo como imagen (2019-2024, tabla anterior) no están aplicadas: los artículos indicados conservan su texto anterior desde esa fecha.

## Código Orgánico Integral Penal (COIP, 2014)

`coip/` holds the Criminal Code as enacted (Registro Oficial Suplemento 180, 10 February 2014; in force 10 August 2014, 180 days after publication) and 50 versions to 7 August 2026. Each later version replays one amending act or constitutional ruling, cut from the text layer of its own Registro Oficial edition, on its in-force day; no version carries wording from an act published after that day. The largest are the 2019 reform (Supplement 107, 118 provisions, in force 22 June 2020) and the 2023 security law (Supplement 279, 85 provisions, in force 13 May 2023).

**Coverage and gaps.** Reforms from 2023 on were indexed from two editorial consolidations (Ediciones Legales to 29 April 2026, Andina Ediciones to 24 August 2026), read only as indexes, and from the Asamblea Nacional's list of published laws: every law on that list from 2023 to October 2026 was downloaded and its text layer searched for the Code. Most laws since 2021 are printed only as page images, so the text of the Code today is far from complete:

- 22 acts and rulings are **not applied** (table below): their files keep the earlier wording, which is not the law.
- When an image-only reform has amended an article, a later act's partial amendment of it (a numeral, an inciso, a phrase) is not applied either, so no version grafts new words onto outdated text. This leaves out art. 47 numeral 24 and art. 430.1 (2023), arts. 47, 77, 536 (Solidaridad 2025), arts. 45, 698, 699 (Integridad Pública 2025), arts. 698, 699 (2026 prison reform) and art. 232 (2026 cybersecurity law). Whole articles an act substitutes or adds are always applied.
- Laws published after 24 August 2026 as page images could not be checked for COIP reforms and may be missing.
- The Ley Orgánica de Solidaridad Nacional (June 2025) and the penal reforms of the Ley Orgánica de Integridad Pública (June 2025) are applied as published and undone on 3 October 2025, when the Corte Constitucional's rulings 51-25-IN/25 and 52-25-IN/25 annulled them with retroactive effect.
- The internal-armed-conflict law of March 2024 (Supplement 516) and the 21 April 2024 referendum changed no words of the Code; the referendum's penal questions were carried out by the July 2024 law in the table.

### Changes that are missing (not applied)

These acts are printed only as page images, with no text layer, and this repository does not OCR. Each has a commit on its date that changes no words and says "NOT APPLIED". From that date on, the articles listed keep their earlier wording, which is no longer the law:

| In force | Act | Articles whose current wording is missing |
| --- | --- | --- |
| 2017-12-29 | Ley Orgánica para la Reactivación de la Economía (Segundo Supl. 150) | 299 |
| 2019-06-03 | Corte Constitucional, Edición Constitucional 90 | 202 |
| 2019-08-15 | Sentencia 5-13-IN/19 (Edición Constitucional 6) | 581 |
| 2019-11-13 | Corte Constitucional, Edición Constitucional 21 | 653 |
| 2021-02-05 | Ley Reformatoria de la Ley Orgánica de Movilidad Humana (Tercer Supl. 386) | 91 |
| 2021-02-17 | Ley Reformatoria del COIP en materia anticorrupción (Segundo Supl. 392) | 45, 47, 49, 60, 68, 69, 77, 270, 278, 280, 281, 285, 286, 430.1, 430.2, 536, 581, 630, 698, 699; new 294.1, 320.1, 422.1, 550.1, 581.1 |
| 2021-05-14 | Ley Orgánica de Extinción de Dominio (Quinto Supl. 452) | 452 |
| 2021-08-10 | Ley Reformatoria de la Ley de Tránsito (Quinto Supl. 512) | 17, 388-392, 404 |
| 2021-08-27 | Ley contra el comercio ilícito (Quinto Supl. 525) | 60, 65, 208 A, 267, 299, 300, 301, 303, 317; new 208 B, 208 C |
| 2021-08-30 | Ley Reformatoria del COIP sobre violencia sexual digital (Cuarto Supl. 526) | 47, 103, 157, 166, 169, 170, 171, 175, 179, 230, 232, 234, 396, 497; new 154.2, 154.3, 172.1, 234.1-234.4, 477.1 |
| 2021-10-13 | Sentencia 8-20-CN/21 (strikes words the 2021 anticorruption reform added) | 536 |
| 2022-08-22 | Ley Orgánica que regula el Uso Legítimo de la Fuerza (Tercer Supl. 131) | 30.1, 47, 274, 275, 293, 537, 685, 686; new 30.2, 533.1 |
| 2024-01-05 | Ley Orgánica de Salud Mental (Supl. 471) | 76 |
| 2024-02-09 | Ley para el Ahorro y la Monetización de Recursos (Segundo Supl. 496) | 69, 443 |
| 2024-06-27 | Ley de Reparación a Familiares de Víctimas de Femicidio (Tercer Supl. 588) | 78.1, 441, 520, 558.1, 570; new 77.1 |
| 2024-07-12 | Ley para la Aplicación de la Consulta Popular de 2024 (Supl. 599) | 92, 140, 143, 162, 260, 317, 362, 366, 367, 369, 698, 699; new 360.1, 474.2-474.4 |
| 2024-12-10 | Decreto Ley 477, Mejora Recaudatoria (Quinto Supl. 700) | 69, 552 |
| 2025-03-27 | Sentencia 94-24-IN/25 (annuls Decreto Ley 477 with retroactive effect) | 69, 552 |
| 2025-05-14 | Ley Reformatoria de la Ley de Tránsito (Quinto Supl. 38) | 388 |
| 2025-10-24 | Ley Reformatoria de la Ley Orgánica de Movilidad Humana (Séptimo Supl. 151) | 12, 61, 667.1, 729, 730; new 633.1 |
| 2026-07-01 | Ley contra el uso delictivo de uniformes (Quinto Supl. 316) | 47, 69; new 362.1, 362.2 |
| 2026-08-07 | Ley Orgánica de Extradición (Quinto Supl. 343) | 541 |

Sentencia 129-21-IN/25 (Edición Constitucional 78, 2025) strikes words of art. 294.1, which the image-only 2021 anticorruption reform added; this record does not have that article, so the ruling has no commit.

The acts to 2023 were found through two editorial consolidations, read only as indexes (Ediciones Legales to October 2021, Lexis to March 2023). On 13 October 2021 the replayed text agrees with the Ediciones Legales consolidation in 663 of 754 articles; each difference is classified in REPRODUCE.md (decisions).

### En español

`coip/` contiene el Código Orgánico Integral Penal publicado en el Suplemento 180 (10-II-2014, vigente desde el 10-VIII-2014) y 50 versiones hasta el 7 de agosto de 2026, cada una tomada del texto del Registro Oficial que publicó la reforma o la sentencia. Las reformas publicadas solo como imagen (tabla anterior) no están aplicadas; tampoco las reformas parciales posteriores de los artículos que esas reformas dejaron desactualizados. Las leyes publicadas solo como imagen después del 24 de agosto de 2026 no se han podido revisar. La Ley de Solidaridad Nacional y las reformas penales de la Ley de Integridad Pública (2025) se aplican y se deshacen el 3-X-2025, con las sentencias 51-25-IN/25 y 52-25-IN/25.

## Código de Comercio (2019)

`codigo-comercio/` holds the Código de Comercio as published in the Registro Oficial, Suplemento 497 (29 May 2019), in force on publication: 1,348 articles, its general, transitional, repealing and final provisions, and its headings (`codigo-comercio/titulos.md`). The Asamblea Nacional's list of laws from 2019 to October 2026 was screened, law by law, for amendments to the Code in each law's gazette text; the Lexis consolidation of 10 December 2020 was read as an index only.

| In force | Law | What it did |
| --- | --- | --- |
| 2019-05-29 | Código de Comercio | As enacted |
| 2020-12-10 | Ley de Modernización a la Ley de Compañías (Tercer Supl. 347) | **Not applied:** printed only as page images. It adds Capítulo Tercero, arts. 607.1-607.6 (asociación o cuentas de participación), which are missing here from this day |
| 2023-02-07 | Ley Orgánica para la Transformación Digital y Audiovisual (Tercer Supl. 245) | Arts. 78-80, 84, 85, 88, 90, 92, 95, 96, 109, 112, 126, 272; new articles after 112, 113 and 189 (electronic títulos valor) |

- Many laws since 2020 are printed only as page images, so whether they amend the Code could not be read. A later consolidation is reported to name 13 October 2025 as its last reform (the Ley Orgánica Reformatoria del Código Orgánico Monetario y Financiero, Sexto Supl. 142, image-only); any change it made is missing.
- On 10 December 2020 the text agrees with the Lexis consolidation in 1,321 of 1,348 articles; each difference is classified in REPRODUCE.md (decisions).

### En español

`codigo-comercio/` contiene el Código de Comercio publicado en el Suplemento 497 (29-V-2019) y sus reformas hasta el 7-II-2023, tomadas del texto del Registro Oficial. La Ley de Modernización a la Ley de Compañías (2020), publicada solo como imagen, no está aplicada: faltan los arts. 607.1 a 607.6. Las reformas posteriores publicadas solo como imagen (posiblemente la de 13-X-2025) no se han podido leer.

## Código Orgánico General de Procesos (COGEP, 2015)

**Preview only.** `cogep/` is built on the `preview` branch and not published on `main`, because its current text cannot be shown to equal an official or official-publisher consolidated text: four of its amending acts and rulings were printed only as page images, which this repository does not OCR, no consolidation newer than 7 February 2023 was found, and 50 of the 97 laws published from 2023 to October 2026 are image-only, so whether they amend the Code is unknown. Some gazette editions since 2024 set their text in a symbol font whose characters sit at a fixed offset from the printed ones; those are read from the text layer by undoing the offset (not OCR), which is how the 2025 procurement reform is applied.

The Code as published in the Registro Oficial, Suplemento 506 (22 May 2015): 439 articles, its general, transitional, amending, repealing and final provisions, and its headings (`cogep/titulos.md`). It took effect twelve months after publication (22 May 2016), which is the date of the first version; the provisions its Disposición final segunda put in force earlier (abandono, citación, copias certificadas, inquilinato, remate) are not dated separately. Amending acts were found from the notes of a Lexis consolidation to 7 February 2023 (read as an index only) and, after it, by searching the gazette text of every law on the Asamblea Nacional's list.

| In force | Law or ruling | What it did |
| --- | --- | --- |
| 2016-05-22 | Código Orgánico General de Procesos | As enacted |
| 2016-05-22 | Ley de Incentivos para Asociaciones Público-Privadas (Supl. 652, 2015) | Art. 329 (before the Code took effect) |
| 2016-12-09 | Código Orgánico de la Economía Social de los Conocimientos (Supl. 899) | New article after art. 133 |
| 2017-05-31 | Corte Constitucional, Edición Constitucional 1 | **Not applied** (image-only): art. 137 |
| 2017-11-14 | Sentencia 006-17-SCN-CC (Edición Constitucional 19) | **Not applied** (image-only): words added to arts. 23 and 25; arts. 27, 28 |
| 2018-07-07 | Código Orgánico Administrativo (Segundo Supl. 31, 2017) | Arts. 14 A, 53, 326, 327, 370 A; general provision 4 |
| 2018-08-21 | Ley Orgánica para el Fomento Productivo (Supl. 309) | Arts. 102-106 ('laudo arbitral'); repealing provision 13 |
| 2019-06-26 | Ley Orgánica Reformatoria del COGEP (Supl. 517) | 70 articles (recusación, citación, abandono, apelación, casación, procedimiento sumario, títulos de ejecución) |
| 2020-12-08 | Ley Orgánica Reformatoria del COFJ (Supl. 345) | **Not applied** (image-only): arts. 53, 55, new 53.1 |
| 2021-02-23 | Sentencia 92-15-IN/21 | Last inciso of art. 324 |
| 2021-04-09 | Sentencia 19-20-CN/21 | Conditioned reading of art. 22 num. 8: no words changed |
| 2021-05-14 | Ley Orgánica de Extinción de Dominio (Quinto Supl. 452) | **Not applied** (image-only): arts. 1, 36 |
| 2021-11-29 | Ley Orgánica para el Desarrollo Económico (Tercer Supl. 587) | **Not applied** (image-only): arts. 10, 76, 317, 324 |
| 2022-07-15 | Sentencia 36-16-IN/22 | Art. 27 as published in 2015 (already replaced): no words changed |
| 2023-02-07 | Ley Orgánica para la Transformación Digital y Audiovisual (Tercer Supl. 245) | Arts. 4, 53, 55, 55.1, 115, 193, 194, 196, 347, 363, 373, 405 (art. 25 not applied: see below) |
| 2025-06-26 | Ley Orgánica de Integridad Pública (Tercer Supl. 68) | Arts. 96, 146, 326, 327, 332 |
| 2025-10-03 | Sentencia 52-25-IN/25 | The whole law unconstitutional: the earlier wording of those five articles returns |
| 2025-10-07 | Ley Orgánica Reformatoria a la Ley Orgánica del Sistema Nacional de Contratación Pública (Cuarto Supl. 140) | Arts. 96, 146, 326, 327, 332 again, in the same words |

- Arts. 1, 10, 23, 25, 36, 76, 317 and 324 keep wording that is not the law in force after the dates above, and art. 53.1 is missing; the 2023 amendment of incisos 2 and 4 of art. 25 is not applied either, because the article already lacked the 2017 ruling's words.
- On 7 February 2023 the text agrees with the Lexis consolidation in 358 articles; every difference is classified in REPRODUCE.md (decisions).

### En español

`cogep/` contiene el Código Orgánico General de Procesos (Suplemento 506, 22-V-2015, vigente desde el 22-V-2016) y sus reformas hasta el 7-X-2025, tomadas del texto del Registro Oficial. Solo está en la rama `preview`: cuatro reformas y sentencias se publicaron solo como imagen (Edición Constitucional 1 y 19 de 2017, Suplemento 345 de 2020, Quinto Suplemento 452 y Tercer Suplemento 587 de 2021) y no están aplicadas, y no se halló una codificación posterior a febrero de 2023; el texto final no es el vigente.

## Código del Trabajo (Codificación 2005)

**Preview only, and the text is not the law in force: it follows every reform with a text layer up to 1 August 2025 but misses image-only reforms from 2018 on (see below), and nothing after 1 August 2025 could be applied.** `codigo-trabajo/` holds the Codificación 2005-017 (Registro Oficial, Suplemento 167, 16 December 2005) and every act and ruling that amended it, each applied from its own gazette text: the Leyes 2006-28 (with its fe de erratas), 2006-39, 2006-40, 2006-48, 2006-60 and 2007-77, the codification's fe de erratas (2006), the Mandato Constituyente No. 8 (2008), the 2009 laws on maternity leave and on the monthly fondo de reserva, the Código de la Producción (2010), sentencia 031-10-SCN-CC (2011), the Ley para la Defensa de los Derechos Laborales (2012), the Código Orgánico Monetario y Financiero (2014), the Ley Orgánica para la Justicia Laboral (2015, about 60 provisions; its cap on profit shares from 1 January 2016), the COGEP (2015, mostly in force 22 May 2016), the laws on youth employment (2016), public holidays (2016), the public sector (2017), workplace harassment (2017), violence against women (2018), Fomento Productivo (2018), the COGEP reform (2019), Apoyo Humanitario (2020, teletrabajo), sentencia 36-19-IN/21, the laws of January and February 2023 (Juventudes, Economía Violeta, workers' rights), the Ley del Derecho al Cuidado Humano (May 2023) and the law of 20 June 2025 on workers with disabilities and catastrophic illnesses, and the law of 1 August 2025 on paid domestic work (heading of Título III, Capítulo I; arts. 262, 262.1, 263, 266), whose articles are set in a symbol font and are read from the text layer by undoing a fixed character offset (not OCR).

Not applied, because the gazette edition is page images only (no OCR): the Corte Constitucional's ruling of April 2018 on arts. 97.1 and 459; the law of 16 May 2024 on violence and harassment at work (arts. 42, 44, 46.1, 172, 173, 545 keep their earlier words); and the law of 27 June 2024 on families of femicide victims (a new art. 152.3 is missing). About 40 image-only laws published after June 2024 could not be checked for reforms of the Code at all. No official consolidation reaches today: the newest from a public body is the SRI's of 27 June 2024, which this record matches except for the differences listed in `REPRODUCE.md` (decisions). **The files of `codigo-trabajo/` are therefore not the law in force today.**

### En español

`codigo-trabajo/` contiene la Codificación 2005-017 del Código del Trabajo y todas sus reformas publicadas con capa de texto en el Registro Oficial hasta el 1-VIII-2025 (incluida la ley sobre el trabajo del hogar), tomadas del texto de cada edición. No se aplican las reformas cuya edición es solo imagen (sentencia de abril de 2018 sobre los arts. 97.1 y 459; leyes de 16-V-2024 sobre violencia y acoso laboral y de 27-VI-2024 sobre víctimas de femicidio), ni se pudieron revisar unas 40 leyes posteriores a junio de 2024 publicadas solo como imagen: el texto final no es el vigente. Solo está en la rama `preview`.

## LOTAIP (Ley Orgánica de Transparencia y Acceso a la Información Pública, 2023)

`lotaip/` holds the transparency and access-to-information law as published in the Registro Oficial, Segundo Suplemento 245 (7 February 2023), in force on publication: its 44 articles, general, transitional, amending, repealing and final provisions, and the headings of its chapters and sections (`lotaip/titulos.md`). It repealed the LOTAIP of 2004, which is not part of this history. Its amending provisions (reforms of other laws) are kept as printed.

| In force | Law or ruling | What it did |
| --- | --- | --- |
| 2023-02-07 | Ley Orgánica de Transparencia y Acceso a la Información Pública | As enacted |
| 2024-05-29 | Sentencia 21-23-IN/24 (Edición Constitucional 367) | Transitional provision 9 (web forms with the requester's personal data) struck down and removed |

- The ruling was decided on 25 April 2024; like the repository's other abstract-control rulings it is dated on its publication.
- Every word is cut from the gazette's own text. The text in force today was compared, for reading only, with a Lexis consolidation (last reform 29 May 2024): the differences are that publisher's typesetting, listed in `REPRODUCE.md`.
- No later amendment was found in the text of the 97 laws the Asamblea lists for 2023-2026; 50 of them are printed only as page images and could not be read.

### En español

`lotaip/` contiene la Ley Orgánica de Transparencia y Acceso a la Información Pública (Segundo Suplemento 245, 7-II-2023) y la sentencia 21-23-IN/24 (Edición Constitucional 367, 29-V-2024), que expulsa la disposición transitoria novena. Todo el texto proviene del Registro Oficial.

## Ley Orgánica para la Transformación Digital y Audiovisual (2023)

`ley-transformacion-digital/` holds the law as published in the Registro Oficial, Tercer Suplemento 245 (7 February 2023), in force on publication: arts. 1-88 (Libro II, arts. 35-88, reforms other laws and is kept as printed), its general, transitional and final provisions, and the headings of its books and titles. Where this repository holds a law it reformed (Código de Comercio, COGEP), the reform is also applied there.

| In force | Law | What it did |
| --- | --- | --- |
| 2023-02-07 | Ley Orgánica para la Transformación Digital y Audiovisual | As enacted |
| 2025-06-13 | Ley Orgánica Reformatoria a la Ley Orgánica de Telecomunicaciones (Quinto Supl. 59) | Repeals the transitional provision art. 41 had added to the telecommunications law: no words of this law changed (art. 41) |
| 2026-05-22 | Ley Orgánica para el Fortalecimiento de la Ciberseguridad (Quinto Supl. 290) | Arts. 1, 2, 3, 5, 32, 33; new art. 7-A; new Título (...) De la Ciberseguridad, arts. 20-A to 20-Z |

- Parts of the 2026 act are set in a symbol font whose characters sit at a fixed offset from the printed ones; they are read from the gazette's text layer by undoing the offset (no OCR).
- The text in force on 31 December 2025 was compared, for reading only, with a Lexis consolidation (last reform 13 June 2025): the differences are that publisher's typesetting and its treatment of art. 41, listed in `REPRODUCE.md`.
- Laws published from June 2026 on that are printed only as page images could not be checked for amendments.

### En español

`ley-transformacion-digital/` contiene la Ley Orgánica para la Transformación Digital y Audiovisual (Tercer Suplemento 245, 7-II-2023), la derogatoria de 2025 que no cambia su texto (art. 41) y la reforma de la Ley Orgánica para el Fortalecimiento de la Ciberseguridad (Quinto Suplemento 290, 22-V-2026). Todo el texto proviene del Registro Oficial.

## How it is built

Lexifina reads the sources listed here and records each act's dated versions, and the laws that made each change, in one corpus file. `tools/build.py` writes this repository from that file, and the same corpus always gives the same commit hashes; `REPRODUCE.md` gives the details and the checks. A model (Claude) wrote Lexifina's code; it wrote no legal text, and no model runs when the history is built.

No generative AI model wrote legal text. Claude Opus 5.5 wrote the scripts, chose the sources and wrote the map of which provision each act changes. No OCR output is legal text here; see `REPRODUCE.md`.

## Sources

| Source | Kind | Past versions | Names the amending act | Bulk | Notes |
| --- | --- | --- | --- | --- | --- |
| [Registro Oficial](https://www.registroficial.gob.ec) | Official gazette (run by the Corte Constitucional) | gazette editions only | no | month listings and site search; one PDF per edition | Used. |
| [Corte Constitucional](https://www.corteconstitucional.gob.ec) | Constitutional court | n/a | n/a | no | Rulings are read from their Registro Oficial editions |
| [Asamblea Nacional](https://www.asambleanacional.gob.ec) | Legislature | n/a | n/a | no | Not needed: enmiendas are read from the gazette |
| Lexis Finder consolidation (via defensa.gob.ec) | Commercial consolidation | no | yes, per provision | n/a | Reconciliation only; no text copied |

Research guides that cover every country: [GlobaLex](https://www.nyulawglobal.org/globalex/) and the [Law Library of Congress Guide to Law Online](https://www.loc.gov/research-centers/law-library-of-congress/researcher-resources/guide-to-law-online/).

## Licence

The legal texts are official texts of the Republic of Ecuador, as published in the Registro Oficial (www.registroficial.gob.ec). The Registro Oficial states no licence for its editions; official legal texts are public. The scripts, tables and documentation are by Lexifina, under the terms in `LICENSE`.

This repository is not legal advice and not an official publication.

## En español

Historia del derecho ecuatoriano en git: un archivo por disposición y un commit por ley, fechado el día de su entrada en vigencia y firmado por la ley, sentencia o referéndum que hizo el cambio (`git blame` nombra la norma de cada párrafo). Contiene la Constitución de la República de 2008 tal como se publicó en el Registro Oficial No. 449 (20 de octubre de 2008) y todas sus modificaciones: el referéndum de 2011, las enmiendas de 2015 (y su caída por la sentencia 018-18-SIN-CC), el referéndum de 2018, la reforma parcial y el referéndum de 2024; los referéndums rechazados de 2023, 2024 (preguntas D y E) y 2025 constan como commits sin cambio de texto.

- Texto vigente en una fecha: `python tools/vigente_el.py 2017-01-01 constitucion 158`
- Regla supletoria de vigencia: la ley rige desde su promulgación en el Registro Oficial, salvo que ella disponga otra cosa (Código Civil, art. 6).
- Fuente: Registro Oficial. No existe una codificación oficial actualizada; cada versión se reconstruye aplicando el texto de cada norma modificatoria publicado en el Registro Oficial. Ningún modelo de IA generativa escribió texto legal y no se usa texto obtenido por OCR.
- No fue posible: las enmiendas de 2021 (art. 272, numeral 4; Tercer Suplemento 377, 25-I-2021) y de 2024 (art. 138; Tercer Suplemento 568, 30-V-2024) se publicaron solo como imagen y no se halló copia oficial legible por máquina; desde esas fechas este registro muestra el texto anterior de esos dos artículos, que no es el vigente.
