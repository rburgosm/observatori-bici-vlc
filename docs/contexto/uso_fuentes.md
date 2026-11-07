# Uso y parque de bicis y patinetes: fuentes para dar contexto a los siniestros

Búsqueda del 03/11/2026. **Para qué:** saber si el aumento de siniestros con bici o VMP (1.339 → 1.659, +24 % entre 2022 y 2025) va más rápido o más despacio que el uso, y poder decirlo en la web sin inventar un denominador.

Conviene distinguir tres tipos de dato, que no son intercambiables:

- **Flujo (ventas):** cuántos vehículos se venden cada año.
- **Stock (parque):** cuántos hay.
- **Uso (viajes o pasos):** cuántas veces circulan. Es la exposición que importa.

Solo el uso mide la exposición. Las ventas y el parque son contexto nacional.

## 1. Tabla de fuentes

| Fuente | Qué mide | Tipo | Ámbito | Periodo | ¿Separa bici y VMP? | Fiabilidad | URL |
|---|---|---|---|---|---|---|---|
| **Contadores (espiras) del carril bici, Movilidad** (ya en `data/raw/intensidades/`) | IMD de laborables por punto | Uso | València, solo carril bici | 2019-sep 2026 (mensual) | **No.** El Ayuntamiento lo comunica como «uso de la bicicleta y el patinete» (nota de 17/08/2022) | Alta como serie. El panel de puntos cambia y hay meses estimados | valencia.es/cas/movilidad/otras-descargas; nota: [Valencia Plaza 17/08/2022](https://valenciaplaza.com/valenciaplaza/el-uso-de-la-bicicleta-crece-un-21-desde-principios-de-ano-y-apuntala-su-crecimiento-constante) |
| **Análisis de movilidad. Ejercicio 2025** (Ayuntamiento, presentación de enero de 2026) | Gráficos mensuales de carril bici (30 puntos representativos) y de **viajes de Valenbisi**, de 2019 a 2025 | Uso | València | 2019-2025 | No | Alta (fuente municipal), pero Valenbisi solo en gráfico, sin tabla | [PDF](https://www.valencia.es/documents/20142/232631/an%C3%A1lisis%20movilidad%202025.pdf/3c8e820e-2de4-bda6-eb69-01505c335940) |
| **Valenbisi**, totales anuales | Viajes en bici pública (mecánica) | Uso | València | 2023: 4.357.218; 2025: unos 5,4 M | Solo bici (Valenbisi) | Media-alta: prensa con nota municipal (2023) y Plan Director (2025) | [Valencia Plaza 08/06/2024](https://valenciaplaza.com/valenciaplaza/los-usuarios-de-valenbisi-crecen-un-15-en-2023-hasta-las-510000-personas-y-los-4-3-millones-de-movimientos); `data/raw/pdsv/pdsv.txt` (apartado 2.2.3) |
| **Conteos manuales a pie de carril bici**, Agència de la Bicicleta (ETRA y Esther Anaya) | Proporción de bici, VMP y otros | Uso (composición) | València: 2 puntos en 2019 y 5 en 2020 | Octubre de 2019 y octubre-noviembre de 2020 | **Sí** | Media: pocos puntos y pocos días; 2020 fue año de pandemia | [El Periòdic 03/02/2020](https://www.elperiodic.com/valencia/cada-cuatro-vehiculos-carril-bici-valencia-bici_663307); [elDiario.es 08/04/2021](https://www.eldiario.es/comunitat-valenciana/valencia/bici-patinete-aumenta-mujeres-valencia-plena-pandemia-especialmente-carriles-bici-protegidos_1_7389625.html) |
| **Estudio «La red ciclista en València»**, Càtedra d'Economia Col·laborativa (UV, financiada por Las Naves) | Proporción de bici propia, patinete y Valenbisi | Uso (composición) | València: 12 puntos | 16-20/11/2020 (28.591 observaciones) y una edición de 2021 | **Sí** | Media-alta para 2020-21 (muestra grande). No hay ediciones posteriores | [Resumen ejecutivo 2020 (PDF)](https://www.uv.es/ceconomiacol/estudi_mobilitat/CAS/Resumen_ejecutivo_movilidad.pdf); [página del informe](https://www.uv.es/catedra-economia-colaborativa-transformacion-digital/es/areas-investigacion/movilidad/informe-movilidad-sostenible-colaborativa-valencia.html) |
| **Barómetro de la Bicicleta en España 2024** (Red de Ciudades por la Bicicleta y GESOP) | Uso declarado de la bici; tenencia de bici, de bici eléctrica y de **patinete eléctrico** en casa | Encuesta (uso declarado y stock en hogares) | España, con submuestra de 400 personas en València ciudad | Ediciones 2008-2024. **El patinete solo se pregunta en 2024** (no en 2022) | Sí | Media. València con n = 400 (error de unos ±5 puntos); en 2024 cambia el método (CATI + online) | [Informe 2024 (PDF)](https://www.industriambiente.com/media/uploads/noticias/documentos/2024_RedBici_Barometro_Bicicleta_Informe.pdf) |
| **AMBE** (Asociación de Marcas y Bicicletas de España), informe anual con Cofidis | Ventas de bicis y de bicis eléctricas | Flujo | España | Anual. **No incluye patinetes** | Solo bici | Alta: es la fuente del sector y se cita igual en toda la prensa | Ver §2 |
| **Ventas de patinetes** (GfK citado en prensa sectorial) | Unidades vendidas | Flujo | España | Datos sueltos de 2022 y 2023 | Solo VMP | **Baja**: no hay serie publicada; las cifras llegan por prensa, a veces sin fuente | [Newsbook 28/06/2023](https://newsbook.es/actualidad/esprinet-y-red-bull-viaje-de-negocio-en-patinete-electrico-20230628103472.htm); [Diario de Huelva 18/10/2025](https://www.diariodehuelva.es/articulo/sin-categoria/ventas-patinetes-electricos-caen-44%E2%80%AF-espana-nuevas-normas-endurecen-uso-huelva/20251018055309331043.html) |
| **DGT y Ministerio del Interior**: Registro de Vehículos Personales Ligeros (RD 52/2026) | Parque estimado de VMP | Stock | España | Estimación puntual (enero de 2026) | Solo VMP | Baja-media: es una estimación oficial redonda, sin método. **El registro no publica inscripciones** | [Nota de prensa de Interior, 27/01/2026 (PDF)](https://www.dgt.es/export/sites/web-DGT/.galleries/downloads/nota_prensa/2026/260127-mir_DGT_pone_marcha_registro_patinetes.pdf); [Revista DGT, 21/01/2024](https://www.dgt.es/comunicacion/noticias/vmp-nuevas-reglas-nueva-formacion/) |
| **Seguro obligatorio de VMP** (Ley 5/2025) | Pólizas | Stock | España | Desde 2026 | Solo VMP | **No hay cifras publicadas** | — |
| **Plan Director de Seguridad Vial 2026-2030** | Reparto modal, Valenbisi e indicador de desplazamientos en bici o VMP | Uso | València | Puntual | No | Alta (documento municipal), con cifras de segunda mano | `data/raw/pdsv/pdsv.txt` |
| **Portal opendata.vlci.valencia.es** (consulta CKAN del 03/11/2026) | Valenbisi: solo disponibilidad en tiempo real (capa 228). Espiras de bici: capa 225, con puntos y sin series (marcada «con errores de procesamiento») | — | València | Sin histórico | No | — | `package_search?q=valenbisi`, `bicicleta`, `patinete` (0 resultados), `aforos` |
| Observatorio de la Movilidad Metropolitana (OMM) y encuesta del PMUS | Reparto modal del área metropolitana | Uso | València y área | PMUS de 2013; el OMM no publica Valenbisi por año en lo encontrado | No | Antigua o sin el dato | [OMM](https://observatoriomovilidad.es/) |

**Fuentes que no dan el dato (comprobado):**

- **Registro de VMP de la DGT:** no publica cuántos vehículos hay inscritos, ni en España ni por provincia.
- **Seguro obligatorio:** no hay cifras de pólizas.
- **Ventas de patinetes:** no hay ninguna serie anual pública y fiable.
- **Valenbisi:** no hay totales oficiales publicados de 2022 ni de 2024.
- **Portal municipal:** no tiene ningún dataset histórico de uso de bici o VMP. Las series de los contadores están en la web de Movilidad, no en el portal.
- **Conteos manuales que separen bici y patinete:** no hay ninguno posterior a 2021.

## 2. Cifras clave por año

### 2.1 València: uso (la exposición)

| Año | Carril bici, panel fijo de 116 contadores (cálculo propio, la lista interna de pendientes n.º 42) | Carril bici, 30 puntos «representativos» (Movilidad, media anual de los totales mensuales; cálculo propio) | Valenbisi (viajes) |
|---|---|---|---|
| 2019 | — | 44.967 (66) | unos 5,1 M (lectura del gráfico) |
| 2021 | — | 59.915 (87) | — (+23 % en 2022 frente a 2021, según JCDecaux) |
| **2022** | **100** | 68.590 (**100**) | **unos 4,0 M** (lectura del gráfico) (100) |
| 2023 | — | 72.623 (106) | **4.357.218** (publicado) (109) |
| 2024 | — | 75.057 (109) | unos 4,8 M (lectura del gráfico) (120) |
| **2025** | **115** | 81.923 (**119**) | **unos 5,4 M** (Plan Director) (**136**) |

Notas:

- La serie de 30 puntos sale de la hoja «Carriles Bici Representativos» de `evolucion_imd_mensual_2019-sep2026.xlsx` (fila de totales). Incluye IMD estimadas y puntos de carriles nuevos. El propio Ayuntamiento atribuye el crecimiento «a la construcción de nuevos km de carriles bici», así que mezcla más uso con una red más grande. **El panel fijo de 116 contadores (115) es el indicador más limpio.**
- Las cifras de Valenbisi de 2022 y 2024 son una **lectura aproximada (±5 %) del gráfico mensual** de la diapositiva 19 del *Análisis de movilidad 2025*. La suma leída para 2023 da unos 4,36 M y la de 2025 unos 5,4 M, lo que cuadra con las cifras publicadas. No son cifras oficiales; para usarlas hay que pedir la serie a Movilidad o a JCDecaux.
- El «+15 %» de 2023 en Valenbisi es de **personas usuarias** (más de 510.000), no de viajes.

### 2.2 València: composición del tráfico en el carril bici (bici frente a VMP)

| Fecha | Bici (propia + Valenbisi) | VMP | Fuente |
|---|---|---|---|
| Octubre de 2019 | 74-75 % | 25 % | Agència de la Bicicleta (2 puntos, 2 días) |
| Octubre-noviembre de 2020 | 71 % | 28 % | Agència de la Bicicleta (5 puntos) |
| Noviembre de 2020 | 71 % (58 % propia y 13 % Valenbisi) | casi un tercio (entre el 20 % y el 31 % según la zona) | Càtedra UV (12 puntos, 28.591 observaciones) |
| 2021 | 69 % (57 % propia y 12 % Valenbisi) | 31 % | Càtedra UV |
| 2022-2025 | **sin dato** | **sin dato** | — |

Uno de cada cuatro o cinco vehículos del carril bici era un patinete en 2019-2021, y la proporción subía. Por tanto, los contadores **no** miden solo bicis. No hay ningún dato de composición del periodo 2022-2025.

### 2.3 València: tenencia y uso declarado (Barómetro 2024, n = 400)

- **El 21,0 % de las personas encuestadas en València tiene algún patinete eléctrico en casa.** Es la proporción más alta de las siete grandes ciudades; la media de España es el 15,2 %. Es el único punto de la serie: el barómetro de 2022 no lo preguntaba.
- **El 57,4 % de la población de València usa la bici** (con cualquier frecuencia), frente al 48,1 % de España. Es la segunda ciudad tras Sevilla.
- En España, la proporción de personas que usan la bici fue del 52,9 % en 2019, del 57,1 % en 2022 y del 48,1 % en 2024. El cambio de método de 2024 impide leerlo como una caída real.
- En España, el 6 % de quienes tienen bici tiene alguna eléctrica (3,1 % solo eléctrica y 2,9 % de los dos tipos).

### 2.4 València: Plan Director de Seguridad Vial (`pdsv.txt`)

- **Reparto modal:** la bici supone el 4,8 % de los viajes internos y el pie más del 50,5 %, «según la planificación metropolitana más reciente», sin año. El PMUS de 2013 es la última encuesta propia.
- **Indicador del Plan «Incremento de desplazamientos en bici/VMP»:** se mide con «aforos en principales carriles bici». Línea base +3,4 % y meta +5 % anual. **El propio Plan usa los contadores como exposición conjunta de bici y VMP**, lo que respalda nuestro indicador.
- Habla del «crecimiento del uso de VMP y bicicletas» sin cuantificarlo. En 2025, los lesionados en VMP aumentan un 14 % respecto a 2024.

### 2.5 España: ventas (flujo) y parque (stock)

| Año | Bicis vendidas (AMBE) | **Bicis eléctricas vendidas (AMBE)** | Índice de eléctricas, 2022 = 100 | Patinetes |
|---|---|---|---|---|
| 2019 | — | unas 143.000 (deducido: las de 2024 son un 36 % más) | 61 | — |
| 2021 | 1.571.368 | 223.561 | 95 | — |
| **2022** | unos 1,35 M | **236.183** | **100** | unos 300.000 vendidos (previsión del sector, sin fuente primaria) |
| 2023 | unos 1,26 M (deducido) | más de 241.000 | 102 | 251.000 entre jun-2022 y may-2023 (−4 %); ene-may de 2023: 91.000 unidades (GfK) |
| 2024 | 1.101.057 | 194.986 | 83 | «−44 % frente a 2023» (Diario de Huelva, sin fuente) |
| **2025** | 1.093.478 | **234.880** (21,5 % del total) | **99** | — |

Fuentes de AMBE (vía Híbridos y Eléctricos):

- [2021](https://www.hibridosyelectricos.com/bicicletas/bicicletas-electricas-tambien-exito-espana-record-ventas-2021_56900_102.html)
- [2022](https://www.hibridosyelectricos.com/bicicletas/ya-sabemos-precio-medio-236000-bicicletas-electricas-vendidas-en-espana-en-2022_69098_102.html)
- [2023](https://www.hibridosyelectricos.com/bicicletas/bicicletas-electricas-lideran-ventas-sector-ligeramente-estancado_74604_102.html)
- [2024](https://www.hibridosyelectricos.com/bicicletas/en-2024-se-vendieron-menos-bicicletas-en-espana-aunque-si-se-fabricaron-mas_79449_102.html)
- [2025](https://www.hibridosyelectricos.com/bicicletas/2-cada-10-bicicletas-se-han-vendido-en-nuestro-pais-en-2025-fueron-bicicletas-electricas_85957_102.html)

Las ventas de bicis eléctricas están **planas** entre 2022 y 2025: el flujo anual no crece. Como cada año se venden unas 200.000-240.000, el parque sí crece, pero no se puede estimar sin una tasa de bajas, que nadie publica. AMBE no informa por comunidad autónoma en lo encontrado.

**Parque de VMP en España:**

- «Más de 4 millones» circulando, según la estimación de Interior y la DGT (enero de 2026).
- «Unos 5 millones», según la Federación Española de VMP, citada por la DGT (enero de 2024).

Son dos estimaciones redondas, sin método, que no permiten trazar una evolución.

## 3. Qué podemos usar como exposición, y con qué limitaciones

1. **Contadores del carril bici, con panel fijo (índice de 2022 a 2025: 100 → 115). Es el indicador principal.**
   - Es dato municipal, en la misma ciudad y los mismos años que los siniestros, y el Plan Director lo usa para el mismo fin.
   - Limitaciones:
     - suma bicis y patinetes sin separarlos (en 2019-2021, entre el 25 % y el 31 % eran VMP);
     - solo cubre el carril bici, mientras que buena parte de los siniestros ocurre en la calzada o en cruces;
     - solo laborables, con lo que falta el ocio de fin de semana, el Jardín del Turia y el turismo;
     - es una medida de pasos, no de kilómetros.
   - Mide bien la **suma** de bici y VMP, que es justo la población de la meta del Plan (−50 % de siniestros con ciclistas o VMP).
2. **Valenbisi (4,0 → 5,4 M de viajes, índice de unos 136). Solo como contexto.** Es solo bici mecánica compartida y crece por el bono diario turístico (un millón de usos en 2025). No representa al patinete.
3. **Composición bici/VMP en el carril bici. No hay dato de 2022 a 2025.** Sin él **no se puede separar la exposición del VMP de la de la bici.** Ejemplo aritmético, que es un escenario y no una estimación:
   - supongamos que en 2022 el 30 % del tráfico del carril bici era VMP;
   - para que el riesgo por viaje del patinete no hubiera cambiado con sus siniestros +44 % (825 → 1.190), su tráfico tendría que crecer un 44 %;
   - eso deja la cuota de VMP en el 38 % en 2025 y el tráfico de bici casi plano (+3 %), compatible con sus siniestros también planos (576 → 549).
   - Es un escenario verosímil, y por eso **con los datos actuales no se puede afirmar que el patinete sea más peligroso por viaje.** Coincide con lo anotado en las notas internas de trabajo sobre el «+76 % a igual uso».
4. **Ventas de AMBE (bici eléctrica) y parque de VMP. No sirven como exposición en València:**
   - son nacionales;
   - son flujo o stock, no uso;
   - de patinetes no hay serie;
   - las bicis eléctricas de AMBE son sobre todo de montaña (141.000 de 241.000 en 2023), no urbanas.
   - Sirven como contexto en una frase: «las ventas de bicis eléctricas en España están estables desde 2022 y el parque de patinetes se estima en más de 4 millones».
5. **Barómetro 2024 (21 % de los hogares de València con patinete). Es contexto de nivel, no de tendencia**, porque es un solo año.

**Hueco que una entidad colaboradora podría cubrir:** repetir los **conteos manuales que separan bici y VMP** de 2019-2021, en los mismos puntos y con el mismo método. Se haría con la Càtedra d'Economia Col·laborativa de la UV (ya los hizo, financiada por Las Naves) o con la Agència de la Bicicleta. Una campaña anual en 5-12 puntos daría la cuota de VMP y permitiría separar los dos índices de exposición. Es el dato que falta para responder si el patinete tiene más riesgo por viaje.

## 4. Propuesta de indicadores para la web (2022 = 100)

**Indicador 1. «Siniestros frente a uso del carril bici» (el principal).**

- Dos líneas: siniestros con bici o VMP (100 → 124) y tráfico en el carril bici con panel fijo de 116 contadores (100 → 115).
- Lectura: «los siniestros crecen algo más deprisa que el tráfico medido».
- Nota fija: «Los contadores suman bicis y patinetes y solo cubren el carril bici en laborables. El Plan Director usa el mismo indicador (aforos en carriles bici) para medir los desplazamientos en bici o VMP».
- Actualización anual con la hoja de Movilidad.

**Indicador 2. «Bici y patinete, por separado».**

- Tres líneas: siniestros con VMP (100 → 144), siniestros con bici (100 → 95) y la misma línea de tráfico (115).
- Un recuadro sobre la composición: «en 2019-2021, entre el 25 % y el 31 % de los vehículos del carril bici eran patinetes (conteos manuales de la Agència de la Bicicleta y de la UV); desde entonces no se ha vuelto a medir».
- Mensaje: los siniestros con patinete crecen mucho más que el tráfico total, pero sin saber cuántos patinetes circulan no se puede decir si es por más uso o por más riesgo.
- Propuesta: recuperar el conteo (véase el §3).

**Indicador 3 (contexto, opcional). «Otras señales de uso».**

- Una tira de cifras pequeñas:
  - Valenbisi: unos 4,0 M de viajes en 2022 y unos 5,4 M en 2025;
  - València, la gran ciudad con más hogares con patinete (21 %, Barómetro 2024);
  - ventas de bicis eléctricas en España estables (236.183 en 2022 y 234.880 en 2025, AMBE);
  - parque de VMP en España: más de 4 M (estimación de la DGT, 2026).
- No forman un índice: son de distinta naturaleza y en parte nacionales. Cada cifra, con su fuente y su tipo (uso, stock o ventas).

**Lo que no hay que hacer:** dividir siniestros entre ventas o entre el parque nacional, presentar Valenbisi como el uso de la bici en general, o dar un índice de uso del patinete, que no existe.

## 5. Pendiente de verificar

- **Valenbisi:** pedir a Movilidad o a JCDecaux la serie anual oficial (sobre todo 2022 y 2024). La lectura del gráfico es aproximada.
- **Detección de patinetes por las espiras:** confirmar con Movilidad que las espiras del carril bici detectan patinetes (la nota municipal de 2022 lo da por hecho) y si hay alguna calibración frente a los conteos manuales. El informe de conteos de 2019 (`valencia.es/agenciabici/.../201901231_informe_contajes_vlcoct2019.pdf`) devolvió un error 503.
- **Registro de VMP de la DGT:** comprobar si publica inscripciones por provincia. Por ahora no hay cifras.
