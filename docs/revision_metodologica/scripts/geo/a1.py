_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json, pandas as pd, collections as C
R=_ROOT+'/'
d=pd.DataFrame(json.load(open(R+'data/raw/siniestros/siniestros-de-trafico-2022-2025.json')))
d['FECHA']=pd.to_datetime(d.FECHA); d['y']=d.FECHA.dt.year
print(d.y.value_counts().sort_index().to_dict())
print('id unique', d._id.is_unique, d._id.min(), d._id.max())
u=d.UNIDADES_IMPLICADAS.fillna('')
toks=u.str.split(',').explode().str.strip()
print(toks.value_counts().to_dict())
print('rows with [ :', u.str.contains(r'\[').sum(), u[u.str.contains(r'\[')].head(5).tolist())
print('null unidades', d.UNIDADES_IMPLICADAS.isna().sum(), (u=='').sum())
# variants of bike/vmp tokens
for pat in ['BICI','VMP','PATIN','CICL','MONO','SEGWAY','PERSONAL']:
    print(pat, sorted(set(t for t in toks.unique() if pat in t.upper())))
cols=[c for c in d.columns if c not in ('_id',)]
dup=d.duplicated(subset=cols,keep=False)
print('dup rows all cols (excl id):', dup.sum(), 'extra', d.duplicated(subset=cols).sum())
bv=u.str.contains('VMP')|u.str.contains('BICICLETA')
print('dup among bv extra:', d[bv].duplicated(subset=cols).sum())
print('dup by y among bv', d[bv & d.duplicated(subset=cols)].y.value_counts().sort_index().to_dict())
# near duplicates: same fecha+ubicacion
k=['FECHA','UBICACION']
nd=d.duplicated(subset=k,keep=False)
print('same fecha+ubic rows', nd.sum(), 'extra', d.duplicated(subset=k).sum(), 'of which bv extra', d[bv].duplicated(subset=k).sum())
x=d[bv & d.duplicated(subset=k,keep=False) & ~d.duplicated(subset=cols,keep=False)].sort_values(k)
print(x.head(12).drop(columns=['y']).to_string()[:3000])
# per year counts with/without dedup
s=d[bv]
print('bv per year raw', s.y.value_counts().sort_index().to_dict())
s2=s[~s.duplicated(subset=cols)]
print('bv per year dedup allcols', s2.y.value_counts().sort_index().to_dict())
s3=s[~s.duplicated(subset=k)]
print('bv per year dedup fecha+ubic', s3.y.value_counts().sort_index().to_dict())
# vmp, bici separately
for g,m in [('vmp',u.str.contains('VMP')),('bici',u.str.contains('BICICLETA'))]:
    t=d[m & ~d.duplicated(subset=cols)]
    print(g, t.y.value_counts().sort_index().to_dict())
# dup ids by year whole dataset
print('all dedup allcols per year', d[~d.duplicated(subset=cols)].y.value_counts().sort_index().to_dict())
