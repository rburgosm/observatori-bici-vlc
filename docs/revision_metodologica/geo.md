# Revisión metodológica: base de datos y geocodificación (04/11/2026)

Ámbito: `siniestros-de-trafico-2022-2025.json` → `scripts/geocodificar.py` → `data/processed/siniestros_geo.csv`, validaciones y serie anual de la meta (bici o VMP).
Scripts propios (no tocan el proyecto): `docs/revision_metodologica/scripts/geo/a1.py … a14.py` (el diagnóstico de cruces, `cruces_diag.csv`, era una salida temporal y no se conserva).

## Lo que se sostiene (para no perder tiempo)
- **Reproducibilidad del geocodificador.** He reejecutado `geocode()` sobre las 34.244 filas: el `metodo` coincide al 100 % y las coordenadas difieren menos de 5·10⁻⁷ grados del CSV.
- **Serie de la meta.** Bici o VMP, sin duplicados exactos: 1.339 / 1.472 / 1.501 / 1.659 (2022-2025). La base 2025 = 1.659 y la meta = 830 son correctas. La serie no depende de la geocodificación. Bici y VMP salen solo del campo `UNIDADES_IMPLICADAS` («BICICLETA», «VMP»): no hay variantes de escritura (ni «PATINETE» ni «CICLO…» ambiguos).
- **Posición de los cruces** frente a la intersección real de los ejes (shapely): mediana 0 m, p95 2,1 m, p99 40 m y máximo 73 m; 267 casos a más de 25 m (23 de bici o VMP). **Portales** frente al eje: mediana 13 m, p90 24 m y p99 55 m. Es compatible con celdas y radios de 100 m.
- **Ambigüedad de nombres, baja.** 46 siniestros situados se resuelven sin tipo de vía (9 de bici o VMP) y el 1,2 % de los cruces de bici o VMP tiene varias vías candidatas. No hay ningún cruce de una calle consigo misma entre los situados.

---

## A. Errores de código

**A1. `Makefile`: la regla de `siniestros_geo.csv` no depende de las tablas que usa.** Gravedad: media. CONFIRMADO.
- `Makefile`, regla `data/processed/siniestros_geo.csv:` (líneas 12-13). Solo depende de `geocodificar.py` y del JSON de siniestros. Faltan `equivalencias_calles.csv`, `vias.json`, `ejes.geojson` y `portales.geojson`.
- Si se edita una equivalencia o se baja un callejero nuevo, `make` no regeneraría el dataset y la web publicaría un CSV desfasado.
- Conclusión afectada: «reproducible con `make`» (reproducibilidad) y la aportación principal.
- Corrección: añadir esas cuatro dependencias a la regla.

**A2. Portales con el mismo (codvia, número) en sitios distintos: se toma el primero.** Gravedad: baja. CONFIRMADO.
- `geocodificar.py:75` (`portal.setdefault(...)`). Hay 1.019 claves con varias geometrías: 103 a más de 50 m entre sí y 13 a más de 200 m.
- Afecta a 168 siniestros situados por portal (27 de bici o VMP) con una ambigüedad de más de 50 m, y a 42 con más de 200 m (7 de bici o VMP).
- Corrección: si la dispersión supera 50 m, marcar el caso como ambiguo (un método aparte) o usar el centroide del eje entre los candidatos y declararlo.

**A3. Cruces en grandes nudos: el punto es un vértice arbitrario del nudo.** Gravedad: media-baja. CONFIRMADO.
- `geocodificar.py:91-107`: «vértices primero» y `min(res)`.
- 815 cruces (161 de bici o VMP, el 5,5 % de sus cruces) son pares de calles que se acercan a menos de 40 m en dos o más zonas separadas más de 100 m. Son rotondas y avenidas de doble calzada.
- Ejemplos:
  - Tres Cruces × Tres Forques: 110 siniestros, el punto queda a entre 0 y 74 m de las otras zonas del nudo.
  - Peris y Valero × Regne de València: 32 siniestros, entre 0 y 121 m.
  - Hermanos Machado × Santo Domingo Savio: 32 siniestros, entre 0 y 127 m.
- Todo el nudo cae en un solo punto, que puede estar en la celda de 100 m vecina a la de su centro.
- Corrección: para pares con varias zonas, usar el centroide de la zona de cercanía (`ga.buffer(40) ∩ gb`) y guardar su extensión en una columna `incertidumbre_m`.

**A4. Geometría a mano que queda.** Gravedad: baja. CONFIRMADO.
- `validar_geocodificacion.py:20-22`: `metros()` es una distancia equirectangular escrita a mano, contra la regla del proyecto. `geocodificar.py` ya usa shapely en EPSG:25830.
- Corrección: migrar el script a geopandas.

**A5. `numero()` recorre un `set` de codvias y se queda con el primero que tenga portal.** Gravedad: baja. CONFIRMADO.
- `geocodificar.py:110-117`. Con homónimos, el orden de iteración decide el resultado. Hoy afecta a 2 siniestros situados por portal (0 de bici o VMP).
- Corrección: si hay más de un codvia con ese número, marcarlo como ambiguo.

## B. Errores de diseño metodológico

**B1. La cobertura cambia por calle, no solo por año, y la ponderación 1/cobertura del periodo no lo corrige.** Gravedad: alta. CONFIRMADO.
- La cobertura de bici o VMP sube del 80,5 % en 2022-23 al 93,3 % en 2024-25 (×1,16). Ya se conocía y el exportador la pondera por periodo (`exportar_web.py:115-119`).
- Pero el hueco se concentra en calles concretas. Calles con 25 o más casos por periodo, cobertura 2022-23 → 2024-25:

  | Calle | 2022-23 | 2024-25 |
  |---|---|---|
  | Maestro Rodrigo | 0,80 | 1,00 |
  | Hermanos Machado | 0,71 | 0,90 |
  | Naranjos | 0,67 | 0,86 |
  | Guillem de Castro | 0,79 | 0,97 |
  | Antonio Ferrandis | 0,77 | 0,95 |

- Las barras «Siniestros cada año» de cada ficha (`por`, `vy`, `exportar_web.py:102-103` y `126-129`) se cuentan con siniestros geolocalizados y sin ponderar. En esas avenidas muestran una subida de hasta +25 % que es del registro, no de la calle. Lo mismo vale para la comparación A/B de cada lugar.
- Conclusión afectada: la evolución por lugar en las fichas y la tarjeta «los puntos negros no desaparecen» (en menor medida, porque usa rangos).
- Corrección (cualquiera de las tres):
  - (a) calcular la cobertura por calle y periodo, y ponderar por ella;
  - (b) no mostrar barras por año en las fichas antes de julio de 2024;
  - (c) añadir una barra gris «sin situar en esta calle» por año.

**B2. Los 30 «lugares» dependen de dónde cae la rejilla.** Gravedad: alta. CONFIRMADO.
- Con los siniestros de bici o VMP situados (2022-25), desplazar la rejilla de 100 m solo 50 m deja una coincidencia (Jaccard de casos en el top-30) de 0,55 (50 m en x), 0,65 (en y) y **0,43** (en diagonal).
- La celda 30 tiene 14-15 casos y hay empates.
- `exportar_web.py:112` (`x // 100`): una cuadrícula UTM fija y arbitraria.
- Conclusiones afectadas: «26 de los 30 lugares con más siniestros no aparecen en el Plan» y «15 de 30 citados» (PLAUSIBLE que cambien con la rejilla; no lo he recalculado), «13 de 30 persistentes en los tres periodos» y la lista de puntos negros en general.
- Corrección:
  - Usar la unidad que el dato ya trae: agrupar por **nudo** (cruces con el mismo par de codvias o a menos de 30-50 m, con un DBSCAN de scikit-learn o el `buffer`/`dissolve` de geopandas) y por **tramo entre cruces** para los portales.
  - O bien, como mínimo, publicar la sensibilidad (4 desplazamientos) y marcar los lugares estables en todas las rejillas.

**B3. Huecos sistemáticos que sesgan bici frente a VMP.** Gravedad: media. CONFIRMADO.
- Siniestros sin situar: bici, 26,8 % en 2022 y 6,4 % en 2025; VMP, 19,8 % y 3,4 %.
- La causa principal es el Jardín del Turia: 156 de bici o VMP, 99 de ellos de bici, **0 situados**. Le siguen los puentes («LLOC PUENTE DEL REAL», «…ÀNGEL CUSTODIO», «ASSUT DE L'OR»…: 6 + 3 + 3… solo en 2025) y las autovías (V-31, V-21).
- El Turia ya se trata como zona en la web. Pero toda comparación espacial bici frente a VMP (cuotas por lugar, distancia a la red ciclista en `vmp_carril_bici.py`) excluye justo el entorno más ciclista y segregado.
- Corrección:
  - asignar los puentes al punto medio del tablero (los ejes del callejero existen, método «puente») y el Turia a su polígono, como zona;
  - declarar en los análisis bici frente a VMP que el Turia queda fuera.

**B4. En 2022-2024 «X cruce Y» no siempre significa un cruce.** Gravedad: media. PLAUSIBLE (indicio confirmado, efecto sin medir).
- Entre los fallos, los pares de calles que no se tocan son 472 en 2022, 481 en 2023, 233 en 2024 y 20 en 2025, con una mediana de 577 m en 2022 y de 47 m en 2025.
- Si el campo era a veces «a la altura de», algunos «cruces» resueltos en 2022-24 pueden ser referencias aproximadas que han caído donde las dos calles se tocan. Serían errores silenciosos que ninguna validación detecta.
- Conclusión afectada: los puntos negros del periodo P1-P2 y la persistencia entre periodos.
- Corrección:
  - sensibilidad con solo el periodo P3 (julio de 2024-2025) para la lista de lugares;
  - una columna `periodo_formato` en el dataset;
  - una muestra de 30 cruces de 2022-23 revisada a mano frente a la calle Y.

**B5. La subida «Más siniestros, no menos» no es propia de la bici ni del patinete.** Gravedad: media. CONFIRMADO.
- Bici o VMP 2022 → 2025: +23,9 % (1.339 → 1.659). El total de la ciudad: +24,0 % (7.462 → 9.252). El resto (sin bici ni VMP): +24,0 %.
- La cuota de bici o VMP es la misma en 2022 y en 2025: **17,9 %** (17,9 / 17,2 / 16,8 / 17,9). Lo propio es la composición: VMP +44 % y bici −4,7 %.
- Para la meta, esto significa que un cambio de registro o de tráfico general puede cumplir o incumplir el −50 % sin que cambie nada específico de bici y patinete.
- Conclusiones afectadas: la tarjeta `hall[0]` y la lectura de la meta cuando llegue 2026.
- Corrección:
  - decir en la tarjeta que todo el tráfico sube lo mismo;
  - publicar junto a la meta dos series de control: la cuota de bici o VMP sobre el total, y los siniestros con heridos (bici o VMP: 1.056 / 1.067 / 1.150 / 1.279).

**B6. Definición de la meta: unión frente a recuento por vehículo.** Gravedad: media (comunicación del indicador). CONFIRMADO.
- El observatorio cuenta la unión: 1.659 → meta 830. El Plan publica VMP y bici por separado y, como su cifra coincide con las filas sin desduplicar (VMP 2023: 1.003; bici 2024: 511), cuenta por fila y por vehículo.
- Si el Ayuntamiento evalúa 3.2.2 como VMP + bici, la base 2025 es 1.192 + 549 = 1.741 y la meta 870, porque los 80 choques bici–patinete cuentan dos veces.
- Lo que no cuadra: VMP 2025, 1.190 frente a 1.192 del Plan, sin duplicados ese año. PLAUSIBLE: son las 2 filas de VMP del 01/01/2026 (`_id` 34234 y 34244).
- Corrección: una línea en la página de la meta: «Con el recuento por vehículo del Plan, la base sería 1.741 y la meta 870; lo que el observatorio mide es la unión».

**B7. Duplicados aproximados y filas rotas.** Gravedad: baja. CONFIRMADO.
- Duplicados exactos salvo `_id`: 18 (2 de bici o VMP). Están bien quitados.
- Además hay 5 pares de bici o VMP con la misma fecha y ubicación pero campos distintos. Por ejemplo, 2956/2957 (VMP, uno con heridos leves y otro sin heridos) y 17607 «[» / 17608 (Suecia × Alfonso de Córdoba).
- Las 25 filas «[» incluyen 5 caídas: podrían ser hasta unas 5 bici o VMP perdidas, menos del 0,3 % del año.
- No cambia nada. Basta con documentarlo como cota del error de la serie (±5 por año).

**B8. El dato de enero de 2026 ya está en el fichero.** Gravedad: baja. PLAUSIBLE.
- Hay 17 filas del 01/01/2026 (2 de VMP). Cuando se publique 2026, si llega como fichero nuevo y se concatena, esas filas pueden duplicarse con `_id` distinto: la deduplicación «todo salvo `_id`» solo las quita si son idénticas campo a campo.
- Corrección: añadir a `comprobar.py` el solape por fecha entre ficheros.

## C. Problemas de comunicación

**C1. La «aportación principal» no existe todavía como dato abierto.** Gravedad: alta. CONFIRMADO.
- No hay ningún script que escriba el CSV o GeoJSON público. Tampoco hay licencia (no existe `LICENSE`), ni diccionario de campos, ni versionado. La web dice «Disponible en la versión publicada» (`observatori.plantilla.html`, `d1_b`).
- `siniestros_geo.csv` no tiene:
  - un campo de precisión ni de incertidumbre;
  - el codvia;
  - las marcas de duplicado, de fila «[» y de periodo de formato;
  - la versión del callejero.
- Corrección:
  - un script `scripts/exportar_dataset.py` (objetivo `make dataset`) que escriba CSV y GeoJSON con: `id` del portal, campos originales, `metodo`, `incertidumbre_m` (cruce a 0-40 m, nudo con varias zonas = su extensión, portal ≈ 15 m, portal cercano = distancia al número pedido), `codvia_1`/`codvia_2`, `periodo_formato`, `duplicado`, `unidades_rotas` y `version`;
  - un README con la licencia CC BY 4.0, la atribución a la fuente y la suma de comprobación del JSON de origen.

**C2. «Precisión estimada del 94-100 %» de la geocodificación sobrestima lo validado.** Gravedad: media. CONFIRMADO.
- las notas internas de trabajo y la lista interna de pendientes.
- `verificar_muestra_osm.py:41-44` solo comprueba que alguna palabra de **alguna** de las dos calles coincida cerca del punto. Un cruce pasa aunque esté en otro lugar de una de las calles. La muestra son 50 puntos, solo de VMP, y no mide metros.
- Con 44 de 50, el IC95 de Wilson va del 76 % al 94 %. Con 47 de 50 (contando los 3 explicados), del 84 % al 98 %.
- La página de método ya lo dice bien («comprueba el nombre, no el error en metros»), pero los documentos internos que alimentarán los textos públicos no.
- Corrección: sustituir la cifra por las métricas de posición de esta revisión:
  - cruce frente a intersección de ejes: p95 2 m y p99 40 m;
  - portal frente a eje: mediana 13 m y p99 55 m;
  - nudos con varias zonas: 5,5 % de los cruces de bici o VMP;
  - y la muestra con su IC.

**C3. Cifras de cobertura desfasadas en los documentos.** Gravedad: baja. CONFIRMADO.
- el resumen interno del proyecto (86,8 %) y la tabla de las notas internas de trabajo (29.740) son anteriores a la mejora del 03/11. Hoy son 30.225 (88,3 %).

**C4. Método web: «Portal cercano: el número más cercano de la misma calle».** Gravedad: baja. CONFIRMADO.
- En realidad es el de la misma paridad y a ±10 números como máximo (`geocodificar.py:114`). Conviene decirlo, porque fija el error máximo (unos 5 portales).

---

## Qué ya se conocía, si se aplicó y qué es nuevo

| Problema | ¿Conocido? | ¿Corregido en el código actual? |
|---|---|---|
| Cobertura creciente por año (B1, parte anual) | Sí (revisión independiente §1; estado «Cobertura…») | **Parcial**: la meta usa todos los siniestros (bien) y los puntos negros se ponderan por periodo. **Nuevo**: el sesgo por calle y las barras por año sin ponderar en las fichas. |
| Cruces solo por vértices; geometría a mano (E6) | Sí | **Sí** en `geocodificar.py` (shapely, vértices y luego segmentos). **No** en `validar_geocodificacion.py:20` (A4). **Nuevo**: el punto arbitrario en nudos con varias zonas (A3). |
| La validación OSM solo mira el nombre (E6) | Sí | Bien dicho en la web. **No** en las notas internas de trabajo/la lista interna de pendientes («94-100 %»): C2. |
| Sensibilidad a la rejilla (rev. ind. 7c y 9) | Sí | **No aplicado**: sigue la rejilla fija y no se publica la sensibilidad. Cuantificado aquí (Jaccard 0,43-0,65): B2. |
| Jardín del Turia sin punto | Sí (estado; revisión de coherencia A1) | Sí, como zona. **Nuevo**: los puentes y el sesgo bici frente a VMP en los análisis espaciales (B3). |
| «Cruces» entre calles lejanas en 2022-24 | Sí (estado, «Cobertura…») | Se trató como un fallo. **Nuevo**: el riesgo de cruces mal situados en silencio en 2022-24 (B4). |
| Filas «[» y duplicados | Sí (E-menor) | Documentados en la página de método. **Nuevo**: los duplicados aproximados y la cota ±5 (B7). |
| 1.190 frente a 1.192 y el recuento por vehículo | Sí (coherencia B9) | Texto corregido. **Nuevo**: la meta alternativa 870 con el recuento del Plan y la hipótesis del 01/01/2026 (B6). |
| La cuota de bici o VMP es constante y la subida es de toda la ciudad | **Nuevo** | — (B5) |
| Dependencias del `Makefile` | **Nuevo** | — (A1) |
| Portales duplicados (codvia, número) | **Nuevo** | — (A2) |
| El dataset descargable no existe, sin licencia | Implícito («disponible en la versión publicada») | — (C1) |

**Veredicto.** La serie de la meta y la geocodificación de cada punto son sólidas para trabajar con 100 m. Ninguna conclusión pública queda invalidada por un error de código. Los riesgos serios son tres:
1. Las conclusiones por lugar dependen de una rejilla arbitraria y de una cobertura desigual por calle (B1 y B2).
2. La tarjeta «más siniestros» no distingue la bici y el patinete de la tendencia general (B5).
3. El dataset que se presenta como aportación principal aún no se publica con licencia, precisión y trazabilidad (C1).
