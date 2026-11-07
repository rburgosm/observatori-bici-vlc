/* Tema claro, oscuro o automático, común a todas las páginas (lo inserta construir_web.py en el marcador TEMA_JS).
   - Va en un <script> al principio del <body>: aplica el tema guardado antes del primer pintado.
   - Automático (por defecto): sin data-theme en <html>; manda prefers-color-scheme. Claro u oscuro: data-theme="light" | "dark".
   - Se recuerda en localStorage ("obs-tema"), siempre con try/catch.
   - Botón: cualquier <button data-tema>; ciclo Automático → Claro → Oscuro. Textos según <html lang> (ca | es).
   - Cada cambio efectivo (botón, o el sistema estando en Automático) lanza en document el evento "tema-cambiado"
     con detail {tema: "auto"|"light"|"dark", oscuro: bool}: cada página repinta lo que no sale de var() (MapLibre, canvas, d3). */
(function(){
  var CLAVE = "obs-tema", ORDEN = ["auto", "light", "dark"], raiz = document.documentElement;
  var mq = window.matchMedia ? matchMedia("(prefers-color-scheme: dark)") : null;
  var TXT = {
    ca: {auto: "Auto", light: "Clar", dark: "Fosc", nom: {auto: "automàtic", light: "clar", dark: "fosc"},
         aria: function(a, s){ return "Tema: " + a + ". Canvia a " + s; }},
    es: {auto: "Auto", light: "Claro", dark: "Oscuro", nom: {auto: "automático", light: "claro", dark: "oscuro"},
         aria: function(a, s){ return "Tema: " + a + ". Cambiar a " + s; }}
  };
  var ICO = {
    auto: '<circle cx="8" cy="8" r="6"/><path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor" stroke="none"/>',
    light: '<circle cx="8" cy="8" r="3"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6 13 13M3 13l1.4-1.4M11.6 4.4 13 3"/>',
    dark: '<path d="M13.5 9.5A6 6 0 0 1 6.5 2.5a6 6 0 1 0 7 7z"/>'
  };
  function leer(){ try { var v = localStorage.getItem(CLAVE); return ORDEN.indexOf(v) >= 0 ? v : "auto"; } catch(e){ return "auto"; } }
  function guardar(v){ try { if (v === "auto") localStorage.removeItem(CLAVE); else localStorage.setItem(CLAVE, v); } catch(e){} }
  function esOscuro(v){ return v === "dark" || (v === "auto" && !!(mq && mq.matches)); }
  var tema = leer();
  function poner(v){ if (v === "auto") raiz.removeAttribute("data-theme"); else raiz.setAttribute("data-theme", v); }
  poner(tema);   // antes del primer pintado

  function botones(){
    var t = TXT[(raiz.lang || "ca").slice(0, 2) === "es" ? "es" : "ca"], sig = ORDEN[(ORDEN.indexOf(tema) + 1) % 3];
    var bs = document.querySelectorAll("button[data-tema]");
    for (var i = 0; i < bs.length; i++){
      var b = bs[i];
      b.setAttribute("data-estado", tema);
      b.setAttribute("aria-label", t.aria(t.nom[tema], t.nom[sig]));
      b.title = b.getAttribute("aria-label");
      b.innerHTML = '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">' + ICO[tema] + '</svg>'
                  + '<span class="tema-txt">' + t[tema] + '</span>';
    }
  }
  function avisar(){
    try { document.dispatchEvent(new CustomEvent("tema-cambiado", {detail: {tema: tema, oscuro: esOscuro(tema)}})); } catch(e){}
  }
  function fijar(v){ tema = v; poner(v); guardar(v); botones(); avisar(); }

  document.addEventListener("click", function(ev){
    var b = ev.target && ev.target.closest ? ev.target.closest("button[data-tema]") : null;
    if (b) fijar(ORDEN[(ORDEN.indexOf(tema) + 1) % 3]);
  });
  if (mq){
    var cambioSistema = function(){ if (tema === "auto") avisar(); };
    if (mq.addEventListener) mq.addEventListener("change", cambioSistema); else if (mq.addListener) mq.addListener(cambioSistema);
  }
  // los textos siguen al idioma de la página (las páginas cambian <html lang> al pulsar VA/ES)
  if (window.MutationObserver) new MutationObserver(botones).observe(raiz, {attributes: true, attributeFilter: ["lang"]});
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", botones); else botones();

  window.Tema = {actual: function(){ return tema; }, oscuro: function(){ return esOscuro(tema); }, fijar: function(v){ if (ORDEN.indexOf(v) >= 0) fijar(v); }};
})();
