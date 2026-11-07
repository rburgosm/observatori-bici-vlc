"""Comprobaciones de los datos y de la web para cuando el portal publica datos nuevos (p. ej. 2026).

Imprime una línea OK / AVISO / ERROR por comprobación y termina con código 1 si hay algún ERROR.
- años del dataset crudo y de siniestros_geo.csv (frente a la referencia);
- cobertura de geolocalización por año y por mes (bici/VMP y total);
- categorías nuevas de gravedad, tipo y unidades (referencia en data/processed/referencia_categorias.csv,
  que se crea con lo visto la primera vez; para aceptar una categoría nueva, añadirla a mano a ese CSV);
- totales anuales de bici y VMP frente al Plan Director, y la unión de 2024;
- que el año base exportado sea 2025 (1.659) y que los tres niveles del anillo del Plan sumen y sean iguales en las tres páginas;
- meta (scripts/meta.py): base, comprobación con la media, banda y juicio recalculados desde la serie; el juicio probado con un
  año simulado (no se guarda); series de control coherentes; Paseo de la Alameda igual en informe y metode;
- lugares (nudos de cruce y tramos de calle, scripts/lugares.py): 30 con su geometría, los mismos que outputs/lugares_nudos.csv,
  sin restos de la rejilla de 100 m; persistencia fuera de muestra igual en las tres páginas y coherente con
  outputs/lugares_nudos_resumen.json; pista igual en herramienta y método;
- que cada lugar de pdsv_lugares.csv esté decidido en exportar_web.py (CLAVES o SIN_CLAVE con motivo);
- que la web esté exportada después de los datos y que va y es tengan las mismas claves, cada una definida una sola vez;
- años del último dato: tipo de accidente del último año, periodos de la persistencia de los datos, panel de uso hasta
  el último año con IMD (probado con un año simulado sin IMD, sin NaN);
- que las páginas no tengan años escritos a mano (salvo las excepciones justificadas de EXC_AÑOS) ni los scripts
  de make filtros con un año literal;
- errores detectados en los datos del Ajuntament: data/processed/incidencias_datos.csv igual que la tabla de metode.js, estados
  coherentes con la fecha de comunicación y avisos de la última re-verificación (scripts/incidencias.py, make incidencias);
- «Hi col·laboren / Colaboran» (data/processed/colaboran.csv): cada fila publicada (publicar = si) con fecha, prueba, tipo
  y texto en va y es, y datos/colaboran.json al día;
- que cada página de web/proto/build/ cargue sus datos de build/datos/<página>.<hash>.js con el SRI correcto y el mismo
  contenido que web/proto/datos/, que el HTML no los incruste y, si se publica (PUBLICAR_JSON, hoy desactivado), que la
  descarga estable <página>.json lleve esos datos.
Uso: .venv/bin/python -I scripts/comprobar.py   (o make comprobar)"""
import ast, json, re, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/siniestros"; GEO = ROOT / "data/processed/observatorio.sqlite"   # la base (siniestros, lugares, Plan)
sys.path.insert(0, str(ROOT / "scripts")); import bd as BD                                    # lectura de la base (scripts/bd.py)
_con = BD.conectar()
REF = ROOT / "data/processed/referencia_categorias.csv"
WEB = ROOT / "web/proto"
# Plan Director de Seguridad Vial 2026-2030, siniestros por año según sus tablas (por vehículo, sin desduplicar; data/raw/pdsv/pdsv.txt)
PLAN = {"VMP": {2022: 825, 2023: 1003, 2024: 1054, 2025: 1192}, "bici": {2022: 576, 2023: 538, 2024: 511, 2025: 549}}
PLAN_UNION_2024, TOL = 1501, 0.01
# año base de la meta 3.2.2 (decisión del 03/11/2026; AÑO_BASE de exportar_web.py) y su total de bici o VMP
AÑO_BASE_ESPERADO, BASE_ESPERADA = 2025, 1659
COB_AÑO_MIN, COB_MES_MIN = 0.80, 0.60
errores = 0


def msg(nivel, texto):
    global errores
    errores += nivel == "ERROR"
    print(f"{nivel:5s}  {texto}")


def pc(x): return f"{100 * x:.1f} %".replace(".", ",")


# ---------- datos ----------
crudos = sorted(RAW.glob("siniestros-de-trafico-*.json"), key=lambda p: p.stat().st_mtime)
if len(crudos) > 1:
    msg("AVISO", f"hay {len(crudos)} ficheros de siniestros en data/raw/siniestros; se usa el más reciente ({crudos[-1].name}); revisar Makefile y geocodificar.py")
crudo = pd.DataFrame(json.loads(crudos[-1].read_text()))
crudo["fecha"] = pd.to_datetime(crudo["FECHA"], errors="coerce")
s = BD.todos(_con)          # tabla siniestro de la base (= siniestros_geo.csv; construir_sqlite.py comprueba que exporta idéntico)
if len(crudo) == len(s):
    msg("OK", f"{crudos[-1].name}: {len(crudo)} filas, las mismas que la base (siniestros_geo.csv)")
else:
    msg("ERROR", f"{crudos[-1].name} tiene {len(crudo)} filas y la base {len(s)}: hay que rehacer geocodificar.py y make sqlite")
if crudo.fecha.isna().any():
    msg("AVISO", f"{int(crudo.fecha.isna().sum())} fechas ilegibles en el crudo")


def completos(f):
    """Años con los 12 meses (como exportar_web.py) y años incompletos."""
    m = f.groupby(f.dt.year).agg(lambda x: x.dt.month.nunique())
    return sorted(int(a) for a, n in m.items() if n == 12), {int(a): int(n) for a, n in m.items() if n < 12}


# ---------- referencia de categorías y años ----------
def categorias(d):
    uni = d.unidades.dropna().str.split(",").explode().str.strip()
    return pd.concat([pd.DataFrame({"campo": "gravedad", "valor": d.gravedad.dropna().unique()}),
                      pd.DataFrame({"campo": "tipo", "valor": d.tipo.dropna().unique()}),
                      pd.DataFrame({"campo": "unidades", "valor": uni[uni != ""].unique()})])


años_geo, incompletos = completos(s.fecha)
if not REF.exists():
    ref = pd.concat([categorias(s), pd.DataFrame({"campo": "año", "valor": [str(a) for a in años_geo]})])
    ref.sort_values(["campo", "valor"]).to_csv(REF, index=False)
    msg("OK", f"creada la referencia {REF.relative_to(ROOT)} con {len(ref)} valores (años {años_geo[0]}-{años_geo[-1]})")
ref = pd.read_csv(REF, dtype=str)
años_ref = sorted(int(a) for a in ref.loc[ref.campo == "año", "valor"])

# ---------- años ----------
años_crudo, inc_crudo = completos(crudo.fecha.dropna())
if años_crudo != años_geo:
    msg("ERROR", f"años completos distintos: crudo {años_crudo}, base (siniestros_geo.csv) {años_geo}")
nuevos = [a for a in años_geo if a not in años_ref]; faltan = [a for a in años_ref if a not in años_geo]
huecos = [a for a in range(años_geo[0], años_geo[-1] + 1) if a not in años_geo]
if nuevos:
    msg("AVISO", f"año nuevo en los datos: {nuevos}. Rehacer el análisis (make all) y, revisado, añadirlo a la referencia")
if faltan:
    msg("ERROR", f"faltan años que había antes: {faltan}")
if huecos:
    msg("AVISO", f"años sin datos completos entre {años_geo[0]} y {años_geo[-1]}: {huecos}")
if not (nuevos or faltan or huecos):
    msg("OK", f"años completos {años_geo[0]}-{años_geo[-1]}, los mismos que la referencia")
for a, n in incompletos.items():
    k = int((s.fecha.dt.year == a).sum())
    msg("AVISO" if n > 1 else "OK", f"{a}: año incompleto ({n} mes{'es' if n > 1 else ''}, {k} siniestros); no se usa en la web")

# ---------- cobertura de geolocalización ----------
d = s[s.fecha.dt.year.isin(años_geo)]; d = d.loc[~d.drop(columns="id").duplicated()].copy()
d["vmp"] = d.unidades.str.contains("VMP", na=False); d["bici"] = d.unidades.str.contains("BICICLETA", na=False)
d["geo"] = d.lon.notna(); d["año"] = d.fecha.dt.year; d["mes"] = d.fecha.dt.to_period("M")
for nombre, g in (("bici/VMP", d[d.vmp | d.bici]), ("total", d)):
    por_año = g.groupby("año").geo.mean()
    bajos = {a: v for a, v in por_año.items() if a in nuevos and v < COB_AÑO_MIN}
    texto = ", ".join(f"{a} {pc(v)}" for a, v in por_año.items())
    if bajos:
        msg("ERROR", f"cobertura {nombre}: año nuevo por debajo del {COB_AÑO_MIN:.0%}: " + ", ".join(f"{a} {pc(v)}" for a, v in bajos.items()))
    else:
        msg("OK", f"cobertura {nombre} por año: {texto}")
    por_mes = g.groupby("mes").geo.agg(["mean", "size"])
    m = por_mes[por_mes["mean"] < COB_MES_MIN]
    if len(m):
        msg("AVISO", f"cobertura {nombre}: {len(m)} meses por debajo del {COB_MES_MIN:.0%}: "
            + ", ".join(f"{p} {pc(r['mean'])}" for p, r in m.iterrows()))
    else:
        msg("OK", f"cobertura {nombre}: ningún mes por debajo del {COB_MES_MIN:.0%} (mínimo {pc(por_mes['mean'].min())})")

# ---------- categorías nuevas ----------
vistas = categorias(s)
nuevas = vistas.merge(ref, how="left", indicator=True).query("_merge == 'left_only'")
for campo in ("gravedad", "tipo", "unidades"):
    v = nuevas[nuevas.campo == campo].valor.tolist()
    if v:
        msg("AVISO", f"{campo}: categorías no vistas antes: {v}. Revisar exportar_web.py (grav, contrario) y añadirlas a la referencia")
    else:
        msg("OK", f"{campo}: sin categorías nuevas ({int((ref.campo == campo).sum())} en la referencia)")

# ---------- totales frente al Plan Director ----------
for grupo, col in (("VMP", "vmp"), ("bici", "bici")):
    obs = d[d[col]].groupby("año").size()
    fuera = {a: (int(obs.get(a, 0)), p) for a, p in PLAN[grupo].items() if abs(obs.get(a, 0) - p) > TOL * p}
    texto = ", ".join(f"{a} {int(obs.get(a, 0))}/{p}" for a, p in PLAN[grupo].items())
    if fuera:
        msg("ERROR", f"{grupo}: totales fuera de ±{TOL:.0%} del Plan (datos/Plan): " + ", ".join(f"{a} {o}/{p}" for a, (o, p) in fuera.items()))
    else:
        msg("OK", f"{grupo}: totales dentro de ±{TOL:.0%} del Plan (datos/Plan): {texto}")
u24 = int(((d.año == 2024) & (d.vmp | d.bici)).sum())
msg("OK" if u24 == PLAN_UNION_2024 else "ERROR", f"bici o VMP en 2024, sin duplicados: {u24} (Plan: {PLAN_UNION_2024})")

# ---------- web ----------
for f in ("observatori.js", "relato.js"):
    p = WEB / "datos" / f
    if not p.exists():
        msg("ERROR", f"falta web/proto/datos/{f}: ejecutar make web")
    elif p.stat().st_mtime < GEO.stat().st_mtime:
        msg("ERROR", f"web/proto/datos/{f} es anterior a la base (observatorio.sqlite): ejecutar make web")
    else:
        msg("OK", f"web/proto/datos/{f} exportado después de la base (observatorio.sqlite)")


def datos_js(f):
    """Objeto JSON de web/proto/datos/<f> (window.X={...};)."""
    t = (WEB / "datos" / f).read_text()
    return json.loads(t[t.index("=") + 1:].rstrip().rstrip(";"))


try:
    OBS, REL, MET = datos_js("observatori.js"), datos_js("relato.js"), datos_js("metode.js")
except Exception as e:
    msg("ERROR", f"no se pueden leer los datos de la web ({type(e).__name__}: {e})"); OBS = None
if OBS:
    # meta de la acción 3.2.2: el mismo año base en las tres páginas (AÑO_BASE de exportar_web.py)
    metas = [OBS["kpi"]["meta"], REL["meta"], MET["meta"]]
    e0 = metas[0]["esc"][0]
    if any(m != metas[0] for m in metas):
        msg("ERROR", "la meta (año base, senda) no es igual en observatori.js, relato.js y metode.js")
    elif metas[0]["año_base"] != AÑO_BASE_ESPERADO or e0["base"] != BASE_ESPERADA:
        msg("ERROR", f"año base exportado {metas[0]['año_base']} con {e0['base']} siniestros (esperado {AÑO_BASE_ESPERADO}: {BASE_ESPERADA})")
    else:
        msg("OK", f"año base exportado {metas[0]['año_base']}: {e0['base']} siniestros → meta {e0['meta']}; conclusión «{e0['concl']}»; igual en las tres páginas")
    # comprobación con la media, banda del año siguiente y juicio (scripts/meta.py), recalculados aquí desde la serie
    m0, em = metas[0], metas[0]["media"]
    tot = {int(a): v for a, v in MET["bv"].items()}
    try:
        sys.path.insert(0, str(ROOT / "scripts")); import meta as _meta
        a = str(m0["desde"])
        r0, rm = _meta.escenario(tot, [m0["año_base"]], m0["año_meta"]), _meta.escenario(tot, em["años"], m0["año_meta"])
        if r0 != json.loads(json.dumps(e0)) or rm != json.loads(json.dumps(em)):
            msg("ERROR", "la meta exportada no coincide con la que recalcula scripts/meta.py desde la serie: ejecutar make web")
        else:
            b = e0["banda"].get(a)
            msg("OK", f"meta: senda {a} {e0['senda'].get(a)} (margen {b}); comprobación con la media {em['etq']}: {em['base_x']} → meta {em['meta']}; "
                f"por vehículo {m0['vehiculo']['base']} → {m0['vehiculo']['meta']}")
        # el juicio funciona solo cuando llegue un año nuevo: año simulado (no se guarda) por debajo, dentro y por encima del margen
        sim = int(a); lo, hi = e0["banda"][a]
        res = {x: _meta.escenario({**tot, sim: x}, [m0["año_base"]], m0["año_meta"])["concl"] for x in (lo - 1, (lo + hi) // 2, hi + 1)}
        esper = dict(zip(res, ("debajo", "compatible", "encima")))
        j = _meta.escenario({**tot, sim: (lo + hi) // 2}, [m0["año_base"]], m0["año_meta"])["juicio"][a]["base"]
        if res != esper or not (j["ic"][0] < j["razon"] < j["ic"][1]):
            msg("ERROR", f"juicio con un {sim} simulado: {res} (esperado {esper}); frente a la base {j}")
        else:
            msg("OK", f"juicio con un {sim} simulado: " + ", ".join(f"{x} → {v}" for x, v in res.items()) + f"; frente a la base, razón {j['razon']} {j['ic']}")
    except Exception as e:
        msg("ERROR", f"no se puede recalcular la meta con scripts/meta.py ({type(e).__name__}: {e})")
    # series de control: cuadran con la serie de la meta y entre sí
    ct = m0["control"]; n = len(ct["años"])
    ok = (ct["bv"] == [tot[a] for a in ct["años"]] and all(ct["bv_her"][i] + ct["bv_sin"][i] == ct["bv"][i] for i in range(n))
          and all(ct["bv"][i] + ct["resto_her"][i] + ct["resto_sin"][i] == ct["ciudad"][i] for i in range(n))
          and ct["ciudad"] == [MET["todos"][str(a)] for a in ct["años"]]
          and all(abs(ct["cuota"][i] - ct["bv"][i] / ct["ciudad"][i]) < 1e-4 for i in range(n)))
    msg("OK" if ok else "ERROR", f"series de control {'coherentes' if ok else 'incoherentes'}: con heridos {ct['bv_her']}, cuota {ct['cuota']}, ciudad {ct['ciudad']}")
    # todo el Paseo de la Alameda, igual en el informe y en metode
    msg("OK" if REL.get("ala_paseo") and REL["ala_paseo"] == MET.get("ala_paseo") else "ERROR", f"Paseo de la Alameda por año: {REL.get('ala_paseo')} (informe) y {MET.get('ala_paseo')} (metode)")
    # anillo del Plan: tres niveles que suman los lugares con más siniestros, iguales en las tres páginas
    pl = [OBS["kpi"]["pl3"], REL["pl3"], MET["plan"]["pl3"]]
    neg = [n for n in OBS["negros"] if not n.get("zona")]
    recuento = {"lugar": sum(n["pl"] == 1 for n in neg), "calle": sum(n["pl"] == 2 for n in neg), "no": sum(n["pl"] == 0 for n in neg)}
    p0 = pl[0]
    if any(p != p0 for p in pl):
        msg("ERROR", f"recuentos del anillo del Plan distintos entre páginas: {pl}")
    elif p0["lugar"] + p0["calle"] + p0["no"] != p0["n"] or p0["n"] != len(neg) or any(p0[k] != v for k, v in recuento.items()):
        msg("ERROR", f"recuentos del anillo del Plan incoherentes: {p0} frente a los lugares {recuento} ({len(neg)})")
    else:
        msg("OK", f"anillo del Plan: cita el lugar {p0['lugar']}, solo su calle {p0['calle']}, no lo menciona {p0['no']} (suman {p0['n']}); igual en las tres páginas")
    # lugares: nudos y tramos (scripts/lugares.py), los mismos que outputs/lugares_nudos.csv, con geometría y sin la rejilla
    try:
        lug = BD.lugares(_con).reset_index()      # tabla lugar de la base (= outputs/lugares_nudos.csv)
        top = lug[lug["rank"] <= 30].sort_values("rank")
        res = BD.resumen(_con)
        noms = [n["nom"] for n in neg]
        geo_ok = all(n.get("geo", {}).get("type") in ("Polygon", "MultiPolygon", "LineString", "MultiLineString") for n in neg)
        rejilla = [k for n in OBS["negros"] for k in ("cel", "tres") if k in n] + [k for k in ("tres", "top") if k in OBS["kpi"] or k in MET]
        rel_ok = [n["nom"] for n in REL["negros"]] == noms and REL.get("ala_geo") == neg[0].get("geo")
        if len(neg) != 30 or noms != top.nom.tolist() or [n["n"] for n in neg] != top.n.astype(int).tolist():
            msg("ERROR", f"lugares: {len(neg)} en la web; no coinciden con outputs/lugares_nudos.csv (rehacer make analisis y make web)")
        elif not geo_ok or rejilla or not rel_ok:
            msg("ERROR", f"lugares: geometría {'bien' if geo_ok else 'falta'}; restos de la rejilla {rejilla}; informe {'igual' if rel_ok else 'distinto'}")
        else:
            tipos = pd.Series([n["tipo"] for n in neg]).value_counts().to_dict()
            msg("OK", f"lugares: 30 ({tipos}), los mismos que lugares_nudos.csv, con geometría; el informe dibuja el nudo del primero; sin restos de la rejilla")
        # nombres del callejero (pendiente 87): únicos, en las dos formas y sin número de portal en los nudos
        _nud = lug[lug.tipo == "nudo"]
        # (salvo los espacios provisionales del callejero, «EP …», que llevan el número en el nombre oficial)
        malos = _nud.nom[_nud.nom.str.contains(r"\s\d+[A-Z]*$", regex=True) & ~_nud.nom.str.contains(r"\bEP\b", regex=True)].tolist()
        if not lug.nom.is_unique or lug[["nom", "nom_es"]].isna().any().any() or malos or any(not n.get("nom_es") for n in neg):
            msg("ERROR", f"nombres de lugar: únicos {lug.nom.is_unique}; vacíos {int(lug[['nom', 'nom_es']].isna().sum().sum())}; nudos con número de portal {malos[:5]}")
        else:
            msg("OK", f"nombres de lugar: {len(lug)} únicos, del callejero y en las dos formas; ningún nudo con número de portal")
        # nombres congelados (data/processed/nombres_lugares.csv): en el top 30, el calculado distinto del publicado o un
        # lugar sin nombre guardado es un AVISO (no error): decide una persona; cambiarlo = editar el fichero + docs/cambios.csv
        _nl = pd.read_sql_query("SELECT nom FROM nombre_lugar", _con)      # nombres congelados (= nombres_lugares.csv)
        _dif = top[top.nom != top.nom_calc]; _nue = top[top.nuevo.astype(bool)]
        _web = all(n["nom"] in set(_nl.nom) for n in neg)
        if not _web:
            msg("ERROR", "nombres congelados: hay lugares de la web sin su nombre en data/processed/nombres_lugares.csv (rehacer make analisis)")
        elif len(_dif) or len(_nue):
            msg("AVISO", f"nombres congelados: en el top 30, {len(_dif)} con el nombre calculado distinto del publicado "
                f"({'; '.join(f'n.º {int(r.rank)} «{r.nom}» → «{r.nom_calc}»' for r in _dif.itertuples())}) y {len(_nue)} lugares nuevos "
                f"({'; '.join(f'n.º {int(r.rank)} «{r.nom}»' for r in _nue.itertuples())}). Decidir: si se cambia, editar nombres_lugares.csv y anotarlo en docs/cambios.csv")
        else:
            msg("OK", f"nombres congelados: los 30 primeros tienen su nombre publicado ({len(_nl)} guardados en nombres_lugares.csv) y el calculado coincide")
        # persistencia fuera de muestra: igual en las tres páginas, la de lugares_nudos_resumen.json y coherente
        ps = [OBS["kpi"]["pers"], REL["pers"], MET["pers"]]
        ab = {(p["corte"], p["k"]): p for p in res["pers"]}
        ok_p = all(p == ps[0] for p in ps) and ps[0]["todas"] == res["pers"] and ps[0]["ab"] == ab[("AB", 30)] and ps[0]["j7"] == ab[("jul24", 30)]
        coh = all(0 <= p["obs"] <= p["A"] and p["perf_lo"] <= p["perf"] <= p["perf_hi"] and p["glob"] <= p["loc"] < p["obs"]
                  and p["p_glob"] < 0.001 and p["p_loc"] < 0.001 for p in res["pers"])
        if not ok_p or not coh:
            msg("ERROR", f"persistencia: {'igual' if ok_p else 'distinta'} en las páginas y el resumen; {'coherente' if coh else 'incoherente'}")
        else:
            a = ps[0]["ab"]
            dentro = a["perf_lo"] <= a["obs"] <= a["perf_hi"]
            msg("OK" if dentro else "AVISO", f"persistencia (top 30, {' → '.join('-'.join(str(x) for x in (y[0], y[-1])) for y in (res['per']['A'], res['per']['B']))}): {a['A']:.0f} → {a['obs']:.0f}; si se mantuvieran {a['perf']:.0f} "
                f"[{a['perf_lo']:.0f}-{a['perf_hi']:.0f}]{'' if dentro else ' (FUERA: revisar los textos, que dicen «es lo que se espera»)'}; "
                f"nulos {a['glob']:.0f} y {a['loc']:.0f}; igual en las tres páginas")
        pi = OBS["kpi"]["pista"]
        npista = sum(bool(n.get("pista")) for n in OBS["negros"])
        msg("OK" if pi == MET["pista"] and npista == len({c[0] for c in pi["con"]}) else "ERROR",
            f"pista: {pi['holm']} pruebas pasan Holm de {pi['familia']} ({pi['probadas']} probadas, >= {pi['min']} casos), en {npista} lugares")
    except Exception as e:
        msg("ERROR", f"no se pueden comprobar los lugares ({type(e).__name__}: {e})")
    # capa «más de lo normal para el tráfico» (cribado_eb.py → exportar_web.py): mismos niveles en las tres páginas, iguales
    # que outputs/cribado_eb_vmp_o_bici.csv; ejemplos del informe que cumplen su regla; sin índice de año ni P sueltas
    try:
        cb = pd.read_csv(ROOT / "outputs/cribado_eb_vmp_o_bici.csv")
        clave = lambda d: (d["N"], d["mu"], d["lv"], d["sv"], tuple(d["b"]), tuple(d["v"]))
        k_obs, k_rel = sorted(map(clave, OBS["uso"])), sorted(map(clave, REL["sc"]))
        k_csv = sorted((int(r.N), round(r.mu, 1), int(r.nivel), int(r.solo_vmp), (int(r.N_bici), round(r.mu_bici, 1)),
                        (int(r.N_vmp), round(r.mu_vmp, 1))) for r in cb.itertuples())
        nv = {k: int((cb.nivel == k).sum()) for k in (2, 1)}
        ok_n = MET["eb"]["alta"] == nv[2] and MET["eb"]["quiza"] == nv[1] and len(MET["eb"]["claro"]) == nv[2]
        de = REL["dest"]; sc = REL["sc"]; cbi = cb.set_index(cb.index)
        x, t, b = (sc[de[c]["i"]] for c in "xtb"); rb = cbi.iloc[de["b"]["i"]]
        ok_d = x["lv"] == 0 and t["lv"] == 2 and t["sv"] and b["lv"] == 2 and not b["sv"] and rb.p_exceso_bici > .8 and rb.nivel_vmp > 0
        viejo = "ix" in REL or any("p" in u for u in OBS["uso"]) or any("p" in d for d in sc)
        bd = all(lo <= hi for _, lo, hi in REL["banda"])
        if k_obs != k_csv or k_rel != k_csv or not ok_n or not ok_d or viejo or not bd:
            msg("ERROR", f"capa de uso: observatorio {'igual' if k_obs == k_csv else 'distinto'} y informe {'igual' if k_rel == k_csv else 'distinto'} "
                f"que cribado_eb_vmp_o_bici.csv; niveles en el método {'bien' if ok_n else 'mal'}; ejemplos del informe {'bien' if ok_d else 'NO cumplen su regla'}; "
                f"{'restos del índice de año o de P sueltas; ' if viejo else ''}franja {'bien' if bd else 'mal'}")
        else:
            msg("OK", f"capa de uso: {len(cb)} puntos de conteo, {nv[2]} claramente ({int(cb[cb.nivel == 2].solo_vmp.sum())} solo de patinete) "
                f"y {nv[1]} quizá, iguales en las tres páginas y en el CSV; ejemplos del informe: {', '.join(de[c]['nom'] for c in 'xtb')}")
    except Exception as e:
        msg("ERROR", f"no se puede comprobar la capa de uso ({type(e).__name__}: {e})")

# ---------- años del último dato (pendiente 78): tipo, periodos de la persistencia y panel de uso ----------
# Al llegar un año nuevo nada se queda en 2025: el tipo de accidente es el del último año; los periodos de la persistencia
# se reparten los años completos (lugares.py, periodos); el panel de uso llega al último año con IMD, que puede ser
# anterior al último de siniestros (se prueba con un año simulado sin IMD, que no se guarda).
if OBS:
    try:
        anys = OBS["kpi"]["anys"]
        ta = OBS["kpi"].get("tipo_any")
        viejas = [k for n in OBS["negros"] for k in ("t25", "n25") if k in n]
        if ta != anys[-1] or viejas or any("tu" not in n for n in OBS["negros"]):
            msg("ERROR", f"tipo de accidente: año {ta} (esperado el último, {anys[-1]}); claves antiguas {sorted(set(viejas))}")
        else:
            msg("OK", f"tipo de accidente: el del último año ({ta}) en las fichas y la lista")
        sys.path.insert(0, str(ROOT / "scripts")); import lugares as _LG
        res = BD.resumen(_con)
        pa, pb = _LG.periodos(anys)
        pers = [OBS["kpi"]["pers"].get("per"), MET["pers"].get("per"), res.get("per")]
        if any(x != pers[0] for x in pers) or not pers[0] or [pers[0]["A"], pers[0]["B"]] != [pa, pb] or REL["per"] != {"A": pa, "B": pb}:
            msg("ERROR", f"periodos de la persistencia: {pers} y el informe {REL.get('per')} (esperados {pa} → {pb} con los años {anys}); rehacer make")
        else:
            msg("OK", f"periodos de la persistencia: {_LG.etq_años(pa)} → {_LG.etq_años(pb)} y corte de {pers[0]['corte7']}, de los datos e iguales en las tres páginas")
        # panel de uso: recalculado con scripts/meta.py (uso) desde los índices exportados, y con un año simulado sin IMD
        import math, meta as _meta
        tot = {int(a): v for a, v in MET["bv"].items()}
        ix = pd.DataFrame([{int(a): v for a, v in MET["uso_ix"].items()}])          # panel de un «contador» con los índices
        u0 = _meta.uso(ix, tot, MET["meta"]["año_base"], MET["meta"]["año_meta"])
        cerca = all(abs(u0[k] - MET[k]) < 0.002 for k in ("uso_g", "uso_ult", "sin_ult")) and all(abs(u0[k][x] - MET[k][x]) < 0.002 for k in ("uso30", "riesgo") for x in ("igual", "sigue"))
        sim = anys[-1] + 1
        u1 = _meta.uso(ix, {**tot, sim: tot[anys[-1]]}, MET["meta"]["año_base"], MET["meta"]["año_meta"])
        nums = [u1[k] for k in ("uso_g", "uso_ult", "sin_ult")] + list(u1["uso30"].values()) + list(u1["riesgo"].values()) + list(u1["uso_ix"].values()) + list(u1["sin_ix"].values())
        sim_ok = u1["uso_a1"] == MET["uso_a1"] and str(sim) in u1["sin_ix"] and str(sim) not in u1["uso_ix"] and all(math.isfinite(x) for x in nums)
        plant = (WEB / "metode.plantilla.html").read_text()
        a1_mal = re.findall(r"(?:uso_ix|sin_ix)\[A1\]", plant)
        if MET["uso_a1"] != max(MET["anys_eb"]) or not cerca or not sim_ok or a1_mal:
            msg("ERROR", f"panel de uso: último año con IMD {MET['uso_a1']} (años con IMD {MET['anys_eb']}); recalculado {'igual' if cerca else 'distinto'}; "
                f"con un {sim} simulado sin IMD {'bien' if sim_ok else 'MAL (NaN o año equivocado)'}; la plantilla indexa el uso por el último año de siniestros {a1_mal}")
        else:
            msg("OK", f"panel de uso: hasta {MET['uso_a1']} (último año con IMD); con un {sim} simulado sin IMD sigue en {u1['uso_a1']}, sin NaN "
                f"(riesgo por viaje {u1['riesgo']['igual']}-{u1['riesgo']['sigue']})")
    except Exception as e:
        msg("ERROR", f"no se pueden comprobar los años del último dato ({type(e).__name__}: {e})")

# ---------- lugares del Plan: todos decididos (CLAVES o SIN_CLAVE de exportar_web.py) ----------
try:
    _arb = ast.parse((ROOT / "scripts/exportar_web.py").read_text())
    _dic = {t.id: ast.literal_eval(n.value) for n in _arb.body if isinstance(n, ast.Assign)
            for t in n.targets if isinstance(t, ast.Name) and t.id in ("CLAVES", "SIN_CLAVE")}
    _lug = set(pd.read_csv(ROOT / "data/processed/pdsv_lugares.csv").nombre)
    _cl, _sc = _dic.get("CLAVES", {}), _dic.get("SIN_CLAVE", {})
    _sin = sorted(_lug - set(_cl) - set(_sc)); _dos = sorted(set(_cl) & set(_sc))
    _vacias = sorted(k for k, v in _cl.items() if not v) + sorted(k for k, v in _sc.items() if not (isinstance(v, dict) and all(str(v.get(i, "")).strip() for i in ("es", "va"))))
    _sobran = sorted((set(_cl) | set(_sc)) - _lug)
    if _sin or _dos or _vacias:
        msg("ERROR", f"lugares del Plan sin decidir {_sin}, en CLAVES y SIN_CLAVE a la vez {_dos}, o sin claves/motivo {_vacias}")
    else:
        msg("OK", f"lugares del Plan: los {len(_lug)} nombres distintos de pdsv_lugares.csv decididos ({len(_lug & set(_cl))} con claves, {len(_lug & set(_sc))} sin clave con motivo)")
    if _sobran:
        msg("AVISO", f"claves de lugares que ya no están en pdsv_lugares.csv: {_sobran}")
except Exception as e:
    msg("ERROR", f"no se pueden leer CLAVES y SIN_CLAVE de exportar_web.py ({type(e).__name__}: {e})")


def fin_cadena(t, j):
    """Índice tras la cadena JS que empieza en t[j] (comillas simples, dobles o plantilla con ${...})."""
    q = t[j]; j += 1
    while t[j] != q:
        if t[j] == "\\": j += 2; continue
        if q == "`" and t.startswith("${", j): j = fin_bloque(t, j + 1); continue
        j += 1
    return j + 1


def fin_bloque(t, j):
    """Índice tras el bloque {…}, […] o (…) que empieza en t[j]."""
    n = 0
    while True:
        c = t[j]
        if c in "\"'`": j = fin_cadena(t, j); continue
        if c in "{[(": n += 1
        elif c in "}])":
            n -= 1
            if n == 0: return j + 1
        j += 1


def claves(t, i, rep=None):
    """Claves de primer nivel del objeto literal que empieza en t[i] == '{', con la posición de su valor.
    Si se da rep (lista), añade las claves que ya estaban (repetidas: la última tapa a las anteriores)."""
    out, j, fin = {}, i + 1, fin_bloque(t, i) - 1
    while True:
        while j < fin and t[j] in " \t\r\n,": j += 1
        if j >= fin: return out
        if t[j] in "\"'": k = t[j + 1:fin_cadena(t, j) - 1]; j = fin_cadena(t, j)
        else: k = re.match(r"[\w$]+", t[j:]).group(); j += len(k)
        j = t.index(":", j) + 1
        while t[j] in " \t\r\n": j += 1
        if rep is not None and k in out: rep.append(k)
        out[k] = j
        while j < fin and t[j] != ",":        # saltar el valor hasta la coma de este nivel
            j = fin_cadena(t, j) if t[j] in "\"'`" else fin_bloque(t, j) if t[j] in "{[(" else j + 1


for pag in ("observatori", "informe", "pla"):
    t = (WEB / f"{pag}.plantilla.html").read_text()
    try:
        T = claves(t, t.index("{", t.index("const T = {")))
        rep = {"va": [], "es": []}
        k = {l: set(claves(t, T[l], rep[l])) for l in ("va", "es")}
        for m in re.finditer(r"Object\.assign\(T\.(va|es),\s*\{", t):
            nuevas = claves(t, m.end() - 1, rep[m.group(1)])
            rep[m.group(1)] += sorted(k[m.group(1)] & set(nuevas)); k[m.group(1)] |= set(nuevas)
    except Exception as e:                    # la plantilla cambió de forma: no se puede leer T
        msg("ERROR", f"{pag}.plantilla.html: no se pueden leer los textos T ({type(e).__name__}: {e})"); continue
    # cada clave, una sola vez por idioma: un texto definido dos veces deja el primero muerto (pendiente 88)
    if rep["va"] or rep["es"]:
        msg("ERROR", f"{pag}.plantilla.html: textos definidos más de una vez (el último tapa a los anteriores): va {sorted(set(rep['va']))}, es {sorted(set(rep['es']))}")
    solo = {l: sorted(k[l] - k[o]) for l, o in (("va", "es"), ("es", "va"))}
    if solo["va"] or solo["es"]:
        msg("ERROR", f"{pag}.plantilla.html: claves solo en va {solo['va']}, solo en es {solo['es']}")
    else:
        msg("OK", f"{pag}.plantilla.html: va y es con las mismas {len(k['va'])} claves")

# ---------- años escritos a mano en las páginas y en los scripts ----------
# Las páginas sacan sus años de los datos (anys, la meta, los periodos de la persistencia, el panel de uso, el tipo…), para
# que se adapten solas cuando se publique un año nuevo (pendiente 78). Solo se admiten estos años fijos, con su motivo
# (hechos ya pasados o fechas de documentos, que no cambian con datos nuevos). Se ignoran los comentarios de JS.
EXC_AÑOS = [
    (r"2026-2030", "nombre del Plan Director de Seguridad Vial 2026-2030"),
    (r"getFullYear\(\)-1980", "origen de las fechas DOS del formato ZIP (escritor de ZIP de la descarga del mapa), no un año de datos"),

    (r"2030", "año de la meta del Plan (fijo; en el código, AÑO_META)"),
    (r"GRAV_COMP = 2024, ALA0 = 2023", "constantes: heridos graves comparables desde 2024 (cambio de criterio en 2023); la Alameda se cuenta desde 2023"),
    (r"(?:juliol|julio) de 2024|(?:mitjan|mediados de) 2024|(?:format|formato) de 2024", "SIASV de la Policía Local y cambio de formato de la dirección (julio de 2024)"),
    (r"(?:viària|vial) \(2024\)|(?:cruïlla|cruce|encreuament) \(2025\)", "actuaciones del Plan en la Alameda (auditoría de 2024, reordenación de 2025)"),
    (r"(?:maig|mayo) de 2026|(?:període|periodo) de 2025", "primeras señales de la Policía Local (enero-mayo de 2026 frente a 2025); solo se muestran sin datos de 2026"),
    (r"(?:puja molt|sube mucho|creix molt|crece mucho) en 2025", "la categoría «baja gravedad» sube mucho en 2025 (hecho del dato)"),
    (r"fiable (?:des de|desde) 2025", "el tipo de accidente solo es fiable desde 2025 (hecho del dato; se muestra el del último año)"),
    (r"En 2022 el portal", "en 2022 el portal daba menos direcciones exactas (cobertura de geolocalización)"),
    (r"(?:des de|desde|fins a|hasta|abans de|antes de) 2024|(?:comença|empieza) en 2023|(?:Durant|Durante) 2023|INT/2223/2014",
     "heridos graves: cambio de criterio aplicado durante 2023, comparables desde 2024 (hecho del dato y del Plan)"),
    (r"de 2019 a 2025|2019 hasta 2025» (?:i|y) en (?:detall|detalle) 2023, 2024 (?:i|y) 2025", "periodo que analiza el Plan Director (cita)"),
    (r"respecte a 2019 i de ferides greus respecte a 2024|respecto a 2019 y de heridas graves respecto a 2024", "meta global del Plan (apartado 4.4, cita)"),
    (r"(?:xifres per a|cifras para|greus de|graves de) 2024", "cifras de heridos graves de 2024 transcritas del Plan"),
    (r"(?:premsa|prensa) sobre 2026|(?:octubre de|d'octubre de) 2026|Decret[o]? 52/2026|Decret[o]? 518/2026|BOE-A-2026-13889", "contexto externo citado (prensa de 2026, casco obligatorio desde octubre de 2026 por el Real Decreto 518/2026, Real Decreto 52/2026)"),
    (r"(?:novembre de|noviembre de|04/11/)2026|(?:novembre|noviembre) de 2026", "fecha del prototipo o de un cambio de método (registro de cambios)"),
    (r"(?:primer|primero) 2024|(?:i|y) 2024 queda|(?:pujada|subida) de 2022-2025", "historia de la revisión metodológica (lo que se decidió entonces)"),
    (r"w3\.org/2000", "espacio de nombres de SVG"),
    (r"data:image/svg\+xml,[^\"]*", "favicon SVG en línea, codificado para URL (%20 seguido de cifras)"),
]
for pag in ("informe", "observatori", "metode"):
    t = (WEB / f"{pag}.plantilla.html").read_text()
    t = re.sub(r"(?<![:\\])//[^\n]*", "", t)
    for patron, _ in EXC_AÑOS:
        t = re.sub(patron, "", t)
    sueltos = [t[max(0, m.start() - 40):m.end() + 15].replace("\n", " ") for m in re.finditer(r"(?<![\w.$])(?:19|20)\d\d(?!\w)", t)]
    if sueltos:
        msg("ERROR", f"{pag}.plantilla.html: {len(sueltos)} años escritos a mano (sacarlos de los datos o justificarlos en EXC_AÑOS): " + " · ".join(sueltos[:8]))
    else:
        msg("OK", f"{pag}.plantilla.html: sin años escritos a mano (salvo las excepciones justificadas de EXC_AÑOS)")
# scripts: comparaciones, filtros y rangos con un año literal (== 2025, <= 2023, between(2022, 2025), isin([2022, …]), range(2022, …)).
# persistencia_puntos.py es histórico (fuera de make) y comprobar.py tiene sus referencias del Plan.
SCRIPTS_AÑOS = ["exportar_web.py", "lugares.py", "lugares_nudos.py", "meta.py", "cribado_eb.py", "vmp_vs_bici.py",
                "vmp_vs_bici_condicionado.py", "construir_web.py", "geocodificar.py"]
_pat = re.compile(r"(?:==|!=|<=|>=|<|>)\s*(?:19|20)\d\d\b|between\(\s*(?:19|20)\d\d|isin\(\s*\[\s*(?:19|20)\d\d|range\(\s*(?:19|20)\d\d")
_mal = []
for f in SCRIPTS_AÑOS:
    for i, l in enumerate((ROOT / "scripts" / f).read_text().splitlines(), 1):
        c = l.split("#")[0]
        if _pat.search(c): _mal.append(f"{f}:{i}: {c.strip()[:70]}")
if _mal:
    msg("ERROR", f"scripts con años escritos a mano en filtros ({len(_mal)}; sacarlos de los años completos de los datos): " + " · ".join(_mal[:6]))
else:
    msg("OK", f"scripts: ningún filtro por un año escrito a mano en {len(SCRIPTS_AÑOS)} scripts de make")

# ---------- errores detectados en los datos del Ajuntament: registro, web y última re-verificación (scripts/incidencias.py) ----------
try:
    _ic = pd.read_csv(ROOT / "data/processed/incidencias_datos.csv", dtype=str).fillna("")
    _iw = MET["inc"]
    _col = ["id", "dataset_va", "dataset", "web_que_va", "web_que_es", "web_trato_va", "web_trato_es", "estado"]
    _ok = (_iw["n"] == len(_ic) and _iw["filas"] == _ic[_col].values.tolist() and _iw["auto"] == int((_ic.verificacion == "auto").sum())
           and _ic.id.is_unique and set(_ic.estado) <= {"detectada", "comunicada", "respondida", "corregida", "no_se_corrige"})
    _vacios = [i for i, r in _ic.iterrows() if not all(r[c] for c in _col + ["descripcion", "prueba", "sugerencia", "fecha_deteccion"])]
    _com = [r.id for r in _ic.itertuples() if (r.estado != "detectada") != bool(r.fecha_comunicacion and r.canal)]
    _pl = (WEB / "metode.plantilla.html").read_text()
    _tpl = _pl.count("errores:{h:") == 2 and "hola@observatoribicivlc.org" in _pl
    msg("OK" if _ok and not _vacios and not _com and _tpl else "ERROR",
        f"errores en los datos: {len(_ic)} en el registro, {_iw['n']} en metode.js ({'iguales' if _ok else 'DISTINTOS: ejecutar make web'}); "
        f"filas incompletas {_vacios or 'ninguna'}; estado sin fecha y canal de comunicación (o al revés) {_com or 'ninguno'}; "
        f"sección y contacto en la plantilla {'sí' if _tpl else 'NO'}")
    _vf = ROOT / "outputs/incidencias_verificacion.csv"
    if _vf.exists():
        _v = pd.read_csv(_vf, dtype=str).fillna("")
        _ya = _v[_v.detalle.str.contains("YA NO APARECE|MARCADA COMO CORREGIDA|CAMBIA:")].id.tolist()
        msg("AVISO" if _ya else "OK", f"incidencias que cambian o ya no aparecen en la última re-verificación ({_v.fecha.max()}): {_ya}; revisar el registro"
            if _ya else f"incidencias: última re-verificación {_v.fecha.max()}, sin cambios")
    else:
        msg("AVISO", "incidencias: sin re-verificar (ejecutar make incidencias)")
except Exception as e:
    msg("ERROR", f"no se pueden comprobar los errores en los datos ({type(e).__name__}: {e})")

# ---------- «Hi col·laboren / Colaboran» (data/processed/colaboran.csv -> datos/colaboran.json -> pie común) ----------
try:
    import datetime as _dt
    _cc = pd.read_csv(ROOT / "data/processed/colaboran.csv", dtype=str).fillna("")
    _cols = ["entidad", "tipo", "que_aporta_va", "que_aporta_es", "url", "desde", "prueba", "publicar"]
    _pub = _cc[_cc.publicar.str.strip().str.lower() == "si"] if list(_cc.columns) == _cols else _cc.iloc[0:0]
    def _fecha_ok(f):
        try: _dt.date.fromisoformat(f.strip()); return True
        except ValueError: return False
    _malas = [r.entidad or f"fila {i + 2}" for i, r in _pub.iterrows()
              if not (r.entidad.strip() and r.que_aporta_va.strip() and r.que_aporta_es.strip() and _fecha_ok(r.desde)
                      and r.prueba.strip() in {"carta", "convenio", "enlace", "acta"}
                      and r.tipo.strip() in {"institucion", "universidad", "asociacion", "medio", "persona"})]
    _otras = sorted(set(_cc.publicar.str.strip().str.lower()) - {"si", "no"}) if "publicar" in _cc else ["sin columna"]
    _js = json.loads((WEB / "datos/colaboran.json").read_text())
    _igual = [e["ent"] for e in _js] == _pub.sort_values(["desde", "entidad"]).entidad.str.strip().tolist()
    _ok = list(_cc.columns) == _cols and not _malas and not _otras and _igual
    msg("OK" if _ok else "ERROR",
        f"colaboran: {len(_cc)} filas, {len(_pub)} publicadas ({'se ven en el pie' if len(_pub) else 'no se pinta nada'}); "
        f"columnas {'bien' if list(_cc.columns) == _cols else 'MAL'}; publicadas sin fecha (AAAA-MM-DD), prueba "
        f"(carta/convenio/enlace/acta), tipo o texto va/es: {_malas or 'ninguna'}; publicar distinto de si/no: {_otras or 'ninguno'}; "
        f"colaboran.json {'al día' if _igual else 'DISTINTO: ejecutar make web'}")
except Exception as e:
    msg("ERROR", f"no se puede comprobar colaboran ({type(e).__name__}: {e})")

# ---------- build: datos aparte, versionados y con SRI (scripts/construir_web.py) ----------
import base64, hashlib
BUILD = WEB / "build"
for pag, fuente in (("observatori", "observatori.js"), ("informe", "relato.js"), ("metode", "metode.js"), ("cambios", "cambios.js"), ("pla", "pla.js")):
    h = BUILD / f"{pag}.html"
    if not h.exists():
        msg("ERROR", f"falta web/proto/build/{pag}.html: ejecutar make web"); continue
    html = h.read_text()
    # (el índice de las fichas del buscador, datos/fichas_indice.<hash>.js, lo comprueba la sección «SQLite y fichas»)
    refs = [r for r in re.findall(r'<script src="(datos/[^"]+)" integrity="([^"]+)"', html) if not r[0].startswith("datos/fichas_indice.")]
    if len(refs) != 1:
        msg("ERROR", f"{pag}.html: se esperaba un <script> de datos con integrity y hay {len(refs)}"); continue
    src, sri = refs[0]
    f = BUILD / src
    if not re.fullmatch(rf"datos/{pag}\.[0-9a-f]{{8}}\.js", src) or not f.exists():
        msg("ERROR", f"{pag}.html: {src} no existe o no tiene nombre versionado"); continue
    b = f.read_bytes()
    sri_ok = sri == "sha384-" + base64.b64encode(hashlib.sha384(b).digest()).decode()
    igual = b == (WEB / "datos" / fuente).read_bytes() and src.split(".")[1] == hashlib.sha256(b).hexdigest()[:8]
    fj = BUILD / "datos" / f"{pag}.json"   # descarga estable: solo con PUBLICAR_JSON de construir_web.py (hoy no)
    try:
        estable = not fj.exists() or json.loads(fj.read_text())["datos"] == datos_js(fuente)
    except Exception:
        estable = False
    kb = len(html.encode()) / 1e3
    if not (sri_ok and igual and estable and kb < 500):
        msg("ERROR", f"{pag}.html: datos {src}: SRI {'bien' if sri_ok else 'MAL'}, contenido {'igual' if igual else 'DISTINTO'} "
                     f"que web/proto/datos/{fuente}, descarga {pag}.json {'bien' if estable else 'MAL'}, HTML {kb:.0f} kB (máx. 500)")
    else:
        msg("OK", f"{pag}.html ({kb:.0f} kB) carga {src} con SRI" + (f"; descarga estable datos/{pag}.json con los mismos datos" if fj.exists() else ""))

# ---------- «El Pla, al dia» (pla.html; sin publicar hasta que el usuario revise los estados, pendiente 65) ----------
try:
    PLA = datos_js("pla.js")
    ps = BD.plan(_con)        # seguimiento del Plan de la base (su fuente de verdad)
    ps = ps[ps.clase == "medida"].reset_index(drop=True)     # el indicador 3.2.2 no se publica como medida (07/11/2026)

    cuenta = {e: int((ps.estado == e).sum()) for e in PLA["estados"]}
    est_web = {e: sum(a["est"] == e for a in PLA["acts"]) for e in PLA["estados"]}
    ok = (PLA["n"] == len(ps) == len(PLA["acts"]) and PLA["por_estado"] == cuenta == est_web and set(ps.estado) <= set(PLA["estados"])
          and [a["id"] for a in sorted(PLA["acts"], key=lambda a: a["id"])] == sorted(ps.id))
    msg("OK" if ok else "ERROR", f"pla: {PLA['n']} actuaciones {PLA['por_estado']} (base {len(ps)} {cuenta}; fichas {est_web})")
    # fuentes numeradas: sin URL repetida y toda referencia [n] existe
    urls = [f["url"] for f in PLA["fuentes"]]; ns = {f["n"] for f in PLA["fuentes"]}
    refs_ok = len(urls) == len(set(urls)) and all(a["fn"] in ns and set(a["fnotas"]) <= ns for a in PLA["acts"]) and PLA["plan_doc"]["n"] in ns
    msg("OK" if refs_ok else "ERROR", f"pla: {len(urls)} fuentes únicas; referencias [n] {'bien' if refs_ok else 'ROTAS'}")
    # «sin información pública», nunca «no hecho»: ni en la plantilla, ni en la página, ni en los datos de las sin_info
    NO_HECHO = re.compile(r"\bno (?:fet|feta|fetes|fets|hecho|hecha|hechas|hechos)\b|no s'ha fet|no se ha hecho", re.I)
    textos = {"plantilla": (WEB / "pla.plantilla.html").read_text(), "build": (WEB / "build/pla.html").read_text(),
              "sin_info": " ".join(" ".join(str(a.get(k) or "") for k in ("es", "nota", "transp")) for a in PLA["acts"] if a["est"] == "sin_info")}
    malos = {k: NO_HECHO.findall(v) for k, v in textos.items() if NO_HECHO.search(v)}
    msg("ERROR" if malos else "OK", f"pla: «no fet / no hecho» en {malos}" if malos else "pla: sin_info se dice «sense informació pública / sin información pública», nunca «no fet / no hecho»")
    # lo que el Plan prevé publicar (TRANSPARENCIA en exportar_web.py): cada id existe y sigue en sin_info (si no, revisar la lista)
    _ex = (ROOT / "scripts/exportar_web.py").read_text()
    _tr = re.findall(r'^\s+"([\w.-]+)": \(', _ex[_ex.index("TRANSPARENCIA = {"):_ex.index("}", _ex.index("TRANSPARENCIA = {"))], re.M)
    _est = dict(zip(ps.id, ps.estado)) | {a["id"]: a["est"] for a in PLA.get("pub_ind", [])}   # + el indicador 3.2.2
    _fuera = [i for i in _tr if _est.get(i) != "sin_info"]

    msg("AVISO" if _fuera else "OK", f"pla: de lo que el Plan prevé publicar ya no están en sin_info (o no existen): {_fuera}; revisar TRANSPARENCIA" if _fuera
        else f"pla: {len(_tr)} actuaciones del Plan previstas y sin información pública")
    # publicada (04/11/2026): sin noindex, en el menú de las otras 4 páginas, en deploy.sh (subida, verificación y sitemap),
    # con su tarjeta OG; y la tarjeta «Què s'hi fa?» de la portada y la capa del mapa con los mismos recuentos que pla.js
    _b = textos["build"]; _sin = [p for p in ("observatori", "informe", "metode", "cambios") if 'href="pla.html"' not in (WEB / f"build/{p}.html").read_text()]
    _dep = not (ROOT / "deploy/deploy.sh").exists() or "pla" in re.search(r"^PAGINAS=\((.*)\)", (ROOT / "deploy/deploy.sh").read_text(), re.M).group(1).split()
    _noidx = 'name="robots" content="noindex' in _b
    _og = (WEB / "build/og/pla.png").exists() and 'og/pla.png' in _b
    _obs = OBS.get("pla", {}) if OBS else {}
    _con = [a for a in PLA["acts"] if a["id"] in {p[7] for p in _obs.get("pts", [])}]
    _coh = (_obs.get("n") == PLA["n"] and _obs.get("por_estado") == PLA["por_estado"]
            and len(_obs.get("pts", [])) == len(ps[ps.lon.notna() & ps.lat.notna()]) and all(p[2] == next(a["est"] for a in _con if a["id"] == p[7]) for p in _obs.get("pts", []))
            and sum(len(v) for v in PLA["cerca"].values()) == sum(len(n.get("pla", [])) for n in OBS["negros"]))
    ok = not _noidx and not _sin and _dep and _og and _coh
    msg("OK" if ok else "ERROR", f"pla.html publicada: noindex {'SÍ' if _noidx else 'no'}, sin enlace en {_sin or 'ninguna'}, deploy.sh {'sí' if _dep else 'NO'}, "
        f"tarjeta OG {'sí' if _og else 'NO'}; portada y mapa {'coherentes' if _coh else 'DISTINTOS'} con pla.js "
        f"({len(_obs.get('pts', []))} actuaciones en el mapa, {sum(1 for n in OBS['negros'] if n.get('pla'))} fichas con actuaciones)")
except Exception as e:
    msg("ERROR", f"no se puede comprobar pla ({type(e).__name__}: {e})")

# ---------- SQLite y fichas estáticas por lugar y calle (scripts/construir_sqlite.py, scripts/fichas.py) ----------
print("\n== SQLite y fichas ==")
try:
    sys.path.insert(0, str(ROOT / "scripts")); import fichas as _FI
    for _niv, _txt in _FI.comprobaciones(): msg(_niv, _txt)
except Exception as e:
    msg("ERROR", f"no se pueden comprobar la base y las fichas ({type(e).__name__}: {e})")

print(f"\n{'ERROR: ' + str(errores) + ' comprobaciones fallan' if errores else 'Sin errores.'}")
sys.exit(1 if errores else 0)
