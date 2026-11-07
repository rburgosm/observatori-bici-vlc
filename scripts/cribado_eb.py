"""Cribado de puntos con exceso de siniestros según el uso (Bayes empírico, Hauer / HSM).

Grupo principal: VMP + BICI juntos ("vmp_o_bici"). Las espiras no distinguen patinete de bici (supuesto,
pendiente de confirmar con Movilidad): si suman los dos, es el único modelo en que numerador y exposición
son la misma población. Desgloses: "bici" y "vmp". Si las espiras cuentan ambos, la IMD sobrestima el uso
en bici (y lo infraestima en VMP) donde hay muchos patinetes: el riesgo de la bici sale a la baja y el del
VMP al alza. Si solo cuentan bicis, el desglose de bici es el limpio. Se presentan los dos escenarios.

Sitios: zonas de los contadores de carril bici de Movilidad (capa 225 + ODS de IMD laborable).
Se usan TODOS los contadores con IMD, también los que no tienen siniestros (población de
referencia completa, sin selección por el resultado). Puntos de conteo (revisión A6): se agrupan los contadores a
<50 m y los del mismo enlace de una vía (misma calle, <= 400 m, sin ningún cruce entre ellos: los dos sentidos del
Pont de l'Assut de l'Or); IMD sumada (salvo un contador de «ambos sentidos» en el mismo enlace, que ya cuenta todo) y
zona = unión de los círculos de sus contadores. Detalle y justificación junto a AGRUPA, MISMA_VIA y PASILLO.
Cada siniestro geocodificado se asigna al contador más cercano a <=R m y cuenta para su punto (sin doble conteo).

Modelo (SPF): binomial negativa NB2 por sitio y año (statsmodels),
    N_iy ~ NB(mu_iy, alpha),
    log mu_iy = b0 + b1 log(IMD bici_iy) + b2 log(IMD vehículos_i) + b3 log(1 + cruces_i) + año_y
  cruces_i: nodos de grado >= 3 del callejero (ejes.geojson) a <= R m del sitio (revisión metodológica A2, 04/11/2026).
  No usa ningún siniestro. Se compara en la salida con los nudos de scripts/lugares.py (los mismos nodos fundidos a
  30 m; glorietas, un nudo), calculados solo con el callejero, y con los nudos de la web (que añaden los puntos de cruce
  del geocodificador, es decir, posiciones de siniestros). Elección: los nodos sin fundir ajustan mucho mejor que los
  nudos fundidos (ΔAIC ≈ −13) y tanto como los de la web sin usar siniestros. Al fundir se pierde el tamaño del cruce: un
  cruce de avenida con dos calzadas y carril bici tiene varios nodos (más puntos de conflicto) y queda en un solo nudo.
EB multianual (Hauer 1997; HSM 2010, cap. 9 y apéndice 9A):
    w_i = 1 / (1 + alpha * sum_y mu_iy);   EB_i = w_i * sum mu + (1 - w_i) * sum N
    exceso_i = EB_i - sum mu;  P(theta_i > t) con la posterior gamma(1/alpha + N, 1/alpha + sum mu) (scipy), t = 1 y 1,5.
Niveles (revisión A3-A4): «claramente» = P(theta > 1) > P_CLARO con los tres radios (75, 100 y 150 m, cada uno con su
modelo): por encima de la media de los puntos con un tráfico parecido y estable con el radio; «quizá» = P(theta > 1) >
P_QUIZA con 100 m; el resto, «como la media». P(theta > UMBRAL = 1,5) («al menos un 50 % más») se calcula y se informa:
con los tres radios casi ningún punto la cumple, así que los datos sostienen «por encima de la media», no «anomalía». Calibración por simulación desde el propio modelo ajustado
(theta_i ~ gamma(1/alpha, alpha), N_iy ~ Poisson(theta_i mu_iy)): cuántos sitios marcaría cada regla y cuántos de los
marcados tienen en realidad theta < 1 o < UMBRAL.
Se ajustan tres modelos (VMP + bici, bici y VMP, todos con la misma IMD de las espiras); la salida principal
(cribado_eb_vmp_o_bici.csv) lleva por sitio los observados y esperados de bici y de VMP por separado (revisión A1).

Validación fuera de muestra, sin fuga:
  - las 6 particiones de los 4 años en 2 + 2 (ordenar con A, medir en B);
  - el ranking EB usa un modelo ajustado SOLO con A; el exceso observado en B usa un modelo ajustado SOLO con B;
  - bootstrap pareado de sitios (scipy no lo da para rankings: se remuestrea con numpy y se re-ordena)
    para la diferencia EB − recuento bruto en los siniestros de B recogidos por el top-k.

Covariables de diseño (modelo alternativo, no el del cribado): regulador semafórico municipal a <=R
(capa 182, independiente de los siniestros). El tipo de vía ciclista (capa 189) no sirve como covariable:
todos los contadores están en carril bici (se guarda en la salida solo como descripción).
No entran en el cribado principal: si el modelo «explica» el semáforo, el ranking deja de señalarlo.

Uso: .venv/bin/python -I scripts/cribado_eb.py [vmp_o_bici|bici|vmp]   (por defecto: los tres)
"""
import json
import re
import sys
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
CRS = "EPSG:25830"
# años: los completos (12 meses) de los siniestros que tienen fichero de IMD de carril bici de Movilidad
_f = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", usecols=["fecha"], parse_dates=["fecha"]).fecha
AÑOS = sorted(int(a) for a, n in _f.groupby(_f.dt.year).agg(lambda x: x.dt.month.nunique()).items()
              if n == 12 and (RAW / f"intensidades/carril_bici_{a}.ods").exists())
# IMD de vehículos y descripciones de contadores: el fichero más reciente que haya
IMD_VEH = sorted((RAW / "intensidades").glob("imds_vehiculos_*.ods"))[-1]
CB_ULT = RAW / f"intensidades/carril_bici_{AÑOS[-1]}.ods"
N_BOOT = 2000
RNG = np.random.default_rng(20261103)
RADIO = 100                       # radio principal (m)
RADIOS = (75, 100, 150)           # el «claramente» tiene que mantenerse con los tres
UMBRAL, P_CLARO, P_QUIZA = 1.5, .95, .80
N_SIM = 1000
sys.path.insert(0, str(Path(__file__).resolve().parent))      # -I no añade la carpeta del script
import lugares as LG                                            # nudos de cruce (scripts/lugares.py)
TIPOS_VIA = {"1": "carril bici", "4": "Jardín del Turia", "6": "senda ciclable", "7": "bus-bici",
             "2": "ciclocalle", "9": "ciclobarrio", "3": "peatonal"}
pd.set_option("display.width", 160)


# ---------- exposición ----------
def imd_anual(path, patron):
    """Media de las IMD mensuales (>0) por código; los meses a 0 se tratan como avería."""
    # el formato cambia entre hojas (columnas desplazadas, sin «Sentido»): se detectan por contenido
    partes = []
    for h in pd.read_excel(path, engine="odf", sheet_name=None, header=None).values():
        es_cod = h.apply(lambda c: c.astype(str).str.strip().str.fullmatch(patron).mean())
        c_cod = es_cod.idxmax()
        filas = h[h[c_cod].astype(str).str.strip().str.fullmatch(patron)]
        num = filas.drop(columns=c_cod).apply(lambda c: pd.to_numeric(c, errors="coerce").notna().mean())
        c_imd = num[num > .5].index.max()                  # la columna numérica más a la derecha
        partes.append(pd.DataFrame({"cod": filas[c_cod].astype(str).str.strip(),
                                    "imd": pd.to_numeric(filas[c_imd], errors="coerce")}))
    d = pd.concat(partes)
    return d[d.imd > 0].groupby("cod").imd.agg(["mean", "size"])


esp = gpd.read_file(RAW / "siniestros/espiras_bici.geojson").to_crs(CRS)
esp = esp[esp.geometry.notna()].drop_duplicates("idpm")
bici = []
for a in AÑOS:
    t = imd_anual(RAW / f"intensidades/carril_bici_{a}.ods", r"P\d+")
    t = t[t["size"] >= 6]                                  # al menos medio año con dato
    bici.append(pd.DataFrame({"idpm": t.index.str[1:].astype(int), "año": a, "imd": t["mean"].values}))
bici = pd.concat(bici)
cont = esp[esp.idpm.isin(bici.idpm)][["idpm", "geometry"]].reset_index(drop=True)


def descripciones():
    """Descripciones de cada contador (idpm → textos de todos los años, del más reciente al más antiguo) en los ODS de carril
    bici: el texto cambia entre años (en 2025 desaparece «(AMBOS SENTIDOS)»)."""
    out = {}
    for a in sorted(AÑOS, reverse=True):
        for h in pd.read_excel(RAW / f"intensidades/carril_bici_{a}.ods", engine="odf", sheet_name=None, header=None).values():
            es_cod = h.apply(lambda c: c.astype(str).str.strip().str.fullmatch(r"P\d+").mean()); c_cod = es_cod.idxmax()
            for _, r in h[h[c_cod].astype(str).str.strip().str.fullmatch(r"P\d+")].iterrows():
                out.setdefault(int(str(r[c_cod]).strip()[1:]), []).append(str(r[c_cod + 1]).strip())
    return pd.Series(out, name="desc")


# ---------- puntos de conteo: contadores agrupados (revisión A6, 04/11/2026) ----------
# Dos reglas, unidas por componentes conexas (scipy):
#  1) a < AGRUPA m (cualquier vía): los contadores de un mismo cruce (antes, la única regla);
#  2) MISMO ENLACE: el eje más cercano (a <= VIA_TOL m) es la misma vía (codvia), están a <= MISMA_VIA m y no hay ningún
#     nodo de grado >= 3 del callejero en un pasillo de PASILLO m a cada lado del segmento que los une: miden el mismo
#     flujo (los dos sentidos de un puente, las dos aceras de una avenida a la altura de la misma manzana) y no son puntos
#     independientes. Con 10 m de pasillo pasaban pares de bloques distintos de Blasco Ibáñez (el segmento va por el
#     bulevar, lejos de los cruces de cada calzada); con 30 m solo quedan los del mismo enlace. MISMA_VIA: el par sin
#     nodos más largo es el Assut de l'Or (328 m, los dos extremos del puente); el siguiente, a 556 m, ya cruza calles.
# IMD del punto: suma de sus contadores (sentidos o carriles distintos), salvo en un mismo enlace con algún contador de
# «ambos sentidos», que ya cuenta todo el flujo: entonces vale ese (Pont de Fusta: P1163 «ambos sentidos» y P238 dan la
# misma IMD cada año, 2.997 y 3.035 en 2022; sumarlos la duplicaría).
# Zona del punto a R m: la UNIÓN de los círculos de sus contadores (cada siniestro va al contador más cercano a <= R m y
# cuenta para su punto). Con el centroide, el círculo del Assut quedaría en medio del puente, a 164 m de cada contador, y
# dejaría fuera los dos extremos, donde se cruza con las calles; con la unión, cada contador sigue mirando su sitio.
AGRUPA, MISMA_VIA, VIA_TOL, PASILLO = 50, 400, 15, 30
_ds = cont.idpm.map(descripciones())
cont["ambos"] = _ds.map(lambda x: any(re.search(r"ambos\s+s?entidos", d, re.I) for d in x) if isinstance(x, list) else False)
_ej = gpd.read_file(RAW / "siniestros/ejes.geojson").to_crs(CRS)
_nn = gpd.sjoin_nearest(cont[["geometry"]], _ej[["codvia", "geometry"]], max_distance=VIA_TOL, how="left")
cont["codvia"] = _nn[~_nn.index.duplicated()].codvia


def agrupar_contadores(cont, nodos):
    from scipy.sparse.csgraph import connected_components
    import shapely
    xy = np.c_[cont.geometry.x, cont.geometry.y]
    d = np.hypot(xy[:, 0, None] - xy[:, 0], xy[:, 1, None] - xy[:, 1])
    cerca = d < AGRUPA
    enlace = np.zeros_like(cerca)
    for i, j in zip(*np.where(np.triu(d <= MISMA_VIA, 1))):
        if pd.notna(cont.codvia[i]) and cont.codvia[i] == cont.codvia[j]:
            pas = shapely.LineString([xy[i], xy[j]]).buffer(PASILLO, cap_style="flat")
            enlace[i, j] = enlace[j, i] = not nodos.intersects(pas).any()
    _, cont["sitio"] = connected_components(cerca | enlace, directed=False)
    _, cont["enlace"] = connected_components(enlace, directed=False)     # bloques del mismo enlace (para «ambos sentidos»)
    return [sorted(cont.idpm[np.where(enlace[i])[0]].tolist() + [cont.idpm[i]]) for i in range(len(cont)) if enlace[i].any()]


_v0 = pd.DataFrame({"metodo": pd.Series(dtype=str), "lon": pd.Series(dtype=float), "lat": pd.Series(dtype=float)})
CJ = LG.callejero(_v0)                                   # callejero sin siniestros (también para los cruces del círculo)
PARES_ENLACE = sorted({tuple(x) for x in agrupar_contadores(cont, CJ["semillas"])})
sitios = cont.dissolve("sitio").centroid.rename("geometry").to_frame().set_geometry("geometry")


def zonas(radio):
    """Zona de cada punto de conteo: unión de los círculos de radio R de sus contadores (índice: sitio)."""
    return cont.assign(geometry=cont.buffer(radio)).dissolve("sitio")[["geometry"]]


_e = bici.merge(cont[["idpm", "sitio", "enlace", "ambos"]], on="idpm")
_e = _e[_e.ambos | ~_e.groupby(["enlace", "año"]).ambos.transform("any")]           # en un enlace con «ambos», solo esos
_e = pd.concat([_e[_e.ambos].groupby(["sitio", "enlace", "año"]).imd.max(),         # ya cuentan todo el flujo
                _e[~_e.ambos].groupby(["sitio", "enlace", "año"]).imd.sum()]).reset_index()   # sentidos o carriles distintos
expo = (_e.groupby(["sitio", "año"]).imd.sum().rename("imd_bici").to_frame()
        .join(bici.merge(cont[["idpm", "sitio"]], on="idpm").groupby(["sitio", "año"]).size().rename("n_cont")).reset_index())
# un sitio-año solo vale si están todos sus contadores (si no, la IMD sumada está incompleta)
expo = expo[expo.n_cont == expo.sitio.map(cont.groupby("sitio").size())]

tr = gpd.read_file(RAW / "siniestros/intensidad_tramos.geojson")
tr = tr[tr.geometry.notna()].to_crs(CRS)
veh = imd_anual(IMD_VEH, r"A\d+")
tr = tr.merge(veh["mean"].rename("imd_veh"), left_on="idtramo", right_index=True)

# ---------- diseño del sitio ----------
reg = gpd.read_file(RAW / "siniestros/reguladores_semaforos.geojson")
reg = reg[reg.geometry.notna()].to_crs(CRS)
via = gpd.read_file(RAW / "siniestros/carriles_bici.geojson")
via = via[via.geometry.notna() & via.estado.isin(TIPOS_VIA)].to_crs(CRS)
tv = gpd.sjoin_nearest(sitios, via[["estado", "geometry"]], max_distance=30, how="left", distance_col="d")
tv = tv[~tv.index.duplicated()]
sitios["tipo_via"] = tv.estado.map(TIPOS_VIA).fillna("sin vía a 30 m")
# agrupación con casos suficientes: carril bici / Turia / otro
sitios["via"] = sitios.tipo_via.where(sitios.tipo_via.isin(["carril bici", "Jardín del Turia"]), "otra o ninguna")

# ---------- cruces dentro del círculo (A2) ----------
# principal: nudos de lugares.py SOLO con el callejero (sin puntos del geocodificador, que salen de los siniestros)
NODOS = CJ["semillas"]                                   # nodos de grado >= 3, sin fundir
_u = LG.unidades(CJ)[0]; NUDOS = _u[_u.tipo == "nudo"].reset_index(drop=True)
_u = LG.unidades(LG.callejero(LG.siniestros()[0]))[0]; NUDOS_WEB = _u[_u.tipo == "nudo"].reset_index(drop=True)


def cruces(radio, capa):
    """Número de elementos de la capa (nodos o nudos) a <= radio m de cada sitio (distancia a su geometría)."""
    z = zonas(radio).rename_axis("sitio_v").reset_index()
    return gpd.sjoin(capa[["geometry"]], z, predicate="intersects").groupby("sitio_v").size().reindex(sitios.index, fill_value=0)


print(f"callejero: {len(NODOS)} nodos de grado >= 3 → {len(NUDOS)} nudos solo con el callejero ({len(NUDOS_WEB)} en la web, "
      f"con los cruces del geocodificador)")

# ---------- siniestros ----------
s = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", parse_dates=["fecha"])
n0 = len(s)
s = s[s.fecha.dt.year.isin(AÑOS)]
s = s.loc[~s.drop(columns="id").duplicated()]
s = s[s.lon.notna()]
s["año"] = s.fecha.dt.year
s = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs="EPSG:4326").to_crs(CRS)
s["vmp"] = s.unidades.str.contains("VMP", na=False)
s["bici"] = s.unidades.str.contains("BICICLETA", na=False)

print(f"siniestros: {n0} → {len(s)} geocodificados {AÑOS[0]}-{AÑOS[-1]} sin duplicados (bici: {s.bici.sum()}, VMP: {s.vmp.sum()})")
print(f"contadores con IMD y posición: {len(cont)} → {len(sitios)} sitios; sitio-años con exposición: {len(expo)}")
_d = lambda a, b: cont.set_index("idpm").geometry[a].distance(cont.set_index("idpm").geometry[b])
print(f"agrupados por el mismo enlace (misma vía, <= {MISMA_VIA} m, sin cruces a {PASILLO} m): "
      + "; ".join(f"{'+'.join(f'P{i}' for i in g)} ({_d(g[0], g[-1]):.0f} m)" for g in PARES_ENLACE))
print(f"tramos de vehículos con IMD ({IMD_VEH.stem}) y geometría: {len(tr)}; reguladores semafóricos: {len(reg)}")
print("tipo de vía ciclista del sitio:", sitios.tipo_via.value_counts().to_dict(), "\n")


def panel(radio, grupo):
    """Sitio × año con N, IMD bici, IMD vehículos (máximo de los tramos a <=radio) y diseño."""
    ev = s[s[grupo]] if grupo != "vmp_o_bici" else s[s.vmp | s.bici]
    # cada siniestro, al contador más cercano a <= radio m, y de ahí a su punto (unión de círculos); en un empate exacto
    # entre contadores, el primero: ningún siniestro cuenta en dos puntos
    asig = gpd.sjoin_nearest(ev[["año", "geometry"]], cont[["sitio", "geometry"]], max_distance=radio, how="inner")
    asig = asig[~asig.index.duplicated()]
    n = asig.groupby(["sitio", "año"]).size().rename("N")
    p = expo.set_index(["sitio", "año"]).join(n).fillna({"N": 0}).reset_index()
    zonas_r = zonas(radio).rename_axis("sitio_v").reset_index()
    v = gpd.sjoin(tr[["imd_veh", "geometry"]], zonas_r)
    p["imd_veh"] = p.sitio.map(v.groupby("sitio_v").imd_veh.max())
    p["sin_veh"] = p.imd_veh.isna().astype(int)
    # sin tramo aforado cerca: vía local; se imputa la IMD mínima observada y se marca con indicador
    p["imd_veh"] = p.imd_veh.fillna(tr.imd_veh.min())
    p["l_bici"], p["l_veh"] = np.log(p.imd_bici), np.log(p.imd_veh)
    sem = gpd.sjoin(reg[["geometry"]], zonas_r).groupby("sitio_v").size()
    p["semaforo"] = p.sitio.map(sem).fillna(0).gt(0).astype(int)
    p["via"] = p.sitio.map(sitios.via)
    for c, capa in (("cruces", NODOS), ("nudos", NUDOS), ("nudos_web", NUDOS_WEB)):
        p[c] = p.sitio.map(cruces(radio, capa))
        p["l_" + c] = np.log1p(p[c])
    return p, len(asig), len(ev)


F_SIN = "N ~ l_bici + l_veh + sin_veh + C(año)"
F_BASE = F_SIN + " + l_cruces"
F_DISEÑO = F_BASE + " + semaforo"


def ajustar(p, f=F_BASE):
    return smf.negativebinomial(f, p).fit(disp=0, maxiter=300)


def eb(p, nb, años):
    q = p[p.año.isin(años)].copy()
    q["mu"] = nb.predict(q)
    a = nb.params["alpha"]
    g = q.groupby("sitio").agg(N=("N", "sum"), mu=("mu", "sum"), expo=("imd_bici", "sum"))
    g["w"] = 1 / (1 + a * g.mu)
    g["EB"] = g.w * g.mu + (1 - g.w) * g.N
    g["exceso"] = g.EB - g.mu
    g["p_exceso"] = stats.gamma.sf(1, a=1 / a + g.N, scale=1 / (1 / a + g.mu))
    g["p_umbral"] = stats.gamma.sf(UMBRAL, a=1 / a + g.N, scale=1 / (1 / a + g.mu))
    g["tasa_bruta"] = g.N / g.expo
    return g


def comparar_cruces(p, nb):
    """A2: ¿qué medida de los cruces? LR frente al modelo sin cruces, AIC y sitios con P(theta > 1) > 0,95."""
    sin = ajustar(p, F_SIN)
    out = {"sin": {"aic": round(float(sin.aic), 1), "alpha": round(float(sin.params["alpha"]), 3),
                   "p95": int((eb(p, sin, AÑOS).p_exceso > .95).sum())}}
    print(f"cruces en el círculo: sin cruces α={sin.params['alpha']:.3f} AIC={sin.aic:.1f}, P>0,95 en {out['sin']['p95']}")
    for nom, f in (("nodos (principal)", F_BASE), ("nodos, lineal", F_SIN + " + cruces"),
                   ("nudos fundidos", F_SIN + " + l_nudos"), ("nudos de la web", F_SIN + " + l_nudos_web")):
        m = nb if f == F_BASE else ajustar(p, f)
        lr = 2 * (m.llf - sin.llf)
        k = [c for c in m.params.index if any(x in c for x in ("cruces", "nodos", "nudos"))][0]
        out[nom] = {"lr": round(float(lr), 1), "p": float(f"{stats.chi2.sf(lr, 1):.2g}"), "aic": round(float(m.aic), 1),
                    "alpha": round(float(m.params["alpha"]), 3), "coef": round(float(m.params[k]), 3),
                    "p95": int((eb(p, m, AÑOS).p_exceso > .95).sum())}
        print(f"  + {nom:18s} coef={m.params[k]:.3f} LR={lr:.1f} (p={stats.chi2.sf(lr, 1):.2g}) AIC={m.aic:.1f} "
              f"α={m.params['alpha']:.3f} P>0,95 en {out[nom]['p95']}")
    sit = p.drop_duplicates("sitio")
    print(f"  nodos por sitio: mediana {sit.cruces.median():.0f}, rango {sit.cruces.min()}-{sit.cruces.max()}; "
          f"nudos fundidos: mediana {sit.nudos.median():.0f}")
    out["mediana"] = float(sit.cruces.median()); out["rango"] = [int(sit.cruces.min()), int(sit.cruces.max())]
    return out


def simular(p, nb, g):
    """A3: calibración desde el propio modelo (sin puntos «especiales»: los theta solo varían como dice la gamma).
    No reajusta el modelo: mu y alpha fijos (la posterior tampoco propaga su incertidumbre)."""
    q = p.assign(mu=nb.predict(p))
    a = nb.params["alpha"]
    mu = q.pivot_table(index="sitio", columns="año", values="mu").reindex(g.index)
    smu = mu.sum(axis=1).values
    res = {"p1": [], "pu": [], "fd1": [], "fdu": []}
    for _ in range(N_SIM):
        th = RNG.gamma(1 / a, a, len(smu))
        n = RNG.poisson(np.nan_to_num(mu.values) * th[:, None]).sum(axis=1)
        p1 = stats.gamma.sf(1, a=1 / a + n, scale=1 / (1 / a + smu))
        pu = stats.gamma.sf(UMBRAL, a=1 / a + n, scale=1 / (1 / a + smu))
        res["p1"].append((p1 > P_CLARO).sum()); res["pu"].append((pu > P_CLARO).sum())
        res["fd1"].append((th[p1 > P_CLARO] < 1).sum()); res["fdu"].append((th[pu > P_CLARO] < UMBRAL).sum())
    r = {k: round(float(np.mean(v)), 1) for k, v in res.items()}
    r.update({"obs_p1": int((g.p_exceso > P_CLARO).sum()), "obs_pu": int((g.p_umbral > P_CLARO).sum()),
              "a_priori_1": round(float(stats.gamma.sf(1, 1 / a, scale=a)), 2),
              "a_priori_u": round(float(stats.gamma.sf(UMBRAL, 1 / a, scale=a)), 2)})
    print(f"calibración ({N_SIM} simulaciones desde el modelo): P(θ>1)>{P_CLARO}: se esperan {r['p1']} (de ellos con θ<1: {r['fd1']}), "
          f"se observan {r['obs_p1']}; P(θ>{UMBRAL})>{P_CLARO}: se esperan {r['pu']} (con θ<{UMBRAL}: {r['fdu']}), "
          f"se observan {r['obs_pu']}. A priori P(θ>1)={r['a_priori_1']}, P(θ>{UMBRAL})={r['a_priori_u']}")
    return r


def resumen_modelo(nb, p):
    po = smf.poisson(F_BASE, p).fit(disp=0)
    lr = 2 * (nb.llf - po.llf)
    b, se = nb.params["l_bici"], nb.bse["l_bici"]
    mu = nb.predict(p)
    pear = (((p.N - mu) ** 2) / (mu * (1 + nb.params["alpha"] * mu))).sum() / nb.df_resid
    print(nb.summary2().tables[1][["Coef.", "Std.Err.", "P>|z|"]].round(3).to_string())
    print(f"alpha={nb.params['alpha']:.3f} | LR NB vs Poisson={lr:.1f} (p={stats.chi2.sf(lr, 1) / 2:.2g}) | "
          f"Pearson χ²/gl NB={pear:.2f} | AIC NB={nb.aic:.0f}, Poisson={po.aic:.0f}")
    print(f"elasticidad IMD bici = {b:.2f} (IC95 {b - 1.96 * se:.2f}–{b + 1.96 * se:.2f}); "
          f"test b=1 (offset puro): p={2 * stats.norm.sf(abs(b - 1) / se):.2g}")
    dec = p.assign(mu=mu, d=pd.qcut(mu, 5, labels=False))
    print("calibración por quintiles de μ (observado/predicho):",
          " ".join(f"{r.N:.0f}/{r.mu:.0f}" for r in dec.groupby("d")[["N", "mu"]].sum().itertuples()))


def top(r, k):
    return r.sort_values(ascending=False, kind="stable").index[:k]


def validar(p, k_list=(10, 20)):
    """6 particiones 2+2 sin fuga + bootstrap pareado de sitios para EB − bruto."""
    filas, boot, rhos = [], {k: [] for k in k_list}, []
    for A in combinations(AÑOS, 2):
        B = [y for y in AÑOS if y not in A]
        pa, pb = p[p.año.isin(A)], p[p.año.isin(B)]
        ga, gb = eb(pa, ajustar(pa), A), eb(pb, ajustar(pb), B)
        comun = ga.index.intersection(gb.index)
        ga, gb = ga.loc[comun], gb.loc[comun]
        res_b = gb.N - gb.mu                               # exceso observado en B (modelo de B)
        met = {"bruto": ga.N, "tasa": ga.tasa_bruta, "EB": ga.exceso}
        for k in k_list:
            for nom, r in met.items():
                t = top(r, k)
                filas.append((f"{A[0] % 100}-{A[1] % 100}", k, nom, gb.loc[t, "N"].sum(), res_b.loc[t].sum(),
                              (res_b.loc[t] > 0).mean()))
            # bootstrap pareado: remuestrear sitios, re-ordenar en la muestra, comparar EB y bruto
            idx = np.arange(len(comun))
            for _ in range(N_BOOT // 6):
                m = RNG.choice(idx, len(idx), replace=True)
                eb_r = pd.Series(ga.exceso.values[m]).sort_values(ascending=False, kind="stable").index[:k]
                br_r = pd.Series(ga.N.values[m]).sort_values(ascending=False, kind="stable").index[:k]
                rb = res_b.values[m]
                boot[k].append(rb[eb_r].sum() - rb[br_r].sum())
        rhos.append(stats.spearmanr(ga.exceso, res_b).statistic)
    t = pd.DataFrame(filas, columns=["A", "k", "método", "N_B", "exceso_B", "pct_N>μ"])
    print(f"validación fuera de muestra sin fuga (6 particiones 2+2, ~{len(comun)} sitios):")
    piv = t.pivot_table(index=["k", "método"], values=["N_B", "exceso_B", "pct_N>μ"], aggfunc="mean")
    gana = t.pivot_table(index=["A", "k"], columns="método", values="exceso_B")
    print(piv.round(2).to_string())
    for k in k_list:
        gk = gana.xs(k, level="k")
        d = np.array(boot[k])
        print(f"  top-{k}: EB > bruto en {(gk.EB > gk.bruto).sum()}/6 particiones, EB > tasa en {(gk.EB > gk.tasa).sum()}/6; "
              f"bootstrap EB−bruto en exceso_B: media {d.mean():.1f}, IC95 {np.percentile(d, 2.5):.1f}–{np.percentile(d, 97.5):.1f}, "
              f"P(EB≤bruto)={(d <= 0).mean():.2f}")
    print(f"  Spearman exceso EB (A) vs exceso observado (B): media {np.mean(rhos):.2f} "
          f"(rango {min(rhos):.2f}–{max(rhos):.2f})")
    # resumen para la página «Mètode» (exportar_web.py lo lee de cribado_eb_coef.json)
    VAL.clear(); VAL["particiones"] = 6; VAL["spearman_AB"] = round(float(np.mean(rhos)), 2)
    for k in k_list:
        gk, d = gana.xs(k, level="k"), np.array(boot[k])
        VAL[f"top{k}"] = {"eb_gana": int((gk.EB > gk.bruto).sum()), "ic95": [round(float(np.percentile(d, 2.5)), 1),
                          round(float(np.percentile(d, 97.5)), 1)], "p_eb_no_mejor": round(float((d <= 0).mean()), 2)}
    return t


def diseño(p):
    m = ajustar(p, F_DISEÑO)
    base = ajustar(p)
    lr = 2 * (m.llf - base.llf)
    print(f"modelo con diseño (semáforo a <=100 m): LR frente al base = {lr:.1f} (gl=1, p={stats.chi2.sf(lr, 1):.2g}); "
          f"AIC {m.aic:.0f} frente a {base.aic:.0f}")
    t = m.summary2().tables[1]
    t = t[t.index.str.contains("semaforo")]
    for n, r in t.iterrows():
        print(f"  {n:55s} RR={np.exp(r['Coef.']):.2f} (IC95 {np.exp(r['[0.025']):.2f}–{np.exp(r['0.975]']):.2f}), p={r['P>|z|']:.3g}")
    print("  sitios por diseño:", p.drop_duplicates("sitio").semaforo.value_counts().to_dict())
    return m


def describir():
    hojas = pd.read_excel(CB_ULT, engine="odf", sheet_name=None).values()
    d = (pd.concat(hojas).iloc[:, :2].set_axis(["cod", "desc"], axis=1).dropna().drop_duplicates("cod"))
    d = d[d.cod.astype(str).str.fullmatch(r"P\d+")].assign(idpm=lambda x: x.cod.str[1:].astype(int))
    c = cont.merge(d, on="idpm", how="left")
    return c.groupby("sitio").apply(lambda x: " | ".join(f"P{i} {str(t)[:45]}" for i, t in zip(x.idpm, x["desc"])),
                                    include_groups=False)


DESC = describir()


def cribado(grupo):
    p, asignados, total = panel(RADIO, grupo)
    print(f"\n{'=' * 30} {grupo.upper()}, radio {RADIO} m {'=' * 30}")
    print(f"{asignados} de {total} siniestros asignados a un sitio ({asignados / total:.0%}); {p.sitio.nunique()} sitios, "
          f"{len(p)} sitio-años, {int((p.groupby('sitio').N.sum() == 0).sum())} sitios con 0")
    nb = ajustar(p)
    # sin índice de año: los efectos de año recogen la cobertura de geolocalización creciente (revisión A5), no se exportan
    COEF[grupo] = {"elasticidad_bici": round(float(nb.params["l_bici"]), 4),
                   "cruces_coef": round(float(nb.params["l_cruces"]), 3)}
    resumen_modelo(nb, p)
    COEF[grupo]["cruces"] = comparar_cruces(p, nb)
    g = eb(p, nb, AÑOS)
    g["rank_bruto"] = g.N.rank(ascending=False, method="min")
    g["rank_tasa"] = g.tasa_bruta.rank(ascending=False, method="min")
    g["rank_eb"] = g.exceso.rank(ascending=False, method="min")
    print(f"\nSpearman ranking EB vs recuento bruto: {stats.spearmanr(g.exceso, g.N).statistic:.2f}; "
          f"vs tasa bruta: {stats.spearmanr(g.exceso, g.tasa_bruta).statistic:.2f}")
    for k in (10, 20):
        tb, ttasa, te = (set(g.nsmallest(k, c).index) for c in ("rank_bruto", "rank_tasa", "rank_eb"))
        print(f"top-{k}: comparte con bruto {len(te & tb)}, con tasa bruta {len(te & ttasa)}")
    print(f"sitios con P(exceso)>0,95: {(g.p_exceso > .95).sum()}; >0,90: {(g.p_exceso > .90).sum()}")
    sim = simular(p, nb, g)
    # P con los otros radios del criterio (cada radio con su modelo)
    for r_ in RADIOS:
        if r_ == RADIO: continue
        pp, _, _ = panel(r_, grupo)
        gg = eb(pp, ajustar(pp), AÑOS).reindex(g.index)
        g[f"p_exceso_{r_}"], g[f"p_umbral_{r_}"] = gg.p_exceso, gg.p_umbral
    g[f"p_exceso_{RADIO}"], g[f"p_umbral_{RADIO}"] = g.p_exceso, g.p_umbral
    pu = g[[f"p_umbral_{r_}" for r_ in RADIOS]]
    p1 = g[[f"p_exceso_{r_}" for r_ in RADIOS]]
    # p1: P(θ>1) > 0,95; pu: P(θ>UMBRAL) > 0,95 (pu90: > 0,90); _100 con 100 m; _3r con los tres radios
    reglas = {"p1_100": g.p_exceso > P_CLARO, "p1_3r": (p1 > P_CLARO).all(axis=1), "pu_100": g.p_umbral > P_CLARO,
              "pu_3r": (pu > P_CLARO).all(axis=1), "pu90_3r": (pu > .90).all(axis=1)}
    print("reglas de «claramente»:", {k: int(v.sum()) for k, v in reglas.items()})
    g["claro"] = (p1 > P_CLARO).all(axis=1)
    g["nivel"] = np.select([g.claro, g.p_exceso > P_QUIZA], [2, 1], 0)
    print(f"niveles: claramente {int((g.nivel == 2).sum())}, quizá {int((g.nivel == 1).sum())}, como la media {int((g.nivel == 0).sum())}\n")
    validar(p)
    COEF[grupo].update({"alpha": round(float(nb.params["alpha"]), 3), "asignados": int(asignados), "geolocalizados": int(total),
                        "validacion": dict(VAL), "radio": {}, "sim": sim, "reglas": {k: int(v.sum()) for k, v in reglas.items()},
                        "niveles": {str(k): int((g.nivel == k).sum()) for k in (2, 1, 0)}})
    print()
    m = diseño(p)
    gd = eb(p, m, AÑOS)
    print(f"  ranking con diseño frente al base: Spearman {stats.spearmanr(gd.exceso, g.exceso).statistic:.2f}, "
          f"solape top-10 {len(set(gd.exceso.nlargest(10).index) & set(g.exceso.nlargest(10).index))}")

    g["contadores"] = DESC.reindex(g.index)
    g["tipo_via"] = sitios.tipo_via.reindex(g.index)
    g["semaforo_100m"] = p.drop_duplicates("sitio").set_index("sitio").semaforo.reindex(g.index)
    g["cruces_100m"] = p.drop_duplicates("sitio").set_index("sitio").cruces.reindex(g.index)
    g["n_años"] = p.groupby("sitio").año.nunique().reindex(g.index)
    g["n_cont"] = cont.groupby("sitio").size().reindex(g.index)
    g["idpm"] = cont.groupby("sitio").idpm.agg(lambda x: " ".join(map(str, sorted(x)))).reindex(g.index)
    ll = sitios.to_crs("EPSG:4326")
    g["lon"], g["lat"] = ll.geometry.x.reindex(g.index), ll.geometry.y.reindex(g.index)
    out = g.sort_values("exceso", ascending=False)
    out.round(4).to_csv(ROOT / f"outputs/cribado_eb_{grupo}.csv")
    print(f"\ntop-10 por exceso EB ({grupo}):")
    for _, r in out.head(10).iterrows():
        print(f"  {str(r.contadores)[:58]:58s} N={r.N:3.0f} μ={r.mu:5.1f} EB={r.EB:5.1f} P={r.p_exceso:.2f} "
              f"P{UMBRAL}={r.p_umbral:.2f} nivel={r.nivel} bruto#{r.rank_bruto:.0f} tasa#{r.rank_tasa:.0f}")

    print(f"\n--- sensibilidad {grupo} (elasticidad bici, alpha, Spearman EB-bruto, solape top-10 con el principal) ---")
    top_ref = set(out.index[:10])
    alta = set(g.index[g.p_exceso > P_CLARO])
    for radio in (75, 150, 200):
        pp, asig, tot = panel(radio, grupo)
        mm = ajustar(pp)
        gg = eb(pp, mm, AÑOS)
        a2 = set(gg.index[gg.p_exceso > P_CLARO])
        COEF[grupo]["radio"][str(radio)] = {"solape_top10": len(top_ref & set(gg.exceso.nlargest(10).index)),
                                            "elasticidad": round(float(mm.params["l_bici"]), 2),
                                            "jaccard_p95": round(len(alta & a2) / max(len(alta | a2), 1), 2)}
        print(f"R={radio}: asignados {asig}/{tot}, b_bici={mm.params['l_bici']:.2f}, alpha={mm.params['alpha']:.2f}, "
              f"Spearman={stats.spearmanr(gg.exceso, gg.N).statistic:.2f}, solape top-10={len(top_ref & set(gg.exceso.nlargest(10).index))}, "
              f"P>0,95: {len(a2)} (Jaccard con {RADIO} m {COEF[grupo]['radio'][str(radio)]['jaccard_p95']})")
    return out


COEF = {}
VAL = {}
grupos_arg = sys.argv[1:] or ["vmp_o_bici", "bici", "vmp"]
res = {gr: cribado(gr) for gr in grupos_arg}
print("\n=== concordancia entre grupos (Spearman del exceso EB; solape top-10 / top-20) ===")
for x, y in combinations(res, 2):
    a, b = res[x], res[y]
    c = a.index.intersection(b.index)
    print(f"{x} vs {y}: {stats.spearmanr(a.exceso[c], b.exceso[c]).statistic:.2f}; "
          f"{len(set(a.index[:10]) & set(b.index[:10]))} / {len(set(a.index[:20]) & set(b.index[:20]))}")

# A1: en la salida principal, observados y esperados de bici y de VMP por separado (cada uno con su modelo)
if {"vmp_o_bici", "bici", "vmp"} <= set(res):
    m = res["vmp_o_bici"]
    for gr in ("bici", "vmp"):
        x = res[gr].reindex(m.index)
        for c in ("N", "mu", "p_exceso", "p_umbral", "nivel"):
            m[f"{c}_{gr}"] = x[c]
    # exceso solo de patinete: el conjunto está por encima (quizá o claramente), el VMP también y la bici no
    m["solo_vmp"] = (m.nivel > 0) & (m.nivel_vmp > 0) & (m.p_exceso_bici <= P_QUIZA)
    m.round(4).to_csv(ROOT / "outputs/cribado_eb_vmp_o_bici.csv")
    c = m[m.nivel == 2]
    print(f"\n=== «claramente» en el conjunto: {len(c)}; de ellos, solo de patinete (bici P(θ>1) <= {P_QUIZA}): {int(c.solo_vmp.sum())}")
    for _, r in c.iterrows():
        print(f"  {str(r.contadores)[:50]:50s} N={r.N:.0f}/{r.mu:.1f} bici {r.N_bici:.0f}/{r.mu_bici:.1f} (P {r.p_exceso_bici:.2f}, "
              f"nivel {r.nivel_bici:.0f}) VMP {r.N_vmp:.0f}/{r.mu_vmp:.1f} (P {r.p_exceso_vmp:.2f}, nivel {r.nivel_vmp:.0f})")
    COEF["vmp_o_bici"]["desglose"] = {
        "claro": int(len(c)), "claro_solo_vmp": int(c.solo_vmp.sum()),
        "claro_bici": int((c.nivel_bici == 2).sum()), "claro_vmp": int((c.nivel_vmp == 2).sum()),
        "quiza_solo_vmp": int(m[m.nivel == 1].solo_vmp.sum())}
# A6: ningún siniestro en dos puntos de conteo (con los tres radios y el de 200 m de la sensibilidad)
for r_ in RADIOS + (200,):
    _a = gpd.sjoin_nearest(s[["geometry"]], cont[["sitio", "geometry"]], max_distance=r_, how="inner")
    _a = _a[~_a.index.duplicated()]
    assert _a.index.is_unique and len(_a) == _a.index.nunique()
    print(f"R={r_}: {len(_a)} siniestros en algún punto de conteo, ninguno en dos")
COEF["agrupa"] = {"agrupa": AGRUPA, "misma_via": MISMA_VIA, "pasillo": PASILLO, "via_tol": VIA_TOL,
                  "enlace": [[f"P{i}" for i in g] for g in PARES_ENLACE],
                  "ambos": [f"P{i}" for i in cont[cont.ambos & cont.enlace.duplicated(keep=False)].idpm]}
COEF["criterio"] = {"umbral": UMBRAL, "p_claro": P_CLARO, "p_quiza": P_QUIZA, "radios": list(RADIOS), "radio": RADIO, "n_sim": N_SIM,
                    "nodos": int(len(NODOS)), "nudos": int(len(NUDOS)), "nudos_web": int(len(NUDOS_WEB))}
(ROOT / "outputs/cribado_eb_coef.json").write_text(json.dumps(COEF, ensure_ascii=False, indent=1))
