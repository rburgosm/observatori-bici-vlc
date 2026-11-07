# Regenera el análisis y la web desde los datos de data/raw/, rehaciendo solo lo que ha cambiado.
# Uso: make               (análisis que esté desfasado + web + comprobar)
#      make web           (solo la web, con los outputs/ que haya: nunca relanza el análisis; segundos)
#      make comprobar     (comprueba datos nuevos y web: OK / AVISO / ERROR)
#      make analisis      (solo el análisis desfasado)
#      make plan          (transcripción del Plan Director: data/processed/pdsv_*.csv)
#      make sqlite        (base data/processed/observatorio.sqlite: de ella leen exportar_web.py, fichas, comprobar y bocetos)
#      make geocodificar  (lento y cambia todo: solo a propósito; ver siniestros_geo.csv abajo)
#      make incidencias   (re-verifica las incidencias de los datos del Ajuntament e informe para enviarlo, en .md y .pdf; no entra en make web)
#      make capturas ETIQUETA=v1-…  (capturas de la web servida en localhost:8000, en capturas/; no entra en make ni make web)
#      make -B web        (fuerza exportar, montar y tarjetas aunque nada haya cambiado; lo usa deploy/deploy.sh)
# Cada script es una regla cuyo objetivo son sus salidas reales y cuyos prerequisitos son el script, los módulos que
# importa y los ficheros que lee. Las descargas (fetch_callejero.py, intensidades) no tienen regla: nunca se disparan.
# Candado: dos make a la vez (sesiones o agentes en paralelo) chocaban en la SQLite («disk I/O error», «readonly
# database») y en build/. El make de fuera solo toma el candado (flock) y se relanza a sí mismo con OBS_CANDADO=1;
# un segundo make espera a que acabe el primero. Para saltarlo a propósito: OBS_CANDADO=1 make …
ifndef OBS_CANDADO
.PHONY: _candado
_candado:
	@OBS_CANDADO=1 flock $(CURDIR)/.make.lock $(MAKE) --no-print-directory $(MAKECMDGOALS)
$(filter-out _candado,$(MAKECMDGOALS)): _candado
	@:
else
PY = .venv/bin/python -I
$(shell mkdir -p outputs)   # en un clon nuevo no existe (no va al repositorio)
# límite de hilos de BLAS: sin esto, statsmodels ocupa todos los núcleos
# (vmp_vs_bici.py lo baja a 1 por proceso: hace sus dos ajustes en 2 procesos)
export OMP_NUM_THREADS = 2
export OPENBLAS_NUM_THREADS = 2
export MKL_NUM_THREADS = 2

.PHONY: all analisis web plan sqlite comprobar geocodificar incidencias capturas
all: analisis web comprobar

# ---------- entradas ----------
SIN = data/raw/siniestros
GEO = data/processed/siniestros_geo.csv
GEO_IN = scripts/geocodificar.py $(SIN)/siniestros-de-trafico-2022-2025.json $(SIN)/vias.json $(SIN)/ejes.geojson \
         $(SIN)/portales.geojson data/processed/equivalencias_calles.csv
# scripts/lugares.py: siniestros(), unidades y nombres; importa geocodificar.py (índice nombre -> codvia) al nombrar
LUG = scripts/lugares.py $(GEO_IN)
IMD_BICI = $(wildcard data/raw/intensidades/carril_bici_*.ods)
IMD_VEH = $(wildcard data/raw/intensidades/imds_vehiculos_*.ods)
PDSV = data/processed/pdsv_indicadores.csv data/processed/pdsv_lugares.csv

# ---------- salidas del análisis ----------
LUGARES = outputs/lugares_nudos.csv outputs/lugares_nudos_resumen.json
CRIBADO = outputs/cribado_eb_vmp_o_bici.csv outputs/cribado_eb_bici.csv outputs/cribado_eb_vmp.csv outputs/cribado_eb_coef.json
VVB = outputs/vmp_vs_bici.csv
VVBC = outputs/vmp_vs_bici_condicionado.csv
ANALISIS = $(LUGARES) $(CRIBADO) $(VVB) $(VVBC)

# ---------- web ----------
W = web/proto
DATOS = $(W)/datos/observatori.js $(W)/datos/relato.js $(W)/datos/metode.js $(W)/datos/pla.js
PAGINAS = observatori informe metode cambios pla
HTML = $(PAGINAS:%=$(W)/build/%.html)
OG = $(foreach p,$(PAGINAS),$(W)/build/og/$(p).png $(W)/build/og/$(p)_es.png)
SQLITE = data/processed/observatorio.sqlite
FICHAS = $(W)/build/.fichas
# web pública (scripts/construir_sitio.py): /, /mapa/, /ajuntament/, /informe/, /informe/2025/, /dades/, /lloc/, /carrer/
SITIO = $(W)/build/.sitio
SITIO_IN = scripts/sitio.py scripts/sitio_textos_plan.py scripts/sitio_dades.py scripts/nombres.py data/processed/nombres_puntos_conteo.csv $(SIN)/vias.json $(wildcard web/sitio/*)

analisis: $(ANALISIS)
web: $(HTML) $(OG) $(FICHAS) $(SITIO)
plan: $(PDSV)
sqlite: $(SQLITE)

# `make web` / `make comprobar` solos: el análisis, la geocodificación y el Plan NO se rehacen. Sus ficheros son
# entradas fijas; si alguno falta, se para diciendo qué ejecutar (el test -e hace que `make -B web` no los toque).
SOLO_WEB := $(if $(MAKECMDGOALS),$(if $(filter-out web comprobar sqlite,$(MAKECMDGOALS)),,1),)
ifeq ($(SOLO_WEB),1)
$(ANALISIS):
	@test -e $@ || { echo "falta $@: ejecutar 'make analisis' (o 'make $@') antes de 'make web'" >&2; exit 1; }
$(GEO):
	@test -e $@ || { echo "falta $@: ejecutar 'make geocodificar'" >&2; exit 1; }
$(PDSV):
	@test -e $@ || { echo "falta $@: ejecutar 'make plan'" >&2; exit 1; }
else

# siniestros_geo.csv: el geocodificador NO se lanza solo (es lento y cambia todo lo de abajo). Si sus entradas son más
# nuevas, make se para y avisa; se rehace a propósito con `make geocodificar`, o con `touch` si el cambio no le afecta.
$(GEO): $(GEO_IN)
	@echo "$@ es anterior a: $?" >&2; \
	 echo "  rehacerlo a propósito con 'make geocodificar' (lento; cambia todo el análisis)," >&2; \
	 echo "  o 'touch $@' si el cambio no afecta a la geocodificación." >&2; exit 1

# lugares (nudos de cruce y tramos de calle): estabilidad, persistencia y pista; los usa la web (exportar_web.py)
# nombres_lugares.csv: nombres congelados (lugares.py, congelar); lo amplía lugares_nudos.py (antes de escribir sus
# salidas, así que no se queda desfasado) y se edita a mano para cambiar un nombre
$(LUGARES) &: scripts/lugares_nudos.py $(LUG) $(GEO) data/processed/nombres_lugares.csv
	$(PY) scripts/lugares_nudos.py

$(CRIBADO) &: scripts/cribado_eb.py $(LUG) $(GEO) $(IMD_BICI) $(IMD_VEH) $(SIN)/espiras_bici.geojson \
              $(SIN)/intensidad_tramos.geojson $(SIN)/reguladores_semaforos.geojson $(SIN)/carriles_bici.geojson
	$(PY) scripts/cribado_eb.py

# el más lento (dos modelos mixtos variacionales, en paralelo)
$(VVB): scripts/vmp_vs_bici.py $(LUG) $(GEO) $(SIN)/carriles_bici.geojson
	$(PY) scripts/vmp_vs_bici.py

$(VVBC): scripts/vmp_vs_bici_condicionado.py $(LUG) $(GEO) $(SIN)/meteo_openmeteo_2022_2025.json
	$(PY) scripts/vmp_vs_bici_condicionado.py

$(PDSV) &: scripts/transcribir_pdsv.py data/raw/pdsv/pdsv.txt
	$(PY) scripts/transcribir_pdsv.py
endif

geocodificar:
	$(PY) scripts/geocodificar.py

# persistencia_puntos.py (rejilla de 100 m) queda como histórico, fuera de make: lo sustituye lugares_nudos.py

# datos de la web (exportar_web.py): siniestros, lugares y Plan de la base ($(SQLITE), leída con scripts/bd.py); no rehace
# el análisis en `make web`
$(DATOS) $(W)/datos/colaboran.json &: scripts/exportar_web.py scripts/bd.py scripts/construir_sqlite.py scripts/lugares.py \
            scripts/meta.py $(SQLITE) $(SIN)/ejes.geojson \
            outputs/cribado_eb_vmp_o_bici.csv outputs/cribado_eb_coef.json $(PDSV) $(IMD_BICI) $(IMD_VEH) \
            $(SIN)/carriles_bici.geojson $(SIN)/reguladores_semaforos.geojson $(SIN)/osm_semaforos.json \
            $(SIN)/espiras_bici.geojson data/processed/incidencias_datos.csv $(wildcard data/processed/plan_seguimiento_propuestas.csv) \
            data/processed/colaboran.csv requirements.txt
	$(PY) scripts/exportar_web.py

# páginas (construir_web.py): plantillas + datos + comun/ + registro de cambios; escribe también datos/cambios.js y
# build/datos/ (datos de cada página con nombre versionado por contenido y la descarga estable <página>.json)
# observatori.html e informe.html cargan el índice de las fichas (buscador → <clase>/<slug>/), con su SRI
$(HTML) $(W)/datos/cambios.js &: scripts/construir_web.py $(PAGINAS:%=$(W)/%.plantilla.html) $(DATOS) $(W)/datos/colaboran.json \
            $(wildcard $(W)/comun/*) docs/cambios.csv $(SIN)/siniestros-de-trafico-2022-2025.json $(W)/datos/fichas_indice.sri
	$(PY) scripts/construir_web.py

# imágenes para compartir (tarjetas_og.py), de los datos de las cuatro páginas
$(OG) &: scripts/tarjetas_og.py $(DATOS) $(W)/datos/cambios.js $(wildcard $(W)/fuentes/*/*)
	$(PY) scripts/tarjetas_og.py

# base de datos (scripts/construir_sqlite.py): lo ya calculado, sin rehacer análisis; congela los slugs de las fichas
# (data/processed/fichas_slugs.csv). `make sqlite` solo la base. Es la FUENTE DE VERDAD del seguimiento del Plan: lo carga
# de su volcado en git (data/processed/observatorio_plan.sql) y reescribe su exportación plan_seguimiento.csv; los cambios
# del Plan entran con scripts/aplicar_propuestas_plan.py (escribe en la base, el volcado y el CSV). Se para si el CSV se
# editó a mano o si la base tiene cambios sin volcar (docs/plan_seguimiento.md, sec. 7).
$(SQLITE) &: scripts/construir_sqlite.py $(LUG) $(GEO) $(LUGARES) data/processed/nombres_lugares.csv \
            $(wildcard data/processed/observatorio_plan.sql) docs/cambios.csv
	$(PY) scripts/construir_sqlite.py
# fichas estáticas por lugar y calle (scripts/fichas.py): build/lloc/<slug>/ y build/carrer/<slug>/; solo reescribe lo que
# cambia. Marca: build/.fichas (oculta: el deploy no sube ficheros que empiezan por punto)
$(FICHAS): scripts/fichas.py $(SQLITE) $(wildcard $(W)/fichas/*) $(SIN)/ejes.geojson $(W)/observatori.plantilla.html $(SITIO_IN) \
           $(W)/datos/pla.js $(W)/datos/observatori.js
	$(PY) scripts/fichas.py && touch $@
# el índice del buscador lo escribe fichas.py (solo si cambia)
$(W)/datos/fichas_indice.sri: $(FICHAS) ;
# web pública: después de las fichas (usa su índice para el buscador y enlaza las fichas); hereda la lógica del mapa y del
# método de observatori.plantilla.html y metode.plantilla.html. Marca: build/.sitio
$(SITIO): scripts/construir_sitio.py $(SITIO_IN) $(FICHAS) $(DATOS) $(SQLITE) $(SIN)/ejes.geojson $(W)/observatori.plantilla.html \
          $(W)/metode.plantilla.html $(W)/comun/carga.js $(W)/comun/tema.js docs/cambios.csv
	$(PY) scripts/construir_sitio.py && touch $@

comprobar:
	$(PY) scripts/comprobar.py
	$(PY) scripts/comprobar_sitio.py

# incidencias en los datos del Ajuntament (scripts/incidencias.py): re-verifica las comprobables contra data/raw/ y escribe
# el informe para enviar. Registro a mano: data/processed/incidencias_datos.csv (la web lo lee vía exportar_web.py).
INC_OUT = outputs/incidencias_verificacion.csv docs/incidencias_para_el_ajuntament.md
INC_PDF = docs/incidencias_para_el_ajuntament.pdf
incidencias: $(INC_OUT) $(INC_PDF)
# PDF para enviarlo (scripts/incidencias_pdf.py): markdown (python3 del sistema, no .venv) + Chrome sin pantalla
$(INC_PDF): scripts/incidencias_pdf.py docs/incidencias_para_el_ajuntament.md $(wildcard $(W)/fuentes/*/*.ttf)
	python3 -I scripts/incidencias_pdf.py
$(INC_OUT) &: scripts/incidencias.py data/processed/incidencias_datos.csv $(GEO_IN) $(IMD_BICI) $(IMD_VEH) \
              $(wildcard $(SIN)/vmp_tipo_*.geojson) $(SIN)/intensidad_tramos.geojson $(SIN)/obras_ejecutadas.csv \
              $(SIN)/espiras_bici.geojson $(SIN)/ckan_siniestros_package.json $(SIN)/portales_atributos.json
	$(PY) scripts/incidencias.py

# capturas de la web para seguir su evolución (scripts/capturas.py): python3 del sistema + Chrome sin pantalla, contra la
# web servida en localhost:8000 (cd web/proto/build && python3 -m http.server 8000). Salida en capturas/ (fuera de git),
# con capturas/index.html para comparar versiones. No rehace la web: si hace falta, `make web` antes.
capturas:
	@test -n "$(ETIQUETA)" || { echo "uso: make capturas ETIQUETA=v1-descripcion" >&2; exit 1; }
	python3 -I scripts/capturas.py "$(ETIQUETA)"
endif
