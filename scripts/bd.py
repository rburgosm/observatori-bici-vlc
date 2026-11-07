"""Lectura de data/processed/observatorio.sqlite (la fuente de los datos ya calculados) para los scripts con pandas.

Devuelve las mismas tablas que antes se leían de los CSV, con los mismos tipos (vacíos como NaN, fechas como datetime),
para que el cambio de fuente no cambie ningún resultado:
- todos(con): todas las filas de siniestros_geo.csv (tabla siniestro);
- siniestros(con): las del análisis (años completos y sin duplicados, en_analisis = 1) y los años, como lugares.siniestros();
- bici_vmp(con, s): los de bici o VMP con año, v, dir, w y k de siniestro_bv, y la cobertura, como lugares.bici_vmp();
- lugares(con): outputs/lugares_nudos.csv (tabla lugar, índice uid); resumen(con): lugares_nudos_resumen.json;
- geom_lugares(con): geometría exacta de cada lugar (EPSG:25830) con su tipo, como lugares.unidades() en esos uid;
- uid_siniestro(con): lugar de cada siniestro situado (siniestro_lugar);
- plan(con): una fila por actuación del Plan, con los campos de la base (fecha_fuente, fecha_comprobacion, ref_plan,
  texto_plan, clase, fuente principal y fuente del estado) y las fuentes de la nota en su orden.
Uso: import bd; con = bd.conectar()"""
import json, sqlite3
from pathlib import Path

import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/processed/observatorio.sqlite"
COLS_SIN = ["id", "fecha", "gravedad", "tipo", "unidades", "factores", "ubicacion", "metodo", "lon", "lat", "dist_ejes_m"]


def conectar(ruta=DB):
    if not ruta.exists():
        raise SystemExit(f"falta {ruta.relative_to(ROOT)}: ejecutar make sqlite")
    return sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)


# textos que read_csv lee como vacíos por defecto (los scripts leían así siniestros_geo.csv): el portal escribe «NULL» en
# TIPO_ACCIDENTE de muchas filas y la base lo guarda tal cual (para exportar el CSV idéntico); al leer cuentan como vacío
NA_CSV = {"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL",
          "NaN", "None", "n/a", "nan", "null"}


def _nan(d, na=False):
    """NULL de texto -> NaN (como read_csv con una celda vacía); con na, también los textos de NA_CSV."""
    for c in d.columns:
        if d[c].dtype == object or pd.api.types.is_string_dtype(d[c]):
            m = d[c].notna()
            if na: m &= ~d[c].isin(NA_CSV)
            d[c] = d[c].where(m, np.nan)
    return d


def todos(con, con_analisis=False):
    s = pd.read_sql_query(f"SELECT {', '.join(COLS_SIN)}{', en_analisis' if con_analisis else ''} FROM siniestro ORDER BY id", con)
    s["fecha"] = pd.to_datetime(s.fecha)
    for c in ("lon", "lat", "dist_ejes_m"): s[c] = s[c].astype(float)
    return _nan(s, na=True)


def años(con):
    return [int(a) for a in con.execute("SELECT valor FROM meta WHERE clave = 'años'").fetchone()[0].split(",")]


def siniestros(con):
    s = todos(con, con_analisis=True)
    s = s[s.pop("en_analisis") == 1].copy()
    return s, años(con)


def bici_vmp(con, s):
    s = s.copy()
    s["vmp"] = s.unidades.str.contains("VMP", na=False); s["bici"] = s.unidades.str.contains("BICICLETA", na=False)
    b = pd.read_sql_query("SELECT siniestro_id AS id, año, v, dir, peso AS w, k FROM siniestro_bv", con)
    s = s[s.id.isin(b.id)].copy()
    assert len(s) == len(b), "siniestro_bv no coincide con los siniestros del análisis: make sqlite"
    b = b.set_index("id").loc[s.id]
    for c in ("año", "v", "dir", "w", "k"):
        s[c] = b[c].values
    s["año"] = s["año"].astype(s.fecha.dt.year.dtype)
    s["w"] = s.w.astype(float).fillna(np.inf)                  # sin punto («otra»): peso infinito, como lugares.bici_vmp
    cob = s.groupby(["año", "dir"]).lon.apply(lambda x: x.notna().mean())
    return s, cob


def lugares(con):
    cols = [c for (c,) in con.execute("SELECT columna FROM _export_formato WHERE csv = 'outputs/lugares_nudos.csv' ORDER BY orden")]
    fmt = dict(con.execute("SELECT columna, formato FROM _export_formato WHERE csv = 'outputs/lugares_nudos.csv'"))
    L = pd.read_sql_query(f"SELECT {', '.join(cols)} FROM lugar ORDER BY rank", con)
    for c in cols:
        if fmt[c] == "b": L[c] = L[c].astype(bool)
        elif fmt[c] == "f": L[c] = L[c].astype(float)
    return _nan(L).set_index("uid")


def resumen(con):
    return {k: json.loads(v) for k, v in con.execute("SELECT clave, valor FROM resumen_lugares")}


def geom_lugares(con, crs="EPSG:25830"):
    import geopandas as gpd, shapely
    d = pd.read_sql_query("SELECT g.uid, l.tipo, g.geom FROM lugar_geom g JOIN lugar l USING (uid) ORDER BY g.uid", con)
    return gpd.GeoDataFrame(d[["uid", "tipo"]], geometry=shapely.from_wkb(d.geom.values), crs=crs).set_index("uid")


def uid_siniestro(con):
    return dict(con.execute("SELECT siniestro_id, uid FROM siniestro_lugar"))


def plan(con):
    """Actuaciones en el orden de la base (el del CSV validado). Textos vacíos como "" (como el CSV leído con fillna(""));
    lon/lat como número (NaN sin coordenadas). fuente_*: la principal (título con el que la cita esta actuación);
    estado_*: la que respalda el estado; notas: URL de las fuentes citadas en la nota, en su orden."""
    P = pd.read_sql_query("""
        SELECT a.id, a.orden, a.clase, a.accion_plan, a.actuacion, a.ambito, a.lugar, a.lon, a.lat, a.meta, a.estado,
               a.fecha_fuente, a.fecha_comprobacion, a.ref_plan, a.texto_plan, a.nota,
               f.url AS fuente_url, f.tipo AS fuente_tipo, af.titulo_cita AS fuente_titulo,
               fe.url AS estado_url, fe.tipo AS estado_tipo, fe.titulo AS estado_titulo
        FROM plan_actuacion a JOIN plan_fuente f ON f.id = a.fuente_id
        LEFT JOIN plan_actuacion_fuente af ON af.actuacion_id = a.id AND af.fuente_id = a.fuente_id AND af.rol = 'principal'
        LEFT JOIN plan_fuente fe ON fe.id = a.fuente_estado_id
        ORDER BY a.orden""", con)
    notas = {}
    for i, u in con.execute("""SELECT af.actuacion_id, f.url FROM plan_actuacion_fuente af JOIN plan_fuente f ON f.id = af.fuente_id
                               WHERE af.rol = 'nota' ORDER BY af.actuacion_id, af.pos"""):
        notas.setdefault(i, []).append(u)
    lon, lat = P.lon.astype(float), P.lat.astype(float)
    P = P.drop(columns=["lon", "lat"]).fillna("")
    P["lon"], P["lat"] = lon, lat
    P["notas"] = [notas.get(i, []) for i in P.id]
    return P


def tipo_fuente(con, url):
    r = con.execute("SELECT tipo FROM plan_fuente WHERE url = ?", (url,)).fetchone()
    return r[0] if r else None
