_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import sys, json, re, collections as C
sys.path.insert(0,_ROOT+'/scripts')
import geocodificar as G
import pandas as pd, numpy as np
from shapely.ops import nearest_points
from shapely import Point
from pyproj import Transformer
to25=Transformer.from_crs(4326,25830,always_xy=True).transform
R=_ROOT+'/'
s=pd.read_csv(R+'data/processed/siniestros_geo.csv'); s['ubicacion']=s.ubicacion.fillna('')
s['bv']=s.unidades.str.contains('VMP|BICICLETA',na=False)
# 1) reproducibility: recompute
rec=[G.geocode(u) for u in s.ubicacion]
m2=[r[1] for r in rec]
print('metodo identical:', (s.metodo.values==np.array(m2)).mean())
lon2=np.array([r[0][0] if r[0] else np.nan for r in rec]); 
print('lon diff max', np.nanmax(np.abs(s.lon.values-lon2)))
# 2) ambiguity: number of codvias per street name
uniq=s.ubicacion.unique()
amb=C.Counter(); amb_bv=0
def ncv(c): return len(G.codvias(c))
rows=[]
for u,met,bv in zip(s.ubicacion,s.metodo,s.bv):
    if met=='cruce':
        a,b=u.split(' cruce ',1); na,nb=ncv(a),ncv(b)
        rows.append((met,bv,max(na,nb)>1, G.norm(a)==G.norm(b) or G.codvias(a)==G.codvias(b)))
    elif met in('portal','portal_cercano'):
        m=re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$",u.strip()); rows.append((met,bv,ncv(m.group(1))>1,False))
df=pd.DataFrame(rows,columns=['met','bv','ambig','self'])
print(df.groupby(['met','bv'])[['ambig','self']].mean().round(4).to_string())
print(df.groupby(['met','bv'])[['ambig','self']].sum().to_string())
