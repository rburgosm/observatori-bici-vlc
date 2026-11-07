exec(open('base.py').read())
import warnings; warnings.filterwarnings("ignore")
import statsmodels.api as sm
p = pd.read_pickle("panel100.pkl"); nb = ajustar(p); a = nb.params["alpha"]
g = eb(p, nb, AÑOS)
print("P>.95:", (g.p_exceso>.95).sum(), "P .8-.95:", ((g.p_exceso>.8)&(g.p_exceso<=.95)).sum(), "de", len(g))
# alpha a nivel de sitio (suma de años) con mu fijo del modelo sitio-año
nbs = sm.NegativeBinomial(g.N.values, np.ones(len(g)), offset=np.log(g.mu.values)).fit(disp=0)
print("alpha sitio-año", round(a,3), "| alpha en totales de sitio (offset Σμ):", round(nbs.params[-1],3), "intercept", round(nbs.params[0],3))
# Poisson GLMM con efecto aleatorio de sitio (el modelo que el EB multianual supone)
from statsmodels.genmod.bayes_mixed_glm import PoissonBayesMixedGLM
mm = PoissonBayesMixedGLM.from_formula(F_BASE, {"sitio":"0 + C(sitio)"}, p).fit_vb()
print("GLMM Poisson: DE efecto sitio", round(float(np.exp(mm.vcp_mean[0])),3), "-> varianza", round(float(np.exp(2*mm.vcp_mean[0])),3),
      "| l_bici", round(float(mm.fe_mean[list(mm.model.exog_names).index('l_bici')]),3))
# Pearson de las sumas por sitio
print("dispersión Poisson de sumas por sitio (Σ(N-μ)²/μ /n):", round((((g.N-g.mu)**2)/g.mu).sum()/len(g),2))
# correlación intra-sitio de residuos de año a año (si alpha sitio-año fuera puro sitio, los residuos estarían correlados)
p["mu"]=nb.predict(p); p["r"]=(p.N-p.mu)/np.sqrt(p.mu)
w = p.pivot(index="sitio", columns="año", values="r")
cc=[stats.spearmanr(w[x],w[y],nan_policy="omit").statistic for x,y in combinations(AÑOS,2)]
print("Spearman residuos entre años (media de 6 pares):", round(np.mean(cc),2), np.round(cc,2))
# Recalcular P(exceso) con alpha de nivel sitio
a2 = nbs.params[-1]
p2 = stats.gamma.sf(1, a=1/a2+g.N, scale=1/(1/a2+g.mu))
print("con alpha de sitio: P>.95", (p2>.95).sum(), "P .8-.95", ((p2>.8)&(p2<=.95)).sum())
# esperado bajo el propio modelo: simular theta~gamma(1/a,a), N~Poisson(theta*Σμ) y contar P>.95
rng=np.random.default_rng(1); cnt=[]; tru=[]
for _ in range(500):
    th=rng.gamma(1/a, a, len(g)); n=rng.poisson(th*g.mu.values)
    pp=stats.gamma.sf(1,a=1/a+n,scale=1/(1/a+g.mu.values)); cnt.append((pp>.95).sum()); tru.append(((pp>.95)&(th>1)).mean()/max((pp>.95).mean(),1e-9))
print("bajo el modelo (sin ningún 'punto negro' especial): nº esperado de P>.95 =", np.mean(cnt), "| P(theta>1) a priori =", round(stats.gamma.sf(1,1/a,scale=a),2))
# Banda Poisson frente a clasificación
lo=stats.poisson.ppf(.025,g.mu); hi=stats.poisson.ppf(.975,g.mu)
print("sobre banda Poisson:", (g.N>hi).sum(), "| P>.95:", (g.p_exceso>.95).sum(), "| sobre banda y P<=.95:", ((g.N>hi)&(g.p_exceso<=.95)).sum(),
      "| P>.95 y dentro banda:", ((g.N<=hi)&(g.p_exceso>.95)).sum(), "| bajo banda:", (g.N<lo).sum())
nbhi = stats.nbinom.ppf(.975, 1/a, 1/(1+a*g.mu))
print("sobre banda NB(α sitio-año, Σμ):", (g.N>nbhi).sum())
print("N por sitio: mediana", g.N.median(), "p25", g.N.quantile(.25), "p75", g.N.quantile(.75), "ceros", (g.N==0).sum(), "| μ mediana", round(g.mu.median(),2))
g.to_pickle("g100.pkl")
