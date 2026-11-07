# Revisión metodológica (04/11/2026): síntesis

Cuatro revisiones independientes, escépticas y en paralelo, que recalcularon cada cifra con scripts propios y sin tocar el proyecto. Leyeron las revisiones anteriores (`docs/revision_independiente.md` y `docs/revision_coherencia.md`) solo al final.

| Revisión | Ámbito | Informe | Scripts |
|---|---|---|---|
| Datos y geocodificación | serie, bici/VMP, posición, dataset abierto | `geo.md` | `scripts/geo/` |
| Exposición y modelos | Bayes empírico, contadores, VMP frente a bici | `eb.md` | `scripts/eb/` |
| Puntos negros y meta | persistencia, rejilla, anillo del Plan, pista, `exportar_web.py` | `puntos.md` | `scripts/puntos/` |
| Afirmaciones públicas | las tres páginas frente a la evidencia | `relato.md` | `scripts/relato/` |

Los scripts leen `data/` con rutas absolutas y se ejecutan con `.venv/bin/python -I`. Son material de la revisión, no forman parte de `make`.

**Aviso:** los revisores son agentes automáticos lanzados por el propio proyecto. No son una revisión externa y no deben presentarse como tal.

## Veredicto

No hay errores de cálculo que tumben el proyecto, pero sí errores de diseño y de lectura que hoy invalidan varias afirmaciones públicas. Ningún revisor encontró fuga en la validación, y la geocodificación se reproduce al 100 %. Los problemas están en:

- **qué se compara:** la subida de la ciudad, el año base y el denominador del patinete;
- **cómo se agrupa:** la rejilla de 100 m;
- **cómo se cruza con el Plan:** claves que faltan.

## Lo que se sostiene (comprobado por al menos un revisor)

- **La serie de la meta.** Siniestros con bici o VMP sin duplicados: 1.339, 1.472, 1.501 y 1.659 (de 2022 a 2025). La base 2025 es 1.659 y la meta, 830.
- **El indicador.** Coincide con el de la acción 3.2.2 (`pdsv.txt:3080`): siniestros con ciclistas o VMP, de cualquier gravedad, −50 %.
- **La geocodificación.**
  - Se reproduce al 100 %.
  - Error de posición en cruces: mediana de 0 m y p95 de 2 m (máximo 73 m).
  - Error de posición en portales: mediana de 13 m.
  - Compatible con celdas y radios de 100 m.
- **Hay concentración persistente.** Al ordenar con 2022-23 y medir en 2024-25, los 30 primeros suman 278 siniestros, frente a unos 85 con un nulo local (permutación en bloques de 500 m) y 53 con el global (p < 0,0005).
- **El modelo EB se reproduce.** α = 0,493, elasticidad 0,662 y 21 sitios con P > 0,95. La validación no tiene fuga.
- **El tráfico del carril bici sube de 100 a 115.** Con la serie oficial de Movilidad da 118,5.
- **Los resultados nulos de VMP frente a bici** se comunican bien en la web («no detectable»).
- **Correcciones previas aplicadas:**
  - retirado el +76 %;
  - retirada la tarjeta «0 de 2.508»;
  - IMD dividida por los años con dato;
  - orden por total;
  - clasificación de vehículos;
  - cobertura en las limitaciones.

## Problemas, por prioridad

Entre corchetes, los revisores que lo detectan: G (geo), E (EB), P (puntos), R (relato).

### Críticos: invalidan una afirmación pública o la aportación principal

1. **Anillo del Plan y «Fuera del radar del Plan» [P, R].**
   - `exportar_web.py` (`CLAVES` y `plan_de()`) descarta sin aviso 8 de las 37 filas de `pdsv_lugares.csv`.
     - Tres Cruces × Campos Crespo, que el Plan cita, sale como «no lo menciona». Lo mismo pasa con Pelayo × Xàtiva.
     - El reparto real es **5 · 12 · 13**, o **5 · 13 · 12** si cuenta Peris y Valero (el Plan solo pone una foto).
     - `comprobar.py` solo verifica que la suma sea 30.
   - Además hay un fallo de lógica: el Plan solo publica los tres primeros de cada lista, así que no aparecer no prueba que el lugar esté «fuera del radar».
   - **Corrección:**
     - claves para todas las filas y un `assert` si falta alguna;
     - decidir sobre Peris y Valero y sobre el Anillo Ciclista;
     - redactar: «El Plan solo publica los tres primeros. De nuestros 30 cita 5 por su nombre y 12-13 por su calle; pedimos la lista completa.»
   - las notas internas de trabajo y `docs/enfoque.md` arrastran cifras antiguas (4/6/20 y «26 de 30»).
2. **El dataset geolocalizado, la aportación principal, no existe como dato abierto [G].**
   - Falta un script de exportación y faltan licencia, diccionario de campos y versionado. La web dice «Disponible en la versión publicada».
   - **Corrección:**
     - `scripts/exportar_dataset.py` y un objetivo de `make`;
     - CSV y GeoJSON con `metodo`, `incertidumbre_m`, `codvia`, marcas de duplicado y de fila rota, y el periodo de formato;
     - README con CC BY 4.0 y atribución.
3. **El +24 % no es propio de la bici y el patinete [G, R].**
   - Todos los siniestros de la ciudad suben lo mismo: 7.462 → 9.252 (+24,0 %). La cuota de bici o VMP se queda en el 17,9 %.
   - Lo que más crece son los siniestros sin heridos (+31 % en la ciudad y +34 % con bici o VMP). Encaja con un cambio de registro: el Plan describe el SIASV, creado en julio de 2024 con los estándares de la DGT.
   - Hay señal real: con heridos, bici o VMP suben un 21 %, frente al 10 % del resto.
   - Lo propio es la composición: VMP +44 % y bici −5 %.
   - **Corrección:**
     - reescribir «Más siniestros, no menos» y la «tendencia en contra»;
     - publicar dos series de control: la cuota sobre el total y los siniestros con heridos.
4. **«Más de lo normal para el tráfico» es sobre todo señal del patinete, medida con un contador de bicis [E].**
   - El número de sitios con P > 0,95 cambia mucho según el modelo:

     | Modelo | Sitios con P > 0,95 |
     |---|---|
     | Solo bici | 4 |
     | Solo VMP | 18 |
     | Bici + VMP | 21 |

   - Tirso de Molina y Balaciart no destacan con el modelo de bici (P de 0,74 y 0,61). Con el de patinete, P = 1,00.
   - El «exceso» puede ser solo composición del tráfico: que la espira no cuente patinetes o que su proporción cambie de un sitio a otro. Es la pregunta abierta del pendiente 5b.
   - Además:
     - falta como covariable el número de cruces dentro del círculo (mejora el modelo, p ≈ 2e-7, y los 21 sitios pasan a 18);
     - sin ningún punto especial se esperan de media 19,5 sitios con P > 0,95, y se observan 21;
     - la lista cambia con el radio (Jaccard de 0,43 a 0,54).
   - El informe presenta Xàtiva (P138) como «explicada por el tráfico», pero es el n.º 2 del exceso, con P = 0,996.
   - **Corrección:**
     - observados y esperados de bici y de VMP por separado en cada ficha;
     - «claramente» solo si se cumple con bici y con 75, 100 y 150 m;
     - añadir los cruces al modelo;
     - rótulo: «por encima de la media de puntos con tráfico parecido»;
     - cambiar el ejemplo de Xàtiva (P237 sí encaja: 26 frente a 23,4).
5. **Los 30 lugares dependen de dónde cae la rejilla de 100 m [G, P, E].**
   - Al desplazar la rejilla 25-75 m se mantienen de 18 a 24 de los 30, con un Jaccard de 0,43 a 0,65.
   - El recuento del n.º 1 va de 34 a 57; se publica 48.
   - La causa es que el 27 % de los siniestros comparten coordenada con al menos otros cuatro (pilas en el nodo del cruce).
   - Afecta a los 30 lugares, al anillo, a «13 de 30» y a las fichas.
   - **Corrección:** agrupar por nudo de cruce y tramo (buffer y dissolve, o DBSCAN de 30-50 m) en lugar de por celdas fijas. Hasta entonces, publicar la sensibilidad.

### Altos

6. **Base 2025 = pico de la serie [R, P].**
   - Partir del peor año favorece al Plan por regresión a la media.
   - **Corrección:**
     - decirlo en metode;
     - añadir un escenario con la media 2023-2025 (≈ 1.544);
     - estado «compatible con la senda» con una prueba de Poisson (`statsmodels` `test_poisson_2indep`). Un 2026 con 1.480 saldría hoy «sobre la senda», aunque el IC95 de la senda es 1.370-1.519.
7. **Qué se mide frente a qué dice el Plan [G, R].**
   - El −50 % es el indicador de una acción (3.2.2), no «la meta de València». La meta del Plan es de fallecidos y heridos graves.
   - Con el criterio del Plan (por vehículo, sin desduplicar), la base 2025 sería 1.739 y la meta, 870. La revisión daba 1.741 porque usaba el VMP de 2025 del Plan (1.192), que incluye 2 filas del 01/01/2026.
   - **Corrección:**
     - «el indicador de la acción 3.2.2 pide…»;
     - explicar la unión (830) frente a la suma por vehículo (870).
8. **Alameda–Zaragoza «de 16 a 6» [R].**
   - La dirección literal «en el cruce» pasa de 14 a 2, pero en todo el paseo hay 50, 50, 39 y 44 siniestros.
   - La bajada empieza en 2024, con el cambio de formato, y antes de la obra.
   - El lugar se eligió por ser el n.º 1, el caso típico de regresión a la media.
   - **Corrección:** reescribirlo como el relato propone; no atribuir el cambio a la obra.
9. **«13 de 30 se repiten» y los 17 sellos «no se mantiene» se leen al revés [P, R].**
   - Con persistencia perfecta y ruido de Poisson, saldrían unos 12 (IC90 9-16).
   - Además, el «13 de 30» se mide dentro de la muestra, con empates resueltos por la coordenada X (`nlargest(60)`).
   - **Corrección:**
     - quitar el sello;
     - publicar la prueba fuera de muestra con nulo local, que sí es robusta.
10. **La «pista» de las fichas [P, R, ya en la revisión independiente].**
    - Holm corrige 4 pruebas por lugar, cuando hay 124 en el mapa.
    - La referencia es la ciudad, cuando debería ser los cruces (70 % de choques con vehículo frente al 57 % de la ciudad).
    - Corregida, pasa de 7 pistas a 3.
11. **Barras por año de las fichas sin corregir la cobertura [G, P].**
    - El hueco de 2022-23 se concentra en ciertas avenidas (Hermanos Machado, Naranjos, Maestro Rodrigo).
    - Los portales pasan de 322 a 775 (+141 %) y los cruces, de 694 a 807. Los lugares de portal «crecen» por el formato del dato.
    - **Corrección:** ponderar o avisar junto al gráfico. Valorar también los puntos negros solo desde julio de 2024.
12. **El índice anual «crece a igual uso» sigue vivo fuera de la web [E].**
    - `cribado_eb.py:271` y `exportar_web.py:325` lo siguen exportando sin corregir.
    - El artefacto es mayor en las zonas de contador: índice 124 con todos los siniestros, 154 con los geolocalizados y 181 con los de contador.
    - El índice del VMP, corregido, baja de 178 a 146 (IC95 109-196).
    - el resumen interno del proyecto («crecen a igual uso», «los puntos negros piden obra», «no se concentran») y las notas internas de trabajo lo siguen afirmando: es un riesgo directo para los textos públicos.

### Medios

13. **«Cuando el tráfico se duplica, los siniestros no» (metode) [E, R].** Es una elasticidad transversal entre sitios (0,66). Con solo bici es 0,87, compatible con 1, y dentro de cada sitio da 0,47 [−0,41 a 1,36]. Hay que reformularlo como asociación entre puntos.
14. **La franja de «variación normal» es de Poisson [E].** Deja fuera 46 de 145 sitios, cuando se esperaría un 5 %; con la del modelo, solo 2 quedan por encima. Hay que cambiar la etiqueta o la franja.
15. **«Dónde actuar» sobre un mapa sin exposición [R].** Propuesta: «Dónde se acumulan». El rótulo «Punto negro» se usa igual para concentración sin exposición.
16. **Frases que se pueden leer mal [R]:**
    - «dos revisiones externas»: fueron agentes del propio proyecto;
    - «todo el código es abierto»: el repositorio no está publicado (pendiente 62);
    - «ninguna cifra está escrita a mano»: hay cifras transcritas (`ctx2026`, `plan_graves_2024`, `DEST`).
17. **Infradeclaración y vigilancia, distintas en bici y VMP [R].** No se mencionan: caídas sin atestado, controles, casco obligatorio desde octubre de 2026. Afectan a «7 de cada 10» y a la evaluación de 2026. Hay que añadirlo a las limitaciones.
18. **Huecos de geolocalización que sesgan bici frente a VMP [G].** En 2022 quedan sin situar el 27 % de la bici y el 20 % del VMP, sobre todo en el Jardín del Turia, los puentes y las autovías. Los análisis espaciales excluyen el entorno más ciclista.
19. **Grandes nudos [G].** 815 cruces (161 de bici o VMP) caen en un vértice arbitrario del nudo, a hasta 127 m de otras zonas (por ejemplo, Tres Cruces × Tres Forques, con 110 casos). Usar el centroide de la zona e `incertidumbre_m`.
20. **«Cruces» entre calles que no se tocan en 2022-24 [G].** Son 472 en 2022, con una mediana de 577 m. Algunos se resuelven mal sin aviso.
21. **«El Plan, al día» no existe [P].** No hay `plan_seguimiento.csv` ni sección, pero `enfoque.md` lo presenta como «ya se puede».
22. **«Baja gravedad» +44 % con bici o VMP en 2025 [R].** Hay que matizar «comparable desde 2024».
23. **`Makefile` [G].** `siniestros_geo.csv` no depende de `equivalencias_calles.csv`, `vias.json`, `ejes.geojson` ni `portales.geojson`.
24. **Peso por cobertura por periodo y no por tipo de dirección [P].** El efecto es pequeño (28 de 30 iguales).
25. **Sitios vecinos no independientes [E].** 57 de 145 tienen otro a menos de 200 m (Spearman 0,20). El bootstrap no reajusta el modelo.

### Bajos

- **Datos y geocodificación:**
  - portales repetidos: se queda la primera geometría (168 casos con más de 50 m, 27 de bici o VMP);
  - homónimos que dependen del orden del set (2 casos);
  - 25 filas «[» fuera de los recuentos sin decirlo;
  - 5 pares casi duplicados;
  - posible duplicado de las 17 filas del 01/01/2026 al concatenar el fichero de 2026.
- **Código heredado:**
  - distancias a mano en `validar_*`, `vmp_carril_bici.py` y `analisis_viabilidad.py`;
  - χ² no válido en `vmp_vs_bici.py:81-84` (el resultado sigue siendo negativo);
  - `MOTOR` muerto y `comprobar.py:110`;
  - textos tapados repetidos en `observatori.plantilla.html`.
- **Textos:**
  - la «precisión del 94-100 %» en las notas internas de trabajo y la lista interna de pendientes: solo comprueba el nombre; con 44 de 50, el IC95 es 76-94 %;
  - cifras desfasadas en el resumen interno del proyecto (86,8 % y 29.740; hoy son 88,3 % y 30.225);
  - «portal cercano» mal descrito;
  - incoherencias menores entre páginas: «cuenta por vehículo» frente a «fecha de extracción», «el patinete ya es mayoría», la serie `falta3`.

## Orden de corrección propuesto

1. Anillo del Plan (1): es un error de código y se arregla rápido.
2. Textos que hoy son falsos o exagerados (3, 7, 8, 9, 13, 15, 16): solo es redacción.
3. Desglose bici/VMP en el exceso y el ejemplo de Xàtiva (4).
4. Agrupar por nudo y tramo en lugar de la rejilla (5), y rehacer el top 30, el anillo, la persistencia fuera de muestra y la pista (9, 10).
5. Meta: el escenario 2023-25, el estado «compatible» y las series de control (3, 6).
6. Dataset abierto publicable (2), con `incertidumbre_m` (19).
7. Limpiar el resumen interno del proyecto y las notas internas de trabajo de afirmaciones retiradas (12) antes de redactar los textos públicos.
