"""Publica las novedades del Observatori en su canal de Telegram (solo difusión), en valenciano y castellano.

Solo biblioteca estándar (urllib para la Bot API). Lee:
  - docs/cambios.csv                          registro público de cambios (solo los tipos de TIPOS_CANVI: datos y web)
  - data/processed/plan_seguimiento.csv       «Què està fent l'Ajuntament?»: estado y fecha de cada medida
  - data/processed/avisos_ciudadanos.csv      avisos de la ciudadanía; solo se publican los de resultado = incorporado
Los títulos en valenciano y castellano de las medidas salen de scripts/sitio_textos_plan.py (MEDIDAS); si falta una
medida, se usa `actuacion` del CSV.

Qué es una novedad (un identificador por elemento; se guarda en el estado lo ya publicado):
  - cambio:  fecha + tipo + principio del texto en castellano (una errata al final del texto no lo vuelve a publicar);
  - medida:  id + estado + fecha_estado (una medida nueva, un cambio de estado o una fuente nueva con otra fecha);
  - aviso:   fecha + medida + resumen, solo si resultado = incorporado.

Estado (fuera de git): ~/.local/state/observatori/telegram_publicado.json (o $OBSERVATORI_TELEGRAM_ESTADO), con dos
listas: lo publicado mensaje a mensaje y lo incluido en un resumen semanal. Lo que ya salió en una no sale en la otra.
Primera ejecución sin estado: todo lo que ya existe se marca como publicado y no se envía nada (para no inundar el
canal), salvo lo que tenga fecha >= --desde AAAA-MM-DD. En modo --prova solo se dice qué se marcaría.

Credenciales (nunca en el repositorio): variables TELEGRAM_TOKEN y TELEGRAM_CANAL o, si faltan, el fichero
~/.config/observatori/telegram.env (o $OBSERVATORI_TELEGRAM_ENV) con líneas CLAVE=valor y permisos 600.

Uso (.venv/bin/python -I scripts/telegram_publicar.py ...):
  (sin opciones) / --prova     enseña los mensajes que se enviarían; no envía ni escribe nada
  --enviar                     los envía y guarda el estado tras cada mensaje enviado
  --resum-setmanal             un único mensaje con lo que no se ha publicado aún (o nada si no hay nada);
                               con --prova se enseña, con --enviar se envía
  --desde AAAA-MM-DD           en la primera ejecución, publica lo que tenga esa fecha o posterior
  --max N                      tope de mensajes por ejecución (10); si hay más, se para sin enviar (estado perdido?)
  --subscriptors               pide el número de miembros del canal (getChatMemberCount) y añade fecha,subscriptors a
                               data/processed/telegram_subscriptors.csv (prueba de uso para la memoria)
  --autoprova                  prueba sin red con datos y credenciales falsos (make telegram-prova)
Ver deploy/README.md, «Canal de Telegram».
"""
import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import stat
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

WEB = "https://observatoribicivlc.org"
UTM = "utm_source=telegram"
CAMBIOS = ROOT / "docs/cambios.csv"
PLAN = ROOT / "data/processed/plan_seguimiento.csv"
AVISOS = ROOT / "data/processed/avisos_ciudadanos.csv"
SUBS = ROOT / "data/processed/telegram_subscriptors.csv"
ESTADO = Path(os.environ.get("OBSERVATORI_TELEGRAM_ESTADO", Path.home() / ".local/state/observatori/telegram_publicado.json"))
ENV = Path(os.environ.get("OBSERVATORI_TELEGRAM_ENV", Path.home() / ".config/observatori/telegram.env"))
API = "https://api.telegram.org"
LIMITE = 4096          # longitud máxima de un mensaje de Telegram
RESUM_MAX = 8          # líneas como mucho en el resumen semanal
LARGO = 600            # caracteres de texto por idioma en un mensaje (el resto, en la web)
PAUSA = 3.0            # segundos entre mensajes (un canal admite unos 20 por minuto)

EST = {"hecha": ("feta", "hecha"), "en_marcha": ("en marxa", "en marcha"), "anunciada": ("anunciada", "anunciada"),
       "sin_info": ("sense informació pública", "sin información pública")}
TIPO = {"datos": ("Dades", "Datos"), "metode": ("Mètode", "Método"), "web": ("Web", "Web")}
SEP = "\n\n— — —\n\n"


class ErrorTelegram(Exception):
    pass


def e(s):
    return html.escape(s or "", quote=False)


def enlace(ruta, ancla=""):
    """URL pública con utm_source=telegram (la consulta va antes del ancla)."""
    return f"{WEB}/{ruta}?{UTM}" + (f"#{ancla}" if ancla else "")


def fecha_txt(f):
    try:
        return dt.date.fromisoformat(f).strftime("%d/%m/%Y")
    except ValueError:
        return f


def h(*partes):
    return hashlib.sha1("|".join(partes).encode()).hexdigest()[:16]


def leer_csv(p):
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def textos_medidas():
    try:
        import sitio_textos_plan
        return sitio_textos_plan.MEDIDAS
    except Exception:          # el módulo es de la web; si cambia o falta, se cae a `actuacion`
        return {}


def _cortes(t):
    """Posiciones de fin de frase: punto seguido de espacio y mayúscula (o final), sin abreviaturas como «Pl.» o «Av.»."""
    for i, c in enumerate(t):
        if c != "." or (i + 1 < len(t) and not (t[i + 1] == " " and i + 2 < len(t) and t[i + 2].isupper())):
            continue
        palabra = t[:i].rsplit(" ", 1)[-1]
        if len(palabra) > 3 or palabra.isdigit():
            yield i + 1


def recortar(t, n):
    """Las frases enteras que caben en n caracteres; si no cabe ni la primera, se corta por palabra con «…»."""
    t = " ".join((t or "").split())
    if len(t) <= n:
        return t
    cortes = [i for i in _cortes(t) if i <= n]
    if cortes:
        return t[:cortes[-1]] + " […]"
    return t[:n - 1].rsplit(" ", 1)[0] + "…"


def recortar_par(va, es, n):
    """Recorta los dos idiomas al mismo número de frases (el que quepa en n en los dos)."""
    va, es = (" ".join((x or "").split()) for x in (va, es))
    if len(va) <= n and len(es) <= n:
        return va, es
    cv, ce = list(_cortes(va)), list(_cortes(es))
    k = min(sum(i <= n for i in cv), sum(i <= n for i in ce))
    if k and len(cv) == len(ce):
        return va[:cv[k - 1]] + " […]", es[:ce[k - 1]] + " […]"
    return recortar(va, n), recortar(es, n)


def primera_frase(t, n=220):
    t = " ".join((t or "").split())
    c = next(_cortes(t), len(t))
    return recortar(t[:c], n)


# ---------------------------------------------------------------- novedades

# Decisión del usuario (07/11/2026): el canal publica las novedades en cuanto las hay, sin cita fija (sin resumen
# semanal): cambios de las medidas del Plan, avisos ciudadanos incorporados y cambios de datos y de la web de
# docs/cambios.csv (no los de método). Los cambios salen cortos: su resumen (resumen_va/resumen_es; si falta, la primera
# frase) y el enlace al registro.
TIPOS_CANVI = frozenset({"datos", "web"})


def novedades(cambios=CAMBIOS, plan=PLAN, avisos=AVISOS, tipos_canvi=TIPOS_CANVI):
    """Lista de dicts: id, fecha, clase, va, es (mensaje HTML) y va_corto, es_corto (línea del resumen)."""
    out = []
    for r in leer_csv(cambios):
        if r.get("tipo") not in tipos_canvi or not (r.get("va") and r.get("es")):
            continue
        tv, te = TIPO.get(r["tipo"], (r["tipo"], r["tipo"]))
        url = enlace("sobre/", "canvis")
        # resumen corto de docs/cambios.csv (resumen_va/resumen_es, ≤ 120 caracteres); si falta, la primera frase
        cv = " ".join((r.get("resumen_va") or "").split()) or primera_frase(r["va"])
        ce = " ".join((r.get("resumen_es") or "").split()) or primera_frase(r["es"])
        out.append(dict(
            id="canvi:" + h(r["fecha"], r["tipo"], " ".join(r["es"].split())[:80]), fecha=r["fecha"], clase="canvi",
            va=f"<b>Què ha canviat</b> · {e(tv)} · {fecha_txt(r['fecha'])}\n\n{e(cv)}\n\n<a href=\"{url}\">Tots els canvis</a>",
            es=f"<b>Qué ha cambiado</b> · {e(te)} · {fecha_txt(r['fecha'])}\n\n{e(ce)}\n\n<a href=\"{url}\">Todos los cambios</a>",
            va_corto=e(cv), es_corto=e(ce), url=url))

    med = textos_medidas()
    for r in leer_csv(plan):
        mid, est, fe = r["id"], r["estado"], r.get("fecha_estado", "")
        if est not in EST:
            continue
        t = med.get(mid, {}).get("tit") or {"va": r["actuacion"], "es": r["actuacion"]}
        url = enlace("ajuntament/", f"a-{mid}")
        n = dict(id=f"pla:{mid}:{est}:{fe}", fecha=fe or r.get("comprobado", ""), clase="pla", medida=mid,
                 tit=t, estado=est, fecha_estado=fe, url=url)
        n.update(texto_pla(n))
        out.append(n)

    for r in leer_csv(avisos):
        if r.get("resultado") != "incorporado":
            continue
        mp = r.get("medida_plan", "")
        url = enlace("ajuntament/", f"a-{mp}" if mp in med else "avisa")
        lv = f" ({e(r['lugar'])})" if r.get("lugar") else ""
        out.append(dict(
            id="avis:" + h(r["fecha"], mp, r.get("resumen_es", "")), fecha=r["fecha"], clase="avis",
            va=(f"<b>Avís de la ciutadania</b>{lv}\n\nGràcies a un avís, i després de trobar-ne la font oficial, hem afegit açò: "
                f"{e(r.get('resumen_va', ''))}\n\n<a href=\"{url}\">Mira-ho en la web</a>"),
            es=(f"<b>Aviso de la ciudadanía</b>{lv}\n\nGracias a un aviso, y tras encontrar la fuente oficial, hemos añadido esto: "
                f"{e(r.get('resumen_es', ''))}\n\n<a href=\"{url}\">Verlo en la web</a>"),
            va_corto=e(primera_frase(r.get("resumen_va", ""))), es_corto=e(primera_frase(r.get("resumen_es", ""))), url=url))
    return out


FRASE_EST = {"hecha": ("ja està <b>feta</b>", "ya está <b>hecha</b>"),
             "en_marcha": ("està <b>en marxa</b>", "está <b>en marcha</b>"),
             "anunciada": ("està <b>anunciada</b>", "está <b>anunciada</b>"),
             "sin_info": ("encara no hem trobat informació pública", "todavía no hemos encontrado información pública")}


def texto_pla(n, anterior=None):
    """Textos de una medida. anterior = estado ya publicado de la misma medida (None si es la primera vez)."""
    t, est, fe, url = n["tit"], n["estado"], n["fecha_estado"], n["url"]
    fv, fes = FRASE_EST[est]
    if est == "sin_info":
        cv, ce = "De moment, no hem trobat informació pública.", "Por ahora, no hemos encontrado información pública."
    elif fe:
        cv, ce = f"Segons la font del {fecha_txt(fe)}, {fv}.", f"Según la fuente del {fecha_txt(fe)}, {fes}."
    else:
        cv, ce = f"Ara {fv}.", f"Ahora {fes}."
    if anterior is None:
        iv, ie = "Seguim una mesura nova", "Seguimos una medida nueva"
    elif anterior == est:
        iv, ie = "Hi ha una font nova sobre aquesta mesura", "Hay una fuente nueva sobre esta medida"
    else:
        iv = f"Aquesta mesura canvia d'estat (abans, {EST[anterior][0]})"
        ie = f"Esta medida cambia de estado (antes, {EST[anterior][1]})"
    return dict(
        va=(f"<b>Què està fent l'Ajuntament?</b>\n\n{iv}: «{e(t['va'].rstrip('.'))}». {cv}\n\n"
            f"<a href=\"{url}\">Mira la mesura i la font</a>"),
        es=(f"<b>¿Qué está haciendo el Ayuntamiento?</b>\n\n{ie}: «{e(t['es'].rstrip('.'))}». {ce}\n\n"
            f"<a href=\"{url}\">Ver la medida y la fuente</a>"),
        va_corto=f"«{e(primera_frase(t['va'], 140).rstrip('.'))}»: {EST[est][0]}",
        es_corto=f"«{e(primera_frase(t['es'], 140).rstrip('.'))}»: {EST[est][1]}")


def anterior_pla(n, estado):
    """Último estado publicado (en cualquiera de los dos modos) de la misma medida, o None."""
    previo = None
    for clave in ("publicat", "resum"):
        for k in estado.get(clave, {}):
            if k.startswith(f"pla:{n['medida']}:") and k != n["id"]:
                previo = k.split(":")[2]
    return previo


def mensaje(n):
    return n["va"] + SEP + n["es"]


def resumen(ns, hoy):
    """Un único mensaje bilingüe con la lista de novedades; recorta la lista si no cabe."""
    def montar(k):
        sel = ns[:k]
        resto = len(ns) - k
        lv = "\n".join(f"• {n['va_corto']}" for n in sel) + (f"\n• i {resto} més" if resto else "")
        le = "\n".join(f"• {n['es_corto']}" for n in sel) + (f"\n• y {resto} más" if resto else "")
        url = enlace("sobre/", "canvis")
        return (f"<b>Resum de la setmana</b> · {fecha_txt(hoy)}\n\n{lv}\n\n<a href=\"{url}\">Tots els canvis</a>"
                + SEP + f"<b>Resumen de la semana</b> · {fecha_txt(hoy)}\n\n{le}\n\n<a href=\"{url}\">Todos los cambios</a>")
    orden = {"pla": 0, "avis": 1, "canvi": 2}       # primero el Plan; dentro, lo más reciente primero
    rel = {"hecha": 0, "en_marcha": 1, "anunciada": 2, "sin_info": 3}
    ns = sorted(sorted(ns, key=lambda n: n["fecha"], reverse=True),
                key=lambda n: (orden[n["clase"]], rel.get(n.get("estado"), 0)))
    k = min(len(ns), RESUM_MAX)
    while k > 1 and len(montar(k)) > LIMITE:
        k -= 1
    return montar(k)


# ---------------------------------------------------------------- estado y credenciales

def leer_estado(p=None):
    p = p or ESTADO
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as ex:
        sys.exit(f"ERROR: no se puede leer el estado {p}: {ex}. No se envía nada (arreglarlo o borrarlo a propósito).")
    d.setdefault("publicat", {})
    d.setdefault("resum", {})
    return d


def guardar_estado(d, p=None):
    p = p or ESTADO
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".telegram_", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, p)


def credenciales(env=None):
    token, canal = os.environ.get("TELEGRAM_TOKEN", ""), os.environ.get("TELEGRAM_CANAL", "")
    env = env or ENV
    if (not token or not canal) and env.exists():
        modo = stat.S_IMODE(env.stat().st_mode)
        if modo & 0o077:
            print(f"AVISO: {env} tiene permisos {oct(modo)}; debería ser 600 (chmod 600 {env})", file=sys.stderr)
        for linea in env.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = (x.strip() for x in linea.split("=", 1))
            v = v.strip("'\"")
            if k == "TELEGRAM_TOKEN" and not token:
                token = v
            elif k == "TELEGRAM_CANAL" and not canal:
                canal = v
    if not token or not canal:
        sys.exit(f"ERROR: faltan TELEGRAM_TOKEN y/o TELEGRAM_CANAL (variables de entorno o {env}). Ver deploy/README.md, «Canal de Telegram».")
    return token, canal


# ---------------------------------------------------------------- Bot API

def llamar(token, metodo, datos, abrir=urllib.request.urlopen, intentos=3, dormir=time.sleep):
    """POST a la Bot API. Respeta 429 (retry_after). Los errores nunca incluyen el token."""
    url = f"{API}/bot{token}/{metodo}"
    cuerpo = json.dumps(datos).encode()
    for intento in range(1, intentos + 1):
        req = urllib.request.Request(url, data=cuerpo, headers={"Content-Type": "application/json"})
        try:
            with abrir(req, timeout=30) as r:
                resp = json.loads(r.read().decode())
        except urllib.error.HTTPError as ex:
            try:
                resp = json.loads(ex.read().decode())
            except Exception:
                resp = {"ok": False, "error_code": ex.code, "description": ex.reason}
        except (urllib.error.URLError, TimeoutError, OSError) as ex:
            motivo = str(getattr(ex, "reason", ex)).replace(token, "***")
            if intento < intentos:
                print(f"  red: {motivo}; reintento {intento}/{intentos - 1} en 5 s", file=sys.stderr)
                dormir(5)
                continue
            raise ErrorTelegram(f"{metodo}: sin conexión con la API de Telegram ({motivo})") from None
        if resp.get("ok"):
            return resp.get("result")
        codigo = resp.get("error_code")
        desc = str(resp.get("description", "")).replace(token, "***")
        espera = (resp.get("parameters") or {}).get("retry_after")
        if codigo == 429 and espera is not None and intento < intentos:
            print(f"  Telegram pide esperar {espera} s (429); reintento {intento}/{intentos - 1}", file=sys.stderr)
            dormir(int(espera) + 1)
            continue
        pista = {401: " (token incorrecto o revocado)",
                 400: " (¿TELEGRAM_CANAL bien escrito? @nombre o -100…; ¿HTML mal formado?)",
                 403: " (¿el bot es administrador del canal con permiso para publicar?)"}.get(codigo, "")
        raise ErrorTelegram(f"{metodo}: error {codigo}: {desc}{pista}")
    raise ErrorTelegram(f"{metodo}: sin respuesta válida tras {intentos} intentos")


def enviar(token, canal, texto, **kw):
    return llamar(token, "sendMessage", {"chat_id": canal, "text": texto, "parse_mode": "HTML",
                                         "link_preview_options": {"is_disabled": True}}, **kw)


# ---------------------------------------------------------------- principal

def pendientes(ns, estado, desde):
    """Lo que no se ha publicado ni en un mensaje propio ni en un resumen semanal."""
    hecho = set(estado["publicat"]) | set(estado["resum"]) if estado else set()
    return [n for n in ns if n["id"] not in hecho and (not desde or n["fecha"] >= desde)]


def ejecutar(a, ns=None, ruta_estado=None, env=None, abrir=urllib.request.urlopen, dormir=time.sleep, hoy=None):
    hoy = hoy or dt.date.today().isoformat()
    ns = novedades() if ns is None else ns
    estado = leer_estado(ruta_estado)
    clave = "resum" if a.resum_setmanal else "publicat"
    primera = estado is None
    if estado is None:
        estado = {"publicat": {}, "resum": {}}

    if primera:
        viejas = [n for n in ns if not a.desde or n["fecha"] < a.desde]
        for n in viejas:
            estado[clave][n["id"]] = "inicial"
        print(f"Primera ejecución ({'resumen semanal' if a.resum_setmanal else 'mensajes'}): {len(viejas)} de {len(ns)} "
              f"elementos existentes se marcan como ya publicados" + (f" (los anteriores a {a.desde})" if a.desde else "")
              + (" (en --prova no se guarda)" if not a.enviar else ""))
        if a.enviar and not pendientes(ns, estado, a.desde):
            guardar_estado(estado, ruta_estado)
            print("Estado guardado; no se envía nada.")
            return 0

    nuevas = pendientes(ns, estado, a.desde)
    if not nuevas:
        print("Nada nuevo que publicar.")
        if a.enviar and primera:
            guardar_estado(estado, ruta_estado)
        return 0

    for n in nuevas:
        if n["clase"] == "pla":
            n.update(texto_pla(n, anterior_pla(n, estado)))
    if a.resum_setmanal:
        textos = [(nuevas, resumen(nuevas, hoy))]
    else:
        if len(nuevas) > a.max and a.enviar:
            print(f"ERROR: hay {len(nuevas)} novedades y el tope es {a.max}. ¿Se ha perdido el estado ({ruta_estado or ESTADO})? "
                  f"Revisar con --prova; para enviarlas de verdad, --max {len(nuevas)}.", file=sys.stderr)
            return 2
        textos = [([n], mensaje(n)) for n in nuevas]

    if not a.enviar:
        for i, (_, t) in enumerate(textos, 1):
            print(f"\n===== mensaje {i}/{len(textos)} ({len(t)} caracteres) =====\n{t}")
        print(f"\n--prova: {len(textos)} mensaje(s); no se ha enviado nada. Para enviarlos: --enviar")
        return 0

    token, canal = credenciales(env)
    for i, (grupo, t) in enumerate(textos, 1):
        if len(t) > LIMITE:
            print(f"ERROR: el mensaje {grupo[0]['id']} tiene {len(t)} caracteres (> {LIMITE}); no se envía", file=sys.stderr)
            return 1
        try:
            enviar(token, canal, t, abrir=abrir, dormir=dormir)
        except ErrorTelegram as ex:
            print(f"ERROR al enviar el mensaje {i}/{len(textos)}: {ex}. Los anteriores quedan marcados; se puede repetir.",
                  file=sys.stderr)
            return 1
        for n in grupo:
            estado[clave][n["id"]] = hoy
        guardar_estado(estado, ruta_estado)
        print(f"enviado {i}/{len(textos)}: {', '.join(n['id'] for n in grupo[:3])}{' …' if len(grupo) > 3 else ''}")
        if i < len(textos):
            dormir(PAUSA)
    return 0


def subscriptors(env=None, abrir=urllib.request.urlopen, ruta=SUBS, hoy=None):
    token, canal = credenciales(env)
    n = llamar(token, "getChatMemberCount", {"chat_id": canal}, abrir=abrir)
    hoy = hoy or dt.date.today().isoformat()
    nuevo = not ruta.exists()
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "subscriptors"])
        w.writerow([hoy, n])
    print(f"{hoy}: {n} miembros en el canal (incluye el bot y las personas administradoras) → {ruta}")
    return 0


# ---------------------------------------------------------------- prueba sin red

def autoprova():
    """Datos, credenciales y API falsos: primera ejecución sin inundar, una novedad, escape HTML, 429 y resumen."""
    class Resp:
        def __init__(self, d): self.d = d
        def read(self): return json.dumps(self.d).encode()
        def __enter__(self): return self
        def __exit__(self, *x): return False

    enviados, cola = [], []

    def abrir(req, timeout=None):
        assert "/botFALSO:123/" in req.full_url
        d = cola.pop(0) if cola else {"ok": True, "result": {"message_id": len(enviados) + 1}}
        if d.get("ok"):
            enviados.append(json.loads(req.data))
        return Resp(d)

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "cambios.csv").write_text("fecha,tipo,va,es,resumen_va,resumen_es\n2026-11-01,web,\"Primer canvi.\",\"Primer cambio.\",Primer.,Primero.\n", encoding="utf-8")
        (t / "plan.csv").write_text("id,actuacion,estado,fecha_estado,comprobado\nx-1,Medida <prueba> & co,anunciada,2026-10-01,\n",
                                    encoding="utf-8")
        (t / "avisos.csv").write_text("fecha,medida_plan,lugar,resumen_va,resumen_es,resultado,fuente_url\n"
                                      "2026-11-02,,C/ Falsa,Avís no comprovat,Aviso no comprobado,pendiente,\n", encoding="utf-8")
        envf = t / "telegram.env"
        envf.write_text("TELEGRAM_TOKEN=FALSO:123\nTELEGRAM_CANAL=@canal_falso\n", encoding="utf-8")
        envf.chmod(0o600)
        est = t / "estado.json"
        for k in ("TELEGRAM_TOKEN", "TELEGRAM_CANAL"):
            os.environ.pop(k, None)
        A = lambda **kw: argparse.Namespace(**{"enviar": False, "resum_setmanal": False, "desde": None, "max": 10, **kw})
        nov = lambda: novedades(t / "cambios.csv", t / "plan.csv", t / "avisos.csv", tipos_canvi={"web", "datos"})
        assert all(n["clase"] != "canvi" for n in novedades(t / "cambios.csv", t / "plan.csv", t / "avisos.csv", tipos_canvi=frozenset())), "sin tipos, no se publican cambios"
        run = lambda a, **kw: ejecutar(a, ns=nov(), ruta_estado=est, env=envf, abrir=abrir, dormir=lambda s: None, **kw)

        assert len(nov()) == 2, "el aviso pendiente no se publica"
        assert run(A()) == 0 and not est.exists(), "--prova no escribe estado"
        assert run(A(enviar=True)) == 0 and not enviados, "la primera vez no se envía nada"
        assert len(json.loads(est.read_text())["publicat"]) == 2
        with open(t / "cambios.csv", "a", encoding="utf-8") as f:
            f.write('2026-11-07,datos,"Detall llarg. Segona frase.","Detalle largo. Segunda frase.","Dades <noves> & més.","Datos <nuevos> & más."\n')
        cola.append({"ok": False, "error_code": 429, "description": "Too Many Requests", "parameters": {"retry_after": 1}})
        assert run(A(enviar=True)) == 0 and len(enviados) == 1, "un 429 se reintenta y se envía una vez"
        txt = enviados[0]["text"]
        assert "&lt;noves&gt; &amp; més" in txt and "<noves>" not in txt and enviados[0]["parse_mode"] == "HTML"
        assert "Detall llarg" not in txt and "Detalle largo" not in txt, "el mensaje usa el resumen, no el detalle"
        assert txt.index("Què ha canviat") < txt.index("Qué ha cambiado") and "utm_source=telegram#canvis" in txt
        assert run(A(enviar=True)) == 0 and len(enviados) == 1, "lo enviado no se repite"
        cola.append({"ok": False, "error_code": 403, "description": "Forbidden: bot is not a member"})
        with open(t / "cambios.csv", "a", encoding="utf-8") as f:
            f.write('2026-11-08,web,"Un altre.","Otro.",,\n')   # sin resumen: la primera frase
        print("(se espera un 429 y un error 403 simulados)")
        assert run(A(enviar=True)) == 1, "un 403 para con error"
        with open(t / "plan.csv", "a", encoding="utf-8") as f:
            f.write("x-2,Otra medida,en_marcha,2026-11-08,\n")
        assert run(A(resum_setmanal=True, enviar=True), hoy="2026-11-09") == 0 and len(enviados) == 2
        r = enviados[1]["text"]
        assert "Resum de la setmana" in r and "Otra medida" in r and "Un altre" in r and "Dades &lt;noves&gt;" not in r, "resumen: solo lo no publicado"
        assert run(A(resum_setmanal=True, enviar=True)) == 0 and len(enviados) == 2, "sin novedades, no hay resumen"
        txt = (t / "plan.csv").read_text().replace("x-1,Medida <prueba> & co,anunciada,2026-10-01", "x-1,Medida <prueba> & co,en_marcha,2026-11-09")
        (t / "plan.csv").write_text(txt, encoding="utf-8")
        assert run(A(enviar=True, max=10)) == 0 and any("canvia d'estat (abans, anunciada)" in m["text"] for m in enviados[-3:]), "cambio de estado"
        assert "&lt;prueba&gt;" in mensaje(next(n for n in nov() if n["clase"] == "pla")), "escape en los títulos del Plan"
        subscriptors(env=envf, abrir=lambda req, timeout=None: Resp({"ok": True, "result": 7}), ruta=t / "subs.csv", hoy="2026-11-09")
        assert (t / "subs.csv").read_text().splitlines() == ["fecha,subscriptors", "2026-11-09,7"]
    print("autoprova OK: primera ejecución sin inundar, resumen del cambio, escape HTML, 429, 403, resumen semanal y subscriptors (sin red)")
    return 0


def main():
    p = argparse.ArgumentParser(description="Publica las novedades del Observatori en Telegram.")
    m = p.add_mutually_exclusive_group()
    m.add_argument("--prova", action="store_true", help="enseña los mensajes sin enviar (por defecto)")
    m.add_argument("--enviar", action="store_true", help="envía los mensajes y guarda el estado")
    p.add_argument("--resum-setmanal", action="store_true", help="un único mensaje con lo nuevo desde el último resumen")
    p.add_argument("--desde", help="AAAA-MM-DD: en la primera ejecución, publicar lo de esa fecha o posterior")
    p.add_argument("--max", type=int, default=10, help="tope de mensajes por ejecución (10)")
    p.add_argument("--subscriptors", action="store_true", help="anota el número de miembros del canal en el CSV")
    p.add_argument("--autoprova", action="store_true", help="prueba sin red (make telegram-prova)")
    a = p.parse_args()
    if a.desde:
        try:
            dt.date.fromisoformat(a.desde)
        except ValueError:
            p.error("--desde debe ser AAAA-MM-DD")
    if a.autoprova:
        return autoprova()
    if a.subscriptors:
        try:
            return subscriptors()
        except ErrorTelegram as ex:
            print(f"ERROR: {ex}", file=sys.stderr)
            return 1
    return ejecutar(a)


if __name__ == "__main__":
    sys.exit(main())
