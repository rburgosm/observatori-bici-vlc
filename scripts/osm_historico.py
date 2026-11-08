"""Fotos anuales de OpenStreetMap (complemento externo, ODbL) para fechar el carril bici y los límites de velocidad.

Para qué: las capas del portal (carril bici, capa 189; velocidades) no tienen fecha, así que no dicen qué calles ganaron
carril bici o pasaron a 30 entre 2022 y 2025. El histórico de OSM (consultas `[date:…]` de Overpass) sí lo permite, con
dos límites: la fecha es la de cuando alguien lo dibujó (suele ir con retraso) y parte de lo «nuevo» es redibujado de lo que
ya existía. Por eso se valida contra la capa del portal y con noticias (scripts/politicas_comparativa.py, pendiente 127).

Uso: .venv/bin/python -I scripts/osm_historico.py            (descarga lo que falte; no repite lo descargado)
Salida: data/raw/osm/{cicl,vel}_AAAA-01-01.json  (respuesta de Overpass tal cual, con geometría)
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/osm"
URL = "https://overpass-api.de/api/interpreter"
UA = "observatori-bici-vlc (investigacion con datos abiertos)"
FECHAS = [f"{a}-01-01" for a in range(2022, 2027)]
AREA = 'area["name"="València"]["admin_level"="8"]->.a;'
Q = {
    # infraestructura ciclista: vía ciclista propia o carril/pista en la calzada
    "cicl": '(way(area.a)[highway=cycleway];way(area.a)["cycleway"~"track|lane|opposite_lane|opposite_track"];'
            'way(area.a)["cycleway:right"~"track|lane"];way(area.a)["cycleway:left"~"track|lane"];'
            'way(area.a)["cycleway:both"~"track|lane"];);out tags geom;',
    # calles con límite de velocidad anotado (para la zona 30)
    "vel": 'way(area.a)[highway~"^(primary|secondary|tertiary|residential|unclassified|living_street|primary_link|secondary_link|tertiary_link|trunk|trunk_link)$"][maxspeed];out tags geom;',
}


def bajar(tipo, fecha):
    f = OUT / f"{tipo}_{fecha}.json"
    if f.exists() and f.stat().st_size > 1000:
        return f, False
    q = f'[out:json][timeout:300][date:"{fecha}T00:00:00Z"];{AREA}{Q[tipo]}'
    req = urllib.request.Request(URL, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": UA})
    for intento in range(5):                       # 429/502/504: Overpass saturado; se espera cada vez más
        try:
            with urllib.request.urlopen(req, timeout=400) as r:
                datos = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 502, 503, 504) or intento == 4:
                raise
            print(f"  {tipo} {fecha}: HTTP {e.code}, reintento en {60 * (intento + 1)} s", flush=True)
            time.sleep(60 * (intento + 1))
    j = json.loads(datos)
    if j.get("remark"):
        sys.exit(f"Overpass avisa en {tipo} {fecha}: {j['remark']}")
    f.write_bytes(datos)
    return f, True


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for tipo in Q:
        for fecha in FECHAS:
            f, nuevo = bajar(tipo, fecha)
            n = len(json.loads(f.read_text())["elements"])
            print(f"{tipo} {fecha}: {n} vías{' (descargado)' if nuevo else ''}")
            if nuevo:
                time.sleep(20)      # Overpass es un servicio compartido: una consulta pesada cada vez y con pausa


if __name__ == "__main__":
    main()
