"""¿Hay casos suficientes alrededor de cada punto de conteo del carril bici? (validación inicial; no alimenta la web)

Cruza los contadores de los ODS de Movilidad (IMD de laborables por mes) con su posición (capa 225, campo idpm) y cuenta
los siniestros con VMP y con bici o VMP a 100 y 200 m. Geometría con geopandas en EPSG:25830 (migrado el 04/11/2026
desde distancias equirectangulares hechas a mano).
- Sin doble conteo (misma regla que cribado_eb.py): cada siniestro va al contador más cercano a <= R m
  (geopandas.sjoin_nearest) y de ahí a su punto de conteo; los contadores a menos de 50 m entre sí (los dos sentidos del
  mismo carril) forman un punto. Antes, un siniestro contaba en todos los contadores a <= R m; se imprime también así
  («por contador, como antes») para comparar, con cuántos siniestros caían en más de un contador.
- Tasa ilustrativa: siniestros por millón de pasos, con la IMD de cada año (IMD × 250 días laborables) y solo los años
  completos de siniestros que tienen fichero de IMD (antes: IMD de 2025 × 4 años fijos).
Siniestros: los de los años completos, sin duplicados (scripts/lugares.py, siniestros()).

Uso: .venv/bin/python -I scripts/validar_contadores.py
"""
import re, statistics, zipfile, sys
import xml.etree.ElementTree as ET
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import lugares as LG  # noqa: E402  (siniestros de los años completos, sin duplicados)

CRS = "EPSG:25830"
T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
TXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
DIAS, JUNTAR, RADIOS = 250, 50, (100, 200)


def leer_ods(path):
    """{codigo: [imd por mes]} de un ODS de carril bici (una hoja por mes)."""
    imd = {}
    root = ET.fromstring(zipfile.ZipFile(path).read("content.xml"))
    for hoja in root.iter(T + "table"):
        for fila in hoja.iter(T + "table-row"):
            celdas = [" ".join("".join(p.itertext()) for p in c.findall(TXT + "p")) for c in fila.iter(T + "table-cell")]
            if len(celdas) >= 4 and re.fullmatch(r"P\d+", celdas[0].strip()) and celdas[3].strip().isdigit():
                imd.setdefault(int(celdas[0].strip()[1:]), []).append(int(celdas[3]))
    return imd


# siniestros con punto, en metros
s, AÑOS = LG.siniestros()
s = s[s.lon.notna()].copy(); s["año"] = s.fecha.dt.year
s = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs=4326).to_crs(CRS)
grupos = {"VMP": s[s.unidades.str.contains("VMP", na=False)],
          "VMP o bici": s[s.unidades.str.contains("VMP|BICICLETA", na=False)]}

# IMD media de cada contador y año (años completos con fichero de IMD)
años_imd = [a for a in AÑOS if (ROOT / f"data/raw/intensidades/carril_bici_{a}.ods").exists()]
imd = pd.DataFrame([(k, a, statistics.mean(v)) for a in años_imd
                    for k, v in leer_ods(ROOT / f"data/raw/intensidades/carril_bici_{a}.ods").items()], columns=["idpm", "año", "imd"])
esp = gpd.read_file(ROOT / "data/raw/siniestros/espiras_bici.geojson")
esp = esp[esp.geometry.notna()].drop_duplicates("idpm").to_crs(CRS)
ult = imd[imd["año"] == años_imd[-1]]
cont = esp[esp.idpm.isin(ult.idpm)][["idpm", "geometry"]].reset_index(drop=True)
print(f"años de siniestros {AÑOS}; con IMD {años_imd}")
print(f"contadores en el ODS de {años_imd[-1]}: {ult.idpm.nunique()}, con posición: {len(cont)}")

# puntos de conteo: contadores a menos de JUNTAR m entre sí (unión de círculos de JUNTAR/2 m)
zonas = gpd.GeoDataFrame(geometry=[cont.buffer(JUNTAR / 2).union_all()], crs=CRS).explode(ignore_index=True)
cont = gpd.sjoin(cont, zonas.assign(sitio=zonas.index), predicate="within").drop(columns="index_right")
print(f"contadores a menos de {JUNTAR} m (mismo carril, dos sentidos) juntados: {len(cont)} contadores → {cont.sitio.nunique()} puntos de conteo")


def casos(g, radio, como_antes=False):
    """Siniestros de g a <= radio m. como_antes: los de cada contador (un siniestro cuenta en todos los que tiene a <= radio);
    si no, cada siniestro al contador más cercano y a su punto de conteo. Devuelve (recuento por unidad, siniestro-unidad)."""
    if como_antes:
        j = gpd.sjoin(g[["año", "geometry"]], cont.assign(geometry=cont.buffer(radio))[["idpm", "geometry"]], predicate="within")
        return j.groupby("idpm").size().reindex(cont.idpm, fill_value=0), j
    j = gpd.sjoin_nearest(g[["año", "geometry"]], cont[["sitio", "geometry"]], max_distance=radio, how="inner")
    j = j[~j.index.duplicated()]                     # empate exacto entre dos contadores: uno solo
    return j.groupby("sitio").size().reindex(sorted(cont.sitio.unique()), fill_value=0), j


def resumen(n):
    n = sorted(n); q = lambda x: n[int(x * (len(n) - 1))]
    return (f"mediana {q(.5)}, p25 {q(.25)}, p75 {q(.75)}, máx {n[-1]} | con >=5: {sum(x >= 5 for x in n)}, "
            f">=10: {sum(x >= 10 for x in n)}, 0: {n.count(0)}")


for nom, g in grupos.items():
    for radio in RADIOS:
        n_c, jc = casos(g, radio, como_antes=True)
        n_s, j = casos(g, radio)
        varios = int((jc.index.value_counts() > 1).sum())
        print(f"{nom:11s} radio {radio} m · por contador (como antes): {resumen(n_c.tolist())}; "
              f"suma {int(n_c.sum())}, {varios} de {jc.index.nunique()} siniestros en más de un contador")
        print(f"{'':11s}              · al más cercano, por punto de conteo: {resumen(n_s.tolist())}; suma {int(n_s.sum())}")

# tasa ilustrativa: siniestros con bici o VMP a 200 m por millón de pasos, con la IMD de cada año
_, j = casos(grupos["VMP o bici"], 200)
n_sa = j.groupby(["sitio", "año"]).size()
ex = imd.merge(cont[["idpm", "sitio"]], on="idpm").groupby(["sitio", "año"]).imd.sum()
ta = pd.DataFrame({"imd": ex, "n": n_sa.reindex(ex.index, fill_value=0)}).groupby("sitio").agg(
    pasos=("imd", lambda v: v.sum() * DIAS), n=("n", "sum"), años=("imd", "size"), imd=("imd", "mean"))
ta = ta[ta.pasos > 0]; ta["tasa"] = ta.n / ta.pasos * 1e6
nombre = cont.groupby("sitio").idpm.apply(lambda x: " + ".join(f"P{i}" for i in sorted(x)))
print(f"\npuntos de conteo con mayor tasa (bici o VMP a 200 m por millón de pasos, IMD de cada año × {DIAS} días) — "
      "solo los que tienen >=5 siniestros:")
for k, r in ta[ta.n >= 5].sort_values("tasa", ascending=False).head(8).iterrows():
    print(f"  {nombre[k]}: {r.tasa:5.1f}  ({int(r.n)} siniestros en {int(r.años)} años, IMD media {round(r.imd)})")
