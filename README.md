# Observatori de la bici i el patinet de València

**Web:** https://observatoribicivlc.org · **Codi / Código:** https://github.com/rburgosm/observatori-bici-vlc

[Valencià](#valencià) · [Castellano](#castellano)

---

## Valencià

### Què és

Un observatori obert que segueix l'indicador de l'acció 3.2.2 del Pla Director de Seguretat Viària de València 2026-2030 (reduir un 50 % els sinistres amb bici o patinet en 2030) i mostra on s'acumulen els sinistres. Fa públic el seguiment que el Pla preveu per a ús intern.

- **Arxiu i mapes:** sinistres de trànsit de 2022 a 2025 amb bici i patinet (VMP) per separat, situats en el mapa a partir del carrer i el número que dona el portal.
- **El Pla, al dia:** estat de les actuacions del Pla sobre bici i patinet, cadascuna amb la seua font.
- **La meta:** la base és 2025. Sense les dades de 2026, el Pla encara no es pot avaluar.

Els llocs amb més sinistres no són llocs de més risc: no hi ha dades de quanta gent hi passa en bici o en patinet. El risc del patinet per viatge no es pot mesurar amb els comptadors actuals, que no separen bicis i patinets. Les limitacions de les dades s'expliquen a la pàgina de mètode de la web.

### Com es reprodueix

Tot (dades processades, xifres, web i comprovacions) es regenera a partir de les dades d'origen de `data/raw/`. Cal Python 3.12, GNU Make i `flock` (util-linux, ja instal·lat en la majoria de distribucions Linux); per al PDF de l'informe d'incidències, també Google Chrome o Chromium.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # versions fixades
make geocodificar   # situa els sinistres en el mapa: data/processed/siniestros_geo.csv (només la primera vegada o quan canvia el carrerer)
make                # l'anàlisi que estiga desfasada + web + comprovacions (la primera vegada, uns minuts)
```

Després, per a treballar:

- `make web`: només la web, amb l'anàlisi que ja hi haja (segons). Necessita que abans s'haja fet `make geocodificar` i `make` (o `make analisis`).
- `make comprobar`: comprova les dades i la web (OK / AVÍS / ERROR).
- `make sqlite`: la base `data/processed/observatorio.sqlite`, d'on llig la web. El seguiment del Pla es guarda en text a `data/processed/observatorio_plan.sql`.
- `make incidencias`: torna a verificar els errors trobats en les dades de l'Ajuntament i escriu l'informe (`.md` i, amb Chrome, `.pdf`).

La web queda en `web/proto/build/`. Per a veure-la: `python3 -m http.server 8000 --directory web/proto/build` i obrir http://localhost:8000/.

`make` regenera tots els fitxers derivats (`data/processed/siniestros_geo.csv`, `outputs/`, `web/proto/datos/`, `web/proto/build/` i la base SQLite). Cap d'ells està al repositori.

### Estructura

| Carpeta | Contingut |
|---|---|
| `scripts/` | Un script per pas: geocodificació, llocs, cribratge amb comptadors, seguiment de l'indicador, exportació, web, fitxes i comprovacions. El `Makefile` encadena les dependències. |
| `data/raw/` | Dades d'origen, sense modificar (procedència i llicència a `DATOS.md`) |
| `data/processed/` | Entrades preparades a mà: noms dels llocs i dels punts de comptatge, equivalències de carrers, adreces fixes de les fitxes, transcripció del Pla, seguiment de les actuacions i registre d'incidències |
| `web/` | Plantilles, estils i JavaScript de la web estàtica (sense servidor d'aplicacions) i fonts tipogràfiques |
| `docs/` | Mètode, revisions metodològiques, llicència i privacitat del conjunt de dades, registre de canvis |
| `.claude/agents/` | Procediment de l'agent d'IA que proposa canvis en «El Pla, al dia» (una persona els revisa sempre abans de publicar-los) |

El mètode complet, en llenguatge planer i amb el detall tècnic, està en https://observatoribicivlc.org/metode/.

### Com es replica en una altra ciutat

El codi està pensat per a València, però l'esquema serveix per a qualsevol ciutat que publique els seus sinistres de trànsit. Cal adaptar:

1. **Sinistres** (`data/raw/siniestros/`): un fitxer amb un registre per sinistre, amb data, vehicles implicats i l'adreça o les coordenades. Si ja porten coordenades, es pot saltar la geocodificació (`scripts/geocodificar.py`).
2. **Carrerer**: eixos de carrer i portals numerats (per a situar les adreces) i la xarxa ciclista. Les regles per a llegir les adreces («C/ X cruce C/ Y», número de portal) estan en `scripts/geocodificar.py` i depenen del format de cada ciutat.
3. **Comptadors de bicis** (opcional): sense ells es perd la comparació amb el trànsit, però la resta funciona.
4. **El pla de seguretat viària**: el seguiment de les mesures està en la base SQLite (taules `plan_*`, amb el bolcat en text `data/processed/observatorio_plan.sql`) i s'edita amb propostes revisades (`scripts/aplicar_propuestas_plan.py`).
5. **Textos**: les pàgines estan en valencià i castellà (`scripts/sitio*.py`, `scripts/construir_sitio.py` i les plantilles de `web/`).

### Conjunt de dades

El conjunt de dades derivat no s'inclou: es regenera amb `make` a partir de les dades del portal (`make geocodificar` crea els sinistres amb coordenades, mètode i incertesa de la geocodificació).

### Llicències

- **Codi:** MIT (`LICENSE`), excepte les fonts tipogràfiques (OFL 1.1).
- **Documentació i dades pròpies o derivades** (sinistres situats en el mapa, llocs, seguiment del Pla): CC BY 4.0 (`LICENSE-docs`). Cita: «Observatori de la bici i el patinet de València. Dades de l'Ajuntament de València (CC BY 4.0), modificades per l'observatori».
- **Dades de tercers:** la seua llicència d'origen (vegeu més avall i `DATOS.md`).

### Atribucions

- **Font de les dades: Ajuntament de València – Dades Obertes** (https://opendata.vlci.valencia.es i geoportal https://geoportal.valencia.es), CC BY 4.0, descarregades el 30/10/2026. Conjunts: «Accidents de tràfic 2022-2025», vies, eixos de carrer, portals, carrils bici, reguladors semafòrics, espires de bici, intensitat per trams, xarxa de VMP i centres educatius. **Dades modificades**: s'hi afegeixen coordenades, mètode de geocodificació i marques de bici i VMP. L'Ajuntament de València no participa en aquest treball ni el respalda.
- **Intensitats de trànsit:** Ajuntament de València, Servei de Mobilitat (https://www.valencia.es/cas/movilidad/otras-descargas), reutilitzades segons l'avís legal de valencia.es, sense modificar.
- **Pla Director de Seguretat Viària de València 2026-2030:** Ajuntament de València (https://www.valencia.es/documents/d/guest/pdsv_valencia_2026-2030-pdf). Ací només n'hi ha la transcripció en text (`data/raw/pdsv/pdsv.txt`).
- **© Col·laboradors d'OpenStreetMap**, ODbL 1.0 (https://www.openstreetmap.org/copyright): semàfors (`data/raw/siniestros/osm_semaforos.json`) i verificació de la geocodificació amb Nominatim. No entren en el conjunt de dades CC BY.
- **Weather data by Open-Meteo.com** (https://open-meteo.com), CC BY 4.0: pluja horària i posta de sol.
- **Fonts tipogràfiques:** Public Sans i Barlow Semi Condensed, SIL Open Font License 1.1 (`web/proto/fuentes/*/OFL.txt`).

### Privacitat

Les dades no contenen atributs de persones. La coordenada és la del lloc del sinistre que consta en el parte, no un domicili. No intentes identificar ningú: la política d'ús del portal prohibeix reidentificar persones creuant aquestes dades amb altres fonts. Per a qualsevol dubte o retirada: hola@observatoribicivlc.org.

### Com es cita

Vegeu `CITATION.cff` (GitHub mostra el botó «Cite this repository»).

---

## Castellano

### Qué es

Un observatorio abierto que sigue el indicador de la acción 3.2.2 del Plan Director de Seguridad Vial de València 2026-2030 (reducir un 50 % los siniestros con bici o patinete en 2030) y muestra dónde se acumulan los siniestros. Hace público el seguimiento que el Plan prevé para uso interno.

- **Archivo y mapas:** siniestros de tráfico de 2022 a 2025 con bici y patinete (VMP) por separado, situados en el mapa a partir de la calle y el número que da el portal.
- **El Plan, al día:** estado de las actuaciones del Plan sobre bici y patinete, cada una con su fuente.
- **La meta:** la base es 2025. Sin los datos de 2026, el Plan aún no se puede evaluar.

Los lugares con más siniestros no son lugares de más riesgo: no hay datos de cuánta gente pasa por ellos en bici o en patinete. El riesgo del patinete por viaje no se puede medir con los contadores actuales, que no separan bicis y patinetes. Las limitaciones de los datos se explican en la página de método de la web.

### Cómo se reproduce

Todo (datos procesados, cifras, web y comprobaciones) se regenera a partir de los datos de origen de `data/raw/`. Hace falta Python 3.12, GNU Make y `flock` (util-linux, ya instalado en la mayoría de distribuciones Linux); para el PDF del informe de incidencias, también Google Chrome o Chromium.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # versiones fijadas
make geocodificar   # sitúa los siniestros en el mapa: data/processed/siniestros_geo.csv (solo la primera vez o cuando cambia el callejero)
make                # el análisis que esté desfasado + web + comprobaciones (la primera vez, unos minutos)
```

Después, para trabajar:

- `make web`: solo la web, con el análisis que ya haya (segundos). Necesita que antes se haya hecho `make geocodificar` y `make` (o `make analisis`).
- `make comprobar`: comprueba los datos y la web (OK / AVISO / ERROR).
- `make sqlite`: la base `data/processed/observatorio.sqlite`, de la que lee la web. El seguimiento del Plan se guarda en texto en `data/processed/observatorio_plan.sql`.
- `make incidencias`: vuelve a verificar los errores encontrados en los datos del Ajuntament y escribe el informe (`.md` y, con Chrome, `.pdf`).

La web queda en `web/proto/build/`. Para verla: `python3 -m http.server 8000 --directory web/proto/build` y abrir http://localhost:8000/.

`make` regenera todos los ficheros derivados (`data/processed/siniestros_geo.csv`, `outputs/`, `web/proto/datos/`, `web/proto/build/` y la base SQLite). Ninguno de ellos está en el repositorio.

### Estructura

| Carpeta | Contenido |
|---|---|
| `scripts/` | Un script por paso: geocodificación, lugares, cribado con contadores, seguimiento del indicador, exportación, web, fichas y comprobaciones. El `Makefile` encadena las dependencias. |
| `data/raw/` | Datos de origen, sin modificar (procedencia y licencia en `DATOS.md`) |
| `data/processed/` | Entradas preparadas a mano: nombres de los lugares y de los puntos de conteo, equivalencias de calles, direcciones fijas de las fichas, transcripción del Plan, seguimiento de las actuaciones y registro de incidencias |
| `web/` | Plantillas, estilos y JavaScript de la web estática (sin servidor de aplicaciones) y fuentes tipográficas |
| `docs/` | Método, revisiones metodológicas, licencia y privacidad del conjunto de datos, registro de cambios |
| `.claude/agents/` | Procedimiento del agente de IA que propone cambios en «El Plan, al día» (una persona los revisa siempre antes de publicarlos) |

El método completo, en lenguaje llano y con el detalle técnico, está en https://observatoribicivlc.org/metode/.

### Cómo replicarlo en otra ciudad

El código está pensado para València, pero el esquema sirve para cualquier ciudad que publique sus siniestros de tráfico. Hay que adaptar:

1. **Siniestros** (`data/raw/siniestros/`): un fichero con un registro por siniestro, con fecha, vehículos implicados y la dirección o las coordenadas. Si ya vienen con coordenadas, la geocodificación (`scripts/geocodificar.py`) se puede saltar.
2. **Callejero**: ejes de calle y portales numerados (para situar las direcciones) y la red ciclista. Las reglas para leer las direcciones («C/ X cruce C/ Y», número de portal) están en `scripts/geocodificar.py` y dependen del formato de cada ciudad.
3. **Contadores de bicis** (opcional): sin ellos se pierde la comparación con el tráfico, pero el resto funciona.
4. **El plan de seguridad vial**: el seguimiento de las medidas está en la base SQLite (tablas `plan_*`, con el volcado en texto `data/processed/observatorio_plan.sql`) y se edita con propuestas revisadas (`scripts/aplicar_propuestas_plan.py`).
5. **Textos**: las páginas están en valenciano y castellano (`scripts/sitio*.py`, `scripts/construir_sitio.py` y las plantillas de `web/`).

### Conjunto de datos

El conjunto de datos derivado no se incluye: se regenera con `make` a partir de los datos del portal (`make geocodificar` crea los siniestros con coordenadas, método e incertidumbre de la geocodificación).

### Licencias

- **Código:** MIT (`LICENSE`), salvo las fuentes tipográficas (OFL 1.1).
- **Documentación y datos propios o derivados** (siniestros situados en el mapa, lugares, seguimiento del Plan): CC BY 4.0 (`LICENSE-docs`). Cita: «Observatori de la bici i el patinet de València. Datos del Ajuntament de València (CC BY 4.0), modificados por el observatorio».
- **Datos de terceros:** su licencia de origen (ver abajo y `DATOS.md`).

### Atribuciones

- **Fuente de los datos: Ajuntament de València – Dades Obertes** (https://opendata.vlci.valencia.es y geoportal https://geoportal.valencia.es), CC BY 4.0, descargados el 30/10/2026. Conjuntos: «Accidentes de tráfico 2022-2025», vías, ejes de calle, portales, carriles bici, reguladores semafóricos, espiras de bici, intensidad por tramos, red de VMP y centros educativos. **Datos modificados**: se añaden coordenadas, método de geocodificación y marcas de bici y VMP. El Ajuntament de València no participa en este trabajo ni lo respalda.
- **Intensidades de tráfico:** Ajuntament de València, Servicio de Movilidad (https://www.valencia.es/cas/movilidad/otras-descargas), reutilizadas según el aviso legal de valencia.es, sin modificar.
- **Plan Director de Seguridad Vial de València 2026-2030:** Ajuntament de València (https://www.valencia.es/documents/d/guest/pdsv_valencia_2026-2030-pdf). Aquí solo está su transcripción en texto (`data/raw/pdsv/pdsv.txt`).
- **© Colaboradores de OpenStreetMap**, ODbL 1.0 (https://www.openstreetmap.org/copyright): semáforos (`data/raw/siniestros/osm_semaforos.json`) y verificación de la geocodificación con Nominatim. No entran en el conjunto de datos CC BY.
- **Weather data by Open-Meteo.com** (https://open-meteo.com), CC BY 4.0: lluvia horaria y puesta de sol.
- **Fuentes tipográficas:** Public Sans y Barlow Semi Condensed, SIL Open Font License 1.1 (`web/proto/fuentes/*/OFL.txt`).

### Privacidad

Los datos no contienen atributos de personas. La coordenada es la del lugar del siniestro que consta en el parte, no un domicilio. No intentes identificar a nadie: la política de uso del portal prohíbe reidentificar personas cruzando estos datos con otras fuentes. Para cualquier duda o retirada: hola@observatoribicivlc.org.

### Cómo citar

Ver `CITATION.cff` (GitHub muestra el botón «Cite this repository»).
