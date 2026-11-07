"""Imágenes Open Graph (1200×630 PNG) para compartir cada página en redes.

Lee los datos ya exportados por exportar_web.py (web/proto/datos/*.js: un
objeto JSON asignado a window.X) y escribe web/proto/build/og/{pagina}.png
(valenciano, la lengua por defecto de la web) y {pagina}_es.png (castellano).

Cada tarjeta lleva la marca, una cifra clave calculada desde los datos (nunca
escrita a mano), el mapa de los siniestros situados de fondo y la URL. Todo lo
importante va centrado: WhatsApp y otras apps recortan la miniatura a un
cuadrado central.

Cautela en los textos (afirmaciones retiradas: docs/revision_metodologica/README.md): «llocs amb més sinistres», nunca «punts
negres» ni «perillós»; el −50 % es el indicador de la acción 3.2.2, no un
compromiso de la ciudad.

Uso: .venv/bin/python -I scripts/tarjetas_og.py  (lo llama `make web`).
"""
import io
import json
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from PIL import Image  # noqa: E402  (dependencia de matplotlib)
from shapely.geometry import shape  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "web/proto/datos"
SALIDA = RAIZ / "web/proto/build/og"
DOMINIO = "observatoribicivlc.org"
W, H = 1200, 630

# Paleta clara de la web (variables CSS de observatori.plantilla.html)
C = dict(bg="#EEF1F2", surface="#FFFFFF", line="#D3D9DC", ink="#15202B", ink2="#55626E",
         bici="#2a78d6", pat="#C94B17", mix="#8A949D", sel="#b87a00",
         street="#C9D0D4", lane="#9DB8AE", mapbg="#F7F8F8")


# Tipografía de la web (Google Fonts en las plantillas: Barlow Semi Condensed
# 500-800 y Public Sans 400-600), con los TTF estáticos oficiales y su OFL en
# web/proto/fuentes/. Si falta alguno, se para: nada de caer a otra letra.
FUENTES = RAIZ / "web/proto/fuentes"
TTF = {
    "marca": "barlow-semi-condensed/BarlowSemiCondensed-ExtraBold.ttf",   # .marca: 800
    "cifra": "barlow-semi-condensed/BarlowSemiCondensed-ExtraBold.ttf",
    "titulo": "barlow-semi-condensed/BarlowSemiCondensed-Bold.ttf",       # .eyebrow, url: 700
    "texto": "public-sans/PublicSans-Regular.ttf",                         # body: 400
}


def fuentes():
    # un glifo que la letra no tiene sería otra fuente en silencio: error
    warnings.filterwarnings("error", message=r"Glyph \d+ .* missing from font")
    faltan = [r for r in sorted(set(TTF.values())) if not (FUENTES / r).is_file()]
    if faltan:
        raise SystemExit("tarjetas_og: faltan fuentes en web/proto/fuentes/: " + ", ".join(faltan)
                         + " (TTF estáticos de github.com/google/fonts, ofl/barlowsemicondensed,"
                         " y github.com/uswds/public-sans, fonts/ttf)")
    for r in set(TTF.values()):
        font_manager.fontManager.addfont(str(FUENTES / r))
    return {k: font_manager.FontProperties(fname=str(FUENTES / r)) for k, r in TTF.items()}


def cargar(nombre):
    t = (DATOS / nombre).read_text(encoding="utf-8")
    return json.loads(t[t.index("=") + 1:].strip().rstrip(";"))


def miles(n):
    return f"{int(round(n)):,}".replace(",", ".")


def pct(x):
    return f"{round(100 * x)} %"


def fecha(iso):
    a, m, d = iso.split("-")
    return f"{int(d)}/{int(m)}/{a}"


# ── Textos (va por defecto, es) ──────────────────────────────────────────────
T = {
    "va": dict(
        marca="Observatori de la bici i el patinet de València",
        obs_ey="Sinistres amb bici o patinet",
        obs_lbl="sinistres amb bici o patinet en {ult}",
        obs_sub="Al mapa, els llocs amb més sinistres ({a0}-{ult})",
        inf_ey="Informe · Pla Director de Seguretat Viària",
        inf_lbl="indicador de l'acció 3.2.2: −{red} % de sinistres amb bici o patinet en {meta} (base {base}, triada per l'observatori)",
        inf_sub_pend="Sense dades de {pend} encara no es pot avaluar",
        inf_sub="Darrer any avaluat: {ult}",
        met_ey="Mètode · Com ho hem fet",
        met_lbl="sinistres situats en el mapa: el {cob} dels {nbv} amb bici o patinet ({a0}-{ult})",
        met_sub="Dades obertes de l'Ajuntament de València, amb el carrerer municipal",
        cam_ey="Canvis · Què ha canviat",
        cam_lbl="canvis publicats en dades, mètode i web",
        cam_sub="Darrer canvi: {f}",
        pla_ey="El Pla, al dia · Què s'hi fa",
        pla_lbl="actuacions del Pla per a la bici i el patinet, amb estat, data i font",
        pla_sub="{h} fetes · {m} en marxa · {a} anunciades · {s} sense informació pública",
    ),
    "es": dict(
        marca="Observatorio de la bici y el patinete de València",
        obs_ey="Siniestros con bici o patinete",
        obs_lbl="siniestros con bici o patinete en {ult}",
        obs_sub="En el mapa, los lugares con más siniestros ({a0}-{ult})",
        inf_ey="Informe · Plan Director de Seguridad Vial",
        inf_lbl="indicador de la acción 3.2.2: −{red} % de siniestros con bici o patinete en {meta} (base {base}, elegida por el observatorio)",
        inf_sub_pend="Sin datos de {pend} aún no se puede evaluar",
        inf_sub="Último año evaluado: {ult}",
        met_ey="Método · Cómo lo hemos hecho",
        met_lbl="siniestros situados en el mapa: el {cob} de los {nbv} con bici o patinete ({a0}-{ult})",
        met_sub="Datos abiertos del Ajuntament de València, con el callejero municipal",
        cam_ey="Cambios · Qué ha cambiado",
        cam_lbl="cambios publicados en datos, método y web",
        cam_sub="Último cambio: {f}",
        pla_ey="El Plan, al día · Qué se hace",
        pla_lbl="actuaciones del Plan para la bici y el patinete, con estado, fecha y fuente",
        pla_sub="{h} hechas · {m} en marcha · {a} anunciadas · {s} sin información pública",
    ),
}


# ── Mapa de fondo (se dibuja una vez y se reutiliza) ────────────────────────
def capas(obs):
    calles = gpd.GeoDataFrame.from_features(obs["calles"]["features"], crs=4326).to_crs(25830)
    ciclo = gpd.GeoDataFrame.from_features(obs["ciclo"]["features"], crs=4326).to_crs(25830)
    p = obs["pts"]
    pts = gpd.GeoDataFrame({"t": [r[3] for r in p]},
                           geometry=gpd.points_from_xy([r[0] for r in p], [r[1] for r in p]),
                           crs=4326).to_crs(25830)
    lug = gpd.GeoDataFrame(geometry=[shape(n["geo"]) for n in obs["negros"] if n.get("rank")], crs=4326).to_crs(25830)
    return calles, ciclo, pts, lug


def extension(pts):
    """Encuadre 1200:630 con el núcleo de los siniestros entero, centrado en la
    zona libre bajo la banda de la marca (64 px): asoma alrededor del panel."""
    x, y = pts.geometry.x, pts.geometry.y
    x0, x1 = x.quantile(0.03), x.quantile(0.97)
    y0, y1 = y.quantile(0.03), y.quantile(0.97)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mpp = min((x1 - x0) / W, (y1 - y0) / (H - 64)) * 1.05   # metros por píxel
    yc = (H - 64) / 2                                         # centro de la zona libre, en px
    return cx - W / 2 * mpp, cx + W / 2 * mpp, cy - yc * mpp, cy + (H - yc) * mpp


def dibujar_mapa(ax, capas_, ext):
    calles, ciclo, pts, lug = capas_
    ax.set_facecolor(C["mapbg"])
    calles.plot(ax=ax, color=C["street"], linewidth=0.6, zorder=1)
    ciclo.plot(ax=ax, color=C["lane"], linewidth=1.2, zorder=2)
    color = pts["t"].map({"b": C["bici"], "p": C["pat"]}).fillna(C["mix"])
    pts.plot(ax=ax, color=color, markersize=10, alpha=0.7, linewidth=0, zorder=3)
    lug.boundary.plot(ax=ax, color=C["ink"], linewidth=2.2, zorder=4)
    ax.set_xlim(ext[0], ext[1])
    ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal")
    ax.set_axis_off()


# ── Pictograma de la bici (<span class="senal"> de la web) ─────────────────
def senal(fig, cx, cy, r, fondo, linea):
    """Círculo con la bici del SVG de la web (viewBox 24×24), en px. En la web
    es tinta con trazo claro; sobre la banda oscura de la marca, al revés."""
    ax = fig.add_axes([0, 0, 1, 1], facecolor="none", zorder=20)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_axis_off()
    ax.add_patch(Circle((cx, cy), r, color=fondo))
    esc = (r * 2 * 18 / 28) / 24       # el svg ocupa 18 de 28 px

    def p(x, y):
        return (cx + (x - 12) * esc, cy - (y - 12) * esc)
    trazo = dict(fill=False, edgecolor=linea, linewidth=2 * esc, capstyle="round", joinstyle="round")
    for x in (6, 18):
        ax.add_patch(Circle(p(x, 16), 3.5 * esc, **trazo))
    M, L = MPath.MOVETO, MPath.LINETO
    v = [(6, 16), (10, 9), (15, 9), (18, 16), (10, 9), (9, 6.5), (7.5, 6.5), (13, 9), (15, 9)]
    c = [M, L, L, L, M, L, L, M, L]
    ax.add_patch(PathPatch(MPath([p(*q) for q in v], c), **trazo))


# ── Tarjeta ──────────────────────────────────────────────────────────────────
def ajustar(fig, txt, ancho):
    """Reduce el cuerpo de un texto hasta que quepa en `ancho` px."""
    fig.canvas.draw()
    while txt.get_window_extent().width > ancho and txt.get_fontsize() > 10:
        txt.set_fontsize(txt.get_fontsize() * 0.95)
        fig.canvas.draw()


def tarjeta(destino, capas_, ext, F, lang, eyebrow, cifra, etiqueta, sub):
    t = T[lang]
    fig = plt.figure(figsize=(W / 72, H / 72), dpi=72)   # 1 pt = 1 px
    ax = fig.add_axes([0, 0, 1, 1])
    dibujar_mapa(ax, capas_, ext)

    # capa de texto en píxeles
    tx = fig.add_axes([0, 0, 1, 1], facecolor="none", zorder=10)
    tx.set_xlim(0, W)
    tx.set_ylim(0, H)
    tx.set_axis_off()

    # marca arriba, a todo lo ancho, con el pictograma de la web
    tx.add_patch(FancyBboxPatch((0, H - 64), W, 64, boxstyle="square,pad=0",
                                facecolor=C["ink"], edgecolor="none"))
    tm = tx.text(W / 2 + 24, H - 32, t["marca"].upper(), ha="center", va="center", color=C["bg"],
                 fontproperties=F["marca"], fontsize=31)
    ajustar(fig, tm, W - 120)
    senal(fig, tm.get_window_extent().x0 - 30, H - 32, 21, fondo=C["bg"], linea=C["ink"])

    # panel central: cabe en el cuadrado central que recortan las miniaturas
    pw, ph = 700, 380
    x0, y0 = (W - pw) / 2, 112
    cx, util = W / 2, pw - 50
    tx.add_patch(FancyBboxPatch((x0, y0), pw, ph, boxstyle="round,pad=0,rounding_size=12",
                                facecolor=C["surface"], edgecolor=C["line"], linewidth=1.5, alpha=0.84))
    e = tx.text(cx, y0 + ph - 38, eyebrow.upper(), ha="center", va="center", color=C["ink2"],
                fontproperties=F["titulo"], fontsize=25)
    ajustar(fig, e, util)
    yn = y0 + ph - 140
    if isinstance(cifra, tuple):
        # «base → meta»: Barlow no trae la flecha (U+2192); se dibuja aparte
        hueco, tam = 150, 150
        while True:
            a = tx.text(0, yn, cifra[0], ha="left", va="center", color=C["ink"],
                        fontproperties=F["cifra"], fontsize=tam)
            b = tx.text(0, yn, cifra[1], ha="left", va="center", color=C["ink"],
                        fontproperties=F["cifra"], fontsize=tam)
            fig.canvas.draw()
            wa, wb = a.get_window_extent().width, b.get_window_extent().width
            if wa + wb + hueco <= util or tam < 20:
                break
            a.remove(); b.remove()
            tam *= 0.95; hueco *= 0.95
        xa = cx - (wa + wb + hueco) / 2
        a.set_x(xa)
        b.set_x(xa + wa + hueco)
        tx.annotate("", xy=(xa + wa + hueco * 0.8, yn), xytext=(xa + wa + hueco * 0.2, yn),
                    arrowprops=dict(arrowstyle="-|>,head_length=1.1,head_width=0.6",
                                    color=C["ink"], linewidth=tam / 12, shrinkA=0, shrinkB=0))
    else:
        n = tx.text(cx, yn, cifra, ha="center", va="center", color=C["ink"],
                    fontproperties=F["cifra"], fontsize=150)
        ajustar(fig, n, util)
    lb = tx.text(cx, y0 + 112, etiqueta, ha="center", va="center", color=C["ink"],
                 fontproperties=F["texto"], fontsize=27, linespacing=1.15)
    ajustar(fig, lb, util)
    sb = tx.text(cx, y0 + 38, sub, ha="center", va="center", color=C["ink2"],
                 fontproperties=F["texto"], fontsize=21)
    ajustar(fig, sb, util)

    # URL abajo, sobre el mapa
    tx.text(cx, 42, DOMINIO, ha="center", va="center", color=C["ink"], fontproperties=F["titulo"],
            fontsize=30,
            bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.6", facecolor=C["surface"],
                      edgecolor=C["line"], alpha=0.95))
    # PNG con paleta de 256 colores: ~4 veces menos peso (WhatsApp descarta
    # las imágenes de más de ~300 kB) sin pérdida visible en un mapa plano.
    buf = io.BytesIO()
    fig.savefig(buf, dpi=72, facecolor=C["mapbg"], format="png")
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                                                  dither=Image.Dither.NONE)
    img.save(destino, optimize=True)


def partir(texto, max_chars):
    """Corta la etiqueta en dos líneas equilibradas si es larga."""
    if len(texto) <= max_chars:
        return texto
    palabras, mejor = texto.split(), None
    for i in range(1, len(palabras)):
        a, b = " ".join(palabras[:i]), " ".join(palabras[i:])
        d = max(len(a), len(b))
        if mejor is None or d < mejor[0]:
            mejor = (d, a + "\n" + b)
    return mejor[1]


def main():
    obs, rel, met, cam = cargar("observatori.js"), cargar("relato.js"), cargar("metode.js"), cargar("cambios.js")
    pla = cargar("pla.js")
    pe = pla["por_estado"]
    anys = rel["anys"]
    a0, ult = anys[0], anys[-1]
    tot_ult = rel["tot"][-1]
    meta = obs["kpi"]["meta"]
    esc = meta["esc"][0]
    red = round(100 * (1 - esc["meta"] / esc["base"]))
    ult_cambio = max(c["f"] for c in cam)

    F = fuentes()
    capas_ = capas(obs)
    ext = extension(capas_[2])
    SALIDA.mkdir(parents=True, exist_ok=True)
    for lang in ("va", "es"):
        t = T[lang]
        suf = "" if lang == "va" else "_es"
        sub_inf = (t["inf_sub_pend"].format(pend=meta["pendiente"]) if esc["concl"] == "pendiente"
                   else t["inf_sub"].format(ult=meta["ult"]))
        fichas = {
            "observatori": (t["obs_ey"], miles(tot_ult), t["obs_lbl"].format(ult=ult),
                            t["obs_sub"].format(a0=a0, ult=ult)),
            "informe": (t["inf_ey"], (miles(esc["base"]), miles(esc["meta"])),
                        t["inf_lbl"].format(red=red, meta=meta["año_meta"], base=esc["etq"]), sub_inf),
            "metode": (t["met_ey"], miles(met["n_geo"]),
                       t["met_lbl"].format(cob=pct(met["cob_bv_tot"]), nbv=miles(met["n_bv"]), a0=a0, ult=ult),
                       t["met_sub"]),
            "cambios": (t["cam_ey"], miles(len(cam)), t["cam_lbl"], t["cam_sub"].format(f=fecha(ult_cambio))),
            "pla": (t["pla_ey"], miles(pla["n"]), t["pla_lbl"],
                    t["pla_sub"].format(h=pe["hecha"], m=pe["en_marcha"], a=pe["anunciada"], s=pe["sin_info"])),
        }
        for pag, (ey, cifra, lbl, sub) in fichas.items():
            tarjeta(SALIDA / f"{pag}{suf}.png", capas_, ext, F, lang, ey, cifra, partir(lbl, 44), sub)
    print(f"tarjetas_og: {len(fichas) * 2} imágenes en {SALIDA.relative_to(RAIZ)} "
          "(Barlow Semi Condensed y Public Sans)")


if __name__ == "__main__":
    main()
