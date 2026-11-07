"""Nombres de lugares y calles como los escribiría una persona: una sola función de formato para toda la web.

«PG ALBEREDA cruce PL SARAGOSSA (S)» → «Passeig de l'Albereda amb plaça de Saragossa» (va)
«PG ALAMEDA cruce PL ZARAGOZA (S)»   → «Paseo de la Alameda con plaza de Zaragoza» (es)

La usan el mapa (construir_sitio.py le pasa una tabla nombre de los datos → [va, es]), las fichas estáticas y su índice
(fichas.py, que también alimenta el buscador) y los índices de lugares y calles. Los nombres de los datos
(data/processed/nombres_lugares.csv, congelados) no cambian: esto solo decide cómo se muestran.

Reglas:
  - tipo de vía desarrollado y en minúscula dentro del nombre («plaza», «carrer»; «Gran Vía» y «Gran Via» siempre así);
  - «de» entre el tipo y el nombre, con el artículo cuando el nombre lo lleva (tabla ARTICULO: títulos como «Doctor» o
    «Pintor» y nombres como «Alameda» o «Puerto») y con las contracciones de cada lengua (del, de l', d');
  - sin el sufijo de calzada («(S)», «(SO)»…), salvo si dos lugares se llamarían igual: entonces «(lado sur)»;
  - en castellano, con tildes: las del nombre oficial cuando coinciden, las de cualquier nombre oficial del callejero, la
    terminación -ción y una tabla pequeña (TILDES_ES) para lo que el callejero no resuelve («Aragon», «Angel Guimera»);
  - las direcciones del parte (en castellano) se pasan al valenciano con la traducción del propio callejero.
"""
import csv, functools, json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TIPO = {  # código del callejero → (castellano, valenciano, género es, género va); "" = sin tipo visible
    "C/": ("calle", "carrer", "f", "m"), "AV": ("avenida", "avinguda", "f", "f"), "PL": ("plaza", "plaça", "f", "f"),
    "PG": ("paseo", "passeig", "m", "m"), "GV": ("Gran Vía", "Gran Via", "f", "f"), "CTRA": ("carretera", "carretera", "f", "f"),
    "CRA": ("carretera", "carretera", "f", "f"), "CAMI": ("camino", "camí", "m", "m"), "CN": ("camino", "camí", "m", "m"),
    "PTGE": ("pasaje", "passatge", "m", "m"), "TRAV": ("travesía", "travessera", "f", "f"), "PTDA": ("partida", "partida", "f", "f"),
    "SENDA": ("senda", "senda", "f", "f"), "GRUP": ("grupo", "grup", "m", "m"),
    "LLOC": ("", "", "", ""), "ENTD": ("", "", "", ""), "BARRI": ("", "", "", ""), "CV": ("", "", "", ""), "CH": ("", "", "", ""),
    "CRO": ("", "", "", "")}
SIN_DE = {"GV"}                                   # «Gran Vía Marqués del Turia», sin «de»
MENUDAS = {"DE", "DEL", "DELS", "LA", "LES", "EL", "ELS", "I", "Y", "A", "AL", "EN", "LOS", "LAS", "LO", "D'", "L'"}

# artículo que lleva el nombre detrás de «de»: primera palabra (sin tildes) → (es, va). Títulos y nombres comunes
# frecuentes en el callejero de València; si una palabra no está, va solo «de».
_M = ("el", "el"); _F = ("la", "la")
ARTICULO = {w: _M for w in (
    "DOCTOR PINTOR MAESTRO MESTRE PADRE PARE GENERAL MARQUES COMTE CONDE DUQUE DUC REINO REGNE PUERTO PORT CID PRIMADO "
    "PRIMAT ALCALDE CARDENAL POETA PROFESOR PROFESSOR MUSICO MUSIC ARQUITECTO ARQUITECTE INGENIERO ENGINYER ESCULTOR "
    "CAPITAN CAPITA ALMIRANTE ALMIRALL OBISPO BISBE ARZOBISPO ARQUEBISBE BOTANICO BOTANIC LITERATO LITERAT PERIODISTA "
    "ACTOR BARON BARO REY REI AYUNTAMIENTO AJUNTAMENT MERCADO MERCAT RIO RIU CATEDRATICO CATEDRATIC CRONISTA TENOR "
    "MEDICO METGE ESCRIPTOR ESCRITOR HISTORIADOR GRABADOR GRAVADOR ORGANISTA DRAMATURGO DRAMATURG COMPOSITOR "
    "MAESTRE SERRADOR CIRUJANO PLA LLANO INSTITUT INSTITUTO CONVENT CONVENTO").split()}
ARTICULO.update({w: _F for w in (
    "ALAMEDA ALBEREDA CONSTITUCION CONSTITUCIO PLATA PECHINA PETXINA JUSTICIA CIUDADELA CIUTADELLA MALVARROSA "
    "MALVA-ROSA PAZ PAU REINA UNIVERSIDAD UNIVERSITAT DOCTORA MAESTRA MESTRA PINTORA POETISA POETESSA VIRGEN "
    "SAFOR RIBERA ESTACION ESTACIO PORTA PUERTA SETMANA SEMANA ANTIGA ANTIGUA").split()})
ARTICULO.update({w: ("los", "els") for w in "HERMANOS GERMANS NARANJOS TARONGERS".split()})
ARTICULO.update({w: ("las", "les") for w in "TRES CORTES CORTS ISLAS ILLES GAVIOTAS GAVINES".split()})
ARTICULO["MAR"] = ("el", "la")

# tildes del castellano que el callejero no da (su traducción va sin tildes y el nombre oficial es valenciano)
TILDES_ES = {w.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U"): w for w in (
    "ARAGÓN ÁNGEL GUIMERÁ JOSÉ MARÍA RAMÓN JOAQUÍN TOMÁS NICOLÁS ANDRÉS PÉREZ GARCÍA MARTÍNEZ LÓPEZ GÓMEZ SÁNCHEZ "
    "FERNÁNDEZ RODRÍGUEZ GONZÁLEZ HERNÁNDEZ JIMÉNEZ GIMÉNEZ MARQUÉS COLÓN LEÓN IBÁÑEZ GALDÓS BOSCÁ CATÓLICO MÚSICO "
    "MÉDICO BOTÁNICO CAPITÁN JARDÍN PÍO JESÚS GUILLÉN RÍO ÁVILA ÁLVARO VÍCTOR SEBASTIÁN JULIÁN MARTÍN AGUSTÍN "
    "CRISTÓBAL FERMÍN VALENTÍN BARÓN CATEDRÁTICO TARANCÓN MENÉNDEZ PELÁEZ DÍAZ RUÍZ MARTÍ ROVIRÁ ÁFRICA AMÉRICA "
    "MÁRTIR MÚSICOS POLÍTICO TRÁNSITO CATÓLICA JERUSALÉN").split()}
TILDES_ES["IBANEZ"] = "IBÁÑEZ"; TILDES_ES["IBAÑEZ"] = "IBÁÑEZ"

# erratas del nombre oficial en el callejero (vias.json), corregidas solo al mostrarlas
CALLEJERO_FIX = {"PONT DE LA L'EXPOSICIO": "PONT DE L'EXPOSICIÓ", "FRANCISCO LOZANO 'PINTOR'": "FRANCISCO LOZANO (PINTOR)"}

LADO = {"N": ("norte", "nord"), "S": ("sur", "sud"), "E": ("este", "est"), "O": ("oeste", "oest"), "NE": ("noreste", "nord-est"),
        "NO": ("noroeste", "nord-oest"), "SE": ("sureste", "sud-est"), "SO": ("suroeste", "sud-oest")}
SUF = re.compile(r"\s*\((N|S|E|O|NE|NO|SE|SO)\)$")
NUM = re.compile(r"^(.*?)\s+(\d+\s?[A-Z]?(?:-\d+[A-Z]?)?|S/N)$")


def _st(w):
    return "".join(c for c in unicodedata.normalize("NFD", w) if unicodedata.category(c) != "Mn")


def _sin_tilde_salvo_enye(w):
    return "".join(c for c in unicodedata.normalize("NFD", w.replace("Ñ", "\0")) if unicodedata.category(c) != "Mn").replace("\0", "Ñ")


@functools.lru_cache(None)
def _callejero():
    """Traducción calle castellana → valenciana del callejero (solo las que no son ambiguas). No se toman tildes de otros
    nombres oficiales: el valenciano también usa la tilde aguda («Justícia») y daría tildes falsas en castellano."""
    vias = json.loads((ROOT / "data/raw/siniestros/vias.json").read_text())
    es_va, dup = {}, set()
    for v in vias:
        of, tr, tp = (v.get("nomoficial") or "").upper(), (v.get("traducnooficial") or "").upper(), v.get("codtipovia") or ""
        of = CALLEJERO_FIX.get(of, of)
        if of and tr:
            k = _st(f"{tp} {tr}")
            if k in es_va and es_va[k] != f"{tp} {of}": dup.add(k)
            es_va[k] = f"{tp} {of}"
    for k in dup: es_va.pop(k, None)
    return es_va


@functools.lru_cache(None)
def ambiguos():
    """Nombres de lugar con ficha (valenciano, sin sufijo) que se repiten: esos conservan el lado («(lado sur)»)."""
    import collections, sqlite3
    con = sqlite3.connect(ROOT / "data/processed/observatorio.sqlite")
    c = collections.Counter(SUF.sub("", n) for (n,) in con.execute("SELECT l.nom FROM ficha f JOIN lugar l ON l.uid = f.uid WHERE f.clase = 'lloc'"))
    return frozenset(k for k, v in c.items() if v > 1)


def tildes_es(es, va=None):
    """Castellano del callejero o del parte, en mayúsculas y sin tildes → con tildes."""
    of = {}
    if va:
        of = {_sin_tilde_salvo_enye(w): w for w in re.split(r"[\s()–]+", va)
              if w and not re.search("[ÀÈÒÏÇ·]", w) and not re.search(r"[ÍÚ][^AEIOU]*IA$", w)}

    def una(m):
        w = m.group(0)
        if re.search("[ÁÉÍÓÚ]", w): return w
        k = _sin_tilde_salvo_enye(w)
        if k in of and of[k] != w: return of[k]
        if k in TILDES_ES: return TILDES_ES[k]
        if re.fullmatch(r"[A-ZÑ]{3,}CION", k): return k[:-3] + "IÓN"
        return w
    return re.sub(r"[A-ZÁÉÍÓÚÑÜ]+", una, es)


def _limpia(raw):
    """«C/ FRANCISCO LOZANO (PINTOR).CARRER DE 1» (el parte copia a veces la forma larga) → «C/ FRANCISCO LOZANO (PINTOR) 1»;
    y las erratas del callejero (CALLEJERO_FIX)."""
    t = re.sub(r"\)\.[A-ZÀ-Ú' ]+? DE(?=\s|$)", ")", raw.strip())
    for a, b in CALLEJERO_FIX.items(): t = t.replace(a, b)
    return t


def _palabras(resto):
    pal = []
    ws = [w for w in resto.split(" ") if w]
    for k, w in enumerate(ws):
        if k and k < len(ws) - 1 and w in ("I", "Y"): pal.append(w.lower()); continue   # «Arts i Oficis», pero «Jaume I»
        if re.fullmatch(r"[IVXLC]+|[A-Z]?\d+[A-Z]?(?:-\d+[A-Z]?)?|S/N|CV-\d+", w): pal.append(w); continue
        m = re.match(r"^([LD])'(.*)$", w)
        if m: pal.append(m.group(1).lower() + "'" + m.group(2)[:1] + m.group(2)[1:].lower()); continue
        if re.fullmatch(r"(?:[A-ZÀ-Ú]\.)+", w): pal.append(" ".join(x + "." for x in w.split(".") if x)); continue
        low = w.lower()
        pal.append(low if (k and w in MENUDAS) else "-".join(x[:1].upper() + x[1:] for x in low.split("-")))
    return " ".join(pal)


def _vocal(s):
    return bool(re.match(r"[aeiouàèéíòóúhAEIOUÀÈÉÍÒÓÚH]", _st(s)[:1] if s else ""))


def via(raw, l, art=False):
    """Una calle (con número de portal, si lo lleva): «AV PUERTO 12» → «Avenida del Puerto, 12». raw en la lengua l (el
    castellano ya con tildes). art=True: con artículo delante del tipo («la avenida», «l'avinguda»), para «entre … y …»."""
    t = _limpia(raw)
    num = ""
    m = NUM.match(t)
    if m: t, num = m.group(1), m.group(2).replace(" ", "")
    tipo, _, resto = t.partition(" ")
    if tipo not in TIPO: tipo, resto = "", t
    m = re.match(r"^(.*?) \(([^()]+)\)$", resto)                     # «FRANCISCO LOZANO (PINTOR)» → «PINTOR FRANCISCO LOZANO»
    if m and not SUF.search(resto): resto = f"{m.group(2)} {m.group(1)}"
    es = l == "es"
    nom = _palabras(resto)
    tp = TIPO[tipo][0 if es else 1] if tipo else ""
    if tp:
        if tipo in SIN_DE:
            cuerpo = f"{tp} {nom}"
        else:
            p0 = _st(resto.split(" ")[0]) if resto else ""
            if p0 in ("EL", "LA", "LOS", "LAS", "ELS", "LES") and " " in nom:   # el nombre ya lleva artículo
                a, nom = p0.lower(), nom.split(" ", 1)[1]
            elif p0.startswith("L'"):
                a, nom = "l'", nom[2:]
            else:
                a = ARTICULO.get(p0, ("", ""))[0 if es else 1]
            if es:
                cuerpo = f"{tp} " + ("del " if a == "el" else f"de {a} " if a else "de ") + nom
            else:
                if a == "el": pre = "de l'" if _vocal(nom) else "del "
                elif a == "la": pre = "de l'" if _vocal(nom) and not nom.lower().startswith(("i", "u", "hi", "hu")) else "de la "
                elif a == "l'": pre = "de l'"
                elif a == "els": pre = "dels "
                elif a: pre = f"de {a} "
                else: pre = "d'" if _vocal(nom) else "de "
                cuerpo = f"{tp} {pre}{nom}"
        if art:
            g = TIPO[tipo][2 if es else 3]
            cuerpo = ((("el " if g == "m" else "la ") if es else ("l'" if _vocal(tp) else "el " if g == "m" else "la ")) + cuerpo)
    else:
        cuerpo = nom
    return cuerpo + (f", {num}" if num else "")


def cap(s):
    return s[:1].upper() + s[1:] if s else s


def minus(s):
    """Para dentro de una frase: «Paseo de la Alameda…» → «paseo de la Alameda…» (no toca «Gran Vía» ni nombres propios)."""
    p = s.split(" ", 1)[0].lower()
    tipos = {x for v in TIPO.values() for x in v[:2] if x and not x.startswith("Gran")}
    return (s[:1].lower() + s[1:]) if p in tipos else s


def con_articulo(s, l):
    """Dentro de una frase, con el artículo del tipo de vía: «Avenida de Aragón» → «la avenida de Aragón»,
    «Avinguda d'Aragó» → «l'avinguda d'Aragó». Sin tipo de vía, igual."""
    p = s.split(" ", 1)[0].lower()
    for es_, va_, ge, gv in TIPO.values():
        if not es_ or es_.startswith("Gran"): continue
        if l == "es" and p == es_: return ("el " if ge == "m" else "la ") + minus(s)
        if l == "va" and p == va_: return ("l'" if _vocal(va_) else "el " if gv == "m" else "la ") + minus(s)
    if s.startswith("Gran V"): return "la " + s
    return s


def _nombre(raw, l):
    """Nombre de lugar o dirección ya en la lengua l (y con tildes): cruces, tramos y portales."""
    con, y = (" con ", " y ") if l == "es" else (" amb ", " i ")
    m = re.match(r"^(.*?) \((.*) – (.*)\)$", raw)
    if m:
        a, b = via(m.group(2), l, art=True), via(m.group(3), l, art=True)
        ent = "entre " + a + y + b if l == "es" else "entre " + a + y + b
        return cap(via(m.group(1), l)) + ", " + ent
    partes = [p for p in raw.split(" cruce ") if p.strip()]
    if not partes: return raw
    out = cap(via(partes[0], l))
    if len(partes) > 1:
        resto = [via(p, l) for p in partes[1:]]
        out += con + (", ".join(resto[:-1]) + y + resto[-1] if len(resto) > 1 else resto[0])
    return out


def lugar(nom_va, nom_es, l, amb=None):
    """Nombre visible de un lugar (nombres_lugares.csv: nom, nom_es). amb: nombres (va, sin sufijo) repetidos; por
    defecto, los de nombres_lugares.csv."""
    amb = ambiguos() if amb is None else amb
    m = SUF.search(nom_va or "")
    base_va = SUF.sub("", nom_va or "")
    if l == "es":
        base = SUF.sub("", tildes_es(nom_es or nom_va, nom_va))
    else:
        base = base_va
    n = _nombre(base, l)
    if m and base_va in amb:
        n += f" ({'lado' if l == 'es' else 'costat'} {LADO[m.group(1)][0 if l == 'es' else 1]})"
    return n


def calle(nom_va, nom_es, tipo, l):
    """Nombre visible de una calle (vias.json: codtipovia, nomoficial, traducnooficial)."""
    raw = f"{tipo} {nom_va}" if l == "va" else f"{tipo} {tildes_es(nom_es or nom_va, nom_va)}"
    return cap(via(raw.strip(), l))


def direccion(raw_es, l):
    """Una dirección del parte (castellano, sin tildes: «AV PUERTO cruce PL ZARAGOZA», «C/ JUSTICIA 8») en la lengua l.
    Al valenciano, cada calle con la traducción del callejero; si no está, queda en castellano."""
    raw_es = _limpia(SUF.sub("", raw_es))
    if l == "es":
        return _nombre(tildes_es(raw_es), "es")
    es_va = _callejero()

    def tr(p):
        p = p.strip(); num = ""
        m = NUM.match(p)
        if m: p, num = m.group(1), " " + m.group(2)
        return es_va.get(_st(p), tildes_es(p)) + num
    m = re.match(r"^(.*?) \((.*) – (.*)\)$", raw_es)
    if m: return _nombre(f"{tr(m.group(1))} ({tr(m.group(2))} – {tr(m.group(3))})", "va")
    return _nombre(" cruce ".join(tr(p) for p in raw_es.split(" cruce ")), "va")


def clave(nom):
    """Clave para ordenar y para la letra del índice: el nombre propio, sin tipo, «de», artículo ni tildes."""
    x = nom
    tipos = sorted({v for t in TIPO.values() for v in t[:2] if v}, key=len, reverse=True)
    for t in tipos:
        if x.lower().startswith(t.lower() + " "): x = x[len(t) + 1:]; break
    x = re.sub(r"^(de les |de los |de las |de la |de l'|dels |del |de |d')", "", x, flags=re.I)
    return _st(x).lower()


if __name__ == "__main__":                       # prueba rápida
    for va, es in [("PG ALBEREDA cruce PL SARAGOSSA (S)", "PG ALAMEDA cruce PL ZARAGOZA (S)"),
                   ("AV REGNE DE VALÈNCIA cruce C/ ALCALDE REIG", "AV REGNE DE VALENCIA cruce C/ ALCALDE REIG"),
                   ("C/ ACTOR LLORENS (AV PORT – C/ ARTS I DELS OFICIS)", "C/ ACTOR LLORENS (AV PUERTO – C/ ARTES Y OFICIOS)"),
                   ("AV BLASCO IBÁÑEZ 19-21", "AV BLASCO IBAÑEZ 19-21"), ("PL MANUEL SANCHIS GUARNER", "PL MANUEL SANCHIS GUARNER"),
                   ("GV FERRAN EL CATÒLIC cruce C/ ÀNGEL GUIMERÀ", "GV FERNANDO EL CATOLICO cruce C/ ANGEL GUIMERA")]:
        print(lugar(va, es, "va"), "|", lugar(va, es, "es"))
    for d in ["PG ALAMEDA cruce PL ZARAGOZA", "C/ JUSTICIA 8", "LLOC PUENTE DE LA EXPOSICION cruce PG CIUDADELA",
              "C/ FRANCISCO LOZANO (PINTOR).CARRER DE 1", "AV ARAGON cruce C/ EDUARDO BOSCA", "AV TRES CRUCES 105"]:
        print(direccion(d, "va"), "|", direccion(d, "es"))
    print(calle("ARAGÓ", "ARAGON", "AV", "va"), "|", calle("ARAGÓ", "ARAGON", "AV", "es"))
