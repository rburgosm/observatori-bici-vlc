_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json, pandas as pd
R=_ROOT+'/'
d=pd.DataFrame(json.load(open(R+'data/raw/siniestros/siniestros-de-trafico-2022-2025.json')))
print(d[d.FECHA.str.startswith('2026')][['_id','FECHA','UBICACION','UNIDADES_IMPLICADAS','TIPO GRAVEDAD']].to_string())
b=d[d.UNIDADES_IMPLICADAS.str.strip()=='[']
print(b[['_id','FECHA','TIPO GRAVEDAD','TIPO ACCIDENTE','UBICACION','FACTORES CONCURRENTES']].to_string())
print(d['TIPO GRAVEDAD'].groupby(d.FECHA.str[:4]).value_counts().unstack().to_string())
print(d['TIPO ACCIDENTE'].groupby(d.FECHA.str[:4]).apply(lambda s:(s=='NULL').mean()).to_dict())
print('max fecha by id ordering check', d.sort_values('_id').FECHA.is_monotonic_increasing)
