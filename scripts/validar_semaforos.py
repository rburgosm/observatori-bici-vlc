"""Clasifica los cruces con siniestros en «con semáforo» / «sin semáforo» y mide la incertidumbre.

Fuentes:
- Reguladores semafóricos del portal (capa 182). El punto es el armario, no el cruce, y la
  descripción nombra el cruce («BLASCO IBAÑEZ - ALMELA Y VIVES»).
- Nodos highway=traffic_signals de OpenStreetMap (complemento externo).

Reglas para el regulador: coincide el nombre (un token de cada calle) a <=200 m, o hay uno a <=25 m:
con semáforo. Ninguno a <=80 m: sin semáforo. Resto: dudoso. Para OSM: un nodo a <=30 m del cruce.

Uso: .venv/bin/python -I scripts/validar_semaforos.py
"""
import json, re, unicodedata
from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
CRS = "EPSG:25830"
STOP = set("C AV PG PL CTRA GV LLOC DE DEL LA LAS LOS EL Y I DELS AVDA CALLE PLAZA CAMI CAMINO DOCTOR SAN SANTA".split())


def tokens(s):
    s = unicodedata.normalize("NFD", (s or "").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return {w for w in re.sub(r"[^A-Z ]", " ", s).split() if len(w) > 3 and w not in STOP}


s = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv")
s = s[s.metodo == "cruce"]
cr = (s.assign(vmp=s.unidades.str.contains("VMP", na=False))
        .groupby("ubicacion").agg(lon=("lon", "first"), lat=("lat", "first"), n=("id", "size"), n_vmp=("vmp", "sum"))
        .reset_index())
cr = gpd.GeoDataFrame(cr, geometry=gpd.points_from_xy(cr.lon, cr.lat), crs="EPSG:4326").to_crs(CRS)

reg = gpd.read_file(ROOT / "data/raw/siniestros/reguladores_semaforos.geojson").to_crs(CRS)
reg = reg[reg.geometry.notna()].reset_index(drop=True)
reg["tok"] = reg.descripcion.map(tokens)

osm = json.loads((ROOT / "data/raw/siniestros/osm_semaforos.json").read_text())["elements"]
osm = gpd.GeoDataFrame(geometry=gpd.points_from_xy([e["lon"] for e in osm], [e["lat"] for e in osm]), crs="EPSG:4326").to_crs(CRS)

# reguladores a <=200 m de cada cruce
pares = gpd.sjoin_nearest(cr, reg[["tok", "geometry"]], max_distance=200, distance_col="d", how="left")


def clase_regulador(g):
    a, b = g.name.split(" cruce ", 1)
    ta, tb = tokens(a), tokens(b)
    if g.d.notna().any():
        if any((t & ta) and (t & tb) for t in g.tok.dropna()):
            return "con (nombre)"
        if g.d.min() <= 25:
            return "con (<=25 m)"
        if g.d.min() <= 80:
            return "dudoso"
    return "sin"


# sjoin_nearest solo da el más cercano; para el nombre miramos todos los de <=200 m
todos = gpd.sjoin(cr, gpd.GeoDataFrame(reg[["tok"]], geometry=reg.buffer(200), crs=CRS), how="left")
todos["d"] = [cr.geometry.iloc[i].distance(reg.geometry.iloc[int(j)]) if pd.notna(j) else None
              for i, j in zip(todos.index, todos.index_right)]
cr["regulador"] = todos.groupby("ubicacion").apply(clase_regulador, include_groups=False).reindex(cr.ubicacion).values

d_osm = gpd.sjoin_nearest(cr[["geometry"]], osm, distance_col="d").groupby(level=0).d.min()
cr["osm"] = (d_osm.reindex(cr.index) <= 50).map({True: "con", False: "sin"})

print("Clasificación por regulador municipal (cruces / siniestros VMP):")
print(cr.groupby("regulador").agg(cruces=("n", "size"), vmp=("n_vmp", "sum")).to_string())
print("\nAcuerdo regulador × OSM (cruces):")
print(pd.crosstab(cr.regulador, cr.osm).to_string())

conf = cr[cr.regulador != "dudoso"]
acuerdo = ((conf.regulador.str.startswith("con")) == (conf.osm == "con")).mean()
print(f"\nacuerdo en los cruces no dudosos: {acuerdo:.0%}")

cr["final"] = cr.regulador.where(cr.regulador != "dudoso", "dudoso→" + cr.osm)
print("\nDudosos resueltos con OSM:")
print(cr[cr.regulador == "dudoso"].groupby("final").agg(cruces=("n", "size"), vmp=("n_vmp", "sum")).to_string())
cr.drop(columns="geometry").to_csv(ROOT / "outputs/cruces_semaforo.csv", index=False)
