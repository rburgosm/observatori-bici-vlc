"""Monta las páginas del prototipo: plantillas + comun/ + datos de web/proto/datos/, con la cabecera HTML.

Los datos ya no van incrustados en el HTML (observatori.html pesaba 2,9 MB): cada página los carga de un fichero aparte
con nombre versionado por contenido, build/datos/<página>.<hash8>.js (sha256), con integridad SRI sha384 en el <script>.
Se sigue usando .js (window.OBS = {...}) y no .json + fetch: el <script> clásico y bloqueante va en el mismo sitio que
antes los datos, así que la lógica de las plantillas sigue leyendo window.OBS/REL/MET/CAMBIOS de forma síncrona sin
reescribirla, el SRI es nativo y la página también abre con file://. Delante va comun/carga.js (aviso de carga y
mensaje si falla). Descarga con URL estable, build/datos/<página>.json (los mismos datos, envueltos con fuente, licencia
y aviso de no reidentificar): DESACTIVADA (PUBLICAR_JSON = False). Decisión del usuario del 04/11/2026: la descarga será
un ZIP versionado (datos de la web + dataset geolocalizado, README, licencia, diccionario y versión; pendiente 74).

Salida: web/proto/build/{observatori,informe,metode,cambios}.html y build/datos/ (las que se publican).
Uso: .venv/bin/python -I scripts/construir_web.py"""
import base64, hashlib, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "web/proto"
(W / "build").mkdir(exist_ok=True)
# tema claro/oscuro/automático, común a las páginas: se inserta solo donde la plantilla tiene el marcador
COMUN = {"/*TEMA_JS*/": W / "comun/tema.js", "/*TEMA_CSS*/": W / "comun/tema.css", "/*PIE_JS*/": W / "comun/pie.js"}
BD = W / "build/datos"
BD.mkdir(exist_ok=True)
PAGINAS = (("observatori", "observatori.js"), ("informe", "relato.js"), ("metode", "metode.js"), ("cambios", "cambios.js"),
           ("pla", "pla.js"))   # None: sin datos

# registro público de cambios: docs/cambios.csv (fecha, tipo, va, es) -> web/proto/datos/cambios.js
import csv, json
with open(ROOT / "docs/cambios.csv", newline="", encoding="utf-8") as f:
    CAMBIOS = [{"f": r["fecha"], "t": r["tipo"], "va": r["va"], "es": r["es"]} for r in csv.DictReader(f)]
assert all(c["t"] in {"datos", "metode", "web"} and c["va"] and c["es"] for c in CAMBIOS), "docs/cambios.csv: tipo o texto vacío"
(W / "datos/cambios.js").write_text("window.CAMBIOS = " + json.dumps(CAMBIOS, ensure_ascii=False) + ";\n")
# pie común (comun/pie.js): conjunto de siniestros del portal y su fecha de obtención (la pide la política de uso del portal;
# es la fecha del fichero descargado) y versión de la web (último cambio público de docs/cambios.csv)
import datetime
_crudo = sorted((ROOT / "data/raw/siniestros").glob("siniestros-de-trafico-*.json"))[-1]
PIE_INFO = {"conjunto": _crudo.stem, "descarga": datetime.date.fromtimestamp(_crudo.stat().st_mtime).isoformat(),
            "version": max(c["f"] for c in CAMBIOS)}
# «Hi col·laboren / Colaboran» (solo filas con publicar = si de data/processed/colaboran.csv, exportadas por exportar_web.py):
# si la lista está vacía no se pasa al pie y no se pinta nada
_colab = W / "datos/colaboran.json"
if _colab.exists() and json.loads(_colab.read_text()):
    PIE_INFO["colab"] = json.loads(_colab.read_text())

# Envoltorio de la descarga estable (build/datos/<página>.json). Licencia y aviso: docs/dataset_licencia_privacidad.md.
# Desactivado hasta el ZIP del pendiente 74: con False no se escribe nada (y se borra el que hubiera en build/datos/).
PUBLICAR_JSON = False
CAMPOS = {"pla": {"acts": "una actuación del Plan por fila (data/processed/plan_seguimiento.csv): acción, actuación, estado "
                          "(hecha, en_marcha, anunciada, sin_info = sin información pública), fecha de la prueba, fuente [n] de "
                          "«fuentes», cita del Plan, nota y fecha de comprobación"},
          "observatori": {"pts": "un siniestro geolocalizado por fila: [lon, lat, año, vehículo (b bici, p patinete, a los dos), "
                          "gravedad (0 sin heridos, 1 leves, 2 baja gravedad, 3 graves, 4 fallecidos, -1 otra), tipo de accidente "
                          "(solo el último año con el campo fiable; si no, vacío), UBICACION del portal, método de situación "
                          "(c cruce, p portal, q portal cercano, o otro), fecha y hora (dd/mm/aaaa hh:mm), UNIDADES_IMPLICADAS, "
                          "FACTORES CONCURRENTES, lugar (índice en negros o -1), Jardín del Turia (0 no, 1 sí, 2 sí y dentro de la zona)]",
                          "sp": "un siniestro SIN punto por fila, solo para los filtros: [año, vehículo, gravedad, con quién (m vehículo, "
                          "w peatón, d entre bicis o patinetes, s solo), franja horaria (0-5), laborable (1/0), factores (bits: 1 prioridad, "
                          "2 distracción, 4 estado de la vía, 8 velocidad), tipo (solo el último año), Jardín del Turia (1/0)]"}}
FUENTE_PAG = {"pla": "Seguimiento del observatorio a partir de fuentes públicas (Plan Director de Seguridad Vial de València "
                      "2026-2030, notas de prensa y documentos del Ajuntament, prensa), citadas una a una en «fuentes». "
                      "Revisión trimestral con validación humana. El Ajuntament de València no participa en este trabajo ni lo avala."}
def publicar_datos(pag, fichero):
    """Escribe build/datos/<pag>.<hash8>.js (y borra las versiones anteriores de esa página en build/: deploy.sh guarda
    la anterior en el servidor) y build/datos/<pag>.json. Devuelve (ruta relativa, integridad SRI)."""
    b = (W / "datos" / fichero).read_bytes()
    m = re.match(rb"window\.(\w+)\s*=\s*", b)
    assert m, f"{fichero}: se esperaba «window.X = {{...}};»"
    obj = json.loads(b[m.end():].decode().strip().rstrip(";"))
    nombre = f"{pag}.{hashlib.sha256(b).hexdigest()[:8]}.js"
    for viejo in BD.glob(f"{pag}.*.js"):
        if viejo.name != nombre:
            viejo.unlink()
    (BD / nombre).write_bytes(b)
    env = {"titulo": {"va": f"Observatori de la bici i el patinet de València: dades de la pàgina {pag}.html",
                      "es": f"Observatorio de la bici y el patinete de València: datos de la página {pag}.html"},
           "pagina": f"{pag}.html", "version": PIE_INFO["version"],
           "fuente": FUENTE_PAG[pag] if pag in FUENTE_PAG else f"Ajuntament de València – Dades Obertes (opendata.vlci.valencia.es), CC BY 4.0: siniestros de tráfico "
                     f"({PIE_INFO['conjunto']}), callejero, carril bici y puntos de conteo, obtenidos el {PIE_INFO['descarga']}. "
                     "Datos modificados por el observatorio: los siniestros se sitúan en el mapa con el callejero. "
                     "El Ajuntament de València no participa en este trabajo ni lo avala.",
           "licencia": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)",
           "aviso": "Sin datos de las personas implicadas. Está prohibido reidentificar personas cruzando estos datos con otras "
                    "fuentes (política de uso del portal de datos abiertos de València).",
           "variable": m.group(1).decode(), "campos": CAMPOS.get(pag, {}), "datos": obj}
    if PUBLICAR_JSON:
        (BD / f"{pag}.json").write_text(json.dumps(env, ensure_ascii=False, separators=(",", ":")) + "\n")
    else:
        (BD / f"{pag}.json").unlink(missing_ok=True)
    sri = "sha384-" + base64.b64encode(hashlib.sha384(b).digest()).decode()
    return f"datos/{nombre}", sri

CARGA_JS = (W / "comun/carga.js").read_text()
# índice de las fichas estáticas por lugar y calle (scripts/fichas.py lo escribe en build/datos/fichas_indice.<hash8>.js y deja
# su ruta y su SRI en web/proto/datos/fichas_indice.sri): lo cargan el observatorio y el informe para que el buscador enlace
# a <clase>/<slug>/. Mismo origen (script-src 'self' de la CSP) y con SRI. Sin índice, el buscador sigue sin fichas.
FICHAS_SRI = W / "datos/fichas_indice.sri"
CON_FICHAS = ("observatori", "informe")
FICHAS_TAG = ""
if FICHAS_SRI.exists():
    _fsrc, _fsri = FICHAS_SRI.read_text().split()
    _fb = (W / "build" / _fsrc).read_bytes()
    assert "sha384-" + base64.b64encode(hashlib.sha384(_fb).digest()).decode() == _fsri, f"{_fsrc}: el SRI de fichas_indice.sri no coincide"
    FICHAS_TAG = f'\n<script src="{_fsrc}" integrity="{_fsri}"></script>'
else:
    print("AVISO: falta web/proto/datos/fichas_indice.sri (scripts/fichas.py): el buscador no enlazará las fichas")
for pag, datos in PAGINAS:
    if not (W / f"{pag}.plantilla.html").exists():
        continue
    plantilla = (W / f"{pag}.plantilla.html").read_text()
    info = dict(PIE_INFO)
    if datos:
        assert plantilla.count("<script>/*DATA*/</script>") == 1, pag
        src, sri = publicar_datos(pag, datos)
        if PUBLICAR_JSON:
            info["datos"] = {"url": f"datos/{pag}.json", "mb": round((BD / f"{pag}.json").stat().st_size / 1e6, 2)}
        cuerpo = plantilla.replace("<script>/*DATA*/</script>",
                                   f"<script>{CARGA_JS}</script>\n"
                                   f'<script src="{src}" integrity="{sri}" onerror="__cargaFallo()"></script>'
                                   + (FICHAS_TAG if pag in CON_FICHAS else ""))
    else:
        cuerpo = plantilla
    for marca, fichero in COMUN.items():
        assert cuerpo.count(marca) <= 1, (pag, marca)
        if marca in cuerpo:
            js = fichero.read_text()
            if marca == "/*PIE_JS*/":
                js = "window.PIE_INFO = " + json.dumps(info, ensure_ascii=False) + ";\n" + js
            cuerpo = cuerpo.replace(marca, js)
    # las líneas iniciales de la plantilla con <title>, <meta> y <link> (descripción, theme-color, favicon, fuentes) van al <head>
    lineas = cuerpo.split("\n"); n = 0
    while n < len(lineas) and lineas[n].startswith(("<title", "<meta", "<link")): n += 1
    cabeza, cuerpo = "\n".join(lineas[:n]), "\n".join(lineas[n:])
    html = ('<!doctype html>\n<html lang="ca">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{cabeza}\n'
            '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
            f'</head>\n<body>\n{cuerpo}\n</body>\n</html>\n')
    (W / "build" / f"{pag}.html").write_text(html)
    print(f"web/proto/build/{pag}.html ({len(html.encode()) / 1e3:.0f} kB)")
