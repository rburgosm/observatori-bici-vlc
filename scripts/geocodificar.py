"""Geocodifica los siniestros de tráfico 2022-2025 con el callejero municipal.

Formatos de UBICACION: "C/ X cruce AV Y" (cruce), "AV X 46" (portal) y "C/ X" (solo calle, no se geocodifica).
Nombres: la tabla `vias` da el nombre en castellano sin tildes (traducnooficial) y el codtipovia
con el mismo formato que los siniestros; geometría de `ejes` (por codvia) y `portales`.
Equivalencias manuales de nombres: data/processed/equivalencias_calles.csv.

Cruce (shapely, EPSG:25830): primero, distancia mínima entre VÉRTICES de los dos ejes <= 40 m (criterio
original); el punto es el punto medio de los dos vértices más cercanos. Si falla, se mide entre SEGMENTOS
(mismo umbral de 40 m): recupera cruces reales en tramos rectos con vértices separados (03/11/2026).
Se hace en ese orden para no mover ningún cruce ya geocodificado. `dist_ejes_m` guarda la distancia.

Uso: OMP_NUM_THREADS=1 .venv/bin/python -I scripts/geocodificar.py
Salida: data/processed/siniestros_geo.csv (+ resumen por pantalla)
"""
import csv, functools, json, re, unicodedata, collections as C
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely import MultiPoint, get_coordinates
from shapely.ops import nearest_points

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/siniestros"
EQUIV = ROOT / "data/processed/equivalencias_calles.csv"
MAX_CRUCE_M = 40  # distancia máxima entre ejes para aceptar un cruce


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").upper())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"(?<=[A-Z])[·.](?=[A-Z])", "", s)  # IL·LUSIO / IL.LUSIO -> ILLUSIO
    s = s.replace("·", "").replace("'", " ").replace("-", " ")
    s = re.sub(r"[^A-Z0-9() ]", " ", s)
    s = re.sub(r"\bPROFESSOR\b", "PROFESOR", s)  # el callejero mezcla las dos grafías
    s = re.sub(r"\([^)]*$", "", s)  # paréntesis sin cerrar (texto truncado)
    return re.sub(r"\s+", " ", s).strip()


def sin_parentesis(s):
    return re.sub(r"\s*\([^)]*\)", "", s).strip()


# --- índice de nombres -> codvia
vias = json.loads((RAW / "vias.json").read_text())
por_tipo_nombre, por_nombre = C.defaultdict(set), C.defaultdict(set)
for v in vias:
    if v.get("fechabaja"):
        continue
    for nom in (v.get("traducnooficial"), v.get("nomoficial")):
        for n in {norm(nom), sin_parentesis(norm(nom))}:
            if n:
                por_tipo_nombre[(norm(v["codtipovia"]), n)].add(v["codvia"])
                por_nombre[n].add(v["codvia"])

# --- geometría: ejes unidos por codvia, en metros (EPSG:25830)
_ejes = gpd.read_file(RAW / "ejes.geojson")[["codvia", "geometry"]].dropna(subset=["geometry"])
geom = _ejes.to_crs(25830).dissolve(by="codvia").geometry.to_dict()
vertices = {cv: MultiPoint(get_coordinates(g)) for cv, g in geom.items()}
a_wgs84 = Transformer.from_crs(25830, 4326, always_xy=True).transform

equiv = {}
with EQUIV.open() as fh:
    for r in csv.DictReader(fh):
        equiv[norm(r["en_siniestros"])] = r["en_callejero"]

portal = {}
num_por_via = C.defaultdict(list)
for f in json.loads((RAW / "portales.geojson").read_text())["features"]:
    p = f["properties"]
    if not f.get("geometry") or p.get("numportal") is None:
        continue
    pt = tuple(f["geometry"]["coordinates"])
    portal.setdefault((p["codvia"], p["numportal"]), pt)
    num_por_via[p["codvia"]].append((p["numportal"], pt))


def codvias(calle):
    calle = norm(calle)
    calle = norm(equiv.get(calle, calle))
    tipo, _, nombre = calle.partition(" ")
    for n in (nombre, sin_parentesis(nombre)):
        c = por_tipo_nombre.get((tipo, n)) or por_nombre.get(n)
        if c:
            return c
    return set()


@functools.lru_cache(maxsize=None)
def _cruce_vias(ca, cb):
    """(0 vértices | 1 segmentos, distancia, (lon, lat)) del cruce entre dos codvias, o None. Vértices primero; segmentos si falla."""
    for orden, capa in enumerate((vertices, geom)):
        ga, gb = capa.get(ca), capa.get(cb)
        if ga is None or gb is None:
            return None
        d = ga.distance(gb)
        if d <= MAX_CRUCE_M:
            pa, pb = nearest_points(ga, gb)
            return orden, d, a_wgs84((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)
    return None


def cruce(a, b):
    """Prefiere el resultado por vértices de cualquier par de codvias; si no hay, el de segmentos."""
    res = [r for ca in codvias(a) for cb in codvias(b) if (r := _cruce_vias(ca, cb))]
    return min(res) if res else None


def numero(calle, n):
    for cv in codvias(calle):
        if (cv, n) in portal:
            return portal[(cv, n)], "portal"
        cand = [(abs(m - n), pt) for m, pt in num_por_via.get(cv, []) if m % 2 == n % 2 and abs(m - n) <= 10]
        if cand:
            return min(cand)[1], "portal_cercano"
    return None, None


def geocode(u):
    u = (u or "").strip()
    if " cruce " in u:
        a, b = u.split(" cruce ", 1)
        r = cruce(a, b)
        return (r[2], "cruce", r[1]) if r else (None, "cruce_fallo", None)
    m = re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$", u)
    if m:
        pt, how = numero(m.group(1), int(m.group(2)))
        return pt, (how or "numero_fallo"), None
    return None, "solo_calle", None


if __name__ == "__main__":
    sin = json.loads((RAW / "siniestros-de-trafico-2022-2025.json").read_text())
    out = ROOT / "data/processed/siniestros_geo.csv"
    stats, fallos = C.Counter(), C.Counter()
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "fecha", "gravedad", "tipo", "unidades", "factores", "ubicacion", "metodo", "lon", "lat", "dist_ejes_m"])
        for r in sin:
            pt, how, dist = geocode(r["UBICACION"])
            stats[how] += 1
            if pt is None and how != "solo_calle":
                fallos[r["UBICACION"].split(" cruce ")[0]] += 1
            w.writerow([r["_id"], r["FECHA"], r["TIPO GRAVEDAD"], r["TIPO ACCIDENTE"], r["UNIDADES_IMPLICADAS"],
                        r["FACTORES CONCURRENTES"], r["UBICACION"], how,
                        f"{pt[0]:.6f}" if pt else "", f"{pt[1]:.6f}" if pt else "", f"{dist:.1f}" if dist is not None else ""])
    tot = sum(stats.values())
    ok = sum(v for k, v in stats.items() if k in ("cruce", "portal", "portal_cercano"))
    print(f"geocodificados {ok}/{tot} ({ok/tot:.1%})", dict(stats))
    print("calles que más fallan:", fallos.most_common(15))
