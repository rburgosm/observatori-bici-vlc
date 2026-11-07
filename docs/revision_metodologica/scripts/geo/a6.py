_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import sys, re, collections as C
sys.path.insert(0,_ROOT+'/scripts')
import geocodificar as G
import pandas as pd, numpy as np
from shapely import Point, MultiPoint
from shapely.ops import unary_union
from pyproj import Transformer
to25=Transformer.from_crs(4326,25830,always_xy=True).transform
R=_ROOT+'/'
s=pd.read_csv(R+'data/processed/siniestros_geo.csv'); s['ubicacion']=s.ubicacion.fillna('')
s['bv']=s.unidades.str.contains('VMP|BICICLETA',na=False)
c=s[s.metodo=='cruce'].copy()
print('dist_ejes_m quantiles', c.dist_ejes_m.quantile([.5,.75,.9,.95,.99]).round(1).to_dict(), ' >0:',(c.dist_ejes_m>0).mean().round(3), ' >10:',(c.dist_ejes_m>10).mean().round(3),' >20:',(c.dist_ejes_m>20).mean().round(3))
cache={}
def analyse(u):
    if u in cache: return cache[u]
    a,b=u.split(' cruce ',1)
    best=None
    for ca in G.codvias(a):
        for cb in G.codvias(b):
            ga,gb=G.geom.get(ca),G.geom.get(cb)
            if ga is None or gb is None: continue
            inter=ga.intersection(gb)
            # zones where the two axes are within 40 m: buffer approach
            near=ga.buffer(40).intersection(gb)
            best=(ca,cb,inter,near) if best is None else best
    cache[u]=best; return best
res=[]
for u,lon,lat,d,bv in zip(c.ubicacion,c.lon,c.lat,c.dist_ejes_m,c.bv):
    r=analyse(u)
    if r is None: res.append((np.nan,np.nan,np.nan,bv)); continue
    ca,cb,inter,near=r
    p=Point(to25(lon,lat))
    err=p.distance(inter) if not inter.is_empty else np.nan
    # spread of near-zone: number of distinct components separated > 100 m
    comps=getattr(near,'geoms',[near]) if not near.is_empty else []
    # cluster components by distance
    pts=[g.centroid for g in comps]
    groups=[]
    for q in pts:
        for gr in groups:
            if q.distance(gr)<100: break
        else: groups.append(q)
    ext=near.length
    res.append((err,len(groups),ext,bv))
r=pd.DataFrame(res,columns=['err','nzonas','len_near','bv'])
c=c.reset_index(drop=True).join(r[['err','nzonas','len_near']])
print('true intersection exists:', c.err.notna().mean().round(3))
print('err (m) quantiles where intersect:', c.err.quantile([.5,.9,.95,.99,1]).round(1).to_dict())
print('err>25m:', (c.err>25).sum(), ' err>50:',(c.err>50).sum(), '  bv err>25:',(c[c.bv].err>25).sum())
print('no true intersection (only near):', c.err.isna().sum(), 'bv:', c[c.bv].err.isna().sum())
print('nzonas dist (pairs that are within 40 m in >1 place >100m apart):', c.nzonas.value_counts().sort_index().to_dict())
print('bv nzonas>1:', (c[c.bv].nzonas>1).sum(), 'of', c.bv.sum())
x=c[c.bv&(c.nzonas>1)].ubicacion.value_counts().head(15)
print(x.to_dict())
y=c[c.bv&(c.err>25)].ubicacion.value_counts().head(10); print('err>25',y.to_dict())
c[['id','ubicacion','bv','err','nzonas','len_near','dist_ejes_m']].to_csv('cruces_diag.csv',index=False)
