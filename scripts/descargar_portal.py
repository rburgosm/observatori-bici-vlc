"""Comprueba si el portal opendata.vlci.valencia.es publica siniestros de tráfico nuevos y, solo entonces, los descarga.

Para qué: la actualización semanal (deploy/actualizar.sh) necesita saber si hay datos nuevos (p. ej. 2026) sin bajar
34.000 filas cada semana ni tocar data/raw cuando nada cambia.

Qué mira (API CKAN, 3-4 s entre peticiones, User-Agent genérico del proyecto):
  1. package_show del conjunto que usa el proyecto (siniestros-de-trafico-2022-2025, guardado en
     data/raw/siniestros/ckan_siniestros_package.json): recursos nuevos o quitados y, en cada recurso, cambios en
     last_modified, metadata_modified, size, hash o url;
  2. datastore_search (limit=0) del recurso: filas publicadas frente a las del crudo local;
  3. package_search: otro conjunto de siniestros/accidentes de tráfico (p. ej. «siniestros-de-trafico-2022-2026»).
Si hay indicio de cambio, baja el datastore completo y compara fila a fila con el crudo; solo escribe en data/raw si
el contenido cambia de verdad (o si aparece un recurso o conjunto nuevo).

Salida: resumen JSON en --resumen (por defecto ~/.local/state/observatori/ultima_descarga.json) y código
  0  sin cambios · 10  datos nuevos (escritos en data/raw) · 1  error (red, WAF, respuesta rara) · 2  uso.
--simular: hace las consultas reales pero no escribe nada y sale con 10, para probar el aviso.

Uso: .venv/bin/python -I scripts/descargar_portal.py [--simular] [--resumen RUTA]
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIN = ROOT / "data/raw/siniestros"
CKAN_LOCAL = SIN / "ckan_siniestros_package.json"
CRUDO = SIN / "siniestros-de-trafico-2022-2025.json"
API = "https://opendata.vlci.valencia.es/api/3/action/"
UA = "observatori-bici-patinet/1.0 (comprobacion semanal de datos abiertos; +https://observatoribicivlc.org)"
PAUSA = 4            # segundos entre peticiones (el CKAN del portal limita)
INTENTOS = 3
CAMPOS_RECURSO = ("last_modified", "metadata_modified", "size", "hash", "url")
PATRON_CONJUNTO = re.compile(r"(siniestr|accident).*(tr[aà]fic)", re.I)
PAGINA = 10000

_ultima = 0.0


class ErrorPortal(Exception):
    pass


def pedir(accion, **params):
    """Llamada a la API con pausa, timeout y reintentos limitados. Un 403 no se reintenta (WAF: no se sortea)."""
    global _ultima
    url = API + accion + "?" + urllib.parse.urlencode(params)
    for intento in range(1, INTENTOS + 1):
        espera = PAUSA - (time.monotonic() - _ultima)
        if espera > 0:
            time.sleep(espera)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                datos = json.load(r)
            _ultima = time.monotonic()
            if not datos.get("success"):
                raise ErrorPortal(f"{accion}: success=false ({datos.get('error')})")
            return datos["result"]
        except urllib.error.HTTPError as e:
            _ultima = time.monotonic()
            if e.code in (401, 403, 404):
                raise ErrorPortal(f"{accion}: HTTP {e.code}" + (" (posible bloqueo del WAF: no se sortea)" if e.code == 403 else ""))
            fallo = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            _ultima = time.monotonic()
            fallo = f"{type(e).__name__}: {e}"
        if intento < INTENTOS:
            time.sleep(15 * intento)
    raise ErrorPortal(f"{accion}: sin respuesta tras {INTENTOS} intentos ({fallo})")


def huella(registros):
    return hashlib.sha256(json.dumps(registros, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def bajar_datastore(rid):
    registros, off = [], 0
    while True:
        r = pedir("datastore_search", resource_id=rid, limit=PAGINA, offset=off, sort="_id")
        registros += r["records"]
        off += len(r["records"])
        if not r["records"] or off >= r["total"]:
            return registros


def nombre_crudo(texto, rid):
    años = re.findall(r"(20\d\d(?:-20\d\d)?)", texto or "")
    return f"siniestros-de-trafico-{años[-1] if años else rid[:8]}.json"


def ficha_json(pkg):
    """Mismo formato que la respuesta de package_show guardada hasta ahora (una línea, ASCII)."""
    return json.dumps({"help": API + "help_show?name=package_show", "success": True, "result": pkg})


def escribir(ruta, contenido):
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(contenido)
    tmp.replace(ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true", help="consulta el portal pero no escribe y sale con 10")
    ap.add_argument("--resumen", default=os.path.expanduser("~/.local/state/observatori/ultima_descarga.json"))
    a = ap.parse_args()
    resumen = {"fecha": dt.datetime.now().isoformat(timespec="seconds"), "simulado": a.simular,
               "conjunto": None, "cambios": [], "ficheros_escritos": []}
    cambios, escritos = resumen["cambios"], resumen["ficheros_escritos"]

    def terminar(codigo, resultado, texto):
        resumen.update(resultado=resultado, resumen=texto)
        Path(a.resumen).parent.mkdir(parents=True, exist_ok=True)
        Path(a.resumen).write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
        print(texto)
        for c in cambios:
            print("  -", c)
        return codigo

    try:
        local_pkg = json.loads(CKAN_LOCAL.read_text())["result"]
        local_reg = json.loads(CRUDO.read_text())
        resumen["conjunto"] = local_pkg["name"]

        # 1. ficha del conjunto
        pkg = pedir("package_show", id=local_pkg["id"])
        loc_rec = {r["id"]: r for r in local_pkg["resources"]}
        rem_rec = {r["id"]: r for r in pkg["resources"]}
        nuevos_rec = [r for rid, r in rem_rec.items() if rid not in loc_rec]
        for rid in loc_rec.keys() - rem_rec.keys():
            cambios.append(f"el portal ya no tiene el recurso «{loc_rec[rid].get('name')}» ({rid})")
        for r in nuevos_rec:
            cambios.append(f"recurso nuevo en {pkg['name']}: «{r.get('name')}» ({r.get('format')}, {r.get('last_modified') or r.get('created')})")
        sospecha = {}
        for rid in loc_rec.keys() & rem_rec.keys():
            dif = [f"{k}: {loc_rec[rid].get(k)} → {rem_rec[rid].get(k)}" for k in CAMPOS_RECURSO
                   if loc_rec[rid].get(k) != rem_rec[rid].get(k)]
            if dif:
                sospecha[rid] = "; ".join(dif)
        if pkg.get("metadata_modified") != local_pkg.get("metadata_modified") and not sospecha and not nuevos_rec:
            print(f"Ficha del conjunto retocada ({local_pkg.get('metadata_modified')} → {pkg.get('metadata_modified')}), recursos iguales.")

        # 2. filas publicadas en el datastore del recurso que usamos
        rid_crudo = next((rid for rid, r in loc_rec.items() if r.get("datastore_active")), None)
        if rid_crudo in rem_rec and rem_rec[rid_crudo].get("datastore_active"):
            total = pedir("datastore_search", resource_id=rid_crudo, limit=0)["total"]
            if total != len(local_reg):
                sospecha[rid_crudo] = (sospecha.get(rid_crudo, "") + f"; filas: {len(local_reg)} → {total}").lstrip("; ")

        # 3. otros conjuntos de siniestros de tráfico
        bus = pedir("package_search", q="siniestros OR accidentes OR accidents OR sinistres", rows=200,
                    fl="id,name,title,metadata_created,num_resources")
        otros = [p for p in bus["results"] if p["name"] != local_pkg["name"]
                 and not (SIN / f"ckan_{p['name']}_package.json").exists()      # ya bajado en una vuelta anterior
                 and PATRON_CONJUNTO.search(p["name"] + " " + (p.get("title") or ""))]
        for p in otros:
            cambios.append(f"conjunto nuevo en el portal: {p['name']} («{p.get('title')}», creado {str(p.get('metadata_created'))[:10]})")

        # 4. confirmar con el contenido: bajar solo si hay indicio
        a_escribir = {}
        for rid, motivo in sospecha.items():
            r = rem_rec[rid]
            if not r.get("datastore_active"):
                cambios.append(f"recurso «{r.get('name')}» cambiado ({motivo}) pero sin datastore: revisar a mano")
                continue
            regs = bajar_datastore(rid)
            if huella(regs) == huella(local_reg):
                print(f"Recurso {rid}: metadatos distintos ({motivo}) pero mismas filas; no se toca data/raw.")
                continue
            cambios.append(f"«{r.get('name')}» cambia ({motivo}): ahora {len(regs)} filas (antes {len(local_reg)}), "
                           f"la última del {max((x.get('FECHA') or '') for x in regs)[:10]}")
            a_escribir[CRUDO] = json.dumps(regs, ensure_ascii=False)
        for r in nuevos_rec:
            if r.get("datastore_active"):
                regs = bajar_datastore(r["id"])
                a_escribir[SIN / nombre_crudo(f"{r.get('name')} {r.get('url')}", r["id"])] = json.dumps(regs, ensure_ascii=False)
        for p in otros:
            ficha = pedir("package_show", id=p["id"])
            a_escribir[SIN / f"ckan_{p['name']}_package.json"] = ficha_json(ficha)
            for r in ficha["resources"]:
                if r.get("datastore_active"):
                    regs = bajar_datastore(r["id"])
                    a_escribir[SIN / nombre_crudo(p["name"], r["id"])] = json.dumps(regs, ensure_ascii=False)
        if a_escribir or nuevos_rec or loc_rec.keys() - rem_rec.keys():
            a_escribir[CKAN_LOCAL] = ficha_json(pkg)

        if a.simular:
            cambios.append("SIMULACIÓN: no se ha escrito nada en data/raw")
            return terminar(10, "datos_nuevos", "Simulación: el portal publica datos nuevos de siniestros (prueba del aviso).")
        if not cambios:
            return terminar(0, "sin_cambios", f"Sin cambios en el portal ({pkg['name']}: {len(local_reg)} filas, "
                                              f"recurso de {max(str(r.get('last_modified')) for r in rem_rec.values())[:10]}).")
        for ruta, contenido in a_escribir.items():
            escribir(ruta, contenido)
            escritos.append(str(ruta.relative_to(ROOT)))
        return terminar(10, "datos_nuevos", f"Datos nuevos de siniestros en el portal: {len(cambios)} cambio(s).")
    except Exception as e:  # noqa: BLE001  cualquier fallo → código 1 con el motivo en el resumen
        cambios.append(f"{type(e).__name__}: {e}")
        return terminar(1, "error", "Error al comprobar el portal de datos abiertos.")


if __name__ == "__main__":
    sys.exit(main())
