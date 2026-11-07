# Revisión del relato y de las afirmaciones públicas (04/11/2026)

Ámbito: razonamiento de conjunto y afirmaciones públicas de `informe.plantilla.html` (REL), `observatori.plantilla.html` (OBS) y `metode.plantilla.html` (MET), con cifras de `web/proto/datos/*.js`. En OBS cuentan los textos del último `Object.assign` («glosario de la revisión de coherencia»), que sustituyen a los anteriores. Comprobaciones propias en `docs/revision_metodologica/scripts/relato/` (`chk1.py` … `chk7.py`), sobre `data/processed/siniestros_geo.csv` (años 2022-2025, sin duplicados exactos). No se ha tocado nada del proyecto.

## (a) Problemas, por prioridad

### 1. CRÍTICA · CONFIRMADO: «Fuera del radar del Plan» no se sostiene, por la lógica y por un fallo de cruce
**Dónde:** OBS `hall_plan` (es/va, último assign), anillo del mapa; REL `donde` («discontinuo, no lo menciona (15)»); MET `plan` (tabla 4/11/15); `scripts/exportar_web.py` `CLAVES` y `plan_de()`.

**Por qué (lógica):** las listas del Plan (`pdsv_lugares.csv`) son **top-3**: 3 cruces con VMP, 3 con bici, 3 con peatones y 3 calles por colectivo. Con eso, de nuestros 30 lugares solo unos pocos *pueden* aparecer citados como lugar. Que no aparezcan en una lista de tres no prueba que estén «fuera del radar». El Plan dice que la Policía actúa «en los puntos con más siniestros», y la acción 3.2.2 habla de «zonas de elevada siniestralidad» sin listarlas. El titular atribuye al Ayuntamiento algo que el documento no permite afirmar.

**Por qué (código):** `plan_de()` se salta en silencio las filas de `pdsv_lugares.csv` que no tienen entrada en `CLAVES` (`if not cl: continue`). Quedan fuera, entre otras, «Tres Cruces - Campos Crespo» (cruce), «Av. de Peris y Valero» (punto), «C/ Xàtiva» (calle, con actuación), «Peset Aleixandre - Camí de Montcada» y «Giorgeta - Jesús». He cruzado esas claves con las direcciones de los 30 lugares (`chk5.py`):
- AV TRES CRUCES × C/ CAMPOS CRESPO: `pl = 0` («no lo menciona»), pero el Plan cita **ese mismo cruce** (peatones, 7 siniestros). Debería ser 1.
- C/ PELAYO × C/ XÀTIVA: `pl = 0`; el Plan cita la calle Xàtiva con una actuación. Con la regla B debería ser 2.
- AV PERIS Y VALERO × DUQUE DE CALABRIA: `pl = 0`; el Plan cita la Av. de Peris y Valero. Debería ser 2.

Con esto el reparto pasa de **4 / 11 / 15 a 5 / 13 / 12**. `make comprobar` no lo detecta, porque solo comprueba que los tres números sumen 30 y coincidan entre páginas.

**Redacción alternativa:** «El Plan publica solo los tres cruces y las tres calles con más siniestros de cada colectivo. De nuestros 30 lugares, cita 5 por su nombre y 13 por su calle. Del resto no dice nada: ni que se vaya a actuar ni que no. Pedimos la lista completa que usa la Policía Local.» Y en el código: generar `CLAVES` para **todas** las filas (o que un `assert` falle si una fila no tiene claves).

### 2. ALTA · CONFIRMADO (cifra) / PLAUSIBLE (causa): la subida de 2022-2025 no es propia de la bici y el patinete
**Dónde:** OBS `hall[0]` («Más siniestros, no menos», +24 %), `h_meta`/`partida_max` («Parte del peor año de la serie… un 24 % más»); REL `y2025` («El Plan arranca con la tendencia en contra»); MET `uso`.

**Por qué:** todos los siniestros de la ciudad crecen exactamente lo mismo: 7.462 → 9.252 (**+24,0 %**, frente al +23,9 % de bici o patinete). La parte de bici y patinete se mantiene en el 17,9 % en 2022 y en 2025 (`chk1.py`). Lo que más crece en la ciudad son los siniestros **sin heridos** (4.354 → 5.719, +31 %; con bici o patinete, 283 → 380, +34 %), que es la huella típica de un cambio de registro. El Plan describe la creación del SIASV en julio de 2024, «adaptando el registro a los estándares de la DGT» (pdsv.txt l. 553-560, 960, 2407), y los accesos de tráfico a motor bajan frente a 2019 (l. 271-276). Hay señal real: los siniestros con heridos de bici o patinete suben un 21 % (1.056 → 1.279), frente a un +10 % del resto. Pero ninguna página separa lo real de lo administrativo. Además, si el registro vuelve a cambiar en 2026, la evaluación de la meta quedará contaminada.

**Redacción alternativa** (OBS hall[0] y REL y2025): «Entre 2022 y 2025 los siniestros con bici o patinete pasan de 1.339 a 1.659 (+24 %), lo mismo que todos los siniestros de la ciudad. Parte puede deberse a cómo se registran: lo que más crece son los siniestros sin heridos. Con heridos, los de bici o patinete suben un 21 % y el resto, un 10 %.» Añadirlo a `lim` y a MET `limites`.

### 3. ALTA · CONFIRMADO: el año base es el máximo de la serie y favorece la evaluación del Plan
**Dónde:** REL `partida` («y el peor de la serie»); OBS `nota_base`; MET `meta`.

**Por qué:** si se toma como base el pico de la serie, el año siguiente tiende a salir por debajo por simple vuelta a lo habitual (regresión a la media), y más aún si parte del pico es de registro (punto 2). El proyecto presenta como mérito que 2025 sea «el peor», pero no advierte de que eso inclina la balanza a favor del «van al ritmo». La meta del Plan se seguirá con esta base, que es la función central del observatorio.

**Redacción alternativa** (MET `meta`, nueva viñeta): «Ojo: ${B} es el peor año de la serie. Un año récord suele ir seguido de uno menor aunque no cambie nada, así que una bajada en ${MT.desde} no bastará para decir que el Plan funciona. Por eso mostramos también la base ${E1.año} y la media 2023-2025 (≈ 1.544).» Añadir esa tercera fila a la tabla de escenarios.

### 4. ALTA · CONFIRMADO: la bajada de Alameda–Zaragoza depende de cómo se anota la dirección y de la regresión a la media
**Dónde:** REL `alameda3` («Los siniestros han bajado: de 16 en 2023 a 6 en 2025»).

**Por qué** (`chk3.py`):
- La celda baja 16 → 16 → 10 → 6, pero la dirección literal «PG ALAMEDA cruce PL ZARAGOZA» pasa de 14 → 11 → 7 → **2**.
- En todo el paseo de la Alameda, los siniestros con bici o patinete son 50, 50, 39 y **44**: no bajan en 2025. En las 9 celdas de alrededor, 28, 23, 21 y 10.
- La parte situada «por cruce» baja en toda la ciudad (bici o VMP: 69,5 % en ene-sep 2022, 57,8 % hasta jun 2024, 49,5 % después). Con el cambio de formato del portal (julio de 2024, el mes en que se crea el SIASV), los siniestros de un cruce se reparten entre portales cercanos. Así, una celda centrada en un cruce pierde casos aunque no cambie nada.
- La bajada empieza en 2024, antes de la reordenación de 2025.
- El lugar se eligió por ser el n.º 1 (el Plan lo auditó por eso): es el caso de libro de regresión a la media.

La frase «es pronto para atribuirlo a la obra» se queda corta.

**Redacción alternativa:** «En el cuadrado del cruce, los siniestros pasan de 16 en 2023 a 6 en 2025. Pero en todo el paseo apenas cambian (39 en 2024, 44 en 2025) y desde mediados de 2024 la policía anota menos siniestros "en el cruce" y más por número de portal. Un lugar elegido por ser el peor suele mejorar algo por sí solo. Sin un grupo de comparación no se puede atribuir a la obra.»

### 5. MEDIA · CONFIRMADO: la cabecera «Dónde actuar» sobre un mapa de recuentos sin exposición
**Dónde:** OBS `ey_mapa` («Dónde actuar» / «On actuar»), sin sustituir en ningún assign posterior.

**Por qué:** la vista por defecto son los lugares con más siniestros, que el propio texto dice que «no significa que sea el lugar más peligroso». La cabecera prescribe la actuación que el método no permite deducir. El cribado EB, la única capa con exposición, cubre el 22 % de los siniestros y no predice mejor que el recuento.

**Redacción alternativa:** «Dónde se acumulan» / «On s'acumulen» (o «Dónde mirar primero»).

### 6. MEDIA · CONFIRMADO: «seguridad en número» presentada como ley
**Dónde:** MET `normal`, última viñeta: «No es un riesgo por persona: los siniestros crecen menos que el tráfico (cuando el tráfico se duplica, los siniestros no)».

**Por qué:** es una elasticidad **transversal** entre puntos (0,66), no lo que pasa cuando crece el tráfico de un punto. Con solo bici sale 0,87, compatible con 1 (las notas internas de trabajo). Que en el conjunto salga menor que 1 puede deberse a que la proporción de patinetes cambia de un punto a otro (si las espiras los suman), a error de medida en la IMD (que atenúa la pendiente) o a que se usa un radio de 100 m alrededor del contador. MET `tec` da el 0,87 sin decir que es compatible con 1.

**Redacción alternativa:** «Entre puntos de conteo, los que tienen el doble de tráfico no tienen el doble de siniestros (elasticidad 0,66). Con solo bicis la diferencia desaparece (0,87, compatible con 1), así que puede deberse a la mezcla de bicis y patinetes que cuentan los contadores. No dice qué pasará si crece el tráfico de un punto.»

### 7. MEDIA · CONFIRMADO: la «pista» sigue comparando con la media de la ciudad (ya señalado y sin corregir)
**Dónde:** OBS `pista`/`pista_nota`; `exportar_web.py` l. 154-160.

**Por qué:** la referencia sigue siendo la media de toda la ciudad (incluye el Turia, con 96 caídas de 165). Los 30 lugares son casi todos cruces (lo dice MET: 76 % situados como cruce, frente al 56 % de la ciudad). Que salga «m» (vehículo a motor) en Alameda, Ausiàs March, Alcalde Reig y Antonio Ferrandis es casi tautológico. Holm corrige 4 pruebas por lugar, pero hay unas 12-30 fichas probadas y no se corrige entre lugares. La «pista» propone medidas («Mirar la prioridad, los semáforos…») que salen de la comparación con la media.

**Redacción alternativa:** comparar con los cruces de la ciudad (o con los lugares del mismo tipo) y redactarlo así: «Aquí, 9 de cada 10 siniestros son con un vehículo a motor; en los cruces de la ciudad, X de cada 10.» La recomendación, solo cuando la diferencia sobreviva a esa comparación.

### 8. MEDIA · CONFIRMADO: «se repiten» se mide con los mismos datos que eligen los lugares
**Dónde:** OBS `hall[2]` («13 de 30… entre los 60 con más siniestros en los tres periodos»); REL `donde` («no es cosa de un año»); MET `lugares`.

**Por qué:** los 30 se eligen con el total 2022-2025, que incluye los tres periodos. Mi reproducción (cuadrícula UTM y pesos de MET; la diferencia con 13 puede ser de duplicados o empates) da 11 en las tres etapas. Fuera de muestra (ordenar con 2022 a jun 2024 y mirar jul 2024-2025), **16 de 30** entran en el top-60, frente a 23 de 30 dentro de muestra. Con cobertura corregida, esos 30 tendrían unos 269 siniestros en P3 si se mantuvieran y tienen 222: un 18 % de vuelta a la media. Además, los periodos de los textos se solapan («2022, 2022-24 y 2024-25») y el primero tiene 9 meses.

**Redacción alternativa:** «Si ordenamos los lugares con los datos hasta junio de 2024, la mitad (16 de 30) sigue entre los 60 primeros después: la concentración se repite, aunque menos de lo que parece.» Y escribir los periodos con meses: «ene-sep 2022, oct 2022-jun 2024, jul 2024-dic 2025».

### 9. MEDIA · CONFIRMADO: la meta del Plan, presentada como compromiso de ciudad
**Dónde:** REL `sub` («València quiere reducir a la mitad los siniestros con bicis y patinetes para 2030»), `promesa` («El Plan… se compromete a reducir a la mitad»); OBS `h_meta` («El Plan quiere reducir a la mitad…»).

**Por qué:** es el indicador de impacto de una acción (3.2.2, «Mejorar la seguridad vial en los itinerarios ciclistas existentes»), no la meta del Plan, que es de fallecidos y heridos graves (apartado 4.4). Además, casi **todos** los indicadores de impacto tienen la línea base «—» (`plan_pdsv_resumen.md` §2): presentar esa casilla vacía como una omisión singular («¿La mitad de qué?») es injusto con el documento. MET lo explica bien, pero la portada y el informe no.

**Redacción alternativa:** «Una de las acciones del Plan (la 3.2.2) se pone como indicador reducir a la mitad los siniestros con ciclistas y patinetes para 2030. Como casi todos los indicadores del Plan, no dice respecto a qué año.»

### 10. MEDIA · PLAUSIBLE: infradeclaración diferencial y cambios de vigilancia, sin mencionar
**Dónde:** REL `quien2` («El patinete pasa de 825 a 1.190»); MET `limites` (solo cita, en general, «siniestros que no registra la Policía Local»).

**Por qué:** solo entran los siniestros con atestado. Las caídas sin terceros (25 % del total; muy probablemente infradeclaradas) y los cambios de vigilancia sobre el patinete (ordenanza, controles del Plan Vector, casco obligatorio desde octubre de 2026, registro de la DGT) pueden cambiar con el tiempo, y de forma distinta para la bici y el patinete, cuántos siniestros acaban registrados. Eso afecta a la cuota «7 de cada 10» y a la evaluación de 2026 en adelante.

**Redacción alternativa** (MET `limites`): «Solo vemos los siniestros que registra la Policía Local. Si cambia cuánto se vigila o se denuncia el patinete (controles, casco obligatorio desde octubre de 2026), puede cambiar el número registrado sin que cambie el riesgo.»

### 11. MEDIA · CONFIRMADO: «revisiones externas» y «el código es abierto»
**Dónde:** MET `revisiones` («Dos revisiones externas, hechas por agentes revisores…»; «El código es abierto»); OBS `d3_p` («Todo el código es abierto»); MET `revisiones` («Ninguna cifra de las páginas está escrita a mano»).

**Por qué:**
- Las revisiones son de agentes automáticos lanzados por el propio proyecto, no externas. Quien lo lea puede entenderlo como revisión por pares.
- El repositorio no está publicado (pendiente 62).
- Hay cifras transcritas a mano: `ctx2026` (−50, de una noticia), `plan_graves_2024` (176/167/185, pendiente 63), los porcentajes de los conteos manuales y los tres puntos destacados de REL `trafico3` (`DEST`, por nombre).

**Redacción alternativa:** «Dos revisiones automáticas independientes del análisis (agentes de IA sin acceso a nuestras notas)…»; «El código se publicará en [enlace]»; «Ninguna cifra calculada está escrita a mano; las que vienen de documentos (Plan, prensa, conteos manuales) están transcritas y citadas.»

### 12. BAJA-MEDIA · CONFIRMADO: «baja gravedad» sigue cambiando en 2025
**Dónde:** REL `falta2` y OBS `lim[0]` («la serie solo se puede comparar desde 2024»).

**Por qué:** los graves de 2024 y 2025 son coherentes por semestre (67/100 frente a 74/107), así que esa afirmación aguanta. Pero «baja gravedad» sube de 158 a 227 (+44 %) con bici o patinete entre 2024 y 2025 (ciudad: +24 %, con un salto en el segundo trimestre de 2025), mientras los siniestros suben un 10,5 %. El Plan agrupa graves y baja gravedad como «heridos de gravedad». MET `tec` lo apunta, pero las páginas principales no.

**Redacción alternativa** (`lim[0]`): «… Los graves solo se pueden comparar desde 2024, y la categoría "baja gravedad" sigue creciendo en 2025 por cambios de clasificación.»

### 13. BAJA · CONFIRMADO: coherencia entre páginas y docs
- **OBS `proto`** atribuye las diferencias con el Plan a que «el Plan cuenta por vehículo». MET `tec` y `plan_pdsv_resumen.md` dicen que es por la **fecha de extracción**. Hay que unificarlo con la explicación de la fecha.
- **OBS `hall_plan`**: «ni el lugar ni su calle entre las de más siniestros». Con la regla B, también cuenta la calle citada por un radar o en la lista de peatones (MET `plan`). Mejor: «ni el lugar ni su calle por ningún motivo».
- **las notas internas de trabajo**, sección «Anillo del Plan en tres niveles»: dice 4 / 6 / 20 (regla sin peatones ni radares). Las páginas y la lista interna de pendientes (67) dicen 4 / 11 / 15. Actualizar las notas internas de trabajo (y, tras el punto 1, 5 / 13 / 12).
- **OBS `hall[1]`** «El patinete ya es mayoría»: ya lo era en 2022 (6 de 10) y, según el Plan, en 2021 (640 frente a 525). Mejor: «El patinete, cada vez más: de 6 a 7 de cada 10».
- **REL `falta3`** une como serie tres conteos con métodos y puntos distintos (2 puntos en 2019, 5 en 2020, la UV en 2021) y dice «sabíamos cuántos patinetes había». Mejor: «Tres conteos manuales, con métodos distintos, daban un 25-31 % de patinetes en el carril bici (2019-2021)».
- **MET `uso`** compara el tráfico de 116 contadores del carril bici con los siniestros de **toda la ciudad**. Son ámbitos distintos: decirlo, o usar los siniestros a 100 m de esos contadores, con la cobertura corregida.
- **REL `y2025`** solo trae una «primera señal», y es favorable (−50 con patinete, de una noticia). Está bien marcada como pendiente, pero conviene decir que es de la propia Policía, sin datos publicados.
- **el resumen interno del proyecto**, «La idea», punto 4: sigue diciendo «sus siniestros crecen a igual uso» y «los puntos negros piden obra», afirmaciones retiradas de la web. Riesgo de que vuelvan en los textos públicos.

## (b) Afirmaciones públicas: tabla resumida

| # | Afirmación (página · clave) | Respaldo | ¿Responde exactamente? | Alternativa no descartada |
|---|---|---|---|---|
| 1 | 1.339 → 1.659 (+24 %); 2025 es el peor año (OBS hall[0], h_meta; REL partida/y2025) | `exportar_web.py` (serie); reproducido | Sí como recuento | Cambio de registro: todos los siniestros +24 %, cuota constante (punto 2) |
| 2 | Base 2025, meta 830, −12,9 %/año, alternativa 2024 → 751 (OBS, REL, MET) | `META` en exportar_web.py | Aritmética correcta | Base en el pico → regresión a la media (punto 3) |
| 3 | «El Plan quiere / se compromete a reducir a la mitad» (REL sub/promesa, OBS h_meta) | pdsv.txt l. ~3080 | Más débil: es un indicador de acción | Meta global = víctimas (punto 9) |
| 4 | Bici 576 → 549, patinete 825 → 1.190; 7 de cada 10 con patinete (REL quien2, OBS hall[1]) | serie; cuadra con el Plan | Sí; con aviso de exposición en REL | Infradeclaración y vigilancia (punto 10); «ya» mayoría desde 2022 |
| 5 | 30 lugares (celdas de 100 m) con más siniestros, ponderados por cobertura (OBS, REL donde, MET) | exportar_web.py | Sí; aclara que no es riesgo | Concentración en el centroide del cruce; el formato cruce/portal cambia en 2024 (punto 4) |
| 6 | 13 de 30 en el top-60 de los tres periodos: «se repiten», «no es cosa de un año» | exportar_web.py `tres` | Más débil: dentro de muestra | Fuera de muestra, 16/30 en P3; vuelta a la media del 18 % (punto 8) |
| 7 | El anillo 4 / 11 / 15; «Fuera del radar del Plan» (OBS hall_plan, REL donde, MET plan) | `pl_anillo`, `CLAVES` | **No**: faltan claves (sale 5 / 13 / 12) y el Plan solo da top-3 | El Plan no lista más lugares (punto 1) |
| 8 | Alameda: 48 siniestros, 43 con motor, 24 sin respetar la prioridad (REL alameda*) | rel.ala; revisión de coherencia ✓ | Sí | — (la prioridad es del siniestro, avisado) |
| 9 | Alameda: «han bajado de 16 a 6» tras auditoría y reordenación | `vy` de la celda | Más débil | Cambio de anotación cruce → portal, paseo estable (44), regresión a la media (punto 4) |
| 10 | Turia: 165 siniestros, ninguno situable; n.º 1 con bici en el Plan | exportar_web.py `tur` | Sí | — |
| 11 | 145 puntos de conteo; 21 «claramente», 16 «quizá» más de lo normal (REL trafico2, OBS uso) | `cribado_eb.py` | Sí como P(θ>1); no predice mejor que el recuento (dicho en MET) | Mezcla bici/patinete según el sitio; radio (5/10 y 3/10 coinciden a 150/200 m) |
| 12 | Xàtiva 36/22, Tirso 20/7, Balaciart 13/4 (puesto 30) | rel.sc; reproducido por la revisión de coherencia | Sí | Elegidos a mano (`DEST`); dependen del radio |
| 13 | «Los contadores cuentan bicis y, probablemente, patinetes» | supuesto (las notas internas de trabajo) | Supuesto, bien marcado | — |
| 14 | Tráfico 100 → 115, siniestros 100 → 124; el riesgo por viaje debe bajar un 50-60 % (MET uso) | exportar_web.py | Más débil: ámbitos distintos | Desvío entre carriles; contadores solo en carril bici |
| 15 | «Cuando el tráfico se duplica, los siniestros no» (MET normal) | elasticidad 0,66 | **No**: es transversal | Composición, error de medida (punto 6) |
| 16 | «EB no predice mejor que el recuento» (MET) | coef.json (2/6) | Sí, honesto | — |
| 17 | Graves 19 / 76 / 167 / 181; comparables desde 2024 (REL falta2, OBS lim, MET gravedad) | serie; Plan | Sí para graves | «Baja gravedad» +44 % en 2025 (punto 12) |
| 18 | Pista «a revisar» (OBS ficha) | binomial + Holm, n ≥ 20 | Más débil: referencia = media de la ciudad | Tautología de los cruces (punto 7) |
| 19 | Geolocalizados 77 % → 95 %; 87 % del total (OBS lim, REL fin_p, MET datos) | exportar_web.py | Sí | — |
| 20 | 2026 sin publicar; «primeras señales» −50 con patinete (REL y2025) | prensa (elperiodic, 10/06/2026) | Fuente externa y selectiva; marcada como pendiente | — |
| 21 | Cifras = las del Plan «salvo algún siniestro suelto (el Plan cuenta por vehículo)» (OBS proto) | plan_pdsv_resumen §3 | La cifra sí; la explicación no | Fecha de extracción (punto 13) |
| 22 | Nulos patinete frente a bici: «no detectable no quiere decir no existe» (MET limites) | vmp_vs_bici*.py | Sí, bien formulado | — |
| 23 | «Revisiones externas», «código abierto», «ninguna cifra a mano» (MET, OBS d3_p) | — | **No** del todo | Punto 11 |

## (c) Qué ya se conocía y qué es nuevo

**Ya señalado por `docs/revision_independiente.md` y corregido en las páginas actuales:**
- el «+76 % a igual uso»: retirado;
- la tarjeta «0 de 2.508»: retirada; MET dice «no detectable ≠ no existe»;
- la cobertura creciente: está en `lim` y en MET;
- E3, la IMD por años con dato: aplicado;
- «EB no supera al recuento», el 22 % de cobertura y la dependencia del radio: dichos en MET;
- la base y el objetivo global: matizado («la que usa el Plan para los heridos graves»).

**Ya señalado y solo a medias:**
- **Pista** (revisión independiente #10, recomendación 4): se añadió Holm y n ≥ 20, pero sigue comparando con la media de la ciudad (punto 7).
- **Persistencia en la misma muestra** (#7-#8): se cambió el texto a «tres periodos», pero sigue siendo dentro de muestra y el hombre de paja se ha ido sin que se publique la versión fuera de muestra (punto 8).
- **Anillo** (revisión de coherencia, M2): se pasó de 2 a 3 niveles y de 26 a 15 «sin cita», pero la tabla de claves está incompleta (punto 1) y las notas internas de trabajo conserva 4 / 6 / 20.

**Nuevo en esta revisión:**
- el fallo de `CLAVES` y la lógica de las listas top-3 detrás de «Fuera del radar» (1);
- la subida idéntica de todos los siniestros (+24 %, cuota constante) y el crecimiento de los siniestros sin heridos como alternativa de registro (2);
- el sesgo de elegir el pico como base para evaluar el Plan (3);
- el cambio de anotación cruce → portal (69 % → 50 %) que vacía las celdas de cruce, y su efecto sobre la bajada de Alameda (4);
- la cabecera «Dónde actuar» (5);
- la elasticidad transversal presentada como ley (6);
- la versión fuera de muestra de «se repiten» (16/30) (8);
- la meta de una acción presentada como meta de ciudad (9);
- la infradeclaración y vigilancia diferencial (10);
- «revisiones externas» y «código abierto» (11);
- «baja gravedad» en 2025 (12);
- las incoherencias del punto 13.
