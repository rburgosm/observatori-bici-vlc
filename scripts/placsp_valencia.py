"""Licitaciones del Ajuntament de València en los datos abiertos de la Plataforma de Contratación del Sector Público
(PLACSP): descarga los ZIP mensuales de la sindicación 643 y filtra las entradas que pueden afectar a la bici y al
patinete. Lo usa la revisión trimestral de «El Plan, al día» (docs/plan_seguimiento.md, sec. 8; agente verificador-plan).

Uso:
  .venv/bin/python -I scripts/placsp_valencia.py descargar 2026-08 2026-09 [--dir data/raw/placsp] [--pausa 4]
  .venv/bin/python -I scripts/placsp_valencia.py filtrar data/raw/placsp/*.zip -o salida.csv

- descargar: un ZIP por mes (200-300 MB; la PLACSP sirve a ~200 kB/s y sin reanudación, así que tarda 10-20 min
  cada uno). Se bajan de uno en uno, con pausa entre descargas, a un .part que se renombra al terminar; un mes ya
  descargado no se vuelve a pedir. Los ZIP no se versionan (data/raw/placsp/ está en .gitignore).
- filtrar: entradas cuyo órgano es del Ajuntament de València y cuyo título casa con las palabras clave. Escribe el
  estado (PUB, EV, ADJ, RES…), el resultado (TenderResultCode: 3 desierto, 5 renuncia…), presupuesto, adjudicatario,
  importe y fecha de adjudicación y el enlace a la ficha (que se confirma a mano o con WebFetch).
Solo biblioteca estándar. No descarga ni lee nada al importarse.
"""
import argparse
import csv
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

URL = ("https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
       "licitacionesPerfilesContratanteCompleto3_{}.zip")
UA = "observatori-bici-vlc/0.1 (seguimiento del Plan; hola@observatoribicivlc.org)"
NS = {"a": "http://www.w3.org/2005/Atom",
      "cac": "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2",
      "cbc": "urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2",
      "cacext": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2",
      "cbcext": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2"}
# palabras clave del título: bici y VMP, seguridad vial y lugares o actuaciones del Plan
PAT = re.compile(r"bici|ciclo|ciclist|patinet|movilidad personal|semaf|señaliz|seguridad vial|auditor[ií]a de seguridad|"
                 r"glorieta|rotonda|intersecci|calmado|pacificaci|aparcabic|Benlloch|Albereda|Alameda|Campos Crespo|"
                 r"Avenida de la Plata|Avinguda de la Plata|Puerto|Carters|Carteros|Burgos|Gaspar Aguilar|Giorgeta|"
                 r"itinerari", re.I)
COLS = ["actualizado", "organo", "expediente", "estado", "resultado", "titulo", "presupuesto", "adjudicatario",
        "importe_adj", "fecha_adj", "url", "zip"]


def es_ajuntament(org):
    """Órgano del Ajuntament de València (Junta de Gobierno, concejalías…), no de otros «Valencia»."""
    if "Valencia" not in org and "València" not in org:
        return False
    if not any(k in org for k in ("Ayuntamiento", "Ajuntament", "Junta de Gobierno", "Concejal")):
        return False
    return "Don Juan" not in org   # Valencia de Don Juan (León)


def descargar(meses, carpeta, pausa):
    carpeta.mkdir(parents=True, exist_ok=True)
    for i, mes in enumerate(meses):
        if not re.fullmatch(r"\d{4}-\d{2}", mes):
            sys.exit(f"mes no válido: {mes} (formato AAAA-MM)")
        ym = mes.replace("-", "")
        dest = carpeta / f"placsp_643_{ym}.zip"
        if dest.exists():
            print(f"{dest}: ya está"); continue
        if i:
            time.sleep(pausa)
        part = dest.with_suffix(".zip.part")
        req = urllib.request.Request(URL.format(ym), headers={"User-Agent": UA})
        print(f"descargando {URL.format(ym)} …", flush=True)
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(part, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
        except BaseException:
            part.unlink(missing_ok=True)   # sin reanudación: un .part a medias no sirve
            raise
        part.rename(dest)
        print(f"{dest}: {dest.stat().st_size / 1e6:.0f} MB")


def filtrar(zips, salida):
    filas, vistas, n = [], set(), 0
    for zp in zips:
        with zipfile.ZipFile(zp) as z:
            for nombre in z.namelist():
                if not nombre.endswith(".atom"):
                    continue
                raiz = ET.fromstring(z.read(nombre))
                for e in raiz.findall("a:entry", NS):
                    n += 1
                    org = e.findtext(".//cacext:LocatedContractingParty/cac:Party/cac:PartyName/cbc:Name", "", NS)
                    if not es_ajuntament(org):
                        continue
                    titulo = e.findtext("a:title", "", NS) or ""
                    if not PAT.search(titulo):
                        continue
                    enlace = e.find("a:link", NS)
                    f = [(e.findtext("a:updated", "", NS) or "")[:10], org,
                         e.findtext(".//cbc:ContractFolderID", "", NS),
                         e.findtext(".//cbcext:ContractFolderStatusCode", "", NS),
                         e.findtext(".//cac:TenderResult/cbc:ResultCode", "", NS),
                         titulo[:250],
                         e.findtext(".//cac:BudgetAmount/cbc:TotalAmount", "", NS),
                         e.findtext(".//cac:TenderResult/cac:WinningParty/cac:PartyName/cbc:Name", "", NS),
                         e.findtext(".//cac:TenderResult/cac:AwardedTenderedProject/cac:LegalMonetaryTotal/"
                                    "cbc:PayableAmount", "", NS),
                         e.findtext(".//cac:TenderResult/cbc:AwardDate", "", NS),
                         enlace.get("href") if enlace is not None else "", Path(zp).name]
                    clave = tuple(f[:-1])
                    if clave not in vistas:   # la misma entrada repetida en varios .atom
                        vistas.add(clave); filas.append(f)
    filas.sort(key=lambda f: (f[2], f[0]))
    with open(salida, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(COLS); w.writerows(filas)
    print(f"entradas {n}, relevantes {len(filas)} -> {salida}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="orden", required=True)
    d = sub.add_parser("descargar", help="baja los ZIP mensuales de la sindicación 643")
    d.add_argument("meses", nargs="+", help="AAAA-MM")
    d.add_argument("--dir", type=Path, default=Path(__file__).resolve().parents[1] / "data/raw/placsp")
    d.add_argument("--pausa", type=float, default=4.0, help="segundos entre descargas (por defecto, 4)")
    f = sub.add_parser("filtrar", help="filtra las entradas del Ajuntament de bici, VMP y seguridad vial")
    f.add_argument("zips", nargs="+", type=Path)
    f.add_argument("-o", "--salida", type=Path, required=True)
    a = p.parse_args(argv)
    if a.orden == "descargar":
        descargar(a.meses, a.dir, a.pausa)
    else:
        filtrar(a.zips, a.salida)


if __name__ == "__main__":
    main()
