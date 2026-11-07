import sys; sys.path.insert(0,".")
from base import *
s,gg,COB=cargar()
t0,g0=top30(gg,celdas(gg)); top0=t0.index[:30]
ids0=set(g0[g0.c.isin(top0)].id)
cent0=np.array([[ (c[0]+.5)*100,(c[1]+.5)*100] for c in top0])
print("== sensibilidad al origen de la rejilla (100 m) ==")
res=[]
for dx in (0,25,50,75):
    for dy in (0,25,50,75):
        t,g=top30(gg,celdas(gg,100,dx,dy)); top=t.index[:30]
        ids=set(g[g.c.isin(top)].id)
        # lugares originales cuyo siniestros >=50% caen en una celda top del desplazado
        keep=0
        for c in top0:
            ii=g0[g0.c==c].id
            if g[g.id.isin(ii)].c.isin(top).mean()>=.5: keep+=1
        # top1 nombre
        sub=g[g.c==top[0]]
        res.append((dx,dy,keep,round(len(ids&ids0)/len(ids0),2),int(t["T"].iloc[0]),sub.ubicacion.mode().iat[0][:30]))
r=pd.DataFrame(res,columns=["dx","dy","lugares_conservados","frac_siniestros","n_top1","top1"])
print(r.to_string()); print("conservados: min",r.lugares_conservados.min(),"mediana",r.lugares_conservados.median())
# adjacency among top30 original
adj=[(a,b) for i,a in enumerate(top0) for b in top0[i+1:] if max(abs(a[0]-b[0]),abs(a[1]-b[1]))==1]
print("pares de celdas top30 adyacentes:",len(adj))
for a,b in adj: print("  ",g0[g0.c==a].ubicacion.mode().iat[0][:40],"|",g0[g0.c==b].ubicacion.mode().iat[0][:40])
# alternative: cluster at the exact point (intersection) level: count by rounded coordinates
pt=gg.groupby([gg.x.round(0),gg.y.round(0)]).size().sort_values(ascending=False)
print("top puntos exactos (mismo xy):",pt.head(10).tolist())
# share of siniestros sharing exact coordinates with >=5 others
print("frac siniestros en coordenadas repetidas >=5:",round(pt[pt>=5].sum()/len(gg),3))
# 200 m vs 100 m overlap
t2,g2=top30(gg,celdas(gg,200)); top2=t2.index[:30]
keep=sum(g2[g2.id.isin(g0[g0.c==c].id)].c.isin(top2).mean()>=.5 for c in top0)
print("100m top30 que caen en top30 de 200m:",keep)
