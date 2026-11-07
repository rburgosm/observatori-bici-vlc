/* Pie común de las cuatro páginas (lo inserta construir_web.py en el marcador PIE_JS, con window.PIE_INFO delante).
   - Se pinta en cada elemento [data-pie], en el idioma de <html lang> (ca | es), y se repinta al cambiar el idioma.
   - PIE_INFO (de construir_web.py): {conjunto: nombre del fichero del portal, descarga: "AAAA-MM-DD" (fecha de obtención,
     que pide la política de uso del portal), version: "AAAA-MM-DD" (último cambio de docs/cambios.csv),
     colab: [{ent, tipo, va, es, url, desde}] (entidades que colaboran; solo si hay alguna con publicar = si),
     datos: {url, mb} (descarga estable de los datos de la página; solo con PUBLICAR_JSON de construir_web.py)}.
   - Atribución según docs/dataset_licencia_privacidad.md: fuente literal, CC BY 4.0, fecha de obtención, «datos modificados»
     y sin insinuar que el Ajuntament participa o respalda. Licencia de textos y gráficos: CC BY 4.0 (confirmada por el usuario el 04/11/2026). */
(function(){
  var I = window.PIE_INFO || {}, raiz = document.documentElement;
  var dma = function(f){ if (!f) return "—"; var p = f.split("-"); return p[2] + "/" + p[1] + "/" + p[0]; };
  // descarga de los datos: «próximamente» (será un ZIP versionado, pendiente 74). Si construir_web.py publica el JSON
  // estable (PUBLICAR_JSON), PIE_INFO.datos = {url, mb} y aquí sale el enlace.
  var baixa = function(txt, prox, dec){ var d = I.datos; if (!d) return " · " + prox;
    return ' · <a href="' + d.url + '" download>' + txt + '</a> (JSON, ' + String(d.mb).replace(".", dec) + ' MB)'; };
  var CORREU = "hola@observatoribicivlc.org", PORTAL = "https://opendata.vlci.valencia.es";
  // «Hi col·laboren / Colaboran»: PIE_INFO.colab (construir_web.py, de data/processed/colaboran.csv con publicar = si).
  // Sin entidades publicadas no hay PIE_INFO.colab y no se pinta nada, ni el título.
  var esc = function(x){ return String(x == null ? "" : x).replace(/[&<>"]/g, function(c){ return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); };
  var colab = function(l){ var c = I.colab; if (!c || !c.length) return "";
    return '<p class="pie-colab"><b>' + (l === "es" ? "Colaboran" : "Hi col·laboren") + ':</b> ' + c.map(function(e){
      var n = e.url ? '<a href="' + esc(e.url) + '" rel="noopener">' + esc(e.ent) + '</a>' : esc(e.ent);
      var q = l === "es" ? e.es : e.va;
      return n + (q ? ' (' + esc(q) + ')' : ''); }).join(" · ") + '.</p>'; };
  var TXT = {
    ca: function(){ return '<p class="pie-q"><a href="mailto:' + CORREU + '">' + CORREU + '</a> · <a href="cambios.html">Registre de canvis</a>' + baixa("Descarrega les dades d'aquesta pàgina", "Descarrega les dades: pròximament", ",") + '</p>' + colab("ca")
      + '<p>Font de les dades: Ajuntament de València – Dades Obertes (<a href="' + PORTAL + '">opendata.vlci.valencia.es</a>), CC BY 4.0: sinistres de trànsit (<code>' + (I.conjunto || "") + '</code>), carrerer, carril bici i punts de comptatge, obtinguts el ' + dma(I.descarga) + '. Intensitats del carril bici: web de Mobilitat (valencia.es). Pla Director de Seguretat Viària 2026-2030. Semàfors complementaris: © col·laboradors d\'OpenStreetMap (ODbL). <b>Dades modificades</b> per l\'observatori: els sinistres se situen en el mapa amb el carrerer. L\'Ajuntament de València no participa en aquest treball ni l\'avala.</p>'
      + '<p>Textos i gràfics: <a href="https://creativecommons.org/licenses/by/4.0/deed.ca" rel="license">CC BY 4.0</a>. Versió beta del ' + dma(I.version) + '.</p>'; },
    es: function(){ return '<p class="pie-q"><a href="mailto:' + CORREU + '">' + CORREU + '</a> · <a href="cambios.html">Registro de cambios</a>' + baixa("Descarga los datos de esta página", "Descarga los datos: próximamente", ",") + '</p>' + colab("es")
      + '<p>Fuente de los datos: Ajuntament de València – Dades Obertes (<a href="' + PORTAL + '">opendata.vlci.valencia.es</a>), CC BY 4.0: siniestros de tráfico (<code>' + (I.conjunto || "") + '</code>), callejero, carril bici y puntos de conteo, obtenidos el ' + dma(I.descarga) + '. Intensidades del carril bici: web de Movilidad (valencia.es). Plan Director de Seguridad Vial 2026-2030. Semáforos complementarios: © colaboradores de OpenStreetMap (ODbL). <b>Datos modificados</b> por el observatorio: los siniestros se sitúan en el mapa con el callejero. El Ajuntament de València no participa en este trabajo ni lo avala.</p>'
      + '<p>Textos y gráficos: <a href="https://creativecommons.org/licenses/by/4.0/deed.es" rel="license">CC BY 4.0</a>. Versión beta del ' + dma(I.version) + '.</p>'; }
  };
  function estilo(){
    if (document.getElementById("pie-css")) return;
    var s = document.createElement("style"); s.id = "pie-css";
    s.textContent = ".pie{font-size:12.5px;line-height:1.5;color:var(--ink2);border-top:1px solid var(--line);padding-top:16px;padding-bottom:40px;margin-top:20px}"
      + ".pie p{margin:0 0 8px;max-width:110ch}.pie .pie-q{font-size:13.5px;color:var(--ink)}.pie a{color:var(--ink)}"
      + ".pie code{font-size:.95em;overflow-wrap:anywhere}.pie .pie-colab{font-size:13.5px;color:var(--ink)}";
    document.head.appendChild(s);
  }
  // <meta name="description">: en la plantilla, en valenciano; aquí sigue al idioma de la página
  var DESC = {ca: "Seguim els sinistres amb bici i patinet a València amb les dades obertes de l'Ajuntament: on passen, què s'està fent i si el Pla Director de Seguretat Viària 2026-2030 funciona.",
              es: "Seguimos los siniestros con bici y patinete en València con los datos abiertos del Ajuntament: dónde ocurren, qué se está haciendo y si el Plan Director de Seguridad Vial 2026-2030 funciona."};
  function pintar(){
    estilo();
    var l = (raiz.lang || "ca").slice(0, 2) === "es" ? "es" : "ca", m = document.querySelector('meta[name="description"]');
    if (m) m.setAttribute("content", DESC[l]);
    var t = TXT[l](), es = document.querySelectorAll("[data-pie]");
    for (var i = 0; i < es.length; i++){ es[i].classList.add("pie"); es[i].innerHTML = t; }
  }
  if (window.MutationObserver) new MutationObserver(pintar).observe(raiz, {attributes: true, attributeFilter: ["lang"]});
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", pintar); else pintar();
})();
