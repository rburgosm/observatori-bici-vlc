exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
ev = s[s.vmp|s.bici]
for R in (100,150,200):
    a = gpd.sjoin_nearest(ev[["año","geometry"]], sitios[["geometry"]], max_distance=R, how="inner")
    print(R, "filas", len(a), "siniestros únicos", a.index.nunique(), "duplicados por empate", len(a)-a.index.nunique())
# siniestros apilados en el mismo punto (cruce): distribución de tamaño de pila entre asignados
a = gpd.sjoin_nearest(ev[["año","metodo","geometry"]], sitios[["geometry"]], max_distance=100, how="inner")
k = a.groupby([a.geometry.x.round(0), a.geometry.y.round(0)]).size()
print("posiciones distintas", len(k), "| siniestros en posiciones con >=5 apilados:", int(k[k>=5].sum()), "de", len(a))
# sensibilidad: pasar de 100 a 120 m (P>.95)
g0 = pd.read_pickle("g100.pkl"); hi=set(g0.index[g0.p_exceso>.95])
for R in (75,125,150,200):
    p,_,_ = panel(R,"vmp_o_bici"); m=ajustar(p); g=eb(p,m,AÑOS); h=set(g.index[g.p_exceso>.95])
    print(f"R={R}: P>.95 {len(h)}, compartidos con R=100 {len(h&hi)}, Jaccard {len(h&hi)/len(h|hi):.2f}")
