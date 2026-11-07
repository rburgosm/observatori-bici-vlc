exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
desc = pd.read_csv(ROOT/"outputs/cribado_eb_vmp_o_bici.csv").set_index("sitio").contadores
ids = {k:[i for i in desc.index if k.lower() in str(desc[i]).lower()] for k in ["tiva","Tirso","Balaciart"]}
print(ids)
for R in (75,100,125,150,200):
    out=[]
    for gr in ["vmp_o_bici","bici","vmp"]:
        if gr!="vmp_o_bici" and R!=100: continue
        p,_,_=panel(R,gr); g=eb(p,ajustar(p),AÑOS)
        out.append(gr+": "+" ".join(f"{k}{i}:N={g.N.get(i,np.nan):.0f}/μ={g.mu.get(i,np.nan):.1f}/P={g.p_exceso.get(i,np.nan):.2f}" for k,v in ids.items() for i in v))
    print(R, " || ".join(out))
