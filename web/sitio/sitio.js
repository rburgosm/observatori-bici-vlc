// Web pública: comportamiento común de todas las páginas y de las fichas (scripts/construir_sitio.py lo publica en
// build/datos/sitio.<hash8>.js con SRI). Sin dependencias.
//  - Lengua: una URL con las dos lenguas. <html lang> («ca» o «es») decide qué se ve (comun.css); un script en <head> lo
//    fija antes del primer pintado con localStorage «obs-lang». Aquí: botones va/es, título y description, y el evento
//    «obs-lang» (detail: "va" | "es") para que cada página repinte lo suyo (fichas: minimapa). En las páginas que
//    heredan la lógica de la web anterior (mapa y método), además se pulsa su botón oculto #l-va / #l-es.
//  - Menú plegable en el móvil (se superpone al contenido: no lo desplaza).
//  - Buscador de la cabecera y de la portada: índice de las fichas (window.FICHAS = [[clase, slug, nombre va, nombre es,
//    accidentes], …], de scripts/fichas.py) → <raíz><clase>/<slug>/. Sin coincidencia: el mapa con #cerca=texto.
//  - Índices de lugares y calles: filtro de texto y orden (la lista completa ya está en el HTML).
(function(){
  "use strict";
  var raiz = document.documentElement, B = document.body;
  var RAIZ = B.getAttribute("data-raiz") || "";
  var lang = function(){ return (raiz.lang || "ca").slice(0, 2) === "es" ? "es" : "va"; };
  // ---------- lengua ----------
  function poner(l, avisar){
    raiz.lang = l === "es" ? "es" : "ca";
    try { localStorage.setItem("obs-lang", l); } catch (e) {}
    document.querySelectorAll(".lenguas button[data-lang]").forEach(function(b){ b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === l)); });
    var vieja = document.getElementById("l-" + l);              // páginas con la lógica anterior (mapa, método)
    if (vieja && avisar) vieja.click();
    document.querySelectorAll("[data-ph-" + l + "]").forEach(function(i){ i.placeholder = i.getAttribute("data-ph-" + l); });
    // nombres accesibles en la lengua de la página (aria-label no admite los span data-l)
    document.querySelectorAll("[data-aria-" + l + "]").forEach(function(i){ i.setAttribute("aria-label", i.getAttribute("data-aria-" + l)); });

    var t = B.getAttribute("data-titulo-" + l); if (t) document.title = t;
    var d = B.getAttribute("data-desc-" + l), m = document.querySelector('meta[name="description"]');
    if (d && m) m.setAttribute("content", d);
    if (avisar) { try { document.dispatchEvent(new CustomEvent("obs-lang", {detail: l})); } catch (e) {} }
  }
  document.querySelectorAll(".lenguas button[data-lang]").forEach(function(b){
    b.addEventListener("click", function(){ poner(b.getAttribute("data-lang"), true); });
  });
  poner(lang(), false);
  // la lógica anterior (mapa, método) pinta su título al cargar: se repone el de la página
  addEventListener("load", function(){ var t = B.getAttribute("data-titulo-" + lang()); if (t) document.title = t; });
  // ---------- menú del móvil ----------
  var cab = document.querySelector(".cabecera"), bm = cab && cab.querySelector(".b-menu");
  if (bm) {
    bm.addEventListener("click", function(){ var a = cab.classList.toggle("abierto"); bm.setAttribute("aria-expanded", String(a)); });
    document.addEventListener("keydown", function(e){ if (e.key === "Escape" && cab.classList.contains("abierto")) { cab.classList.remove("abierto"); bm.setAttribute("aria-expanded", "false"); bm.focus(); } });
    document.addEventListener("click", function(e){ if (cab.classList.contains("abierto") && !cab.contains(e.target)) { cab.classList.remove("abierto"); bm.setAttribute("aria-expanded", "false"); } });
    cab.addEventListener("focusout", function(e){ if (cab.classList.contains("abierto") && e.relatedTarget && !cab.contains(e.relatedTarget)) { cab.classList.remove("abierto"); bm.setAttribute("aria-expanded", "false"); } });   // al salir del menú con Tab
  }
  // ---------- buscador → fichas ----------
  var sinT = function(s){ return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9ñç·' ]/g, " ").replace(/\s+/g, " ").trim(); };
  var IDX = null;
  function indice(){ if (!IDX) IDX = (window.FICHAS || []).map(function(f){ return [f, sinT(f[2] + " " + f[3])]; }); return IDX; }
  var umbral = function(){ return (window.FICHAS || []).reduce(function(m, f){ return f[0] === "lloc" ? Math.min(m, f[4]) : m; }, 99); };
  var TXT = {va: {lloc: "lloc", carrer: "carrer", acc: function(n){ return n === 1 ? "1 accident" : n + " accidents"; }, mapa: "Busca-ho en el mapa",
                  cap: function(q, u){ return "No hi ha cap fitxa per a «" + q + "». Només en tenen els llocs i carrers amb " + u + " accidents o més."; }},
             es: {lloc: "lugar", carrer: "calle", acc: function(n){ return n === 1 ? "1 accidente" : n + " accidentes"; }, mapa: "Búscalo en el mapa",
                  cap: function(q, u){ return "No hay ninguna ficha para «" + q + "». Solo la tienen los lugares y calles con " + u + " accidentes o más."; }}};
  // 07/11/2026: abreviaturas y tipos de vía no cuentan («avda francia», «pza españa»), y algunos nombres se buscan en las
  // dos lenguas («reino de valencia» → «regne»). Cada palabra vale si aparece ella o un sinónimo.
  var NO_CUENTA = " av avda avd avg avenida avinguda c cl calle carrer pl pza plz plaza placa pg pº pso paseo passeig cm cami camino ctra carretera de del la el les los las l d i y en ";
  var SINON = {reino: ["regne"], regne: ["reino"], espana: ["espanya"], espanya: ["espana"], francia: ["franca"], franca: ["francia"],
               puerto: ["port"], port: ["puerto"], puente: ["pont"], pont: ["puente"], alameda: ["albereda"], albereda: ["alameda"],
               san: ["sant"], sant: ["san"], ayuntamiento: ["ajuntament"], ajuntament: ["ayuntamiento"], pio: ["pius"], pius: ["pio"],
               blasco: ["blasco"], ibanez: ["ibanyez"], ibanyez: ["ibanez"], jose: ["josep"], josep: ["jose"], juan: ["joan"], joan: ["juan"]};
  var palabras = function(q){
    var ws = sinT(q).split(" ").filter(Boolean), utiles = ws.filter(function(w){ return NO_CUENTA.indexOf(" " + w + " ") < 0; });
    return utiles.length ? utiles : ws;
  };
  var coincide = function(t, ws){ return ws.every(function(w){ return t.indexOf(w) >= 0 || (SINON[w] || []).some(function(s){ return t.indexOf(s) >= 0; }); }); };
  window.OBS_BUSCA = {palabras: palabras, coincide: coincide};       // el buscador del mapa usa la misma regla
  function buscar(q){
    var ws = palabras(q); if (!ws.length) return [];
    return indice().filter(function(x){ return coincide(x[1], ws); })
      .map(function(x){ return x[0]; }).sort(function(a, b){ return b[4] - a[4]; }).slice(0, 8);
  }
  var url = function(f){ return RAIZ + f[0] + "/" + f[1] + "/"; };
  document.querySelectorAll("form[data-busca]").forEach(function(form){
    var inp = form.querySelector("input[type=search]"), lista = form.querySelector(".sug");
    if (!inp || !lista) return;
    // región viva aparte (no la lista entera): «N resultats» o «no hi ha cap fitxa…» (4.1.3; prueba de teclado del 07/11/2026)
    var viva = document.createElement("span"); viva.className = "sr"; viva.setAttribute("role", "status"); form.appendChild(viva);
    var tViva = null;
    var avisa = function(t){ clearTimeout(tViva); tViva = setTimeout(function(){ viva.textContent = t; }, 400); };
    function pintar(){
      var l = lang(), t = TXT[l], hs = buscar(inp.value);
      lista.innerHTML = "";
      hs.forEach(function(f){
        var li = document.createElement("li"), a = document.createElement("a"), k = document.createElement("span");
        a.href = url(f); a.textContent = (l === "es" ? f[3] : f[2]) + " ";
        k.className = "k"; k.textContent = "· " + t[f[0]] + " · " + t.acc(f[4]); a.appendChild(k); li.appendChild(a); lista.appendChild(li);
      });
      if (inp.value.trim().length > 2 && !hs.length) {
        var li0 = document.createElement("li"); li0.className = "sin"; li0.textContent = t.cap(inp.value.trim(), umbral()); lista.appendChild(li0);
        avisa(li0.textContent);
      } else if (hs.length) avisa(hs.length + (l === "es" ? " resultados; flecha abajo para elegir" : " resultats; fletxa avall per a triar"));
      else avisa("");
      if (inp.value.trim()) {
        var li = document.createElement("li"), a = document.createElement("a");

        a.href = RAIZ + "mapa/#cerca=" + encodeURIComponent(inp.value.trim()); a.textContent = t.mapa + " →"; li.appendChild(a); lista.appendChild(li);
      }
      lista.hidden = !lista.children.length;
    }
    inp.addEventListener("input", pintar);
    inp.addEventListener("keydown", function(e){
      if (e.key === "ArrowDown" && !lista.hidden) { e.preventDefault(); var a = lista.querySelector("a"); if (a) a.focus(); }
      else if (e.key === "Escape") { lista.hidden = true; }
    });
    lista.addEventListener("keydown", function(e){
      var xs = [].slice.call(lista.querySelectorAll("a")), j = xs.indexOf(document.activeElement);
      if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); var k = j + (e.key === "ArrowDown" ? 1 : -1); if (k < 0) inp.focus(); else xs[Math.min(k, xs.length - 1)].focus(); }
      else if (e.key === "Escape") { lista.hidden = true; inp.focus(); }

    });
    document.addEventListener("click", function(e){ if (!form.contains(e.target)) lista.hidden = true; });
    form.addEventListener("submit", function(e){
      e.preventDefault(); var q = inp.value.trim(); if (!q) { inp.focus(); return; }
      var hs = buscar(q); location.href = hs.length ? url(hs[0]) : RAIZ + "mapa/#cerca=" + encodeURIComponent(q);
    });
  });
  // ---------- índices de lugares y calles: filtro de texto y orden (por nombre o por accidentes) ----------
  var ix = document.querySelector("[data-indice]");
  if (ix) {
    var fil = ix.querySelector("input[type=search]"), cuenta = ix.querySelector(".cuenta");
    var orden = ix.getAttribute("data-orden-def") || "nom";
    var items = [].slice.call(document.querySelectorAll(".idx li"));
    items.forEach(function(li){ li._t = sinT(li.textContent); });
    var aplicar = function(){
      var ws = sinT(fil.value).split(" ").filter(Boolean);
      items.forEach(function(li){ li.hidden = !ws.every(function(w){ return li._t.indexOf(w) >= 0; }); });
      document.querySelectorAll(".idx-grupo").forEach(function(g){ g.hidden = !g.querySelector("li:not([hidden])"); });
      document.querySelectorAll(".letras a").forEach(function(a){ var g = document.getElementById(a.getAttribute("href").slice(1)); a.parentNode.hidden = !!(g && g.hidden); });
      var n = document.querySelectorAll('[data-l="' + lang() + '"] [data-lista="' + orden + '"] .idx li:not([hidden])').length;
      if (cuenta) cuenta.textContent = cuenta.getAttribute("data-" + lang()).replace("{n}", n.toLocaleString(lang() === "es" ? "es-ES" : "ca-ES"));
    };
    fil.addEventListener("input", aplicar);
    document.addEventListener("obs-lang", aplicar);
    ix.querySelectorAll("button[data-orden]").forEach(function(b){
      b.addEventListener("click", function(){
        orden = b.getAttribute("data-orden");
        ix.querySelectorAll("button[data-orden]").forEach(function(x){ x.setAttribute("aria-pressed", String(x === b)); });
        document.querySelectorAll("[data-lista]").forEach(function(d){ d.hidden = d.getAttribute("data-lista") !== orden; });
        aplicar();
      });
    });
    var q0 = new URLSearchParams(location.search).get("q"); if (q0) fil.value = q0;
    aplicar();
  }
  // ---------- mapas del informe recorribles (la lógica del informe anterior, web/proto/informe.plantilla.html) ----------
  // .mapa[data-explora] = [[x %, y %, r % del ancho, corto va, corto es, largo va, largo es, enlace], …] en orden de
  // recorrido (scripts/construir_sitio.py, mapa_explora). Flechas: siguiente y anterior; Inicio y Fin: primero y último;
  // Intro abre la ficha; Esc oculta la etiqueta. Ratón: el más cercano a 16 px o menos (24 px al tocar). Cada paso se
  // anuncia en aria-live. Sin JavaScript queda la imagen con su texto alternativo. El anillo solo se desliza si no se
  // pide menos movimiento (comun.css).
  var EXP = {va: "Mapa explorable amb el teclat: fletxes per a passar d'un punt a un altre, Inici i Fi per al primer i l'últim, Intro per a obrir-ne la fitxa, Esc per a amagar l'etiqueta.",
             es: "Mapa explorable con el teclado: flechas para pasar de un punto a otro, Inicio y Fin para el primero y el último, Intro para abrir su ficha, Esc para ocultar la etiqueta."};
  var mapasExp = document.querySelectorAll(".mapa[data-explora]");
  if (mapasExp.length) {
    var ayuda = document.createElement("p"), vivo = document.createElement("p");
    ayuda.className = vivo.className = "sr"; ayuda.id = "exp-ayuda"; vivo.setAttribute("aria-live", "polite");
    B.appendChild(ayuda); B.appendChild(vivo);
    var ponAyuda = function(){ ayuda.textContent = EXP[lang()]; };
    ponAyuda(); document.addEventListener("obs-lang", ponAyuda);
    var anunciar = function(t){ vivo.textContent = ""; setTimeout(function(){ vivo.textContent = t; }, 50); };
    mapasExp.forEach(function(m, k){
      var D; try { D = JSON.parse(m.getAttribute("data-explora")); } catch (e) { return; }
      if (!D || !D.length) return;
      var alt = m.querySelector(".sr");
      if (alt) { alt.id = alt.id || "exp-alt-" + k; m.setAttribute("aria-labelledby", alt.id); }
      m.tabIndex = 0; m.setAttribute("role", "application"); m.setAttribute("aria-describedby", "exp-ayuda");
      var an = document.createElement("span"), et = document.createElement("span");
      an.className = "exp-anillo"; et.className = "exp-etq"; an.hidden = et.hidden = true;
      an.setAttribute("aria-hidden", "true"); et.setAttribute("aria-hidden", "true");
      m.appendChild(an); m.appendChild(et);
      var j = -1, cur = null;
      var ocultar = function(){ an.hidden = et.hidden = true; cur = null; };
      var es = function(){ return lang() === "es"; };
      function pintar(i, anuncia){
        var d = D[i], W = m.clientWidth, H = m.clientHeight, x = d[0] / 100 * W, y = d[1] / 100 * H, r = d[2] / 100 * W + 5;
        cur = i;
        an.style.left = x + "px"; an.style.top = y + "px"; an.style.width = an.style.height = 2 * r + "px";
        an.hidden = et.hidden = false;
        et.style.left = "0px"; et.style.top = "0px"; et.textContent = d[es() ? 4 : 3];
        // al lado del punto (a la izquierda si está en la parte derecha); si no cabe en ningún lado, encima o debajo
        var ew = et.offsetWidth, eh = et.offsetHeight, izq = x > W * .55;
        var cabeI = x - r - 4 - ew >= 4, cabeD = x + r + 4 + ew <= W - 4, lx, ly = y - eh / 2;
        if ((izq && cabeI) || (!cabeD && cabeI)) lx = x - r - 4 - ew;
        else if (cabeD) lx = x + r + 4;
        else { lx = x - ew / 2; ly = y - r - 4 - eh >= 4 ? y - r - 4 - eh : y + r + 4; }
        et.style.left = Math.max(4, Math.min(W - ew - 4, lx)) + "px";
        et.style.top = Math.max(4, Math.min(H - eh - 4, ly)) + "px";
        if (anuncia) anunciar(d[es() ? 6 : 5]);
      }
      function cercano(e, radio){
        var b = m.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, best = null, bd = radio * radio;
        D.forEach(function(d, i){ var dx = d[0] / 100 * b.width - x, dy = d[1] / 100 * b.height - y, dd = dx * dx + dy * dy;
          if (dd < bd) { bd = dd; best = i; } });
        return best;
      }
      m.addEventListener("focus", function(){
        if (!m.matches(":focus-visible")) return;             // con el ratón, la etiqueta la decide el puntero
        if (j < 0) j = 0; pintar(j, true);
      });
      m.addEventListener("blur", ocultar);
      m.addEventListener("keydown", function(e){
        if (e.altKey || e.ctrlKey || e.metaKey) return;
        var n = D.length;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") j = (j + 1) % n;
        else if (e.key === "ArrowLeft" || e.key === "ArrowUp") j = j < 0 ? n - 1 : (j - 1 + n) % n;
        else if (e.key === "Home") j = 0;
        else if (e.key === "End") j = n - 1;
        else if (e.key === "Escape") { if (cur != null) { e.preventDefault(); ocultar(); } return; }
        else if (e.key === "Enter") { if (j >= 0) { e.preventDefault(); location.href = D[j][7]; } return; }
        else return;
        e.preventDefault(); pintar(j, true);
      });
      // 1.4.13 (prueba visual del 07/11/2026): Esc la cierra también con el ratón, y no desaparece si el puntero pasa encima
      document.addEventListener("keydown", function(e){ if (e.key === "Escape" && cur != null && document.activeElement !== m) ocultar(); });
      m.addEventListener("pointermove", function(e){
        if (e.pointerType !== "mouse") return;
        if (cur != null && !et.hidden) { var q = et.getBoundingClientRect();
          if (e.clientX >= q.left - 4 && e.clientX <= q.right + 4 && e.clientY >= q.top - 4 && e.clientY <= q.bottom + 4) return; }

        var i = cercano(e, 16);

        if (i != null) { if (i !== cur) pintar(i, false); }
        else if (document.activeElement !== m && cur != null) ocultar();
      });
      m.addEventListener("pointerdown", function(e){
        if (e.pointerType === "mouse") return;
        var i = cercano(e, 24); if (i != null) { j = i; pintar(i, false); } else ocultar();
      });
      m.addEventListener("pointerleave", function(e){ if (e.pointerType === "mouse" && document.activeElement !== m) ocultar(); });
      document.addEventListener("obs-lang", function(){ if (cur != null) pintar(cur, false); });
      addEventListener("resize", function(){ if (cur != null) pintar(cur, false); });
    });
  }
})();
