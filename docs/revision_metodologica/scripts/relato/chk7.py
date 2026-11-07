import pandas as pd, numpy as np
g=pd.read_pickle('g.pkl')
g['per']=np.where(g.fecha<'2022-10-01','P1',np.where(g.fecha<'2024-07-01','P2','P3'))
w={'P1':1/0.738,'P2':1/0.847,'P3':1/0.957}; g['w']=g.per.map(w)
g['c']=list(zip(g.cx,g.cy))
tot=g.groupby('c').w.sum().sort_values(ascending=False); top30=list(tot.index[:30])
top60={p:set(g[g.per==p].groupby('c').size().sort_values(ascending=False).index[:60]) for p in ['P1','P2','P3']}
print('in-sample tres:',sum(all(c in top60[p] for p in top60) for c in top30))
# out of sample: rank with P1+P2 -> in top60 of P3?
ab=g[g.per!='P3'].groupby('c').w.sum().sort_values(ascending=False); t30=list(ab.index[:30])
print('fuera de muestra: top30 P1+P2 en top60 P3:',sum(c in top60['P3'] for c in t30),'/30')
print('in-sample: top30 total en top60 P3:',sum(c in top60['P3'] for c in top30),'/30')
# P3 counts: mean of top30(P1+P2) vs their P1+P2 rate scaled
p3=g[g.per=='P3'].groupby('c').size()
r12=g[g.per!='P3'].groupby('c').size()
m=18/30  # P3 months / P1+P2 months
print('top30(P1P2): suma P1P2',int(r12.reindex(t30).sum()),'esperado P3 si estable',round(r12.reindex(t30).sum()*m*0.957/((9*0.738+21*0.847)/30),1),'observado P3',int(p3.reindex(t30).fillna(0).sum()))
# celdas 'cruce' share in top30 by period
for p in ['P1','P2','P3']:
    s=g[(g.per==p)&(g.c.isin(top30))]; print(p,'cuota cruce en top30',round((s.metodo=='cruce').mean(),2),'ciudad',round((g[g.per==p].metodo=='cruce').mean(),2), 'cuota de siniestros del periodo en top30', round(len(s)/len(g[g.per==p]),3))
