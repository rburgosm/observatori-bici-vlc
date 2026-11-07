import pandas as pd, numpy as np
pd.set_option('display.width',200)
df=pd.read_pickle('df.pkl'); b=df[df.bv].copy()
b['per']=np.where(b.fecha<'2022-10-01','P1',np.where(b.fecha<'2024-07-01','P2','P3'))
print('metodo por periodo (bv, geocod):'); g=b[b.lon.notna()]
print(pd.crosstab(g.per,g.metodo,normalize='index').round(3))
ub=b.ubicacion.fillna('').str.upper()
ala=ub.str.contains('ALAMEDA')
az=ala & ub.str.contains('ZARAGOZA')
print('ALAMEDA (texto) por año:', b[ala].groupby('y').size().to_dict())
print('ALAMEDA x ZARAGOZA (texto) por año:', b[az].groupby('y').size().to_dict())
print('ALAMEDA metodo por año:'); print(pd.crosstab(b[ala].y,b[ala].metodo))
# cell of Alameda-Zaragoza (100 m UTM) — approximate with lon/lat from relato: -0.36046,39.46828
import pyproj
tr=pyproj.Transformer.from_crs(4326,25830,always_xy=True)
x,y=tr.transform(g.lon.values,g.lat.values); g=g.assign(cx=(np.floor(np.array(x)/100)).astype(int),cy=(np.floor(np.array(y)/100)).astype(int))
x0,y0=tr.transform(-0.36046,39.46828); c0=(int(x0//100),int(y0//100))
cel=g[(g.cx==c0[0])&(g.cy==c0[1])]
print('celda Alameda-Zaragoza por año:',cel.groupby('y').size().to_dict())
print('ubicaciones en la celda por año (top):'); print(pd.crosstab(cel.ubicacion,cel.y).sort_values(2022,ascending=False).head(8))
# neighbours 3x3
nb=g[(abs(g.cx-c0[0])<=1)&(abs(g.cy-c0[1])<=1)]
print('3x3 alrededor por año:',nb.groupby('y').size().to_dict())
g.to_pickle('g.pkl')
