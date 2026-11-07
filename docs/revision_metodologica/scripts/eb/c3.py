exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
g = pd.read_pickle("g100.pkl")
ev = s[s.vmp|s.bici]
asig = gpd.sjoin_nearest(ev[["año","metodo","ubicacion","geometry"]], sitios[["geometry"]], max_distance=100, how="inner", distance_col="d_sitio")
asig = asig.rename(columns={"index_right":"sitio"})
cb = via  # red ciclista (capa 189, estados válidos)
dcb = gpd.sjoin_nearest(asig[["geometry"]], cb[["geometry"]], distance_col="dcb")
dcb = dcb[~dcb.index.duplicated()].dcb
asig["dcb"]=dcb
print("asignados:", len(asig), "| método:", asig.metodo.value_counts(normalize=True).round(3).to_dict())
print("distancia a red ciclista: <=5 m", round((asig.dcb<=5).mean(),3), "<=15 m", round((asig.dcb<=15).mean(),3), ">30 m", round((asig.dcb>30).mean(),3))
print("distancia al contador: mediana", round(asig.d_sitio.median()), "m; <=25 m", round((asig.d_sitio<=25).mean(),3))
# puntos distintos (posiciones únicas) por sitio
asig["xy"]=list(zip(asig.geometry.x.round(0),asig.geometry.y.round(0)))
pos = asig.groupby("sitio").xy.nunique()
top1 = asig.groupby("sitio").xy.agg(lambda x: x.value_counts().iloc[0]/len(x))
# exceso relativo
g["lexc"]=np.log((g.N+.5)/(g.mu+.5))
g["cruce_sh"]=asig.assign(c=asig.metodo.str.startswith("cruce")).groupby("sitio").c.mean()
g["dcb_far"]=asig.assign(f=asig.dcb>15).groupby("sitio").f.mean()
g["top1"]=top1
# siniestros de todo tipo (sin bici/VMP) a <=100 m: proxy de conflicto general
otros = s[~(s.vmp|s.bici)]
ao = gpd.sjoin_nearest(otros[["geometry"]], sitios[["geometry"]], max_distance=100, how="inner")
g["otros"]=ao.groupby("sitio").size().reindex(g.index).fillna(0)
# cruces distintos (texto 'cruce') en 100 m entre todos los siniestros
allc = s[s.metodo=="cruce"]
ac = gpd.sjoin(allc[["ubicacion","geometry"]], gpd.GeoDataFrame(geometry=sitios.buffer(100), crs=CRS))
g["n_cruces"]=ac.groupby(ac.columns[ac.columns.str.contains("index_right|sitio")][0]).ubicacion.nunique().reindex(g.index).fillna(0)
for v in ["cruce_sh","dcb_far","top1","otros","n_cruces"]:
    x=g[[v,"lexc"]].dropna(); r=stats.spearmanr(x[v],x.lexc)
    print(f"Spearman log(N/μ) vs {v}: {r.statistic:.2f} (p={r.pvalue:.2g}, n={len(x)})")
hi = g[g.p_exceso>.95]
print("sitios P>.95: cuota de siniestros a >15 m de la red ciclista", round(asig[asig.sitio.isin(hi.index)].dcb.gt(15).mean(),3),
      "vs resto", round(asig[~asig.sitio.isin(hi.index)].dcb.gt(15).mean(),3))
print("sitios P>.95: % en un único punto (top1) mediana", round(hi.top1.median(),2), "vs resto", round(g[g.p_exceso<=.95].top1.median(),2))
# modelo NB con otros siniestros como covariable: ¿cuánto baja alpha y cuántos P>.95 quedan?
p = pd.read_pickle("panel100.pkl")
p["l_otros"]=np.log(p.sitio.map(g.otros)+1); p["n_cruces"]=p.sitio.map(g.n_cruces)
for f in [F_BASE, F_BASE+" + l_otros", F_BASE+" + n_cruces"]:
    m=ajustar(p,f); gg=eb(p,m,AÑOS)
    print(f"{f[-22:]:22s} alpha={m.params['alpha']:.3f} b_bici={m.params['l_bici']:.2f} AIC={m.aic:.0f} P>.95={(gg.p_exceso>.95).sum()} solape top10={len(set(gg.exceso.nlargest(10).index)&set(g.exceso.nlargest(10).index))}")
