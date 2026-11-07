"""Secciones estáticas nuevas de la página «Dades i mètode / Datos y método» de la web nueva (boceto los bocetos de diseño (internos)).

Las secciones del método de siempre (web/proto/metode.plantilla.html: datos, contar, meta, uso, lugares, normal, plan, gravedad,
limites, errores, revisiones, futuro) las pinta su propio JS debajo de estas; aquí solo va lo nuevo, en valenciano (AVL) y en
castellano, en lenguaje llano. Ninguna cifra escrita a mano: todas salen de cifras() (SQLite y web/proto/datos/*.js).

Interfaz (la usa el constructor de la web):
    cifras(con, O, R, P, M) -> dict      con = sqlite3 de data/processed/observatorio.sqlite; O, R, P, M = observatori, relato,
                                          pla y metode (web/proto/datos/*.js)
    secciones(c, L) -> [(id, {"va": título, "es": título}, html)]   html en la lengua L ("va" o "es")
Los enlaces internos llevan el marcador literal {RAIZ} (lo sustituye el constructor por la ruta relativa a la raíz).
Solo biblioteca estándar."""
import html

ESC = html.escape


def mil(n):
    """Entero con punto de miles (las dos lenguas)."""
    return f"{int(round(n)):,}".replace(",", ".")


def pc(x, d=1):
    """Proporción (0-1) en porcentaje con coma decimal: 0,9667 -> «96,7 %»."""
    return f"{x * 100:.{d}f}".replace(".", ",") + " %"


def fecha(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if iso else ""


def cifras(con, O, R, P, M):
    q = lambda sql: con.execute(sql).fetchone()
    meta = dict(con.execute("SELECT clave, valor FROM meta").fetchall())
    años = [int(a) for a in meta["años"].split(",")]
    fichas = dict(con.execute("SELECT clase, COUNT(*) FROM ficha GROUP BY clase").fetchall())
    # asignación a calles: siniestros con bici o VMP del análisis, por la dirección escrita
    n, partes, res, amb, sinvia, todas = q("""
        SELECT COUNT(*), SUM(d.partes), SUM(d.resueltas), SUM(d.ambiguas), SUM(d.sin_via), SUM(d.resueltas = d.partes)
        FROM siniestro_direccion d JOIN siniestro_bv b ON b.siniestro_id = d.siniestro_id
        JOIN siniestro s ON s.id = b.siniestro_id WHERE s.en_analisis = 1""")
    por_dist = q("""SELECT COUNT(*) FROM siniestro_via sv JOIN siniestro_bv b ON b.siniestro_id = sv.siniestro_id
                    WHERE sv.resuelta = 'por_distancia'""")[0]
    n_calles = q("SELECT COUNT(DISTINCT codvia) FROM v_calle_bv")[0]
    cob = O["kpi"]["cob_any"]
    a_cob = sorted(cob)
    plan = q("SELECT COUNT(*), SUM(estado = 'hecha'), SUM(estado = 'en_marcha'), SUM(estado = 'anunciada'), SUM(estado = 'sin_info') FROM plan_actuacion WHERE clase = 'medida'")   # sin el indicador 3.2.2 (07/11/2026)
    n_fuentes = q("SELECT COUNT(*) FROM plan_fuente")[0]
    tipos_cons = sum(1 for t in P["tipos"] if t.get("consultada"))
    n_cambios = q("SELECT COUNT(*) FROM cambio")[0]
    tablas = q("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE '\\_%' ESCAPE '\\'")[0]
    return {
        "a0": años[0], "a1": años[-1], "umbral": int(meta["min_ficha"]), "version": meta["version_web"],
        "esquema": meta["esquema"], "descarga": meta["fecha_descarga"], "conjunto": meta["conjunto_siniestros"],
        "f_lloc": fichas.get("lloc", 0), "f_carrer": fichas.get("carrer", 0),
        "n_bv": n, "partes": partes, "resueltas": res, "ambiguas": amb, "sin_via": sinvia, "todas": todas,
        "cob_calles": todas / n, "por_dist": por_dist, "n_calles": n_calles,
        "turia": M["tur"]["n"], "n_geo": O["cob"]["geo"], "n_total": O["cob"]["total"],
        "cob_a0": a_cob[0], "cob_a1": a_cob[-1], "cob_v0": cob[a_cob[0]], "cob_v1": cob[a_cob[-1]],
        "n_uso": len(O["uso"]), "n_top": len(O["negros"]) - 1,
        "plan_n": plan[0], "plan_hecha": plan[1], "plan_marcha": plan[2], "plan_anun": plan[3], "plan_sin": plan[4],
        "plan_rev": P["rev"]["ult"], "plan_prox": P["rev"]["prox"], "plan_aprob": P["plan_doc"]["aprob"],
        "n_fuentes": n_fuentes, "tipos_cons": tipos_cons, "n_tipos": len(P["tipos"]),
        "n_cambios": n_cambios, "tablas": tablas,
    }


def secciones(c, L):
    T = lambda va, es: va if L == "va" else es
    a0, a1 = c["a0"], c["a1"]
    out = []
    from sitio import REPO, TELEGRAM_CANAL, CORREU
    git = T(f'<a href="{REPO}" rel="noopener">codi font a GitHub</a>', f'<a href="{REPO}" rel="noopener">código fuente en GitHub</a>')

    # ---------------------------------------------------------------- en cinco líneas
    out.append(("resum", {"va": "En cinc línies", "es": "En cinco líneas"}, T(
        f"""<ol class="cinco">
<li>Partim del conjunt «Sinistres de trànsit» del portal de dades obertes de l'Ajuntament de València.</li>
<li>Ens quedem amb els {mil(c['n_total'])} accidents de {a0} a {a1} en què hi ha almenys una bici o un patinet.</li>
<li>El portal només dona l'adreça escrita. Amb el carrerer municipal en situem {mil(c['n_geo'])} en el mapa, el {pc(c['n_geo'] / c['n_total'], 0)}.</li>
<li>Agrupem els accidents per cruïlles (amb 30 metres al voltant) i per trams de carrer de fins a 150 metres.</li>
<li>En {mil(c['n_uso'])} punts del carril bici on es compten les bicis, comparem els accidents amb el nombre de bicis que hi passen.</li>
</ol>
<p>Tot el procés és obert i es pot repetir: {git}. Qui manté l'observatori, cada quant s'actualitza i què passaria si es parara ho expliquem en <a href="{{RAIZ}}sobre/#continuitat">la continuïtat de l'observatori</a>.</p>""",
        f"""<ol class="cinco">
<li>Partimos del conjunto «Siniestros de tráfico» del portal de datos abiertos del Ayuntamiento de València.</li>
<li>Nos quedamos con los {mil(c['n_total'])} accidentes de {a0} a {a1} en los que hay al menos una bici o un patinete.</li>
<li>El portal solo da la dirección escrita. Con el callejero municipal situamos {mil(c['n_geo'])} en el mapa, el {pc(c['n_geo'] / c['n_total'], 0)}.</li>
<li>Agrupamos los accidentes por cruces (con 30 metros alrededor) y por tramos de calle de hasta 150 metros.</li>
<li>En {mil(c['n_uso'])} puntos del carril bici donde se cuentan las bicis, comparamos los accidentes con el número de bicis que pasan.</li>
</ol>
<p>Todo el proceso es abierto y se puede repetir: {git}. Quién mantiene el observatorio, cada cuánto se actualiza y qué pasaría si se parase lo explicamos en <a href="{{RAIZ}}sobre/#continuitat">la continuidad del observatorio</a>.</p>""")))

    # ---------------------------------------------------------------- descarga
    out.append(("descarrega", {"va": "Descarrega les dades", "es": "Descarga los datos"}, T(
        f"""<p>Els accidents amb bici o patinet situats en el mapa, un per un, i com hem situat cadascun. És la nostra aportació principal.</p>
<div class="descarga">
<div class="tarjeta"><span class="fmt">Ja disponible</span><span>Des del <a href="{{RAIZ}}mapa/">mapa</a>, amb el botó «Descarrega el que veus (CSV en ZIP)»: es descarrega un ZIP amb un CSV dels accidents situats en el mapa (un per fila), els 30 llocs o els punts de comptatge, amb els filtres que tingues posats, un fitxer LLEGIU-ME amb la font, la llicència i les columnes, i el descriptor <code>datapackage.json</code>. Les columnes tenen sempre el mateix nom, en qualsevol llengua.</span><a class="btn" href="{{RAIZ}}mapa/#vista=pts">Obri el mapa per a descarregar</a></div>
<div class="tarjeta"><span class="fmt">CSV i GeoJSON</span><span>El conjunt complet i versionat, amb com hem situat cada accident i un diccionari de camps. Encara no està publicat.</span><span class="pendiente">Pròximament</span></div>
</div>
<p class="nota">Cada versió anirà datada. Llicència CC BY 4.0, la mateixa que les dades del portal. Sense dades de les persones implicades. Està prohibit reidentificar persones creuant aquestes dades amb altres fonts.</p>
<p class="nota">El CSV del mapa porta la data i l'hora, l'adreça i els factors de cada accident, que ja publica el portal de l'Ajuntament, i les coordenades que n'hem tret. Les fitxes de lloc i de carrer, en canvi, només donen el mes i l'any, perquè ixen en els cercadors amb el nom del lloc. La coordenada és la de la cruïlla o la del número de portal citat en el comunicat, no un domicili. Si un registre t'afecta i vols que el revisem, escriu-nos a <a href="mailto:hola@observatoribicivlc.org">hola@observatoribicivlc.org</a>; i si l'Ajuntament retira o corregix un registre, nosaltres també.</p>
<p class="nota">El descriptor <code>datapackage.json</code> seguix l'estàndard obert Frictionless Data Package: diu què vol dir cada columna, de quin tipus és i en quines unitats va, i també la llicència, les fonts i la versió. Així un programa pot llegir i validar el CSV sense endevinar res. El pots consultar abans de descarregar: <a href="{{RAIZ}}dades/datapackage.json">descriptor de les dades (datapackage.json)</a>. El codi que el genera és públic: {git}.</p>
<p class="cita"><b>Com citar-ho:</b> Observatori de la bici i el patinet de València ({c['version'][:4]}). Accidents de bici i patinet a València, {a0}-{a1}, situats en el mapa. Dades de l'Ajuntament de València (CC BY 4.0), modificades per l'observatori.</p>""",
        f"""<p>Los accidentes con bici o patinete situados en el mapa, uno a uno, y cómo hemos situado cada uno. Es nuestra principal aportación.</p>
<div class="descarga">
<div class="tarjeta"><span class="fmt">Ya disponible</span><span>Desde el <a href="{{RAIZ}}mapa/">mapa</a>, con el botón «Descarga lo que ves (CSV en ZIP)»: se descarga un ZIP con un CSV de los accidentes situados en el mapa (uno por fila), los 30 lugares o los puntos de conteo, con los filtros que tengas puestos, un fichero LEEME con la fuente, la licencia y las columnas, y el descriptor <code>datapackage.json</code>. Las columnas tienen siempre el mismo nombre, en cualquier lengua.</span><a class="btn" href="{{RAIZ}}mapa/#vista=pts">Abrir el mapa para descargar</a></div>
<div class="tarjeta"><span class="fmt">CSV y GeoJSON</span><span>El conjunto completo y versionado, con cómo hemos situado cada accidente y un diccionario de campos. Todavía no está publicado.</span><span class="pendiente">Próximamente</span></div>
</div>
<p class="nota">Cada versión irá fechada. Licencia CC BY 4.0, la misma que los datos del portal. Sin datos de las personas implicadas. Está prohibido reidentificar personas cruzando estos datos con otras fuentes.</p>
<p class="nota">El CSV del mapa lleva la fecha y la hora, la dirección y los factores de cada accidente, que ya publica el portal del Ayuntamiento, y las coordenadas que hemos sacado de ella. Las fichas de lugar y de calle, en cambio, solo dan el mes y el año, porque aparecen en los buscadores con el nombre del sitio. La coordenada es la del cruce o la del número de portal citado en el parte, no un domicilio. Si un registro te afecta y quieres que lo revisemos, escríbenos a <a href="mailto:hola@observatoribicivlc.org">hola@observatoribicivlc.org</a>; y si el Ayuntamiento retira o corrige un registro, nosotros también.</p>


<p class="nota">El descriptor <code>datapackage.json</code> sigue el estándar abierto Frictionless Data Package: dice qué significa cada columna, de qué tipo es y en qué unidades va, y también la licencia, las fuentes y la versión. Así un programa puede leer y validar el CSV sin adivinar nada. Puedes consultarlo antes de descargar: <a href="{{RAIZ}}dades/datapackage.json">descriptor de los datos (datapackage.json)</a>. El código que lo genera es público: {git}.</p>
<p class="cita"><b>Cómo citarlo:</b> Observatorio de la bici y el patinete de València ({c['version'][:4]}). Accidentes de bici y patinete en València, {a0}-{a1}, situados en el mapa. Datos del Ayuntamiento de València (CC BY 4.0), modificados por el observatorio.</p>""")))

    # ---------------------------------------------------------------- límites
    v0, v1 = round(c["cob_v0"] * 100), round(c["cob_v1"] * 100)
    out.append(("limits", {"va": "El que aquestes dades no permeten saber", "es": "Lo que estos datos no permiten saber"}, T(
        f"""<ul class="limites">
<li>Si un lloc és perillós: sense saber quanta gent hi passa, només veiem on s'acumulen els accidents.</li>
<li>Si el patinet té més accidents per viatge: cap comptador separa patinets i bicis.</li>
<li>Si els ferits greus pugen o baixen: des de 2023 es compta com a ferit greu qui passa més de 24 hores a l'hospital.</li>
<li>Com va ser l'accident (xoc lateral, abast, caiguda…) abans de {a1}: eixa dada només és fiable des d'aquell any. Amb qui xoquen sí que es pot veure des de {a0}, llevat de les persones que van a peu (vegeu la línia següent).</li>
<li>Si pugen o baixen els accidents de bici o patinet amb persones que van a peu: fins a mitjan 2024, en molts comunicats no hi consta la persona atropellada. Per això les xifres d'aquests xocs són un mínim.</li>
<li>Per què passen els accidents segons la policia (distracció, no respectar la prioritat…) abans de {a1}: fins a 2023, en un de cada tres comunicats no hi consta cap motiu. Per això les fitxes només en donen els de {a1}.</li>
<li>Quants accidents podem situar en el mapa canvia amb l'any: {v0} de cada 100 en {c['cob_a0']} i {v1} en {c['cob_a1']}. Per això les tendències només amb els accidents del mapa no són fiables, i el seguiment del Pla es fa amb tots.</li>
<li>Si el Pla funciona: les dades de {a1 + 1} encara no estan publicades.</li>
</ul>""",
        f"""<ul class="limites">
<li>Si un lugar es peligroso: sin saber cuánta gente pasa, solo vemos dónde se acumulan los accidentes.</li>
<li>Si el patinete tiene más accidentes por viaje: ningún contador separa patinetes y bicis.</li>
<li>Si los heridos graves suben o bajan: desde 2023 se cuenta como herido grave a quien pasa más de 24 horas en el hospital.</li>
<li>Cómo fue el accidente (choque lateral, alcance, caída…) antes de {a1}: ese dato solo es fiable desde ese año. Con quién chocan sí se puede ver desde {a0}, salvo las personas que van a pie (ver la línea siguiente).</li>
<li>Si suben o bajan los accidentes de bici o patinete con personas que van a pie: hasta mediados de 2024, en muchos partes no consta la persona atropellada. Por eso las cifras de estos choques son un mínimo.</li>
<li>Por qué ocurren los accidentes según la policía (distracción, no respetar la prioridad…) antes de {a1}: hasta 2023, en uno de cada tres partes no consta ningún motivo. Por eso las fichas solo dan los de {a1}.</li>
<li>Cuántos accidentes podemos situar en el mapa cambia con el año: {v0} de cada 100 en {c['cob_a0']} y {v1} en {c['cob_a1']}. Por eso las tendencias hechas solo con los accidentes del mapa no son fiables, y el seguimiento del Plan se hace con todos.</li>
<li>Si el Plan funciona: los datos de {a1 + 1} todavía no están publicados.</li>
</ul>""")))

    # ---------------------------------------------------------------- calles
    out.append(("carrers", {"va": "Com assignem un accident a un carrer", "es": "Cómo asignamos un accidente a una calle"}, T(
        f"""<p>Cada fitxa de carrer compta els accidents que la policia va anotar en eixe carrer. Ho fem amb l'<b>adreça escrita</b> del comunicat, no amb el punt del mapa. Així compten també els accidents que no hem pogut situar.</p>
<ul>
<li>Un accident en una <b>cruïlla</b> compta en els dos carrers. Per això, si sumes les fitxes de carrer, et donarà més accidents dels que hi ha.</li>
<li>Si l'adreça porta un número de portal o només el nom del carrer, compta en eixe carrer.</li>
<li>Si el nom coincideix amb més d'un carrer del carrerer, triem el més pròxim al punt de l'accident, a 50 metres com a màxim. Si l'accident no té punt, el deixem sense assignar.</li>
<li>El <b>Jardí del Túria</b> no és un carrer del carrerer: els seus {mil(c['turia'])} accidents tenen la seua zona en el mapa, però no fitxa de carrer. Tampoc tenen carrer les carreteres i alguns ponts escrits sense número.</li>
</ul>
<p>Resultat: el <b>{pc(c['cob_calles'])}</b> dels accidents amb bici o patinet tenen tots els seus carrers assignats ({mil(c['todas'])} de {mil(c['n_bv'])}).</p>
<details class="saber"><summary>Detall tècnic</summary><div>
<p>Un carrer és una via vigent del carrerer municipal. Usem la mateixa taula de noms de carrer que el programa que situa els accidents en el mapa (el geocodificador, <code>scripts/geocodificar.py</code>). De les {mil(c['partes'])} mencions de carrer en adreces d'accidents amb bici o patinet, {mil(c['resueltas'])} s'assignen, {mil(c['ambiguas'])} queden ambigües (sense punt per a desfer el dubte) i {mil(c['sin_via'])} no tenen via en el carrerer. {mil(c['por_dist'])} assignacions s'han resolt per distància. En total hi ha {mil(c['n_calles'])} carrers amb algun accident amb bici o patinet. Ho calcula <code>scripts/construir_sqlite.py</code>.</p>
</div></details>""",
        f"""<p>Cada ficha de calle cuenta los accidentes que la policía anotó en esa calle. Lo hacemos con la <b>dirección escrita</b> del parte, no con el punto del mapa. Así cuentan también los accidentes que no hemos podido situar.</p>
<ul>
<li>Un accidente en un <b>cruce</b> cuenta en las dos calles. Por eso, si sumas las fichas de calle, te saldrán más accidentes de los que hay.</li>
<li>Si la dirección lleva un número de portal o solo el nombre de la calle, cuenta en esa calle.</li>
<li>Si el nombre coincide con más de una calle del callejero, elegimos la más cercana al punto del accidente, a 50 metros como máximo. Si el accidente no tiene punto, lo dejamos sin asignar.</li>
<li>El <b>Jardín del Turia</b> no es una calle del callejero: sus {mil(c['turia'])} accidentes tienen su zona en el mapa, pero no ficha de calle. Tampoco tienen calle las carreteras y algunos puentes escritos sin número.</li>
</ul>
<p>Resultado: el <b>{pc(c['cob_calles'])}</b> de los accidentes con bici o patinete tienen todas sus calles asignadas ({mil(c['todas'])} de {mil(c['n_bv'])}).</p>
<details class="saber"><summary>Detalle técnico</summary><div>
<p>Una calle es una vía vigente del callejero municipal. Usamos la misma tabla de nombres de calle que el programa que sitúa los accidentes en el mapa (el geocodificador, <code>scripts/geocodificar.py</code>). De las {mil(c['partes'])} menciones de calle en direcciones de accidentes con bici o patinete, {mil(c['resueltas'])} se asignan, {mil(c['ambiguas'])} quedan ambiguas (sin punto para deshacer la duda) y {mil(c['sin_via'])} no tienen vía en el callejero. {mil(c['por_dist'])} asignaciones se han resuelto por distancia. En total hay {mil(c['n_calles'])} calles con algún accidente con bici o patinete. Lo calcula <code>scripts/construir_sqlite.py</code>.</p>
</div></details>""")))

    # ---------------------------------------------------------------- fichas
    u = c["umbral"]
    out.append(("fitxes", {"va": "Les fitxes de lloc i de carrer", "es": "Las fichas de lugar y de calle"}, T(
        f"""<p>Hi ha {mil(c['f_lloc'])} <a href="{{RAIZ}}lloc/">fitxes de lloc</a> (cruïlles i trams de carrer) i {mil(c['f_carrer'])} <a href="{{RAIZ}}carrer/">fitxes de carrer</a>.</p>
<ul>
<li><b>Només amb {u} accidents o més</b> de {a0} a {a1}. Amb menys, la pàgina parlaria d'un o dos accidents concrets i no diria res del lloc; a més, com que les fitxes ixen en els cercadors amb el nom del lloc, ajudaria a trobar un accident concret. {u} és el llindar habitual per a no publicar recomptes amb molt pocs casos.</li>
<li><b>Privacitat.</b> La llista d'accidents, un per un, porta el mes i l'any, sense dia ni hora; els vehicles; la cruïlla o el número del portal citat en el comunicat, que no és un domicili; i la gravetat. Els factors (prioritat, distracció…) només es donen en conjunt, mai accident per accident.</li>
<li><b>Les fitxes no desapareixen.</b> Una fitxa publicada es manté encara que en un any nou baixe de {u} accidents, perquè no es trenquen els enllaços.</li>
<li><b>Adreces estables.</b> L'adreça de cada fitxa no canvia i no es reutilitza per a un altre lloc, encara que en canviem el nom.</li>
<li>Cada fitxa usa el nom oficial del carrerer en cada llengua.</li>
</ul>""",
        f"""<p>Hay {mil(c['f_lloc'])} <a href="{{RAIZ}}lloc/">fichas de lugar</a> (cruces y tramos de calle) y {mil(c['f_carrer'])} <a href="{{RAIZ}}carrer/">fichas de calle</a>.</p>
<ul>
<li><b>Solo con {u} accidentes o más</b> de {a0} a {a1}. Con menos, la página hablaría de uno o dos accidentes concretos y no diría nada del lugar; además, como las fichas aparecen en los buscadores con el nombre del sitio, ayudaría a dar con un accidente concreto. {u} es el umbral habitual para no publicar recuentos con muy pocos casos.</li>
<li><b>Privacidad.</b> La lista de accidentes, uno a uno, lleva el mes y el año, sin día ni hora; los vehículos; el cruce o el número del portal citado en el parte, que no es un domicilio; y la gravedad. Los factores (prioridad, distracción…) solo se dan en conjunto, nunca accidente por accidente.</li>
<li><b>Las fichas no desaparecen.</b> Una ficha publicada se mantiene aunque en un año nuevo baje de {u} accidentes, para no romper los enlaces.</li>
<li><b>Direcciones estables.</b> La dirección de cada ficha no cambia y no se reutiliza para otro lugar, aunque cambiemos su nombre.</li>
<li>Cada ficha usa el nombre oficial del callejero en cada lengua.</li>
</ul>""")))

    # ---------------------------------------------------------------- filtros
    out.append(("filtres", {"va": "Els filtres del mapa", "es": "Los filtros del mapa"}, T(
        f"""<p>En el <a href="{{RAIZ}}mapa/">mapa</a> pots triar els anys, el vehicle i la gravetat. Canvien el que es veu, però no tot:</p>
<ul>
<li><b>Els llocs i el seu lloc en la llista es trien amb tots els accidents</b> de {a0} a {a1}. El filtre canvia les xifres de cada lloc, però no quins llocs hi ha ni en quin ordre.</li>
<li>La vista <b>«Segons el trànsit»</b> no es filtra: el càlcul que compara amb el trànsit usa tots els anys junts.</li>
<li>La <b>gravetat no es pot comparar entre anys</b>: des de 2023 es compta com a ferit greu qui passa més de 24 hores a l'hospital, i al juliol de 2024 la Policia Local va canviar el seu sistema de registre. El mapa ho avisa quan filtres per gravetat.</li>
<li><b>«Descarrega el que veus (CSV)»</b> baixa justament el que es veu, amb la vista i els filtres posats, la font, la llicència i l'avís de no reidentificar persones.</li>
</ul>""",
        f"""<p>En el <a href="{{RAIZ}}mapa/">mapa</a> puedes elegir los años, el vehículo y la gravedad. Cambian lo que se ve, pero no todo:</p>
<ul>
<li><b>Los lugares y su puesto en la lista se eligen con todos los accidentes</b> de {a0} a {a1}. El filtro cambia las cifras de cada lugar, pero no qué lugares hay ni en qué orden.</li>
<li>La vista <b>«Según el tráfico»</b> no se filtra: el cálculo que compara con el tráfico usa todos los años juntos.</li>
<li>La <b>gravedad no se puede comparar entre años</b>: desde 2023 se cuenta como herido grave a quien pasa más de 24 horas en el hospital, y en julio de 2024 la Policía Local cambió su sistema de registro. El mapa lo avisa cuando filtras por gravedad.</li>
<li><b>«Descarga lo que ves (CSV)»</b> baja justo lo que se ve, con la vista y los filtros puestos, la fuente, la licencia y el aviso de no reidentificar personas.</li>
</ul>""")))

    # ---------------------------------------------------------------- base de datos
    out.append(("base", {"va": "Una sola base de dades", "es": "Una sola base de datos"}, T(
        f"""<p>Tot el que publica la web surt d'<b>una sola base de dades</b>: els accidents, els carrers, els llocs, les fitxes, el seguiment del Pla i el registre de canvis. Així, una xifra és la mateixa en totes les pàgines.</p>
<ul>
<li>La base té <b>regles d'integritat</b>: cada accident apunta a carrers i llocs que existeixen, les dates tenen un format fix, els estats de les mesures només poden ser els quatre previstos i una mesura amb estat ha de tindre font i data.</li>
<li>Porta <b>versió</b> (la de la web, {fecha(c['version'])}) i la data en què vam obtindre les dades del portal ({fecha(c['descarga'])}).</li>
<li>Els fitxers CSV que fem servir es <b>tornen a generar idèntics</b> des de la base, i ho comprovem cada vegada que es construeix la web.</li>
</ul>
<details class="saber"><summary>Detall tècnic</summary><div>
<p>SQLite (<code>data/processed/observatorio.sqlite</code>, esquema {ESC(str(c['esquema']))}, {mil(c['tablas'])} taules), construïda per <code>scripts/construir_sqlite.py</code> sense refer l'anàlisi. Claus foranes actives i comprovades; restriccions CHECK en dates, gravetat, mètode i estats. Dues execucions donen el mateix fitxer. <code>make comprobar</code> verifica la integritat i que les exportacions són idèntiques als CSV.</p>
</div></details>""",
        f"""<p>Todo lo que publica la web sale de <b>una sola base de datos</b>: los accidentes, las calles, los lugares, las fichas, el seguimiento del Plan y el registro de cambios. Así, una cifra es la misma en todas las páginas.</p>
<ul>
<li>La base tiene <b>reglas de integridad</b>: cada accidente apunta a calles y lugares que existen, las fechas tienen un formato fijo, los estados de las medidas solo pueden ser los cuatro previstos y una medida con estado tiene que tener fuente y fecha.</li>
<li>Lleva <b>versión</b> (la de la web, {fecha(c['version'])}) y la fecha en que obtuvimos los datos del portal ({fecha(c['descarga'])}).</li>
<li>Los ficheros CSV que usamos se <b>vuelven a generar idénticos</b> desde la base, y lo comprobamos cada vez que se construye la web.</li>
</ul>
<details class="saber"><summary>Detalle técnico</summary><div>
<p>SQLite (<code>data/processed/observatorio.sqlite</code>, esquema {ESC(str(c['esquema']))}, {mil(c['tablas'])} tablas), construida por <code>scripts/construir_sqlite.py</code> sin rehacer el análisis. Claves foráneas activas y comprobadas; restricciones CHECK en fechas, gravedad, método y estados. Dos ejecuciones dan el mismo fichero. <code>make comprobar</code> verifica la integridad y que las exportaciones son idénticas a los CSV.</p>
</div></details>""")))

    # ---------------------------------------------------------------- seguimiento del Plan
    out.append(("seguiment", {"va": "Com seguim les mesures de l'Ajuntament", "es": "Cómo seguimos las medidas del Ayuntamiento"}, T(
        f"""<p>En la pàgina <a href="{{RAIZ}}ajuntament/">«Què està fent l'Ajuntament?»</a> seguim {mil(c['plan_n'])} mesures relacionades amb la bici i el patinet. <b>La selecció és nostra</b>: quasi totes són del Pla Director de Seguretat Viària 2026-2030 (aprovat el {fecha(c['plan_aprob'])}); algunes són obres municipals que no hi figuren, i ho diem en cadascuna.</p>
<p>Cada mesura té un d'aquests estats:</p>
<ul>
<li><b>Feta</b>: acabada o en servei.</li>
<li><b>En marxa</b>: contracte adjudicat, obra començada o servei que ja funciona en part.</li>
<li><b>Anunciada</b>: hi ha un compromís públic concret, però encara no hi ha obra ni contracte adjudicat (una licitació aprovada i sense adjudicar compta com a anunciada).</li>
<li><b>Sense informació pública trobada</b>: no hem trobat res publicat. No vol dir que no s'estiga fent.</li>
</ul>
<ul>
<li><b>Sense font no hi ha estat.</b> Cada estat porta la font que el justifica. Si la prova és dubtosa, triem l'estat més baix.</li>
<li>Hi ha <b>dues dates</b>: la de la font (quan es va publicar la prova) i la de la nostra comprovació (quan la vam mirar).</li>
<li>El que és anterior a l'aprovació del Pla només compta si continua funcionant o si l'Ajuntament mateix ho emmarca en el Pla.</li>
<li><b>Revisió cada tres mesos, amb revisió humana</b> abans de publicar res. L'última, el {fecha(c['plan_rev'])}; la pròxima, cap al {fecha(c['plan_prox'])}. Hem citat {mil(c['n_fuentes'])} fonts i consultem {mil(c['tipos_cons'])} dels {mil(c['n_tipos'])} tipus de font previstos.</li>
</ul>
<p class="nota">L'objectiu de reduir a la meitat els accidents amb bici o patinet per a 2030 és l'indicador de l'acció 3.2.2 del Pla, sense línia de partida. No és la meta global del Pla, que és reduir les persones mortes i ferides greus. No el comptem com una mesura més: el seguim amb les dades en l'<a href="{{RAIZ}}informe/2025/">Informe 2025</a>.</p>""",
        f"""<p>En la página <a href="{{RAIZ}}ajuntament/">«¿Qué está haciendo el Ayuntamiento?»</a> seguimos {mil(c['plan_n'])} medidas relacionadas con la bici y el patinete. <b>La selección es nuestra</b>: casi todas son del Plan Director de Seguridad Vial 2026-2030 (aprobado el {fecha(c['plan_aprob'])}); algunas son obras municipales que no figuran en él, y lo decimos en cada una.</p>
<p>Cada medida tiene uno de estos estados:</p>
<ul>
<li><b>Hecha</b>: terminada o en servicio.</li>
<li><b>En marcha</b>: contrato adjudicado, obra empezada o servicio que ya funciona en parte.</li>
<li><b>Anunciada</b>: hay un compromiso público concreto, pero todavía no hay obra ni contrato adjudicado (una licitación aprobada y sin adjudicar cuenta como anunciada).</li>
<li><b>Sin información pública encontrada</b>: no hemos encontrado nada publicado. No quiere decir que no se esté haciendo.</li>
</ul>
<ul>
<li><b>Sin fuente no hay estado.</b> Cada estado lleva la fuente que lo justifica. Si la prueba es dudosa, elegimos el estado más bajo.</li>
<li>Hay <b>dos fechas</b>: la de la fuente (cuándo se publicó la prueba) y la de nuestra comprobación (cuándo la miramos).</li>
<li>Lo anterior a la aprobación del Plan solo cuenta si sigue funcionando o si el propio Ayuntamiento lo enmarca en el Plan.</li>
<li><b>Revisión cada tres meses, con revisión humana</b> antes de publicar nada. La última, el {fecha(c['plan_rev'])}; la próxima, hacia el {fecha(c['plan_prox'])}. Hemos citado {mil(c['n_fuentes'])} fuentes y consultamos {mil(c['tipos_cons'])} de los {mil(c['n_tipos'])} tipos de fuente previstos.</li>
</ul>
<p class="nota">El objetivo de reducir a la mitad los accidentes con bici o patinete para 2030 es el indicador de la acción 3.2.2 del Plan, sin línea de partida. No es la meta global del Plan, que es reducir las personas fallecidas y heridas graves. No lo contamos como una medida más: lo seguimos con los datos en el <a href="{{RAIZ}}informe/2025/">Informe 2025</a>.</p>""")))

    # ---------------------------------------------------------------- informes anuales
    out.append(("informes", {"va": "Els informes anuals", "es": "Los informes anuales"}, T(
        f"""<p>Cada any publicarem un informe amb el nom de l'any de les dades: l'<a href="{{RAIZ}}informe/2025/">Informe 2025</a> és el primer i, de moment, l'únic.</p>
<ul>
<li>Cada edició té una <b>adreça fixa</b> (/informe/2025/, /informe/2026/…) i queda <b>congelada</b>: no canvia encara que després canvien les dades o el mètode.</li>
<li>Si hi trobem una errada, la corregim amb una <b>nota datada</b> dins de l'edició i una entrada en el registre de canvis. Mai la reescrivim en silenci.</li>
<li>Totes les edicions tindran les mateixes seccions, perquè es puguen comparar any a any.</li>
<li>L'informe de {a1 + 1} serà el primer que podrà dir si els accidents baixen al ritme que demana l'indicador del Pla.</li>
</ul>""",
        f"""<p>Cada año publicaremos un informe con el nombre del año de los datos: el <a href="{{RAIZ}}informe/2025/">Informe 2025</a> es el primero y, de momento, el único.</p>
<ul>
<li>Cada edición tiene una <b>dirección fija</b> (/informe/2025/, /informe/2026/…) y queda <b>congelada</b>: no cambia aunque luego cambien los datos o el método.</li>
<li>Si encontramos un error, lo corregimos con una <b>nota fechada</b> dentro de la edición y una entrada en el registro de cambios. Nunca lo reescribimos en silencio.</li>
<li>Todas las ediciones tendrán las mismas secciones, para que se puedan comparar año a año.</li>
<li>El informe de {a1 + 1} será el primero que podrá decir si los accidentes bajan al ritmo que pide el indicador del Plan.</li>
</ul>""")))

    # ---------------------------------------------------------------- código
    # ---------------------------------------------------------------- continuidad (07/11/2026, criterio 3 de las bases)
    out.append(("continuitat", {"va": "Continuïtat", "es": "Continuidad"}, T(
        f"""<p>L'observatori el manté una iniciativa ciutadana independent i sense ànim de lucre. No rep cap subvenció i no porta publicitat.</p>
<ul>
<li><b>Amb freqüència</b> revisem el seguiment de les mesures del Pla i comprovem si el portal de dades obertes ha publicat dades noves o ha canviat les que ja hi havia. Tan prompte com hi ha novetats en el Pla, en les dades o en la web, les publiquem ací i en el canal de Telegram.</li>
<li><b>Cada any</b>, quan l'Ajuntament publica els accidents de l'any sencer, actualitzem el mapa, les fitxes i el seguiment de l'objectiu, i traiem un informe nou.</li>
<li><b>Costa menys de 90 euros a l'any</b>: un servidor compartit de 5 euros al mes i els dominis. Ho paguem nosaltres.</li>
<li><b>Si un dia el deixem de mantindre, no es perd res.</b> Tot el codi i les dades derivades són públics amb llicències obertes ({git}), i la web sencera es torna a construir amb una sola ordre (<code>make</code>) a partir de les dades del portal. Qualsevol persona o entitat pot continuar-lo o fer-ne un d'igual en una altra ciutat.</li>
<li>Cada canvi en les dades, el mètode o la web queda apuntat, amb la data, en el <a href="#canvis">registre de canvis</a>.</li>
</ul>""",
        f"""<p>El observatorio lo mantiene una iniciativa ciudadana independiente y sin ánimo de lucro. No recibe ninguna subvención y no lleva publicidad.</p>
<ul>
<li><b>Con frecuencia</b> revisamos el seguimiento de las medidas del Plan y comprobamos si el portal de datos abiertos ha publicado datos nuevos o ha cambiado los que ya había. En cuanto hay novedades en el Plan, en los datos o en la web, las publicamos aquí y en el canal de Telegram.</li>
<li><b>Cada año</b>, cuando el Ayuntamiento publica los accidentes del año completo, actualizamos el mapa, las fichas y el seguimiento del objetivo, y sacamos un informe nuevo.</li>
<li><b>Cuesta menos de 90 euros al año</b>: un servidor compartido de 5 euros al mes y los dominios. Lo pagamos nosotros.</li>
<li><b>Si un día dejamos de mantenerlo, no se pierde nada.</b> Todo el código y los datos derivados son públicos con licencias abiertas ({git}), y la web entera se vuelve a construir con una sola orden (<code>make</code>) a partir de los datos del portal. Cualquier persona o entidad puede continuarlo o hacer uno igual en otra ciudad.</li>
<li>Cada cambio en los datos, el método o la web queda anotado, con la fecha, en el <a href="#canvis">registro de cambios</a>.</li>
</ul>""")))

    # ---------------------------------------------------------------- privacidad (07/11/2026)
    tg = (T(f"""<li><b>Telegram.</b> El <a href="{TELEGRAM_CANAL}" rel="noopener">canal de Telegram</a> és un servei extern, amb la seua pròpia política de privacitat. Unir-s'hi es fa dins de Telegram, i és un canal només d'anuncis: no s'hi poden enviar missatges.</li>""",
            f"""<li><b>Telegram.</b> El <a href="{TELEGRAM_CANAL}" rel="noopener">canal de Telegram</a> es un servicio externo, con su propia política de privacidad. Unirse se hace dentro de Telegram, y es un canal solo de anuncios: no se pueden enviar mensajes.</li>""")
          if TELEGRAM_CANAL else "")
    out.append(("privacitat", {"va": "Privacitat i galetes", "es": "Privacidad y cookies"}, T(
        f"""<p>Aquesta web no fa servir galetes (cookies) ni res que et seguisca d'una web a una altra.</p>
<ul>
<li><b>Sense galetes.</b> Només guardem en el teu navegador (en el seu emmagatzematge local) la llengua i el tema, clar o fosc, que tries, perquè no els hages de triar cada vegada. Eixa informació no ix del teu aparell.</li>
<li><b>Estadístiques anònimes.</b> Comptem les visites amb Umami, instal·lat en el nostre propi servidor. No fa servir galetes, no identifica ningú i no compta res si el navegador demana no ser rastrejat (Do Not Track). Només ens diu quantes visites té cada pàgina.</li>
<li><b>Servidor i Cloudflare.</b> El servidor on està la web i Cloudflare, que la servix i la protegix d'atacs, tracten l'adreça IP de les visites només per a fer arribar les pàgines i per seguretat.</li>
<li><b>Avisos per correu.</b> Si ens escrius un avís, mai publiquem el teu nom ni el teu correu. Només els fem servir per a respondre't.</li>
{tg}</ul>
<p>Si tens cap dubte sobre les teues dades, escriu-nos a <a href="mailto:{CORREU}">{CORREU}</a>.</p>""",
        f"""<p>Esta web no usa cookies ni nada que te siga de una web a otra.</p>
<ul>
<li><b>Sin cookies.</b> Solo guardamos en tu navegador (en su almacenamiento local) la lengua y el tema, claro u oscuro, que elijas, para que no tengas que elegirlos cada vez. Esa información no sale de tu aparato.</li>
<li><b>Estadísticas anónimas.</b> Contamos las visitas con Umami, instalado en nuestro propio servidor. No usa cookies, no identifica a nadie y no cuenta nada si el navegador pide no ser rastreado (Do Not Track). Solo nos dice cuántas visitas tiene cada página.</li>
<li><b>Servidor y Cloudflare.</b> El servidor donde está la web y Cloudflare, que la sirve y la protege de ataques, tratan la dirección IP de las visitas solo para hacer llegar las páginas y por seguridad.</li>
<li><b>Avisos por correo.</b> Si nos escribes un aviso, nunca publicamos tu nombre ni tu correo. Solo los usamos para responderte.</li>
{tg}</ul>
<p>Si tienes cualquier duda sobre tus datos, escríbenos a <a href="mailto:{CORREU}">{CORREU}</a>.</p>""")))

    # ---------------------------------------------------------------- accesibilidad (07/11/2026)
    out.append(("accessibilitat", {"va": "Accessibilitat", "es": "Accesibilidad"}, T(
        f"""<p>Volem que l'observatori el puga fer servir tothom, també qui veu malament, qui no distingix colors, qui navega amb el teclat o amb un lector de pantalla. Treballem amb les pautes WCAG 2.1 de nivell AA, les mateixes que la norma UNE-EN 301549 demana a les webs públiques. No és una certificació: és el que hem comprovat nosaltres, i ho expliquem ací.</p>
<ul>
<li><b>Text gran i amb contrast.</b> El text es llig a 18 píxels o més i res baixa de 15. El text té un contrast de 4,5 a 1 o més amb el fons, i les línies, punts i icones dels gràfics, de 3 a 1 o més. Es pot ampliar la pàgina fins al 200 % sense perdre res.</li>
<li><b>No només el color.</b> L'estat de cada mesura es distingix també per la forma de la icona (plena, mig plena, anell o línia discontínua) i per l'etiqueta escrita.</li>
<li><b>Teclat.</b> Tot es pot fer amb el teclat, amb el focus sempre visible. Hi ha un enllaç per a saltar directament al contingut. Els mapes de l'informe es recorren amb les fletxes, i Intro obri la fitxa.</li>
<li><b>Lector de pantalla.</b> Cada mapa i cada gràfic té un text que diu el mateix, i les dades dels mapes també estan en llistes: <a href="{{RAIZ}}lloc/">tots els llocs</a> i <a href="{{RAIZ}}carrer/">tots els carrers</a>. Els títols de cada pàgina segueixen un ordre, i la llengua de cada text està marcada.</li>
<li><b>Mòbil, mode fosc i moviment.</b> La web funciona des de 320 píxels d'amplada, i els botons principals fan almenys 44 píxels. Seguix el mode fosc de l'aparell (o el botó de la capçalera) i, si l'aparell demana reduir el moviment, el mapa no fa animacions.</li>
</ul>
<p>El que encara no hem aconseguit: el mapa interactiu és difícil de fer servir amb un lector de pantalla (per això les mateixes dades estan en les fitxes i les llistes); en les barres per any, la bici, el patinet i els xocs entre els dos es distingixen pel color (el desglossament també està escrit en cada fitxa); alguns controls secundaris del mòbil fan menys de 44 píxels; i els PDF de l'Ajuntament que enllacem no són nostres. Si trobes una barrera, escriu-nos a <a href="mailto:hola@observatoribicivlc.org">hola@observatoribicivlc.org</a> i l'arreglarem.</p>
<p class="nota">Última revisió: 7 de novembre de 2026. Proves automàtiques amb axe en totes les pàgines, en les dues llengües, en tema clar i fosc i a 1440, 390 i 320 píxels, sense cap fallada. Proves guiades amb el navegador: recorregut sencer només amb el teclat, ampliació al 200 %, espaiat de text, contrast mesurat de cada text i simulació de daltonisme. No l'hem provada encara amb persones que facen servir lector de pantalla.</p>""",
        f"""<p>Queremos que el observatorio lo pueda usar todo el mundo, también quien ve mal, quien no distingue colores, quien navega con el teclado o con un lector de pantalla. Trabajamos con las pautas WCAG 2.1 de nivel AA, las mismas que la norma UNE-EN 301549 pide a las webs públicas. No es una certificación: es lo que hemos comprobado nosotros, y lo explicamos aquí.</p>
<ul>
<li><b>Texto grande y con contraste.</b> El texto se lee a 18 píxeles o más y nada baja de 15. El texto tiene un contraste de 4,5 a 1 o más con el fondo, y las líneas, puntos e iconos de los gráficos, de 3 a 1 o más. Se puede ampliar la página hasta el 200 % sin perder nada.</li>
<li><b>No solo el color.</b> El estado de cada medida se distingue también por la forma del icono (lleno, medio lleno, anillo o línea discontinua) y por la etiqueta escrita.</li>
<li><b>Teclado.</b> Todo se puede hacer con el teclado, con el foco siempre visible. Hay un enlace para saltar directamente al contenido. Los mapas del informe se recorren con las flechas, e Intro abre la ficha.</li>
<li><b>Lector de pantalla.</b> Cada mapa y cada gráfico tiene un texto que dice lo mismo, y los datos de los mapas también están en listas: <a href="{{RAIZ}}lloc/">todos los lugares</a> y <a href="{{RAIZ}}carrer/">todas las calles</a>. Los títulos de cada página siguen un orden, y el idioma de cada texto está marcado.</li>
<li><b>Móvil, modo oscuro y movimiento.</b> La web funciona desde 320 píxeles de ancho, y los botones principales miden al menos 44 píxeles. Sigue el modo oscuro del aparato (o el botón de la cabecera) y, si el aparato pide reducir el movimiento, el mapa no hace animaciones.</li>
</ul>
<p>Lo que todavía no hemos conseguido: el mapa interactivo es difícil de usar con un lector de pantalla (por eso los mismos datos están en las fichas y las listas); en las barras por año, la bici, el patinete y los choques entre los dos se distinguen por el color (el desglose también está escrito en cada ficha); algunos controles secundarios del móvil miden menos de 44 píxeles; y los PDF del Ayuntamiento que enlazamos no son nuestros. Si encuentras una barrera, escríbenos a <a href="mailto:hola@observatoribicivlc.org">hola@observatoribicivlc.org</a> y la arreglaremos.</p>
<p class="nota">Última revisión: 7 de noviembre de 2026. Pruebas automáticas con axe en todas las páginas, en las dos lenguas, en tema claro y oscuro y a 1440, 390 y 320 píxeles, sin ningún fallo. Pruebas guiadas con el navegador: recorrido entero solo con el teclado, ampliación al 200 %, espaciado de texto, contraste medido de cada texto y simulación de daltonismo. Todavía no la hemos probado con personas que usen lector de pantalla.</p>""")))

    out.append(("codi", {"va": "Codi i reproductibilitat", "es": "Código y reproducibilidad"}, T(

        f"""<p>Tot el codi és públic: {git}. El codi té llicència MIT, i la documentació i les dades derivades, CC BY 4.0. Amb una sola ordre (<code>make</code>) es tornen a fer les dades, les xifres i la web, a partir de les dades del portal.</p>
<p>Les dades que es descarreguen porten un <a href="{{RAIZ}}dades/datapackage.json">descriptor datapackage.json</a>, de l'estàndard obert Frictionless Data Package, amb el significat, el tipus i les unitats de cada columna.</p>
<p class="nota">Els {mil(c['n_cambios'])} canvis públics en dades, mètode i web estan en el <a href="#canvis">registre de canvis</a>.</p>""",
        f"""<p>Todo el código es público: {git}. El código tiene licencia MIT, y la documentación y los datos derivados, CC BY 4.0. Con una sola orden (<code>make</code>) se vuelven a hacer los datos, las cifras y la web, a partir de los datos del portal.</p>
<p>Los datos que se descargan llevan un <a href="{{RAIZ}}dades/datapackage.json">descriptor datapackage.json</a>, del estándar abierto Frictionless Data Package, con el significado, el tipo y las unidades de cada columna.</p>
<p class="nota">Los {mil(c['n_cambios'])} cambios públicos en datos, método y web están en el <a href="#canvis">registro de cambios</a>.</p>""")))
    return out


# ---------------------------------------------------------------- Data Package (Frictionless) del ZIP de descarga
# Descriptor estándar (https://specs.frictionlessdata.io/data-package/ y tabular-data-resource) de los tres CSV que da el
# botón «Descarga lo que ves» del mapa. Se escribe con la biblioteca estándar (sin la librería frictionless) y lo usan:
# construir_sitio.py, que lo publica en /dades/datapackage.json (las dos lenguas) y lo pasa al mapa para meterlo en el
# ZIP (la lengua de la página, con el CSV descargado como único recurso); y comprobar_sitio.py, que comprueba que los
# campos son las columnas del CSV (CSV_COLS de web/proto/observatori.plantilla.html) en el mismo orden (pendiente 113).
PORTAL = "https://opendata.vlci.valencia.es"
GEOPORTAL = "https://geoportal.valencia.es/server/rest/services/OPENDATA"
_GR = ("graus (WGS 84, EPSG:4326)", "grados (WGS 84, EPSG:4326)")
_ACC = ("accidents", "accidentes")
# vista del mapa -> (nombre del fichero en va, en es, título va, título es, descripción va, descripción es, campos)
# campo: (nombre, tipo Frictionless, descripción va, descripción es, unidad va, unidad es, formato)
DP_VISTAS = {
    "pts": ("accidents", "accidentes", "Accidents situats en el mapa", "Accidentes situados en el mapa",
            "Un accident amb bici o patinet per fila, amb el punt on l'hem situat.",
            "Un accidente con bici o patinete por fila, con el punto donde lo hemos situado.", [
        ("fecha_hora", "datetime", "Data i hora de l'accident (hora local), tal com la publica el portal.", "Fecha y hora del accidente (hora local), tal como la publica el portal.", None, None, "%Y-%m-%dT%H:%M"),
        ("anyo", "year", "Any de l'accident.", "Año del accidente.", None, None, None),
        ("vehiculo", "string", "Quins vehicles d'interés hi ha: només bici, només patinet o bici i patinet.", "Qué vehículos de interés hay: solo bici, solo patinete o bici y patinete.", None, None, None),
        ("gravedad", "string", "Gravetat segons el portal. No es pot comparar entre anys: des de 2023 és ferit greu qui passa més de 24 hores a l'hospital.", "Gravedad según el portal. No se puede comparar entre años: desde 2023 es herido grave quien pasa más de 24 horas en el hospital.", None, None, None),
        ("tipo_ultimo_anyo", "string", "Tipus d'accident (xoc lateral, abast, caiguda…), només en l'últim any, l'únic en què és fiable; buit en els altres.", "Tipo de accidente (choque lateral, alcance, caída…), solo en el último año, el único en que es fiable; vacío en los demás.", None, None, None),
        ("ubicacion", "string", "Adreça escrita en el comunicat de la policia, tal com la publica el portal.", "Dirección escrita en el parte de la policía, tal como la publica el portal.", None, None, None),
        ("localizacion", "string", "Com l'hem situat: per encreuament, per portal, per portal proper o altres.", "Cómo lo hemos situado: por cruce, por portal, por portal cercano u otros.", None, None, None),
        ("vehiculos_implicados", "string", "Vehicles implicats, tal com els publica el portal.", "Vehículos implicados, tal como los publica el portal.", None, None, None),
        ("factores", "string", "Factors concurrents segons la policia, tal com els publica el portal.", "Factores concurrentes según la policía, tal como los publica el portal.", None, None, None),
        ("lat", "number", "Latitud del punt: la cruïlla o el número de portal citat en el comunicat, no un domicili.", "Latitud del punto: el cruce o el número de portal citado en el parte, no un domicilio.", *_GR, None),
        ("lon", "number", "Longitud del punt.", "Longitud del punto.", *_GR, None)]),
    "negros": ("llocs", "lugares", "Llocs amb més accidents", "Lugares con más accidentes",
               "Cruïlles (amb 30 metres al voltant), trams de carrer de fins a 150 metres i zones, amb els seus accidents.",
               "Cruces (con 30 metros alrededor), tramos de calle de hasta 150 metros y zonas, con sus accidentes.", [
        ("orden", "integer", "Posició en la llista, triada amb tots els accidents i tots els anys; buit en les zones.", "Puesto en la lista, elegido con todos los accidentes y todos los años; vacío en las zonas.", None, None, None),
        ("lugar", "string", "Nom del lloc.", "Nombre del lugar.", None, None, None),
        ("tipo", "string", "Cruïlla, tram de carrer o zona.", "Cruce, tramo de calle o zona.", None, None, None),
        ("siniestros_filtro", "integer", "Accidents amb els filtres posats en el mapa.", "Accidentes con los filtros puestos en el mapa.", *_ACC, None),
        ("solo_bici", "integer", "D'aquests, amb bici i sense patinet.", "De ellos, con bici y sin patinete.", *_ACC, None),
        ("solo_patinete", "integer", "D'aquests, amb patinet i sense bici.", "De ellos, con patinete y sin bici.", *_ACC, None),
        ("bici_y_patinete", "integer", "D'aquests, xocs entre bici i patinet.", "De ellos, choques entre bici y patinete.", *_ACC, None),
        ("siniestros_todos", "integer", "Accidents de tots els anys, sense filtres.", "Accidentes de todos los años, sin filtros.", *_ACC, None),
        ("plan_director", "string", "Si el Pla Director de Seguretat Viària cita aquest lloc, només el seu carrer o no l'esmenta.", "Si el Plan Director de Seguridad Vial cita este lugar, solo su calle o no lo menciona.", None, None, None),
        ("lat", "number", "Latitud del centre del lloc.", "Latitud del centro del lugar.", *_GR, None),
        ("lon", "number", "Longitud del centre del lloc.", "Longitud del centro del lugar.", *_GR, None),
        ("ficha", "string", "Enllaç a la fitxa del lloc en el mapa.", "Enlace a la ficha del lugar en el mapa.", None, None, "uri")]),
    "uso": ("punts-comptatge", "puntos-conteo", "Punts de comptatge segons el trànsit", "Puntos de conteo según el tráfico",
            "Punts del carril bici on es compten les bicis, amb els accidents que hi ha i els que tenen de mitjana els punts amb un trànsit semblant.",
            "Puntos del carril bici donde se cuentan las bicis, con los accidentes que hay y los que tienen de media los puntos con un tráfico parecido.", [
        ("punto_conteo", "string", "Codi i nom del punt de comptatge.", "Código y nombre del punto de conteo.", None, None, None),
        ("accidentes", "integer", "Accidents amb bici o patinet en la zona del punt, en els anys amb dades de trànsit.", "Accidentes con bici o patinete en la zona del punto, en los años con datos de tráfico.", *_ACC, None),
        ("media_trafico_parecido", "number", "Accidents que tenen de mitjana els punts amb un trànsit semblant (model binomial negatiu).", "Accidentes que tienen de media los puntos con un tráfico parecido (modelo binomial negativo).", *_ACC, None),
        ("resultado", "string", "Comparació amb la mitjana: sense indicis, potser per damunt o clarament per damunt.", "Comparación con la media: sin indicios, quizá por encima o claramente por encima.", None, None, None),
        ("siniestros_bici", "integer", "Accidents amb bici en la zona del punt.", "Accidentes con bici en la zona del punto.", *_ACC, None),
        ("siniestros_patinete", "integer", "Accidents amb patinet en la zona del punt.", "Accidentes con patinete en la zona del punto.", *_ACC, None),
        ("bicis_dia_laborable", "integer", "Bicis que hi passen un dia laborable, de mitjana (intensitat mitjana diària).", "Bicis que pasan un día laborable, de media (intensidad media diaria).", "bicis per dia", "bicis por día", None),
        ("anyos", "integer", "Anys amb dades de trànsit.", "Años con datos de tráfico.", "anys", "años", None),
        ("contadores", "integer", "Comptadors que formen el punt (els dos sentits d'una via compten junts).", "Contadores que forman el punto (los dos sentidos de una vía cuentan juntos).", None, None, None),
        ("lat", "number", "Latitud del punt.", "Latitud del punto.", *_GR, None),
        ("lon", "number", "Longitud del punt.", "Longitud del punto.", *_GR, None),
        ("ficha", "string", "Enllaç a la fitxa del punt en el mapa.", "Enlace a la ficha del punto en el mapa.", None, None, "uri")]),
}
DP_ORDEN = ["pts", "negros", "uso"]


def datapackage(info, a0, a1, L=None):
    """Descriptor Data Package (dict). L = «va» o «es»: textos en esa lengua (el del ZIP); None: las dos, «va / es» (el
    de /dades/datapackage.json). Los recursos se llaman como los CSV del ZIP sin filtros (observatori-<vista>.csv)."""
    def tx(va, es):
        return va if L == "va" else es if L == "es" else f"{va} / {es}"
    i = 0 if L in (None, "va") else 1
    from sitio import DOMINIO, MARCA, CORREU, REPO
    recursos = []
    for v in DP_ORDEN:
        fva, fes, tva, tes, dva, des, campos = DP_VISTAS[v]
        fs = []
        for n, ty, cva, ces, uva, ues, fmt in campos:
            f = {"name": n, "type": ty, "description": tx(cva, ces)}
            if fmt: f["format"] = fmt
            if uva: f["unit"] = tx(uva, ues)
            fs.append(f)
        recursos.append({
            "name": f"observatori-{(fva, fes)[i]}", "path": f"observatori-{(fva, fes)[i]}.csv",
            "profile": "tabular-data-resource", "title": tx(tva, tes),
            "description": tx(dva + " Els valors de text van en la llengua de la pàgina des de la qual es descarrega.",
                              des + " Los valores de texto van en la lengua de la página desde la que se descarga."),
            "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
            "dialect": {"delimiter": ",", "lineTerminator": "\r\n", "quoteChar": "\"", "doubleQuote": True, "header": True},
            "schema": {"fields": fs, "missingValues": [""]}})
    return {
        "profile": "tabular-data-package",
        "name": "observatori-bici-patinet-valencia",
        "id": f"{DOMINIO}/dades/",
        "title": tx(f"Accidents de bici i patinet a València, {a0}-{a1}, situats en el mapa",
                    f"Accidentes de bici y patinete en València, {a0}-{a1}, situados en el mapa"),
        "description": tx("Accidents de trànsit amb almenys una bici o un patinet a València, del portal de dades obertes de l'Ajuntament, "
                          "situats en el mapa amb el carrerer municipal. El ZIP del mapa porta un sol CSV, el de la vista i els filtres triats. "
                          "Sense dades de les persones implicades: està prohibit reidentificar persones creuant aquestes dades amb altres fonts.",
                          "Accidentes de tráfico con al menos una bici o un patinete en València, del portal de datos abiertos del Ayuntamiento, "
                          "situados en el mapa con el callejero municipal. El ZIP del mapa lleva un solo CSV, el de la vista y los filtros elegidos. "
                          "Sin datos de las personas implicadas: está prohibido reidentificar personas cruzando estos datos con otras fuentes."),
        "homepage": f"{DOMINIO}/dades/",
        "version": info["version"],
        "created": f"{info['version']}T00:00:00Z",
        "keywords": ["seguretat viària", "seguridad vial", "bicicleta", "patinet elèctric", "patinete eléctrico", "VMP", "València", "dades obertes"],
        "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/", "title": "Creative Commons Attribution 4.0"}],
        "contributors": [{"title": MARCA[i] if L else f"{MARCA[0]} / {MARCA[1]}", "email": CORREU, "path": DOMINIO, "role": "author"},
                         {"title": "Ajuntament de València", "path": PORTAL, "role": "publisher"}],
        "sources": [
            {"title": tx(f"Ajuntament de València – Dades Obertes: sinistres de trànsit ({info['conjunto']}), obtinguts el {fecha(info['descarga'])}",
                         f"Ajuntament de València – Dades Obertes: siniestros de tráfico ({info['conjunto']}), obtenidos el {fecha(info['descarga'])}"),
             "path": f"{PORTAL}/dataset/{info['conjunto']}"},
            {"title": tx("Geoportal de l'Ajuntament de València: carrerer (eixos de carrer, portals i vies)",
                         "Geoportal del Ayuntamiento de València: callejero (ejes de calle, portales y vías)"),
             "path": f"{GEOPORTAL}/UrbanismoEInfraestructuras/MapServer"},
            {"title": tx("Geoportal de l'Ajuntament de València: carril bici (capa 189) i punts de comptatge de bicis (capa 225)",
                         "Geoportal del Ayuntamiento de València: carril bici (capa 189) y puntos de conteo de bicis (capa 225)"),
             "path": f"{GEOPORTAL}/Trafico/MapServer"},
            {"title": tx("Ajuntament de València, Mobilitat: intensitats del carril bici", "Ayuntamiento de València, Movilidad: intensidades del carril bici"),
             "path": "https://www.valencia.es/cas/movilidad/otras-descargas"}],
        "codeRepository": REPO,
        "resources": recursos,
    }
