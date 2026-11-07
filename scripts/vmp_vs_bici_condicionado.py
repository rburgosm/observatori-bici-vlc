"""Comparaciones VMP frente a bici condicionadas al siniestro (sin exposición).

Unidad: cada siniestro con VMP o con bici (no con los dos; los «ambos» se cuentan aparte).
Todas las comparaciones son del tipo «entre los siniestros de VMP, ¿qué proporción tiene X,
frente a los de bici?». No dicen qué modo tiene más riesgo: eso necesitaría exposición.

1. Tipo de siniestro (solo el último año: el tipo solo es fiable desde 2025): χ², residuos ajustados y OR por tipo
   (Fisher, Holm). Para qué: orientar la prevención (caídas → vehículo y pavimento; frontolaterales
   → prioridad en cruces) según el modo.
2. Lluvia en la hora del siniestro: logística lluvia ~ VMP + año + mes + franja horaria.
   Para qué: decidir si las campañas o avisos por lluvia deben dirigirse sobre todo al VMP.
3. Oscuridad: en la ventana del ocaso (17-20 h), logística oscuro ~ VMP + año + hora.
   Dentro de una misma hora, que sea de noche depende solo de la época del año.
   Para qué: decidir si la iluminación o la visibilidad (luces obligatorias) pesa más en el VMP.
4. Gravedad dentro de cada año (no comparable entre años): Mantel-Haenszel por año.
   Para qué: saber si un siniestro de VMP es más grave que uno de bici, para priorizar.
5. Tendencia de la cuota VMP/(VMP+bici): por año (Wilson) y logística con tendencia mensual.
   Para qué: el indicador de la transición bici → VMP para el seguimiento del Plan.
6. Factores (solo el último año, exploratorio): Fisher por factor, Benjamini-Hochberg.

Uso: .venv/bin/python -I scripts/vmp_vs_bici_condicionado.py
Salida: outputs/vmp_vs_bici_condicionado.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.contingency_tables import StratifiedTable, Table, Table2x2
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

ROOT = Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))     # -I no añade la carpeta del script
import lugares as LG              # siniestros(): años completos (los 12 meses) y sin duplicados, el mismo filtro de toda la web
OUT = ROOT / "outputs/vmp_vs_bici_condicionado.csv"
filas = []


def fila(analisis, comparacion, d, medida, efecto, lo, hi, p, nota=""):
    """d: dict con k/n por grupo (opcional)."""
    filas.append(dict(analisis=analisis, comparacion=comparacion, **d, medida=medida,
                      efecto=efecto, ic95_inf=lo, ic95_sup=hi, p=p, nota=nota))


def kn(df, col):
    g = df.groupby("grupo")[col].agg(["sum", "count"])
    out = {}
    for m in ("VMP", "BICI"):
        k, n = (int(g.loc[m, "sum"]), int(g.loc[m, "count"])) if m in g.index else (0, 0)
        out.update({f"k_{m.lower()}": k, f"n_{m.lower()}": n,
                    f"pct_{m.lower()}": round(100 * k / n, 1) if n else np.nan})
    return out


def or_logit(res, term="vmp"):
    b, (lo, hi) = res.params[term], res.conf_int().loc[term]
    return np.exp(b), np.exp(lo), np.exp(hi), res.pvalues[term]


def pct(k, n):
    lo, hi = proportion_confint(k, n, method="wilson")
    return f"{100*k/n:.1f} % [{100*lo:.1f}-{100*hi:.1f}]"


# ---------------- datos ----------------
s, AÑOS = LG.siniestros()                 # años completos, deducidos de los datos (nada escrito a mano)
TA, A0 = AÑOS[-1], AÑOS[0]                 # TA: año del tipo y los factores (el último; el tipo solo es fiable desde 2025)
v = s.unidades.str.contains("VMP", na=False)
b = s.unidades.str.contains("BICICLETA", na=False)
ambos = s[v & b]
s = s[v ^ b].copy()
s["grupo"] = np.where(v[s.index], "VMP", "BICI")
s["vmp"] = (s.grupo == "VMP").astype(int)
s["año"] = s.fecha.dt.year
s["mes"] = s.fecha.dt.month
s["hora"] = s.fecha.dt.hour
s["franja"] = pd.cut(s.hora, [-1, 6, 9, 13, 16, 19, 23],
                     labels=["0-6", "7-9", "10-13", "14-16", "17-19", "20-23"])
u = s.unidades.str.split(", ")
s["motor"] = u.apply(lambda l: any(x not in ("VMP", "BICICLETA", "PEATÓN") for x in l)).astype(int)
s["peaton"] = u.apply(lambda l: "PEATÓN" in l).astype(int)
medianoche = (s.fecha.dt.hour == 0) & (s.fecha.dt.minute == 0)
print(f"siniestros {AÑOS[0]}-{AÑOS[-1]} sin duplicados: VMP {s.vmp.sum()}, bici {(1-s.vmp).sum()}, "
      f"ambos {len(ambos)} (aparte); hora 00:00 exacta: {medianoche.sum()} (posible hora desconocida)")

# meteo (Open-Meteo, hora local de Madrid; la precipitación horaria es la suma de la hora anterior)
m = json.loads((ROOT / "data/raw/siniestros/meteo_openmeteo_2022_2025.json").read_text())
lluvia_h = pd.Series(m["hourly"]["precipitation"], index=pd.to_datetime(m["hourly"]["time"]))
lluvia_h = lluvia_h[~lluvia_h.index.duplicated()]
ocaso = pd.Series(pd.to_datetime(m["daily"]["sunset"]), index=pd.to_datetime(m["daily"]["time"]))
slot = s.fecha.dt.floor("h") + pd.Timedelta(hours=1)  # el valor de las 09:00 cubre 08:00-09:00
s["mm"] = slot.map(lluvia_h)
s["mm_prev2"] = sum((slot - pd.Timedelta(hours=h)).map(lluvia_h) for h in (0, 1, 2))
s["lluvia"] = (s.mm >= 0.1).astype(int)
s["mojado"] = (s.mm_prev2 >= 0.1).astype(int)  # sensibilidad: lluvia en la hora o las 2 anteriores
s["oscuro"] = (s.fecha > s.fecha.dt.normalize().map(ocaso)).astype(int)
print(f"sin dato meteo: {s.mm.isna().sum()} (el fichero de Open-Meteo tiene que cubrir {A0}-{TA}); siniestros con lluvia en la hora: {s.lluvia.sum()}\n")

# ---------------- 1. tipo de siniestro, último año (TA) ----------------
print("con vehículo a motor: VMP {:.1f} %, bici {:.1f} %; con peatón: VMP {:.1f} %, bici {:.1f} %\n".format(
    *(100 * s.groupby("grupo")[c].mean()[g] for c in ("motor", "peaton") for g in ("VMP", "BICI"))))
print(f"=== 1. TIPO DE SINIESTRO, {TA} (VMP frente a bici) ===")
t = s[s.año == TA].copy()
agrupa = {"ATROPELLO A ANIMAL": "OTRO", "COLISIÓN MÚLTIPLE": "OTRO",
          "CHOQUE CONTRA OBSTÁCULO O ELEMENTO DE LA VÍA": "CHOQUE CONTRA OBSTÁCULO"}
t["tipo2"] = t.tipo.replace(agrupa).fillna("SIN DATO")
ct = pd.crosstab(t.tipo2, t.grupo)[["VMP", "BICI"]]
chi2, p_chi, dof, _ = stats.chi2_contingency(ct)
res_aj = Table(ct).standardized_resids["VMP"]
print(f"n = {ct.values.sum()} (VMP {ct.VMP.sum()}, bici {ct.BICI.sum()}); "
      f"χ² = {chi2:.1f}, gl = {dof}, p = {p_chi:.2g}; V de Cramér = {np.sqrt(chi2/ct.values.sum()):.2f}")
tipos = []
for tipo, r in ct.iterrows():
    a, c = r.VMP, r.BICI
    tb = Table2x2(np.array([[a, ct.VMP.sum() - a], [c, ct.BICI.sum() - c]]))
    p = stats.fisher_exact(tb.table)[1]
    lo, hi = tb.oddsratio_confint()
    tipos.append((tipo, a, c, tb.oddsratio, lo, hi, p, res_aj[tipo]))
padj = multipletests([x[6] for x in tipos], method="holm")[1]
print(f"{'tipo':26s} {'VMP %':>6s} {'bici %':>6s} {'OR':>5s} {'IC95':>11s} {'res.aj':>6s} {'p Holm':>7s}")
for (tipo, a, c, orr, lo, hi, p, ra), pa in sorted(zip(tipos, padj), key=lambda x: -x[0][7]):
    print(f"{tipo[:26]:26s} {100*a/ct.VMP.sum():6.1f} {100*c/ct.BICI.sum():6.1f} {orr:5.2f} "
          f"{lo:5.2f}-{hi:5.2f} {ra:6.1f} {pa:7.2g}")
    fila(f"tipo_{TA}", tipo, dict(k_vmp=a, n_vmp=ct.VMP.sum(), pct_vmp=round(100*a/ct.VMP.sum(), 1),
                                 k_bici=c, n_bici=ct.BICI.sum(), pct_bici=round(100*c/ct.BICI.sum(), 1)),
         "OR (Fisher)", orr, lo, hi, p, f"p_holm={pa:.3g}; residuo_ajustado={ra:.2f}")
fila(f"tipo_{TA}", "global", {}, "chi2", chi2, np.nan, np.nan, p_chi, f"gl={dof}")
print("Nota: el tipo describe el siniestro, no qué hizo cada vehículo; «atropello» con VMP incluye "
      "peatones atropellados por el VMP.\n")

# ---------------- 2. lluvia ----------------
print("=== 2. LLUVIA EN LA HORA DEL SINIESTRO ===")
principales = []  # (nombre, p) para Holm de la familia principal
d = kn(s, "lluvia")
print(f"con lluvia: VMP {pct(d['k_vmp'], d['n_vmp'])}, bici {pct(d['k_bici'], d['n_bici'])}")
for nom, f in [("bruto", "lluvia ~ vmp"),
               ("ajustado", "lluvia ~ vmp + C(año) + C(mes) + C(franja)")]:
    r = smf.logit(f, s).fit(disp=0)
    o, lo, hi, p = or_logit(r)
    print(f"  OR VMP frente a bici ({nom}): {o:.2f} [{lo:.2f}-{hi:.2f}], p = {p:.2g}")
    fila("lluvia", f"P(lluvia | siniestro) VMP/bici, {nom}", d, "OR logit", o, lo, hi, p, f)
principales.append(("lluvia", p))
r = smf.logit("mojado ~ vmp + C(año) + C(mes) + C(franja)", s).fit(disp=0)
o, lo, hi, p = or_logit(r)
print(f"  sensibilidad, lluvia en la hora o las 2 anteriores: OR {o:.2f} [{lo:.2f}-{hi:.2f}], p = {p:.2g}")
fila("lluvia", "sensibilidad: lluvia 3 h", kn(s, "mojado"), "OR logit", o, lo, hi, p)
r = smf.logit("lluvia ~ vmp + C(año) + C(mes) + C(franja)", s[~medianoche]).fit(disp=0)
o, lo, hi, p = or_logit(r)
print(f"  sensibilidad, sin las 00:00 exactas: OR {o:.2f} [{lo:.2f}-{hi:.2f}]")
# caídas con lluvia, último año (TA): ¿la lluvia aumenta más la proporción de caídas en VMP?
t["caida"] = (t.tipo == "CAÍDA").astype(int)
r = smf.logit("caida ~ vmp * lluvia", t).fit(disp=0)
o, lo, hi, p = or_logit(r, "vmp:lluvia")
for g in ("VMP", "BICI"):
    x = t[t.grupo == g]
    print(f"  {TA}, % caídas {g}: con lluvia {pct(x[x.lluvia == 1].caida.sum(), (x.lluvia == 1).sum())}"
          f" (n={int((x.lluvia == 1).sum())}), sin lluvia {pct(x[x.lluvia == 0].caida.sum(), (x.lluvia == 0).sum())}")
print(f"  interacción VMP × lluvia sobre caída ({TA}): OR {o:.2f} [{lo:.2f}-{hi:.2f}], p = {p:.2g}")
fila("lluvia", f"{TA}: interacción VMP×lluvia en P(caída)", {}, "OR interacción", o, lo, hi, p,
     "caida ~ vmp * lluvia")
print("Lectura: OR = (lluvia/seco en VMP) / (lluvia/seco en bici) entre siniestros. Mezcla riesgo y "
      "exposición: si los usuarios de VMP dejan de circular con lluvia más que los de bici, el OR baja "
      "aunque el riesgo por viaje suba.\n")

# ---------------- 3. oscuridad ----------------
print("=== 3. OSCURIDAD (después del ocaso), ventana 17-20 h ===")
w = s[s.hora.between(17, 20)].copy()  # de 21 h en adelante siempre es de noche (separación)
d = kn(w, "oscuro")
print(f"n = {len(w)}; de noche: VMP {pct(d['k_vmp'], d['n_vmp'])}, bici {pct(d['k_bici'], d['n_bici'])}")
for nom, f in [("bruto", "oscuro ~ vmp"), ("ajustado por hora y año", "oscuro ~ vmp + C(hora) + C(año)")]:
    r = smf.logit(f, w).fit(disp=0)
    o, lo, hi, p = or_logit(r)
    print(f"  OR VMP frente a bici ({nom}): {o:.2f} [{lo:.2f}-{hi:.2f}], p = {p:.2g}")
    fila("oscuridad", f"P(noche | siniestro 17-20 h) VMP/bici, {nom}", d, "OR logit", o, lo, hi, p, f)
principales.append(("oscuridad", p))
print("Lectura: dentro de la misma hora, la noche solo cambia con la estación, así que el OR ajustado "
      "también recoge diferencias estacionales de uso (p. ej., más VMP en invierno).\n")

# ---------------- 4. gravedad dentro de cada año ----------------
print("=== 4. GRAVEDAD DENTRO DE CADA AÑO (Mantel-Haenszel) ===")
s["grave"] = s.gravedad.isin(["CON HERIDOS GRAVES", "CON FALLECIDOS"]).astype(int)
s["herido"] = (s.gravedad != "SIN HERIDOS").astype(int)
s["bajagrave_o_mas"] = s.gravedad.isin(["CON HERIDOS BAJA GRAVEDAD", "CON HERIDOS GRAVES",
                                        "CON FALLECIDOS"]).astype(int)
for y, etiqueta in [("herido", "con heridos (cualquiera)"), ("bajagrave_o_mas", "baja gravedad o más"),
                    ("grave", "graves o fallecidos")]:
    tabs, txt = [], []
    for a in AÑOS:
        x = s[s.año == a]
        tab = pd.crosstab(x.vmp, x[y]).reindex(index=[1, 0], columns=[1, 0], fill_value=0).values
        tabs.append(tab)
        txt.append(f"{a}: {100*tab[0,0]/tab[0].sum():.1f}/{100*tab[1,0]/tab[1].sum():.1f}")
    st = StratifiedTable(tabs)
    lo, hi = st.oddsratio_pooled_confint()
    p = st.test_null_odds(correction=True).pvalue
    p_hom = st.test_equal_odds().pvalue
    r = smf.logit(f"{y} ~ vmp + C(año)", s).fit(disp=0)
    o2, lo2, hi2, _ = or_logit(r)
    print(f"{etiqueta}: % VMP/bici por año {'; '.join(txt)}")
    print(f"  OR MH {st.oddsratio_pooled:.2f} [{lo:.2f}-{hi:.2f}], p = {p:.2g}; homogeneidad entre "
          f"años (Breslow-Day) p = {p_hom:.2g}; logística con año: OR {o2:.2f} [{lo2:.2f}-{hi2:.2f}]")
    r3 = smf.logit(f"{y} ~ vmp + C(año) + motor + peaton", s).fit(disp=0)
    o3, lo3, hi3, _ = or_logit(r3)
    r4 = smf.logit(f"{y} ~ vmp + C(tipo)", s[s.año == TA].assign(tipo=lambda x: x.tipo.where(
        x.tipo.isin(["CAÍDA", "COLISIÓN FRONTOLATERAL", "ATROPELLO A PERSONA"]), "RESTO"))).fit(disp=0)
    o4, lo4, hi4, _ = or_logit(r4)
    print(f"  sensibilidad: + vehículo a motor y peatón OR {o3:.2f} [{lo3:.2f}-{hi3:.2f}]; "
          f"{TA} + tipo OR {o4:.2f} [{lo4:.2f}-{hi4:.2f}]")
    fila("gravedad", f"{etiqueta}: + motor y peatón", {}, "OR logit (año, motor, peatón)", o3, lo3, hi3,
         r3.pvalues["vmp"])
    fila("gravedad", f"{etiqueta}: {TA} + tipo", {}, "OR logit (tipo)", o4, lo4, hi4, r4.pvalues["vmp"])
    fila("gravedad", etiqueta, kn(s, y), "OR Mantel-Haenszel (estratos: año)", st.oddsratio_pooled,
         lo, hi, p, f"Breslow-Day p={p_hom:.3g}; por año VMP/bici %: {'; '.join(txt)}")
    principales.append((f"gravedad: {etiqueta}", p))
print("Nota: la gravedad es la del siniestro (incluye peatones atropellados y ocupantes de otros "
      "vehículos), no la del usuario del VMP o la bici.\n")

# ---------------- 5. tendencia de la cuota VMP ----------------
print("=== 5. CUOTA VMP / (VMP + bici) ===")
for a, x in s.groupby("año"):
    k, n = x.vmp.sum(), len(x)
    lo, hi = proportion_confint(k, n, method="wilson")
    print(f"  {a}: {pct(k, n)} (n = {n})")
    fila("cuota_vmp", str(a), {"k_vmp": k, "n_vmp": n}, "proporción (Wilson)", k / n, lo, hi, np.nan)
mens = s.groupby([s.fecha.dt.to_period("M")]).vmp.agg(["sum", "count"]).reset_index()
mens["t"] = np.arange(len(mens)) / 12  # años desde enero del primer año
mens["mes"] = mens.fecha.dt.month
endog = np.column_stack([mens["sum"], mens["count"] - mens["sum"]])
for nom, X in [("tendencia lineal", sm.add_constant(mens[["t"]])),
               ("tendencia + mes", sm.add_constant(pd.get_dummies(mens[["t", "mes"]].astype({"mes": "category"}),
                                                                   drop_first=True).astype(float)))]:
    g = sm.GLM(endog, X, family=sm.families.Binomial()).fit()
    disp = g.pearson_chi2 / g.df_resid
    # cuasi-binomial: escala de Pearson del ajuste binomial (scale="X2" falla con endog de 2 columnas)
    g = sm.GLM(endog, X, family=sm.families.Binomial()).fit(scale=disp)
    o, (lo, hi), p = np.exp(g.params["t"]), np.exp(g.conf_int().loc["t"]), g.pvalues["t"]
    print(f"  {nom}: OR por año {o:.2f} [{lo:.2f}-{hi:.2f}], p = {max(p, 1e-16):.1g} (dispersión {disp:.2f}, cuasi-binomial)")
    fila("cuota_vmp", f"tendencia mensual {LG.etq_años(AÑOS)} ({nom})", {}, "OR por año (cuasi-binomial)", o, lo, hi, p,
         f"dispersión={disp:.2f}")
principales.append(("tendencia cuota", p))
# ¿lineal en logit? frente a año como factor
r1 = smf.logit(f"vmp ~ I(año - {A0})", s).fit(disp=0)
r2 = smf.logit("vmp ~ C(año)", s).fit(disp=0)
lr = 2 * (r2.llf - r1.llf)
print(f"  desviación de la linealidad entre años: LR = {lr:.2f}, gl = {len(AÑOS) - 2}, p = {stats.chi2.sf(lr, len(AÑOS) - 2):.2g}")
e = s[s.año.isin([A0, TA])]
k = e.groupby("año").vmp.agg(["sum", "count"])
print(f"  diferencia {TA} − {A0}: {100*(k.loc[TA,'sum']/k.loc[TA,'count'] - k.loc[A0,'sum']/k.loc[A0,'count']):.1f} puntos")
print("Lectura: la cuota mezcla la transición del parque (más VMP circulando) y el riesgo relativo; "
      "sin aforo VMP/bici no se separan.\n")

# ---------------- 6. factores, último año (TA, exploratorio) ----------------
print(f"=== 6. FACTORES, {TA} (exploratorio; un siniestro puede tener varios) ===")
fx = t.factores.fillna("").str.split(", ")
todos = fx.explode().value_counts()
todos = todos[(todos >= 15) & (todos.index != "")]
res = []
for fac in todos.index:
    t["f"] = fx.apply(lambda l: fac in l).astype(int)
    tb = pd.crosstab(t.vmp, t.f).reindex(index=[1, 0], columns=[1, 0], fill_value=0).values
    t22 = Table2x2(tb)
    lo, hi = t22.oddsratio_confint()
    res.append((fac, tb[0, 0], tb[1, 0], t22.oddsratio, lo, hi, stats.fisher_exact(tb)[1]))
q = multipletests([x[6] for x in res], method="fdr_bh")[1]
nv, nb = t.vmp.sum(), (1 - t.vmp).sum()
print(f"{'factor':36s} {'VMP %':>6s} {'bici %':>6s} {'OR':>5s} {'IC95':>11s} {'q BH':>7s}")
for (fac, a, c, o, lo, hi, p), qq in sorted(zip(res, q), key=lambda x: x[1]):
    print(f"{fac[:36]:36s} {100*a/nv:6.1f} {100*c/nb:6.1f} {o:5.2f} {lo:5.2f}-{hi:5.2f} {qq:7.2g}")
    fila(f"factores_{TA}", fac, dict(k_vmp=a, n_vmp=nv, pct_vmp=round(100*a/nv, 1), k_bici=c, n_bici=nb,
                                    pct_bici=round(100*c/nb, 1)), "OR (Fisher)", o, lo, hi, p, f"q_bh={qq:.3g}")
print()

# ---------------- familia principal: Holm ----------------
print("=== FAMILIA PRINCIPAL (lluvia, oscuridad, 3 gravedades, tendencia): Holm ===")
ph = multipletests([p for _, p in principales], method="holm")[1]
for (nom, p), pa in zip(principales, ph):
    print(f"  {nom:40s} p = {p:.2g}  p Holm = {pa:.2g}")
out = pd.DataFrame(filas)
out.to_csv(OUT, index=False, float_format="%.4g")
print(f"\nambos (VMP y bici en el mismo siniestro), {TA} por tipo: "
      f"{ambos[ambos.fecha.dt.year == TA].tipo.value_counts().head(3).to_dict()}")
print(f"tabla: {OUT.relative_to(ROOT)} ({len(out)} filas)")
