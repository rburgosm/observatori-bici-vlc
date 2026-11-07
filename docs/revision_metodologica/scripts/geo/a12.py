_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json, pandas as pd
d=pd.DataFrame(json.load(open(_ROOT+'/data/raw/siniestros/siniestros-de-trafico-2022-2025.json')))
d['y']=d.FECHA.str[:4].astype(int); d=d[d.y<=2025]; d=d[~d.drop(columns='_id').duplicated()]
u=d.UNIDADES_IMPLICADAS; bv=d[u.str.contains('VMP|BICICLETA')]
print(pd.crosstab(bv.y,bv['TIPO GRAVEDAD']).to_string())
bv=bv.assign(her=bv['TIPO GRAVEDAD']!='SIN HERIDOS')
print('con heridos por año', bv.groupby('y').her.sum().to_dict(), ' sin', (~bv.her).groupby(bv.y).sum().to_dict())
both=bv[bv.UNIDADES_IMPLICADAS.str.contains('VMP')&bv.UNIDADES_IMPLICADAS.str.contains('BICICLETA')]
print('ambos',both.y.value_counts().sort_index().to_dict())
# solo-unit (single vehicle) bv
single=bv[bv.UNIDADES_IMPLICADAS.isin(['VMP','BICICLETA'])]
print('solo VMP/BICI sin otra unidad', single.y.value_counts().sort_index().to_dict())
# month coverage of bv per year (seasonality/missing months)
print(bv.groupby([bv.y, bv.FECHA.str[5:7]]).size().unstack().to_string())
