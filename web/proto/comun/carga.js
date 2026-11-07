/* Carga de los datos de la página (lo inserta construir_web.py en lugar del marcador DATA, justo antes del
   <script src="datos/<página>.<hash>.js" integrity=…> que define la variable global de la página: OBS, REL, MET o CAMBIOS).
   - El script de datos es clásico y bloqueante, en el mismo sitio que antes ocupaban los datos incrustados: la lógica de
     la página (el <script> siguiente) sigue leyendo window.OBS… sin cambios, y lo que va antes (cabecera, textos fijos,
     pie) ya está pintado mientras llegan los datos.
   - Aviso discreto «Carregant les dades…» si tardan más de 400 ms (para no parpadear con la caché o una red rápida);
     se quita al terminar el análisis del documento (DOMContentLoaded: después de la lógica de la página).
   - Si los datos no llegan (red, 404 o integridad SRI distinta): mensaje con «Torna-ho a provar» que se queda, y se
     silencia el error en cadena de la lógica de la página (window.OBS no existe), que ya no aporta nada. */
(function(){
  var lang = "va";
  try { var s = localStorage.getItem("obs-lang"); if (s === "es" || s === "va") lang = s; } catch(e){}
  var TXT = {va: {carga: "Carregant les dades…", fallo: "No s'han pogut carregar les dades d'aquesta pàgina.", otra: "Torna-ho a provar"},
             es: {carga: "Cargando los datos…", fallo: "No se han podido cargar los datos de esta página.", otra: "Vuelve a intentarlo"}}[lang];
  var css = document.createElement("style");
  css.textContent = ".carga-datos{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:1000;max-width:calc(100% - 32px);box-sizing:border-box;"
    + "background:var(--bg);color:var(--ink2);border:1px solid var(--line);border-radius:999px;padding:6px 14px;font-size:13px;line-height:1.4;"
    + "box-shadow:0 2px 8px rgba(0,0,0,.12);visibility:hidden}.carga-datos.ver{visibility:visible}"
    + ".carga-datos.fallo{color:var(--ink);border-radius:8px}.carga-datos a{color:inherit}";
  document.head.appendChild(css);
  var av = document.createElement("p");
  av.className = "carga-datos"; av.setAttribute("role", "status"); av.textContent = TXT.carga;
  document.body.appendChild(av);
  var t = setTimeout(function(){ av.classList.add("ver"); }, 400);
  window.__datosFallo = false;
  window.__cargaFallo = function(){
    window.__datosFallo = true; clearTimeout(t);
    av.className = "carga-datos fallo ver"; av.setAttribute("role", "alert");
    av.innerHTML = TXT.fallo + ' <a href="" onclick="location.reload();return false">' + TXT.otra + "</a>";
  };
  addEventListener("error", function(e){ if (window.__datosFallo && !(e.target && e.target.tagName)) e.preventDefault(); }, true);
  document.addEventListener("DOMContentLoaded", function(){ if (!window.__datosFallo){ clearTimeout(t); av.remove(); } });
})();
