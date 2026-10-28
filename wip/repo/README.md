# Ecuador: law history in git

The law of Ecuador as a git history: one file per provision, one commit per law on the day it took effect, and the law that made each change as the commit's author. `git blame` names the law behind every paragraph; `git log` lists every change to an article; checking out a date gives the text in force that day.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `ec/`.

**What is in it now**

| Folder | Act | Versions | History |
| --- | --- | ---: | --- |
| `constitucion/` | Constitución de la República del Ecuador (2008) | 12 | As published on 20 October 2008, then every amendment, court ruling and referendum to 16 November 2025 |

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
| 2021-01-25 | Enmienda de 2021 | Art. 272, numeral 4 |
| 2023-02-05 | Referéndum de 2023 | All eight proposals rejected: no words changed |
| 2024-04-21 | Referéndum de 2024, questions D and E | Rejected: no words changed (arts. 327, 422) |
| 2024-05-09 | Reforma parcial and Referéndum de 2024 | Arts. 79, 86, 158; general provision 3; the reform's own transitional and final provisions |
| 2024-05-30 | Enmienda de 2024 | Art. 138 (presidential veto) |
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
- Two enmiendas (2021, art. 272; 2024, art. 138) are printed in the Registro Oficial only as page images. Their words were read by OCR, corrected word by word against the page images (each correction listed in `tools/amendments.py`), and checked against the vocabulary of the 2008 text. The new art. 138 differs from the old only where the enmienda says it does, which corroborates the reading.

## What "author" means

The author of a commit is the law that made the change, with an e-mail address that cannot exist (`referendo-2018@registroficial.invalid`), so `git blame` and `git log --author` name laws. The committer is always `Lexifina <ecuador-law@lexifina.com>`. A change that no act explains would be committed by the publisher, the Registro Oficial, and labelled "unexplained"; there are none.

Blame credits whole lines (one paragraph per line). Use `git log -p --word-diff` to see exactly which words a law changed.

## What it does not show

- **Only the Constitution so far.** Other acts (the Código Civil, the data protection law) need the same replay from the gazette, act by act; they are added only when every version can be shown from the Registro Oficial.
- **Spelling is the gazette's.** Where the Registro Oficial printed a typo ("ei", "Ileva"), the record keeps it.
- **Court rulings that interpret** the Constitution without striking words (several since 2009) are not commits.
- **The 2015 enmiendas' own transitional and final provisions**, and the 2018 transitional regime for the Consejo de Participación Ciudadana y Control Social, belong to the amending acts, not to the Constitution's text, and are not added. The 2024 reform did add its own transitional and final provisions to the Constitution, and they are here as `reforma-2024-*`.
- **Proposals still in progress** (the Corte Constitucional's 2025–2026 rulings on the route for further amendments) are not in force and are not recorded.
- The Kichwa and Shuar versions are not included.

## How it is built

`tools/fetch.py` downloads every gazette edition once through curl (one request per second, cached by the sha256 of the URL), `tools/parse.py` with `tools/rotext.py` and `tools/amendments.py` turns the cache into `corpus.json`, and the shared builder `tools/build.py` writes the history with `git fast-import`. The same corpus always gives the same hashes. `REPRODUCE.md` records every command, tool version, data hash and decision, and the result of a hash-for-hash rebuild.

No generative AI model wrote legal text. Claude Opus 5.5 wrote the scripts, chose the sources and wrote the map of which provision each act changes; OCR read three image-only pages; see `REPRODUCE.md`.

## Sources

| Source | Kind | Past versions | Names the amending act | Bulk | Notes |
| --- | --- | --- | --- | --- | --- |
| [Registro Oficial](https://www.registroficial.gob.ec) | Official gazette (run by the Corte Constitucional) | gazette editions only | no | month listings and site search; one PDF per edition | Used. Every version comes from here |
| [Corte Constitucional](https://www.corteconstitucional.gob.ec) | Constitutional court | n/a | n/a | no | Rulings are read from their Registro Oficial editions |
| [Asamblea Nacional](https://www.asambleanacional.gob.ec) | Legislature | n/a | n/a | no | Not needed: enmiendas are read from the gazette |
| Lexis Finder consolidation (via defensa.gob.ec) | Commercial consolidation | no | yes, per provision | n/a | Reconciliation only; no text copied |

Research guides that cover every country: [GlobaLex](https://www.nyulawglobal.org/globalex/) and the [Law Library of Congress Guide to Law Online](https://www.loc.gov/research-centers/law-library-of-congress/researcher-resources/guide-to-law-online/).

## Licence

The legal texts are official texts of the Republic of Ecuador, as published in the Registro Oficial (www.registroficial.gob.ec). The Registro Oficial states no licence for its editions; official legal texts are public. The scripts, tables and documentation are by Lexifina, under the terms in `LICENSE`.

This repository is not legal advice and not an official publication.

## En español

Historia del derecho ecuatoriano en git: un archivo por disposición y un commit por ley, fechado el día de su entrada en vigencia y firmado por la ley, sentencia o referéndum que hizo el cambio (`git blame` nombra la norma de cada párrafo). Contiene la Constitución de la República de 2008 tal como se publicó en el Registro Oficial No. 449 (20 de octubre de 2008) y todas sus modificaciones: el referéndum de 2011, las enmiendas de 2015 (y su caída por la sentencia 018-18-SIN-CC), el referéndum de 2018, las enmiendas de 2021 (art. 272) y 2024 (art. 138), la reforma parcial y el referéndum de 2024; los referéndums rechazados de 2023, 2024 (preguntas D y E) y 2025 constan como commits sin cambio de texto.

- Texto vigente en una fecha: `python tools/vigente_el.py 2017-01-01 constitucion 158`
- Regla supletoria de vigencia: la ley rige desde su promulgación en el Registro Oficial, salvo que ella disponga otra cosa (Código Civil, art. 6).
- Fuente: Registro Oficial. No existe una codificación oficial actualizada; cada versión se reconstruye aplicando el texto de cada norma modificatoria publicado en el Registro Oficial. Ningún modelo de IA generativa escribió texto legal; dos enmiendas impresas solo como imagen se leyeron por OCR y se corrigieron palabra por palabra contra la imagen.
