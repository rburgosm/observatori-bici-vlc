"""PDF del informe de incidencias para enviarlo al Ajuntament: docs/incidencias_para_el_ajuntament.md -> .pdf.

Markdown -> HTML con la librería `markdown` (tablas y listas) y HTML -> PDF con Chrome sin pantalla (--print-to-pdf), con
las fuentes de la web (web/proto/fuentes: Public Sans y Barlow Semi Condensed, OFL) para que se lea igual que el
observatorio. Ni pandoc ni weasyprint están en el sistema: por eso Chrome.
Requisitos: `markdown` (está en el python3 del sistema; no en .venv) y google-chrome (o chromium) en el PATH.
Uso: python3 -I scripts/incidencias_pdf.py   (lo lanza `make incidencias` después de scripts/incidencias.py)"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs/incidencias_para_el_ajuntament.md"
PDF = MD.with_suffix(".pdf")
F = ROOT / "web/proto/fuentes"

def fuente(familia, fichero, peso):
    return (f"@font-face{{font-family:'{familia}';src:url('{(F / fichero).as_uri()}') format('truetype');"
            f"font-weight:{peso};font-style:normal}}")

CSS = "".join([
    fuente("Public Sans", "public-sans/PublicSans-Regular.ttf", 400),
    fuente("Public Sans", "public-sans/PublicSans-Medium.ttf", 500),
    fuente("Public Sans", "public-sans/PublicSans-SemiBold.ttf", 700),
    fuente("Barlow Semi Condensed", "barlow-semi-condensed/BarlowSemiCondensed-SemiBold.ttf", 600),
    fuente("Barlow Semi Condensed", "barlow-semi-condensed/BarlowSemiCondensed-Bold.ttf", 700),
]) + """
@page{size:A4;margin:18mm 16mm 18mm 16mm;
  @bottom-right{content:counter(page) " / " counter(pages);font:9pt 'Public Sans',sans-serif;color:#555}}
html{font-family:'Public Sans',sans-serif;font-size:10.5pt;line-height:1.45;color:#16202a}
body{margin:0}
h1,h2,h3,h4{font-family:'Barlow Semi Condensed',sans-serif;line-height:1.15;color:#0d1820;break-after:avoid}
h1{font-size:22pt;margin:0 0 6pt}
h2{font-size:15pt;margin:18pt 0 6pt;border-bottom:1px solid #c9d1d8;padding-bottom:3pt}
h3{font-size:13pt;margin:16pt 0 4pt}
h4{font-size:11.5pt;margin:12pt 0 3pt}
p{margin:0 0 6pt}
ul,ol{margin:0 0 6pt;padding-left:16pt}
li{margin:0 0 2pt}
a{color:#0b4f8a;overflow-wrap:anywhere}
code{font-size:.9em;background:#eef1f4;padding:0 2pt;border-radius:2pt;overflow-wrap:anywhere}
table{border-collapse:collapse;width:100%;font-size:8.3pt;line-height:1.3;margin:4pt 0 10pt}
thead{display:table-header-group}
tr{break-inside:avoid}
th,td{border:1px solid #c9d1d8;padding:3pt 4pt;vertical-align:top;text-align:left}
th{background:#e7ecf0;font-weight:700}
td:first-child{white-space:nowrap}
h4+ul{break-before:avoid}
"""

def main():
    texto = MD.read_text(encoding="utf-8")
    cuerpo = markdown.markdown(texto, extensions=["tables", "sane_lists"], output_format="html5")
    html = ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            "<title>Incidencias detectadas en datos abiertos del Ajuntament de València</title>"
            f"<style>{CSS}</style></head><body>{cuerpo}</body></html>")
    chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None)
    if not chrome:
        sys.exit("No hay google-chrome ni chromium en el PATH")
    with tempfile.TemporaryDirectory() as d:
        h = Path(d) / "informe.html"
        h.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                        f"--user-data-dir={d}/perfil", f"--print-to-pdf={PDF}", h.as_uri()],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    print(f"{PDF.relative_to(ROOT)} ({PDF.stat().st_size / 1e3:.0f} kB)")

if __name__ == "__main__":
    main()
