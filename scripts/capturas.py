"""Capturas de la web para seguir su evolución (antes / después de cada rediseño).

Uso:  python3 -I scripts/capturas.py ETIQUETA [--url http://localhost:8000/] [--paginas observatori,informe]
      (o `make capturas ETIQUETA=...`; la web tiene que estar servida: python3 -m http.server en web/proto/build/)

Captura cada página de web/proto/build/*.html en valenciano y castellano, tema claro, a 1280 y 390 px de ancho:
  - <pagina>_<lengua>_<ancho>_pantalla.png: la primera pantalla (1280×800 / 390×844), tal como la ve quien entra;
  - <pagina>_<lengua>_<ancho>_entera.png: la página entera. Se carga con «sin animaciones» (obs-sinanim=1), para que el
    informe pinte todos sus gráficos, y se recorre de arriba abajo antes de capturar (lo que aparece al hacer scroll).
Antes de capturar espera a que no quede el aviso «Cargando los datos…», a las fuentes y a que los mapas (MapLibre) hayan
cargado sus teselas. La lengua y el tema se fijan en localStorage (obs-lang, obs-tema) antes de que cargue la página.

Salida: capturas/AAAA-MM-DD_HHMM_<etiqueta>/ con los PNG y meta.json (fecha, commit, etiqueta), y capturas/index.html,
que pone las versiones en columnas para compararlas. capturas/ no va a git (.gitignore) ni al repositorio público.

Sin dependencias de .venv: Chrome sin pantalla del sistema (google-chrome o chromium) controlado por el protocolo
DevTools sobre tuberías (--remote-debugging-pipe), con la librería estándar. Comprime los PNG sin pérdida con optipng si
existe, si no con Pillow (si está en el python que lo ejecuta); si no hay ninguno, se quedan sin comprimir.
"""
import argparse
import base64
import datetime as dt
import glob
import html
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(RAIZ, "web", "proto", "build")
SALIDA = os.path.join(RAIZ, "capturas")
ORDEN = ["observatori", "informe", "pla", "metode", "cambios"]   # orden de las filas en index.html
LENGUAS = ["es", "va"]
ANCHOS = {1280: 800, 390: 844}   # ancho -> alto de la primera pantalla
ESPERA_MAX = 45                  # segundos para que la página esté lista

LISTA_JS = """(async () => {
  try { await document.fonts.ready; } catch (e) {}
  if (document.readyState !== 'complete') return false;
  if (document.querySelector('.carga-datos')) return false;      // aviso de carga o de fallo
  for (const n of ['map', 'mm']) {                               // mapas MapLibre de la portada
    let m; try { m = eval(n); } catch (e) { continue; }
    if (m && typeof m.loaded === 'function' && !(m.loaded() && m.areTilesLoaded())) return false;
  }
  return true;
})()"""

RECORRER_JS = """(async () => {
  const p = ms => new Promise(r => setTimeout(r, ms));
  for (let y = 0; y < document.documentElement.scrollHeight; y += Math.round(innerHeight * 0.8)) { scrollTo(0, y); await p(120); }
  scrollTo(0, document.documentElement.scrollHeight); await p(300);
  scrollTo(0, 0); await p(600);
  return document.documentElement.scrollHeight;
})()"""


class Chrome:
    """Chrome sin pantalla con el protocolo DevTools por tuberías (fd 3: órdenes; fd 4: respuestas, separadas por \\0)."""

    def __init__(self):
        exe = next((c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None)
        exe = exe or ("/opt/google/chrome/chrome" if os.path.exists("/opt/google/chrome/chrome") else None)
        if not exe:
            sys.exit("No hay google-chrome ni chromium")
        self.perfil = tempfile.mkdtemp(prefix="capturas_chrome_")
        a_r, a_w = os.pipe()   # nosotros -> Chrome (su fd 3)
        b_r, b_w = os.pipe()   # Chrome -> nosotros (su fd 4)

        def hijo():   # en el hijo: fd 3 y 4 heredables (pasar antes por fd altos, por si ya eran el 3 o el 4)
            x, y = os.dup(a_r), os.dup(b_w)
            os.dup2(x, 3)
            os.dup2(y, 4)

        self.p = subprocess.Popen(
            [exe, "--headless=new", "--remote-debugging-pipe", "--no-first-run", "--no-default-browser-check",
             "--hide-scrollbars", "--disable-extensions", "--mute-audio", f"--user-data-dir={self.perfil}", "about:blank"],
            preexec_fn=hijo, close_fds=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(a_r)
        os.close(b_w)
        self.w = os.fdopen(a_w, "wb", buffering=0)
        self.r = os.fdopen(b_r, "rb", buffering=0)
        self.n = 0
        self.resp = {}
        self.cv = threading.Condition()
        self.eventos = queue.Queue()
        threading.Thread(target=self._leer, daemon=True).start()

    def _leer(self):
        buf = b""
        while True:
            trozo = self.r.read(1 << 16)
            if not trozo:
                break
            buf += trozo
            while b"\0" in buf:
                msg, buf = buf.split(b"\0", 1)
                d = json.loads(msg)
                if "id" in d:
                    with self.cv:
                        self.resp[d["id"]] = d
                        self.cv.notify_all()
                else:
                    self.eventos.put(d)

    def __call__(self, metodo, params=None, sesion=None, espera=60):
        with self.cv:
            self.n += 1
            i = self.n
        m = {"id": i, "method": metodo, "params": params or {}}
        if sesion:
            m["sessionId"] = sesion
        self.w.write(json.dumps(m).encode() + b"\0")
        with self.cv:
            if not self.cv.wait_for(lambda: i in self.resp, timeout=espera):
                raise TimeoutError(metodo)
            d = self.resp.pop(i)
        if "error" in d:
            raise RuntimeError(f"{metodo}: {d['error']}")
        return d.get("result", {})

    def cerrar(self):
        try:
            self("Browser.close", espera=5)
        except Exception:
            pass
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()
        shutil.rmtree(self.perfil, ignore_errors=True)


def evaluar(ch, ses, expr, espera=60):
    r = ch("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True}, ses, espera)
    if "exceptionDetails" in r:
        raise RuntimeError(r["exceptionDetails"].get("text", "error JS"))
    return r["result"].get("value")


def capturar(ch, url, lang, ancho, alto, entera, destino):
    """Abre url en un contexto limpio (localStorage propio), espera a que esté lista y guarda el PNG. Devuelve avisos."""
    avisos = []
    ctx = ch("Target.createBrowserContext")["browserContextId"]
    tid = ch("Target.createTarget", {"url": "about:blank", "browserContextId": ctx})["targetId"]
    ses = ch("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    try:
        ch("Page.enable", sesion=ses)
        ch("Runtime.enable", sesion=ses)
        movil = ancho < 600
        ch("Emulation.setDeviceMetricsOverride",
           {"width": ancho, "height": alto, "deviceScaleFactor": 1, "mobile": movil}, ses)
        if movil:
            ch("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5}, ses)
        ch("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": "light"},
                                                       {"name": "prefers-reduced-motion", "value": "no-preference"}]}, ses)
        fijar = {"obs-lang": lang, "obs-tema": "light"}
        if entera:
            fijar["obs-sinanim"] = "1"
        ch("Page.addScriptToEvaluateOnNewDocument", {"source": "try{" + "".join(
            f"localStorage.setItem({json.dumps(k)},{json.dumps(v)});" for k, v in fijar.items()) + "}catch(e){}"}, ses)
        ch("Page.navigate", {"url": url}, ses)
        t0 = time.time()
        listo = False
        while time.time() - t0 < ESPERA_MAX:
            time.sleep(0.5)
            try:
                if evaluar(ch, ses, LISTA_JS, 15):
                    listo = True
                    break
            except Exception:
                pass   # navegación aún en curso
        if not listo:
            avisos.append(f"no quedó lista en {ESPERA_MAX} s (aviso de carga o mapa sin teselas)")
        time.sleep(1.5)   # transiciones y primera animación
        if entera:
            evaluar(ch, ses, RECORRER_JS, 120)
            evaluar(ch, ses, LISTA_JS, 15)   # por si el recorrido pidió teselas o gráficos nuevos
            time.sleep(1.0)
            m = ch("Page.getLayoutMetrics", sesion=ses)
            cs = m.get("cssContentSize") or m["contentSize"]
            h = int(min(cs["height"], 60000))
            if cs["height"] > 60000:
                avisos.append(f"página de {int(cs['height'])} px: recortada a 60000")
            r = ch("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True,
                                              "clip": {"x": 0, "y": 0, "width": ancho, "height": h, "scale": 1}}, ses, 120)
        else:
            r = ch("Page.captureScreenshot", {"format": "png"}, ses)
        with open(destino, "wb") as f:
            f.write(base64.b64decode(r["data"]))
    finally:
        ch("Target.closeTarget", {"targetId": tid})
        ch("Target.disposeBrowserContext", {"browserContextId": ctx})
    return avisos


def comprimir(rutas):
    """Sin pérdida: optipng si está; si no, Pillow; si no, nada. Devuelve el método usado."""
    if shutil.which("optipng"):
        subprocess.run(["optipng", "-quiet", "-o2", *rutas], check=False)
        return "optipng"
    try:
        from PIL import Image
    except ImportError:
        return "ninguno"
    for r in rutas:
        with Image.open(r) as im:
            im.load()
            im.save(r, optimize=True)
    return "Pillow"


def git_commit():
    try:
        c = subprocess.run(["git", "-C", RAIZ, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        sucio = subprocess.run(["git", "-C", RAIZ, "status", "--porcelain", "--", "web", "scripts"],
                               capture_output=True, text=True).stdout.strip()
        return c, bool(sucio)
    except Exception:
        return None, None


def indice():
    """capturas/index.html: una fila por página/lengua/ancho/tipo y una columna por versión (de la más antigua a la última)."""
    versiones = []
    for mj in sorted(glob.glob(os.path.join(SALIDA, "*", "meta.json"))):
        with open(mj, encoding="utf-8") as f:
            m = json.load(f)
        m["carpeta"] = os.path.basename(os.path.dirname(mj))
        versiones.append(m)
    claves = set()
    for v in versiones:
        for png in v.get("capturas", []):
            pag, lang, ancho, tipo = png[:-4].rsplit("_", 3)
            claves.add((pag, lang, int(ancho), tipo))
    orden = lambda k: (ORDEN.index(k[0]) if k[0] in ORDEN else 99, k[0], k[1], -k[2], k[3] != "pantalla")
    filas = []
    for pag, lang, ancho, tipo in sorted(claves, key=orden):
        nombre = f"{pag}_{lang}_{ancho}_{tipo}.png"
        celdas = []
        for v in versiones:
            if nombre in v.get("capturas", []):
                src = html.escape(f"{v['carpeta']}/{nombre}")
                celdas.append(f'<td><a href="{src}" target="_blank"><img loading="lazy" src="{src}" alt=""></a></td>')
            else:
                celdas.append('<td class="falta">—</td>')
        filas.append(f'<tr data-pag="{pag}" data-lang="{lang}" data-ancho="{ancho}" data-tipo="{tipo}">'
                     f'<th>{pag}<br>{lang} · {ancho} px<br>{"primera pantalla" if tipo == "pantalla" else "entera"}</th>'
                     + "".join(celdas) + "</tr>")
    cab = "".join(f'<th class="ver">{html.escape(v.get("etiqueta", ""))}<br><small>{html.escape(v.get("fecha", ""))}'
                  f' · {html.escape(str(v.get("commit") or ""))}{" +cambios" if v.get("sin_commit") else ""}</small></th>'
                  for v in versiones)
    sel = lambda nom, vals: (f'<label>{nom} <select data-f="{nom}"><option value="">todas</option>'
                             + "".join(f"<option>{x}</option>" for x in vals) + "</select></label>")
    pags = sorted({k[0] for k in claves}, key=lambda p: (ORDEN.index(p) if p in ORDEN else 99, p))
    filtros = (sel("pag", pags) + sel("lang", sorted({k[1] for k in claves}))
               + sel("ancho", sorted({str(k[2]) for k in claves}, key=int, reverse=True)) + sel("tipo", ["pantalla", "entera"]))
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Capturas de la web</title>
<style>
:root{{--bg:#fff;--ink:#1d1d1f;--ink2:#666;--line:#ddd;--cel:#f5f5f5}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161616;--ink:#eee;--ink2:#aaa;--line:#333;--cel:#222}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--ink);font:14px/1.4 system-ui,sans-serif}}
h1{{font-size:20px;margin:0 0 8px}} p{{color:var(--ink2);margin:0 0 12px}}
.filtros{{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 12px}}
.tabla{{overflow-x:auto}} table{{border-collapse:collapse}}
th,td{{border:1px solid var(--line);padding:6px;vertical-align:top}}
thead th{{position:sticky;top:0;background:var(--bg);z-index:1}}
tbody th{{text-align:left;font-weight:600;white-space:nowrap;background:var(--cel)}}
td img{{display:block;width:var(--w,420px);height:auto;max-height:var(--hmax,none);object-fit:cover;object-position:top}}
td.falta{{color:var(--ink2);text-align:center}} small{{color:var(--ink2);font-weight:400}}
</style></head><body>
<h1>Capturas de la web</h1>
<p>{len(versiones)} versiones, de la más antigua (izquierda) a la última. Clic en una imagen para verla a tamaño real.
Se generan con <code>make capturas ETIQUETA=…</code> (scripts/capturas.py).</p>
<div class="filtros">{filtros}
<label>ancho de columna <input type="range" min="200" max="1280" value="420" data-w></label>
<label><input type="checkbox" data-corta> recortar las enteras a 3 pantallas</label></div>
<div class="tabla"><table><thead><tr><th></th>{cab}</tr></thead><tbody>
{chr(10).join(filas)}
</tbody></table></div>
<script>
const f = {{}};
function aplicar(){{ document.querySelectorAll("tbody tr").forEach(tr => {{
  tr.hidden = Object.entries(f).some(([k, v]) => v && tr.dataset[k] !== v); }}); }}
document.querySelectorAll("select[data-f]").forEach(s => s.onchange = () => {{ f[s.dataset.f] = s.value; aplicar(); }});
const w = document.querySelector("[data-w]"), c = document.querySelector("[data-corta]");
const tam = () => {{ document.body.style.setProperty("--w", w.value + "px");
  document.body.style.setProperty("--hmax", c.checked ? (w.value * 2.5) + "px" : "none"); }};
w.oninput = tam; c.onchange = tam;
</script>
</body></html>
"""
    with open(os.path.join(SALIDA, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("etiqueta", help="nombre corto de la versión, p. ej. v0-antes-de-rehacer")
    ap.add_argument("--url", default="http://localhost:8000/")
    ap.add_argument("--paginas", help="lista separada por comas (por defecto, todas las de web/proto/build/*.html)")
    ap.add_argument("--solo-indice", action="store_true", help="solo rehace capturas/index.html")
    a = ap.parse_args()
    if a.solo_indice:
        indice()
        return
    etiqueta = "".join(c if c.isalnum() or c in "-_." else "-" for c in a.etiqueta).strip("-")
    pags = a.paginas.split(",") if a.paginas else [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(BUILD, "*.html"))]
    pags = sorted(pags, key=lambda p: (ORDEN.index(p) if p in ORDEN else 99, p))
    if not pags:
        sys.exit(f"No hay páginas en {BUILD}: ejecutar make web")
    import urllib.request
    try:
        urllib.request.urlopen(a.url + pags[0] + ".html", timeout=5).read(1)
    except Exception as e:
        sys.exit(f"La web no responde en {a.url} ({e}). Servirla: cd web/proto/build && python3 -m http.server 8000")
    ahora = dt.datetime.now()
    carpeta = os.path.join(SALIDA, f"{ahora:%Y-%m-%d_%H%M}_{etiqueta}")
    os.makedirs(carpeta, exist_ok=True)
    commit, sucio = git_commit()
    ch = Chrome()
    hechos, avisos = [], {}
    try:
        ch("Target.setDiscoverTargets", {"discover": False})
        for pag in pags:
            for lang in LENGUAS:
                for ancho, alto in ANCHOS.items():
                    for tipo in ("pantalla", "entera"):
                        nombre = f"{pag}_{lang}_{ancho}_{tipo}.png"
                        try:
                            av = capturar(ch, f"{a.url}{pag}.html", lang, ancho, alto, tipo == "entera",
                                          os.path.join(carpeta, nombre))
                            hechos.append(nombre)
                        except Exception as e:
                            av = [f"fallo: {e}"]
                        if av:
                            avisos[nombre] = av
                        print(f"{nombre}: {'; '.join(av) if av else 'ok'}", flush=True)
    finally:
        ch.cerrar()
    metodo = comprimir([os.path.join(carpeta, n) for n in hechos])
    meta = {"etiqueta": etiqueta, "fecha": ahora.strftime("%Y-%m-%d %H:%M"), "commit": commit, "sin_commit": sucio,
            "url": a.url, "paginas": pags, "lenguas": LENGUAS, "anchos": {str(k): v for k, v in ANCHOS.items()},
            "tema": "light", "compresion": metodo, "capturas": hechos, "avisos": avisos}
    with open(os.path.join(carpeta, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    indice()
    mb = sum(os.path.getsize(os.path.join(carpeta, n)) for n in hechos) / 1e6
    print(f"{len(hechos)} capturas ({mb:.1f} MB, compresión: {metodo}) en {os.path.relpath(carpeta, RAIZ)}; "
          f"{len(avisos)} con avisos. Comparar: capturas/index.html")


if __name__ == "__main__":
    main()
