_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json, collections as C, pandas as pd, numpy as np
from pyproj import Transformer
t=Transformer.from_crs(4326,25830,always_xy=True).transform
f=json.load(open(_ROOT+'/data/raw/siniestros/portales.geojson'))['features']
d=C.defaultdict(list)
for x in f:
    p=x['properties']
    if not x.get('geometry') or p.get('numportal') is None: continue
    d[(p['codvia'],p['numportal'])].append(t(*x['geometry']['coordinates'][:2]))
multi={k:v for k,v in d.items() if len(v)>1}
spread={k:max(np.hypot(a[0]-b[0],a[1]-b[1]) for a in v for b in v) for k,v in multi.items()}
sp=pd.Series(spread)
print('claves', len(d), 'con varias geometrías', len(multi), ' >50 m', (sp>50).sum(), ' >200 m', (sp>200).sum())
s=pd.read_csv(_ROOT+'/data/processed/siniestros_geo.csv'); s['ubicacion']=s.ubicacion.fillna('')
import sys, re
sys.path.insert(0,_ROOT+'/scripts'); import geocodificar as G
p=s[s.metodo=='portal']; bv=p.unidades.str.contains('VMP|BICICLETA',na=False)
hit=[];
for u in p.ubicacion:
    m=re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$",u.strip()); cvs=G.codvias(m.group(1)); n=int(m.group(2))
    k=next(((cv,n) for cv in cvs if (cv,n) in G.portal),None)
    hit.append(spread.get(k,0))
hit=pd.Series(hit,index=p.index)
print('siniestros portal con clave ambigua >50 m:', (hit>50).sum(), ' bv:', (hit[bv]>50).sum(), ' >200m:', (hit>200).sum(), 'bv', (hit[bv]>200).sum())
# ambos composition
a=s[s.unidades.str.contains('VMP',na=False)&s.unidades.str.contains('BICICLETA',na=False)]
a=a[a.fecha.str[:4]<'2026']
only=a.unidades.str.split(',').apply(lambda l:set(x.strip() for x in l)<={'VMP','BICICLETA'})
print('ambos',len(a),' solo bici+VMP sin otras unidades', only.sum(), ' con otras', (~only).sum())
