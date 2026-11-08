"""Archivo mensual propio de las capas de infraestructura del geoportal y detección de cambios por geometría.

Para qué: ninguna capa de infraestructura del portal tiene fecha (itinerarios ciclistas, velocidad de las calles, red
VMP, pasos pintados, ocupación de la vía). Si se guarda una foto cada mes y se compara con la anterior, se puede
fechar un cambio (carril bici nuevo, calle pasada a 30 o a 20, paso ciclista nuevo) y verificar actuaciones de
«El Plan, al día» con datos del propio portal. No hay retroactivo: el archivo empieza el 07/11/2026.
Uso en el seguimiento del Plan: docs/plan_seguimiento.md, sec. 10.

Qué hace:
  1. Descarga cada capa de la API del geoportal (MapServer OPENDATA/Trafico, páginas de 2000, ≥ 4 s entre
     peticiones, User-Agent del proyecto). Un 403 o una respuesta que no es JSON para la ejecución entera:
     no se sortea el WAF y no se escribe ninguna foto a medias.
  2. Normaliza: sin identificadores internos (objectid, gid, GLOBALID: el portal recarga en bloque y los
     reasigna), coordenadas WGS84 a 7 decimales (~1 cm), geometría canónica (shapely.normalize) y entidades
     ordenadas. El sha256 se calcula sobre ese contenido normalizado.
  3. Guarda data/archivo_capas/AAAA-MM-DD/<capa>.geojson.gz (gzip determinista) y manifest.json (URL, hora de
     descarga, n.º de entidades, sha256, CRS). Si una capa es idéntica a la de la foto anterior, no se escribe:
     el manifest la marca «sin_cambios» y apunta al fichero que la contiene.
  4. Compara con la foto anterior por GEOMETRÍA, no por ID (en EPSG:25830, con una tolerancia de TOL m): lo que
     hay en una foto y no queda a menos de TOL m de nada de la misma clase en la otra es alta o baja; si queda
     cubierto por otra clase, es un cambio de atributo (p. ej. «velocidad: 50 → 30»). Resultado en
     data/archivo_capas/cambios.csv y un resumen por capa en pantalla.

Aviso: un cambio en la capa NO prueba un cambio en la calle (puede ser una corrección del inventario o una
recarga). Es una pista que hay que confirmar con una fuente oficial antes de tocar plan_seguimiento.csv, con la
misma validación humana que docs/plan_seguimiento.md.

Uso: .venv/bin/python -I scripts/archivar_capas.py                  (descarga, archiva y compara; `make archivar`)
     .venv/bin/python -I scripts/archivar_capas.py --comparar A B    (solo compara dos fotos ya guardadas)
     .venv/bin/python -I scripts/archivar_capas.py --destino DIR     (archivo en otra carpeta, para pruebas)
Códigos de salida: 0 bien · 1 error (red, WAF, respuesta rara) · 2 uso.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
ARCHIVO = ROOT / "data/archivo_capas"
SERVICIO = "https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer"
UA = "observatori-bici-patinet/1.0 (archivo mensual de capas de datos abiertos; +https://observatoribicivlc.org)"
PAUSA = 4            # segundos entre peticiones (misma cortesía que con el CKAN del portal)
INTENTOS = 3
PAGINA = 2000        # maxRecordCount del servicio
DECIMALES = 7        # WGS84: ~1 cm
CRS_MEDIR = 25830
TOL = 2.0            # m: tolerancia de la comparación por geometría (redigitalizaciones y redondeos)
MIN_LONG = 5.0       # m: los restos de línea más cortos no se cuentan como cambio (1 m en los trazos de pintura)
TOL_PUNTO = 5.0      # m: en capas de puntos

PASOS_CICLISTAS = ("Pasos Bicis", "CarrilBiciPaso", "CarrilBiciPasoPoli", "CarrilBiciPasoAcri")
PASOS_PEATONES = ("Pasos Pastillas", "Pasos Tacos")


def _in(valores):
    return "GRUPO IN (" + ",".join(f"'{v}'" for v in valores) + ")"


# clave: atributos que definen la «clase» en la comparación; etiqueta: atributos que solo describen
CAPAS = {
    "189_itinerarios_ciclistas": dict(capa=189, oid="objectid", nombre="Itinerarios Ciclistas", campos=["estado"],
                                      clave=["estado"], etiqueta=[], unidad="tramo"),
    "223_velocidad_calles": dict(capa=223, oid="objectid", nombre="Velocidad Calles",
                                 campos=["velocidad", "tipcalle", "nomcalle", "tipnomcall"],
                                 clave=["velocidad"], etiqueta=["tipnomcall"], unidad="tramo"),
    "2_vmp_tipo_a": dict(capa=2, oid="gid", nombre="Vehículos Movilidad Personal Tipo A", campos=[], clave=[], etiqueta=[],
                         unidad="tramo"),
    "3_vmp_tipo_b": dict(capa=3, oid="gid", nombre="Vehículos Movilidad Personal Tipo B", campos=[], clave=[], etiqueta=[],
                         unidad="tramo"),
    "238_pasos_ciclistas": dict(capa=238, oid="OBJECTID", nombre="Señalización Horizontal: pasos ciclistas", where=_in(PASOS_CICLISTAS),
                                campos=["GRUPO", "CALLE", "TIPOCALLE", "COLOR", "CREATED_DATE", "LAST_EDITED_DATE"],
                                clave=["GRUPO"], etiqueta=["CALLE"], unidad="trazo", min_long=1.0),
    "238_pasos_peatones": dict(capa=238, oid="OBJECTID", nombre="Señalización Horizontal: pasos de peatones", where=_in(PASOS_PEATONES),
                               campos=["GRUPO", "CALLE", "TIPOCALLE", "COLOR", "CREATED_DATE", "LAST_EDITED_DATE"],
                               clave=["GRUPO"], etiqueta=["CALLE"], unidad="trazo", min_long=1.0),
    "209_ocupacion_via_publica": dict(capa=209, oid="objectid", nombre="Ocupación vía pública",
                                      campos=["id_incidencia", "desc_incidencia", "tipo_incidencia", "desc_calle",
                                              "tipo_afectacion", "fecha_inicio", "fecha_fin", "numero_policia_origen"],
                                      clave=["tipo_incidencia", "desc_incidencia", "fecha_inicio", "fecha_fin"],
                                      etiqueta=["desc_calle"], unidad="punto"),
}
CAMPOS_FECHA = {"CREATED_DATE", "LAST_EDITED_DATE", "fecha_inicio", "fecha_fin"}

_ultima = 0.0


class ErrorPortal(Exception):
    pass


def pedir(url):
    """GET con pausa, timeout y reintentos limitados. Un 403 o HTML no se reintenta: posible WAF, no se sortea."""
    global _ultima
    fallo = ""
    for intento in range(1, INTENTOS + 1):
        espera = PAUSA - (time.monotonic() - _ultima)
        if espera > 0:
            time.sleep(espera)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                cuerpo = r.read()
            _ultima = time.monotonic()
            if cuerpo.lstrip()[:1] not in (b"{", b"["):
                raise ErrorPortal(f"respuesta que no es JSON (posible bloqueo del WAF: no se sortea): {url}")
            datos = json.loads(cuerpo)
            if "error" in datos:
                raise ErrorPortal(f"error del servicio {datos['error']}: {url}")
            return datos
        except urllib.error.HTTPError as e:
            _ultima = time.monotonic()
            if e.code in (401, 403, 404):
                raise ErrorPortal(f"HTTP {e.code}" + (" (posible bloqueo del WAF: no se sortea)" if e.code == 403 else "")
                                  + f": {url}")
            fallo = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            _ultima = time.monotonic()
            fallo = f"{type(e).__name__}: {e}"
        if intento < INTENTOS:
            time.sleep(15 * intento)
    raise ErrorPortal(f"sin respuesta tras {INTENTOS} intentos ({fallo}): {url}")


def url_consulta(cfg, offset=None):
    p = dict(where=cfg.get("where", "1=1"), outFields=",".join(cfg["campos"] + [cfg["oid"]]), returnGeometry="true",
             outSR=4326, geometryPrecision=DECIMALES, f="geojson")
    if offset is not None:  # orden por el OID: paginación estable dentro de una descarga (el OID no se guarda)
        p.update(orderByFields=cfg["oid"], resultOffset=offset, resultRecordCount=PAGINA)
    return f"{SERVICIO}/{cfg['capa']}/query?" + urllib.parse.urlencode(p)


def descargar(cfg):
    total = pedir(f"{SERVICIO}/{cfg['capa']}/query?" + urllib.parse.urlencode(
        dict(where=cfg.get("where", "1=1"), returnCountOnly="true", f="json")))["count"]
    feats, off = [], 0
    while off < total:
        fs = pedir(url_consulta(cfg, off)).get("features", [])
        if not fs:
            break
        feats += fs
        off += len(fs)
    if len(feats) != total:
        raise ErrorPortal(f"capa {cfg['capa']}: {len(feats)} entidades descargadas y el servicio dice {total}")
    return feats


def fecha_iso(v):
    if v is None or isinstance(v, str):
        return v
    return dt.datetime.fromtimestamp(v / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def normalizar(feats, cfg):
    """FeatureCollection canónica: sin IDs internos, coordenadas redondeadas, geometría normalizada y orden fijo."""
    filas = []
    for f in feats:
        props = {k: (fecha_iso(v) if k in CAMPOS_FECHA else v)
                 for k, v in (f.get("properties") or {}).items() if k in cfg["campos"]}
        g = f.get("geometry")
        if g:
            geom = shapely.normalize(shapely.set_precision(shape(g), 10 ** -DECIMALES))
            g = json.loads(json.dumps(mapping(geom)))  # tuplas -> listas
            g = _redondear(g)
        filas.append({"type": "Feature", "properties": props, "geometry": g})
    filas.sort(key=lambda x: json.dumps([x["geometry"], x["properties"]], sort_keys=True, ensure_ascii=False))
    return {"type": "FeatureCollection", "features": filas}


def _redondear(g):
    def r(c):
        return [r(x) for x in c] if isinstance(c[0], list) else [round(x, DECIMALES) for x in c]
    if g.get("type") == "GeometryCollection":
        return {"type": g["type"], "geometries": [_redondear(x) for x in g["geometries"]]}
    return {"type": g["type"], "coordinates": r(g["coordinates"])} if g.get("coordinates") else g


def serializar(fc):
    return json.dumps(fc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def gzip_determinista(datos):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0, filename="") as g:
        g.write(datos)
    return buf.getvalue()


# ---------- fotos guardadas ----------
def fotos(base):
    return sorted(p.name for p in base.iterdir() if p.is_dir() and (p / "manifest.json").exists()) if base.exists() else []


def leer_manifest(base, fecha):
    return json.loads((base / fecha / "manifest.json").read_text())


def leer_capa(base, fecha, clave):
    """GeoDataFrame de la capa en la foto `fecha` (siguiendo «sin_cambios» hasta el fichero que la contiene)."""
    m = leer_manifest(base, fecha)["capas"].get(clave)
    if m is None:
        return None
    fc = json.loads(gzip.decompress((base / m["archivo"]).read_bytes()))
    if not fc["features"]:
        return gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs=4326)
    return gpd.GeoDataFrame.from_features(fc["features"], crs=4326)


# ---------- comparación por geometría ----------
def _texto(v):
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)


def _clase(df, cols, sin_vacios=False):
    """Atributos unidos con « | » (la clase de la comparación o, con sin_vacios, una etiqueta descriptiva)."""
    if not cols:
        return pd.Series([""] * len(df), index=df.index)
    partes = [[_texto(v) for v in fila] for fila in df[cols].itertuples(index=False)]
    return pd.Series([" | ".join(x for x in p if x) if sin_vacios else " | ".join(p) for p in partes], index=df.index)


def _restos(a, b, tol, misma_clase):
    """Parte de cada geometría de `a` que no queda a menos de `tol` m de `b` (de su misma clase o de cualquiera).
    Devuelve (restos, clase de b que más cubre cada entidad de a)."""
    bb = gpd.GeoDataFrame({"clase_b": b["clase"].values}, geometry=b.geometry.buffer(tol).values, crs=b.crs)
    j = gpd.sjoin(a[["clase", "geometry"]], bb, predicate="intersects", how="inner")
    if misma_clase:
        j = j[j["clase"] == j["clase_b"]]
    else:
        j = j[j["clase"] != j["clase_b"]]
    restos = a.geometry.copy()
    otra = pd.Series(None, index=a.index, dtype=object)
    if len(j):
        cubre = gpd.GeoDataFrame({"k": j.index.values, "clase_b": j["clase_b"].values},
                                 geometry=bb.geometry.values[j["index_right"].values], crs=a.crs)
        if not misma_clase:
            otra.loc[:] = cubre.groupby("k")["clase_b"].agg(lambda s: s.mode().iat[0]).reindex(a.index)
        u = cubre.dissolve(by="k")
        restos.loc[u.index] = a.geometry.loc[u.index].difference(u.geometry, align=True)
    return restos, otra


def _medida(geoms, puntos):
    return (~geoms.is_empty).astype(float) if puntos else geoms.length


def _nombre(dominios, campo, valor):
    """Valor con su nombre del dominio del servicio, si lo tiene (p. ej. estado 5 → «5 Cortado por obras»)."""
    n = (dominios or {}).get(campo, {}).get(valor)
    return f"{valor} {n}" if n else valor


def _describir_cambio(cfg, antes, despues, dominios):
    a, d = antes.split(" | "), despues.split(" | ")
    return "; ".join(f"{k}: {_nombre(dominios, k, x)} → {_nombre(dominios, k, y)}"
                     for k, x, y in zip(cfg["clave"], a, d) if x != y)


def comparar(clave, cfg, viejo, nuevo, fecha, fecha_ant, dominios=None):
    """Filas de cambios (alta, baja, cambio_atributo) entre dos fotos de una capa."""
    preparar = []
    for df in (viejo, nuevo):
        df = df[df.geometry.notna() & ~df.geometry.is_empty].to_crs(CRS_MEDIR).reset_index(drop=True)
        if cfg["unidad"] != "punto":  # nodar: una línea que se pisa a sí misma rompe difference() (trazos de pintura)
            df["geometry"] = shapely.node(df.geometry.values)
        df["clase"] = _clase(df, cfg["clave"])
        df["etiqueta"] = _clase(df, cfg["etiqueta"], sin_vacios=True)
        preparar.append(df)
    viejo, nuevo = preparar
    puntos = cfg["unidad"] == "punto"
    tol, minimo = (TOL_PUNTO, 0.5) if puntos else (TOL, cfg.get("min_long", MIN_LONG))
    filas = []

    def fila(tipo, geom, df, i, desc, medida):
        p = gpd.GeoSeries([geom], crs=CRS_MEDIR).representative_point().to_crs(4326).iloc[0]
        filas.append(dict(fecha_snapshot=fecha, fecha_anterior=fecha_ant, capa=clave, tipo=tipo,
                          descripcion=(desc + (f" ({df.at[i, 'etiqueta']})" if df.at[i, "etiqueta"] else "")).strip(),
                          lon=round(p.x, 6), lat=round(p.y, 6),
                          longitud_m="" if puntos else round(medida, 1), n=1))

    for tipo, a, b in (("alta", nuevo, viejo), ("baja", viejo, nuevo)):
        r1, _ = _restos(a, b, tol, misma_clase=True)
        cand = _medida(r1, puntos) >= minimo
        if not cand.any():
            continue
        ac = a[cand].copy()
        ac["geometry"] = r1[cand].values
        ac = ac.set_geometry("geometry")
        r2, otra = _restos(ac, b, tol, misma_clase=False)
        cubierto = _medida(ac.geometry, puntos) - _medida(r2, puntos)
        for i in ac.index:
            if tipo == "alta" and otra.get(i) is not None and cubierto[i] >= minimo:
                fila("cambio_atributo", ac.geometry[i].difference(r2[i]) if not puntos else ac.geometry[i], ac, i,
                     _describir_cambio(cfg, otra[i], ac.at[i, "clase"], dominios), cubierto[i])
            if _medida(gpd.GeoSeries([r2[i]]), puntos).iat[0] >= minimo:
                txt = ("nuevo " if tipo == "alta" else "quitado ") + cfg["unidad"]
                if cfg["clave"]:
                    txt += " " + "; ".join(f"{k}={_nombre(dominios, k, v)}"
                                          for k, v in zip(cfg["clave"], ac.at[i, "clase"].split(" | ")))
                fila(tipo, r2[i], ac, i, txt, _medida(gpd.GeoSeries([r2[i]]), puntos).iat[0])
    return filas


def resumen_capa(clave, cfg, filas):
    if not filas:
        return f"{clave}: contenido distinto, pero sin cambios de geometría ni de clase (p. ej. recarga o atributo descriptivo)"
    df = pd.DataFrame(filas)
    partes = []
    for tipo, signo in (("alta", "+"), ("baja", "−"), ("cambio_atributo", "~")):
        d = df[df.tipo == tipo]
        if len(d):
            txt = f"{signo}{len(d)} {cfg['unidad']}{'s' if len(d) != 1 else ''}"
            if cfg["unidad"] != "punto":
                m = pd.to_numeric(d.longitud_m).sum()
                txt += (f" ({m / 1000:.1f} km)" if m >= 1000 else f" ({m:.0f} m)").replace(".", ",")
            partes.append(txt + (" con cambio de atributo" if tipo == "cambio_atributo" else ""))
    return f"{clave}: " + ", ".join(partes)


def escribir_cambios(base, filas, fecha):
    ruta = base / "cambios.csv"
    cols = ["fecha_snapshot", "fecha_anterior", "capa", "tipo", "descripcion", "lon", "lat", "longitud_m", "n"]
    previo = pd.read_csv(ruta, dtype=str, keep_default_na=False) if ruta.exists() else pd.DataFrame(columns=cols)
    previo = previo[previo.fecha_snapshot != fecha]
    nuevo = pd.concat([previo, pd.DataFrame(filas, columns=cols).astype(str)], ignore_index=True)
    nuevo.sort_values(["fecha_snapshot", "capa", "tipo"], kind="stable").to_csv(ruta, index=False)


def comparar_fotos(base, fecha_ant, fecha, manifest=None):
    manifest = manifest or leer_manifest(base, fecha)
    m_ant = leer_manifest(base, fecha_ant)
    filas, lineas = [], []
    for clave, cfg in CAPAS.items():
        m, ma = manifest["capas"].get(clave), m_ant["capas"].get(clave)
        if m is None or ma is None:
            lineas.append(f"{clave}: sin foto anterior con la que comparar")
            continue
        if m["sha256"] == ma["sha256"]:
            lineas.append(f"{clave}: sin cambios")
            continue
        f = comparar(clave, cfg, leer_capa(base, fecha_ant, clave), leer_capa(base, fecha, clave), fecha, fecha_ant,
                     m.get("dominios"))
        filas += f
        lineas.append(resumen_capa(clave, cfg, f) + f" [{ma['n']} → {m['n']} entidades]")
    return filas, lineas


def archivar(base):
    hoy = dt.date.today().isoformat()
    previas = [f for f in fotos(base) if f < hoy]
    ant = previas[-1] if previas else None
    m_ant = leer_manifest(base, ant) if ant else None
    destino = base / hoy
    tmp = base / f".{hoy}.tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.iterdir():
        p.unlink()
    manifest = {"fecha": hoy, "servicio": SERVICIO, "crs": "EPSG:4326", "decimales": DECIMALES,
                "normalizacion": "sin IDs internos; coordenadas a 7 decimales; shapely.normalize; entidades ordenadas; "
                                 "sha256 del JSON canónico (claves ordenadas, sin espacios, UTF-8)",
                "foto_anterior": ant, "capas": {}}
    metadatos = {}
    for clave, cfg in CAPAS.items():
        print(f"descargando {clave} (capa {cfg['capa']})…", flush=True)
        if cfg["capa"] not in metadatos:
            metadatos[cfg["capa"]] = pedir(f"{SERVICIO}/{cfg['capa']}?f=json")
        dominios = {c["name"]: {str(v["code"]): v["name"] for v in c["domain"]["codedValues"]}
                    for c in metadatos[cfg["capa"]].get("fields", [])
                    if c["name"] in cfg["campos"] and (c.get("domain") or {}).get("type") == "codedValue"}
        feats = descargar(cfg)
        fc = normalizar(feats, cfg)
        datos = serializar(fc)
        sha = hashlib.sha256(datos).hexdigest()
        ent = {"capa": cfg["capa"], "nombre": cfg["nombre"], "url": url_consulta(cfg), "dominios": dominios,
               "filtro": cfg.get("where", "1=1"), "campos": cfg["campos"],
               "descargado": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               "n": len(fc["features"]), "sin_geometria": sum(1 for f in fc["features"] if not f["geometry"]),
               "sha256": sha, "crs": "EPSG:4326"}
        previa = m_ant["capas"].get(clave) if m_ant else None
        if previa and previa["sha256"] == sha:
            ent.update(sin_cambios=True, archivo=previa["archivo"])
        else:
            gz = gzip_determinista(datos)
            (tmp / f"{clave}.geojson.gz").write_bytes(gz)
            ent.update(sin_cambios=False, archivo=f"{hoy}/{clave}.geojson.gz", bytes_gz=len(gz))
        manifest["capas"][clave] = ent
    (tmp / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    if destino.exists():
        for p in destino.iterdir():
            p.unlink()
        destino.rmdir()
    tmp.rename(destino)
    tam = sum(p.stat().st_size for p in destino.iterdir())
    print(f"\nfoto {hoy}: {len(manifest['capas'])} capas, "
          f"{sum(1 for c in manifest['capas'].values() if not c['sin_cambios'])} escritas, {tam / 1e6:.2f} MB en disco")
    for clave, c in manifest["capas"].items():
        print(f"  {clave}: {c['n']} entidades" + (" (sin cambios)" if c["sin_cambios"] else f", {c['bytes_gz'] / 1e6:.2f} MB gz"))
    if not ant:
        print("\nprimera foto: es la línea base, no hay nada con lo que comparar")
        escribir_cambios(base, [], hoy)
        return
    filas, lineas = comparar_fotos(base, ant, hoy, manifest)
    escribir_cambios(base, filas, hoy)
    print(f"\ncambios frente a la foto del {ant} (pistas que confirmar con una fuente oficial, no hechos):")
    for l in lineas:
        print("  " + l)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--destino", default=str(ARCHIVO), help="carpeta del archivo (por defecto data/archivo_capas)")
    ap.add_argument("--comparar", nargs=2, metavar=("ANTERIOR", "NUEVA"), help="compara dos fotos guardadas, sin descargar")
    a = ap.parse_args()
    base = Path(a.destino)
    try:
        if a.comparar:
            ant, nueva = a.comparar
            if ant not in fotos(base) or nueva not in fotos(base):
                print(f"no existen las fotos {ant} y {nueva} en {base}", file=sys.stderr)
                return 2
            filas, lineas = comparar_fotos(base, ant, nueva)
            escribir_cambios(base, filas, nueva)
            print("\n".join(lineas))
        else:
            archivar(base)
    except ErrorPortal as e:
        print(f"ERROR: {e}\nNo se ha escrito ninguna foto nueva.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
