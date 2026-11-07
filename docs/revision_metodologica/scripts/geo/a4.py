_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import pandas as pd, numpy as np
R=_ROOT+'/'
s=pd.read_csv(R+'data/processed/siniestros_geo.csv')
s['y']=s.fecha.str[:4].astype(int)
s['v']=s.unidades.str.contains('VMP',na=False); s['b']=s.unidades.str.contains('BICICLETA',na=False)
s['g']=np.select([s.v&s.b,s.v,s.b],['ambos','vmp','bici'],'otro')
print(s.metodo.value_counts().to_dict())
ok=s.metodo.isin(['cruce','portal','portal_cercano'])
print('geo rate total',ok.mean().round(4))
print(pd.crosstab(s.y,s.metodo,normalize='index').round(3).to_string())
bv=s[s.v|s.b]
print('bv geo rate', bv.metodo.isin(['cruce','portal','portal_cercano']).mean().round(4))
print(pd.crosstab([bv.y],bv.metodo.isin(['cruce','portal','portal_cercano']),normalize='index').round(3).to_string())
print(pd.crosstab(bv.g,bv.metodo,normalize='index').round(3).to_string())
print(pd.crosstab([bv.y,bv.g],bv.metodo.isin(['cruce','portal','portal_cercano']),normalize='index').round(3).to_string())
# formats of ubicacion per year: 
fmt=np.select([s.ubicacion.str.contains(' cruce '),s.ubicacion.str.match(r'^.*\s\d+\s*[A-Z]*$')],['cruce','num'],'solo')
print(pd.crosstab(s.y,fmt,normalize='index').round(3).to_string())
