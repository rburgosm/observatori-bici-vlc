# Revisión de coherencia: observatorio y relato

Revisión externa del 03/11/2026, solo de lectura, sobre las plantillas de `web/proto/` (copiadas a las 22:13), `datos/observatori.js`, `datos/relato.js` y los datos de `data/processed/` y `outputs/`. He recalculado las cifras con pandas y geopandas. Las capturas se hicieron con Chrome sin interfaz: el mapa grande de MapLibre no pinta las capas WebGL en ese modo (calles, zona y halo), así que esas capas se han revisado leyendo el código.

Abreviaturas: **OBS** = herramienta (`observatori`) · **REL** = relato (`informe`) · «ambos» = siniestro con bici **y** patinete (`v = "a"`).

---

## 1. Tabla priorizada

### Gravedad alta

| # | Página · vista | Qué se ve | Por qué es incoherente | Corrección propuesta |
|---|---|---|---|---|
| A1 | OBS · «On s'acumulen» · ficha y zona del Jardín del Turia | «191 siniestros»; «solo 26 llevan una dirección que se pueda situar en el mapa». | `exportar_web.py` selecciona el Turia con `contains("TURIA")`, y eso también recoge **GV Marqués del Turia (21), C/ Camp de Túria (4) y C/ Asturias × Grao (1)** («As-TURIA-s»). Los 26 «situables» son **exactamente esos 26**: ninguno está en el jardín. Los siniestros del jardín son **165, con 0 geolocalizados**. Además, los 5 de Regne de València × GV Marqués del Turia se cuentan dos veces: en el lugar n.º 15 y en el Turia. | Usar la misma clave que `CLAVES`: `JARDIN DEL TURIA\|JARDI DEL TURIA`. El texto pasa a ser: «165 siniestros; ninguno tiene punto exacto». Hay que repetir la prueba binomial de la pista, el perfil y `por`. |
| A2 | OBS · minimapa con el Turia seleccionado | La leyenda dice «Círculos: solo los 26 siniestros que llevan una dirección situable», pero el minimapa pinta un manto de quesitos por todo el centro (captura). | `quesitosMini()` dibuja **todos** los grupos que caen en el rectángulo de la zona: 3.282 de 5.215 puntos (63 % de la ciudad). La leyenda contradice el dibujo y, tras A1, no hay ningún punto del jardín. | Para una zona, no dibujar puntos (solo el contorno y la sombra) o filtrar por `within(zona)`. Cambiar la leyenda en consecuencia. |
| A3 | REL · modo «Sense animació» (todas las leyendas) | Los iconos de las leyendas casi no se ven: se quedan en rayitas sueltas (captura). | En `montarTodo()`, `document.querySelectorAll(".fig-paso svg")` también selecciona los `<svg>` de los iconos de la `.ley`, y `montar()` dibuja el escenario entero dentro de cada icono. En el modo accesible ninguna leyenda funciona. | Cambiar el selector por `.fig-paso > svg` y ajustar el CSS a `.fig-paso > svg`. |
| A4 | REL · «quien» (y OBS en todas partes) | En **un solo paso** hay tres nombres para lo mismo: el rótulo «Les dues 80», la leyenda «xoc bici–patinet» y el texto «amb tots dos alhora». En OBS, «Xoc bici–patinet» aparece en la leyenda del gráfico de la meta, el filtro, la tabla y los quesitos, pero `pts_lead` dice «amb tots dos / con los dos». | Es el problema que ya detectó el usuario y sigue ahí. «Choque» es además falso para el 4 % (11 de 273 tienen también coche o peatón). Se confunde con la categoría «Una altra bici o patinet» (con quién) y con la pista `d`, «xocs entre bicis i patinets», que incluye bici-bici y patinete-patinete. | Un solo término en las dos páginas: **«Bici i patinet» / «Bici y patinete»**, con la nota «el 96 % son choques entre ellos» calculada a partir de los datos. La pista `d` pasa a «choques entre ciclistas o usuarios de patinete». |
| A5 | OBS y REL · contadores | Hay cinco versiones de qué cuentan los contadores: «Mobilitat compta les bicis» (expl.uso, f_uso «comptador de bicis»), «Bicis i patinets que hi passen» (etiqueta IMD), «probablement compten bicis i patinets junts» (uso_com), «No sabem si distingeixen… Ho preguntarem» (lim), y en REL falta3 lo afirma: «compten bicis i patinets junts». | La misma página se contradice y REL afirma lo que OBS duda. Además, «145 comptadors» (REL, trafico) son **145 sitios con 148 contadores** (3 sitios agrupan varios). | Una sola formulación prudente en todas partes: «contadores de bicis (es probable que cuenten también patinetes; pendiente de confirmar con Movilidad)». Decir «145 puntos de conteo», no «145 contadores». |
| A6 | REL · falta2 (y OBS · Limitaciones) | La línea une 2023, 2024 y 2025 como serie comparable y solo 2022 aparece hueco («no comparable»). El texto dice: «2022 no es pot comparar amb la resta». | En los datos, los siniestros con heridos graves por trimestre suben poco a poco durante 2023 (10, 17, 18, 31) y siguen subiendo en 2024 (34, 33, 44, 56). Por años: 19, 76, 167 y 181. El cambio de criterio no es un escalón en 2023, y la propia nota del proyecto (`pdsv_indicadores.csv`) dice «homogénea solo desde 2024». | 2022 y 2023 huecos, y la línea solo entre 2024 y 2025. Texto: «el cambio empieza en 2023 y no se aplica del todo hasta 2024». Hay que alinear OBS `lim[0]` y `gravTxt`. |
| A7 | OBS · gráfico de la meta; REL · partida | OBS: «Senda del Pla cada any (objectiu)». REL: leyenda «senda del Pla (objectiu)», rótulo «senda del Pla», aria «Senda del Pla». | El propio REL explica que el Plan **no tiene línea base** y que la senda es una construcción nuestra («Si cada any baixara en la mateixa proporció…»). Atribuírsela al Plan contradice el paso anterior. | «Senda propuesta (base 2024, −50 % en 2030)» en las dos páginas. |
| A8 | OBS · «Més del normal»; OBS y REL · rojos | Naranja = patinete en toda la web **y** «Potser més del normal» en la vista de uso (`verd` → `--pat`, círculos del mapa y píldora). Rojo (`--warn`) = «el Plan no lo menciona» (anillo), «claramente más de lo normal», marca de la **media de la ciudad** en las barras de la ficha, el desfase con la senda, 2025, «sin línea base» y «cambio de criterio». | Un mismo color con varios significados en la misma página. El caso más grave es el naranja: al pasar de «On s'acumulen» a «Més del normal», el naranja deja de significar patinete. La media de la ciudad en rojo parece una alerta. | Escala propia para el exceso (por ejemplo, rojo oscuro, rojo claro y gris), nunca `--pat`. Media de la ciudad en `--ink2`. Reservar el rojo para «alerta o desviación» (ver el glosario). |
| A9 | OBS · «On s'acumulen» | El lugar seleccionado lleva un anillo negro (`selh`, `--ink`, radio 22) y la leyenda dice «Anillo negro: el Plan prevé o ha hecho alguna actuación». | El mismo código tiene dos significados en la misma vista: al seleccionar un lugar sin actuación, parece que la tiene. | La selección se marca con otra forma: halo amarillo `--hl` grueso y semitransparente, o un cuadrado. |
| A10 | REL · donde, trafico y cruce; OBS · mapa | En REL la red ciclista se pinta con `--bici` (verde azulado), el mismo color de los siniestros «solo bici». En OBS, con `--lane` (verde). La leyenda del minimapa llama «verd» a la bici, que es verde azulado, mientras que la línea verde es el carril. | El mismo dato tiene códigos distintos entre páginas y el mismo color tiene dos significados dentro de REL (en la captura, la red verde azulada domina el mapa de los 30 lugares). | Usar `--lane` (o un gris) para la red en las dos páginas, incluirla en la leyenda de REL y nombrar el color de la bici «verd blavós / verde azulado». |
| A11 | REL · alameda3 frente a OBS · ficha de Alameda–Zaragoza | REL: «El Pla **preveu** auditar i reordenar aquesta intersecció» y «És un problema de com es creua». OBS: «Auditoria de seguretat viària (2024) i reordenació (2025)», en «Què s'hi ha fet o s'hi farà». | El Plan da la auditoría (2024) y la reordenación (2025) como hechas. Los datos lo muestran: **16, 16, 10 y 6** siniestros de 2022 a 2025 (−63 %). El relato presenta como problema pendiente el lugar que mejor ha evolucionado, y su gráfico de 48 puntos no deja ver la caída. | REL: «El Pla hi va fer una auditoria (2024) i la va reordenar (2025); des de 2024 els sinistres han baixat de 16 a 6». Es un buen hallazgo para el relato, no un problema que esconder. |
| A12 | OBS · ficha de lugar · «Sinistres cada any» | Barras apiladas en dos colores (verde azulado y naranja), sin leyenda. | `vy = [solo bici, patinete con ambos]`: «ambos» se pinta de naranja, mientras que el quesito del mismo lugar, el minimapa y el gráfico de la meta lo pintan morado. Es otra vez el problema de esconder la mezcla. | Tres segmentos (b, a, p) con los colores comunes y una leyenda. |

### Gravedad media

| # | Página · vista | Qué se ve | Por qué es incoherente | Corrección propuesta |
|---|---|---|---|---|
| M1 | OBS · «Tots els sinistres» | Con zoom < 14, cada círculo va de verde azulado o naranja según lo que **predomina** (`step f .5`). Con zoom ≥ 14 aparecen quesitos con morado. La leyenda solo dice «Predomina la bici / el patinet». | El color por mayoría esconde la mezcla, y el morado de los quesitos no está en la leyenda de esa vista. | Quesitos o color continuo también con zoom bajo, o gris para «mezcla». Añadir el morado a la leyenda. |
| M2 | OBS (anillo y «El Pla ja el senyala») y REL (anillo) | «Sin anillo: el Plan lo señala» en C/ Eduardo Boscà × Alameda, Puente de la Exposición, 3 lugares de la Av. del Puerto y Blasco Ibáñez × Haro. En C/ Colón × Isabel la Católica, C/ Colón 8 y San Vicente Mártir 88, la cita es una **lista de calles con peatones**. | La cita es de la **calle** (o del colectivo peatón), no del lugar. Pasa lo mismo con las actuaciones: «radar» en el Paseo de la Ciutadella marca dos lugares y el de Fausto Elío marca Naranjos × Luis Peixó. El anillo sobrestima lo que dice el Plan. | Tres niveles: «cita este lugar», «cita la calle» y «no lo cita». En la ficha, decir el colectivo: «la cita por siniestros con peatones». |
| M3 | OBS · «Què diu el Pla» del Turia | En «Què s'hi ha fet o s'hi farà» aparece «Actuació citada pel Pla · Jardín del Turia». | La fuente es «Zona de concentración de uso de VMP», que es diagnóstico. `kind` se decide con `startswith("2.3.4")`, así que todo lo demás pasa a actuación (también caería así «Anillo Ciclista… itinerario de mayor intensidad»). | Añadir una columna `kind` explícita (diag/act) en `pdsv_lugares.csv` y no deducirla del texto. |
| M4 | OBS · ficha · titular | C/ Colón 8: «La majoria són xocs amb cotxes, motos o furgonetes», y la pista de la misma ficha dice «molts més atropellaments». San Vicente Mártir 88: «Molts són xocs entre bicis i patinets» con un empate 5 a 5 con las caídas. | En Colón 8 son 8 de 20 (40 %): no es la mayoría. Con empate, la frase sale del orden de las claves. | «La majoria» solo si pasa del 50 %. Si no, «el més freqüent». Si hay empate, nombrar las dos categorías. |
| M5 | OBS · ficha de Alameda frente a REL · alameda3 | OBS: barra «No respectar la prioritat 50 %» y «sovint». REL: «**6 de cada 10** xocs amb vehicle de motor». | El mismo dato del mismo lugar aparece con dos denominadores (24 de 48 frente a 24 de 43). | Usar el mismo denominador en las dos o nombrarlo siempre («de los choques con vehículo»). |
| M6 | OBS · ficha · chip de semáforo | «Sense semàfor municipal a 40 m» en 20 de 30 lugares, entre ellos Alameda–Zaragoza y Ausiàs March–Abril Martorell. | La capa 182 son **reguladores** (armarios), no semáforos. En 12 de esos 20 hay un semáforo de OSM a 40 m o menos (Alameda–Zaragoza a 26 m, Ausiàs March a 39 m y Tres Cruces × Campos Crespo a 6 m). El lector entiende «no hay semáforo». | Quitar el chip o rehacerlo: «Cruce semaforizado» si hay un regulador a 80 m o menos o un semáforo de OSM a 40 m o menos, indicando la fuente. |
| M7 | OBS (3 niveles) frente a REL (2 niveles) | OBS: rojo con p > 0,95, naranja entre 0,8 y 0,95, gris por debajo. REL: lleno con p > 0,95 y todo lo demás «dins del normal». | 16 contadores son «Quizá más de lo normal» en la herramienta y «dentro de lo normal» en el relato. | Los mismos umbrales y las mismas etiquetas en las dos páginas, o en REL «resto: sin exceso claro». |
| M8 | REL · lleno/hueco | Hueco = senda (partida), «sin ese factor» (alameda3), «dentro de lo normal» (trafico2) y «no comparable» (falta2). | Un código con cuatro significados en una misma página. | Hueco solo para «referencia u objetivo». «Sin factor» con relleno claro, «normal» en gris lleno y «no comparable» en gris tramado o con un aspa. |
| M9 | OBS frente a REL · senda | OBS: barras huecas discontinuas. REL: círculos huecos y una línea punteada. | El mismo concepto se dibuja con dos códigos entre páginas. | Elegir uno (círculos huecos y línea punteada, que se lee mejor) y usarlo en las dos. |
| M10 | REL · cruce y fin | «Pots buscar qualsevol cruïlla… i veure els seus sinistres any a any, amb qui xoquen i què en diu el Pla». | Fuera de los 30 lugares y de los 145 puntos, el buscador abre «Tots els sinistres», cuya ficha es solo una lista: sin evolución, sin «amb qui» y sin Plan. | Ampliar la ficha de «pts» o rebajar el texto: «la llista dels seus sinistres; per als 30 llocs, una fitxa completa». |
| M11 | REL · fin_p | «L'observatori mostra **cada** sinistre… en el mapa». | Solo se muestran 5.215 de 5.971 (87 %). | «el 87 % que es pot situar», con la cifra sacada de `cob`. |
| M12 | OBS · cambio de idioma con un lugar seleccionado | La ficha cambia de idioma y la leyenda del minimapa (`mm-ley`) se queda en el idioma anterior. | `mm-ley` solo se escribe en `moverMini()`, y `textos()` no la llama. Tampoco cambian el `aria-label` del buscador, los botones de zoom ni el `<title>` del gráfico (solo en VA). | Llamar a la escritura de `mm-ley` desde `textos()` y traducir los atributos. |
| M13 | OBS · «Tots els sinistres» con el filtro de año o vehículo | El mapa grande se filtra y el minimapa de la ficha sigue mostrando todos los años y vehículos. | El minimapa tiene un código distinto al del mapa grande (el mismo tipo de error que ya se encontró). | Que `gruposMM` use el mismo filtro que `agrupar()`. |
| M14 | OBS frente a REL · formato de números | OBS escribe «1659» y «1501» en el estado y el gráfico (`toLocaleString` no agrupa 4 cifras), pero «1.659» en «El que hem aprés». REL siempre escribe «1.659». | La misma cifra aparece escrita de dos maneras. | Un solo `fmt` con `useGrouping:"always"`, como en REL. |
| M15 | OBS y REL · nombre de los 30 lugares | «Punts negres» (tarjeta de hallazgos y su título), «On s'acumulen» (pestaña), «Lloc amb molts sinistres» (ficha), «llocs amb més sinistres» (REL) y el chip «Ha estat **dels pitjors** llocs». | Hay cuatro nombres, y «pitjors» o «punt negre» contradicen el aviso de la propia ficha: «no vol dir que siga el lloc més perillós». El criterio de «tres» (entre los 60 primeros de cada periodo) ya no se dice en ningún texto («els primers» o «els pitjors»). | Un solo nombre: «llocs amb més sinistres». Chip: «Entre els 60 amb més sinistres en els tres períodes». |
| M16 | OBS y REL · «más de lo normal» | Pestaña VA «Més del normal pel trànsit» / ES «Más de lo normal para el tráfico». También «Més del que toca» (texto antiguo), «el que tocaria», «Esperats», «El normal», «Sinistres que tindria un lloc amb el mateix trànsit» y «Seguretat que n'hi ha més del normal» (que es una probabilidad posterior). | Seis maneras de nombrar la misma cifra (μ). «Seguretat» sugiere certeza. | Glosario: μ = «el normal per al trànsit»; la franja = «variació normal»; p = «probabilitat que n'hi haja més del normal». |
| M17 | OBS · nota_base frente a REL · partida | OBS: «prenem 2024, com fa per a la seua meta general». REL: «l'any que el Pla usa per als ferits greus». | La meta general del Plan usa 2019 para fallecidos y 2024 para heridos graves. Lo que dice OBS es inexacto y no coincide con REL. | Usar la fórmula de REL en las dos. |
| M18 | OBS · «Què diu el Pla» | «és el número 2 amb patinet (25 siniestros), segons el Pla (2019-2025)» en Ausiàs March, junto a nuestros «26 sinistres en 2022-2025». | Se comparan unidades (cruce frente a celda de 100 m) y periodos distintos sin avisar, y nuestro recuento de 4 años supera al del Plan de 7. «siniestros» sale en castellano dentro del texto en VA (`cifra_plan`). | Añadir una nota: «el Pla compta el creuament de 2019 a 2025; nosaltres, la cel·la de 100 m de 2022 a 2025». Traducir la cifra. |
| M19 | OBS · leyenda de «Més del normal» | No se explica el tamaño: `ley_uso` existe, pero `leyenda()` lo vacía en esta vista. El gris «normal» del círculo es `--street2`, el mismo color que las avenidas, y la píldora de la ficha usa `--ink2`. | La leyenda no coincide con lo dibujado y una categoría tiene dos grises. | Mostrar «Mida: sinistres observats». Dar un gris propio para «normal» que no coincida con las calles. |
| M20 | OBS · ficha de contador | «Ací hi ha hagut N sinistres en **quatre** anys» e «IMD = `expo/4`». | En `cribado_eb.py`, N y `expo` solo suman los años-sitio con exposición completa. Si un sitio tiene menos de 4 años, la IMD sale baja y «quatre anys» es falso. **Hay que comprobarlo** (no lo he podido medir sin reejecutar el modelo). | Exportar `n_años` por sitio y usarlo en el texto y en el divisor. |
| M21 | REL · donde frente a OBS | REL deja fuera el Jardín del Turia, que el Plan pone como n.º 1 con bici. En OBS, la zona del Turia no lleva anillo del Plan aunque el Plan la cita. | Los dos mapas cuentan cosas distintas del mismo lugar. | Una frase en REL («i el Jardí del Túria, que no té punts exactes») y el anillo también en la zona de OBS. |
| M22 | REL · trafico y cruce | Los puntos negros (contadores) y la red ciclista no tienen leyenda (`leyenda()` no tiene `trafico` ni ningún alias para él, y `cruce` usa la de `donde`). | Hay marcas sin explicar. | Añadir la entrada «comptador» y «xarxa ciclista». |

### Gravedad baja

| # | Página · vista | Qué se ve | Por qué | Corrección |
|---|---|---|---|---|
| B1 | OBS y REL | Cifras escritas a mano: «el 96 %» (ques_ley), «n.º 1 també per al Pla» (`pla1`), el nombre «Pg. de l'Albereda × pl. de Saragossa» (`lug1`), «en quatre anys», los nombres de los destacados (`DEST`) y «(p. 60)». | Hoy son correctas (96,0 %, `pr` = 1), pero no se actualizarán con 2026. | Sacarlas de los datos (`R.negros[0].pr`, `nomLugar`, `nw(AÑOS.length)`). |
| B2 | OBS · `{p1}` | «En 2022 el portal anotava pitjor». | P1 va de enero a septiembre de 2022, y 2023 también tiene una cobertura baja (84 % frente al 95 % de 2025). | «Fins a setembre de 2022, i en menor mesura fins a mitjan 2024». |
| B3 | OBS frente a REL | Apilado en el orden b, p, a (OBS) y b, a, p (REL). | La misma categoría ocupa posiciones distintas. | Un solo orden. |
| B4 | OBS y REL · leyenda del anillo | «Sense anell» se dibuja como un anillo gris claro. | Se usa un anillo para decir «sin anillo». | Dibujar el quesito sin anillo. |
| B5 | REL · trafico2 (900 px) | Se cortan la etiqueta del eje X y «el que to…». | Desbordamiento. | Partir la etiqueta en dos líneas o anclarla a la derecha. |
| B6 | REL · quien2 frente a quien | «bici» en quien = solo bici; «Bici» en quien2 = bici con ambos (suma por vehículo). Mismo color y mismo nombre. | Dos definiciones en pasos consecutivos (el aviso lo explica, pero la leyenda no). | En quien2: «bici (amb les compartides)». |
| B7 | OBS · `pla_diag` | «El seu carrer, Jardín del Turia, és el número 1…»; «és un amb vianants (65 siniestros)». | Es un parque, no una calle, y la frase es poco natural. | Texto propio para zonas y parques. Para las listas sin rango: «apareix en la llista de carrers amb més sinistres amb vianants». |
| B8 | OBS · `verd` y porcentaje | Con p = 0,95, la etiqueta es «Potser» y el texto dice «95 %». Con 0,953, «Clarament» y también «95 %». | El redondeo cruza el umbral. | Mostrar un decimal cerca del umbral o comparar con el valor redondeado. |
| B9 | OBS · proto | «Les xifres anuals quadren amb les del Pla». | VMP 2023: 1.002 frente a 1.003. VMP 2025: 1.190 frente a 1.192. Bici 2024: 510 frente a 511. El Plan suma por vehículo y el titular usa la unión. | «Difereixen en 1-2 sinistres; el Pla compta per vehicle». |
| B10 | REL · promesa | «abans de 2030» frente a la meta «en 2030». | Matiz de fecha. | «en 2030». |
| B11 | OBS · minimapa | El cuadrado de 100 m se dibuja alineado al norte y la celda real es UTM (unos 2° girada). | Algún punto en el borde puede verse dentro o fuera por error. | Dibujar el polígono UTM reproyectado. |
| B12 | Código muerto | `neg-plan` (siempre oculto), `colLugar`, `todos` del minimapa, `--mix` y el color por mayoría de `neg`. | Pueden reactivar códigos antiguos. | Eliminarlos. |

---

## 2. Cifras recalculadas (coinciden salvo donde se indica)

| Cifra | Valor recalculado | OBS | REL |
|---|---|---|---|
| Siniestros bici o VMP (unión) 2022-2025 | 1.339 · 1.472 · 1.501 · 1.659 | ✓ | ✓ |
| Desglose 2025: solo bici · ambos · solo patinete | 469 · 80 · 1.110 | ✓ | ✓ |
| Con VMP y con bici (suma por vehículo) | VMP 825 → 1.190; bici 576 → 549 (2025: 1.739 sumando) | — | ✓ (y lo avisa) |
| Variación 2025 frente a 2024 | +10,5 % | ✓ | ✓ |
| Variación 2025 frente a 2022 | +24 % | ✓ | — |
| Meta 2030 / senda 2025 / desfase | 751 / 1.337 / +322 | ✓ | ✓ |
| Bajada anual necesaria | 14,7 % → «15 %» | ✓ | ✓ |
| Con patinete de cada 10 (2025 / 2022) | 7,2 / 6,2 → 7 / 6 | ✓ | ✓ |
| Lugares y estables en los tres periodos | 30 y 13 | ✓ | ✓ |
| Lugares que el Plan no cita | 15 de 30 | ✓ | ✓ (pero ver M2) |
| Puntos de conteo / con p > 0,95 / entre 0,8 y 0,95 | 145 (148 contadores) / 21 / 16 | ✓ | 145 ✓, 21 ✓, 16 → «normal» (M7) |
| Xàtiva, Tirso, Balaciart (N / μ / puesto) | 36 / 21,7; 20 / 7,0; 13 / 4,2 / puesto 30 | — | ✓ |
| Alameda: n, con motor, prioridad, VMP/bici/ambos | 48; 43; 24; 31/17/0 | ✓ | ✓ (ver M5 y A11) |
| Ambos que son solo bici con VMP | 262 de 273 = 96,0 % | ✓ (a mano) | — |
| Siniestros con heridos graves (toda la ciudad) | 19 · 76 · 167 · 181 | — | ✓ (pero ver A6) |
| Cobertura geográfica por periodo | 73,8 % · 84,7 % · 95,7 %; total 87,3 % | ✓ | — |
| **Turia** | **165** del jardín, **0** geolocalizados | ✗ 191 y 26 (A1) | — |

---

## 3. Reglas de estilo (glosario para que no vuelva a pasar)

### Colores: un significado por token en las dos páginas

| Token | Significa **solo** | No usar para |
|---|---|---|
| `--bici` (verde azulado) | siniestro solo con bici | la red ciclista, el foco y los botones |
| `--pat` (naranja) | siniestro solo con patinete | «quizá más de lo normal» y cualquier escala |
| `--amb` (morado) | siniestro con bici **y** patinete | — |
| `--lane` (verde) | red ciclista (las dos páginas) | la bici |
| `--warn` (rojo) | alerta o desviación: por encima de lo normal o de la senda, y «el Plan no lo menciona» | la media de la ciudad y los años observados |
| `--ink` (negro) | dato observado; anillo «el Plan actúa» | la selección |
| `--hl` (amarillo) | **selección** (halo) en las dos páginas | — |
| `--ink2` y `--mute` (grises) | contexto: media de la ciudad, años sin destacar, «normal» | las calles con el mismo valor exacto |

### Formas y trazos

- **Quesito** = mezcla de bici, ambos y patinete, en todas las vistas y en el minimapa. Nunca un color por mayoría.
- **Anillo** = solo lo que dice el Plan (rojo: no lo cita; negro: actuación; ninguno: lo cita sin actuación). La selección no es un anillo.
- **Hueco** = referencia u objetivo (senda). No para «sin factor», «normal» ni «no comparable».
- **Discontinuo** = límite geográfico (celda, zona o radio del contador) en los mapas, y senda en los gráficos. Una sola forma de dibujar la senda en las dos páginas.
- **Tamaño** = número de siniestros, siempre explicado en la leyenda.
- Cada leyenda se genera a partir de las categorías **presentes** en lo dibujado, y cada marca dibujada tiene su entrada.

### Términos (va / es)

| Concepto | Término único | Evitar |
|---|---|---|
| Siniestro con bici y patinete | «bici i patinet» / «bici y patinete» | «les dues», «tots dos alhora», «a la vez», «xoc bici–patinet» |
| Contar cada siniestro una vez | «sinistres amb bici o patinet (cada un una vegada)» | mezclarlo con la suma por vehículo sin decirlo |
| Los 30 | «llocs amb més sinistres» / «lugares con más siniestros» | «punts negres», «pitjors», «on s'acumulen» |
| Estables | «entre els 60 amb més sinistres en els tres períodes» | «dels pitjors», «els primers» |
| μ del modelo | «el normal per al trànsit» / «lo normal para el tráfico» | «el que toca», «esperats», «el que tocaria» |
| p > 0,95 / 0,8-0,95 | «clarament més del normal» / «potser més del normal» | otros umbrales en REL |
| p | «probabilitat que n'hi haja més del normal» | «seguretat» |
| Contadores | «punts de conteo de bicis (probablement també patinets)» | afirmar o negar que cuentan patinetes |
| Senda | «senda proposada (base 2024)» | «senda del Pla» |
| Gravedad | «comparable des de 2024» | «des de 2023» sin matiz |
| Plan sobre un lugar | «cita aquest lloc» / «cita el carrer» / «no el cita» | «el senyala» cuando solo cita la calle |

### Procedimiento

1. Ninguna cifra ni ningún nombre de lugar escrito a mano en las plantillas: todo sale de `kpi` o de `REL`.
2. Un solo `fmt` compartido (con agrupación de miles) y una sola tabla de términos, importada por las dos plantillas.
3. Las búsquedas de texto en `ubicacion` con palabra completa (`\bTURIA\b` no basta: hay que usar la frase).
4. `kind` diag/act explícito en `pdsv_lugares.csv`, no deducido del texto.
5. Hay que añadir a `comprobar.py`: que las claves y categorías de leyenda coincidan entre las dos páginas, que va y es tengan las mismas claves en `Object.assign`, y una prueba de que el Turia no incluye «MARQUES DEL TURIA».
6. Al cambiar de idioma, de vista o de filtro, rehacer **todo** lo que depende de ello (ficha, minimapa y su leyenda, atributos `aria`).

---

## 4. Aplicado en el informe (`web/proto/informe.plantilla.html`, 03/11/2026)

Estado de cada problema en el relato. «OBS» = solo afecta a la herramienta y lo corrige otra sesión.

| # | Estado en el informe |
|---|---|
| A1, A2 | OBS. El relato deja el Turia fuera del mapa y solo cita su n.º del Plan con bici, leído de los datos (`turia_pr`), sin cifras de siniestros. |
| A3 | **Corregido.** Selector `.fig-paso > svg` (y CSS). Comprobado: las leyendas del modo «Sense animació» ya no reciben el escenario. |
| A4 | **Corregido.** Un solo nombre: «xoc bici–patinet / choque bici–patinete» (rótulo, leyenda, textos y aria). Fuera «les dues», «tots dos alhora», «las dos», «a la vez». |
| A5 | **Corregido.** «punts de comptatge / puntos de conteo» (145, con 148 contadores, `n_contadores` exportado) y una sola fórmula prudente: «compten bicis i, probablement, també patinets, sense separar-los». |
| A6 | **Corregido.** 2022 y 2023 en gris como «transició»; la línea solo une 2024 y 2025; marca «comparable des de 2024». Texto: el cambio entra a poco a poco durante 2023. |
| A7 | **Corregido.** «senda proposada (base 2024)» en leyenda, rótulos, tabla y aria; el texto dice que es una propuesta nuestra, no del Plan. |
| A8 | **Corregido en el informe.** `--warn` solo para cifras de alerta en texto (+10,5 %, +322). La barra de 2025, el corchete, «sense línia base», el «canvi de criteri», los segmentos de trafico3 y la cifra de alameda3 pasan a tinta. Paleta común `--bici/--pat/--amb` validada con `validate_palette.js` (claro: pasa, aviso de contraste < 3:1 en patinete y choque, compensado con rótulos y bordes; oscuro: pasa). |
| A9 | Aplicado el criterio: el lugar destacado (Alameda en «dónde») y los tres puntos destacados de trafico3 llevan halo `--sel`, no anillo. |
| A10 | **Corregido.** Red ciclista en `--lane` y con entrada «xarxa ciclista» en la leyenda. |
| A11 | **Corregido.** «Segons el Pla, ja s'hi va fer una auditoria (2024) i una reordenació (2025)»; se cuenta con prudencia la bajada de 2023 a 2025 (16 → 6, de los datos) y por qué se cuenta desde 2023. |
| A12 | OBS. |
| M1 | OBS. En el relato los lugares ya son quesitos (b, p, a). |
| M2 | **Corregido.** El anillo solo cuenta citas del **lugar** (cruce o plaza), no de la calle, de listas de peatones ni de radares de la calle: 26 sin cita (anillo discontinuo), 1 con actuación (continuo: Alameda), 3 citados sin actuación (sin anillo). Regla en `_pl()` de `exportar_web.py`; conviene la misma en la herramienta. |
| M3, M4, M6, M12, M13, M14, M18, M19, M20 | OBS. |
| M5 | **Corregido.** «24 dels 48 sinistres» (mismo denominador que la ficha, 50 %). |
| M7 | **Corregido.** Tres niveles con los umbrales de la herramienta: p > 0,95 claramente (relleno `--ink`), 0,80–0,95 quizá (relleno `--ink2`), resto lo normal (hueco `--line`); 21 y 16 de 145, de los datos. |
| M8 | Parcial. «Sin factor» pasa a relleno claro y «no comparable» a gris lleno; «lo normal» queda hueco `--line` por decisión explícita de la paleta común. |
| M9 | Informe: círculos huecos y línea punteada (la herramienta debe adoptarlo). |
| M10 | **Corregido.** «Els 30 llocs i els 145 punts de comptatge tenen fitxa completa; per a la resta, la llista dels seus sinistres». |
| M11 | **Corregido.** «situa en el mapa el 87 %» (de `cob`, exportado). |
| M15 | **Corregido.** «llocs amb més sinistres» y «entre els 60 llocs amb més sinistres en els tres períodes». |
| M16 | **Corregido.** μ = «el normal per al trànsit / lo normal para el tráfico» (eje, diagonal, textos y tabla); fuera «esperats», «el que tocaria». |
| M17 | Sin cambio (el informe ya usaba la fórmula buena). |
| M21 | **Corregido.** Frase del Turia en «dónde» (n.º del Plan desde los datos). |
| M22 | **Corregido.** Leyendas de trafico y cruce con «punt de comptatge» y «xarxa ciclista». |
| B1 | Parcial. Del dato: n.º del Plan de Alameda y del Turia, años del periodo, cifras de prioridad y de la bajada. Siguen escritos: el nombre traducido del cruce y los nombres de los tres puntos destacados. |
| B2, B7, B8, B9, B11 | OBS. |
| B3 | **Corregido.** Orden fijo bici, patinete, choque en barras, quesitos y leyendas. |
| B4 | **Corregido.** «Sense anell» se dibuja como quesito sin anillo. |
| B5 | **Corregido.** Rótulo de la diagonal anclado a la derecha. |
| B6 | **Corregido.** Leyenda de quien2: «bici (amb els xocs bici–patinet)» y lo mismo para el patinete; aviso en el texto. |
| B10 | **Corregido.** «en 2030 / per a 2030». |
| B12 | **Corregido en el informe.** Fuera `colLugar`, `cuotaPat`, `--mix` y el color por mayoría. |

---

## Aplicado en la herramienta (03/11/2026)

Ámbito: `scripts/exportar_web.py` (salvo la sección «datos del relato»), `web/proto/observatori.plantilla.html` y, para M3, `scripts/transcribir_pdsv.py` (añade la columna `kind`). Comprobado con `exportar_web.py` + `construir_web.py`, sintaxis de cada `<script>` con node, `make comprobar` (sin errores) y una pasada con Chrome sin interfaz: sin errores de página y sin desbordamiento a 360 px.

**Paleta (decisión del usuario, la misma en las dos páginas).** Las categorías, en orden fijo, son: bici `#2a78d6` / `#3987e5`; patinete `#eb6834` / `#d95926`; choque bici–patinete `#1baf7a` / `#199e70`. El resto de tokens:
- selección: `--sel` `#eda100` / `#c98500`, como halo con un hueco del color del fondo;
- red ciclista: `--lane` `#9DB8AE` / `#4E6A60`;
- `--mix` (gris): solo para «varias categorías en el mismo punto» en «Todos los siniestros».

Validación con `validate_palette.js`:
- **Oscuro:** pasa todo sobre `#0F151B`, `#17212A` y `#121A21`.
- **Claro:** pasa todo sobre `#EEF1F2`, salvo el contraste. El naranja (2,82:1) y el aqua (2,48:1) no llegan a 3:1. Sobre la ficha blanca y el fondo del mapa, el aqua queda por debajo (2,82 y 2,65:1). Por eso siempre van con leyenda o etiqueta.
- **Rojo (`--warn`):** solo para el titular cuando «van a más» y para la cifra del desfase con la senda (+322) en el gráfico. No aparece en ninguna marca del mapa.

**Umbrales de exceso:** clarament / claramente si p > 0,95; potser / quizá si 0,8 < p ≤ 0,95; el normal per al trànsit / lo normal para el tráfico en el resto. Se dicen en la explicación, en «Cómo lo sabemos» y en «Método». El porcentaje de la ficha se muestra con un decimal.

**Términos unificados** (va / es):
- «Xoc bici–patinet» / «Choque bici–patinete».
- «Llocs amb més sinistres» / «Lugares con más siniestros» (pestaña y ficha). Se dejan de usar «punts negres», «on s'acumulen» y «dels pitjors».
- Chip de los estables: «Entre els 60 amb més sinistres en els tres períodes».
- «Punts de comptatge» / «puntos de conteo» (145, con 148 contadores), que «compten bicis i, probablement, també patinets, sense separar-los».
- «El normal per al trànsit» / «lo normal para el tráfico».
- «Probabilitat que n'hi haja més del normal», en lugar de «seguretat».
- «Senda proposada (base 2024, −50 % en 2030)».
- La gravedad es «comparable des de 2024».
- La categoría `d` es «xocs entre ciclistes o usuaris de patinet».
- Sobre el Plan: «cita aquest lloc» y «cita el seu carrer».
- Titular nuevo (petición del usuario): «El Pla vol reduir a la meitat els sinistres amb bici i patinet abans de 2030», con la conclusión calculada.

| # | Estado | Qué se ha hecho |
|---|---|---|
| A1 | Hecho | Turia con la frase completa (`\bJARDIN? DEL TURIA\b`, cauce y llit) y un `assert` contra Marqués del Turia, Camp de Túria y Asturias. Resultado: 165 siniestros, 0 geolocalizados y 0 duplicados con los 30 lugares. Se rehacen la binomial (pista «caídas»), el perfil y `por`. |
| A2 | Hecho | El minimapa de la zona solo pinta los siniestros del jardín con punto dentro de la zona (`mm`, `dentro`). Ahora son 0 y la leyenda lo dice. |
| A3 | No aplica | Es del informe. |
| A4 | Hecho (con el nombre que decidió el usuario) | «Xoc bici–patinet» en todas partes, también `pts_lead`. El «96 %» sale de `kpi.amb_solo`. La pista `d` pasa a «ciclistes o usuaris de patinet». |
| A5 | Hecho | Una sola fórmula prudente en la explicación, la ficha, «Cómo lo sabemos» y Limitaciones. «Punts de comptatge», con `kpi.n_contadores` = 148. |
| A6 | Hecho en la herramienta | `lim[0]` y `gravTxt`: «només es pot comparar des de 2024; el canvi comença en 2023». |
| A7 | Hecho | «Senda proposada (base 2024, −50 % en 2030)». |
| A8 | Hecho | La escala de exceso es de un solo tono (tinta, gris y hueco), sin naranja ni rojo. La media de la ciudad va en `--ink2` y los anillos del Plan, en tinta. |
| A9 | Hecho | La selección es un halo `--sel` con hueco, con un radio que depende de la marca, y tiene su entrada en la leyenda. |
| A10 | Hecho en la herramienta | Red ciclista en `--lane` neutro. Los colores se nombran (blau, taronja, verd aigua). |
| A11 | No aplica | Es del informe. La ficha ya decía «Auditoria (2024) i reordenació (2025)». |
| A12 | Hecho | La ficha apila los tres segmentos (b, p, a) con leyenda. |
| M1 | Hecho | En «Todos los siniestros», cada punto lleva el color de su categoría, o gris («diverses categories») si mezcla varias; nunca el de la mayoría. Con zoom ≥ 14, quesitos. |
| M2 | Hecho | Regla común `pl_anillo()` (la misma que el relato): el anillo solo cuenta si el Plan cita el lugar (un cruce o plaza). Resultado: 26 sin cita, 1 con actuación y 3 citados. Las citas de calle y las listas de peatones se rotulan «El Pla no cita aquest lloc, sinó el seu carrer… (sense número d'ordre)» o «També cita el seu carrer». Las actuaciones de calle, como «al carrer: Paseo de la Ciutadella». |
| M3 | Hecho | Columna `kind` explícita en `pdsv_lugares.csv` (`transcribir_pdsv.py`). «Zona de concentración de uso de VMP» es diagnóstico y se presenta como tal. |
| M4 | Hecho | «La majoria» solo por encima del 50 %. Si no, «Els més freqüents són…», y en caso de empate se nombran las dos categorías. |
| M5 | Hecho | La prioridad se cuenta sobre los choques con vehículo (`pm`): «en 6 de cada 10 d'aquests xocs» (24 de 43, como el relato). Las barras dicen «Percentatge sobre tots els sinistres del lloc». |
| M6 | Hecho | Chip con la fuente: «Semàfor a N m (OpenStreetMap)», «Regulador semafòric municipal a N m» o «Sense semàfor conegut a 40 m». Alameda queda con semáforo a 26 m. |
| M7 | Hecho en la herramienta | Tres niveles con los umbrales de arriba. El informe debe usar los mismos. |
| M8 | No aplica | Es del informe. |
| M9 | Hecho | La senda se dibuja con círculos huecos y línea punteada, como en el informe. |
| M10 | No aplica | Es texto del informe. |
| M11 | Hecho | La explicación de «Tots els sinistres» dice que se sitúa el {cobt} (87 %). |
| M12 | Hecho | `textos()` rehace la leyenda del minimapa (`mmLey`), el `aria-label` del buscador y de los botones de zoom, y el `<title>` del gráfico. |
| M13 | Hecho | `gruposMM()` aplica el filtro de año y vehículo del mapa grande. La leyenda dice qué filtro se usa. |
| M14 | Hecho | Un solo `fmt`, con punto de miles siempre. |
| M15 | Hecho | Ver «Términos». |
| M16 | Hecho | Ver «Términos». |
| M17 | Hecho | Se usa la fórmula del informe («l'any que el Pla usa per als ferits greus»). La senda se presenta como nuestra. |
| M18 | Hecho | Nota de unidades y periodos («El Pla compta l'encreuament de 2019 a 2025; nosaltres, el quadrat de 100 m de 2022-2025»). La cifra se traduce. |
| M19 | Hecho | La leyenda dice «Mida: sinistres observats». «Lo normal» es un hueco con borde `--line`. **Aviso:** en el mapa claro, ese borde casi no se distingue de las calles. Si molesta, usar `--ink2` para el borde. |
| M20 | Hecho | Años con datos por punto de conteo (`na`; mismo criterio que `cribado_eb.py`, con `assert` sobre `expo`): 112 tienen 4 años, 26 tienen 3, 2 tienen 2 y 5 tienen 1. IMD = expo / na. El texto dice «en els tres anys amb dades». |
| M21 | No aplica | El Turia es una zona sombreada y el Plan la cita (`pl` = 2, sin anillo). La frase del informe no es de esta parte. |
| M22 | No aplica | Es del informe. |
| B1 | Hecho en parte | El 96 % y los periodos ya salen de los datos. Siguen fijos «2030», «base 2024» y la frase «abans de 2030», que pidió el usuario. |
| B2 | Hecho | «Fins a setembre de 2022, i en menor mesura fins a juny de 2024», calculado a partir de `kpi.cortes`. |
| B3 | Hecho | Orden b, p, a. |
| B4 | Hecho | En la leyenda, «sin anillo» se dibuja como una marca sin anillo. |
| B5 | No aplica | Es del informe. |
| B6 | No aplica | Es del informe. |
| B7 | Hecho | Texto propio para zonas y parques. Las listas sin número dicen «apareix en la llista… sense número d'ordre». |
| B8 | Hecho | El porcentaje se muestra con un decimal (con p = 0,950 sale «Potser» y 95,0 %). |
| B9 | Hecho | «coincideixen… llevat d'algun sinistre solt (el Pla compta per vehicle)». |
| B10 | No aplica / pendiente | El usuario pidió «abans de 2030» en el titular de la herramienta, mientras que el informe usa «en 2030». Hay que decidir si se igualan. |
| B11 | No aplica | Por decisión del usuario, el cuadrado se dibuja alineado con el norte del mapa. La celda de cálculo sigue siendo la UTM. |
| B12 | Hecho | Eliminados `neg-plan`, el `todos` del minimapa, `c3` y el color por mayoría. `--mix` se mantiene solo para la mezcla. |
