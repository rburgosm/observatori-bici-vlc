"""Descarga ejes de calle, portales y centros educativos (WGS84) para geocodificar siniestros.
Uso: python3 -I scripts/fetch_callejero.py
"""
import json, time, urllib.request, urllib.parse
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data/raw/siniestros"
B = "https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/{}/query"
CAPAS = {"ejes": (223, "codvia,tipcalle,nomcalle,tipnomcalle,lf_add,lt_add,rf_add,rt_add"),
         "portales": (217, "codvia,numportal,dupli_trip")}

def capa(layer, fields):
    feats, off = [], 0
    while True:
        q = urllib.parse.urlencode(dict(where="1=1", outFields=fields, outSR=4326, f="geojson",
                                        resultOffset=off, resultRecordCount=2000, orderByFields="objectid"))
        r = json.load(urllib.request.urlopen(B.format(layer) + "?" + q, timeout=120))
        fs = r.get("features", [])
        feats += fs; off += len(fs)
        if len(fs) < 2000: break
        time.sleep(1.5)
    return {"type": "FeatureCollection", "features": feats}

for nombre, (layer, fields) in CAPAS.items():
    fc = capa(layer, fields)
    (OUT / f"{nombre}.geojson").write_text(json.dumps(fc, ensure_ascii=False))
    print(nombre, len(fc["features"]), flush=True)

url = "https://opendata.vlci.valencia.es/dataset/11436f0c-082b-4e5b-9659-005f5b528bde/resource/938e34b7-bb7d-4b0c-8176-3602d47ebd6a/download/centros-educativos-en-valencia.geojson"
(OUT / "centros_educativos.geojson").write_bytes(urllib.request.urlopen(url, timeout=120).read())
print("centros ok")

# Vías: nombre oficial (valenciano) + traducción no oficial (castellano), con el mismo codtipovia que los siniestros
VIAS = "https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/273/query"
rows, off = [], 0
while True:
    q = urllib.parse.urlencode(dict(where="1=1", outFields="codvia,codtipovia,nomoficial,traducnooficial,fechabaja",
                                    returnGeometry="false", f="json", resultOffset=off, resultRecordCount=2000, orderByFields="objectid"))
    fs = [f["attributes"] for f in json.load(urllib.request.urlopen(VIAS + "?" + q, timeout=120))["features"]]
    rows += fs; off += len(fs)
    if len(fs) < 2000: break
    time.sleep(1.5)
(OUT / "vias.json").write_text(json.dumps(rows, ensure_ascii=False))
print("vias", len(rows))
