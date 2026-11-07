"""Genera data/processed/pdsv_indicadores.csv y pdsv_lugares.csv (transcripción manual del PDSV 2026-2030)."""
import csv, re, sys
from pathlib import Path
BASE = str(Path(__file__).resolve().parents[1])
txt = open(f"{BASE}/data/raw/pdsv/pdsv.txt", encoding="utf-8").read().split("\n")
norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
lines = [norm(l) for l in txt]
used = {}
def find(key, after=0):
    k = norm(key)
    for i in range(after, len(lines)):
        if k in lines[i]:
            return i + 1
    return None
def ref(pdf, key, after=2850):
    ln = find(key, after) if key else None
    s = f"PDF p.{pdf} (pág. {pdf-3})"
    return s + (f"; txt l.{ln}" if ln else "")

E1="1 Personas formadas y capaces"; E2="2 Tolerancia cero"; E3="3 Vías seguras"; E4="4 Vehículos seguros"
E5="5 Respuesta al siniestro"; E6="6 Datos y conocimiento"; E7="7 Administraciones y organizaciones seguras"
NO_GESTION="no: dato de gestión municipal (actividad interna), no está en datos abiertos"
# (eje, accion, tipo, indicador, unidad, formula, base, meta, fuente, periodicidad, calculable, motivo, pdf)
R = [
(E1,"1.1.1 Acciones educativas en centros educativos","Actividad","Sesiones educativas en centros escolares","Nº sesiones","Nº actividades realizadas","—","90/año","Policía Local","Anual","no",NO_GESTION,61),
(E1,"1.1.1","Resultado","Centros educativos participantes","%","(Centros participantes / total centros) ×100","—","95%","Educación","Anual","no",NO_GESTION,61),
(E1,"1.1.1","Resultado","Alumnos formados en seguridad vial","Nº alumnos","Nº participantes en programas","—","8.000","Educación","Anual","no",NO_GESTION,61),
(E1,"1.1.1","Impacto","Mejora del nivel de concienciación en seguridad vial del alumnado","%","Evaluación antes/después","—","90%","Educación","Anual","no","no: requiere encuesta propia del programa",61),
(E1,"1.1.2 Formación dirigida a colectivos vulnerables","Actividad","Acciones formativas dirigidas a colectivos vulnerables","Nº acciones","Nº actividades realizadas","—","40","Policía Local","Anual","no",NO_GESTION,61),
(E1,"1.1.2","Resultado","Personas vulnerables formadas","Nº personas","Nº participantes","—","2.000","Policía Local","Anual","no",NO_GESTION,61),
(E1,"1.1.2","Impacto","Reducción de siniestros en colectivos vulnerables","%","Comparación anual","—","-40%","Policía Local","Anual","parcial","sí para usuarios vulnerables por modo (peatón, bici, VMP, moto, ciclomotor en UNIDADES_IMPLICADAS); no para mayores o discapacidad (sin edad). Año base no fijado",61),
(E1,"1.1.3 Centro de Educación Vial de Viveros","Actividad","Visitas escolares al Centro de Educación Vial","Nº visitas","Nº visitas organizadas","—","150","Policía Local","Anual","no",NO_GESTION,61),
(E1,"1.1.3","Resultado","Escolares participantes en actividades del centro","Nº alumnos","Nº participantes","—","5.000","Policía Local","Anual","no",NO_GESTION,61),
(E1,"1.1.3","Resultado","Centros educativos visitantes","%","(Centros visitantes / total centros) ×100","—","85%","Policía Local y Educación","Anual","no",NO_GESTION,61),
(E1,"1.1.3","Impacto","Mejora de conductas seguras en alumnado","%","Evaluación práctica en circuito","—","90%","Policía Local","Anual","no","no: evaluación interna",61),
(E1,"1.2.1 Campañas de concienciación","Actividad","Campañas de concienciación realizadas","Nº campañas","Nº campañas ejecutadas","—","8","Comunicación","Anual","no",NO_GESTION,62),
(E1,"1.2.1","Resultado","Impactos en redes sociales","Nº impactos","Nº visualizaciones","—","200.000","SERTIC","Trimestral","no",NO_GESTION,62),
(E1,"1.2.2 Campañas de divulgación","Actividad","Acciones divulgativas realizadas","Nº acciones","Nº charlas, jornadas, eventos","—","40","Comunicación","Anual","no",NO_GESTION,62),
(E1,"1.2.2","Resultado","Participantes en acciones divulgativas","Nº personas","Nº asistentes","—","3.000","Comunicación","Anual","no",NO_GESTION,62),
(E1,"1.2.3 Colaboración con asociaciones","Actividad","Convenios o colaboraciones con asociaciones","Nº convenios","Nº acuerdos firmados","—","15","Alcaldía","Anual","no",NO_GESTION,62),
(E1,"1.2.3","Resultado","Actividades conjuntas realizadas","Nº actividades","Nº acciones realizadas","—","20","Alcaldía","Anual","no",NO_GESTION,62),
(E1,"1.2.4 Difusión del Plan en medios y redes","Actividad","Publicaciones en medios y redes sociales","Nº publicaciones","Nº contenidos difundidos","—","150","Comunicación","Trimestral","no",NO_GESTION,62),
(E1,"1.2.4","Resultado","Impactos en redes sociales","Nº impactos","Nº visualizaciones","—","600.000","SERTIC","Trimestral","no",NO_GESTION,62),
(E1,"1.2.4 Transparencia y web municipal de seguridad vial","Actividad","Creación del portal web de seguridad vial","Documento","Existencia portal","—","Portal operativo","Movilidad","Puntual","no","verificable (sí/no) mirando la web; no se calcula con datos",62),
(E1,"1.2.4 Transparencia y web municipal de seguridad vial","Resultado","Actualizaciones de contenidos de seguridad vial","Nº actualizaciones","Nº publicaciones","—","20","Movilidad y SERTIC","Anual","no","verificable contando publicaciones; no se calcula con datos",62),
(E1,"1.2.4 Transparencia y web municipal de seguridad vial","Resultado","Visitas a la sección web de seguridad vial","Nº visitas","Nº accesos","—","40.000","SERTIC","Anual","no",NO_GESTION,62),
(E1,"1.3.1 Promoción de movilidad peatonal y ciclista","Actividad","Campañas de promoción de movilidad sostenible","Nº campañas","Nº campañas realizadas","—","6","Movilidad","Anual","no",NO_GESTION,63),
(E1,"1.3.1","Resultado","Participantes en campañas","Nº personas","Nº participantes","—","12.000","Comunicación","Anual","no",NO_GESTION,63),
(E1,"1.3.1","Resultado","Plazas de aparca-bici","Nº plazas","Nº plazas de aparca bicis","22.638","25.000","Urbanismo","Anual","parcial","posible si el portal publica la capa de aparcabicis (no descargada); no está en nuestros datos",63),
(E1,"1.3.1","Resultado","Paneles contadores de intensidad en infraestructura ciclista","Nº paneles","Nº paneles","3","9","Urbanismo","Anual","no","los paneles visibles no se distinguen en la capa 225 de espiras; no calculable",63),
(E1,"1.3.1","Impacto","Incremento de desplazamientos a pie","% viajes","Encuesta movilidad","—","40%","Movilidad","Anual","no","requiere encuesta de movilidad",63),
(E1,"1.3.1","Impacto","Incremento de desplazamientos en vehículo privado","% viajes","Aforos en red viaria principal","+1,3%","-5%","Movilidad","Anual","sí","con imds_vehiculos_2025.ods y evolucion_imd_mensual_2019-sep2026.xlsx (web de Movilidad; complemento, no portal). Hay que fijar qué aforos son la red principal",63),
(E1,"1.3.1","Impacto","Incremento de desplazamientos en bici/VMP","% viajes","Aforos en principales carriles bici","+3,4%","+5%","Movilidad","Anual","sí","con carril_bici_2022..2025.ods (IMD laborables por espira) y capa 225. Los aforos no separan bici de VMP. Hay que fijar qué carriles son los principales",63),
(E1,"1.3.2 Transporte público entre jóvenes","Actividad","Campañas informativas en centros de ocio","Nº campañas","Nº campañas realizadas","—","5","Área juventud","Anual","no",NO_GESTION,63),
(E1,"1.3.2","Resultado","Jóvenes alcanzados por las campañas","Nº personas","Nº jóvenes participantes","—","10.000","Comunicación","Anual","no",NO_GESTION,63),
(E1,"1.3.2","Resultado","km de carril EMT-Taxi","km","Km de carril EMT-Taxi","106 km","150","Urbanismo","Anual","no","fuera de alcance (sin capa descargada)",63),
(E1,"1.3.2","Resultado","km de carril EMT-Taxi segregado","km","Km de carril EMT-Taxi segregado","18,4 km","25","Urbanismo","Anual","no","fuera de alcance (sin capa descargada)",63),
(E1,"1.3.2","Impacto","Incremento uso transporte público en población joven","% viajes","Encuesta movilidad","—","40%","Movilidad","Anual","no","requiere encuesta",63),
(E2,"2.1 Reforzar y segmentar los controles policiales","Actividad","Controles policiales de seguridad vial realizados","Nº controles","Nº controles ejecutados por Policía Local","—","—","Policía Local","Anual","no",NO_GESTION+" (detalle en Plan Vector)",64),
(E2,"2.1","Actividad","Campañas específicas de control (velocidad, alcohol, distracciones, etc.)","Nº campañas","Nº campañas policiales realizadas","—","—","Policía Local","Anual","no",NO_GESTION,64),
(E2,"2.1","Actividad","Controles específicos en zonas de alto riesgo","Nº controles","Nº controles realizados en puntos de siniestralidad","—","—","Policía Local","Anual","no",NO_GESTION,64),
(E2,"2.1","Resultado","Conductores sometidos a controles de alcohol y drogas","Nº pruebas","Nº pruebas realizadas","—","—","Policía Local","Anual","no",NO_GESTION,64),
(E2,"2.1","Resultado","Infracciones detectadas en controles","Nº infracciones","Nº sanciones registradas","—","—","Policía Local","Anual","no",NO_GESTION,64),
(E2,"2.1","Impacto","Reducción de siniestros asociados a comportamientos de riesgo","%","Comparación anual","—","—","Policía Local","Anual","parcial","con FACTORES CONCURRENTES (alcohol, drogas, velocidad inadecuada, distracción, temeraria). Sin meta numérica. Campo con huecos (vacío o NULL en ~45 % de filas)",64),
(E2,"2.2 Nuevas tecnologías para análisis, control y vigilancia","Actividad","Elaboración del plan municipal de implantación tecnológica","Documento","Existencia del plan","No existente","Plan aprobado","Movilidad","Puntual","no","verificable (sí/no)",64),
(E2,"2.2","Resultado","Dispositivos tecnológicos de control implantados. Radares informativos","Nº radares","Nº radares informativos","7","20","Movilidad","Anual","no",NO_GESTION,64),
(E2,"2.2","Resultado","Dispositivos tecnológicos de control implantados. Cámaras CCTV","Nº cámaras","Nº cámaras CCTV","819","900","Movilidad","Anual","no",NO_GESTION,64),
(E2,"2.2","Resultado","Puntos o zonas monitorizadas","Nº puntos","Nº intersecciones o tramos monitorizados","—","50","Movilidad y Policía Local","Anual","no",NO_GESTION,64),
(E2,"2.2","Impacto","Reducción de infracciones en zonas monitorizadas","%","Comparación anual","—","-30%","Policía Local","Anual","no","no hay datos abiertos de infracciones",64),
(E3,"3.1 Diseño seguro en proyectos de construcción","Actividad","Difusión de estándares de diseño seguro a equipos redactores","Nº equipos","Nº equipos informados/formados","—","100% equipos","Movilidad","Anual","no",NO_GESTION,65),
(E3,"3.2.1 Seguridad peatonal","Actividad","Pasos de peatones intervenidos","Nº pasos","Nº actuaciones ejecutadas","—","120/año","Urbanismo","Anual","no",NO_GESTION,65),
(E3,"3.2.1","Resultado","Nuevos pasos en grandes avenidas","Nº pasos","Nº nuevos pasos","—","25","Urbanismo","Anual","no",NO_GESTION,65),
(E3,"3.2.1","Impacto","Reducción de atropellos","%","Comparación anual","—","-50%","Policía Local","Anual","sí","siniestros con PEATÓN en UNIDADES_IMPLICADAS (todos los años) o TIPO ACCIDENTE = atropello (fiable solo desde 2025). Año base no fijado",65),
(E3,"3.2.2 Seguridad ciclista y de usuarios VMP","Actividad","Km de carriles bici construidos","km","Longitud anual ejecutada","225 km","250 km","Urbanismo","Anual","parcial","longitud de la capa 189 (carriles_bici.geojson) con geopandas en EPSG:25830; hay que descargarla cada año y comprobar que 225 km se refiere a la misma red",65),
(E3,"3.2.2","Actividad","Km de ciclocalles","km","Longitud ejecutada","18 km","75 km","Urbanismo","Anual","parcial","solo si la capa 189 distingue la tipología ciclocalle (por comprobar)",65),
(E3,"3.2.2","Actividad","Alfombras rojas señalizadas en carriles bici","Nº alfombras","Nº alfombras ejecutadas","786","1000","Urbanismo","Anual","no",NO_GESTION,65),
(E3,"3.2.2","Actividad","Pasos de peatones sobre carril bici de acceso a contenedores","Nº pasos","Nº pasos de peatones de acceso a contenedores sobre carril bici","3","100","Urbanismo","Anual","no",NO_GESTION,65),
(E3,"3.2.2","Resultado","Actuaciones del Plan Director de la Bicicleta ejecutadas","%","(Actuaciones ejecutadas / previstas) ×100","—","100%","Movilidad","Anual","no",NO_GESTION,65),
(E3,"3.2.2","Impacto","Reducción de siniestros con ciclistas/VMP","%","Comparación anual","—","-50%","Policía Local","Anual","sí","siniestros con BICICLETA o VMP en UNIDADES_IMPLICADAS (sin duplicar). Cuadra casi exacto con las cifras del Plan. El Plan no fija año base: proponemos 2024 (como el objetivo global) y mostrar también 2025",65),
(E3,"3.2.3 Entornos escolares","Resultado","Rutas escolares seguras","Nº rutas","Nº caminos escolares","117","100","Educación","Anual","no",NO_GESTION+" (ojo: la meta es menor que la base)",65),
(E3,"3.2.3","Resultado","Superficie recuperada para espacio peatonal","m2","m2 espacio recuperado","3.000 m2","5.000","Urbanismo","Anual","no",NO_GESTION,65),
(E3,"3.2.3","Impacto","Reducción de siniestros en entorno escolar","%","Comparación anual","—","-60%","Policía Local","Anual","parcial","con siniestros_geo.csv y centros_educativos.geojson (buffer con geopandas). El Plan no define el radio de 'entorno escolar' ni el año base. 13 % de siniestros sin geocodificar",65),
(E3,"3.3 Conservación de la red viaria","Actividad","Evaluaciones del estado de la red viaria","Nº evaluaciones","Nº diagnósticos realizados","—","Diagnóstico anual","Urbanismo","Anual","no",NO_GESTION,66),
(E3,"3.3","Actividad","Estudios de seguridad vial en distribución urbana de mercancías (DUM)","Nº estudios","Nº análisis realizados","—","6","Movilidad","Anual","no",NO_GESTION,66),
(E3,"3.3","Resultado","Plazas de estacionamiento para motos","Nº plazas","Nº plazas de estacionamiento para motos","14.766","20.000","Urbanismo","Anual","no",NO_GESTION,66),
(E3,"3.3","Resultado","Plazas carga descarga","Nº plazas","Nº plazas carga/descarga","2.851","3.500","Urbanismo","Anual","no",NO_GESTION,66),
(E3,"3.3","Impacto","Reducción siniestros relacionados con estado de la vía","%","Comparación anual","—","-40%","Policía Local","Anual","parcial","FACTORES CONCURRENTES = 'ESTADO O CONDICIÓN DE LA VÍA' (y 'OBSTACULO EN CALZADA'). Campo con huecos; año base no fijado",66),
(E3,"3.4 Accesibilidad universal y seguridad vial","Actividad","Jornadas con asociaciones de discapacidad","Nº jornadas","Nº jornadas realizadas","—","10","Movilidad","Anual","no",NO_GESTION,66),
(E3,"3.4","Resultado","Pasos con descontadores semafóricos","Nº dispositivos","Nº de dispositivos instalados","1.198","1.500","Movilidad","Anual","no",NO_GESTION,66),
(E3,"3.4","Resultado","Pasos con avisador acústico para invidentes","Nº dispositivos","Nº de dispositivos instalados","1.830","2.500","Movilidad","Anual","no",NO_GESTION,66),
(E3,"3.4","Resultado","Plazas PMR","Nº plazas","Nº de plazas para PMR","3.080","4.000","Urbanismo","Anual","no",NO_GESTION,66),
(E3,"3.4","Resultado","Paradas accesibles mediante pavimento podotáctil","%","% (paradas adecuadas / total de paradas)","90%","100%","Urbanismo","Anual","no",NO_GESTION,66),
(E3,"3.4","Impacto","Reducción siniestros con personas mayores y con discapacidad","%","Comparación anual","—","-40%","Policía Local","Anual","no","el dataset abierto no tiene edad ni discapacidad",66),
(E3,"3.5 Adaptación de calles y señalización al Reglamento","Resultado","Calles 20 y residenciales","%","(km vías ≤30 / km red urbana) ×100 [sic]","3%","10%","Urbanismo","Anual","parcial","solo si se descarga una capa de límites de velocidad o zonas 20/30 del geoportal (no la tenemos). La fórmula del Plan repite '≤30' (errata probable)",67),
(E3,"3.5","Resultado","Áreas recuperadas para uso peatonal","km2","km2 áreas recuperadas","96","150","Urbanismo","Anual","no","fuera de alcance; la unidad (km2) parece errata",67),
(E3,"3.5","Resultado","Calles 30","%","(km vías ≤30 / km red urbana) ×100","64%","95%","Urbanismo","Anual","parcial","igual que 'Calles 20': requiere capa de velocidades (no descargada)",67),
(E3,"3.5","Resultado","Calles peatonales","%","(km calles peatonales / km red urbana) ×100","11%","25","Urbanismo","Anual","parcial","posible con el callejero si tipifica calles peatonales (por comprobar)",67),
(E3,"3.5","Resultado","Bandas sonoras","Nº tramos","Nº tramos con bandas sonoras","62","120","Urbanismo","Anual","no",NO_GESTION,67),
(E3,"3.5","Resultado","Reductores de velocidad","Nº reductores","Nº reductores de velocidad","113","150","Urbanismo","Anual","no",NO_GESTION,67),
(E3,"3.5","Resultado","Pasos sobreelevados","Nº pasos","Nº pasos sobreelevados","44","100","Urbanismo","Anual","no",NO_GESTION,67),
(E3,"3.5","Impacto","Reducción siniestros en zonas 30 / coexistencia / residenciales","%","Comparación anual","—","-50%","Policía Local","Anual","parcial","siniestros geocodificados dentro de zonas 30: falta la capa de zonas 30/coexistencia. Año base no fijado",67),
(E3,"3.6 Señalización de obras","Resultado","Manual municipal de señalización de obras","Documento","Existencia del manual","No","Manual aprobado","Movilidad","Puntual","no","verificable (sí/no)",67),
(E3,"3.6","Impacto","Reducción de incidentes en zonas de obra","%","Comparación anual","—","-40%","Policía Local","Anual","parcial","FACTORES CONCURRENTES = 'TRAMO EN OBRAS' (90 casos en 2022-2025; muy pocos). obras_ejecutadas.csv no sirve",67),
(E3,"3.7 Herramientas de gestión de seguridad vial","Actividad","Proyectos con auditoría de seguridad vial","Nº auditorías","Nº auditorías de proyectos relevantes","—","10","Movilidad","Anual","no",NO_GESTION,67),
(E3,"3.7","Actividad","Auditoría de seguridad vial en tramos en servicio","Nº auditorías","Nº auditorías en tramos críticos en servicio","4","30","Movilidad","Anual","no","dato de gestión; pero nuestro cribado (outputs/cribado_eb.csv) puede proponer qué tramos críticos auditar",67),
(E3,"3.7","Resultado","Procedimientos del Centro de Gestión de Tráfico actualizados","Documento","Existencia protocolo actualizado","No","Actualizado","Movilidad","Puntual","no","verificable (sí/no)",67),
(E3,"3.7","Resultado","Reuniones de coordinación análisis viario-movilidad","Nº reuniones","Nº reuniones realizadas","—","6/año","Movilidad","Anual","no",NO_GESTION,67),
(E4,"4.1.1 Control de vehículos de mercancías","Actividad","Controles específicos a vehículos de mercancías","Nº controles","Nº controles policiales realizados","—","600/año","Policía Local","Anual","no",NO_GESTION,68),
(E4,"4.1.1","Actividad","Campañas de control de transporte de mercancías","Nº campañas","Nº campañas realizadas","—","6","Policía Local","Anual","no",NO_GESTION,68),
(E4,"4.1.1","Resultado","Vehículos de mercancías inspeccionados","Nº vehículos","Nº vehículos sometidos a control","—","3.500","Policía Local","Anual","no",NO_GESTION,68),
(E4,"4.1.1","Resultado","Infracciones detectadas en transporte de mercancías","Nº infracciones","Nº sanciones registradas","—","-30%","Policía Local","Anual","no","no hay datos abiertos de sanciones",68),
(E4,"4.1.1","Impacto","Reducción de siniestros con vehículos de mercancías implicados","%","(Siniestros año base - actuales) / año base ×100","—","-40%","Policía Local","Anual","sí","UNIDADES_IMPLICADAS con CAMIÓN o FURGONETA (aproximación: no toda furgoneta es de mercancías). Año base no fijado",68),
(E4,"4.1.2 Control de ITV y seguro obligatorio","Actividad","Controles de ITV y seguro obligatorio realizados","Nº controles","Nº controles policiales realizados","—","2.000","Policía Local","Anual","no",NO_GESTION,68),
(E4,"4.1.2","Resultado","Vehículos inspeccionados con ITV o seguro irregular","Nº vehículos","Nº vehículos detectados sin ITV o seguro","—","-50%","Policía Local","Anual","no",NO_GESTION,68),
(E4,"4.1.2","Impacto","Reducción de circulación de vehículos sin ITV o seguro","%","Comparación anual","—","-60%","Policía Local","Anual","no",NO_GESTION,68),
(E4,"4.1.2","Impacto","Reducción de siniestros relacionados con fallos mecánicos o irregularidades administrativas","%","Comparación anual","—","-30%","Policía Local","Anual","parcial","FACTORES CONCURRENTES = 'AVERÍA MECÁNICA' o 'MAL ESTADO DEL VEHÍCULO'; las irregularidades administrativas no constan",68),
(E5,"5.1.1 Atención rápida y eficaz a los siniestros","Actividad","Intervenciones en siniestros viales","Nº intervenciones","Nº actuaciones realizadas","—","3.000/año","Policía Local","Anual","no","dato de gestión (el nº de siniestros registrados sí lo tenemos, pero no es lo mismo)",69),
(E5,"5.1.1","Resultado","Coordinación entre servicios de emergencia","Nº reuniones","Nº reuniones de coordinación realizadas","—","6/año","Policía Local","Anual","no",NO_GESTION,69),
(E5,"5.1.1","Impacto","Reducción del tiempo de atención a siniestros","%","Comparación anual","—","-30%","Policía Local","Anual","no","no hay tiempos de atención en datos abiertos",69),
(E5,"5.1.2 Profesionalizar la investigación de siniestros","Actividad","Agentes formados en investigación de siniestros","Nº agentes","Nº agentes con formación especializada","—","40","Policía Local","Anual","no",NO_GESTION,69),
(E5,"5.1.2","Resultado","Informes técnicos de investigación de siniestros elaborados","Nº informes","Nº investigaciones realizadas","—","200","Policía Local","Anual","no",NO_GESTION,69),
(E5,"5.1.3 Análisis de siniestros con consecuencias graves","Actividad","Estudios de siniestros graves realizados","Nº estudios","Nº análisis técnicos elaborados","—","40","Policía Local","Anual","no",NO_GESTION,69),
(E5,"5.1.3","Resultado","Recomendaciones de mejora derivadas del análisis","Nº recomendaciones","Nº medidas propuestas","—","60","Policía Local","Anual","no",NO_GESTION,69),
(E5,"5.1.4 Atención personalizada a víctimas","Actividad","Servicios de atención a víctimas de siniestros viales","Nº servicios","Nº intervenciones de atención especializada","—","200","Policía Local","Anual","no",NO_GESTION,69),
(E5,"5.1.4","Resultado","Víctimas atendidas mediante programas de apoyo","Nº personas","Nº víctimas o familiares atendidos","—","400","Policía Local","Anual","no",NO_GESTION,69),
(E5,"5.1.4","Impacto","Nivel de satisfacción de víctimas con la atención recibida","% satisfacción","Encuestas de satisfacción","—","95%","Policía Local","Bienal","no","requiere encuesta",69),
(E6,"6.1.1 Sistemas informáticos de registro y análisis de siniestros","Actividad","Desarrollo de nuevos módulos informáticos para gestión de siniestros viales","Nº herramientas","Nº aplicaciones o módulos desarrollados","—","5","Movilidad","Anual","no",NO_GESTION,70),
(E6,"6.1.1","Resultado","Informes de análisis de indicadores de siniestralidad vial","Nº informes","Nº informes técnicos publicados","—","6/año","Movilidad","Anual","no","verificable contando informes publicados; no se calcula con datos",70),
(E6,"6.2 Colaboración con proyectos de investigación","Actividad","Convenios de colaboración con entidades investigadoras","Nº convenios","Nº acuerdos firmados","—","10","Movilidad y Policía Local","Anual","no","dato de gestión; un convenio con nuestro socio sumaría a este indicador",70),
(E6,"6.2","Resultado","Estudios técnicos realizados en colaboración con centros de investigación","Nº estudios","Nº informes técnicos elaborados","—","15","Movilidad","Anual","no",NO_GESTION,70),
(E6,"6.2","Resultado","Proyectos piloto de innovación en seguridad vial","Nº proyectos","Nº pilotos implementados","—","6","Movilidad","Anual","no",NO_GESTION,70),
(E6,"6.2","Impacto","Medidas de seguridad vial implementadas a partir de investigación","% medidas","(Medidas implementadas / medidas propuestas en investigaciones) ×100","—","80%","Movilidad","Anual","no",NO_GESTION,70),
(E7,"7.1 Mecanismos de gestión municipal","Actividad","Cuadro de mando de seguimiento del PDSVV implantado","Sistema","Existencia de plataforma operativa","No existente","Sistema operativo","Movilidad","Puntual","no","verificable (sí/no); es justo lo que nuestra web ofrecería en abierto",71),
(E7,"7.1","Resultado","Memoria anual de siniestralidad elaborada","Nº informes","Nº informes anuales publicados","1","1/año","Policía Local","Anual","no","verificable (sí/no)",71),
(E7,"7.1","Actividad","Acciones formativas en seguridad vial dirigidas a personal municipal","Nº cursos","Nº cursos realizados","—","8","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.1","Resultado","Personal municipal formado en seguridad vial","Nº personas","Nº participantes en formación","—","150","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.1","Resultado","Planes especiales de movilidad elaborados (Fallas, Navidad, etc.)","Nº planes","Nº planes específicos desarrollados","—","2","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.2 Coordinación de la gestión","Actividad","Reuniones de coordinación entre Movilidad y Policía Local","Nº reuniones","Nº reuniones realizadas","—","12/año","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.2","Actividad","Reuniones de coordinación con otros Servicios del Ayuntamiento","Nº reuniones","Nº reuniones realizadas","—","4/año","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.3 Participación","Actividad","Informes de seguimiento presentados en la Comisión de Seguridad Vial","Nº informes","Nº presentaciones realizadas","—","2/año","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.3","Resultado","Acciones conjuntas con entidades de distribución urbana de mercancías","Nº acciones","Nº iniciativas realizadas","—","15","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.3","Resultado","Empresas de alquiler o venta de vehículos implicadas en campañas de seguridad vial","Nº empresas","Nº empresas colaboradoras","5","30","Movilidad","Anual","no",NO_GESTION,71),
(E7,"7.4 Políticas integradas","Actividad","Convenio firmado con la DGT para intercambio de información","Documento","Existencia convenio","No","Convenio firmado","Alcaldía","Puntual","no","verificable (sí/no)",71),
]
GLOBAL = [
("Objetivo global (4.4)","Objetivo global","Objetivo","Víctimas mortales","Nº personas fallecidas (30 días)","(fallecidos 2030 - fallecidos 2019) / fallecidos 2019","2019 (el Plan solo da 18 siniestros con fallecidos en 2019)","-50% en 2030","Policía Local","Anual","sí","TIPO GRAVEDAD = CON FALLECIDOS cuenta siniestros, no personas. El portal empieza en 2022: el año base 2019 no está en datos abiertos (usar la cifra del Plan)",26,"REDUCIR EL NÚMERO DE VÍCTIMAS MORTALES",1000),
("Objetivo global (4.4)","Objetivo global","Objetivo","Personas heridas graves","Nº personas","(graves 2030 - graves 2024) / graves 2024","2024 (176 personas hospitalizadas según tabla del cap. 8; 167 siniestros con heridos graves según gráfico)","-50% en 2030","Policía Local","Anual","parcial","el portal da siniestros CON HERIDOS GRAVES (2024: 167, igual que el Plan), no personas. Gravedad homogénea solo desde 2024 (Orden INT/2223/2014). 'Baja gravedad' es otra categoría",26,"PERSONAS HERIDAS GRAVES RESPECTO",1000),
]
out = f"{BASE}/data/processed/pdsv_indicadores.csv"
cols = ["eje","accion","tipo","indicador","unidad","formula","linea_base","meta_2030","fuente","periodicidad","calculable","como_o_por_que","ref"]
with open(out,"w",newline="",encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(cols)
    for g in GLOBAL:
        w.writerow(list(g[:12]) + [ref(g[12], g[13], g[14])])
    last = 2850
    for r in R:
        key = r[3][:28]
        ln = find(key, last)
        if ln and ln < 3400: last = ln
        w.writerow(list(r[:12]) + [f"PDF p.{r[12]} (pág. {r[12]-3})" + (f"; txt l.{ln}" if ln else "")])
n = len(R); from collections import Counter
print("indicadores:", n, Counter(r[10] for r in R), "+ globales", len(GLOBAL))
print("sin línea txt:", [r[3] for r in R if not find(r[3][:28], 2850)])

# Lugares
L = [
# nombre, tipo_lugar, colectivo, cifra_plan, periodo, contexto/accion, pdf, clave
("Av. de Blasco Ibáñez","calle","VMP","196 siniestros","2019-2025","2.3.4 Conclusiones: calles con más siniestros con VMP (n.º 1)",22,"Blasco Ibáñez (196)"),
("Av. del Puerto","calle","VMP","167 siniestros","2019-2025","2.3.4: calles con más siniestros con VMP (n.º 2)",22,"Avda. del Puerto (167)"),
("Paseo de la Alameda","calle","VMP","166 siniestros","2019-2025","2.3.4: calles con más siniestros con VMP (n.º 3)",22,"Paseo de la Alameda (166)"),
("Paseo de la Alameda - Plaza de Zaragoza","cruce","VMP","32 siniestros","2019-2025","2.3.4: cruces con más siniestros con VMP (n.º 1)",22,"Plaza Zaragoza (32)"),
("Ausiàs March - Fernando Abril Martorell","cruce","VMP","25 siniestros","2019-2025","2.3.4: cruces con más siniestros con VMP (n.º 2)",22,"Ausias March-Fernando Abril Martorell (25)"),
("Av. dels Tarongers (Naranjos) - Luis Peixó","cruce","VMP","22 siniestros","2019-2025","2.3.4: cruces con más siniestros con VMP (n.º 3)",22,"Naranjos-Luís"),
("Jardín del Turia","calle/parque","bici","185 siniestros","2019-2025","2.3.4: calles con más siniestros con bicicleta (n.º 1). En 2.3.3: 39 (2024) y 27 (2025), -30,76 %",22,"Jardín del Túria (185)"),
("Av. de Blasco Ibáñez","calle","bici","154 siniestros","2019-2025","2.3.4: calles con más siniestros con bicicleta (n.º 2)",22,"la Avda. Blasco Ibañez (154)"),
("Av. del Puerto","calle","bici","110 siniestros","2019-2025","2.3.4: calles con más siniestros con bicicleta (n.º 3)",22,"Avda del Puerto (110)"),
("Paseo de la Alameda - Plaza de Zaragoza","cruce","bici","22 siniestros","2019-2025","2.3.4: cruces con más siniestros con bicicleta (n.º 1)",22,"Plaza Zaragoza (22)"),
("Av. dels Tarongers (Naranjos) - Luis Peixó","cruce","bici","15 siniestros","2019-2025","2.3.4: cruces con más siniestros con bicicleta (n.º 2)",22,"Naranjos-Luís Peixó (15)"),
("Fernando Abril Martorell - Ctra. de Malilla","cruce","bici","14 siniestros","2019-2025","2.3.4: cruces con más siniestros con bicicleta (n.º 3)",22,"Malilla (14)"),
("C/ San Vicente Mártir","calle","peatón","87 siniestros","2019-2025","2.3.4: calles con más siniestros con peatón",22,"San Vicente Mártir (87)"),
("Av. de Blasco Ibáñez","calle","peatón","68 siniestros","2019-2025","2.3.4: calles con más siniestros con peatón",22,"Blasco Ibañez (68)"),
("C/ Colón","calle","peatón","65 siniestros","2019-2025","2.3.4: calles con más siniestros con peatón",22,"Colón (65)"),
("Peset Aleixandre - Camí de Montcada","cruce","peatón","10 siniestros","2019-2025","2.3.4: cruces con más siniestros con peatón",22,"Peset Aleixandre-"),
("Giorgeta - Jesús","cruce","peatón","8 siniestros","2019-2025","2.3.4: cruces con más siniestros con peatón",22,"Giorgeta-Jesús (8)"),
("Tres Cruces - Campos Crespo","cruce","peatón","7 siniestros","2019-2025","2.3.4: cruces con más siniestros con peatón",22,"Tres Cruces-Campos Crespo (7)"),
("Av. de Blasco Ibáñez - Av. Cardenal Benlloch","cruce","todos","","2024","Auditoría de seguridad vial (una de las 4 primeras, 'intersecciones de mayor siniestralidad'). Indicador 3.7: auditorías en tramos en servicio 4 -> 30",23,"Auditorías de Seguridad Vial en cuatro"),
("Av. Cardenal Benlloch - Av. del Puerto","cruce","todos","","2024","Auditoría de seguridad vial (acción 3.7)",23,"Cardenal Benlloch con Avenida del Puerto"),
("Plaza de Zaragoza","cruce/plaza","todos","","2024-2025","Auditoría de seguridad vial 2024 y reordenación de intersección crítica 2025 (acción 3.7)",23,"Auditorías de Seguridad Vial en cuatro"),
("Gran Vía Fernando el Católico - C/ Àngel Guimerà","cruce","todos","","2024-2025","Auditoría de seguridad vial 2024 y reordenación de intersección crítica 2025",23,"Ferran el Catòlic"),
("Blasco Ibáñez - Cardenal Benlloch - Clariano","cruce","todos","","2025","Reordenación de intersección crítica: marcas viales, fin del ámbar intermitente, visibilidad peatonal",23,"Reordenación de intersecciones críticas"),
("Paseo de la Ciutadella","punto","todos","","2025","Radar didáctico en 'punto sensible' (limitaciones de velocidad)",23,"radares didácticos"),
("Av. del General Avilés","punto","todos","","2025","Radar didáctico en 'punto sensible'",23,"avenida del General Avilés"),
("C/ Enginyer Fausto Elío","punto","todos","","2025","Radar didáctico en 'punto sensible'",23,"Enginyer Fausto Elío"),
("Ronda Norte","tramo","peatón","","2025","Iluminación LED en pasos de peatones de alta siniestralidad",23,"Ronda Norte"),
("C/ Xàtiva - C/ Jesús","cruce","bici","","—","Configuración ciclista pendiente de estudio: giro de vehículos con fase ámbar sobre paso de peatones y carril bici (acción 3.2.2)",40,"calle Xátiva con calle Jesús"),
("C/ Xàtiva","calle","peatón/bici","","—","Marca vial 'Espere verde' en carril bici; descontador peatonal desde 2021",40,"Espere Verde en Calle"),
("Gran Vía Germanías a la altura de C/ Castellón","punto","peatón","","2021","Primer descontador de tiempo para peatones",22,"Gran vía Germanías"),
("Anillo Ciclista (Ronda Interior)","eje ciclista","bici","más de 10.000 ciclistas/día en algunos tramos","mayo 2025","Itinerario ciclista de mayor intensidad (cita el plano de intensidades de Movilidad)",12,"Anillo Ciclista para la Ronda"),
("Jardín del Turia","zona","VMP","","—","Zona de concentración de uso de VMP",41,"del Jardín del Turia. Los principales"),
("Ciutat Vella (Área de Prioridad Residencial)","zona","todos","","2022","APR implantada en 2022; ampliación de 30 km/h a otros distritos (acción 3.5)",23,"Ciutat Vella e implantación"),
("Lonja de la Seda y Plaza del Mercado","zona","peatón","","—","Peatonalización progresiva",23,"Lonja de la Seda"),
("Estación Joaquín Sorolla (Kiss and Go)","punto","todos","","2024","Carriles y parada rápida para reducir conflictos",23,"Joaquín Sorolla"),
("Av. del General Avilés - C/ Luis Buñuel (Campanar)","cruce","peatón","","—","Ejemplo de nuevo paso de peatones en gran avenida (acción 3.2.1)",37,"Buñuel"),
("Av. de Peris y Valero","punto","peatón","","—","Foto de paso peatonal accesible (acción 3.4)",47,"Peris y Valero"),
]
# tipo de cita, explícito fila a fila (no se deduce del texto): «diag» = diagnóstico o contexto (rankings de 2.3.4,
# zona de concentración de uso, itinerario de mayor intensidad, foto de ejemplo); «act» = actuación hecha o prevista
KIND = ["diag"] * 18 + ["act"] * 12 + ["diag", "diag"] + ["act"] * 4 + ["diag"]
assert len(KIND) == len(L), (len(KIND), len(L))
out2 = f"{BASE}/data/processed/pdsv_lugares.csv"
with open(out2,"w",newline="",encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["nombre","tipo_lugar","colectivo","cifra_plan","periodo","accion_o_contexto","ref","kind"])
    miss=[]
    for l, kd in zip(L, KIND):
        ln = find(l[7], 0)
        if not ln: miss.append(l[0])
        w.writerow(list(l[:6]) + [f"PDF p.{l[6]} (pág. {l[6]-3})" + (f"; txt l.{ln}" if ln else ""), kd])
print("lugares:", len(L), "sin línea:", miss)
