"""¿Hay puntos que se repiten? Persistencia de los recuentos VMP+bici en toda la ciudad (sin exposición)."""
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
from scipy import stats
ROOT = Path(__file__).resolve().parents[1]; CRS = "EPSG:25830"
s = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", parse_dates=["fecha"])
s = s[s.fecha.dt.year.between(2022, 2025)]; s = s.loc[~s.drop(columns="id").duplicated()]
s = s[s.unidades.str.contains("VMP|BICICLETA", na=False) & s.lon.notna()].copy()
s["P"] = np.where(s.fecha.dt.year <= 2023, "A", "B")
s = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs="EPSG:4326").to_crs(CRS)
print(f"siniestros VMP o bici geocodificados: {len(s)} (A=22-23: {(s.P=='A').sum()}, B=24-25: {(s.P=='B').sum()})")
# cuadrícula completa del área urbana (incluye celdas con 0) para evitar selección por resultado
x0, y0, x1, y1 = s.total_bounds
rng = np.random.default_rng(1)
for tam in (100, 200):
    s["c"] = list(zip((s.geometry.x // tam).astype(int), (s.geometry.y // tam).astype(int)))
    t = s.groupby(["c", "P"]).size().unstack(fill_value=0)
    # población: celdas con al menos 1 caso en cualquier periodo (las de 0 y 0 no cambian el top)
    a, b = t.get("A", 0), t.get("B", 0)
    rho = stats.spearmanr(a, b)
    nb_ratio = b.mean() / a.mean()
    print(f"\n== celdas de {tam} m: {len(t)} con casos ==  Spearman A-B = {rho.statistic:.2f} (p={rho.pvalue:.1g})")
    for k in (10, 20, 50):
        top = a.sort_values(ascending=False, kind="stable").index[:k]
        obs = b[top].sum(); esp_media = b.mean() * k
        # nulo: si no hubiera sitios peores, B del top seguiría la media (regresión a la media total).
        # permutación: reasignar al azar los recuentos de B entre celdas
        null = np.array([rng.permutation(b.values)[:k].sum() for _ in range(5000)])
        print(f"  top-{k} de A: N_A={a[top].sum()}, N_B={obs} (media celda×k={esp_media:.0f}; "
              f"perm. p={(null >= obs).mean():.4f}); retención N_B/N_A={obs / a[top].sum():.2f} vs total {nb_ratio:.2f}")
    if tam == 100:
        tot = (a + b).sort_values(ascending=False)
        print(f"  concentración: el 1 % de celdas con casos ({int(len(t)*.01)}) reúne el {tot.iloc[:int(len(t)*.01)].sum()/tot.sum():.0%} de los casos; "
              f"el 5 %: {tot.iloc[:int(len(t)*.05)].sum()/tot.sum():.0%}")
        # dispersión: NB intercepto sobre celdas (incl. 0 de un periodo) frente a Poisson
        g = s.groupby("c").size()
        print(f"  casos por celda (4 años): media {g.mean():.1f}, varianza {g.var():.1f}; máx {g.max()}")
        top = tot.index[:10]
        ll = gpd.GeoSeries(gpd.points_from_xy([(c[0]+.5)*tam for c in top], [(c[1]+.5)*tam for c in top]), crs=CRS).to_crs(4326)
        for c, p in zip(top, ll):
            sub = s[s.c == c]
            print(f"   {a.get(c,0):2d}+{b.get(c,0):2d}  {p.y:.5f},{p.x:.5f}  {sub.ubicacion.mode().iat[0][:60]}")
