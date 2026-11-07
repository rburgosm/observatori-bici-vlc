"""Verifica la muestra de outputs/muestra_geocodificacion.csv contra OpenStreetMap.

Para cada punto pide a Nominatim las vías en un radio pequeño (reverse, zoom de calle)
y comprueba si alguna palabra significativa del nombre de la calle del siniestro aparece
en la calle que devuelve OSM. Respeta la política de uso: 1 petición/segundo y User-Agent propio.

Uso: python3 -I scripts/verificar_muestra_osm.py
"""
import csv, json, time, unicodedata, re, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOP = set("C AV PG PL CTRA GV LLOC DE DEL LA LAS LOS EL Y I DELS CALLE CARRER AVINGUDA AVENIDA PLAZA PLACA "
           "PASSEIG PASEO GRAN VIA CAMI CAMINO SAN SANT SANTA DOCTOR".split())


def tokens(s):
    s = unicodedata.normalize("NFD", (s or "").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return {w for w in re.sub(r"[^A-Z ]", " ", s).split() if len(w) > 3 and w not in STOP}


def osm_calles(lat, lon):
    nombres = set()
    for zoom in (17, 18):
        q = urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "jsonv2", "zoom": zoom, "namedetails": 1})
        req = urllib.request.Request(f"https://nominatim.openstreetmap.org/reverse?{q}",
                                     headers={"User-Agent": "observatori-bici-vlc/0.1 (validacion geocodificacion; hola@observatoribicivlc.org)"})
        d = json.load(urllib.request.urlopen(req, timeout=20))
        a = d.get("address", {})
        nombres |= {a.get("road", ""), d.get("name", "")}
        nombres |= set((d.get("namedetails") or {}).values())
        time.sleep(1.1)
    return {n for n in nombres if n}


path = ROOT / "outputs/muestra_geocodificacion.csv"
filas = list(csv.DictReader(path.open()))
ok = 0
for f in filas:
    calles = f["ubicacion"].split(" cruce ") if f["metodo"] == "cruce" else [f["ubicacion"].rsplit(" ", 1)[0]]
    osm = osm_calles(f["lat"], f["lon"])
    t_osm = set().union(*(tokens(n) for n in osm)) if osm else set()
    acierto = any(tokens(c) & t_osm for c in calles)
    ok += acierto
    f["correcto (s/n)"] = "s" if acierto else "?"
    f["nota"] = "OSM: " + " | ".join(sorted(osm))[:120]
with path.open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)
print(f"coinciden con OSM: {ok}/{len(filas)}")
for f in filas:
    if f["correcto (s/n)"] != "s":
        print(f"  ? {f['metodo']:6s} {f['ubicacion'][:55]:55s} {f['nota'][:90]}")
