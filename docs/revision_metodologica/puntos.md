# Revisión metodológica: puntos negros, meta del Plan y web (04/11/2026)

Ámbito: `scripts/persistencia_puntos.py`, `scripts/exportar_web.py` (entero), `scripts/construir_web.py`, `scripts/comprobar.py`, Plan Director (`pdsv.txt`, `pdsv_lugares.csv`, `pdsv_indicadores.csv`) y los datos publicados en `web/proto/datos/`. Todo se ha recalculado con scripts propios en este directorio (`a1.py` … `a8.py`, `base.py`). No he tocado el proyecto.

**Veredicto corto.** Ningún hallazgo invalida las tres conclusiones de fondo:
- hay concentración persistente de siniestros de bici y VMP, y se sostiene incluso frente a un nulo local;
- el indicador que se sigue es literalmente el de la acción 3.2.2;
- con base 2025, la meta está «pendiente».

Sí hay **dos cifras públicas mal calculadas**: el anillo del Plan (4 · 11 · 15) y la lista de «los 30 lugares», que depende de dónde cae la rejilla. Hay además varias frases que dicen más de lo que el dato permite.

---

## A. Errores de código

### A1. ALTA · CONFIRMADO · El anillo del Plan omite citas que el Plan sí hace (4 · 11 · 15 → 5 · 12 · 13)
- **Dónde:** `scripts/exportar_web.py:165-185` (`CLAVES`) y `:192-194`. Si un lugar de `pdsv_lugares.csv` no tiene clave, se descarta sin aviso (`if not cl: continue`).
- **Lugares sin clave:** 8 de los 37 de `pdsv_lugares.csv`. Dos afectan a los 30 lugares publicados:
  - **Av. Tres Cruces × C/ Campos Crespo** (puesto 25 de 30, 16 siniestros). El Plan la cita **como cruce**: n.º 3 de los cruces con más siniestros con peatón (fila 17 de `pdsv_lugares.csv`). Hoy sale `pl = 0`, «el Plan no lo menciona». Con la regla vigente le corresponde `pl = 1` (cita el lugar).
  - **C/ Pelayo × C/ Xàtiva** (puesto 23). El Plan tiene una actuación en la C/ Xàtiva, la marca «Espere verde» en el carril bici (fila 28, `tipo_lugar = calle`). Con la opción B («la calle cuenta por cualquier motivo») le corresponde `pl = 2`; hoy sale 0.
  - Dudoso: **Av. Peris y Valero × Duque de Calabria**. El Plan solo pone una foto de un paso accesible (fila 36). Con la opción B literal sería `pl = 2`. Hay que decidirlo.
- **Recálculo** (`a3.py`): de 4 · 11 · 15 se pasa a **5 · 12 · 13**, o a 5 · 13 · 12 si cuenta Peris y Valero.
- **Conclusión pública afectada:**
  - la tarjeta y el relato «fuera del radar del Plan» (15);
  - la ficha de Tres Cruces–Campos Crespo, que afirma algo falso: «el Plan no lo menciona».
- **Corrección:**
  - añadir las claves `"Tres Cruces - Campos Crespo": ["TRES CRUCES", "CAMPOS CRESPO"]` y `"C/ Xàtiva": ["C/ XATIVA|C/ JATIVA"]`, y decidir Peris y Valero;
  - convertir el `continue` silencioso en un `assert` o un aviso que liste los lugares de `pdsv_lugares.csv` sin clave. Los 8 actuales son Peset Aleixandre–Montcada, Giorgeta–Jesús, Tres Cruces–Campos Crespo, C/ Xàtiva, Ronda Norte, Germanías–Castellón, Peris y Valero y Anillo Ciclista.
  - Ojo: una clave genérica «GERMANIAS» empareja por error Regne de València × GV Marqués del Turia. Esa cita es un **punto** concreto, a la altura de C/ Castellón, no toda la calle.
- **Pendiente de decidir:** el Anillo Ciclista (Ronda Interior) es una cita de diagnóstico del Plan. Pasa por 6 de los 30 lugares: Justicia–Ciudadela, Colón ×2, Pelayo–Xàtiva, Guillem de Castro–Quart y Puente del Real. Con la opción B, ¿cuenta como «cita su calle»? Hay que decidirlo y escribirlo.

### A2. MEDIA · CONFIRMADO · «Tres periodos»: el corte del top 60 se decide por empates
- **Dónde:** `exportar_web.py:120` y `:147`. `nlargest(60)` usa `keep='first'`, así que desempata por el orden de la tupla de celda, es decir, por la coordenada X: gana la celda más al oeste.
- **El problema está en P1** (ene-sep 2022: 9 meses y 74 % de cobertura). El puesto 60 tiene **2 siniestros**. Hay 55 celdas por encima y **77 empatadas a 2**, de las que entran 5 por su posición en el mapa. En P2 hay 41 empatadas en el corte y en P3, 32.
- **Recálculo** (`a2.py`): se publica `tres = 13`; con los empates incluidos salen **15**.
- **Conclusión pública afectada:** la tarjeta «13 de 30 se repiten» y el sello de la ficha «No se mantiene entre los primeros en todos los periodos».
- **Corrección:** usar `keep='all'` (o un umbral, «≥ k siniestros») y decirlo. Mejor aún, cambiar el indicador (ver C1).

### A3. BAJA · CONFIRMADO · El orden de la lista no coincide con la cifra que se muestra
- **Dónde:** `exportar_web.py:123`. Se ordena por `W` (pesos 1/cobertura) y se muestra `n` sin pesos.
- **En la web:** Regne de València (20) aparece después de Abril Martorell–Malilla (19), y Tres Cruces–Campos Crespo (16) después de Tres Forques (15). El texto dice «los lugares con más siniestros».
- **Corrección:** decir «ordenados por siniestros corregidos por cobertura» o mostrar `W` redondeado.

### A4. BAJA · CONFIRMADO · El peso 1/cobertura por periodo infla los cruces
- **Dónde:** `exportar_web.py:117-119`.
- **Recálculo** (`a2.py`): en P1, los siniestros escritos como «X cruce Y» se localizaban al 86,7 % y los demás al 55,1 %. El peso medio de P1 (1/0,738 = 1,35) les da 1,35 a los dos tipos, cuando a los de cruce les correspondería 1,15. Entre los 30 hay un 75,9 % de cruces, frente al 55,8 % en la ciudad.
- **Efecto:** pequeño. Sin pesos coinciden 28 de 30.
- **Corrección:** calcular la cobertura por periodo × tipo de dirección (cruce / portal / otra).

### A5. BAJA · CONFIRMADO · Restos y comentarios que no cuadran con el código
- `exportar_web.py:74`: `MOTOR` ya no se usa (`contrario()` ya clasifica cualquier otro vehículo como «m»). La corrección E1 de la revisión anterior **sí se aplicó**. Pero `comprobar.py:110` sigue mandando a revisar `MOTOR`. Hay que borrar las dos referencias.
- `persistencia_puntos.py:13-14`: el comentario dice «cuadrícula completa… incluye celdas con 0», pero `x0, y0, x1, y1` no se usan y la población son las celdas con algún caso. Hay que corregir el comentario o el código.
- Las 25 filas con `unidades = "["` (2 / 5 / 14 / 4 por año) no entran en ningún recuento de bici o VMP. Algunas pueden ser de bici o VMP (4 «caída», 4 «choque contra obstáculo»). Esto subestima el total como mucho en 14 en 2024 y en 4 en 2025. Basta con nombrarlo en las limitaciones.

### A6. Sin errores en `construir_web.py` ni en `comprobar.py`
- `comprobar.py` solo verifica que la base sea 1.659 y que el anillo sume. **No detecta lugares del Plan sin clave (A1)**: conviene añadir esa comprobación.
- La IMD media por sitio (`expo / N_AÑOS`) ya divide por los años reales (E3 corregido) y un `assert` la cuadra con `cribado_eb.py`.

---

## B. Diseño metodológico

### B1. ALTA · CONFIRMADO · Los «30 lugares» dependen de dónde cae la rejilla
- **Dónde:** `exportar_web.py:112`, con la cuadrícula UTM de 100 m y origen fijo.
- **Recálculo** (`a4.py`): desplazando el origen 25, 50 y 75 m en X e Y (16 rejillas), de los 30 lugares publicados **se conservan entre 18 y 24 (mediana 21)**. Es decir, **unos 9 de 30 cambian solo por mover la rejilla**. Comparten entre el 58 % y el 79 % de los siniestros.
- **El primer puesto** (Alameda–Pl. Zaragoza) es estable, pero su recuento va de **34 a 57** según la rejilla (se publica 48).
- **Con celdas de 200 m** se conservan 20 de 30.
- **Por qué pasa:** el 27 % de los siniestros geolocalizados comparten coordenada exacta con 4 o más (el nodo de cruce del geocodificador; máximo, 34 en un punto). Un cruce cerca del borde de una celda se parte o no según el origen.
- **Qué sabía el proyecto:** la revisión anterior lo citó para el «×7 frente al azar» (punto 9), no para la lista publicada. La página de método no menciona esta sensibilidad. Solo da la del radio del EB.
- **Corrección:** cambiar la unidad de análisis por el **lugar físico**:
  - agrupar por nodo de cruce (el geocodificador ya lo tiene) y por tramo de calle entre cruces para los portales;
  - o, al menos, un buffer de 50 m alrededor de cada nodo, o un agrupamiento por distancia (DBSCAN, `eps` de 30-50 m, de scikit-learn) en EPSG:25830.
  - Mientras tanto, publicar la cifra «entre 18 y 24 de los 30 se mantienen al mover la rejilla 25-75 m».
  - De paso desaparecen los lugares duplicados (Ausiàs March × Abril Martorell y Ferrandis × Ausiàs March, cuyos centros están a 94 m: posiblemente el mismo nudo, PLAUSIBLE).

### B2. MEDIA · CONFIRMADO · La persistencia es real, pero «13 de 30» se lee al revés
- **Recálculo** (`a5.py`, `a8.py`):
  - **sin persistencia** (cada periodo permutado entre celdas), «tres» sale 0,1 de media (IC90 0-1);
  - con **persistencia perfecta** (tasa constante por celda y ruido de Poisson), sale **12,3 (IC90 9-16)**;
  - el observado es **13**.
- **Lectura correcta:** los datos son compatibles con que **los 30** sean persistentes. Que 17 no estén en el top 60 de los tres periodos se explica por el ruido y por el corte de P1 (9 meses, umbral de 2 casos con empates).
- **Conclusión pública afectada:**
  - el sello de la ficha «No es manté entre els primers en tots els períodes» (17 lugares) da a entender que esos no persisten;
  - la frase del informe «no es cosa de un año» está bien.
- **Corrección:**
  - quitar el sello negativo o cambiarlo por «sin datos suficientes en 2022 para decirlo»;
  - mejor, sustituir «tres periodos» por la prueba fuera de muestra que ya existe (ordenar con 2022-23 y medir en 2024-25) con el nulo local (B3).

### B3. MEDIA · CONFIRMADO · El nulo de `persistencia_puntos.py` es un hombre de paja, pero el resultado aguanta un nulo exigente
- **Nulo actual:** permutar los recuentos de B entre todas las celdas con casos. Solo rechaza «todas las celdas tienen la misma media», cosa que el tráfico ya garantiza.
- **Nulo local** que he probado (`a5.py`): permutar B **dentro de bloques de 500 m**. Contrasta si la celda supera a su entorno, que es lo que significa «punto negro».

| | N_A | N_B observado | Nulo global | Nulo local (500 m) | p |
|---|---|---|---|---|---|
| top 10 | 144 | 128 | 17 | 29,7 | < 0,0005 |
| top 30 | 319 | 278 | 53 | 84,8 | < 0,0005 |
| top 50 | 454 | 384 | 88 | 125,6 | < 0,0005 |

- **Conclusión:** «hay puntos de concentración persistentes» **se sostiene**.
- **Regresión a la media:** la retención es de 0,85-0,89, frente a 1,30 de la ciudad geolocalizada (1,12 con todos los siniestros). Parte de esa diferencia es un artefacto: los 30 lugares son sobre todo cruces, que ya se localizaban bien en 2022, así que ganan menos cobertura (cruce +12 % frente a +71 % en el resto entre P1 y P3).
- **Corrección:**
  - poner el nulo local en el script y en las notas internas de trabajo;
  - comparar la retención con la ciudad **del mismo tipo de dirección** (cruce o portal), no con el total.

### B4. MEDIA · CONFIRMADO · La «pista»: la familia de Holm y la referencia no son las adecuadas
- **Dónde:** `exportar_web.py:154-160` y `:260-264`.
- **Familia de Holm:** Holm corrige 4 pruebas por lugar, pero se hacen 31 × 4 = **124 pruebas** y se publican las que salen. La familia correcta es todo el mapa.
- **Referencia:** es la media de la ciudad (m 56,9 %, w 8,9 %, d 8,8 %, s 25,4 %). Esa media mezcla tramos, parques y el Turia. Que un cruce tenga «más choques con vehículo» es casi tautológico: en los cruces de la ciudad, «m» es el 70,3 %.
- **Recálculo** (`a6.py`), sobre los 30 lugares:
  - como ahora (ciudad, Holm por lugar): **7 pistas**, las publicadas. Alameda m, Ausiàs March m, Alcalde Reig m, Ferrandis m, Colón × Isabel la Católica w, Padre Ferris 21 d y Colón 8 w;
  - ciudad con Holm sobre las 120 pruebas: 4;
  - **referencia de cruces** con Holm sobre las 120: **3**, Colón × Isabel la Católica w, Colón 8 w y Padre Ferris 21 d. Las cuatro pistas «m» desaparecen; con BH sobrevive Alameda m.
- **Qué sabía el proyecto:** la revisión anterior ya pedía la referencia de cruces y BH (punto 10, recomendación 4). **Solo se aplicó a medias**: hay Holm y n ≥ 20, pero sigue la referencia de ciudad y Holm por lugar.
- **Corrección:**
  - referencia según el tipo de lugar (cruces frente a tramos, por `metodo`);
  - Holm o BH sobre todas las pruebas del mapa;
  - excluir el propio lugar de la referencia.
  - En el Turia, la pista «s» frente a la ciudad es trivial (es un parque): quitarla o explicarla.

### B5. MEDIA · CONFIRMADO / PLAUSIBLE · Meta 3.2.2: indicador correcto, pero se juzga sin incertidumbre
- **El indicador es el que dice el Plan (CONFIRMADO).** En `pdsv.txt:3080`, la acción 3.2.2 tiene el indicador de impacto «Reducción de siniestros con ciclistas/VMP», en %, con fórmula «Comparación anual», **línea base «—»** y meta −50 %, de la Policía Local. Es un indicador de **siniestros, de cualquier gravedad**, no de víctimas.
  - El proyecto cuenta siniestros con BICICLETA o VMP en `unidades`, sin duplicar (1.659 en 2025). Las series separadas cuadran con el Plan con una diferencia de 0 a 2 por año (`comprobar.py`).
  - La meta global (−50 % de fallecidos sobre 2019 y de heridos graves sobre 2024, todos los colectivos) es otra. La página de método lo dice bien (`metode.plantilla.html:201/389`).
  - **No hay error crítico de indicador.**
- **Matices de comunicación:**
  - la base 2025 es una elección nuestra y la web lo dice («propuesta nuestra»). Correcto;
  - 2025 es el máximo de la serie: elegir el pico como base hace la meta algo más fácil. Pero la subida +10,5 % encaja con la tendencia (+7,4 % anual de 2022 a 2025) y no parece un año atípico;
  - el Plan nunca da la unión, sino VMP y bici por separado. Si el Ayuntamiento evalúa con la suma (2024: 1.565), las cifras no casarán. Conviene mostrar también las dos series y su meta.
- **Problema de diseño (CONFIRMADO):** `escenario()` (`exportar_web.py:47-59`) clasifica en «sobre_senda» o «en_senda» comparando un recuento con la senda redondeada, sin incertidumbre.
  - El IC95 de Poisson alrededor de la senda es **2026: 1.370-1.519**, 2027: 1.188-1.327 … 2030: 774-887.
  - Un 2026 con 1.480 saldría «sobre la senda» siendo compatible con ella.
  - Además, el 21-28 % son siniestros «sin heridos», que dependen de cuánto se registra. Más controles de patinetes (acción 2.1) pueden subir el recuento sin que empeore nada.
- **Corrección:**
  - añadir a `escenario()` el estado «compatible con la senda» si el observado cae dentro del IC95 de Poisson (`scipy.stats.poisson.ppf`, como ya se hace con `rel["banda"]`);
  - para «se cumple», usar una prueba unilateral de razón de Poisson frente a la base (`statsmodels.stats.rates.test_poisson_2indep`);
  - seguir también los siniestros con heridos (sin «sin heridos») como control de los cambios de registro.

### B6. MEDIA · CONFIRMADO · Las fichas muestran tendencias por lugar infladas por la cobertura
- La ficha («Toca un punto negro para ver su evolución») dibuja barras por año (`vy`) con recuentos geolocalizados.
- La cobertura sube del 76,9 % al 95,5 %. Los portales geolocalizados pasan de 322 a 775 (+141 %) y los cruces, de 694 a 807 (+16 %).
- Un lugar de portal (Padre Ferris 21: 3 → 2 → 7 → 9) puede «crecer» solo por el formato. La limitación general está en `lim`, pero no junto al gráfico.
- **Corrección:** una nota en la ficha o barras ponderadas por 1/cobertura del periodo y tipo de dirección.

---

## C. Comunicación

- **C1. MEDIA · CONFIRMADO · Sello «no se mantiene».** Ver B2: 17 sellos negativos que el dato no respalda. Cambiarlos por una formulación neutra o quitarlos.
- **C2. MEDIA · CONFIRMADO · «El Plan, al día» no existe todavía.**
  - `docs/enfoque.md:12-27` lo presenta como «ya se puede».
  - No hay `data/processed/plan_seguimiento.csv` ni sección en la web.
  - No se puede presentar como implantado, y las bases exigen que el proyecto esté «implantado».
- **C3. BAJA · CONFIRMADO · Cifras del anillo que no coinciden entre documentos.**
  - `docs/enfoque.md:22` dice «26 de los 30 no aparecen en el Plan»;
  - las notas internas de trabajo («Anillo del Plan en tres niveles») da 4 / 6 / 20 y la regla «las listas de peatones y los radares no cuentan»;
  - el código (opción B) da 4 · 11 · 15, y tras A1, 5 · 12 · 13.
  - Hay que unificarlo en todos los documentos.
- **C4. BAJA · PLAUSIBLE · Llamarlos «punto negro».** La ficha usa «Punt negre» en lugares que son de concentración, sin exposición. las notas internas de trabajo lo reconoce («no de riesgo por uso»). Convendría que el rótulo dijera «lugar con más siniestros», como el informe, y dejar «punto negro» para la definición explícita.
- **C5. BAJA · Contexto externo fijado a mano.** El «unos 50 siniestros de patinete menos en enero-mayo de 2026» (`exportar_web.py:68`) es una cifra policial. Que no salga como dato del observatorio.

---

## D. Qué se conocía, qué se aplicó y qué es nuevo

| Tema | Revisión anterior / las notas internas de trabajo | ¿Aplicado en el código actual? | Esta revisión |
|---|---|---|---|
| Orden por total y texto «persistente» (E2) | Sí | Sí: el texto ahora dice «con más siniestros» | — |
| `MOTOR` incompleto (E1) | Sí | Sí: `contrario()` ya es correcto; queda código muerto (A5) | Menor |
| IMD /4 (E3) | Sí | Sí (`N_AÑOS`) | — |
| Rejilla (punto 9) | Sí, para el ×7 | **No**: nada en el método | **Nuevo:** 18-24 de 30 lugares estables (B1) |
| Nulo «azar» como hombre de paja (punto 7) | Sí | El «×7» ya no está en la web; el script sigue igual | **Nuevo:** el nulo local también rechaza (B3): la conclusión se refuerza |
| Pista: referencia de cruces y BH (punto 10) | Sí | **A medias** (Holm por lugar, referencia de ciudad) | **Nuevo:** recálculo 7 → 3 (B4) |
| Empates en el corte del top 30 | Sí (T = 14) | Desempate por `W` y luego `T`: correcto | **Nuevo:** empates en el **top 60 por periodo** (A2, 13 → 15) |
| «Tres periodos» frente a persistencia perfecta | No | — | **Nuevo** (B2) |
| Lugares del Plan sin clave | No | — | **Nuevo** (A1, 4·11·15 → 5·12·13) |
| Indicador 3.2.2 y año base | las notas internas de trabajo («Fechas del Plan y año base») | Correcto | Confirmado; **nuevo:** falta incertidumbre en la conclusión (B5) |
| Cobertura en las tendencias | Sí (general) | En `lim` y en el método | **Nuevo:** las barras de las fichas (B6) y el sesgo del peso por tipo (A4) |
| Revisión manual de los diez primeros por geocodificación | Pendiente en las notas internas de trabajo | No hecha | Sigue pendiente: 27 % de los siniestros en coordenadas repetidas |

## E. Orden de corrección propuesto
1. A1: claves del Plan y aviso de lugares sin clave. Cambia una cifra pública y una ficha falsa.
2. B1: unidad de lugar por cruce o tramo, o publicar la sensibilidad a la rejilla.
3. B2, A2 y C1: quitar el sello negativo y el indicador «tres periodos», o rehacerlos con `keep='all'` y fuera de muestra.
4. B4: la pista con referencia de cruces y Holm/BH sobre todo el mapa.
5. B5: el estado «compatible con la senda» y la prueba de Poisson antes de que llegue 2026.
6. C2 y C3: no presentar «El Plan, al día» como implantado y unificar las cifras del anillo.
