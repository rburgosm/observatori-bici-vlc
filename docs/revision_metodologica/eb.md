# Revisión estadística: exposición y modelos (EB, contadores, VMP frente a bici)

Ámbito: `scripts/cribado_eb.py`, `validar_contadores.py`, `vmp_vs_bici*.py`, `vmp_carril_bici.py`, `analisis_viabilidad.py`, la parte de uso de `exportar_web.py` y los textos públicos (`web/proto/*.plantilla.html`). Todo se ha recalculado con copias en `.../scratchpad/metodo/eb/` (`base.py` reproduce el panel de `cribado_eb.py` líneas 34-169; `c1.py`…`c10.py` son las comprobaciones). Reproduce el modelo del proyecto: α = 0,493, elasticidad 0,662, 21 sitios con P > 0,95 y 16 entre 0,8 y 0,95. No se ha tocado el proyecto.

## Resumen

Ninguna conclusión pública de esta parte es falsa por un error de código. Las cuentas cuadran y la validación no tiene fuga. Los problemas son de diseño y de lectura:

1. La capa «más de lo normal para el tráfico» es, en la práctica, una señal del **patinete medida con un contador de bicis**.
2. Falta una variable de diseño evidente: el **número de cruces** que caen dentro del círculo de 100 m.
3. Tres textos dicen más de lo que el modelo sostiene: la franja de «variación normal», la frase de que «los siniestros crecen menos que el tráfico» y la lectura de Xàtiva.

El «+76 % a igual uso» se retiró de la web, pero sigue calculándose sin corregir y sigue en el resumen interno del proyecto y las notas internas de trabajo.

---

## A. Diseño metodológico

### A1. ALTA · PLAUSIBLE (con cifras CONFIRMADAS): la señal de «exceso según el uso» la pone el patinete, y su denominador no está validado
- **Dónde:** `cribado_eb.py:16, 150` (modelo de VMP + bici con la IMD de las espiras de bici); en el informe, `trafico`/`trafico2`/`trafico3` (`informe.plantilla.html:279-281`); en el observatorio, la vista «uso».
- **Cifras recalculadas (R = 100 m):**
  - **Sitios con P > 0,95:** 4 solo con bici, frente a 18 solo con VMP; con VMP + bici, 21.
  - **Elasticidad de la IMD de bici:** 0,87 en bici y 0,63 en VMP.
  - **Heterogeneidad que explica la IMD de bici** (bajada de α sin y con covariables): 68 % en bici (0,98 → 0,32) y solo 43 % en VMP (0,93 → 0,53).
  - **Los dos ejemplos del informe:**
    - Tirso de Molina: 18 de sus 20 siniestros tienen patinete. Con el modelo de bici, P = 0,74 (no destaca); con el de VMP, P = 1,00.
    - Balaciart – Primado Reig: 12 de 13 con patinete. Con bici, P = 0,61; con VMP, P = 1,00.
  - **Cuota de VMP:** 76 % en los sitios con P > 0,95 y 71 % en el resto (Spearman 0,21; p = 0,13).
- **Lectura:** el contador explica bien los siniestros de bici y mal los de patinete. Es lo que cabe esperar si las espiras miden mal los VMP, cuyo cuadro de aluminio tiene poca masa metálica, o si la proporción de patinetes en el tráfico cambia de un sitio a otro. Las dos hipótesis convierten el «exceso» en composición del tráfico, no en peligro. las notas internas de trabajo ya lo apunta («Cribado EB v2»), pero la web solo enseña el modelo conjunto, y el informe elige como ejemplos dos sitios que son casi solo de patinete sin decirlo.
- **Conclusión afectada:** «Hay más siniestros de los que tocarían por el tráfico que pasa» (`uso_txt`) y los ejemplos de Tirso y Balaciart.
- **Corrección:**
  1. En cada ficha, dar N y μ por separado para bici y para patinete.
  2. Marcar el «claramente» solo si se cumple en el modelo de bici, o añadir «sobre todo por siniestros con patinete; los contadores podrían no contar bien los patinetes».
  3. En el informe, decirlo de Tirso y Balaciart.
  4. Mantener la pregunta a Movilidad (pendiente 5b) como condición para publicar esta capa como «riesgo».

### A2. ALTA/MEDIA · CONFIRMADO: falta el número de cruces dentro del círculo, y el «exceso» lo recoge en parte
- **Dónde:** `cribado_eb.py:150` (`F_BASE` solo lleva IMD de bici, IMD de vehículos, `sin_veh` y año) y `panel()`, líneas 131-147.
- **Mecanismo:**
  - El 55,6 % de los siniestros asignados están geolocalizados «como cruce», en el centro del cruce. El 32 % (368 de 1.138) caen en pilas de 5 o más en un mismo punto.
  - Un contador a mitad de manzana con un círculo de 100 m recoge 0 o 1 cruces; uno junto a una plaza, muchos.
  - El HSM separa las SPF de intersección y de tramo. Aquí se mezclan.
- **Cifras recalculadas:**
  - Cruces del callejero, contados con independencia de los siniestros (nodos de grado ≥ 3 de `ejes.geojson` a ≤ 100 m): Spearman con log(N/μ) de 0,34 (p = 2e-5).
  - Al añadirlos al modelo:
    - LR = 27,5 con 1 gl (p ≈ 2e-7);
    - α pasa de 0,49 a 0,44;
    - los sitios con P > 0,95 pasan de 21 a 18 (16 en común) y el top-10 comparte 8.
  - Con un indicador más directo de conflicto (cruces distintos con siniestros a ≤ 100 m, en parte derivado del resultado): α = 0,34 y solo 12 sitios con P > 0,95.
  - En cambio, el semáforo, que sí se probó, no discrimina (124 de 145 sitios lo tienen).
- **Conclusión afectada:** qué sitios son «claramente más de lo normal» (más o menos 1 de cada 4 cambia) y la persistencia (Spearman de 0,53 entre periodos). Parte de esa persistencia es geometría fija del círculo, no riesgo.
- **Corrección:** meter `n_int` (o `log1p(n_int)`) en la SPF o, mejor, estratificar los sitios en «junto a un cruce» y «a mitad de manzana». La alternativa es asignar los siniestros por tramo de vía (de cruce a cruce) y no por círculo.

### A3. MEDIA · CONFIRMADO: «claramente más de lo normal» es la cola alta de la variación normal, no una anomalía
- **Dónde:** `cribado_eb.py:166` (`p_exceso = P(θ > 1)`); en el observatorio, `uso_txt` y `uso_nota`; en el método, «Tres niveles».
- **Cifras recalculadas:**
  - Con el propio modelo (θ ~ gamma(1/α, α), sin ningún «punto negro» añadido), P(θ > 1) a priori = 0,41: 4 de cada 10 sitios tienen, por definición, más que la media.
  - Al simular 500 veces con los μ reales, salen de media **19,5 sitios con P > 0,95**. Se observan 21.
  - La posterior trata μ y α como conocidos: no recoge la incertidumbre de los parámetros.
- **Ya se conocía en parte:** la revisión independiente, punto 19, dice que es una posterior condicionada y sin corrección por 145 comparaciones. La cuantificación es nueva.
- **Corrección:** redactarlo como «por encima de la media de los puntos con un tráfico parecido». Si se quiere señalar anomalías, usar P(θ > 1,5) o P(θ > 2) (con scipy, la misma gamma) o un percentil del exceso.

### A4. MEDIA · CONFIRMADO: la lista de sitios «claramente» depende mucho del radio
- **Cifras recalculadas:** sitios con P > 0,95 según el radio (Jaccard frente a R = 100 m):

  | R | Sitios | Compartidos | Jaccard |
  |---|---|---|---|
  | 75 m | 19 | 14 | 0,54 |
  | 125 m | 25 | 16 | 0,53 |
  | 150 m | 26 | 15 | 0,47 |
  | 200 m | 29 | 15 | 0,43 |

- **Causa:** las pilas de cruce de A2. Un centro de cruce a 95 o a 105 m entra o sale entero.
- **Ya se conocía:** el solape del top-10 (5 y 3), en la revisión independiente y en la web. El dato por etiqueta es nuevo.
- **Corrección:** las fichas no deberían dar P con tres decimales. Un sitio debería salir «claramente» solo si lo es con 75, 100 y 150 m. Los tres ejemplos del informe sí son estables (Tirso, P ≥ 0,99 en todos los radios; Balaciart, ≥ 0,97 hasta 150 m), así que el informe puede mantenerlos con la salvedad de A1.

### A5. MEDIA/BAJA · CONFIRMADO: el artefacto de geolocalización no es igual en todo el espacio
- **Cifras recalculadas** (siniestros con bici o VMP, de 2022 a 2025):

  | Siniestros | Índice 2025 (2022 = 100) |
  |---|---|
  | Todos | 124 |
  | Geolocalizados | 154 |
  | Asignados a una zona de contador | **181** |

  En VMP: 144, 175 y 202.
- **Causa:** entre 2022 y 2025, la geolocalización «por portal» pasa del 24 % al 47 % y «solo calle» del 14,5 % al 3,1 %. Mejora sobre todo a mitad de manzana en las avenidas, que es donde están los contadores.
- **Consecuencias:**
  - El efecto año del EB solo absorbe la media de las zonas de contador. Con solo 2024-25 (cobertura ≥ 91 %), salen 14 sitios con P > 0,95, de los que 12 están entre los 21 del modelo de cuatro años, y el top-10 comparte 5.
  - El índice anual de VMP con offset de la cobertura de toda la ciudad baja de 178 a 146 (IC95 109-196). Como la cobertura en las zonas de contador sube más, incluso ese offset se queda corto.
  - Bici con offset: 91 (sin tendencia).
- **Ya se conocía:** E4 de la revisión independiente. **La corrección no está en el código:** `cribado_eb.py:271` sigue calculando `indice_año` sin corregir, y `exportar_web.py:325` sigue exportando `rel["ix"]` (ninguna plantilla lo usa). el resumen interno del proyecto («sus siniestros crecen a igual uso») y las notas internas de trabajo siguen diciéndolo. Es un riesgo directo para los textos públicos del proyecto.
- **Corrección:**
  1. Quitar `indice_año` y `rel["ix"]`, o calcularlos con offset de la cobertura por periodo y por método.
  2. Reescribir la idea 4 del resumen interno del proyecto y la tabla de las notas internas de trabajo.
  3. Como análisis de sensibilidad del EB, dar el resultado con solo 2024-25.

### A6. BAJA · CONFIRMADO: sitios que no son independientes
- **Cifras recalculadas:** 57 de 145 sitios tienen otro a menos de 200 m (sus círculos se tocan) y 12 a menos de 100 m. El exceso de sitios vecinos (pares a < 400 m, n = 196) está correlacionado: Spearman 0,20 (p = 0,004).
- **Efecto:** los errores estándar del NB y la posterior del EB suponen independencia. El bootstrap remuestrea sitios sueltos, no bloques.
- **Corrección:** errores agrupados por zona o bootstrap por bloques espaciales. Con decirlo basta.

### A7. BAJA · CONFIRMADO, sin efecto apreciable: IMD de laborables frente a siniestros de todos los días
- **Cifras recalculadas:** el 19-20 % de los siniestros asignados son en fin de semana. Esa cuota no se relaciona con el exceso (Spearman −0,13; p = 0,24; 85 sitios). Con solo los siniestros de laborables salen 18 sitios con P > 0,95, todos dentro de los 21.
- **Corrección:** basta con decirlo en el método.

### A8. BAJA · CONFIRMADO, sin efecto apreciable: siniestros que no ocurren en el carril bici
- **Cifras recalculadas:** el 72 % de los asignados está a ≤ 15 m de la red ciclista y el 7,6 % a más de 30 m. No hay diferencia entre los sitios marcados y el resto (27,8 % frente a 27,6 % a más de 15 m). El desajuste existe, pero no explica las etiquetas. Lo que sí las explica es A2.

### A9. BAJA · CONFIRMADO: la validación no tiene fuga y es honesta; el bootstrap es aproximado
- **Lo que está bien:** el ranking usa solo A (modelo y N); la diana usa solo B. La exposición se usa en los dos lados, pero no es resultado.
- **Lo que no favorece al método:** la diana (N_B − μ_B) favorece al EB, porque los dos restan μ. Aun así, el EB no gana: exceso en B del top-10 de 29,5 con EB frente a 31,3 con el recuento bruto (recalculado). Bien comunicado en la web.
- **El bootstrap:** no reajusta los modelos y junta las 6 particiones, que no son independientes. El «IC 95 %» no es el de una sola cantidad, pero como incluye el 0, la conclusión prudente se mantiene.
- **Corrección:** llamarlo «intervalo de remuestreo de sitios, con los modelos fijos».

### A10. Comprobaciones que salen bien
- **Índice de tráfico del carril bici** (`exportar_web.py:422-424`; método, «Uso frente a siniestros»): suma 115,1. Con la mediana de razones, 117,5; con la media geométrica, 116,1; con la serie oficial «Carriles Bici Representativos» del xlsx, 118,5. **Es sólido.**
- **Empates en `sjoin_nearest`:** 0 duplicados con 100, 150 y 200 m. No hay doble conteo.
- **Sobredispersión:** el α de los totales por sitio (0,54, con offset Σμ) es parecido al α de sitio-año (0,49). La correlación entre años de los residuos es de 0,41. El EB multianual del HSM es una aproximación razonable aquí.
- **Correcciones E3 y E5** de la revisión independiente: aplicadas (`exportar_web.py:294-299`, IMD dividida por los años con dato y campo `na`).

---

## B. Comunicación

### B1. MEDIA · CONFIRMADO: la franja de «variación normal» es la de Poisson y deja fuera a un tercio de los puntos
- **Dónde:** `exportar_web.py:363` (`poisson.ppf` 2,5-97,5 %); en el informe, `trafico2` (`informe.plantilla.html:280`): «La franja es la variación normal».
- **Cifras recalculadas:** 22 puntos por encima y 24 por debajo: 46 de 145 (32 %), cuando se esperaría un 5 %. Con la predictiva NB del propio modelo (α = 0,49), solo 2 quedan por encima.
- **Problema:** la franja no es «variación normal» sino «lo que daría el azar si el punto fuera exactamente como la media». Que la mitad de los puntos fuera de la franja estén por debajo muestra que «lo normal» no lo es para muchos sitios.
- **Corrección:** cambiar la etiqueta («margen del azar si el punto fuera como la media») y mencionar los puntos de debajo, o dibujar la franja NB y explicar que el color usa otra regla.

### B2. MEDIA · CONFIRMADO: Xàtiva aparece como «explicado por el tráfico» y es el n.º 2 del exceso
- **Dónde:** `informe.plantilla.html:281` (y :221 en valenciano): «*Xàtiva* es el que más siniestros tiene (36), **pero** también de los que más tráfico tienen: lo normal serían unos 22».
- **Cifras recalculadas:** el sitio elegido (P138 Játiva – Convento Jerusalén) tiene P = 0,996 y es el puesto 2 del EB: está «claramente más de lo normal». El sitio que sí encaja con esa frase es el otro contador de Xàtiva (P237 Játiva – Ruzafa): 26 frente a 23,4, P = 0,67.
- **Ya se conocía:** la revisión independiente (punto 18) comprobó las cifras, pero no este encuadre.
- **Corrección:** cambiar el ejemplo a P237 o reescribir: «36 donde lo normal serían 22: más, aunque menos de lo que sugiere el recuento».

### B3. MEDIA · CONFIRMADO: «los siniestros crecen menos que el tráfico (cuando el tráfico se duplica, los siniestros no)»
- **Dónde:** `metode.plantilla.html:433` (y :245).
- **Cifras recalculadas:**
  - La elasticidad conjunta es 0,66 (IC95 0,54-0,79), pero es transversal, entre sitios.
  - Solo bici: 0,87, y en las notas internas de trabajo, 0,89 (0,71-1,06), compatible con 1.
  - Dentro de cada sitio, con Poisson de efectos fijos y errores agrupados: 0,47 (IC95 −0,41 a 1,36). No se sabe qué pasa cuando el tráfico de un mismo sitio se duplica.
  - Además, el error de medida de la exposición (un contador puntual para un círculo con calles transversales) empuja la elasticidad hacia 0.
- **Problema:** las propias notas internas de trabajo dice que el efecto es del VMP y que puede ser composición del tráfico.
- **Corrección:** quitar el paréntesis o decir «entre puntos de conteo, los que tienen el doble de tráfico no tienen el doble de siniestros; en bici sola, la relación es casi proporcional».

### B4. MEDIA · CONFIRMADO: «el patinete no se concentra en puntos» (el resumen interno del proyecto, idea 4) no se sostiene así
- **Cifras recalculadas:** con los contadores, el VMP tiene más heterogeneidad entre sitios que la bici (α de 0,53 frente a 0,32) y 18 sitios con P > 0,95 frente a 4. El exceso de bici y el de VMP por sitio están correlacionados (Spearman 0,59).
- **Lo que sí está demostrado** (`vmp_vs_bici.py`) es más estrecho: no hay sitios donde la **proporción** de patinete frente a la bici sea anómala, y eso con potencia baja.
- **Efecto:** la web lo dice bien («no detectable»), pero el resumen del proyecto (el resumen interno del proyecto) y su argumento «pide medidas generales, no obra» están por encima de los datos.
- **Corrección:** «no hay lugares donde el patinete salga peor *que la bici*; los lugares con muchos siniestros lo son para los dos».

### B5. BAJA · CONFIRMADO: textos antiguos que siguen en la plantilla
- **Dónde:** `observatori.plantilla.html` define `lim`, `d3_p`, `h_meta` y `expl` hasta 6 veces (líneas 281, 326, 378, 428, 487 y 554), y los bloques posteriores los tapan con `Object.assign`.
- **Problema:** las versiones antiguas siguen en el código: «el análisis por uso presenta las dos hipótesis, y el crecimiento del patinete con el mismo tráfico…», «¿Vamos hacia el −50 %? De momento, no» y «ordenadas con {pA} y comprobadas con {pB}». La versión final está bien, pero un fallo de orden las haría volver a la página.
- **Corrección:** borrar los bloques muertos.

---

## C. Código

### C1. BAJA · CONFIRMADO: scripts exploratorios con geometría hecha a mano
- **Dónde:** `validar_contadores.py:31-33`, `vmp_carril_bici.py:20-41` y `analisis_viabilidad.py:19-21` calculan distancias equirectangulares a mano, contra la regla del propio proyecto.
- **Problemas de `validar_contadores.py`:**
  - cuenta un mismo siniestro en varios contadores solapados, porque no asigna al más cercano;
  - la tasa «× 250 días × 4 años» la aplica también a contadores con menos años.
- **Efecto:** no alimentan ninguna cifra pública.
- **Corrección:** migrarlos a geopandas o marcarlos como históricos.

### C2. BAJA · PLAUSIBLE: el χ² de homogeneidad de `vmp_vs_bici.py:81-84` no es válido con tan pocos casos
- **Problema:** se aplica con sitios de solo 5 casos, así que muchas frecuencias esperadas son menores que 5 y el χ² no vale.
- **Efecto:** el resultado es negativo y está bien comunicado como «no detectable».
- **Corrección:** test exacto por simulación o el propio GLMM.

### C3. BAJA · CONFIRMADO: otros límites del cálculo (ya conocidos)
- El EB no propaga la incertidumbre de β ni de α.
- A 15 de 145 sitios se les imputa la IMD de vehículos mínima (1.184).
- La IMD de vehículos es solo de 2025 y es el máximo de los tramos a 100 m, que puede ser una calle transversal.

---

## D. Qué se conocía, qué se aplicó y qué es nuevo

| Tema | ¿Se conocía? | ¿Corregido en el código actual? |
|---|---|---|
| ¿Cuentan las espiras patinetes? (A1) | Sí (las notas internas de trabajo, pendiente 5b) | No se puede corregir sin Movilidad. **Nuevo:** las cifras (bici 4 frente a VMP 18 sitios; 68 % frente a 43 %) y que los ejemplos del informe son de patinete. La web no presenta «los dos escenarios». |
| Cruces dentro del círculo (A2) | **No** | — |
| P(θ > 1) como cola alta (A3) | En parte (rev. indep. 19) | Texto en parte cambiado. **Nuevo:** 19,5 esperados frente a 21. |
| Dependencia del radio (A4) | Sí (top-10) | Avisado en la web. **Nuevo:** Jaccard de las etiquetas, 0,43-0,54. |
| Cobertura y «+76 %» (A5) | Sí (rev. indep. 6 y E4) | **Solo se retiró de la web.** `cribado_eb.py:271` y `exportar_web.py:325` siguen igual; el resumen interno del proyecto y las notas internas de trabajo lo afirman. **Nuevo:** el artefacto es mayor en las zonas de contador (181 frente a 154). |
| E3 (IMD/4) y E5 (años) | Sí | **Sí**, aplicados. |
| EB no mejor que el recuento | Sí | Bien comunicado. Fuga: ninguna. |
| Franja de Poisson (B1) | No como problema | — |
| Encuadre de Xàtiva (B2) | No | — |
| «Cuando el tráfico se duplica…» (B3) | Contradicho por las propias notas internas de trabajo | No |
| «No se concentra en puntos» (B4) | En parte (las notas internas de trabajo) | Web bien; el resumen interno del proyecto no |

## Prioridad de las correcciones
1. **A1 + B2:** desglose bici/patinete en las fichas y en el informe; cambiar el ejemplo de Xàtiva.
2. **A2:** SPF con número de cruces o sitios estratificados; volver a sacar las etiquetas.
3. **A5:** borrar `indice_año`/`rel["ix"]` o corregirlos; limpiar el resumen interno del proyecto y las notas internas de trabajo antes de redactar los textos públicos.
4. **B1, B3, A3:** etiquetas de la franja, de la elasticidad y de «claramente».
5. **A4:** «claramente» solo si se mantiene con 75, 100 y 150 m.
6. Lo demás (A6, A9, B5, C1-C3): una línea en el método o limpieza.

Scripts de la revisión: `docs/revision_metodologica/scripts/eb/` (`base.py`, `c1.py`…`c10.py`).
