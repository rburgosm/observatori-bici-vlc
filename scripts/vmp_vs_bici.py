"""¿Dónde salen los VMP peor parados que las bicis en el mismo sitio?

Cada siniestro con VMP o con bici (no con los dos) es un ensayo: y = 1 si es VMP. Como VMP y bici
comparten la vía, la proporción no necesita exposición y vale para toda la ciudad.

Sitios: los cruces (nombre del cruce) y los tramos del callejero (eje más cercano a <=30 m) para el resto.
Modelo: logístico de efectos aleatorios por sitio (statsmodels BinomialBayesMixedGLM, Bayes variacional):
    logit P(VMP) = año + tipo de sitio + en carril bici (<=15 m) + u_sitio,   u ~ N(0, s²)
u_sitio es el exceso (o defecto) de VMP en el sitio, suavizado hacia 0 cuando hay pocos casos.
Validación: u estimado con los primeros años (2022-23) frente al exceso observado (VMP - esperado) en los últimos
(2024-25), la misma duración; los periodos de scripts/lugares.py (periodos).

Uso: .venv/bin/python -I scripts/vmp_vs_bici.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import statsmodels.formula.api as smf
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))     # -I no añade la carpeta del script
import lugares as LG              # siniestros(): años completos (los 12 meses) y sin duplicados, el mismo filtro de toda la web
RAW = ROOT / "data/raw/siniestros"
CRS = "EPSG:25830"

s, AÑOS = LG.siniestros()                 # años completos, deducidos de los datos (nada escrito a mano)
s["vmp"] = s.unidades.str.contains("VMP", na=False)
s["bici"] = s.unidades.str.contains("BICICLETA", na=False)
s = s[(s.vmp ^ s.bici) & s.lon.notna()].copy()
s["año"] = s.fecha.dt.year
s["y"] = s.vmp.astype(int)
s = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs="EPSG:4326").to_crs(CRS)

# sitios: cruce por nombre; resto, eje del callejero más cercano
ejes = gpd.read_file(RAW / "ejes.geojson").to_crs(CRS)[["nomcalle", "geometry"]]
cruce = s.metodo == "cruce"
near = gpd.sjoin_nearest(s[~cruce][["geometry"]], ejes, max_distance=30, how="left")
near = near[~near.index.duplicated()]
s.loc[cruce, "sitio"] = "X|" + s.loc[cruce, "ubicacion"]
s.loc[~cruce, "sitio"] = ("T|" + near.nomcalle.astype(str) + "#" + near.index_right.astype("Int64").astype(str)).where(near.index_right.notna())
s["tipo_sitio"] = np.where(cruce, "cruce", "tramo")
cb = gpd.read_file(RAW / "carriles_bici.geojson").to_crs(CRS)
s["en_carril"] = (gpd.sjoin_nearest(s[["geometry"]], cb[["geometry"]], distance_col="d").groupby(level=0).d.min() <= 15).astype(int)
s = s[s.sitio.notna()]

print(f"siniestros VMP o bici (no ambos), geocodificados y con sitio: {len(s)} (VMP {s.y.sum()}, bici {len(s) - s.y.sum()})")
n_sit = s.groupby("sitio").size()
print(f"sitios: {len(n_sit)}; con >=3 casos: {(n_sit >= 3).sum()}, >=5: {(n_sit >= 5).sum()}, >=10: {(n_sit >= 10).sum()}")
print("cuota VMP por año:", s.groupby("año").y.mean().round(3).to_dict())

# efectos fijos sin sitio, para referencia
glm = smf.logit("y ~ C(año) + tipo_sitio + en_carril", s).fit(disp=0)
print("\nefectos fijos (logit, sin efecto de sitio):")
print(pd.DataFrame({"OR": np.exp(glm.params), "IC95 inf": np.exp(glm.conf_int()[0]), "IC95 sup": np.exp(glm.conf_int()[1]),
                    "p": glm.pvalues}).round(3).iloc[1:].to_string())


# Lento (fit_vb usa BFGS denso sobre ~5.000 parámetros: unos 18 min con 2 hilos de BLAS). No se paraleliza con el ajuste
# de la validación: probado el 04/11/2026 con 2 procesos de 1 hilo, tarda más (30 min) porque este ajuste depende del BLAS.
def mixto(d):
    m = BinomialBayesMixedGLM.from_formula("y ~ C(año) + tipo_sitio + en_carril", {"sitio": "0 + C(sitio)"}, d)
    r = m.fit_vb()
    nombres = [n.split("[")[1].rstrip("]") for n in m.vc_names]
    u = pd.DataFrame({"u": r.vc_mean, "sd": r.vc_sd}, index=nombres)
    return m, r, u


m, r, u = mixto(s)
sd_sitio = np.exp(r.vcp_mean[0])
print(f"\nmixto: DE del efecto de sitio = {sd_sitio:.2f} en logit "
      f"(un sitio a +1 DE multiplica la odds de VMP por {np.exp(sd_sitio):.2f})")

# significación de la heterogeneidad entre sitios (sitios con >=5 casos). El χ² asintótico no vale aquí: con 5-10 casos por
# sitio casi todas las casillas esperan menos de 5 (04/11/2026). Se usa la misma estadística χ² con su distribución por
# permutación (scipy.stats.permutation_test): se barajan los VMP/bici entre siniestros manteniendo los casos de cada sitio.
g5 = s[s.sitio.isin(n_sit[n_sit >= 5].index)]
_cod = pd.factorize(g5.sitio)[0]; _y = g5.y.to_numpy()
def _chi2(y):
    v = np.bincount(_cod, weights=y, minlength=_cod.max() + 1); n = np.bincount(_cod)
    return stats.chi2_contingency(np.column_stack([n - v, v]), correction=False).statistic
_esp = stats.contingency.expected_freq(pd.crosstab(g5.sitio, g5.y).to_numpy())
perm = stats.permutation_test((_y,), _chi2, permutation_type="pairings", n_resamples=999, alternative="greater",
                              vectorized=False, random_state=2026)
print(f"homogeneidad de la cuota VMP entre {_cod.max() + 1} sitios con >=5 casos: χ²={perm.statistic:.0f}, "
      f"p por permutación={perm.pvalue:.3f} (999 permutaciones; {np.mean(_esp < 5):.0%} de casillas esperan <5, "
      f"por eso no se usa el p asintótico)")

agg = s.assign(p_fijo=glm.predict(s)).groupby("sitio").agg(
    n=("y", "size"), vmp=("y", "sum"), esperado=("p_fijo", "sum"), tipo=("tipo_sitio", "first"),
    lon=("lon", "mean"), lat=("lat", "mean"), calle=("ubicacion", "first"))
agg = agg.join(u)
agg["p_exceso"] = stats.norm.sf(0, loc=agg.u, scale=agg.sd)
agg["OR_sitio"] = np.exp(agg.u)
agg = agg.sort_values("u", ascending=False)
agg.round(4).to_csv(ROOT / "outputs/vmp_vs_bici.csv")
print(f"sitios con P(exceso VMP)>0,95: {(agg.p_exceso > .95).sum()}; >0,90: {(agg.p_exceso > .90).sum()}")
print("\ntop-15 por exceso de VMP (n casos, VMP obs/esperado, OR del sitio, P):")
for k, x in agg.head(15).iterrows():
    print(f"  {x.calle[:58]:58s} {x.tipo:5s} n={x.n:3d} VMP {x.vmp:3d}/{x.esperado:5.1f} OR={x.OR_sitio:4.2f} P={x.p_exceso:.2f}")
print("\ndefecto de VMP (más bici de lo esperado), top-5:")
for k, x in agg.tail(5).iloc[::-1].iterrows():
    print(f"  {x.calle[:58]:58s} {x.tipo:5s} n={x.n:3d} VMP {x.vmp:3d}/{x.esperado:5.1f} OR={x.OR_sitio:4.2f}")

# ---------- validación fuera de muestra ----------
PA, PB = LG.periodos(AÑOS); EA, EB = LG.etq_años(PA), LG.etq_años(PB)
a = s[s.año.isin(PA)]
b = s[s.año.isin(PB)].copy()
_, _, ua = mixto(a)
fb = smf.logit("y ~ C(año) + tipo_sitio + en_carril", b).fit(disp=0)
b["e"] = fb.predict(b)
ob = b.groupby("sitio").agg(n=("y", "size"), exc=("y", "sum"), e=("e", "sum"))
ob["exc"] -= ob.e
v = ua.join(ob, how="inner")
v = v[v.n >= 3]
rho = stats.spearmanr(v.u, v.exc / v.n)
print(f"\nvalidación: {len(v)} sitios con casos en ambos periodos (>=3 en {EB}). "
      f"Spearman u({EA}) vs exceso por caso ({EB}) = {rho.statistic:.2f} (p={rho.pvalue:.2g})")
for q in (20, 50):
    top = v.u.nlargest(q).index
    resto = v.index.difference(top)
    print(f"  top-{q} de {EA}: exceso VMP en {EB} = {v.loc[top, 'exc'].sum():+.1f} en {v.loc[top, 'n'].sum()} casos "
          f"({v.loc[top, 'exc'].sum() / v.loc[top, 'n'].sum():+.3f}/caso) | resto {v.loc[resto, 'exc'].sum() / v.loc[resto, 'n'].sum():+.3f}/caso")

# ---------- ¿mecanismo? tipo de siniestro del último año (fiable solo desde 2025) ----------
TIPO_AÑO = AÑOS[-1]
t = s[(s.año == TIPO_AÑO) & s.tipo.notna()].copy()
t["sitio_top"] = t.sitio.isin(agg[agg.p_exceso > .90].index)
t["caida"] = t.tipo.str.contains("CAÍDA", na=False)
ct = pd.crosstab([t.y.map({1: "VMP", 0: "bici"}), t.sitio_top.map({True: "sitio exceso", False: "resto"})], t.caida)
print(f"\n{TIPO_AÑO}, caídas por grupo (False=otro tipo, True=caída):")
print(ct.to_string())
tv = t[t.y == 1]
f = stats.fisher_exact(pd.crosstab(tv.sitio_top, tv.caida))
print(f"VMP: caídas en sitios de exceso frente al resto, OR={f.statistic:.2f} p={f.pvalue:.2g}")

# ---------- escala mayor: calle (los cruces cuentan para sus dos calles) ----------
# Ojo: a esta escala la cuota VMP mezcla riesgo con composición del tráfico (más VMP circulando).
todos, _ = LG.siniestros()
v_ = todos.unidades.str.contains("VMP", na=False)
b_ = todos.unidades.str.contains("BICICLETA", na=False)
c = todos[v_ ^ b_].assign(y=v_.astype(int))
c["calle"] = c.ubicacion.str.replace(r"\s+\d+.*$", "", regex=True).str.split(" cruce ")
c = c.explode("calle")
print("\nheterogeneidad por calle (χ² de homogeneidad):")
for nmin in (10, 20, 40):
    n = c.groupby("calle").size()
    g = c[c.calle.isin(n[n >= nmin].index)]
    chi = stats.chi2_contingency(pd.crosstab(g.calle, g.y))
    print(f"  calles con >={nmin} casos: {g.calle.nunique()}, χ²={chi.statistic:.0f}, gl={chi.dof}, p={chi.pvalue:.2g}")
n = c.groupby("calle").size()
t = c[c.calle.isin(n[n >= 20].index)].groupby("calle").y.agg(["size", "mean"]).sort_values("mean")
print("calles extremas (>=20 casos, cuota VMP):")
print(pd.concat([t.head(4), t.tail(4)]).round(2).to_string())
