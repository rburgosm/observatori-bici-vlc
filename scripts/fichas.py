"""Fichas estáticas por lugar y por calle, a partir de data/processed/observatorio.sqlite (scripts/construir_sqlite.py).

Escribe, para cada fila de la tabla `ficha` (>= MIN_FICHA siniestros, o con slug ya publicado):
- web/proto/build/lloc/<slug>/index.html   (lugar: nudo de cruce o tramo de calle)
- web/proto/build/carrer/<slug>/index.html (calle: por la dirección escrita de los siniestros)
Cada página lleva las dos lenguas, como el resto de la web: valenciano por defecto y castellano con el botón (localStorage
«obs-lang»); <main data-l="va"> y <main data-l="es" hidden>. Todo el texto va en el HTML (indexable); el minimapa lo dibuja
MapLibre en el navegador con los datos de la propia página (<script type="application/json">), sin imágenes por ficha.
Recursos comunes, con el contenido en el nombre y SRI: build/datos/fichas.<hash8>.css y fichas.<hash8>.js (de
web/proto/fichas/). Índice para el buscador: build/datos/fichas_indice.<hash8>.js y web/proto/datos/fichas_indice.js
(window.FICHAS = [[clase, slug, nombre va, nombre es, siniestros], …]).

Rendimiento: una sola consulta por tabla (no por ficha), plantilla única con sustitución y escritura solo si el contenido
cambia (las fechas de los ficheros no cambian si no cambia nada). Se borran las fichas que ya no están en la tabla.

Privacidad (docs/dataset_licencia_privacidad.md): en la lista de siniestros uno a uno van mes y año (sin día ni hora), los
vehículos, el cruce o el número de portal citado en el parte (no un domicilio) y la gravedad; los factores concurrentes solo
en conjunto. El mapa de la web sigue teniendo el detalle completo del portal.

Uso: .venv/bin/python -I scripts/fichas.py"""
import base64, collections, hashlib, html, json, re, shutil, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))                    # -I no añade la carpeta del script
import sitio                                                  # cabecera, menú, migas, pie y CSS comunes de la web
import sitio_textos_plan as STP                               # títulos y lugares de las medidas del Plan en va y es
import nombres as N                                           # nombres de lugares y calles como los escribe una persona
DB = ROOT / "data/processed/observatorio.sqlite"
W = ROOT / "web/proto"; BUILD = W / "build"; BD = BUILD / "datos"
DOMINIO = "https://observatoribicivlc.org"        # dominio principal (deploy/deploy.conf)
MAPLIBRE = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.js" '
            'integrity="sha384-SYKAG6cglRMN0RVvhNeBY0r3FYKNOJtznwA0v7B5Vp9tr31xAHsZC0DqkQ/pZDmj" crossorigin="anonymous"></script>')
FR = [0, 7, 10, 14, 17, 21, 24]                   # franjas horarias (las de exportar_web.py)
# factores concurrentes (los mismos patrones que exportar_web.py)
FACT = [("prio", "PRIORIDAD", "No respectar la prioritat", "No respetar la prioridad"),
        ("dist", "DISTRA", "Distracció", "Distracción"),
        ("via", "ESTADO O CONDICI", "Estat de la via", "Estado de la vía"),
        ("vel", "VELOCIDAD", "Velocitat inadequada", "Velocidad inadecuada")]
KCAT = [("m", "Cotxe, moto o un altre vehicle", "Coche, moto u otro vehículo"), ("w", "Una persona a peu", "Una persona a pie"),
        ("d", "Una altra bici o un altre patinet", "Otra bici u otro patinete"), ("s", "Ningú més (caiguda)", "Nadie más (caída)")]
GRAV = {"SIN HERIDOS": ("Sense ferits", "Sin heridos"), "CON HERIDOS LEVES": ("Ferits lleus", "Heridos leves"),
        "CON HERIDOS BAJA GRAVEDAD": ("Ferits de baixa gravetat", "Heridos de baja gravedad"),
        "CON HERIDOS GRAVES": ("Ferits greus", "Heridos graves"), "CON FALLECIDOS": ("Morts", "Fallecidos")}
VEH = {"BICICLETA": ("bici", "bici"), "VMP": ("patinet", "patinete"), "TURISMO": ("cotxe", "coche"),
       "TODO TERRENO": ("cotxe", "coche"), "MOTOCICLETA": ("moto", "moto"), "CICLOMOTOR": ("ciclomotor", "ciclomotor"),
       "PEATÓN": ("vianant", "peatón"), "FURGONETA": ("furgoneta", "furgoneta"), "AUTOBÚS": ("autobús", "autobús"),
       "CAMIÓN": ("camió", "camión"), "TRANVÍA": ("tramvia", "tranvía")}
PLURAL = {"va": {"un altre vehicle": "altres vehicles", "autobús": "autobusos", "camió": "camions", "ciclomotor": "ciclomotors"},
          "es": {"peatón": "peatones", "camión": "camiones", "otro vehículo": "otros vehículos", "autobús": "autobuses", "ciclomotor": "ciclomotores"}}
EST = {"hecha": ("Feta", "Hecha"), "en_marcha": ("En marxa", "En marcha"), "anunciada": ("Anunciada", "Anunciada"),
       "sin_info": ("Sense informació pública", "Sin información pública")}
MES = {"va": "gen feb març abr maig juny jul ag set oct nov des".split(), "es": "ene feb mar abr may jun jul ago sep oct nov dic".split()}
ESC = html.escape


# ---------------------------------------------------------------- textos
def nom_lugar(L, l, D=None):
    """Nombre visible de un lugar en la lengua l (scripts/nombres.py: el mismo en el mapa, las fichas y los índices)."""
    return N.lugar(L["nom"], L["nom_es"], l)


def nom_via(V, l):
    """Nombre visible de una calle (tabla via: nom con el tipo, nom_es)."""
    return N.lugar(V["nom"], V["nom_es"], l)


def _proy():
    from pyproj import Transformer
    a = Transformer.from_crs(4326, 25830, always_xy=True).transform; b = Transformer.from_crs(25830, 4326, always_xy=True).transform
    return a, b
A_UTM, A_GEO = _proy()


def mil(n): return f"{n:,}".replace(",", ".")


def de10(x, n):
    """«x de cada 10», con «menos de 1» y «ninguno» (las dos lenguas)."""
    if n == 0 or x == 0: return ("cap", "ninguno")
    v = 10 * x / n
    if v < 0.5: return ("menys d'1", "menos de 1")
    return (str(round(v)), str(round(v)))


def vehiculos(unidades, l):
    us = [u.strip() for u in (unidades or "").split(",") if u.strip()]
    # primero la bici y el patinete, después lo demás; plural con PLURAL
    orden = {"BICICLETA": 0, "VMP": 1}
    c = collections.Counter(VEH.get(u, ("un altre vehicle", "otro vehículo"))[l == "es"] for u in sorted(us, key=lambda u: orden.get(u, 2)))
    # «dues» con los femeninos en valenciano (bici, moto; revisión UX del 07/11/2026: salía «Dos bicis»)
    FEM = {"bici", "moto"}
    num = lambda n, k: {2: ("dues" if l == "va" and k in FEM else "dos"), 3: "tres", 4: "quatre" if l == "va" else "cuatro"}.get(n, n)
    partes = [k if n == 1 else f"{num(n, k)} {PLURAL[l].get(k, k + 's')}" for k, n in c.items()]
    if not partes: return "—"
    y = " i " if l == "va" else " y "
    t = ", ".join(partes[:-1]) + y + partes[-1] if len(partes) > 1 else partes[0]
    return t[:1].upper() + t[1:]


# ---------------------------------------------------------------- gráficos SVG (texto en tinta; colores por clase)
def svg_años(años, por):
    """Barras apiladas por año: por = {año: [b, p, a]}."""
    W_, H, x0, top, base = 520, 230, 44, 23, 200
    mx = max(1, max(sum(v) for v in por.values()))
    paso = next(p for p in (1, 2, 5, 10, 20, 50, 100, 200) if mx / p <= 5)
    tope = paso * -(-mx // paso)
    y = lambda v: base - (base - top) * v / tope
    o = [f'<svg class="graf w520" viewBox="0 0 {W_} {H}" role="img" aria-hidden="true">']
    for t in range(0, tope + 1, paso):
        o.append(f'<line class="rej" x1="{x0}" x2="512" y1="{y(t):.1f}" y2="{y(t):.1f}"/><text class="tn" x="36" y="{y(t) + 4:.1f}" text-anchor="end">{t}</text>')
    o.append(f'<line class="eje" x1="{x0}" x2="512" y1="{base}" y2="{base}"/>')
    ancho = (512 - x0) / len(años)
    for i, a in enumerate(años):
        cx = x0 + ancho * (i + .5); bw = min(64, ancho * .6); acum = 0
        for cl, v in zip("bpa", por[a]):
            if v:
                o.append(f'<rect class="{cl}" x="{cx - bw / 2:.1f}" y="{y(acum + v):.1f}" width="{bw:.1f}" height="{y(acum) - y(acum + v) - 1:.1f}" rx="2"/>')
            acum += v
        o.append(f'<text class="val" x="{cx:.1f}" y="{y(acum) - 7:.1f}" text-anchor="middle">{acum}</text>'
                 f'<text x="{cx:.1f}" y="222" text-anchor="middle">{a}</text>')
    return "".join(o) + "</svg>"


def svg_hora(fr, ref):
    """Barras por franja horaria (fr) y raya con lo esperable con el reparto de la ciudad (ref, en proporción)."""
    n = sum(fr); W_, base, top, x0 = 520, 180, 30, 34
    esp = [n * r for r in ref]; mx = max(1, max(fr), max(esp))
    y = lambda v: base - (base - top) * v / mx
    et = ["0-7 h", "7-10 h", "10-14 h", "14-17 h", "17-21 h", "21-24 h"]
    o = [f'<svg class="graf w520 hora" viewBox="0 0 {W_} 240" role="img" aria-hidden="true"><line class="eje" x1="{x0}" x2="512" y1="{base}" y2="{base}"/>']
    ancho = (512 - x0) / 6
    for i, v in enumerate(fr):
        cx = x0 + ancho * (i + .5); bw = ancho * .6
        if v: o.append(f'<rect class="k" x="{cx - bw / 2:.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{base - y(v):.1f}" rx="2"/>')
        o.append(f'<line class="lg" x1="{cx - bw / 2 - 4:.1f}" x2="{cx + bw / 2 + 4:.1f}" y1="{y(esp[i]):.1f}" y2="{y(esp[i]):.1f}"/>'
                 f'<text class="val" x="{cx:.1f}" y="{min(y(v), y(esp[i])) - 6:.1f}" text-anchor="middle">{v}</text>'
                 f'<text class="et{" o" if i % 2 else ""}" x="{cx:.1f}" y="202" text-anchor="middle">{et[i]}</text>')
    return "".join(o) + "</svg>"


def comp(filas, nom_aqui):
    """Barras «este lugar» frente a «la ciudad», las dos en «de cada 10» (07/11/2026: antes «19 de 83» al lado de «6» de cada
    10, y se comparaban unidades distintas): filas = [(etiqueta, x, n, ref_proporción, texto x)]."""
    o = ['<div class="comp">']
    d10 = lambda p: str(round(10 * p)) if p >= .05 else "&lt;1"
    for et, x, n, r, tx in filas:
        p = x / max(n, 1)
        o.append(f'<div class="fila"><span class="nom">{et}</span><div class="barras">'
                 f'<span class="br"><i style="width:{100 * p:.0f}%"></i><b>{d10(p) if x else "0"} <small>({tx})</small></b></span>'
                 f'<span class="br c"><i style="width:{100 * r:.0f}%"></i>{d10(r)}</span></div></div>')
    return "".join(o) + "</div>"


# ---------------------------------------------------------------- datos
def cargar(con):
    con.row_factory = sqlite3.Row
    q = lambda s, *a: con.execute(s, a).fetchall()
    meta = {r["clave"]: r["valor"] for r in q("SELECT * FROM meta")}
    años = [int(a) for a in meta["años"].split(",")]
    sin = {r["id"]: dict(r) for r in q("SELECT id, fecha, gravedad, unidades, factores, ubicacion, metodo, lon, lat, año, v, k, uid FROM v_siniestro_bv")}
    via_de = collections.defaultdict(list)            # siniestro -> [(codvia, rol)]
    sin_de_via = collections.defaultdict(list)
    for r in q("SELECT sv.siniestro_id, sv.codvia, sv.rol FROM siniestro_via sv JOIN siniestro_bv b USING (siniestro_id)"):
        via_de[r[0]].append((r[1], r[2])); sin_de_via[r[1]].append(r[0])
    vias = {r["codvia"]: dict(r) for r in q("SELECT codvia, nom, nom_es FROM via")}
    lug = {r["uid"]: dict(r) for r in q("SELECT uid, rank, tipo, nom, nom_es, plaza, codvia, n, v_b, v_p, v_a, k_m, k_w, k_d, k_s, pista_holm, en_top30, geom_wkt FROM lugar")}
    fichas = [dict(r) for r in q("SELECT * FROM ficha ORDER BY clase, slug")]
    plan = {r["id"]: dict(r) for r in q("""SELECT a.id, a.accion_plan, a.actuacion, a.estado, a.fecha_fuente, a.fecha_comprobacion,
               f.url AS url_estado, f.titulo AS tit_estado FROM v_plan_medida a LEFT JOIN plan_fuente f ON f.id = a.fuente_estado_id""")}
    plan_lug = collections.defaultdict(list); plan_via = collections.defaultdict(list)
    for r in q("SELECT actuacion_id, uid FROM plan_actuacion_lugar ORDER BY d_m"):
        if r[0] in plan: plan_lug[r[1]].append(r[0])
    for r in q("SELECT actuacion_id, codvia FROM plan_actuacion_via WHERE nombrada = 1 ORDER BY d_m"):
        if r[0] in plan: plan_via[r[1]].append(r[0])
    return dict(meta=meta, años=años, sin=sin, via_de=via_de, sin_de_via=sin_de_via, vias=vias, lug=lug, fichas=fichas,
                plan=plan, plan_lug=plan_lug, plan_via=plan_via)


def perfil(ss):
    fr = [0] * 6
    for s in ss:
        h = int(s["fecha"][11:13]); fr[next(i for i in range(6) if FR[i] <= h < FR[i + 1])] += 1
    import datetime
    lab = sum(datetime.date.fromisoformat(s["fecha"][:10]).weekday() < 5 for s in ss)
    # factores: solo el último año (07/11/2026, revisión de datos): los de antes no se comparan (sin ningún factor el 35 %
    # en 2022 y el 12 % en 2025) y mezclar años hacía parecer «menos distraído» un lugar con más casos antiguos
    sf = [s for s in ss if s["año"] == AÑO_FACT]
    return {"k": collections.Counter(s["k"] for s in ss), "fr": fr, "lab": lab, "nf": len(sf),
            "f": {c: sum(pat in (s["factores"] or "") for s in sf) for c, pat, _, _ in FACT}}


AÑO_FACT = None          # el último año de la serie; lo fija main() antes de calcular los perfiles


# ---------------------------------------------------------------- página
def pagina(D, f, slug_lloc, slug_carrer, ref, ejes_idx):
    import numpy as np, shapely, shapely.wkt
    A = D["años"]; a0, a1 = A[0], A[-1]
    if f["clase"] == "lloc":
        L = D["lug"][f["uid"]]; ss = [s for s in D["sin"].values() if s["uid"] == f["uid"]]
        nom = {"va": nom_lugar(L, "va", D), "es": nom_lugar(L, "es", D)}
        zona = shapely.wkt.loads(L["geom_wkt"])
        if L["tipo"] == "nudo":                          # lo que se cuenta: envolvente + R = 30 m (lugares.geometria)
            pr = lambda g, f: shapely.transform(g, lambda c: np.column_stack(f(c[:, 0], c[:, 1])))
            zona = pr(pr(zona, A_UTM).buffer(30), A_GEO)
    else:
        V = D["vias"][f["codvia"]]; ss = [D["sin"][i] for i in D["sin_de_via"][f["codvia"]]]
        nom = {"va": nom_via(V, "va"), "es": nom_via(V, "es")}; zona = None
    ss.sort(key=lambda s: s["fecha"], reverse=True)
    n = len(ss); assert n == f["n"], (f["slug"], n, f["n"])
    mix = [sum(s["v"] == c for s in ss) for c in "bpa"]
    por = {a: [sum(s["año"] == a and s["v"] == c for s in ss) for c in "bpa"] for a in A}
    P = perfil(ss)
    con_pt = [s for s in ss if s["lon"] is not None]
    # minimapa: accidentes agrupados por punto y vehículo; calles del callejero alrededor (la de la ficha resaltada)
    g = collections.Counter((round(s["lon"], 5), round(s["lat"], 5), s["v"]) for s in con_pt)
    pts = [[lo, la, v, k] for (lo, la, v), k in sorted(g.items())]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    if zona is not None:
        b = zona.bounds; xs += [b[0], b[2]]; ys += [b[1], b[3]]
    bbox = [[min(xs), min(ys)], [max(xs), max(ys)]] if xs else None
    calles = {"type": "FeatureCollection", "features": []}
    if bbox:
        mx_ = 0.005           # 07/11/2026: unos 400 m alrededor, para que el minimapa tenga contexto (maxZoom 15,6 en fichas.js)
        caja = shapely.box(bbox[0][0] - mx_, bbox[0][1] - mx_ * .8, bbox[1][0] + mx_, bbox[1][1] + mx_ * .8)
        ejes, arbol = ejes_idx
        # calle: solo ella y las que la cruzan en las direcciones de sus accidentes (una avenida cruza media ciudad)
        cerca = {cv for s in ss for cv, _ in D["via_de"][s["id"]]} if f["clase"] == "carrer" else None
        for i in arbol.query(caja):
            cv, geom = ejes[i]
            if cerca is not None and cv not in cerca: continue
            gg = geom.intersection(caja)
            if gg.is_empty: continue
            sel = int(f["clase"] == "carrer" and cv == f["codvia"] or f["clase"] == "lloc" and L["tipo"] == "tramo" and cv == L["codvia"])
            calles["features"].append({"type": "Feature", "properties": {"s": sel}, "geometry": geojson(gg, 0.00002)})
    url = {"lloc": f"{DOMINIO}/lloc/{f['slug']}/", "carrer": f"{DOMINIO}/carrer/{f['slug']}/"}[f["clase"]]
    per = f"{a0}-{a1}"
    titulo = {"va": f"{nom['va']}: {n} accidents amb bici o patinet ({per}) · Observatori de la bici i el patinet",
              "es": f"{nom['es']}: {n} accidentes con bici o patinete ({per}) · Observatorio de la bici y el patinete"}
    desc = {"va": f"{n} accidents amb bici o patinet de {a0} a {a1} " + (f"en {N.con_articulo(nom['va'], 'va')}" if f["clase"] == "carrer" else f"en aquest lloc de València") +
                  ", segons les dades obertes de l'Ajuntament. Llocs amb molts accidents, sense dades d'ús: no és un índex de risc.",
            "es": f"{n} accidentes con bici o patinete de {a0} a {a1} " + (f"en {N.con_articulo(nom['es'], 'es')}" if f["clase"] == "carrer" else "en este lugar de València") +
                  ", según los datos abiertos del Ayuntamiento. Lugares con muchos accidentes, sin datos de uso: no es un índice de riesgo."}
    datos = {"titulo": titulo, "url": url, "pts": pts, "bbox": bbox, "calles": calles,
             "zona": geojson(zona, 0.000005) if zona is not None else None}
    mains = []
    for l in ("va", "es"):
        T = lambda va, es: va if l == "va" else es
        o = []
        if f["clase"] == "lloc":
            tipo = T("Cruïlla", "Cruce") if L["tipo"] == "nudo" else T("Tram de carrer", "Tramo de calle")
            if L["plaza"] and L["nom"].startswith("PL ") and " cruce " not in L["nom"]: tipo = T("Plaça o glorieta", "Plaza o glorieta")
            top = (f'<span class="tipo top">{T("Un dels 30 llocs amb més accidents de València", "Uno de los 30 lugares con más accidentes de València")} · n.º {L["rank"]}</span> '
                   if L["en_top30"] else "")
            ca = D["cob_any"]; a_0, a_1 = min(ca), max(ca)
            nota_puesto = (f'<p class="nota" style="margin:8px 0 0">' + T(
                f"El lloc en la llista té en compte que els primers anys es van poder situar en el mapa menys accidents ({round(100 * ca[a_0])} de cada 100 en {a_0} i {round(100 * ca[a_1])} en {a_1}): els d'aquells anys compten una mica més. Per això un lloc amb menys accidents pot anar per davant d'un altre amb més.",
                f"El puesto tiene en cuenta que en los primeros años se pudieron situar en el mapa menos accidentes ({round(100 * ca[a_0])} de cada 100 en {a_0} y {round(100 * ca[a_1])} en {a_1}): los de esos años cuentan un poco más. Por eso un lugar con menos accidentes puede ir por delante de otro con más.") + "</p>"
                if L["en_top30"] else "")
            cab_tipo = f'{top}<span class="tipo">{tipo}</span>'
        else:
            cab_tipo = f'<span class="tipo">{T("Fitxa de carrer", "Ficha de calle")}</span>'
        o.append('<div class="ficha-cab"><div>' + cab_tipo + f'<h1>{re.sub(r"(\d)-(\d)", "\\1\u2011\\2", ESC(nom[l]))}</h1>' + (nota_puesto if f["clase"] == "lloc" else ""))
        o.append(f'<div class="grande"><span class="cifra">{mil(n)}</span><p class="etq">{T("accidents amb bici o patinet", "accidentes con bici o patinete")} {T("de", "de")} {a0} {T("a", "a")} {a1}</p></div>')
        o.append('<div class="mix" aria-hidden="true">' + "".join(f'<i style="flex:{x};background:var(--{c})"></i>' for x, c in zip(mix, ("bici", "pat", "amb")) if x) + "</div>")
        cn = lambda x: str(x) if x else T("Cap", "Ninguno")
        o.append(f'<div class="ley" style="margin:0"><span><i class="pt b"></i>{cn(mix[0])} {T("només amb bici", "solo con bici")}</span>'
                 f'<span><i class="pt p"></i>{cn(mix[1])} {T("només amb patinet", "solo con patinete")}</span>'
                 f'<span><i class="pt a"></i>{cn(mix[2])} {T("amb bici i patinet alhora", "con bici y patinete a la vez")}</span></div>')
        if f["clase"] == "lloc":
            o.append(f'<p class="aviso-exp nota">' + (T("És un lloc amb molts accidents, no un índex de risc: no sabem quantes bicis i patinets hi passen.", "Es un lugar con muchos accidentes, no un índice de riesgo: no sabemos cuántas bicis y patinetes pasan por él.")
                     if L["en_top30"] else T("És un lloc amb accidents registrats, no un índex de risc: no sabem quantes bicis i patinets hi passen.", "Es un lugar con accidentes registrados, no un índice de riesgo: no sabemos cuántas bicis y patinetes pasan por él.")) + '</p>')
            enl = []
            for cv in sorted({cv for s in ss for cv, _ in D["via_de"][s["id"]]}, key=lambda c: -sum(c in [x for x, _ in D["via_de"][s["id"]]] for s in ss)):
                if cv in slug_carrer:
                    enl.append(f'<a href="../../carrer/{slug_carrer[cv]}/">{ESC(nom_via(D["vias"][cv], l))}</a>')
            if enl: o.append(f'<p class="nota" style="margin-top:10px">{T("Fitxa del carrer", "Ficha de la calle")}: {" · ".join(enl[:4])}</p>')
        else:
            tops = collections.Counter(s["uid"] for s in ss if s["uid"] is not None and D["lug"][s["uid"]]["en_top30"])
            if tops:
                ls = [f'<a href="../../lloc/{slug_lloc[u]}/">{ESC(nom_lugar(D["lug"][u], l, D))}</a>' for u, _ in tops.most_common() if u in slug_lloc]
                o.append(f'<p style="margin:14px 0 0">{T("Llocs d&#39;aquest carrer entre els 30 amb més accidents de la ciutat", "Lugares de esta calle entre los 30 con más accidentes de la ciudad")}: {" · ".join(ls)}</p>')
            else:
                o.append(f'<p style="margin:14px 0 0">{T("Cap dels seus encreuaments no està entre els 30 llocs amb més accidents. Un carrer sencer suma tots els seus trams, i els 30 són llocs solts: per això les xifres no es comparen.", "Ninguno de sus cruces está entre los 30 lugares con más accidentes. Una calle entera suma todos sus tramos, y los 30 son lugares sueltos: por eso las cifras no se comparan.")}</p>')
            o.append(f'<p class="aviso-exp nota">{T("Un carrer llarg suma més accidents que un de curt: no vol dir que siga més perillós.", "Una calle larga suma más accidentes que una corta: no quiere decir que sea más peligrosa.")}</p>')
        o.append(f'<div class="acciones"><button class="btn" type="button" data-compartir data-copiado="{T("Enllaç copiat", "Enlace copiado")}">{T("Compartir aquesta fitxa", "Compartir esta ficha")}</button></div></div>')
        # mapa
        sinpt = n - len(con_pt)
        nota_mapa = (T("Zona comptada: la cruïlla i 30 m al voltant (línia discontínua).", "Zona contada: el cruce y 30 m alrededor (línea discontinua).")
                     if f["clase"] == "lloc" and L["tipo"] == "nudo" else
                     T("Tram comptat: la línia fosca; cada accident, al tram més pròxim.", "Tramo contado: la línea oscura; cada accidente, al tramo más cercano.")
                     if f["clase"] == "lloc" else T("En gris fosc, el carrer; en color, els seus accidents situats en el mapa.", "En gris oscuro, la calle; en color, sus accidentes situados en el mapa."))
        nota_mapa += " " + T("Cercle més gran = més accidents en el mateix punt.", "Círculo más grande = más accidentes en el mismo punto.")
        if sinpt == 1: nota_mapa += " " + T("1 accident no es pot situar en el mapa (l'adreça no ho permet).", "1 accidente no se puede situar en el mapa (la dirección no lo permite).")
        elif sinpt: nota_mapa += " " + T(f"{sinpt} accidents no es poden situar en el mapa (l'adreça no ho permet).", f"{sinpt} accidentes no se pueden situar en el mapa (la dirección no lo permite).")
        o.append(f'<div><div class="mapa mm" role="img" aria-label="{T("Mapa", "Mapa")}: {ESC(nom[l])}">'
                 f'<div class="mapa-sin">{T("El mapa necessita JavaScript.", "El mapa necesita JavaScript.") if pts else T("Cap accident d&#39;aquest carrer no es pot situar en el mapa.", "Ningún accidente de esta calle se puede situar en el mapa.")}</div></div>'
                 f'<p class="nota" style="margin-top:6px">{nota_mapa}</p></div></div>')
        # tarjetas
        o.append('<div class="rejilla">')
        lugar_txt = T("en aquest lloc", "en este lugar") if f["clase"] == "lloc" else T("en aquest carrer", "en esta calle")
        o.append(f'<section class="tarjeta" style="min-width:0"><h2>{T("Accidents cada any", "Accidentes cada año")}</h2><p class="intro">{T("Accidents amb bici o patinet", "Accidentes con bici o patinete")} {lugar_txt}, {a0}-{a1}</p>'
                 + svg_años(A, por) +
                 f'<div class="ley"><span><i class="pt b"></i>{T("Bici", "Bici")}</span><span><i class="pt p"></i>{T("Patinet", "Patinete")}</span><span><i class="pt a"></i>{T("Bici i patinet", "Bici y patinete")}</span></div>'
                 f'<p class="nota" style="margin-top:8px">{T("Amb tan pocs casos, pujar o baixar d&#39;un any a l&#39;altre pot ser casualitat.", "Con tan pocos casos, subir o bajar de un año a otro puede ser casualidad.") if n < 40 else ""} '
                 f'{T("Des de juliol de 2024 la Policia Local registra els accidents amb un sistema nou (SIASV).", "Desde julio de 2024 la Policía Local registra los accidentes con un sistema nuevo (SIASV).")}'
                 + (" " + T(f"A més, els primers anys es podien situar en el mapa menys accidents ({round(100 * D['cob_any'][a0])} de cada 100 en {a0} i {round(100 * D['cob_any'][a1])} en {a1}): part de la pujada pot vindre d'això.",
                            f"Además, los primeros años se podían situar en el mapa menos accidentes ({round(100 * D['cob_any'][a0])} de cada 100 en {a0} y {round(100 * D['cob_any'][a1])} en {a1}): parte de la subida puede venir de ahí.")
                    if f["clase"] == "lloc" else "")

                 + (" " + T("Des de llavors la policia anota més accidents pel número de portal i menys “en la cruïlla”: una cruïlla pot perdre casos sense que hi canvie res.",
                            "Desde entonces la policía anota más accidentes por número de portal y menos “en el cruce”: un cruce puede perder casos sin que cambie nada.")
                    if f["clase"] == "lloc" and L["tipo"] == "nudo" else "") + '</p></section>')
        # con quién
        rk = ref["k"][L["tipo"]] if f["clase"] == "lloc" else ref["k"]["todo"]
        refn = sum(rk.values())
        et_ref = (T("Resta de cruïlles de la ciutat", "Resto de los cruces de la ciudad") if f["clase"] == "lloc" and L["tipo"] == "nudo"
                  else T("Resta de trams de la ciutat", "Resto de los tramos de la ciudad") if f["clase"] == "lloc" else T("Mitjana de la ciutat", "Media de la ciudad"))
        filas = [(T(va, es), P["k"][c], n, rk[c] / refn, f"{P['k'][c]} {T('de', 'de')} {n}") for c, va, es in KCAT]
        o.append(f'<section class="tarjeta" style="min-width:0"><h2>{T("Amb qui xoquen les bicis i els patinets?", "¿Con quién chocan las bicis y los patinetes?")}</h2>'
                 f'<p class="intro">{T("Accidents", "Accidentes")} {lugar_txt}</p>'
                 f'<div class="ley-comp"><span><i style="height:12px;background:var(--ink)"></i>{T("Aquest lloc", "Este lugar") if f["clase"] == "lloc" else T("Aquest carrer", "Esta calle")}</span>'
                 f'<span><i style="height:7px;background:var(--mix)"></i>{et_ref} ({T("de cada 10", "de cada 10")})</span></div>' + comp(filas, "") +
                 f'<p class="nota" style="margin-top:10px">{T("«Una altra bici o un altre patinet» suma els xocs entre dues bicis, entre dos patinets i entre bici i patinet.", "«Otra bici u otro patinete» suma los choques entre dos bicis, entre dos patinetes y entre bici y patinete.")}</p>')
        if f["clase"] == "lloc" and L["pista_holm"]:
            c = L["pista_holm"]; et = dict((k, T(va, es)) for k, va, es in KCAT)[c].lower()
            x10 = de10(P["k"][c], n)[l == "es"]
            o.append(f'<p class="revisar"><b>{T("Senyal en les dades", "Señal en los datos")}:</b> {T("ací,", "aquí,")} {x10} {T("de cada 10 accidents són amb", "de cada 10 accidentes son con")} «{et}», '
                     f'{T("més que en la resta de", "más que en el resto de")} {T("cruïlles", "cruces") if L["tipo"] == "nudo" else T("trams", "tramos")}. '
                     f'{T("La diferència és massa gran per a ser casualitat (prova binomial amb correcció de Holm, amb 20 casos o més). És un senyal per a mirar aquest lloc amb més detall, no un diagnòstic.", "La diferencia es demasiado grande para ser casualidad (prueba binomial con corrección de Holm, con 20 casos o más). Es una señal para mirar este lugar con más detalle, no un diagnóstico.")}</p>')
        o.append("</section>")
        # factores: solo el último año (perfil); con menos de 5 accidentes ese año no se comparan
        rf = ref["f"]; nf = P["nf"]
        o.append(f'<section class="tarjeta" style="min-width:0"><h2>{T("Per què, segons la policia?", "¿Por qué, según la policía?")}</h2>'
                 f'<p class="intro">{T(f"Motius que anota la policia, només en {a1}", f"Motivos que anota la policía, solo en {a1}")} ({nf} {T("accidents", "accidentes") if nf != 1 else T("accident", "accidente")})</p>')
        if nf >= 5:
            filas = [(T(va, es), P["f"][c], nf, rf[c], f"{P['f'][c]} {T('de', 'de')} {nf}") for c, _, va, es in FACT]
            o.append(f'<div class="ley-comp"><span><i style="height:12px;background:var(--ink)"></i>{T("Aquest lloc", "Este lugar") if f["clase"] == "lloc" else T("Aquest carrer", "Esta calle")} ({T("de cada 10", "de cada 10")})</span>'
                     f'<span><i style="height:7px;background:var(--mix)"></i>{T(f"Ciutat en {a1} (de cada 10)", f"Ciudad en {a1} (de cada 10)")}</span></div>' + comp(filas, ""))
            if nf < 10: o.append(f'<p class="nota" style="margin-top:8px">{T("Amb tan pocs accidents, la comparació amb la ciutat diu poca cosa.", "Con tan pocos accidentes, la comparación con la ciudad dice poco.")}</p>')
        else:
            o.append(f'<p>{T(f"En {a1} hi va haver massa pocs accidents ací per a comparar els motius amb la ciutat.", f"En {a1} hubo demasiado pocos accidentes aquí para comparar los motivos con la ciudad.")}</p>')
        o.append(f'<p class="nota" style="margin-top:10px">{T(f"Només comptem {a1}: abans, en un de cada tres comunicats no hi consta cap motiu, i els anys no es poden comparar. Un accident pot tindre diversos motius. El comunicat policial no diu qui en va tindre la culpa.", f"Solo contamos {a1}: antes, en uno de cada tres partes no consta ningún motivo, y los años no se pueden comparar. Un accidente puede tener varios motivos. El parte policial no dice quién tuvo la culpa.")}</p></section>')
        # hora
        lab = de10(P["lab"], n); labc = de10(ref["lab"], 1)
        o.append(f'<section class="tarjeta" style="min-width:0"><h2>{T("A quina hora?", "¿A qué hora?")}</h2><p class="intro">{T("Accidents per franja horària", "Accidentes por franja horaria")}, {a0}-{a1}</p>'
                 + svg_hora(P["fr"], ref["fr"]) +
                 f'<div class="ley-comp" style="margin-top:6px"><span><i style="height:12px;background:var(--ink)"></i>{T("Aquest lloc", "Este lugar") if f["clase"] == "lloc" else T("Aquest carrer", "Esta calle")}</span>'
                 f'<span><i style="height:0;border-top:2px dashed var(--ink2)"></i>{T("L&#39;esperable si seguira l&#39;horari de la resta de la ciutat", "Lo esperable si siguiera el horario del resto de la ciudad")}</span></div>'
                 f'<p class="nota">{T("Ací,", "Aquí,")} {lab[l == "es"]} {T("de cada 10 accidents van ser en dia feiner. En tota la ciutat,", "de cada 10 accidentes fueron en día laborable. En toda la ciudad,")} {labc[l == "es"]} {T("de cada 10", "de cada 10")}.</p></section>')
        # Plan
        ids = D["plan_lug"][f["uid"]] if f["clase"] == "lloc" else D["plan_via"][f["codvia"]]
        o.append(f'<section class="tarjeta ancho" style="min-width:0"><h2>{T("Què hi ha fet o anunciat l&#39;Ajuntament?", "¿Qué ha hecho o anunciado el Ayuntamiento?")}</h2>')
        if ids:
            for i in ids:
                p = D["plan"][i]; e = p["estado"]
                fuente = (f'<a href="{ESC(p["url_estado"])}" rel="noopener">{T("Font", "Fuente")}</a> {T("del", "del")} {fecha_larga(p["fecha_fuente"], l)} '
                          if p["url_estado"] and e != "sin_info" else "")
                o.append(f'<div class="medida {e}"><div><span class="est {e}"><i aria-hidden="true"></i>{EST[e][l == "es"]}</span> '
                         f'<span class="nota">· {fuente}({T("comprovat el", "comprobado el")} {fecha_larga(p["fecha_comprobacion"], l)})</span></div>'
                         + (f'<div class="tit">{ESC(STP.MEDIDAS[i]["tit"][l])}</div>' if i in STP.MEDIDAS else f'<div class="tit" lang="es">{ESC(p["actuacion"])}</div>')
                         + (f'<div class="nota">{ESC(STP.MEDIDAS[i]["nota"][l])}</div>' if i in STP.MEDIDAS and STP.MEDIDAS[i].get("nota") else "")
                         + f'<a href="../../ajuntament/#a-{ESC(i)}">{T("Acció", "Acción")} {ESC(p["accion_plan"])} {T("del Pla Director de Seguretat Viària", "del Plan Director de Seguridad Vial")} →</a></div>')
        else:
            o.append(f'<p>{T("El seguiment del Pla Director que fa l&#39;observatori no té cap actuació situada", "El seguimiento del Plan Director que hace el observatorio no tiene ninguna actuación situada")} {lugar_txt}. '
                     f'<a href="../../ajuntament/">{T("Què està fent l&#39;Ajuntament?", "¿Qué está haciendo el Ayuntamiento?")} →</a></p>')
        # aviso ciudadano (sitio.mailto_aviso): asunto con el nombre del sitio; sin formulario ni datos personales en la web
        o.append(f'<p class="nota" style="margin:12px 0 0">{T(f"Has vist obres o algun canvi {lugar_txt}?", f"¿Has visto obras o algún cambio {lugar_txt}?")} '
                 f'<a href="{sitio.mailto_aviso(l, nom[l])}">{T("Avisa&#39;ns per correu", "Avísanos por correo")}</a>: '
                 f'{T("buscarem la font oficial i, si n&#39;hi ha, ho afegirem al seguiment.", "buscaremos la fuente oficial y, si la hay, lo añadiremos al seguimiento.")}</p>')
        o.append("</section>")
        # uno a uno
        o.append(f'<section class="tarjeta ancho" style="min-width:0"><h2>{T("Els accidents, un a un", "Los accidentes, uno a uno")}</h2>'
                 f'<p class="intro">{T("Els més recents primer", "Los más recientes primero")} · {n}</p><div style="overflow-x:auto" tabindex="0" role="region" aria-label="{T('Els accidents, un a un', 'Los accidentes, uno a uno')}"><table class="tabla"><thead><tr>'
                 f'<th>{T("Quan", "Cuándo")}</th><th>{T("Qui", "Quién")}</th><th>{T("On", "Dónde")}</th><th>{T("Ferits", "Heridos")}</th></tr></thead><tbody>')
        for s in ss:
            o.append(f'<tr><td>{MES[l][int(s["fecha"][5:7]) - 1]} {s["fecha"][:4]}</td><td><span class="v"><i class="pt {s["v"]}"></i>{ESC(vehiculos(s["unidades"], l))}</span></td>'
                     f'<td>{ESC(on(s, f, D, l))}</td><td>{GRAV[s["gravedad"]][l == "es"]}</td></tr>')
        o.append(f'</tbody></table></div><p class="nota" style="margin-top:8px">{T("Sense dia ni hora en aquesta llista; el mapa de la web té el detall del portal de dades obertes. El número és el del portal citat en el comunicat, no un domicili. La policia classifica els ferits, de menys a més, en lleus, de gravetat baixa i greus. Des de 2023 compta com a ferit greu qui passa més de 24 hores en l&#39;hospital: per això la gravetat no es pot comparar entre anys.", "Sin día ni hora en esta lista; el mapa de la web tiene el detalle del portal de datos abiertos. El número es el del portal citado en el parte, no un domicilio. La policía clasifica a los heridos, de menos a más, en leves, de baja gravedad y graves. Desde 2023 se cuenta como herido grave a quien pasa más de 24 horas en el hospital: por eso la gravedad no se puede comparar entre años.")}</p></section>')
        o.append("</div>")
        # cómo lo sabemos
        metodo = (T("Comptem els accidents del portal de dades obertes que, situats amb el carrerer municipal, cauen en aquesta cruïlla o a 30 m (o, en un tram, els que tenen aquest tram com el més pròxim). ",
                    "Contamos los accidentes del portal de datos abiertos que, situados con el callejero municipal, caen en este cruce o a 30 m (o, en un tramo, los que tienen este tramo como el más cercano). ")
                  if f["clase"] == "lloc" else
                  T("Comptem els accidents la direcció escrita dels quals és aquest carrer, en un portal o en una cruïlla (un accident en una cruïlla compta en els dos carrers). ",
                    "Contamos los accidentes cuya dirección escrita es esta calle, en un portal o en un cruce (un accidente en un cruce cuenta en las dos calles). "))
        o.append(f'<details class="saber"><summary>{T("Com ho sabem", "Cómo lo sabemos")}</summary><div><p>{metodo}'
                 f'{T("Només hi ha fitxa dels llocs i carrers amb 5 accidents o més.", "Solo hay ficha de los lugares y calles con 5 accidentes o más.")}</p>'
                 f'<p>{(T("Són llocs amb accidents registrats: sense dades d&#39;ús (quantes bicis i patinets hi passen) no es pot dir que siguen més perillosos.", "Son lugares con accidentes registrados: sin datos de uso (cuántas bicis y patinetes pasan) no se puede decir que sean más peligrosos.") if f["clase"] == "lloc" else T("Són carrers amb accidents registrats: sense dades d&#39;ús (quantes bicis i patinets hi passen) no es pot dir que siguen més perillosos.", "Son calles con accidentes registrados: sin datos de uso (cuántas bicis y patinetes pasan) no se puede decir que sean más peligrosas."))} '
                 f'{T("El tipus d&#39;accident del portal només és fiable des de 2025 i no el fem servir ací.", "El tipo de accidente del portal solo es fiable desde 2025 y no lo usamos aquí.")}</p>'
                 f'<p><a href="../../metode/#{"lugares" if f["clase"] == "lloc" else "carrers"}">{T("Dades i mètode", "Datos y método")} →</a> · <a href="../../dades/#fitxes">{T("Com fem les fitxes", "Cómo hacemos las fichas")} →</a></p></div></details>')
        mains.append(f'<div data-l="{l}" lang="{"ca" if l == "va" else "es"}">' + "".join(o) + "</div>")
    return titulo, desc, url, datos, "\n".join(mains), nom


def geojson(g, tol):
    """Geometría simplificada y con 5 decimales (~1 m), en GeoJSON."""
    import numpy as np, shapely
    return json.loads(shapely.to_geojson(shapely.transform(g.simplify(tol), lambda c: np.round(c, 5))))


MESES = {"va": ["de gener", "de febrer", "de març", "d'abril", "de maig", "de juny", "de juliol", "d'agost", "de setembre", "d'octubre", "de novembre", "de desembre"],
         "es": ["de enero", "de febrero", "de marzo", "de abril", "de mayo", "de junio", "de julio", "de agosto", "de septiembre", "de octubre", "de noviembre", "de diciembre"]}
def fecha_larga(iso, l):
    """«7 de maig de 2026» / «7 de mayo de 2026»."""
    return f"{int(iso[8:10])} {MESES[l][int(iso[5:7]) - 1]} de {iso[:4]}" if iso else "—"


def fecha(iso): return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if iso else "—"


def on(s, f, D, l):
    """Dónde, dentro del lugar o la calle: el cruce («Cruïlla amb …») o el número de portal, con los nombres del callejero
    en la lengua de la versión (los de la dirección escrita del parte vienen en castellano)."""
    ub = s["ubicacion"] or ""
    nv = lambda cv: nom_via(D["vias"][cv], l)
    vias = [cv for cv, _ in D["via_de"][s["id"]] if cv in D["vias"]]
    if " cruce " in ub:
        otras = [cv for cv in vias if not (f["clase"] == "carrer" and cv == f["codvia"])]
        if f["clase"] == "carrer" and otras:
            return ("Cruïlla amb " if l == "va" else "Cruce con ") + N.con_articulo(nv(otras[0]), l)
        if len(vias) >= 2:
            return nv(vias[0]) + (" amb " if l == "va" else " con ") + (" i " if l == "va" else " y ").join(N.minus(nv(cv)) for cv in vias[1:])
        return N.direccion(ub, l)
    m = re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$", ub)
    if m:
        if f["clase"] == "carrer":
            return ("A l'altura del número " if l == "va" else "A la altura del número ") + m.group(2)
        return (nv(vias[0]) if len(vias) == 1 else N.direccion(m.group(1), l)) + ", " + m.group(2)
    if len(vias) == 1 and f["clase"] == "lloc": return nv(vias[0]) + (" (sense número)" if l == "va" else " (sin número)")
    return "Sense número" if l == "va" else "Sin número"


# ---------------------------------------------------------------- montaje
def recurso(src, nombre):
    """Copia web/proto/fichas/<src> a build/datos/<nombre>.<hash8>.<ext> (borra las versiones viejas). Devuelve (ruta, SRI)."""
    b = src.read_bytes(); ext = src.suffix
    dest = f"{nombre}.{hashlib.sha256(b).hexdigest()[:8]}{ext}"
    for viejo in BD.glob(f"{nombre}.*{ext}"):
        if viejo.name != dest and re.fullmatch(rf"{re.escape(nombre)}\.[0-9a-f]{{8}}{re.escape(ext)}", viejo.name): viejo.unlink()
    if not (BD / dest).exists(): (BD / dest).write_bytes(b)
    return f"datos/{dest}", "sha384-" + base64.b64encode(hashlib.sha384(b).digest()).decode()


def escribir(p, texto):
    """Escribe solo si cambia (así una ficha sin cambios conserva su fecha y el deploy no la ve distinta)."""
    b = texto.encode()
    if p.exists() and p.read_bytes() == b: return False
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b); return True


# página: <head>, cabecera, migas y pie comunes de scripts/sitio.py (los mismos que el resto de la web); los Open Graph propios
# de la ficha van en extra. CSS común (build/datos/sitio.<hash8>.css); fichas.js solo dibuja el minimapa y comparte.
R = "../../"
def documento(titulo, desc, url, clase, nom, mains, info, datos, js, js_sri):
    m, ld = sitio.migas([("inici", sitio.NOM["inici"]), ("mapa", sitio.NOM["mapa"]), (clase, sitio.NOM[clase]),
                         (None, (nom["va"], nom["es"]))], R)
    cab = sitio.head(R, (titulo["va"], titulo["es"]), (desc["va"], desc["es"]), url, extra=ld + "\n")
    # og:title sin la marca del final («… · Observatori de la bici i el patinet»)
    cab = cab.replace(f'<meta property="og:title" content="{ESC(titulo["va"])}">', f'<meta property="og:title" content="{ESC(titulo["va"].split(" · ")[0])}">')
    return sitio.pulir(cab + f'<body data-pag="ficha" {sitio.body_attrs(R, (titulo["va"], titulo["es"]), (desc["va"], desc["es"]))}>\n'

            + sitio.cabecera("mapa", R) + f'\n<main class="wrap" id="contingut" tabindex="-1">{m}\n{mains}\n</main>\n' + sitio.pie(R, info) + "\n"
            + '<script type="application/json" id="ficha-datos">'
            + json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"
            + sitio.MAPLIBRE + "\n" + sitio.scripts_fin(R) + f'<script src="{R}{js}" integrity="{js_sri}"></script>\n</body>\n</html>\n')


def main():
    import geopandas as gpd, shapely
    con = sqlite3.connect(DB); D = cargar(con)
    BD.mkdir(parents=True, exist_ok=True)
    js, js_sri = recurso(W / "fichas/fichas.js", "fichas")
    for viejo in BD.glob("fichas.*.css"): viejo.unlink()            # fichas.css ya no se usa: comun.css trae sus clases
    # cobertura por año (el puesto del top 30 la tiene en cuenta) y nombres de lugar que quedarían repetidos sin el sufijo
    _o = (W / "datos/observatori.js").read_text(); _o = json.loads(_o[_o.index("=") + 1:].strip().rstrip(";"))
    D["cob_any"] = {int(a): v for a, v in _o["kpi"]["cob_any"].items()}
    info = {"conjunto": D["meta"]["conjunto_siniestros"], "descarga": D["meta"]["fecha_descarga"], "version": D["meta"]["version_web"]}
    _c = W / "datos/colaboran.json"
    if _c.exists() and json.loads(_c.read_text()): info["colab"] = json.loads(_c.read_text())
    slug_lloc = {f["uid"]: f["slug"] for f in D["fichas"] if f["clase"] == "lloc"}
    slug_carrer = {f["codvia"]: f["slug"] for f in D["fichas"] if f["clase"] == "carrer"}
    # referencias de la ciudad: con quién por tipo de lugar (como la pista) y en todo; factores, franjas y laborables
    todos = list(D["sin"].values())
    con_lugar = [s for s in todos if s["uid"] is not None]
    global AÑO_FACT
    AÑO_FACT = D["años"][-1]
    pc = perfil(todos)

    ref = {"k": {"nudo": collections.Counter(s["k"] for s in con_lugar if D["lug"][s["uid"]]["tipo"] == "nudo"),
                 "tramo": collections.Counter(s["k"] for s in con_lugar if D["lug"][s["uid"]]["tipo"] == "tramo"),
                 "todo": pc["k"]},
           "f": {c: pc["f"][c] / max(pc["nf"], 1) for c, *_ in FACT}, "fr": [x / len(todos) for x in pc["fr"]], "lab": pc["lab"] / len(todos)}

    ej = gpd.read_file(ROOT / "data/raw/siniestros/ejes.geojson")
    ej = ej[ej.geometry.notna()]
    ejes = list(zip(ej.codvia.fillna(-1).astype(int), ej.geometry))
    arbol = shapely.STRtree([g for _, g in ejes])
    m = D["meta"]
    nuevas = 0; vistas = {"lloc": set(), "carrer": set()}; indice = []; paginas = []
    for f in D["fichas"]:
        titulo, desc, url, datos, mains, nom = pagina(D, f, slug_lloc, slug_carrer, ref, (ejes, arbol))
        paginas.append((f, (titulo, desc, url, f["clase"], nom, mains, info, datos, js, js_sri)))
        vistas[f["clase"]].add(f["slug"])
        indice.append([f["clase"], f["slug"], nom["va"], nom["es"], f["n"]])
    # índice para el buscador, antes de escribir las páginas: cada ficha carga el índice vigente (sitio.scripts_fin)
    idx = "window.FICHAS=" + json.dumps(indice, ensure_ascii=False, separators=(",", ":")) + ";\n"
    escribir(W / "datos/fichas_indice.js", idx)
    ruta_idx, sri_idx = recurso(W / "datos/fichas_indice.js", "fichas_indice")
    escribir(W / "datos/fichas_indice.sri", f"{ruta_idx} {sri_idx}\n")   # para enganchar el buscador (ruta y SRI)
    sitio._ASSETS.clear()
    for f, args in paginas:
        nuevas += escribir(BUILD / f["clase"] / f["slug"] / "index.html", documento(*args))
    # fichas que ya no están en la tabla: fuera (solo carpetas: build/lloc/index.html es el índice de la web)
    borradas = 0
    for clase in ("lloc", "carrer"):
        for d in (BUILD / clase).glob("*") if (BUILD / clase).exists() else []:
            if d.is_dir() and d.name not in vistas[clase]: shutil.rmtree(d); borradas += 1
    tam = sum(p.stat().st_size for c in ("lloc", "carrer") for p in (BUILD / c).rglob("index.html"))
    print(f"fichas: {len(vistas['lloc'])} de lugar y {len(vistas['carrer'])} de calle en web/proto/build/{{lloc,carrer}}/ "
          f"({tam / 1e6:.1f} MB); {nuevas} escritas (las demás no cambian), {borradas} borradas; índice {ruta_idx} ({len(idx) / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- comprobaciones (las llama scripts/comprobar.py)
def comprobaciones():
    """[(nivel, texto)]: base íntegra y exportaciones idénticas a los CSV; una página por ficha y ninguna de más; cifra de
    cada página = SQLite; enlaces internos que existen; SRI de los recursos; slugs únicos y estables (los de HEAD siguen)."""
    import subprocess, construir_sqlite as CS
    out = []
    if not DB.exists():
        return [("ERROR", f"falta {DB.relative_to(ROOT)}: make sqlite")]
    con = sqlite3.connect(DB)
    ic = con.execute("PRAGMA integrity_check").fetchone()[0]; fk = con.execute("PRAGMA foreign_key_check").fetchall()
    out.append(("OK" if ic == "ok" and not fk else "ERROR", f"sqlite: integridad {ic}, claves foráneas rotas {len(fk)}"))
    ex = CS.comprobar(DB)
    # entradas de la base (análisis y registros a mano): distintas = base desfasada (AVISO, make sqlite)
    malos = [f"{n} ({d})" for n, ok, d in ex if not ok and n in CS.ENTRADAS]
    out.append(("AVISO" if malos else "OK", f"sqlite: entradas distintas de su exportación desde la base (¿base desfasada? make sqlite): {malos}" if malos
                else f"sqlite: las {len(CS.ENTRADAS)} entradas exportadas desde la base son idénticas a los ficheros"))
    # lo que la base exporta (el Plan: volcado en git y CSV): distinto = editado a mano o base sin volcar (ERROR)
    malos = [f"{n} ({d})" for n, ok, d in ex if not ok and n in CS.DE_LA_BASE]
    out.append(("ERROR" if malos else "OK", f"sqlite: el Plan de la base no coincide con {malos}: no se editan a mano (aplicar_propuestas_plan.py); "
                "si la base es la buena, construir_sqlite.py --volcar; si lo es el CSV, construir_sqlite.py --plan-desde-csv" if malos
                else "sqlite: el Plan de la base es el de su volcado en git (observatorio_plan.sql) y el de su exportación (plan_seguimiento.csv)"))
    # el buscador de la web (portada y mapa; sitio.scripts_fin) carga el índice de las fichas con su SRI
    src, sri_i = (W / "datos/fichas_indice.sri").read_text().split()
    _ok_i = (BUILD / src).exists() and "sha384-" + base64.b64encode(hashlib.sha384((BUILD / src).read_bytes()).digest()).decode() == sri_i
    _pags = [BUILD / "index.html", BUILD / "mapa/index.html"]
    _faltan = [str(p.relative_to(BUILD)) for p in _pags if not p.exists()]
    _sin = [str(p.relative_to(BUILD)) for p in _pags if p.exists() and not re.search(rf'src="(?:\.\./)*{re.escape(src)}" integrity="{re.escape(sri_i)}"', p.read_text())]
    if not _ok_i or _sin:
        out.append(("ERROR", f"buscador → fichas: índice {src} {'bien' if _ok_i else 'MAL (SRI o falta)'}; páginas que no lo cargan: {_sin} (make web)"))
    elif _faltan:
        out.append(("AVISO", f"buscador → fichas: índice {src} bien; aún no existen {_faltan} (make web)"))
    else:
        out.append(("OK", f"buscador → fichas: index.html y mapa/index.html cargan {src} con SRI"))
    fichas = con.execute("""SELECT f.clase, f.slug, f.clave, f.n, COALESCE(l.n, c.n) FROM ficha f LEFT JOIN lugar l USING (uid)
                            LEFT JOIN v_calle_bv c ON c.codvia = f.codvia""").fetchall()
    mal_n = [s for cl, s, _, n, n2 in fichas if n != n2]
    out.append(("OK" if not mal_n else "ERROR", f"fichas: {len(fichas)} en la base, recuentos {'iguales a lugar/v_calle_bv' if not mal_n else f'DISTINTOS en {mal_n[:5]}'}"))
    # páginas
    esperadas = {(cl, s): n for cl, s, _, n, _ in fichas}
    hay = {(cl, d.name) for cl in ("lloc", "carrer") if (BUILD / cl).exists() for d in (BUILD / cl).iterdir() if d.is_dir()}
    faltan, sobran = set(esperadas) - hay, hay - set(esperadas)
    rotos, rotos_pag, cifra, sri = set(), set(), [], []
    recursos = {}
    for (cl, s), n in sorted(esperadas.items()):
        p = BUILD / cl / s / "index.html"
        if not p.exists(): continue
        t = p.read_text()
        m = re.findall(r'<span class="cifra">([\d.]+)</span>', t)
        if len(m) != 2 or any(int(x.replace(".", "")) != n for x in m): cifra.append(s)
        for h in re.findall(r'href="(\.\./\.\./[^"#]*)', t):
            dest = (p.parent / h).resolve()
            if not (dest.is_file() or (dest / "index.html").is_file()):
                (rotos if re.match(r"\.\./\.\./((lloc|carrer)/[a-z0-9-]+/|datos/)", h) else rotos_pag).add(h)
        for ruta, integ in re.findall(r'(?:href|src)="\.\./\.\./(datos/[^"]+)" integrity="([^"]+)"', t):
            if ruta not in recursos:
                f = BUILD / ruta
                recursos[ruta] = f.exists() and "sha384-" + base64.b64encode(hashlib.sha384(f.read_bytes()).digest()).decode() == integ
            if not recursos[ruta]: sri.append(s)
    ok = not (faltan or sobran or rotos or cifra or sri)
    out.append(("OK" if ok else "ERROR", f"fichas: {len(hay)} páginas en build/{{lloc,carrer}}; faltan {sorted(faltan)[:3]}, sobran {sorted(sobran)[:3]}, "
                f"enlaces internos rotos {sorted(rotos)[:3]}, cifra distinta de la base {cifra[:3]}, SRI mal {sorted(set(sri))[:3]}"))
    if rotos_pag:
        out.append(("AVISO", f"fichas: enlazan páginas de la web que aún no existen en build/ (make web): {sorted(rotos_pag)[:6]}"))
    # slugs: únicos por clase y por clave, los de la base = los congelados, y los de HEAD siguen igual
    f = pd_read(CS.SLUGS)
    dup = f.duplicated(["clase", "slug"]).sum() + f.clave.duplicated().sum()
    cong = dict(zip(f.clave, zip(f.clase, f.slug)))
    distintos = [s for cl, s, cv, _, _ in fichas if cong.get(cv) != (cl, s)]
    try:
        head = subprocess.run(["git", "show", f"HEAD:{CS.SLUGS.relative_to(ROOT)}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        import csv, io
        perdidos = [r["slug"] for r in csv.DictReader(io.StringIO(head)) if cong.get(r["clave"]) != (r["clase"], r["slug"])]
        txt_head = f"; de los congelados en HEAD cambian o desaparecen {len(perdidos)} {perdidos[:3]}"
    except subprocess.CalledProcessError:
        perdidos, txt_head = [], " (fichas_slugs.csv aún no está en git: hay que hacer commit para que los slugs queden fijos en el deploy)"
    out.append(("ERROR" if dup or distintos or perdidos else "AVISO" if "aún no" in txt_head else "OK",
                f"slugs: {len(f)} congelados, repetidos {dup}, base distinta del fichero {distintos[:3]}{txt_head}"))
    return out


def pd_read(p):
    import pandas as pd
    return pd.read_csv(p, dtype=str)
