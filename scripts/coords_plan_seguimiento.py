"""Rellena lon/lat de las filas de lugar de data/processed/plan_seguimiento.csv.

Solo toca las filas con ambito=lugar, lon vacío y un id en LUGARES. Para cada una
toma los siniestros geocodificados de data/processed/siniestros_geo.csv cuya
ubicación cumple todos los patrones de un grupo (cruces) y devuelve la mediana de
lon/lat. Es una coordenada de referencia para el mapa, no un levantamiento.
No usa servicios externos. Respeta el resto del CSV.
Desde el 06/11/2026 el Plan vive en la base (data/processed/observatorio.sqlite) y plan_seguimiento.csv es su exportación:
tras usar este script, incorporar el CSV con `construir_sqlite.py --plan-desde-csv` y revisar el diff de
data/processed/observatorio_plan.sql antes de publicar (si no, make sqlite se para: el CSV se ha editado fuera de la base).

Uso: .venv/bin/python -I scripts/coords_plan_seguimiento.py
"""
import csv
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data/processed/plan_seguimiento.csv"
GEO = RAIZ / "data/processed/siniestros_geo.csv"

# id -> (lista de grupos de patrones; un siniestro vale si cumple todos los de algún grupo, solo_cruce)
LUGARES = {
    "3.2.2-pl-zaragoza": ([["PL ZARAGOZA"]], True),
    "3.7-blasco-benlloch-clariano": ([["BLASCO IBA", "CARDENAL BENLLOCH"], ["BLASCO IBA", "CLARIANO"]], True),
    "3.7-granvia-guimera": ([["ANGEL GUIMERA", "FERNANDO EL CATOLICO"]], True),
    "3.7-benlloch-puerto": ([["CARDENAL BENLLOCH", "AV PUERTO"]], True),
    "3.2.2-ausias-abril": ([["AUSIAS MARCH", "ABRIL MARTORELL"]], True),
    "3.2.2-naranjos-peixo": ([["AV NARANJOS", "LUIS PEIXO"]], True),
    "3.2.2-abril-malilla": ([["ABRIL MARTORELL", "CTRA MALILLA"]], True),
    "3.2.2-jardin-turia": ([["JARDÍN DEL TURIA"]], False),
    # tramo Pont del Regne - Montolivet: se usa el cruce del Pont del Regne como referencia
    "3.2.2-albereda-carril": ([["PG ALAMEDA", "PUENTE DEL REINO"]], True),
    "3.2.2-puerto-carril": ([["AV PUERTO"]], False),
    "3.2.2-campos-crespo": ([["CAMPOS CRESPO"]], False),
    "3.2.2-giorgeta-perez-galdos": ([["AV GIORGETA"], ["AV PEREZ GALDOS"]], False),
    # v2 (04/11/2026): tramo pl. de Jesús - Dr. Tomàs Sala; se usa la mediana de toda la avenida (aproximada)
    "3.2.2-gaspar-aguilar": ([["AV GASPAR AGUILAR"]], False),
}

# Cruces sin siniestros geocodificados: intersección de los ejes del callejero (EPSG:25830)
CRUCES_EJES = {
    "3.2.2-xativa-jesus": (("CARRER", "XÀTIVA"), ("CARRER", "JESÚS")),
}


# Tramos de calle entre dos cruces: punto medio del eje de la calle entre sus encuentros con las dos calles que lo
# limitan (callejero, EPSG:25830). La licitación de 10/2026 dice «C/ Nicolás Factor»; en el callejero es la
# C/ Beat Nicolau Factor (codvia 9450), que se cruza con María Jordán (45450) y Assagador de les Monges (7830).
TRAMOS_EJES = {
    "3.2.2-nicolas-factor": (9450, 45450, 7830),
}


def tramo_por_ejes(codvias):
    import geopandas as gpd
    from shapely.ops import linemerge, substring
    ejes = gpd.read_file(RAIZ / "data/raw/siniestros/ejes.geojson").to_crs(25830)
    calle, a, b = (ejes[ejes.codvia == c].union_all() for c in codvias)
    linea = linemerge(calle)
    if linea.geom_type != "LineString":
        return None
    pa, pb = (linea.project(linea.intersection(x).centroid) for x in (a, b))
    punto = substring(linea, min(pa, pb), max(pa, pb)).interpolate(0.5, normalized=True)
    c = gpd.GeoSeries([punto], crs=25830).to_crs(4326).iloc[0]
    return f"{c.x:.6f}", f"{c.y:.6f}"


def cruce_por_ejes(par):
    import geopandas as gpd
    ejes = gpd.read_file(RAIZ / "data/raw/siniestros/ejes.geojson").to_crs(25830)
    geoms = [ejes[(ejes.tipcalle == t) & (ejes.nomcalle == n)].union_all() for t, n in par]
    punto = geoms[0].intersection(geoms[1])
    if punto.is_empty:
        # los ejes no se tocan (p. ej. la calle nace en una plaza): punto medio de los más cercanos, si están a menos de 150 m (Xàtiva y Jesús se unen por la Pl. de Sant Agustí)
        from shapely.geometry import LineString
        from shapely.ops import nearest_points
        a, b = nearest_points(geoms[0], geoms[1])
        if a.distance(b) > 150:
            return None
        punto = LineString([a, b]).interpolate(0.5, normalized=True)
    c = gpd.GeoSeries([punto.centroid], crs=25830).to_crs(4326).iloc[0]
    return f"{c.x:.6f}", f"{c.y:.6f}"


def main():
    geo = pd.read_csv(GEO, usecols=["ubicacion", "metodo", "lon", "lat"]).dropna(subset=["ubicacion", "lon", "lat"])
    geo["u"] = geo["ubicacion"].str.upper()

    with open(CSV, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        campos = lector.fieldnames
        filas = list(lector)

    for fila in filas:
        if fila["ambito"] != "lugar" or fila["lon"]:
            continue
        if fila["id"] in CRUCES_EJES:
            res = cruce_por_ejes(CRUCES_EJES[fila["id"]])
            if res:
                fila["lon"], fila["lat"] = res
                print(f"{fila['id']}: ejes -> {res}")
            continue
        if fila["id"] in TRAMOS_EJES:
            res = tramo_por_ejes(TRAMOS_EJES[fila["id"]])
            if res:
                fila["lon"], fila["lat"] = res
                print(f"{fila['id']}: tramo de eje -> {res}")
            continue
        if fila["id"] not in LUGARES:
            continue
        grupos, solo_cruce = LUGARES[fila["id"]]
        base = geo[geo["metodo"] == "cruce"] if solo_cruce else geo
        mascara = pd.Series(False, index=base.index)
        for grupo in grupos:
            m = pd.Series(True, index=base.index)
            for patron in grupo:
                m &= base["u"].str.contains(patron, regex=False)
            mascara |= m
        sel = base[mascara]
        if sel.empty:
            print(f"{fila['id']}: sin coincidencias")
            continue
        fila["lon"] = f"{sel['lon'].median():.6f}"
        fila["lat"] = f"{sel['lat'].median():.6f}"
        print(f"{fila['id']}: n={len(sel)} -> {fila['lon']}, {fila['lat']}")

    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    main()
