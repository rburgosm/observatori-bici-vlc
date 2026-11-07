exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
import statsmodels.api as sm
g = pd.read_pickle("g100.pkl"); p = pd.read_pickle("panel100.pkl")
g["lexc"]=np.log((g.N+.5)/(g.mu+.5))
nb=ajustar(p); b,se=nb.params.l_bici,nb.bse.l_bici; print(f"elasticidad bici {b:.2f} IC95 {b-1.96*se:.2f}-{b+1.96*se:.2f}")
# within-site (efectos fijos de sitio, Poisson, errores cluster)
fe = smf.glm("N ~ l_bici + C(año) + C(sitio)", p, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": p.sitio})
print(f"elasticidad dentro del sitio (Poisson FE, cluster): {fe.params.l_bici:.2f} IC95 {fe.conf_int().loc['l_bici'].round(2).tolist()}")
# fin de semana
ev = s[s.vmp|s.bici]
asig = gpd.sjoin_nearest(ev[["fecha","geometry"]], sitios[["geometry"]], max_distance=100, how="inner")
asig["fs"]=asig.fecha.dt.dayofweek>=5
print("cuota fin de semana: toda la ciudad", round((ev.fecha.dt.dayofweek>=5).mean(),3), "asignados", round(asig.fs.mean(),3))
g["fs"]=asig.groupby("sitio").fs.mean()
x=g[g.N>=5]; r=stats.spearmanr(x.fs,x.lexc); print(f"Spearman log(N/μ) vs cuota fin de semana (sitios N>=5, n={len(x)}): {r.statistic:.2f} p={r.pvalue:.2g}")
# test con sólo laborables en el numerador
asig["año"]=asig.fecha.dt.year
nl = asig[~asig.fs].groupby(["sitio","año"]).size()
pl = p.drop(columns="N").set_index(["sitio","año"]).join(nl.rename("N")).fillna({"N":0}).reset_index()
ml=ajustar(pl); gl=eb(pl,ml,AÑOS)
print(f"solo laborables: alpha={ml.params.alpha:.3f} P>.95={(gl.p_exceso>.95).sum()} solape top10={len(set(gl.exceso.nlargest(10).index)&set(g.exceso.nlargest(10).index))}, P>.95 compartidos {len(set(gl.index[gl.p_exceso>.95])&set(g.index[g.p_exceso>.95]))}")
# solapes entre sitios y vecinos
d = sitios.geometry.apply(lambda q: sitios.distance(q))
d = d.copy(); dv=d.values.copy(); np.fill_diagonal(dv, np.inf); d=pd.DataFrame(dv,index=d.index,columns=d.columns)
print("sitios con otro sitio a <200 m (círculos de 100 m se tocan):", int((d.min()<200).sum()), "de", len(sitios), "| <100 m:", int((d.min()<100).sum()))
# autocorrelación espacial de residuos: pares de vecinos <400 m
pr=[(i,j) for i in d.index for j in d.columns if i<j and d.loc[i,j]<400]
a_=np.array([g.lexc.get(i,np.nan) for i,j in pr]); b_=np.array([g.lexc.get(j,np.nan) for i,j in pr])
r=stats.spearmanr(a_,b_,nan_policy="omit"); print(f"pares de sitios a <400 m: {len(pr)}; Spearman de log(N/μ) entre vecinos {r.statistic:.2f} p={r.pvalue:.2g}")
print("sin tramo aforado a 100 m (IMD vehículos imputada al mínimo):", int(p.drop_duplicates('sitio').sin_veh.sum()), "de", p.sitio.nunique(), "; min imd_veh", tr.imd_veh.min())
print("sitios por nº de años:", p.groupby("sitio").size().value_counts().sort_index().to_dict())
# contadores con IMD sumada de dos sentidos frente a uno: n_cont
print("variación interanual de IMD dentro de contador (mediana |Δlog|):", round(p.sort_values('año').groupby('sitio').l_bici.diff().abs().median(),3))
