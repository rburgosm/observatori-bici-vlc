exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
# --- 1. cobertura por año: todos bici/VMP vs geolocalizados vs asignados a sitio
raw = pd.read_csv(ROOT/"data/processed/siniestros_geo.csv", parse_dates=["fecha"])
raw = raw[raw.fecha.dt.year.isin(AÑOS)]; raw = raw.loc[~raw.drop(columns="id").duplicated()]
raw["bv"] = raw.unidades.str.contains("VMP|BICICLETA", na=False); raw["vmp"]=raw.unidades.str.contains("VMP",na=False)
r = raw[raw.bv]; r["año"]=r.fecha.dt.year
cov = r.groupby("año").agg(n=("bv","size"), geo=("lon", lambda x: x.notna().mean()))
ev = s[s.vmp|s.bici]
asig = gpd.sjoin_nearest(ev[["año","vmp","geometry"]], sitios[["geometry"]], max_distance=100, how="inner")
cov["asig"] = asig.groupby("año").size(); cov["asig_vmp"]=asig[asig.vmp].groupby("año").size()
cov["vmp_all"]=r[r.vmp].groupby("año").size(); cov["vmp_geo"]=r[r.vmp & r.lon.notna()].groupby("año").size()
print(cov); print("indice todos vmp", (cov.vmp_all/cov.vmp_all.iloc[0]*100).round(1).tolist(),
 "geo vmp", (cov.vmp_geo/cov.vmp_geo.iloc[0]*100).round(1).tolist(), "asig vmp", (cov.asig_vmp/cov.asig_vmp.iloc[0]*100).round(1).tolist())
# exposición en el panel por año
p = pd.read_pickle("panel100.pkl")
print("panel por año: sitios", p.groupby("año").size().to_dict(), "suma IMD", p.groupby("año").imd_bici.sum().round(-2).to_dict())
# metodo por año (artefacto: cruce vs portal)
print(pd.crosstab(r.año, r.metodo.fillna("NA"), normalize="index").round(3))
# --- 2. índice de año del modelo VMP, con y sin corrección por cobertura (offset log cobertura anual de VMP)
pv,_,_ = panel(100,"vmp")
covv = (cov.vmp_geo/cov.vmp_all)
pv["lcov"] = np.log(pv.año.map(covv))
m0 = smf.negativebinomial(F_BASE, pv).fit(disp=0, maxiter=300)
m1 = smf.glm(F_BASE, pv, family=__import__("statsmodels.api").api.families.NegativeBinomial(alpha=m0.params["alpha"]), offset=pv.lcov).fit()
for nm, m in [("sin corr", m0), ("offset cob", m1)]:
    print(nm, {a: round(100*np.exp(m.params.get(f"C(año)[T.{a}]",0)),1) for a in AÑOS},
          "IC2025", np.exp(m.conf_int().loc["C(año)[T.2025]"]).round(2).tolist())
# panel fijo: solo sitios con 4 años
full = pv.groupby("sitio").año.nunique(); pf = pv[pv.sitio.isin(full[full==4].index)]
m2 = smf.negativebinomial(F_BASE, pf).fit(disp=0, maxiter=300)
print("panel equilibrado", pf.sitio.nunique(), {a: round(100*np.exp(m2.params.get(f"C(año)[T.{a}]",0)),1) for a in AÑOS})
pb,_,_=panel(100,"bici")
covb = r[r.unidades.str.contains("BICICLETA",na=False)].groupby("año").lon.apply(lambda x:x.notna().mean())
mb = smf.glm(F_BASE, pb, family=__import__("statsmodels.api").api.families.NegativeBinomial(alpha=.318), offset=np.log(pb.año.map(covb))).fit()
print("bici offset cob", {a: round(100*np.exp(mb.params.get(f"C(año)[T.{a}]",0)),1) for a in AÑOS})
print("cobertura vmp", covv.round(3).to_dict(), "bici", covb.round(3).to_dict())
