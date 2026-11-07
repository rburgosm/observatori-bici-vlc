import sys; sys.path.insert(0,".")
from base import *
from scipy import stats
s,gg,COB=cargar()
rng=np.random.default_rng(7)
gg["c"]=celdas(gg)
# ---------- 'tres' : top60 in each of three periods, for the top30 by weighted total ----------
tab=gg.groupby(["c","per"]).size().unstack(fill_value=0)
W=gg.groupby("c").w.sum(); T=tab.sum(1)
top30=pd.DataFrame({"W":W,"T":T}).sort_values(["W","T"],ascending=False).index[:30]
def tres(tb,top,keep="first"):
    ok=np.ones(len(top),bool)
    for p in tb.columns:
        v=tb[p]; 
        sel=set(v.nlargest(60,keep=keep).index) if keep!="all" else set(v[v>=v.sort_values(ascending=False).iloc[59]].index)
        ok&=np.array([c in sel for c in top])
    return ok.sum()
print("tres observado:",tres(tab,top30),"con empates:",tres(tab,top30,"all"))
# null 1, persistencia perfecta: tasa constante por celda; el total de la celda se reparte entre periodos con la proporción de la ciudad
share=tab.sum()/tab.sum().sum()
sims=[]
for _ in range(500):
    m=np.array([rng.multinomial(n,share.values) for n in T.values])
    tb=pd.DataFrame(m,index=tab.index,columns=tab.columns)
    sims.append(tres(tb,top30))
print("persistencia perfecta (Poisson): tres medio",np.mean(sims),"IC90",np.percentile(sims,[5,95]))
# ---------- persistencia A->B: replicar + nulo local ----------
gg["P"]=np.where(gg.año<=2023,"A","B")
t=gg.groupby(["c","P"]).size().unstack(fill_value=0); a,b=t.A,t.B
blk=pd.Series([(c[0]//5,c[1]//5) for c in t.index],index=t.index)
print("celdas con casos",len(t),"; bloques 500m",blk.nunique())
for k in (10,20,30,50):
    top=a.sort_values(ascending=False,kind="stable").index[:k]
    obs=b[top].sum()
    nullg=np.array([rng.permutation(b.values)[:k].sum() for _ in range(2000)])
    # local null: permute B within 500 m blocks
    bv=b.copy(); grp=blk.groupby(blk).groups
    pos=np.array([t.index.get_loc(c) for c in top])
    nl=[]
    for _ in range(2000):
        nb=b.values.copy()
        for g,ix in grp.items():
            ii=[t.index.get_loc(c) for c in ix]
            nb[ii]=rng.permutation(nb[ii])
        nl.append(nb[pos].sum())
    nl=np.array(nl)
    print(f"top{k}: N_A={a[top].sum()} N_B={obs} retención={obs/a[top].sum():.2f} (ciudad {b.sum()/a.sum():.2f}); nulo global media {nullg.mean():.0f} p={(nullg>=obs).mean():.3f}; nulo local(500m) media {nl.mean():.1f} p={(nl>=obs).mean():.3f}")
