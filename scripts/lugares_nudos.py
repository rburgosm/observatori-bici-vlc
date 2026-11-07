"""Lugares con más siniestros de bici o VMP por NUDO de cruce y TRAMO de calle, en lugar de la rejilla de 100 m.

Análisis de los lugares de la web (04/11/2026; revisión metodológica, problemas 5, 9, 10 y 11). Las unidades, la
asignación, el peso y la pista están en scripts/lugares.py (los usa también exportar_web.py); aquí se miden la
estabilidad (variantes de R y F, frente a la rejilla de 100 m desplazada), la persistencia fuera de muestra con sus
nulos y la pista del top 30.

Uso: OMP_NUM_THREADS=2 .venv/bin/python -I scripts/lugares_nudos.py
Salidas: outputs/lugares_nudos.csv (una fila por unidad con algún siniestro) y outputs/lugares_nudos_resumen.json
(estabilidad, persistencia y pista; lo lee exportar_web.py para la web)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
sys.path.insert(0, str(Path(__file__).resolve().parent))      # -I no añade la carpeta del script
import lugares as LG                                            # unidades, asignación, pesos y pista (scripts/lugares.py)

ROOT = LG.ROOT; CRS = LG.CRS
OUT = ROOT / "outputs/lugares_nudos.csv"; OUT_JSON = ROOT / "outputs/lugares_nudos_resumen.json"
R_BASE, F_BASE = LG.R, LG.F         # radio de asignación al nudo y distancia de fusión de semillas (m)
RS, FS = (20, 30, 40), (20, 30, 40)
K = 30; NSIM = 2000; BLOQUE = 500
rng = np.random.default_rng(20261104)

# ---------------- siniestros: mismo filtro que exportar_web.py (scripts/lugares.py) ----------------
todos, AÑOS = LG.siniestros()
s, COBT = LG.bici_vmp(todos)
g = LG.puntos(s)
# periodos de la persistencia (scripts/lugares.py, periodos): A = los primeros años completos, B = los últimos (misma duración);
# segundo corte, el cambio de registro de julio de 2024 (CORTE7). Etiquetas generadas, nada escrito a mano.
PA, PB = LG.periodos(AÑOS); C7 = pd.Timestamp(LG.CORTE7)
EA, EB = LG.etq_años(PA), LG.etq_años(PB)
_mes = lambda f: f"{f:%m/%Y}"
E7 = f"{_mes(pd.Timestamp(AÑOS[0], 1, 1))}-{_mes(C7 - pd.Timedelta(days=1))} → {_mes(C7)}-{_mes(pd.Timestamp(AÑOS[-1], 12, 1))}"
g["A"] = g["año"].isin(PA); g["A7"] = g.fecha < C7
print(f"bici o VMP {len(s)}; con punto {len(g)} ({len(g)/len(s):.1%}); años {AÑOS}")
print("cobertura año × tipo de dirección:", COBT.unstack().round(3).to_dict())

# ---------------- callejero ----------------
CJ = LG.callejero(todos)
print(f"callejero: {len(CJ['ejes'])} ejes; nodos grado>=3 {CJ['n_nodos']}; semillas (con cruces geocodificados) {len(CJ['semillas'])}; "
      f"glorietas/plazas <= {LG.PLAZA_MAX} m: {len(CJ['plazas'])}")
def unidades(R, F): return LG.unidades(CJ, R, F)
def asignar(u, R): return LG.asignar(g, u, R)
def tabla(uid, u): return LG.tabla(g, uid, u, AÑOS)


def top_casos(d, t, k=K):
    top = t.nsmallest(k, "rank").index
    return set(d.index[d.uid.isin(top)]), top


def jac(a, b): return len(a & b) / len(a | b)


def retenidos(d0, top0, casos1):
    """Lugares del top 0 cuya mayoría de siniestros sigue en el top de la otra variante."""
    return int(sum(d0.index[d0.uid == u].isin(list(casos1)).mean() >= 0.5 for u in top0))


# ---------------- configuración base y variantes ----------------
cfg = {}
for R in RS:
    for F in FS:
        if R != R_BASE and F != F_BASE: continue
        u, zona = unidades(R, F); uid = asignar(u, R); t, d = tabla(uid, u)
        cfg[(R, F)] = (u, uid, t, d, zona)
        print(f"R={R} F={F}: nudos {int((u.tipo=='nudo').sum())}, tramos {int((u.tipo=='tramo').sum())}; "
              f"siniestros en nudo {int(d.uid.map(u.tipo).eq('nudo').sum())} de {len(d)}; unidades con casos {int((t.n>0).sum())}")
u, uid, t, d, zona = cfg[(R_BASE, F_BASE)]
casos0, top0 = top_casos(d, t)

# ---------------- rejilla de 100 m (como exportar_web.py: peso por periodo) y sus desplazamientos ----------------
CORTES = ["2022-10-01", "2024-07-01"]
s["per"] = np.select([s.fecha < CORTES[0], s.fecha < CORTES[1]], ["P1", "P2"], "P3")
COBP = s.groupby("per").lon.apply(lambda x: x.notna().mean())
wper = 1 / g.index.map(s["per"]).map(COBP).values
def rejilla(dx=0, dy=0, tam=100):
    c = pd.Series(list(zip(((g.geometry.x - dx) // tam).astype(int), ((g.geometry.y - dy) // tam).astype(int))), index=g.index)
    W = pd.Series(wper, index=g.index).groupby(c).sum(); n = c.value_counts()
    top = pd.DataFrame({"W": W, "n": n}).sort_values(["W", "n"], ascending=False).index[:K]
    dd = pd.DataFrame({"uid": c}); return set(dd.index[dd.uid.isin(top)]), list(top), dd
gcas0, gtop0, gd0 = rejilla()
gj, gr = [], []
for dx in (0, 25, 50, 75):
    for dy in (0, 25, 50, 75):
        if dx == dy == 0: continue
        c1, _, _ = rejilla(dx, dy); gj.append(jac(gcas0, c1)); gr.append(retenidos(gd0, gtop0, c1))
nj, nr = {}, {}
for key, (u1, uid1, t1, d1, _) in cfg.items():
    if key == (R_BASE, F_BASE): continue
    c1, _ = top_casos(d1, t1); nj[key] = jac(casos0, c1); nr[key] = retenidos(d, top0, c1)
print("\n== ESTABILIDAD DEL TOP 30 (Jaccard de siniestros; lugares cuya mayoría sigue en el top) ==")
print(f"rejilla 100 m, 15 desplazamientos de 25-75 m: Jaccard {min(gj):.2f}-{max(gj):.2f} (mediana {np.median(gj):.2f}); "
      f"retenidos {min(gr)}-{max(gr)} de 30 (mediana {np.median(gr):.0f})")
for key in nj: print(f"nudo/tramo R={key[0]} F={key[1]} frente a R={R_BASE} F={F_BASE}: Jaccard {nj[key]:.2f}; retenidos {nr[key]} de 30")
print(f"nudo/tramo frente a la rejilla publicada: Jaccard {jac(casos0, gcas0):.2f}; lugares de la rejilla retenidos {retenidos(gd0, gtop0, casos0)} de 30")

# ---------------- ficha de cada unidad ----------------
# nombre: calles del callejero que se cruzan en el nudo (o la glorieta), o la calle del tramo y las que lo cierran
# (scripts/lugares.py, nombres). Las calles se eligen con las direcciones de TODOS los siniestros de la ciudad que caen
# en la unidad; «dir» es la dirección más repetida de los de bici o VMP (el nombre antiguo; lo usa el anillo del Plan).
gt = LG.puntos(todos); gt["uid"] = LG.asignar(gt, u)
# nombres congelados (data/processed/nombres_lugares.csv): se reutiliza el publicado; los lugares nuevos se añaden
u = u.join(LG.congelar(u, LG.nombres(u, CJ["ejes"], gt), t.index[t.n > 0]))
u["dir"] = d.groupby("uid").ubicacion.agg(lambda x: x.mode().iat[0])
# estabilidad del nombre: el mismo cálculo con solo los siniestros del periodo A y con solo los del B
_top = t.nsmallest(K, "rank").index; _cas = t.index[t.n > 0]
_nA = LG.nombres(u, CJ["ejes"], gt[gt.fecha.dt.year.isin(PA)]).nom; _nB = LG.nombres(u, CJ["ejes"], gt[gt.fecha.dt.year.isin(PB)]).nom
NOM_EST = {"top": int((_nA[_top] == _nB[_top]).sum()), "k": int(len(_top)),
           "casos": int((_nA[_cas] == _nB[_cas]).sum()), "n_casos": int(len(_cas)),
           "top_A": int((_nA[_top] == u.nom[_top]).sum()), "top_B": int((_nB[_top] == u.nom[_top]).sum())}
print(f"\n== NOMBRES: iguales con {EA} y con {EB} en {NOM_EST['top']} de {K} del top y {NOM_EST['casos']} de "
      f"{NOM_EST['n_casos']} lugares con casos; frente al publicado, {NOM_EST['top_A']} y {NOM_EST['top_B']} de {K} ==")
for i in _top[_nA[_top] != _nB[_top]]: print(f"  {u.at[i, 'nom']}: {EA} «{_nA[i]}» · {EB} «{_nB[i]}»")
cen = u.geometry.representative_point(); c4 = gpd.GeoSeries(cen, crs=CRS).to_crs(4326)
u["lon"], u["lat"] = c4.x.round(5), c4.y.round(5)
u["cruce_frac"] = d.groupby("uid").dir.apply(lambda x: (x == "cruce").mean()).round(2)
for y in AÑOS:
    m = d["año"] == y
    t[f"n{y}"] = d[m].groupby("uid").size().reindex(t.index, fill_value=0)
    t[f"w{y}"] = d[m].groupby("uid").w.sum().reindex(t.index, fill_value=0).round(1)
for c in "bpa": t[f"v_{c}"] = d[d.v == c].groupby("uid").size().reindex(t.index, fill_value=0)
for c in "mwds": t[f"k_{c}"] = d[d.k == c].groupby("uid").size().reindex(t.index, fill_value=0)

# ---------------- persistencia fuera de muestra ----------------
blk = pd.Series(list(zip((cen.x // BLOQUE).astype(int), (cen.y // BLOQUE).astype(int))), index=u.index).reindex(t.index)
gcod = pd.factorize(blk)[0]; est = np.argsort(gcod, kind="stable")      # posiciones agrupadas por bloque
def perm_local(b):
    """Permuta los valores dentro de cada bloque de BLOQUE m (vectorizado con lexsort)."""
    bb = np.empty_like(b); bb[est] = b[np.lexsort((rng.random(len(b)), gcod))]; return bb
tipo = u.tipo.reindex(t.index)
print("\n== PERSISTENCIA FUERA DE MUESTRA (ordenar con A, medir en B; todas las unidades del callejero, también con 0) ==")
print(f"unidades {len(t)}; bloques de {BLOQUE} m {len(set(gcod))}")
pers = {}; KS = (10, 30, 50)
for etq, cA, cB, nA, nB in ((f"{EA} → {EB}", "WA", "WB", "nA", "nB"), (E7, "WA7", "WB7", "nA7", "nB7")):
    a, b = t[cA].values, t[cB].values
    orden = np.argsort(-a, kind="stable")
    # persistencia perfecta + Poisson: cada unidad conserva su total; reparto A/B binomial con la proporción de su tipo
    pa = {k: t.loc[tipo == k, nA].sum() / (t.loc[tipo == k, nA].sum() + t.loc[tipo == k, nB].sum()) for k in ("nudo", "tramo")}
    p_u = tipo.map(pa).values; n_u = (t[nA] + t[nB]).values.astype(int)
    # peso medio por siniestro de la unidad en cada periodo, para pasar los recuentos simulados a ponderados
    wa = np.divide(t[cA].values, t[nA].values, out=np.full(len(t), 1.0), where=t[nA].values > 0)
    wb = np.divide(t[cB].values, t[nB].values, out=np.full(len(t), 1.0), where=t[nB].values > 0)
    sim = {k: {"glob": [], "loc": [], "perf": []} for k in KS}
    for _ in range(NSIM):
        bg, bl = rng.permutation(b), perm_local(b)
        sa = rng.binomial(n_u, p_u); sb = n_u - sa
        op = np.argsort(-(sa * wa + rng.random(len(sa)) * 1e-6))
        for k in KS:
            sim[k]["glob"].append(bg[orden[:k]].sum()); sim[k]["loc"].append(bl[orden[:k]].sum())
            sim[k]["perf"].append((sb * wb)[op[:k]].sum())
    for k in KS:
        top = orden[:k]; obs = b[top].sum(); glob, loc, perf = (np.array(sim[k][x]) for x in ("glob", "loc", "perf"))
        ret = obs / a[top].sum()
        ret_tipo = sum((tipo.values[top] == kk).mean() * (t.loc[tipo == kk, cB].sum() / t.loc[tipo == kk, cA].sum()) for kk in ("nudo", "tramo"))
        p = pers[(etq, k)] = dict(obs=obs, A=a[top].sum(), glob=glob.mean(), p_glob=(glob >= obs).mean(), loc=loc.mean(), p_loc=(loc >= obs).mean(),
                                  perf=perf.mean(), perf_lo=np.percentile(perf, 5), perf_hi=np.percentile(perf, 95), ret=ret, ret_tipo=ret_tipo)
        print(f"{etq} top{k}: A={p['A']:.0f} → B={obs:.0f} (ponderados) · nulo global {p['glob']:.0f} (p={p['p_glob']:.4f}) · "
              f"nulo local {BLOQUE} m {p['loc']:.0f} (p={p['p_loc']:.4f}) · persistencia perfecta+Poisson {p['perf']:.0f} "
              f"[IC90 {p['perf_lo']:.0f}-{p['perf_hi']:.0f}] · retención B/A {ret:.2f} frente a {ret_tipo:.2f} de su tipo "
              f"(cociente {ret/ret_tipo:.2f})")
    if cA == "WA":
        t["rankA"] = pd.Series(np.arange(1, len(t) + 1), index=t.index[orden])
        t["rankB"] = t[cB].rank(ascending=False, method="min")
        print(f"de los 30 primeros de {EA}, entre los 30 primeros de {EB}: {int((t.loc[t.rankA <= 30, 'rankB'] <= 30).sum())}")

# ---------------- pista: con quién, frente a la referencia de su tipo, Holm/BH sobre el top 30 ----------------
ref = {k: d[d.uid.map(u.tipo) == k].groupby("k").size().reindex(LG.CATS, fill_value=0) for k in ("nudo", "tramo")}
PIS, T = LG.pistas({i: (t.loc[i, [f"k_{c}" for c in LG.CATS]].set_axis(LG.CATS).to_dict(),
                        (ref[u.at[i, "tipo"]] - t.loc[i, [f"k_{c}" for c in LG.CATS]].values).to_dict()) for i in top0})
print(f"\n== PISTA: {int(T.probada.sum())} pruebas en lugares con >= {LG.MIN_PISTA} casos; familia = {len(T)} ({K} lugares × 4) ==")
print("referencia nudos:", (ref["nudo"] / ref["nudo"].sum()).round(3).to_dict(), "· tramos:", (ref["tramo"] / ref["tramo"].sum()).round(3).to_dict())
for i, grp in T.groupby("lugar"):
    for col in ("holm", "bh"):
        ok = grp[grp[col]]
        t.loc[i, f"pista_{col}"] = (max(ok.c, key=lambda c: t.at[i, f"k_{c}"] / t.at[i, "n"] - ok.set_index("c").p0[c]) if len(ok) else "")
    t.loc[i, "p_min"] = grp.p.min()
for _, r in T[T.bh].iterrows():
    print(f"  {u.at[r.lugar,'nom'][:55]:55s} {r.c}: {r.x}/{r.n} frente a {r.p0:.1%} · p={r.p:.1e} · Holm {'sí' if r.holm else 'no'}")

# ---------------- top 10 nuevo frente al antiguo ----------------
print("\n== TOP 30 NUEVO (R=30, F=30) ==")
for i in t.nsmallest(K, "rank").index:
    r = t.loc[i]
    print(f"{int(r['rank']):2d} {u.at[i,'tipo']:5s} {u.at[i,'nom'][:58]:58s} n={int(r.n):3d} W={r.W:5.1f} "
          f"años {[int(r[f'n{y}']) for y in AÑOS]} pond {[float(r[f'w{y}']) for y in AÑOS]} ext/long={u.at[i,'ext_m'] if u.at[i,'tipo']=='nudo' else u.at[i,'long_m']}")
print("\n== TOP 10 DE LA REJILLA PUBLICADA → unidad nueva que recoge la mayoría de sus siniestros ==")
for j, c in enumerate(gtop0[:10], 1):
    ids = gd0.index[gd0.uid == c]; nu = d.loc[ids, "uid"].mode().iat[0]
    print(f"{j:2d} {g.loc[ids,'ubicacion'].mode().iat[0][:55]:55s} n={len(ids):3d} → puesto {int(t.at[nu,'rank'])} ({u.at[nu,'nom'][:40]}, n={int(t.at[nu,'n'])})")

# grandes nudos
print("\n== NUDOS MÁS EXTENSOS CON CASOS ==", u[u.tipo == "nudo"].groupby("plaza").ext_m.describe()[["count", "50%", "max"]].to_dict("index"),
      "; sin plaza > 100 m:", int(((u.tipo == "nudo") & ~u.plaza.astype(bool) & (u.ext_m > 100)).sum()))
nn = u[(u.tipo == "nudo") & u.index.isin(t.index[t.n >= 10])].sort_values("ext_m", ascending=False).head(8)
for i, r in nn.iterrows(): print(f"  ext {r.ext_m:.0f} m plaza={r.plaza} n={int(t.at[i,'n'])} puesto {int(t.at[i,'rank'])} {r.nom}")
for patron in ("TRES CRUCES", "TRES FORQUES", "ZARAGOZA"):
    m = u.nom_es.fillna("").str.contains(patron) & (t.n.reindex(u.index) >= 5)
    print(f"  «{patron}»:", [(u.at[i, 'nom'][:45], u.at[i, 'tipo'], int(t.at[i, 'n']), int(t.at[i, 'rank'])) for i in u.index[m]][:8])

# ---------------- salida ----------------
o = u.join(t).loc[lambda x: x.n > 0].copy()
o["geom_wkt"] = gpd.GeoSeries(o.geometry, crs=CRS).to_crs(4326).simplify(0.00002).to_wkt()
o["en_top30"] = o["rank"] <= K
col = (["rank", "tipo", "nom", "nom_es", "nom_calc", "nom_es_calc", "nuevo", "dir", "lon", "lat", "ext_m", "long_m", "plaza", "codvia", "cruce_frac", "n", "W"]
       + [f"n{y}" for y in AÑOS] + [f"w{y}" for y in AÑOS] + ["nA", "nB", "WA", "WB", "nA7", "nB7", "WA7", "WB7", "rankA", "rankB"]
       + [f"v_{c}" for c in "bpa"] + [f"k_{c}" for c in "mwds"] + ["p_min", "pista_holm", "pista_bh", "en_top30", "geom_wkt"])
o = o.reindex(columns=col).sort_values("rank")
for c in ("W", "WA", "WB", "WA7", "WB7"): o[c] = o[c].round(2)
o.to_csv(OUT, index_label="uid")
print(f"\nescrito {OUT.relative_to(ROOT)} ({len(o)} unidades con casos)")

# ---------------- resumen para la web (exportar_web.py) ----------------
_r = lambda x: round(float(x), 2)
res = {"R": R_BASE, "F": F_BASE, "pieza": LG.PIEZA, "paralela": LG.PARALELA, "plaza_max": LG.PLAZA_MAX, "k": K, "nsim": NSIM, "bloque": BLOQUE,
       "n_nudos": int((u.tipo == "nudo").sum()), "n_tramos": int((u.tipo == "tramo").sum()), "n_unid": int(len(u)),
       "en_nudo": int(d.uid.map(u.tipo).eq("nudo").sum()), "n_geo": int(len(d)), "n_semillas": int(len(CJ["semillas"])),
       "n_nodos": int(CJ["n_nodos"]), "n_plazas": int(len(CJ["plazas"])),
       "tramo_max": {"n": int(t.loc[u.index[u.tipo == "tramo"], "n"].max()), "rank": int(t.loc[u.index[u.tipo == "tramo"], "rank"].min())},
       "estab": {"rejilla": {"jac": [_r(min(gj)), _r(max(gj)), _r(np.median(gj))], "ret": [int(min(gr)), int(max(gr)), int(np.median(gr))]},
                 "variantes": [{"R": k[0], "F": k[1], "jac": _r(nj[k]), "ret": int(nr[k])} for k in nj],
                 "frente_rejilla": {"jac": _r(jac(casos0, gcas0)), "ret": int(retenidos(gd0, gtop0, casos0))}},
       "per": {"A": PA, "B": PB, "corte7": LG.CORTE7[:7]},      # periodos de la persistencia (años; mes del segundo corte)
       "pers": [{"corte": "AB" if e == f"{EA} → {EB}" else "jul24", "k": k, **{c: (round(float(v), 4) if c.startswith("p_") else _r(v)) for c, v in p.items()}} for (e, k), p in pers.items()],
       "top_ab": int((t.loc[t.rankA <= K, "rankB"] <= K).sum()),
       "pista": {"ref": {k: {c: _r(v) for c, v in (ref[k] / ref[k].sum()).items()} for k in ref},
                 "probadas": int(T.probada.sum()), "familia": int(len(T)), "holm": int(T.holm.sum()), "bh": int(T.bh.sum())},
       "nombres": NOM_EST, "top": [int(i) for i in top0]}
OUT_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(f"escrito {OUT_JSON.relative_to(ROOT)}")
