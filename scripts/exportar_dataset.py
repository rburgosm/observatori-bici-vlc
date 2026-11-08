"""Conjunto de datos abierto y versionado: los siniestros del portal situados en el mapa (pendiente 74).

Cada publicación es una versión CERRADA: data/publicado/v<X.Y>/ guarda los ficheros tal como se publicaron (CSV,
GeoJSON, LLEGIU-ME / LÉEME y datapackage.json) y un manifest.json con el sha256, las filas, la fecha y las fuentes.
Nunca se regenera: una corrección es una versión nueva.
  v1.x  correcciones o mejoras de la geolocalización con los mismos datos de origen;
  v2.0  datos de 2026 (otra descarga del portal) o cambio de columnas.
Licencia y privacidad: docs/dataset_licencia_privacidad.md (opción A, decidida el 07/11/2026: los campos del portal tal
cual, con la coordenada; nada de atributos de personas ni de campos de OpenStreetMap, que llevarían la ODbL).

Fuente: data/processed/observatorio.sqlite (tabla siniestro = siniestros_geo.csv, con en_analisis; siniestro_via para el
codvia) y el geocodificador (geocodificar.py) para la incertidumbre, que mide con geopandas/shapely en EPSG:25830.

Uso:
  .venv/bin/python -I scripts/exportar_dataset.py --publicar 1.0 [--mes 2026-11]   crea data/publicado/v1.0/ (se para si existe)
  .venv/bin/python -I scripts/exportar_dataset.py --build      copia las versiones a web/proto/build/datos/ y el alias «ultima»
  .venv/bin/python -I scripts/exportar_dataset.py --comprobar  OK / AVISO / ERROR (lo llama también comprobar.py)
  .venv/bin/python -I scripts/exportar_dataset.py --probar     genera la versión siguiente en un temporal y dice si cambiaría
make: `make web` hace --build; `make dataset VERSION=1.1` publica una versión nueva."""
import argparse, csv, datetime, hashlib, io, json, math, re, shutil, sqlite3, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "data/publicado"
DB = ROOT / "data/processed/observatorio.sqlite"
GEO_CSV = ROOT / "data/processed/siniestros_geo.csv"
RAW_JSON = ROOT / "data/raw/siniestros/siniestros-de-trafico-2022-2025.json"
BUILD_DATOS = ROOT / "web/proto/build/datos"
BASE = "siniestros_geo"
ULTIMA = f"{BASE}_ultima"
DOMINIO = "https://observatoribicivlc.org"
CORREU = "hola@observatoribicivlc.org"
REPO = "https://github.com/rburgosm/observatori-bici-vlc"
PORTAL = "https://opendata.vlci.valencia.es"
CONJUNTO = "siniestros-de-trafico-2022-2025"
BBOX = (-0.45, 39.27, -0.27, 39.57)          # término municipal de València con pedanías (lon0, lat0, lon1, lat1), holgado

# columnas: (nombre, tipo Frictionless, descripción va, descripción es, unidad va, unidad es)
COLS = [
    ("id_portal", "integer", "Identificador de l'accident en el portal (camp _id del conjunt «Accidents de trànsit 2022-2025»). És l'únic identificador que publica el portal.",
     "Identificador del accidente en el portal (campo _id del conjunto «Accidentes de tráfico 2022-2025»). Es el único identificador que publica el portal.", None, None),
    ("fecha_hora", "datetime", "Data i hora (local), tal com la publica el portal. Els segons només hi són des de juliol de 2024; abans valen 00.", "Fecha y hora (local), tal como la publica el portal. Los segundos solo están desde julio de 2024; antes valen 00.", None, None),
    ("anyo", "year", "Any de l'accident.", "Año del accidente.", None, None),
    ("gravedad", "string", "Gravetat segons el portal. No es pot comparar entre anys: des de 2023 es compta com a ferit greu qui passa més de 24 hores a l'hospital.",
     "Gravedad según el portal. No se puede comparar entre años: desde 2023 se cuenta como herido grave a quien pasa más de 24 horas en el hospital.", None, None),
    ("tipo_accidente", "string", "Tipus d'accident segons el portal (buit si no consta). Només és fiable des de juliol de 2024: abans falta en moltes files.",
     "Tipo de accidente según el portal (vacío si no consta). Solo es fiable desde julio de 2024: antes falta en muchas filas.", None, None),
    ("vehiculos_implicados", "string", "Vehicles implicats, tal com els publica el portal (separats per comes).", "Vehículos implicados, tal como los publica el portal (separados por comas).", None, None),
    ("factores", "string", "Factors concurrents segons la policia, tal com els publica el portal (buit si no consta).", "Factores concurrentes según la policía, tal como los publica el portal (vacío si no consta).", None, None),
    ("ubicacion", "string", "Adreça escrita en el comunicat de la policia, tal com la publica el portal.", "Dirección escrita en el parte de la policía, tal como la publica el portal.", None, None),
    ("con_bici", "boolean", "Hi ha almenys una bicicleta entre els vehicles implicats.", "Hay al menos una bicicleta entre los vehículos implicados.", None, None),
    ("con_patinete", "boolean", "Hi ha almenys un patinet o un altre vehicle de mobilitat personal (VMP) entre els vehicles implicats.",
     "Hay al menos un patinete u otro vehículo de movilidad personal (VMP) entre los vehículos implicados.", None, None),
    ("metodo", "string", "Com hem situat l'accident: cruce (cruïlla de dos carrers), portal (número de portal), portal_cercano (número de portal proper, de la mateixa banda i a 10 números o menys), "
     "cruce_fallo i numero_fallo (no s'ha pogut situar) o solo_calle (l'adreça només dona el carrer i no se situa).",
     "Cómo hemos situado el accidente: cruce (cruce de dos calles), portal (número de portal), portal_cercano (número de portal cercano, del mismo lado y a 10 números o menos), "
     "cruce_fallo y numero_fallo (no se ha podido situar) o solo_calle (la dirección solo da la calle y no se sitúa).", None, None),
    ("lon", "number", "Longitud del punt: la cruïlla o el número de portal citat en el comunicat, no un domicili. Buit si no s'ha pogut situar.",
     "Longitud del punto: el cruce o el número de portal citado en el parte, no un domicilio. Vacío si no se ha podido situar.", "graus (WGS 84, EPSG:4326)", "grados (WGS 84, EPSG:4326)"),
    ("lat", "number", "Latitud del punt.", "Latitud del punto.", "graus (WGS 84, EPSG:4326)", "grados (WGS 84, EPSG:4326)"),
    ("incertidumbre_m", "integer", "Radi aproximat al voltant del punt on pot estar el lloc que descriu l'adreça. No és un error mesurat: és una estimació segons el mètode (vegeu el LLEGIU-ME).",
     "Radio aproximado alrededor del punto en el que puede estar el lugar que describe la dirección. No es un error medido: es una estimación según el método (ver el LÉEME).", "metres", "metros"),
    ("codvia", "integer", "Codi del carrer en el carrerer municipal (codvia): el carrer del portal o el primer carrer de la cruïlla. Buit si el nom no casa amb cap carrer o casa amb més d'un.",
     "Código de la calle en el callejero municipal (codvia): la calle del portal o la primera calle del cruce. Vacío si el nombre no casa con ninguna calle o casa con más de una.", None, None),
    ("codvia_2", "integer", "Codi del segon carrer de la cruïlla (només en les cruïlles).", "Código de la segunda calle del cruce (solo en los cruces).", None, None),
    ("duplicado_de", "integer", "Si la fila és idèntica a una altra en tots els camps del portal llevat de l'identificador, l'id_portal de la primera. Buit en la resta.",
     "Si la fila es idéntica a otra en todos los campos del portal salvo el identificador, el id_portal de la primera. Vacío en el resto.", None, None),
    ("mismo_lugar_y_hora", "boolean", "Hi ha una altra fila amb la mateixa data, hora i adreça però algun altre camp diferent: pot ser el mateix accident registrat dues vegades o dos accidents.",
     "Hay otra fila con la misma fecha, hora y dirección pero algún otro campo distinto: puede ser el mismo accidente registrado dos veces o dos accidentes.", None, None),
    ("fila_incompleta", "boolean", "La fila ve trencada del portal: els vehicles són només «[» o l'adreça porta «nan» en lloc d'un carrer o d'un número.",
     "La fila viene rota del portal: los vehículos son solo «[» o la dirección lleva «nan» en lugar de una calle o de un número.", None, None),
    ("en_analisis", "boolean", "L'observatori la fa servir en les xifres: anys complets i sense duplicats exactes.", "El observatorio la usa en las cifras: años completos y sin duplicados exactos.", None, None),
    ("incidencias", "string", "Codis dels errors detectats en les dades del portal que afecten la fila, separats per «;» (vegeu el LLEGIU-ME).",
     "Códigos de los errores detectados en los datos del portal que afectan a la fila, separados por «;» (ver el LÉEME).", None, None),
]
NOMBRES = [c[0] for c in COLS]
INC = {"INC-001": ("fila idèntica a una altra llevat del _id (duplicat exacte)", "fila idéntica a otra salvo el _id (duplicado exacto)"),
       "INC-002": ("mateixa data, hora i adreça que una altra fila, amb algun camp diferent", "misma fecha, hora y dirección que otra fila, con algún campo distinto"),
       "INC-003": ("vehicles implicats buits o tallats («[»)", "vehículos implicados vacíos o cortados («[»)"),
       "INC-004": ("accident de l'1 de gener de 2026 dins del conjunt 2022-2025", "accidente del 1 de enero de 2026 dentro del conjunto 2022-2025"),
       "INC-027": ("adreça amb «nan» o cruïlla d'un carrer amb si mateix", "dirección con «nan» o cruce de una calle consigo misma")}


def vtupla(v): return tuple(int(x) for x in v.split("."))


def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def nombre(version, mes): return f"{BASE}_v{version}_{mes}"


def versiones():
    """Manifiestos de las versiones publicadas, de la más antigua a la más nueva."""
    ms = [json.loads(p.read_text()) for p in PUB.glob("v*/manifest.json")]
    return sorted(ms, key=lambda m: vtupla(m["version"]))


# ---------------------------------------------------------------- filas
def filas():
    """DataFrame con las columnas de COLS, una fila por siniestro del portal (todas, situadas o no), y metadatos."""
    import numpy as np, pandas as pd
    sys.path.insert(0, str(ROOT / "scripts"))
    import geocodificar as GC, lugares as LG
    import geopandas as gpd, shapely
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    s = pd.read_sql("SELECT id, fecha, gravedad, tipo, unidades, factores, ubicacion, metodo, lon, lat, dist_ejes_m, en_analisis FROM siniestro ORDER BY id", con)
    sv = pd.read_sql("SELECT siniestro_id, codvia, rol FROM siniestro_via", con)
    meta = dict(con.execute("SELECT clave, valor FROM meta").fetchall())
    con.close()
    txt = lambda x: "" if x is None or (isinstance(x, float) and math.isnan(x)) else str(x)
    for c in ("tipo", "unidades", "factores", "ubicacion"): s[c] = s[c].map(txt)

    # campos del portal; «NULL» (texto) y vacío son lo mismo: dato desconocido (INC-006), se publica vacío
    d = pd.DataFrame({"id_portal": s.id})
    d["fecha_hora"] = s.fecha.str.replace(" ", "T")                # con los segundos, como el portal (desde julio de 2024)
    d["anyo"] = s.fecha.str.slice(0, 4).astype(int)
    d["gravedad"] = s.gravedad
    d["tipo_accidente"] = s.tipo.where(s.tipo.str.strip().str.upper() != "NULL", "")
    d["vehiculos_implicados"] = s.unidades
    d["factores"] = s.factores.where(s.factores.str.strip().str.upper() != "NULL", "")
    d["ubicacion"] = s.ubicacion
    d["con_bici"] = s.unidades.str.contains("BICICLETA")
    d["con_patinete"] = s.unidades.str.contains("VMP")          # mismo criterio que lugares.bici_vmp
    d["metodo"] = s.metodo
    d["lon"], d["lat"] = s.lon, s.lat

    # incertidumbre (m): cruce = R del nudo (lugares.R) + la mitad de la separación entre ejes; portal = distancia del portal
    # al eje de su calle + media separación típica entre portales; portal cercano = además, la distancia estimada hasta
    # el número escrito (|n − m| / 2 portales de la misma acera)
    pts = gpd.GeoSeries(gpd.points_from_xy(s.lon, s.lat), crs=4326).to_crs(25830)
    por = gpd.GeoDataFrame([{"codvia": cv, "num": n, "geometry": shapely.Point(pt)} for cv, xs in GC.num_por_via.items() for n, pt in xs], crs=4326).to_crs(25830)
    por = por.drop_duplicates(["codvia", "num"]).sort_values(["codvia", "num"])
    por["par"] = por.num % 2; por["x"] = por.geometry.x; por["y"] = por.geometry.y
    g = por.groupby(["codvia", "par"])
    paso = np.hypot(g.x.diff(), g.y.diff())
    SEP = float(paso[g.num.diff() == 2].median())                 # entre portales consecutivos de la misma acera (n, n + 2)
    inc = pd.Series(np.nan, index=s.index)
    cr = s.metodo == "cruce"
    inc[cr] = LG.R + s.dist_ejes_m[cr].fillna(0) / 2
    for i in s.index[s.metodo.isin(["portal", "portal_cercano"])]:
        m = re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$", s.ubicacion[i].strip()); n = int(m.group(2))
        hallado = None
        for cv in GC.codvias(m.group(1)):                        # el mismo recorrido que geocodificar.numero
            if (cv, n) in GC.portal: hallado = (cv, n, GC.portal[(cv, n)]); break
            cand = [(abs(k - n), pt, k) for k, pt in GC.num_por_via.get(cv, []) if k % 2 == n % 2 and abs(k - n) <= 10]
            if cand: _, pt, k = min(cand); hallado = (cv, k, pt); break
        cv, k, pt = hallado
        assert abs(pt[0] - s.lon[i]) < 1e-6 and abs(pt[1] - s.lat[i]) < 1e-6, f"el portal de {s.id[i]} no coincide con el geocodificador"
        inc[i] = GC.geom[cv].distance(pts[i]) + SEP / 2 + abs(n - k) / 2 * SEP
    d["incertidumbre_m"] = inc.map(lambda x: pd.NA if pd.isna(x) else int(math.ceil(x - 1e-9))).astype("Int64")

    # codvia por la dirección escrita (siniestro_via de la base: la misma asignación que las fichas de calle), en el orden
    # en que la dirección nombra las calles
    vias = sv.groupby("siniestro_id").codvia.apply(set).to_dict()
    c1, c2, mismo = [], [], []
    for r in s.itertuples():
        ub = r.ubicacion.strip(); vs = vias.get(r.id, set())
        partes = ub.split(" cruce ", 1) if " cruce " in ub else [re.sub(r"\s+\d+\s*[A-Z]*$", "", re.sub(r"\s+S/N$", "", ub))]
        orden = []
        for p in partes:
            for cv in sorted(c for c in GC.codvias(p) if c in vs):
                if cv not in orden: orden.append(cv); break
        orden += sorted(vs - set(orden))
        c1.append(orden[0] if orden else pd.NA); c2.append(orden[1] if len(orden) > 1 and " cruce " in ub else pd.NA)
        mismo.append(" cruce " in ub and GC.norm(partes[0]) == GC.norm(partes[1]))
    d["codvia"] = pd.array(c1, dtype="Int64"); d["codvia_2"] = pd.array(c2, dtype="Int64")

    # marcas de calidad (data/processed/incidencias_datos.csv)
    campos = ["fecha", "gravedad", "tipo", "unidades", "factores", "ubicacion"]
    primero = s.groupby(campos).id.transform("min")
    d["duplicado_de"] = primero.where(primero != s.id).astype("Int64")
    clave = s.fecha + "|" + s.ubicacion                           # sin contar los duplicados exactos (que heredan la marca)
    d["mismo_lugar_y_hora"] = clave.map(clave[d.duplicado_de.isna()].value_counts()) > 1
    corto = s.unidades.str.strip() == "["
    nan_ub = s.ubicacion.str.contains(r"(?:^|\s)nan(?:\s|$)", regex=True)
    d["fila_incompleta"] = corto | nan_ub
    d["en_analisis"] = s.en_analisis.astype(bool)
    marcas = {"INC-001": d.duplicado_de.notna(), "INC-002": d.mismo_lugar_y_hora, "INC-003": corto,
              "INC-004": d.anyo > 2025, "INC-027": nan_ub | pd.Series(mismo, index=s.index)}
    d["incidencias"] = [";".join(k for k, v in marcas.items() if v[i]) for i in s.index]
    info = {"sep_portales_m": round(SEP, 1), "radio_cruce_m": LG.R, "fecha_descarga": meta["fecha_descarga"],
            "conjunto": meta["conjunto_siniestros"], "marcas": {k: int(v.sum()) for k, v in marcas.items()}}
    return d[NOMBRES], info


# ---------------------------------------------------------------- escritura
def _v(x, tipo):
    import pandas as pd
    if x is None or x is pd.NA or (isinstance(x, float) and math.isnan(x)): return ""
    if tipo == "boolean": return "true" if x else "false"
    if tipo == "number": return f"{x:.6f}"
    return str(x)


def csv_bytes(d):
    tipos = {c[0]: c[1] for c in COLS}
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)     # RFC 4180
    w.writerow(NOMBRES)
    for r in d.itertuples(index=False):
        w.writerow([_v(x, tipos[c]) for c, x in zip(NOMBRES, r)])
    return ("﻿" + b.getvalue()).encode("utf-8")                         # con BOM, como el CSV del mapa (Excel)


def geojson_bytes(d):
    """RFC 7946 (WGS 84, sin «crs»): un Feature por accidente situado; propiedades = las columnas salvo lon y lat."""
    import pandas as pd
    tipos = {c[0]: c[1] for c in COLS}
    props = [c for c in NOMBRES if c not in ("lon", "lat")]
    def js(x, t):
        if x is None or x is pd.NA or (isinstance(x, float) and math.isnan(x)): return None
        if t == "boolean": return bool(x)
        if t in ("integer", "year"): return int(x)
        return str(x)
    feats = []
    for r in d[d.lon.notna()].itertuples(index=False):
        r = r._asdict()
        feats.append('{"type":"Feature","id":%d,"geometry":{"type":"Point","coordinates":[%.6f,%.6f]},"properties":%s}' % (
            r["id_portal"], r["lon"], r["lat"], json.dumps({c: js(r[c], tipos[c]) for c in props}, ensure_ascii=False, separators=(",", ":"))))
    return ('{"type":"FeatureCollection","features":[\n' + ",\n".join(feats) + "\n]}\n").encode("utf-8")


def datapackage(version, mes, n_csv, n_geo, info, sha):
    base = nombre(version, mes)
    def campos(geo):
        fs = []
        for n, t, va, es, uva, ues in COLS:
            if geo and n in ("lon", "lat"): continue
            f = {"name": n, "type": t, "description": f"{va} / {es}"}
            if t == "datetime": f["format"] = "%Y-%m-%dT%H:%M:%S"
            if t == "boolean": f["trueValues"], f["falseValues"] = ["true"], ["false"]
            if uva: f["unit"] = f"{uva} / {ues}"
            fs.append(f)
        return fs
    return {
        "profile": "data-package",
        "name": "observatori-bici-patinet-valencia-accidents-geolocalitzats",
        "id": f"{DOMINIO}/datos/{base}_datapackage.json",
        "title": "Accidents de trànsit de València geolocalitzats, 2022-2025 / Accidentes de tráfico de València geolocalizados, 2022-2025",
        "description": ("Tots els accidents de trànsit del conjunt «Accidents de trànsit 2022-2025» del portal de dades obertes de l'Ajuntament de València, "
                        "amb la seua posició en el mapa (situada amb el carrerer municipal), el mètode i la incertesa de cada posició, el codi de carrer, "
                        "si hi ha bici o patinet i marques de qualitat. Sense dades de les persones implicades: està prohibit reidentificar persones. / "
                        "Todos los accidentes de tráfico del conjunto «Accidentes de tráfico 2022-2025» del portal de datos abiertos del Ayuntamiento de València, "
                        "con su posición en el mapa (situada con el callejero municipal), el método y la incertidumbre de cada posición, el código de calle, "
                        "si hay bici o patinete y marcas de calidad. Sin datos de las personas implicadas: está prohibido reidentificar personas."),
        "homepage": f"{DOMINIO}/dades/#accidents-geo",
        "version": version,
        "created": f"{datetime.date.today().isoformat()}T00:00:00Z",
        "keywords": ["seguretat viària", "seguridad vial", "accidents de trànsit", "accidentes de tráfico", "bicicleta", "patinet", "patinete", "VMP", "geocodificació", "geocodificación", "València"],
        "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/", "title": "Creative Commons Attribution 4.0 International"}],
        "contributors": [{"title": "Observatori de la bici i el patinet de València / Observatorio de la bici y el patinete de València", "email": CORREU, "path": DOMINIO, "role": "author"},
                         {"title": "Ajuntament de València", "path": PORTAL, "role": "publisher"}],
        "sources": [
            {"title": f"Font de les dades: Ajuntament de València – Dades Obertes. Accidents de trànsit 2022-2025 ({info['conjunto']}), obtinguts el {info['fecha_descarga']} / "
                      f"Fuente de los datos: Ajuntament de València – Dades Obertes. Accidentes de tráfico 2022-2025 ({info['conjunto']}), obtenidos el {info['fecha_descarga']}",
             "path": f"{PORTAL}/dataset/{info['conjunto']}"},
            {"title": "Ajuntament de València – Dades Obertes: vies, eixos de carrer i portals (carrerer) / vías, ejes de calle y portales (callejero)",
             "path": "https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer"}],
        "resources": [
            {"name": "accidents-geolocalitzats-csv", "path": f"{base}.csv", "profile": "tabular-data-resource",
             "title": "Tots els accidents (també els no situats) / Todos los accidentes (también los no situados)",
             "format": "csv", "mediatype": "text/csv", "encoding": "utf-8", "bytes": sha[f"{base}.csv"]["bytes"], "hash": "sha256:" + sha[f"{base}.csv"]["sha256"],
             "dialect": {"delimiter": ",", "lineTerminator": "\r\n", "quoteChar": "\"", "doubleQuote": True, "header": True},
             "schema": {"fields": campos(False), "missingValues": [""], "primaryKey": ["id_portal"]}},
            {"name": "accidents-geolocalitzats-geojson", "path": f"{base}.geojson", "profile": "data-resource",
             "title": "Només els accidents situats en el mapa / Solo los accidentes situados en el mapa",
             "description": "GeoJSON (RFC 7946, WGS 84). Les propietats són les columnes del CSV llevat de lon i lat. / Las propiedades son las columnas del CSV salvo lon y lat.",
             "format": "geojson", "mediatype": "application/geo+json", "encoding": "utf-8",
             "bytes": sha[f"{base}.geojson"]["bytes"], "hash": "sha256:" + sha[f"{base}.geojson"]["sha256"]},
            {"name": "llegiu-me-leeme", "path": f"{base}_LLEGIU-ME_LEEME.txt", "profile": "data-resource", "title": "LLEGIU-ME / LÉEME",
             "format": "txt", "mediatype": "text/plain", "encoding": "utf-8",
             "bytes": sha[f"{base}_LLEGIU-ME_LEEME.txt"]["bytes"], "hash": "sha256:" + sha[f"{base}_LLEGIU-ME_LEEME.txt"]["sha256"]}],
    }


def _num(n): return f"{n:,}".replace(",", ".")


def _pc(x, d=1): return f"{100 * x:.{d}f}".replace(".", ",") + " %"


def readme(version, mes, d, info, historia):
    base = nombre(version, mes)
    n, ng = len(d), int(d.lon.notna().sum())
    bv = d.con_bici | d.con_patinete
    cob = d.groupby("anyo").lon.apply(lambda x: x.notna().mean())
    cob_bv = d[bv].groupby("anyo").lon.apply(lambda x: x.notna().mean())
    años = [a for a in cob.index if a <= 2025]
    met = d.metodo.value_counts()
    inc_med = d.groupby("metodo").incertidumbre_m.median()
    fd = info["fecha_descarga"]; fd_es = f"{fd[8:10]}/{fd[5:7]}/{fd[:4]}"
    tabla = "\n".join(f"| `{c[0]}` | {c[1]} | {c[2]}{' Unitat: ' + c[4] + '.' if c[4] else ''} |" for c in COLS)
    tabla_es = "\n".join(f"| `{c[0]}` | {c[1]} | {c[3]}{' Unidad: ' + c[5] + '.' if c[5] else ''} |" for c in COLS)
    cob_va = "; ".join(f"{a}: {_pc(cob[a], 0)} (bici o patinet: {_pc(cob_bv[a], 0)})" for a in años)
    cob_es = "; ".join(f"{a}: {_pc(cob[a], 0)} (bici o patinete: {_pc(cob_bv[a], 0)})" for a in años)
    inc_va = "\n".join(f"- `{k}` ({_num(info['marcas'][k])} files): {v[0]}." for k, v in INC.items())
    inc_es = "\n".join(f"- `{k}` ({_num(info['marcas'][k])} filas): {v[1]}." for k, v in INC.items())
    hist_va = "\n".join(f"- v{h['version']} ({h['fecha']}): {h['nota_va']}" for h in historia)
    hist_es = "\n".join(f"- v{h['version']} ({h['fecha']}): {h['nota_es']}" for h in historia)
    sep, rc = str(info["sep_portales_m"]).replace(".", ","), info["radio_cruce_m"]
    m = lambda k: _num(int(met.get(k, 0)))
    im = lambda k: _num(int(inc_med.get(k, 0)))
    return f"""ACCIDENTS DE TRÀNSIT DE VALÈNCIA GEOLOCALITZATS, 2022-2025 — versió {version} ({mes})
ACCIDENTES DE TRÁFICO DE VALÈNCIA GEOLOCALIZADOS, 2022-2025 — versión {version} ({mes})

Observatori de la bici i el patinet de València · {DOMINIO}/dades/#accidents-geo
(Castellano más abajo.)

==============================================================================
VALENCIÀ
==============================================================================

## Què és

Tots els accidents de trànsit que publica l'Ajuntament de València en el conjunt «Accidents de trànsit 2022-2025»
del seu portal de dades obertes ({_num(n)} files), amb el lloc on els hem situat en el mapa. El portal només dona
l'adreça escrita en el comunicat de la policia («C/ X cruce C/ Y», «AV X 46»); nosaltres la convertim en coordenades
amb el carrerer municipal. N'hem pogut situar {_num(ng)}, el {_pc(ng / n)}.

Cada fila diu també com l'hem situada (`metodo`), quina incertesa té la posició (`incertidumbre_m`), el codi del
carrer en el carrerer (`codvia`), si hi ha bici o patinet i si la fila té algun error que ve del portal.

Fitxers:
- `{base}.csv`: tots els accidents, també els que no s'han pogut situar (sense coordenades). CSV (RFC 4180), UTF-8
  amb BOM, separat per comes.
- `{base}.geojson`: només els {_num(ng)} accidents situats, en GeoJSON (RFC 7946, WGS 84).
- `{base}_datapackage.json`: descriptor Frictionless Data Package (columnes, tipus, unitats, llicència, fonts i sha256).
- `{ULTIMA}.csv` i `{ULTIMA}.geojson` (en la web): sempre la versió més nova.

## Llicència i atribució

CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.ca). Pots copiar les dades, redistribuir-les, transformar-les
i fer-les servir per a qualsevol fi, també comercial, si cites la font.

Font de les dades: Ajuntament de València – Dades Obertes ({PORTAL}). Conjunts «Accidents de trànsit 2022-2025»
({CONJUNTO}), «Vies», «Eixos de carrer» i «Portals dels carrers», CC BY 4.0, obtinguts el {fd_es}.
Dades modificades per l'Observatori de la bici i el patinet: s'hi afigen les coordenades situades amb el carrerer
municipal, el mètode i la incertesa de la posició, el codi de carrer, les marques de bici i patinet i les marques de
qualitat; «NULL» es publica com a camp buit. L'Ajuntament de València no participa en aquest treball ni l'avala.

## Privacitat

- No hi ha cap dada de les persones implicades: ni edat, ni sexe, ni noms, ni matrícules. Una fila és un accident.
- La coordenada és la de la cruïlla o la del número de portal citat en el comunicat, no un domicili.
- Està prohibit reidentificar persones creuant aquestes dades amb altres fonts, com en la política d'ús del portal.
- Si un registre t'afecta i vols que el revisem, escriu-nos a {CORREU}. Si l'Ajuntament retira o corregix un
  registre, la versió següent el retira o el corregix igual.

## Diccionari de dades

| Columna | Tipus | Què és |
|---|---|---|
{tabla}

Codis de la columna `incidencias` (errors del portal que hem comunicat a l'Ajuntament):
{inc_va}

## Com l'hem fet

Amb el carrerer municipal (vies, eixos de carrer i portals) i sense cap dada d'OpenStreetMap. Mètode complet:
{DOMINIO}/metode/ i codi obert: {REPO}

- Cruïlla (`cruce`, {m('cruce')} files): el punt més pròxim entre els eixos dels dos carrers, si estan a 40 m o menys.
- Portal (`portal`, {m('portal')} files): el punt del número de portal en el carrerer.
- Portal proper (`portal_cercano`, {m('portal_cercano')} files): si el número no existeix, el més pròxim de la mateixa
  banda del carrer, a 10 números o menys.
- No situats: `cruce_fallo` ({m('cruce_fallo')}; els carrers no es toquen o no es troben), `numero_fallo`
  ({m('numero_fallo')}; el carrer no es troba o no té portals pròxims) i `solo_calle` ({m('solo_calle')}; l'adreça només
  dona el carrer).

`incertidumbre_m` és una estimació, no un error mesurat, del radi on pot estar el lloc que descriu l'adreça:
- cruïlla: {rc} m (el radi que fem servir per a una cruïlla) més la meitat de la distància entre els eixos;
- portal: la distància del portal a l'eix del carrer (l'accident és en la calçada, no en la porta) més la meitat de la
  separació típica entre dos portals seguits de la mateixa banda ({sep} m, la mediana del carrerer);
- portal proper: el mateix, més la distància estimada fins al número escrit.
Medianes: cruïlla {im('cruce')} m, portal {im('portal')} m, portal proper {im('portal_cercano')} m. Les cruïlles molt grans
(places i rotondes) poden tindre més incertesa de la que diu la columna.

## Limitacions

- Mostra on es registren més accidents, no on és més perillós: no sabem quanta gent passa per cada lloc.
- Hem pogut situar el {_pc(ng / n, 0)} dels accidents, però la part situada canvia amb l'any:
  {cob_va}.
  Les tendències fetes només amb els accidents situats estan esbiaixades: per a seguir-les, cal fer servir totes les
  files o corregir per la cobertura de cada any.
- La gravetat no es pot comparar entre anys (des de 2023 es compta com a ferit greu qui passa més de 24 hores a
  l'hospital). El tipus d'accident i els factors només són complets des de juliol de 2024.
- Fins a mitjan 2024, en molts comunicats no hi consta la persona atropellada.
- Les 17 files de l'1 de gener de 2026 venen dins del conjunt 2022-2025 del portal; no entren en les xifres de
  l'observatori (`en_analisis` = false).
- `id_portal` és el `_id` del portal en la descàrrega del {fd_es}. És l'únic identificador que hi ha. Si el portal
  els renumera en una publicació futura, la versió següent dirà com es corresponen.

## Versions

Cada versió és tancada: el fitxer d'una versió no canvia mai. Una correcció és una versió nova.
- v1.x: correccions o millores de la geolocalització amb les mateixes dades d'origen.
- v2.0: dades de 2026 (una altra descàrrega del portal) o canvi de columnes.
Totes les versions estan en {DOMINIO}/dades/#accidents-geo i en el registre de canvis ({DOMINIO}/sobre/#canvis).

{hist_va}

## Com citar-ho

Observatori de la bici i el patinet de València ({mes[:4]}). Accidents de trànsit de València geolocalitzats,
2022-2025, versió {version}. {DOMINIO}/datos/{base}.csv. Dades de l'Ajuntament de València – Dades Obertes
(CC BY 4.0), modificades per l'observatori.


==============================================================================
CASTELLANO
==============================================================================

## Qué es

Todos los accidentes de tráfico que publica el Ayuntamiento de València en el conjunto «Accidentes de tráfico
2022-2025» de su portal de datos abiertos ({_num(n)} filas), con el lugar donde los hemos situado en el mapa. El portal
solo da la dirección escrita en el parte de la policía («C/ X cruce C/ Y», «AV X 46»); nosotros la convertimos en
coordenadas con el callejero municipal. Hemos podido situar {_num(ng)}, el {_pc(ng / n)}.

Cada fila dice también cómo la hemos situado (`metodo`), qué incertidumbre tiene la posición (`incertidumbre_m`), el
código de la calle en el callejero (`codvia`), si hay bici o patinete y si la fila tiene algún error que viene del portal.

Ficheros:
- `{base}.csv`: todos los accidentes, también los que no se han podido situar (sin coordenadas). CSV (RFC 4180),
  UTF-8 con BOM, separado por comas.
- `{base}.geojson`: solo los {_num(ng)} accidentes situados, en GeoJSON (RFC 7946, WGS 84).
- `{base}_datapackage.json`: descriptor Frictionless Data Package (columnas, tipos, unidades, licencia, fuentes y sha256).
- `{ULTIMA}.csv` y `{ULTIMA}.geojson` (en la web): siempre la versión más nueva.

## Licencia y atribución

CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.es). Puedes copiar los datos, redistribuirlos, transformarlos
y usarlos para cualquier fin, también comercial, si citas la fuente.

Fuente de los datos: Ajuntament de València – Dades Obertes ({PORTAL}). Conjuntos «Accidentes de tráfico 2022-2025»
({CONJUNTO}), «Vías», «Ejes de calle» y «Portales de las calles», CC BY 4.0, obtenidos el {fd_es}.
Datos modificados por el Observatorio de la bici y el patinete: se añaden las coordenadas situadas con el callejero
municipal, el método y la incertidumbre de la posición, el código de calle, las marcas de bici y patinete y las marcas
de calidad; «NULL» se publica como campo vacío. El Ajuntament de València no participa en este trabajo ni lo avala.

## Privacidad

- No hay ningún dato de las personas implicadas: ni edad, ni sexo, ni nombres, ni matrículas. Una fila es un accidente.
- La coordenada es la del cruce o la del número de portal citado en el parte, no un domicilio.
- Está prohibido reidentificar personas cruzando estos datos con otras fuentes, como en la política de uso del portal.
- Si un registro te afecta y quieres que lo revisemos, escríbenos a {CORREU}. Si el Ayuntamiento retira o corrige un
  registro, la versión siguiente lo retira o lo corrige igual.

## Diccionario de datos

| Columna | Tipo | Qué es |
|---|---|---|
{tabla_es}

Códigos de la columna `incidencias` (errores del portal que hemos comunicado al Ayuntamiento):
{inc_es}

## Cómo lo hemos hecho

Con el callejero municipal (vías, ejes de calle y portales) y sin ningún dato de OpenStreetMap. Método completo:
{DOMINIO}/metode/ y código abierto: {REPO}

- Cruce (`cruce`, {m('cruce')} filas): el punto más próximo entre los ejes de las dos calles, si están a 40 m o menos.
- Portal (`portal`, {m('portal')} filas): el punto del número de portal en el callejero.
- Portal cercano (`portal_cercano`, {m('portal_cercano')} filas): si el número no existe, el más próximo del mismo lado
  de la calle, a 10 números o menos.
- No situados: `cruce_fallo` ({m('cruce_fallo')}; las calles no se tocan o no se encuentran), `numero_fallo`
  ({m('numero_fallo')}; la calle no se encuentra o no tiene portales próximos) y `solo_calle` ({m('solo_calle')}; la
  dirección solo da la calle).

`incertidumbre_m` es una estimación, no un error medido, del radio en el que puede estar el lugar que describe la dirección:
- cruce: {rc} m (el radio que usamos para un cruce) más la mitad de la distancia entre los ejes;
- portal: la distancia del portal al eje de la calle (el accidente está en la calzada, no en la puerta) más la mitad de
  la separación típica entre dos portales seguidos del mismo lado ({sep} m, la mediana del callejero);
- portal cercano: lo mismo, más la distancia estimada hasta el número escrito.
Medianas: cruce {im('cruce')} m, portal {im('portal')} m, portal cercano {im('portal_cercano')} m. Los cruces muy grandes
(plazas y rotondas) pueden tener más incertidumbre de la que dice la columna.

## Limitaciones

- Muestra dónde se registran más accidentes, no dónde es más peligroso: no sabemos cuánta gente pasa por cada lugar.
- Hemos podido situar el {_pc(ng / n, 0)} de los accidentes, pero la parte situada cambia con el año:
  {cob_es}.
  Las tendencias hechas solo con los accidentes situados están sesgadas: para seguirlas, hay que usar todas las filas
  o corregir por la cobertura de cada año.
- La gravedad no se puede comparar entre años (desde 2023 se cuenta como herido grave a quien pasa más de 24 horas en
  el hospital). El tipo de accidente y los factores solo están completos desde julio de 2024.
- Hasta mediados de 2024, en muchos partes no consta la persona atropellada.
- Las 17 filas del 1 de enero de 2026 vienen dentro del conjunto 2022-2025 del portal; no entran en las cifras del
  observatorio (`en_analisis` = false).
- `id_portal` es el `_id` del portal en la descarga del {fd_es}. Es el único identificador que hay. Si el portal los
  renumera en una publicación futura, la versión siguiente dirá cómo se corresponden.

## Versiones

Cada versión es cerrada: el fichero de una versión no cambia nunca. Una corrección es una versión nueva.
- v1.x: correcciones o mejoras de la geolocalización con los mismos datos de origen.
- v2.0: datos de 2026 (otra descarga del portal) o cambio de columnas.
Todas las versiones están en {DOMINIO}/dades/#accidents-geo y en el registro de cambios ({DOMINIO}/sobre/#canvis).

{hist_es}

## Cómo citarlo

Observatorio de la bici y el patinete de València ({mes[:4]}). Accidentes de tráfico de València geolocalizados,
2022-2025, versión {version}. {DOMINIO}/datos/{base}.csv. Datos del Ayuntamiento de València – Dades Obertes
(CC BY 4.0), modificados por el observatorio.
""".encode("utf-8")


def generar(dest, version, mes, nota_va, nota_es):
    """Escribe en dest/ los cuatro ficheros de la versión y el manifest.json. Devuelve el manifiesto."""
    d, info = filas()
    base = nombre(version, mes)
    dest.mkdir(parents=True, exist_ok=True)
    historia = [{"version": m["version"], "fecha": m["fecha"], "nota_va": m["nota_va"], "nota_es": m["nota_es"]} for m in versiones()
                if vtupla(m["version"]) < vtupla(version)]
    historia.append({"version": version, "fecha": datetime.date.today().isoformat(), "nota_va": nota_va, "nota_es": nota_es})
    fich = {f"{base}.csv": csv_bytes(d), f"{base}.geojson": geojson_bytes(d), f"{base}_LLEGIU-ME_LEEME.txt": readme(version, mes, d, info, historia)}
    sha = {k: {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)} for k, b in fich.items()}
    n_geo = int(d.lon.notna().sum())
    dp = (json.dumps(datapackage(version, mes, len(d), n_geo, info, sha), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fich[f"{base}_datapackage.json"] = dp
    sha[f"{base}_datapackage.json"] = {"sha256": hashlib.sha256(dp).hexdigest(), "bytes": len(dp)}
    for k, b in fich.items(): (dest / k).write_bytes(b)
    man = {"version": version, "mes": mes, "fecha": datetime.date.today().isoformat(), "nombre": base,
           "filas_csv": len(d), "features_geojson": n_geo, "columnas": NOMBRES,
           "ficheros": sha, "nota_va": nota_va, "nota_es": nota_es,
           "fuentes": {"conjunto": info["conjunto"], "fecha_descarga": info["fecha_descarga"],
                       RAW_JSON.relative_to(ROOT).as_posix(): sha256(RAW_JSON), GEO_CSV.relative_to(ROOT).as_posix(): sha256(GEO_CSV)},
           "parametros": {"sep_portales_m": info["sep_portales_m"], "radio_cruce_m": info["radio_cruce_m"]}, "marcas": info["marcas"],
           "cobertura": {str(a): round(float(v), 4) for a, v in d[d.anyo <= 2025].groupby("anyo").lon.apply(lambda x: x.notna().mean()).items()}}
    (dest / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")
    return man


# ---------------------------------------------------------------- web
def construir_build():
    """Copia cada versión cerrada a build/datos/ (los mismos bytes) y el alias «ultima» (CSV y GeoJSON de la más nueva)."""
    vs = versiones()
    if not vs: print("exportar_dataset: ninguna versión publicada en data/publicado/"); return
    BUILD_DATOS.mkdir(parents=True, exist_ok=True)
    for m in vs:
        for f in m["ficheros"]:
            src, dst = PUB / f"v{m['version']}" / f, BUILD_DATOS / f
            if not dst.exists() or dst.read_bytes() != src.read_bytes(): shutil.copyfile(src, dst)
    u = vs[-1]
    for ext in ("csv", "geojson"):
        src, dst = PUB / f"v{u['version']}" / f"{u['nombre']}.{ext}", BUILD_DATOS / f"{ULTIMA}.{ext}"
        if not dst.exists() or dst.read_bytes() != src.read_bytes(): shutil.copyfile(src, dst)
    print(f"exportar_dataset: {len(vs)} versión(es) en web/proto/build/datos/; «{ULTIMA}» = v{u['version']}")


def info_web():
    """Para la página /dades/: [{version, fecha, mes, filas, features, ficheros: {ext: (nombre, bytes)}}], de la más nueva a la más vieja."""
    out = []
    for m in reversed(versiones()):
        b = m["nombre"]; F = m["ficheros"]
        out.append({"version": m["version"], "fecha": m["fecha"], "mes": m["mes"], "filas": m["filas_csv"], "features": m["features_geojson"],
                    "nota_va": m["nota_va"], "nota_es": m["nota_es"], "descarga": m["fuentes"]["fecha_descarga"], "cobertura": m["cobertura"],
                    "ficheros": {"csv": (f"{b}.csv", F[f"{b}.csv"]["bytes"]), "geojson": (f"{b}.geojson", F[f"{b}.geojson"]["bytes"]),
                                 "txt": (f"{b}_LLEGIU-ME_LEEME.txt", F[f"{b}_LLEGIU-ME_LEEME.txt"]["bytes"]),
                                 "json": (f"{b}_datapackage.json", F[f"{b}_datapackage.json"]["bytes"])}})
    return out


# ---------------------------------------------------------------- comprobaciones
def comprobaciones():
    """[(nivel, texto)]: versiones cerradas intactas (sha256 del manifiesto), «ultima» = la más nueva en build/, la copia
    del build idéntica, filas y coordenadas coherentes, y aviso si los datos de origen han cambiado desde la última."""
    out = []
    vs = versiones()
    if not vs: return [("AVISO", "dataset: ninguna versión publicada en data/publicado/ (pendiente 74)")]
    for m in vs:
        carpeta = PUB / f"v{m['version']}"
        malos = [f for f, h in m["ficheros"].items() if not (carpeta / f).exists() or sha256(carpeta / f) != h["sha256"]]
        out.append(("ERROR" if malos else "OK", f"dataset v{m['version']}: {'CAMBIADOS o ausentes ' + str(malos) + ' (una versión cerrada no se regenera: publicar una nueva)' if malos else str(len(m['ficheros'])) + ' ficheros con el sha256 del manifiesto'}"))
        nombres = {f for f in m["ficheros"]}
        if not all(f.startswith(m["nombre"]) for f in nombres) or m["nombre"] != nombre(m["version"], m["mes"]):
            out.append(("ERROR", f"dataset v{m['version']}: nombres de fichero sin versión y mes"))
        extra = sorted(p.name for p in carpeta.iterdir() if p.name not in nombres | {"manifest.json"})
        if extra: out.append(("AVISO", f"dataset v{m['version']}: ficheros que no están en el manifiesto: {extra}"))
    u = vs[-1]; cu = PUB / f"v{u['version']}"
    try:
        import pandas as pd
        d = pd.read_csv(cu / f"{u['nombre']}.csv", encoding="utf-8-sig", dtype={"id_portal": int})
        g = json.loads((cu / f"{u['nombre']}.geojson").read_text())
        n_raw = len(json.loads(RAW_JSON.read_text())) if sha256(RAW_JSON) == u["fuentes"][RAW_JSON.relative_to(ROOT).as_posix()] else None
        xs = [f["geometry"]["coordinates"] for f in g["features"]]
        fuera = sum(not (BBOX[0] <= x <= BBOX[2] and BBOX[1] <= y <= BBOX[3]) for x, y in xs)
        ok = (list(d.columns) == u["columnas"] and len(d) == u["filas_csv"] and d.id_portal.is_unique and len(xs) == u["features_geojson"]
              == int(d.lon.notna().sum()) and fuera == 0 and (n_raw is None or n_raw == len(d)))
        out.append(("OK" if ok else "ERROR", f"dataset v{u['version']}: {len(d)} filas{' (= las del portal)' if n_raw == len(d) else ''}, {len(xs)} situadas, "
                    f"id_portal único, {fuera} coordenadas fuera de València, columnas {'como el manifiesto' if list(d.columns) == u['columnas'] else 'DISTINTAS'}"))
    except Exception as e:
        out.append(("ERROR", f"dataset v{u['version']}: no se puede leer ({type(e).__name__}: {e})"))
    # build: cada versión copiada tal cual y «ultima» = la más nueva
    if BUILD_DATOS.exists():
        dif = [f for m in vs for f in m["ficheros"] if not (BUILD_DATOS / f).exists() or sha256(BUILD_DATOS / f) != m["ficheros"][f]["sha256"]]
        ult = [e for e in ("csv", "geojson") if not (BUILD_DATOS / f"{ULTIMA}.{e}").exists() or sha256(BUILD_DATOS / f"{ULTIMA}.{e}") != u["ficheros"][f"{u['nombre']}.{e}"]["sha256"]]
        out.append(("ERROR" if dif or ult else "OK", f"dataset en la web: {'distintos de la versión cerrada ' + str(dif) if dif else 'versiones idénticas'}; "
                    f"«{ULTIMA}» {'NO es v' + u['version'] + ' ' + str(ult) if ult else '= v' + u['version']}"))
    # ¿han cambiado los datos de origen desde la última versión? (no es un error: toca publicar una versión nueva)
    cambiados = [k for k, v in u["fuentes"].items() if k.startswith("data/") and (not (ROOT / k).exists() or sha256(ROOT / k) != v)]
    out.append(("AVISO" if cambiados else "OK", f"dataset: {'han cambiado ' + str(cambiados) + ' desde v' + u['version'] + ': publicar una versión nueva (make dataset VERSION=…)' if cambiados else 'los datos de origen son los de v' + u['version']}"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--publicar", metavar="X.Y"); ap.add_argument("--mes", default=datetime.date.today().strftime("%Y-%m"))
    ap.add_argument("--nota-va", default=""); ap.add_argument("--nota-es", default="")
    ap.add_argument("--build", action="store_true"); ap.add_argument("--comprobar", action="store_true"); ap.add_argument("--probar", action="store_true")
    a = ap.parse_args()
    if a.publicar:
        if not re.fullmatch(r"\d+\.\d+", a.publicar) or not re.fullmatch(r"\d{4}-\d{2}", a.mes): sys.exit("versión X.Y y mes AAAA-MM")
        dest = PUB / f"v{a.publicar}"
        if dest.exists(): sys.exit(f"{dest.relative_to(ROOT)} ya existe: una versión cerrada no se regenera")
        vs = versiones()
        if vs and vtupla(a.publicar) <= vtupla(vs[-1]["version"]): sys.exit(f"la versión nueva tiene que ser mayor que v{vs[-1]['version']}")
        if not (a.nota_va and a.nota_es): sys.exit("falta --nota-va y --nota-es (qué cambia en esta versión, para el historial)")
        m = generar(dest, a.publicar, a.mes, a.nota_va, a.nota_es)
        print(f"publicada v{m['version']} en {dest.relative_to(ROOT)}: {m['filas_csv']} filas, {m['features_geojson']} situadas")
        for f, h in m["ficheros"].items(): print(f"  {f}  {h['bytes'] / 1e6:.2f} MB  sha256 {h['sha256'][:12]}")
    if a.probar:
        vs = versiones()
        with tempfile.TemporaryDirectory() as t:
            u = vs[-1] if vs else None
            m = generar(Path(t), u["version"] if u else "1.0", u["mes"] if u else a.mes, u["nota_va"] if u else "-", u["nota_es"] if u else "-")
            if u:
                iguales = all(m["ficheros"][f"{u['nombre']}.{e}"]["sha256"] == u["ficheros"][f"{u['nombre']}.{e}"]["sha256"] for e in ("csv", "geojson"))
                print(f"con los datos de hoy, CSV y GeoJSON {'IGUALES' if iguales else 'DISTINTOS'} que v{u['version']}")
    if a.build: construir_build()
    if a.comprobar:
        r = comprobaciones()
        for n, t in r: print(f"{n:5s}  {t}")
        sys.exit(1 if any(n == "ERROR" for n, _ in r) else 0)


if __name__ == "__main__":
    main()
