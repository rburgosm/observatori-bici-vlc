# Dataset abierto derivado: licencia y privacidad

Fecha: 04/11/2026. Prepara el punto 74 de la lista interna de pendientes (exportación del dataset geolocalizado). Es investigación y recomendación: no cambia código ni datos.

Cálculos en scripts temporales de la sesión, fuera del proyecto (`k.py` y `util.py`, de usar y tirar; no se conservan). Si se quieren conservar, conviene rehacerlos como `scripts/privacidad_dataset.py`.

---

## 1. Licencia

### Qué dicen las fichas (API CKAN `package_show`, consultada el 04/11/2026)

| Dataset (portal) | Id CKAN | Licencia |
|---|---|---|
| Accidentes de tráfico 2022-2025 («Accidents de tràfic 2022-2025») | `siniestros-de-trafico-2022-2025` | `cc-by`: «Atribución 4.0 Internacional (CC BY 4.0)», `license_url` http://creativecommons.org/licenses/by/4.0/deed.es |
| Vías (geoportal, capa 273) | `vias` | CC BY 4.0 |
| Ejes de calle (capa 223) | `eixos-de-carrer-ejes-de-calle` | CC BY 4.0 |
| Portales de las calles (capa 217) | `portals-dels-carrers-portales-de-las-calles` | CC BY 4.0 |
| Centros educativos (no entra en el dataset de siniestros) | `centros-educativos-en-valencia` | CC BY 4.0 |

- Las capas se descargan del servicio del geoportal (`geoportal.valencia.es/.../OPENDATA/UrbanismoEInfraestructuras/MapServer`), que no declara `copyrightText`. Su ficha en el portal es la de la tabla.
- La ficha de siniestros es de la organización «Ajuntament de València», sin autor ni mantenedor, con `isopen: True` y fecha de modificación 10/08/2026.
- El catálogo DCAT (`catalog.ttl`) declara a nivel de catálogo `dct:license <https://opendata.vlci.valencia.es/aviso-legal/catalog>`, pero esa URL da **404**. Hay que fiarse de la licencia de cada ficha y de la política de uso.

### Política de uso del portal

Fuente: https://www.valencia.es/web/gobierno-abierto/cas/datos-abiertos/reutilizacion/politica-de-uso-datos-abiertos/politica-de-uso. Se leyó con WebFetch, que solo devuelve citas breves. Antes de publicar, conviene guardar una copia del texto íntegro con la fecha de consulta.

- **Licencia por defecto:** reutilización «sin sujeción a condiciones» (art. 4.2 a) de la Ley 37/2007) y licencia CC BY 4.0, salvo que se indique otra.
- **Usos permitidos:** copiar, distribuir, **crear obras derivadas** y usar con fines comerciales o no comerciales.
- **Atribución, fórmula literal:** «**Fuente de los datos: Ajuntament de València – Dades Obertes**». Hay que añadir la **fecha de obtención o de última actualización** de los datos y, en HTML, se puede enlazar a http://www.valencia.es/dadesobertes.
- **Modificaciones:** «toda modificación debe identificarse como tal» al distribuirla. CC BY 4.0 exige lo mismo en la sección 3(a)(1)(B).
- **Sentido:** prohibido desvirtuar el sentido de la información.
- **Respaldo:** no se puede insinuar que el Ayuntamiento participa, patrocina o respalda el uso.
- **Proyectos derivados:** se pide comunicárselos al Ayuntamiento (encaja con la colaboración prevista con el Ayuntamiento y con entidades).
- **Garantías:** datos «tal cual», sin garantía ni responsabilidad del Ayuntamiento, y con régimen sancionador del art. 11 de la Ley 37/2007.
- **Datos personales:** en los datos anonimizados, «está expresamente prohibido reidentificar personas» cruzándolos con otras fuentes.

Aviso legal general de valencia.es (https://www.valencia.es/cas/aviso-legal, leído con WebFetch):

- El Ayuntamiento «permite reutilizar todos los datos e informaciones» difundidos en su web, salvo indicación contraria.
- Pone como condiciones no alterar el contenido, no desvirtuar el sentido, citar la fuente y no insinuar patrocinio.
- Lo limita la protección de datos personales.
- No menciona Creative Commons. Para los datasets prevalecen la ficha y la política de uso, más específicas.

### Conclusión sobre la licencia

- **Se puede publicar el derivado y con CC BY 4.0.** CC BY no tiene cláusula «compartir igual», así que el derivado puede llevar la misma licencia, que además es la más coherente.
- **Restricciones propias de los siniestros:** la ficha no dice nada. La única es la general de no reidentificar personas (ver la parte 2).
- **Cuidado con mezclar fuentes:** si el dataset llevara campos derivados de **OpenStreetMap** (`osm_semaforos.json` o la verificación con Nominatim), quedaría sujeto a la **ODbL**, que sí obliga a compartir igual. Esos campos no deben entrar en el dataset abierto: el semáforo, si se añade, ha de salir del regulador municipal (capa 182, CC BY). Open-Meteo usa CC BY 4.0 y es compatible.
- La licencia del **código** es otra decisión (punto 62).

**Atribución propuesta para el README y el pie de la web** (en castellano y en valenciano):

> Fuente de los datos: Ajuntament de València – Dades Obertes (https://opendata.vlci.valencia.es). Conjuntos «Accidentes de tráfico 2022-2025» (siniestros-de-trafico-2022-2025), «Vías», «Ejes de calle» y «Portales de las calles», CC BY 4.0, descargados el 30/10/2026. **Datos modificados** por el Observatori de la bici i el patinet: se añaden coordenadas geocodificadas con el callejero municipal, método e incertidumbre de la geocodificación, marcas de bici/VMP y marcas de calidad. El Ajuntament de València no participa en este trabajo ni lo respalda.
>
> Font de les dades: Ajuntament de València – Dades Obertes (…) **Dades modificades** per l'Observatori de la bici i el patinet (…). L'Ajuntament de València no participa en aquest treball ni l'avala.

Además, cada versión publicada debe llevar su fecha de descarga de la fuente (la política de uso pide la fecha de obtención).

---

## 2. Privacidad (RGPD y LOPDGDD)

### Qué trae el original y qué añade el nuestro

**Original** (7 campos):

- `_id`;
- `FECHA`, con **hora y minuto**: el 89 % de los registros tiene minutos distintos de 0;
- `TIPO GRAVEDAD`, con 5 valores (46 «CON FALLECIDOS»);
- `UBICACION` en texto: el 51 % son «cruce» y el 42 % lleva número, p. ej. «C/ CAVITE 99»;
- `TIPO ACCIDENTE`;
- `UNIDADES_IMPLICADAS`, la lista de vehículos;
- `FACTORES CONCURRENTES`.

No trae **ni edad, ni sexo, ni tipo de persona, ni alcohol o drogas, ni matrícula, ni número de atestado**. Hay un registro por siniestro, no por persona.

**Lo que añadimos** (`siniestros_geo.csv`): `metodo`, `lon/lat`, `dist_ejes_m` y, en la exportación, `incertidumbre_m`, `codvia` y las marcas bici/VMP y de calidad.

- Las marcas salen de campos que ya existen (`UNIDADES_IMPLICADAS`).
- La coordenada es una **función determinista del texto de `UBICACION`**: cada texto distinto da exactamente 1 coordenada (máximo 1), y cada coordenada corresponde de media a 1,05 textos.
- Por tanto, **la coordenada no añade información sobre el siniestro**. Traduce a un punto lo que el texto ya dice y, como mucho, agrupa variantes de escritura del mismo lugar.
- Cualquiera puede rehacerla con el callejero municipal, que también es abierto.

### k-anonimidad (calculada sobre los 30.225 siniestros con coordenadas)

| Combinación de campos | únicos (k=1) | k<5 |
|---|---|---|
| **Original:** ubicación (texto) + fecha y hora | 99,7 % | 100 % |
| Original: ubicación + día | 97,3 % | 100 % |
| Original: ubicación + mes | 76,5 % | 97,4 % |
| Original: ubicación + año | 40,3 % | 70,2 % |
| Coordenada exacta + día | 97,2 % | 100 % |
| Coordenada exacta + año | 38,8 % | 68,2 % |
| Celda de 100 m + año | 11,4 % | 42,0 % |
| Celda de 100 m + mes | 58,9 % | 94,4 % |
| Celda de 200 m + mes | 36,4 % | 86,6 % |
| Solo graves y fallecidos: ubicación + año (original) | 83,6 % | 100 % |
| Solo graves y fallecidos: celda de 100 m + año | 67,2 % | 98,2 % |

Cómo leer la tabla:

- **El original ya identifica de forma única casi cada siniestro** por lugar y hora: un 99,7 % es único. Es lo normal en un registro de sucesos, porque cada uno pasa en un sitio y a una hora.
- **La coordenada exacta no empeora nada**: coordenada + año da un 38,8 % de únicos frente al 40,3 % del texto + año. Es incluso algo mejor, porque une variantes del mismo lugar.
- Que un siniestro sea único no lo hace dato personal. Hace falta poder llegar a una **persona**, y el dataset no lleva ningún atributo de las personas.

### Riesgo concreto

El escenario realista es el de una persona que conoce el suceso por otra vía: la prensa local publica los atropellos mortales con calle, hora y a veces el nombre, o es un vecino o un familiar. Esa persona busca el registro y averigua lo que añade el dataset: gravedad, tipo, vehículos y factores concurrentes. Por ejemplo, «conducción distraída», que puede leerse como una imputación de culpa.

- **Ese riesgo ya existe con el original**, con el mismo lugar, minuto y campos. El geocodificado no lo aumenta.
- Lo que cambia es la **facilidad**: el mapa permite encontrar un suceso sin conocer el texto exacto. Es un aumento de *exposición*, no de *información*.
- La **coordenada en un portal** puede leerse como «aquí vive la víctima», cuando solo es el número que anotó la policía. Se corrige con texto: «la coordenada es la del número de portal citado en el parte, no un domicilio».
- **Fallecidos:** el RGPD no se aplica a los datos de personas fallecidas (considerando 27; art. 2.2 b de la LOPDGDD). Sí afecta a las demás personas implicadas (otro conductor, heridos).
  - Hay 46 siniestros con fallecidos en total, 42 geocodificados: 23 en cruce, 19 en portal y 4 sin coordenada.
  - De ellos, 9 son de bici o VMP.
- **Prohibición de reidentificar** (política de uso): el proyecto no la incumple, porque no cruza para identificar a nadie. Hay que repetir la prohibición en nuestra licencia y no publicar nunca cruces con noticias o nombres.

### Qué hacen otros portales (comprobado en sus API el 04/11/2026)

**Madrid** (`datos.madrid.es`, dataset `300228-0-accidentes-trafico-detalle`, CC BY 4.0):

- un registro **por persona** implicada;
- `fecha` y `hora` con minuto («0:49:00»);
- `localizacion` y `numero` de portal;
- `rango_edad` en tramos de 5 años, `sexo`, `tipo_persona` y `lesividad`;
- `positiva_alcohol` y `positiva_droga`;
- `coordenada_x_utm` y `coordenada_y_utm`, al metro o al centímetro (p. ej. «442386,41»).

**Barcelona** (`opendata-ajuntament.barcelona.cat`, dataset `accidents-persones-gu-bcn`, CC BY 4.0):

- un registro **por persona** implicada;
- día, mes y año, y `Hora_dia` (hora entera);
- calle y `Num_postal`;
- `Edat` exacta y `Descripcio_sexe`;
- tipo de persona y victimización;
- `Latitud_WGS84` y `Longitud_WGS84` con 8 decimales.

**DGT** (microdatos de accidentes con víctimas 2024, `TABLA_ACCIDENTES_24.XLSX`, vía datos.gob.es):

- año, mes, día de la semana y hora, **sin día del mes**;
- código de municipio, suprimido («00000») en el 12 % de los registros, sobre todo en zona interurbana;
- carretera y kilómetro entero;
- **sin coordenadas ni calle**: en València ciudad, 3.090 de 3.206 registros tienen carretera «No inventariada»;
- es estadística oficial, con secreto estadístico.

En resumen, Madrid y Barcelona publican **mucho más** que nosotros: coordenada exacta, minuto o hora, portal y además **edad y sexo por persona**. Nuestro derivado no lleva ningún atributo de las personas.

### Guía aplicable

- **AEPD**, *Orientaciones y garantías en los procedimientos de anonimización de datos personales* (2016) y *Orientaciones sobre la protección de datos en la reutilización de la información del sector público* (2016). Fichas en https://datos.gob.es/es/documentacion/orientaciones-y-garantias-en-los-procedimientos-de-anonimizacion-de-datos-personales y https://datos.gob.es/es/documentacion/orientaciones-sobre-la-proteccion-de-datos-en-la-reutilizacion-de-la-informacion-del.
  - Ninguna técnica garantiza la anonimización absoluta.
  - Recomiendan un análisis de riesgos documentado y revisarlo periódicamente.
- **AEPD**, nota técnica *La K-anonimidad como medida de la privacidad* (2019; versión inglesa: https://www.aepd.es/documento/nota-tecnica-kanonimidad-en.pdf).
  - Es la métrica usada arriba.
  - Advierte de que el riesgo se mide sobre los **cuasi-identificadores que un atacante puede conocer**. Aquí, lugar y hora, ya públicos.
- **Consejo de Transparencia:** no se ha encontrado un criterio específico sobre datos de siniestros con lugar y hora. En RT 0960/2021 pide suprimir los datos personales del parte de la Policía Local, pero no dice que el lugar y la hora lo sean. Es un punto sin fuente firme.
- **Ninguna de estas guías habla de geolocalización de sucesos de tráfico.**

### Opciones

Contexto para medir el coste:

- el análisis usa celdas de 100 m y 200 m alineadas en EPSG:25830 y radios de 100 m alrededor de las espiras;
- hay 13.960 siniestros geocodificados en portal (2.309 de bici o VMP) y 16.265 en cruce.

| Opción | Protección real | Coste para la utilidad |
|---|---|---|
| **A. Publicar tal cual**: coordenada exacta, fecha y hora del original y sin atributos de persona | Igual que el original, que ya es público | Ninguno |
| **B. Cruces exactos; portales llevados al centro de una rejilla de 50 m** alineada con la de 100 m | **Casi nula**: el texto `UBICACION` y el `id` siguen ahí y se puede volver a geocodificar con el callejero. Solo protege si además se quitan el texto y el id, y entonces el dataset deja de ser verificable contra la fuente | Las celdas de 100 y 200 m no cambian (0 %). Desplazamiento medio de 19 m (máx. 35). 75 de 2.309 siniestros de bici o VMP en portal cambian su estado «a menos de 100 m de una espira» (25 m: 43; 100 m: 138). Pierde precisión para agrupar por nudo y tramo (punto 77) |
| **C. Quitar el minuto (solo la hora) o agrupar en franjas** | Casi nula por la misma razón: el original lleva el minuto | Pequeño: lluvia y ocaso se cruzan por hora (`meteo_openmeteo`) |
| **D. Sin coordenada para los siniestros con fallecidos** (42) | Simbólica: el original los tiene, y la prensa también | Pequeño en cifras (9 de bici o VMP), pero desaparecen del mapa los casos más graves, que son los que más interesan en seguridad vial. Además, el RGPD no protege a las personas fallecidas |
| **E. Publicar solo agregados** (celdas de 100 m por año) | Real (11 % únicos), pero ya no es el dataset geolocalizado | Alto: pierde la aportación principal (punto 1 de la idea) y la verificabilidad |

### Recomendación

**Opción A, publicar tal cual, con cuatro salvaguardas de bajo coste.**

Por qué A:

- El derivado **no añade información personal**: la coordenada se deduce del texto público.
- No lleva ningún atributo de las personas, a diferencia de Madrid y Barcelona.
- Cualquier recorte que hagamos se deshace uniendo con el original por `id` o regeocodificando el texto. Las opciones B, C y D solo restan utilidad sin proteger nada.
- El riesgo residual es el que ya asume el Ayuntamiento al publicar el original.

Salvaguardas:

1. **No añadir campos de persona ni de otras fuentes que identifiquen**: nada de noticias, nombres, matrículas o edades. Si algún día el Ayuntamiento publica edad o sexo, revisar este análisis antes de incorporarlos.
2. **Aviso en el README y en la web**, en castellano y valenciano:
   - la coordenada es la del cruce o el número de portal citado en el parte, no un domicilio;
   - está prohibido reidentificar personas, como en la política de uso del portal;
   - hay un canal para pedir la revisión de un registro.
3. **Seguir a la fuente**: si el Ayuntamiento retira o corrige filas, la siguiente versión las retira o corrige igual. Si un registro se borra en origen por motivos de privacidad, no debe seguir vivo en nuestro dataset.
4. **Dejar escrito este análisis** como registro de la decisión (responsabilidad proactiva, art. 5.2 del RGPD), con la tabla de k-anonimidad, y revisarlo con cada versión anual.

Opcional, si se quiere un gesto visible sin coste analítico: en la **web pública** (no en el dataset), mostrar los siniestros con fallecidos sin hora exacta en la ficha emergente. Es un criterio editorial de respeto, no una medida de protección de datos.

### Qué decide el usuario

1. **Opción A o B.** A es la recomendada. B solo tiene sentido si se quiere prudencia de cara a terceros (Ayuntamiento, entidades colaboradoras), sabiendo que no protege nada mientras el texto siga en el dataset.
2. **Si el dataset repite el texto `UBICACION` y el resto de campos del original** (recomendado, para que sea autosuficiente y verificable) o solo `id` + campos nuevos, para unir con el original.
3. **El criterio editorial de la web con los fallecidos** (hora en la ficha emergente).
4. **Consultar o no al Ayuntamiento** (Oficina de Datos Abiertos, https://www.valencia.es/web/gobierno-abierto/cas/datos-abiertos/contacta) antes de publicar:
   - la política de uso pide comunicar los proyectos derivados;
   - su conformidad con las coordenadas refuerza la colaboración con el Ayuntamiento y descarta sorpresas.

### Decisión del usuario (07/11/2026)
**Opción A** para el mapa y su CSV: fecha y hora, dirección, factores y coordenada de cada accidente, como el portal («déjalo así, siempre y cuando el resto sea coherente»). Las fichas estáticas (indexadas por los buscadores con el nombre del sitio) siguen con mes y año y factores en conjunto. La web lo explica en `dades/#descarrega`, con el canal de revisión de un registro (hola@) y el compromiso de seguir a la fuente si retira o corrige filas. Quedan abiertos los puntos 2-4 de «Qué decide el usuario» para el dataset versionado (pendiente 74).
