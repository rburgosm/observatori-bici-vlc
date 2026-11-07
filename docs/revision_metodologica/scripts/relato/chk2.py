import pandas as pd
pd.set_option('display.width',200); pd.set_option('display.max_columns',20)
df=pd.read_pickle('df.pkl')
ab={'CON FALLECIDOS':'F','CON HERIDOS GRAVES':'G','CON HERIDOS BAJA GRAVEDAD':'B','CON HERIDOS LEVES':'L','SIN HERIDOS':'S'}
df['gv']=df.gravedad.map(ab)
print(pd.crosstab(df.y,df.gv)); print(pd.crosstab(df[df.bv].y,df[df.bv].gv))
print('bv con heridos (L+B+G+F) por año:', df[df.bv & (df.gv!='S')].groupby('y').size().to_dict())
print('todos con heridos:', df[(df.gv!='S')].groupby('y').size().to_dict())
q=df[df.y>=2023].copy(); q['q']=q.fecha.dt.to_period('Q')
print(pd.crosstab(q.q,q.gv)[['G','B']].T)
# bv share heridos
