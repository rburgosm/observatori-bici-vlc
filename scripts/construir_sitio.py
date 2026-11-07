"""Web pública (bocetos aceptados el 06/11/2026, pendiente 100): construye en web/proto/build/ las páginas nuevas, en
valenciano y castellano (una URL con las dos lenguas, como las fichas), con la cabecera, el menú, las migas y el pie
comunes de scripts/sitio.py.

  build/index.html              inicio (boceto inicio.html)
  build/mapa/index.html         mapa: la herramienta de la web anterior (filtros, vistas, CSV, teclado, minimapa, anillo
                                del Plan, buscador), con la lógica de web/proto/observatori.plantilla.html sin reescribir
  build/ajuntament/index.html   ¿Qué está haciendo el Ayuntamiento? (boceto ayuntamiento.html)
  build/informe/index.html      ediciones del informe anual (punto 95)
  build/informe/2025/index.html Informe 2025 (boceto informe.html, con las secciones 5-7 escritas)
  build/dades/index.html        Datos y método: secciones nuevas (scripts/sitio_dades.py), el método de siempre (con la
                                lógica de web/proto/metode.plantilla.html) y el registro de cambios (#canvis)
  build/lloc/index.html, build/carrer/index.html   índices de las fichas (lista completa en el HTML)
  build/img/*.svg               mapas estáticos (portada, informe, Ayuntamiento)

Datos: web/proto/datos/{observatori,relato,pla,metode}.js (los escribe exportar_web.py) y data/processed/observatorio.sqlite
(fichas, cambios, metadatos). Ninguna cifra escrita a mano: todas salen de ahí. Textos: aquí (va/es), en
scripts/sitio_textos_plan.py (medidas del Plan) y scripts/sitio_dades.py (método nuevo).
No toca las páginas viejas (construir_web.py); deploy/nginx las redirige con 301.

Uso: .venv/bin/python -I scripts/construir_sitio.py"""
import collections, csv, json, math, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sitio as S
import sitio_textos_plan as TP
import sitio_dades as SD
import nombres as N
from sitio import T, ESC, num

W = S.W; BUILD = S.BUILD
DB = ROOT / "data/processed/observatorio.sqlite"


def cargar(n):
    s = (W / "datos" / n).read_text()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


O, R, P, M = (cargar(f"{n}.js") for n in ("observatori", "relato", "pla", "metode"))
CON = sqlite3.connect(DB)
META = dict(CON.execute("SELECT clave, valor FROM meta").fetchall())
CAMBIOS = CON.execute("SELECT fecha, tipo, va, es FROM cambio ORDER BY orden").fetchall()
_colab = W / "datos/colaboran.json"
INFO = {"conjunto": META["conjunto_siniestros"], "descarga": META["fecha_descarga"], "version": max(c[0] for c in CAMBIOS)}
if _colab.exists() and json.loads(_colab.read_text()):
    INFO["colab"] = json.loads(_colab.read_text())
# fichas: [clase, slug, nombre va, nombre es, n] (scripts/fichas.py) y uid del lugar → slug
FICHAS = cargar("fichas_indice.js")
SLUG_UID = dict(CON.execute("SELECT uid, slug FROM ficha WHERE clase = 'lloc'").fetchall())
UID_RANK = dict(CON.execute("SELECT rank, uid FROM lugar WHERE en_top30 = 1").fetchall())
NOMF = {(f[0], f[1]): (f[2], f[3]) for f in FICHAS}
ANYS = R["anys"]; A0, A1 = ANYS[0], ANYS[-1]; PER = f"{A0}-{A1}"
E0 = R["meta"]["esc"][0]; MED = R["meta"]["media"]; CT = R["meta"]["control"]
EST = {"hecha": ("Feta", "Hecha"), "en_marcha": ("En marxa", "En marcha"), "anunciada": ("Anunciada", "Anunciada"),
       "sin_info": ("Sense informació pública trobada", "Sin información pública encontrada")}
ESTS = {"hecha": ("Fetes", "Hechas"), "en_marcha": ("En marxa", "En marcha"), "anunciada": ("Anunciades", "Anunciadas"),
        "sin_info": ("Sense informació pública trobada", "Sin información pública encontrada")}
ORDEN_EST = ["hecha", "en_marcha", "anunciada", "sin_info"]
MESES = {"va": "gener febrer març abril maig juny juliol agost setembre octubre novembre desembre".split(),
         "es": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()}


def limpio(n):
    """Sin el sufijo de calzada del nombre congelado («(S)», «(SO)»…): no se entiende fuera de contexto."""
    return re.sub(r"\s*\((?:N|S|E|O|NE|NO|SE|SO)\)$", "", n)


def fecha(f): return f"{f[8:10]}/{f[5:7]}/{f[:4]}" if f else ""


def fecha_larga(f, l):
    if not f: return ""
    d, m, a = int(f[8:10]), int(f[5:7]), f[:4]
    if l == "va":
        mes = MESES["va"][m - 1]
        return f"{d} {'d’' if mes[0] in 'aeiou' else 'de '}{mes} de {a}"
    return f"{d} de {MESES['es'][m - 1]} de {a}"


def de_cada(x, n=10):
    """0,57 → («quasi 6 de cada 10», «casi 6 de cada 10»)."""
    k = round(x * n); pre = ("quasi ", "casi ") if x * n < k - .05 else ("més de ", "más de ") if x * n > k + .05 else ("", "")
    return (f"{pre[0]}{k} de cada {n}", f"{pre[1]}{k} de cada {n}")


def pct(x, d=0): return num(x * 100, d) + " %"


def mes_any(ym, l):
    a, m = ym.split("-"); mes = MESES[l][int(m) - 1]
    return (f"{'d’' if mes[0] in 'aeiou' else 'de '}{mes} de {a}" if l == "va" else f"{mes} de {a}")


SIASV = R["meta"]["siasv"]


def ficha_top(rank):
    uid = UID_RANK.get(rank); slug = SLUG_UID.get(uid)
    return (slug, NOMF.get(("lloc", slug))) if slug else (None, None)


# ---------------------------------------------------------------- mapas estáticos (SVG con tema claro y oscuro; sin texto)
ESTILO_MAPA = """<style>
.bg{fill:#F7F8F8}.c0{stroke:#DDE2E5;fill:none;stroke-width:.7;stroke-linejoin:round}.c1{stroke:#BCC4C9;fill:none;stroke-width:1.5;stroke-linejoin:round}.cl{stroke:#9DB8AE;fill:none;stroke-width:1.2;stroke-dasharray:3 2}
.b{fill:#2a78d6}.p{fill:#C94B17}.a{fill:#14875E}.x{fill:#8A949D}.pt{stroke:#FFFFFF;stroke-width:.9}
.k{fill:#15202B}.k2{fill:#55626E}.hu{fill:#FFFFFF;stroke:#55626E;stroke-width:1.6}
.ux{fill:#B42318;stroke:#15202B;stroke-width:1.5}.um{fill:#FFFFFF;stroke:#15202B;stroke-width:3.2}
.zona{fill:#8A949D;fill-opacity:.22;stroke:#55626E;stroke-width:1;stroke-dasharray:4 3}
.eh{fill:#6E1470}.em{fill:#A23A9E}.ea{fill:#F6EAF5;stroke:#A23A9E;stroke-width:2.2}.ems{fill:#FFFFFF;stroke:#A23A9E;stroke-width:2.2}
text{font-family:system-ui,sans-serif}.tb{fill:#FFFFFF;font-size:13px;font-weight:700;text-anchor:middle;dominant-baseline:central}
@media (prefers-color-scheme:dark){
.bg{fill:#121A21}.c0{stroke:#212D37}.c1{stroke:#34434F}.cl{stroke:#4E6A60}.b{fill:#3987e5}.p{fill:#d95926}.a{fill:#199e70}.x{fill:#6F7B86}
.pt{stroke:#121A21}.k{fill:#E7ECEF}.k2{fill:#9AA7B2}.hu{fill:#121A21;stroke:#9AA7B2}.zona{fill:#6F7B86;stroke:#9AA7B2}
.ux{fill:#F97066;stroke:#E7ECEF}.um{fill:#121A21;stroke:#E7ECEF}
.eh{fill:#E7A6E3}.em{fill:#B657B2}.ea{fill:#241D2B;stroke:#B657B2}.ems{fill:#121A21;stroke:#B657B2}.tb{fill:#121A21}}
</style>"""
CIUDAD = (-0.415, 39.44, -0.322, 39.499)


class Proy:
    def __init__(self, lon0, lat0, lon1, lat1, ancho):
        self.lon0, self.lat1 = lon0, lat1
        self.c = math.cos(math.radians((lat0 + lat1) / 2))
        self.k = ancho / ((lon1 - lon0) * self.c)
        self.w, self.h = ancho, round((lat1 - lat0) * self.k)

    def __call__(self, lon, lat):
        return round((lon - self.lon0) * self.c * self.k, 1), round((self.lat1 - lat) * self.k, 1)

    def dentro(self, x, y, m=20):
        return -m <= x <= self.w + m and -m <= y <= self.h + m


def lineas(pr, lista, clase):
    d = []
    for coords in lista:
        pts = [pr(*c) for c in coords]
        if any(pr.dentro(x, y) for x, y in pts):
            d.append("M" + "L".join(f"{x:g},{y:g}" for x, y in pts))
    return f'<path class="{clase}" d="{"".join(d)}"/>' if d else ""


# 07/11/2026: el fondo era solo las vías «principales» recortadas al núcleo de los siniestros (R["mapa"]["princ"]) y se
# veían calles cortadas o sueltas. Ahora es toda la red del callejero municipal (ejes.geojson) recortada a la caja CIUDAD:
# avenidas, grandes vías, paseos, rondas, bulevares, puentes y carreteras en «c1» (más gruesas) y el resto en «c0» (finas y
# claras), unidas (union_all + line_merge) y simplificadas a 4 m en EPSG:25830 para que cada SVG pese poco.
PRINCIPALES = {"AVINGUDA", "GRAN VIA", "PASSEIG", "BULEVARD", "RONDA", "PONT", "CARRETERA"}
_FONDO = {}


def fondo(pr):
    if pr.w not in _FONDO:
        import geopandas as gpd, shapely
        caja = gpd.GeoSeries([shapely.box(*CIUDAD)], crs=4326).to_crs(25830).iloc[0].buffer(200)
        ejes = gpd.read_file(ROOT / "data/raw/siniestros/ejes.geojson").to_crs(25830)
        ejes = ejes[ejes.intersects(caja)]
        capas = []
        for clase, sel in (("c0", ~ejes.tipcalle.isin(PRINCIPALES)), ("c1", ejes.tipcalle.isin(PRINCIPALES))):
            red = shapely.line_merge(ejes[sel].geometry.union_all().intersection(caja)).simplify(4)
            red = gpd.GeoSeries([red], crs=25830).explode(index_parts=False).to_crs(4326)
            capas.append(lineas(pr, [list(ln.coords) for ln in red if not ln.is_empty], clase))
        _FONDO[pr.w] = "".join(capas)
    return _FONDO[pr.w]


def svg_mapa(pr, cuerpo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {pr.w} {pr.h}">{ESTILO_MAPA}'
            f'<rect class="bg" width="{pr.w}" height="{pr.h}"/>{fondo(pr)}{cuerpo}</svg>')


def quesito(x, y, r, c):
    n = sum(c.values())
    if len(c) == 1:
        return f'<circle class="pt {next(iter(c))}" cx="{x}" cy="{y}" r="{r}"/>'
    out, a0 = [f'<circle class="pt x" cx="{x}" cy="{y}" r="{r}"/>'], -math.pi / 2
    for cl in "bpa":
        if not c.get(cl): continue
        a1 = a0 + 2 * math.pi * c[cl] / n
        x0, y0, x1, y1 = x + r * math.cos(a0), y + r * math.sin(a0), x + r * math.cos(a1), y + r * math.sin(a1)
        out.append(f'<path class="{cl}" d="M{x},{y}L{x0:.1f},{y0:.1f}A{r},{r} 0 {1 if a1 - a0 > math.pi else 0} 1 {x1:.1f},{y1:.1f}Z"/>')
        a0 = a1
    return "".join(out) + f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" class="pt"/>'


def mapas():
    out = {}
    pr = Proy(*CIUDAD, 1000)
    g = {}
    for p in O["pts"]:
        g.setdefault((p[0], p[1]), collections.Counter())[p[3]] += 1
    cuerpo = []
    for (lon, lat), c in sorted(g.items(), key=lambda kv: -sum(kv[1].values())):
        x, y = pr(lon, lat)
        if pr.dentro(x, y, 0): cuerpo.append(quesito(x, y, round(1.5 + math.sqrt(sum(c.values())), 1), c))
    out["todos"] = svg_mapa(pr, "".join(cuerpo))
    cuerpo = []
    tur = next((n for n in O["negros"] if n.get("zona")), None)
    if tur:
        cuerpo.append('<polygon class="zona" points="' + " ".join(f"{x},{y}" for x, y in (pr(*c) for c in tur["zona"])) + '"/>')
    for n in sorted(O["negros"][:30], key=lambda n: -n["n"]):
        x, y = pr(n["lon"], n["lat"]); r = round(5 + 2.1 * math.sqrt(n["n"]), 1)
        cuerpo.append(f'<circle class="pt k" cx="{x}" cy="{y}" r="{r}" fill-opacity=".88"/>')
    out["lugares"] = svg_mapa(pr, "".join(cuerpo))
    cuerpo = [lineas(pr, R["mapa"]["ciclo"], "cl")]
    for u in sorted(O["uso"], key=lambda u: u["lv"]):
        x, y = pr(u["lon"], u["lat"])
        # 07/11/2026: «claramente» (rojo, grande) y «quizá» (anillo grueso) se distinguen por color, forma y tamaño
        cuerpo.append(f'<circle class="{ {2: "ux", 1: "um", 0: "hu"}[u["lv"]] }" cx="{x}" cy="{y}" r="{12 if u["lv"] == 2 else 9 if u["lv"] else 6}"/>')
    out["uso"] = svg_mapa(pr, "".join(cuerpo))
    cuerpo = []
    for i, p in enumerate(O["pla"]["pts"], 1):
        x, y = pr(p[0], p[1]); est = p[2]; r = 12
        if est == "hecha": cuerpo.append(f'<circle class="eh pt" cx="{x}" cy="{y}" r="{r}"/>')
        elif est == "en_marcha": cuerpo.append(f'<circle class="ems" cx="{x}" cy="{y}" r="{r}"/><path class="em" d="M{x},{y - r} A{r},{r} 0 0 0 {x},{y + r} Z"/>')
        elif est == "anunciada": cuerpo.append(f'<circle class="ea" cx="{x}" cy="{y}" r="{r}"/>')
        else: cuerpo.append(f'<circle class="hu" cx="{x}" cy="{y}" r="{r}" stroke-dasharray="3 2"/>')
    out["medidas"] = svg_mapa(pr, "".join(cuerpo))
    for k, v in out.items():
        S.escribir(BUILD / "img" / f"mapa_{k}.svg", v)


# ---------------------------------------------------------------- gráficos en línea (clases de comun.css)
def ticks(maximo, n=4):
    paso = 10 ** math.floor(math.log10(maximo / n))
    for m in (1, 2, 2.5, 5, 10):
        if maximo / (paso * m) <= n: paso *= m; break
    return [i * paso for i in range(int(maximo // paso) + 2) if i * paso <= maximo * 1.15]


def barras_apiladas(anys, filas, etq, alto=190, ancho=440):
    ml, mr, mt, mb = 44, 8, 22, 30
    tot = [sum(f) for f in filas]; tk = ticks(max(max(tot), 1)); top = max(tk[-1], max(tot))
    y = lambda v: mt + (alto - mt - mb) * (1 - v / top)
    paso = (ancho - ml - mr) / len(anys); bw = min(64, paso * .56)
    s = [f'<svg class="graf w{ancho}" viewBox="0 0 {ancho} {alto}" role="img" aria-label="{ESC(etq)}">']
    for t in tk:
        s.append(f'<line class="rej" x1="{ml}" x2="{ancho - mr}" y1="{y(t):.1f}" y2="{y(t):.1f}"/><text class="tn" x="{ml - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{num(t)}</text>')
    s.append(f'<line class="eje" x1="{ml}" x2="{ancho - mr}" y1="{y(0)}" y2="{y(0)}"/>')
    for i, (a, f) in enumerate(zip(anys, filas)):
        x = ml + paso * i + (paso - bw) / 2; base = 0
        for cl, v in zip(("b", "p", "a"), f):
            if v:
                y0, y1 = y(base), y(base + v)
                s.append(f'<rect class="{cl}" x="{x:.1f}" y="{y1 + 1:.1f}" width="{bw:.1f}" height="{max(y0 - y1 - 2, 1):.1f}" rx="2"/>'); base += v
        s.append(f'<text class="val" x="{x + bw / 2:.1f}" y="{y(base) - 6:.1f}" text-anchor="middle">{num(base)}</text>'
                 f'<text x="{x + bw / 2:.1f}" y="{alto - 8}" text-anchor="middle">{a}</text>')
    return "".join(s) + "</svg>"


def lineas_svg(xs, series, etq, alto=300, ancho=640, ymin=0, ymax=None, banda=None, fmt=num, marcas=None, xlabs=None, mr=None, fin_dentro=False):
    ml, mr0, mt, mb = (48, 120, 24, 40) if ancho > 560 else (66, 70, 30, 40)
    mr = mr or mr0
    todos = [v for se in series for _, v in se[1]] + ([h for _, _, h in banda] if banda else [])
    ymax = ymax or max(todos) * 1.08
    tk = [t for t in ticks(ymax - ymin) if ymin + t <= ymax]
    X = lambda a: ml + (ancho - ml - mr) * (a - xs[0]) / (xs[-1] - xs[0])
    Y = lambda v: mt + (alto - mt - mb) * (1 - (v - ymin) / (ymax - ymin))
    s = [f'<svg class="graf w{ancho}" viewBox="0 0 {ancho} {alto}" role="img" aria-label="{ESC(etq)}">']
    for t in tk:
        v = ymin + t
        s.append(f'<line class="rej" x1="{ml}" x2="{ancho - mr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text class="tn" x="{ml - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{fmt(v)}</text>')
    for a in xlabs or xs:
        s.append(f'<text x="{X(a):.1f}" y="{alto - 8}" text-anchor="middle">{a}</text>')
    if banda:
        pts = [(X(a), Y(h)) for a, _, h in banda] + [(X(a), Y(l)) for a, l, _ in reversed(banda)]
        s.append('<polygon class="banda" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
    for serie in series:
        cl, pts, et = serie[:3]; dy = serie[3] if len(serie) > 3 else 0
        s.append(f'<path class="{cl}" d="M' + "L".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in pts) + '"/>')
        if cl != "lg":
            s += [f'<circle class="{ {"lb": "b", "lp": "p", "lk": "k"}[cl] }" cx="{X(a):.1f}" cy="{Y(v):.1f}" r="4"/>' for a, v in pts]
        if et:
            a, v = pts[-1]
            s.append(f'<text class="val" x="{X(a):.1f}" y="{Y(v) - 12 + dy:.1f}" text-anchor="end">{et}</text>' if fin_dentro
                     else f'<text class="val" x="{X(a) + 10:.1f}" y="{Y(v) + 4 + dy:.1f}">{et}</text>')
    for a, v, t in marcas or []:
        s.append(f'<text class="val" x="{X(a):.1f}" y="{Y(v):.1f}" text-anchor="middle">{t}</text>')
    return "".join(s) + "</svg>"


def graf_lang(f):
    """Pinta un gráfico en las dos lenguas (sus etiquetas cambian)."""
    return f'<div data-l="va">{f("va")}</div><div data-l="es" lang="es">{f("es")}</div>'


# ---------------------------------------------------------------- inicio
def p_inicio():
    R_ = ""
    tot = R["tot"]; base, meta = E0["base"], E0["meta"]
    pe = P["por_estado"]; n_med = P["n"]
    k = O["ciudad"]["k"]; ntot = O["cob"]["total"]; ngeo = O["cob"]["geo"]
    motor = de_cada(k["m"] / ntot)
    top30 = sum(n["n"] for n in O["negros"][:30]); uno_de = round(ngeo / top30)
    amb_ult = O["ciudad"]["vy3"][-1][2]; dv = R["vmp"][-1] - R["vmp"][0]
    s1, n1 = ficha_top(1)
    calle_top = max((f for f in FICHAS if f[0] == "carrer"), key=lambda f: f[4])
    maxim = R["meta"]["max"]
    sube_ciudad = CT["ciudad"][-1] / CT["ciudad"][0] - 1
    sube_bv = tot[-1] / tot[0] - 1
    # la conclusión de la tarjeta: ¿suben más, menos o igual que todos los accidentes de la ciudad? (±2 puntos = «igual»)
    if abs(sube_bv - sube_ciudad) <= 0.02:
        ritmo = T(f"Però tots els accidents de trànsit de la ciutat han pujat igual, un {pct(sube_ciudad)}.",
                  f"Pero todos los accidentes de tráfico de la ciudad han subido lo mismo, un {pct(sube_ciudad)}.")
    else:
        mas = sube_bv > sube_ciudad
        ritmo = T(f"Han pujat un {pct(sube_bv)}, {'més' if mas else 'menys'} que el total d'accidents de trànsit de la ciutat (un {pct(sube_ciudad)}).",
                  f"Han subido un {pct(sube_bv)}, {'más' if mas else 'menos'} que el total de accidentes de tráfico de la ciudad (un {pct(sube_ciudad)}).")
    aprob = P["plan_doc"]["aprob"]
    cuerpo = f'''<div class="portada">
<h1>{T(*S.TITULO)}</h1>
<p class="apoyo">{T(*S.APOYO)}</p>
<p class="quien">{T("Observatori ciutadà independent · dades del portal de dades obertes de l'Ajuntament", "Observatorio ciudadano independiente · datos del portal de datos abiertos del Ayuntamiento")}</p>
<form class="gran-busca" role="search" data-busca action="mapa/">
<label for="busca-portada">{T("Busca el teu carrer o una cruïlla", "Busca tu calle o un cruce")}</label>
<div class="caja"><input id="busca-portada" name="cerca" type="search" autocomplete="off" aria-controls="sug-portada" placeholder="Pérez Galdós"><button type="submit">{T("Cerca", "Buscar")}</button><ul class="sug" id="sug-portada" hidden></ul></div>
<p class="ej">{T("Per exemple:", "Por ejemplo:")} <a href="lloc/{s1}/">{T(f"«{ESC(limpio(n1[0]))}»", f"«{ESC(limpio(n1[1]))}»")}</a> {T("o", "o")} <a href="carrer/{calle_top[1]}/">{T(f"«{ESC(calle_top[2])}»", f"«{ESC(calle_top[3])}»")}</a>. {T("També pots consultar la llista de", "También puedes consultar la lista de")} <a href="carrer/">{T("tots els carrers", "todas las calles")}</a> {T("i de", "y de")} <a href="lloc/">{T("tots els llocs", "todos los lugares")}</a>.</p>
</form>
</div>
<ul class="puertas rej-cifras">
<li><div class="tc">
<h2 class="tc-preg">{T("Què està passant?", "¿Qué está pasando?")}</h2>
<span class="tc-etq">{T(f"Accidents amb bici o patinet en {A1}", f"Accidentes con bici o patinete en {A1}")}</span>
<span class="tc-cifra">{num(tot[-1])}</span>
<span class="tc-texto"><span class="tc-frase">{T(f"És la xifra més alta de la sèrie ({A0}-{A1}); en {A0} n'hi va haver {num(tot[0])}." if maxim else f"En {A0} n'hi va haver {num(tot[0])}.", f"Es la cifra más alta de la serie ({A0}-{A1}); en {A0} hubo {num(tot[0])}." if maxim else f"En {A0} hubo {num(tot[0])}.")} {ritmo}</span>
<span class="tc-nota">{T(f"A més, al {MESES['va'][int(SIASV[5:7]) - 1]} de {SIASV[:4]} la Policia Local va canviar la manera de registrar-los, i això complica comparar els anys.", f"Además, en {mes_any(SIASV, 'es')} la Policía Local cambió su forma de registrarlos, lo que complica comparar los años.")}</span></span>
<a class="mas" href="mapa/">{T("Mira en el mapa on passen →", "Ver en el mapa dónde ocurren →")}</a></div></li>
<li><div class="tc">
<h2 class="tc-preg">{T("Què està fent l'Ajuntament?", "¿Qué está haciendo el Ayuntamiento?")}</h2>
<span class="tc-etq">{T("Mesures fetes", "Medidas hechas")}</span>
<span class="tc-cifra">{pe['hecha']}<small> {T("de", "de")} {n_med}</small></span>
<span class="tc-texto"><span class="tc-frase">{T(f"De les {n_med} mesures que seguim, <a href='ajuntament/#f=hecha'>{pe['hecha']} estan fetes</a>, <a href='ajuntament/#f=en_marcha'>{pe['en_marcha']} estan en marxa</a> i <a href='ajuntament/#f=anunciada'>{pe['anunciada']}, anunciades</a>.", f"De las {n_med} medidas que seguimos, <a href='ajuntament/#f=hecha'>{pe['hecha']} están hechas</a>, <a href='ajuntament/#f=en_marcha'>{pe['en_marcha']} están en marcha</a> y <a href='ajuntament/#f=anunciada'>{pe['anunciada']}, anunciadas</a>.")}<span class="minibarra" aria-hidden="true"><i style="flex:{pe['hecha']};background:var(--e-hecha)"></i><i style="flex:{pe['en_marcha']};background:var(--e-marcha)"></i><i style="flex:{pe['anunciada']};background:var(--e-anun)"></i><i style="flex:{pe['sin_info']};background:var(--line)"></i></span></span>
<span class="tc-nota">{T(f"De les <a href='ajuntament/#f=sin_info'>altres {pe['sin_info']}</a> encara no hem trobat informació pública. Quasi totes les mesures són del Pla Director de Seguretat Viària 2026-2030, que es va aprovar el {fecha_larga(aprob, 'va')}.", f"De las <a href='ajuntament/#f=sin_info'>otras {pe['sin_info']}</a> todavía no hemos encontrado información pública. Casi todas las medidas son del Plan Director de Seguridad Vial 2026-2030, que se aprobó el {fecha_larga(aprob, 'es')}.")}</span></span>
<a class="mas" href="ajuntament/">{T(f"Mira les {n_med} mesures →", f"Ver las {n_med} medidas →")}</a></div></li>
<li><div class="tc">
<h2 class="tc-preg">{T("Funciona?", "¿Funciona?")}</h2>
<span class="tc-etq">{T(f"Encara no ho sabem. Objectiu: la meitat en {R['meta']['año_meta']}", f"Todavía no lo sabemos. Objetivo: la mitad en {R['meta']['año_meta']}")}</span>
<span class="tc-cifra tc-cifra-par">{num(base)}<small> → {num(meta)}</small></span>
<span class="tc-texto"><span class="tc-frase">{T(f"Sabrem si baixen al ritme necessari quan es publiquen les dades de {R['meta']['pendiente']}. Una de les accions del Pla vol reduir aquests accidents a la meitat: dels {num(base)} de {E0['año']} a {num(meta)} en {R['meta']['año_meta']}.", f"Sabremos si bajan al ritmo necesario cuando se publiquen los datos de {R['meta']['pendiente']}. Una de las acciones del Plan quiere reducir estos accidentes a la mitad: de los {num(base)} de {E0['año']} a {num(meta)} en {R['meta']['año_meta']}.")}</span>
<span class="tc-nota">{T(f"El Pla no diu des de quin any es compta; nosaltres prenem {E0['año']}.", f"El Plan no dice desde qué año se cuenta; nosotros tomamos {E0['año']}.")}</span></span>
<a class="mas" href="informe/2025/#objectiu">{T("Mira d'on partim i el ritme necessari →", "Ver de dónde partimos y el ritmo necesario →")}</a></div></li>
</ul>
<section class="bloque">
<h2>{T("On hi ha més accidents de bici i patinet", "Dónde hay más accidentes de bici y patinete")}</h2>
<p class="intro">{T(f"Cada cercle marca on hi va haver accidents amb bici o patinet de {A0} a {A1}, segons l'adreça que va anotar la policia. Toca el mapa per a obrir-lo.", f"Cada círculo marca dónde hubo accidentes con bici o patinete de {A0} a {A1}, según la dirección que anotó la policía. Toca el mapa para abrirlo.")}</p>
<a class="vista" href="mapa/"><div class="mapa"><img src="img/mapa_todos.svg" width="1000" height="{Proy(*CIUDAD, 1000).h}" alt=""></div><span class="abrir">{T("Obri el mapa →", "Abrir el mapa →")}</span></a>
<div class="ley"><span><i class="pt b"></i>{T("Accident amb bici (sense patinet)", "Accidente con bici (sin patinete)")}</span><span><i class="pt p"></i>{T("Accident amb patinet (sense bici)", "Accidente con patinete (sin bici)")}</span><span><i class="pt a"></i>{T("Xoc entre bici i patinet", "Choque entre bici y patinete")}</span><span class="nota">{T("Un cercle més gran vol dir més accidents, no més trànsit.", "Un círculo más grande indica más accidentes, no más tráfico.")}</span></div>
</section>
<section class="bloque">
<h2>{T("Quatre dades sobre els accidents de bici i patinet", "Cuatro datos sobre los accidentes de bici y patinete")}</h2>
<ul class="datos4 rej-cifras">
<li class="tc"><span class="tc-etq">{T(f"Accidents amb un vehicle de motor, {PER}", f"Accidentes con un vehículo de motor, {PER}")}</span>
<span class="tc-cifra">{pct(k['m'] / ntot)}</span>
<span class="tc-texto"><span class="tc-frase">{T(f"{motor[0][0].upper() + motor[0][1:]} accidents amb bici o patinet impliquen un cotxe, una moto o un altre vehicle de motor.", f"{motor[1][0].upper() + motor[1][1:]} accidentes con bici o patinete implican a un coche, una moto u otro vehículo de motor.")}</span></span>
<a class="mas" href="lloc/{s1}/">{T("Amb qui xoquen en cada lloc →", "Con quién chocan en cada lugar →")}</a></li>
<li class="tc"><span class="tc-etq">{T(f"Accidents amb patinet en {A1}", f"Accidentes con patinete en {A1}")}</span>
<span class="tc-cifra">{num(R['vmp'][-1])}</span>
<span class="tc-texto"><span class="tc-frase">{T(f"Són {num(abs(dv))} {'més' if dv > 0 else 'menys'} que en {A0}. Els de bici gairebé no han canviat: de {num(R['bici'][0])} a {num(R['bici'][-1])}.", f"Son {num(abs(dv))} {'más' if dv > 0 else 'menos'} que en {A0}. Los de bici apenas cambiaron: de {num(R['bici'][0])} a {num(R['bici'][-1])}.")}</span>
<span class="tc-nota">{T(f"Un xoc entre bici i patinet compta en les dues xifres ({num(amb_ult)} en {A1}).", f"Un choque entre bici y patinete cuenta en las dos cifras ({num(amb_ult)} en {A1}).")}</span></span>
<a class="mas" href="informe/2025/#patinet">{T("Mira com canvien any a any →", "Ver cómo cambian año a año →")}</a></li>
<li class="tc"><span class="tc-etq">{T(f"Accidents en els 30 llocs amb més, {PER}", f"Accidentes en los 30 lugares con más, {PER}")}</span>
<span class="tc-cifra">{num(top30)}</span>
<span class="tc-texto"><span class="tc-frase">{T(f"Només 30 cruïlles i trams de carrer reuneixen 1 de cada {uno_de} accidents dels que hi ha en el mapa.", f"Solo 30 cruces y tramos de calle reúnen 1 de cada {uno_de} accidentes de los que hay en el mapa.")}</span></span>
<a class="mas" href="mapa/#llocs">{T("Mira els 30 llocs →", "Ver los 30 lugares →")}</a></li>
<li class="tc"><span class="tc-etq">{T(f"Xocs amb una persona a peu, {PER} (almenys)", f"Choques con una persona a pie, {PER} (al menos)")}</span>
<span class="tc-cifra">{num(k['w'])}</span>
<span class="tc-texto"><span class="tc-frase">{T("Una bici o un patinet va xocar amb algú que anava a peu, sense cap cotxe ni moto pel mig. N'hi ha almenys aquests, i segurament més.", "Una bici o un patinete chocó con alguien que iba a pie, sin ningún coche ni moto de por medio. Hay al menos estos, y seguramente más.")}</span>
<span class="tc-nota">{T("Fins a mitjan 2024, molts comunicats de la policia no recollien la persona atropellada. Per això no podem dir si pugen o baixen.", "Hasta mediados de 2024, muchos partes de la policía no recogían a la persona atropellada. Por eso no podemos decir si suben o bajan.")}</span></span>

<a class="mas" href="dades/#limits">{T("Per què no es poden comparar els anys →", "Por qué no se pueden comparar los años →")}</a></li>
</ul>
</section>
{S.telegram_invitacion("h-tg", R_)}
<aside class="capa-sig" aria-labelledby="h-capa">
<h2 id="h-capa">{T("Vols saber-ne més?", "¿Quieres saber más?")}</h2>
<a href="informe/2025/">{T(f"Informe {A1}: què ha passat i si els accidents baixen al ritme necessari per a {R['meta']['año_meta']} →", f"Informe {A1}: qué ha pasado y si los accidentes bajan al ritmo necesario para {R['meta']['año_meta']} →")}</a>
<a href="dades/">{T("Dades i mètode: d'on ixen les dades i com les tractem →", "Datos y método: de dónde salen los datos y cómo los tratamos →")}</a>
<p class="nota">{T("Dades del portal de dades obertes de l'Ajuntament de València.", "Datos del portal de datos abiertos del Ayuntamiento de València.")}</p>
</aside>'''
    t = (S.MARCA[0] + " · " + S.TITULO[0], S.MARCA[1] + " · " + S.TITULO[1]); d = (S.APOYO[0], S.APOYO[1])
    html = S.pagina("inici", "", R_, t, d, cuerpo, INFO, None, "og/observatori.png")
    S.escribir(BUILD / "index.html", html)


# ---------------------------------------------------------------- páginas con la lógica de la web anterior (mapa, método)
def publicar_datos(fichero, nombre):
    b = (W / "datos" / fichero).read_bytes()
    return S.recurso(b, nombre, "js")


def css_viejo(plantilla, ambito):
    """El <style> de la plantilla vieja sin lo que choca con la cabecera común (cabecera, marca, cuerpo, enlaces)."""
    css = re.search(r"<style>(.*?)</style>", plantilla, re.S).group(1)
    fuera = ("a{", ".wrap{", "header.top", "body::before", ".top ", ".marca", ".senal", ".proto", ".navlink", "h1,h2,h3{")
    lin = []
    for x in css.split("\n"):
        st = x.strip()
        if st.startswith(fuera): continue
        if st.startswith("--display:") or st.startswith("--body:"): continue
        if st.startswith("body{"):
            m = re.search(r"font-size:[^;}]+;line-height:[^;}]+", st)
            lin.append(f"{ambito}{{font-size:var(--t-body);line-height:1.55}}"); continue
        # escala de la web nueva (textos_grandes): la web anterior escribía la prosa a 13-17 px y las etiquetas a 11,5-12,5 px.
        # Prosa (13 px o más en la vieja) → --t-body (18-19 px); etiquetas cortas (menos de 13 px) → --t-meta (16 px); los
        # títulos (más de 17 px) se quedan como estaban.
        x = re.sub(r"font-size:(\d+(?:\.\d+)?)px", lambda m: ("font-size:var(--t-meta)" if float(m.group(1)) < 13
                   else "font-size:var(--t-body)" if float(m.group(1)) <= 17 else m.group(0)), x)
        # sin columnas estrechas: la prosa ocupa el ancho del contenido, como en el resto de la web
        x = re.sub(r"max-width:\d+ch", "max-width:none", x)
        # ni anchos fijos de columna de lectura (main section{max-width:760px} del método; no las @media) — 07/11/2026
        x = re.sub(r"(?<!\()max-width:(\d+)px", lambda m: "max-width:none" if 600 <= int(m.group(1)) <= 1100 else m.group(0), x)
        # el estilo de la web nueva: etiquetas en minúscula normal, sin espaciado de letras (las mayúsculas espaciadas de
        # la web anterior, subidas a 16-19 px, gritaban: revisión de diseño del 07/11/2026)
        x = re.sub(r"font-size:(\.\d+)em", r"font-size:max(\1em,15px)", x)      # nada por debajo de 15 px (código, notas)
        x = re.sub(r"text-transform:uppercase;?", "", x)

        x = re.sub(r"letter-spacing:\.?\d*\.?\d+em;?", "", x)
        lin.append(x)
    return ("<style>" + "\n".join(lin) + "\n" + ambito + " h1," + ambito + " h2," + ambito + " h3{font-family:var(--display);text-wrap:balance}\n.vieja .mapa-sec>.eyebrow{display:none}.vieja #t-mapa{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;margin:0}"
            "\n.vieja p.ref{font-size:var(--t-body)}.vieja button,.vieja select,.vieja input,.vieja sup,.vieja sub,.vieja code,.vieja kbd{font-size:var(--t-meta)}.vieja h5{font-size:var(--t-body)}.vieja th{font-size:var(--t-meta)!important}"
            "\n.vieja .seg button{font-family:var(--display);font-weight:600;font-size:var(--t-body);border:1px solid var(--line);background:var(--surface);color:var(--ink);padding:6px 12px;cursor:pointer;border-radius:3px}"
            "\n.vieja .seg button[aria-pressed=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}"
            # ficha del mapa: dos columnas como mucho (antes 4 de unos 250 px) y etiquetas como las de la web nueva
            "\n.vieja .secs{grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr));gap:12px 32px}"
            "\n.vieja .eyebrow,.vieja .ficha h4,.vieja .selbar .et{font-family:var(--display);font-weight:700;color:var(--ink2)}"
            "\n.vieja .b-comp{font-size:var(--t-meta);min-height:44px;padding:6px 14px;border-radius:8px;border:1.5px solid var(--ink)}"
            "\n.vieja select,.vieja input[type=search]{min-height:44px;padding:6px 10px;border-radius:6px}"
            "\n.vieja .zoom button{width:44px;height:44px}"
            "\n.vieja #ver{min-height:44px;padding:6px 12px}.vieja .c-pla{min-height:44px;display:inline-flex;align-items:center;gap:8px}.vieja .c-pla input{width:22px;height:22px}"

            "\n.vieja #res li.sin{padding:10px 12px;color:var(--ink2)}"
            # en el móvil, el mapa primero: vistas y buscador, mapa, ficha; los filtros, después (antes empezaba a unos 1.160 px)
            "\n@media (max-width:700px){.vieja .mapa-sec{display:flex;flex-direction:column}.vieja .mapa-sec>*{order:3}"
            ".vieja .mapa-sec>.controles:not(.filtros-fila){order:1}.vieja .mapa-sec>.mapa-wrap{order:2}"
            ".vieja .mapa-sec>.filtros-fila,.vieja .mapa-sec>#avis-grav,.vieja .mapa-sec>#f-resum,.vieja .mapa-sec>#expl{order:4}}</style>")




def enlaces_viejos(txt, R_):
    txt = txt.replace("observatori.html", f"{R_}mapa/").replace("metode.html", f"{R_}metode/").replace("pla.html", f"{R_}ajuntament/")
    txt = txt.replace("informe.html", f"{R_}informe/2025/").replace("cambios.html", f"{R_}sobre/#canvis")
    return txt


def accidentes(txt):
    """Vocabulario de la web pública (la guía interna de estilo, decisiones confirmadas): «accidentes / accidents» en el texto
    público; «siniestros / sinistres» solo en el método. Para el mapa, que hereda los textos de la web anterior."""
    txt = re.sub(r"\b([Dd])e (sinistres?)\b", lambda m: m.group(1) + "'accident" + ("s" if m.group(2).endswith("s") else ""), txt)
    txt = re.sub(r"(?<![\w-])([Ss])inistre(s?)(?![\w-])", lambda m: ("A" if m.group(1) == "S" else "a") + "ccident" + m.group(2), txt)
    txt = re.sub(r"(?<![\w-])([Ss])iniestro(s?)(?![\w-])", lambda m: ("A" if m.group(1) == "S" else "a") + "ccidente" + m.group(2), txt)
    return txt


def agrupar_lineas(fc):
    """FeatureCollection de líneas → una MultiLineString por combinación de propiedades (las mismas coordenadas, sin fundir
    ni simplificar). Si hay otra geometría, la deja como está."""
    if any(f["geometry"]["type"] not in ("LineString", "MultiLineString") for f in fc["features"]): return fc
    grupos = {}
    for f in fc["features"]:
        g = f["geometry"]
        grupos.setdefault(json.dumps(f["properties"], sort_keys=True), []).extend(g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]])
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": json.loads(k), "geometry": {"type": "MultiLineString", "coordinates": co}}
                                                      for k, co in sorted(grupos.items())]}


def derivar(plantilla, datos_js, nombre, R_, ocultar=(), aparte=None):
    """Cuerpo de una página vieja dentro de la cabecera nueva: devuelve (css, html, scripts) sin <head> ni cabecera ni pie.
    La lógica (scripts en línea) no se reescribe: solo se cambian las rutas y los nodos que ya no se ven quedan ocultos."""
    t = (W / plantilla).read_text()
    css = css_viejo(t, ".vieja")
    cuerpo = t[t.index("</style>") + len("</style>"):]
    cuerpo = cuerpo.replace("<script>/*TEMA_JS*/</script>", "").replace("<script>/*PIE_JS*/</script>", "")
    # cabecera vieja → sus botones de lengua, ocultos (sitio.js los pulsa al cambiar de lengua)
    cuerpo = re.sub(r'<header class="top">.*?</header>', '<div hidden><button id="l-va" aria-pressed="true">VA</button><button id="l-es" aria-pressed="false">ES</button></div>', cuerpo, count=1, flags=re.S)
    cuerpo = cuerpo.replace('<div class="wrap"><p class="proto" data-t="proto"></p></div>', "")
    cuerpo = re.sub(r'<footer class="wrap" data-pie></footer>', "", cuerpo)
    for sel in ocultar:
        assert cuerpo.count(sel) == 1, (plantilla, sel)
        cuerpo = cuerpo.replace(sel, sel[:-1] + " hidden>")
    if aparte:
        # claves que no hacen falta para el primer pintado (07/11/2026: las calles del fondo del mapa, 1,7 MB de 2,8): van
        # en su propio recurso (<nombre>-<clave>.<hash8>.js, window.OBS_<CLAVE>, con SRI) que la página pide después. Las
        # líneas con las mismas propiedades se agrupan en una sola MultiLineString (agrupar_lineas): mismas coordenadas (5
        # decimales) y mismo dibujo, en 0,6 MB en vez de 1,7 (13.010 objetos «Feature» menos que leer y copiar al mapa)
        b = (W / "datos" / datos_js).read_bytes()
        m = re.match(rb"window\.(\w+)\s*=\s*", b)
        obj = json.loads(b[m.end():].decode().strip().rstrip(";"))
        for k in aparte:
            js = f"window.OBS_{k.upper()}=" + json.dumps(agrupar_lineas(obj.pop(k)), ensure_ascii=False, separators=(",", ":")) + ";"
            asrc, asri = S.recurso(js.encode(), f"{nombre}-{k}", "js")
            assert cuerpo.count(f'<div id="{aparte[k]}">') == 1, (plantilla, aparte[k])
            cuerpo = cuerpo.replace(f'<div id="{aparte[k]}">', f'<div id="{aparte[k]}" data-{k}="{R_}{asrc}" data-{k}-sri="{asri}">')
        src, sri = S.recurso((f"window.{m.group(1).decode()}=" + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + ";").encode(), nombre, "js")
    else:
        src, sri = publicar_datos(datos_js, nombre)
    carga = (W / "comun/carga.js").read_text()
    A = S.assets()
    fich = f'\n<script src="{R_}{A["fichas"]}" integrity="{A["fichas_sri"]}"></script>' if A.get("fichas") else ""
    cuerpo = cuerpo.replace("<script>/*DATA*/</script>", f'<script>{carga}</script>\n<script src="{R_}{src}" integrity="{sri}" onerror="__cargaFallo()"></script>{fich}')
    # el buscador del mapa enlaza las fichas con ruta relativa a la raíz
    cuerpo = cuerpo.replace('a.href=f[0]+"/"+f[1]+"/"', f'a.href="{R_}"+f[0]+"/"+f[1]+"/"')
    cuerpo = enlaces_viejos(cuerpo, R_)
    return css, cuerpo


# Al elegir un lugar o un punto (clic, Intro, buscador o enlace), la ficha se ve: si está fuera de la vista, se desplaza
# hasta ella (suave, sin animación con prefers-reduced-motion, con margen de la cabecera fija); si ya se ve, se resalta un
# momento. Foco al título (tabindex=-1) y aviso en la región aria-live. Las flechas, N y P (recorrer el mapa con el teclado)
# y la selección automática al cargar o al cambiar de vista o filtro (sinHash) no desplazan. Envuelve elegir() de la
# lógica anterior (declaración global de observatori.plantilla.html) sin reescribirla. «Volver al mapa»: sube al mapa con el
# lugar todavía elegido.
SELECCION = """<script>
(function(){
  if (typeof elegir !== "function") return;
  var orig = elegir, tecla = null;
  var reduce = function(){ return matchMedia("(prefers-reduced-motion: reduce)").matches; };
  var alto = function(){ var c = document.querySelector(".cabecera"); return c ? c.getBoundingClientRect().height : 0; };
  document.addEventListener("keydown", function(e){ tecla = e.key; }, true);
  document.addEventListener("pointerdown", function(){ tecla = null; }, true);
  function mostrar(){
    var w = document.getElementById("ficha-wrap"); if (!w) return;
    var t = w.querySelector("#ficha-top h2, #ficha-top h3, #ficha-top h4") || w;
    var r = t.getBoundingClientRect(), a = alto();
    w.style.scrollMarginTop = (a + 8) + "px";
    if (r.top >= a && r.bottom <= innerHeight) {
      w.classList.remove("resalta"); void w.offsetWidth; w.classList.add("resalta");
    } else {
      w.scrollIntoView({behavior: reduce() ? "auto" : "smooth", block: "start"});
    }
    t.setAttribute("tabindex", "-1"); t.focus({preventScroll: true});
    var an = document.getElementById("anunci");
    if (an) an.textContent = (document.documentElement.lang === "es" ? "Ficha: " : "Fitxa: ") + t.textContent.trim();
  }
  elegir = function(tipo, i, volar, sinHash){
    var r = orig.apply(this, arguments), k = tecla; tecla = null;
    if (sinHash) return r;
    if (k && k !== "Enter") return r;            // recorrer el mapa con el teclado: sin saltar a la ficha
    setTimeout(mostrar, 0);
    return r;
  };
  var v = document.getElementById("volver-mapa");
  if (v) v.addEventListener("click", function(){
    var m = document.getElementById("mapa"); m.style.scrollMarginTop = (alto() + 8) + "px";
    m.scrollIntoView({behavior: reduce() ? "auto" : "smooth", block: "start"});
    var c = m.querySelector("canvas"); if (c) c.focus({preventScroll: true});
  });
})();
</script>
"""


def p_mapa():
    R_ = "../"
    css, cuerpo = derivar("observatori.plantilla.html", "observatori.js", "web-mapa", R_, aparte={"calles": "mapa"}, ocultar=(
        '<section class="wrap entrada" aria-labelledby="t-entrada">', '<section class="wrap meta" id="funciona" aria-labelledby="t-meta">',
        '<section class="wrap" aria-labelledby="t-hall">', '<section class="wrap" aria-labelledby="t-dades">'))
    cuerpo = accidentes(cuerpo)
    # nombres de lugares y direcciones como los escribe una persona (scripts/nombres.py, los mismos que las fichas) y
    # títulos de las actuaciones del Plan en va y es (sitio_textos_plan.py): un recurso con SRI tras los datos del mapa
    noms = {}
    for p in O["pts"]: noms.setdefault(p[6], [N.direccion(p[6], "va"), N.direccion(p[6], "es")])
    for n in O["negros"]:
        for u, _ in n.get("ubis") or []: noms.setdefault(u, [N.direccion(u, "va"), N.direccion(u, "es")])
    for n in O["negros"]:
        v = [N.lugar(n["nom"], n.get("nom_es") or n["nom"], "va"), N.lugar(n["nom"], n.get("nom_es") or n["nom"], "es")]
        noms[n["nom"]] = v
        if n.get("nom_es"): noms[n["nom_es"]] = v
    ids = {p[7] for p in O["pla"]["pts"]} | {x[0] for n in O["negros"] for x in (n.get("pla") or [])}
    pla_t = {i: [TP.MEDIDAS[i]["tit"]["va"], TP.MEDIDAS[i]["tit"]["es"]] + ([TP.MEDIDAS[i]["lugar"]["va"], TP.MEDIDAS[i]["lugar"]["es"]] if TP.MEDIDAS[i].get("lugar") else [])
             for i in sorted(ids) if i in TP.MEDIDAS}
    js = ("window.NOMS=" + json.dumps(noms, ensure_ascii=False, separators=(",", ":")) + ";\nwindow.PLA_T="
          + json.dumps(pla_t, ensure_ascii=False, separators=(",", ":")) + ";\n").encode()
    nsrc, nsri = S.recurso(js, "mapa-nombres", "js")
    marca = 'onerror="__cargaFallo()"></script>'
    assert cuerpo.count(marca) == 1
    cuerpo = cuerpo.replace(marca, marca + f'\n<script src="{R_}{nsrc}" integrity="{nsri}" onerror="__cargaFallo()"></script>', 1)
    cuerpo = cuerpo.replace('<div class="ficha-wrap" id="ficha-wrap">', '<div class="ficha-wrap" id="ficha-wrap"><p class="volver-mapa"><button type="button" id="volver-mapa">'
                            + T("↑ Torna al mapa", "↑ Volver al mapa") + '</button></p>', 1)
    cuerpo = cuerpo.replace("<main>", '<div class="vieja">', 1).replace("</main>", "</div>", 1).replace('class="wrap mapa-sec"', 'class="mapa-sec"')
    # lista de los 10 primeros y los índices
    lis = []
    for n in O["negros"][:10]:
        slug, nom = ficha_top(n["rank"])
        lis.append(f'<li><a href="{R_}lloc/{slug}/">{T(ESC(limpio(nom[0])), ESC(limpio(nom[1])))}</a> · {num(n["n"])}</li>' if slug else f'<li>{ESC(n["nom"])} · {n["n"]}</li>')
    cob = O["kpi"]["cob_any"]
    top = f'''<section class="bloque" id="llocs">
<h2>{T(f"Els 10 llocs amb més accidents de bici i patinet ({PER})", f"Los 10 lugares con más accidentes de bici y patinete ({PER})")}</h2>
<ol class="lista-pts" style="font-size:var(--t-body)">{"".join(lis)}</ol>
<p class="nota">{T(f"El lloc en la llista té en compte que els primers anys es van poder situar en el mapa menys accidents ({round(cob[str(A0)] * 100)} de cada 100 en {A0} i {round(cob[str(A1)] * 100)} en {A1}): els d'aquells anys compten una mica més. Per això un lloc amb menys accidents pot anar per davant d'un altre.", f"El puesto tiene en cuenta que en los primeros años se pudieron situar en el mapa menos accidentes ({round(cob[str(A0)] * 100)} de cada 100 en {A0} y {round(cob[str(A1)] * 100)} en {A1}): los de esos años cuentan un poco más. Por eso un lugar con menos accidentes puede ir por delante de otro.")}</p>
<p><a class="mas" href="{R_}lloc/">{T("Tots els llocs amb fitxa →", "Todos los lugares con ficha →")}</a> &nbsp; <a class="mas" href="{R_}carrer/">{T("Tots els carrers amb fitxa →", "Todas las calles con ficha →")}</a></p>
</section>
<p class="nota" style="margin-top:18px">{T("Més accidents no vol dir més perill: pot ser que hi passe més gent.", "Más accidentes no quiere decir más peligro: puede que pase más gente.")} <a href="{R_}metode/#filtres">{T("Vols saber-ne més? →", "¿Quieres saber más? →")}</a></p>'''
    cab = (f'<h1 class="h1-pag">{T("On hi ha més accidents de bici i patinet a València", "Dónde hay más accidentes de bici y patinete en València")}</h1>'
           f'<p class="sub">{T(f"El mapa mostra els accidents amb bici o patinet de {A0} a {A1}. Toca un punt per a veure què passa en aquell lloc; filtra per any, vehicle o gravetat i descarrega el que veus.", f"El mapa muestra los accidentes con bici o patinete de {A0} a {A1}. Toca un punto para ver qué pasa en ese lugar; filtra por año, vehículo o gravedad y descarga lo que ves.")}</p>'
           f'<p class="nota">{T("Llista de", "Lista de")} <a href="{R_}lloc/">{T("tots els llocs", "todos los lugares")}</a> {T("i de", "y de")} <a href="{R_}carrer/">{T("tots els carrers", "todas las calles")}</a> {T("amb fitxa.", "con ficha.")} {T(f"De {A0} a {A1} hi va haver {num(O['cob']['total'])} accidents amb bici o patinet; el mapa en situa {num(O['cob']['geo'])}, perquè la resta no té una adreça precisa.", f"De {A0} a {A1} hubo {num(O['cob']['total'])} accidentes con bici o patinete; el mapa sitúa {num(O['cob']['geo'])}, porque el resto no tiene una dirección precisa.")} <a href="{R_}metode/#datos">{T("Com els situem", "Cómo los situamos")}</a>.</p>')
    # los scripts de la lógica van al final, tras el contenido: se separan del cuerpo
    i = cuerpo.index("<script>")
    html_, scr = cuerpo[:i], cuerpo[i:]
    t = ("Mapa d'accidents de bici i patinet · " + S.MARCA[0], "Mapa de accidentes de bici y patinete · " + S.MARCA[1])
    d = (f"On hi ha més accidents de bici i patinet a València ({PER}): mapa amb filtres per any, vehicle i gravetat, fitxa de cada lloc i descàrrega del que veus.",
         f"Dónde hay más accidentes de bici y patinete en València ({PER}): mapa con filtros por año, vehículo y gravedad, ficha de cada lugar y descarga de lo que ves.")
    pasos = [("inici", S.NOM["inici"]), (None, S.NOM["mapa"])]
    # conjunto, fecha de descarga y versión para el LLEGIU-ME / LEEME del ZIP de descarga (descargarCSV)
    pie_info = ("<script>window.PIE_INFO = "
                + json.dumps({k: INFO[k] for k in ("conjunto", "descarga", "version")}, ensure_ascii=False).replace("</", "<\\/")
                + ";window.DATAPACKAGE = "
                # descriptor Frictionless de cada lengua: el mapa mete en el ZIP el recurso de la vista descargada
                + json.dumps({l: SD.datapackage(INFO, A0, A1, l) for l in ("va", "es")}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
                + ";</script>\n")
    html = S.pagina("mapa", "mapa/", R_, t, d, cab + html_ + top, INFO, pasos, "og/observatori.png", extra_head=css,
                    extra_fin=pie_info + scr + "\n" + SELECCION, main_attrs=' data-pag="mapa"')
    S.escribir(BUILD / "mapa/index.html", html)


# ---------------------------------------------------------------- ¿Qué está haciendo el Ayuntamiento?
def fuente_de(a):
    """(url, título va, título es, tipo, fecha de la fuente). Si la principal es el propio Plan y hay una fuente en la nota,
    la que respalda el estado es esa (el Plan no prueba que se haya hecho)."""
    F = {f["n"]: f for f in P["fuentes"]}
    f = F.get(a.get("fn"))
    if (not f or f["tipo"] == "plan") and a.get("fnotas") and a["est"] != "sin_info":
        f = F[a["fnotas"][0]]
    if not f: return None
    tt = TP.TITULO_FUENTE.get(f["url"])
    return f["url"], (tt["va"] if tt else f["tit"]), (tt["es"] if tt else f["tit"]), f["tipo"]


def mapa_medidas_datos():
    """Datos del mapa de las medidas: calles del callejero (las de O['calles'], fundidas, simplificadas a ~8 m y con 4
    decimales: ~75 kB con gzip, en vez de 1,9 MB), red ciclista (capa 189, la misma que el mapa de accidentes) y las
    medidas con punto, numeradas como la lista. build/datos/ajuntament-mapa.<hash8>.js con SRI."""
    from shapely.geometry import shape, MultiLineString
    from shapely.ops import linemerge
    feats = []
    for m in (0, 1):
        ls = []
        for f in O["calles"]["features"]:
            if f["properties"]["m"] != m: continue
            g = shape(f["geometry"]); ls += list(g.geoms) if g.geom_type == "MultiLineString" else [g]
        g = linemerge(MultiLineString(ls)).simplify(0.00008)
        co = [[[round(x, 4), round(y, 4)] for x, y in l.coords] for l in (g.geoms if hasattr(g, "geoms") else [g])]
        feats.append({"type": "Feature", "properties": {"m": m}, "geometry": {"type": "MultiLineString", "coordinates": co}})
    med = [[p[0], p[1], p[2], p[7], i] for i, p in enumerate(O["pla"]["pts"], 1)]
    d = {"calles": {"type": "FeatureCollection", "features": feats}, "ciclo": O["ciclo"], "med": med}
    b = ("window.AJM=" + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n").encode()
    return S.recurso(b, "ajuntament-mapa", "js")


CON_PUNTO = {p[7]: i for i, p in enumerate(O["pla"]["pts"], 1)}

MAPA_MED_JS = """<script>
(function(){
  var D = window.AJM, el = document.getElementById("mapa-med");
  var lang = function(){ return document.documentElement.lang === "es" ? "es" : "va"; };
  if (!D || !el || !window.maplibregl) return;
  var css = function(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); };
  var reduce = function(){ return matchMedia("(prefers-reduced-motion: reduce)").matches; };
  var alto = function(){ var c = document.querySelector(".cabecera"); return c ? c.getBoundingClientRect().height : 0; };
  var lon = D.med.map(function(m){ return m[0]; }), lat = D.med.map(function(m){ return m[1]; });
  var caja = [[Math.min.apply(0, lon), Math.min.apply(0, lat)], [Math.max.apply(0, lon), Math.max.apply(0, lat)]];
  var map = new maplibregl.Map({container: el, bounds: caja, fitBoundsOptions: {padding: 40}, attributionControl: false,
    cooperativeGestures: true, dragRotate: false, pitchWithRotate: false, locale: lang() === "es" ? {
      "CooperativeGesturesHandler.WindowsHelpText": "Usa Ctrl + rueda para acercar o alejar el mapa", "CooperativeGesturesHandler.MacHelpText": "Usa ⌘ + rueda para acercar o alejar el mapa",
      "CooperativeGesturesHandler.MobileHelpText": "Usa dos dedos para mover el mapa", "NavigationControl.ZoomIn": "Acercar", "NavigationControl.ZoomOut": "Alejar",
      "Map.Title": "Mapa de las medidas", "Marker.Title": "Medida"} : {
      "CooperativeGesturesHandler.WindowsHelpText": "Fes servir Ctrl + roda per a acostar o allunyar el mapa", "CooperativeGesturesHandler.MacHelpText": "Fes servir ⌘ + roda per a acostar o allunyar el mapa",
      "CooperativeGesturesHandler.MobileHelpText": "Fes servir dos dits per a moure el mapa", "NavigationControl.ZoomIn": "Acosta", "NavigationControl.ZoomOut": "Allunya",
      "Map.Title": "Mapa de les mesures", "Marker.Title": "Mesura"},

    style: {version: 8, sources: {}, layers: [{id: "bg", type: "background", paint: {"background-color": css("--mapbg")}}]}});
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({showCompass: false}), "top-right");
  function colores(){
    map.setPaintProperty("bg", "background-color", css("--mapbg"));
    map.setPaintProperty("calles", "line-color", css("--calle"));
    map.setPaintProperty("ciclo", "line-color", css("--amb"));
  }
  map.on("load", function(){
    map.addSource("calles", {type: "geojson", data: D.calles});
    map.addSource("ciclo", {type: "geojson", data: D.ciclo});
    map.addLayer({id: "calles", type: "line", source: "calles", paint: {"line-color": css("--calle"),
      "line-width": ["interpolate", ["linear"], ["zoom"], 12, ["case", ["==", ["get", "m"], 1], 1.4, .4], 16, ["case", ["==", ["get", "m"], 1], 5, 2.5]]}});
    map.addLayer({id: "ciclo", type: "line", source: "ciclo", paint: {"line-color": css("--amb"), "line-opacity": .85,
      "line-width": ["interpolate", ["linear"], ["zoom"], 12, 1.2, 16, 3.5]}});
  });
  document.addEventListener("tema-cambiado", function(){ if (map.isStyleLoaded()) colores(); });
  var marcas = {};
  D.med.forEach(function(m){
    var b = document.createElement("button"); b.type = "button"; b.className = "mk " + m[2]; b.textContent = m[4];
    var li = document.querySelector('#llista-mapa li[data-id="' + m[3] + '"]');
    var nom = li ? li.textContent.trim() : m[3];
    b.addEventListener("click", function(e){ e.stopPropagation(); obrir(m[3]); });
    marcas[m[3]] = b;
    new maplibregl.Marker({element: b}).setLngLat([m[0], m[1]]).addTo(map);
    // después de addTo (MapLibre pone «Map marker»): número y medida; fuera del orden de Tab, porque la lista del costat
    // tiene lo mismo y un marcador fuera del recuadro recibía el foco invisible (prueba de teclado, 07/11/2026). «Mira-la en
    // el mapa» le da el foco por programa.
    b.setAttribute("aria-label", "n.º " + m[4] + ": " + nom); b.tabIndex = -1;
  });
  // abrir la medida en la lista y desplazarse a ella (mismo criterio que el mapa de accidentes)
  function obrir(id){
    var li = document.getElementById("a-" + id); if (!li) return;
    document.querySelectorAll(".filtro-lista .chip[data-f='']").forEach(function(c){ c.click(); });
    var d = li.querySelector("details"); d.open = true;
    var fl = document.querySelector(".filtro-lista"), extra = fl && getComputedStyle(fl).position === "sticky" ? fl.getBoundingClientRect().height : 0;
    scrollTo({top: li.getBoundingClientRect().top + scrollY - alto() - extra - 8, behavior: reduce() ? "auto" : "smooth"});
    var s = li.querySelector("summary"); s.focus({preventScroll: true});
  }
  // desde la lista: centrar el mapa en la medida y subir al mapa
  document.querySelectorAll(".ver-mapa").forEach(function(btn){ btn.addEventListener("click", function(){
    var id = btn.getAttribute("data-id"), m = D.med.filter(function(x){ return x[3] === id; })[0]; if (!m) return;
    el.style.scrollMarginTop = (alto() + 8) + "px";
    el.scrollIntoView({behavior: reduce() ? "auto" : "smooth", block: "start"});
    map.flyTo({center: [m[0], m[1]], zoom: 16, animate: !reduce()});
    Object.keys(marcas).forEach(function(k){ marcas[k].classList.toggle("sel", k === id); });
    marcas[id].focus({preventScroll: true});
  }); });
  document.querySelectorAll("#llista-mapa a[data-id]").forEach(function(a){ a.addEventListener("click", function(e){ e.preventDefault(); obrir(a.getAttribute("data-id")); }); });
})();
</script>
"""


def avisos_bloque():
    """«Has vist una obra o una mesura del Pla? Avisa'ns»: mailto con plantilla (sitio.mailto_aviso) y el registro público de
    los avisos recibidos (data/processed/avisos_ciudadanos.csv; sin nombres ni correos de quien avisa)."""
    with open(S.AVISOS_CSV, newline="", encoding="utf-8") as fh:
        av = sorted(csv.DictReader(fh), key=lambda r: r["fecha"], reverse=True)
    n = len(av)
    if n:
        filas = []
        for r in av:
            m = TP.MEDIDAS.get(r["medida_plan"]) if r["medida_plan"] else None
            que = []
            if m: que.append(f'<a href="#a-{ESC(r["medida_plan"])}">{T(ESC(m["tit"]["va"]), ESC(m["tit"]["es"]))}</a>')
            if r["lugar"]: que.append(ESC(r["lugar"]))
            res = T(*S.AVISOS_RESULTADO[r["resultado"]])
            if r["fuente_url"]: res += f' · <a href="{ESC(r["fuente_url"])}" rel="noopener">{T("Font", "Fuente")}</a>'
            filas.append(f'<tr><td>{fecha(r["fecha"])}</td><td>{T(ESC(r["resumen_va"]), ESC(r["resumen_es"]))}</td><td>{" · ".join(que) or "—"}</td><td>{res}</td></tr>')
        registro = (f'<p>{T(f"Hem rebut {n} avís" if n == 1 else f"Hem rebut {n} avisos", f"Hemos recibido {n} aviso" if n == 1 else f"Hemos recibido {n} avisos")}. '
                    f'{T("Ací tens què ens van dir i què n'hem fet, el més recent primer.", "Aquí tienes lo que nos dijeron y lo que hemos hecho, el más reciente primero.")}</p>'
                    f'<div class="tabla-caja" tabindex="0" role="region" aria-label="Avisos rebuts / Avisos recibidos"><table class="tabla"><thead><tr><th>{T("Data", "Fecha")}</th><th>{T("Què ens van dir", "Qué nos dijeron")}</th>'
                    f'<th>{T("Mesura o lloc", "Medida o lugar")}</th><th>{T("Què n'hem fet", "Qué hemos hecho")}</th></tr></thead><tbody>{"".join(filas)}</tbody></table></div>')
    else:
        registro = f'<p>{T("Encara no n'hem rebut cap. Quan n'arribe un, l'apuntarem ací amb la data, què ens van dir i què n'hem fet.", "Todavía no hemos recibido ninguno. Cuando llegue uno, lo apuntaremos aquí con la fecha, lo que nos dijeron y lo que hemos hecho con él.")}</p>'
    return f'''<section class="bloque avisa" id="avisa" data-avisos="{n}">
<h2>{T("Has vist una obra o una mesura del Pla? Avisa'ns", "¿Has visto una obra o una medida del Plan? Avísanos")}</h2>
<div class="tarjeta">
<p style="margin:0">{T("Si veus pel carrer un carril bici nou, un pas de vianants que ha canviat, unes obres que comencen o una mesura anunciada que no acaba d'arribar, conta-nos-ho. Amb el teu avís busquem la font oficial que ho confirma i l'afegim al seguiment. Només publiquem el que una font pot demostrar, i mai el nom ni el correu de qui ens escriu.", "Si ves en la calle un carril bici nuevo, un paso de peatones que ha cambiado, unas obras que empiezan o una medida anunciada que no acaba de llegar, cuéntanoslo. Con tu aviso buscamos la fuente oficial que lo confirma y lo añadimos al seguimiento. Solo publicamos lo que una fuente puede demostrar, y nunca el nombre ni el correo de quien nos escribe.")}</p>
<p style="margin:14px 0 0"><a class="btn" data-l="va" href="{S.mailto_aviso("va")}">Escriu-nos un avís</a><a class="btn" data-l="es" lang="es" href="{S.mailto_aviso("es")}">Escríbenos un aviso</a></p>
<p class="nota" style="margin:10px 0 0">{T(f"S'obri el teu programa de correu amb un missatge preparat: què has vist, on, quan i, si en tens, un enllaç o una foto. Si no s'obri, l'adreça és <a href=\"mailto:{S.CORREU}\">{S.CORREU}</a>.", f"Se abre tu programa de correo con un mensaje preparado: qué has visto, dónde, cuándo y, si tienes, un enlace o una foto. Si no se abre, la dirección es <a href=\"mailto:{S.CORREU}\">{S.CORREU}</a>.")}</p>
</div>
<h3>{T("Avisos rebuts", "Avisos recibidos")}</h3>
{registro}
</section>'''


def p_ajuntament():
    R_ = "../"
    msrc, msri = mapa_medidas_datos()
    pe = P["por_estado"]; n = P["n"]; url_plan = P["plan_doc"]["url"]; aprob = P["plan_doc"]["aprob"]; rev = P["rev"]
    cuatro = "".join(f'<button type="button" data-f="{e}" style="--c:var(--e-{ {"hecha": "hecha", "en_marcha": "marcha", "anunciada": "anun", "sin_info": "sin"}[e] })" aria-pressed="false">'
                     f'<span class="cifra">{pe[e]}</span><span class="est {e}"><i></i>{T(*ESTS[e])}</span><span class="ir">{T("Mira quines →", "Ver cuáles →")}</span></button>' for e in ORDEN_EST)
    unidades = "".join(f'<i class="u-{e}"></i>' for e in ORDEN_EST for _ in range(pe[e]))
    chips = (f'<button class="chip" type="button" data-f="" aria-pressed="true">{T("Totes", "Todas")}</button>'
             + "".join(f'<button class="chip {e}" type="button" data-f="{e}" aria-pressed="false"><i aria-hidden="true"></i>{T(*ESTS[e])} <b>{pe[e]}</b></button>' for e in ORDEN_EST))
    por_eje = collections.defaultdict(list)
    for a in P["acts"]: por_eje[a["eje"]].append(a)
    temas = []
    for eje in sorted(por_eje, key=lambda e: -len(por_eje[e])):
        acts = sorted(por_eje[eje], key=lambda a: (ORDEN_EST.index(a["est"]), a["acc"]))
        nsin = sum(a["est"] == "sin_info" for a in acts); ne = len(acts)
        lis = []
        for a in acts:
            m = TP.MEDIDAS[a["id"]]
            donde = T(ESC(m["lugar"]["va"]), ESC(m["lugar"]["es"]), "span", ' class="donde"') if m.get("lugar") else ""
            cuando = T(f"Font del {fecha(a['f'])}", f"Fuente del {fecha(a['f'])}", "span", ' class="cuando"') if a.get("f") else ""
            pags = sorted({int(x) for x in re.findall(r"PDF p\.(\d+)", a.get("cita") or "")})
            det = []
            if m.get("plan"): det.append(f'<p>{T("<b>Què diu el Pla.</b> " + ESC(m["plan"]["va"]), "<b>Lo que dice el Plan.</b> " + ESC(m["plan"]["es"]))}</p>')
            if a.get("meta"):
                mv, lg = TP.meta_va(a["meta"])
                det.append(f'<p class="nota">{T(f"Meta del Pla: <span{lg}>{ESC(mv)}</span>", f"Meta del Plan: {ESC(a["meta"])}")}</p>')
            if pags:
                pp = " i ".join(map(str, pags)); pq = " y ".join(map(str, pags))
                det.append(f'<p class="nota">{T(f"Referència: pàgina {pp} del PDF del Pla." if len(pags) == 1 else f"Referència: pàgines {pp} del PDF del Pla.", f"Referencia: página {pq} del PDF del Plan." if len(pags) == 1 else f"Referencia: páginas {pq} del PDF del Plan.")} <a href="{url_plan}#page={pags[0]}">{T("Obri el Pla →", "Abrir el Plan →")}</a></p>')
            if m.get("nota"): det.append(f'<p>{T(ESC(m["nota"]["va"]), ESC(m["nota"]["es"]))}</p>')
            if a["id"] in CON_PUNTO:
                det.append(f'<p><button type="button" class="ver-mapa" data-id="{ESC(a["id"])}">{T(f"Mira-la en el mapa (n.º {CON_PUNTO[a["id"]]}) →", f"Verla en el mapa (n.º {CON_PUNTO[a["id"]]}) →")}</button></p>')
            comp = a.get("comp")
            if a["est"] == "sin_info":
                det.append(f'<p class="nota">{T("Encara no hem trobat informació pública sobre el seu estat.", "Todavía no hemos encontrado información pública sobre su estado.")} {T(f"Ho vam comprovar per última vegada el {fecha(comp)}.", f"Lo comprobamos por última vez el {fecha(comp)}.") if comp else ""}</p>')
            else:
                f = fuente_de(a)
                if f:
                    tipo = TP.TIPO_FUENTE.get(f[3], {"va": f[3], "es": f[3]})
                    det.append(f'<p>{T("<b>Font:</b> ", "<b>Fuente:</b> ")}<a href="{ESC(f[0])}" rel="noopener">{T(ESC(f[1]), ESC(f[2]))}</a> <span class="nota">({T(ESC(tipo["va"]), ESC(tipo["es"]))})</span></p>')
                if comp: det.append(f'<p class="nota">{T(f"Ho vam comprovar per última vegada el {fecha(comp)}.", f"Lo comprobamos por última vez el {fecha(comp)}.")}</p>')
            lis.append(f'<li data-est="{a["est"]}" id="a-{ESC(a["id"])}"><details><summary><span class="est {a["est"]}"><i aria-hidden="true"></i>{T(*EST[a["est"]])}</span>'
                       f'<span class="tit">{T(ESC(m["tit"]["va"]), ESC(m["tit"]["es"]))}</span>{donde}{cuando}</summary><div class="det">{"".join(det)}</div></details></li>')
        inv = (f'<p class="nota">{T(f"De {nsin} d" + ("’aquestes mesures" if nsin > 1 else "’aquesta mesura") + " encara no hem trobat informació pública. Si en tens, escriu-nos.", f"De {nsin} de estas medidas todavía no hemos encontrado información pública. Si la tienes, escríbenos." if nsin > 1 else "De esta medida todavía no hemos encontrado información pública. Si la tienes, escríbenos.")}</p>' if nsin else "")
        temas.append(f'<section class="tema" data-tema="{eje}"><h3>{T(ESC(P["ejes"][str(eje)]["va"]), ESC(P["ejes"][str(eje)]["es"]))} <span class="n">{T(f"{ne} mesura" if ne == 1 else f"{ne} mesures", f"{ne} medida" if ne == 1 else f"{ne} medidas")}</span></h3>{inv}<ul class="medidas">{"".join(lis)}</ul></section>')
    # mapa de las medidas con punto
    pts = O["pla"]["pts"]; con_lugar = sum(1 for a in P["acts"] if a.get("lugar"))
    sp = [a["id"] for a in P["acts"] if a.get("lugar") and a["id"] not in CON_PUNTO]
    y = lambda xs, c: (", ".join(xs[:-1]) + f" {c} " + xs[-1]) if len(xs) > 1 else "".join(xs)
    nl = lambda i, l: ESC((TP.MEDIDAS[i].get("lugar") or TP.MEDIDAS[i]["tit"])[l])
    sin_punto = {"va": y([nl(i, "va") for i in sp], "i"), "es": y([nl(i, "es") for i in sp], "y")} if sp else None
    lmap = "".join(f'<li data-id="{ESC(p[7])}"><a data-id="{ESC(p[7])}" href="#a-{ESC(p[7])}">{T(ESC(TP.MEDIDAS[p[7]]["lugar"]["va"] if TP.MEDIDAS[p[7]].get("lugar") else TP.MEDIDAS[p[7]]["tit"]["va"]), ESC(TP.MEDIDAS[p[7]]["lugar"]["es"] if TP.MEDIDAS[p[7]].get("lugar") else TP.MEDIDAS[p[7]]["tit"]["es"]))}</a> <span class="est {p[2]}"><i aria-hidden="true"></i>{T(*EST[p[2]])}</span></li>' for p in pts)
    pub = P.get("pub_ind", []) + [a for a in P["acts"] if a.get("transp")]

    npub_sin = sum(1 for a in pub if a["est"] == "sin_info" and a["id"] not in TP.AUN_NO)
    lpub = "".join(f'<li>{(f"<span class=\"est aun_no\"><i aria-hidden=\"true\"></i>{T(TP.AUN_NO[a["id"]]["va"], TP.AUN_NO[a["id"]]["es"])}</span>" if a["id"] in TP.AUN_NO else f"<span class=\"est {a["est"]}\"><i aria-hidden=\"true\"></i>{T(*EST[a["est"]])}</span>")}<span>{T(ESC(TP.PUBLICA[a["id"]]["va"]), ESC(TP.PUBLICA[a["id"]]["es"]))}</span></li>' for a in pub)
    cuerpo = f'''<h1 class="h1-pag">{T("El que està fent l'Ajuntament per a reduir els accidents de bici i patinet", "Lo que está haciendo el Ayuntamiento para reducir los accidentes de bici y patinete")}</h1>
<p class="sub">{T("Seguim una a una les mesures de l'Ajuntament que afecten la bici i el patinet. Quasi totes són del Pla Director de Seguretat Viària 2026-2030; les que no ho són, obres municipals, van assenyalades. De cadascuna diem en quin punt està i quina font ho avala.", "Seguimos una a una las medidas del Ayuntamiento que afectan a la bici y el patinete. Casi todas son del Plan Director de Seguridad Vial 2026-2030; las que no lo son, obras municipales, van señaladas. De cada una decimos en qué punto está y qué fuente lo respalda.")}</p>
<p class="nota">{T(f"L'objectiu de reduir a la meitat els accidents de bici i patinet per a {R['meta']['año_meta']} (indicador de l'acció 3.2.2 del Pla) no és una mesura com les altres: es comprova amb les dades d'accidents, i el seguim en l'", f"El objetivo de reducir a la mitad los accidentes de bici y patinete para {R['meta']['año_meta']} (indicador de la acción 3.2.2 del Plan) no es una medida como las demás: se comprueba con los datos de accidentes, y lo seguimos en el ")}<a href="{R_}informe/2025/#objectiu">Informe {A1}</a>.</p>
<section class="estado" aria-labelledby="h-estado">
<div class="total"><h2 id="h-estado" class="sr">{T(f"En quin punt estan les {n} mesures", f"En qué punto están las {n} medidas")}</h2>
<p class="tc-etq">{T("Mesures que seguim", "Medidas que seguimos")}</p>
<p class="tc-cifra">{n}</p>
<p class="tc-frase">{T("Les ha triades l'observatori. Quasi totes són accions del Pla Director de Seguretat Viària 2026-2030.", "Las ha elegido el observatorio. Casi todas son acciones del Plan Director de Seguridad Vial 2026-2030.")}</p>
<p class="nota">{T(f"El Pla es va aprovar el {fecha_larga(aprob, 'va')}. Revisem l'estat de cada mesura cada tres mesos: l'última revisió va ser el {fecha_larga(rev['ult'], 'va')} i la pròxima serà el {fecha_larga(rev['prox'], 'va')}.", f"El Plan se aprobó el {fecha_larga(aprob, 'es')}. Revisamos el estado de cada medida cada tres meses: la última revisión fue el {fecha_larga(rev['ult'], 'es')} y la próxima será el {fecha_larga(rev['prox'], 'es')}.")}</p></div>
<div><div class="cuatro">{cuatro}</div><div class="unidades" aria-hidden="true">{unidades}</div><p class="nota" style="margin-top:8px">{T("Cada quadrat és una mesura.", "Cada cuadrado es una medida.")}</p></div>
</section>
<section class="bloque" id="llista">
<h2>{T(f"Les {n} mesures, una a una, per tema", f"Las {n} medidas, una a una, por tema")}</h2>
<p class="intro">{T("Al costat de cada mesura veuràs en quin punt està i la data de la font que ho avala. Obri-la per a llegir què diu el Pla i consultar aquesta font.", "Junto a cada medida verás en qué punto está y la fecha de la fuente que lo respalda. Ábrela para leer qué dice el Plan y consultar esa fuente.")}</p>
<div class="filtro-lista" role="group" aria-label="Filtra per estat / Filtrar por estado">{chips}<span class="cuenta" id="cuenta" aria-live="polite" data-va="{{n}} mesures" data-es="{{n}} medidas" data-va1="1 mesura" data-es1="1 medida">{T(f"{n} mesures", f"{n} medidas")}</span></div>
{"".join(temas)}
</section>
<section class="bloque" id="mapa-mesures">
<h2>{T("On són les mesures que afecten un lloc concret", "Dónde están las medidas que afectan a un lugar concreto")}</h2>
<p class="intro">{T(f"De les {con_lugar} mesures que afecten un lloc concret, {len(pts)} apareixen en el mapa. Les altres ocupen un tram llarg o diversos carrers i no tenen un punt únic.", f"De las {con_lugar} medidas que afectan a un lugar concreto, {len(pts)} aparecen en el mapa. Las demás ocupan un tramo largo o varias calles y no tienen un punto único.")}</p>
<div class="mapa-med"><div><div class="mapa mm med-mapa" id="mapa-med" role="region" aria-label="Mapa de les mesures amb lloc; la llista del costat té la mateixa informació" data-aria-va="Mapa de les mesures amb lloc; la llista del costat té la mateixa informació" data-aria-es="Mapa de las medidas con lugar; la lista de al lado tiene la misma información"></div>

<p class="nota" style="margin-top:6px">{T(f"No apareixen en el mapa: {sin_punto['va']}.", f"No aparecen en el mapa: {sin_punto['es']}.") if sin_punto else ""} {T("Carrers: carrerer municipal. Carril bici: capa 189 del portal de dades obertes de l'Ajuntament de València (CC BY 4.0).", "Calles: callejero municipal. Carril bici: capa 189 del portal de datos abiertos del Ayuntamiento de València (CC BY 4.0).")}</p></div>
<div><div class="ley-est">{"".join(f'<span class="est {e}"><i></i>{T(*EST[e])}</span>' for e in ORDEN_EST)}<span class="est" style="background:none"><i style="background:var(--amb);border-radius:2px;height:4px;width:18px"></i>{T("Carril bici", "Carril bici")}</span></div><ol id="llista-mapa" style="margin-top:12px">{lmap}</ol></div></div>
</section>
<section class="bloque" id="publicacions">
<h2>{T("El Pla preveu publicar dades i informes per a seguir-lo: això és el que hem trobat", "El Plan prevé publicar datos e informes para seguirlo: esto es lo que hemos encontrado")}</h2>
<p class="intro">{T(f"Són {len(pub)} publicacions, i encara no n'hem trobat {npub_sin}. Si saps on n'hi ha alguna, escriu-nos i l'afegim.", f"Son {len(pub)} publicaciones, y todavía no hemos encontrado {npub_sin} de ellas. Si sabes dónde está alguna, escríbenos y la añadimos.")}</p>
<ul class="publica">{lpub}</ul>
</section>
{avisos_bloque()}
{S.telegram_invitacion("h-tg", R_)}
<div class="escribe">
<aside class="tarjeta" aria-labelledby="h-aj-mas"><h2 class="h-tarjeta" id="h-aj-mas">{T("Vols saber-ne més?", "¿Quieres saber más?")}</h2><p style="margin:8px 0 0">{T("Com decidim l'estat de cada mesura i quines fonts consultem.", "Cómo decidimos el estado de cada medida y qué fuentes consultamos.")}</p><a class="mas" href="{R_}metode/#seguiment">{T("Dades i mètode →", "Datos y método →")}</a></aside>
</div>'''
    js = '''<script>
(function(){
  var li=[].slice.call(document.querySelectorAll(".medidas li")), cu=document.getElementById("cuenta");
  function filtra(f){
    li.forEach(function(x){ x.hidden=!!f&&x.getAttribute("data-est")!==f; });
    document.querySelectorAll(".tema").forEach(function(t){ t.classList.toggle("vacio",!t.querySelector("li:not([hidden])")); });
    document.getElementById("llista").classList.toggle("filtrada",!!f);
    document.querySelectorAll(".filtro-lista .chip, .cuatro button").forEach(function(c){ c.setAttribute("aria-pressed",String(c.getAttribute("data-f")===f)); });
    var n=li.filter(function(x){return !x.hidden;}).length, l=document.documentElement.lang==="es"?"es":"va";
    cu.textContent=(n===1?cu.getAttribute("data-"+l+"1"):cu.getAttribute("data-"+l).replace("{n}",n));
  }
  document.querySelectorAll(".filtro-lista .chip").forEach(function(c){ c.addEventListener("click",function(){ filtra(c.getAttribute("data-f")); }); });
  document.querySelectorAll(".cuatro button").forEach(function(c){ c.addEventListener("click",function(){ filtra(c.getAttribute("data-f")); document.getElementById("llista").scrollIntoView(); }); });
  document.addEventListener("obs-lang",function(){ var p=document.querySelector(".filtro-lista .chip[aria-pressed=true]"); filtra(p?p.getAttribute("data-f"):""); });
  function abrir(){ var h=location.hash.slice(1), m=/^f=(hecha|en_marcha|anunciada|sin_info)$/.exec(h);
    if(m){ filtra(m[1]); document.getElementById("llista").scrollIntoView(); return; }
    if(!/^a-/.test(h)) return; var e=document.getElementById(h); if(e){ filtra(""); e.querySelector("details").open=true; e.scrollIntoView(); } }
  addEventListener("hashchange",abrir); abrir();
})();
</script>
'''
    t = ("Què està fent l'Ajuntament? · " + S.MARCA[0], "¿Qué está haciendo el Ayuntamiento? · " + S.MARCA[1])
    d = (f"Seguim {n} mesures relacionades amb la bici i el patinet, quasi totes del Pla Director de Seguretat Viària 2026-2030 de l'Ajuntament de València: {pe['hecha']} fetes, {pe['en_marcha']} en marxa, {pe['anunciada']} anunciades i, de {pe['sin_info']}, encara no hem trobat informació pública.",
         f"Seguimos {n} medidas relacionadas con la bici y el patinete, casi todas del Plan Director de Seguridad Vial 2026-2030 del Ayuntamiento de València: {pe['hecha']} hechas, {pe['en_marcha']} en marcha, {pe['anunciada']} anunciadas y, de {pe['sin_info']}, todavía no hemos encontrado información pública.")
    html = S.pagina("ajuntament", "ajuntament/", R_, t, d, cuerpo, INFO, [("inici", S.NOM["inici"]), (None, S.NOM["ajuntament"])], "og/pla.png",
                    extra_fin=js + S.MAPLIBRE + f'\n<script src="{R_}{msrc}" integrity="{msri}"></script>\n' + MAPA_MED_JS)
    S.escribir(BUILD / "ajuntament/index.html", html)


# ---------------------------------------------------------------- figuras explorables (mapas del informe)
def slug_js(s):
    """Como slug() de la web anterior (#lloc=…): sin acentos, minúsculas y guiones."""
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def mapa_explora(img, R_, alt, items, rotulo=None):
    """Mapa estático (<img> SVG, 1000 de ancho) que web/sitio/sitio.js hace recorrible con el teclado y el ratón
    (flechas, Inicio/Fin, Intro abre la ficha, Esc oculta la etiqueta, anuncio en aria-live). Sin JavaScript queda la
    imagen con su texto alternativo (alt: (va, es)). items: [x, y, r] en unidades del SVG + textos y enlace, en orden de
    recorrido. rotulo: (x, y, texto) fijo en HTML a 15 px (el SVG no lleva texto: a su ancho real saldría por debajo)."""
    pr = Proy(*CIUDAD, 1000)
    d = [[round(x / pr.w * 100, 2), round(y / pr.h * 100, 2), round(r / pr.w * 100, 2), cv, ce, lv, le, h]
         for x, y, r, cv, ce, lv, le, h in items]
    rot = (f'<span class="mapa-rot" aria-hidden="true" style="left:{rotulo[0] / pr.w * 100:.2f}%;top:{rotulo[1] / pr.h * 100:.2f}%">{rotulo[2]}</span>'
           if rotulo else "")
    return (f'<div class="mapa" data-explora="{ESC(json.dumps(d, ensure_ascii=False, separators=(",", ":")))}">'
            f'<img src="{R_}img/{img}" alt="" width="1000" height="{pr.h}">{rot}<p class="sr">{T(ESC(alt[0]), ESC(alt[1]))}</p></div>')


# ---------------------------------------------------------------- informe 2025
def nom_punto(s):
    """Nombre de un punto de conteo tal como viene de Movilidad («P12 CARRIL BICI LLANO DE ZAIDÍA, 14 – CONSTITUCIÓN») escrito
    como lo haría una persona: sin código ni «carril bici» delante y sin mayúsculas sostenidas."""
    s = re.sub(r"^P\d+\s+", "", s).strip()
    s = re.sub(r"^CARRIL BICI\s+", "", s, flags=re.I)
    if s != s.upper(): return s
    menores = {"de", "del", "la", "las", "el", "los", "y", "i", "a", "en", "con", "d", "l"}
    out = []
    for k, w in enumerate(re.split(r"(\s+|-|–|/|,|\.|')", s.lower())):
        out.append(w if (w in menores and k) else w[:1].upper() + w[1:])
    return "".join(out)


_NOM_PC = {r["id"]: (r["nom"], r["nom_es"]) for r in csv.DictReader(open(ROOT / "data/processed/nombres_puntos_conteo.csv", encoding="utf-8"))}


def nom_punto2(s):
    """(va, es) de un punto de conteo: el nombre revisado de data/processed/nombres_puntos_conteo.csv si lo hay (07/11/2026:
    los del informe, traducidos y sin cortes) y, si no, el del portal limpio (nom_punto) en las dos lenguas."""
    m = re.match(r"^P\d+", s)
    if m and m.group(0) in _NOM_PC: return _NOM_PC[m.group(0)]
    n = nom_punto(s); return n, n


def p_informe():

    R_ = "../../"
    m = R["meta"]; base, meta = E0["base"], E0["meta"]; am = m["año_meta"]; ab = E0["año"]; des = m["desde"]
    sen = E0["senda"][str(des)]; lo, hi = E0["banda"][str(des)]
    tot = R["tot"]; ib = [round(v / CT["bv"][0] * 100) for v in CT["bv"]]; ic = [round(v / CT["ciudad"][0] * 100) for v in CT["ciudad"]]
    her_bv = CT["bv_her"][-1] / CT["bv_her"][0] - 1; her_r = CT["resto_her"][-1] / CT["resto_her"][0] - 1
    cuota = CT["cuota"][-1]
    baja = 1 - (1 - E0["senda_anual"])
    n0 = O["negros"][0]; s1, nom1 = ficha_top(1); paseo = R["ala_paseo"]
    pers = O["kpi"]["pers"]["ab"]; top_ab = O["kpi"]["pers"]["top_ab"]
    var = R["estab"]["variantes"]; rmin, rmax = min(v["ret"] for v in var), max(v["ret"] for v in var)
    top30 = sum(n["n"] for n in O["negros"][:30]); ngeo = O["cob"]["geo"]
    uso = O["uso"]; alto = [u for u in uso if u["lv"] == 2]; quiza = sum(u["lv"] == 1 for u in uso); resto = sum(u["lv"] == 0 for u in uso)
    solo_p = sum(1 for u in alto if u["sv"])
    medidas_ala = n0.get("pla") or []

    def g_obj(l, movil):
        reales = list(zip(ANYS, tot)); senda = [(int(a), v) for a, v in E0["senda"].items()]
        banda = [(ab, base, base)] + [(int(a), lo_, hi_) for a, (lo_, hi_) in E0["banda"].items()]
        serie = ", ".join(f"{num(v)} {'en' if l == 'va' else 'en'} {a}" for a, v in zip(ANYS, tot))
        etq = (f"Accidents amb bici o patinet per any: {serie}. Ritme necessari: baixar fins a {num(meta)} en {am}; en {des}, uns {num(sen)}, amb un marge de {num(lo)} a {num(hi)}. Les dades de {des} encara no estan publicades."
               if l == "va" else
               f"Accidentes con bici o patinete por año: {serie}. Ritmo necesario: bajar hasta {num(meta)} en {am}; en {des}, unos {num(sen)}, con un margen de {num(lo)} a {num(hi)}. Los datos de {des} todavía no están publicados.")
        sp = "sense publicar" if l == "va" else "sin publicar"
        ymax = math.ceil(max(tot) * 1.15 / 100) * 100
        if movil:
            return lineas_svg(list(range(A0, am + 1)), [("lk", reales, ""), ("lg", senda, num(meta))], etq, ymin=0, ymax=ymax, banda=banda,
                              ancho=520, alto=440, xlabs=[A0, ab, am], marcas=[(A0 + .3, tot[0] - ymax * .09, num(tot[0])), (ab, base + ymax * .065, num(base)), (des + 1, lo - ymax * .17, f"{des}: {sp}")])
        return lineas_svg(list(range(A0, am + 1)), [("lk", reales, ""), ("lg", senda, f"{num(meta)} {'en' if l == 'es' else 'en'} {am}")], etq, ymin=0, ymax=ymax, banda=banda,
                          ancho=960, alto=360, marcas=[(A0, tot[0] - ymax * .08, num(tot[0])), (ab, base + ymax * .058, num(base)), (des + .15, lo - ymax * .1, f"{des}: {sp}")])

    def g_ind(l, movil):
        a, b = ("Amb bici o patinet", "Tots") if l == "va" else ("Con bici o patinete", "Todos")
        etq = (f"{'Índex' if l == 'va' else 'Índice'} {A0} = 100. {a}: " + ", ".join(f"{v} ({x})" for x, v in zip(ANYS, ib))
               + f". {b}: " + ", ".join(f"{v} ({x})" for x, v in zip(ANYS, ic)) + ".")
        ymin = math.floor(min(ib + ic) / 10) * 10 - 10; ymax = math.ceil(max(ib + ic) / 10) * 10 + 10
        if movil:
            e = (f"{'Les dues' if l == 'va' else 'Las dos'}: {ib[-1]}" if ib[-1] == ic[-1] else f"{ib[-1]} {'i' if l == 'va' else 'y'} {ic[-1]}")
            return lineas_svg(ANYS, [("lk", list(zip(ANYS, ib)), e), ("lg", list(zip(ANYS, ic)), "")], etq, ymin=ymin, ymax=ymax, ancho=360, alto=260, fmt=lambda v: str(int(v)), mr=14, fin_dentro=True)
        return lineas_svg(ANYS, [("lk", list(zip(ANYS, ib)), f"{a}: {ib[-1]}", 12), ("lg", list(zip(ANYS, ic)), f"{b}: {ic[-1]}", -10)], etq, ymin=ymin, ymax=ymax, ancho=600, alto=260, fmt=lambda v: str(int(v)), mr=190)

    def g_veh(l, movil):
        p, b = ("Amb patinet", "Amb bici") if l == "va" else ("Con patinete", "Con bici")
        ymax = math.ceil(max(R["vmp"]) * 1.1 / 100) * 100
        etq = (("Accidents amb patinet i amb bici per any. " if l == "va" else "Accidentes con patinete y con bici por año. ")
               + f"{p}: " + ", ".join(f"{num(v)} ({x})" for x, v in zip(ANYS, R["vmp"])) + f". {b}: " + ", ".join(f"{num(v)} ({x})" for x, v in zip(ANYS, R["bici"])) + ".")

        ser = [("lp", list(zip(ANYS, R["vmp"])), f"{p}: {num(R['vmp'][-1])}"), ("lb", list(zip(ANYS, R["bici"])), f"{b}: {num(R['bici'][-1])}")]
        return (lineas_svg(ANYS, ser, etq, ymin=0, ymax=ymax, ancho=360, alto=260, mr=14, fin_dentro=True) if movil
                else lineas_svg(ANYS, ser, etq, ymin=0, ymax=ymax, ancho=600, alto=280, mr=190))

    ala_barras = graf_lang(lambda l: barras_apiladas(ANYS, n0["vy3"], ("Accidents cada any" if l == "va" else "Accidentes cada año")))
    tits = [("objectiu", (f"Un indicador del Pla de Seguretat Viària demana reduir a la meitat els accidents de bici i patinet per a {am}", f"Un indicador del Plan de Seguridad Vial pide reducir a la mitad los accidentes de bici y patinete para {am}")),
            ("pujada", (f"De {A0} a {A1}, els accidents de bici i patinet van pujar un {pct(tot[-1] / tot[0] - 1)}, quasi igual que tots els de la ciutat", f"De {A0} a {A1}, los accidentes de bici y patinete subieron un {pct(tot[-1] / tot[0] - 1)}, casi igual que todos los de la ciudad")),
            ("patinet", ("Cada vegada hi ha més accidents amb patinet; els de bici es mantenen", "Cada vez hay más accidentes con patinete; los de bici se mantienen")),
            ("llocs", ("Els accidents es repetixen en els mateixos llocs", "Los accidentes se repiten en los mismos lugares")),
            ("transit", (f"En {len(alto)} dels {len(uso)} punts on es compten bicis hi ha clarament més accidents que en altres amb un trànsit semblant", f"En {len(alto)} de los {len(uso)} puntos donde se cuentan bicis hay claramente más accidentes que en otros con un tráfico parecido")),
            ("ajudaria", ("Què ens ajudaria a seguir el Pla", "Qué nos ayudaría a seguir el Plan")),
            ("sabem", ("El que ja sabem i el que encara no", "Lo que ya sabemos y lo que todavía no"))]
    nt = len(tits)
    num_s = lambda i: T(f"{i} de {nt}", f"{i} de {nt}", "span", ' class="num"')
    h2 = lambda i: f'<h2>{T(*tits[i - 1][1])}</h2>'
    ind = "".join(f'<li><a href="#{k}">{T(*v)}</a></li>' for k, v in tits)
    medid = "".join(f'<li>{T(ESC(TP.MEDIDAS[x[0]]["tit"]["va"]), ESC(TP.MEDIDAS[x[0]]["tit"]["es"]))} <span class="est {x[2]}"><i aria-hidden="true"></i>{T(*EST[x[2]])}</span></li>' for x in medidas_ala if x[0] in TP.MEDIDAS)
    pr = Proy(*CIUDAD, 1000); PL = (("El Pla Director no l'esmenta.", "El Pla Director cita aquest lloc.", "El Pla Director només cita el seu carrer."),
                                    ("El Plan Director no lo menciona.", "El Plan Director cita este lugar.", "El Plan Director solo cita su calle."))
    it_lug = []
    for n in O["negros"][:30]:
        sl, nf = ficha_top(n["rank"]); nv, ne = (limpio(nf[0]), limpio(nf[1])) if nf else (n["nom"], n.get("nom_es") or n["nom"])
        x, y = pr(n["lon"], n["lat"]); pl = n.get("pl", 0) or 0
        it_lug.append([x, y, round(5 + 2.1 * math.sqrt(n["n"]), 1), f'{n["rank"]}. {nv} · {num(n["n"])}', f'{n["rank"]}. {ne} · {num(n["n"])}',
                       f'{n["rank"]}. {nv}: {num(n["n"])} accidents amb bici o patinet de {A0} a {A1}. {PL[0][pl]}',
                       f'{n["rank"]}. {ne}: {num(n["n"])} accidentes con bici o patinete de {A0} a {A1}. {PL[1][pl]}',
                       f"{R_}lloc/{sl}/" if sl else f"{R_}mapa/#lloc={slug_js(n['nom'])}"])
    top3 = "; ".join(f"{i[3]}" for i in it_lug[:3]), "; ".join(f"{i[4]}" for i in it_lug[:3])
    alt_lug = (f"Mapa de València amb els 30 llocs amb més accidents amb bici o patinet de {A0} a {A1}: com més gran el cercle, més accidents. Els tres primers: {top3[0]}.",
               f"Mapa de València con los 30 lugares con más accidentes con bici o patinete de {A0} a {A1}: cuanto mayor el círculo, más accidentes. Los tres primeros: {top3[1]}.")
    NV = (("Sense indicis de tindre'n més que els punts semblants.", "Potser per damunt de la mitjana.", "Clarament per damunt de la mitjana."),
          ("Sin indicios de tener más que los puntos parecidos.", "Quizá por encima de la media.", "Claramente por encima de la media."))
    it_uso = []
    for u in sorted(uso, key=lambda u: u["lon"]):                                                   # de oeste a este
        x, y = pr(u["lon"], u["lat"]); nv, ne = nom_punto2(u["nom"]); pid = (re.match(r"^P\d+", u["nom"]) or [slug_js(u["nom"])])[0]
        it_uso.append([x, y, 12 if u["lv"] == 2 else 9 if u["lv"] else 6, f'{nv} · {u["N"]} accidents; se n’esperaven {num(u["mu"], 1)}', f'{ne} · {u["N"]} accidentes; se esperaban {num(u["mu"], 1)}',
                       f'{nv}: {u["N"]} accidents; en punts amb un trànsit semblant se n’esperarien uns {num(u["mu"], 1)}. {NV[0][u["lv"]]}',
                       f'{ne}: {u["N"]} accidentes; en puntos con un tráfico parecido se esperarían unos {num(u["mu"], 1)}. {NV[1][u["lv"]]}',
                       f"{R_}mapa/#punt={pid}"])
    alt_uso = (f"Mapa dels {len(uso)} punts de comptatge del carril bici: {len(alto)} amb clarament més accidents que la mitjana dels punts semblants, {quiza} potser per damunt i {resto} amb els que cal esperar.",
               f"Mapa de los {len(uso)} puntos de conteo del carril bici: {len(alto)} con claramente más accidentes que la media de los puntos parecidos, {quiza} quizá por encima y {resto} con los que cabe esperar.")
    x1, y1 = pr(O["negros"][0]["lon"], O["negros"][0]["lat"]); r1 = 5 + 2.1 * math.sqrt(O["negros"][0]["n"])
    m_lug = mapa_explora("mapa_lugares.svg", R_, alt_lug, it_lug, (x1 + r1, y1 - r1, "1"))
    m_uso = mapa_explora("mapa_uso.svg", R_, alt_uso, it_uso)
    pts_alto = "".join(f'<li>{T(ESC(nom_punto2(u["nom"])[0]), ESC(nom_punto2(u["nom"])[1]))} · {T(f"{u["N"]} accidents; en serien d’esperar uns {num(u["mu"], 1)}", f"{u["N"]} accidentes; se esperarían unos {num(u["mu"], 1)}")}{T(" (l’excés és només de patinet)", " (el exceso es solo de patinete)") if u["sv"] else ""}</li>' for u in sorted(alto, key=lambda u: -u["N"]))
    cuerpo = f'''<section class="inf-cab" id="objectiu">
<p class="kicker">{T(f"Informe {A1}: què va passar amb els accidents de bici i patinet a València ({PER})", f"Informe {A1}: qué pasó con los accidentes de bici y patinete en València ({PER})")}</p>
<h1>{T(*tits[0][1])}</h1>
<p class="frase par-frase">{T(f"Partim dels <b class=\"cg\">{num(base)}</b> accidents de {ab}. La meitat serien <b class=\"cg\">{num(meta)}</b> en {am}.", f"Partimos de los <b class=\"cg\">{num(base)}</b> accidentes de {ab}. La mitad serían <b class=\"cg\">{num(meta)}</b> en {am}.")}</p>
<div class="texto"><p>{T(f"El Pla no indica des de quin any es compta. Per a poder seguir-lo any a any, prenem com a punt de partida {ab}, l'últim any amb dades.", f"El Plan no indica desde qué año se cuenta. Para poder seguirlo año a año, tomamos como punto de partida {ab}, el último año con datos.")}</p>
<p>{T(f"Per a arribar a {num(meta)}, cada any hauria d'haver-hi uns {round(baja * 100)} de cada 100 accidents menys que l'any anterior.", f"Para llegar a {num(meta)}, cada año tendría que haber unos {round(baja * 100)} de cada 100 accidentes menos que el año anterior.")}</p></div>
<div class="graf-caja" style="margin-top:20px"><p class="graf-t">{T(f"Accidents amb bici o patinet per any, i el ritme necessari fins a {am}", f"Accidentes con bici o patinete por año, y el ritmo necesario hasta {am}")}</p>
<div class="solo-esc">{graf_lang(lambda l: g_obj(l, False))}</div><div class="solo-mov">{graf_lang(lambda l: g_obj(l, True))}</div>
<div class="ley-l"><span><i></i>{T(f"El que va passar ({PER})", f"Lo que pasó ({PER})")}</span><span><i class="disc"></i>{T(f"Ritme necessari per a arribar a {num(meta)}", f"Ritmo necesario para llegar a {num(meta)}")}</span><span><i class="ban"></i>{T("Marge per atzar: el que varia d'un any a l'altre sense que canvie res", "Margen por azar: lo que varía de un año a otro sin que nada cambie")}</span></div>
<p class="graf-f">{T("Font: portal de dades obertes de l'Ajuntament de València. Accidents amb almenys una bici o un patinet.", "Fuente: portal de datos abiertos del Ayuntamiento de València. Accidentes con al menos una bici o un patinete.")}</p></div>
<div class="ritmo">
<div class="tarjeta"><p class="frase">{T(f"Si va al ritme necessari, en {des} hi haurà uns <b class=\"cg\">{num(sen)}</b> accidents.", f"Si va al ritmo necesario, en {des} habrá unos <b class=\"cg\">{num(sen)}</b> accidentes.")}</p><p class="nota" style="margin-top:6px">{T(f"Amb qualsevol xifra entre {num(lo)} i {num(hi)} direm que <b>no es pot descartar</b> que vaja al ritme, però tampoc que no hi vaja: els accidents varien cada any per atzar, i el punt de partida també.", f"Con cualquier cifra entre {num(lo)} y {num(hi)} diremos que <b>no se puede descartar</b> que vaya al ritmo, pero tampoco que no vaya: los accidentes varían cada año por azar, y el punto de partida también.")}</p></div>
<div class="tarjeta"><p class="frase">{T(f"El primer any que podrem comparar amb el punt de partida serà <b class=\"cg\">{des}</b>.", f"El primer año que podremos comparar con el punto de partida será <b class=\"cg\">{des}</b>.")}</p><p class="nota" style="margin-top:6px">{T("Les seues dades encara no estan en el portal.", "Sus datos todavía no están en el portal.")}</p></div>
<div class="tarjeta"><p class="frase">{T(f"De {MED['etq']} hi va haver una mitjana de <b class=\"cg\">{num(MED['base'])}</b> accidents l'any. És la nostra segona referència: amb ella, la meitat serien {num(MED['meta'])}.", f"De {MED['etq']} hubo una media de <b class=\"cg\">{num(MED['base'])}</b> accidentes al año. Es nuestra segunda referencia: con ella, la mitad serían {num(MED['meta'])}.")}</p><p class="nota" style="margin-top:6px">{T(f"La fem servir perquè {ab} és l'any amb més accidents de la sèrie ({PER}).", f"La usamos porque {ab} es el año con más accidentes de la serie ({PER}).") if m["max"] else ""}</p></div>
</div>
<details class="saber"><summary>{T(f"Vols saber-ne més? D'on ix l'objectiu i per què {ab}", f"¿Quieres saber más? De dónde sale el objetivo y por qué {ab}")}</summary>
<div><p>{T(f"És l'indicador de l'acció 3.2.2 del Pla Director de Seguretat Viària 2026-2030: reduir un 50 % els accidents amb bici o patinet en {am}. El Pla no fixa l'any de partida; l'elecció de {ab} és nostra. La meta general del Pla és una altra: reduir a la meitat les persones mortes i ferides greus.", f"Es el indicador de la acción 3.2.2 del Plan Director de Seguridad Vial 2026-2030: reducir un 50 % los accidentes con bici o patinete en {am}. El Plan no fija el año de partida; la elección de {ab} es nuestra. La meta general del Plan es otra: reducir a la mitad las personas fallecidas y heridas graves.")}</p>
<p>{T(f"Cada any direm una de tres coses: que baixa més del necessari, que no es pot descartar que vaja al ritme, o que no baixa al ritme necessari. Només direm que baixa més o que no baixa prou si la diferència és massa gran per a ser casualitat (amb un {round(m['nivel'] * 100)} % de confiança). El marge té en compte l'atzar de l'any i el del punt de partida, però no altres variacions d'un any a l'altre (pluja, obres, festes). Per això un sol any dins del marge no vol dir que el Pla funcione, i ho direm també amb la segona referència ({MED['etq']}).", f"Cada año diremos una de tres cosas: que baja más de lo necesario, que no se puede descartar que vaya al ritmo, o que no baja al ritmo necesario. Solo diremos que baja más o que no baja lo suficiente si la diferencia es demasiado grande para ser casualidad (con un {round(m['nivel'] * 100)} % de confianza). El margen tiene en cuenta el azar del año y el del punto de partida, pero no otras variaciones de un año a otro (lluvia, obras, fiestas). Por eso un solo año dentro del margen no quiere decir que el Plan funcione, y lo diremos también con la segunda referencia ({MED['etq']}).")}</p>
<p><a href="{R_}metode/#meta">{T("El mètode complet →", "El método completo →")}</a></p></div></details>
<nav class="indice" aria-labelledby="h-indice"><h2 id="h-indice">{T("En aquest informe", "En este informe")}</h2><ol>{ind}</ol></nav>
</section>
<section class="seccion" id="pujada">{num_s(2)}{h2(2)}
<div class="cols"><div>
<p>{T(f"Els accidents amb bici o patinet van passar de {num(tot[0])} en {A0} a {num(tot[-1])} en {A1}.", f"Los accidentes con bici o patinete pasaron de {num(tot[0])} en {A0} a {num(tot[-1])} en {A1}.")}</p>
<p>{T(f"Tots els accidents de trànsit de València, amb bici o sense, van passar de {num(CT['ciudad'][0])} en {A0} a {num(CT['ciudad'][-1])} en {A1}.", f"Todos los accidentes de tráfico de València, con bici o sin ella, pasaron de {num(CT['ciudad'][0])} en {A0} a {num(CT['ciudad'][-1])} en {A1}.")}</p>
<p>{T(f"Els accidents amb bici o patinet continuen sent uns {round(cuota * 100)} de cada 100 accidents de trànsit de la ciutat.", f"Los accidentes con bici o patinete siguen siendo unos {round(cuota * 100)} de cada 100 accidentes de tráfico de la ciudad.")}</p>
<p>{T(f"Si es compten només els accidents amb ferits, els de bici i patinet pugen una mica més: un {pct(her_bv)}, davant d'un {pct(her_r)} de la resta. Però la diferència pot ser casual, i el canvi de registre de 2024 pot haver canviat qui es compta com a ferit.", f"Si se cuentan solo los accidentes con heridos, los de bici y patinete suben algo más: un {pct(her_bv)}, frente a un {pct(her_r)} del resto. Pero la diferencia puede ser casual, y el cambio de registro de 2024 puede haber cambiado a quién se cuenta como herido.")}</p>
<p class="nota">{T(f"La Policia Local va canviar el seu sistema de registre {mes_any(SIASV, 'va')}. Per això comparem amb el total de la ciutat, que va passar pel mateix canvi.", f"En {mes_any(SIASV, 'es')} la Policía Local cambió su sistema de registro. Por eso comparamos con el total de la ciudad, que pasó por el mismo cambio.")}</p>
</div><div class="graf-caja"><p class="graf-t">{T(f"Com canvien els accidents des de {A0} ({A0} = 100; {ib[-1]} vol dir un {ib[-1] - 100} % més)", f"Cómo cambian los accidentes desde {A0} ({A0} = 100; {ib[-1]} quiere decir un {ib[-1] - 100} % más)")}</p>
<div class="solo-esc">{graf_lang(lambda l: g_ind(l, False))}</div><div class="solo-mov">{graf_lang(lambda l: g_ind(l, True))}</div>
<div class="ley-l"><span><i></i>{T("Amb bici o patinet", "Con bici o patinete")}</span><span><i class="disc"></i>{T("Tots els de la ciutat", "Todos los de la ciudad")}</span></div>
<p class="graf-f">{T("L'eix vertical no comença en 0, perquè el que importa és la diferència entre les dues línies. Font: portal de dades obertes de l'Ajuntament de València.", "El eje vertical no empieza en 0, porque lo que importa es la diferencia entre las dos líneas. Fuente: portal de datos abiertos del Ayuntamiento de València.")}</p></div></div>

</section>
<section class="seccion" id="patinet">{num_s(3)}{h2(3)}
<div class="cols"><div>
<p>{T(f"Els accidents amb patinet van passar de {num(R['vmp'][0])} en {A0} a {num(R['vmp'][-1])} en {A1}.", f"Los accidentes con patinete pasaron de {num(R['vmp'][0])} en {A0} a {num(R['vmp'][-1])} en {A1}.")}</p>
<p>{T(f"Els accidents amb bici van passar de {num(R['bici'][0])} en {A0} a {num(R['bici'][-1])} en {A1}.", f"Los accidentes con bici pasaron de {num(R['bici'][0])} en {A0} a {num(R['bici'][-1])} en {A1}.")}</p>
<p class="nota">{T("Pot ser que hi haja més accidents de patinet perquè hi ha més patinets. Per a saber-ho caldria comptar-los, i cap comptador de la ciutat els separa de les bicis.", "Puede que haya más accidentes de patinete porque hay más patinetes. Para saberlo habría que contarlos, y ningún contador de la ciudad los separa de las bicis.")}</p>
</div><div class="graf-caja"><p class="graf-t">{T(f"Accidents amb patinet i amb bici per any, {PER}", f"Accidentes con patinete y con bici por año, {PER}")}</p>
<div class="solo-esc">{graf_lang(lambda l: g_veh(l, False))}</div><div class="solo-mov">{graf_lang(lambda l: g_veh(l, True))}</div>
<p class="graf-f">{T("Un xoc entre bici i patinet compta en les dues línies. Font: portal de dades obertes de l'Ajuntament.", "Un choque entre bici y patinete cuenta en las dos líneas. Fuente: portal de datos abiertos del Ayuntamiento.")}</p></div></div>
</section>
<section class="seccion con-ejemplo" id="llocs">{num_s(4)}{h2(4)}
<div class="cols"><div>
<p>{T(f"En només 30 llocs hi va haver {num(top30)} accidents de {A0} a {A1}: 1 de cada {round(ngeo / top30)} dels situats en el mapa.", f"En solo 30 lugares hubo {num(top30)} accidentes de {A0} a {A1}: 1 de cada {round(ngeo / top30)} de los situados en el mapa.")}</p>
<p>{T(f"Els llocs que més accidents tenien en {'-'.join(map(str, [ANYS[0], ANYS[1]]))} en van continuar tenint molts en {'-'.join(map(str, [ANYS[2], ANYS[3]]))}.", f"Los lugares que más accidentes tenían en {'-'.join(map(str, [ANYS[0], ANYS[1]]))} siguieron teniendo muchos en {'-'.join(map(str, [ANYS[2], ANYS[3]]))}.")}</p>
<p class="nota">{T("Són llocs amb molts accidents. Sense comptar quanta gent hi passa, no es pot dir que siguen més perillosos.", "Son lugares con muchos accidentes. Sin contar cuánta gente pasa, no se puede decir que sean más peligrosos.")}</p>
</div>{m_lug}</div>
<div class="ejemplo"><span class="etiqueta">{T(f"Exemple: el primer dels 30 llocs ({PER})", f"Ejemplo: el primero de los 30 lugares ({PER})")}</span>
<p class="donde">{T(ESC(limpio(nom1[0])), ESC(limpio(nom1[1])))}</p>
<div class="cols"><div><p class="frase" style="margin:0 0 12px">{T(f"Ací hi va haver <b class=\"cg\">{n0['n']}</b> accidents amb bici o patinet de {A0} a {A1}. En {n0['k']['m']} hi havia un cotxe, una moto o un altre vehicle.", f"Aquí hubo <b class=\"cg\">{n0['n']}</b> accidentes con bici o patinete de {A0} a {A1}. En {n0['k']['m']} había un coche, una moto u otro vehículo.")}</p>
<p>{T(f"És el n.º 1 dels 30 llocs del mapa de dalt. Els seus accidents van baixar en {ANYS[2]} i {ANYS[3]}, però en tot el passeig de l'Albereda gairebé no canvien ({', '.join(num(x) for x in paseo[:-1])} i {num(paseo[-1])}).", f"Es el n.º 1 de los 30 lugares del mapa de arriba. Sus accidentes bajaron en {ANYS[2]} y {ANYS[3]}, pero en todo el paseo de la Alameda apenas cambian ({', '.join(num(x) for x in paseo[:-1])} y {num(paseo[-1])}).")}</p>
<p class="nota">{T(f"Des {mes_any(SIASV, 'va')} la policia anota més accidents pel número de portal i menys «en la cruïlla»: una cruïlla pot perdre casos sense que hi canvie res. Amb aquestes dades no es pot saber si les mesures de l'Ajuntament hi han influït:", f"Desde {mes_any(SIASV, 'es')} la policía anota más accidentes por número de portal y menos «en el cruce»: un cruce puede perder casos sin que cambie nada. Con estos datos no se puede saber si las medidas del Ayuntamiento han influido:")}</p>
<ul class="lista-pts">{medid}</ul>
<a class="mas" href="{R_}lloc/{s1}/">{T("Mira la fitxa d'aquest lloc →", "Ver la ficha de este lugar →")}</a></div>
<div><p class="graf-t">{T("Accidents cada any en aquest lloc", "Accidentes cada año en este lugar")}</p>{ala_barras}
<div class="ley"><span><i class="pt b"></i>{T("Només bici", "Solo bici")}</span><span><i class="pt p"></i>{T("Només patinet", "Solo patinete")}</span><span><i class="pt a"></i>{T("Bici i patinet", "Bici y patinete")}</span></div></div></div></div>
<p class="vuelta">{T(f"Dels 30 llocs amb més accidents en {ANYS[0]}-{ANYS[1]}, {top_ab} continuen entre els 30 primers en {ANYS[2]}-{ANYS[3]}. ", f"De los 30 lugares con más accidentes en {ANYS[0]}-{ANYS[1]}, {top_ab} siguen entre los 30 primeros en {ANYS[2]}-{ANYS[3]}. ")}<a href="{R_}mapa/#llocs">{T("Mira els 30 llocs en el mapa →", "Ver los 30 lugares en el mapa →")}</a></p>
<details class="saber"><summary>{T("Vols saber-ne més? Com comprovem que es repetixen", "¿Quieres saber más? Cómo comprobamos que se repiten")}</summary>
<div><p>{T(f"Triem els 30 llocs amb les dades de {ANYS[0]}-{ANYS[1]}. Com que aquells anys es situaven en el mapa menys accidents, comptem cada accident amb un pes que corregix la cobertura: així hi van tindre uns {num(pers['A'])} accidents, i en {ANYS[2]}-{ANYS[3]} uns {num(pers['obs'])}. Van baixar, com és d'esperar quan es trien en el seu pitjor moment, perquè part d'aquell mal moment era atzar. Si el nivell de fons de cada lloc no haguera canviat, n'esperaríem entre {num(pers['perf_lo'])} i {num(pers['perf_hi'])}, i {num(pers['obs'])} hi cap. Llocs qualssevol del mateix barri en sumarien uns {num(pers['loc'])}. Si dibuixem cada lloc una mica més gran o més xicotet, la llista quasi no canvia: continuen entre {rmin} i {rmax} dels 30.", f"Elegimos los 30 lugares con los datos de {ANYS[0]}-{ANYS[1]}. Como esos años se situaban en el mapa menos accidentes, contamos cada accidente con un peso que corrige la cobertura: así tuvieron unos {num(pers['A'])} accidentes, y en {ANYS[2]}-{ANYS[3]} unos {num(pers['obs'])}. Bajaron, lo esperable al elegirlos en su peor momento, porque parte de ese mal momento era azar. Si el nivel de fondo de cada lugar no hubiera cambiado, esperaríamos entre {num(pers['perf_lo'])} y {num(pers['perf_hi'])}, y {num(pers['obs'])} cabe ahí. Lugares cualesquiera del mismo barrio sumarían unos {num(pers['loc'])}. Si dibujamos cada lugar un poco más grande o más pequeño, la lista apenas cambia: siguen entre {rmin} y {rmax} de los 30.")}</p>
<p><a href="{R_}metode/#lugares">{T("El mètode complet →", "El método completo →")}</a></p></div></details>
</section>
<section class="seccion" id="transit">{num_s(5)}{h2(5)}
<div class="cols"><div>
<p>{T(f"En {len(uso)} punts del carril bici es compten les bicis que hi passen. Allí podem comparar els accidents amb el trànsit: els comparem amb altres punts amb un trànsit semblant de bicis i de cotxes i amb un nombre semblant de cruïlles.", f"En {len(uso)} puntos del carril bici se cuentan las bicis que pasan. Allí podemos comparar los accidentes con el tráfico: los comparamos con otros puntos con un tráfico parecido de bicis y de coches y con un número parecido de cruces.")}</p>
<p>{T(f"{len(alto)} punts tenen clarament més accidents que la mitjana dels punts semblants. En {solo_p} d'ells l'excés és només de patinet, que el comptador pot no comptar. En {quiza} més podria haver-hi més accidents, però no es pot assegurar; en els altres {resto} no hi ha indicis que en tinguen més.", f"{len(alto)} puntos tienen claramente más accidentes que la media de los puntos parecidos. En {solo_p} de ellos el exceso es solo de patinete, que el contador puede no contar. En {quiza} más podría haber más accidentes, pero no se puede asegurar; en los otros {resto} no hay indicios de que tengan más.")}</p>
<ol class="lista-pts">{pts_alto}</ol>
<p class="nota">{T("És un senyal per a mirar amb més detall, no un diagnòstic. Que un punt tinga més accidents que altres semblants no diu per què. I la llista només és estable en part: amb uns altres anys o un altre radi, alguns punts entren o ixen.", "Es una señal para mirar con más detalle, no un diagnóstico. Que un punto tenga más accidentes que otros parecidos no dice por qué. Y la lista solo es estable en parte: con otros años u otro radio, algunos puntos entran o salen.")}</p>
</div><div>{m_uso}
<div class="ley"><span><i class="pt x pt-g" style="background:var(--warn);box-shadow:0 0 0 1.5px var(--ink)"></i>{T("Clarament per damunt", "Claramente por encima")}</span><span><i class="pt x pt-m" style="background:var(--surface);box-shadow:inset 0 0 0 3px var(--ink)"></i>{T("Potser per damunt", "Quizá por encima")}</span><span><i class="pt x" style="background:var(--surface);box-shadow:0 0 0 1.5px var(--ink2)"></i>{T("Sense indicis d'excés", "Sin indicios de exceso")}</span></div>

<p><a class="mas" href="{R_}mapa/#vista=uso">{T("Mira'ls en el mapa →", "Verlos en el mapa →")}</a></p></div></div>
</section>
<section class="seccion" id="ajudaria">{num_s(6)}{h2(6)}
<ul class="limites">
<li>{T(f"Les dades de {m['pendiente']} en el portal de dades obertes, amb el mateix format, per a poder fer la primera comparació amb el punt de partida.", f"Los datos de {m['pendiente']} en el portal de datos abiertos, con el mismo formato, para poder hacer la primera comparación con el punto de partida.")}</li>
<li>{T("La línia base de l'indicador de l'acció 3.2.2, fixada per l'Ajuntament: si en tria una altra, l'observatori la farà servir.", "La línea base del indicador de la acción 3.2.2, fijada por el Ayuntamiento: si elige otra, el observatorio la usará.")}</li>
<li>{T("Un criteri de gravetat estable: des de 2023 es compta com a ferit greu qui passa més de 24 hores a l'hospital. Per a comparar els anys, caldria mantindre'l o avisar quan canvie.", "Un criterio de gravedad estable: desde 2023 se cuenta como herido grave a quien pasa más de 24 horas en el hospital. Para comparar los años, habría que mantenerlo o avisar cuando cambie.")}</li>
<li>{T("Les coordenades de cada accident en el portal: ara només ve l'adreça escrita.", "Las coordenadas de cada accidente en el portal: ahora solo viene la dirección escrita.")}</li>
<li>{T("Comptadors que separen patinets i bicis, per a poder saber si el patinet té més accidents per viatge.", "Contadores que separen patinetes y bicis, para poder saber si el patinete tiene más accidentes por viaje.")}</li>
<li>{T("Els informes i el quadre de comandament que el Pla preveu publicar.", "Los informes y el cuadro de mando que el Plan prevé publicar.")} <a href="{R_}ajuntament/#publicacions">{T("Així anem →", "Así vamos →")}</a></li>
</ul>
</section>
<section class="seccion" id="sabem">{num_s(7)}{h2(7)}
<div class="cols"><div><h3>{T("Ja ho sabem", "Ya lo sabemos")}</h3><ul class="limites">
<li>{T(f"D'on partim: {num(base)} accidents amb bici o patinet en {ab}, i on cal arribar: {num(meta)} en {am}.", f"De dónde partimos: {num(base)} accidentes con bici o patinete en {ab}, y adónde hay que llegar: {num(meta)} en {am}.")}</li>
<li>{T("Que pugen quasi igual que tots els accidents de la ciutat.", "Que suben casi igual que todos los accidentes de la ciudad.")}</li>
<li>{T("Que cada vegada hi ha més accidents amb patinet.", "Que cada vez hay más accidentes con patinete.")}</li>
<li>{T("On s'acumulen, i que els llocs amb més accidents en continuen tenint molts.", "Dónde se acumulan, y que los lugares con más accidentes siguen teniendo muchos.")}</li>
</ul></div><div><h3>{T("Encara no ho sabem", "Todavía no lo sabemos")}</h3><ul class="limites">
<li>{T(f"Si el Pla funciona: falten les dades de {m['pendiente']}.", f"Si el Plan funciona: faltan los datos de {m['pendiente']}.")}</li>
<li>{T("Si un lloc és perillós: sense saber quanta gent hi passa, només veiem on s'acumulen els accidents.", "Si un lugar es peligroso: sin saber cuánta gente pasa, solo vemos dónde se acumulan los accidentes.")}</li>
<li>{T("Si el patinet té més accidents per viatge: cap comptador el separa de la bici.", "Si el patinete tiene más accidentes por viaje: ningún contador lo separa de la bici.")}</li>
<li>{T("Si els ferits greus pugen o baixen: el criteri de gravetat va canviar.", "Si los heridos graves suben o bajan: el criterio de gravedad cambió.")}</li>
</ul></div></div>
</section>
<aside class="capa-sig" aria-labelledby="h-capa"><h2 id="h-capa">{T("Vols saber-ne més?", "¿Quieres saber más?")}</h2>
<a href="{R_}carrer/">{T("Busca el teu carrer i mira la seua fitxa →", "Busca tu calle y mira su ficha →")}</a>
<a href="{R_}dades/">{T("Dades i mètode: d'on ixen les dades i com les tractem →", "Datos y método: de dónde salen los datos y cómo los tratamos →")}</a>
<p class="nota">{T(f"Com citar-lo: Observatori de la bici i el patinet de València, Informe {A1}. Versió del {fecha(INFO['version'])}. CC BY 4.0.", f"Cómo citarlo: Observatorio de la bici y el patinete de València, Informe {A1}. Versión del {fecha(INFO['version'])}. CC BY 4.0.")}</p></aside>'''
    t = (f"Informe {A1} · " + S.MARCA[0], f"Informe {A1} · " + S.MARCA[1])
    d = (f"Què va passar amb els accidents de bici i patinet a València de {A0} a {A1} i com seguir l'indicador del Pla per a {am}.",
         f"Qué pasó con los accidentes de bici y patinete en València de {A0} a {A1} y cómo seguir el indicador del Plan para {am}.")
    pasos = [("inici", S.NOM["inici"]), ("informes", S.NOM["informes"]), (None, (f"Informe {A1}", f"Informe {A1}"))]
    S.escribir(BUILD / "informe/2025/index.html", S.pagina("informe", "informe/2025/", R_, t, d, cuerpo, INFO, pasos, "og/informe.png"))
    # índice de ediciones
    R2 = "../"
    c2 = (f'<h1 class="h1-pag">{T("Informes anuals", "Informes anuales")}</h1>'
          f'<p class="sub">{T("Una edició per any, amb el nom de l’any de les dades. Cada edició es congela quan es publica: si hi ha una errata, es corregix amb una nota amb data dins de l’edició i en el registre de canvis.", "Una edición por año, con el nombre del año de los datos. Cada edición se congela cuando se publica: si hay una errata, se corrige con una nota con fecha dentro de la edición y en el registro de cambios.")}</p>'
          f'<ul class="ediciones"><li class="tarjeta"><a class="mas" style="margin:0" href="2025/">Informe {A1} →</a>'
          f'<p class="nota" style="margin:6px 0 0">{T(f"Dades de {PER}. Versió del {fecha(INFO["version"])} (edició en preparació; es congelarà en publicar-se).", f"Datos de {PER}. Versión del {fecha(INFO["version"])} (edición en preparación; se congelará al publicarse).")}</p></li></ul>'
          f'<p class="nota" style="margin-top:14px"><a href="{R2}metode/#informes">{T("Com es fan i es congelen els informes →", "Cómo se hacen y se congelan los informes →")}</a></p>')
    t2 = ("Informes · " + S.MARCA[0], "Informes · " + S.MARCA[1])
    d2 = ("Informes anuals de l'observatori sobre els accidents de bici i patinet a València.", "Informes anuales del observatorio sobre los accidentes de bici y patinete en València.")
    S.escribir(BUILD / "informe/index.html", S.pagina("informe", "informe/", R2, t2, d2, c2, INFO, [("inici", S.NOM["inici"]), (None, S.NOM["informes"])], "og/informe.png"))


# ---------------------------------------------------------------- datos y método
# «Dades i mètode» en tres páginas (07/11/2026, decisión del usuario: «sepáralo, y en el menú una sola entrada»):
# /dades/ para reutilizar los datos, /metode/ para cómo se hace (con el método viejo, tema a tema) y /sobre/ (quiénes
# somos, accesibilidad, código y registro de cambios, desde el pie). Una sola entrada de menú («Dades i mètode»), que se
# marca en /dades/ y /metode/; las tres llevan pestañas entre ellas. Las anclas viejas de /dades/ redirigen a su sitio.
PAG_DM = {"dades": ["descarrega", "limits", "base", "fitxes"],
          "metode": ["resum", "carrers", "filtres", "seguiment", "informes"],
          "sobre": ["continuitat", "codi", "privacitat", "accessibilitat"]}
METODE_VIEJO = ["datos", "contar", "meta", "uso", "lugares", "normal", "plan", "gravedad", "limites", "errores", "revisiones", "futuro"]
TIT_DM = {"dades": (("Dades", "Datos"), ("Les dades: descarrega, límits i ús", "Los datos: descarga, límites y uso"),
                    ("Què hi ha, com descarregar-ho, què no permet saber i com citar-ho.", "Qué hay, cómo descargarlo, qué no permite saber y cómo citarlo.")),
          "metode": (("Mètode", "Método"), ("Com ho fem", "Cómo lo hacemos"),
                     ("Cada decisió, explicada en llenguatge planer, amb el detall tècnic en les caixes plegables.", "Cada decisión, explicada en lenguaje llano, con el detalle técnico en las cajas plegables.")),
          "sobre": (("Sobre l'observatori", "Sobre el observatorio"), ("Sobre l'observatori", "Sobre el observatorio"),
                    ("Qui som, com es manté, el codi, la privacitat, l'accessibilitat i tot el que ha canviat.", "Quiénes somos, cómo se mantiene, el código, la privacidad, la accesibilidad y todo lo que ha cambiado."))}


def pestanyes_dm(actual, R_):
    o = []
    for k in ("dades", "metode", "sobre"):
        cur = ' aria-current="page"' if k == actual else ""
        o.append(f'<a href="{R_}{k}/"{cur}>{T(*TIT_DM[k][0])}</a>')
    return f'<nav class="pest-dm" aria-label="Dades i mètode / Datos y método">{"".join(o)}</nav>'


def p_dm(pag):
    R_ = "../"
    c = SD.cifras(CON, O, R, P, M)
    secs = {l: {k: (t, h) for k, t, h in SD.secciones(c, l)} for l in ("va", "es")}
    ids = PAG_DM[pag]
    bloques = []
    for k in ids:
        tv, hv = secs["va"][k]; he = secs["es"][k][1]
        bloques.append(f'<section class="dades-sec" id="{k}"><h2>{T(ESC(tv["va"]), ESC(tv["es"]))}</h2><div data-l="va">{hv.replace("{RAIZ}", R_)}</div><div data-l="es" lang="es">{he.replace("{RAIZ}", R_)}</div></section>')
    toc = [(k, (secs["va"][k][0]["va"], secs["va"][k][0]["es"])) for k in ids]
    css = scr = viejo = canvis = qui = ""
    toc_viejo = ""
    if pag == "metode":
        css, cuerpo = derivar("metode.plantilla.html", "metode.js", "web-metode", R_)
        scr = cuerpo[cuerpo.index("<script"):]
        viejo = (f'<section class="dades-sec" id="metode-detall"><h2>{T("El mètode, tema a tema", "El método, tema a tema")}</h2>'
                 f'<p class="nota">{T("Totes les xifres es calculen amb les mateixes dades i el mateix codi que la resta de la web.", "Todas las cifras se calculan con los mismos datos y el mismo código que el resto de la web.")}</p>'
                 f'<div class="vieja"><div id="contingut-metode"></div></div></section>')
        scr = scr.replace('getElementById("contingut")', 'getElementById("contingut-metode")').replace('document.querySelectorAll("main section")', 'document.querySelectorAll("#contingut-metode section")')
        scr = '<div hidden><button id="l-va" aria-pressed="true">VA</button><button id="l-es" aria-pressed="false">ES</button></div>' + scr
        toc_viejo = f'<p>{T("El mètode, tema a tema", "El método, tema a tema")}</p><ol id="toc"></ol>'
    if pag == "sobre":
        qui = (f'<section class="dades-sec" id="qui"><h2>{T("Qui som", "Quiénes somos")}</h2>'
               f'<p>{T("L&#39;Observatori de la bici i el patinet de València és una iniciativa ciutadana independent. Seguix amb les dades obertes de l&#39;Ajuntament on passen els accidents amb bici i patinet, què fa l&#39;Ajuntament per a reduir-los i si funciona. No depén de l&#39;Ajuntament, que no participa en aquest treball ni l&#39;avala.", "El Observatorio de la bici y el patinete de València es una iniciativa ciudadana independiente. Sigue con los datos abiertos del Ayuntamiento dónde ocurren los accidentes con bici y patinete, qué hace el Ayuntamiento para reducirlos y si funciona. No depende del Ayuntamiento, que no participa en este trabajo ni lo avala.")}</p>'
               f'<p>{T("Per a qualsevol cosa, escriu-nos a", "Para cualquier cosa, escríbenos a")} <a href="mailto:{S.CORREU}">{S.CORREU}</a>.</p></section>')
        toc.insert(0, ("qui", ("Qui som", "Quiénes somos")))
        tipos = {"datos": ("Dades", "Datos"), "metode": ("Mètode", "Método"), "web": ("Web", "Web")}
        lc = "".join(f'<li data-tipo="{ESC(t)}"><span>{fecha(f)}</span><span class="t">{T(*tipos[t])}</span><span>{T(ESC(va), ESC(es))}</span></li>' for f, t, va, es in reversed(CAMBIOS))
        nc = len(CAMBIOS); f0 = min(x[0] for x in CAMBIOS)
        canvis = (f'<section class="dades-sec" id="canvis"><h2>{T("Què ha canviat", "Qué ha cambiado")}</h2>'
                  f'<p class="nota">{T(f"{nc} canvis públics en les dades, el mètode o la web des del {fecha(f0)}, del més nou al més antic.", f"{nc} cambios públicos en los datos, el método o la web desde el {fecha(f0)}, del más nuevo al más antiguo.")}</p>'
                  f'<div class="chips" role="group" aria-label="Filtra els canvis / Filtrar los cambios"><button class="chip" type="button" data-ft="" aria-pressed="true">{T("Tot", "Todo")}</button>'
                  + "".join(f'<button class="chip" type="button" data-ft="{k}" aria-pressed="false">{T(*v)}</button>' for k, v in tipos.items())
                  + f'</div><ul class="cambios">{lc}</ul></section>')
        toc.append(("canvis", ("Què ha canviat", "Qué ha cambiado")))
    toc_html = "".join(f'<li><a href="#{k}">{T(ESC(va), ESC(es))}</a></li>' for k, (va, es) in toc)
    k0, h1, sub = TIT_DM[pag]
    cuerpo_html = f'''<p class="kicker">{T("Dades i mètode", "Datos y método")}</p>
{pestanyes_dm(pag, R_)}
<h1 class="h1-pag">{T(*h1)}</h1>
<p class="sub">{T(*sub)}</p>
<div class="lado"><nav class="toc" aria-label="En aquesta pàgina / En esta página"><p>{T("En aquesta pàgina", "En esta página")}</p><ol>{toc_html}</ol>
{toc_viejo}</nav>
<div>{qui}{"".join(bloques)}{viejo}{canvis}</div></div>'''
    # anclas viejas (de cuando todo estaba en /dades/) → su página nueva; y los alias del boceto
    mover = {**{k: f"{R_}metode/#{k}" for k in PAG_DM["metode"] + METODE_VIEJO if k != "limites"},
             **{k: f"{R_}sobre/#{k}" for k in PAG_DM["sobre"] + ["canvis"]},
             "cambios": f"{R_}sobre/#canvis", "codigo": f"{R_}sobre/#codi", "medidas": f"{R_}metode/#seguiment",
             "objetivo": f"{R_}metode/#meta", "resumen": f"{R_}metode/#resum", "limites": "#limits", "descarga": "#descarrega"}
    js = ""
    if pag == "dades":
        js = ("<script>(function(){var m=" + json.dumps({"#" + k: v for k, v in mover.items()}) +
              ";function al(){var u=m[location.hash];if(u)location.replace(u);}al();addEventListener(\"hashchange\",al);})();</script>\n")
    if pag == "sobre":
        js = '''<script>
(function(){
  var cs=[].slice.call(document.querySelectorAll(".cambios li"));
  document.querySelectorAll(".chips .chip[data-ft]").forEach(function(b){ b.addEventListener("click",function(){
    var f=b.getAttribute("data-ft"); cs.forEach(function(li){ li.hidden=!!f&&li.getAttribute("data-tipo")!==f; });
    document.querySelectorAll(".chips .chip[data-ft]").forEach(function(x){ x.setAttribute("aria-pressed",String(x===b)); }); }); });
})();
</script>
'''
    marca = (TIT_DM[pag][0][0] + " · " + S.MARCA[0], TIT_DM[pag][0][1] + " · " + S.MARCA[1])
    desc = {"dades": ("Descarrega els accidents de bici i patinet de València situats en el mapa: què hi ha, què no permeten saber, privacitat i com citar-ho.",
                      "Descarga los accidentes de bici y patinete de València situados en el mapa: qué hay, qué no permiten saber, privacidad y cómo citarlo."),
            "metode": ("Com situem els accidents en el mapa, com fem els llocs i els carrers, com seguim l'objectiu del Pla i les mesures de l'Ajuntament.",
                       "Cómo situamos los accidentes en el mapa, cómo hacemos los lugares y las calles, cómo seguimos el objetivo del Plan y las medidas del Ayuntamiento."),
            "sobre": ("Qui fa l'observatori, com es manté i s'actualitza, codi obert, privacitat, accessibilitat i registre de canvis.", "Quién hace el observatorio, cómo se mantiene y actualiza, código abierto, privacidad, accesibilidad y registro de cambios.")}[pag]
    pasos = [("inici", S.NOM["inici"]), ("dades", S.NOM["dades"]), (None, TIT_DM[pag][0])] if pag != "dades" else [("inici", S.NOM["inici"]), (None, S.NOM["dades"])]
    if pag == "dades":
        # Data Package (Frictionless) de los CSV del ZIP del mapa, en las dos lenguas: /dades/datapackage.json
        S.escribir(BUILD / "dades/datapackage.json", json.dumps(SD.datapackage(INFO, A0, A1), ensure_ascii=False, indent=2) + "\n")
        # metadatos estándar del conjunto (schema.org/Dataset, que leen Google Dataset Search y los catálogos; criterio 3 de
        # las bases: «estándares abiertos y buenas prácticas»). Sin «distribution» hasta que haya fichero versionado (pend. 74)
        ds = {"@context": "https://schema.org", "@type": "Dataset",
              "name": "Accidents amb bici i patinet a València situats en el mapa / Accidentes con bici y patinete en València situados en el mapa",
              "description": ("Accidents de trànsit amb almenys una bici o un patinet a València, del portal de dades obertes de l'Ajuntament, "
                              "situats en el mapa amb el carrerer municipal i agrupats en cruïlles i trams de carrer. / Accidentes de tráfico con "
                              "al menos una bici o un patinete en València, del portal de datos abiertos del Ayuntamiento, situados en el mapa "
                              "con el callejero municipal y agrupados en cruces y tramos de calle."),
              "url": f"{S.DOMINIO}/dades/", "sameAs": f"{S.DOMINIO}/mapa/",
              "license": "https://creativecommons.org/licenses/by/4.0/", "isAccessibleForFree": True,
              "inLanguage": ["ca", "es"], "temporalCoverage": f"{A0}/{A1}", "dateModified": INFO["version"],
              "version": INFO["version"],
              "spatialCoverage": {"@type": "Place", "name": "València", "geo": {"@type": "GeoShape", "box": "39.40 -0.43 39.53 -0.31"}},
              "creator": {"@type": "Organization", "name": "Observatori de la bici i el patinet de València", "email": S.CORREU, "url": S.DOMINIO},
              "isBasedOn": {"@type": "Dataset", "name": INFO["conjunto"], "url": "https://opendata.vlci.valencia.es",
                            "creator": {"@type": "Organization", "name": "Ajuntament de València"}},
              "keywords": ["seguretat viària", "seguridad vial", "bicicleta", "patinet elèctric", "VMP", "accidents", "València", "dades obertes"],
              "variableMeasured": ["data i hora", "vehicles implicats", "gravetat", "factors concurrents", "coordenades (WGS 84)"]}
        css += '<script type="application/ld+json">' + json.dumps(ds, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
    html = S.pagina("dades" if pag != "sobre" else None, f"{pag}/", R_, marca, desc, cuerpo_html, INFO, pasos, "og/metode.png",
                    extra_head=css,
 extra_fin=scr + js)
    S.escribir(BUILD / pag / "index.html", html)


def p_dades():
    for pag in ("dades", "metode", "sobre"): p_dm(pag)


# ---------------------------------------------------------------- índices de lugares y calles
def inicial(nom):
    """Letra del índice: la del nombre propio (sin «Avinguda de», «Calle del»…), sin tilde (nombres.clave)."""
    c = N.clave(nom)[:1].upper()
    return c if c.isalpha() else "#"


def p_indice(clase):
    R_ = "../"
    fs = [f for f in FICHAS if f[0] == clase]
    tot = len(fs)
    acc = lambda n, l: (f"{num(n)} accident" + ("" if n == 1 else "s")) if l == "va" else (f"{num(n)} accidente" + ("" if n == 1 else "s"))
    li = lambda f, l: f'<li><a href="{f[1]}/">{ESC(f[2] if l == "va" else f[3])}</a><b>{acc(f[4], l)}</b></li>'
    bloques = []
    for l in ("va", "es"):
        k = 2 if l == "va" else 3
        lang_attr = ' lang="es"' if l == "es" else ""
        por_nom = sorted(fs, key=lambda f: N.clave(f[k]))
        por_n = sorted(fs, key=lambda f: (-f[4], f[k]))
        if clase == "carrer":
            grupos = collections.OrderedDict()
            for f in sorted(por_nom, key=lambda f: inicial(f[k])):
                grupos.setdefault(inicial(f[k]), []).append(f)
            letras = "".join(f'<li><a href="#{l}-{g}">{g}</a></li>' for g in grupos)
            nom_html = (f'<ul class="letras" aria-label="{"Lletres" if l == "va" else "Letras"}">{letras}</ul>'
                        + "".join(f'<section class="idx-grupo" id="{l}-{g}"><h2>{g}</h2><ul class="idx">{"".join(li(f, l) for f in xs)}</ul></section>' for g, xs in grupos.items()))
            n_html = f'<section class="idx-grupo"><ul class="idx">{"".join(li(f, l) for f in por_n)}</ul></section>'
            def_ord = "nom"
        else:
            nom_html = f'<section class="idx-grupo"><ul class="idx">{"".join(li(f, l) for f in por_nom)}</ul></section>'
            n_html = f'<section class="idx-grupo"><ul class="idx">{"".join(li(f, l) for f in por_n)}</ul></section>'
            def_ord = "n"
        bloques.append(f'<div data-l="{l}"{lang_attr}><div data-lista="nom"{"" if def_ord == "nom" else " hidden"}>{nom_html}</div><div data-lista="n"{"" if def_ord == "n" else " hidden"}>{n_html}</div></div>')
    d_ord = "nom" if clase == "carrer" else "n"
    ctrl = (f'<div class="idx-ctrl" data-indice data-orden-def="{d_ord}"><label><span class="sr">{T("Filtra", "Filtrar")}</span>'
            f'<input type="search" autocomplete="off" placeholder="Filtra per nom" data-ph-va="Filtra per nom" data-ph-es="Filtrar por nombre"></label>'
            f'<span role="group" aria-label="Ordena / Ordenar"><button class="chip" type="button" data-orden="nom" aria-pressed="{str(d_ord == "nom").lower()}">{T("Per nom", "Por nombre")}</button> '
            f'<button class="chip" type="button" data-orden="n" aria-pressed="{str(d_ord == "n").lower()}">{T("Per accidents", "Por accidentes")}</button></span>'
            f'<span class="cuenta" aria-live="polite" data-va="{{n}} de {tot}" data-es="{{n}} de {tot}">{tot}</span></div>')
    mn = META["min_ficha"]
    if clase == "lloc":
        h1 = T("Tots els llocs amb fitxa", "Todos los lugares con ficha")
        sub = T(f"Les {tot} cruïlles, places i trams de carrer amb {mn} accidents o més amb bici o patinet de {A0} a {A1}. Comptem cada cruïlla amb 30 metres al voltant.", f"Los {tot} cruces, plazas y tramos de calle con {mn} accidentes o más con bici o patinete de {A0} a {A1}. Contamos cada cruce con 30 metros alrededor.")
        t = ("Llocs amb accidents de bici i patinet · " + S.MARCA[0], "Lugares con accidentes de bici y patinete · " + S.MARCA[1])
        d = (f"Llista dels {tot} llocs de València amb {mn} accidents o més amb bici o patinet ({PER}), amb la seua fitxa.", f"Lista de los {tot} lugares de València con {mn} accidentes o más con bici o patinete ({PER}), con su ficha.")
    else:
        h1 = T("Tots els carrers amb fitxa", "Todas las calles con ficha")
        sub = T(f"Els {tot} carrers amb {mn} accidents o més amb bici o patinet de {A0} a {A1}, segons l'adreça escrita en el comunicat de la policia. Un accident en una cruïlla compta en els dos carrers.", f"Las {tot} calles con {mn} accidentes o más con bici o patinete de {A0} a {A1}, según la dirección escrita en el parte de la policía. Un accidente en un cruce cuenta en las dos calles.")
        t = ("Carrers amb accidents de bici i patinet · " + S.MARCA[0], "Calles con accidentes de bici y patinete · " + S.MARCA[1])
        d = (f"Llista dels {tot} carrers de València amb {mn} accidents o més amb bici o patinet ({PER}), amb la seua fitxa.", f"Lista de las {tot} calles de València con {mn} accidentes o más con bici o patinete ({PER}), con su ficha.")
    cuerpo = (f'<h1 class="h1-pag">{h1}</h1><p class="sub">{sub}</p>'
              f'<p class="nota">{T("Són llocs amb accidents registrats, no un índex de risc: no sabem quanta gent hi passa.", "Son lugares con accidentes registrados, no un índice de riesgo: no sabemos cuánta gente pasa.")} '
              f'<a href="{R_}dades/#fitxes">{T("Com fem les fitxes →", "Cómo hacemos las fichas →")}</a></p>{ctrl}{"".join(bloques)}')
    pasos = [("inici", S.NOM["inici"]), ("mapa", S.NOM["mapa"]), (None, S.NOM[clase])]
    S.escribir(BUILD / clase / "index.html", S.pagina("mapa", f"{clase}/", R_, t, d, cuerpo, INFO, pasos, "og/observatori.png"))


def main():
    S.assets(); mapas()
    p_inicio(); p_mapa(); p_ajuntament(); p_informe(); p_dades(); p_indice("lloc"); p_indice("carrer")
    for p in ("index.html", "mapa/index.html", "ajuntament/index.html", "informe/index.html", "informe/2025/index.html", "dades/index.html", "lloc/index.html", "carrer/index.html"):
        print(f"web/proto/build/{p} ({(BUILD / p).stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
