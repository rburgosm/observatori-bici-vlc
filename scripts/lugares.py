"""Lugares de la web: NUDOS de cruce y TRAMOS de calle (<= 150 m). Código común de lugares_nudos.py y exportar_web.py.

Unidades (EPSG:25830; geometría con geopandas/shapely, agrupaciones con scipy):
- Nudo: semillas = nodos de grado >= 3 del callejero (ejes.geojson; el grafo ya viene troceado en los cruces)
  + los puntos de cruce que da el geocodificador a TODOS los siniestros de la ciudad (posiciones, no recuentos; no solo
  bici o VMP, para no elegir por el resultado). Las semillas a menos de F m se funden con buffer(F/2) + dissolve. Las
  plazas pequeñas (PLAÇA con diámetro <= 150 m: glorietas) son un solo nudo con las semillas a <= F/2, sin encadenar
  más allá; las plazas grandes no se funden (cada entrada es un cruce). Zona del nudo: envolvente convexa + R m.
- Tramo: lo que queda de cada calle (codvia) fuera de las zonas de nudo, troceado en piezas iguales de <= 150 m; las
  piezas de la misma calle con puntos medios a <= 60 m (las dos calzadas de una avenida) se agrupan por enlace
  completo (scipy.cluster.hierarchy), que no encadena.
- Siniestro: al nudo si está a <= R m de su envolvente; si no, al tramo más cercano.
Peso de cada siniestro: 1 / cobertura de geolocalización de bici o VMP de su año y su tipo de dirección (cruce / portal).
Pista: prueba binomial unilateral de cada categoría «con quién» frente a la referencia de su tipo (nudos con nudos,
tramos con tramos), sin el propio lugar; Holm sobre todas las pruebas del mapa; solo con >= MIN_PISTA casos."""
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, shapely, shapely.ops
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw/siniestros"; CRS = "EPSG:25830"
R, F = 30, 30                       # radio de asignación al nudo y distancia de fusión de semillas (m)
PIEZA, PARALELA, PLAZA_MAX = 150, 60, 150
MIN_PISTA = 20                      # casos mínimos para probar la pista de un lugar
NOMBRE_TOL, PLAZA_VOTOS = 15, 0.15  # nombres: calles a <= 15 m del nudo; la glorieta da nombre si la nombra el 15 % de sus siniestros
# nombres congelados (04/11/2026): un nombre publicado es una referencia pública y no cambia en silencio con datos nuevos
NOMBRES_CSV = ROOT / "data/processed/nombres_lugares.csv"
CONGELA_TOL = 10                    # m entre centroides (mismo tipo; en tramos, también la misma vía): ver congelar()
CATS = list("mwds")                 # con quién: m vehículo, w peatón, d entre bicis o patinetes, s solo
# periodos de la persistencia fuera de muestra (pendiente 78: nada escrito a mano con los años):
# - A / B: los primeros h años completos frente a los últimos h, con h = la mitad (redondeando hacia abajo). Los dos
#   periodos tienen la misma duración, para que «antes» y «después» se puedan comparar en número (la bajada del top es
#   vuelta a la media); con un número impar de años, el del medio no entra. Con 2022-2025, 2022-23 → 2024-25; con 2026,
#   2022-23 → 2025-26; con 2027, 2022-24 → 2025-27;
# - CORTE7: el cambio de registro de la Policía Local (SIASV y formato de la dirección, julio de 2024): un hecho, no un periodo.
CORTE7 = "2024-07-01"


def periodos(años):
    """Años del periodo A (ordenar) y del B (medir) de la persistencia fuera de muestra."""
    años = sorted(int(a) for a in años); h = len(años) // 2
    return años[:h], años[len(años) - h:]


def etq_años(xs):
    """«2022-23», «2024-26» o «2025» (un solo año)."""
    return str(xs[0]) if len(xs) == 1 else f"{xs[0]}-{str(xs[-1])[2:]}"


def contrario(u):
    """Con quién: w peatón, d solo bicis/VMP (2+), s solo uno, m cualquier otro vehículo (motor, tranvía, etc.)."""
    us = [x.strip() for x in str(u).split(",") if x.strip()]
    if [x for x in us if x not in ("BICICLETA", "VMP", "PEATÓN")]: return "m"
    if "PEATÓN" in us: return "w"
    return "d" if len(us) >= 2 else "s"


def siniestros():
    """Todos los siniestros de los años completos, sin duplicados (mismo filtro en todos los scripts); y los años."""
    s = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", parse_dates=["fecha"])
    m = s.groupby(s.fecha.dt.year).fecha.agg(lambda x: x.dt.month.nunique())
    años = sorted(int(a) for a, n in m.items() if n == 12)
    s = s[s.fecha.dt.year.isin(años)]
    return s.loc[~s.drop(columns="id").duplicated()].copy(), años


def bici_vmp(s):
    """Siniestros con bici o VMP con las columnas comunes (año, v, dir, w, k) y la cobertura por año × tipo de dirección.
    Las filas con unidades «[» no contienen ninguno de los dos y quedan fuera."""
    s = s.copy()
    s["vmp"] = s.unidades.str.contains("VMP", na=False); s["bici"] = s.unidades.str.contains("BICICLETA", na=False)
    s = s[s.vmp | s.bici].copy(); s["año"] = s.fecha.dt.year
    s["v"] = np.select([s.vmp & s.bici, s.vmp], ["a", "p"], "b")       # a ambos, p patinete, b bici
    s["dir"] = np.select([s.metodo.isin(["cruce", "cruce_fallo"]), s.metodo.isin(["portal", "portal_cercano", "numero_fallo"])],
                         ["cruce", "portal"], "otra")
    cob = s.groupby(["año", "dir"]).lon.apply(lambda x: x.notna().mean())
    s["w"] = 1 / pd.Series(list(zip(s["año"], s["dir"])), index=s.index).map(cob)   # inf solo sin punto («otra»)
    s["k"] = s.unidades.map(contrario)
    return s, cob


def puntos(s):
    """Los siniestros con punto, como GeoDataFrame en EPSG:25830 (mismo índice)."""
    g = s[s.lon.notna()].copy()
    return gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g.lon, g.lat), crs=4326).to_crs(CRS)


def callejero(todos):
    """Ejes, semillas de nudo y glorietas. todos: todos los siniestros de la ciudad (para los puntos de cruce)."""
    cr = todos[(todos.metodo == "cruce") & todos.lon.notna()][["lon", "lat"]].drop_duplicates()
    ejes = gpd.read_file(RAW / "ejes.geojson"); ejes = ejes[ejes.geometry.notna()].to_crs(CRS).explode(ignore_index=True)
    ends = ejes.geometry.boundary.explode(index_parts=False)
    ep = pd.DataFrame(shapely.get_coordinates(ends.values).round(1), columns=["x", "y"])
    deg = ep.groupby(["x", "y"]).size(); nod = deg[deg >= 3].reset_index()
    xy = np.vstack([nod[["x", "y"]].values,
                    shapely.get_coordinates(gpd.GeoSeries(gpd.points_from_xy(cr.lon, cr.lat), crs=4326).to_crs(CRS).values)])
    sem = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xy[:, 0], xy[:, 1]), crs=CRS)
    sem = sem[~sem.geometry.duplicated()].reset_index(drop=True)
    pl = ejes[ejes.tipcalle == "PLAÇA"].dissolve("codvia", as_index=False)
    b = pl.bounds; pl = pl[np.hypot(b.maxx - b.minx, b.maxy - b.miny) <= PLAZA_MAX]
    plazas = gpd.GeoDataFrame({"plaza": pl.nomcalle.values}, geometry=pl.geometry.convex_hull.values, crs=CRS)
    return {"ejes": ejes, "semillas": sem, "plazas": plazas, "n_nodos": len(nod)}


def unidades(cj, R=R, F=F):
    """Nudos (envolvente) y tramos (líneas) para un radio R y una fusión F. Devuelve (unidades, zonas de nudo)."""
    ejes, semillas, plazas = cj["ejes"], cj["semillas"], cj["plazas"]
    # glorietas y plazas pequeñas: la plaza (envolvente) + las semillas a <= F/2 de ella son un nudo, sin encadenar más allá
    pz = gpd.GeoDataFrame(geometry=list(plazas.buffer(F / 2).union_all().geoms), crs=CRS)
    jp = gpd.sjoin(semillas, pz, predicate="within")
    # resto de semillas: buffer(F/2) + dissolve (enlace simple a distancia F)
    libres = semillas[~semillas.index.isin(jp.index)]
    blobs = gpd.GeoDataFrame(geometry=list(libres.buffer(F / 2).union_all().geoms), crs=CRS)
    j = gpd.sjoin(libres, blobs, predicate="within")
    hull = j.groupby("index_right").geometry.agg(lambda x: shapely.MultiPoint(list(x)).convex_hull)
    hp = [shapely.union_all([pz.geometry[i].buffer(-F / 2)] + list(jp[jp.index_right == i].geometry)).convex_hull for i in pz.index]
    nud = gpd.GeoDataFrame({"plaza": [True] * len(hp) + [False] * len(hull)}, geometry=hp + list(hull.values), crs=CRS)
    nud = nud[~nud.geometry.is_empty].reset_index(drop=True)
    nud["tipo"] = "nudo"
    bb = nud.bounds; nud["ext_m"] = np.hypot(bb.maxx - bb.minx, bb.maxy - bb.miny).round(0)
    zona = gpd.GeoDataFrame(geometry=nud.buffer(R).values, crs=CRS)
    # tramos: cada calle fuera de las zonas de nudo, unida y troceada en piezas de <= PIEZA m
    resto = gpd.overlay(ejes[["codvia", "geometry"]], zona, how="difference", keep_geom_type=True)
    resto = resto[~resto.geometry.is_empty].dissolve("codvia")
    piezas = []
    for cv, geom in resto.geometry.items():
        for ln in getattr(shapely.line_merge(geom), "geoms", [shapely.line_merge(geom)]):
            n = max(1, int(np.ceil(ln.length / PIEZA)))
            for i in range(n):
                piezas.append((cv, shapely.ops.substring(ln, i / n, (i + 1) / n, normalized=True)))
    tr = gpd.GeoDataFrame(piezas, columns=["codvia", "geometry"], crs=CRS)
    tr = tr[tr.length > 0].reset_index(drop=True)
    mid = tr.geometry.interpolate(0.5, normalized=True)
    tr["grupo"] = 0
    for cv, ix in tr.groupby("codvia").groups.items():          # calzadas paralelas de la misma calle: un tramo
        if len(ix) == 1: continue
        xy = shapely.get_coordinates(mid[ix].values)
        tr.loc[ix, "grupo"] = fcluster(linkage(xy, "complete"), PARALELA, "distance")
    tr = tr.dissolve(["codvia", "grupo"], as_index=False)
    tr["tipo"] = "tramo"; tr["plaza"] = False; tr["long_m"] = tr.length.round(0)
    u = pd.concat([nud, tr[["codvia", "geometry", "tipo", "plaza", "long_m"]]], ignore_index=True)
    return gpd.GeoDataFrame(u, geometry="geometry", crs=CRS), zona


def asignar(g, u, R=R):
    """uid por siniestro (índice de g): nudo a <= R m de su envolvente; si no, el tramo más cercano."""
    nud = u[u.tipo == "nudo"]; tr = u[u.tipo == "tramo"]
    a = gpd.sjoin_nearest(g[["geometry"]], nud[["geometry"]], max_distance=R, distance_col="d")
    a = a[~a.index.duplicated()].index_right
    rest = g.loc[~g.index.isin(a.index), ["geometry"]]
    b = gpd.sjoin_nearest(rest, tr[["geometry"]], distance_col="d")
    b = b[~b.index.duplicated()].index_right
    return pd.concat([a, b]).reindex(g.index)


def tabla(g, uid, u, años=None):
    """Recuentos por unidad (todas las unidades, también las de 0; brutos n y ponderados W, por periodo A y B (periodos(años):
    primeros y últimos años, la misma duración) y A7 = antes de CORTE7) y puesto por total ponderado (empate: número de siniestros).
    años: los años completos (por defecto, los que hay en g)."""
    pA, pB = periodos(sorted(g["año"].unique()) if años is None else años)
    d = g.assign(uid=uid.values, A=g["año"].isin(pA), B=g["año"].isin(pB), A7=g.fecha < CORTE7)
    t = pd.DataFrame(index=u.index)
    t["n"] = d.groupby("uid").size(); t["W"] = d.groupby("uid").w.sum()
    for c, m in (("nA", d.A), ("nB", d.B), ("nA7", d.A7), ("nB7", ~d.A7)):
        t[c] = d[m].groupby("uid").size()
    for c, m in (("WA", d.A), ("WB", d.B), ("WA7", d.A7), ("WB7", ~d.A7)):
        t[c] = d[m].groupby("uid").w.sum()
    t = t.fillna(0)
    orden = t.sort_values(["W", "n"], ascending=False).index
    t["rank"] = pd.Series(np.arange(1, len(t) + 1), index=orden)
    return t, d


def geometria(u, R=R):
    """Lo que se dibuja de cada unidad (EPSG:25830): la zona del nudo (envolvente + R) o la línea del tramo."""
    return u.geometry.where(u.tipo == "tramo", u.geometry.buffer(R))


def _vias():
    """Callejero de vías vigentes (vias.json): tipo abreviado, nombre oficial y forma castellana si es válida."""
    import json, re
    v = pd.DataFrame(json.loads((RAW / "vias.json").read_text()))
    v = v[v.fechabaja.isna()].set_index("codvia")
    tr = v.traducnooficial.fillna("").str.strip()
    # la «traducción no oficial» a veces es otra cosa: provisional (EP …), con número, con año o con el tipo dentro
    mal = (tr.eq("") | tr.str.match(r"^E\.?\s?P\b") | (tr.str.contains(r"\d") & ~v.nomoficial.str.contains(r"\d"))
           | tr.str.contains(r"\bCARRER\b|\(PLAÇA\)"))
    v["es"] = tr.where(~mal, v.nomoficial)
    # sin el paréntesis aclaratorio («(ACTOR)», «(HISTORIADOR DE MEDICINA)»): más corto y es como se rotula la calle
    for c in ("nomoficial", "es"): v[c] = v[c].str.replace(r"\s*\([^)]*\)?", "", regex=True).str.strip()
    return v


def nombres(u, ejes, todos_pts, TOL=NOMBRE_TOL, R=R):
    """Nombre de cada unidad a partir del callejero (nombre oficial, con el tipo de vía abreviado), en dos formas:
    nom (oficial) y nom_es (forma castellana de vias.json cuando la da; si no, la oficial).
    - Nudo: calles del callejero que pasan por él (eje a <= TOL m de la envolvente y >= 10 m dentro de la zona).
      Se eligen por cuántos siniestros de la ciudad (todos los vehículos y años, asignados a la unidad) las nombran en
      su dirección, y a igualdad por longitud de la calle; se escriben «A cruce B» (la web lo pinta «A × B»), primero
      la calle y después la plaza, y entre calles la más larga primero. Glorieta o plaza pequeña: «PL X» si al menos
      PLAZA_VOTOS de sus siniestros nombran la plaza (si no, es una placita junto al cruce y manda «A cruce B»).
    - Tramo: «VÍA (A – B)», con A y B los nudos de sus extremos (la plaza o la calle que cruza), ordenados a lo largo
      del tramo; si no, la numeración del callejero («VÍA 80-96»); si no, la vía.
    todos_pts: siniestros de la ciudad con punto (EPSG:25830) con su uid y su ubicación."""
    import re, collections, geocodificar as GC          # mismo índice nombre -> codvia que el geocodificador
    v = _vias()
    ej = ejes[ejes.codvia.notna()].copy(); ej["codvia"] = ej.codvia.astype(int)
    ej = ej[ej.codvia.isin(v.index)]
    largo = ej.length.groupby(ej.codvia).sum()
    va = lambda c: f"{v.codtipovia[c]} {v.nomoficial[c]}"; es = lambda c: f"{v.codtipovia[c]} {v.es[c]}"
    # votos: calles que nombra la dirección de cada siniestro de la unidad (cruce: las dos; portal: la calle)
    def vias_de(ub):
        partes = ub.split(" cruce ", 1) if " cruce " in ub else [re.sub(r"\s+\d+\s*[A-Z]*$", "", ub)]
        return set().union(*[GC.codvias(p) for p in partes])
    cv_ub = {ub: vias_de(ub) for ub in todos_pts.ubicacion.astype(str).unique()}
    votos, n_u = collections.defaultdict(collections.Counter), todos_pts.groupby("uid").size()
    for (uid, ub), n in todos_pts.groupby(["uid", todos_pts.ubicacion.astype(str)]).size().items():
        for c in cv_ub[ub]: votos[uid][c] += n
    nud = u[u.tipo == "nudo"]; tr = u[u.tipo == "tramo"]
    j = gpd.sjoin(ej[["codvia", "geometry"]], gpd.GeoDataFrame(geometry=nud.buffer(TOL), crs=CRS), predicate="intersects")
    calles = {}                                     # nudo -> calles elegidas (codvia), en orden de votos
    out = {}
    for i, grp in j.groupby("index_right"):
        L = grp.geometry.intersection(nud.geometry[i].buffer(R)).length.groupby(grp.codvia).sum()
        vt = votos.get(i, collections.Counter())
        cand = sorted(L.index[L >= 10], key=lambda c: (-vt[c], -largo[c], c))
        calles[i] = cand
        pl = [c for c in cand if v.codtipovia[c] == "PL"]
        if nud.plaza[i] and pl and vt[pl[0]] >= PLAZA_VOTOS * n_u.get(i, 0):
            out[i] = (va(pl[0]), es(pl[0]), pl[0]); continue
        dos = sorted(cand[:2], key=lambda c: (v.codtipovia[c] == "PL", -largo[c], c))
        if dos: out[i] = (" cruce ".join(map(va, dos)), " cruce ".join(map(es, dos)), dos[0])
    # nudos sin calle a <= TOL m (pocos): la vía más cercana
    sin = nud.index.difference(list(out))
    if len(sin):
        cer = gpd.sjoin_nearest(gpd.GeoDataFrame(geometry=nud.geometry[sin], crs=CRS), ej[["codvia", "geometry"]])
        for i, c in cer.codvia.groupby(level=0).first().items(): out[i] = (va(c), es(c), c)
    # tramos
    zon = gpd.GeoDataFrame({"nudo": nud.index}, geometry=nud.buffer(R + 2).values, crs=CRS)
    num = lambda g: pd.to_numeric(g.stack(), errors="coerce").loc[lambda x: x > 0]
    ends = gpd.GeoDataFrame(geometry=tr.geometry.boundary, crs=CRS).explode(index_parts=False)
    ext = gpd.sjoin(ends[~ends.geometry.is_empty], zon, predicate="within").nudo.groupby(level=0).unique()
    for i, r in tr.iterrows():
        c = int(r.codvia)
        if c not in v.index: continue
        ln = max(getattr(r.geometry, "geoms", [r.geometry]), key=lambda x: x.length)
        nn = ext.get(i, [])
        pos = {}
        for k in nn:                                 # lo que cruza en cada extremo: la plaza o la calle principal que no es esta
            if k not in out: continue
            if out[k][0].count(" cruce ") == 0 and out[k][2] != c: x = out[k]
            else:
                otra = [z for z in calles.get(k, []) if z != c]
                if not otra: continue
                x = (va(otra[0]), es(otra[0]), otra[0])
            pos.setdefault(x[:2], ln.project(nud.geometry[k].centroid))
        if len(pos) >= 2:
            (a, pa), (b, pb) = sorted(pos.items(), key=lambda kv: kv[1])[0], sorted(pos.items(), key=lambda kv: kv[1])[-1]
            out[i] = (f"{va(c)} ({a[0]} – {b[0]})", f"{es(c)} ({a[1]} – {b[1]})", c); continue
        ns = num(ej[(ej.codvia == c) & ej.intersects(r.geometry.buffer(1))][["lf_add", "lt_add", "rf_add", "rt_add"]])
        rg = "" if ns.empty else f" {int(ns.min())}" + (f"-{int(ns.max())}" if ns.max() > ns.min() else "")
        out[i] = (va(c) + rg, es(c) + rg, c)
    N = pd.DataFrame({"nom": {i: x[0] for i, x in out.items()}, "nom_es": {i: x[1] for i, x in out.items()}}).reindex(u.index)
    # nombres repetidos (cada calzada de una avenida cruza por separado, dos entradas de la misma plaza): se añade
    # dónde está cada uno respecto a los demás, con siglas que valen en las dos lenguas (N, S, E, O; NE, SO…). Dos: el
    # eje en que más se separan. Tres o más: el octante desde su centro; si dos coinciden, número de oeste a este.
    p = u.geometry.representative_point()
    for nom, ix in N.groupby("nom").groups.items():
        if len(ix) < 2: continue
        x, y = p.x[ix] - p.x[ix].mean(), p.y[ix] - p.y[ix].mean()
        if len(ix) == 2:
            suf = (x > 0).map({True: "E", False: "O"}) if np.ptp(x) >= np.ptp(y) else (y > 0).map({True: "N", False: "S"})
        else:
            suf = pd.Series(np.array(["E", "NE", "N", "NO", "O", "SO", "S", "SE"])[
                np.round(np.degrees(np.arctan2(y, x)) / 45).astype(int) % 8], index=ix)
        if suf.duplicated().any(): suf = x.rank(method="first").astype(int).astype(str)
        for c in ("nom", "nom_es"): N.loc[ix, c] = N.loc[ix, c] + " (" + suf + ")"
    assert N.nom.notna().all() and N.nom.is_unique, "nombres de lugar vacíos o repetidos"
    return N


def congelar(u, N, con_casos, tol=CONGELA_TOL, ruta=NOMBRES_CSV):
    """Nombres congelados. u: unidades (EPSG:25830); N: nombres calculados (nom, nom_es) con el índice de u; con_casos:
    unidades con siniestros (las que se publican). Cada unidad con casos reutiliza el nombre de data/processed/
    nombres_lugares.csv si hay un lugar guardado del mismo tipo (y, en un tramo, de la misma vía) con el centroide a
    <= tol m; el emparejamiento es uno a uno, de la pareja más cercana a la más lejana. Las que no tienen pareja reciben el
    nombre calculado y se añaden al fichero (si coincide con uno ya guardado, se numera: «… (2)»), con la fecha de alta.
    Por qué 10 m: los nudos distintos tienen el centroide a >= 20,5 m (los tramos de una misma vía, a >= 33 m), así que a
    <= 10 m no hay dos candidatos; y al añadir un año de siniestros (simulado: 2022-24 → 2022-25) el 99 % de los lugares
    con casos se mueve menos de 4 m (nudos) o 12 m (tramos): solo 13 de 2.138 se mueven más de 10 m, porque cambian de
    forma (se funden o se parten) y entonces son otro lugar. Cambiar un nombre a propósito: editar el fichero y anotarlo
    en docs/cambios.csv. Devuelve nom, nom_es (los publicados), nom_calc, nom_es_calc y nuevo (alta en esta ejecución)."""
    import datetime
    N = N.copy(); N["nom_calc"], N["nom_es_calc"] = N.nom, N.nom_es; N["nuevo"] = False
    col = ["tipo", "codvia", "x", "y", "nom", "nom_es", "alta"]
    f = pd.read_csv(ruta, dtype={"codvia": "Int64"}) if ruta.exists() else pd.DataFrame(columns=col)
    ids = u.index[u.index.isin(con_casos)]
    c = u.geometry.centroid[ids]
    pares = []
    if len(f):
        fp = gpd.GeoDataFrame(f[["tipo", "codvia"]], geometry=gpd.points_from_xy(f.x, f.y), crs=CRS)
        j = gpd.sjoin(gpd.GeoDataFrame({"tipo_u": u.tipo[ids], "cv_u": u.codvia[ids]}, geometry=c.buffer(tol).values, crs=CRS),
                      fp, predicate="intersects")
        j = j[(j.tipo_u == j.tipo) & ((j.tipo == "nudo") | (j.cv_u.astype("Int64") == j.codvia))]
        j["d"] = [c[i].distance(fp.geometry[k]) for i, k in zip(j.index, j.index_right)]
        usados_u, usados_f = set(), set()
        for i, r in j.sort_values("d").iterrows():
            if i in usados_u or r.index_right in usados_f: continue
            usados_u.add(i); usados_f.add(r.index_right); pares.append((i, r.index_right))
    for i, k in pares:
        N.loc[i, ["nom", "nom_es"]] = f.loc[k, ["nom", "nom_es"]].values
    emp = {i for i, _ in pares}
    nombres_f = set(f.nom)
    nuevos = []
    for i in ids:
        if i in emp: continue
        nom, nom_es, k = N.at[i, "nom"], N.at[i, "nom_es"], 1
        while nom in nombres_f:                       # un nombre guardado no se reutiliza para otro lugar
            k += 1; nom, nom_es = f"{N.at[i, 'nom']} ({k})", f"{N.at[i, 'nom_es']} ({k})"
        nombres_f.add(nom); N.loc[i, ["nom", "nom_es", "nuevo"]] = [nom, nom_es, True]
        nuevos.append({"tipo": u.tipo[i], "codvia": u.codvia[i] if u.tipo[i] == "tramo" else pd.NA,
                       "x": round(c[i].x, 1), "y": round(c[i].y, 1), "nom": nom, "nom_es": nom_es,
                       "alta": datetime.date.today().isoformat()})
    if nuevos:
        f = pd.concat([f, pd.DataFrame(nuevos)], ignore_index=True)[col]
        f["codvia"] = f.codvia.astype("Int64")
        f.to_csv(ruta, index=False)
    print(f"nombres: {len(pares)} congelados reutilizados, {len(nuevos)} nuevos añadidos a {ruta.name} "
          f"({len(f)} guardados); en {int((N.loc[ids, 'nom'] != N.loc[ids, 'nom_calc']).sum())} el calculado difiere del congelado")
    return N


def pistas(lugares, alfa=0.05):
    """Pista de cada lugar. lugares: {clave: (k observados {c: n}, referencia de su tipo SIN el propio lugar {c: n})}.
    Prueba binomial unilateral por categoría; los lugares con menos de MIN_PISTA casos cuentan como p = 1. Holm sobre
    todas las pruebas (todo el mapa). Devuelve ({clave: categoría o None}, tabla de pruebas)."""
    filas = []
    for cl, (k, ref) in lugares.items():
        n = sum(k.values()); tot = sum(ref.values())
        for c in CATS:
            p0 = ref[c] / tot
            p = binomtest(int(k[c]), int(n), p0, alternative="greater").pvalue if n >= MIN_PISTA else 1.0
            filas.append((cl, c, int(k[c]), int(n), p0, p, n >= MIN_PISTA))
    T = pd.DataFrame(filas, columns=["lugar", "c", "x", "n", "p0", "p", "probada"])
    T["holm"] = multipletests(T.p, alpha=alfa, method="holm")[0]
    T["bh"] = multipletests(T.p, alpha=alfa, method="fdr_bh")[0]
    out = {}
    for cl, grp in T.groupby("lugar", sort=False):
        ok = grp[grp.holm]
        out[cl] = max(ok.c, key=lambda c: ok.set_index("c").x[c] / ok.n.iat[0] - ok.set_index("c").p0[c]) if len(ok) else None
    return out, T
