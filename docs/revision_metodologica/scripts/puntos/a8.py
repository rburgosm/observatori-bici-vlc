import sys; sys.path.insert(0,".")
from base import *
s,gg,COB=cargar(); rng=np.random.default_rng(3)
gg["c"]=celdas(gg)
tab=gg.groupby(["c","per"]).size().unstack(fill_value=0)
w=1/COB
def tres(tb):
    W=(tb*w).sum(axis=1); T=tb.sum(axis=1)
    top=pd.DataFrame({"W":W,"T":T}).sort_values(["W","T"],ascending=False).index[:30]
    ok=np.ones(30,bool)
    for p in tb.columns: ok&=np.isin(np.arange(len(tb))[tb.index.get_indexer(top)], tb.index.get_indexer(tb[p].nlargest(60).index))
    return ok.sum()
print("obs",tres(tab))
sims=[]
for _ in range(300):
    tb=tab.copy()
    for p in tb.columns: tb[p]=rng.permutation(tb[p].values)
    sims.append(tres(tb))
print("sin persistencia (periodos permutados): media",np.mean(sims),"IC90",np.percentile(sims,[5,95]))
