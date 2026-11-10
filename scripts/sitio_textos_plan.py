"""Textos públicos, en valenciano (AVL) y castellano, de las medidas que sigue la página «Què està fent l'Ajuntament? /
¿Qué está haciendo el Ayuntamiento?» de la web nueva (scripts/construir_sitio.py).

Solo biblioteca estándar. Sin cifras de los datos del observatorio: las cifras que aparecen son las que cita el propio Plan
Director de Seguridad Vial 2026-2030 (sus metas y su diagnóstico 2019-2025) o las fuentes públicas citadas (fechas e importes
de licitaciones). Parten de TIT_ES, LUGAR_ES, PLAN_ES y AUN_NO de los bocetos de diseño (internos), de data/processed/plan_seguimiento.csv
(meta, cita y nota) y de la revisión de textos (la revisión interna de los textos, 2.2, 2.6 y F2). Estado, fechas y fuente salen de
pla.js / la base; aquí solo va el texto.

Interfaz:
  MEDIDAS = {id: {"tit": {va, es}, "lugar": {va, es} | None, "plan": {va, es} | None, "nota": {va, es} | None}}
  PUBLICA = {id: {va, es}}         publicaciones de seguimiento que prevé el Plan (las medidas con transp)
  AUN_NO = {id: {va, es}}          publicaciones que aún no tocan
  TIPO_FUENTE = {tipo: {va, es}}
  TITULO_FUENTE = {url: {va, es, fecha}}   título legible de las fuentes cuyo título en pla.js es automático
"""


def _t(va, es):
    return {"va": va, "es": es}


_ANTERIOR = _t("Anterior a l'aprovació del Pla (23/07/2026).", "Anterior a la aprobación del Plan (23/07/2026).")
_OBRA_MUNICIPAL = _t("És una obra municipal que no figura en el Pla.", "Es una obra municipal que no figura en el Plan.")

MEDIDAS = {
    # ---------- Eix 1 · Persones formades i capaces ----------
    "1.1.3-viveros-vmp": {
        "tit": _t("Centre d'Educació Viària de Vivers: formació d'escolars amb diferents vehicles, també patinets",
                  "Centro de Educación Vial de Viveros: formación de escolares con distintos vehículos, incluidos los patinetes"),
        "lugar": None,
        "plan": _t("El Pla preveu que l'alumnat practique amb diferents vehicles, també patinets, i fixa com a meta 150 visites, 5.000 alumnes i el 85 % dels centres cada any.",
                   "El Plan prevé que el alumnado practique con distintos vehículos, también patinetes, y fija como meta 150 visitas, 5.000 alumnos y alumnas y el 85 % de los centros cada año."),
        "nota": None},
    "1.2.1-campanas-convivencia": {
        "tit": _t("Campanyes per a millorar la convivència entre vianants, bicis, patinets i cotxes",
                  "Campañas para mejorar la convivencia entre peatones, bicis, patinetes y coches"),
        "lugar": None,
        "plan": _t("El Pla preveu 8 campanyes i 40 accions divulgatives.", "El Plan prevé 8 campañas y 40 acciones divulgativas."),
        "nota": _t("No hem trobat cap campanya publicada des de l'aprovació del Pla. Abans sí que n'hi va haver dues: «Tu eres el xassís!» (2024) i una campanya de conscienciació i control de patinets de la Policia Local (febrer de 2025).",
                   "No hemos encontrado ninguna campaña publicada desde la aprobación del Plan. Antes sí hubo dos: «¡Tú eres el chasis!» (2024) y una campaña de concienciación y control de patinetes de la Policía Local (febrero de 2025).")},
    "1.2.4-web-seguridad-vial": {
        "tit": _t("Un apartat del web municipal amb dades d'accidents i la memòria d'actuacions",
                  "Un apartado de la web municipal con datos de accidentes y la memoria de actuaciones"),
        "lugar": None,
        "plan": _t("El Pla preveu un apartat web amb dades d'accidents i la memòria d'actuacions, i fixa com a meta 20 actualitzacions i 40.000 visites.",
                   "El Plan prevé un apartado web con datos de accidentes y la memoria de actuaciones, y fija como meta 20 actualizaciones y 40.000 visitas."),
        "nota": _t("La pàgina de seguretat viària de valencia.es ja existeix i inclou el Pla. Encara no té dades d'accidents, ni mapa, ni memòria d'actuacions.",
                   "La página de seguridad vial de valencia.es ya existe e incluye el Plan. Todavía no tiene datos de accidentes, ni mapa, ni memoria de actuaciones.")},
    "1.3.1-paneles-contadores": {
        "tit": _t("Panells en els carrils bici que mostren quantes bicis hi passen",
                  "Paneles en los carriles bici que muestran cuántas bicis pasan"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 3 a 9 panells.", "El Plan prevé pasar de 3 a 9 paneles."),
        "nota": _t("No hem trobat cap panell nou. Mobilitat sí que publica cada mes les bicis que registren els comptadors del carril bici, però en el seu web, no en panells al carrer.",
                   "No hemos encontrado ningún panel nuevo. Movilidad sí publica cada mes las bicis que registran los contadores del carril bici, aunque en su web, no en paneles en la calle.")},
    "1.3.1-aparcabicis": {
        "tit": _t("Més places per a aparcar bicis", "Más plazas para aparcar bicis"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 22.638 a 25.000 places per a aparcar bicis.", "El Plan prevé pasar de 22.638 a 25.000 plazas para aparcar bicis."),
        "nota": _t("No hem trobat cap instal·lació nova publicada des de l'aprovació del Pla. Al novembre de 2025, l'Ajuntament ja en comptava 22.958, més que el punt de partida del Pla.",
                   "No hemos encontrado ninguna instalación nueva publicada desde la aprobación del Plan. En noviembre de 2025, el Ayuntamiento ya contaba 22.958, más que el punto de partida del Plan.")},
    "1.3.1-desplazamientos-bici-vmp": {
        "tit": _t("Més viatges en bici i patinet, mesurats amb els comptadors dels carrils bici",
                  "Más viajes en bici y patinete, medidos con los contadores de los carriles bici"),
        "lugar": None,
        "plan": _t("No és una obra ni una campanya, sinó una xifra que el Pla vol millorar: passar d'un augment del 3,4 % a un del 5 %.",
                   "No es una obra ni una campaña, sino una cifra que el Plan quiere mejorar: pasar de un aumento del 3,4 % a uno del 5 %."),
        "nota": _t("Mobilitat publica cada mes el trànsit dels carrils bici, però no aquesta xifra.",
                   "Movilidad publica cada mes el tráfico de los carriles bici, pero no esta cifra.")},
    # ---------- Eix 2 · Tolerància zero ----------
    "2.1-controles-vmp": {
        "tit": _t("Controls de la Policia Local adreçats als patinets (una sola persona, casc, velocitat i registre) i vigilància dels carrils bici",
                  "Controles de la Policía Local dirigidos a los patinetes (una sola persona, casco, velocidad y registro) y vigilancia de los carriles bici"),
        "lugar": None,
        "plan": _t("El Pla preveu controls, sobretot als patinets, per a comprovar que porten una sola persona i que s'use el casc. No hi fixa cap meta numèrica.",
                   "El Plan prevé controles, sobre todo a los patinetes, para comprobar que lleven una sola persona y que se use el casco. No fija una meta numérica."),
        "nota": _t("Des del febrer de 2026, un grup de la Policia Local (el GIVIC) patrulla en patinet els carrils bici. A l'abril i al maig de 2026 hi va haver una campanya de control del registre de patinets. Tot és anterior a l'aprovació del Pla (23/07/2026) i no hem trobat cap balanç posterior.",
                   "Desde febrero de 2026, un grupo de la Policía Local (el GIVIC) patrulla en patinete los carriles bici. En abril y mayo de 2026 hubo una campaña de control del registro de patinetes. Todo es anterior a la aprobación del Plan (23/07/2026) y no hemos encontrado ningún balance posterior.")},
    # ---------- Eix 3 · Vies segures ----------
    "3.2.2-meta-siniestros": {
        "tit": _t("Reduir a la meitat els accidents amb bici o patinet per a 2030 (indicador de l'acció 3.2.2). Es podrà mesurar quan es publiquen les dades de 2026",
                  "Reducir a la mitad los accidentes con bici o patinete para 2030 (indicador de la acción 3.2.2). Se podrá medir cuando se publiquen los datos de 2026"),
        "lugar": None,
        "plan": _t("L'indicador de l'acció 3.2.2 demana reduir un 50 % els accidents amb bici o patinet per a 2030 i comparar-los cada any. No diu des de quin any es compta. La meta general del Pla és una altra: reduir el nombre de persones mortes i ferides greus.",
                   "El indicador de la acción 3.2.2 pide reducir un 50 % los accidentes con bici o patinete para 2030 y compararlos cada año. No dice desde qué año se cuenta. La meta general del Plan es otra: reducir el número de personas fallecidas y heridas graves."),
        "nota": _t("No hi ha dades de 2026 en el portal de dades obertes, així que encara no es pot avaluar. El seguim any rere any en l'informe.",
                   "No hay datos de 2026 en el portal de datos abiertos, así que todavía no se puede evaluar. Lo seguimos año a año en el informe.")},
    "3.2.2-carril-bici-km": {
        "tit": _t("Fer més carrils bici separats dels cotxes i passar a la calçada els que van per la vorera",
                  "Hacer más carriles bici separados de los coches y pasar a la calzada los que van por la acera"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 225 a 250 km de carril bici.", "El Plan prevé pasar de 225 a 250 km de carril bici."),
        "nota": _t("Hi ha dues obres en marxa, en Giorgeta i Pérez Galdós i en Gaspar Aguilar (Memòria d'actuacions 2023-2026, apartat 2.11), i diverses licitacions en 2026, l'última la dels itineraris d'Orriols (novembre). Bona part són trasllats a la calçada, que no sumen quilòmetres. No hem trobat cap recompte oficial de quilòmetres posterior al de novembre de 2025 (225,7 km).",
                   "Hay dos obras en marcha, en Giorgeta y Pérez Galdós y en Gaspar Aguilar (Memoria de actuaciones 2023-2026, apartado 2.11), y varias licitaciones en 2026, la última la de los itinerarios de Orriols (noviembre). Buena parte son traslados a la calzada, que no suman kilómetros. No hemos encontrado ningún recuento oficial de kilómetros posterior al de noviembre de 2025 (225,7 km).")},
    "3.2.2-ciclocalles": {
        "tit": _t("Ampliar els ciclocarrers, carrers senyalitzats en què la bici va per la calçada al costat dels cotxes",
                  "Ampliar las ciclocalles, calles señalizadas en las que la bici va por la calzada junto a los coches"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 18 a 75 km de ciclocarrers.", "El Plan prevé pasar de 18 a 75 km de ciclocalles."),
        "nota": _t("El Pla parteix de 18 km. L'Ajuntament, en canvi, ja en comptava 46,89 al novembre de 2025.",
                   "El Plan parte de 18 km. El Ayuntamiento, en cambio, ya contaba 46,89 km en noviembre de 2025.")},
    "3.2.2-alfombras-rojas": {
        "tit": _t("Pintar de roig el carril bici en les cruïlles perquè es veja millor",
                  "Pintar de rojo el carril bici en los cruces para que se vea mejor"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 786 a 1.000 cruïlles pintades de roig.", "El Plan prevé pasar de 786 a 1.000 cruces pintados de rojo."),
        "nota": None},
    "3.2.2-pasos-contenedores": {
        "tit": _t("Passos de vianants sobre el carril bici per a arribar als contenidors",
                  "Pasos de peatones sobre el carril bici para llegar a los contenedores"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 3 a 100 passos.", "El Plan prevé pasar de 3 a 100 pasos."),
        "nota": _t("La Memòria d'actuacions de mobilitat 2023-2026 diu que se n'estan senyalitzant molts, sense precisar quants ni on.",
                   "La Memoria de actuaciones de movilidad 2023-2026 dice que se están señalizando muchos, sin precisar cuántos ni dónde.")},
    "3.2.2-plan-director-bici": {
        "tit": _t("Fer les obres previstes en el Pla Director de la Bicicleta de 2023",
                  "Hacer las obras previstas en el Plan Director de la Bicicleta de 2023"),
        "lugar": None,
        "plan": _t("El Pla demana fer totes les obres i mesures del Pla Director de la Bicicleta.", "El Plan pide llevar a cabo todas las obras y medidas del Plan Director de la Bicicleta."),
        "nota": _t("No hem trobat cap seguiment publicat del Pla Director de la Bicicleta.", "No hemos encontrado ningún seguimiento publicado del Plan Director de la Bicicleta.")},
    "3.2.2-zonas-lista": {
        "tit": _t("Localitzar les zones amb molts accidents de bici o patinet i proposar mesures per a cadascuna",
                  "Localizar las zonas con muchos accidentes de bici o patinete y proponer medidas para cada una"),
        "lugar": None,
        "plan": _t("El Pla demana proposar mesures específiques per a les zones amb molts accidents amb bici o patinet. No explica com es defineix una d'aquestes zones ni en publica la llista.",
                   "El Plan pide proponer medidas específicas para las zonas con muchos accidentes con bici o patinete. No explica cómo se define una de esas zonas ni publica la lista."),
        "nota": _t("Segons una nota municipal de febrer de 2026, la Policia Local identificarà aquestes zones.",
                   "Según una nota municipal de febrero de 2026, la Policía Local identificará estas zonas.")},
    "3.2.2c-ambar-intermitente": {
        "tit": _t("Llevar l'ambre intermitent dels semàfors en algunes cruïlles on els cotxes giren mentre creuen bicis i vianants",
                  "Quitar el ámbar intermitente de los semáforos en algunos cruces donde los coches giran mientras cruzan bicis y peatones"),
        "lugar": None,
        "plan": _t("El Pla demana estudiar llevar la fase d'ambre intermitent en determinades cruïlles.",
                   "El Plan pide estudiar quitar la fase de ámbar intermitente en determinados cruces."),
        "nota": _t("Va començar al març de 2026, en la cruïlla de Tarongers amb Lluís Peixó (Memòria d'actuacions 2023-2026, apartat 5.5), abans de l'aprovació del Pla, però l'Ajuntament l'emmarca en el Pla. A l'agost de 2026, l'Ajuntament parlava de 20 cruïlles.",
                   "Empezó en marzo de 2026, en el cruce de Naranjos con Luis Peixó (Memoria de actuaciones 2023-2026, apartado 5.5), antes de la aprobación del Plan, pero el Ayuntamiento la enmarca en el Plan. En agosto de 2026, el Ayuntamiento hablaba de 20 cruces.")},
    "3.2.2b-semaforizacion-carriles-bici": {
        "tit": _t("Posar semàfors en més cruïlles dels carrils bici amb més conflictes",
                  "Poner semáforos en más cruces de los carriles bici con más conflictos"),
        "lugar": None,
        "plan": _t("El Pla demana reforçar la senyalització en les cruïlles sense semàfor i revisar les fases dels semàfors.",
                   "El Plan pide reforzar la señalización en los cruces sin semáforo y revisar las fases de los semáforos."),
        "nota": _t("Es va anunciar en el Debat de l'Estat de la Ciutat de 2026, sense precisar quins carrils ni quan. L'enllaç és la nota de l'Ajuntament sobre el Debat: la llista d'anuncis on apareix aquesta mesura no l'hem trobada publicada en la web municipal.",
                   "Se anunció en el Debate del Estado de la Ciudad de 2026, sin precisar qué carriles ni cuándo. El enlace es la nota del Ayuntamiento sobre el Debate: la lista de anuncios donde aparece esta medida no la hemos encontrado publicada en la web municipal.")},
    "3.2.2-resto-lineas": {
        "tit": _t("Altres mesures del mateix apartat del Pla: més visibilitat en cruïlles i passos de vianants, bicis en zones de vianants, parades d'autobús, bicis per la calçada i continuïtat de la xarxa ciclista",
                  "Otras medidas del mismo apartado del Plan: mejor visibilidad en cruces y pasos de peatones, bicis en zonas peatonales, paradas de autobús, bicis por la calzada y continuidad de la red ciclista"),
        "lugar": None,
        "plan": None,
        "nota": _t("Només hi ha mesures soltes en les cruïlles que es van revisar en 2024. No hem trobat cap programa ni llista publicada per a aquestes mesures.",
                   "Solo hay medidas sueltas en los cruces que se revisaron en 2024. No hemos encontrado ningún programa ni lista publicada para estas medidas.")},
    "3.2.2-ausias-abril": {
        "tit": _t("Mesures en una cruïlla amb molts accidents de patinet: Av. d'Ausiàs March amb l'Av. Fernando Abril Martorell",
                  "Medidas en un cruce con muchos accidentes de patinete: avenida Ausiàs March con la avenida Fernando Abril Martorell"),
        "lugar": None,
        "plan": _t("El Pla la senyala com la segona cruïlla amb més accidents amb patinet (25) entre 2019 i 2025. No li assigna cap mesura concreta.",
                   "El Plan lo señala como el segundo cruce con más accidentes con patinete (25) entre 2019 y 2025. No le asigna ninguna medida concreta."),
        "nota": None},
    "3.2.2-naranjos-peixo": {
        "tit": _t("Mesures en una cruïlla amb molts accidents de bici i patinet: Av. dels Tarongers amb el C/ Lluís Peixó",
                  "Medidas en un cruce con muchos accidentes de bici y patinete: avenida de los Naranjos con la calle Luis Peixó"),
        "lugar": None,
        "plan": _t("El Pla la senyala com la tercera cruïlla amb més accidents amb patinet (22) i la segona amb bici (15) entre 2019 i 2025. No li assigna cap mesura concreta.",
                   "El Plan lo señala como el tercer cruce con más accidentes con patinete (22) y el segundo con bici (15) entre 2019 y 2025. No le asigna ninguna medida concreta."),
        "nota": _t("L'única mesura publicada és la retirada de l'ambre intermitent al març de 2026 (Memòria d'actuacions 2023-2026, apartat 5.5), abans de l'aprovació del Pla. No hi ha obra ni projecte publicats.",
                   "La única medida publicada es la retirada del ámbar intermitente en marzo de 2026 (Memoria de actuaciones 2023-2026, apartado 5.5), antes de la aprobación del Plan. No hay obra ni proyecto publicados.")},
    "3.2.2-abril-malilla": {
        "tit": _t("Mesures en una cruïlla amb molts accidents de bici: Av. Fernando Abril Martorell amb la Ctra. de Malilla",
                  "Medidas en un cruce con muchos accidentes de bici: avenida Fernando Abril Martorell con la carretera de Malilla"),
        "lugar": None,
        "plan": _t("El Pla la senyala com la tercera cruïlla amb més accidents amb bici (14) entre 2019 i 2025. No li assigna cap mesura concreta.",
                   "El Plan lo señala como el tercer cruce con más accidentes con bici (14) entre 2019 y 2025. No le asigna ninguna medida concreta."),
        "nota": None},
    "3.2.2-xativa-jesus": {
        "tit": _t("Estudiar les cruïlles on els cotxes giren amb el semàfor en ambre i travessen el pas de vianants i el carril bici (per exemple, C/ Xàtiva amb C/ Jesús)",
                  "Estudiar los cruces donde los coches giran con el semáforo en ámbar y atraviesan el paso de peatones y el carril bici (por ejemplo, calle Játiva con calle Jesús)"),
        "lugar": None,
        "plan": _t("El Pla posa aquesta cruïlla com a exemple de girs de cotxes amb el semàfor en ambre.",
                   "El Plan pone este cruce como ejemplo de giros de coches con el semáforo en ámbar."),
        "nota": _t("En el mapa la situem en la Pl. de Sant Agustí, on el C/ Xàtiva dona pas al C/ Jesús.",
                   "En el mapa la situamos en la plaza de San Agustín, donde la calle Játiva da paso a la calle Jesús.")},
    "3.2.2-jardin-turia": {
        "tit": _t("Mesures en el Jardí del Túria, on el Pla situa més accidents de bici que en cap altre carrer i molt d'ús del patinet",
                  "Medidas en el Jardín del Turia, donde el Plan sitúa más accidentes de bici que en ninguna otra calle y mucho uso del patinete"),
        "lugar": _t("Jardí del Túria", "Jardín del Turia"),
        "plan": _t("El Pla el senyala com el carrer amb més accidents amb bici (185) entre 2019 i 2025, i diu que l'ús del patinet es concentra al llarg del Jardí del Túria.",
                   "El Plan lo señala como la calle con más accidentes con bici (185) entre 2019 y 2025, y dice que el uso del patinete se concentra a lo largo del Jardín del Turia."),
        "nota": _t("No hem trobat cap mesura de seguretat per a bicis o patinets en el llit del riu. Sí que hi ha en obra un camí per a vianants i bicis (tram XVI-Pont de les Drassanes), que no forma part del Pla.",
                   "No hemos encontrado ninguna medida de seguridad para bicis o patinetes en el cauce. Sí hay en obra un camino para peatones y bicis (tramo XVI-Puente de las Atarazanas), que no forma parte del Plan.")},
    "3.2.2-albereda-carril": {
        "tit": _t("Passar a la calçada el carril bici del Passeig de l'Albereda, entre el Pont del Regne i el de Montolivet (uns 450 m)",
                  "Pasar a la calzada el carril bici del paseo de la Alameda, entre el puente del Reino y el de Monteolivete (unos 450 m)"),
        "lugar": None,
        "plan": _t("El Pla senyala el Passeig de l'Albereda com el tercer carrer amb més accidents amb patinet (166) entre 2019 i 2025.",
                   "El Plan señala el paseo de la Alameda como la tercera calle con más accidentes con patinete (166) entre 2019 y 2025."),
        "nota": _t("La licitació està aprovada i encara sense adjudicar; per això la marquem com a «anunciada». La nota municipal no esmenta el Pla de Seguretat Viària ni els accidents.",
                   "La licitación está aprobada y todavía sin adjudicar; por eso la marcamos como «anunciada». La nota municipal no menciona el Plan de Seguridad Vial ni los accidentes.")},
    "3.2.2-puerto-carril": {
        "tit": _t("Projecte per a passar a la calçada el carril bici de l'Av. del Port (tres trams)",
                  "Proyecto para pasar a la calzada el carril bici de la avenida del Puerto (tres tramos)"),
        "lugar": _t("Av. del Port", "Avenida del Puerto"),
        "plan": _t("El Pla senyala l'Av. del Port com el segon carrer amb més accidents amb patinet (167) i el tercer amb bici (110) entre 2019 i 2025.",
                   "El Plan señala la avenida del Puerto como la segunda calle con más accidentes con patinete (167) y la tercera con bici (110) entre 2019 y 2025."),
        "nota": _t("Només es licita el projecte, no l'obra. L'Ajuntament l'emmarca en el Pla Director de la Bicicleta, no en el de Seguretat Viària.",
                   "Solo se licita el proyecto, no la obra. El Ayuntamiento lo enmarca en el Plan Director de la Bicicleta, no en el de Seguridad Vial.")},
    "3.2.2-campos-crespo": {
        "tit": _t("Carril bici en els carrers de Campos Crespo, Pius XI i Conca (1,1 km)",
                  "Carril bici en las calles Campos Crespo, Pío XI y Cuenca (1,1 km)"),
        "lugar": None,
        "plan": _t("El Pla senyala la cruïlla de Tres Creus amb Campos Crespo com la tercera amb més atropellaments (7).",
                   "El Plan señala el cruce de Tres Cruces con Campos Crespo como el tercero con más atropellos (7)."),
        "nota": _t("La licitació de l'obra, aprovada abans que el Pla, va quedar deserta el 12/08/2026. L'1/10/2026 l'Ajuntament va tornar a aprovar el projecte amb els preus actualitzats (958.013,83 €). Encara no n'hem trobat la nova licitació.",
                   "La licitación de la obra, aprobada antes que el Plan, quedó desierta el 12/08/2026. El 1/10/2026 el Ayuntamiento volvió a aprobar el proyecto con los precios actualizados (958.013,83 €). Todavía no hemos encontrado la nueva licitación.")},
    "3.2.2-giorgeta-perez-galdos": {
        "tit": _t("Carril bici de doble sentit, separat dels cotxes, en les avingudes de Giorgeta i de Pérez Galdós, dins de la reforma de les dues avingudes",
                  "Carril bici de doble sentido, separado de los coches, en las avenidas de Giorgeta y Pérez Galdós, dentro de la reforma de las dos avenidas"),
        "lugar": None,
        "plan": _t("El Pla senyala la cruïlla de Giorgeta amb Jesús com la segona amb més atropellaments (8).",
                   "El Plan señala el cruce de Giorgeta con Jesús como el segundo con más atropellos (8)."),
        "nota": _OBRA_MUNICIPAL},
    "3.2.2-itinerarios-3-lotes": {
        "tit": _t("Millora dels carrils bici del C/ Carters, el C/ Burgos i l'Av. de la Plata",
                  "Mejora de los carriles bici de la calle Carteros, la calle Burgos y la avenida de la Plata"),
        "lugar": None,
        "plan": _t("El Pla preveu continuar millorant la seguretat dels itineraris ciclistes que ja existeixen.",
                   "El Plan prevé seguir mejorando la seguridad de los itinerarios ciclistas que ya existen."),
        "nota": _t("La licitació està publicada i encara sense adjudicar. Una d'anterior, de l'Av. de la Plata (maig de 2026), va quedar deserta.",
                   "La licitación está publicada y todavía sin adjudicar. Una anterior, de la avenida de la Plata (mayo de 2026), quedó desierta.")},
    "3.2.2-orriols-itinerarios": {
        "tit": _t("Millora dels itineraris ciclistes d'Orriols: un de nou per l'Av. d'Alfauir, Primat Reig, Benicarló i Peníscola, i la connexió entre els carrils de Reig Genovés i Sant Vicent de Paül",
                  "Mejora de los itinerarios ciclistas de Orriols: uno nuevo por la avenida de Alfauir, Primado Reig, Benicarló y Peñíscola, y la conexión entre los carriles de Reig Genovés y San Vicente de Paúl"),
        "lugar": None,
        "plan": _t("El Pla preveu continuar millorant la seguretat dels itineraris ciclistes que ja existeixen i passar de 225 a 250 km de carril bici.",
                   "El Plan prevé seguir mejorando la seguridad de los itinerarios ciclistas que ya existen y pasar de 225 a 250 km de carril bici."),
        "nota": _t("La Junta de Govern la va aprovar el 29/10/2026 i la licitació es va publicar el 2/11/2026, en dos lots (334.645,28 €, IVA inclòs, amb fons europeus FEDER). Encara no s'ha adjudicat. La nota de l'Ajuntament no cita el Pla.",
                   "La Junta de Gobierno la aprobó el 29/10/2026 y la licitación se publicó el 2/11/2026, en dos lotes (334.645,28 €, IVA incluido, con fondos europeos FEDER). Todavía no se ha adjudicado. La nota del Ayuntamiento no cita el Plan.")},
    "3.2.2-gaspar-aguilar": {
        "tit": _t("Carril bici de doble sentit, separat dels cotxes, en l'Av. de Gaspar Aguilar (1,2 km, de la Pl. de Jesús a l'Av. Doctor Tomàs Sala)",
                  "Carril bici de doble sentido, separado de los coches, en la avenida de Gaspar Aguilar (1,2 km, de la plaza de Jesús a la avenida Doctor Tomás Sala)"),
        "lugar": None,
        "plan": _t("El Pla preveu continuar millorant la seguretat dels itineraris ciclistes que ja existeixen i passar de 225 a 250 km de carril bici.",
                   "El Plan prevé seguir mejorando la seguridad de los itinerarios ciclistas que ya existen y pasar de 225 a 250 km de carril bici."),
        "nota": _OBRA_MUNICIPAL},
    "3.2.2-nicolas-factor": {
        "tit": _t("Millora per a bicis i vianants en el C/ Beat Nicolau Factor, votada en els pressupostos participatius de 2022-2023",
                  "Mejora para bicis y peatones en la calle Beato Nicolás Factor, votada en los presupuestos participativos de 2022-2023"),
        "lugar": _t("C/ Beat Nicolau Factor, entre el C/ María Jordán i el C/ Assagador de les Monges",
                    "Calle Beato Nicolás Factor, entre la calle María Jordán y la calle Azagador de las Monjas"),
        "plan": _t("El Pla preveu continuar millorant la seguretat dels itineraris ciclistes que ja existeixen.",
                   "El Plan prevé seguir mejorando la seguridad de los itinerarios ciclistas que ya existen."),
        "nota": _t("La licitació es va publicar el 20/10/2026 (236.232,97 €, IVA inclòs) i l'Ajuntament la va anunciar el 2/11/2026. Segons la premsa, serà un carril bici de doble sentit separat dels cotxes, de 2,80 m, amb dos mesos d'obra. Encara no s'ha adjudicat.",
                   "La licitación se publicó el 20/10/2026 (236.232,97 €, IVA incluido) y el Ayuntamiento la anunció el 2/11/2026. Según la prensa, será un carril bici de doble sentido separado de los coches, de 2,80 m, con dos meses de obra. Todavía no se ha adjudicado.")},
    "3.2.3c-carril-bici-escolar": {
        "tit": _t("Completar la xarxa de carrils bici al voltant dels col·legis, connectada amb la de la ciutat",
                  "Completar la red de carriles bici en el entorno de los colegios, conectada con la de la ciudad"),
        "lugar": None,
        "plan": _t("No té una meta pròpia; forma part de l'acció 3.2.3, que vol reduir un 60 % els accidents a l'entorn escolar.",
                   "No tiene meta propia; forma parte de la acción 3.2.3, que quiere reducir un 60 % los accidentes en el entorno escolar."),
        "nota": None},
    "3.5-calles-30": {
        "tit": _t("Més carrers amb límit de 30 km/h", "Más calles con límite de 30 km/h"),
        "lugar": None,
        "plan": _t("El Pla preveu que el 95 % dels carrers siguen de 30 km/h. Ara en són el 64 %.",
                   "El Plan prevé que el 95 % de las calles sean de 30 km/h. Hoy son el 64 %."),
        "nota": _t("No hi ha una capa pública dels carrers a 30 km/h per a mesurar-ho.", "No hay una capa pública de las calles a 30 km/h para medirlo.")},
    "3.5-calles-20": {
        "tit": _t("Més carrers a 20 km/h i carrers on vianants, bicis i cotxes comparteixen el mateix espai",
                  "Más calles a 20 km/h y calles donde peatones, bicis y coches comparten el mismo espacio"),
        "lugar": None,
        "plan": _t("El Pla preveu passar del 3 % al 10 % de carrers a 20 km/h o residencials.",
                   "El Plan prevé pasar del 3 % al 10 % de calles a 20 km/h o residenciales."),
        "nota": _t("Segons la Memòria d'actuacions 2023-2026 (apartat 1.3), el 2,39 % dels carrers ja estan limitats a 20 km/h. Al maig de 2026 hi va haver zones noves (a Campanar i al voltant de l'IES Cabanyal), abans de l'aprovació del Pla (23/07/2026). No n'hem trobat cap de posterior.",
                   "Según la Memoria de actuaciones 2023-2026 (apartado 1.3), el 2,39 % de las calles ya están limitadas a 20 km/h. En mayo de 2026 hubo zonas nuevas (en Campanar y alrededor del IES Cabanyal), antes de la aprobación del Plan (23/07/2026). No hemos encontrado ninguna posterior.")},
    "3.5-evaluacion-zonas30": {
        "tit": _t("Avaluar si funcionen les zones 30 i les de preferència residencial",
                  "Evaluar si funcionan las zonas 30 y las de preferencia residencial"),
        "lugar": None,
        "plan": _t("El Pla preveu reduir un 50 % els accidents en les zones 30, de coexistència i residencials.",
                   "El Plan prevé reducir un 50 % los accidentes en las zonas 30, de coexistencia y residenciales."),
        "nota": None},
    "3.6-manual-obras": {
        "tit": _t("Un manual per a senyalitzar les obres que tinga en compte qui va en bici o en patinet",
                  "Un manual para señalizar las obras que tenga en cuenta a quien va en bici o en patinete"),
        "lugar": None,
        "plan": _t("El Pla preveu aprovar el manual i reduir un 40 % els incidents en obres.",
                   "El Plan prevé aprobar el manual y reducir un 40 % los incidentes en obras."),
        "nota": None},
    "3.7-auditorias": {
        "tit": _t("Revisions de seguretat en els trams amb més accidents i també en els projectes de carrers nous",
                  "Revisiones de seguridad en los tramos con más accidentes, y también en los proyectos de calles nuevas"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 4 a 30 revisions de seguretat en trams amb molts accidents i revisar 10 projectes.",
                   "El Plan prevé pasar de 4 a 30 revisiones de seguridad en tramos con muchos accidentes y revisar 10 proyectos."),
        "nota": _t("Només consten les 4 revisions de 2024. Els seus resultats s'estan aplicant (vegeu les mesures de les cruïlles revisades), però no hem trobat cap revisió nova.",
                   "Solo constan las 4 revisiones de 2024. Sus resultados se están aplicando (ver las medidas de los cruces revisados), pero no hemos encontrado ninguna revisión nueva.")},
    "3.2.2-pl-zaragoza": {
        "tit": _t("Es va reordenar la glorieta i es va llevar el semàfor en ambre intermitent, després de la revisió de seguretat de 2024",
                  "Se reordenó la glorieta y se quitó el semáforo en ámbar intermitente, tras la revisión de seguridad de 2024"),
        "lugar": _t("Pl. de Saragossa (Albereda, Aragó i Port)", "Plaza de Zaragoza (Alameda, Aragón y Puerto)"),
        "plan": _t("El Pla la senyala com la cruïlla amb més accidents amb patinet (32) i amb bici (22) entre 2019 i 2025. També recull la revisió de seguretat de 2024 i la reordenació de 2025.",
                   "El Plan lo señala como el cruce con más accidentes con patinete (32) y con bici (22) entre 2019 y 2025. También recoge la revisión de seguridad de 2024 y la reordenación de 2025."),
        "nota": _t("Al febrer de 2025 es van pintar carrils i es va posar el roig fix en el gir d'Aragó a l'Albereda. Al maig de 2026, l'Ajuntament va anunciar que s'hi llevava l'ambre intermitent i es mantenia el roig total. Tot és anterior a l'aprovació del Pla (23/07/2026).",
                   "En febrero de 2025 se pintaron carriles y se puso rojo fijo en el giro de Aragón a la Alameda. En mayo de 2026, el Ayuntamiento anunció que se quitaba el ámbar intermitente y se mantenía el rojo total. Todo es anterior a la aprobación del Plan (23/07/2026).")},
    "3.7-blasco-benlloch-clariano": {
        "tit": _t("Convertir en una rotonda completa la glorieta, ara partida, de Blasco Ibáñez amb Cardenal Benlloch i Clariano, després de la revisió de seguretat de 2024",
                  "Convertir en una rotonda completa la glorieta, hoy partida, de Blasco Ibáñez con Cardenal Benlloch y Clariano, tras la revisión de seguridad de 2024"),
        "lugar": _t("Av. de Blasco Ibáñez - Av. Cardenal Benlloch - C/ Clariano", "Avenida de Blasco Ibáñez con la avenida Cardenal Benlloch y la calle Clariano"),
        "plan": _t("El Pla recull la revisió de seguretat de 2024 d'aquesta cruïlla i la reordenació de les cruïlles amb més accidents en 2025.",
                   "El Plan recoge la revisión de seguridad de 2024 de este cruce y la reordenación de los cruces con más accidentes en 2025."),
        "nota": _t("El projecte està aprovat. No hem trobat la licitació ni l'adjudicació de l'obra.", "El proyecto está aprobado. No hemos encontrado la licitación ni la adjudicación de la obra.")},
    "3.7-granvia-guimera": {
        "tit": _t("Canvi en els semàfors després de la revisió de seguretat de 2024: es va llevar la fase en ambre per a qui ve d'Àngel Guimerà i el roig dura més",
                  "Cambio en los semáforos tras la revisión de seguridad de 2024: se quitó la fase en ámbar para quien viene de Ángel Guimerá y el rojo dura más"),
        "lugar": _t("Gran Via de Ferran el Catòlic - C/ Àngel Guimerà", "Gran Vía de Fernando el Católico con la calle Ángel Guimerá"),
        "plan": _t("El Pla diu que en 2025 es van reordenar les cruïlles amb més accidents revisades en 2024, i cita aquesta.",
                   "El Plan dice que en 2025 se reordenaron los cruces con más accidentes revisados en 2024, y cita este."),
        "nota": _t("És una mesura pensada sobretot per a qui va a peu, per la boca de metro de la mitjana. La font la presenta com «una de les actuacions executades» fins al febrer de 2025; la resta de millores de la cruïlla no les hem trobades fetes. És anterior a l'aprovació del Pla (23/07/2026). El 10/11/2026 l'Ajuntament va anunciar que ha encarregat un estudi per a millorar la seguretat de la cruïlla, sense import ni termini; no parla de bicis ni de patinets.",
                   "Es una medida pensada sobre todo para quien va a pie, por la boca de metro de la mediana. La fuente la presenta como «una de las actuaciones ejecutadas» hasta febrero de 2025; el resto de mejoras del cruce no las hemos encontrado hechas. Es anterior a la aprobación del Plan (23/07/2026). El 10/11/2026 el Ayuntamiento anunció que ha encargado un estudio para mejorar la seguridad del cruce, sin importe ni plazo; no habla de bicis ni de patinetes.")},
    "3.7-benlloch-puerto": {
        "tit": _t("Canvis en la cruïlla de l'Av. Cardenal Benlloch amb l'Av. del Port, després de la revisió de seguretat de 2024",
                  "Cambios en el cruce de la avenida Cardenal Benlloch con la avenida del Puerto, tras la revisión de seguridad de 2024"),
        "lugar": None,
        "plan": _t("El Pla la compta entre les quatre cruïlles que es van revisar en 2024.", "El Plan lo cuenta entre los cuatro cruces que se revisaron en 2024."),
        "nota": _t("Al febrer de 2025 es van separar amb línia contínua, fletxes i zebrat els girs a l'esquerra des de l'Av. del Port, es va reforçar la incorporació des del C/ Eduard Boscà i es van posar viseres als semàfors de vianants. La Memòria d'actuacions 2023-2026 (apartats 5.1 i 5.5) diu que al maig de 2026 s'hi va llevar l'ambre intermitent. Tot és anterior a l'aprovació del Pla (23/07/2026).",
                   "En febrero de 2025 se separaron con línea continua, flechas y cebreado los giros a la izquierda desde la avenida del Puerto, se reforzó la incorporación desde la calle Eduardo Boscá y se pusieron viseras en los semáforos de peatones. La Memoria de actuaciones 2023-2026 (apartados 5.1 y 5.5) dice que en mayo de 2026 se quitó el ámbar intermitente. Todo es anterior a la aprobación del Plan (23/07/2026).")},
    # ---------- Eix 6 · Dades i coneixement ----------
    "6.1.1-mapa-siniestros": {
        "tit": _t("Un mapa públic per a consultar els accidents", "Un mapa público para consultar los accidentes"),
        "lugar": None,
        "plan": _t("El Pla preveu aplicacions per a veure en un mapa les dades d'accidents. No diu si seran públiques.",
                   "El Plan prevé aplicaciones para ver en un mapa los datos de accidentes. No dice si serán públicas."),
        "nota": None},
    "6.1.1-informes-indicadores": {
        "tit": _t("Calcular els accidents en relació amb el trànsit i publicar informes amb aquests indicadors",
                  "Calcular los accidentes en relación con el tráfico y publicar informes con esos indicadores"),
        "lugar": None,
        "plan": _t("El Pla preveu 6 informes a l'any amb aquestes xifres.", "El Plan prevé 6 informes al año con estas cifras."),
        "nota": None},
    "6.2-convenios": {
        "tit": _t("Convenis amb universitats i entitats d'investigació", "Convenios con universidades y entidades de investigación"),
        "lugar": None,
        "plan": _t("El Pla preveu 10 convenis, 15 estudis i 6 proves pilot.", "El Plan prevé 10 convenios, 15 estudios y 6 pruebas piloto."),
        "nota": None},
    # ---------- Eix 7 · Administracions i organitzacions segures ----------
    "7.1.1-cuadro-mando": {
        "tit": _t("Un tauler públic per a seguir l'avanç del Pla", "Un panel público para seguir el avance del Plan"),
        "lugar": None,
        "plan": _t("El Pla preveu un tauler per a seguir-ne l'avanç, que ara no existeix. No diu si serà públic.",
                   "El Plan prevé un panel para seguir su avance, que hoy no existe. No dice si será público."),
        "nota": None},
    "7.1.2-memoria-anual": {
        "tit": _t("Una memòria anual d'accidents per a la Comissió de Seguretat Viària", "Una memoria anual de accidentes para la Comisión de Seguridad Vial"),
        "lugar": None,
        "plan": _t("El Pla preveu publicar un informe d'accidents cada any.", "El Plan prevé publicar un informe de accidentes cada año."),
        "nota": _t("La Memòria d'actuacions de mobilitat 2023-2026 resumeix obres i mesures, però no té xifres d'accidents: no és aquesta memòria.",
                   "La Memoria de actuaciones de movilidad 2023-2026 resume obras y medidas, pero no tiene cifras de accidentes: no es esta memoria.")},
    "7.3.1-informes-comision": {
        "tit": _t("Informes de seguiment davant la Comissió de Seguretat Viària", "Informes de seguimiento ante la Comisión de Seguridad Vial"),
        "lugar": None,
        "plan": _t("El Pla preveu 2 informes a l'any.", "El Plan prevé 2 informes al año."),
        "nota": None},
    "7.3.4-empresas-bici-vmp": {
        "tit": _t("Implicar empreses de venda i lloguer de bicis i patinets en campanyes",
                  "Implicar a empresas de venta y alquiler de bicis y patinetes en campañas"),
        "lugar": None,
        "plan": _t("El Pla preveu passar de 5 a 30 empreses.", "El Plan prevé pasar de 5 a 30 empresas."),
        "nota": None},
}

# Publicaciones de seguimiento que prevé el Plan (medidas con «transp» en pla.js), en lenguaje llano
PUBLICA = {
    "1.2.4-web-seguridad-vial": _t("Un apartat web amb dades d'accidents i la memòria d'actuacions", "Un apartado web con datos de accidentes y la memoria de actuaciones"),
    "3.2.2-meta-siniestros": _t("Dades obertes d'accidents del primer any del Pla", "Datos abiertos de accidentes del primer año del Plan"),
    "3.2.2-plan-director-bici": _t("Seguiment del Pla Director de la Bicicleta", "Seguimiento del Plan Director de la Bicicleta"),
    "3.2.2-zonas-lista": _t("Llista de zones amb molts accidents de bici i patinet", "Lista de zonas con muchos accidentes de bici y patinete"),
    "3.5-evaluacion-zonas30": _t("Avaluació de les zones 30", "Evaluación de las zonas 30"),
    "3.7-auditorias": _t("Revisions de seguretat noves", "Revisiones de seguridad nuevas"),
    "6.1.1-mapa-siniestros": _t("Mapa per a consultar els accidents", "Mapa para consultar los accidentes"),
    "6.1.1-informes-indicadores": _t("Informes d'accidents en relació amb el trànsit", "Informes de accidentes en relación con el tráfico"),
    "6.2-convenios": _t("Convenis amb universitats i entitats d'investigació", "Convenios con universidades y entidades de investigación"),
    "7.1.1-cuadro-mando": _t("Tauler públic per a seguir l'avanç del Pla", "Panel público para seguir el avance del Plan"),
    "7.1.2-memoria-anual": _t("Memòria anual d'accidents", "Memoria anual de accidentes"),
    "7.3.1-informes-comision": _t("Informes de seguiment davant la Comissió de Seguretat Viària", "Informes de seguimiento ante la Comisión de Seguridad Vial"),
}

AUN_NO = {"3.2.2-meta-siniestros": _t("Encara no toca: 2026 no ha acabat", "Todavía no toca: 2026 no ha terminado")}

TIPO_FUENTE = {
    "plan": _t("Pla Director de Seguretat Viària", "Plan Director de Seguridad Vial"),
    "contratacion": _t("Plataforma de Contractació del Sector Públic", "Plataforma de Contratación del Sector Público"),
    "nota_prensa": _t("Nota de premsa de l'Ajuntament", "Nota de prensa del Ayuntamiento"),
    "documento_municipal": _t("Document municipal", "Documento municipal"),
    "prensa": _t("Premsa", "Prensa"),
    "bop": _t("Butlletí Oficial de la Província", "Boletín Oficial de la Provincia"),
    "junta_gobierno": _t("Junta de Govern Local", "Junta de Gobierno Local"),
    "respuesta_movilidad": _t("Resposta del Servei de Mobilitat", "Respuesta del Servicio de Movilidad"),
}


def _f(va, es, fecha=""):
    return {"va": va, "es": es, "fecha": fecha}


_PCSP = "https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl="
# Fuentes de pla.js con título automático (dominio · slug): título legible. Fecha solo si consta en plan_seguimiento.csv.
TITULO_FUENTE = {
    "https://www.valencia.es/documents/d/guest/20260727-memoria-actuaciones-movilidad-2023-2026-julio-2026":
        _f("Ajuntament de València: Memòria d'actuacions de mobilitat 2023-2026 (juliol de 2026)",
           "Ayuntamiento de València: Memoria de actuaciones de movilidad 2023-2026 (julio de 2026)", "2026-07-27"),
    "https://www.elperiodic.com/valencia/plan-vector-policia-local-para-reducir-accidentes-mortales-comienza-frutos-solo-muerto-frente-siete-2025_1079063":
        _f("El Periòdic: el Pla Vector de la Policia Local per a reduir els accidents mortals comença a donar fruits",
           "El Periòdic: el Plan Vector de la Policía Local para reducir los accidentes mortales comienza a dar frutos", "2026-06-10"),
    "https://www.valencia.es/cas/actualidad/-/content/plan-director-de-seguridad-vial-val%C3%A8ncia":
        _f("Ajuntament de València: nota sobre el Pla Director de Seguretat Viària", "Ayuntamiento de València: nota sobre el Plan Director de Seguridad Vial", "2026-02-03"),
    "https://www.google.com/maps/d/u/1/viewer?mid=12T1_6G3wKqRYUdxhyKLF3CLjGNs3cFU":
        _f("Mapa municipal de les cruïlles on s'ha llevat l'ambre intermitent", "Mapa municipal de los cruces donde se ha quitado el ámbar intermitente"),
    "https://www.valencia.es/cas/actualidad/-/content/grupo-inspecci%C3%B3n-v%C3%ADas-ciclistas":
        _f("Ajuntament de València: grup de la Policia Local d'inspecció de les vies ciclistes", "Ayuntamiento de València: grupo de la Policía Local de inspección de las vías ciclistas"),
    "https://www.valencia.es/cas/actualidad/-/content/campa%C3%B1a-control-inscripci%C3%B3n-patinetes-val%C3%A8ncia":
        _f("Ajuntament de València: campanya de control de la inscripció dels patinets", "Ayuntamiento de València: campaña de control de la inscripción de los patinetes"),
    "https://valencianews.es/valencia/movilidad-senaliza-los-carriles-de-plaza-zaragoza-y-mejora-la-seguridad-viaria-de-la-rotonda/":
        _f("Valencia News: Mobilitat senyalitza els carrils de la plaça de Saragossa i millora la seguretat de la rotonda (inclou la Gran Via de Ferran el Catòlic amb Àngel Guimerà i l'Av. Cardenal Benlloch amb l'Av. del Port)",
           "Valencia News: Movilidad señaliza los carriles de la plaza de Zaragoza y mejora la seguridad vial de la rotonda (incluye Gran Vía de Fernando el Católico con Ángel Guimerá y avenida Cardenal Benlloch con avenida del Puerto)",
           "2025-02-22"),
    _PCSP + "O57tLw%2FBLx6TylGzYmBF9Q%3D%3D":
        _f("Plataforma de Contractació del Sector Públic: camí per a vianants i bicis en el Jardí del Túria, tram XVI-Pont de les Drassanes",
           "Plataforma de Contratación del Sector Público: camino para peatones y bicis en el Jardín del Turia, tramo XVI-Puente de las Atarazanas"),
    "https://www.valencia.es/cas/actualidad/-/content/licitaci%C3%B3n-modificaci%C3%B3n-carril-bici-albereda":
        _f("Ajuntament de València: licitació de la modificació del carril bici de l'Albereda", "Ayuntamiento de València: licitación de la modificación del carril bici de la Alameda", "2026-10-16"),
    "https://www.valencia.es/cas/actualidad/-/content/licitaci%C3%B3n-redacci%C3%B3n-proyecto-carril-bici-avenida-del-puerto-val%C3%A8ncia":
        _f("Ajuntament de València: licitació de la redacció del projecte del carril bici de l'Av. del Port", "Ayuntamiento de València: licitación de la redacción del proyecto del carril bici de la avenida del Puerto", "2026-10-27"),
    _PCSP + "3O8TtcPDS30wYTJJ03sHog%3D%3D":
        _f("Plataforma de Contractació del Sector Públic: obra del carril bici de Campos Crespo, Pius XI i Conca (deserta)",
           "Plataforma de Contratación del Sector Público: obra del carril bici de Campos Crespo, Pío XI y Cuenca (desierta)", "2026-08-12"),
    _PCSP + "V3KrMzimy3k%2B1TMyIiZmzw%3D%3D":
        _f("Plataforma de Contractació del Sector Públic: reurbanització de les avingudes de Giorgeta i Pérez Galdós",
           "Plataforma de Contratación del Sector Público: reurbanización de las avenidas de Giorgeta y Pérez Galdós"),
    _PCSP + "YkI%2FJpgVW9rjHF5qKI4aaw%3D%3D":
        _f("Plataforma de Contractació del Sector Públic: carril bici de l'Av. de la Plata (desert)",
           "Plataforma de Contratación del Sector Público: carril bici de la avenida de la Plata (desierta)", "2026-06-29"),
    _PCSP + "A%2BhQh9rSB6xPpzdqOdhuWg%3D%3D":
        _f("Plataforma de Contractació del Sector Públic: carril bici de l'Av. de Gaspar Aguilar",
           "Plataforma de Contratación del Sector Público: carril bici de la avenida de Gaspar Aguilar"),
}


# Meta de cada medida tal como la escribe el Plan (en castellano, en la base) y su traducción para la vista en valenciano
# (07/11/2026, revisión de UX: en la vista va salían en castellano). Una meta nueva sin traducción sale en castellano y
# marcada con lang="es" hasta que se añada aquí.
META_VA = {
    "-50 % de siniestros en zonas 30, de coexistencia y residenciales": "-50 % de sinistres en zones 30, de coexistència i residencials",
    "1 informe anual publicado (línea base 1)": "1 informe anual publicat (línia de base: 1)",
    "10 convenios; 15 estudios; 6 pilotos": "10 convenis; 15 estudis; 6 projectes pilot",
    "100 % de las actuaciones": "100 % de les actuacions",
    "150 visitas, 5.000 alumnos y 85 % de centros al año": "150 visites, 5.000 alumnes i el 85 % dels centres cada any",
    "18 km → 75 km de ciclocalles": "18 km → 75 km de ciclocarrers",
    "2 al año": "2 cada any",
    "225 km → 250 km de carril bici": "225 km → 250 km de carril bici",
    "3 % → 10 % de las calles": "3 % → 10 % dels carrers",
    "3 → 9 paneles": "3 → 9 panells",
    "4 → 30 auditorías en servicio; 10 proyectos auditados": "4 → 30 auditories en servei; 10 projectes auditats",
    "5 módulos informáticos": "5 mòduls informàtics",
    "5 → 30 empresas": "5 → 30 empreses",
    "6 informes publicados al año": "6 informes publicats cada any",
    "64 % → 95 % de las calles": "64 % → 95 % dels carrers",
    "8 campañas; 40 acciones divulgativas": "8 campanyes; 40 accions divulgatives",
    "Manual aprobado; -40 % de incidentes en obras": "Manual aprovat; -40 % d'incidents en obres",
    "No existente → sistema operativo": "No existeix → sistema en funcionament",
    "Portal operativo; 20 actualizaciones; 40.000 visitas": "Portal en funcionament; 20 actualitzacions; 40.000 visites",
    "Sin meta numérica (remite al Plan Vector)": "Sense meta numèrica (remet al Pla Vector)",
    "Sin meta propia": "Sense meta pròpia",
    "Sin meta propia (3.2.3: -60 % de siniestros en el entorno escolar)": "Sense meta pròpia (3.2.3: -60 % de sinistres en l'entorn escolar)",
}


def meta_va(es):
    """(texto va, marca de idioma): la traducción si la hay; si solo son cifras, la misma; si no, el castellano con lang="es"."""
    if es in META_VA: return META_VA[es], ""
    import re as _re
    if not _re.search(r"[A-Za-zÀ-ÿ]{3,}", es): return es, ""
    return es, ' lang="es"'
