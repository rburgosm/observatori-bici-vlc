"""Base de datos del observatorio: data/processed/observatorio.sqlite, fuente única de lo que publica la web.

Por qué ahí: es un dato procesado como los CSV de data/processed/ (no se publica tal cual: la web y las fichas se
generan a partir de ella) y está fuera de web/proto/build/, que se borra y se sube entera.

Dirección de los datos (06/11/2026, las notas internas de trabajo, «SQLite y fichas estáticas»):
- TODOS los consumidores leen de la base: exportar_web.py y comprobar.py (con scripts/bd.py), fichas.py, los bocetos
  (los bocetos de diseño (internos), sqlite3 de la biblioteca estándar) y aplicar_propuestas_plan.py.
- Seguimiento del Plan: la base es su FUENTE DE VERDAD. Se carga del volcado en texto data/processed/observatorio_plan.sql
  (en git; la primera vez, o con --plan-desde-csv, de plan_seguimiento.csv) y, al terminar, se reescriben el volcado y su
  exportación plan_seguimiento.csv. Lo escribe aplicar_propuestas_plan.py (UPDATE/INSERT en una transacción).
- Entradas que se siguen leyendo de texto (sin rehacer ningún análisis): siniestros_geo.csv (geocodificar.py),
  outputs/lugares_nudos.* (lugares_nudos.py), nombres_lugares.csv y docs/cambios.csv (a mano) y fichas_slugs.csv.
  exportar(...) las regenera byte a byte desde la base (`--comprobar`): si no coinciden, la base está desfasada.

Tablas (esquema completo en ESQUEMA, abajo; PRAGMA foreign_keys = ON al construir):
- meta: versión del esquema y de la web, conjunto y fecha de los datos, fuente, licencia, aviso, umbral de las fichas.
- siniestro: data/processed/siniestros_geo.csv (todas las filas) + en_analisis (años completos y sin duplicados: el
  filtro de lugares.siniestros(), el de todos los scripts).
- siniestro_bv: los de bici o VMP del análisis (lugares.bici_vmp): v (b bici, p patinete, a los dos), k (con quién), dir
  (cruce, portal, otra) y peso (1 / cobertura de su año y tipo de dirección; NULL sin punto).
- via: callejero vigente (vias.json), con el nombre oficial y el castellano limpios (lugares._vias).
- siniestro_via + siniestro_direccion: a qué calles (codvia) pertenece cada siniestro por su DIRECCIÓN ESCRITA
  (ubicacion): las dos calles de un cruce, la del portal o la de «solo calle». Mismo índice nombre -> codvia que el
  geocodificador (geocodificar.codvias). Ambigüedad (el nombre casa con varias vías): si el siniestro tiene punto, la
  vía candidata más cercana (<= 50 m); si no, queda sin asignar y cuenta en n_ambiguas.
- nombre_lugar: data/processed/nombres_lugares.csv (nombres congelados).
- lugar: outputs/lugares_nudos.csv (los lugares con siniestros) + nombre_id; resumen_lugares: outputs/lugares_nudos_resumen.json.
- siniestro_lugar: asignación de cada siniestro de bici o VMP con punto a su lugar (lugares.asignar, la misma de
  lugares_nudos.py y exportar_web.py; se comprueba que los recuentos coinciden con lugar.n).
- plan_fuente, plan_actuacion, plan_actuacion_fuente, plan_actuacion_lonlat: el seguimiento validado del Plan, con los campos
  separados (fecha de la fuente / fecha de comprobación; referencia del PDF / texto del Plan; fuente principal / fuente
  que respalda el estado / fuentes citadas en la nota) y clase (indicador_impacto o medida).
- plan_actuacion_lugar / plan_actuacion_via: actuaciones con coordenadas junto a un lugar (lugares.asignar, <= R m, como
  exportar_web.py) o a menos de R m del eje de una calle (punto aproximado: ver la nota de exportar_web.py).
- cambio: docs/cambios.csv.
- ficha: fichas estáticas publicadas (lloc = lugar, carrer = calle), con slug congelado en data/processed/fichas_slugs.csv.

- lugar_geom: geometría exacta de cada lugar con siniestros (WKB, EPSG:25830), la que dibuja y mide exportar_web.py.

Uso: .venv/bin/python -I scripts/construir_sqlite.py              (construye la base; reescribe volcado y CSV del Plan si cambian)
     .venv/bin/python -I scripts/construir_sqlite.py --comprobar  (construye y comprueba que exporta los CSV idénticos)
     .venv/bin/python -I scripts/construir_sqlite.py --exportar DIR   (escribe los CSV exportados en DIR)
     .venv/bin/python -I scripts/construir_sqlite.py --plan-desde-csv (importa el Plan de plan_seguimiento.csv editado a mano)
     .venv/bin/python -I scripts/construir_sqlite.py --volcar     (solo reescribe volcado y CSV del Plan desde la base)"""
import argparse, csv, datetime, hashlib, io, json, os, re, sqlite3, sys, unicodedata
from pathlib import Path

import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
DB = ROOT / "data/processed/observatorio.sqlite"
SLUGS = ROOT / "data/processed/fichas_slugs.csv"
ESQUEMA_VERSION = "1"
# Umbral de una ficha publicada: >= 5 siniestros con bici o VMP en los años completos. Por qué 5:
# - con 1-4 casos la página es, en la práctica, la ficha de uno o dos sucesos concretos: no dice nada de un lugar
#   (la pista exige >= 20 casos con Holm; los «de cada 10» con 4 casos son ruido) y, al ser una URL indexable con el
#   nombre del sitio, facilita llegar a un suceso concreto desde un buscador (exposición, docs/dataset_licencia_privacidad.md);
# - 5 es el umbral habitual de supresión de celdas pequeñas en estadística pública;
# - deja 253 lugares (de 2.138 con casos: el 55 % de los siniestros situados) y las calles con algo que contar.
# El mapa sigue enseñando todos los puntos; lo que no tiene ficha propia solo no tiene URL.
MIN_FICHA = 5
FUENTE = ("Ajuntament de València – Dades Obertes (opendata.vlci.valencia.es), CC BY 4.0: siniestros de tráfico, callejero, "
          "carril bici y puntos de conteo. Datos modificados por el observatorio: los siniestros se sitúan en el mapa con el "
          "callejero. El Ajuntament de València no participa en este trabajo ni lo avala.")
LICENCIA = "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)"
AVISO = ("Sin datos de las personas implicadas. Está prohibido reidentificar personas cruzando estos datos con otras fuentes "
         "(política de uso del portal de datos abiertos de València).")
ESTADOS = ("sin_info", "anunciada", "en_marcha", "hecha")
FUENTE_TIPOS = ("plan", "contratacion", "bop", "junta_gobierno", "nota_prensa", "documento_municipal", "prensa", "respuesta_movilidad")
GRAVEDADES = ("SIN HERIDOS", "CON HERIDOS LEVES", "CON HERIDOS BAJA GRAVEDAD", "CON HERIDOS GRAVES", "CON FALLECIDOS")
METODOS = ("cruce", "portal", "portal_cercano", "cruce_fallo", "numero_fallo", "solo_calle")
AMBIGUA_MAX_M = 50              # vía candidata más cercana al punto del siniestro, si está a <= 50 m

ISO_D = "GLOB '[0-9][0-9][0-9][0-9]-[01][0-9]-[0-3][0-9]'"
def _in(xs): return "(" + ", ".join(f"'{x}'" for x in xs) + ")"

# ---------------------------------------------------------------- esquema
ESQUEMA = f"""
CREATE TABLE meta (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);

CREATE TABLE siniestro (
  id INTEGER PRIMARY KEY,                  -- _id del portal
  fecha TEXT NOT NULL CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[01][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]'),
  gravedad TEXT NOT NULL CHECK (gravedad IN {_in(GRAVEDADES)}),
  tipo TEXT, unidades TEXT, factores TEXT, ubicacion TEXT,
  metodo TEXT NOT NULL CHECK (metodo IN {_in(METODOS)}),
  lon REAL, lat REAL, dist_ejes_m REAL,
  en_analisis INTEGER NOT NULL CHECK (en_analisis IN (0, 1)),   -- años completos y sin duplicados (lugares.siniestros)
  CHECK ((lon IS NULL) = (lat IS NULL)),
  CHECK (lon IS NULL OR metodo IN ('cruce', 'portal', 'portal_cercano'))
);
CREATE INDEX siniestro_fecha ON siniestro (fecha);

CREATE TABLE siniestro_bv (                 -- con bici o VMP, del análisis (lugares.bici_vmp)
  siniestro_id INTEGER PRIMARY KEY REFERENCES siniestro (id),
  año INTEGER NOT NULL,
  v TEXT NOT NULL CHECK (v IN ('b', 'p', 'a')),          -- b solo bici, p solo patinete, a los dos
  k TEXT NOT NULL CHECK (k IN ('m', 'w', 'd', 's')),     -- con quién: m vehículo, w peatón, d entre bicis o VMP, s solo
  dir TEXT NOT NULL CHECK (dir IN ('cruce', 'portal', 'otra')),
  peso REAL                                              -- 1 / cobertura de su año y tipo de dirección; NULL sin punto
);
CREATE INDEX siniestro_bv_año ON siniestro_bv (año);

CREATE TABLE via (
  codvia INTEGER PRIMARY KEY,
  codtipovia TEXT NOT NULL, nomoficial TEXT NOT NULL, traducnooficial TEXT,
  nom TEXT NOT NULL,                       -- «AV PÉREZ GALDÓS» (tipo + nombre oficial, sin paréntesis aclaratorio)
  nom_es TEXT NOT NULL                     -- forma castellana del callejero cuando es válida (lugares._vias)
);

CREATE TABLE siniestro_via (
  siniestro_id INTEGER NOT NULL REFERENCES siniestro (id),
  codvia INTEGER NOT NULL REFERENCES via (codvia),
  rol TEXT NOT NULL CHECK (rol IN ('cruce', 'portal', 'calle')),
  resuelta TEXT NOT NULL CHECK (resuelta IN ('unica', 'por_distancia')),
  PRIMARY KEY (siniestro_id, codvia)
);
CREATE INDEX siniestro_via_codvia ON siniestro_via (codvia);

CREATE TABLE siniestro_direccion (           -- cobertura de la asignación a calles, por siniestro
  siniestro_id INTEGER PRIMARY KEY REFERENCES siniestro (id),
  partes INTEGER NOT NULL,                  -- calles que nombra la dirección (2 en un cruce)
  resueltas INTEGER NOT NULL, ambiguas INTEGER NOT NULL, sin_via INTEGER NOT NULL,
  CHECK (resueltas + ambiguas + sin_via = partes)
);

CREATE TABLE nombre_lugar (                  -- nombres congelados (data/processed/nombres_lugares.csv, en su orden)
  id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL CHECK (tipo IN ('nudo', 'tramo')),
  codvia INTEGER, x REAL NOT NULL, y REAL NOT NULL,       -- centroide en EPSG:25830
  nom TEXT NOT NULL UNIQUE, nom_es TEXT NOT NULL,
  alta TEXT NOT NULL CHECK (alta {ISO_D}),
  CHECK ((tipo = 'tramo') = (codvia IS NOT NULL))
);

CREATE TABLE lugar (                         -- outputs/lugares_nudos.csv (columnas y orden de filas iguales)
  uid INTEGER PRIMARY KEY, rank INTEGER NOT NULL UNIQUE,
  tipo TEXT NOT NULL CHECK (tipo IN ('nudo', 'tramo')),
  nom TEXT NOT NULL UNIQUE REFERENCES nombre_lugar (nom), nom_es TEXT NOT NULL, nom_calc TEXT, nom_es_calc TEXT,
  nuevo INTEGER NOT NULL CHECK (nuevo IN (0, 1)), dir TEXT, lon REAL NOT NULL, lat REAL NOT NULL, ext_m REAL, long_m REAL,
  plaza INTEGER NOT NULL CHECK (plaza IN (0, 1)), codvia INTEGER, cruce_frac REAL,
  n INTEGER NOT NULL CHECK (n > 0), W REAL,
  {", ".join(f"n{y} INTEGER" for y in range(2022, 2026))}, {", ".join(f"w{y} REAL" for y in range(2022, 2026))},
  nA REAL, nB REAL, WA REAL, WB REAL, nA7 REAL, nB7 REAL, WA7 REAL, WB7 REAL, rankA INTEGER, rankB REAL,
  v_b INTEGER, v_p INTEGER, v_a INTEGER, k_m INTEGER, k_w INTEGER, k_d INTEGER, k_s INTEGER,
  p_min REAL, pista_holm TEXT CHECK (pista_holm IN ('m', 'w', 'd', 's')), pista_bh TEXT CHECK (pista_bh IN ('m', 'w', 'd', 's')),
  en_top30 INTEGER NOT NULL CHECK (en_top30 IN (0, 1)), geom_wkt TEXT NOT NULL,
  nombre_id INTEGER NOT NULL REFERENCES nombre_lugar (id),
  CHECK ((tipo = 'tramo') = (codvia IS NOT NULL)),
  CHECK (v_b + v_p + v_a = n AND k_m + k_w + k_d + k_s = n)
);
CREATE TABLE lugar_geom (                    -- geometría exacta de cada lugar (lugares.unidades, EPSG:25830, WKB): envolvente
  uid INTEGER PRIMARY KEY REFERENCES lugar (uid),   -- del nudo (la zona que se dibuja es + R) o línea del tramo
  geom BLOB NOT NULL
);
CREATE TABLE resumen_lugares (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);   -- outputs/lugares_nudos_resumen.json (JSON por clave)

CREATE TABLE siniestro_lugar (
  siniestro_id INTEGER PRIMARY KEY REFERENCES siniestro_bv (siniestro_id),
  uid INTEGER NOT NULL REFERENCES lugar (uid)
);
CREATE INDEX siniestro_lugar_uid ON siniestro_lugar (uid);

CREATE TABLE plan_fuente (
  id INTEGER PRIMARY KEY,
  url TEXT NOT NULL UNIQUE CHECK (url LIKE 'http%'),
  tipo TEXT NOT NULL CHECK (tipo IN {_in(FUENTE_TIPOS)}),
  tipo_origen TEXT NOT NULL CHECK (tipo_origen IN ('declarado', 'deducido_url')),   -- deducido: solo citada en una nota
  titulo TEXT
);
CREATE TABLE plan_actuacion (
  id TEXT PRIMARY KEY,
  orden INTEGER NOT NULL UNIQUE,                         -- orden de las filas del CSV validado
  clase TEXT NOT NULL CHECK (clase IN ('indicador_impacto', 'medida')),
  accion_plan TEXT NOT NULL, actuacion TEXT NOT NULL,
  ambito TEXT NOT NULL CHECK (ambito IN ('ciudad', 'lugar')),
  lugar TEXT, lon REAL, lat REAL, meta TEXT,
  estado TEXT NOT NULL CHECK (estado IN {_in(ESTADOS)}),
  fecha_fuente TEXT CHECK (fecha_fuente {ISO_D}),      -- fecha de la fuente que respalda el estado (era fecha_estado)
  fecha_comprobacion TEXT NOT NULL CHECK (fecha_comprobacion {ISO_D}),   -- cuándo lo comprobó el observatorio (era comprobado)
  fuente_id INTEGER NOT NULL REFERENCES plan_fuente (id),              -- fuente principal de la fila (era fuente_url)
  fuente_estado_id INTEGER REFERENCES plan_fuente (id),                -- la que respalda el estado
  ref_plan TEXT,                                         -- dónde está en el PDF del Plan: «PDF p.65 (pág. 62), l.3080»
  texto_plan TEXT,                                       -- lo que dice el Plan; literal solo lo que va entre «»
  nota TEXT,
  CHECK ((lon IS NULL) = (lat IS NULL)),
  CHECK (estado = 'sin_info' OR (fuente_estado_id IS NOT NULL AND fecha_fuente IS NOT NULL)),
  CHECK (fecha_fuente IS NULL OR fecha_fuente <= fecha_comprobacion)
);
CREATE TABLE plan_actuacion_fuente (
  actuacion_id TEXT NOT NULL REFERENCES plan_actuacion (id),
  fuente_id INTEGER NOT NULL REFERENCES plan_fuente (id),
  rol TEXT NOT NULL CHECK (rol IN ('principal', 'estado', 'nota')),
  titulo_cita TEXT,                                      -- cómo se cita en esta actuación (la misma Memoria, con su apartado)
  pos INTEGER,                                           -- rol nota: orden en que aparece en la nota (1, 2, …)
  PRIMARY KEY (actuacion_id, fuente_id, rol),
  CHECK ((rol = 'nota') = (pos IS NOT NULL))
);
CREATE TABLE plan_actuacion_lonlat (                     -- lon y lat tal como se escribieron (texto), para exportar el CSV igual
  id TEXT PRIMARY KEY REFERENCES plan_actuacion (id), lon TEXT NOT NULL, lat TEXT NOT NULL
);
CREATE TABLE plan_actuacion_lugar (
  actuacion_id TEXT NOT NULL REFERENCES plan_actuacion (id), uid INTEGER NOT NULL REFERENCES lugar (uid),
  d_m REAL NOT NULL,                                     -- sin redondear (la web redondea al mostrarla)
  PRIMARY KEY (actuacion_id, uid)
);
CREATE TABLE plan_actuacion_via (
  actuacion_id TEXT NOT NULL REFERENCES plan_actuacion (id), codvia INTEGER NOT NULL REFERENCES via (codvia),
  d_m REAL NOT NULL,
  nombrada INTEGER NOT NULL CHECK (nombrada IN (0, 1)),  -- la actuación nombra la calle (en «lugar» o «actuacion»)
  PRIMARY KEY (actuacion_id, codvia)
);

CREATE TABLE cambio (
  orden INTEGER PRIMARY KEY,
  fecha TEXT NOT NULL CHECK (fecha {ISO_D}),
  tipo TEXT NOT NULL CHECK (tipo IN ('datos', 'metode', 'web')),
  va TEXT NOT NULL CHECK (va <> ''), es TEXT NOT NULL CHECK (es <> ''),
  -- resumen público (una frase corta; va/es son el detalle): obligatorio, ≤ 120 caracteres y sin saltos de línea
  resumen_va TEXT NOT NULL CHECK (resumen_va <> '' AND length(resumen_va) <= 120 AND instr(resumen_va, char(10)) = 0 AND instr(resumen_va, char(13)) = 0),
  resumen_es TEXT NOT NULL CHECK (resumen_es <> '' AND length(resumen_es) <= 120 AND instr(resumen_es, char(10)) = 0 AND instr(resumen_es, char(13)) = 0)
);

CREATE TABLE ficha (
  slug TEXT NOT NULL CHECK (slug GLOB '[a-z0-9]*' AND slug NOT GLOB '*[^a-z0-9-]*'),
  clase TEXT NOT NULL CHECK (clase IN ('lloc', 'carrer')),             -- URL: /<clase>/<slug>/
  clave TEXT NOT NULL UNIQUE,                            -- lloc: «tipo@x,y» del nombre congelado; carrer: «via@codvia»
  uid INTEGER REFERENCES lugar (uid), codvia INTEGER REFERENCES via (codvia),
  n INTEGER NOT NULL,
  alta TEXT NOT NULL CHECK (alta {ISO_D}),
  PRIMARY KEY (clase, slug),
  CHECK ((clase = 'lloc') = (uid IS NOT NULL) AND (clase = 'carrer') = (codvia IS NOT NULL))
);

-- vistas de consulta
CREATE VIEW v_siniestro_bv AS
  SELECT s.*, b.año, b.v, b.k, b.dir, b.peso, l.uid
  FROM siniestro_bv b JOIN siniestro s ON s.id = b.siniestro_id LEFT JOIN siniestro_lugar l ON l.siniestro_id = b.siniestro_id;
CREATE VIEW v_calle_bv AS                   -- siniestros de bici o VMP por calle (por la dirección escrita)
  SELECT sv.codvia, COUNT(*) AS n, SUM(b.v = 'b') AS v_b, SUM(b.v = 'p') AS v_p, SUM(b.v = 'a') AS v_a
  FROM siniestro_via sv JOIN siniestro_bv b ON b.siniestro_id = sv.siniestro_id GROUP BY sv.codvia;
CREATE VIEW v_plan_medida AS SELECT * FROM plan_actuacion WHERE clase = 'medida';
CREATE VIEW v_plan_indicador AS SELECT * FROM plan_actuacion WHERE clase = 'indicador_impacto';
"""


# ---------------------------------------------------------------- utilidades
def _nulo(x):
    return x is None or (isinstance(x, float) and np.isnan(x)) or x is pd.NA or x == ""


def _val(x):
    """Valor de pandas/numpy -> tipo de sqlite (None para vacío)."""
    if _nulo(x): return None
    if isinstance(x, (np.bool_, bool)): return int(x)
    if isinstance(x, np.integer): return int(x)
    if isinstance(x, np.floating): return float(x)
    return x


def slugify(t):
    t = unicodedata.normalize("NFD", t.replace(" cruce ", " ").replace("·", "").replace("'", " ").replace("–", " "))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


# referencias del PDF del Plan en cita_plan: «PDF p.65 (pág. 62), l.3080» (+ «, l.…» o « y l.…»)
REF = re.compile(r"^PDF p\.\d+(?: \(pág\. \d+\))?(?:,? l\.\d+(?:-\d+)?(?:(?: y |, )l\.\d+(?:-\d+)?)*)?")
def partir_cita(c):
    """cita_plan -> (ref_plan, texto_plan). Se reparte por la referencia inicial; unir_cita lo deshace exactamente."""
    m = REF.match(c or "")
    if not m: return None, (c or None)
    resto = c[m.end():]
    return m.group(0), (resto[2:] if resto.startswith(": ") else resto) or None


def unir_cita(ref, texto):
    if ref is None: return texto or ""
    if texto is None: return ref
    return ref + (texto if texto[:1] in (";", ",", " ", "(") else ": " + texto)


URL = re.compile(r"https?://[^\s)»,;]+[^\s)»,;.]")         # la misma expresión que exportar_web.py
def tipo_url(u):
    """Tipo de una fuente citada solo en una nota (copia de exportar_web._tipo_url)."""
    if "contrataciondelestado.es" in u: return "contratacion"
    if "dival.es" in u or "/bop" in u.lower(): return "bop"
    if "valencia.es" in u: return "nota_prensa" if "/actualidad/" in u else "documento_municipal"
    return "prensa"


# ---------------------------------------------------------------- exportaciones (CSV idénticos a los actuales)
# formato por columna: i entero, f float (repr, como pandas), f6/f1 decimales fijos, b True/False, t texto, fi entero escrito como float
EXPORTS = {
    "data/processed/siniestros_geo.csv": dict(
        sql="SELECT id, fecha, gravedad, tipo, unidades, factores, ubicacion, metodo, lon, lat, dist_ejes_m FROM siniestro ORDER BY rowid",
        fmt=dict(id="i", lon="f6", lat="f6", dist_ejes_m="f1"), fin="\r\n"),
    "data/processed/nombres_lugares.csv": dict(
        sql="SELECT tipo, codvia, x, y, nom, nom_es, alta FROM nombre_lugar ORDER BY id", fmt=dict(codvia="i", x="f", y="f"), fin="\n"),
    "outputs/lugares_nudos.csv": dict(sql=None, fmt=None, fin="\n"),   # columnas de LUGAR_COLS, formato de LUGAR_FMT
    "data/processed/plan_seguimiento.csv": dict(sql=None, fmt=None, fin="\r\n"),
    "docs/cambios.csv": dict(sql="SELECT fecha, tipo, va, es, resumen_va, resumen_es FROM cambio ORDER BY orden", fmt={}, fin="\n"),
}
LUGAR_COLS, LUGAR_FMT = [], {}      # se rellenan al leer el CSV (pandas: int64 -> i, float64 -> f, bool -> b)


def _fmt(v, f):
    if v is None: return ""
    if f == "i": return str(int(v))
    if f == "f": return repr(float(v))
    if f == "fi": return repr(float(v))
    if f == "f6": return f"{v:.6f}"
    if f == "f1": return f"{v:.1f}"
    if f == "b": return "True" if v else "False"
    return str(v)


def exportar(con, nombre):
    """Texto del CSV `nombre` (clave de EXPORTS) regenerado desde la base."""
    e = EXPORTS[nombre]
    if nombre == "outputs/lugares_nudos.csv":
        if not LUGAR_COLS:
            for r in con.execute("SELECT columna, formato FROM _export_formato WHERE csv = ? ORDER BY orden", (nombre,)):
                LUGAR_COLS.append(r[0]); LUGAR_FMT[r[0]] = r[1]
        sql, fmt = f"SELECT {', '.join(LUGAR_COLS)} FROM lugar ORDER BY rank", LUGAR_FMT
    elif nombre == "data/processed/plan_seguimiento.csv":
        return _exportar_plan(con)
    else:
        sql, fmt = e["sql"], e["fmt"]
    cur = con.execute(sql); cols = [d[0] for d in cur.description]
    buf = io.StringIO(); w = csv.writer(buf, lineterminator=e["fin"])
    w.writerow(cols)
    for fila in cur:
        w.writerow([_fmt(v, fmt.get(c, "t")) for c, v in zip(cols, fila)])
    return buf.getvalue()


def _exportar_plan(con):
    cols = ["id", "accion_plan", "actuacion", "ambito", "lugar", "lon", "lat", "meta", "estado", "fecha_estado", "fuente_url",
            "fuente_tipo", "fuente_titulo", "cita_plan", "nota", "comprobado"]
    lonlat = {i: f"{lo},{la}" for i, lo, la in con.execute("SELECT id, lon, lat FROM plan_actuacion_lonlat")}
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\r\n"); w.writerow(cols)
    q = """SELECT a.id, a.accion_plan, a.actuacion, a.ambito, a.lugar, a.meta, a.estado, a.fecha_fuente, f.url, f.tipo, f.titulo,
                  a.ref_plan, a.texto_plan, a.nota, a.fecha_comprobacion
           FROM plan_actuacion a JOIN plan_fuente f ON f.id = a.fuente_id
           LEFT JOIN plan_actuacion_fuente af ON af.actuacion_id = a.id AND af.fuente_id = a.fuente_id AND af.rol = 'principal'
           ORDER BY a.orden"""
    q = q.replace("f.titulo,", "af.titulo_cita,")
    for (i, acc, act, amb, lug, meta, est, ff, url, tipo, tit, ref, txt, nota, comp) in con.execute(q):
        lo, la = lonlat.get(i, ",").split(",")
        w.writerow([i, acc, act, amb, lug or "", lo, la, meta or "", est, ff or "", url, tipo, tit or "", unir_cita(ref, txt),
                    nota or "", comp])
    return buf.getvalue()


# ---------------------------------------------------------------- construcción
def construir(ruta=DB, plan_desde_csv=False):
    import lugares as LG, geocodificar as GC                      # índice nombre -> codvia del geocodificador
    import geopandas as gpd, shapely
    tmp = ruta.with_suffix(".sqlite.tmp"); tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp); con.execute("PRAGMA foreign_keys = ON"); con.executescript(ESQUEMA)
    con.execute("CREATE TABLE _export_formato (csv TEXT, columna TEXT, orden INTEGER, formato TEXT, PRIMARY KEY (csv, columna))")
    avisos, plan_reglas = [], []

    # --- siniestros
    raw = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", dtype=str, keep_default_na=False)
    s, AÑOS = LG.siniestros()
    en = set(s.id.astype(int))
    con.executemany("INSERT INTO siniestro VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(int(r.id), r.fecha, r.gravedad, r.tipo or None, r.unidades or None, r.factores or None, r.ubicacion or None,
                      r.metodo, float(r.lon) if r.lon else None, float(r.lat) if r.lat else None,
                      float(r.dist_ejes_m) if r.dist_ejes_m else None, int(int(r.id) in en)) for r in raw.itertuples()])
    b, _cob = LG.bici_vmp(s)
    con.executemany("INSERT INTO siniestro_bv VALUES (?,?,?,?,?,?)",
                    [(int(r.id), int(r.año), r.v, r.k, r.dir, float(r.w) if np.isfinite(r.w) else None) for r in b.itertuples()])

    # --- callejero
    v = LG._vias()
    crudo = {x["codvia"]: x for x in json.loads((LG.RAW / "vias.json").read_text()) if not x.get("fechabaja")}
    con.executemany("INSERT INTO via VALUES (?,?,?,?,?,?)",
                    [(int(c), r.codtipovia, crudo[c]["nomoficial"], crudo[c].get("traducnooficial"),
                      f"{r.codtipovia} {r.nomoficial}", f"{r.codtipovia} {r.es}") for c, r in v.sort_index().iterrows()])
    vias_ok = set(int(c) for c in v.index)

    # --- calles de cada siniestro, por la dirección escrita
    geomv = GC.geom                              # codvia -> geometría (EPSG:25830), la del geocodificador
    from pyproj import Transformer
    a_utm = Transformer.from_crs(4326, 25830, always_xy=True).transform
    sv, sd = [], []
    for r in raw.itertuples():
        ub = (r.ubicacion or "").strip()
        if " cruce " in ub: partes = [("cruce", p) for p in ub.split(" cruce ", 1)]
        else:
            m = re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$", ub)
            partes = [("portal", m.group(1))] if m else ([("calle", re.sub(r"\s+S/N$", "", ub))] if ub else [])
        res = amb = sinv = 0; vistos = set()
        for rol, p in partes:
            cand = sorted(c for c in GC.codvias(p) if c in vias_ok)
            if len(cand) == 1: elegido, como = cand[0], "unica"
            elif len(cand) > 1 and r.lon:
                pt = shapely.Point(a_utm(float(r.lon), float(r.lat)))
                d = sorted((geomv[c].distance(pt), c) for c in cand if c in geomv)
                elegido, como = (d[0][1], "por_distancia") if d and d[0][0] <= AMBIGUA_MAX_M else (None, None)
            else: elegido, como = None, None
            if elegido is None:
                if cand: amb += 1
                else: sinv += 1
                continue
            res += 1
            if elegido not in vistos:
                vistos.add(elegido); sv.append((int(r.id), int(elegido), rol, como))
        sd.append((int(r.id), len(partes), res, amb, sinv))
    con.executemany("INSERT INTO siniestro_via VALUES (?,?,?,?)", sv)
    con.executemany("INSERT INTO siniestro_direccion VALUES (?,?,?,?,?)", sd)

    # --- nombres y lugares
    nl = pd.read_csv(LG.NOMBRES_CSV, dtype={"codvia": "Int64"})
    con.executemany("INSERT INTO nombre_lugar VALUES (?,?,?,?,?,?,?,?)",
                    [(i + 1, r.tipo, _val(r.codvia), float(r.x), float(r.y), r.nom, r.nom_es, r.alta) for i, r in enumerate(nl.itertuples())])
    nid = {nom: i + 1 for i, nom in enumerate(nl.nom)}
    L = pd.read_csv(ROOT / "outputs/lugares_nudos.csv")
    for j, (c, dt) in enumerate(L.dtypes.items()):
        f = "b" if dt == bool else "i" if str(dt) == "int64" else "f" if str(dt) == "float64" else "t"
        LUGAR_COLS.append(c); LUGAR_FMT[c] = f
    con.executemany("INSERT INTO _export_formato VALUES (?,?,?,?)",
                    [("outputs/lugares_nudos.csv", c, j, LUGAR_FMT[c]) for j, c in enumerate(LUGAR_COLS)])
    faltan = sorted(set(L.nom) - set(nid))
    assert not faltan, f"lugares sin nombre congelado en nombres_lugares.csv: {faltan[:5]}"
    cols = LUGAR_COLS + ["nombre_id"]
    con.executemany(f"INSERT INTO lugar ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                    [[_val(x) for x in r] + [nid[r[LUGAR_COLS.index('nom')]]] for r in L[LUGAR_COLS].itertuples(index=False)])
    res = json.loads((ROOT / "outputs/lugares_nudos_resumen.json").read_text())
    con.executemany("INSERT INTO resumen_lugares VALUES (?,?)", [(k, json.dumps(x, ensure_ascii=False)) for k, x in res.items()])

    # --- asignación de siniestros a lugares (la misma de lugares_nudos.py; se comprueba contra lugar.n)
    g = LG.puntos(b); CJ = LG.callejero(s); U, _ = LG.unidades(CJ); g["uid"] = LG.asignar(g, U)
    n = g.groupby("uid").size()
    assert (n.reindex(L.uid).fillna(0).values == L.n.values).all() and set(n.index) <= set(L.uid), \
        "la asignación no coincide con outputs/lugares_nudos.csv: ejecutar make analisis"
    con.executemany("INSERT INTO siniestro_lugar VALUES (?,?)", [(int(i), int(u)) for i, u in zip(g.id, g.uid)])
    # geometría exacta de los lugares con siniestros (WKB, EPSG:25830): exportar_web.py la dibuja y mide distancias con ella
    con.executemany("INSERT INTO lugar_geom VALUES (?,?)", [(int(u), shapely.to_wkb(U.at[u, "geometry"])) for u in L.uid])

    # --- Plan: la base es su fuente de verdad. Se carga del volcado data/processed/observatorio_plan.sql (en git); solo la
    # primera vez (sin volcado) o a propósito (--plan-desde-csv) se importa de plan_seguimiento.csv. Lo derivado (junto a qué
    # lugar o calle cae cada actuación) se recalcula siempre.
    origen_plan = cargar_plan(con, plan_desde_csv, avisos, plan_reglas)
    plan_geo(con, LG, U, set(L.uid), geomv, vias_ok, v)

    # --- cambios
    with open(ROOT / "docs/cambios.csv", newline="", encoding="utf-8") as f:
        con.executemany("INSERT INTO cambio VALUES (?,?,?,?,?,?,?)", [(i, r["fecha"], r["tipo"], r["va"], r["es"], r.get("resumen_va"), r.get("resumen_es"))
                                                               for i, r in enumerate(csv.DictReader(f))])

    # --- fichas publicadas y slugs congelados
    fichas(con)

    # --- metadatos
    crudo_sin = sorted((ROOT / "data/raw/siniestros").glob("siniestros-de-trafico-*.json"))[-1]
    entradas = [ROOT / "data/processed/siniestros_geo.csv", LG.NOMBRES_CSV, ROOT / "outputs/lugares_nudos.csv",
                ROOT / "outputs/lugares_nudos_resumen.json", ROOT / "docs/cambios.csv", SLUGS]
    meta = {"esquema": ESQUEMA_VERSION, "version_web": con.execute("SELECT MAX(fecha) FROM cambio").fetchone()[0],
            "conjunto_siniestros": crudo_sin.stem, "fecha_descarga": datetime.date.fromtimestamp(crudo_sin.stat().st_mtime).isoformat(),
            "años": ",".join(map(str, AÑOS)), "fuente": FUENTE, "licencia": LICENCIA, "aviso": AVISO, "min_ficha": str(MIN_FICHA),
            "plan_origen": origen_plan, "entradas": json.dumps({str(p.relative_to(ROOT)): _sha(p) for p in entradas}, ensure_ascii=False)}
    con.executemany("INSERT INTO meta VALUES (?,?)", sorted(meta.items()))

    viol = con.execute("PRAGMA foreign_key_check").fetchall()
    assert not viol, f"claves foráneas rotas: {viol[:5]}"
    con.commit(); con.execute("VACUUM"); con.close()
    os.replace(tmp, ruta)
    return avisos, plan_reglas

# ---------------------------------------------------------------- Plan: la base es la fuente de verdad
# Tablas del Plan que no se pueden recalcular (las cura una persona): se guardan en git como volcado SQL en texto,
# data/processed/observatorio_plan.sql (una sentencia INSERT por fila, en orden fijo: los diff se revisan línea a línea).
# plan_seguimiento.csv es su EXPORTACIÓN (la lee el agente verificador-plan y se revisa en git); no se edita a mano: los
# cambios entran con scripts/aplicar_propuestas_plan.py (UPDATE/INSERT en una transacción) o, a propósito, con
# `construir_sqlite.py --plan-desde-csv` (importa el CSV editado; revisar el diff del volcado antes de publicar).
PLAN_SQL = ROOT / "data/processed/observatorio_plan.sql"
PLAN_CSV = ROOT / "data/processed/plan_seguimiento.csv"
PLAN_TABLAS = (("plan_fuente", "id"), ("plan_actuacion", "orden"), ("plan_actuacion_fuente", "actuacion_id, rol, pos, fuente_id"),
               ("plan_actuacion_lonlat", "id"))
COLS_PLAN_CSV = ["id", "accion_plan", "actuacion", "ambito", "lugar", "lon", "lat", "meta", "estado", "fecha_estado", "fuente_url",
                 "fuente_tipo", "fuente_titulo", "cita_plan", "nota", "comprobado"]
CABECERA_SQL = ("-- Seguimiento del Plan Director (El Pla, al dia): tablas cuya fuente de verdad es data/processed/observatorio.sqlite.\n"
                "-- Lo escriben scripts/construir_sqlite.py y scripts/aplicar_propuestas_plan.py: NO se edita a mano.\n"
                "-- Esquema: ESQUEMA de scripts/construir_sqlite.py. Exportación legible: data/processed/plan_seguimiento.csv.\n")


def _sql(x):
    if x is None: return "NULL"
    if isinstance(x, int): return str(x)
    if isinstance(x, float): return repr(x)
    return "'" + str(x).replace("'", "''") + "'"


def volcar_plan(con):
    """Texto del volcado de las tablas del Plan (determinista: mismo contenido, mismo texto)."""
    out = [CABECERA_SQL]
    for tabla, orden in PLAN_TABLAS:
        cols = [c[1] for c in con.execute(f"PRAGMA table_info({tabla})")]
        for fila in con.execute(f"SELECT {', '.join(cols)} FROM {tabla} ORDER BY {orden}"):
            out.append(f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES ({', '.join(map(_sql, fila))});\n")
    return "".join(out)


def fuente_id(con, url, tipo, titulo, origen):
    """id de la fuente con esa URL; la crea si no existe. Si estaba deducida (solo citada en una nota) y ahora se declara
    como fuente de una fila, pasa a declarada con su tipo."""
    r = con.execute("SELECT id, tipo_origen FROM plan_fuente WHERE url = ?", (url,)).fetchone()
    if r is None:
        i = con.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM plan_fuente").fetchone()[0]
        con.execute("INSERT INTO plan_fuente VALUES (?,?,?,?,?)", (i, url, tipo, origen, titulo or None))
        return i
    if origen == "declarado" and r[1] == "deducido_url":
        con.execute("UPDATE plan_fuente SET tipo = ?, tipo_origen = 'declarado', titulo = COALESCE(titulo, ?) WHERE id = ?",
                    (tipo, titulo or None, r[0]))
    return r[0]


def guardar_actuacion(con, r, orden=None, reglas=None):
    """Guarda una actuación dada como fila de plan_seguimiento.csv (dict de textos, columnas COLS_PLAN_CSV): INSERT si es
    nueva (orden = la última + 1 si no se da), UPDATE si ya existe; sus fuentes se reescriben. Las restricciones de la base
    validan (sqlite3.IntegrityError si algo no cumple). Reparte cita_plan en ref_plan / texto_plan (reversible) y las URL de
    la nota en fuentes con rol «nota» (en su orden). Fuente que respalda el estado: la principal, salvo que sea el propio
    Plan; entonces, la única URL de la nota (si hay una sola)."""
    ref, txt = partir_cita(r["cita_plan"])
    assert unir_cita(ref, txt) == r["cita_plan"], f"cita_plan de {r['id']} no se reparte de forma reversible"
    notas = list(dict.fromkeys(URL.findall(r["nota"])))
    fp = fuente_id(con, r["fuente_url"], r["fuente_tipo"], r["fuente_titulo"], "declarado")
    fid_notas = [fuente_id(con, u, tipo_url(u), None, "deducido_url") for u in notas]
    fe = None
    if r["estado"] != "sin_info":
        if r["fuente_tipo"] != "plan": fe = fp
        elif len(fid_notas) == 1:
            fe = fid_notas[0]
            if reglas is not None: reglas.append(f"{r['id']}: fuente del estado = la de la nota ({notas[0]}), asignada por regla")
    clase = "indicador_impacto" if "indicador de impacto" in r["actuacion"] else "medida"
    vals = dict(clase=clase, accion_plan=r["accion_plan"], actuacion=r["actuacion"], ambito=r["ambito"], lugar=r["lugar"] or None,
                lon=float(r["lon"]) if r["lon"] else None, lat=float(r["lat"]) if r["lat"] else None, meta=r["meta"] or None,
                estado=r["estado"], fecha_fuente=r["fecha_estado"] or None, fecha_comprobacion=r["comprobado"], fuente_id=fp,
                fuente_estado_id=fe, ref_plan=ref, texto_plan=txt, nota=r["nota"] or None)
    if con.execute("SELECT 1 FROM plan_actuacion WHERE id = ?", (r["id"],)).fetchone():
        con.execute(f"UPDATE plan_actuacion SET {', '.join(f'{k} = ?' for k in vals)} WHERE id = ?", (*vals.values(), r["id"]))
        con.execute("DELETE FROM plan_actuacion_fuente WHERE actuacion_id = ?", (r["id"],))
        con.execute("DELETE FROM plan_actuacion_lonlat WHERE id = ?", (r["id"],))
    else:
        if orden is None: orden = con.execute("SELECT COALESCE(MAX(orden), -1) + 1 FROM plan_actuacion").fetchone()[0]
        con.execute(f"INSERT INTO plan_actuacion (id, orden, {', '.join(vals)}) VALUES (?, ?, {', '.join('?' * len(vals))})",
                    (r["id"], orden, *vals.values()))
    if r["lon"] or r["lat"]:
        con.execute("INSERT INTO plan_actuacion_lonlat VALUES (?,?,?)", (r["id"], r["lon"], r["lat"]))
    filas = [(fp, "principal", r["fuente_titulo"] or None, None)] + ([(fe, "estado", None, None)] if fe else []) \
        + [(f, "nota", None, k + 1) for k, f in enumerate(fid_notas)]
    con.executemany("INSERT INTO plan_actuacion_fuente VALUES (?,?,?,?,?)", [(r["id"], f, rol, tit, pos) for f, rol, tit, pos in filas])


def borrar_fuentes_huerfanas(con):
    con.execute("""DELETE FROM plan_fuente WHERE id NOT IN (SELECT fuente_id FROM plan_actuacion_fuente)
                   AND id NOT IN (SELECT fuente_id FROM plan_actuacion) AND id NOT IN (SELECT fuente_estado_id FROM plan_actuacion
                   WHERE fuente_estado_id IS NOT NULL)""")


def importar_plan_csv(con, ruta=PLAN_CSV, avisos=None, reglas=None):
    """Importa plan_seguimiento.csv (la primera vez, o a propósito con --plan-desde-csv). Primero las fuentes principales
    en el orden de las filas, después cada fila; una fila que incumple una restricción no entra (aviso)."""
    with open(ruta, newline="", encoding="utf-8") as f:
        P = list(csv.DictReader(f))
    assert P and list(P[0]) == COLS_PLAN_CSV, f"{ruta.name}: columnas distintas de las esperadas"
    for r in P: fuente_id(con, r["fuente_url"], r["fuente_tipo"], r["fuente_titulo"], "declarado")
    for i, r in enumerate(P):
        con.execute("SAVEPOINT fila")
        try:
            guardar_actuacion(con, r, i, reglas)
            con.execute("RELEASE fila")
        except sqlite3.IntegrityError as e:
            con.execute("ROLLBACK TO fila"); con.execute("RELEASE fila")
            if avisos is not None: avisos.append(f"plan {r['id']}: incumple una restricción ({e}); no entra en la base")


def cargar_plan(con, desde_csv=False, avisos=None, reglas=None):
    """Tablas del Plan en una base nueva: del volcado (lo normal) o del CSV (sin volcado, o --plan-desde-csv)."""
    if desde_csv or not PLAN_SQL.exists():
        importar_plan_csv(con, PLAN_CSV, avisos, reglas)
        return "plan_seguimiento.csv"
    con.executescript(PLAN_SQL.read_bytes().decode("utf-8"))
    return PLAN_SQL.name


def plan_geo(con, LG, U, con_lugar, geomv, vias_ok, v):
    """Derivado: actuaciones con coordenadas junto a un lugar (como los siniestros: lugares.asignar, <= R m de su
    envolvente o línea; solo lugares con siniestros) o a <= R m del eje de una calle (nombrada = la actuación la nombra)."""
    import geopandas as gpd
    con.execute("DELETE FROM plan_actuacion_lugar"); con.execute("DELETE FROM plan_actuacion_via")
    P = pd.read_sql_query("SELECT id, lugar, actuacion, lon, lat FROM plan_actuacion WHERE lon IS NOT NULL ORDER BY orden", con)
    if not len(P): return
    pa = gpd.GeoDataFrame(P[["id"]], geometry=gpd.points_from_xy(P.lon, P.lat), crs=4326).to_crs(LG.CRS)
    pa.index = pa.id
    nr = LG.asignar(pa, U).dropna().astype(int)
    for a, u in nr.items():
        d = float(U.at[u, "geometry"].distance(pa.geometry[a]))
        if d <= LG.R and u in con_lugar:
            con.execute("INSERT INTO plan_actuacion_lugar VALUES (?,?,?)", (a, int(u), d))
    ej = gpd.GeoDataFrame({"codvia": list(geomv)}, geometry=list(geomv.values()), crs=LG.CRS)
    ej = ej[ej.codvia.isin(vias_ok)]
    jj = gpd.sjoin(pa[["geometry"]].rename_axis("aid"), gpd.GeoDataFrame(ej[["codvia"]], geometry=ej.buffer(LG.R), crs=LG.CRS), predicate="within")
    sin_tilde = lambda x: "".join(c for c in unicodedata.normalize("NFD", str(x or "").upper()) if unicodedata.category(c) != "Mn")
    texto = {r.id: sin_tilde((r.lugar or "") + " " + r.actuacion) for r in P.itertuples()}
    for a, cv in sorted(set(zip(jj.index, jj.codvia))):
        noms = {sin_tilde(v.at[cv, "nomoficial"]), sin_tilde(v.at[cv, "es"])}
        con.execute("INSERT INTO plan_actuacion_via VALUES (?,?,?,?)",
                    (a, int(cv), round(float(geomv[cv].distance(pa.geometry[a])), 1), int(any(x and x in texto[a] for x in noms))))


def escribir_si_cambia(ruta, texto, fin=None):
    b = texto.encode("utf-8")
    if not ruta.exists() or ruta.read_bytes() != b:
        ruta.write_bytes(b); return True
    return False


def guardar_plan(con):
    """Tras escribir el Plan en la base: su volcado (git) y su exportación CSV. Devuelve las rutas reescritas."""
    out = []
    if escribir_si_cambia(PLAN_SQL, volcar_plan(con)): out.append(PLAN_SQL)
    if escribir_si_cambia(PLAN_CSV, exportar(con, "data/processed/plan_seguimiento.csv")): out.append(PLAN_CSV)
    return out


def _guarda_plan(ruta=DB, desde_csv=False):
    """Antes de reconstruir: no perder cambios del Plan que estén solo en la base o solo en el CSV exportado."""
    if desde_csv or not PLAN_SQL.exists(): return
    vol = PLAN_SQL.read_bytes().decode("utf-8")
    if ruta.exists():
        try:
            c = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True); txt = volcar_plan(c); exp = exportar(c, "data/processed/plan_seguimiento.csv"); c.close()
        except sqlite3.Error:
            txt = None                                      # base de un esquema anterior: no hay nada que proteger
        if txt is not None and txt != vol and ruta.stat().st_mtime > PLAN_SQL.stat().st_mtime:
            sys.exit(f"{ruta.name} tiene cambios del Plan que no están en {PLAN_SQL.name} (¿se editó la base a mano?). "
                     f"Guardarlos con `construir_sqlite.py --volcar` (y revisar el diff) o borrar la base para descartarlos.")
    if PLAN_CSV.exists() and PLAN_CSV.stat().st_mtime > PLAN_SQL.stat().st_mtime:
        c = sqlite3.connect(":memory:"); c.executescript(ESQUEMA); c.executescript(vol)
        if exportar(c, "data/processed/plan_seguimiento.csv") != PLAN_CSV.read_bytes().decode("utf-8"):
            sys.exit(f"{PLAN_CSV.name} es una exportación de la base y se ha editado a mano: no se sobrescribe. Para incorporar "
                     f"los cambios: `construir_sqlite.py --plan-desde-csv` (y revisar el diff de {PLAN_SQL.name}); para descartarlos: "
                     f"`git checkout {PLAN_CSV.relative_to(ROOT)}`. Lo normal es proponerlos y aplicarlos con aplicar_propuestas_plan.py.")
        c.close()


def fichas(con):
    """Fichas que se publican (>= MIN_FICHA siniestros con bici o VMP, o con slug ya publicado) y sus slugs congelados.
    Un slug publicado no cambia ni se reutiliza: data/processed/fichas_slugs.csv (clase, clave, slug, alta), como los
    nombres congelados. Clave de un lugar: tipo@x,y de su nombre congelado (sobrevive a un cambio de nombre a mano);
    de una calle: via@codvia (código municipal)."""
    hoy = datetime.date.today().isoformat()
    f = pd.read_csv(SLUGS, dtype=str) if SLUGS.exists() else pd.DataFrame(columns=["clase", "clave", "slug", "alta"])
    por_clave = dict(zip(f.clave, zip(f.slug, f.alta))); usados = set(zip(f.clase, f.slug))
    cand = []
    for uid, tipo, x, y, nom, n in con.execute(
            "SELECT l.uid, l.tipo, nl.x, nl.y, l.nom, l.n FROM lugar l JOIN nombre_lugar nl ON nl.id = l.nombre_id ORDER BY l.rank"):
        cand.append(("lloc", f"{tipo}@{x!r},{y!r}", uid, None, re.sub(r"\s*\((\d+|[NSEO]{1,2})\)$", r" \1", nom), n))
    for cv, nom, n in con.execute("SELECT v.codvia, v.nom, c.n FROM v_calle_bv c JOIN via v USING (codvia) ORDER BY c.n DESC, v.codvia"):
        cand.append(("carrer", f"via@{cv}", None, cv, nom, n))
    nuevos, filas = [], []
    for clase, clave, uid, cv, nom, n in cand:
        if clave in por_clave: slug, alta = por_clave[clave]
        elif n >= MIN_FICHA:
            base = slugify(nom) or clase; slug, k = base, 1
            while (clase, slug) in usados: k += 1; slug = f"{base}-{k}"
            usados.add((clase, slug)); alta = hoy; nuevos.append({"clase": clase, "clave": clave, "slug": slug, "alta": alta})
        else: continue
        filas.append((slug, clase, clave, uid, cv, n, alta))
    con.executemany("INSERT INTO ficha VALUES (?,?,?,?,?,?,?)", filas)
    if nuevos:
        pd.concat([f, pd.DataFrame(nuevos)], ignore_index=True).to_csv(SLUGS, index=False)
    huerfanos = set(por_clave) - {c[1] for c in cand}
    print(f"fichas: {sum(r[1] == 'lloc' for r in filas)} de lugar y {sum(r[1] == 'carrer' for r in filas)} de calle "
          f"(>= {MIN_FICHA} siniestros o slug ya publicado); {len(nuevos)} slugs nuevos en {SLUGS.name}"
          + (f"; {len(huerfanos)} slugs congelados sin lugar o calle (no se publican): {sorted(huerfanos)[:5]}" if huerfanos else ""))


# Entradas de la base (las escriben el análisis o una persona y la base las carga): si su exportación no es idéntica, la base
# está desfasada (make sqlite). Exportaciones de la base (la base es la fuente): si no son idénticas, alguien las editó a mano.
ENTRADAS = ("data/processed/siniestros_geo.csv", "data/processed/nombres_lugares.csv", "outputs/lugares_nudos.csv", "docs/cambios.csv")
DE_LA_BASE = ("data/processed/plan_seguimiento.csv", "data/processed/observatorio_plan.sql")


def comprobar(ruta=DB):
    """Cada CSV de EXPORTS regenerado desde la base es idéntico al del disco, y el volcado del Plan es el de la base.
    Devuelve [(fichero, ok, detalle)]."""
    con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True); out = []
    for nombre in list(EXPORTS) + ["data/processed/observatorio_plan.sql"]:
        actual = (ROOT / nombre).read_bytes().decode("utf-8") if (ROOT / nombre).exists() else ""
        nuevo = volcar_plan(con) if nombre.endswith(".sql") else exportar(con, nombre)
        if nuevo == actual: out.append((nombre, True, ""))
        elif nombre in ENTRADAS and not nombre.endswith(".sql") and \
                list(csv.reader(io.StringIO(actual))) == list(csv.reader(io.StringIO(nuevo))):
            # mismo contenido, otro formato (comillas que no hacen falta, fin de línea): p. ej. una fila de cambios.csv escrita a mano
            out.append((nombre, True, "mismo contenido; solo cambia el formato (comillas o fin de línea)"))
        else:
            a, b = actual.splitlines(), nuevo.splitlines()
            i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            out.append((nombre, False, f"primera diferencia en la línea {i + 1}: {a[i][:80] if i < len(a) else '∅'!r} / {b[i][:80] if i < len(b) else '∅'!r}"))
    con.close()
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--comprobar", action="store_true", help="comprobar que la base exporta los CSV idénticos")
    ap.add_argument("--exportar", metavar="DIR", help="escribir los CSV exportados en DIR (con sus rutas relativas)")
    ap.add_argument("--plan-desde-csv", action="store_true",
                    help="importar el Plan de plan_seguimiento.csv (editado a mano) en vez del volcado; revisar el diff del volcado")
    ap.add_argument("--volcar", action="store_true", help="solo reescribir el volcado y el CSV del Plan desde la base actual")
    a = ap.parse_args()
    if a.exportar:
        con = sqlite3.connect(DB)
        for nombre in EXPORTS:
            p = Path(a.exportar) / nombre; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(exportar(con, nombre).encode("utf-8")); print("escrito", p)
        sys.exit(0)
    if a.volcar:
        con = sqlite3.connect(DB); print("reescritos:", [str(x.relative_to(ROOT)) for x in guardar_plan(con)] or "nada (sin cambios)"); sys.exit(0)
    _guarda_plan(DB, a.plan_desde_csv)
    avisos, reglas = construir(plan_desde_csv=a.plan_desde_csv)
    con = sqlite3.connect(DB)
    escritos = guardar_plan(con)
    cnt = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for (t,) in
           con.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE '\\_%' ESCAPE '\\' ORDER BY name")}
    d = con.execute("""SELECT SUM(partes), SUM(resueltas), SUM(ambiguas), SUM(sin_via), SUM(resueltas = partes), COUNT(*)
                       FROM siniestro_direccion JOIN siniestro_bv USING (siniestro_id)""").fetchone()
    origen = con.execute("SELECT valor FROM meta WHERE clave = 'plan_origen'").fetchone()[0]
    con.close()
    print(f"{DB.relative_to(ROOT)} ({DB.stat().st_size / 1e6:.1f} MB):", cnt)
    print(f"plan: cargado de {origen}; " + (f"reescritos {[str(x.relative_to(ROOT)) for x in escritos]}" if escritos else "volcado y CSV sin cambios"))
    print(f"calles (bici o VMP): {d[5]} siniestros, {d[0]} calles nombradas: {d[1]} asignadas, {d[2]} ambiguas, {d[3]} sin vía en el "
          f"callejero; {d[4]} siniestros con todas sus calles asignadas ({d[4] / d[5]:.1%})")
    for x in reglas: print("plan (regla):", x)
    for x in avisos: print("AVISO", x)
    if a.comprobar:
        r = comprobar()
        for nombre, ok, det in r: print(("ok   " if ok else "DIFF ") + nombre, det)
        sys.exit(0 if all(ok for _, ok, _ in r) else 1)
