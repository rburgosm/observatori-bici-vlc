exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
from shapely.geometry import Point
g = pd.read_pickle("g100.pkl"); p = pd.read_pickle("panel100.pkl")
ejes = gpd.read_file(RAW/"siniestros/ejes.geojson").to_crs(CRS)
ejes = ejes[ejes.geometry.notna()].explode(ignore_index=True)
ends = pd.concat([ejes.geometry.apply(lambda l: l.coords[0]), ejes.geometry.apply(lambda l: l.coords[-1])])
k = ends.apply(lambda c: (round(c[0]), round(c[1])))
deg = k.value_counts(); nodos = deg[deg>=3].index
nod = gpd.GeoDataFrame(geometry=[Point(x) for x in nodos], crs=CRS)
print("nodos de grado>=3 en el callejero:", len(nod))
for R in (100,):
    j = gpd.sjoin(nod, gpd.GeoDataFrame(geometry=sitios.buffer(R), crs=CRS))
    col=[c for c in j.columns if c not in ("geometry",)][0]
    n = j.groupby(col).size()
    p["n_int"]=p.sitio.map(n).fillna(0); g["n_int"]=n.reindex(g.index).fillna(0)
g["lexc"]=np.log((g.N+.5)/(g.mu+.5))
r=stats.spearmanr(g.n_int,g.lexc); print(f"Spearman log(N/μ) vs nº intersecciones callejero a 100 m: {r.statistic:.2f} p={r.pvalue:.2g}; mediana n_int {g.n_int.median()} rango {g.n_int.min()}-{g.n_int.max()}")
base=ajustar(p)
for f in [F_BASE+" + n_int", F_BASE+" + np.log1p(n_int)", F_BASE+" + n_int + semaforo"]:
    m=ajustar(p,f); gg=eb(p,m,AÑOS); lr=2*(m.llf-base.llf)
    print(f"{f[-28:]:28s} alpha={m.params['alpha']:.3f} b_bici={m.params['l_bici']:.2f} LR={lr:.1f} AIC={m.aic:.0f} P>.95={(gg.p_exceso>.95).sum()} "
          f"solape top10={len(set(gg.exceso.nlargest(10).index)&set(g.exceso.nlargest(10).index))} | P>.95 en ambos={len(set(gg.index[gg.p_exceso>.95])&set(g.index[g.p_exceso>.95]))}")
    print("   coef:", {k_:round(v,3) for k_,v in m.params.items() if "int" in k_ or "sem" in k_})
m=ajustar(p,F_BASE+" + np.log1p(n_int)"); gg=eb(p,m,AÑOS)
# destacados del informe
for nom in ["XÀTIVA","Xàtiva","TIRSO","Tirso","BALACIART","Balaciart"]:
    pass
desc = pd.read_csv(ROOT/"outputs/cribado_eb_vmp_o_bici.csv").set_index("sitio").contadores
for key in ["tiva","Tirso","Balaciart"]:
    ids=[i for i in g.index if key.lower() in str(desc.get(i,"")).lower()]
    for i in ids: print(f"  {key}: sitio {i} N={g.N[i]:.0f} μ={g.mu[i]:.1f} P={g.p_exceso[i]:.3f} n_int={g.n_int[i]:.0f} | con intersecciones: μ={gg.mu[i]:.1f} P={gg.p_exceso[i]:.3f}")
