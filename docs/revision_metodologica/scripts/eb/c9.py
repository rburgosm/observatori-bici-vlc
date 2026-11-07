exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
w = bici.pivot(index="idpm", columns="año", values="imd").dropna()
print("panel fijo:", len(w), "contadores; índice suma:", (w.sum()/w.sum().iloc[0]*100).round(1).to_dict())
r = np.log(w.div(w[2022],axis=0))
print("índice mediana de razones:", (np.exp(r.median())*100).round(1).to_dict(), "| media geométrica:", (np.exp(r.mean())*100).round(1).to_dict())
print("peso de los 10 mayores en la suma 2022:", round(w[2022].nlargest(10).sum()/w[2022].sum(),2))
# contadores con razón 2025/2022 extrema (cambio de ubicación/avería)
rr = (w[2025]/w[2022]).sort_values(); print("razón 2025/2022: p5", round(rr.quantile(.05),2), "p95", round(rr.quantile(.95),2), "extremos", rr.head(3).round(2).to_dict(), rr.tail(3).round(2).to_dict())
# serie oficial
x = pd.read_excel(ROOT/"data/raw/intensidades/evolucion_imd_mensual_2019-sep2026.xlsx", sheet_name="Carriles Bici Representativos", header=None)
HD = [str(v) for v in x.iloc[0]]; d = x.iloc[1:]
cols = {a:[i for i,hh in enumerate(HD) if hh.startswith(str(a)+"-")] for a in AÑOS}
num = d.apply(pd.to_numeric, errors="coerce")
ann = pd.DataFrame({a: num[cols[a]].where(num[cols[a]]>0).mean(axis=1) for a in AÑOS}).dropna()
print("serie 'Carriles Bici Representativos' (", len(ann), "filas ):", (ann.sum()/ann.sum().iloc[0]*100).round(1).to_dict())
print("descripciones ejemplo:", d.iloc[:4,1].tolist(), "| última fila:", d.iloc[-1,:3].tolist())
