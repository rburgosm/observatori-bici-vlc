"""Exporta los datos reales compactos de la web (prototipo): web/proto/datos/observatori.js, relato.js, metode.js y pla.js.

Entradas: la base data/processed/observatorio.sqlite (scripts/construir_sqlite.py, leída con scripts/bd.py): siniestros
(con bici o VMP: vehículo, con quién, tipo de dirección y peso), lugares (nudos de cruce y tramos de calle de
lugares_nudos.py, con su geometría exacta y la asignación de cada siniestro), su resumen y el seguimiento del Plan.
Además, el callejero y las capas de data/raw/siniestros/, outputs/cribado_eb_vmp_o_bici.csv y outputs/cribado_eb_coef.json
(de scripts/cribado_eb.py), pdsv_*.csv, incidencias_datos.csv y colaboran.csv. Ya no recalcula los lugares (antes lo hacía
con scripts/lugares.py y comprobaba que coincidían): los toma de la base, que lo comprobó al construirse.
Uso: .venv/bin/python -I scripts/exportar_web.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw/siniestros"
OUT = ROOT / "web/proto/datos/observatori.js"; OUT.parent.mkdir(parents=True, exist_ok=True); CRS = "EPSG:25830"

def gj(gdf, props, tol, nd=5):
    g = gdf.to_crs(CRS).copy(); g["geometry"] = g.geometry.simplify(tol)
    g = g[~g.geometry.is_empty].to_crs(4326)
    d = json.loads(g[props + ["geometry"]].to_json(drop_id=True))
    def r(c): return [r(x) for x in c] if isinstance(c[0], list) else [round(c[0], nd), round(c[1], nd)]
    for f in d["features"]: f["geometry"]["coordinates"] = r(f["geometry"]["coordinates"])
    return d

ejes = gpd.read_file(RAW / "ejes.geojson")
ejes = ejes[ejes.geometry.notna()]
ejes["m"] = ejes.tipcalle.isin(["AVINGUDA", "PASSEIG", "GRAN VIA", "PONT", "CAMI", "CARRETERA", "BULEVARD"]).astype(int)
calles = gj(ejes, ["m"], 4)
cb = gpd.read_file(RAW / "carriles_bici.geojson"); cb = cb[cb.geometry.notna() & cb.estado.isin(["1", "4", "6", "7"])]
ciclo = gj(cb.assign(t=cb.estado), ["t"], 3)

sys.path.insert(0, str(Path(__file__).resolve().parent))      # -I no añade la carpeta del script
import lugares as LG                                            # constantes, pista y geometría (scripts/lugares.py)
import bd as BD                                                 # lectura de la base (scripts/bd.py)
_con = BD.conectar()
# años completos (con los 12 meses), deducidos de los datos: el fichero 2022-2025 trae 17 siniestros del 1/1/2026
s, AÑOS = BD.siniestros(_con)
s["vmp"] = s.unidades.str.contains("VMP", na=False); s["bici"] = s.unidades.str.contains("BICICLETA", na=False)
_todo = s.copy()                                                  # todos los siniestros de la ciudad (series de control)
# bici o VMP: v (a=ambos, p=patinete, b=bici), dir (cruce/portal), w (peso por año × tipo de dirección), k (con quién)
s, COBT = BD.bici_vmp(_con, _todo)
serie = (s.groupby(["año", "v"]).size().unstack(fill_value=0)).reset_index().to_dict("records")

# ---------- meta de la acción 3.2.2 del Plan: un único año base para herramienta, relato y método ----------
# AÑO_BASE: último año antes del periodo del Plan (2026-2030), que el Plan ya analiza (decisión del 03/11/2026).
# AÑO_BASE_ALT: la que usa el Plan para los heridos graves, solo por la calidad del dato de gravedad; queda a la vista.
AÑO_BASE, AÑO_BASE_ALT, AÑO_META, AÑO_PLAN = 2025, 2024, 2030, 2026     # AÑO_PLAN: primer año del Plan
assert AÑO_BASE in AÑOS and AÑO_BASE_ALT in AÑOS, "el año base tiene que estar en los datos"
_TOT = {a: int((s["año"] == a).sum()) for a in AÑOS}
_ULT = AÑOS[-1]
_r4 = lambda x: round(float(x), 4)
from meta import escenario as _escenario, NIVEL as _NIVEL      # senda, banda de Poisson y juicio anual (scripts/meta.py)
def escenario(b): return _escenario(_TOT, [b], AÑO_META)
# comprobación: base = media de los tres años antes del Plan (2025 es el máximo de la serie: regresión a la media)
AÑOS_MEDIA = [a for a in range(AÑO_BASE - 2, AÑO_BASE + 1) if a in AÑOS]
# series de control (todos los siniestros de la ciudad, sin duplicados): total, con y sin heridos, bici o VMP y resto
_todo["año"] = _todo.fecha.dt.year; _todo["bv"] = _todo.unidades.str.contains("VMP|BICICLETA", na=False)
_todo["her"] = _todo.gravedad.notna() & (_todo.gravedad != "SIN HERIDOS")
_cnt = lambda m: [int((m & (_todo["año"] == a)).sum()) for a in AÑOS]
_ALL = pd.Series(True, index=_todo.index)
CONTROL = {"años": AÑOS, "ciudad": _cnt(_ALL), "bv": [_TOT[a] for a in AÑOS],
           "bv_her": _cnt(_todo.bv & _todo.her), "resto_her": _cnt(~_todo.bv & _todo.her),
           "bv_sin": _cnt(_todo.bv & ~_todo.her), "resto_sin": _cnt(~_todo.bv & ~_todo.her)}
CONTROL["cuota"] = [_r4(x / y) for x, y in zip(CONTROL["bv"], CONTROL["ciudad"])]
assert CONTROL["bv"] == _cnt(_todo.bv), "la serie de bici o VMP no cuadra con el total de la ciudad"
# recuento por vehículo (como las tablas del Plan): VMP + bici, los choques bici–patinete cuentan dos veces
_veh = int((s["año"] == AÑO_BASE).sum() + ((s["año"] == AÑO_BASE) & s.vmp & s.bici).sum())
META = {"año_base": AÑO_BASE, "año_alt": AÑO_BASE_ALT, "año_meta": AÑO_META, "año_plan": AÑO_PLAN, "ult": _ULT,
        "desde": _ULT + 1, "pendiente": _ULT + 1 if _ULT < AÑO_META else None,
        "esc": [escenario(AÑO_BASE), escenario(AÑO_BASE_ALT)], "nivel": _NIVEL,
        "media": _escenario(_TOT, AÑOS_MEDIA, AÑO_META),                 # comprobación con la media de los años antes del Plan
        "vehiculo": {"base": _veh, "meta": int(_veh / 2 + 0.5), "dobles": int(((s["año"] == AÑO_BASE) & s.vmp & s.bici).sum())},
        "control": CONTROL, "siasv": "2024-07",       # SIASV de la Policía Local, creado en julio de 2024 (pdsv.txt l. 2407)
        # tendencia previa al Plan: del primer año de la serie al año base, y el año anterior a la base
        "primero": AÑOS[0], "tot_primero": _TOT[AÑOS[0]], "previa": _r4(_TOT[AÑO_BASE] / _TOT[AÑOS[0]] - 1),
        "previa_ant": _r4(_TOT[AÑO_BASE] / _TOT[AÑO_BASE - 1] - 1) if AÑO_BASE - 1 in _TOT else None,
        "max": AÑO_BASE == max(_TOT, key=_TOT.get), "año_max": max(_TOT, key=_TOT.get),
        # contexto externo identificado (docs/contexto/cronologia.md): primeras señales, pendientes del dato abierto
        "ctx2026": {"vmp_menos": 50, "fecha": "10/06/2026",
                    "url": "https://www.elperiodic.com/valencia/plan-vector-policia-local-para-reducir-accidentes-mortales-comienza-frutos-solo-muerto-frente-siete-2025_1079063"}}
print("meta:", {k: META[k] for k in ("año_base", "previa", "previa_ant", "max", "vehiculo")}, [{k: e[k] for k in ("etq", "base", "meta", "senda_anual", "necesaria", "concl", "banda")} for e in META["esc"] + [META["media"]]])
print("control:", CONTROL)
geo = {"cruce": "c", "portal": "p", "portal_cercano": "q"}
g = s[s.lon.notna()]
grav = {"SIN HERIDOS": 0, "CON HERIDOS LEVES": 1, "CON HERIDOS BAJA GRAVEDAD": 2, "CON HERIDOS GRAVES": 3, "CON FALLECIDOS": 4}
contrario = LG.contrario             # con quién: m vehículo, w peatón, d entre bicis o patinetes, s solo (ya en s.k)
s["prio"] = s.factores.str.contains("PRIORIDAD", na=False)
s["dist"] = s.factores.str.contains("DISTRA", na=False)
s["via"] = s.factores.str.contains("ESTADO O CONDICI", na=False)
s["vel"] = s.factores.str.contains("VELOCIDAD", na=False)
s["h"] = s.fecha.dt.hour
FR = [0, 7, 10, 14, 17, 21, 24]
s["fr"] = pd.cut(s.h, FR, right=False, labels=False)
s["lab"] = s.fecha.dt.day_of_week < 5
# tipo de accidente: el campo solo es fiable desde 2025 (vacío en el 65 %, 69 % y 34 % de 2022 a 2024); se muestra el del último año, no una suma
TIPO_AÑO = _ULT
def perfil(d):
    n = len(d)
    tu = d[d["año"] == TIPO_AÑO].tipo.value_counts()
    df = d[d["año"] == TIPO_AÑO]       # factores: solo el último año, como el tipo (07/11/2026: sin ningún factor el 35 % en 2022, el 12 % en 2025)
    return {"k": {c: int((d.k == c).sum()) for c in "mwds"},
            "f": {c: int(df[c].sum()) for c in ("prio", "dist", "via", "vel")}, "nf": int(len(df)),

            "fr": d.fr.value_counts().reindex(range(6), fill_value=0).astype(int).tolist(),
            "lab": round(float(d.lab.mean()), 2),
            "tu": [[k, int(v)] for k, v in tu.head(3).items()], "nu": int(tu.sum()),
            "gr": int(d.gravedad.isin(["CON HERIDOS GRAVES"]).sum()), "fa": int((d.gravedad == "CON FALLECIDOS").sum()),
            "pm": int((d.prio & (d.k == "m")).sum()),      # no respetar la prioridad, entre los choques con vehículo
            "vy": [[int(((d["año"] == y) & (d.v == "b")).sum()), int(((d["año"] == y) & (d.v != "b")).sum())] for y in AÑOS],
            "vy3": [[int(((d["año"] == y) & (d.v == c)).sum()) for c in "bpa"] for y in AÑOS]}
ciudad = perfil(s)
g = s[s.lon.notna()]
pts = [[round(r.lon, 5), round(r.lat, 5), int(r.año), r.v, grav.get(r.gravedad, -1),
        (r.tipo if r.año == TIPO_AÑO else ""), r.ubicacion, geo.get(r.metodo, "o"), r.fecha.strftime("%d/%m/%Y %H:%M"), r.unidades, r.factores if isinstance(r.factores, str) else ""] for r in g.itertuples()]
cob = {"total": int(len(s)), "geo": int(len(g))}

# ---------- lugares con más siniestros: nudos de cruce y tramos de calle (scripts/lugares.py) ----------
# El mismo cálculo que scripts/lugares_nudos.py (que mide estabilidad, persistencia y pista): aquí se comprueba que
# el top 30 coincide con su salida. Peso: 1 / cobertura de su año y su tipo de dirección (cruce o portal).
gg = LG.puntos(s)
# lugares de la base: geometría exacta (la de lugares.unidades) de los que tienen siniestros y lugar de cada siniestro
U = BD.geom_lugares(_con)
gg["uid"] = gg.id.map(BD.uid_siniestro(_con))
assert gg.uid.notna().all(), "siniestros situados sin lugar en la base: make sqlite"
TT, _ = LG.tabla(gg, gg.uid, U)              # recuentos y pesos exactos (lugares_nudos.csv los guarda redondeados)
LUG = BD.lugares(_con)
RES = BD.resumen(_con)
K30 = RES["k"]
TOP = list(TT.nsmallest(K30, "rank").index)
assert TOP == RES["top"] and (TT.loc[TOP, "n"].values == LUG.loc[TOP, "n"].values).all(), \
    "los lugares no coinciden con la base: ejecutar make sqlite (o make analisis)"
t = TT.loc[TOP]
reg = gpd.read_file(RAW / "reguladores_semaforos.geojson").to_crs(CRS)
# la capa 182 son reguladores (armarios), no semáforos: se completa con los semáforos de OpenStreetMap (incompletos)
_osm = [e for e in json.loads((RAW / "osm_semaforos.json").read_text())["elements"]
        if e.get("type") == "node" and "traffic_signals" in (e.get("tags", {}).get("highway"), e.get("tags", {}).get("crossing"))]
osm = gpd.GeoSeries(gpd.points_from_xy([e["lon"] for e in _osm], [e["lat"] for e in _osm]), crs=4326).to_crs(CRS)
cbx = gpd.read_file(RAW / "carriles_bici.geojson").to_crs(CRS); cbx = cbx[cbx.geometry.notna() & cbx.estado.isin(["1","4","6","7"])]
# lo que se dibuja: la zona del nudo (envolvente + R) o la línea del tramo, simplificada a 2 m
_dib = gpd.GeoSeries(LG.geometria(U.loc[TOP]).simplify(2), crs=CRS).to_crs(4326)
_cen = gpd.GeoSeries(U.loc[TOP].geometry.representative_point(), crs=CRS)
def _gjson(geom, nd=6):
    d = json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"]
    def r(c): return [r(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], nd), round(c[1], nd)]
    d["coordinates"] = r(d["coordinates"]); return d
negros = []
for c in TOP:
    r = t.loc[c]; sub = gg[gg.uid == c]; ce = _cen[c]; p = gpd.GeoSeries([ce], crs=CRS).to_crs(4326).iloc[0]
    n = {"lon": round(p.x, 5), "lat": round(p.y, 5), "nom": LUG.at[c, "nom"], "nom_es": LUG.at[c, "nom_es"], "tipo": U.at[c, "tipo"],
         "A": int(r.nA), "B": int(r.nB), "rank": int(r["rank"]),
         "por": sub.groupby("año").size().reindex(AÑOS, fill_value=0).tolist(), "pat": int((sub.v != "b").sum()), "n": int(r.n),
         "mix": [int((sub.v == "b").sum()), int((sub.v == "p").sum()), int((sub.v == "a").sum())],
         # barras por año ponderadas (como el orden): siniestros con solo bici, solo patinete y los dos
         "vy3w": [[round(float(sub[(sub["año"] == y) & (sub.v == x)].w.sum()), 1) for x in "bpa"] for y in AÑOS],
         "geo": _gjson(_dib[c])}
    n.update(perfil(sub))
    n["ubis"] = [[k, int(v)] for k, v in sub.ubicacion.value_counts().head(3).items()]
    # distancia (m) desde el lugar (envolvente del nudo o línea del tramo) al regulador municipal y al semáforo de OSM más cercanos
    gu = U.at[c, "geometry"]
    n["sem"] = {"r": int(round(reg.distance(gu).min())), "o": int(round(osm.distance(gu).min()))}
    n["cb"] = int(round(cbx.distance(gu).min()))
    n["cruce"] = round(float((sub.metodo == "cruce").mean()), 2)
    negros.append(n)
# nombre del callejero (scripts/lugares.py, nombres); «dir», la dirección más repetida, es la misma que aquí
assert all(gg[gg.uid == c].ubicacion.mode().iat[0] == LUG.at[c, "dir"] for c in TOP)
# periodos de formato del portal (cambios de formato de UBICACION en oct. de 2022 y en jul. de 2024, con SIASV): solo para describir la cobertura
CORTES = ["2022-10-01", "2024-07-01"]
s["per"] = np.select([s.fecha < CORTES[0], s.fecha < CORTES[1]], ["P1", "P2"], "P3")
COB = s.groupby("per").lon.apply(lambda x: x.notna().mean())
# ---------- lo que dice el Plan de cada lugar (data/processed/pdsv_lugares.csv) ----------
# claves: todas deben aparecer (sin acentos, mayúsculas) en alguna ubicación del lugar; «|» = alternativas
import re, unicodedata
def norm(x): return unicodedata.normalize("NFD", str(x)).encode("ascii", "ignore").decode().upper()
CLAVES = {
    "Paseo de la Alameda - Plaza de Zaragoza": ["ALAMEDA", "ZARAGOZA"],
    "Ausiàs March - Fernando Abril Martorell": ["AUSIAS MARCH", "ABRIL MARTORELL"],
    "Av. dels Tarongers (Naranjos) - Luis Peixó": ["NARANJOS", "PEIXO"],
    "Fernando Abril Martorell - Ctra. de Malilla": ["ABRIL MARTORELL", "MALILLA"],
    "Av. de Blasco Ibáñez - Av. Cardenal Benlloch": ["BLASCO", "BENLLOCH"],
    "Av. Cardenal Benlloch - Av. del Puerto": ["BENLLOCH", "PUERTO"],
    "Plaza de Zaragoza": ["PL ZARAGOZA"],
    "Gran Vía Fernando el Católico - C/ Àngel Guimerà": ["FERNANDO EL CATOLICO", "GUIMERA"],
    "Blasco Ibáñez - Cardenal Benlloch - Clariano": ["BLASCO", "BENLLOCH"],
    "Paseo de la Ciutadella": ["CIUDADELA|CIUTADELLA"],
    "Av. del General Avilés": ["GENERAL AVILES"],
    "C/ Enginyer Fausto Elío": ["FAUSTO ELIO"],
    "C/ Xàtiva - C/ Jesús": ["XATIVA|JATIVA", "JESUS"],
    "Av. de Blasco Ibáñez": ["BLASCO IBANEZ"],
    "Av. del Puerto": ["AV PUERTO"],
    "Paseo de la Alameda": ["PG ALAMEDA"],
    "Jardín del Turia": ["JARDIN DEL TURIA|JARDI DEL TURIA"],
    "C/ Colón": ["C/ COLON"],
    "C/ San Vicente Mártir": ["SAN VICENTE MARTIR"],
    "Peset Aleixandre - Camí de Montcada": ["PESET ALEIXANDRE", "MONCADA|MONTCADA"],
    "Giorgeta - Jesús": ["GIORGETA", "C/ JESUS"],
    "Tres Cruces - Campos Crespo": ["TRES CRUCES", "CAMPOS CRESPO"],
    "C/ Xàtiva": ["C/ XATIVA|C/ JATIVA"],
    # un punto concreto (a la altura de C/ Castellón), nunca «GERMANIAS» sola: emparejaría GV Marqués del Turia
    # × Regne de València y otros cruces de la Gran Vía
    "Gran Vía Germanías a la altura de C/ Castellón": ["GERMANIAS", "CASTELLON"],
    "Lonja de la Seda y Plaza del Mercado": ["PL MERCADO"],
    "Av. del General Avilés - C/ Luis Buñuel (Campanar)": ["GENERAL AVILES", "LUIS BUNUEL"],
}
# filas de pdsv_lugares.csv que no se emparejan con ninguna ubicación, con el motivo (decisión del 04/11/2026).
# Toda fila del CSV tiene que estar en CLAVES o aquí; si no, el script se para (antes se saltaba sin aviso).
SIN_CLAVE = {   # motivo en castellano y valenciano (se publica en la página de método)
    "Anillo Ciclista (Ronda Interior)": {
        "es": "es una infraestructura (el itinerario ciclista con más uso), no un ranking de siniestros ni una actuación en ese lugar",
        "va": "és una infraestructura (l'itinerari ciclista amb més ús), no un rànquing de sinistres ni una actuació en eixe lloc"},
    "Av. de Peris y Valero": {
        "es": "solo aparece en una foto de ejemplo de un paso de peatones accesible; una foto no es una cita",
        "va": "només apareix en una foto d'exemple d'un pas de vianants accessible; una foto no és una cita"},
    "Ronda Norte": {
        "es": "son varias avenidas que en el portal tienen su propio nombre; el Plan no dice en qué tramo",
        "va": "són diverses avingudes que en el portal tenen el seu propi nom; el Pla no diu en quin tram"},
    "Ciutat Vella (Área de Prioridad Residencial)": {
        "es": "es un distrito entero (zona de prioridad residencial y 30 km/h), no un lugar ni una calle",
        "va": "és un districte sencer (zona de prioritat residencial i 30 km/h), no un lloc ni un carrer"},
    "Estación Joaquín Sorolla (Kiss and Go)": {
        "es": "es la estación; su nombre no aparece en las direcciones del portal",
        "va": "és l'estació; el seu nom no apareix en les adreces del portal"},
}
lug = pd.read_csv(ROOT / "data/processed/pdsv_lugares.csv")
_sin = sorted(set(lug.nombre) - set(CLAVES) - set(SIN_CLAVE))
if _sin:
    sys.exit(f"pdsv_lugares.csv: lugares del Plan sin decidir (añadirlos a CLAVES o a SIN_CLAVE con motivo): {_sin}")
assert not set(CLAVES) & set(SIN_CLAVE), "un lugar no puede estar en CLAVES y en SIN_CLAVE"
def plan_de(textos, zona=False):
    """Citas del Plan para un lugar. kind (diag/act) viene explícito en pdsv_lugares.csv; niv dice si la cita es
    del propio lugar (cruce citado o la zona misma) o solo de su calle (rankings de calles, radares en una calle)."""
    tx = [norm(x) for x in textos]
    out = []
    for r in lug.itertuples():
        if r.nombre in SIN_CLAVE: continue     # decidido y con motivo (SIN_CLAVE)
        cl = CLAVES[r.nombre]
        if any(all(any(alt in s for alt in c.split("|")) for c in cl) for s in tx):
            cifra = f" ({r.cifra_plan}, {r.periodo})" if isinstance(r.cifra_plan, str) else (f" ({r.periodo})" if isinstance(r.periodo, str) and r.periodo != "—" else "")
            txt = str(r.accion_o_contexto)
            diag = r.kind == "diag"
            m = re.search(r"n\.º (\d+)", txt)
            act = ("audit_reord" if ("uditor" in txt and "eordenaci" in txt) else "auditoria" if "uditor" in txt else "reordenacion" if "eordenaci" in txt else "radar" if "adar" in txt
                   else "estudio" if "estudio" in txt else "otra")
            niv = "lugar" if (zona or str(r.tipo_lugar).startswith("cruce")) else "calle"
            out.append({"lug": r.nombre, "kind": r.kind, "niv": niv, "col": r.colectivo, "tl": r.tipo_lugar,
                        "cifra": r.cifra_plan if isinstance(r.cifra_plan, str) else "", "per": r.periodo if isinstance(r.periodo, str) else "",
                        "rank": int(m.group(1)) if m else None, "act": None if diag else act, "t": f"{txt}{cifra}",
                        "ref": str(r.ref).split(";")[0]})
    return out
def cita_calle(p):
    """Cita de su calle que cuenta para el anillo (decisión del usuario, 03/11, opción B): el Plan nombra la calle
    del lugar por cualquier motivo (ranking de calles con más siniestros de VMP, bici o peatones, o una actuación en la
    calle, como un radar). La ficha explica el motivo de cada cita."""
    return p["niv"] == "calle"
def pl_anillo(n):
    """Anillo del Plan (regla común de la herramienta, el relato y el método), tres niveles:
    1 cita ESTE lugar (cruce o plaza, o la zona misma; con o sin actuación) · 2 solo cita su calle (cita_calle)
    · 0 no lo menciona de ninguna de esas formas."""
    if any(p["niv"] == "lugar" for p in n["plan"]): return 1
    return 2 if any(cita_calle(p) for p in n["plan"]) else 0
for n, c in zip(negros, TOP):   # con las direcciones de sus siniestros, no con el nombre del callejero (pendiente 87)
    n["plan"] = plan_de([u for u, _ in n["ubis"]] + [LUG.at[c, "dir"]]); n["pl"] = pl_anillo(n)
_n30 = [n for n in negros if not n.get("zona")]
# recuentos del anillo en los lugares con más siniestros (sin zonas): los mismos en las tres páginas
PL3 = {"n": len(_n30), "lugar": sum(n["pl"] == 1 for n in _n30), "calle": sum(n["pl"] == 2 for n in _n30), "no": sum(n["pl"] == 0 for n in _n30),
       "lugar_act": sum(n["pl"] == 1 and any(p["niv"] == "lugar" and p["kind"] == "act" for p in n["plan"]) for n in _n30),
       # el Plan solo publica los primeros de cada ranking (n.º 1 a 3): no aparecer no prueba que esté fuera de su radar
       "top": int(lug.accion_o_contexto.str.extract(r"n\.º (\d+)")[0].dropna().astype(int).max())}
assert PL3["lugar"] + PL3["calle"] + PL3["no"] == PL3["n"]
print("anillo del Plan:", PL3)
print("plan: negros con alguna cita", sum(bool(n["plan"]) for n in negros), "de", len(negros), "; anillo (0 no lo menciona, 1 cita el lugar, 2 solo su calle):",
      pd.Series([n["pl"] for n in negros]).value_counts().sort_index().to_dict())
# ---------- Jardín del Turia como zona ----------
# El Plan lo pone como la «calle» n.º 1 en siniestros con bici, pero sus siniestros vienen sin punto
# («JARDÍN DEL TURIA», «S/N», «JARDÍN DEL TURIA CRUCE LLOC PUENTE…»). Se añade como zona (contorno aproximado: la red
# ciclista del jardín, estado 4 de la capa 189, con un margen de 70 m) con todos sus siniestros.
# Solo el jardín (frase completa): nunca GV Marqués del Turia, C/ Camp de Túria ni C/ Asturias.
TURIA_RE = r"\bJARDIN? DEL TURIA\b|\bCAUCE DEL (?:RIO )?TURIA\b|\bLLIT DEL (?:RIU )?TURIA\b|\bANTIGUO CAUCE\b"
mt = s.ubicacion.map(norm).str.contains(TURIA_RE, regex=True, na=False)
st = s[mt]
_u = st.ubicacion.map(norm)
assert not (_u.str.contains(r"MARQUES DEL TURIA|CAMP DE TURIA|ASTURIAS", regex=True)
            & ~_u.str.contains(r"\bJARDIN? DEL TURIA\b", regex=True)).any(), "Turia: entra otra calle"
assert st.index.is_unique
tz = cbx[cbx.estado == "4"].buffer(70).union_all().simplify(15)
tz = max(getattr(tz, "geoms", [tz]), key=lambda g: g.area)
tz4 = gpd.GeoSeries([tz], crs=CRS).to_crs(4326).iloc[0]
rp = gpd.GeoSeries([tz.representative_point()], crs=CRS).to_crs(4326).iloc[0]
# siniestros del jardín con punto dentro de la zona (para el minimapa), agrupados por punto como en la web
_sg = st[st.lon.notna()]
_sg = _sg[gpd.GeoSeries(gpd.points_from_xy(_sg.lon, _sg.lat), crs=4326, index=_sg.index).to_crs(CRS).within(tz)]
_mm = (_sg.assign(lo=_sg.lon.round(5), la=_sg.lat.round(5)).groupby(["lo", "la"]).v
       .agg(lambda x: [int((x == c).sum()) for c in "bpa"]))
# los del jardín que también estén en uno de los 30 lugares (nudo o tramo) se contarían dos veces
_dup = int(gg.ubicacion.map(norm).str.contains(TURIA_RE, regex=True).pipe(lambda m: gg[m].uid.isin(TOP)).sum())
tur = {"lon": round(rp.x, 5), "lat": round(rp.y, 5), "nom": "JARDÍ DEL TÚRIA", "nom_es": "JARDÍN DEL TURIA", "n": int(len(st)),   # nombre en va y es (pendiente 87)
       "pat": int((st.v != "b").sum()), "mix": [int((st.v == "b").sum()), int((st.v == "p").sum()), int((st.v == "a").sum())], "A": int(st["año"].isin(RES["per"]["A"]).sum()), "B": int(st["año"].isin(RES["per"]["B"]).sum()),
       "por": st.groupby("año").size().reindex(AÑOS, fill_value=0).astype(int).tolist(),
       "ubis": [[k, int(v)] for k, v in st.ubicacion.value_counts().head(3).items()], "sem": None, "cb": 0, "cruce": 0.0,
       "tipo": "zona", "zona": [[round(x, 5), round(y, 5)] for x, y in tz4.exterior.coords],
       "geo": int(st.lon.notna().sum()), "dentro": int(len(_sg)),
       "mm": [[lo, la, *m] for (lo, la), m in _mm.items()]}
tur.update(perfil(st))
tur["plan"] = plan_de(["JARDÍN DEL TURIA"], zona=True); tur["pl"] = pl_anillo(tur)
negros.append(tur)
# ---------- filtros de la web (año, vehículo y gravedad, en el navegador; pendiente 37 y filtros del mapa) ----------
# Para rehacer en el navegador el recuento y el perfil de cada lugar con un filtro, cada siniestro situado (pts) lleva su
# lugar (índice en negros de 0 a K30-1, o -1) y si es del Jardín del Turia (0 no, 1 sí, 2 sí y con punto dentro de la zona,
# los del minimapa; puede ser de un lugar y del Turia a la vez, como en _dup).
# Los siniestros SIN punto van aparte («sp»), sin dirección ni fecha exacta, solo con lo que pide el perfil: año,
# vehículo, gravedad, con quién (k), franja horaria (fr), laborable, factores (bits: 1 prioridad, 2 distracción,
# 4 estado de la vía, 8 velocidad), tipo (solo el último año) y si es del Turia. Así la «mitjana de la ciutat» y el Turia
# (que incluye siniestros sin punto) también se pueden filtrar. Ningún campo nuevo de las personas.
_TOPI = {c: i for i, c in enumerate(TOP)}
_lug = gg.uid.map(_TOPI).fillna(-1).astype(int)
assert list(g.index) == list(gg.index) and len(pts) == len(g)
_dentro = set(_sg.index)                 # del Turia con punto dentro de la zona (los del minimapa): 2
for p, i in zip(pts, g.index):
    p += [int(_lug[i]), int(mt[i]) + int(i in _dentro)]
_bits = lambda d: (d.prio.astype(int) + 2 * d.dist.astype(int) + 4 * d.via.astype(int) + 8 * d["vel"].astype(int))
_sp = s[s.lon.isna()].assign(bits=lambda d: _bits(d))
sp = [[int(r.año), r.v, grav.get(r.gravedad, -1), r.k, int(r.fr), int(r.lab), int(r.bits),
       (r.tipo if r.año == TIPO_AÑO and isinstance(r.tipo, str) else ""), int(mt[r.Index])] for r in _sp.itertuples()]
assert len(pts) + len(sp) == len(s)
# comprobación: con los campos exportados se rehacen el número de siniestros y «con quién» de cada lugar y de la ciudad
_kp = [LG.contrario(p[9]) for p in pts]
for i, n in enumerate(negros):
    ks = [k for p, k in zip(pts, _kp) if (p[12] if n.get("zona") else p[11] == i)] + [r[3] for r in sp if n.get("zona") and r[8]]
    assert len(ks) == n["n"] and {c: ks.count(c) for c in "mwds"} == n["k"], ("filtros: no cuadra", n["nom"])
assert {c: _kp.count(c) + sum(r[3] == c for r in sp) for c in "mwds"} == ciudad["k"], "filtros: no cuadra la ciudad"
assert sum(p[12] == 2 for p in pts) == tur["dentro"] == sum(m[2] + m[3] + m[4] for m in tur["mm"]), "filtros: Turia dentro"
# ---------- pista (con quién) de todos los lugares del mapa: referencia de su tipo sin el propio lugar ----------
# nudos con nudos y tramos con tramos (siniestros con punto); el Jardín del Turia con el resto de la ciudad (con o sin punto).
# Holm sobre todas las pruebas del mapa (4 por lugar; los de menos de LG.MIN_PISTA casos cuentan como p = 1).
_tipo_g = gg.uid.map(U.tipo)
_REF = {k: gg[_tipo_g == k].k.value_counts().reindex(LG.CATS, fill_value=0) for k in ("nudo", "tramo")}
_REF["zona"] = s[~mt].k.value_counts().reindex(LG.CATS, fill_value=0) + st.k.value_counts().reindex(LG.CATS, fill_value=0)
_pis_in = {i: (n["k"], {c: int(_REF[n["tipo"]][c] - n["k"][c]) for c in LG.CATS}) for i, n in enumerate(negros)}
PISTA, PT = LG.pistas(_pis_in)
for i, n in enumerate(negros): n["pista"] = PISTA[i]
PIS = {"familia": int(len(PT)), "probadas": int(PT.probada.sum()), "lugares_prob": int(PT[PT.probada].lugar.nunique()),
       "holm": int(PT.holm.sum()), "min": LG.MIN_PISTA,
       "ref": {k: {c: round(float(v / _REF[k].sum()), 3) for c, v in _REF[k].items()} for k in ("nudo", "tramo")},
       "con": [[negros[r.lugar]["nom"], r.c, r.x, r.n, round(float(r.p0), 3)] for r in PT[PT.holm].itertuples()]}
print("pista:", PIS)
print("turia:", tur["n"], "siniestros,", tur["geo"], "geolocalizados,", tur["dentro"], "dentro de la zona;", _dup,
      "también en los 30 lugares; pista", tur["pista"], "; plan", [(p["kind"], p["niv"]) for p in tur["plan"]])
print("ubicaciones del Turia:", st.ubicacion.map(norm).str.replace(r" \d+$| CRUCE .*", "", regex=True).value_counts().to_dict())
eb = pd.read_csv(ROOT / "outputs/cribado_eb_vmp_o_bici.csv")
# años con exposición y contadores de cada punto de conteo: los da cribado_eb.py (n_años, n_cont, idpm), que agrupa los
# contadores a <50 m y los del mismo enlace de una vía (revisión A6); aquí solo se leen
def _imd_anual(path, patron):
    partes = []
    for h in pd.read_excel(path, engine="odf", sheet_name=None, header=None).values():
        es_cod = h.apply(lambda c: c.astype(str).str.strip().str.fullmatch(patron).mean()); c_cod = es_cod.idxmax()
        filas = h[h[c_cod].astype(str).str.strip().str.fullmatch(patron)]
        num = filas.drop(columns=c_cod).apply(lambda c: pd.to_numeric(c, errors="coerce").notna().mean())
        partes.append(pd.DataFrame({"cod": filas[c_cod].astype(str).str.strip(),
                                    "imd": pd.to_numeric(filas[num[num > .5].index.max()], errors="coerce")}))
    d = pd.concat(partes); return d[d.imd > 0].groupby("cod").imd.agg(["mean", "size"])
_ab = [a for a in AÑOS if (ROOT / f"data/raw/intensidades/carril_bici_{a}.ods").exists()]
_bici = []
for a in _ab:
    _t = _imd_anual(ROOT / f"data/raw/intensidades/carril_bici_{a}.ods", r"P\d+"); _t = _t[_t["size"] >= 6]
    _bici.append(pd.DataFrame({"idpm": _t.index.str[1:].astype(int), "año": a, "imd": _t["mean"].values}))
_bici = pd.concat(_bici)
_esp = gpd.read_file(RAW / "espiras_bici.geojson").to_crs(CRS); _esp = _esp[_esp.geometry.notna()].drop_duplicates("idpm")
_cont = _esp[_esp.idpm.isin(_bici.idpm)][["idpm", "geometry"]].reset_index(drop=True)
_sit = eb.set_index("sitio").idpm.astype(str).str.split().explode().astype(int)
_cont = _cont.merge(pd.DataFrame({"idpm": _sit.values, "sitio": _sit.index}), on="idpm")
N_AÑOS = eb.set_index("sitio").n_años.astype(int); N_CONT = eb.set_index("sitio").n_cont.astype(int)
_chk = _cont.groupby("sitio").size().reindex(N_CONT.index) - N_CONT
assert (_chk == 0).all(), "los contadores no coinciden con cribado_eb.py (rehacer make analisis)"
# zona de los puntos con varios contadores: unión de los círculos de 100 m de sus contadores (la del análisis); el mapa la
# dibuja en lugar del círculo alrededor del centro (el Assut de l'Or: los dos extremos del puente)
_zu = _cont.assign(geometry=_cont.buffer(100)).dissolve("sitio").geometry.simplify(2).to_crs(4326)
_anillo = lambda g: [[[round(x, 5), round(y, 5)] for x, y in g.exterior.coords]]
ZONA_USO = {k: {"type": "Polygon", "coordinates": _anillo(g)} if g.geom_type == "Polygon" else
            {"type": "MultiPolygon", "coordinates": [_anillo(x) for x in g.geoms]}       # círculos separados (Assut)
            for k, g in _zu.items() if N_CONT[k] > 1}


def _nom_uso(r):
    """Nombre del punto de conteo: el del primer contador; si el punto junta varios, sin el sentido («(sentido Menorca)»)."""
    n = str(r.contadores).split(" | ")[0]
    return re.sub(r"\s*\(sentido.*$", "", n, flags=re.I) if N_CONT[r.sitio] > 1 else n     # (el texto viene cortado a 45)
# lv: nivel (2 claramente por encima de la media de los puntos con un tráfico parecido, con 75, 100 y 150 m; 1 quizá; 0 como
# la media), decidido en cribado_eb.py; pr: probabilidad de estar por encima con 75, 100 y 150 m (en %, sin decimales);
# b y v: observados y esperados de bici y de VMP, cada uno con su modelo; sv: el exceso es solo de patinete (revisión A1)
_RAD = json.loads((ROOT / "outputs/cribado_eb_coef.json").read_text())["criterio"]["radios"]
uso = [{"lon": round(r.lon, 5), "lat": round(r.lat, 5), "nom": _nom_uso(r), "N": int(r.N), "mu": round(r.mu, 1),
        "lv": int(r.nivel), "pr": [int(round(100 * getattr(r, f"p_exceso_{x}"))) for x in _RAD],
        "b": [int(r.N_bici), round(r.mu_bici, 1)], "v": [int(r.N_vmp), round(r.mu_vmp, 1)], "sv": int(r.solo_vmp),
        "na": int(N_AÑOS[r.sitio]), "nc": int(N_CONT[r.sitio]),
        "imd": int(round(r.expo / N_AÑOS[r.sitio])), "plan": plan_de([r.contadores])}
       | ({"geo": ZONA_USO[r.sitio]} if r.sitio in ZONA_USO else {})
       for r in eb.itertuples() if pd.notna(r.lon)]
print("puntos de conteo:", len(uso), "con", sum(u["nc"] for u in uso), "contadores; años con datos:",
      pd.Series([u["na"] for u in uso]).value_counts().sort_index().to_dict())

# cifras de los textos de la web (nada escrito a mano en la plantilla)
# persistencia fuera de muestra del top (outputs/lugares_nudos_resumen.json): ordenar con un periodo y medir en el otro
_pk = {(p["corte"], p["k"]): p for p in RES["pers"]}
PERS = {"ab": _pk[("AB", K30)], "j7": _pk[("jul24", K30)], "top_ab": RES["top_ab"], "nsim": RES["nsim"], "bloque": RES["bloque"],
        "todas": RES["pers"], "per": RES["per"]}       # per: años de A y de B y mes del segundo corte (lugares_nudos.py)
# peso de cada siniestro: 1 / cobertura de su año y tipo de dirección (cruce o portal)
COBD = {str(a): {d: round(float(COBT[(a, d)]), 3) for d in ("cruce", "portal")} for a in AÑOS}
kpi = {"pers": PERS, "cob": {k: round(float(v), 3) for k, v in COB.items()}, "cobd": COBD,
       "anys": AÑOS, "tipo_any": TIPO_AÑO, "n_neg": sum(not n.get("zona") for n in negros), "pista": PIS,
       "per": {p: [int(x.min()), int(x.max())] for p, x in s.groupby("per")["año"]},          # años que abarca cada periodo de formato
       "cob_any": {str(a): round(float(v), 4) for a, v in s.groupby("año").lon.apply(lambda x: x.notna().mean()).items()},
       "cortes": [c[:7] for c in CORTES],                                                     # fin de P1 y de P2 (año-mes)
       "n_contadores": sum(u["nc"] for u in uso),                                                   # contadores de los puntos de conteo
       # de los choques bici–patinete, los que no tienen nada más (ni coche ni peatón)
       "amb_solo": round(float(s[s.v == "a"].unidades.map(lambda u: set(x.strip() for x in u.split(",")) <= {"BICICLETA", "VMP"}).mean()), 3),
       "meta": META, "pl3": PL3,
       # siniestros (sin peso) de los lugares del mapa, {a0}-{a1}, y todos los situados en el mapa (tarjeta de la portada)
       "conc": {"n": int(t.n.sum()), "geo": int(len(gg))}}
assert kpi["conc"]["geo"] == cob["geo"] and kpi["conc"]["n"] == sum(n["n"] for n in negros if not n.get("zona"))
data = {"kpi": kpi, "ciudad": ciudad, "serie": serie, "pts": pts, "sp": sp, "cob": cob, "negros": negros, "uso": uso, "calles": calles, "ciclo": ciclo}
OUT.write_text("window.OBS=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
print(f"{OUT.stat().st_size/1e6:.2f} MB; puntos {len(pts)}; negros {len(negros)}; uso {len(uso)}; serie {serie}; cob {cob}")
print("calles", len(calles["features"]), "ciclo", len(ciclo["features"]))
print("pistas:", {x["nom"][:30]: x["pista"] for x in negros if x["pista"]}); print(negros[:1]); print(sorted(uso, key=lambda u: (-u["lv"], -u["N"]))[:2])

# ---------- datos del relato ----------
coef = json.loads((ROOT / "outputs/cribado_eb_coef.json").read_text())
# años: los completos de los datos (AÑOS); el informe saca de aquí todos sus años, ejes y textos
tot = [int((s["año"] == a).sum()) for a in AÑOS]
rel = {"anys": AÑOS, "tot": tot, "meta": META, "pl3": PL3,
       "vmp": [int(((s["año"] == a) & s.vmp).sum()) for a in AÑOS],
       "bici": [int(((s["año"] == a) & s.bici).sum()) for a in AÑOS],
       # años del cribado por uso (los que tienen IMD de carril bici, misma regla que cribado_eb.py) y periodos de la
       # persistencia (los de lugares_nudos.py: ordenar con los primeros años, medir con los últimos, la misma duración)
       "anys_eb": _ab, "per": {"A": RES["per"]["A"], "B": RES["per"]["B"]},
       # puntos de conteo: lv nivel, sv exceso solo de patinete, b / v observados y esperados de bici y de VMP
       # id: código del primer contador (P + idpm), el del enlace directo a la ficha del observatorio (#punt=…)
       "sc": [{"id": (re.match(r"P\d+", str(r.contadores)) or [""])[0],
               "n": str(r.contadores).split(" | ")[0].split(" ", 1)[1].replace("CARRIL BICI", "").replace("Carril bici", "").strip(" ,-–"),
               "N": int(r.N), "mu": round(r.mu, 1), "lv": int(r.nivel), "sv": int(r.solo_vmp),
               "b": [int(r.N_bici), round(r.mu_bici, 1)], "v": [int(r.N_vmp), round(r.mu_vmp, 1)], "rb": int(r.rank_bruto)}
              for r in eb.itertuples()]}


_NUDOS = LUG[LUG.tipo == "nudo"]
_NUDOS = gpd.GeoDataFrame(_NUDOS, geometry=gpd.points_from_xy(_NUDOS.lon, _NUDOS.lat), crs=4326).to_crs(25830)
_nz = lambda s: unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()


def _esquina(n, lon, lat):
    """«…, esquina X»: la descripción del contador viene cortada a 45 caracteres («ESQUINA GUILLEM D»). Se completa X con
    la calle de un nudo a ≤ 200 m cuyo nombre empiece por ese fragmento; si no hay una sola, se quita la esquina."""
    m = re.search(r",\s*esquina\s+(.*)$", n, flags=re.I)
    if not m: return n
    frag = _nz(m.group(1)).strip()
    p = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(25830).iloc[0]
    hits = {part for s in _NUDOS[_NUDOS.distance(p) <= 200].nom_es for part in s.split(" cruce ")
            if _nz(re.sub(r"^(C/|AV|PL|PG|GV|CTRA|LLOC)\s+", "", part)).startswith(frag)}
    calle = re.sub(r"^(C/|AV|PL|PG|GV|CTRA|LLOC)\s+", "", hits.pop()) if len(hits) == 1 else None
    return n[:m.start()] + (f" – {calle}" if calle else "")


def _nom_corto(n, lon=None, lat=None):
    """Nombre corto de un punto de conteo para el texto: sin número de portal ni sentido, con la esquina completada
    (si se da la posición), y en minúsculas con mayúscula inicial."""
    if lon is not None: n = _esquina(n, lon, lat)
    n = re.sub(r"\s*\(.*$|,\s*esquina.*$", "", n, flags=re.I); n = re.sub(r",?\s*(nº|n\.º)?\s*\d+.*$", "", n).strip(" ,-–.")
    n = re.sub(r"\s+[-–]\s+", " – ", n.title())
    return re.sub(r"\b(De|Del|La|Las|Los|El|Y|I|D’|L’|D'|L')(?=\s|[A-ZÀ-Ú])", lambda m: m.group(1).lower(), n)


# ejemplos del paso «trafico3» del informe, elegidos por regla (no a mano): x, el punto con más siniestros de los que
# están como la media; t, el «claramente» solo de patinete con más siniestros; b, el «claramente» que no es solo de
# patinete con menos siniestros (el más bajo en una lista por número de siniestros)
_c2 = eb[eb.nivel == 2]
_dx = {"x": eb[eb.nivel == 0].sort_values(["N", "mu"], ascending=False).index[0],
       "t": _c2[_c2.solo_vmp].sort_values(["N", "mu"], ascending=False).index[0],
       "b": _c2[~_c2.solo_vmp].sort_values(["rank_bruto", "N"], ascending=[False, True]).index[0]}
rel["dest"] = {k: {"i": int(eb.index.get_loc(i)), "nom": _nom_corto(rel["sc"][eb.index.get_loc(i)]["n"], eb.at[i, "lon"], eb.at[i, "lat"])} for k, i in _dx.items()}
(OUT.parent / "relato.js").write_text("window.REL=" + json.dumps(rel, ensure_ascii=False, separators=(",", ":")) + ";")
print("relato:", {k: rel[k] for k in ("tot", "vmp", "bici", "dest")})

# ---------- datos del relato: escenario único (informe.plantilla.html) ----------
from scipy.stats import nbinom
from shapely.geometry import box as _box
rel["serie"] = serie                                    # por año: b solo bici, a las dos, p solo patinete
# siniestros con heridos graves (todos los siniestros, no solo bici/VMP): cambia el criterio en 2023
todos = BD.todos(_con)[["id", "fecha", "gravedad"]]
todos = todos[todos.fecha.dt.year.isin(AÑOS)]; todos = todos.loc[~todos.drop(columns="id").duplicated()]
rel["grav"] = [int(((todos.fecha.dt.year == a) & (todos.gravedad == "CON HERIDOS GRAVES")).sum()) for a in AÑOS]
# los 30 lugares con más siniestros (mismo cálculo que el observatorio) y el rango que les da el Plan, si los cita como cruce
# anillo del Plan, tres niveles (pl_anillo): 1 cita ESTE lugar · 2 solo cita su calle (ranking de calles) · 0 no lo menciona
def _pl(n):
    return pl_anillo(n)          # regla común, definida junto a plan_de (la usa también la herramienta)
def _rank_plan(n):
    rs = [p["rank"] for p in n["plan"] if p["kind"] == "diag" and p["tl"] == "cruce" and p["rank"]]
    return min(rs) if rs else None
rel["pers"] = PERS; rel["estab"] = RES["estab"]       # persistencia y estabilidad de los lugares (lugares_nudos.py)
rel["negros"] = [{"lon": n["lon"], "lat": n["lat"], "n": n["n"], "nom": n["nom"], "nom_es": n["nom_es"], "tipo": n["tipo"], "k": n["k"],
                  "prio": n["f"]["prio"], "vy": n["vy"], "pr": _rank_plan(n),
                  # como el anillo de la herramienta: 0 el Plan no lo menciona, 1 prevé o ha hecho alguna actuación, 2 lo señala sin actuación
                  "pl": _pl(n)} for n in negros if not n.get("zona")]   # sin zonas (Turia): solo nudos y tramos
# siniestros del primer lugar, uno a uno: posición, con quién (m/w/d/s), prioridad, bici o patinete
# mezcla de cada lugar (para el quesito): siniestros con solo bici, solo patinete y los dos (columna v: b, p, a)
for d, c in zip(rel["negros"], TOP):
    sub = gg[gg.uid == c]; d["v3"] = [int((sub.v == x).sum()) for x in "bpa"]
    assert sum(d["v3"]) == d["n"], (d["nom"], d["v3"], d["n"])
sub0 = gg[gg.uid == TOP[0]]
rel["ala"] = [[round(r.lon, 6), round(r.lat, 6), r.k, int(r.prio), r.v, int(r.año)] for r in sub0.itertuples()]
rel["ala_geo"] = negros[0]["geo"]          # zona del nudo del primer lugar (envolvente + R), para el zoom del informe
# todo el Paseo de la Alameda (dirección con «PG ALAMEDA», cualquier tramo o cruce), siniestros con bici o VMP por año
rel["ala_paseo"] = [int(((s["año"] == a) & s.ubicacion.astype(str).str.contains(r"\bPG ALAMEDA\b")).sum()) for a in AÑOS]
# contadores con posición, y franja de la variación entre puntos con un tráfico parecido: predictiva del propio modelo
# (binomial negativa con el α del conjunto, revisión B1), 95 %. Con θ fijo por punto, el total de los años es NB(1/α, Σμ)
for d, r in zip(rel["sc"], eb.itertuples()):
    d["lon"], d["lat"] = round(r.lon, 5), round(r.lat, 5)
_al = coef["vmp_o_bici"]["alpha"]
def _nb(q, m): return int(nbinom.ppf(q, 1 / _al, 1 / (1 + _al * m)))
mus = np.arange(0, np.ceil(eb.mu.max()) + 1.01, 0.5)
rel["banda"] = [[float(m), _nb(0.025, m), _nb(0.975, m)] for m in mus]
BANDA = {"encima": int(sum(r.N > _nb(0.975, r.mu) for r in eb.itertuples())),
         "debajo": int(sum(r.N < _nb(0.025, r.mu) for r in eb.itertuples()))}
print("franja NB: fuera por encima", BANDA["encima"], "y por debajo", BANDA["debajo"], "de", len(eb))
# fondo del mapa: vías principales simplificadas (toda la ciudad) y todas las calles alrededor del primer lugar (para el zoom)
def _lineas(gdf, tol, nd):
    gs = gdf.to_crs(CRS).geometry.simplify(tol); gs = gs[~gs.is_empty].to_crs(4326)
    out = []
    for geom in gs:
        for ln in (geom.geoms if geom.geom_type.startswith("Multi") else [geom]):
            cs = [[round(x, nd), round(y, nd)] for x, y in ln.coords]
            if len(cs) >= 2: out.append(cs)
    return out
princ = ejes[ejes.tipcalle.isin(["AVINGUDA", "PASSEIG", "GRAN VIA", "PONT", "BULEVARD", "RONDA"])]
c0 = gpd.GeoSeries([gpd.points_from_xy([negros[0]["lon"]], [negros[0]["lat"]])[0]], crs=4326).to_crs(CRS).iloc[0]
cerca = ejes.to_crs(CRS); cerca = cerca[cerca.intersects(_box(c0.x - 1000, c0.y - 750, c0.x + 1000, c0.y + 750))]
cerca = cerca.assign(geometry=cerca.geometry.intersection(_box(c0.x - 1000, c0.y - 750, c0.x + 1000, c0.y + 750)))
# núcleo urbano: envolvente convexa de los siniestros geolocalizados de bici/VMP sin el 1 % más alejado del centro, con un buffer;
# el buffer crece hasta que caben todos los lugares y contadores del relato
_pg = gpd.GeoSeries(gpd.points_from_xy(g.lon, g.lat), crs=4326).to_crs(CRS)
_c = gpd.points_from_xy([_pg.x.median()], [_pg.y.median()], crs=CRS)[0]
_d = _pg.distance(_c); _hull = _pg[_d <= _d.quantile(.99)].union_all().convex_hull
_marcas = gpd.GeoSeries(gpd.points_from_xy([n["lon"] for n in rel["negros"]] + [d["lon"] for d in rel["sc"]],
                                           [n["lat"] for n in rel["negros"]] + [d["lat"] for d in rel["sc"]]), crs=4326).to_crs(CRS)
_buf = 400
while not _marcas.within(_hull.buffer(_buf)).all(): _buf += 200
nucleo = gpd.GeoSeries([_hull.buffer(_buf)], crs=CRS)
_rec = lambda gdf: gpd.clip(gdf.to_crs(CRS), nucleo)
rel["mapa"] = {"princ": _lineas(_rec(princ), 15, 4), "cerca": _lineas(cerca.to_crs(4326), 1, 6),
               "ciclo": _lineas(_rec(cb), 20, 4)}
_bb = nucleo.to_crs(4326).total_bounds
_tur = [n for n in negros if n.get("zona")]
rel["turia_pr"] = min([p["rank"] for t_ in _tur for p in t_["plan"] if p["kind"] == "diag" and p["col"] == "bici" and p["rank"]], default=None)
rel["n_contadores"] = int(sum(len(str(r.contadores).split(" | ")) for r in eb.itertuples()))   # 145 puntos de conteo, con varios contadores en algunos
rel["cob"] = round(cob["geo"] / cob["total"], 3)
# paso «falta3»: uso del carril bici. Panel fijo: contadores con IMD (>= 6 meses con dato) en todos los años; suma de IMD; primer año = 100
_pan = _bici.pivot_table(index="idpm", columns="año", values="imd").dropna()
rel["uso_idx"] = {"años": [int(a) for a in _pan.columns], "idx": [round(float(v)) for v in _pan.sum() / _pan.sum().iloc[0] * 100], "n": int(len(_pan))}
# proporción de patinetes en conteos manuales a pie de carril bici (fuente externa, complemento; docs/contexto/uso_fuentes.md §2.2)
rel["uso_manual"] = [
    {"año": 2019, "pat": .25, "f": "Agència de la Bicicleta (ETRA i Esther Anaya), octubre de 2019, 2 punts"},
    {"año": 2020, "pat": .28, "f": "Agència de la Bicicleta, octubre-novembre de 2020, 5 punts"},
    {"año": 2021, "pat": .31, "f": "Càtedra d'Economia Col·laborativa (UV), 2021"}]
print("panel de uso:", rel["uso_idx"])      # parte de los siniestros con bici o patinete que se pueden situar en el mapa
rel["nucleo_bb"] = [[round(_bb[0], 5), round(_bb[1], 5)], [round(_bb[2], 5), round(_bb[3], 5)]]
print("núcleo: buffer", _buf, "m; caja", rel["nucleo_bb"], "; marcas fuera", int((~_marcas.within(nucleo.iloc[0])).sum()))
(OUT.parent / "relato.js").write_text("window.REL=" + json.dumps(rel, ensure_ascii=False, separators=(",", ":")) + ";")
print(f"relato.js: {(OUT.parent / 'relato.js').stat().st_size/1e3:.0f} kB; grav {rel['grav']}; ala {len(rel['ala'])}; "
      f"ala_paseo {rel['ala_paseo']}; princ {len(rel['mapa']['princ'])} cerca {len(rel['mapa']['cerca'])} ciclo {len(rel['mapa']['ciclo'])}; banda {len(rel['banda'])}")

# ---------- datos del método (web/proto/metode.plantilla.html → datos/metode.js) ----------
# Todas las cifras de la página «Mètode / Método». Reutiliza lo calculado arriba (s, gg, COB, TT, TOP, RES, negros, eb, _bici…).
import platform
_raw = BD.todos(_con)
_ra = _raw[_raw.fecha.dt.year.isin(AÑOS)]
_rd = _ra.loc[~_ra.drop(columns="id").duplicated()].copy()
_rd["per"] = np.select([_rd.fecha < CORTES[0], _rd.fecha < CORTES[1]], ["P1", "P2"], "P3")
_pc = lambda x: round(float(x), 4)
_per = ["P1", "P2", "P3"]
# meta 3.2.2: la de META (arriba), con la base principal AÑO_BASE y la alternativa AÑO_BASE_ALT
_tot, _ult, _esc, _e0 = _TOT, _ULT, META["esc"], META["esc"][0]
# uso frente a siniestros: contadores con IMD los cuatro años (suma de IMD; 2022 = 100)
# hasta el último año con IMD, que puede ser anterior al último de siniestros (scripts/meta.py, uso)
_w = _bici.pivot(index="idpm", columns="año", values="imd").dropna()
from meta import uso as _uso_panel
USO = _uso_panel(_w, _tot, AÑO_BASE, AÑO_META)
# lugares: sensibilidad de la selección
# sensibilidad de la selección: ordenar solo con 2022-23 (ponderado) o sin peso
_selA = set(TT.sort_values(["WA", "nA"], ascending=False).index[:K30])
_selU = set(TT.sort_values(["n", "W"], ascending=False).index[:K30])
_en30 = gg[gg.uid.isin(TOP)]
_tur = [n for n in negros if n.get("zona")][0]
# Plan: lugares e indicadores transcritos
_ind = pd.read_csv(ROOT / "data/processed/pdsv_indicadores.csv")
_ind = _ind[_ind.eje != "Objetivo global (4.4)"]
_neg30 = [n for n in negros if not n.get("zona")]
# gravedad de los siniestros con bici o patinete por año
_gr = {a: int(((s["año"] == a) & (s.gravedad == "CON HERIDOS GRAVES")).sum()) for a in AÑOS}
_bg = {a: int(((s["año"] == a) & (s.gravedad == "CON HERIDOS BAJA GRAVEDAD")).sum()) for a in AÑOS}
_req = {l.split("==")[0]: l.split("==")[1] for l in (ROOT / "requirements.txt").read_text().split() if "==" in l}
_c0 = coef["vmp_o_bici"]
met = {
    "anys": AÑOS, "cortes": [c[:7] for c in CORTES],
    "per": {p: [x.min().strftime("%Y-%m"), x.max().strftime("%Y-%m")] for p, x in s.groupby("per").fecha},
    # datos
    "filas": int(len(_raw)), "fuera": int((~_raw.fecha.dt.year.isin(AÑOS)).sum()), "fuera_anys": sorted(int(a) for a in _raw.fecha.dt.year.unique() if a not in AÑOS),
    "dup": int(len(_ra) - len(_rd)), "todos": {str(a): int((_rd.fecha.dt.year == a).sum()) for a in AÑOS},
    "unidades_rotas": int((_rd.unidades.astype(str).str.strip() == "[").sum()),
    "bv": {str(a): _tot[a] for a in AÑOS}, "serie": serie,
    "vmp": {str(a): int(((s["año"] == a) & s.vmp).sum()) for a in AÑOS}, "bici": {str(a): int(((s["año"] == a) & s.bici).sum()) for a in AÑOS},
    "amb_solo": kpi["amb_solo"],
    "cob_bv": {p: _pc(COB[p]) for p in _per}, "cob_todos": {p: _pc(_rd[_rd.per == p].lon.notna().mean()) for p in _per},
    "cob_bv_tot": _pc(s.lon.notna().mean()), "n_geo": int(s.lon.notna().sum()), "n_bv": int(len(s)),
    "solo_calle": {p: _pc((s[s.per == p].metodo == "solo_calle").mean()) for p in _per},
    "cruce_fallo": {p: _pc((s[s.per == p].metodo == "cruce_fallo").mean()) for p in _per},
    "metodo": {m: _pc(v) for m, v in g.metodo.value_counts(normalize=True).items()},
    "n_ejes": int(len(ejes)), "km_ciclo": round(float(cbx.length.sum() / 1000), 1), "n_reg": int(len(reg)), "n_osm": int(len(osm)),
    "n_espiras": int(len(_esp)), "n_cont": int(len(_cont)), "n_sitios": int(len(eb)),
    "imd_veh": sorted((ROOT / "data/raw/intensidades").glob("imds_vehiculos_*.ods"))[-1].stem.split("_")[-1],
    # meta
    "meta": META, "esc": _esc, "concl": _e0["concl"], "ult": _ult, "ala_paseo": rel["ala_paseo"],
    # uso
    **USO,
    "anys_eb": _ab,                                                     # años con IMD (puntos de conteo del cribado)
    # lugares
    "n_neg": len(_neg30), "pers": PERS, "pista": PIS, "cobd": COBD,
    "pesos": {a: {d: round(1 / v, 2) for d, v in x.items()} for a, x in COBD.items()},
    # unidades, estabilidad y parámetros (scripts/lugares_nudos.py → outputs/lugares_nudos_resumen.json)
    "lug": {k: RES[k] for k in ("R", "F", "pieza", "paralela", "plaza_max", "n_nudos", "n_tramos", "n_unid", "en_nudo", "n_geo",
                                "n_semillas", "n_nodos", "n_plazas", "tramo_max", "estab", "nombres")} | {"plaza_votos": LG.PLAZA_VOTOS, "congela_tol": LG.CONGELA_TOL},
    "tipos30": {k: sum(n["tipo"] == k for n in _neg30) for k in ("nudo", "tramo")},
    "cambia_A": len(set(TOP) - _selA), "igual_sinpeso": len(set(TOP) & _selU), "dup_turia": _dup,
    "cruce_30": _pc((_en30.metodo == "cruce").mean()), "cruce_ciudad": _pc((g.metodo == "cruce").mean()),
    "tur": {"n": _tur["n"], "geo": _tur["geo"], "dentro": _tur["dentro"], "pr": rel["turia_pr"], "buffer": 70},
    # uso / Bayes empírico
    "eb": {"sitios": int(len(eb)), "cont": kpi["n_contadores"], "radio": 100, "agrupa": coef["agrupa"]["agrupa"], "enlace": coef["agrupa"],
           "asig": _c0["asignados"], "geo": _c0["geolocalizados"], "elast": _c0["elasticidad_bici"], "alpha": _c0["alpha"],
           "alta": int((eb.nivel == 2).sum()), "quiza": int((eb.nivel == 1).sum()),
           # criterio y desglose (cribado_eb.py; revisión metodológica A1-A4 y B1)
           "crit": coef["criterio"], "cruces": _c0["cruces"], "sim": _c0["sim"], "desglose": _c0["desglose"],
           "cruces_coef": _c0["cruces_coef"], "alpha_bici": coef["bici"]["alpha"], "alpha_vmp": coef["vmp"]["alpha"],
           "reglas": _c0["reglas"], "bici_p95": coef["bici"]["reglas"]["p1_100"], "vmp_p95": coef["vmp"]["reglas"]["p1_100"],
           "bici_claro": int((eb.nivel_bici == 2).sum()), "vmp_claro": int((eb.nivel_vmp == 2).sum()),
           "jaccard": {k: v["jaccard_p95"] for k, v in _c0["radio"].items()}, "banda": BANDA,
           "claro": [[_nom_corto(d["n"], r.lon, r.lat), str(r.contadores).split()[0], d["N"], d["mu"], d["sv"]]
                     for d, r in zip(rel["sc"], eb.itertuples()) if d["lv"] == 2],
           "radio_solape": {k: v["solape_top10"] for k, v in _c0["radio"].items()},
           "na4": int((N_AÑOS == len(_ab)).sum()),      # puntos con IMD todos los años con IMD
           "val": _c0["validacion"], "elast_bici": coef["bici"]["elasticidad_bici"]},
    # Plan
    "plan": {"lugares": int(len(lug)), "diag": int((lug.kind == "diag").sum()), "act": int((lug.kind == "act").sum()),
             "pl": [sum(n["pl"] == k for n in _neg30) for k in (0, 1, 2)], "pl3": PL3, "alguna": sum(bool(n["plan"]) for n in _neg30),
             "sin_clave": [[k, v] for k, v in SIN_CLAVE.items()],
             "ind": int(len(_ind)), "sin_base": int((_ind.linea_base.astype(str).str.strip() == "—").sum()), "calc": {k: int(v) for k, v in _ind.calculable.value_counts().items()}},
    # gravedad
    "grav_todos": dict(zip(map(str, AÑOS), rel["grav"])) if len(rel["grav"]) == len(AÑOS) else {},
    "grav_bv": {str(a): v for a, v in _gr.items()}, "baja_bv": {str(a): v for a, v in _bg.items()},
    # Plan Director, cap. 8 y apartado 2 (transcripción, docs/plan_pdsv_resumen.md): tres cifras de heridos graves de 2024
    "plan_graves_2024": [176, 167, 185],
    "tipo_lleno": {str(a): _pc(_rd[_rd.fecha.dt.year == a].tipo.notna().mean()) for a in AÑOS},
    # reproducibilidad
    "libs": _req, "python": platform.python_version(),
}
# errores detectados en los datos del Ajuntament (registro a mano: data/processed/incidencias_datos.csv; scripts/incidencias.py
# los re-verifica y escribe el informe para enviar). La web solo publica los textos cortos va/es y el estado.
_inc = pd.read_csv(ROOT / "data/processed/incidencias_datos.csv", dtype=str).fillna("")
met["inc"] = {"n": int(len(_inc)), "auto": int((_inc.verificacion == "auto").sum()),
              "por_estado": {k: int(v) for k, v in _inc.estado.value_counts().items()},
              # [id, conjunto va, conjunto es, qué pasa va, qué pasa es, cómo lo tratamos va, es, estado]
              "filas": [[r.id, r.dataset_va, r.dataset, r.web_que_va, r.web_que_es, r.web_trato_va, r.web_trato_es, r.estado]
                        for r in _inc.itertuples()]}
(OUT.parent / "metode.js").write_text("window.MET=" + json.dumps(met, ensure_ascii=False, separators=(",", ":")) + ";")
print("metode.js:", {k: met[k] for k in ("dup", "cob_bv", "cob_todos", "esc", "concl", "uso_a1", "uso_ix", "sin_ix", "riesgo", "cambia_A", "igual_sinpeso", "cruce_30", "cruce_ciudad", "tur", "plan")})
print("metode.js eb:", met["eb"])

# ---------- «El Pla, al dia / El Plan, al día» (pla.html): seguimiento de las actuaciones de bici y patinete ----------
# Lee SOLO el seguimiento validado de la base (tablas plan_*; su fuente de verdad, con volcado en git y exportación en
# data/processed/plan_seguimiento.csv). Las propuestas del agente verificador van en plan_seguimiento_propuestas.csv y no se
# publican hasta que una persona las acepta y se aplican con aplicar_propuestas_plan.py. Procedimiento: docs/plan_seguimiento.md.
import re as _re
from construir_sqlite import unir_cita as _unir_cita
_PS = BD.plan(_con)        # campos de la base: fecha_fuente, fecha_comprobacion, ref_plan, texto_plan, notas (URL en su orden)…
# solo las medidas (07/11/2026, revisión de datos): el indicador 3.2.2 (clase indicador_impacto) no es una medida y se sigue
# con los datos en el informe; contarlo entre las medidas «sin información» era engañoso
_IND = _PS[_PS.clase != "medida"]       # el indicador: no es una medida, pero sí sale en «lo que el Plan prevé publicar»
_PS = _PS[_PS.clase == "medida"].reset_index(drop=True)

ESTADOS = ["hecha", "en_marcha", "anunciada", "sin_info"]
assert _PS.estado.isin(ESTADOS).all() and _PS.id.is_unique, "plan: estado fuera de la lista o id repetido"
# ejes del Plan: nombre en castellano de pdsv_indicadores.csv («3 Vías seguras»); en valenciano, traducción nuestra
_EJ = {int(m.group(1)): m.group(2) for m in (_re.match(r"(\d) (.+)", e) for e in _ind.eje.unique()) if m}
EJES_VA = {1: "Persones formades i capaces", 2: "Tolerància zero", 3: "Vies segures", 4: "Vehicles segurs",
           5: "Resposta al sinistre", 6: "Dades i coneixement", 7: "Administracions i organitzacions segures"}
# Lo que el Plan prevé publicar o hacer público y de lo que no hay información pública (sección 2 de la página). Solo se
# muestran mientras sigan en sin_info; comprobar.py avisa si un id ya no está o ha cambiado de estado.
TRANSPARENCIA = {
    "3.2.2-meta-siniestros": ("Dades obertes de sinistres del primer any del Pla", "Datos abiertos de siniestros del primer año del Plan"),
    "3.2.2-zonas-lista": ("Llista de zones d'elevada sinistralitat amb bici i patinet", "Lista de zonas de elevada siniestralidad con bici y patinete"),
    "6.1.1-mapa-siniestros": ("Mapa de consulta dels sinistres", "Mapa de consulta de los siniestros"),
    "6.1.1-informes-indicadores": ("Informes d'indicadors de sinistralitat", "Informes de indicadores de siniestralidad"),
    "7.1.1-cuadro-mando": ("Quadre de comandament del Pla", "Cuadro de mando del Plan"),
    "7.1.2-memoria-anual": ("Memòria anual de sinistralitat", "Memoria anual de siniestralidad"),
    "7.3.1-informes-comision": ("Informes de seguiment davant la Comissió de Seguretat Viària", "Informes de seguimiento ante la Comisión de Seguridad Vial"),
    "1.2.4-web-seguridad-vial": ("Apartat web amb dades de sinistralitat i memòria d'actuacions", "Apartado web con datos de siniestralidad y memoria de actuaciones"),
    "6.2-convenios": ("Convenis amb universitats i entitats investigadores", "Convenios con universidades y entidades investigadoras"),
    "3.7-auditorias": ("Auditories noves de seguretat viària", "Auditorías nuevas de seguridad vial"),
    "3.5-evaluacion-zonas30": ("Avaluació de les zones 30", "Evaluación de las zonas 30"),
    "3.2.2-plan-director-bici": ("Seguiment del Pla Director de la Bicicleta", "Seguimiento del Plan Director de la Bicicleta"),
}
# Tipos de fuente. «consultada»: si la búsqueda la ha recorrido directamente (docs/plan_seguimiento.md, apartado 1:
# desde la v2 (04/11/2026) también la Plataforma de Contratación, con sus datos abiertos; el BOP aún no. Los acuerdos de la
# Junta de Gobierno Local solo se conocen por las notas). Las fuentes que solo aparecen dentro de una nota se clasifican por su dominio.
TIPOS_FUENTE = {"plan": ("Pla Director de Seguretat Viària", "Plan Director de Seguridad Vial", True),
                "contratacion": ("Plataforma de Contractació del Sector Públic", "Plataforma de Contratación del Sector Público", True),
                "bop": ("Butlletí Oficial de la Província", "Boletín Oficial de la Provincia", False),
                "junta_gobierno": ("Acords de la Junta de Govern Local", "Acuerdos de la Junta de Gobierno Local", False),
                "nota_prensa": ("Notes de premsa de l'Ajuntament", "Notas de prensa del Ajuntament", True),
                "documento_municipal": ("Altres documents i pàgines municipals", "Otros documentos y páginas municipales", True),
                "respuesta_movilidad": ("Respostes del Servei de Mobilitat", "Respuestas del Servicio de Movilidad", False),
                "prensa": ("Premsa", "Prensa", True)}
assert set(_PS.fuente_tipo) <= set(TIPOS_FUENTE), f"plan: fuente_tipo nuevo {set(_PS.fuente_tipo) - set(TIPOS_FUENTE)}"
FUENTES, _fidx = [], {}
def _fuente(url, titulo, tipo, fecha):
    """Número [n] de la fuente (deduplicada por URL; se queda con el primer título y la fecha más reciente)."""
    if url not in _fidx:
        _fidx[url] = len(FUENTES); FUENTES.append({"n": len(FUENTES) + 1, "url": url, "tit": titulo, "tipo": tipo, "f": ""})
    f = FUENTES[_fidx[url]]
    if fecha and tipo != "plan" and fecha > (f["f"] or ""): f["f"] = fecha   # el Plan: su fecha es la de aprobación (plan_doc)
    return f["n"]
# la fuente principal de cada fila primero (así el Plan es la [1] si es la primera fila), y después las de las notas
_PS["fn_"] = [_fuente(r.fuente_url, r.fuente_titulo, r.fuente_tipo, r.fecha_fuente) if r.fuente_url else 0 for r in _PS.itertuples()]
def _tit_url(u):
    """Título de una fuente que solo aparece dentro de una nota (sin título propio): dominio · último tramo de la dirección."""
    from urllib.parse import unquote
    tramo = unquote(u.rstrip("/").split("/")[-1]).replace("-", " ").replace("_", " ").strip("* ")
    return _re.sub(r"^www\.", "", u.split("/")[2]) + (f" · {tramo}" if len(u.split("/")) > 3 and tramo else "")
# fuentes citadas en la nota (plan_actuacion_fuente, rol nota, en su orden); su tipo, el de la base (por el dominio si solo
# salen en notas, construir_sqlite.tipo_url)
_PS["fnotas_"] = [[_fuente(u, _tit_url(u), BD.tipo_fuente(_con, u), "") for u in r.notas] for r in _PS.itertuples()]
_plan_url = _PS[_PS.fuente_tipo == "plan"].fuente_url.mode().iat[0]
_plan_tit = _PS[_PS.fuente_tipo == "plan"].fuente_titulo.mode().iat[0]
_m = _re.search(r"(\d\d)/(\d\d)/(\d{4})", _plan_tit)
PLAN_DOC = {"url": _plan_url, "tit": _plan_tit, "aprob": f"{_m.group(3)}-{_m.group(2)}-{_m.group(1)}" if _m else "",
            "n": FUENTES[_fidx[_plan_url]]["n"]}

# Actuaciones con coordenadas junto a los lugares del observatorio: se asignan con la MISMA regla que los siniestros
# (scripts/lugares.py, asignar): al nudo cuya envolvente está a <= R = 30 m (es decir, dentro de la zona que se dibuja)
# y, si no hay ninguno, al tramo más cercano. Así una actuación cuenta en un lugar si un siniestro en ese punto contaría
# en él: absorbe la imprecisión de la coordenada (mediana de los siniestros del cruce o encuentro de ejes), no salta al
# cruce de al lado (en el Eixample hay ~110 m entre cruces) y no se cuenta dos veces en nudos vecinos (con un radio fijo
# de 75 m desde el centro, Ausiàs March-Abril Martorell caía también en Ausiàs March-Antonio Ferrandis, otro cruce).
# Los tramos solo cuentan a <= RADIO_PLA m de su línea. Las actuaciones de calle (carril de l'Albereda, Av. del Port…)
# tienen un punto aproximado, no su línea: no se enlazan con fiabilidad (pendiente: geometría de línea en el CSV).
RADIO_PLA = LG.R
_geo = _PS[_PS.lon.notna() & _PS.lat.notna()]
_pa = _geo.set_index("id")
# la asignación la guarda la base (plan_actuacion_lugar, calculada con lugares.asignar al construirla; solo lugares con
# siniestros y a <= R m), en el orden de las actuaciones
_nr = pd.read_sql_query("""SELECT pl.actuacion_id AS id, pl.uid, pl.d_m AS d FROM plan_actuacion_lugar pl
                           JOIN plan_actuacion a ON a.id = pl.actuacion_id ORDER BY a.orden""", _con).set_index("id")
assert RADIO_PLA == LG.R and (_nr.d <= RADIO_PLA).all()
_rank = {c: i + 1 for i, c in enumerate(TOP)}
CERCA = {}                              # uid del top -> [[id de la actuación, distancia en m a la envolvente o la línea]]
for i, r in _nr.iterrows():
    if r.uid in _rank: CERCA.setdefault(int(r.uid), []).append([i, int(round(r.d))])
_sens = {x: int((_nr.d <= x).sum()) for x in (10, 20, 30)}

def _eje(a): m = _re.match(r"\s*(\d)", a); return int(m.group(1)) if m else 0
def _orden(a): return [int(x) for x in _re.findall(r"\d+", a.split("/")[0])]
_PS["eje_"] = _PS.accion_plan.map(_eje)
_PS = _PS.iloc[sorted(range(len(_PS)), key=lambda i: (_PS.eje_.iat[i], _orden(_PS.accion_plan.iat[i]), _PS.ambito.iat[i] != "ciudad"))]
_ult = max(x for x in list(_PS.fecha_comprobacion) + list(_PS.fecha_fuente) if x)
_prox = (pd.Timestamp(_ult) + pd.DateOffset(months=3)).date().isoformat()   # revisión trimestral con validación humana
# propuestas del agente verificador aún sin revisar (plan_seguimiento_propuestas.csv): solo su número y la fecha de la
# comprobación, para decirlo en la página; su contenido no se publica hasta que una persona lo valide
try:
    _pp = pd.read_csv(ROOT / "data/processed/plan_seguimiento_propuestas.csv", dtype=str).fillna("")
    _pp = _pp[_pp.decision.isin(["", "pendiente"])]
    PEND = {"n": int(len(_pp)), "act": int(_pp.id.nunique()), "f": max(_pp.fecha_comprobacion) if len(_pp) else ""}
except (FileNotFoundError, AttributeError, KeyError):
    PEND = {"n": 0, "act": 0, "f": ""}
pla = {
    "rev": {"ult": _ult, "prox": _prox, "comprobado": max(x for x in _PS.fecha_comprobacion if x), "pend": PEND},
    "estados": ESTADOS, "n": int(len(_PS)), "por_estado": {e: int((_PS.estado == e).sum()) for e in ESTADOS},
    "ejes": {str(k): {"va": EJES_VA.get(k, v), "es": v} for k, v in sorted(_EJ.items())},
    "acts": [{"id": r.id, "acc": r.accion_plan, "eje": int(r.eje_), "es": r.actuacion,
              "amb": r.ambito, "lugar": r.lugar, "meta": r.meta, "est": r.estado, "f": r.fecha_fuente, "fn": int(r.fn_),
              "ftipo": r.fuente_tipo, "cita": _unir_cita(r.ref_plan or None, r.texto_plan or None), "nota": r.nota,
              "fnotas": r.fnotas_, "comp": r.fecha_comprobacion,
              "transp": list(TRANSPARENCIA[r.id]) if r.id in TRANSPARENCIA and r.estado == "sin_info" else None,
              # lugar del top del observatorio al lado (n.º, nombre va, nombre es, distancia en m)
              "top": ([_rank[_nr.at[r.id, "uid"]], LUG.at[_nr.at[r.id, "uid"], "nom"], LUG.at[_nr.at[r.id, "uid"], "nom_es"], int(round(_nr.at[r.id, "d"]))]
                      if r.id in _nr.index and _nr.at[r.id, "uid"] in _rank else None)}
             for r in _PS.itertuples()],
    "fuentes": FUENTES, "plan_doc": PLAN_DOC,
    "tipos": [{"k": k, "va": v[0], "es": v[1], "consultada": v[2], "n": sum(f["tipo"] == k for f in FUENTES)} for k, v in TIPOS_FUENTE.items()],
    "radio": RADIO_PLA, "cerca": {str(k): v for k, v in CERCA.items()}, "top_k": len(TOP),
    "con_coord": int(len(_pa)),
    "pub_ind": [{"id": r.id, "est": r.estado, "transp": list(TRANSPARENCIA[r.id])} for r in _IND.itertuples()
                if r.id in TRANSPARENCIA and r.estado == "sin_info"],
}

(OUT.parent / "pla.js").write_text("window.PLA=" + json.dumps(pla, ensure_ascii=False, separators=(",", ":")) + ";")
print(f"pla.js: {pla['n']} actuaciones {pla['por_estado']}; {len(FUENTES)} fuentes; revisión {_ult} → {_prox}; "
      f"con coordenadas {len(_pa)}, a <= {RADIO_PLA} m de un lugar del top: {len(CERCA)} lugares {CERCA}; "
      f"asignadas por distancia a la envolvente: {_sens}; sin lugar con siniestros: {sorted(set(_pa.index) - set(_nr.index))}")

# lo que usa observatori.html de «El Pla, al dia»: la tarjeta de la portada (recuentos), la capa del mapa (actuaciones con
# coordenadas, color por estado) y el bloque de las fichas de los lugares (PLA.cerca). Se reescribe observatori.js.
_A = {a["id"]: a for a in pla["acts"]}
data["pla"] = {"n": pla["n"], "por_estado": pla["por_estado"], "estados": ESTADOS, "rev": _ult,
               # [lon, lat, estado, acción, actuación (original), lugar, fecha de la prueba, id]
               "pts": [[round(float(r.lon), 5), round(float(r.lat), 5), _A[r.id]["est"], _A[r.id]["acc"], _A[r.id]["es"], _A[r.id]["lugar"],
                        _A[r.id]["f"], r.id] for r in _geo.itertuples()]}
for n, c in zip(negros, TOP):
    n.pop("pla", None)
    if c in CERCA:
        n["pla"] = [[i, _A[i]["acc"], _A[i]["est"], _A[i]["es"], _A[i]["f"]] for i, _d in CERCA[c]]
OUT.write_text("window.OBS=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
print(f"observatori.js con pla: {len(data['pla']['pts'])} actuaciones en el mapa; fichas con actuaciones: {sum('pla' in n for n in negros)}")

# «Hi col·laboren / Colaboran»: entidades con su sí por escrito (data/processed/colaboran.csv, una fila por entidad). Solo
# se exportan las filas con publicar = si; sin ninguna, colaboran.json es [] y el pie común (comun/pie.js, lo inserta
# construir_web.py) no pinta nada, ni el título. Una fila se añade al recibir el sí por escrito (con fecha y prueba).
_COL_CAMPOS = ["entidad", "tipo", "que_aporta_va", "que_aporta_es", "url", "desde", "prueba", "publicar"]
_col = pd.read_csv(ROOT / "data/processed/colaboran.csv", dtype=str).fillna("")
assert list(_col.columns) == _COL_CAMPOS, f"colaboran.csv: columnas {list(_col.columns)}"
_col = _col[_col.publicar.str.strip().str.lower() == "si"].sort_values(["desde", "entidad"])
COLAB = [{"ent": r.entidad.strip(), "tipo": r.tipo.strip(), "va": r.que_aporta_va.strip(), "es": r.que_aporta_es.strip(),
          "url": r.url.strip(), "desde": r.desde.strip()} for r in _col.itertuples()]
(OUT.parent / "colaboran.json").write_text(json.dumps(COLAB, ensure_ascii=False, indent=1) + "\n")
print(f"colaboran.json: {len(COLAB)} entidades publicadas")
