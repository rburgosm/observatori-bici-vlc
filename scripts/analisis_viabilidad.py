"""Viabilidad de dos ideas con los siniestros geocodificados:
 1) ranking de colegios por siniestralidad en su entorno en horario escolar
 2) observatorio de accidentes con VMP (patinetes)

Distancias y celdas con geopandas en EPSG:25830 (migrado el 04/11/2026 desde distancias equirectangulares y celdas en
grados hechas a mano). Exploración inicial: no alimenta la web.

Uso: .venv/bin/python -I scripts/analisis_viabilidad.py
Requiere data/processed/siniestros_geo.csv (geocodificar.py)
"""
import csv, json, collections as C, datetime as D
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / "data/processed/siniestros_geo.csv").open()))
geo = [r for r in rows if r["lon"]]
for r in geo:
    r["pt"] = (float(r["lon"]), float(r["lat"]))
    r["dt"] = D.datetime.fromisoformat(r["fecha"])


def grave(r):
    return "GRAVES" in r["gravedad"] or "FALLEC" in r["gravedad"]


# ---------- validación: cruces con más siniestros
print("== Cruces con más siniestros (validación: Blasco Ibáñez / Clariano debería salir)")
cr = C.Counter(r["ubicacion"] for r in geo if r["metodo"] == "cruce")
for u, n in cr.most_common(10):
    print(f"  {n:4d}  {u}")
lon = [r["pt"][0] for r in geo]; lat = [r["pt"][1] for r in geo]
print(f"  bbox lon {min(lon):.3f}..{max(lon):.3f} lat {min(lat):.3f}..{max(lat):.3f}")

# ---------- 1) colegios
def horario_escolar(dt):
    if dt.weekday() >= 5 or dt.month in (7, 8):
        return False
    h = dt.hour + dt.minute / 60
    return 7.75 <= h <= 9.5 or 12.5 <= h <= 14.0 or 16.25 <= h <= 17.75

cole = [f for f in json.loads((ROOT / "data/raw/siniestros/centros_educativos.geojson").read_text())["features"]
        if f["properties"]["municipio"] == "València" and f.get("geometry")]
print(f"\n== 1) Colegios: {len(cole)} centros en València")
he = [r for r in geo if horario_escolar(r["dt"])]
print(f"  siniestros geocodificados en horario escolar: {len(he)} de {len(geo)}")
CRS = "EPSG:25830"
g_he = gpd.GeoDataFrame({"i": range(len(he))}, geometry=gpd.points_from_xy([r["pt"][0] for r in he], [r["pt"][1] for r in he]), crs=4326).to_crs(CRS)
g_co = gpd.GeoDataFrame({"c": range(len(cole))}, geometry=gpd.points_from_xy([f["geometry"]["coordinates"][0] for f in cole],
                                                                               [f["geometry"]["coordinates"][1] for f in cole]), crs=4326).to_crs(CRS)

for radio in (100, 150, 250):
    # siniestros a <= radio m de cada centro (círculo de radio m alrededor del centro)
    j = gpd.sjoin(g_he, g_co.assign(geometry=g_co.buffer(radio)), predicate="within")
    cerca = j.groupby("c").i.apply(list).to_dict()
    res = []
    for c, f in enumerate(cole):
        near = [he[i] for i in cerca.get(c, [])]
        peat = [r for r in near if "PEAT" in r["unidades"] or "ATROPELLO A PERSONA" in r["tipo"]]
        res.append((len(near), len(peat), sum(grave(r) for r in near), f["properties"]["dlibre"], f["properties"]["regimen"]))
    tot = sorted(x[0] for x in res); pe = sorted(x[1] for x in res)
    q = lambda v, p: v[int(p * (len(v) - 1))]
    print(f"  radio {radio} m: siniestros/colegio mediana {q(tot,.5)} p90 {q(tot,.9)} max {tot[-1]} | "
          f"con atropello: {sum(1 for x in pe if x>0)} colegios, mediana {q(pe,.5)} p90 {q(pe,.9)} max {pe[-1]} | "
          f"colegios con 0 siniestros: {sum(1 for x in tot if x==0)}")
    if radio == 150:
        print("  top 10 (150 m, horario escolar 2022-2025): total / atropellos / graves")
        for x in sorted(res, reverse=True)[:10]:
            print(f"    {x[0]:3d} {x[1]:3d} {x[2]:2d}  {x[3][:60]} ({x[4]})")
        top = sorted(res, reverse=True)
        print(f"  concentración: el 10% de colegios con más siniestros suma {sum(x[0] for x in top[:len(top)//10])/max(1,sum(x[0] for x in top)):.0%}")

# ---------- 2) VMP
vmp = [r for r in rows if "VMP" in r["unidades"]]
print(f"\n== 2) VMP: {len(vmp)} siniestros con patinete")
print("  por año:", sorted(C.Counter(r["fecha"][:4] for r in vmp).items()))
print("  total siniestros por año:", sorted(C.Counter(r["fecha"][:4] for r in rows).items()))
fal = [r for r in rows if "FALLEC" in r["gravedad"]]
print(f"  fallecidos (siniestros con fallecidos): {len(fal)}, con VMP: {sum('VMP' in r['unidades'] for r in fal)}")
print(f"  graves+fallecidos con VMP: {sum(grave(r) for r in vmp)} de {sum(grave(r) for r in rows)} totales")
print("  unidades:", C.Counter(r["unidades"] for r in vmp).most_common(6))
print("  tipo:", C.Counter(r["tipo"] for r in vmp).most_common(6))
print("  factores:", C.Counter(r["factores"] for r in vmp).most_common(6))
print("  hora:", sorted(C.Counter(int(r["fecha"][11:13]) for r in vmp).items()))
print("  dia semana:", sorted(C.Counter(D.datetime.fromisoformat(r["fecha"]).weekday() for r in vmp).items()))
vg = [r for r in vmp if r["lon"]]
print(f"  geocodificados: {len(vg)} ({len(vg)/len(vmp):.0%})")
_xy = gpd.GeoSeries(gpd.points_from_xy([float(r["lon"]) for r in vg], [float(r["lat"]) for r in vg]), crs=4326).to_crs(CRS)
celda = list(zip((_xy.x // 100).astype(int), (_xy.y // 100).astype(int)))      # celdas de 100 m en EPSG:25830
cel = C.Counter(celda)
ub = C.defaultdict(C.Counter)
for r, k in zip(vg, celda):
    ub[k][r["ubicacion"]] += 1
print("  celdas de 100 m con más siniestros VMP:")
for k, n in cel.most_common(10):
    print(f"    {n:3d}  {ub[k].most_common(1)[0][0]}")
print(f"  celdas con >=5: {sum(1 for n in cel.values() if n>=5)}, con >=10: {sum(1 for n in cel.values() if n>=10)}")
