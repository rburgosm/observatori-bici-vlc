_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import pandas as pd, numpy as np, re
R=_ROOT+'/'
s=pd.read_csv(R+'data/processed/siniestros_geo.csv'); s['ubicacion']=s.ubicacion.fillna('')
s['y']=s.fecha.str[:4].astype(int)
s=s[s.y<=2025]
s['bv']=s.unidades.str.contains('VMP|BICICLETA',na=False)
s['ok']=s.lon.notna()
s['calle']=s.ubicacion.str.split(' cruce ').str[0].str.replace(r'\s+\d+\s*[A-Z]*$','',regex=True).str.replace(' S/N','')
b=s[s.bv]
for y in (2022,2025):
    x=b[(b.y==y)&~b.ok]
    print(y,'bv no geo',len(x), x.metodo.value_counts().to_dict())
    print('  top streets:', x.calle.value_counts().head(12).to_dict())
print('ejemplos cruce_fallo 2022:', s[(s.y==2022)&(s.metodo=='cruce_fallo')].ubicacion.sample(12,random_state=1).tolist())
print('ejemplos solo_calle 2022:', s[(s.y==2022)&(s.metodo=='solo_calle')].ubicacion.sample(10,random_state=1).tolist())
# share of geocoded by street (bv) per period for main streets
b=b.assign(P=np.where(b.y<=2023,'A','B'))
t=b.groupby(['calle','P']).ok.agg(['mean','size']).unstack()
t=t[(t['size'].min(axis=1)>=25)]
t['dif']=t[('mean','B')]-t[('mean','A')]
print(t.sort_values('dif',ascending=False).round(2).head(15).to_string())
# concentration of non-geocoded: share of non-geo cases in top 10 streets
x=b[~b.ok]; vc=x.calle.value_counts()
print('non-geo bv:',len(x),' top10 streets share', round(vc.head(10).sum()/len(x),2), ' JARDIN TURIA', int(x.calle.str.contains('JARDÍN DEL TURIA').sum()))
# group difference: bici vs vmp share of jardin del turia
bi=b[b.unidades.str.contains('BICICLETA')]
print('bici in JARDÍN DEL TURIA:', int(bi.calle.str.contains('JARDÍN DEL TURIA').sum()), 'geocoded', int(bi[bi.calle.str.contains('JARDÍN DEL TURIA')].ok.sum()))
