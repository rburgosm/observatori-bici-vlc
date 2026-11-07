# Datos de origen (`data/raw/`) / Dades d'origen

Procedencia, licencia y uso de cada fichero de `data/raw/`. Se descargaron el **30/10/2026** (salvo los que indican otra fecha) y se guardan **sin modificar**. Las modificaciones (geocodificación, marcas de bici y VMP, agregados) se hacen en los scripts y sus resultados no están en el repositorio: se regeneran con `make`.

*[va] Procedència, llicència i ús de cada fitxer de `data/raw/`. Tots es van descarregar el 30/10/2026 i es guarden sense modificar. Les modificacions es fan en els scripts i els seus resultats es regeneren amb `make`.*

Atribución común a los datos del Ajuntament: **«Fuente de los datos: Ajuntament de València – Dades Obertes»** (https://opendata.vlci.valencia.es), CC BY 4.0. El Ajuntament de València no participa en este trabajo ni lo respalda.

## `data/raw/siniestros/`

| Fichero | Contenido | Procedencia | Licencia | Lo usa |
|---|---|---|---|---|
| `siniestros-de-trafico-2022-2025.json` | Siniestros de tráfico 2022-2025 (una fila por siniestro, 34.244, con todos los vehículos implicados en `UNIDADES_IMPLICADAS`, separados por comas; ubicación como calle escrita) | Portal de datos abiertos, conjunto `siniestros-de-trafico-2022-2025` («Accidentes de tráfico 2022-2025») | CC BY 4.0 | `geocodificar.py` y todo el análisis |
| `vias.json` | Vías del callejero (código y nombres oficial y castellano) | Geoportal, capa 273 (`fetch_callejero.py`) | CC BY 4.0 | `geocodificar.py`, `lugares.py` |
| `ejes.geojson` | Ejes de calle con rangos de portales | Geoportal, capa 223 (`fetch_callejero.py`) | CC BY 4.0 | `geocodificar.py`, `lugares.py` |
| `portales.geojson` | Portales de las calles (número y posición) | Geoportal, capa 217 (`fetch_callejero.py`) | CC BY 4.0 | `geocodificar.py` |
| `carriles_bici.geojson` | Red de carriles bici | Geoportal, capa 189 | CC BY 4.0 | `cribado_eb.py`, `vmp_vs_bici.py`, `exportar_web.py` |
| `reguladores_semaforos.geojson` | Reguladores semafóricos municipales | Geoportal, capa 182 | CC BY 4.0 | `cribado_eb.py`, `validar_semaforos.py`, `exportar_web.py` |
| `espiras_bici.geojson` | Puntos de conteo del carril bici (`idpm`, sin conteos) | Geoportal, capa 225 | CC BY 4.0 | `cribado_eb.py`, `exportar_web.py` (geolocalizan las intensidades) |
| `intensidad_tramos.geojson` | Tramos de intensidad de tráfico en tiempo real (`idtramo`); **no sirve como IMD**, solo para situar `imds_vehiculos_2025.ods` | Geoportal, capa 188 | CC BY 4.0 | `cribado_eb.py` |
| `vmp_tipo_a.geojson` | Red por la que pueden circular los VMP (951 km) | Geoportal, capa 2 («Vehículos Movilidad Personal Tipo A») | CC BY 4.0 | contexto; `incidencias.py` (INC-019) |
| `vmp_tipo_b.geojson` | Red de los VMP de tipo B: idéntica byte a byte a la A (misma suma MD5) | Geoportal, capa 3 («Vehículos Movilidad Personal Tipo B») | CC BY 4.0 | `incidencias.py` (INC-019: se incluye para poder comprobar que las dos capas son iguales) |
| `centros_educativos.geojson` | Centros educativos | Portal de datos abiertos, conjunto `centros-educativos-en-valencia` (`fetch_callejero.py`) | CC BY 4.0 | `analisis_viabilidad.py` |
| `meteo_openmeteo_2022_2025.json` | Lluvia horaria, lluvia diaria y hora de la puesta de sol en València (39,47 N, 0,37 O), 2022-2025 | Open-Meteo, API histórica (https://open-meteo.com). «Weather data by Open-Meteo.com» | CC BY 4.0 | `vmp_vs_bici_condicionado.py` |
| `obras_ejecutadas.csv` | Conjunto «Obras ejecutadas»: en realidad, permisos de ocupación de la vía pública (no sirve para el análisis) | Portal de datos abiertos, conjunto `obres-executades` | CC BY 4.0 | `incidencias.py` (INC-021) |
| `portales_atributos.json` | Portales con todos sus atributos (`codvia`, `numportal`, `dupli_trip`, `accesorio`, `descripcion` y posición), descargados el 04/11/2026 | Geoportal, capa 217 (`incidencias.py --red`) | CC BY 4.0 | `incidencias.py` (INC-018) |
| `ckan_siniestros_package.json` | Ficha CKAN (`package_show`) del conjunto de siniestros, consultada el 04/11/2026 | API del portal de datos abiertos | CC BY 4.0 | `incidencias.py` (`--red` la vuelve a descargar) |
| `osm_semaforos.json` | Semáforos de OpenStreetMap en València (1.051 elementos; complemento, incompleto) | Overpass API, base OSM del 30/10/2026. «© OpenStreetMap contributors» | **ODbL 1.0** (https://opendatacommons.org/licenses/odbl/1-0/) | `validar_semaforos.py`, `exportar_web.py` |

`osm_semaforos.json` es un extracto de OpenStreetMap y sigue bajo ODbL: si se redistribuye o se combina con otros datos en una base de datos, la base resultante debe cumplir la ODbL. Por eso **no entra** en el conjunto de datos derivado CC BY.

`obras_ejecutadas.csv` y `vmp_tipo_b.geojson` no sirven para el análisis, pero se incluyen para que se puedan comprobar las incidencias INC-021 y INC-019 (`make incidencias`).

## `data/raw/intensidades/`

| Fichero | Contenido | Procedencia | Licencia | Lo usa |
|---|---|---|---|---|
| `carril_bici_2022.ods` … `carril_bici_2025.ods` | Intensidad media diaria (IMD) de laborables por mes y punto de conteo del carril bici | Ajuntament de València, Servicio de Movilidad, https://www.valencia.es/cas/movilidad/otras-descargas | Aviso legal de valencia.es: reutilización citando la fuente, sin alterar ni desvirtuar los datos y sin sugerir respaldo | `cribado_eb.py`, `exportar_web.py` |
| `imds_vehiculos_2025.ods` | IMD de vehículos por tramo, 2025 | Ídem | Ídem | `cribado_eb.py`, `exportar_web.py` |
| `evolucion_imd_mensual_2019-sep2026.xlsx` | Series mensuales largas de IMD | Ídem | Ídem | contexto |

Estos ficheros no están en el portal de datos abiertos y se descargaron a mano de la web de Movilidad: son los únicos que no se regeneran con un script del repositorio. Se publican tal cual, con su fuente.

## `data/raw/pdsv/`

| Fichero | Contenido | Procedencia | Lo usa |
|---|---|---|---|
| `pdsv.txt` | Transcripción en texto (pdftotext) del Plan Director de Seguridad Vial de València 2026-2030 | Ajuntament de València, https://www.valencia.es/documents/d/guest/pdsv_valencia_2026-2030-pdf | `transcribir_pdsv.py` (`make plan`) |

El PDF original no se incluye. El que se usó tiene este SHA-256: `6e84d664ffb77b7da2ff1eee699b4133966cacee4ff9c2617e1138d689cd6b7d`.

## `data/processed/` (entradas propias, CC BY 4.0)

| Fichero | Contenido |
|---|---|
| `nombres_lugares.csv` | Nombres publicados (congelados) de los lugares con siniestros |
| `nombres_puntos_conteo.csv` | Nombres legibles de los puntos de conteo del carril bici |
| `fichas_slugs.csv` | Direcciones (slugs) fijas de las fichas de cada lugar y calle, para que los enlaces no cambien |
| `equivalencias_calles.csv` | Equivalencias entre la calle escrita en el parte y el callejero |
| `referencia_categorias.csv` | Valores de referencia de los campos categóricos del portal (años, tipos…), para que `comprobar.py` avise si aparecen valores nuevos |
| `pdsv_indicadores.csv`, `pdsv_lugares.csv` | Indicadores y lugares del Plan Director (los regenera `make plan` desde `pdsv.txt`) |
| `observatorio_plan.sql` | Seguimiento del Plan en texto (volcado SQL): es la fuente de las tablas `plan_*` de la base SQLite que construye `make sqlite` |
| `plan_seguimiento.csv` | Estado de las actuaciones del Plan sobre bici y patinete, cada una con su fuente («El Plan, al día»); es la exportación de la base |
| `plan_fuentes.csv` | Registro de las fuentes consultadas para «El Plan, al día»: qué publican, si son útiles y accesibles, consultas y aciertos |
| `colaboran.csv` | Entidades que colaboran con el observatorio, con qué aportan y desde cuándo (solo las que lo han confirmado por escrito); las publica el pie de la web |
| `incidencias_datos.csv` | Registro de incidencias detectadas en los datos del Ajuntament (prueba, impacto, cómo se tratan, sugerencia y estado de la comunicación); lo re-verifica `incidencias.py` (`make incidencias`) y lo publica la página de método |
| `avisos_ciudadanos.csv` | Registro público de los avisos de la ciudadanía sobre obras o medidas del Plan (fecha, medida o lugar, resumen en va y es, resultado `incorporado`/`en_revision`/`sin_fuente` y fuente oficial); sin nombres ni correos de quien avisa. Lo publica la página del Ayuntamiento (`/ajuntament/#avisa`) y lo valida `comprobar_sitio.py` |

Derivados de los datos del Ajuntament (callejero y Plan Director), con la atribución de arriba.

El conjunto de datos derivado no se incluye: se regenera con `make` a partir de los datos del portal. *[va] El conjunt de dades derivat no s'inclou: es regenera amb `make` a partir de les dades del portal.*
