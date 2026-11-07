import sys,json; sys.path.insert(0,".")
from base import *
from scipy.stats import binomtest, poisson
from statsmodels.stats.multitest import multipletests
s,gg,COB=cargar()
raw=pd.read_csv(R+"data/processed/siniestros_geo.csv",parse_dates=["fecha"]); raw=raw[raw.fecha.dt.year.between(2022,2025)]
br=raw[raw.unidades.astype(str).str.strip()=="["]; print("unidades rotas por año:",br.groupby(br.fecha.dt.year).size().to_dict(),"tipos:",br.tipo.value_counts().head(5).to_dict())
print("gravedad bici/VMP por año (%):"); print((pd.crosstab(s.año,s.gravedad,normalize="index")*100).round(1).to_string())
# poisson band around senda
senda={2026:1444,2027:1257,2028:1095,2029:953,2030:830}
print("IC95 Poisson en la senda:",{a:(int(poisson.ppf(.025,v)),int(poisson.ppf(.975,v))) for a,v in senda.items()})
# pista recompute
def contrario(u):
    us=[x.strip() for x in str(u).split(",") if x.strip()]
    otros=[x for x in us if x not in ("BICICLETA","VMP","PEATÓN")]
    if otros: return "m"
    if "PEATÓN" in us: return "w"
    if len(us)>=2: return "d"
    return "s"
s["k"]=s.unidades.map(contrario); gg["k"]=gg.unidades.map(contrario)
print("m incluye DESCONOCIDO/OTROS/[:", int(s.unidades.str.contains("DESCONOCIDO|OTROS|\\[",na=False).sum()))
city=s.k.value_counts(normalize=True)
cruce=gg[gg.metodo=="cruce"].k.value_counts(normalize=True)
print("ref ciudad",city.round(3).to_dict(),"ref cruces",cruce.round(3).to_dict())
gg["c"]=celdas(gg)
t,g2=top30(gg,gg.c.tolist()); top=t.index[:30]
rows=[]
for i,c in enumerate(top):
    sub=g2[g2.c==c]; n=len(sub)
    for ref,nm in ((city,"ciudad"),(cruce,"cruces")):
        for cat in "mwds":
            p=binomtest(int((sub.k==cat).sum()),n,ref.get(cat,0),alternative="greater").pvalue
            rows.append((i,sub.ubicacion.mode().iat[0][:35],n,nm,cat,p))
d=pd.DataFrame(rows,columns=["i","nom","n","ref","cat","p"])
for nm in ("ciudad","cruces"):
    x=d[d.ref==nm].copy()
    x["holm_lugar"]=x.groupby("i").p.transform(lambda p: multipletests(p,method="holm")[0])
    x["holm_todo"]=multipletests(x.p,method="holm")[0]
    x["bh_todo"]=multipletests(x.p,method="fdr_bh")[0]
    x=x[x.n>=20]
    print(f"ref {nm}: Holm por lugar",x[x.holm_lugar][["nom","cat"]].values.tolist())
    print(f"   Holm sobre los {len(d[d.ref==nm])} tests:",x[x.holm_todo][["nom","cat"]].values.tolist(), " BH:",x[x.bh_todo][["nom","cat"]].values.tolist())
