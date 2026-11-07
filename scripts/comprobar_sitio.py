"""Comprobaciones de la web pública (scripts/construir_sitio.py y las fichas): OK / AVISO / ERROR, como comprobar.py.
Lo llama `make comprobar` después de comprobar.py. Termina con 1 si hay algún ERROR.

- Cada página existe, en las dos lenguas (mismo número de bloques va y es) y con la cabecera y el pie comunes.
- Migas en todas salvo la portada: nav con aria-label en va y es, aria-current y JSON-LD BreadcrumbList válido.
- Recursos con SRI que existen y coinciden; solo scripts de este origen o de cdnjs (MapLibre); ninguna hoja externa.
- Enlaces internos que existen (carpeta con index.html o fichero) y anclas de la misma página que existen.
- Nada interno en el texto público: notas de boceto, líneas de pdsv.txt, nombres de scripts, «Preguntar…».
- Cifras = datos: accidentes del último año, medidas del Plan, fichas de los índices (SQLite).

Uso: .venv/bin/python -I scripts/comprobar_sitio.py"""
import base64, hashlib, json, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "web/proto/build"
UMAMI_JS = "https://estadisticas.observatoribicivlc.org/script.js"   # contador sin cookies en el propio servidor (deploy/umami/)
PAGS = ["index.html", "mapa/index.html", "ajuntament/index.html", "informe/index.html", "informe/2025/index.html",
        "dades/index.html", "metode/index.html", "sobre/index.html", "lloc/index.html", "carrer/index.html"]
errores = 0


def nota(nivel, texto):
    global errores
    errores += nivel == "ERROR"
    print(f"{nivel:5s}  {texto}")


def cargar(n):
    s = (ROOT / "web/proto/datos" / n).read_text()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def sin_scripts(t):
    t = re.sub(r"<script\b.*?</script>", " ", t, flags=re.S)
    return re.sub(r"<style\b.*?</style>", " ", t, flags=re.S)


print("== Web pública ==")
faltan = [p for p in PAGS if not (B / p).exists()]
nota("ERROR" if faltan else "OK", f"páginas: faltan {faltan} (make web)" if faltan else f"las {len(PAGS)} páginas de la web pública existen")
if faltan: sys.exit(1)
TXT = {p: (B / p).read_text() for p in PAGS}
# fichas de muestra (las comprueba a fondo fichas.comprobaciones())
for d in ("lloc", "carrer"):
    xs = sorted(x for x in (B / d).iterdir() if x.is_dir())[:3]
    for x in xs: TXT[f"{d}/{x.name}/index.html"] = (x / "index.html").read_text()

# cabecera, pie, lenguas
mal = []
for p, t in TXT.items():
    cuerpo = sin_scripts(t)
    if cuerpo.count('<header class="cabecera">') != 1 or cuerpo.count('<footer class="pie">') != 1: mal.append(f"{p}: cabecera o pie")
    if 'data-lang="va"' not in t or 'data-lang="es"' not in t: mal.append(f"{p}: botones va/es")
    nva, nes = len(re.findall(r'data-l="va"', cuerpo)), len(re.findall(r'data-l="es"', cuerpo))
    if nva != nes or not nva: mal.append(f"{p}: bloques va {nva} ≠ es {nes}")
    if not re.search(r'<html lang="ca">', t) or "localStorage.getItem(\"obs-lang\")" not in t.split("</head>")[0]: mal.append(f"{p}: lengua antes del primer pintado")
nota("ERROR" if mal else "OK", f"cabecera, pie y lenguas: {mal[:5]}" if mal else "cabecera y pie comunes, botones va/es y el mismo número de bloques en valenciano y en castellano en todas")

# menú idéntico en todas (salvo la página actual)
menus = {re.sub(r' aria-current="page"', "", re.search(r'<nav class="menu".*?</nav>', t, re.S).group(0)).replace("../", "").replace('href=""', 'href="./"')
         for t in TXT.values()}
nota("OK" if len(menus) == 1 else "ERROR", "el menú es el mismo en todas las páginas" if len(menus) == 1 else f"menús distintos: {len(menus)}")

# migas y JSON-LD
mal = []
for p, t in TXT.items():
    if p == "index.html":
        if 'class="migas"' in t: mal.append("la portada no lleva migas")
        continue
    navs = re.findall(r'<nav class="migas" data-l="(va|es)"[^>]*aria-label="([^"]+)"', t)
    if sorted(n[0] for n in navs) != ["es", "va"]: mal.append(f"{p}: migas va/es")
    if t.count('aria-current="page"><') < 1 and 'aria-current="page">' not in t: mal.append(f"{p}: aria-current")
    # puede haber más de un JSON-LD (dades/ lleva también el schema.org/Dataset): se busca el BreadcrumbList
    lds = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)]
    try:
        ld = next(x for x in lds if x.get("@type") == "BreadcrumbList"); assert len(ld["itemListElement"]) >= 2

    except Exception as e:
        mal.append(f"{p}: JSON-LD ({e})")
nota("ERROR" if mal else "OK", f"migas: {mal[:5]}" if mal else "migas en va y es con aria-label, aria-current y JSON-LD BreadcrumbList en todas salvo la portada")

# recursos con SRI y orígenes
mal, ext = [], set()
cache = {}
for p, t in TXT.items():
    base = (B / p).parent
    for tag in re.findall(r"<(?:script|link)\b[^>]*>", t):
        src = re.search(r'(?:src|href)="([^"]+)"', tag)
        if not src or ("<link" in tag and "stylesheet" not in tag and "preload" not in tag): continue
        u = src.group(1)
        if u.startswith("http"):
            ext.add(u.split("/")[2])
            # el contador de Umami (servidor propio) no lleva SRI: el script cambia con cada actualización de Umami (07/11/2026)
            if "<script" in tag and "integrity=" not in tag and u != UMAMI_JS: mal.append(f"{p}: {u} sin SRI")
            if "<link" in tag and "stylesheet" in tag: mal.append(f"{p}: hoja externa {u}")
            continue
        f = (base / u).resolve()
        if not f.exists(): mal.append(f"{p}: falta {u}"); continue
        i = re.search(r'integrity="([^"]+)"', tag)
        if i:
            if f not in cache: cache[f] = "sha384-" + base64.b64encode(hashlib.sha384(f.read_bytes()).digest()).decode()
            if cache[f] != i.group(1): mal.append(f"{p}: SRI de {u}")
        elif "<script" in tag: mal.append(f"{p}: {u} sin SRI")
    # recursos que la página pide después del primer pintado (data-<clave>="…" data-<clave>-sri="…", p. ej. las calles del mapa)
    for k, u, i in re.findall(r'data-(\w+)="([^"]+\.js)" data-\1-sri="([^"]+)"', t):
        f = (base / u).resolve()
        if not f.exists(): mal.append(f"{p}: falta {u}"); continue
        if "sha384-" + base64.b64encode(hashlib.sha384(f.read_bytes()).digest()).decode() != i: mal.append(f"{p}: SRI de {u}")
EXT_OK = {"cdnjs.cloudflare.com", UMAMI_JS.split("/")[2]}
nota("ERROR" if mal or ext - EXT_OK else "OK",
     f"recursos: {mal[:5]}; orígenes externos {sorted(ext)}" if mal or ext - EXT_OK else

     f"recursos: todos existen y su SRI coincide; único origen externo {sorted(ext)} (MapLibre, como antes)")

# enlaces internos y anclas
rotos, anclas = set(), set()
for p, t in TXT.items():
    base = (B / p).parent
    ids = set(re.findall(r'\bid="([^"]+)"', t))
    for h in re.findall(r'href="([^"]+)"', sin_scripts(t)):
        if h.startswith(("http", "mailto:", "data:")): continue
        ruta, _, frag = h.partition("#")
        if not ruta:
            if frag and frag not in ids and not frag.startswith(("lloc=", "punt=", "cerca=", "vista=")): anclas.add(f"{p}#{frag}")
            continue
        d = (base / ruta).resolve()
        if not (d.is_file() or (d / "index.html").is_file()): rotos.add(f"{p} → {h}")
nota("ERROR" if rotos else "OK", f"enlaces internos rotos: {sorted(rotos)[:6]}" if rotos else "enlaces internos: todos existen")
nota("AVISO" if anclas else "OK", f"anclas de la misma página que no existen: {sorted(anclas)[:6]}" if anclas else "anclas internas: todas existen")

# nada interno en el texto público
PROHIBIDO = [r"Nota interna", r"[Bb]oceto", r"\bl\.\d{3,}", r"pdsv\.txt", r"coords_plan", r"Preguntar", r"\(v2\)", r"añadida en la v2",
             r"docs/", r"codvia", r"TODO", r"\{[a-z_]+\}"]
mal = []
for p, t in TXT.items():
    txt = re.sub(r"<[^>]+>", " ", sin_scripts(t))
    for pat in PROHIBIDO:
        m = re.search(pat, txt)
        if m: mal.append(f"{p}: «{txt[max(0, m.start() - 30):m.end() + 30].strip()}»")
nota("ERROR" if mal else "OK", f"texto interno en público: {mal[:5]}" if mal else "sin notas internas, líneas de pdsv.txt, rutas ni tareas en el texto público")

# cifras = datos
R, P = cargar("relato.js"), cargar("pla.js")
con = sqlite3.connect(ROOT / "data/processed/observatorio.sqlite")
fich = dict(con.execute("SELECT clase, COUNT(*) FROM ficha GROUP BY clase").fetchall())
num = lambda n: f"{n:,}".replace(",", ".")
mal = []
if f'<span class="tc-cifra">{num(R["tot"][-1])}</span>' not in TXT["index.html"]: mal.append(f"portada: {R['tot'][-1]} accidentes en {R['anys'][-1]}")
if f'<p class="tc-cifra">{P["n"]}</p>' not in TXT["ajuntament/index.html"]: mal.append(f"Ayuntamiento: {P['n']} medidas")
for e, n in P["por_estado"].items():
    if f'data-f="{e}"' not in TXT["ajuntament/index.html"] or f'<span class="cifra">{n}</span>' not in TXT["ajuntament/index.html"]: mal.append(f"Ayuntamiento: {e} = {n}")
n_med = len(re.findall(r'<li data-est="', TXT["ajuntament/index.html"]))
if n_med != P["n"]: mal.append(f"Ayuntamiento: {n_med} medidas en la lista, {P['n']} en los datos")
for c in ("lloc", "carrer"):
    t = TXT[f"{c}/index.html"]
    va = re.search(r'<div data-l="va"><div data-lista="nom"[^>]*>(.*?)</div><div data-lista', t, re.S)
    n = len(re.findall(r"<li><a href=\"[a-z0-9-]+/\">", va.group(1))) if va else -1
    if n != fich.get(c): mal.append(f"índice {c}: {n} en la lista, {fich.get(c)} fichas en la base")
nota("ERROR" if mal else "OK", f"cifras: {mal}" if mal else f"cifras = datos: {R['tot'][-1]} accidentes en {R['anys'][-1]}, {P['n']} medidas y su reparto, "
     f"{fich.get('lloc')} lugares y {fich.get('carrer')} calles en los índices")

# redirecciones de las direcciones viejas en el vhost
_vh = ROOT / "deploy/nginx/DOMINIO.conf.plantilla"   # deploy/ no se publica
conf = _vh.read_text() if _vh.exists() else None
red = {"observatori.html": "/mapa/", "informe.html": "/informe/2025/", "pla.html": "/ajuntament/", "metode.html": "/metode/", "cambios.html": "/sobre/#canvis"}
mal = [k for k, v in red.items() if conf is not None and not re.search(rf"location = /{re.escape(k)}\s*\{{\s*return 301 {re.escape(v)}", conf)]
nota("ERROR" if mal else "OK", "vhost: deploy/ no está en este repositorio; no se comprueba" if conf is None else f"vhost: faltan las 301 de {mal}" if mal else "vhost: las 5 direcciones viejas redirigen con 301 a las nuevas")

print(f"\n{'ERROR: ' + str(errores) + ' comprobaciones fallan' if errores else 'Sin errores.'}")
sys.exit(1 if errores else 0)
