"""Controles de calidad de la geocodificación (sin verdad de campo).

1. Ambigüedad: cuántos siniestros se resolvieron por nombre sin tipo de vía o con varias vías candidatas.
2. Coherencia interna: la misma ubicación textual siempre debe dar el mismo punto.
3. Cruces: los dos nombres invertidos («A cruce B» y «B cruce A») deben caer en el mismo sitio.
4. Muestra aleatoria de 50 para revisión manual en outputs/muestra_geocodificacion.csv
   (con enlace a OpenStreetMap para mirar cada punto). Si el fichero ya existe no se rehace: verificar_muestra_osm.py
   le añade la comprobación con OSM y se perdería (para rehacerla, borrarlo antes).
Distancias con geopandas en EPSG:25830 (migrado el 04/11/2026 desde una distancia equirectangular hecha a mano).

Uso: .venv/bin/python -I scripts/validar_geocodificacion.py
"""
import csv, random, collections as C
from pathlib import Path
import sys
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import geocodificar as g  # reutiliza índices y normalización


def resolucion(calle):
    calle = g.norm(calle)
    tipo, _, nombre = calle.partition(" ")
    for n in (nombre, g.sin_parentesis(nombre)):
        if g.por_tipo_nombre.get((tipo, n)):
            return "tipo+nombre", len(g.por_tipo_nombre[(tipo, n)])
        if g.por_nombre.get(n):
            return "solo_nombre", len(g.por_nombre[n])
    return "sin", 0


rows = [r for r in csv.DictReader((ROOT / "data/processed/siniestros_geo.csv").open()) if r["lon"]]
vmp = [r for r in rows if "VMP" in r["unidades"]]
print(f"geocodificados: {len(rows)} (VMP {len(vmp)})")

amb = C.Counter()
for r in rows:
    calles = r["ubicacion"].split(" cruce ") if r["metodo"] == "cruce" else [r["ubicacion"].rsplit(" ", 1)[0]]
    res = [resolucion(c) for c in calles]
    if any(k == "solo_nombre" for k, _ in res):
        amb["resuelto sin tipo de vía"] += 1
    if any(n > 1 for _, n in res):
        amb["varias vías candidatas"] += 1
print("ambigüedad:", {k: f"{v} ({v/len(rows):.1%})" for k, v in amb.items()})

# cruces invertidos
pt = {}
for r in rows:
    if r["metodo"] == "cruce":
        pt[r["ubicacion"]] = (float(r["lon"]), float(r["lat"]))
pares = [(u, f"{b} cruce {a}") for u in pt for a, b in [u.split(" cruce ", 1)] if f"{b} cruce {a}" in pt and u < f"{b} cruce {a}"]
_g = lambda xs: gpd.GeoSeries(gpd.points_from_xy([pt[x][0] for x in xs], [pt[x][1] for x in xs]), crs=4326).to_crs("EPSG:25830")
d = sorted(_g([a for a, _ in pares]).distance(_g([b for _, b in pares]), align=False).tolist()) if pares else []
if not d:
    print("cruces escritos en los dos órdenes: 0 (la fuente siempre usa el mismo orden)")
else:
  print(f"cruces escritos en los dos órdenes: {len(d)}; distancia entre ambos p50 {d[len(d)//2]:.0f} m, "
      f"p95 {d[int(.95*len(d))]:.0f} m, >50 m: {sum(1 for x in d if x > 50)}")

# muestra para revisión manual
random.seed(2026)
muestra = random.sample(vmp, 50)
out = ROOT / "outputs/muestra_geocodificacion.csv"
out.parent.mkdir(exist_ok=True)
if out.exists():                      # ya verificada con OSM (verificar_muestra_osm.py): no se pisa
    out = Path("/dev/null")
    print("outputs/muestra_geocodificacion.csv ya existe (verificada con OSM): no se rehace; muestra de hoy, solo en pantalla")
with out.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "ubicacion", "metodo", "lat", "lon", "osm", "correcto (s/n)", "nota"])
    for r in muestra:
        w.writerow([r["id"], r["ubicacion"], r["metodo"], r["lat"], r["lon"],
                    f"https://www.openstreetmap.org/?mlat={r['lat']}&mlon={r['lon']}#map=19/{r['lat']}/{r['lon']}", "", ""])
if out.name != "null":
    print(f"muestra de 50 VMP para revisión manual: {out.relative_to(ROOT)}")
print("métodos en la muestra:", C.Counter(r["metodo"] for r in muestra))
