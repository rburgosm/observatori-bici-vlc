exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
g = pd.read_pickle("g100.pkl"); p = pd.read_pickle("panel100.pkl")
hi = set(g.index[g.p_exceso>.95])
# robustez a cobertura: solo 2024-25 (cobertura >=91 %)
q = p[p.año>=2024]; m = ajustar(q); gq = eb(q, m, [2024,2025])
print(f"solo 2024-25: P>.95={(gq.p_exceso>.95).sum()}, compartidos con 4 años {len(hi & set(gq.index[gq.p_exceso>.95]))}, solape top10 {len(set(gq.exceso.nlargest(10).index)&set(g.exceso.nlargest(10).index))}")
# cuota de N de 2022 por sitio frente a la media: ¿heterogeneidad del artefacto?
w = p.pivot(index="sitio", columns="año", values="N")
p["mu"]=ajustar(p).predict(p)
wm = p.pivot(index="sitio", columns="año", values="mu")
ratio = (w[2022]/wm[2022]) / ((w[[2024,2025]].sum(1))/(wm[[2024,2025]].sum(1)))
print("N/μ 2022 relativo a 2024-25 (sitios con >=8 casos en 24-25): mediana", round(ratio[(w[[2024,2025]].sum(1)>=8)].median(),2))
# validación: ¿la métrica favorece al EB? objetivos alternativos
rows=[]
for A in combinations(AÑOS,2):
    B=[y for y in AÑOS if y not in A]; pa,pb=p[p.año.isin(A)],p[p.año.isin(B)]
    ga,gb=eb(pa,ajustar(pa),A),eb(pb,ajustar(pb),B); c=ga.index.intersection(gb.index); ga,gb=ga.loc[c],gb.loc[c]
    for k in (10,20):
        for nom,r in {"bruto":ga.N,"EB":ga.exceso,"EB_total":ga.EB,"tasa":ga.tasa_bruta}.items():
            t=r.sort_values(ascending=False,kind="stable").index[:k]
            rows.append((A,k,nom,gb.loc[t,"N"].sum(),(gb.N-gb.mu).loc[t].sum(), (gb.loc[t,"p_exceso"]>.5).mean()))
t=pd.DataFrame(rows,columns=["A","k","m","N_B","exc_B","frac_Bpexc>.5"])
print(t.groupby(["k","m"])[["N_B","exc_B","frac_Bpexc>.5"]].mean().round(2).to_string())
# regresión a la media: los top10 por exceso EB en A, ¿cuánto de su N/μ en A se mantiene en B?
