_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import pandas as pd, numpy as np
df=pd.read_csv(_ROOT+'/data/processed/siniestros_geo.csv')
df['fecha']=pd.to_datetime(df.fecha); df['y']=df.fecha.dt.year
df=df[df.y<=2025]
cols=[c for c in df.columns if c not in('id',)]
df=df.drop_duplicates(subset=['fecha','gravedad','tipo','unidades','factores','ubicacion'])
u=df.unidades.fillna('')
df['bici']=u.str.contains('BICICLETA'); df['vmp']=u.str.contains('VMP'); df['bv']=df.bici|df.vmp
g=df.groupby('y')
t=pd.DataFrame({'todos':g.size(),'bv':g.bv.sum(),'bici':g.bici.sum(),'vmp':g.vmp.sum()})
t['bv/todos%']=(100*t.bv/t.todos).round(2); t['no_bv']=t.todos-t.bv
print(t); print('crec 22-25 %', (100*(t.iloc[-1]/t.iloc[0]-1)).round(1).to_dict())
# gravedad
print(pd.crosstab(df.y,df.gravedad))
print('bv:'); print(pd.crosstab(df[df.bv].y,df[df.bv].gravedad))
q=df[df.y.isin([2023,2024])]; q['q']=q.fecha.dt.to_period('Q')
print(pd.crosstab(q.q,q.gravedad)[['CON HERIDOS GRAVES','CON HERIDOS BAJA GRAVEDAD']] if 'CON HERIDOS BAJA GRAVEDAD' in df.gravedad.unique() else pd.crosstab(q.q,q.gravedad))
df.to_pickle('df.pkl')
