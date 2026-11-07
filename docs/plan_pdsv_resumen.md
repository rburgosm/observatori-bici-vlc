# Plan Director de Seguridad Vial de València 2026-2030: lo que necesitamos

Fuente: `data/raw/pdsv/pdsv_valencia_2026-2030.pdf` (72 páginas) y `data/raw/pdsv/pdsv.txt`.
Formato de las referencias: «PDF p.N (pág. M)». N es la página del fichero y M el número impreso (M = N − 3). «l.» es la línea de `pdsv.txt`.
Las cifras de los gráficos (que son imágenes) se han leído del PDF renderizado.
Tablas derivadas: `data/processed/pdsv_indicadores.csv` y `data/processed/pdsv_lugares.csv`. Las genera `gen_pdsv.py`, una transcripción manual que está en el scratchpad y no en `scripts/`.

## 1. Metas oficiales exactas

**Objetivo global** (apartado 4.4, PDF p.26, pág. 23, l.1073-1075), en literal:
> «REDUCIR EL NÚMERO DE VÍCTIMAS MORTALES RESPECTO A 2019 Y DE PERSONAS HERIDAS GRAVES RESPECTO A 2024 AL 50% PARA 2030».
- Son dos metas, ambas de −50 % en 2030:
  - **fallecidos**: −50 % respecto a **2019**;
  - **personas heridas graves**: −50 % respecto a **2024**.
- Son metas de **víctimas**, no de siniestros, y valen para **todos los colectivos**: no se limitan a ciclistas ni a VMP.
- Por qué el año base es 2024: desde 2024 la gravedad sigue la Orden INT/2223/2014. Lo dice la nota 2 (l.1086), que remite al apartado 2.3.2, y lo explica el capítulo 8 (PDF p.60, pág. 57, l.2852).
- Bases numéricas que da el propio Plan:
  - **Fallecidos 2019**: solo hay un gráfico de *siniestros con fallecidos*, que marca 18 (PDF p.14, pág. 11). El Plan dice que los fallecidos bajan un 28 % entre 2019 y 2025 (l.845); eso cuadra con 18 → 13 siniestros. **Meta ≈ 9.**
  - **Heridos graves 2024**: el Plan da tres cifras distintas.
    - 176 «personas heridas hospitalizadas» (tabla del cap. 8, PDF p.60, l.2825);
    - 167 «siniestros con heridos graves» (gráfico de PDF p.15, pág. 12);
    - un «nuevo nivel base de 185 casos», citado del Plan Vector (l.604).
  - **Meta ≈ 88 personas** (con 176) o ≈ 84 siniestros (con 167).
- **Indicador de impacto de la acción 3.2.2** (PDF p.65, pág. 62, l.3080):
  - «Reducción de siniestros con ciclistas/VMP»: −50 %, unidad %, fórmula «Comparación anual»;
  - **línea base: «—»**, fuente Policía Local, periodicidad anual.

**¿Era correcta nuestra suposición?** Lo era a medias.
- «−50 % de siniestros con ciclistas/VMP en 2030» **existe tal cual**, pero como indicador de impacto de la acción 3.2.2. **No es la meta global.**
- Ese indicador **no fija año base** y la fórmula es ambigua («comparación anual»).
- Propuesta: usar **2024** como base, coherente con el objetivo global, y mostrar también 2025.
- Con nuestras cifras (BICICLETA o VMP, sin duplicar): 2024 = 1.501, así que la **meta para 2030 es 751**. En 2025 hubo 1.659 (+10,5 %): se va en sentido contrario.
- La meta global (heridos graves −50 % sobre 2024) debería ir en la web como **segunda referencia**, calculada para bici y VMP. Ojo: el portal da la gravedad por siniestro, no por persona.

Otros −50 % del Plan:
- atropellos (3.2.1, l.3064);
- siniestros en zonas 30/coexistencia/residenciales (3.5, l.3160);
- vehículos sin ITV o seguro (4.1.2, l.3213).

## 2. Tablas de indicadores (cap. 8, PDF p.61-71, pág. 58-68)

- Se han transcrito **119 indicadores** de las acciones 1.1 a 7.4, más 2 filas del objetivo global, en `data/processed/pdsv_indicadores.csv`.
- Columnas: eje, accion, tipo, indicador, unidad, formula, linea_base, meta_2030, fuente, periodicidad, calculable, como_o_por_que, ref.
- Qué podemos calcular con el dataset abierto de siniestros, los contadores y el callejero:
  - **Sí: 5.**
    - Reducción de siniestros con ciclistas/VMP (3.2.2).
    - Reducción de atropellos (3.2.1): con PEATÓN en unidades; el tipo «atropello» solo es fiable en 2025.
    - Incremento de desplazamientos en bici/VMP con los aforos de carril bici (1.3.1). Base +3,4 %, meta +5 %; los aforos no separan bici de VMP.
    - Variación del vehículo privado con los aforos (1.3.1). Base +1,3 %, meta −5 %.
    - Siniestros con vehículos de mercancías (4.1.1): CAMIÓN o FURGONETA, como aproximación.
  - **Parcial: 13.** Requieren una capa que no tenemos o una definición que el Plan no da. Por ejemplo:
    - entorno escolar −60 % (no define el radio);
    - zonas 30 −50 % (falta la capa de zonas 30);
    - estado de la vía −40 % y obras −40 % (por factores concurrentes);
    - colectivos vulnerables −40 %;
    - km de carril bici (base 225 → meta 250) con la capa 189;
    - % de calles 30 (64 → 95 %);
    - también los dos objetivos globales: el portal empieza en 2022 y cuenta siniestros, no personas.
  - **No: 101.** Son datos de gestión interna (campañas, reuniones, controles, cámaras, plazas…), encuestas, o datos que el dataset no tiene (edad, infracciones, tiempos de atención).
- Rasgos generales de las tablas:
  - Casi todos los indicadores de impacto tienen **línea base «—»** y fórmula «Comparación anual», **sin año de referencia**.
  - Hay erratas:
    - la fórmula de «Calles 20» repite «≤30»;
    - la unidad de «Áreas recuperadas» es km²;
    - en «Rutas escolares» la meta (100) es menor que la base (117).
  - Los indicadores de 2.1, 4.1 y 5.1 remiten al **Plan Vector de la Policía Local**, que no tenemos.

## 3. Cifras base de ciclistas y VMP que da el Plan, frente a las nuestras

Siniestros con el colectivo implicado. Gráficos de PDF p.18-19 (pág. 15-16); totales en el texto, l.1829 y l.754.

| Año | VMP según el Plan | VMP nuestro (solo VMP + ambos) | Bici según el Plan | Bici nuestra (solo bici + ambos) |
|---|---|---|---|---|
| 2019 | 346 | — | 498 | — |
| 2020 | 407 | — | 417 | — |
| 2021 | 640 | — | 525 | — |
| 2022 | 825 | 825 | 576 | 576 |
| 2023 | 1.003 | 1.002 | 538 | 538 |
| 2024 | 1.054 | 1.054 | 511 | 510 |
| 2025 | 1.192 | 1.190 | 549 | 549 |
| Total 2019-25 | 5.467 | | 3.614 | |

- **Cuadran casi exactamente**, con una diferencia de 0 a 2 por año.
- Las diferencias se explican porque el Plan sale del SIASV con una fecha de extracción distinta a la de nuestra descarga del portal.
- El total general también cuadra:
  - 2022-2024 es idéntico (7.467, 8.547 y 8.961);
  - 2025: el Plan da 9.264 y el portal 9.252.
- La gravedad por siniestro de 2023 y 2024 coincide al 100 % con los gráficos de PDF p.15 (por ejemplo, 2024: 167 graves, 371 de baja gravedad y 10 con fallecidos).
- El Plan **cuenta VMP y bici por separado y nunca da la unión**.
  - Si se suman, en 2024 salen 1.565 en lugar de 1.501: los 63 siniestros con bici y VMP a la vez cuentan dos veces.
  - Para el indicador de 3.2.2, usar la unión sin duplicados.
- Otros datos del Plan que no podemos reproducir, porque el portal no da personas:
  - personas lesionadas VMP: 644 (2023), 728 (2024) y 833 (2025), +14 % en 2025 (PDF p.16, l.650);
  - personas lesionadas en bicicleta: 333, 352 y 373;
  - porcentaje de lesionados de gravedad que son usuarios de VMP: 13 %, 16 %, 19 % y 23 % (2022-2025, PDF p.19);
  - fallecidos desde 2023: 4 usuarios de VMP (3 en 2025) y 2 ciclistas (l.576-580).
- La tabla global de 2022-2024 del capítulo 8 (PDF p.60, l.2817-2833) no separa bici ni VMP.

## 4. Acciones relevantes para bici y VMP

- **Calendario**: no hay plazo por acción.
  - Solo hay tres plazos globales sin asignar: corto 2026, medio 2027-2028 y largo 2029-2030 (5.2, PDF p.27, l.1131).
- **Presupuesto**: el Plan no da ninguna cifra. No hay «€» ni «presupuesto» en todo el documento.
- **Responsables**: según el cuadro resumen del cap. 7 (PDF p.56-59).

Acciones:
- **3.2.2 Mejorar la seguridad vial en los itinerarios ciclistas existentes** (PDF p.42, l.1845-1870).
  - Medidas «en zonas de elevada siniestralidad con ciclistas y/o usuarios de VMP», con nueve líneas (a-i):
    - visibilidad en intersecciones carril bici–calzada;
    - señalización y fases semafóricas;
    - eliminar el ámbar intermitente;
    - bici en zonas peatonales;
    - pasos de peatones y contenedores;
    - paradas de bus;
    - cruces con itinerarios peatonales;
    - ciclistas en calzada sin carril;
    - continuidad de la red.
  - También: aplicar el Plan Director de la Bicicleta (2023) y seguir creando carriles bici segregados.
  - Responsable: Servicio de Movilidad.
  - Indicadores:
    - km de carril bici: 225 → 250;
    - ciclocalles: 18 → 75 km;
    - alfombras rojas: 786 → 1.000;
    - pasos a contenedores: 3 → 100;
    - Plan de la Bici: 100 %;
    - **siniestros con ciclistas/VMP: −50 %**.
- **1.3.1 Fomento de la movilidad peatonal y ciclista** (Movilidad y Policía Local).
  - Indicadores:
    - aparcabicis: 22.638 → 25.000;
    - **paneles contadores ciclistas: 3 → 9**;
    - **desplazamientos en bici/VMP: +3,4 % → +5 %**, medido con aforos en los principales carriles bici (l.2972-2978).
- **1.2.1 y 1.2.2 Campañas** (Movilidad y Policía Local). Entre los temas, la convivencia entre modos. Antecedente: la campaña «¡Tú eres el chasis!» (2024), dirigida a bicis y patinetes (PDF p.23).
- **2.1 Controles policiales** (Policía Local).
  - Cita expresamente la «ocupación del vehículo (especialmente en VMP)» y el uso de casco (l.1457).
  - Sin metas numéricas: remite al Plan Vector.
  - Antecedente: el grupo policial de vigilancia de los viales ciclistas (l.995).
- **2.2 Tecnología** (Movilidad y Policía Local): radares (7 → 20), foto-rojo en los cruces con más siniestros y CCTV (819 → 900).
- **3.5.1 Zonas 30 y calles 20** (Movilidad).
  - Evaluar la efectividad de las zonas 30 y de preferencia residencial (l.2162).
  - Indicadores: calles 30, 64 → 95 %; calles 20 y residenciales, 3 → 10 %; siniestros en esas zonas, −50 %.
- **3.6 Obras**: una señalización que tenga en cuenta la micromovilidad (Movilidad y Policía Local).
- **3.7 Auditorías de seguridad vial** (Movilidad).
  - Auditorías de tramos en servicio: **4 → 30**.
  - Las 4 primeras (2024) se hicieron en las «intersecciones de mayor siniestralidad» (l.909, 2258-2300).
- **6.1.1 Desarrollo informático de datos de siniestros** (Policía Local; PDF p.53, l.2430-2439). Prevé:
  - a) cruzar con la red vial clasificada y las intensidades;
  - b) aplicaciones de indicadores siniestros/IMD;
  - c) aplicaciones para ver en un mapa las consultas a la base de datos.
  - Indicadores: 5 módulos informáticos y **6 informes al año de indicadores «publicados»** (Movilidad).
  - No dice que sea solo para uso interno, pero **tampoco habla de publicar datos ni de un visor público**.
- **6.2 Convenios de investigación** con universidades, centros tecnológicos, hospitales y empresas (Servicio de Movilidad; l.2400). Meta: **10 convenios**, 15 estudios, 6 pilotos y 80 % de medidas aplicadas.
- **7.1.1 Cuadro de mando de seguimiento del PDSVV** (Movilidad; l.2472). Línea base «No existente», meta «Sistema operativo», puntual.
- **7.1.2 Memoria anual de siniestralidad** para la Comisión de Seguridad Vial de la Mesa de la Movilidad (Movilidad y Policía Local; l.2477; meta 1 al año).
- **7.3.1** Seguimiento ante la Comisión de Seguridad Vial (2 al año).
- **7.3.4** Implicar a las empresas de venta y alquiler de bicis y VMP en la divulgación (Movilidad y Policía Local; l.2532). Meta: 5 → 30 empresas.

**Lugares concretos** (detalle en `data/processed/pdsv_lugares.csv`, 37 filas).
- Calles y cruces con más siniestros, 2019-2025 (apartado 2.3.4, PDF p.22, l.862-875):
  - **VMP, calles**: Blasco Ibáñez (196), Av. del Puerto (167) y Paseo de la Alameda (166).
  - **VMP, cruces**: Alameda–Pl. Zaragoza (32), Ausiàs March–Fernando Abril Martorell (25) y Naranjos–Luis Peixó (22).
  - **Bici, calles**: Jardín del Turia (185; 39 en 2024 → 27 en 2025), Blasco Ibáñez (154) y Av. del Puerto (110).
  - **Bici, cruces**: Alameda–Pl. Zaragoza (22), Naranjos–Luis Peixó (15) y Fernando Abril Martorell–Ctra. Malilla (14).
  - **Peatón**: San Vicente Mártir, Blasco Ibáñez y Colón; cruces Peset Aleixandre–Camí de Montcada, Giorgeta–Jesús y Tres Cruces–Campos Crespo.
- **Auditorías de 2024** (acción 3.7):
  - Blasco Ibáñez–Cardenal Benlloch;
  - Cardenal Benlloch–Av. del Puerto;
  - Pl. de Zaragoza;
  - Gran Vía Fernando el Católico–Àngel Guimerà.
- **Intersecciones críticas reordenadas en 2025**: Pl. Zaragoza, Gran Vía Ferran el Catòlic–Àngel Guimerà y Blasco Ibáñez–Cardenal Benlloch–Clariano.
- **Configuración ciclista pendiente de estudio**: C/ Xàtiva–C/ Jesús, con giro de vehículos y ámbar sobre el carril bici (l.1775).
- **Radares didácticos de 2025**: Paseo de la Ciutadella, Av. General Avilés y C/ Enginyer Fausto Elío. Iluminación LED en pasos de la Ronda Norte.
- **Zonas**:
  - Anillo Ciclista, con más de 10.000 ciclistas al día en algunos tramos;
  - Jardín del Turia, donde se concentra el uso de VMP;
  - APR de Ciutat Vella (2022).
- **No hay** una lista de ejes ciclistas a reformar ni de zonas 30 nuevas con nombre.
- Los rankings son **acumulados de 2019-2025 y en cifras absolutas**. Nuestros datos del portal empiezan en 2022: para compararlos, hay que acumular 2022-2025 o mostrar el ranking del Plan como capa aparte.

## 5. Puntos y tramos de concentración: cómo los define el Plan

- **No hay ningún criterio formal.** El Plan no define tramos de concentración de accidentes (TCA), ni umbrales, ni índice de peligrosidad, ni ventanas temporales.
- Lo único que hace es ordenar calles y cruces por **número absoluto de siniestros** (2.3.4).
- **El propio Plan reconoce esa carencia** (4.2, PDF p.26, pág. 23, l.1055-1066):
  > «Actualmente lo que se detectan son las calles o cruces con mayor número de siniestros, pero sin tener en cuenta el tipo de vía […] ni la cantidad de vehículos que circulan por los mismos».
- Como mejora propone:
  - agrupar la red por tipo de vía y por escalón de IMD;
  - calcular el índice de peligrosidad;
  - «identificar tramos conflictivos por elevada siniestralidad en cada categoría para evitar que siempre aparezcan los mismos puntos críticos».
  - Esto lo concreta la acción 6.1.1 a-b.
- Otras expresiones que el Plan usa **sin definirlas**:
  - «zonas de elevada siniestralidad con ciclistas y/o VMP» (3.2.2);
  - «puntos de siniestralidad / zonas de alto riesgo» (2.1);
  - «tramos críticos en servicio» (3.7);
  - «puntos con mayor índice de siniestralidad», que se tratan en reuniones de Policía Local y Movilidad (l.567, l.1002).
- Para nosotros:
  - nuestro cribado con Bayes empírico y exposición (contadores e IMD) es exactamente lo que el Plan dice que falta;
  - hay que presentarlo como aportación a 6.1.1 b) y como propuesta de lista para las 26 auditorías pendientes de 3.7.

## 6. Qué prevé publicar el Ayuntamiento, y nuestro valor añadido

Lo que prevé el Plan:
- **1.2.4 Web** (Movilidad). Prevé:
  - mejorar la sección de seguridad vial de valencia.es;
  - crear un apartado «con datos de siniestralidad, memoria de actuaciones, etc.» (l.1338-1342).
  - Indicadores:
    - portal operativo (puntual, sin fecha);
    - 20 actualizaciones al año;
    - 40.000 visitas.
- **6.1.1**:
  - 6 informes técnicos de indicadores «publicados» al año;
  - aplicaciones de mapa sobre la base de datos (Policía Local), sin decir si serán públicas.
- **7.1.1**: cuadro de mando de seguimiento, sin decir si será público.
- **7.1.2**: memoria anual de siniestralidad (base 1, meta 1 al año), presentada a la Comisión de Seguridad Vial.
- **7.3.1**: dos informes de seguimiento al año a esa Comisión.
- **Fechas**: ninguna. Solo cuenta la vigencia general 2026-2030.

Lo que el Plan no prevé:
- **Datos abiertos**: el Plan nunca menciona el portal de datos abiertos ni publicar siniestros **geolocalizados**. El SIASV es una base «georreferenciada» (l.2404), pero de uso policial.
- **VMP separado de bici por cruce**: el Plan solo los separa en el ranking de 2.3.4 (las 3 primeras calles y los 3 primeros cruces).
- **Siniestros por uso**: no se calculan. Es una tarea pendiente de 6.1.1 b).
- **Seguimiento público de la meta de 3.2.2**: no está previsto, y la meta no tiene año base.

Valor añadido nuestro:
- dataset abierto geolocalizado;
- mapa por cruce con bici y VMP separados;
- tasas por exposición;
- seguimiento público y con base explícita (2024) de la meta del −50 % y del objetivo global de heridos graves;
- encaja como socio en 6.2 (convenios: meta 10) y cubriría en abierto 7.1.1 y 1.2.4.
