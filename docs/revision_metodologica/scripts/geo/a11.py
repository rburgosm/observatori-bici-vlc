_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import sys
sys.path.insert(0,_ROOT+'/scripts')
import geocodificar as G
import pandas as pd
from shapely import Point
from pyproj import Transformer
to25=Transformer.from_crs(4326,25830,always_xy=True).transform
c=pd.read_csv('cruces_diag.csv')
s=pd.read_csv(_ROOT+'/data/processed/siniestros_geo.csv')
for u in ['PG ALAMEDA cruce PL ZARAGOZA','AV FERNANDO ABRIL MARTORELL cruce CTRA MALILLA','AV TRES CRUCES cruce C/ TRES FORQUES','AV BLASCO IBAÑEZ cruce C/ JOSÉ MARIA HARO (MAGISTRAT)','AV DOCTOR TOMAS SALA cruce C/ SAN VICENTE MARTIR','AV PERIS Y VALERO cruce AV REGNE DE VALENCIA','AV HERMANOS MACHADO cruce C/ SANTO DOMINGO SAVIO']:
    a,b=u.split(' cruce ')
    A,B=G.codvias(a),G.codvias(b)
    ca,cb=next(iter(A)),next(iter(B))
    ga,gb=G.geom[ca],G.geom[cb]
    near=ga.buffer(40).intersection(gb)
    comps=list(getattr(near,'geoms',[near]))
    r=s[s.ubicacion==u].iloc[0]; p=Point(to25(r.lon,r.lat))
    cents=[(round(g.centroid.x),round(g.centroid.y),round(g.length)) for g in comps]
    dists=[round(p.distance(g)) for g in comps]
    inter=ga.intersection(gb)
    ni=len(getattr(inter,'geoms',[inter])) if not inter.is_empty else 0
    print(u[:60], '| n casos', (s.ubicacion==u).sum(),'| intersecciones', ni, '| dist del punto a cada zona', dists, '| max sep zonas', round(max(g1.distance(g2) for g1 in comps for g2 in comps)))
