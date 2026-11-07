"""¿Ocurren los siniestros con VMP en la red ciclista o fuera?

Para cada siniestro geocodificado calcula la distancia al tramo más cercano de la red ciclista
(capa 189 del geoportal) y compara VMP con el resto de siniestros como referencia: los cruces
de avenidas con carril bici concentran también mucho tráfico de coches.

Distancias con geopandas (sjoin_nearest) en EPSG:25830 (migrado el 04/11/2026 desde una proyección equirectangular
y una rejilla hechas a mano). Validación inicial: no alimenta la web.

Uso: .venv/bin/python -I scripts/vmp_carril_bici.py
Requiere data/processed/siniestros_geo.csv y data/raw/siniestros/carriles_bici.geojson
"""
import collections as C
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TIPOS = {"1": "carril bici", "4": "Jardín del Turia", "6": "senda ciclable", "7": "bus-bici",
         "2": "ciclocalle", "9": "ciclobarrio", "3": "peatonal"}
SEGREGADO = {"1", "4", "6", "7"}
RADIOS = (15, 30)

red = gpd.read_file(ROOT / "data/raw/siniestros/carriles_bici.geojson")
red["estado"] = red.estado.astype(str)
red = red[red.estado.isin(TIPOS) & red.geometry.notna()][["estado", "geometry"]].to_crs("EPSG:25830")
df = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", dtype=str, keep_default_na=False)
df = df[df.lon != ""]
g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon.astype(float), df.lat.astype(float)), crs=4326).to_crs("EPSG:25830")
# vía ciclista más cercana (hasta 100 m: solo se usan 15 y 30 m); en un empate exacto, la primera
near = gpd.sjoin_nearest(g[["geometry"]], red, max_distance=100, how="left", distance_col="d")
near = near[~near.index.duplicated()]
rows = df.to_dict("records")
for r, d, t in zip(rows, near.d.fillna(1e9), near.estado):
    r["d"], r["red"] = d, t
    r["vmp"] = "VMP" in r["unidades"]
    r["bici"] = "BICI" in r["unidades"].upper() and not r["vmp"]

grupos = {"VMP": [r for r in rows if r["vmp"]],
          "bicicleta (sin VMP)": [r for r in rows if r["bici"]],
          "resto (sin VMP ni bici)": [r for r in rows if not r["vmp"] and not r["bici"]]}
for radio in RADIOS:
    print(f"\n== Siniestros a <= {radio} m de la red ciclista")
    for nom, g in grupos.items():
        seg = sum(1 for r in g if r["d"] <= radio and r["red"] in SEGREGADO)
        cua = sum(1 for r in g if r["d"] <= radio)
        print(f"  {nom:24s} n={len(g):6d}  red segregada {seg/len(g):5.1%}  cualquier vía ciclista {cua/len(g):5.1%}")

vmp = grupos["VMP"]
print("\n== VMP a <= 15 m, por tipo de vía ciclista")
c = C.Counter(TIPOS[r["red"]] for r in vmp if r["d"] <= 15)
for k, n in c.most_common():
    print(f"  {n:5d}  {k}")
print(f"  fuera de la red: {sum(1 for r in vmp if r['d'] > 15)}")

print("\n== VMP según método de geocodificación (a <= 15 m de red segregada)")
for m in ("cruce", "portal", "portal_cercano"):
    g = [r for r in vmp if r["metodo"] == m]
    if g:
        print(f"  {m:15s} n={len(g):5d}  {sum(1 for r in g if r['d'] <= 15 and r['red'] in SEGREGADO)/len(g):5.1%}")

def grave(r):
    return "GRAVES" in r["gravedad"] or "FALLEC" in r["gravedad"]

print("\n== VMP: tipo de siniestro y gravedad, dentro (<=15 m red segregada) vs fuera (>30 m)")
den = [r for r in vmp if r["d"] <= 15 and r["red"] in SEGREGADO]
fue = [r for r in vmp if r["d"] > 30]
for nom, g in (("en red segregada", den), ("fuera de la red", fue)):
    print(f"  {nom}: n={len(g)}, graves/fallecidos {sum(map(grave, g))} ({sum(map(grave, g))/len(g):.1%})")
    for k, n in C.Counter(r["tipo"] for r in g).most_common(4):
        print(f"      {n:4d} {k}")

print("\n== VMP fuera de la red (>30 m): calles con más siniestros")
for k, n in C.Counter(r["ubicacion"].split(" cruce ")[0] if r["metodo"] == "cruce"
                      else r["ubicacion"].rsplit(" ", 1)[0] for r in fue).most_common(10):
    print(f"  {n:4d}  {k}")
