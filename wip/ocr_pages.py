"""Machine OCR of the Registro Oficial pages that carry no text layer (page images only).

Two amendments to the Constitution are printed only as page images:
  - Tercer Suplemento 377, 25 January 2021 (enmienda adding art. 272, numeral 4), PDF page index 2;
  - Tercer Suplemento 568, 30 May 2024 (enmienda replacing art. 138), PDF page indexes 3 and 4.

    python -X utf8 ocr_pages.py --make     render the pages (pymupdf, 200 dpi) and OCR them with the
                                           Windows.Media.Ocr engine (en-US; no Spanish engine was
                                           installed), writing ocr_pages.json next to this file

The raw OCR output is kept as is in ocr_pages.json. amendments.py takes the words of each provision from
it and applies the explicit word corrections listed there (OCR_FIXES); every corrected or accented word
must also occur in the 2008 Constitution's own text, or be listed in OCR_NEW_WORDS.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ocr_pages.json"
PAGES = {
    "ro377-2021": ("http://esacc.corteconstitucional.gob.ec/storage/api/v1/10_DWL_FL/"
                   "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiY2NiNDhjMmUtYjIwNy00YTBhLWFkZTEtMDczNTA2OGEyYzI3LnBkZiJ9", [2]),
    "ro568-2024": ("http://esacc.corteconstitucional.gob.ec/storage/api/v1/10_DWL_FL/"
                   "eyJjYXJwZXRhIjoicm8iLCJ1dWlkIjoiYmE0MDA2ZDgtYThkZi00YzUzLTg0NTItZWFmYzc1NDZjODRhLnBkZiJ9", [3, 4]),
}

PS1 = r"""
param([string]$Dir)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait() | Out-Null; $task.Result }
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
Get-ChildItem $Dir -Filter *.png | Sort-Object Name | ForEach-Object {
  $f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)) ([Windows.Storage.StorageFile])
  $s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $r = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  [IO.File]::WriteAllText(($_.FullName -replace '\.png$', '.txt'), (($r.Lines | ForEach-Object { $_.Text }) -join "`n"), [Text.Encoding]::UTF8)
  $s.Dispose()
}
"""


def make() -> None:
    import fitz
    sys.path.insert(0, str(HERE))
    import fetch
    work = HERE / ".tmp-ocr"
    work.mkdir(exist_ok=True)
    for f in work.iterdir():
        f.unlink()
    (work / "ocr.ps1").write_text(PS1, encoding="utf-8")
    for name, (url, pages) in PAGES.items():
        doc = fitz.open(fetch.cached(url))
        for p in pages:
            doc[p].get_pixmap(dpi=200).save(str(work / f"{name}-p{p}.png"))
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(work / "ocr.ps1"),
                    "-Dir", str(work)], check=True)
    out = {}
    for name, (url, pages) in PAGES.items():
        out[name] = {"url": url, "pages": {str(p): (work / f"{name}-p{p}.txt").read_text(encoding="utf-8-sig")
                                           for p in pages}}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", OUT)


def load() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if sys.argv[1:] == ["--make"]:
        make()
