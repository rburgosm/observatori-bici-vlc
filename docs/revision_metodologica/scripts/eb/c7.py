exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
g = pd.read_pickle("g100.pkl"); p = pd.read_pickle("panel100.pkl")
g["lexc"]=np.log((g.N+.5)/(g.mu+.5))
ev = s[s.vmp|s.bici]
a = gpd.sjoin_nearest(ev[["vmp","geometry"]], sitios[["geometry"]], max_distance=100, how="inner")
g["sh_vmp"]=a.groupby("sitio").vmp.mean(); g["n"]=a.groupby("sitio").size()
x=g[g.n>=8]; r=stats.spearmanr(x.sh_vmp,x.lexc)
print(f"cuota VMP de los siniestros del sitio vs log(N/μ) (vmp_o_bici), sitios n>=8 ({len(x)}): Spearman {r.statistic:.2f} p={r.pvalue:.2g}")
print("cuota VMP: P>.95", round(a[a.sitio.isin(g.index[g.p_exceso>.95])].vmp.mean(),3), "resto", round(a[~a.sitio.isin(g.index[g.p_exceso>.95])].vmp.mean(),3))
# separados: excess bici-only y vmp-only models
res={}
for gr in ["bici","vmp"]:
    pp,_,_=panel(100,gr); m=ajustar(pp); gg=eb(pp,m,AÑOS); res[gr]=np.log((gg.N+.5)/(gg.mu+.5))
    print(gr, "elasticidad", round(m.params.l_bici,2), "alpha", round(m.params.alpha,2), "P>.95", (gg.p_exceso>.95).sum())
c=res["bici"].index.intersection(res["vmp"].index)
print("Spearman exceso bici vs exceso VMP por sitio:", round(stats.spearmanr(res["bici"][c],res["vmp"][c]).statistic,2))
# ¿el nivel de VMP (excess vmp) se explica con IMD bici peor que el de bici? -> pseudo R2
for gr in ["bici","vmp"]:
    pp,_,_=panel(100,gr); m=ajustar(pp); m0=smf.negativebinomial("N ~ C(año)", pp).fit(disp=0)
    print(gr, "alpha sin covariables", round(m0.params.alpha,2), "con IMD:", round(m.params.alpha,2), "-> % de heterogeneidad explicada", round(100*(1-m.params.alpha/m0.params.alpha)))
