_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import pandas as pd, numpy as np, geopandas as gpd
R=_ROOT+"/"
CRS="EPSG:25830"; CORTES=["2022-10-01","2024-07-01"]
def cargar():
    s=pd.read_csv(R+"data/processed/siniestros_geo.csv",parse_dates=["fecha"])
    s=s[s.fecha.dt.year.between(2022,2025)]; s=s.loc[~s.drop(columns="id").duplicated()]
    s["vmp"]=s.unidades.str.contains("VMP",na=False); s["bici"]=s.unidades.str.contains("BICICLETA",na=False)
    s=s[s.vmp|s.bici].copy(); s["año"]=s.fecha.dt.year
    s["per"]=np.select([s.fecha<CORTES[0],s.fecha<CORTES[1]],["P1","P2"],"P3")
    COB=s.groupby("per").lon.apply(lambda x:x.notna().mean())
    g=s[s.lon.notna()].copy()
    gg=gpd.GeoDataFrame(g,geometry=gpd.points_from_xy(g.lon,g.lat),crs=4326).to_crs(CRS)
    gg["x"]=gg.geometry.x; gg["y"]=gg.geometry.y
    gg["w"]=1/gg.per.map(COB); gg["P"]=np.where(gg.año<=2023,"A","B")
    return s,gg,COB
def celdas(gg,tam=100,dx=0,dy=0):
    return list(zip(((gg.x-dx)//tam).astype(int),((gg.y-dy)//tam).astype(int)))
def top30(gg,c,k=30):
    gg=gg.assign(c=c)
    t=gg.groupby(["c","P"]).size().unstack(fill_value=0); t["T"]=t.A+t.B; t["W"]=gg.groupby("c").w.sum()
    return t.sort_values(["W","T"],ascending=False), gg
