# Incidencias detectadas en datos abiertos del Ajuntament de València

*Observatorio de la bici y el patinete de València · hola@observatoribicivlc.org · última comprobación: 2026-11-07*

Usamos los datos abiertos del Ajuntament de València para seguir los siniestros con bici y patinete en la ciudad. Sin el portal de datos abiertos, el callejero del geoportal y las intensidades del Servicio de Movilidad, el observatorio no sería posible: gracias por publicarlos.

Al trabajar con ellos hemos encontrado algunas incidencias. Las recogemos aquí para devolverlas, por si son útiles para mejorar los datos. Es lo que vemos al reutilizarlos, con propuestas que harían más fácil el trabajo de otras personas que también los usan. Cada incidencia lleva un ejemplo, su alcance, cómo la tratamos nosotros, una sugerencia y la forma de reproducirla con los datos publicados. Puede que alguna tenga una explicación que desconocemos; si es así, nos encantará saberlo y corregir este registro.

Son **39 incidencias**: 8 de falta de dato, 7 de documentación, 5 de duplicado, 5 de formato, 4 de valor erróneo, 3 de publicación, 3 de inconsistencia entre años, 2 de geometría, 1 de valor impreciso, 1 de errata. 36 se vuelven a comprobar automáticamente con cada descarga de los datos, así que sabremos cuándo dejan de aparecer.

## Las más útiles de corregir

1. **No hay coordenadas: el lugar viene escrito como una dirección** (INC-011). Sugerencia: Publicar las coordenadas de cada siniestro (o al menos del cruce o tramo) o, como mínimo, el código de vía (codvia) y el número. Según el Plan Director, el SIASV ya es una base de datos georreferenciada, así que podría ser el origen de esas coordenadas.
1. **Un solo fichero 2022-2025, sin frecuencia de actualización ni años anteriores** (INC-014). Sugerencia: Indicar la frecuencia en la ficha, publicar cada año (mejor ampliando el mismo conjunto, con un nombre sin años) y, si existen, los años anteriores.
1. **El criterio de herido grave cambió a partir de 2023 y la ficha no lo indica** (INC-007). Sugerencia: Añadir una nota en la ficha con la fecha del cambio de criterio y, si es posible, un campo con el criterio aplicado a cada fila.
1. **La forma de anotar los siniestros cambia en octubre de 2022, julio de 2024 y octubre de 2024, sin nota en la ficha** (INC-010). Sugerencia: Documentar en la ficha las fechas de cambio de sistema y de criterio de anotación.
1. **Algunos «cruces» son de dos calles que no se tocan** (INC-009). Sugerencia: Revisar estos casos; si el registro quiere decir «a la altura de», indicarlo así, o publicar las coordenadas.

## Resumen

| Id | Conjunto | Tipo | Qué pasa | Alcance | Estado |
|---|---|---|---|---|---|
| INC-001 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | duplicado | Filas repetidas, iguales en todo salvo el identificador. | 18 filas sobrantes (36 implicadas; 2 con bici o VMP) | comunicada |
| INC-002 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | duplicado | Filas con la misma fecha, hora y lugar, y algún dato distinto. | 29 grupos, 58 filas (5 grupos con bici o VMP) | comunicada |
| INC-003 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | valor erróneo | En algunas filas la lista de vehículos está vacía («[»). | 25 filas | comunicada |
| INC-004 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | publicación | Un conjunto titulado 2022-2025 incluye siniestros del 1 de enero de 2026. | 17 filas | comunicada |
| INC-005 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | inconsistencia entre años | El tipo de accidente falta en buena parte de las filas anteriores a julio de 2024, y los factores, también en 2025. | 13.787 filas sin tipo; 15.652 sin factores (14.469 vacías y 1.183 con «NULL») | comunicada |
| INC-006 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | formato | El dato que falta se escribe unas veces «NULL» y otras vacío, según el campo y el año. | 13.787 filas sin tipo y 15.652 sin factores | comunicada |
| INC-007 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | inconsistencia entre años | El criterio de herido grave cambió a partir de 2023 y la ficha no lo indica. | Las comparaciones de gravedad que incluyen 2022, 2023 o 2024 (24.975 filas) | comunicada |
| INC-008 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | falta de dato | Muchas direcciones de 2022 son solo el nombre de la calle. | 2.422 filas (7,1 %); 120 son del Jardín del Turia, donde no hay números de portal | comunicada |
| INC-009 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | valor impreciso | Algunos «cruces» son de dos calles que no se tocan. | 800 filas a más de 100 m si se admite que el tipo de vía (C/, PL…) pueda estar cambiado, y 966 si no; de ellas, 571 y 715 a más de 300 m (con nuestro método) | comunicada |
| INC-010 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | inconsistencia entre años | La forma de anotar los siniestros cambia en octubre de 2022, julio de 2024 y octubre de 2024, sin nota en la ficha. | Todo el conjunto (tres etapas) | comunicada |
| INC-011 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | falta de dato | No hay coordenadas: el lugar viene escrito como una dirección. | 34.244 filas (todas) | comunicada |
| INC-012 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | formato | Algunos nombres de calle no coinciden con el callejero o usan entradas sin eje o dadas de baja. | 514 filas en los ejemplos (453 + 54 + 7) | comunicada |
| INC-013 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | falta de dato | Hay siniestros en lugares que no están en el callejero (Jardín del Turia, autovías). | 168 filas con el Jardín del Turia y 164 con autovías o carreteras (sin contar la V-30, que sí está en el callejero); con nuestro método, 94 cruces no se pueden situar por una de estas vías (42 con el Jardín del Turia) | comunicada |
| INC-014 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | publicación | Un solo fichero 2022-2025, sin frecuencia de actualización ni años anteriores. | El conjunto entero | comunicada |
| INC-015 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | documentación | La ficha no explica los campos ni la fecha de extracción. | El conjunto entero | comunicada |
| INC-016 | Catálogo del portal de datos abiertos (DCAT) | documentación | El enlace de la licencia del catálogo lleva a una página no encontrada (404). | — | comunicada |
| INC-017 | Servicio OPENDATA del geoportal municipal | documentación | Los servicios del geoportal no declaran la licencia. | — | comunicada |
| INC-018 | Portales de las calles (geoportal, capa 217) | geometría | Algunos portales tienen varios puntos distintos para la misma dirección. | 51 combinaciones con todo igual en posiciones distintas (11 a más de 50 m y 2 a más de 200 m); 19 portales con numportal distinto de su rótulo | comunicada |
| INC-019 | Vehículos de movilidad personal tipo A y tipo B (geoportal, capas 2 y 3) | documentación | Las capas de la red de patinetes tipo A y tipo B son idénticas. | 9.256 tramos | comunicada |
| INC-020 | Intensidad de tráfico por tramos (geoportal, capa 188) | documentación | La capa de intensidad de tráfico es en tiempo real, sin histórico. | 36 de 394 tramos con −1 (30/10/2026 y 04/11/2026) | comunicada |
| INC-022 | Intensidades de tráfico (web del Servicio de Movilidad) | publicación | Las intensidades de tráfico solo están en la web de Movilidad, no en el portal. | — | comunicada |
| INC-023 | IMD del carril bici, ODS anuales (web de Movilidad) | formato | El formato de las hojas de intensidades cambia de un mes a otro. | 4 ficheros, 48 hojas | comunicada |
| INC-024 | IMD del carril bici, ODS anuales (web de Movilidad) | errata | Una errata en el sentido de un contador del Pont de Fusta. | 1 contador (P1163), 44 de 48 hojas mensuales | comunicada |
| INC-025 | IMD del carril bici, ODS anuales (web de Movilidad) | falta de dato | Algunos contadores del carril bici no tienen posición publicada. | 12 de los 160 contadores de 2025; 29 de 178 en 2022-2025 (17 de ellos ya no aparecen en 2025) | comunicada |
| INC-026 | IMD de vehículos 2025, ODS (web de Movilidad) y capa 188 | falta de dato | Muchos tramos de la intensidad de vehículos no tienen posición publicada. | 122 de 412 códigos A y 14 de 102 códigos B (además, 15 F y 2 E, ninguno en la capa), 2025 | comunicada |
| INC-027 | Accidentes de tráfico 2022-2025 (portal de datos abiertos) | falta de dato | Ubicaciones con el texto «nan» en lugar de una calle o un número. | 28 filas con «nan» (16 «… cruce nan», 7 «nan» con número y 5 solo «nan»; 9 con bici o VMP); 16 cruces de una calle consigo misma (12 del Jardín del Turia; 12 con bici o VMP) | comunicada |
| INC-028 | Vías del callejero (geoportal, capa 273) | valor erróneo | Algunos nombres de calle en castellano están cortados. | 6 nombres cortados (32 filas de siniestros los usan); 9 nombres con un espacio o un salto de línea al final | comunicada |
| INC-029 | Ejes de calle (geoportal, capa 223) | falta de dato | Tramos de calle sin código de vía y un tramo repetido. | 19 tramos sin codvia (3,8 km); 1 tramo repetido; 1 tramo con la vía de baja | comunicada |
| INC-030 | Ejes de calle (geoportal, capa 223) | formato | Los ejes escriben algunos nombres y tipos de vía de otra forma que la capa de vías. | 210 tramos de 65 vías con «´»; 23 tramos con un tipo de vía distinto del de la capa de vías | comunicada |
| INC-031 | Portales de las calles (geoportal, capa 217) | geometría | Algunos portales están lejos de su calle. | 15 portales a más de 200 m del eje de su calle (2 a más de 1 km); 6 siniestros, ninguno con bici o VMP, situados en ellos | comunicada |
| INC-032 | Itinerarios ciclistas (geoportal, capa 189) | documentación | La ficha de los carriles bici no explica los códigos de tipo de tramo. | 1.705 tramos (los 199 con código 8 suman 33,2 km) | comunicada |
| INC-033 | Reguladores de grupos semafóricos (geoportal, capa 182) | falta de dato | Dos campos de los reguladores de semáforos están vacíos. | 1.072 de 1.072 reguladores | comunicada |
| INC-034 | Intensidad de tráfico por tramos (geoportal, capa 188) | duplicado | Algunos códigos de tramo de tráfico están repetidos en sitios distintos. | 3 códigos en 6 tramos; 2 registros sin geometría | comunicada |
| INC-035 | Vehículos de movilidad personal tipo A y tipo B (geoportal, capas 2 y 3) | duplicado | La red de los patinetes tiene tramos repetidos. | 23 tramos sobrantes en cada capa (19 en el mismo sentido), 3,8 km de 954 | comunicada |
| INC-036 | IMD del carril bici, ODS anuales (web de Movilidad) | formato | Un contador escrito en minúscula y cifras guardadas como texto. | 45 hojas con «p2821»; 491 valores de IMD como texto (4 hojas); 1.007 valores con decimales (8 hojas) | comunicada |
| INC-037 | IMD del carril bici, ODS anuales (web de Movilidad) | duplicado | Contadores repetidos en las hojas del carril bici. | P9200201 repetido en 8 hojas; 17 códigos F (134 filas), 7 iguales a un P en 8 meses | comunicada |
| INC-038 | IMD del carril bici, ODS anuales (web de Movilidad) | valor erróneo | Un tramo de coches entre los contadores de bici y meses a 0. | 4 filas de A409; 5 IMD a 0; 1 IMD vacía | comunicada |
| INC-039 | IMD de vehículos 2025, ODS (web de Movilidad) | valor erróneo | Tramos de tráfico con intensidad 0 en un mes. | 4 IMD a 0; 976 valores con decimales (enero y mayo); 2 celdas con solo espacios | comunicada |
| INC-040 | Evolución mensual de la IMD 2019-2026, XLSX (web de Movilidad) | documentación | Las intensidades estimadas o poco fiables solo se marcan con colores. | 331 celdas marcadas solo con color (279 estimadas y 52 de fiabilidad < 85 %) en 3 hojas; 3 de 1.404 valores del carril bici distintos de los ODS | comunicada |

## Detalle

### Accidentes de tráfico 2022-2025 (portal de datos abiertos)

#### INC-001 · Filas repetidas, iguales en todo salvo el identificador

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** todos salvo _id · **Tipo:** duplicado · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Hay pares de filas idénticas en todos los campos salvo el identificador _id. En todos los casos los dos _id son consecutivos, y todos son de septiembre de 2022 a junio de 2024 (ninguno desde julio de 2024).
- **Ejemplo:** _id 5005 y 5006 (2022-09-09 14:12); 7585 y 7586; 20523 y 20524
- **Alcance:** 18 filas sobrantes (36 implicadas; 2 con bici o VMP). Última comprobación automática: 18 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Si no se quitan, 18 siniestros cuentan dos veces.
- **Cómo lo tratamos en el observatorio:** Se cuentan una sola vez (se quitan las filas iguales en todo salvo _id).
- **Sugerencia:** Confirmar si son duplicados de carga y retirarlos; a medio plazo, un identificador estable por siniestro (por ejemplo, el número de atestado anonimizado).
- **Cómo reproducirlo:** `df.drop(columns="_id").duplicated().sum()` → 18

#### INC-002 · Filas con la misma fecha, hora y lugar, y algún dato distinto

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** FECHA, UBICACION y el resto · **Tipo:** duplicado · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Grupos de filas con la misma fecha y hora y la misma ubicación, y con algún otro campo distinto (gravedad, vehículos o factores). Pueden ser un mismo siniestro registrado dos veces o dos siniestros distintos.
- **Ejemplo:** _id 2956 y 2957 (VMP: uno con heridos leves y otro sin heridos); 17607 («[» en vehículos) y 17608
- **Alcance:** 29 grupos, 58 filas (5 grupos con bici o VMP). Última comprobación automática: 29 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** No se puede saber si son uno o dos siniestros. Con bici o VMP son 5 grupos en todo el periodo (4 de ellos en 2024 y 1 en 2022).
- **Cómo lo tratamos en el observatorio:** Se mantienen todas las filas y se declara como margen de error de la serie.
- **Sugerencia:** Revisarlos en origen y, si son el mismo siniestro, dejar una sola fila.
- **Cómo reproducirlo:** Agrupar por FECHA y UBICACION las filas que no son duplicados exactos y contar los grupos con más de una fila → 29

#### INC-003 · En algunas filas la lista de vehículos está vacía («[»)

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UNIDADES_IMPLICADAS · **Tipo:** valor erróneo · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El campo de vehículos implicados vale solo «[» (lista vacía o cortada).
- **Ejemplo:** _id 17607; reparto por año: 2 (2022), 5 (2023), 14 (2024), 4 (2025)
- **Alcance:** 25 filas. Última comprobación automática: 25 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** No se sabe qué vehículos intervinieron; algunas son caídas que podrían ser de bici o patinete.
- **Cómo lo tratamos en el observatorio:** Quedan fuera de los recuentos por vehículo, y se dice en la página de método.
- **Sugerencia:** Rellenar el campo desde el registro de origen.
- **Cómo reproducirlo:** `(df.UNIDADES_IMPLICADAS.str.strip() == "[").sum()` → 25

#### INC-004 · Un conjunto titulado 2022-2025 incluye siniestros del 1 de enero de 2026

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** FECHA · **Tipo:** publicación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El conjunto se titula 2022-2025 e incluye siniestros del 1 de enero de 2026.
- **Ejemplo:** 17 filas del 2026-01-01 (2 con VMP: _id 34234 y 34244)
- **Alcance:** 17 filas. Última comprobación automática: 17 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Quien sume «todo el fichero» como 2022-2025 incluye un día de 2026; y si 2026 se publica en otro fichero, esas filas pueden aparecer dos veces.
- **Cómo lo tratamos en el observatorio:** Solo se usan años completos; al cargar 2026 se comprobará el solape por fecha.
- **Sugerencia:** Cortar el fichero en el 31/12/2025, o decirlo en la ficha; y que esas filas entren una sola vez en la publicación de 2026.
- **Cómo reproducirlo:** `(df.FECHA.str[:4] == "2026").sum()` → 17

#### INC-005 · El tipo de accidente falta en buena parte de las filas anteriores a julio de 2024, y los factores, también en 2025

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** TIPO ACCIDENTE, FACTORES CONCURRENTES · **Tipo:** inconsistencia entre años · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El tipo de accidente falta en el 64,8 % de las filas de 2022, el 69,4 % de 2023 y el 33,7 % de 2024; está completo desde julio de 2024. Los factores concurrentes faltan en el 64,7 % (2022), el 69,3 % (2023), el 41,4 % (2024) y el 12,8 % (2025).
- **Ejemplo:** Tipo que falta: 4.840 filas (2022), 5.929 (2023), 3.018 (2024, ninguna desde julio), 0 (2025). Factores que faltan: 4.834, 5.927, 3.708 y 1.182
- **Alcance:** 13.787 filas sin tipo; 15.652 sin factores (14.469 vacías y 1.183 con «NULL»). Última comprobación automática: 13.787 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** El tipo solo se puede comparar desde julio de 2024; los factores, con cautela incluso en 2025.
- **Cómo lo tratamos en el observatorio:** El tipo de siniestro se muestra solo del último año completo; se dice en las limitaciones.
- **Sugerencia:** Completarlos si están en el registro de origen; si no, indicar en la ficha desde cuándo están completos.
- **Cómo reproducirlo:** Porcentaje por año de FECHA de `TIPO ACCIDENTE == "NULL"` → 64,8 / 69,4 / 33,7 / 0 %; de FACTORES CONCURRENTES vacío o «NULL» → 64,7 / 69,3 / 41,4 / 12,8 %

#### INC-006 · El dato que falta se escribe unas veces «NULL» y otras vacío, según el campo y el año

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** TIPO ACCIDENTE, FACTORES CONCURRENTES · **Tipo:** formato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El dato que falta se escribe de dos formas, y cambia con los años: en TIPO ACCIDENTE siempre es el texto «NULL»; en FACTORES CONCURRENTES es un campo vacío hasta 2024 y el texto «NULL» desde 2025.
- **Ejemplo:** TIPO ACCIDENTE = «NULL» en 13.787 filas; FACTORES CONCURRENTES vacío en 14.469 (2022-2024) y «NULL» en 1.183 (1.182 de 2025 y 1 de 2026)
- **Alcance:** 13.787 filas sin tipo y 15.652 sin factores. Última comprobación automática: 15.652 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Muchas herramientas leen «NULL» como una categoría más («tipo NULL») en lugar de como dato que falta, y quien cuente solo los campos vacíos no ve los «NULL» de 2025.
- **Cómo lo tratamos en el observatorio:** «NULL» y el campo vacío se tratan como dato desconocido.
- **Sugerencia:** Usar siempre la misma forma para el dato que falta (mejor, un campo vacío), en todos los campos y años.
- **Cómo reproducirlo:** `(df["TIPO ACCIDENTE"] == "NULL").sum()` → 13.787; `df["FACTORES CONCURRENTES"].isna().sum()` → 14.469 y `(df["FACTORES CONCURRENTES"] == "NULL").sum()` → 1.183 (con la API; en el CSV, el vacío es una cadena vacía)

#### INC-007 · El criterio de herido grave cambió a partir de 2023 y la ficha no lo indica

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** TIPO GRAVEDAD · **Tipo:** inconsistencia entre años · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El criterio de herido grave cambió a partir de 2023, de forma progresiva (Orden INT/2223/2014: cuenta como grave todo ingreso hospitalario de más de 24 horas). El Plan Director de Seguridad Vial 2026-2030 explica que el cambio está detrás del aumento de 2023 y 2024. La ficha del conjunto no lo indica.
- **Ejemplo:** Siniestros CON HERIDOS GRAVES: 19 (2022), 76 (2023), 167 (2024), 181 (2025)
- **Alcance:** Las comparaciones de gravedad que incluyen 2022, 2023 o 2024 (24.975 filas). Última comprobación automática: 24.975 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Una lectura directa sugiere que los siniestros graves se han multiplicado por nueve, cuando, según el Plan, el aumento se debe sobre todo al cambio de registro.
- **Cómo lo tratamos en el observatorio:** No se publican tendencias de gravedad; solo comparaciones dentro de cada año. Los heridos graves se comparan desde 2024.
- **Sugerencia:** Añadir una nota en la ficha con la fecha del cambio de criterio y, si es posible, un campo con el criterio aplicado a cada fila.
- **Cómo reproducirlo:** Tabla de `TIPO GRAVEDAD` por año → CON HERIDOS GRAVES: 19, 76, 167, 181. El Plan Director lo explica en el capítulo 8 («con anterioridad al año 2023 no se utilizaba el criterio establecido por la Orden INT/2223/2014»; «este cambio explica el incremento observado en los años 2023 y 2024»)

#### INC-008 · Muchas direcciones de 2022 son solo el nombre de la calle

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UBICACION · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Muchas ubicaciones son solo el nombre de la calle, sin número ni cruce, sobre todo de enero a septiembre de 2022 (el 27 % de las filas). El mes con más es marzo de 2022: el 36 % de las filas solo trae la calle y, con nuestro método, hemos podido situar el 57 % de las filas de ese mes.
- **Ejemplo:** «C/ MARINA», «AV TIRSO DE MOLINA»; marzo de 2022: 192 de 527 filas
- **Alcance:** 2.422 filas (7,1 %); 120 son del Jardín del Turia, donde no hay números de portal. Última comprobación automática: 2.422 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Sin número ni cruce no se pueden situar en un punto; y como pasa más en los primeros años, las tendencias calculadas solo con siniestros situados crecen de forma artificial.
- **Cómo lo tratamos en el observatorio:** Cada siniestro situado pesa según la cobertura de su año y tipo de dirección; el seguimiento del Plan se hace con todos los siniestros, situados o no.
- **Sugerencia:** Completar el número o el cruce si constan en el atestado, o publicar las coordenadas.
- **Cómo reproducirlo:** Filas cuya UBICACION no contiene « cruce » ni termina en un número de portal (expresión regular `\s\d+\s*[A-Z]*$`, que admite «12», «12 B» o «1AC»): 2.390 sin ninguna cifra y 32 de carreteras identificadas solo por su código (A V-31, CTRA CV-500…) → 2.422; por mes, máximo en 2022-03 (192 de 527)

#### INC-009 · Algunos «cruces» son de dos calles que no se tocan

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UBICACION · **Tipo:** valor impreciso · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Hay «cruces» entre dos calles que, en el callejero, están a más de 100 m una de otra. Parecen una referencia aproximada del tipo «a la altura de». Son alrededor del 7 % de los cruces hasta junio de 2024 y el 0,1 % desde julio de 2024. En algunos casos el tipo de vía no coincide: por ejemplo, «PL JESUS» donde la calle de Jesús sí cruza.
- **Ejemplo:** «AV CATALUÑA cruce AV HERMANOS MACHADO» (calles a 1,5 km, 41 filas); «AV HERMANOS MACHADO cruce CAMI FARINOS» (470 m, 44 filas)
- **Alcance:** 800 filas a más de 100 m si se admite que el tipo de vía (C/, PL…) pueda estar cambiado, y 966 si no; de ellas, 571 y 715 a más de 300 m (con nuestro método). Última comprobación automática: 800 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** El siniestro no se puede situar, o se sitúa mal si se toma un punto entre las dos calles.
- **Cómo lo tratamos en el observatorio:** No se sitúan y se declaran. Los de 40 a 100 m, que también quedan sin situar, dependen sobre todo de la geometría de los ejes del callejero (avenidas con calzadas separadas, rotondas) y de nuestro método; por eso no se incluyen en esta incidencia.
- **Sugerencia:** Revisar estos casos; si el registro quiere decir «a la altura de», indicarlo así, o publicar las coordenadas.
- **Cómo reproducirlo:** Para las UBICACION «A cruce B», distancia mínima entre los ejes de A y B en el callejero (EPSG:25830) mayor de 100 m → 966 filas con el tipo de vía del registro; 800 si para cada nombre se toma la vía más cercana de cualquier tipo

#### INC-010 · La forma de anotar los siniestros cambia en octubre de 2022, julio de 2024 y octubre de 2024, sin nota en la ficha

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UBICACION, FECHA, TIPO ACCIDENTE · **Tipo:** inconsistencia entre años · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La forma de registrar los siniestros cambia en tres momentos, sin nota en la ficha: en octubre de 2022 casi todas las direcciones pasan a llevar número (solo calle: del 19 % de septiembre al 4 %); en julio de 2024 (cuando, según el Plan Director, se crea el SIASV en la Policía Local) desaparecen casi todos los cruces entre calles que no se tocan y el tipo de accidente se completa; y desde octubre de 2024 las horas llevan segundos.
- **Ejemplo:** FECHA con segundos distintos de 00: 0 filas hasta junio de 2024; 21 de julio a septiembre de 2024; 1.771 de octubre a diciembre de 2024 y 8.272 en 2025
- **Alcance:** Todo el conjunto (tres etapas). Última comprobación automática: 34.244 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Las comparaciones entre años mezclan cambios reales con cambios de registro (cobertura del mapa de los siniestros con bici o VMP, con nuestro método: 74 % en enero-septiembre de 2022 y 96 % desde julio de 2024; reparto entre cruce y portal).
- **Cómo lo tratamos en el observatorio:** Se trabaja con tres etapas (enero-septiembre de 2022, octubre de 2022-junio de 2024 y desde julio de 2024) y se corrige por cobertura.
- **Sugerencia:** Documentar en la ficha las fechas de cambio de sistema y de criterio de anotación.
- **Cómo reproducirlo:** Por mes: porcentaje de UBICACION solo con calle (receta de INC-008), de TIPO ACCIDENTE = «NULL» y de FECHA con segundos ≠ 00 → saltos en 2022-10, 2024-07 y 2024-10

#### INC-011 · No hay coordenadas: el lugar viene escrito como una dirección

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UBICACION · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La ubicación es solo texto: el conjunto no trae coordenadas ni el código de vía del callejero.
- **Ejemplo:** «AV DEL PUERTO 12», «C/ X cruce AV Y»
- **Alcance:** 34.244 filas (todas). Última comprobación automática: 34.244 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Cada persona que reutiliza el dato tiene que geocodificarlo por su cuenta; con nuestro método, una parte no se puede situar (11,7 % del total).
- **Cómo lo tratamos en el observatorio:** Geocodificación propia con el callejero municipal (vías, ejes y portales): hemos podido situar el 88,3 %.
- **Sugerencia:** Publicar las coordenadas de cada siniestro (o al menos del cruce o tramo) o, como mínimo, el código de vía (codvia) y el número. Según el Plan Director, el SIASV ya es una base de datos georreferenciada, así que podría ser el origen de esas coordenadas.
- **Cómo reproducirlo:** Columnas del conjunto: _id, FECHA, TIPO GRAVEDAD, UBICACION, TIPO ACCIDENTE, UNIDADES_IMPLICADAS, FACTORES CONCURRENTES (ninguna de coordenadas ni codvia)

#### INC-012 · Algunos nombres de calle no coinciden con el callejero o usan entradas sin eje o dadas de baja

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UBICACION (frente al callejero) · **Tipo:** formato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Algunos nombres de calle del conjunto no coinciden con el callejero municipal (vías, capa 273) o usan entradas del callejero sin eje o dadas de baja.
- **Ejemplo:** «PROFESOR LOPEZ PIÑERO» (453 filas) frente a «PROFESSOR LOPEZ PIÑERO» en el callejero; «LLOC PUENTE MONTEOLIVETE» (54) es una entrada del callejero sin eje (codvia 990210; el puente con eje es la 81699, que el conjunto usa desde 2024); «C/ FRANCISCO LOZANO (PINTOR).CARRER DE» (7) es la entrada dada de baja 81475
- **Alcance:** 514 filas en los ejemplos (453 + 54 + 7). Última comprobación automática: 514 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Los siniestros no casan con el callejero si no se normalizan los nombres a mano.
- **Cómo lo tratamos en el observatorio:** Normalización de nombres y una tabla de equivalencias de 4 calles.
- **Sugerencia:** Incluir el código de vía (codvia) en cada siniestro.
- **Cómo reproducirlo:** Contar UBICACION con «PROFESOR LOPEZ PIÑERO», «LLOC PUENTE MONTEOLIVETE» y «FRANCISCO LOZANO (PINTOR).CARRER DE» → 453 + 54 + 7; buscar esos nombres en vias.json (capa 273) y sus codvia en los ejes (capa 223)

#### INC-013 · Hay siniestros en lugares que no están en el callejero (Jardín del Turia, autovías)

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UBICACION (frente al callejero) · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Parte de las ubicaciones son de lugares que no son calles municipales y no están en el callejero: el Jardín del Turia y autovías y carreteras (V-21, V-31, CV-500…). Es lógico que el callejero no los incluya; sin coordenadas, estos siniestros no se pueden situar.
- **Ejemplo:** «JARDÍN DEL TURIA cruce …», «A V-31 …», «A V-21 …»
- **Alcance:** 168 filas con el Jardín del Turia y 164 con autovías o carreteras (sin contar la V-30, que sí está en el callejero); con nuestro método, 94 cruces no se pueden situar por una de estas vías (42 con el Jardín del Turia). Última comprobación automática: 94 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** No se pueden situar con el callejero.
- **Cómo lo tratamos en el observatorio:** El Jardín del Turia se trata como una zona; el resto queda sin situar.
- **Sugerencia:** Publicar coordenadas o una referencia (punto kilométrico, tramo) para las vías que no están en el callejero.
- **Cómo reproducirlo:** Contar UBICACION con «JARDÍN DEL TURIA» (168) y con «A» o «CTRA» seguidas de un código de carretera, sin la V-30 (164); para «A cruce B», casos en que A o B no tiene codvia en vias.json y es el Jardín del Turia o una carretera → 94

#### INC-014 · Un solo fichero 2022-2025, sin frecuencia de actualización ni años anteriores

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** ficha del conjunto · **Tipo:** publicación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Es el único conjunto de siniestros del portal: un solo recurso CSV de 2022-2025, creado el 28/05/2026, sin frecuencia de actualización ni años anteriores (2019-2021). No consta si habrá datos de 2026 ni cómo se publicarán.
- **Ejemplo:** Ficha CKAN (package_show): num_resources = 1; sin campo de frecuencia; título «Accidentes de tráfico 2022-2025»
- **Alcance:** El conjunto entero. Última comprobación automática: —, sigue presente.
- **Por qué importa a quien reutiliza:** No se puede planificar un seguimiento anual (por ejemplo, del indicador 3.2.2 del Plan Director) ni automatizar la descarga.
- **Cómo lo tratamos en el observatorio:** Se ha pedido la publicación de 2026; el observatorio se actualiza solo cuando llega un año completo.
- **Sugerencia:** Indicar la frecuencia en la ficha, publicar cada año (mejor ampliando el mismo conjunto, con un nombre sin años) y, si existen, los años anteriores.
- **Cómo reproducirlo:** `package_show?id=siniestros-de-trafico-2022-2025` → num_resources 1, sin frecuencia de actualización

#### INC-015 · La ficha no explica los campos ni la fecha de extracción

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** ficha del conjunto · **Tipo:** documentación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La ficha describe el conjunto en una frase: no hay diccionario de campos (qué significa cada categoría de gravedad, qué es «NULL», cómo se escribe la ubicación), ni fecha de extracción o versión, ni notas de cambios de criterio. Los campos de la API (datastore) no llevan descripción. El campo description del recurso, el que devuelve la API por defecto, dice «2022y 2025»; la versión en castellano (description_es) lo escribe bien.
- **Ejemplo:** notes_es: «Accidentes de tráfico ocurridos entre los años 2022 y 2025 en la ciudad de València.»
- **Alcance:** El conjunto entero. Última comprobación automática: —, sigue presente.
- **Por qué importa a quien reutiliza:** Quien reutiliza tiene que deducir el significado de los campos y los cambios de criterio.
- **Cómo lo tratamos en el observatorio:** Lo deducido se documenta en la página de método.
- **Sugerencia:** Añadir un diccionario de campos, la fecha de extracción y una nota de cambios (gravedad desde 2023, formato de la dirección, SIASV en julio de 2024).
- **Cómo reproducirlo:** `package_show`: notes_es tiene una sola frase; no hay recurso de diccionario ni fecha de extracción. `datastore_search?limit=0`: los 7 campos, sin descripción

#### INC-027 · Ubicaciones con el texto «nan» en lugar de una calle o un número

- **Conjunto:** Accidentes de tráfico 2022-2025 (portal de datos abiertos) (https://opendata.vlci.valencia.es/dataset/siniestros-de-trafico-2022-2025)
- **Campo:** UBICACION · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** En algunas filas la ubicación lleva el texto «nan» en lugar de la calle, del número o de la segunda calle del cruce («C/ SOL cruce nan», «nan 22», «nan»). Todas son de julio de 2022 a junio de 2024. Además, hay cruces de una calle consigo misma («AV GIORGETA cruce AV GIORGETA»), la mayoría con el Jardín del Turia.
- **Ejemplo:** _id 17141 (C/ SOL cruce nan), 12215 (nan 22) y 4173 (nan); _id 6621 (AV GIORGETA cruce AV GIORGETA)
- **Alcance:** 28 filas con «nan» (16 «… cruce nan», 7 «nan» con número y 5 solo «nan»; 9 con bici o VMP); 16 cruces de una calle consigo misma (12 del Jardín del Turia; 12 con bici o VMP). Última comprobación automática: 28 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** «nan» es como algunos programas escriben un dato vacío: la parte que falta no se puede recuperar y la fila no se puede situar.
- **Cómo lo tratamos en el observatorio:** Las filas con «nan» quedan sin situar. Los cruces de una calle consigo misma se sitúan en un punto de esa calle; pendiente tratarlos como «solo calle».
- **Sugerencia:** Dejar vacío el dato que falta, o completarlo desde el atestado, y revisar los cruces de una calle consigo misma.
- **Cómo reproducirlo:** `UBICACION.str.contains(r"\bnan\b").sum()` → 28; cruces con las dos calles iguales → 16

### Catálogo del portal de datos abiertos (DCAT)

#### INC-016 · El enlace de la licencia del catálogo lleva a una página no encontrada (404)

- **Conjunto:** Catálogo del portal de datos abiertos (DCAT) (https://opendata.vlci.valencia.es/catalog.ttl)
- **Campo:** dct:license del catálogo · **Tipo:** documentación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El catálogo DCAT declara como licencia general https://opendata.vlci.valencia.es/aviso-legal/catalog, y esa dirección devuelve la respuesta 404 (página no encontrada). Las fichas de cada conjunto declaran CC BY 4.0.
- **Ejemplo:** https://opendata.vlci.valencia.es/aviso-legal/catalog → 404 (04/11/2026)
- **Alcance:** —.
- **Por qué importa a quien reutiliza:** Un agregador o una herramienta que lea el catálogo no encuentra la licencia general.
- **Cómo lo tratamos en el observatorio:** Se usa la licencia de cada ficha (CC BY 4.0) y la política de uso del portal.
- **Sugerencia:** Corregir el enlace de la licencia del catálogo.
- **Cómo reproducirlo:** Abrir https://opendata.vlci.valencia.es/aviso-legal/catalog → 404

### Servicio OPENDATA del geoportal municipal

#### INC-017 · Los servicios del geoportal no declaran la licencia

- **Conjunto:** Servicio OPENDATA del geoportal municipal (https://geoportal.valencia.es/server/rest/services/OPENDATA)
- **Campo:** copyrightText · **Tipo:** documentación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Los servicios de mapas del geoportal de los que se descargan las capas (UrbanismoEInfraestructuras: callejero y portales; Trafico: carril bici, semáforos, espiras, VMP e intensidad) no declaran la licencia ni la atribución (copyrightText vacío). La licencia (CC BY 4.0) está en la ficha de cada capa en el portal.
- **Ejemplo:** …/OPENDATA/UrbanismoEInfraestructuras/MapServer?f=json y …/OPENDATA/Trafico/MapServer?f=json → copyrightText vacío (04/11/2026)
- **Alcance:** —.
- **Por qué importa a quien reutiliza:** Quien descarga del servicio no ve la licencia ni la fórmula de atribución.
- **Cómo lo tratamos en el observatorio:** Se cita la licencia de la ficha del portal (CC BY 4.0).
- **Sugerencia:** Rellenar copyrightText de los dos servicios con la licencia y la atribución.
- **Cómo reproducirlo:** Consultar los dos servicios con f=json y mirar copyrightText

### Portales de las calles (geoportal, capa 217)

#### INC-018 · Algunos portales tienen varios puntos distintos para la misma dirección

- **Conjunto:** Portales de las calles (geoportal, capa 217) (https://opendata.vlci.valencia.es/dataset/portals-dels-carrers-portales-de-las-calles)
- **Campo:** codvia, numportal, dupli_trip, accesorio, descripcion · **Tipo:** geometría · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Algunos portales aparecen varias veces con todos los atributos iguales (calle, número, dupli_trip, accesorio y descripción) en posiciones distintas. En otros, el número (numportal) no coincide con el rótulo (descripcion). Los números bis, A, B… están bien distinguidos por dupli_trip; esto es otra cosa.
- **Ejemplo:** codvia 11880, n.º 46: dos puntos a 445 m con todos los atributos iguales; codvia 77580: n.º 10 rotulado «27» y n.º 8 rotulado «37». Además, accesorio se escribe «SI», «SÍ», «Sí» o «si»
- **Alcance:** 51 combinaciones con todo igual en posiciones distintas (11 a más de 50 m y 2 a más de 200 m); 19 portales con numportal distinto de su rótulo. Última comprobación automática: 51 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Una dirección puede situarse en sitios distintos según qué punto se tome.
- **Cómo lo tratamos en el observatorio:** El geocodificador toma el primero; pendiente marcar estos casos como ambiguos.
- **Sugerencia:** Revisar estas combinaciones y dejar un solo punto por portal; unificar los valores de accesorio.
- **Cómo reproducirlo:** Agrupar la capa 217 por (codvia, numportal, dupli_trip, accesorio, descripcion) y medir la distancia máxima entre puntos (EPSG:25830) → 63 grupos con más de un punto, 51 en posiciones distintas, 11 a más de 50 m; comparar numportal con el número inicial de descripcion → 19

#### INC-031 · Algunos portales están lejos de su calle

- **Conjunto:** Portales de las calles (geoportal, capa 217) (https://opendata.vlci.valencia.es/dataset/portals-dels-carrers-portales-de-las-calles)
- **Campo:** geometría, codvia · **Tipo:** geometría · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Algunos portales están a cientos de metros, o a kilómetros, del eje de su propia calle: o el punto está mal situado o falta un tramo del eje.
- **Ejemplo:** C/ Proa 31 duplicado (codvia 61530), a 20,9 km de su calle, junto a Rodrigo Pertegás; C/ Picaio 9 (rótulo «5ac»), a 2,3 km; Camí del Salinar 51 a 61, a 500-620 m, junto al Camí Nou del Salinar
- **Alcance:** 15 portales a más de 200 m del eje de su calle (2 a más de 1 km); 6 siniestros, ninguno con bici o VMP, situados en ellos. Última comprobación automática: 15 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Una dirección con esos portales se sitúa lejos de su calle.
- **Cómo lo tratamos en el observatorio:** Pendiente descartar los portales a más de 200 m de su calle; ningún siniestro con bici o VMP se ha situado en ellos.
- **Sugerencia:** Revisar la posición de estos portales o completar el eje de su calle.
- **Cómo reproducirlo:** Distancia de cada portal (capa 217, EPSG:25830) al eje de su codvia (capa 223) → 15 a más de 200 m y 2 a más de 1 km

### Vehículos de movilidad personal tipo A y tipo B (geoportal, capas 2 y 3)

#### INC-019 · Las capas de la red de patinetes tipo A y tipo B son idénticas

- **Conjunto:** Vehículos de movilidad personal tipo A y tipo B (geoportal, capas 2 y 3) (https://geoportal.valencia.es/server/rest/services/OPENDATA)
- **Campo:** geometría y atributos · **Tipo:** documentación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Las capas «Vehículos Movilidad Personal Tipo A» y «Tipo B» devuelven los mismos 9.256 tramos con la misma geometría (unos 950 km). La leyenda de la de tipo A incluye una clase «calles peatonales» que la de tipo B no tiene; esa clase no tiene tramos, y el campo que distingue las clases (subtipo: carril bici, ciclocalle, calle residencial, calle 30, viejo cauce) no se incluye en la descarga.
- **Ejemplo:** vmp_tipo_a.geojson y vmp_tipo_b.geojson: misma suma MD5 (descarga del 30/10/2026); en el servidor, los mismos 9.256 identificadores el 04/11/2026
- **Alcance:** 9.256 tramos. Última comprobación automática: 9.256 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** No se sabe si los VMP de tipo B tienen la misma red permitida que los de tipo A.
- **Cómo lo tratamos en el observatorio:** Se usa solo como contexto; ningún análisis depende de ella.
- **Sugerencia:** Confirmar si las dos redes deben ser iguales y, si no, publicar la de cada tipo; publicar también el campo subtipo.
- **Cómo reproducirlo:** Comparar los dos ficheros descargados (`md5sum`) → idénticos

#### INC-035 · La red de los patinetes tiene tramos repetidos

- **Conjunto:** Vehículos de movilidad personal tipo A y tipo B (geoportal, capas 2 y 3) (https://geoportal.valencia.es/server/rest/services/OPENDATA)
- **Campo:** geometría · **Tipo:** duplicado · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** En las dos capas hay tramos repetidos: la misma línea aparece dos veces con gid distinto, a veces dibujada en sentido contrario.
- **Ejemplo:** gid 10909 y 16729; 9708 y 18336; 14557 y 14571
- **Alcance:** 23 tramos sobrantes en cada capa (19 en el mismo sentido), 3,8 km de 954. Última comprobación automática: 23 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** La longitud de la red por la que pueden circular los VMP sale unos 3,8 km mayor.
- **Cómo lo tratamos en el observatorio:** No medimos la longitud de esta red; la usamos solo como capa del mapa.
- **Sugerencia:** Quitar los tramos repetidos.
- **Cómo reproducirlo:** Geometrías iguales tras `normalize()` (EPSG:25830) → 23 repetidas; sin normalizar → 19

### Intensidad de tráfico por tramos (geoportal, capa 188)

#### INC-020 · La capa de intensidad de tráfico es en tiempo real, sin histórico

- **Conjunto:** Intensidad de tráfico por tramos (geoportal, capa 188) (https://geoportal.valencia.es/server/rest/services/OPENDATA)
- **Campo:** lectura, imv · **Tipo:** documentación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La capa da la última lectura de cada sensor, sin histórico ni fecha de la lectura. La ficha describe los campos, sin las unidades de lectura e imv («Intensidad Media Vehicular o aforo estimado»), el periodo de imv ni el significado de −1. En las descargas del 30/10/2026 y del 04/11/2026, 36 tramos tienen lectura = −1.
- **Ejemplo:** Pérez Galdós y Peris y Valero con lectura -1
- **Alcance:** 36 de 394 tramos con −1 (30/10/2026 y 04/11/2026). Última comprobación automática: 36 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Sin saber qué mide imv, no se puede usar como intensidad media diaria (IMD), que es lo que se necesita para medir exposición.
- **Cómo lo tratamos en el observatorio:** Se usa solo para situar los tramos de la IMD de vehículos de Movilidad (idtramo).
- **Sugerencia:** Documentar las unidades, el periodo de imv y el valor −1, y publicar en el portal la serie histórica de IMD por tramo.
- **Cómo reproducirlo:** `(capa188.lectura == -1).sum()` → 36; no hay campo de fecha de la lectura

#### INC-034 · Algunos códigos de tramo de tráfico están repetidos en sitios distintos

- **Conjunto:** Intensidad de tráfico por tramos (geoportal, capa 188) (https://geoportal.valencia.es/server/rest/services/OPENDATA)
- **Campo:** idtramo, fiwareid · **Tipo:** duplicado · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Tres códigos de tramo aparecen en dos tramos distintos y separados por 2 a 4 km, uno con fiwareid y otro sin él. Además, dos registros no tienen geometría ni idtramo y solo llevan el fiwareid de otros dos tramos (tramo_A363 y tramo_A364), que a su vez no tienen fiwareid. Sigue igual en la consulta del 07/11/2026.
- **Ejemplo:** A122 «GRAN VIA RAMON Y CAJAL»: gid 810, en la Gran Via, y gid 811, a 4 km; también A39 y A85; gid 1185 y 1585, sin geometría
- **Alcance:** 3 códigos en 6 tramos; 2 registros sin geometría. Última comprobación automática: 3 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Al unir por idtramo la IMD de vehículos de Movilidad, el valor se asigna a dos sitios y uno de ellos no es el tramo medido.
- **Cómo lo tratamos en el observatorio:** Hoy la IMD se asigna a los dos tramos; pendiente quedarnos con el que corresponde al nombre del tramo.
- **Sugerencia:** Dejar un solo tramo por código y unir los registros partidos.
- **Cómo reproducirlo:** `capa188.idtramo[capa188.idtramo.duplicated()]` → A122, A39 y A85; `capa188.geometry.isna().sum()` → 2

### Intensidades de tráfico (web del Servicio de Movilidad)

#### INC-022 · Las intensidades de tráfico solo están en la web de Movilidad, no en el portal

- **Conjunto:** Intensidades de tráfico (web del Servicio de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** publicación · **Tipo:** publicación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Las intensidades medias de tráfico (IMD del carril bici, IMD de vehículos y la evolución mensual 2019-2026) están en la web de Movilidad, como ficheros ODS, XLSX y PDF, y no en el portal de datos abiertos.
- **Ejemplo:** carril_bici_2025.ods, imds_vehiculos_2025.ods, evolucion_imd_mensual_2019-sep2026.xlsx
- **Alcance:** —.
- **Por qué importa a quien reutiliza:** No tienen ficha, licencia explícita ni dirección estable: la dirección de cada fichero incluye un identificador interno, así que no se puede prever la del año siguiente.
- **Cómo lo tratamos en el observatorio:** Se descargan de la web de Movilidad y se citan como complemento.
- **Sugerencia:** Publicarlas en el portal (CKAN) con su histórico, licencia y diccionario, idealmente como CSV.
- **Cómo reproducirlo:** Buscar «IMD», «aforo» o «intensidad media» en el portal (CKAN) → solo las capas en tiempo real (188 y 225); los ficheros están en https://www.valencia.es/cas/movilidad/otras-descargas

### IMD del carril bici, ODS anuales (web de Movilidad)

#### INC-023 · El formato de las hojas de intensidades cambia de un mes a otro

- **Conjunto:** IMD del carril bici, ODS anuales (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** estructura de las hojas · **Tipo:** formato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La estructura de las hojas mensuales cambia: los nombres de las columnas varían de un mes a otro (el código se llama ATA, Nombre, NOMBRE, CAR o PM; la IMD, «IMD Lab.», «IMD_LABORABLES», «IMD» o «Lab.», entre otros), el sentido pasa de la descripción a una columna propia en octubre de 2022, algunas hojas tienen columnas vacías y los nombres de hoja no siguen siempre el mismo patrón.
- **Ejemplo:** Diciembre de 2022: primera columna vacía; junio de 2023: columnas vacías al final y hoja «CARRI_BICI_JUNIO_2023»; septiembre de 2023: hoja «CARRIL_BICI_SEPTIEMBRE», sin año
- **Alcance:** 4 ficheros, 48 hojas. Última comprobación automática: 48 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Hay que detectar las columnas hoja a hoja; un programa que suponga un formato fijo puede leer mal los datos sin darse cuenta.
- **Cómo lo tratamos en el observatorio:** Se detecta el código y la IMD por su contenido, no por su posición.
- **Sugerencia:** Publicar un formato tabular estable y largo (año, mes, código, descripción, sentido, IMD), en CSV.
- **Cómo reproducirlo:** Para cada hoja, cabecera (primera fila) de la columna con códigos P### y de la IMD, columna «Sentido» y columnas vacías → 5 nombres del código, 10 de la IMD, «Sentido» desde octubre de 2022 y 3 hojas con columnas vacías o el código desplazado

#### INC-024 · Una errata en el sentido de un contador del Pont de Fusta

- **Conjunto:** IMD del carril bici, ODS anuales (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** descripción y sentido del contador · **Tipo:** errata · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El contador P1163 (Pont de Fusta) lleva la errata «AMBOS ENTIDOS» (por «ambos sentidos»): de enero a agosto de 2022, dentro de la descripción, y desde octubre de 2022, en la columna de sentido.
- **Ejemplo:** P1163 «CARRIL BICI PONT DE FUSTA (AMBOS ENTIDOS)» (enero-agosto de 2022); «CARRIL BICI PONT DE FUSTA | AMBOS ENTIDOS» (desde octubre de 2022)
- **Alcance:** 1 contador (P1163), 44 de 48 hojas mensuales. Última comprobación automática: 44 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Quien busque «AMBOS SENTIDOS» no lo encuentra. En el mismo puente hay otro contador, P238 («contador bicicletas»), sin sentido indicado y con valores casi iguales (enero de 2023: 3.021 y 2.998), y no queda claro si miden lo mismo.
- **Cómo lo tratamos en el observatorio:** Se revisan las descripciones de todos los años; en el Pont de Fusta usamos solo P1163, porque P238 da casi los mismos valores y sumarlos los contaría dos veces.
- **Sugerencia:** Corregir la errata y dar el sentido siempre en un campo propio con valores fijos («ambos», «entrada», «salida»).
- **Cómo reproducirlo:** Buscar «ENTIDOS» en las filas de los cuatro ODS → P1163 en 44 hojas (11, 12, 11 y 10 por año)

#### INC-025 · Algunos contadores del carril bici no tienen posición publicada

- **Conjunto:** IMD del carril bici, ODS anuales (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** código del contador · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Algunos códigos de contador de los ODS no tienen punto en la capa de espiras del carril bici (geoportal, capa 225), así que no se pueden situar. La mayoría ya no aparece en 2025 (posiblemente, contadores retirados). La ficha de la capa ya indica que tiene errores de procesamiento en revisión.
- **Ejemplo:** 2025: P1047, P1167, P1227, P1228, P1553, P1921…
- **Alcance:** 12 de los 160 contadores de 2025; 29 de 178 en 2022-2025 (17 de ellos ya no aparecen en 2025). Última comprobación automática: 12 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Esos contadores no se pueden usar para comparar siniestros con uso.
- **Cómo lo tratamos en el observatorio:** Quedan fuera del análisis de uso.
- **Sugerencia:** Incluir las coordenadas en el propio fichero de intensidades, también las de los contadores retirados, o completar la capa 225.
- **Cómo reproducirlo:** Códigos P### de los ODS de cada año que no están en `idpm` de la capa 225 → 13 (2022), 23 (2023), 12 (2024), 12 (2025); 29 de 178 en total

#### INC-036 · Un contador escrito en minúscula y cifras guardadas como texto

- **Conjunto:** IMD del carril bici, ODS anuales (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** código del contador, IMD · **Tipo:** formato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El contador P2821 (Av. de los Naranjos) se escribe en minúscula, «p2821», en 45 hojas (de enero de 2022 a septiembre de 2025); de octubre a diciembre de 2025, «P2821». La IMD de enero a abril de 2022 está guardada como texto y no como número, y 8 de las 48 hojas dan la IMD con decimales sin redondear (por ejemplo, 1433,50757575758), mientras que las demás la dan en enteros.
- **Ejemplo:** «p2821» en IMD_ENERO_2022 y en CARRIL_BICI_SEPTIEMBRE_2025; «841» como texto en IMD_ENERO_2022; 1433,50757575758 en IMD_SEPTIEMBRE_2022
- **Alcance:** 45 hojas con «p2821»; 491 valores de IMD como texto (4 hojas); 1.007 valores con decimales (8 hojas). Última comprobación automática: 45 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Quien filtre los códigos por «P» y cifras pierde ese contador casi todos los meses; los valores guardados como texto no suman al abrir el fichero.
- **Cómo lo tratamos en el observatorio:** Nuestros scripts buscaban la «P» en mayúscula y dejaban fuera P2821 en esos meses (lo hemos visto en esta revisión; pendiente de corregir). El texto lo convertimos a número.
- **Sugerencia:** Escribir los códigos siempre igual, en mayúscula, y guardar la IMD como número y con el mismo redondeo en todas las hojas.
- **Cómo reproducirlo:** Códigos `[a-z]\d+` en las hojas → «p2821» en 45; celdas de IMD de tipo texto → 491; hojas con valores no enteros → 8

#### INC-037 · Contadores repetidos en las hojas del carril bici

- **Conjunto:** IMD del carril bici, ODS anuales (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** código del contador · **Tipo:** duplicado · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El contador P9200201 aparece dos veces en la misma hoja, con dos descripciones casi iguales («F.CATOLICO [ENTRADA]» y «F.CATOLICO ENTRADA») y valores iguales o casi iguales. Además, de 2022 a 2025 hay 17 códigos F que no están en la capa de espiras; 7 de ellos repiten, mes a mes, el valor exacto de un contador P (por ejemplo, F37 y P1163, Pont de Fusta).
- **Ejemplo:** P9200201 en CARRIL_BICI_MARZO_2023: 598 y 597; F37 y P1163: 3.314 los dos en abril de 2023
- **Alcance:** P9200201 repetido en 8 hojas; 17 códigos F (134 filas), 7 iguales a un P en 8 meses. Última comprobación automática: 8 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Si se suman los contadores, esos aforos cuentan dos veces.
- **Cómo lo tratamos en el observatorio:** Solo usamos los códigos P con punto en la capa de espiras; P9200201 y los códigos F no lo tienen, así que no entran.
- **Sugerencia:** Dejar una fila por contador y hoja, y explicar qué son los códigos F o quitarlos si repiten un P.
- **Cómo reproducirlo:** Filas con el mismo código en la misma hoja → P9200201 en 8 hojas; códigos F con el mismo valor que un P el mismo mes → 7 pares en 8 meses

#### INC-038 · Un tramo de coches entre los contadores de bici y meses a 0

- **Conjunto:** IMD del carril bici, ODS anuales (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** código del contador, IMD · **Tipo:** valor erróneo · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** En 4 hojas de 2023 del carril bici aparece el tramo de vehículos A409 (Camino de las Moreras), con más de 8.000 vehículos al día. Además, 5 contadores tienen IMD 0 en un mes, que parece una avería más que un dato, y P836 (Pérez Galdós) no tiene valor en marzo de 2022.
- **Ejemplo:** A409 en CARRIL_BICI_MARZO_2023 (8.203); P1552 y P1553 con 0 en mayo de 2023; P237 con 0 en agosto de 2025
- **Alcance:** 4 filas de A409; 5 IMD a 0; 1 IMD vacía. Última comprobación automática: 4 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Un 0 se confunde con un dato real y baja la media anual del contador; el tramo de vehículos infla cualquier total del carril bici.
- **Cómo lo tratamos en el observatorio:** Solo usamos códigos P; los meses a 0 se tratan como avería y no entran en la media.
- **Sugerencia:** Quitar A409 de los ficheros del carril bici y dejar vacío, o marcar, el mes en que un contador no mide.
- **Cómo reproducirlo:** Códigos A### en los ODS del carril bici → A409 en 4 hojas; IMD = 0 → 5; IMD vacía → 1

### IMD de vehículos 2025, ODS (web de Movilidad) y capa 188

#### INC-026 · Muchos tramos de la intensidad de vehículos no tienen posición publicada

- **Conjunto:** IMD de vehículos 2025, ODS (web de Movilidad) y capa 188 (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** código del tramo · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Muchos tramos de la IMD de vehículos no tienen geometría en la capa 188, la única que hemos encontrado con esos códigos.
- **Ejemplo:** Códigos A### y B### del ODS sin idtramo en la capa 188
- **Alcance:** 122 de 412 códigos A y 14 de 102 códigos B (además, 15 F y 2 E, ninguno en la capa), 2025. Última comprobación automática: 122 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Esos tramos no se pueden situar para medir el tráfico de vehículos alrededor de un lugar.
- **Cómo lo tratamos en el observatorio:** Se usan solo los tramos que casan.
- **Sugerencia:** Publicar la IMD de vehículos con la geometría de cada tramo.
- **Cómo reproducirlo:** Códigos A###, B###, E### y F### del ODS que no están en `idtramo` de la capa 188 → A 122 de 412, B 14 de 102, E 2 de 2, F 15 de 15

### Vías del callejero (geoportal, capa 273)

#### INC-028 · Algunos nombres de calle en castellano están cortados

- **Conjunto:** Vías del callejero (geoportal, capa 273) (https://opendata.vlci.valencia.es/dataset/vias)
- **Campo:** traducnooficial, nomoficial · **Tipo:** valor erróneo · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La traducción al castellano (traducnooficial) de algunos nombres largos está cortada a 43 o 44 caracteres, aunque el campo admite 75 y el nombre oficial (nomoficial) está completo. El conjunto de siniestros usa esos mismos nombres cortados. Además, algunos nombres terminan con un espacio o un salto de línea.
- **Ejemplo:** codvia 81675: «FEDERICO ALCACER AGUILAR (DOCTOR EN MEDICINA» (oficial: «… MEDICINA)»); 81570: «FREDERIC JORDAN I CALVO (PRESIDENT DE LA SOC»; 81629: «JOSE BELENGUER CUENCA» seguido de un salto de línea
- **Alcance:** 6 nombres cortados (32 filas de siniestros los usan); 9 nombres con un espacio o un salto de línea al final. Última comprobación automática: 6 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Quien busque o una las calles por el nombre completo no las encuentra.
- **Cómo lo tratamos en el observatorio:** Casamos los siniestros con la traducción tal como está publicada (cortada igual) y quitamos los espacios de los extremos.
- **Sugerencia:** Completar las traducciones cortadas y quitar los espacios y saltos de línea sobrantes.
- **Cómo reproducirlo:** Capa 273: traducnooficial con más «(» que «)» cuando nomoficial los cierra → 6; nombres que cambian al quitar los espacios finales → 9

### Ejes de calle (geoportal, capa 223)

#### INC-029 · Tramos de calle sin código de vía y un tramo repetido

- **Conjunto:** Ejes de calle (geoportal, capa 223) (https://opendata.vlci.valencia.es/dataset/eixos-de-carrer-ejes-de-calle)
- **Campo:** codvia, nomcalle · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** Hay tramos de eje de alta sin código de vía ni nombre, un tramo repetido (misma geometría y mismos atributos) y un tramo cuya vía figura como dada de baja en la capa de vías.
- **Ejemplo:** objectid 78282, 78283 y 79562 a 79566, sin codvia; objectid 66861 y 67774 (Comte de Torrefiel, 5-7), iguales; codvia 50920 (MUELA), con tramo y de baja en la capa de vías
- **Alcance:** 19 tramos sin codvia (3,8 km); 1 tramo repetido; 1 tramo con la vía de baja. Última comprobación automática: 19 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Los tramos sin código no se pueden asociar a ninguna calle; el repetido cuenta dos veces si se mide la longitud de la calle.
- **Cómo lo tratamos en el observatorio:** Los tramos sin codvia no se usan; el repetido no cambia nada, porque unimos los tramos de cada calle.
- **Sugerencia:** Asignar la vía a los tramos sin código, o darlos de baja, y quitar el tramo repetido.
- **Cómo reproducirlo:** `ejes.codvia.isna().sum()` → 19; filas iguales en atributos y geometría → un par

#### INC-030 · Los ejes escriben algunos nombres y tipos de vía de otra forma que la capa de vías

- **Conjunto:** Ejes de calle (geoportal, capa 223) (https://opendata.vlci.valencia.es/dataset/eixos-de-carrer-ejes-de-calle)
- **Campo:** nomcalle, tipcalle · **Tipo:** formato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** En los ejes, el apóstrofo de los nombres se escribe con el acento agudo «´» («FORN D´ALCEDO»), mientras que la capa de vías usa el apóstrofo «'». El tipo de vía también tiene grafías distintas: «PASSAGE» en 16 tramos y «PASSATGE» en 1, un tramo con «C/» en lugar de «CARRER» y 6 tramos de avenidas con el tipo «CARRER» o «PLAÇA».
- **Ejemplo:** codvia 36120: «FORN D´ALCEDO» en los ejes y «FORN D'ALCEDO» en la capa de vías; tipcalle «PASSAGE» en Doctor Serra
- **Alcance:** 210 tramos de 65 vías con «´»; 23 tramos con un tipo de vía distinto del de la capa de vías. Última comprobación automática: 65 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Quien una ejes y vías por el nombre, o filtre por tipo de vía, pierde esos tramos.
- **Cómo lo tratamos en el observatorio:** Tomamos los nombres de la capa de vías; de los ejes, solo la geometría y el código de vía.
- **Sugerencia:** Usar el mismo apóstrofo que la capa de vías y unificar los tipos de vía.
- **Cómo reproducirlo:** `ejes.nomcalle.str.contains("´")` → 210 tramos de 65 codvia; tipcalle frente a codtipovia de la capa 273 → 23 distintos

### Itinerarios ciclistas (geoportal, capa 189)

#### INC-032 · La ficha de los carriles bici no explica los códigos de tipo de tramo

- **Conjunto:** Itinerarios ciclistas (geoportal, capa 189) (https://opendata.vlci.valencia.es/dataset/itinerarios-ciclistas-itineraris-ciclistes)
- **Campo:** estado, st_length · **Tipo:** documentación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La ficha describe estado como un «código numérico que clasifica la situación operativa o tipología del tramo ciclista», sin el significado de los códigos 1 a 9. Ese significado solo está en el servicio de mapas (dominio del campo) y no llega con las descargas. Entre ellos están el 8, «Red ciclista fuera del término municipal», y el 5, «Cortado por obras». El campo de longitud que describe la ficha (st_length) se descarga como st_length_the_geom_ y vale 0 en todos los tramos.
- **Ejemplo:** código 8: 199 tramos y 33,2 km de los 327,8 km de la capa; st_length_the_geom_ = 0 en los 1.705 tramos
- **Alcance:** 1.705 tramos (los 199 con código 8 suman 33,2 km). Última comprobación automática: 1.705 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Sin el significado de los códigos, quien mida la red ciclista de València incluye un 10 % de kilómetros fuera del término municipal y tramos cortados por obras.
- **Cómo lo tratamos en el observatorio:** Tomamos el significado de los códigos del servicio de mapas y medimos la longitud con la geometría.
- **Sugerencia:** Poner en la ficha la tabla de códigos y, en la descarga, el texto de cada código; rellenar el campo de longitud o quitarlo.
- **Cómo reproducirlo:** Dominio del campo estado en …/OPENDATA/Trafico/MapServer/189?f=json; `(capa189.st_length_the_geom_ == 0).sum()` → 1.705

### Reguladores de grupos semafóricos (geoportal, capa 182)

#### INC-033 · Dos campos de los reguladores de semáforos están vacíos

- **Conjunto:** Reguladores de grupos semafóricos (geoportal, capa 182) (https://opendata.vlci.valencia.es/dataset/reguladors-grups-semaforics-reguladores-grupos-semaforicos)
- **Campo:** tiporegulador, codregulador · **Tipo:** falta de dato · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** La ficha describe los campos de tipo y código del regulador, que están vacíos en todos los registros (también en el servicio de mapas, consultado el 07/11/2026).
- **Ejemplo:** codcruce 2408: tiporegulador y codregulador vacíos, como en el resto
- **Alcance:** 1.072 de 1.072 reguladores. Última comprobación automática: 1.072 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** No se puede distinguir el tipo de regulador ni enlazarlo con otros datos del sistema de gestión del tráfico.
- **Cómo lo tratamos en el observatorio:** Solo usamos la posición del regulador, para saber si un cruce tiene semáforo.
- **Sugerencia:** Rellenar los dos campos o retirarlos de la capa y de la ficha.
- **Cómo reproducirlo:** `(capa182.tiporegulador.isna() & capa182.codregulador.isna()).sum()` → 1.072; en el servicio, `tiporegulador IS NOT NULL OR codregulador IS NOT NULL` → 0

### IMD de vehículos 2025, ODS (web de Movilidad)

#### INC-039 · Tramos de tráfico con intensidad 0 en un mes

- **Conjunto:** IMD de vehículos 2025, ODS (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** IMD · **Tipo:** valor erróneo · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** En abril de 2025, cuatro tramos tienen IMD 0, entre ellos Blasco Ibáñez (A49), que el resto del año supera los 27.000 vehículos al día. Además, enero y mayo dan la IMD con decimales y los demás meses en enteros, y hay dos celdas con solo espacios (la descripción de A96 en marzo y una columna de más en julio).
- **Ejemplo:** A49, Blasco Ibáñez: 33.073 en enero, 0 en abril y 27.376 en agosto; también A17, A224 y A359 en abril
- **Alcance:** 4 IMD a 0; 976 valores con decimales (enero y mayo); 2 celdas con solo espacios. Última comprobación automática: 4 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Un 0 se confunde con un dato real y baja la media anual del tramo.
- **Cómo lo tratamos en el observatorio:** Los meses a 0 se tratan como avería y no entran en la media.
- **Sugerencia:** Dejar vacío, o marcar, el mes en que un tramo no mide y usar el mismo redondeo en todas las hojas.
- **Cómo reproducirlo:** IMD = 0 en las hojas de imds_vehiculos_2025.ods → 4 (abril); valores no enteros → enero y mayo

### Evolución mensual de la IMD 2019-2026, XLSX (web de Movilidad)

#### INC-040 · Las intensidades estimadas o poco fiables solo se marcan con colores

- **Conjunto:** Evolución mensual de la IMD 2019-2026, XLSX (web de Movilidad) (https://www.valencia.es/cas/movilidad/otras-descargas)
- **Campo:** calidad de cada IMD (formato de la celda) · **Tipo:** documentación · **Estado:** comunicada (2026-11-07, Formulario «Contacte» del portal de datos abiertos (aviso breve; el informe completo se enviará a la dirección que indiquen))
- **Qué pasa:** El fichero marca las IMD estimadas y las de fiabilidad inferior al 85 % solo con el color de la celda (relleno amarillo y letra verde o roja): al leerlo como datos, esa marca se pierde. Hay además 5 celdas con relleno naranja que la leyenda no explica. Los ODS anuales del carril bici no marcan nada y, en algunos meses estimados, dan otro valor: P1444 tiene 38 en octubre de 2023 en el ODS y 2.247 (estimada) en el XLSX.
- **Ejemplo:** Hoja «Carriles Bici Representativos»: 1444 en 2023-10 (2.247, estimada; 38 en el ODS); 1545 en 2022-03 (fórmula =AVERAGE(AC8,BA8), 2.544,5; 1.843 en el ODS)
- **Alcance:** 331 celdas marcadas solo con color (279 estimadas y 52 de fiabilidad < 85 %) en 3 hojas; 3 de 1.404 valores del carril bici distintos de los ODS. Última comprobación automática: 331 (comprobado el 2026-11-07), sigue presente.
- **Por qué importa a quien reutiliza:** Quien use los ODS no sabe qué meses son poco fiables o están estimados, y quien lea el XLSX con un programa pierde la marca.
- **Cómo lo tratamos en el observatorio:** Usamos los ODS; pendiente quitar de nuestras medias los meses que el XLSX marca como estimados o poco fiables.
- **Sugerencia:** Añadir, en el XLSX y en los ODS, una columna con la calidad de cada dato (medido, estimado o fiabilidad < 85 %).
- **Cómo reproducirlo:** openpyxl: celdas de dato con relleno FFFFFF00 → 331 (letra FF00B050, estimada: 279; FFFF0000, fiabilidad < 85 %: 52); hoja «Carriles Bici Representativos» frente a los ODS → 3 diferencias de más del 5 %

## Cómo se ha comprobado

Los datos son los publicados en el portal de datos abiertos, el geoportal y la web de Movilidad, descargados entre el 30/10/2026 y el 04/11/2026 (siniestros: 34.244 filas). Las pruebas se han hecho con Python (pandas y geopandas; distancias en EPSG:25830). Las 36 comprobaciones automáticas se repiten cada vez que se descargan datos nuevos; las demás (3) se revisan a mano. No hemos usado ni publicado ningún dato personal: los ejemplos son identificadores de fila (_id) o valores de los campos.

El conjunto de siniestros se ha leído con la API del portal (`datastore_search`), que coincide celda a celda con el CSV publicado (34.244 filas). Los `_id` son los de la API; en el CSV descargable (ISO-8859-1, separado por «;», con la cabecera `UBICACIÓN` con tilde y sin `_id`), cada `_id` corresponde a la línea `_id` + 1. En la API, un campo vacío llega como nulo; en el CSV, como texto vacío.

Algunas cifras (INC-008 a INC-013) dependen de nuestro método para situar las direcciones con el callejero municipal. En esos casos lo indicamos y, cuando es posible, damos una receta que se puede repetir sin nuestro código. Las cifras de INC-001 a INC-026 se han vuelto a comprobar el 04/11/2026 en una revisión independiente, con código propio y descargas nuevas. INC-027 a INC-040 salen de una revisión sistemática del 07/11/2026, con la misma lista de comprobaciones para cada conjunto (duplicados, vacíos, formatos, valores, geometrías, claves entre conjuntos, coherencia entre años y fichas); las de las capas 182, 188, 189 y 273 se han confirmado ese día en el servicio de mapas.

## Gracias

Gracias por el trabajo del portal y por tener en cuenta estas notas. Si alguna incidencia está mal planteada, ya está corregida o tiene una explicación, pueden escribirnos a hola@observatoribicivlc.org y lo reflejaremos en el registro. Estaremos encantados de seguir colaborando como personas que reutilizan los datos y avisan de lo que encuentran.
