"""Incidencias en los datos del Ajuntament de València: re-verificación automática e informe para devolvérselas.

Registro (a mano): data/processed/incidencias_datos.csv, una fila por incidencia (INC-NNN) con su prueba, impacto, cómo
la tratamos, sugerencia y estado (detectada / comunicada / respondida / corregida / no_se_corrige). Los textos cortos de
la web (web_que_*, web_trato_*, dataset_va) los publica exportar_web.py en la página de método.

Este script:
  (a) vuelve a comprobar contra data/raw/ las incidencias con verificacion = auto (para saber, al llegar datos nuevos,
      si siguen o se han corregido) y escribe outputs/incidencias_verificacion.csv y un resumen por pantalla;
      AVISO si una incidencia ya no aparece (¿corregida? cambiar su estado a mano) o si cambia el número medido;
  (b) genera docs/incidencias_para_el_ajuntament.md (castellano): el informe para enviar al Ajuntament, con la prueba
      reproducible, la sugerencia y lo medido en la última comprobación.
Las verificaciones manuales (enlaces, web de Movilidad, servicio del geoportal) no necesitan red y no se hacen aquí.
La ficha CKAN del conjunto de siniestros se lee de data/raw/siniestros/ckan_siniestros_package.json; con --red se
vuelve a descargar (una sola petición) antes de comprobar. Los portales con todos sus atributos (capa 217: codvia,
numportal, dupli_trip, accesorio, descripcion; INC-018) se leen de data/raw/siniestros/portales_atributos.json, que se
descarga con --red o si falta (unas 30 peticiones, con pausa). El geocodificador sigue usando portales.geojson.

Revisión escéptica del 04/11/2026 (las notas internas de trabajo, «Incidencias verificadas»): las comprobaciones miden exactamente lo
que dice el registro corregido (FACTORES con vacío y «NULL», receta de INC-008, INC-009 a más de 100 m con tolerancia de
tipo de vía, INC-018 con todos los atributos, INC-023 por cabeceras, INC-025 por año).

Uso: .venv/bin/python -I scripts/incidencias.py [--red]   (o make incidencias)"""
import csv, datetime as dt, hashlib, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"; SIN = RAW / "siniestros"; INT = RAW / "intensidades"
REG = ROOT / "data/processed/incidencias_datos.csv"
OUT = ROOT / "outputs/incidencias_verificacion.csv"
INFORME = ROOT / "docs/incidencias_para_el_ajuntament.md"
CKAN = SIN / "ckan_siniestros_package.json"
CKAN_URL = "https://opendata.vlci.valencia.es/api/3/action/package_show?id=siniestros-de-trafico-2022-2025"
PORT_ATR = SIN / "portales_atributos.json"
PORT_URL = "https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/217/query"
CRS = "EPSG:25830"
CONTACTO = "hola@observatoribicivlc.org"
# medido al detectarlas (04/11/2026): si cambia, AVISO para revisar filas_afectadas del registro
ESPERADO = {"INC-001": 18, "INC-002": 29, "INC-003": 25, "INC-004": 17, "INC-005": 13787, "INC-006": 15652, "INC-007": 24975,
            "INC-008": 2422, "INC-009": 800, "INC-010": 34244, "INC-011": 34244, "INC-012": 514, "INC-013": 94,
            "INC-018": 51, "INC-019": 9256, "INC-020": 36, "INC-023": 48, "INC-024": 44, "INC-025": 12, "INC-026": 122,
            # revisión sistemática del 07/11/2026
            "INC-027": 28, "INC-028": 6, "INC-029": 19, "INC-030": 65, "INC-031": 15, "INC-032": 1705, "INC-033": 1072, "INC-034": 3,
            "INC-035": 23, "INC-036": 45, "INC-037": 8, "INC-038": 4, "INC-039": 4, "INC-040": 331}
# las más útiles de corregir para quien reutiliza (orden del informe)
PRIORIDAD = ["INC-011", "INC-014", "INC-007", "INC-010", "INC-009"]
ESTADOS = ["detectada", "comunicada", "respondida", "corregida", "no_se_corrige"]

sys.path.insert(0, str(Path(__file__).resolve().parent))      # -I no añade la carpeta del script
import geocodificar as G                                         # índice de nombres -> codvia y cruces del callejero


def fmt(n):
    return f"{n:,}".replace(",", ".") if isinstance(n, int) else str(n)


# ---------- datos ----------
def _bajar_portales():
    """Capa 217 con los atributos que documenta su ficha, en EPSG:25830 (lista de dicts con x, y)."""
    filas, off = [], 0
    while True:
        q = urllib.parse.urlencode(dict(where="1=1", outFields="codvia,numportal,dupli_trip,accesorio,descripcion", outSR=25830,
                                        f="json", resultOffset=off, resultRecordCount=2000, orderByFields="objectid"))
        fs = json.load(urllib.request.urlopen(PORT_URL + "?" + q, timeout=120)).get("features", [])
        filas += [{**f["attributes"], "x": f["geometry"]["x"], "y": f["geometry"]["y"]} for f in fs if f.get("geometry")]
        off += len(fs)
        if len(fs) < 2000:
            break
        time.sleep(1.5)
    PORT_ATR.write_text(json.dumps({"descargado": dt.date.today().isoformat(), "portales": filas}, ensure_ascii=False))


if "--red" in sys.argv:
    CKAN.write_bytes(urllib.request.urlopen(CKAN_URL, timeout=60).read()); time.sleep(4)
if "--red" in sys.argv or not PORT_ATR.exists():
    _bajar_portales()
crudo_f = sorted(SIN.glob("siniestros-de-trafico-*.json"), key=lambda p: p.stat().st_mtime)[-1]
df = pd.DataFrame(json.loads(crudo_f.read_text()))
df["f"] = pd.to_datetime(df.FECHA, errors="coerce")
df["y"] = df.f.dt.year
_m = re.search(r"(\d{4})-(\d{4})", crudo_f.stem)
AÑO_FIN = int(_m.group(2)) if _m else int(df.y.max())
MESES = df.groupby("y").f.agg(lambda x: x.dt.month.nunique())
COMPLETOS = [int(a) for a, n in MESES.items() if n == 12]
dup_exacto = df.drop(columns=["_id", "f", "y"]).duplicated(keep=False)
bv = df.UNIDADES_IMPLICADAS.astype(str).str.contains("BICICLETA|VMP")
metodo = df.UBICACION.map(lambda u: G.geocode(u)[1])
es_cruce = df.UBICACION.astype(str).str.contains(" cruce ")


def _cv_cualquier_tipo(calle):
    """codvias del mismo nombre con cualquier tipo de vía (C/, PL, AV…): por si el tipo está cambiado en el registro."""
    c = G.norm(calle); c = G.norm(G.equiv.get(c, c)); nombre = c.partition(" ")[2]
    return set().union(*(G.por_nombre.get(n, set()) for n in (nombre, G.sin_parentesis(nombre)))) | G.codvias(calle)


def _dmin(ca, cb):
    d = [G.geom[x].distance(G.geom[y]) for x in ca for y in cb if x in G.geom and y in G.geom]
    return min(d) if d else None


def cruce_estado(u):
    """(estado, distancia con el tipo de vía del registro, distancia admitiendo otro tipo de vía del mismo nombre)."""
    a, b = u.split(" cruce ", 1)
    ca, cb = G.codvias(a), G.codvias(b)
    if not ca or not cb:
        return "sin_via", None, None
    if G.cruce(a, b):
        return "ok", None, None
    return "no_tocan", _dmin(ca, cb), _dmin(_cv_cualquier_tipo(a), _cv_cualquier_tipo(b))


_ce = {u: cruce_estado(u) for u in df.UBICACION[es_cruce].unique()}
cr_est = df.UBICACION.map(lambda u: _ce.get(u, (None,) * 3)[0])
cr_dist = df.UBICACION.map(lambda u: _ce.get(u, (None,) * 3)[1]).astype(float)
cr_dist_tol = df.UBICACION.map(lambda u: _ce.get(u, (None,) * 3)[2]).astype(float)
ckan = json.loads(CKAN.read_text())["result"] if CKAN.exists() else None


def hojas(path):
    return pd.read_excel(path, engine="odf", sheet_name=None, header=None)


ODS_BICI = sorted(INT.glob("carril_bici_*.ods"))
_bici = {p: hojas(p) for p in ODS_BICI}


# ---------- comprobaciones: cada una devuelve (sigue: bool | None, medido: int | None, detalle) ----------
def inc001():
    n = int(df.drop(columns=["_id", "f", "y"]).duplicated().sum())
    ids = df[dup_exacto]._id.tolist()
    return n > 0, n, f"{n} filas sobrantes ({int(dup_exacto.sum())} implicadas, {int((dup_exacto & bv).sum() // 2)} pares con bici o VMP); primeros _id {ids[:4]}"


def inc002():
    g = df[~dup_exacto].groupby(["FECHA", "UBICACION"])._id.agg(list)
    g = g[g.str.len() > 1]
    ids_bv = set(df[bv]._id)
    nbv = sum(any(i in ids_bv for i in l) for l in g)
    return len(g) > 0, int(len(g)), f"{len(g)} grupos, {int(g.str.len().sum())} filas, {nbv} con bici o VMP"


def inc003():
    m = df.UNIDADES_IMPLICADAS.astype(str).str.strip() == "["
    return m.any(), int(m.sum()), "por año " + str({int(a): int(n) for a, n in df[m].groupby("y").size().items()})


def inc004():
    m = df.y > AÑO_FIN
    return m.any(), int(m.sum()), f"filas posteriores a {AÑO_FIN} (título del fichero): {sorted(df[m].FECHA.str[:10].unique().tolist())[:3]}"


def _falta(col):
    """Dato que falta en una columna: vacío de verdad (en la API, null) o el texto «NULL»."""
    s = df[col]
    return s.isna() | s.astype(str).str.strip().isin(["", "NULL"])


def _por_año(m, pc=True):
    g = df[df.y.isin(COMPLETOS)].assign(n=m).groupby("y").n
    return ", ".join(f"{a} {100 * v:.1f} %" for a, v in g.mean().items()) if pc else str({int(a): int(v) for a, v in g.sum().items()})


def inc005():
    tipo, fac = _falta("TIPO ACCIDENTE"), _falta("FACTORES CONCURRENTES")
    pc = df[df.y.isin(COMPLETOS)].assign(n=tipo).groupby("y").n.mean()
    mes = df.assign(n=tipo).groupby(df.f.dt.strftime("%Y-%m")).n.mean()
    lleno = next((m for m in mes.index if (mes.loc[m:] < .01).all()), None)
    return bool((pc > .05).any()), int(tipo.sum()), (f"tipo falta: {_por_año(tipo)} (completo desde {lleno}); "
                                                      f"factores faltan ({int(fac.sum())} filas): {_por_año(fac)}")


def inc006():
    t, f = df["TIPO ACCIDENTE"], df["FACTORES CONCURRENTES"]
    t_txt, f_vac = t.astype(str).eq("NULL"), f.isna() | f.astype(str).str.strip().eq("")
    f_txt = f.astype(str).eq("NULL")
    años = lambda m: sorted(int(a) for a in df[m].y.dropna().unique())
    sigue = bool(f_vac.any() and (f_txt.any() or t_txt.any()))
    return sigue, int((f_vac | f_txt).sum()), (f"TIPO: «NULL» {int(t_txt.sum())}, vacío {int((t.isna() | t.astype(str).str.strip().eq('')).sum())}; "
                                               f"FACTORES: vacío {int(f_vac.sum())} (años {años(f_vac)}), «NULL» {int(f_txt.sum())} (años {años(f_txt)})")


def inc007():
    gr = df[df["TIPO GRAVEDAD"] == "CON HERIDOS GRAVES"].groupby("y").size().reindex(COMPLETOS, fill_value=0)
    antes = int(df.y.isin([a for a in COMPLETOS if a < 2025]).sum())      # el Plan: el cambio explica el aumento de 2023 y 2024
    sigue = len(gr) > 1 and gr.iloc[-1] >= 3 * max(gr.iloc[0], 1)
    return bool(sigue), antes, "CON HERIDOS GRAVES por año " + str({int(a): int(n) for a, n in gr.items()}) + f"; filas de 2022-2024 {antes}"


# receta reproducible sin nuestro código (= metodo «solo_calle» del geocodificador): sin « cruce » y sin número de portal
# al final (espacio, cifras y, como mucho, letras: «12», «12 B», «1AC»)
SOLO_CALLE = (~df.UBICACION.astype(str).str.contains(" cruce ")) & (~df.UBICACION.astype(str).str.strip().str.contains(r"\s\d+\s*[A-Z]*$"))


def inc008():
    m = SOLO_CALLE
    mes = df.assign(m=m).groupby(df.f.dt.strftime("%Y-%m")).m.agg(["mean", "sum", "size"])
    peor = mes["mean"].idxmax()
    sitm = metodo[df.f.dt.strftime("%Y-%m") == peor].isin(["cruce", "portal", "portal_cercano"]).mean()
    turia = int((m & df.UBICACION.astype(str).str.contains("JARD[IÍ]N DEL TURIA")).sum())
    sin_digito = int((m & ~df.UBICACION.astype(str).str.contains(r"\d")).sum())
    igual = int((m != (metodo == "solo_calle")).sum())
    return m.any(), int(m.sum()), (f"{100 * m.mean():.1f} % de las filas ({sin_digito} sin ninguna cifra + {int(m.sum()) - sin_digito} carreteras con código); "
                                   f"{100 * m[df.f < pd.Timestamp('2022-10-01')].mean():.1f} % en ene.-sep. 2022; peor mes {peor}: "
                                   f"{int(mes.loc[peor, 'sum'])} de {int(mes.loc[peor, 'size'])} ({100 * mes.loc[peor, 'mean']:.1f} %), situado por nosotros {100 * sitm:.1f} %; "
                                   f"Jardín del Turia {turia}; filas en que la receta y el geocodificador difieren {igual}")


def inc009():
    """Cruces entre calles que no se tocan, a más de 100 m (la franja de 40-100 m depende de nuestro método y no se publica).
    Medido: admitiendo que el tipo de vía (C/, PL…) esté cambiado; entre paréntesis, con el tipo del registro."""
    lej, lej_tol = cr_dist > 100, cr_dist_tol > 100
    per = df.f < pd.Timestamp("2024-07-01")
    pc = lambda m: f"{100 * m[per & es_cruce].mean():.1f} % de los cruces hasta jun. 2024 y {100 * m[~per & es_cruce].mean():.1f} % desde jul. 2024"
    return lej_tol.any(), int(lej_tol.sum()), (f">100 m {int(lej_tol.sum())} ({int(lej.sum())} con el tipo del registro); >300 m {int((cr_dist_tol > 300).sum())} "
                                               f"({int((cr_dist > 300).sum())}); {pc(lej_tol)}; solo lejanos por el tipo de vía {int((lej & ~lej_tol).sum())}")


def inc010():
    seg = df.FECHA.astype(str).str[-2:] != "00"
    antes = seg[df.f < pd.Timestamp("2024-07-01")].sum()
    t3 = seg[(df.f >= pd.Timestamp("2024-07-01")) & (df.f < pd.Timestamp("2024-10-01"))].sum()
    t4 = seg[(df.f >= pd.Timestamp("2024-10-01")) & (df.y == 2024)].sum()
    solo = SOLO_CALLE
    p1 = solo[(df.f >= pd.Timestamp("2022-09-01")) & (df.f < pd.Timestamp("2022-10-01"))].mean()
    p2 = solo[(df.f >= pd.Timestamp("2022-10-01")) & (df.f < pd.Timestamp("2022-11-01"))].mean()
    tipo = _falta("TIPO ACCIDENTE"); mes = df.f.dt.strftime("%Y-%m")
    sigue = antes == 0 and seg.any() and p1 > 3 * p2
    return bool(sigue), int(len(df)), (f"horas con segundos: {int(antes)} hasta jun. 2024, {int(t3)} jul.-sep. 2024, {int(t4)} oct.-dic. 2024, "
                                       f"{int(seg[df.y == 2025].sum())} en 2025; solo calle {100 * p1:.1f} % en sep. 2022 y {100 * p2:.1f} % en oct. 2022; "
                                       f"tipo que falta {100 * tipo[mes == '2024-06'].mean():.1f} % en jun. 2024 y {100 * tipo[mes == '2024-07'].mean():.1f} % en jul. 2024")


def inc011():
    cols = [c for c in df.columns if re.search(r"lon|lat|coord|^x$|^y_|codvia|geom", c, re.I) and c not in ("f", "y")]
    return not cols, int(len(df)), f"columnas: {', '.join(c for c in df.columns if c not in ('f', 'y'))}"


# grafía distinta del callejero (1) y entradas del callejero sin eje o dadas de baja (2): «IL·LUSIÓ» queda fuera, porque
# es el callejero el que escribe «IL.LUSIÓ» (con punto) y en cambio «IL·LUSTRACIÓ» (con punto volado)
EJ12 = {"PROFESOR LOPEZ PIÑERO": None, "LLOC PUENTE MONTEOLIVETE": 990210, "FRANCISCO LOZANO (PINTOR).CARRER DE": 81475}


def inc012():
    c = {e: int(df.UBICACION.astype(str).str.contains(re.escape(e)).sum()) for e in EJ12}
    vias = {v["codvia"]: v for v in G.vias}
    notas = []
    if not any("PROFESOR LOPEZ PI" in (v.get("nomoficial") or "") + (v.get("traducnooficial") or "") for v in G.vias):
        notas.append("PROFESOR (con una s) no está en el callejero")
    for e, cv in EJ12.items():
        if cv:
            v = vias.get(cv, {})
            notas.append(f"{cv}: {'de baja' if v.get('fechabaja') else 'vigente'}, {'con' if cv in G.geom else 'sin'} eje")
    return sum(c.values()) > 0, sum(c.values()), f"{c}; {'; '.join(notas)}"


def inc013():
    m = cr_est == "sin_via"
    u = df.UBICACION.astype(str)
    turia = u.str.contains("JARD[IÍ]N DEL TURIA")
    ctra = u.str.contains(r"\b(?:A|CTRA)\s+C?V-?\d") & ~u.str.contains(r"\bV-?30\b")
    mc = m & (turia | u.str.contains(r"\b(?:A|CTRA)\s+C?V-?\d"))           # cruces sin situar por el Turia o una carretera
    nan = m & u.str.endswith(" cruce nan")
    return mc.any(), int(mc.sum()), (f"{int(mc.sum())} cruces sin situar por estas vías ({int((mc & turia).sum())} con el Jardín del Turia); "
                                     f"de {int(m.sum())} cruces con alguna vía sin codvia ({int(nan.sum())} terminan en «cruce nan»); "
                                     f"filas con el Jardín del Turia {int(turia.sum())}; con autovías o carreteras (sin la V-30, que sí está) {int(ctra.sum())}")


def inc014():
    if not ckan:
        return None, None, "sin ficha CKAN descargada"
    frec = [k for k in ckan if re.search(r"freq|frecuen|accrual|periodic", k, re.I)]
    return ckan["num_resources"] == 1 and not frec and "2022-2025" in ckan["title_es"], None, \
        f"recursos {ckan['num_resources']}; campos de frecuencia {frec or 'ninguno'}; creado {ckan['metadata_created'][:10]}; título «{ckan['title_es']}»"


def inc015():
    if not ckan:
        return None, None, "sin ficha CKAN descargada"
    notas = ckan.get("notes_es") or ""
    dicc = [r for r in ckan["resources"] if re.search(r"diccion|diccio|schema|esquema", (r.get("name") or "") + (r.get("description") or ""), re.I)]
    errata = any("2022y" in (r.get("description") or "") for r in ckan["resources"])
    errata_es = any("2022y" in (r.get("description_es") or "") for r in ckan["resources"])
    return len(notas) < 200 and not dicc, None, (f"notes_es de {len(notas)} caracteres; recursos de diccionario {len(dicc)}; "
                                                 f"errata «2022y» en description {'sí' if errata else 'no'}, en description_es {'sí' if errata_es else 'no'}")


def inc018():
    p = pd.DataFrame(json.loads(PORT_ATR.read_text())["portales"])
    for c in ("dupli_trip", "accesorio", "descripcion"):
        p[c] = p[c].fillna("").astype(str).str.strip()
    claves = ["codvia", "numportal", "dupli_trip", "accesorio", "descripcion"]

    def grupos(k):
        d = {g: max(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** .5 for a in xy for b in xy)
             for g, xy in ((g, list(zip(t.x, t.y))) for g, t in p.groupby(k) if len(t) > 1)}
        return pd.Series(d, dtype=float)

    d3, d5 = grupos(claves[:3]), grupos(claves)
    d5d = d5[d5 > .5]                                          # en posiciones distintas
    num = p.descripcion.str.extract(r"^(\d+)")[0]
    rot = int((num.notna() & (num != p.numportal.astype("Int64").astype(str))).sum())
    acc = sorted(p.accesorio.unique().tolist())
    return len(d5d) > 0, int(len(d5d)), (f"{len(p)} portales; con los 5 atributos iguales: {len(d5)} combinaciones, {len(d5d)} en posiciones distintas, "
                                          f"{int((d5d > 50).sum())} a más de 50 m, {int((d5d > 200).sum())} a más de 200 m, máximo {d5d.max():.0f} m; "
                                          f"solo con (codvia, numportal, dupli_trip): {len(d3)}; numportal distinto de su rótulo: {rot}; valores de accesorio {acc}")


def inc019():
    a, b = SIN / "vmp_tipo_a.geojson", SIN / "vmp_tipo_b.geojson"
    if not (a.exists() and b.exists()):
        return None, None, "falta una de las dos capas descargadas"
    igual = hashlib.md5(a.read_bytes()).digest() == hashlib.md5(b.read_bytes()).digest()
    g = gpd.read_file(a)
    campos = [c for c in g.columns if c != "geometry"]
    return igual, len(g), f"{'idénticas' if igual else 'distintas'}; {len(g)} tramos, {g.to_crs(CRS).length.sum() / 1000:.0f} km; campos descargados {campos}"


def inc020():
    t = pd.DataFrame([f["properties"] for f in json.loads((SIN / "intensidad_tramos.geojson").read_text())["features"]])
    fecha = [c for c in t.columns if re.search(r"fecha|date|hora|time", c, re.I)]
    n = int((pd.to_numeric(t.lectura, errors="coerce") == -1).sum())
    return not fecha, n, f"{n} de {len(t)} tramos con lectura -1; campos de fecha {fecha or 'ninguno'}"


# INC-021 (Obras ejecutadas) retirada el 07/11/2026 por decisión del usuario: el observatorio no usa ese conjunto


def _cod_col(h, patron):
    es = h.apply(lambda c: c.astype(str).str.strip().str.fullmatch(patron).mean())
    return es.idxmax()


def inc023():
    """Cambia la estructura: nombres de cabecera (primera fila) del código y de la IMD, sentido en columna propia o no,
    hojas con columnas vacías (o el código fuera de la primera columna) y número de columnas con contenido."""
    cab, cab_imd, llenas, vacias, sentido, n = set(), set(), {}, [], {}, 0
    for p, hs in _bici.items():
        for nom, h in hs.items():
            n += 1
            c = _cod_col(h, r"P\d+")
            fila0 = [str(v).strip() for v in h.iloc[0].tolist()]
            cab.add(fila0[c])
            cab_imd.add([v for v in fila0 if v not in ("", "nan")][-1])
            sentido[f"{p.stem[-4:]}/{nom}"] = any(v.lower() == "sentido" for v in fila0)
            con = [k for k in h.columns if h[k].notna().sum() > 1]
            llenas[len(con)] = llenas.get(len(con), 0) + 1
            if len(con) < h.shape[1] or c != h.columns[0]:
                vacias.append(f"{p.stem[-4:]}/{nom}")
    prim = next((k for k, v in sentido.items() if v), None)
    return len(cab) > 1 or len(cab_imd) > 1, n, (f"{n} hojas; cabecera del código {sorted(cab)}; de la IMD {sorted(cab_imd)}; "
                                                 f"columna Sentido desde {prim}; hojas por n.º de columnas con contenido {dict(sorted(llenas.items()))}; "
                                                 f"hojas con columnas vacías o el código desplazado {vacias}")


def inc024():
    hojas_err, cods, columna = {}, set(), {}
    for p, hs in _bici.items():
        for nom, h in hs.items():
            filas = h[h.apply(lambda f: bool(re.search(r"\bENTIDOS\b", " ".join(map(str, f.values)).upper())), axis=1)]
            if len(filas):
                hojas_err[p.stem[-4:]] = hojas_err.get(p.stem[-4:], 0) + 1
                cods |= {str(v).strip() for v in filas.values.ravel() if re.fullmatch(r"P\d+", str(v).strip())}
                aparte = any(str(v).strip().upper() == "AMBOS ENTIDOS" for v in filas.values.ravel())
                columna.setdefault("columna aparte" if aparte else "en la descripción", []).append(f"{p.stem[-4:]}/{nom}")
    n = sum(hojas_err.values())
    prim = {k: v[0] for k, v in columna.items()}
    return n > 0, n, f"contadores {sorted(cods)}; hojas con «ENTIDOS» por año {hojas_err}; primera hoja de cada forma {prim}"


def _codigos(hs):
    cod = set()
    for h in hs.values():
        c = _cod_col(h, r"P\d+"); s = h[c].astype(str).str.strip()
        cod |= set(s[s.str.fullmatch(r"P\d+")])
    return cod


def inc025():
    """Medido: códigos sin punto en la capa 225 en el último año; en el detalle, por año y en el total."""
    ids = set(gpd.read_file(SIN / "espiras_bici.geojson").idpm.dropna().astype(int))
    por = {p.stem[-4:]: _codigos(hs) for p, hs in _bici.items()}
    sin = {a: {c for c in cs if int(c[1:]) not in ids} for a, cs in por.items()}
    ult = max(por)
    tot, tot_sin = set().union(*por.values()), set().union(*sin.values())
    return bool(sin[ult]), len(sin[ult]), (f"sin punto en la capa 225 por año {{{', '.join(f'{a}: {len(sin[a])} de {len(por[a])}' for a in sorted(por))}}}; "
                                           f"en total {len(tot_sin)} de {len(tot)}, {len(tot_sin - por[ult])} de ellos ya no están en {ult}; en {ult}: {sorted(sin[ult])[:6]}")


def inc026():
    veh = sorted(INT.glob("imds_vehiculos_*.ods"))[-1]
    cod = {}
    for h in hojas(veh).values():
        for c in h.columns:
            s = h[c].astype(str).str.strip()
            for x in s[s.str.fullmatch(r"[A-Z]\d+")]:
                cod.setdefault(x[0], set()).add(x)
    tr = {f["properties"]["idtramo"] for f in json.loads((SIN / "intensidad_tramos.geojson").read_text())["features"]}
    sin = {k: len(v - tr) for k, v in cod.items()}
    return sin.get("A", 0) > 0, sin.get("A", 0), f"{veh.name}: sin idtramo en la capa 188 por prefijo " + ", ".join(f"{k} {sin[k]} de {len(cod[k])}" for k in sorted(cod))


# ---------- revisión sistemática del 07/11/2026 (INC-027 a INC-040) ----------
def inc027():
    """«nan» escrito en la ubicación (calle o segunda calle que falta) y cruces de una calle consigo misma."""
    u = df.UBICACION.astype(str)
    nan = u.str.contains(r"\bnan\b")
    p = u.str.split(" cruce ")
    misma = es_cruce & (p.str[0].str.strip() == p.str[1].str.strip())
    turia = u.str.contains("JARD[IÍ]N DEL TURIA")
    return bool(nan.any()), int(nan.sum()), (f"«nan» {int(nan.sum())} filas ({int((nan & bv).sum())} con bici o VMP), de {df[nan].f.min():%Y-%m} a {df[nan].f.max():%Y-%m}: "
                                             f"{int(u[nan].str.endswith(' cruce nan').sum())} «… cruce nan», {int((u[nan] == 'nan').sum())} «nan» solo, "
                                             f"{int(u[nan].str.fullmatch(r'nan \d+').sum())} «nan <número>»; calle cruzada consigo misma {int(misma.sum())} "
                                             f"({int((misma & turia).sum())} Jardín del Turia, {int((misma & bv).sum())} con bici o VMP); primeros _id {df[nan]._id.tolist()[:3]}")


def _vias():
    return pd.DataFrame(json.loads((SIN / "vias.json").read_text()))


def inc028():
    """Traducción al castellano del callejero cortada (paréntesis sin cerrar donde el nombre oficial lo cierra) y nombres con
    espacio o salto de línea al final."""
    v = _vias()
    t, o = v.traducnooficial.fillna(""), v.nomoficial.fillna("")
    abre = lambda s: s.str.count(r"\(") > s.str.count(r"\)")
    cort = v[abre(t) & ~abre(o)]
    sobra = int(((t != t.str.rstrip()) & (t != "")).sum() + (o != o.str.rstrip()).sum())
    u = df.UBICACION.astype(str)
    sin = sum(int(u.str.contains(re.escape(x) + r"(?=$| cruce |\s\d)").sum()) for x in cort.traducnooficial)
    return len(cort) > 0, int(len(cort)), (f"cortados {dict(zip(cort.codvia, cort.traducnooficial.str.len()))}; "
                                           f"con espacio o salto de línea al final {sobra}; filas de siniestros con un nombre cortado {sin}")


def _ejes():
    return gpd.read_file(SIN / "ejes.geojson")


def inc029():
    e = _ejes(); v = _vias()
    sin = int(e.codvia.isna().sum())
    m = e.to_crs(CRS)
    dup = m.drop(columns="geometry").assign(w=m.geometry.to_wkb()).duplicated(keep=False)
    baja = set(v[v.fechabaja.notna()].codvia)
    return sin > 0 or dup.any(), sin, (f"tramos sin codvia {sin} ({m[e.codvia.isna()].length.sum():.0f} m); tramos repetidos en todo "
                                       f"{int(dup.sum())} ({e[dup][['codvia', 'nomcalle', 'lf_add', 'lt_add']].drop_duplicates().values.tolist()}); "
                                       f"tramos con codvia de baja {int(e.codvia.isin(baja).sum())} {sorted(e[e.codvia.isin(baja)].codvia.astype(int).unique().tolist())}")


TIPO_VIA = {"C/": "CARRER", "AV": "AVINGUDA", "PL": "PLAÇA", "CAMI": "CAMÍ", "CTRA": "CARRETERA", "ENTD": "ENTRADOR", "GV": "GRAN VIA",
            "LLOC": "LLOC", "PG": "PASSEIG", "CV": "CAMÍ VELL", "CN": "CAMÍ NOU", "CRA": "CARRERA", "SENDA": "SENDA", "PTDA": "PARTIDA",
            "BARRI": "BARRI", "GRUP": "GRUP", "PTGE": "PASSATGE", "TRAV": "TRAVESSERA", "CRO": "CARRERÓ", "CH": "CAMÍ FONDO"}


def inc030():
    e = _ejes().merge(_vias()[["codvia", "codtipovia", "nomoficial"]], on="codvia", how="left")
    acento = e.nomcalle.fillna("").str.contains("´")
    tipo = e.dropna(subset=["codtipovia", "tipcalle"])
    distinto = tipo[tipo.codtipovia.map(TIPO_VIA) != tipo.tipcalle]
    return bool(acento.any()), int(e[acento].codvia.nunique()), (f"«´» en {int(acento.sum())} tramos de {e[acento].codvia.nunique()} vías (vías: 0 con «´»); "
                                                                 f"tipcalle distinto del tipo de vía de la capa 273: {distinto.groupby(['codtipovia', 'tipcalle']).size().to_dict()}")


def inc031():
    """Portales a más de 200 m del eje de su propia calle (EPSG:25830)."""
    p = pd.DataFrame(json.loads(PORT_ATR.read_text())["portales"])
    g = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.x, p.y), crs=CRS)
    ejes = _ejes().dropna(subset=["codvia"]).to_crs(CRS).dissolve("codvia").geometry
    g = g[g.codvia.isin(ejes.index)].reset_index(drop=True)
    d = g.geometry.distance(gpd.GeoSeries(ejes.reindex(g.codvia).values, crs=CRS))
    lej = g.assign(d=d)[d > 200].sort_values("d", ascending=False)
    return bool(len(lej)), int(len(lej)), (f"{len(lej)} portales a más de 200 m del eje de su calle, {int((d > 1000).sum())} a más de 1 km; "
                                           f"mayores: {[(int(r.codvia), int(r.numportal), r.descripcion, round(r.d)) for r in lej.head(3).itertuples()]}")


def inc032():
    c = gpd.read_file(SIN / "carriles_bici.geojson")
    km = c.to_crs(CRS).assign(km=lambda x: x.length / 1000).groupby("estado").km.sum()
    cero = int((pd.to_numeric(c.st_length_the_geom_, errors="coerce") == 0).sum())
    return cero == len(c), cero, (f"st_length_the_geom_ = 0 en {cero} de {len(c)}; tramos por código {c.estado.value_counts().sort_index().to_dict()}; "
                                  f"km del código 8 (fuera del término) {km.get('8', 0):.1f} de {km.sum():.1f}")


def inc033():
    r = gpd.read_file(SIN / "reguladores_semaforos.geojson")
    vac = r.tiporegulador.isna() & r.codregulador.isna()
    return bool(vac.all()), int(vac.sum()), f"tiporegulador y codregulador vacíos en {int(vac.sum())} de {len(r)}"


def inc034():
    t = gpd.read_file(SIN / "intensidad_tramos.geojson")
    rep = t[t.idtramo.notna() & t.idtramo.duplicated(keep=False)]
    sin = t[t.geometry.isna()]
    return bool(len(rep) or len(sin)), int(rep.idtramo.nunique()), (f"idtramo repetido {sorted(rep.idtramo.unique())} (gid {rep.gid.tolist()}); "
                                                                     f"registros sin geometría ni idtramo {len(sin)} con fiwareid {sin.fiwareid.tolist()}")


def inc035():
    out = {}
    for k in ("a", "b"):
        g = gpd.read_file(SIN / f"vmp_tipo_{k}.geojson").to_crs(CRS)
        n = g.geometry.normalize().to_wkb()
        sob = n.duplicated()
        out[k] = (int(sob.sum()), int(g.geometry.to_wkb().duplicated().sum()), g[sob].length.sum() / 1000, g[n.isin(n[sob])].gid.sort_values().tolist()[:4])
    return out["a"][0] > 0, out["a"][0], "; ".join(f"tipo {k.upper()}: {v[0]} tramos repetidos ({v[1]} en el mismo sentido), {v[2]:.1f} km; gid {v[3]}" for k, v in out.items())


def _imd_largo(hs):
    """Hojas mensuales → filas (mes, código tal cual, valor de la IMD tal cual). La columna del código es la que más casa con
    letra + cifras (sin distinguir mayúsculas); la de la IMD, la numérica más a la derecha."""
    filas = []
    for i, h in enumerate(hs.values()):
        c = h.apply(lambda s: s.astype(str).str.strip().str.fullmatch(r"[A-Za-z]\d+").mean()).idxmax()
        cuerpo = h[h[c].astype(str).str.strip().str.fullmatch(r"[A-Za-z]\d+")]
        num = cuerpo.drop(columns=c).apply(lambda s: pd.to_numeric(s, errors="coerce").notna().mean())
        ci = num[num > .5].index.max()
        filas += [(i + 1, str(a).strip(), b) for a, b in zip(cuerpo[c], cuerpo[ci])]
    return pd.DataFrame(filas, columns=["mes", "cod", "raw"]).assign(imd=lambda d: pd.to_numeric(d.raw, errors="coerce"))


_bici_largo = pd.concat([_imd_largo(hs).assign(año=int(p.stem[-4:])) for p, hs in _bici.items()], ignore_index=True)


def inc036():
    b = _bici_largo
    minus = b[b.cod.str.fullmatch(r"[a-z]\d+")]
    texto = b[b.raw.map(lambda x: isinstance(x, str))]
    dec = b[b.imd % 1 != 0].groupby(["año", "mes"]).size()
    return bool(len(minus)), int(len(minus)), (f"códigos en minúscula {minus.cod.value_counts().to_dict()} por año {minus.groupby('año').size().to_dict()}; "
                                               f"IMD como texto {len(texto)} celdas {texto.groupby(['año', 'mes']).size().to_dict()}; "
                                               f"hojas con decimales {len(dec)} de {b.groupby(['año', 'mes']).ngroups} ({int(dec.sum())} valores)")


def inc037():
    b = _bici_largo
    rep = b[b.duplicated(["año", "mes", "cod"], keep=False)]
    f = b[b.cod.str.startswith("F")]
    par = f.merge(b[b.cod.str.startswith("P")], on=["año", "mes", "imd"], suffixes=("_f", "_p")).groupby(["cod_f", "cod_p"]).size()
    par = par[par >= 6]
    return bool(len(rep)), int(rep.groupby(["año", "mes"]).ngroups), (f"código repetido en la misma hoja: {rep.cod.unique().tolist()} en {rep.groupby(['año', 'mes']).ngroups} hojas; "
                                                                      f"códigos F {f.cod.nunique()} ({len(f)} filas), {len(par)} repiten el valor de un P en 6 meses o más: "
                                                                      f"{dict(list(par.to_dict().items())[:4])}")


def inc038():
    b = _bici_largo
    a = b[b.cod.str.fullmatch(r"A\d+")]
    cero = b[(b.imd == 0) & b.cod.str.fullmatch(r"P\d+")]
    vacia = b[b.imd.isna() & b.cod.str.fullmatch(r"P\d+")]
    return bool(len(a)), int(len(a)), (f"códigos de tramo de vehículos en el carril bici {a.cod.unique().tolist()} en {len(a)} hojas (IMD {int(a.imd.min())}-{int(a.imd.max())}); "
                                       f"IMD = 0 {len(cero)} {cero[['año', 'mes', 'cod']].values.tolist()}; IMD vacía {vacia[['año', 'mes', 'cod']].values.tolist()}")


def inc039():
    veh = sorted(INT.glob("imds_vehiculos_*.ods"))[-1]
    hs = hojas(veh)
    v = _imd_largo(hs)
    cero = v[v.imd == 0]
    dec = v[v.imd % 1 != 0].groupby("mes").size()
    blancos = sum(int(h.map(lambda x: isinstance(x, str) and x != "" and x.strip() == "").values.sum()) for h in hs.values())
    return bool(len(cero)), int(len(cero)), (f"{veh.name}: IMD = 0 {cero[['mes', 'cod']].values.tolist()}; meses con decimales {dec.to_dict()}; "
                                             f"celdas con solo espacios {blancos}")


XLSX_HOJAS = ["Accesos", "Vías Principales", "Carriles Bici Representativos"]


def inc040():
    """XLSX de evolución mensual: la fiabilidad y la estimación se marcan solo con colores; y no cuadra con los ODS del carril bici."""
    import openpyxl
    xl = sorted(INT.glob("evolucion_imd_mensual_*.xlsx"))[-1]
    wb = openpyxl.load_workbook(xl)
    col, otro = {}, 0
    for nom in XLSX_HOJAS:
        ws = wb[nom]
        cab = {c.column: str(c.value)[:7] for c in ws[1]}
        for fila in ws.iter_rows(min_row=2):
            if not re.fullmatch(r"A?\d+", str(fila[0].value)):
                continue
            for c in fila:
                if c.value is None or not re.match(r"\d{4}-\d{2}", cab.get(c.column, "")) or not c.fill.fill_type:
                    continue
                f = c.fill.fgColor.rgb
                if f == "FFFFFF00":
                    k = "fiabilidad < 85 %" if c.font.color is not None and c.font.color.rgb == "FFFF0000" else "estimada"
                    col[k] = col.get(k, 0) + 1
                else:
                    otro += 1
    x = pd.read_excel(xl, sheet_name="Carriles Bici Representativos", header=None)
    cab = [str(c)[:7] for c in x.iloc[0]]
    xs = [("P" + str(r[0]), cab[i], pd.to_numeric(r[i], errors="coerce")) for _, r in x.iloc[1:].iterrows() if re.fullmatch(r"\d+", str(r[0]))
          for i in range(len(cab)) if re.match(r"\d{4}-\d{2}$", cab[i])]
    xs = pd.DataFrame(xs, columns=["cod", "ym", "xlsx"]).dropna()
    b = _bici_largo.assign(ym=lambda d: d.año.astype(str) + "-" + d.mes.map("{:02d}".format)).drop_duplicates(["cod", "ym"])
    m = xs.merge(b[["cod", "ym", "imd"]], on=["cod", "ym"])
    dif = m[(m.xlsx - m.imd).abs() > .05 * m.imd]
    n = sum(col.values())
    return n > 0, n, (f"{xl.name}: celdas marcadas solo con color {col}, con otro relleno sin leyenda {otro}; carril bici XLSX frente a ODS: "
                      f"{len(m)} comparados, {len(dif)} difieren más de un 5 %: {[(r.cod, r.ym, round(r.xlsx), r.imd) for r in dif.itertuples()]}")


CHECKS = {f"INC-{k[3:]}": v for k, v in globals().items() if re.fullmatch(r"inc\d{3}", k)}

# ---------- (a) re-verificación ----------
reg = pd.read_csv(REG, dtype=str).fillna("")
assert reg.id.is_unique and set(reg.estado) <= set(ESTADOS), "registro: ids repetidos o estado desconocido"
assert set(CHECKS) <= set(reg.id), f"comprobaciones sin fila en el registro: {set(CHECKS) - set(reg.id)}"
hoy = dt.date.today().isoformat()
filas, avisos = [], 0
print(f"Incidencias: {len(reg)} en el registro; datos de {crudo_f.name} ({len(df)} filas)")
for r in reg.itertuples():
    if r.verificacion != "auto":
        filas.append([r.id, r.verificacion, "", "", ESPERADO.get(r.id, ""), "", "comprobación manual", hoy])
        print(f"MANUAL {r.id}  {r.web_que_es}")
        continue
    if r.id not in CHECKS:
        print(f"AVISO  {r.id}: verificacion = auto sin comprobación en el script"); avisos += 1; continue
    sigue, n, det = CHECKS[r.id]()
    esp = ESPERADO.get(r.id)
    cambia = esp is not None and n is not None and n != esp
    nivel = "OK" if sigue and not cambia else "AVISO"
    if sigue is False and r.estado != "corregida":
        det = "YA NO APARECE: ¿corregida? (cambiar el estado en el registro) · " + det
    elif sigue and r.estado == "corregida":
        det = "MARCADA COMO CORREGIDA Y SIGUE · " + det
    elif cambia:
        det = f"CAMBIA: {fmt(esp)} → {fmt(n)} (revisar filas_afectadas) · " + det
    elif sigue is None:
        nivel = "AVISO"
    avisos += nivel == "AVISO"
    filas.append([r.id, "auto", {True: "sí", False: "no", None: "?"}[sigue], "" if n is None else n, "" if esp is None else esp,
                  "sí" if cambia else "no", det, hoy])
    print(f"{nivel:6s} {r.id}  sigue: {filas[-1][2]:2s} medido: {fmt(n) if n is not None else '—':>7s}  {det[:150]}")
OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "verificacion", "sigue", "medido", "esperado", "cambia", "detalle", "fecha"])
    w.writerows(filas)
ver = {f[0]: f for f in filas}
print(f"\nPor tipo: {reg.tipo.value_counts().to_dict()}")
print(f"Por estado: {reg.estado.value_counts().to_dict()}; automáticas {int((reg.verificacion == 'auto').sum())}, manuales {int((reg.verificacion != 'auto').sum())}")
print(f"{avisos} avisos. Salidas: {OUT.relative_to(ROOT)} y {INFORME.relative_to(ROOT)}")

# ---------- (b) informe para el Ajuntament ----------
NOM = {"detectada": "detectada", "comunicada": "comunicada", "respondida": "con respuesta", "corregida": "corregida", "no_se_corrige": "no se corregirá"}


def celda(t):
    return str(t).replace("|", "\\|").replace("\n", " ")


def ficha(r):
    v = ver.get(r.id)
    medido = (f"{fmt(int(v[3]))} (comprobado el {v[7]})" if v and v[3] != "" else "—") if v and v[1] == "auto" else "comprobación manual"
    sigue = {"sí": "sigue presente", "no": "**ya no aparece en los datos actuales**", "?": "no se ha podido comprobar"}.get(v[2], "") if v and v[1] == "auto" else ""
    out = [f"#### {r.id} · {r.web_que_es.rstrip('.')}", "",
           f"- **Conjunto:** {r.dataset} ({r.url})",
           f"- **Campo:** {r.campo} · **Tipo:** {r.tipo} · **Estado:** {NOM[r.estado]}" + (f" ({r.fecha_comunicacion}, {r.canal})" if r.fecha_comunicacion else ""),
           f"- **Qué pasa:** {r.descripcion}",
           f"- **Ejemplo:** {r.ejemplo}",
           f"- **Alcance:** {r.filas_afectadas}" + (f". Última comprobación automática: {medido}, {sigue}." if sigue else "."),
           f"- **Por qué importa a quien reutiliza:** {r.impacto}",
           f"- **Cómo lo tratamos en el observatorio:** {r.como_lo_tratamos}",
           f"- **Sugerencia:** {r.sugerencia}",
           f"- **Cómo reproducirlo:** {r.prueba}"]
    if r.respuesta:
        out.append(f"- **Respuesta del Ajuntament:** {r.respuesta}")
    return "\n".join(out) + "\n"


R = {r.id: r for r in reg.itertuples()}
n_auto = int((reg.verificacion == "auto").sum())
md = [
    "# Incidencias detectadas en datos abiertos del Ajuntament de València",
    "",
    f"*Observatorio de la bici y el patinete de València · {CONTACTO} · última comprobación: {hoy}*",
    "",
    "Usamos los datos abiertos del Ajuntament de València para seguir los siniestros con bici y patinete en la ciudad. "
    "Sin el portal de datos abiertos, el callejero del geoportal y las intensidades del Servicio de Movilidad, el observatorio no sería posible: gracias por publicarlos.",
    "",
    "Al trabajar con ellos hemos encontrado algunas incidencias. Las recogemos aquí para devolverlas, por si son útiles para mejorar los datos. "
    "Es lo que vemos al reutilizarlos, con propuestas que harían más fácil el trabajo de otras personas que también los usan. "
    "Cada incidencia lleva un ejemplo, su alcance, cómo la tratamos nosotros, una sugerencia y la forma de reproducirla con los datos publicados. "
    "Puede que alguna tenga una explicación que desconocemos; si es así, nos encantará saberlo y corregir este registro.",
    "",
    f"Son **{len(reg)} incidencias**: " + ", ".join(f"{n} de {t}" for t, n in reg.tipo.value_counts().items()) + ". "
    f"{n_auto} se vuelven a comprobar automáticamente con cada descarga de los datos, así que sabremos cuándo dejan de aparecer.",
    "",
    "## Las más útiles de corregir",
    "",
]
for i in PRIORIDAD:
    r = R[i]
    md.append(f"1. **{r.web_que_es.rstrip('.')}** ({r.id}). Sugerencia: {r.sugerencia}")
md += ["", "## Resumen", "", "| Id | Conjunto | Tipo | Qué pasa | Alcance | Estado |", "|---|---|---|---|---|---|"]
md += [f"| {r.id} | {celda(r.dataset)} | {r.tipo} | {celda(r.web_que_es)} | {celda(r.filas_afectadas)} | {NOM[r.estado]} |" for r in reg.itertuples()]
md += ["", "## Detalle", ""]
for ds, g in reg.groupby("dataset", sort=False):
    md += [f"### {ds}", ""]
    md += [ficha(r) for r in g.itertuples()]
md += ["## Cómo se ha comprobado", "",
       f"Los datos son los publicados en el portal de datos abiertos, el geoportal y la web de Movilidad, descargados entre el 30/10/2026 y el 04/11/2026 "
       f"(siniestros: {fmt(len(df))} filas). Las pruebas se han hecho con Python (pandas y geopandas; distancias en EPSG:25830). "
       f"Las {n_auto} comprobaciones automáticas se repiten cada vez que se descargan datos nuevos; las demás ({len(reg) - n_auto}) se revisan a mano. "
       "No hemos usado ni publicado ningún dato personal: los ejemplos son identificadores de fila (_id) o valores de los campos.",
       "",
       f"El conjunto de siniestros se ha leído con la API del portal (`datastore_search`), que coincide celda a celda con el CSV publicado ({fmt(len(df))} filas). "
       "Los `_id` son los de la API; en el CSV descargable (ISO-8859-1, separado por «;», con la cabecera `UBICACIÓN` con tilde y sin `_id`), "
       "cada `_id` corresponde a la línea `_id` + 1. En la API, un campo vacío llega como nulo; en el CSV, como texto vacío.",
       "",
       "Algunas cifras (INC-008 a INC-013) dependen de nuestro método para situar las direcciones con el callejero municipal. "
       "En esos casos lo indicamos y, cuando es posible, damos una receta que se puede repetir sin nuestro código. "
       "Las cifras de INC-001 a INC-026 se han vuelto a comprobar el 04/11/2026 en una revisión independiente, con código propio y descargas nuevas. "
       "INC-027 a INC-040 salen de una revisión sistemática del 07/11/2026, con la misma lista de comprobaciones para cada conjunto (duplicados, vacíos, formatos, "
       "valores, geometrías, claves entre conjuntos, coherencia entre años y fichas); las de las capas 182, 188, 189 y 273 se han confirmado ese día en el servicio de mapas.",
       "",
       "## Gracias", "",
       f"Gracias por el trabajo del portal y por tener en cuenta estas notas. Si alguna incidencia está mal planteada, ya está corregida o tiene una explicación, "
       f"pueden escribirnos a {CONTACTO} y lo reflejaremos en el registro. Estaremos encantados de seguir colaborando como personas que reutilizan los datos y avisan de lo que encuentran.",
       ""]
INFORME.write_text("\n".join(md))
