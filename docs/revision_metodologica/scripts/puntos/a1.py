_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import pandas as pd, numpy as np, collections
R=_ROOT+"/"
s=pd.read_csv(R+"data/processed/siniestros_geo.csv",parse_dates=["fecha"])
print(s.columns.tolist()); print(len(s))
s=s[s.fecha.dt.year.between(2022,2025)]
d=s.loc[~s.drop(columns="id").duplicated()]
print("dups", len(s)-len(d))
# units vocabulary
c=collections.Counter(x.strip() for u in d.unidades.dropna() for x in str(u).split(","))
print(c.most_common(40))
bv=d[d.unidades.str.contains("VMP|BICICLETA",na=False)]
print(bv.groupby(bv.fecha.dt.year).size().to_dict())
print(pd.crosstab(bv.fecha.dt.year, bv.metodo))
print(pd.crosstab(bv.metodo, bv.lon.notna()))
# dup groups: what fields duplicated?
dd=s[s.drop(columns="id").duplicated(keep=False)]
print("dup rows sample", dd.head(4)[["id","fecha","ubicacion","unidades"]].to_string())
