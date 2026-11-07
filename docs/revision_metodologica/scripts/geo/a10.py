_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import sys, json, re, collections as C
sys.path.insert(0,_ROOT+'/scripts')
import geocodificar as G
import pandas as pd
vias=json.load(open(_ROOT+'/data/raw/siniestros/vias.json'))
baja=set()
for v in vias:
    if v.get('fechabaja'):
        for nom in (v.get('traducnooficial'),v.get('nomoficial')):
            baja.add(G.sin_parentesis(G.norm(nom)).partition(' ')[2]); baja.add(G.norm(nom).partition(' ')[2])
print('vias con baja', sum(1 for v in vias if v.get('fechabaja')), 'ejemplo', [ (v.get('nomoficial'),v.get('fechabaja')) for v in vias if v.get('fechabaja')][:3])
s=pd.read_csv(_ROOT+'/data/processed/siniestros_geo.csv'); s['ubicacion']=s.ubicacion.fillna('')
s['y']=s.fecha.str[:4]
f=s[s.metodo.isin(['cruce_fallo','numero_fallo'])]
names=[]
for u,y in zip(f.ubicacion,f.y):
    parts=u.split(' cruce ') if ' cruce ' in u else [re.sub(r'\s+\d+\s*[A-Z]*$','',u)]
    for p in parts:
        if not G.codvias(p):
            n=G.norm(p).partition(' ')[2]
            names.append((y,n, n in baja or G.sin_parentesis(n) in baja))
d=pd.DataFrame(names,columns=['y','n','baja'])
print(d.groupby('y').baja.agg(['sum','size']).to_string())
print(d.n.value_counts().head(15).to_dict())
