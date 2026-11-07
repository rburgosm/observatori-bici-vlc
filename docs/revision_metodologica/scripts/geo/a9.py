_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import sys, re
sys.path.insert(0,_ROOT+'/scripts')
import geocodificar as G
import pandas as pd, numpy as np, geopandas as gpd
R=_ROOT+'/'
s=pd.read_csv(R+'data/processed/siniestros_geo.csv'); s['ubicacion']=s.ubicacion.fillna('')
m=pd.read_csv(R+'outputs/muestra_geocodificacion.csv')
j=m.merge(s[['id','ubicacion','metodo','lon','lat']],on='id',suffixes=('_m',''))
print('muestra: filas',len(m),'coinciden id',len(j),'misma ubic',(j.ubicacion_m==j.ubicacion).sum(),'mismo punto(<1e-5)',((j.lon_m-j.lon).abs()<1e-5).sum(), 'correcto s:',(m['correcto (s/n)']=='s').sum())
print(m.metodo.value_counts().to_dict())
# type-mismatch resolution
def res(c):
    c=G.norm(c); c=G.norm(G.equiv.get(c,c)); t,_,n=c.partition(' ')
    for nn in (n,G.sin_parentesis(n)):
        if G.por_tipo_nombre.get((t,nn)): return 'tipo'
        if G.por_nombre.get(nn): return 'solo_nombre'
    return 'sin'
s['bv']=s.unidades.str.contains('VMP|BICICLETA',na=False)
ok=s[s.lon.notna()]
def kinds(r):
    cs=r.ubicacion.split(' cruce ') if r.metodo=='cruce' else [re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$",r.ubicacion.strip()).group(1)]
    return any(res(c)=='solo_nombre' for c in cs)
ok=ok.assign(sn=[kinds(r) for r in ok.itertuples()])
print('resuelto sin tipo: total',ok.sn.sum(),'bv',ok[ok.bv].sn.sum())
print(ok[ok.sn&ok.bv].ubicacion.str.split(' cruce ').explode().map(lambda c: c if res(c)=='solo_nombre' else None).dropna().value_counts().head(12).to_dict())
# stacking: identical coords
g=ok[ok.bv]; vc=g.groupby(['lon','lat']).size()
print('bv geocoded',len(g),'distinct points',len(vc),'max stack',vc.max(),' share in stacks>=5:', round(vc[vc>=5].sum()/len(g),3))
# portal offset to axis
p=ok[ok.metodo.isin(['portal','portal_cercano'])]
gp=gpd.GeoSeries(gpd.points_from_xy(p.lon,p.lat),crs=4326).to_crs(25830)
cv=[next(iter(G.codvias(re.match(r"^(.*?)\s+(\d+)\s*[A-Z]*$",u.strip()).group(1))),None) for u in p.ubicacion]
d=[pt.distance(G.geom[c]) if c in G.geom else np.nan for pt,c in zip(gp,cv)]
print('portal->eje dist quantiles', pd.Series(d).quantile([.5,.9,.99]).round(1).to_dict())
# grid sensitivity: top-30 100m cells over bv geocoded, offsets
gg=gpd.GeoSeries(gpd.points_from_xy(g.lon,g.lat),crs=4326).to_crs(25830)
X,Y=gg.x.values,gg.y.values
def top(dx,dy,k=30):
    c=pd.Series(list(zip(((X+dx)//100).astype(int),((Y+dy)//100).astype(int))))
    vc=c.value_counts(); return vc.head(k), c
t0,c0=top(0,0)
for dx,dy in [(50,0),(0,50),(50,50)]:
    t1,c1=top(dx,dy)
    # overlap in terms of cases: for each top cell in t0, fraction of its points that are in a top cell of t1
    in0=c0.isin(t0.index); in1=c1.isin(t1.index)
    jac=(in0&in1).sum()/(in0|in1).sum()
    print(f'offset {dx},{dy}: casos en top30 {in0.sum()} vs {in1.sum()}, Jaccard de casos {jac:.2f}; umbral 30º {t0.iloc[-1]} vs {t1.iloc[-1]}')
