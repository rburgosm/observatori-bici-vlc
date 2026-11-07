// Fichas estáticas (scripts/fichas.py): minimapa y compartir (la lengua, la cabecera y el buscador, en sitio.js). Un solo fichero para todas las fichas:
// build/datos/fichas.<hash8>.js, con integridad SRI. Los datos de cada ficha van en <script type="application/json" id="ficha-datos">
// (no se ejecuta: la CSP no cambia). MapLibre 4.7.1 de cdnjs, la misma versión y el mismo SRI que observatori.html.
(function(){
  "use strict";
  var D = JSON.parse(document.getElementById("ficha-datos").textContent);
  var css = function(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); };
  // ---------- idioma: lo lleva sitio.js (cambia <html lang> y lanza «obs-lang»); aquí solo el título y el minimapa ----------
  var L = (document.documentElement.lang || "ca").slice(0, 2) === "es" ? "es" : "va";
  var mapa = null;
  function idioma(l){ L = l; document.title = D.titulo[l]; pintar(); }
  document.addEventListener("obs-lang", function(e){ idioma(e.detail === "es" ? "es" : "va"); });
  document.addEventListener("tema-cambiado", function(){ pintar(); });
  // ---------- compartir ----------
  document.querySelectorAll("[data-compartir]").forEach(function(b){
    b.addEventListener("click", function(){
      var url = D.url, tit = D.titulo[L];
      if (navigator.share) { navigator.share({title: tit, url: url}).catch(function(){}); return; }
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(function(){ b.textContent = b.getAttribute("data-copiado"); });
    });
  });
  // ---------- minimapa: fondo liso, calles de alrededor, la zona o el tramo y los siniestros (sin teselas) ----------
  function pintar(){
    var cont = document.querySelector('[data-l="' + L + '"] .mapa');
    if (!cont || !window.maplibregl) return;
    if (mapa) { mapa.remove(); mapa = null; }
    if (!D.pts.length) return;
    cont.innerHTML = "";
    var fc = function(f){ return {type: "FeatureCollection", features: f}; };
    var pts = fc(D.pts.map(function(p){ return {type: "Feature", properties: {v: p[2], n: p[3]}, geometry: {type: "Point", coordinates: [p[0], p[1]]}}; }));
    mapa = new maplibregl.Map({container: cont, attributionControl: false, interactive: true, keyboard: false, dragRotate: false, pitchWithRotate: false,
      scrollZoom: false, bounds: D.bbox, fitBoundsOptions: {padding: 36, maxZoom: 15.6},
      locale: {"Map.Title": L === "es" ? "Minimapa de los accidentes de esta ficha" : "Minimapa dels accidents d'aquesta fitxa"},
      style: {version: 8, sources: {}, layers: [{id: "bg", type: "background", paint: {"background-color": css("--mapbg")}}]}});
    mapa.touchZoomRotate.disableRotation();
    // es una imagen de apoyo (role="img" con su texto en el contenedor): el lienzo, fuera del orden de Tab y del árbol accesible
    mapa.getCanvas().setAttribute("tabindex", "-1"); mapa.getCanvas().setAttribute("aria-hidden", "true");
    mapa.on("load", function(){
      mapa.addSource("calles", {type: "geojson", data: D.calles});
      mapa.addLayer({id: "calles", type: "line", source: "calles", paint: {"line-color": css("--calle"),
        "line-width": ["interpolate", ["linear"], ["zoom"], 14, 1.5, 18, 9]}});
      mapa.addLayer({id: "sel", type: "line", source: "calles", filter: ["==", ["get", "s"], 1], paint: {"line-color": css("--calle-sel"),
        "line-opacity": .8, "line-width": ["interpolate", ["linear"], ["zoom"], 14, 2.5, 18, 8]}});
      if (D.zona) {
        mapa.addSource("zona", {type: "geojson", data: D.zona});
        var linea = D.zona.type === "LineString" || D.zona.type === "MultiLineString";
        if (!linea) mapa.addLayer({id: "zona-f", type: "fill", source: "zona", paint: {"fill-color": css("--ink"), "fill-opacity": .08}});
        mapa.addLayer({id: "zona", type: "line", source: "zona", paint: {"line-color": css("--ink"), "line-width": linea ? 4 : 1.5,
          "line-dasharray": linea ? [1, 0] : [3, 2], "line-opacity": linea ? .85 : 1}});
      }
      mapa.addSource("pts", {type: "geojson", data: pts});
      mapa.addLayer({id: "pts", type: "circle", source: "pts", paint: {
        "circle-color": ["match", ["get", "v"], "b", css("--bici"), "p", css("--pat"), css("--amb")],
        "circle-radius": ["interpolate", ["linear"], ["get", "n"], 1, 5, 10, 12, 40, 22],
        "circle-opacity": .85, "circle-stroke-color": css("--surface"), "circle-stroke-width": 1.2}});
    });
  }
  idioma(L);
})();
