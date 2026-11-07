# Enfoque del observatorio (03/11/2026)

Tras revisar las fechas del Plan Director de Seguridad Vial 2026-2030 (ver las notas internas de trabajo, «Fechas del Plan y año base»), la base de la meta pasa a ser **2025**. Como no hay datos de 2026, **hoy no se puede evaluar si el Plan funciona**. El proyecto se reorganiza en torno a tres preguntas, de la que se puede responder ya a la que tendrá que esperar.

## 1. Qué pasa: archivo público y mapas (ya se puede)
- El histórico de los siniestros de bici y patinete (2022-2025), **geolocalizado** (el portal solo da la calle escrita), descargable y versionado.
- Mapas para cualquier persona: dónde se acumulan, con quién se choca, por qué y a qué hora, más el detalle de cada calle.
- Cada año nuevo se añade con `make` y se comprueba con `make comprobar`.
- **Estado:** casi entero (herramienta, informe y método). Falta la descarga de los datos y publicarlo.

## 2. Qué se está haciendo: «El Plan, al día» (ya se puede, con trabajo continuo)
Es el cuadro de mando que el propio Plan reconoce como «no existente» (acción 7.1.1), centrado en bici y patinete.
- **Actuaciones del Plan que afectan a bici y patinete**, cada una con su estado, la fecha y el enlace a la prueba (nota de prensa, acuerdo de Junta de Gobierno, BOP, perfil del contratante). Estados: sin información publicada / en marcha / hecha. Ejemplos:
  - auditorías de seguridad vial (de 4 a 30, acción 3.7);
  - paneles contadores ciclistas (de 3 a 9, acción 1.3.1);
  - zonas 30 (del 64 % al 95 % de las calles, acción 3.5);
  - controles de patinetes (acción 2.1);
  - medidas en zonas de elevada siniestralidad ciclista o con VMP (acción 3.2.2);
  - consulta en mapa de los siniestros (acción 6.1.1);
  - convenios con universidades (acción 6.2);
  - cuadro de mando y memoria anual (acciones 7.1.1 y 7.1.2).
- **En el mapa:** las actuaciones junto a los puntos negros. Hoy (04/11/2026), de los 30 lugares con más siniestros el Plan cita 5 por su nombre y 12 por su calle, y de 13 no dice nada. Como el Plan solo publica los tres primeros de cada lista, eso no prueba que estén fuera de su radar: pedimos la lista completa.
- **Indicadores del Plan calculables con datos abiertos** (5 de 119), con su valor cada año.
- **Fuente de datos:** un CSV propio (`data/processed/plan_seguimiento.csv`) con acción, actuación, lugar, estado, fecha, fuente (URL) y fecha de comprobación. Se recoge a mano o con un agente y se actualiza cada cierto tiempo. Es un trabajo ideal para un socio (València en Bici, la universidad).
- **Tono:** seguimiento, no auditoría. «Esto es lo que hemos encontrado publicado», con fuentes, y abierto a que el Ayuntamiento corrija o complete.

## 3. Si funciona: la meta (cuando haya datos de 2026)
- Lo que se mide es el indicador de la acción 3.2.2 del Plan (no la meta global, que es de fallecidos y heridos graves). La base es 2025 (1.659 siniestros), con la meta de 830 en 2030 y una bajada de en torno al 13 % anual. 2025 es el pico de la serie: se comprueba con la media 2023-2025 (1.544 → 772). 2024 (1.501 → 751) queda solo como tabla en metode. Detalle en las notas internas de trabajo, «Meta: decisiones del 04/11».
- Cada año se juzga con un margen de Poisson al 95 % alrededor de la senda (por debajo · compatible · por encima; 2026: 1.370-1.519) y se lee junto a dos series de control (con heridos y cuota sobre la ciudad).
- El primer año evaluable es 2026, cuando se publique. Mientras tanto, la portada dice de dónde se parte y qué hace falta.
- **Primeras señales, solo como contexto externo:** el balance policial de enero-mayo de 2026 (unos 50 siniestros con patinete menos que en el mismo periodo de 2025), pendiente de confirmar con datos abiertos.

## Por qué esto es también una reclamación de transparencia
Sin los datos de 2026 en abierto, nadie fuera del Ayuntamiento puede seguir la meta del Plan. El observatorio lo hace visible y **pide su publicación**:
- La web lo dice en la portada («El primer año del Plan, 2026, aún no está publicado») y en la página de método.
- Solicitudes formales de información (borradores internos):
  - 01 (Servicio de Movilidad);
  - 03 (portal de datos abiertos);
  - **09 (solicitud de acceso y de publicación de los siniestros de 2026, por la ley de transparencia)**.
- Argumentos:
  - el propio Plan prevé indicadores, memoria anual y cuadro de mando;
  - el dataset existe para 2022-2025;
  - la ley obliga a publicar la información relevante para controlar la actuación pública;
  - el Ayuntamiento tiene una política de datos abiertos.
