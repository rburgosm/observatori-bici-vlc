import sys; sys.path.insert(0,".")
from base import *
s,gg,COB=cargar()
gg["c"]=celdas(gg); t,g=top30(gg,gg.c.tolist()); top=t.index[:30]
r=[]
for c in top:
    sub=g[g.c==c]; r.append(((sub.metodo=="cruce").mean(),(sub.P=="B").sum()/max((sub.P=="A").sum(),1), sub.ubicacion.mode().iat[0][:30]))
d=pd.DataFrame(r,columns=["cruce","BA","nom"])
print("B/A en lugares con cruce>=.8:",round(d[d.cruce>=.8].BA.median(),2),"n",(d.cruce>=.8).sum(),"; cruce<.5:",round(d[d.cruce<.5].BA.median(),2),"n",(d.cruce<.5).sum())
print(d[d.cruce<.5].to_string())
# city geocoded counts by year by metodo
print(pd.crosstab(gg.año,gg.metodo))
# distances between adjacent top cells' centroids of points
from itertools import combinations
cen={c:(g[g.c==c].x.mean(),g[g.c==c].y.mean()) for c in top}
for a,b in combinations(top,2):
    dd=np.hypot(cen[a][0]-cen[b][0],cen[a][1]-cen[b][1])
    if dd<130: print(round(dd),g[g.c==a].ubicacion.mode().iat[0][:35],"|",g[g.c==b].ubicacion.mode().iat[0][:35])
