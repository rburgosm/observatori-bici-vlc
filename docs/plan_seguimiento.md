# «El Plan, al día»: seguimiento de las actuaciones de bici y patinete (v1 y v2, 04/11/2026)

Fichero de datos: `data/processed/plan_seguimiento.csv` (46 filas, una por actuación, tras aplicar la v2; la v1 tenía 42). Coordenadas: `scripts/coords_plan_seguimiento.py`.
Es la base de la futura sección «El Plan, al día» y de una tabla compartida (por ejemplo, en Grist) que podrá mantener una entidad colaboradora. **Tono: seguimiento, no auditoría.** Es lo que hemos encontrado publicado, con fuente, y está abierto a que el Ajuntament lo corrija o lo complete.

## 1. Cómo se ha hecho

1. **Selección de actuaciones** en el texto del Plan (`data/raw/pdsv/pdsv.txt`) y en sus tablas de indicadores (`data/processed/pdsv_indicadores.csv`):
   - **directas**: carril bici, ciclocalles, VMP, aparcabicis, paneles contadores, controles de patinetes, la acción 3.2.2 y sus líneas a-i;
   - **claras**: zonas 30 y calles 20, auditorías (3.7), señalización de obras con micromovilidad (3.6), mapa e informes de siniestros (6.1.1), convenios (6.2), cuadro de mando y memoria (7.1.1 y 7.1.2), informes a la Comisión (7.3.1), empresas de bici y VMP (7.3.4), web de seguridad vial (1.2.4) y campañas de convivencia (1.2.1 y 1.2.2);
   - **lugares**: los cruces y calles de bici y VMP del apartado 2.3.4, las 4 auditorías de 2024, el cruce Xàtiva-Jesús y los proyectos de carril bici de 2026 que tocan esos lugares o la meta de km.
   - Se ha dejado fuera la 2.2 (radares, foto-rojo, CCTV): no es específica de bici ni de VMP. Si se quiere, se puede añadir.
   - Cada fila lleva `cita_plan` (página del PDF, línea de `pdsv.txt` y cita corta) y, si la hay, la meta del Plan.
2. **Búsqueda de lo publicado** con WebSearch y WebFetch (unas 40 consultas, el 04/11/2026):
   - notas de prensa de valencia.es, que esta vez sí se pudieron leer, sin bloqueo del WAF;
   - prensa local (Valencia News, El Periòdic, El Español, elDiario.es);
   - la lista oficial de anuncios del Debate del Estado de la Ciudad (17/09/2026).
   No se ha consultado la Plataforma de Contratación ni el BOP directamente. Las licitaciones se han tomado de las notas municipales que informan del acuerdo de la Junta de Gobierno Local.
3. **Coordenadas** (solo en las filas de lugar):
   - en los cruces, la mediana de los siniestros geocodificados en ese cruce (`siniestros_geo.csv`, método `cruce`);
   - en las calles, la mediana de los siniestros de la calle (es aproximada);
   - para Xàtiva-Jesús, el encuentro de los ejes del callejero.
   Quedan sin coordenadas el Jardí del Túria (zona lineal) y los tres lotes de itinerarios (son tres calles). No se ha usado ningún servicio externo.

## 2. Criterio de estados

| Estado | Significa | Ejemplo |
|---|---|---|
| `sin_info` | No hemos encontrado nada publicado. **No quiere decir que no se esté haciendo.** | Paneles contadores (3 → 9) |
| `anunciada` | Hay un compromiso público concreto, pero ni obra ni contrato adjudicado. **Incluye las licitaciones aprobadas y aún sin adjudicar.** | Carril bici de l'Albereda (licitación del 16/10/2026) |
| `en_marcha` | Contrato adjudicado, obra empezada o servicio funcionando en parte | GIVIC y controles de VMP; fin del ámbar intermitente (primera fase) |
| `hecha` | Terminada o en servicio | Pl. de Saragossa (reordenación de 2025 y fin del ámbar en 05/2026) |

Reglas:
- **Sin fuente no hay estado**: se queda en `sin_info`. Si la prueba es dudosa, se elige el estado más bajo y se explica en `nota`.
- **Lo anterior al 23/07/2026 cuenta** si es un servicio que sigue funcionando (GIVIC) o si el propio Ajuntament lo enmarca en el Plan (ámbar, 07/05/2026). Las campañas puntuales anteriores solo aparecen como antecedente en `nota`.
- `fuente_tipo = nota_prensa` también cuando la nota informa de un acuerdo de la Junta de Gobierno. Si hay anuncio en la Plataforma de Contratación, la fuente pasa a ser ese anuncio (`contratacion`), como en la v2.
- `fecha_estado` es la fecha de la prueba, no la de la comprobación. `comprobado` = 2026-11-04 en todas las filas.

Reglas fijadas por el usuario en la revisión de la v2 (Roberto Burgos, 04/11/2026):
1. **Programas enmarcados en el Plan.** Una medida anterior al Plan dentro de un programa que el Ajuntament enmarca en el Plan cuenta como `en_marcha` (p. ej. el fin del ámbar intermitente en Tarongers-Lluís Peixó, 03/2026).
2. **Medidas sin detalle.** Si una fuente dice que hubo medidas pero no detalla cuáles, el estado es `en_marcha`, no `hecha` (p. ej. Cardenal Benlloch-Av. del Port).
3. **Fechas.** `fecha_estado` = fecha de la fuente. La fecha del hecho, si se conoce, va en `nota`.
4. **Licitación desierta.** Mantiene `anunciada`, con una nota que lo explique. No hay estado nuevo (p. ej. Campos Crespo-Pius XI-Conca).
5. **Vocabulario único de `fuente_tipo`**, el del agente verificador: `contratacion`, `bop`, `junta_gobierno`, `nota_prensa`, `documento_municipal`, `prensa`, `respuesta_movilidad` y, además, `plan` para el propio Plan Director (solo como fuente de una actuación sin otra prueba publicada o que el Plan da por hecha; nunca para justificar un cambio de estado). `otro` desaparece: las dos filas de la v1 que lo usaban se migraron (edición validada por el usuario) a `nota_prensa` (anuncios del Debate del Estado de la Ciudad, nota de valencia.es) y `documento_municipal` (página de seguridad vial de valencia.es). Lo validan `scripts/aplicar_propuestas_plan.py` y `exportar_web.py`, y está en `.claude/agents/verificador-plan.md`.

## 3. Recuento

**Por estado** (46 actuaciones, tras la v2; en la v1 eran 42: 28 sin_info, 6 anunciadas, 6 en marcha y 2 hechas):

| Estado | Total | De ciudad | De lugar |
|---|---|---|---|
| sin_info | 28 | 24 | 4 |
| anunciada | 7 | 1 | 6 |
| en_marcha | 9 | 5 | 4 |
| hecha | 2 | 0 | 2 |

**Por acción del Plan:**

| Acción | Filas | Estados |
|---|---|---|
| 3.2.2 (ciclistas y VMP) | 22 | 6 en_marcha, 6 anunciadas, 10 sin_info |
| 3.7 (auditorías y cruces auditados) | 5 | 2 hechas, 1 en_marcha, 1 anunciada, 1 sin_info |
| 1.3.1 (fomento bici) | 3 | 3 sin_info |
| 3.5 / 3.5.1 (zonas 30, calles 20) | 3 | 1 en_marcha, 2 sin_info |
| 6.1.1 (mapa e informes) | 2 | 2 sin_info |
| 2.1 (controles) | 1 | en_marcha |
| 1.1.3, 1.2.1, 1.2.4, 3.2.3 c), 3.6, 6.2, 7.1.1, 7.1.2, 7.3.1, 7.3.4 | 1 cada una | sin_info |

Nota: se cuenta por la primera acción de `accion_plan`. La Pl. de Saragossa («3.7 / 3.2.2 c)»), Blasco-Benlloch-Clariano y Gran Via-Àngel Guimerà van en 3.7, porque derivan de la auditoría de 2024.

**Lo más relevante:**
- **Pl. de Saragossa**, `hecha`. Es el cruce n.º 1 del Plan tanto en VMP como en bici. En 02/2025 se reordenó la glorieta y en 05/2026 se eliminó el ámbar intermitente en dos ramales más.
- **Blasco Ibáñez-Cardenal Benlloch-Clariano**, `anunciada`. El proyecto de glorieta circular se aprobó el 30/09/2026 (973.083 €), pero aún no hay licitación adjudicada. Se hicieron medidas previas en 05/2025 y figura como anuncio n.º 32 del Debate.
- **Fin del ámbar intermitente (3.2.2 c)**, `en_marcha` desde el 07/05/2026 (primera fase).
- **Controles de VMP y GIVIC (2.1)**, `en_marcha`. El GIVIC funciona desde el 23/02/2026 y hubo controles en 05/2026 y en 06/2026. No hay balance posterior al Plan.
- **Carril bici (225 → 250 km)**, `en_marcha`. Están en obra Giorgeta y Pérez Galdós y hay cinco licitaciones o proyectos en 2026 (l'Albereda, Av. del Port, Campos Crespo y tres lotes). Muchos son traslados a la calzada, que no suman km.

## 4. Lo que no tiene nada publicado (sin_info)

- **Medición y transparencia**:
  - mapa de siniestros (6.1.1 c);
  - 6 informes de indicadores al año (6.1.1 b);
  - cuadro de mando (7.1.1);
  - memoria anual de siniestralidad (7.1.2);
  - informes a la Comisión de Seguridad Vial (7.3.1);
  - apartado de datos en la web de seguridad vial (1.2.4).

  Justo lo que el observatorio cubre en abierto.
- **Meta de 3.2.2**: no hay datos de 2026 en el portal. La única cifra pública es el balance del Plan Vector de ene-may 2026 (−50 siniestros con VMP).
- **Lista de zonas de elevada siniestralidad con ciclistas o VMP** (3.2.2): no está definida ni publicada.
- **Auditorías nuevas** (4 → 30): solo constan las 4 de 2024.
- **Cruces del Plan sin actuación publicada**:
  - Ausiàs March-Fernando Abril Martorell (VMP n.º 2);
  - Tarongers-Lluís Peixó (VMP n.º 3, bici n.º 2);
  - Fernando Abril Martorell-Ctra. de Malilla (bici n.º 3);
  - Cardenal Benlloch-Av. del Port (auditado en 2024);
  - Xàtiva-Jesús (el Plan lo cita como pendiente de estudio);
  - Jardí del Túria (bici n.º 1 y concentración de VMP).
- **Indicadores de 3.2.2 y 1.3.1**:
  - alfombras rojas;
  - pasos a contenedores;
  - grado de avance del Plan Director de la Bicicleta;
  - paneles contadores;
  - aparcabicis;
  - indicador de desplazamientos.
- **Otros**:
  - calles 30 (64 → 95 %);
  - evaluación de las zonas 30;
  - manual de obras con micromovilidad (3.6);
  - convenios de investigación (6.2);
  - empresas de bici y VMP (7.3.4);
  - campañas de convivencia posteriores al Plan.

## 5. Qué conviene preguntar al Servicio de Movilidad

Sirve para preparar la solicitud de información al Servicio de Movilidad. Se proponen estas preguntas, por orden de utilidad para el observatorio:

1. **Zonas de elevada siniestralidad (3.2.2)**: qué criterio usan y cuál es la lista, más allá de los 3 primeros cruces de 2.3.4.
2. **Auditorías (3.7)**: si hay auditorías nuevas contratadas o previstas para 2026-2027 y en qué tramos. Si les sirve la lista de puntos persistentes del observatorio como propuesta.
3. **Cruces del Plan sin actuación publicada**: si hay algo previsto en Ausiàs March-Abril Martorell, Tarongers-Lluís Peixó, Abril Martorell-Malilla, Cardenal Benlloch-Port y Xàtiva-Jesús.
4. **Ámbar intermitente**: la lista de los cruces donde ya se ha eliminado y el calendario para el resto. Así podremos marcarlos en el mapa y medir el antes y el después.
5. **Blasco Ibáñez-Cardenal Benlloch**: la fecha prevista de licitación y de obra.
6. **Cuadro de mando (7.1.1), memoria (7.1.2) e informes de indicadores (6.1.1)**: si serán públicos y en qué plazo. Cuál es la memoria que el Plan cuenta como línea base («1»). Ya es la pregunta 2 del correo; se puede ampliar.
7. **Indicadores de infraestructura**: el valor actual de km de carril bici, ciclocalles, alfombras rojas, pasos a contenedores, paneles contadores y aparcabicis. Hay dudas de línea base:
   - ciclocalles: el Plan da 18 km y el Ajuntament hablaba de 46,89 km en 11/2025;
   - aparcabicis: el Plan da 22.638 y el Ajuntament 22.958 en 11/2025.
8. **Convenios (6.2)**: si hay alguno firmado o en trámite y cuál es el procedimiento para proponer uno.
9. **Memoria de actuaciones de movilidad 2023-2026** (07/2026): si hay una versión ligera o datos tabulados. El PDF pesa más de 10 MB y no se ha podido leer.

## 6. Límites de esta versión

- **No se ha consultado la Plataforma de Contratación** del Sector Público. Puede haber adjudicaciones que cambien licitaciones de `anunciada` a `en_marcha`.
- **No se ha leído la Memoria de actuaciones de movilidad 2023-2026.** Seguramente cambie algunos `sin_info` de infraestructura.
- **Varias fuentes son de prensa**: ciclocalles, calles 20 y Giorgeta. Falta la nota municipal original.
- **El estado de las actuaciones de lugar no se ha visto sobre el terreno.**
- **Mantenimiento**: el CSV se edita a mano. `coords_plan_seguimiento.py` solo rellena las coordenadas vacías y no pisa el resto.

## 7. v2 (04/11/2026): propuestas revisadas y aplicadas

> **Desde el 06/11/2026 el seguimiento validado vive en la base** `data/processed/observatorio.sqlite` (tablas `plan_fuente`, `plan_actuacion`, `plan_actuacion_fuente` y `plan_actuacion_lonlat`), que es su fuente de verdad. En git va su **volcado en texto**, `data/processed/observatorio_plan.sql` (una sentencia `INSERT` por fila, en orden fijo), y `plan_seguimiento.csv` pasa a ser su **exportación**: la leen el agente `verificador-plan` y quien revisa, pero ya no se edita a mano. Lo que sigue describe la v2 tal como se hizo, con el CSV como fuente; el procedimiento vigente está en la sec. 8. Campos de la base: `fecha_fuente` (era `fecha_estado`), `fecha_comprobacion` (era `comprobado`), `ref_plan` y `texto_plan` (las dos partes de `cita_plan`), `fuente_id` (la principal, `fuente_url`), `fuente_estado_id` (la que respalda el estado; si la principal es el propio Plan, la única URL de la nota) y `clase` (`indicador_impacto` o `medida`).

**Aplicada el 04/11/2026.** Roberto Burgos revisó las 56 propuestas (`decision`, `revisado_por` y `fecha_revision` rellenos en todas): **53 aceptadas y 3 rechazadas**, y `scripts/aplicar_propuestas_plan.py --aplicar` las aplicó sin conflictos.
- **Aceptadas:** todas las de confianza alta (21 `sin_novedad`, 18 correcciones y 6 fuentes nuevas), más -001 (Tarongers-Peixó → en_marcha), -003 (Benlloch-Port → en_marcha, no hecha), -020, -024, -025 (Gaspar Aguilar), -026 (Viveros con VMP), -027 (3.2.3 c, carril bici escolar) y -035 (Nicolás Factor), esta última condicionada a confirmar la calle.
- **C/ Nicolás Factor = C/ Beat Nicolau Factor.** Se confirmó en el callejero municipal: en `vias.json` es `codvia` 9450, «BEAT NICOLAU FACTOR» (en castellano, «BEATO NICOLAS FACTOR»). En `ejes.geojson` se cruza con María Jordán (45450) y Assagador de les Monges (7830), los dos extremos de la licitación (tramo de unos 60 m del eje). Los siniestros del portal la llaman «C/ BEATO NICOLAS FACTOR». Se corrigieron `actuacion` y `lugar` con el nombre oficial antes de aplicar.
- **Rechazadas** (motivo en `motivo`): -005 (pasos a contenedores: sin número ni lugar y anterior al Plan; se queda la nota), -015 (la nota mezclaba los cruces del ámbar con la lista de zonas de elevada siniestralidad) y -028 (formación general, fuera del alcance de bici y VMP).
- **Resultado:** 46 actuaciones: 2 hechas, 9 en marcha, 7 anunciadas y 28 sin información pública. La previsión de abajo («de 42 a 47… en_marcha 6 → 10») suponía aceptarlo todo. Sin -005 y -028, el resultado es 46 con 9 en marcha: 6 + Tarongers-Peixó + Benlloch-Port + Gaspar Aguilar, que entra en obra como Giorgeta. Hay 28 sin_info: 28 − 2 + Viveros + carril escolar.
- **Coordenadas de las filas nuevas de lugar** (`scripts/coords_plan_seguimiento.py`):
  - Gaspar Aguilar: mediana de los 174 siniestros geocodificados de la avenida (aproximada, como Campos Crespo);
  - Beat Nicolau Factor: punto medio del eje del callejero entre sus cruces con María Jordán y Assagador de les Monges (`TRAMOS_EJES`).
- **Migración de `fuente_tipo`** de la v1 al vocabulario único (sec. 2, regla 5).
- Las dudas de abajo quedan resueltas con las reglas 1-5 de la sec. 2 y con estas decisiones.

Texto de la v2 tal como se escribió antes de la revisión:

El CSV validado (`plan_seguimiento.csv`) seguía como en la v1. Las propuestas están en `data/processed/plan_seguimiento_propuestas.csv`, con el esquema del agente `verificador-plan` (`.claude/agents/verificador-plan.md`): una fila por cambio, con fuente, fecha, cita literal corta, confianza y `decision = pendiente`. Ningún cambio de estado se publica sin que una persona lo valide.

**Recuento** (56 filas):

| Tipo | Filas | Confianza |
|---|---|---|
| cambio_estado | 3 | 2 media, 1 baja |
| nueva_fuente | 6 | 6 alta |
| correccion (notas) | 21 | 18 alta, 3 media |
| nueva_actuacion | 5 | 4 media, 1 baja |
| sin_novedad | 21 | constancia de la comprobación |

**Cambios de estado propuestos** (si se acepta todo, con las 5 filas nuevas, de 42 a 47 actuaciones: sin_info 28 → 28, en_marcha 6 → 10, anunciada 6 → 7, hecha 2):
- **Tarongers-Lluís Peixó** (`3.2.2-naranjos-peixo`), sin_info → en_marcha, confianza media. La Memoria de actuaciones lo pone el primero de los cruces «detectados como conflictivos» donde se quitó el ámbar intermitente (03/2026). Es anterior al Plan, pero es el mismo programa que el Ajuntament enmarca en el Plan.
- **Cardenal Benlloch-Av. del Port** (`3.7-benlloch-puerto`), sin_info → en_marcha, confianza media. La Memoria dice que en los cuatro puntos auditados se impulsaron medidas y lo incluye en el fin del ámbar de 05/2026, pero no detalla qué se hizo en este cruce.
- **Pasos a contenedores** (`3.2.2-pasos-contenedores`), sin_info → en_marcha, confianza **baja**: la Memoria dice que «se están señalizando», sin número ni lugar. Alternativa: rechazarlo y quedarse con la nota.

**Otras propuestas importantes:**
- **Campos Crespo-Pius XI-Conca: la licitación de la obra quedó desierta** (ninguna oferta; resultado publicado en la PLACSP el 12/08/2026) y la de dirección de obra acabó en renuncia. No consta nueva licitación a 31/10/2026. Sigue `anunciada`, pero la nota tiene que decirlo. Lo mismo pasó con la Av. de la Plata (desierta, 06/2026), que vuelve como lote de los tres lotes de 10/2026.
- **Anuncios oficiales de la PLACSP** para l'Albereda, la Av. del Port y los tres lotes: todos publicados y sin adjudicar, así que siguen `anunciada`.
- **Fin del ámbar (3.2.2 c)**: nueva fuente posterior al Plan (27/08/2026: «supresión del ámbar intermitente en 20 cruces conflictivos») y la lista de los 17 cruces de la Memoria, con el mapa municipal de Google. Permite ponerlos en el mapa y medir el antes y el después.
- **Ciclocalles y calles 20**: la fuente de prensa se cambia por la municipal (nota del 22/09/2026 y Memoria). La Memoria da un dato comparable con el indicador de calles 20 (2,39 % de las calles a 20 km/h), pero hay que aclarar la definición.
- **Contratos oficiales** en las notas de Giorgeta-Pérez Galdós (formalizado el 12/06/2025, 23,96 M€) y del camino ciclopeatonal del Túria (12/06/2026, 1,87 M€).
- **Actuaciones nuevas**:
  - carril bici de Gaspar Aguilar (en obra, mismo criterio que Giorgeta);
  - 1.1.3, Centro de Educación Vial de Viveros con VMP;
  - 3.2.3 c), carril bici en el entorno escolar;
  - itinerario ciclista y peatonal de la C/ Nicolás Factor, licitado el 20/10/2026 (236.232,97 €; falta comprobar qué calle es);
  - 1.1.1, formación que incluye VMP (confianza baja; solo si se quiere cubrir toda la formación).
- **Lo que no cambia y queda documentado**: no hay auditorías nuevas, ni grado de avance del Plan Director de la Bicicleta. La Memoria no es una memoria de siniestralidad. Ninguna licitación de bici de 2026 tiene adjudicación: unas siguen en plazo y otras quedaron desiertas. Blasco-Benlloch no aparece licitada.

**Fuentes consultadas en la v2** (detalle y calificación en `data/processed/plan_fuentes.csv`):
- **Memoria de actuaciones de movilidad 2023-2026** (13 MB, 48 págs.): WebFetch falla por el límite de 10 MB. Se descargó con una petición normal (curl, sin cabeceras ni técnicas para sortear el WAF de valencia.es), que respondió 200, a un directorio temporal, y se extrajo el texto con pdftotext. Es la fuente que más ha dado. Ojo: casi todo es anterior al Plan.
- **Buscador de contratos del Ajuntament** (Gobierno abierto, `buscador-2026`): 798 contratos formalizados de 2018-2026, descargados en una página. La formalización más reciente es de 06/2026, así que no cubre las licitaciones de Movilidad de 2026. El filtro de texto por URL no funciona.
- **Plataforma de Contratación (PLACSP)**:
  - el buscador web es un formulario JSF, que no se puede consultar por URL ni encontrar con buscadores;
  - la descarga de datos abiertos (ZIP mensual) es muy lenta (~200 kB/s, sin reanudación). Resultado en la línea siguiente.
  - se bajaron los ZIP de 10/2026 (194 MB) y 09/2026 (303 MB) y se filtraron por órgano del Ajuntament y palabras clave (ahora con `scripts/placsp_valencia.py filtrar`). Ha sido la fuente más precisa: estado de cada licitación, ofertas, desiertas y renuncias. El de 08/2026 se dejó a medias por tiempo, así que **julio y agosto no se han revisado** en la PLACSP.
- **BOP de València**: búsqueda por formulario con sesión, sin URL de búsqueda. No se ha buscado dentro.
- **Acuerdos de la Junta de Gobierno Local**: no se publican extractos. El Pleno «da cuenta» de las sesiones sin detalle. Solo se conocen por las notas municipales.
- **Notas de valencia.es** (WebFetch, sin bloqueo): fin del ámbar en 20 cruces (27/08/2026) y ciclocalles (22/09/2026). La sección de seguridad vial sigue sin datos ni memoria.
- **Búsquedas web** (unas 15): sin adjudicaciones de 2026, sin convenios de seguridad vial (6.2), sin aparcabicis nuevos (lo último es de 2023) y sin campañas de VMP posteriores a 06/2026.

**Dudas para quien revise:**
1. ¿Una medida anterior al Plan (03/2026) en un cruce del Plan cuenta como en_marcha si es parte del programa del ámbar?
2. ¿Benlloch-Port tiene que ir en en_marcha, o en hecha como Gran Via-Guimerà?
3. `fecha_estado`: ¿la fecha de la Memoria (27/07/2026) o la del hecho (03/2026, 05/2026)? El criterio dice «fecha de la prueba», y por eso se ha puesto la de la Memoria.
4. **C/ Nicolás Factor**: ¿entra en el alcance? Es una licitación de itinerario ciclista que no toca lugares del Plan. ¿Es la C/ Beat Nicolau Factor? Comprobarlo en el callejero.
5. **Campos Crespo, desierta**: ¿se mantiene en `anunciada` mientras no haya otra licitación? El criterio no prevé un estado para «desierta», y se propone no inventarlo.
6. **Vocabulario de `fuente_tipo`**: el CSV v1 usa `plan` y `otro`, y las propuestas usan el del verificador (`documento_municipal`, `contratacion`…). El script de aplicación acepta los dos. Conviene decidir si se migra el v1.

## 8. Procedimiento trimestral

Una revisión cada trimestre (enero, abril, julio y octubre), con revisión humana antes de publicar. **El criterio de estados es el de la sec. 2 y no cambia.**

1. **Lanzar el agente `verificador-plan`** (`.claude/agents/verificador-plan.md`) con alcance «revisión trimestral». Lee este documento, el CSV validado, las propuestas pendientes y `data/processed/plan_fuentes.csv`. Consulta las fuentes en este orden, saltándose o dejando para el final las que el registro marca `util = no`:
   1. **PLACSP**, con los datos abiertos: los ZIP mensuales de la sindicación 643 de los tres meses del trimestre.
      - Herramienta: `scripts/placsp_valencia.py` (datos abiertos mensuales de la PLACSP). `descargar AAAA-MM …` baja los ZIP de uno en uno, con pausa entre descargas, a `data/raw/placsp/` (no se versiona); `filtrar <zips> -o <csv>` deja las entradas del Ajuntament que casan con las palabras clave, con estado, resultado, adjudicatario, importe y enlace a la ficha.
      - Cada uno pesa unos 200-300 MB y tarda 10-20 min: bajarlos en segundo plano, de uno en uno.
      - Se filtran por órgano («Junta de Gobierno del Ajuntament de València» y «Concejalía Delegada de Contratación del Ajuntament de València») y por palabras clave.
      - De cada licitación se mira el estado (PUB, EV, ADJ, RES) y el resultado (`TenderResultCode`: 3 desierto, 5 renuncia; adjudicado o formalizado, con adjudicatario e importe). Se confirma en la ficha (deeplink) con WebFetch.
      - El buscador de contratos del Ajuntament solo llega a 06/2026: sirve para lo antiguo.
   2. BOP y acuerdos de la Junta de Gobierno.
   3. Notas de valencia.es (Movilidad, Policía Local).
   4. Documentos municipales: Memoria de actuaciones, informes y Comisión de Seguimiento.
   5. Prensa, solo como pista.

   Deja 3-4 s entre peticiones al mismo servidor y no sortea ningún WAF. Escribe filas nuevas en `plan_seguimiento_propuestas.csv` con `decision = pendiente`: una por cambio y una `sin_novedad` por cada actuación revisada sin cambios. También actualiza `plan_fuentes.csv` (consultas, aciertos, accesibilidad).
2. **Revisión humana.** La persona lee cada propuesta pendiente, abre la fuente y rellena:
   - `decision` (`aceptada` o `rechazada`);
   - `revisado_por`;
   - `fecha_revision`.

   Revisa primero los `cambio_estado` y la confianza `baja`. Si una propuesta no tiene fuente verificable, la rechaza. Si un rechazo enseña algo, lo anota en `motivo`.
3. **Ensayo:** `.venv/bin/python -I scripts/aplicar_propuestas_plan.py` (por defecto, `--dry-run`). Antes, `make sqlite` si hace falta: el script se para si el Plan de la base no es el de `observatorio_plan.sql`. El ensayo:
   - lista qué aplicaría y qué salta, por conflicto (el valor actual de la base ya no es el de la propuesta) o porque falta quien revisa;
   - valida el esquema y los estados permitidos;
   - escribe los cambios en la base **dentro de una transacción y la deshace**: así también prueba las restricciones de la base (un estado distinto de `sin_info` sin fuente o sin fecha de la fuente, una fecha de la fuente posterior a la de la comprobación, un tipo de fuente fuera del vocabulario…);
   - no escribe nada.

   Las propuestas siguen con los nombres del CSV exportado (`fecha_estado`, `comprobado`, `cita_plan`…); en una `correccion`, `campo` admite también `fecha_fuente`, `fecha_comprobacion`, `ref_plan` y `texto_plan`.
4. **Aplicar:** `.venv/bin/python -I scripts/aplicar_propuestas_plan.py --aplicar`. El script:
   - escribe en la base con `UPDATE` (actuaciones que existen) e `INSERT` (nuevas y fuentes nuevas) en **una sola transacción**: si una fila incumple una restricción, no se aplica ninguna;
   - actualiza estado, fecha de la fuente, fuente principal y fuente del estado, nota y fecha de comprobación, y borra las fuentes que ya nadie cita;
   - hecho el `COMMIT`, reescribe el volcado `data/processed/observatorio_plan.sql` y la exportación `data/processed/plan_seguimiento.csv`;
   - marca cada propuesta con la fecha en `aplicada`.

   Las coordenadas de las filas nuevas de lugar se rellenan con `scripts/coords_plan_seguimiento.py`, que escribe en el CSV: después, `construir_sqlite.py --plan-desde-csv` las lleva a la base (y al volcado).
5. **Revisión humana de lo que se va a publicar:** `git diff data/processed/plan_seguimiento.csv data/processed/observatorio_plan.sql`. El CSV se lee mejor; el volcado enseña además lo que el CSV no tiene (la fuente del estado y el tipo de cada fuente). Si algo está mal, se corrige con otra propuesta (o se deshace con `git checkout` de los dos ficheros y `make sqlite`).
6. **`make web`**, que reconstruye la base desde el volcado (con lo derivado: junto a qué lugar o calle cae cada actuación) y regenera la web y las fichas. Se revisa en localhost antes de publicar. **Commit del volcado y del CSV juntos**: el deploy reconstruye la base desde el volcado de HEAD, así que un cambio sin commit no se publica.
7. **Una fila curada en `docs/cambios.csv`** por revisión, no una por actuación. Lleva la fecha y el tipo `datos`, en va y en es. Por ejemplo: «Revisión trimestral de "El Plan, al día": 3 actuaciones cambian de estado, 2 nuevas; fuentes: Memoria de actuaciones y contratos».
8. Actualizar el recuento de la sec. 3 y dejar constancia de la revisión en la lista de tareas del proyecto.

**Salvaguardas** (`make sqlite`, `make comprobar`):
- si `plan_seguimiento.csv` se ha editado a mano (no coincide con la exportación de la base), `make sqlite` se para sin sobrescribirlo. Para incorporar la edición a propósito: `construir_sqlite.py --plan-desde-csv` y revisar el diff del volcado; para descartarla, `git checkout` del CSV;
- si la base tiene cambios del Plan que no están en el volcado (alguien la editó con otra herramienta), `make sqlite` se para; `construir_sqlite.py --volcar` los guarda en el volcado y el CSV;
- `make comprobar` da ERROR si el volcado o el CSV no son los de la base.

**Registro de fuentes** (`data/processed/plan_fuentes.csv`): tiene una fila por fuente, con lo que publica de verdad, si es útil (`si`/`parcial`/`no`) y si es accesible (`si`/`waf`/`pdf_grande`…), además de las consultas y los aciertos acumulados. Sirve para no gastar consultas en fuentes que nunca aportan. Una fuente que solo repite notas municipales sin dato propio cuenta como `no`. Un agregador nunca es fuente.

## 9. Correcciones validadas por el usuario (04/11/2026)
Aplicadas a mano en `data/processed/plan_seguimiento.csv`, fuera del flujo de propuestas (desde el 06/11/2026, una corrección así se hace con una propuesta `correccion` o editando el CSV y `construir_sqlite.py --plan-desde-csv`, con revisión del diff del volcado):
- `3.2.2-meta-siniestros`: la nota decía «Propuesta del observatorio: base 2024». Pasa a base 2025 (1.659 → 830), la de la meta del observatorio.
- `7.1.1-cuadro-mando`: se quita la mención a un partido. Queda solo el hecho y su fuente. Revisado el CSV entero: no hay más partidos. También se quitan las frases internas o de parte: «Preguntar…» (3.2.2-zonas-lista y 7.1.2), «Candidatas: la lista de puntos persistentes del observatorio» (3.7) y «Es la vía de entrada de un socio del observatorio» (6.2).
- `1.2.4-web-seguridad-vial`: se queda en `sin_info`. Nota: «La web existe, pero sin el apartado de datos que prevé el Plan…».
- Los textos de actuaciones, notas y citas no se traducen: la web los muestra en la lengua original de la fuente.
