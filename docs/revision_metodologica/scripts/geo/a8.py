_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import sys
sys.path.insert(0,_ROOT+'/scripts')
import geocodificar as G
import pandas as pd, numpy as np
R=_ROOT+'/'
s=pd.read_csv(R+'data/processed/siniestros_geo.csv'); s['ubicacion']=s.ubicacion.fillna('')
s['y']=s.fecha.str[:4].astype(int)
f=s[s.metodo=='cruce_fallo'].copy()
def why(u):
    a,b=u.split(' cruce ',1); A,B=G.codvias(a),G.codvias(b)
    if not A and not B: return 'ninguna',np.nan
    if not A or not B: return 'una_no_encontrada',np.nan
    L=[G.geom[x].distance(G.geom[y]) for x in A for y in B if x in G.geom and y in G.geom]
    if not L: return 'sin_geom',np.nan
    d=min(L)
    return 'lejos',d
r=f.ubicacion.map(why); f['why']=r.str[0]; f['d']=r.str[1]
print(pd.crosstab(f.y,f.why).to_string())
print('dist quantiles (lejos)', f[f.why=='lejos'].d.quantile([.1,.25,.5,.75,.9]).round(0).to_dict())
print(f[(f.why=='lejos')].groupby('y').d.median().round(0).to_dict())
print('ejemplos lejos <100m', f[(f.why=='lejos')&(f.d<100)].ubicacion.value_counts().head(8).to_dict())
print('una_no_encontrada ejemplos', f[f.why=='una_no_encontrada'].ubicacion.value_counts().head(10).to_dict())
# Blasco/Serreria
for u in ['AV BLASCO IBAÑEZ cruce C/ SERRERIA','AV CATALUÑA cruce AV NARANJOS','C/ SAN PIO X cruce C/ SAN VICENTE MARTIR']:
    print(u, why(u), G.codvias(u.split(' cruce ')[0]), G.codvias(u.split(' cruce ')[1]))
f['bv']=f.unidades.str.contains('VMP|BICICLETA',na=False)
for lo,hi in [(40,80),(80,150),(150,500),(500,1e9)]:
    m=(f.why=='lejos')&(f.d>lo)&(f.d<=hi)
    print(f'fallo d in ({lo},{hi}] total',m.sum(),'bv',(m&f.bv).sum(), 'by year bv', f[m&f.bv].y.value_counts().sort_index().to_dict())
print('bv 40-150 ubic', f[(f.why=='lejos')&(f.d<=150)&f.bv].ubicacion.value_counts().head(10).to_dict())
