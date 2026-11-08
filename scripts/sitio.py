"""Piezas comunes de la web pública (cabecera, menú, migas de pan, pie, <head>, recursos con SRI y fuentes woff2).

Las usan scripts/construir_sitio.py (páginas) y scripts/fichas.py (fichas de lugar y de calle), para que la cabecera, el
menú y el pie sean idénticos en todas las páginas. Una URL con las dos lenguas: todo texto va dos veces, con
data-l="va" / data-l="es", y lo muestra <html lang> (comun.css), que fija un script en <head> antes del primer pintado.

Rutas (decididas el 06/11/2026, en valenciano porque el valenciano es la lengua por defecto de la web y de los slugs de
las fichas; ver las notas internas de trabajo, «Web pública»):
  /                inicio                  /mapa/          mapa (herramienta: filtros, vistas, CSV, teclado)
  /ajuntament/     ¿Qué está haciendo el Ayuntamiento?     /informe/       ediciones del informe anual
  /informe/2025/   Informe 2025 (edición congelada, punto 95)
  /dades/          Datos y método (incluye el registro de cambios en #canvis)
  /lloc/ y /carrer/   índices de las fichas;  /lloc/<slug>/ y /carrer/<slug>/  fichas
Las antiguas (observatori.html, informe.html, pla.html, metode.html, cambios.html) redirigen con 301 (deploy/nginx)."""
import base64, hashlib, html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "web/proto"; BUILD = W / "build"; BD = BUILD / "datos"; FU = BUILD / "fuentes"
SITIO = ROOT / "web/sitio"
DOMINIO = "https://observatoribicivlc.org"
ESC = lambda s: html.escape(str(s), quote=True)
MAPLIBRE = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.js" '
            'integrity="sha384-SYKAG6cglRMN0RVvhNeBY0r3FYKNOJtznwA0v7B5Vp9tr31xAHsZC0DqkQ/pZDmj" crossorigin="anonymous"></script>')
ICONO = ("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Ccircle%20cx='12'%20cy='12'"
         "%20r='11.5'%20fill='%2315202B'%20stroke='%2355626E'/%3E%3Cg%20fill='none'%20stroke='%23EEF1F2'%20stroke-width='2.2'"
         "%20stroke-linecap='round'%20stroke-linejoin='round'%3E%3Ccircle%20cx='6.5'%20cy='15'%20r='3.3'/%3E%3Ccircle%20cx='17.5'"
         "%20cy='15'%20r='3.3'/%3E%3Cpath%20d='M6.5%2015l3.8-6.5h4.7l2.5%206.5M10.3%208.5%209.3%206.2'/%3E%3C/g%3E%3C/svg%3E")

# ruta de cada página (relativa a la raíz) y su nombre en el menú y en las migas
RUTA = {"inici": "", "mapa": "mapa/", "ajuntament": "ajuntament/", "informes": "informe/", "informe": "informe/2025/",
        "dades": "dades/", "lloc": "lloc/", "carrer": "carrer/", "resso": "resso/"}
NOM = {"inici": ("Inici", "Inicio"), "mapa": ("Mapa d'accidents", "Mapa de accidentes"),
       "ajuntament": ("Què està fent l'Ajuntament?", "¿Qué está haciendo el Ayuntamiento?"),
       "informes": ("Informes", "Informes"), "informe": ("Informe 2025", "Informe 2025"),
       "dades": ("Dades i mètode", "Datos y método"), "lloc": ("Llocs", "Lugares"), "carrer": ("Carrers", "Calles"),
       "resso": ("Ressò", "Repercusión")}
MENU = ["inici", "mapa", "ajuntament", "informe", "dades"]
TITULO = ("Accidents de bici i patinet a València", "Accidentes de bici y patinete en València")
APOYO = ("Dades obertes per a veure què passa al teu carrer, on actua l'Ajuntament i què hi canvia.",
         "Datos abiertos para ver qué pasa en tu calle, dónde actúa el Ayuntamiento y qué cambia allí.")
# titular de la portada (rediseño del 07/11/2026, opción A del boceto los bocetos de diseño (internos)/, aprobada por el usuario)
FRASE = ("Seguim el Pla de Seguretat Viària de València mesura a mesura i mostrem on es registren els accidents amb bici i patinet.",
         "Seguimos el Plan de Seguridad Vial de València medida a medida y mostramos dónde se registran los accidentes con bici y patinete.")
# fecha en que la web se publicó (servidor propio, 07/11/2026): la usan los estados vacíos de «Ressò / Repercusión»
PUBLICADA = "2026-11-07"
MARCA = ("Observatori de la bici i el patinet de València", "Observatorio de la bici y el patinete de València")
CORREU = "hola@observatoribicivlc.org"
# repositorio público del código (MIT) y de la documentación y los datos derivados (CC BY 4.0); lo enlazan el pie, /dades/,
# /metode/ y /sobre/ (pendiente 111). Se exporta con scripts/exportar_publico.sh.
REPO = "https://github.com/rburgosm/observatori-bici-vlc"
# canal de Telegram de novedades (solo difusión: novedades del Plan, de los datos y de la web, y avisos incorporados, en cuanto las hay
# incorporados). Vacío: la web no muestra nada. Con una URL (tiene que empezar por https://t.me/, lo comprueba
# scripts/comprobar_sitio.py) salen el bloque del pie y la invitación de la portada y de /ajuntament/ (pendiente 112).
TELEGRAM_CANAL = "https://t.me/observatoribicivlc"   # canal creado el 07/11/2026
# avisos ciudadanos sobre obras o medidas del Plan (pendiente 110): solo un mailto con asunto y plantilla; sin formulario,
# sin servidor y sin servicios de terceros. El registro público está en data/processed/avisos_ciudadanos.csv (sin nombres
# ni correos de quien avisa) y el procedimiento, en las solicitudes de información (borradores internos)
AVISOS_CSV = ROOT / "data/processed/avisos_ciudadanos.csv"
AVISOS_CAMPOS = ["fecha", "medida_plan", "lugar", "resumen_va", "resumen_es", "resultado", "fuente_url"]
AVISOS_RESULTADO = {"incorporado": ("Incorporat al seguiment", "Incorporado al seguimiento"),
                    "en_revision": ("En revisió", "En revisión"),
                    "sin_fuente": ("Sense font oficial, de moment", "Sin fuente oficial, por ahora")}


def telegram_invitacion(id_, R):
    """Invitación visible al canal de Telegram (portada y /ajuntament/). Vacía si TELEGRAM_CANAL no está puesto."""
    if not TELEGRAM_CANAL: return ""
    u = ESC(TELEGRAM_CANAL)
    return (f'<aside class="tarjeta telegram" aria-labelledby="{id_}"><h2 class="h-tarjeta" id="{id_}">'
            f'{T("Segueix les novetats en Telegram", "Sigue las novedades en Telegram")}</h2>'
            f'<p>{T("En el nostre canal de Telegram publiquem les novetats tan prompte com n&#39;hi ha: cada canvi d&#39;estat d&#39;una mesura del Pla, les dades noves, les millores de la web i els avisos de la ciutadania que hem incorporat al seguiment. És un canal només d&#39;anuncis: no s&#39;hi poden enviar missatges.", "En nuestro canal de Telegram publicamos las novedades en cuanto las hay: cada cambio de estado de una medida del Plan, los datos nuevos, las mejoras de la web y los avisos de la ciudadanía que hemos incorporado al seguimiento. Es un canal solo de anuncios: no se pueden enviar mensajes.")}</p>'
            f'<p class="tg-acc"><a class="btn" href="{u}" rel="noopener">{T("Uneix-te al canal de Telegram", "Únete al canal de Telegram")}</a></p>'
            f'<p class="nota">{T("Telegram és un servei extern, amb la seua pròpia política de privacitat.", "Telegram es un servicio externo, con su propia política de privacidad.")} '
            f'<a href="{R}sobre/#privacitat">{T("Com tractem les dades", "Cómo tratamos los datos")}</a>.</p></aside>')


def mailto_aviso(l, lugar=None):
    """Enlace mailto: para avisar de una obra o medida del Plan, con asunto y plantilla en la lengua l («va» o «es»).
    Con lugar, el asunto lleva su nombre y el «On:/Dónde:» va relleno. Escapado para un atributo HTML."""
    from urllib.parse import quote
    if l == "va":
        asunto = f"Avís sobre el Pla: {lugar}" if lugar else "Avís sobre una obra o una mesura del Pla"
        cuerpo = ["Què has vist (una obra, un carril bici nou, un pas canviat, una mesura anunciada que no arriba…):", "",
                  f"On: {lugar or ''}", "", "Quan:", "", "Enllaç o foto, si en tens:", ""]
    else:
        asunto = f"Aviso sobre el Plan: {lugar}" if lugar else "Aviso sobre una obra o una medida del Plan"
        cuerpo = ["Qué has visto (una obra, un carril bici nuevo, un paso cambiado, una medida anunciada que no llega…):", "",
                  f"Dónde: {lugar or ''}", "", "Cuándo:", "", "Enlace o foto, si tienes:", ""]
    return ESC(f"mailto:{CORREU}?subject={quote(asunto, safe='')}&body={quote(chr(13) + chr(10)).join(quote(x, safe='') for x in cuerpo)}")


SENAL = ('<svg viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="var(--bg)" stroke-width="2.2" stroke-linecap="round">'
         '<circle cx="6.5" cy="15" r="3.6"/><circle cx="17.5" cy="15" r="3.6"/><path d="M6.5 15 10 8h5l2.5 7M10 8 12.5 15"/></g></svg>')


def T(va, es, tag="span", attrs=""):
    """Texto en las dos lenguas: <span data-l="va">…</span><span data-l="es" lang="es">…</span>."""
    return f'<{tag} data-l="va"{attrs}>{va}</{tag}><{tag} data-l="es" lang="es"{attrs}>{es}</{tag}>'


def num(n, d=0):
    s = f"{n:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- recursos con el contenido en el nombre y SRI
def sri(b):
    return "sha384-" + base64.b64encode(hashlib.sha384(b).digest()).decode()


def escribir(p, texto):
    """Escribe solo si cambia (la fecha del fichero no cambia si no cambia nada). Devuelve True si escribe."""
    b = texto.encode() if isinstance(texto, str) else texto
    if p.exists() and p.read_bytes() == b: return False
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b); return True


def recurso(b, nombre, ext):
    """build/datos/<nombre>.<hash8>.<ext> (borra las versiones viejas). Devuelve (ruta relativa a la raíz, SRI)."""
    BD.mkdir(parents=True, exist_ok=True)
    dest = f"{nombre}.{hashlib.sha256(b).hexdigest()[:8]}.{ext}"
    for viejo in BD.glob(f"{nombre}.*.{ext}"):
        if viejo.name != dest and re.fullmatch(rf"{re.escape(nombre)}\.[0-9a-f]{{8}}\.{ext}", viejo.name): viejo.unlink()
    escribir(BD / dest, b)
    return f"datos/{dest}", sri(b)


# fuentes: subconjunto latino (Latin-1, Latin Ext-A, puntuación general, flechas, ×, −) en woff2 (fontTools + brotli)
FUENTES = {"barlow-600": "barlow-semi-condensed/BarlowSemiCondensed-SemiBold.ttf",
           "barlow-700": "barlow-semi-condensed/BarlowSemiCondensed-Bold.ttf",
           "barlow-800": "barlow-semi-condensed/BarlowSemiCondensed-ExtraBold.ttf",
           "public-400": "public-sans/PublicSans-Regular.ttf", "public-500": "public-sans/PublicSans-Medium.ttf",
           "public-600": "public-sans/PublicSans-SemiBold.ttf"}
PRECARGA = ["public-400", "barlow-800", "barlow-600", "public-600"]   # las que pinta la primera pantalla


def fuentes():
    """build/fuentes/<nombre>.woff2 (+ OFL). Solo se rehacen si el TTF es más nuevo."""
    from fontTools import subset
    FU.mkdir(parents=True, exist_ok=True)
    uni = "U+0020-007E,U+00A0-00FF,U+0100-017F,U+2010-2027,U+2030-203A,U+2190-2193,U+2212,U+00D7,U+20AC"
    for nom, src in FUENTES.items():
        s, d = W / "fuentes" / src, FU / f"{nom}.woff2"
        if d.exists() and d.stat().st_mtime >= s.stat().st_mtime: continue
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga", "tnum", "lnum"]
        opts.desubroutinize = True
        f = subset.load_font(str(s), opts)
        sub = subset.Subsetter(opts); sub.populate(unicodes=subset.parse_unicodes(uni)); sub.subset(f)
        subset.save_font(f, str(d), opts)
    for lic in ("barlow-semi-condensed", "public-sans"):
        escribir(FU / f"OFL-{lic}.txt", (W / "fuentes" / lic / "OFL.txt").read_bytes())


_ASSETS = {}
def assets():
    """Publica comun.css y sitio.js (con las fuentes) una vez por proceso. {css, css_sri, js, js_sri, fichas, fichas_sri}."""
    if _ASSETS: return _ASSETS
    fuentes()
    css, css_sri = recurso((SITIO / "comun.css").read_bytes(), "sitio", "css")
    js, js_sri = recurso((SITIO / "sitio.js").read_bytes(), "sitio", "js")
    _ASSETS.update(css=css, css_sri=css_sri, js=js, js_sri=js_sri)
    f = W / "datos/fichas_indice.sri"
    if f.exists():
        src, s = f.read_text().split()
        if (BUILD / src).exists() and sri((BUILD / src).read_bytes()) == s:
            _ASSETS.update(fichas=src, fichas_sri=s)
    return _ASSETS


# ---------------------------------------------------------------- piezas
def cabecera(actual, R):
    """Cabecera y menú comunes. actual: clave de MENU resaltada (o None). R: prefijo hasta la raíz («», «../», «../../»)."""
    menu = "".join(f'<a href="{R}{RUTA[k]}"{" aria-current=\"page\"" if k == actual else ""}>{T(*NOM[k])}</a>' for k in MENU)
    return (f'<a class="salta" href="#contingut">{T("Salta al contingut", "Salta al contenido")}</a>'
            f'<header class="cabecera"><div class="wrap"><div class="fila">'
            f'<a class="marca" href="{R or "./"}"><span class="senal">{SENAL}</span><span class="txt"><span class="nom">{T("Observatori de la bici i el patinet", "Observatorio de la bici y el patinete")}</span><span class="subt">{T(*TITULO)}</span></span></a>'
            f'<div class="busca-row"><form class="busca-cab" role="search" data-busca action="{R}mapa/">'
            f'<label class="sr" for="busca-cab">{T("Busca el teu carrer o una cruïlla", "Busca tu calle o un cruce")}</label>'
            f'<input id="busca-cab" name="cerca" type="search" autocomplete="off" '
            f'aria-controls="sug-cab" placeholder="Carrer o cruïlla" data-ph-va="Carrer o cruïlla" data-ph-es="Calle o cruce">'
            f'<button type="submit">{T("Cerca", "Buscar")}</button><ul class="sug" id="sug-cab" hidden></ul></form></div>'
            f'<div class="lenguas" role="group" aria-label="Llengua / Lengua">'
            f'<button type="button" data-lang="va" lang="ca" aria-pressed="true" aria-label="va, Valencià" title="Valencià">va</button>'
            f'<button type="button" data-lang="es" lang="es" aria-pressed="false" aria-label="es, Castellano" title="Castellano">es</button></div>'
            f'<button type="button" data-tema></button>'
            f'<button class="b-menu" type="button" aria-expanded="false" aria-controls="menu" aria-label="Menú"><svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>'
            f'</div><div class="menu-caja"><nav class="menu" id="menu" aria-label="Seccions / Secciones">{menu}<span class="tema-menu"><button type="button" data-tema></button></span></nav></div></div></header>')


def migas(pasos, R):
    """pasos: [(clave_o_url, (va, es))…], el último es la página actual (sin enlace). Devuelve (html, json-ld)."""
    def href(k): return f"{R}{RUTA[k]}" if k in RUTA else k
    def abs_(k): return f"{DOMINIO}/{RUTA[k]}" if k in RUTA else k
    out = []
    for l, i in (("va", 0), ("es", 1)):
        lis = []
        for j, (k, nom) in enumerate(pasos):
            if j == len(pasos) - 1:
                lis.append(f'<li><span aria-current="page">{ESC(nom[i])}</span></li>')
            else:
                lis.append(f'<li><a href="{href(k)}">{ESC(nom[i])}</a></li>')
        aria = "Molles de pa" if l == "va" else "Migas de pan"
        out.append(f'<nav class="migas" data-l="{l}"{" lang=\"es\"" if l == "es" else ""} aria-label="{aria}"><ol>{"".join(lis)}</ol></nav>')
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": j + 1, "name": nom[0], **({"item": abs_(k)} if k else {})} for j, (k, nom) in enumerate(pasos)]}
    return "".join(out), '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def pie(R, info):
    """Pie común. info: {conjunto, descarga (AAAA-MM-DD), version (AAAA-MM-DD), colab?: [...]}."""
    dma = lambda f: f"{f[8:10]}/{f[5:7]}/{f[:4]}" if f else "—"
    colab = ""
    if info.get("colab"):
        def ent(e):
            n = f'<a href="{ESC(e["url"])}" rel="noopener">{ESC(e["ent"])}</a>' if e.get("url") else ESC(e["ent"])
            return n
        colab = T(f'<b>Hi col·laboren:</b> ' + " · ".join(ent(e) + (f' ({ESC(e["va"])})' if e.get("va") else "") for e in info["colab"]),
                  f'<b>Colaboran:</b> ' + " · ".join(ent(e) + (f' ({ESC(e["es"])})' if e.get("es") else "") for e in info["colab"]), "p")
    nav = (f'<nav aria-label="Peu / Pie">'
           f'<a href="{R}sobre/">{T("Sobre l\'observatori", "Sobre el observatorio")}</a>'
           f'<a href="{R}resso/">{T("Ressò", "Repercusión")}</a>'
           f'<a href="{R}lloc/">{T("Tots els llocs", "Todos los lugares")}</a>'
           f'<a href="{R}carrer/">{T("Tots els carrers", "Todas las calles")}</a>'
           f'<a href="{R}informe/">{T("Informes", "Informes")}</a>'
           f'<a href="{R}sobre/#canvis">{T("Què ha canviat", "Qué ha cambiado")}</a>'
           f'<a href="{R}sobre/#accessibilitat">{T("Accessibilitat", "Accesibilidad")}</a>'
           f'<a href="{R}sobre/#privacitat">{T("Privacitat i galetes", "Privacidad y cookies")}</a>'
           f'<a href="mailto:{CORREU}">{T("Contacte", "Contacto")}</a></nav>')
    tg = (f'<p class="pie-tg"><a href="{ESC(TELEGRAM_CANAL)}" rel="noopener">{T("Segueix les novetats al canal de Telegram", "Sigue las novedades en el canal de Telegram")}</a></p>'
          if TELEGRAM_CANAL else "")
    portal = '<a href="https://opendata.vlci.valencia.es">opendata.vlci.valencia.es</a>'
    c = f'<code>{ESC(info.get("conjunto", ""))}</code>'
    va = (f"<p>{MARCA[0]}, una iniciativa ciutadana independent · <a href=\"mailto:{CORREU}\">{CORREU}</a>. "
          f"Si veus un error o hi falta alguna cosa, escriu-nos.</p>"
          f"<p>Font de les dades: Ajuntament de València – Dades Obertes ({portal}), CC BY 4.0: sinistres de trànsit ({c}), carrerer, "
          f"carril bici i punts de comptatge, obtinguts el {dma(info.get('descarga'))}. Intensitats del carril bici: web de Mobilitat "
          f"(valencia.es). Pla Director de Seguretat Viària 2026-2030. Semàfors complementaris: © col·laboradors d'OpenStreetMap (ODbL). "
          f"<b>Dades modificades</b> per l'observatori: situem els accidents en el mapa amb el carrerer. L'Ajuntament de València no "
          f"participa en aquest treball ni l'avala. Està prohibit reidentificar persones creuant aquestes dades amb altres fonts.</p>"
          f"<p>Textos i gràfics: <a href=\"https://creativecommons.org/licenses/by/4.0/deed.ca\" rel=\"license\">CC BY 4.0</a>. "
          f"El codi és lliure (llicència MIT): <a href=\"{REPO}\" rel=\"noopener\">codi font a GitHub</a>. "
          f"Versió beta del {dma(info.get('version'))}.</p>")
    es = (f"<p>{MARCA[1]}, una iniciativa ciudadana independiente · <a href=\"mailto:{CORREU}\">{CORREU}</a>. "
          f"Si ves un error o falta algo, escríbenos.</p>"
          f"<p>Fuente de los datos: Ajuntament de València – Dades Obertes ({portal}), CC BY 4.0: siniestros de tráfico ({c}), callejero, "
          f"carril bici y puntos de conteo, obtenidos el {dma(info.get('descarga'))}. Intensidades del carril bici: web de Movilidad "
          f"(valencia.es). Plan Director de Seguridad Vial 2026-2030. Semáforos complementarios: © colaboradores de OpenStreetMap (ODbL). "
          f"<b>Datos modificados</b> por el observatorio: situamos los accidentes en el mapa con el callejero. El Ayuntamiento de València "
          f"no participa en este trabajo ni lo avala. Está prohibido reidentificar personas cruzando estos datos con otras fuentes.</p>"
          f"<p>Textos y gráficos: <a href=\"https://creativecommons.org/licenses/by/4.0/deed.es\" rel=\"license\">CC BY 4.0</a>. "
          f"El código es libre (licencia MIT): <a href=\"{REPO}\" rel=\"noopener\">código fuente en GitHub</a>. "
          f"Versión beta del {dma(info.get('version'))}.</p>")
    return (f'<footer class="pie"><div class="wrap">{nav}{tg}{colab}<div data-l="va">{va}</div><div data-l="es" lang="es">{es}</div></div></footer>')


HEAD_LANG = ('<script>try{if(localStorage.getItem("obs-lang")==="es")document.documentElement.lang="es"}catch(e){}</script>')


# Estadísticas sin cookies (Umami propio, deploy/README.md «Estadísticas (Umami)»). Vacío: no se añade nada y la web sale
# idéntica. Antes de rellenarlo, activar la CSP comentada de deploy/nginx/DOMINIO.conf.plantilla (si no, la bloquea).
# data-domains: solo cuenta en el dominio publicado (no en localhost); data-do-not-track: respeta «Do Not Track».
UMAMI_ID = "63d73d64-23d6-4de9-99ae-60f66a166f5c"   # sitio «Observatorio Bici» en estadisticas.observatoribicivlc.org (07/11/2026)


def head(R, titulo, desc, url, og_img=None, og_alt=None, extra=""):
    """<head> común: lengua antes del primer pintado, tema, fuentes con preload, CSS común con SRI, Open Graph."""
    A = assets()
    if UMAMI_ID:   # contador de Umami (sin SRI: el script lo sirve y actualiza nuestro propio Umami)
        extra += (f'<script defer src="https://estadisticas.{DOMINIO.split("//")[1]}/script.js" data-website-id="{ESC(UMAMI_ID)}" '
                  f'data-domains="{DOMINIO.split("//")[1]}" data-do-not-track="true"></script>\n')
    pre = "".join(f'<link rel="preload" href="{R}fuentes/{f}.woff2" as="font" type="font/woff2" crossorigin>' for f in PRECARGA)
    tema = (W / "comun/tema.js").read_text()
    og = (f'<meta property="og:type" content="website"><meta property="og:site_name" content="{ESC(MARCA[0])}">'
          f'<meta property="og:url" content="{url}"><meta property="og:title" content="{ESC(titulo[0])}">'
          f'<meta property="og:description" content="{ESC(desc[0])}"><meta property="og:locale" content="ca_ES">'
          f'<meta property="og:locale:alternate" content="es_ES">')
    if og_img:
        og += (f'<meta property="og:image" content="{DOMINIO}/{og_img}"><meta property="og:image:type" content="image/png">'
               f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
               f'<meta property="og:image:alt" content="{ESC(og_alt or titulo[0])}"><meta name="twitter:card" content="summary_large_image">'
               f'<meta name="twitter:title" content="{ESC(titulo[0])}"><meta name="twitter:description" content="{ESC(desc[0])}">'
               f'<meta name="twitter:image" content="{DOMINIO}/{og_img}">')
    return ('<!doctype html>\n<html lang="ca">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{HEAD_LANG}\n<title>{ESC(titulo[0])}</title>\n<meta name="description" content="{ESC(desc[0])}">\n'
            f'<link rel="canonical" href="{url}">\n'
            '<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">\n'
            '<meta name="theme-color" content="#0F151B" media="(prefers-color-scheme: dark)">\n'
            f'<link rel="icon" type="image/svg+xml" href="{ICONO}">\n{og}\n{pre}\n'
            f'<link rel="stylesheet" href="{R}{A["css"]}" integrity="{A["css_sri"]}">\n'
            f'<script>{tema}</script>\n{extra}</head>\n')


def scripts_fin(R):
    """Índice de las fichas (buscador) y sitio.js, con SRI."""
    A = assets(); s = ""
    if A.get("fichas"):
        s += f'<script src="{R}{A["fichas"]}" integrity="{A["fichas_sri"]}"></script>\n'
    return s + f'<script src="{R}{A["js"]}" integrity="{A["js_sri"]}"></script>\n'


def body_attrs(R, titulo, desc):
    return (f'data-raiz="{R}" data-titulo-va="{ESC(titulo[0])}" data-titulo-es="{ESC(titulo[1])}" '
            f'data-desc-va="{ESC(desc[0])}" data-desc-es="{ESC(desc[1])}"')


def pagina(clave, ruta, R, titulo, desc, cuerpo, info, pasos=None, og_img=None, og_alt=None, extra_head="", extra_fin="", main_attrs=""):
    """Página completa. clave: la de MENU que se resalta (o None). ruta: la de la página («mapa/»…), para canonical y og:url.
    R: prefijo hasta la raíz. pasos: migas (None en la portada)."""
    url = f"{DOMINIO}/{ruta}"
    m, ld = migas(pasos, R) if pasos else ("", "")
    return pulir(head(R, titulo, desc, url, og_img, og_alt, extra_head + (ld + "\n" if ld else ""))
            + f'<body data-pag="{clave or ""}" {body_attrs(R, titulo, desc)}>\n{cabecera(clave, R)}\n'
            + f'<main class="wrap" id="contingut" tabindex="-1"{main_attrs}>{m}{cuerpo}</main>\n{pie(R, info)}\n'

            + extra_fin + scripts_fin(R) + '</body>\n</html>\n')


def pulir(html):
    """Retoques de accesibilidad y tipografía sobre la página entera (07/11/2026):
    - aria-label="va / es" → el de la lengua de la página (sitio.js lo cambia con data-aria-va/-es; antes el lector de
      pantalla leía las dos lenguas con la barra);
    - la flecha de los enlaces «… →» nunca se queda sola en otra línea (espacio no separable)."""
    html = re.sub(r'aria-label="([^"/<>]+?) / ([^"/<>]+?)"', r'aria-label="\1" data-aria-va="\1" data-aria-es="\2"', html)
    return html.replace(" →", " →")

