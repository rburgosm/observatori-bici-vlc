import sys; sys.path.insert(0,".")
from base import *
s,gg,COB=cargar()
print("COB",COB.round(3).to_dict())
# coverage by period x type of address text
s["tipo_dir"]=np.where(s.ubicacion.str.contains(" cruce ",case=False,na=False),"cruce","otro")
print(pd.crosstab(s.per,s.tipo_dir,values=s.lon.notna(),aggfunc="mean").round(3))
print(pd.crosstab(s.per,s.tipo_dir))
t,g2=top30(gg,celdas(gg))
top=t.head(31)
print("W at 29..32:",t.W.iloc[27:33].round(2).tolist(), "T:",t["T"].iloc[27:33].tolist())
# months per period
for p,x in s.groupby("per").fecha: print(p,x.min().date(),x.max().date())
# TOP60 ties per period
for p in ("P1","P2","P3"):
    v=g2[g2.per==p].groupby("c").size().sort_values(ascending=False)
    th=v.iloc[59]; print(p,"60th count",th,"n cells with that count",(v==th).sum(),"cells above",(v>th).sum())
TOP60={p:set(g2[g2.per==p].groupby("c").size().nlargest(60).index) for p in ("P1","P2","P3")}
TOP60all={p:set(v[v>=v.sort_values(ascending=False).iloc[59]].index) for p,v in ((p,g2[g2.per==p].groupby("c").size()) for p in ("P1","P2","P3"))}
idx=t.index[:30]
tres=sum(all(c in TOP60[p] for p in TOP60) for c in idx)
tres_ties=sum(all(c in TOP60all[p] for p in TOP60all) for c in idx)
print("tres (nlargest keep first):",tres," incluyendo empates:",tres_ties)
# geocoding method composition of top30 vs city
print("cruce share top30", (g2[g2.c.isin(idx)].metodo=="cruce").mean().round(3), "city", (g2.metodo=="cruce").mean().round(3))
# unweighted top30 overlap
t2=g2.groupby("c").size().sort_values(ascending=False)
print("unweighted top30 overlap",len(set(idx)&set(t2.index[:30])), "30th T", t2.iloc[29], "ties at 30th", (t2==t2.iloc[29]).sum(), "above", (t2>t2.iloc[29]).sum())
# share of P1 in top30 vs city
print("P1 share top30",(g2[g2.c.isin(idx)].per=="P1").mean().round(3),"city",(g2.per=="P1").mean().round(3))
