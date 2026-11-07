_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json, pandas as pd
R=_ROOT+'/'
d=pd.DataFrame(json.load(open(R+'data/raw/siniestros/siniestros-de-trafico-2022-2025.json')))
d['y']=d.FECHA.str[:4].astype(int); u=d.UNIDADES_IMPLICADAS
v=u.str.contains('VMP'); b=u.str.contains('BICICLETA')
def cnt(m,pat,yrs):
    x=d[m & d.y.isin(yrs)]
    return int(x.UBICACION.str.contains(pat,regex=True).sum())
for yrs in [(2022,2023,2024,2025),(2023,2024,2025),(2025,),(2024,)]:
    print(yrs,'VMP blasco',cnt(v,'BLASCO IBA',yrs),'puerto',cnt(v,r'AV PUERTO',yrs),'alameda',cnt(v,'ALAMEDA',yrs),
     'alameda-zaragoza',cnt(v,'ALAMEDA.*ZARAGOZA|ZARAGOZA.*ALAMEDA',yrs),
     '| BICI blasco',cnt(b,'BLASCO IBA',yrs),'puerto',cnt(b,'AV PUERTO',yrs),'turia',cnt(b,'TURIA',yrs),'jardin',cnt(b,'JARDI',yrs))
print(d[b].UBICACION[d[b].UBICACION.str.contains('TURIA|JARD')].value_counts().head(10).to_dict())
