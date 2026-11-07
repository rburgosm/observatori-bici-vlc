_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import os; os.environ.update(OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
import json
import sys
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(_ROOT+"")
RAW = ROOT / "data/raw"
CRS = "EPSG:25830"
# años: los completos (12 meses) de los siniestros que tienen fichero de IMD de carril bici de Movilidad
_f = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", usecols=["fecha"], parse_dates=["fecha"]).fecha
AÑOS = sorted(int(a) for a, n in _f.groupby(_f.dt.year).agg(lambda x: x.dt.month.nunique()).items()
              if n == 12 and (RAW / f"intensidades/carril_bici_{a}.ods").exists())
# IMD de vehículos y descripciones de contadores: el fichero más reciente que haya
IMD_VEH = sorted((RAW / "intensidades").glob("imds_vehiculos_*.ods"))[-1]
CB_ULT = RAW / f"intensidades/carril_bici_{AÑOS[-1]}.ods"
N_BOOT = 2000
RNG = np.random.default_rng(20261103)
TIPOS_VIA = {"1": "carril bici", "4": "Jardín del Turia", "6": "senda ciclable", "7": "bus-bici",
             "2": "ciclocalle", "9": "ciclobarrio", "3": "peatonal"}
pd.set_option("display.width", 160)


# ---------- exposición ----------
def imd_anual(path, patron):
    """Media de las IMD mensuales (>0) por código; los meses a 0 se tratan como avería."""
    # el formato cambia entre hojas (columnas desplazadas, sin «Sentido»): se detectan por contenido
    partes = []
    for h in pd.read_excel(path, engine="odf", sheet_name=None, header=None).values():
        es_cod = h.apply(lambda c: c.astype(str).str.strip().str.fullmatch(patron).mean())
        c_cod = es_cod.idxmax()
        filas = h[h[c_cod].astype(str).str.strip().str.fullmatch(patron)]
        num = filas.drop(columns=c_cod).apply(lambda c: pd.to_numeric(c, errors="coerce").notna().mean())
        c_imd = num[num > .5].index.max()                  # la columna numérica más a la derecha
        partes.append(pd.DataFrame({"cod": filas[c_cod].astype(str).str.strip(),
                                    "imd": pd.to_numeric(filas[c_imd], errors="coerce")}))
    d = pd.concat(partes)
    return d[d.imd > 0].groupby("cod").imd.agg(["mean", "size"])


esp = gpd.read_file(RAW / "siniestros/espiras_bici.geojson").to_crs(CRS)
esp = esp[esp.geometry.notna()].drop_duplicates("idpm")
bici = []
for a in AÑOS:
    t = imd_anual(RAW / f"intensidades/carril_bici_{a}.ods", r"P\d+")
    t = t[t["size"] >= 6]                                  # al menos medio año con dato
    bici.append(pd.DataFrame({"idpm": t.index.str[1:].astype(int), "año": a, "imd": t["mean"].values}))
bici = pd.concat(bici)
cont = esp[esp.idpm.isin(bici.idpm)][["idpm", "geometry"]].reset_index(drop=True)

# agrupar contadores a <50 m en un sitio
grupos = gpd.GeoDataFrame(geometry=[cont.buffer(25).union_all()], crs=CRS).explode(ignore_index=True)
grupos["sitio"] = grupos.index
cont = gpd.sjoin(cont, grupos, predicate="within").drop(columns="index_right")
sitios = cont.dissolve("sitio").centroid.rename("geometry").to_frame().set_geometry("geometry")
expo = (bici.merge(cont[["idpm", "sitio"]], on="idpm").groupby(["sitio", "año"])
        .agg(imd_bici=("imd", "sum"), n_cont=("idpm", "size")).reset_index())
# un sitio-año solo vale si están todos sus contadores (si no, la IMD sumada está incompleta)
expo = expo[expo.n_cont == expo.sitio.map(cont.groupby("sitio").size())]

tr = gpd.read_file(RAW / "siniestros/intensidad_tramos.geojson")
tr = tr[tr.geometry.notna()].to_crs(CRS)
veh = imd_anual(IMD_VEH, r"A\d+")
tr = tr.merge(veh["mean"].rename("imd_veh"), left_on="idtramo", right_index=True)

# ---------- diseño del sitio ----------
reg = gpd.read_file(RAW / "siniestros/reguladores_semaforos.geojson")
reg = reg[reg.geometry.notna()].to_crs(CRS)
via = gpd.read_file(RAW / "siniestros/carriles_bici.geojson")
via = via[via.geometry.notna() & via.estado.isin(TIPOS_VIA)].to_crs(CRS)
tv = gpd.sjoin_nearest(sitios, via[["estado", "geometry"]], max_distance=30, how="left", distance_col="d")
tv = tv[~tv.index.duplicated()]
sitios["tipo_via"] = tv.estado.map(TIPOS_VIA).fillna("sin vía a 30 m")
# agrupación con casos suficientes: carril bici / Turia / otro
sitios["via"] = sitios.tipo_via.where(sitios.tipo_via.isin(["carril bici", "Jardín del Turia"]), "otra o ninguna")

# ---------- siniestros ----------
s = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", parse_dates=["fecha"])
n0 = len(s)
s = s[s.fecha.dt.year.isin(AÑOS)]
s = s.loc[~s.drop(columns="id").duplicated()]
s = s[s.lon.notna()]
s["año"] = s.fecha.dt.year
s = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs="EPSG:4326").to_crs(CRS)
s["vmp"] = s.unidades.str.contains("VMP", na=False)
s["bici"] = s.unidades.str.contains("BICICLETA", na=False)

print(f"siniestros: {n0} → {len(s)} geocodificados {AÑOS[0]}-{AÑOS[-1]} sin duplicados (bici: {s.bici.sum()}, VMP: {s.vmp.sum()})")
print(f"contadores con IMD y posición: {len(cont)} → {len(sitios)} sitios; sitio-años con exposición: {len(expo)}")
print(f"tramos de vehículos con IMD ({IMD_VEH.stem}) y geometría: {len(tr)}; reguladores semafóricos: {len(reg)}")
print("tipo de vía ciclista del sitio:", sitios.tipo_via.value_counts().to_dict(), "\n")


def panel(radio, grupo):
    """Sitio × año con N, IMD bici, IMD vehículos (máximo de los tramos a <=radio) y diseño."""
    ev = s[s[grupo]] if grupo != "vmp_o_bici" else s[s.vmp | s.bici]
    asig = gpd.sjoin_nearest(ev[["año", "geometry"]], sitios[["geometry"]], max_distance=radio, how="inner")
    n = asig.groupby(["sitio", "año"]).size().rename("N")
    p = expo.set_index(["sitio", "año"]).join(n).fillna({"N": 0}).reset_index()
    zonas = gpd.GeoDataFrame({"sitio_v": sitios.index}, geometry=sitios.buffer(radio).values, crs=CRS)
    v = gpd.sjoin(tr[["imd_veh", "geometry"]], zonas)
    p["imd_veh"] = p.sitio.map(v.groupby("sitio_v").imd_veh.max())
    p["sin_veh"] = p.imd_veh.isna().astype(int)
    # sin tramo aforado cerca: vía local; se imputa la IMD mínima observada y se marca con indicador
    p["imd_veh"] = p.imd_veh.fillna(tr.imd_veh.min())
    p["l_bici"], p["l_veh"] = np.log(p.imd_bici), np.log(p.imd_veh)
    sem = gpd.sjoin(reg[["geometry"]], zonas).groupby("sitio_v").size()
    p["semaforo"] = p.sitio.map(sem).fillna(0).gt(0).astype(int)
    p["via"] = p.sitio.map(sitios.via)
    return p, len(asig), len(ev)

F_BASE = "N ~ l_bici + l_veh + sin_veh + C(año)"
F_DISEÑO = F_BASE + " + semaforo"


def ajustar(p, f=F_BASE):
    return smf.negativebinomial(f, p).fit(disp=0, maxiter=300)


def eb(p, nb, años):
    q = p[p.año.isin(años)].copy()
    q["mu"] = nb.predict(q)
    a = nb.params["alpha"]
    g = q.groupby("sitio").agg(N=("N", "sum"), mu=("mu", "sum"), expo=("imd_bici", "sum"))
    g["w"] = 1 / (1 + a * g.mu)
    g["EB"] = g.w * g.mu + (1 - g.w) * g.N
    g["exceso"] = g.EB - g.mu
    g["p_exceso"] = stats.gamma.sf(1, a=1 / a + g.N, scale=1 / (1 / a + g.mu))
    g["tasa_bruta"] = g.N / g.expo
    return g

