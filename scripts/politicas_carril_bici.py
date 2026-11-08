"""¿Qué cambia en las calles que ganan carril bici? Comparativa de diferencias en diferencias (pendiente 127).

Para qué: la portada y el informe prometen mirar las políticas en conjunto, no obra a obra (con ~12 accidentes al año en el
lugar n.º 1, el efecto de una obra no se separa del azar). Quien lo usa: cualquiera que quiera saber si los tramos nuevos de
carril bici van acompañados de menos (o más) accidentes con bici o patinete que calles parecidas que no cambian.

Método (librerías estándar: geopandas, shapely, statsmodels):
- Unidad: tramo del callejero (ejes.geojson), en EPSG:25830.
- Carril bici por año: fotos de OSM a 1 de enero de 2022-2026 (scripts/osm_historico.py). Un tramo «tiene carril bici» en una
  foto si al menos la mitad de su longitud queda a ≤ 25 m de la red ciclista de esa foto (25 m: las pistas de las avenidas
  anchas van lejos del eje). Tratado = sin carril bici en 2022 y con él en una foto posterior y en todas las siguientes.
  La foto del 1 de enero de AAAA refleja lo hecho hasta el año AAAA-1: ese año de cambio se excluye (transición).
- Control: tramos sin carril bici en ninguna foto. Dos variantes: todos, o solo los que están a ≤ 300 m de un tramo tratado
  (mismo barrio). Se excluyen los tramos con carril bici desde 2022 y los que lo pierden.
- Accidentes: siniestros_geo.csv con coordenadas, asignados al tramo más cercano a ≤ 30 m (los de cruce caen en uno de los
  tramos que se cruzan: ruido, no sesgo). Resultado: accidentes con bici o patinete por tramo y año; y, como placebo, los
  accidentes sin bici ni patinete (si también cambian, es que la calle cambió entera: obras, tráfico).
- Modelo: Poisson condicional (statsmodels ConditionalPoisson; el efecto fijo de cada tramo se elimina al condicionar) con
  efectos de año (recogen el cambio de registro de julio de 2024 y la mejora de la geolocalización, comunes a todos) y la
  variable «después». exp(coef) = cambio relativo en los tramos tratados frente a lo esperado sin carril bici.
Límites: la fecha de OSM es la de cuando se dibujó; no hay exposición (un carril nuevo atrae más bicis, así que más accidentes
puede ser más uso); pocos años; efecto medio de todos los tramos, no de cada uno.

Uso: .venv/bin/python -I scripts/politicas_carril_bici.py
Salidas: outputs/politicas_carril_bici.json (resumen) y outputs/politicas_carril_bici_tramos.csv (tramos tratados, para revisar).
"""
import json, os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2"); os.environ.setdefault("OMP_NUM_THREADS", "2")
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import LineString
from statsmodels.discrete.conditional_models import ConditionalPoisson

ROOT = Path(__file__).resolve().parent.parent
FOTOS = list(range(2022, 2027))          # 1 de enero de cada año
AÑOS = list(range(2022, 2026))           # años con accidentes
BUF, UMBRAL, MAXD, LOCAL = 25, 0.5, 30, 300


def red(año):
    j = json.loads((ROOT / f"data/raw/osm/cicl_{año}-01-01.json").read_text())
    e = [x for x in j["elements"] if x.get("geometry")]
    g = gpd.GeoSeries([LineString([(p["lon"], p["lat"]) for p in x["geometry"]]) for x in e], crs=4326).to_crs(25830)
    return g.union_all()


def evento(panel, y):
    """Estudio de eventos: efecto por año relativo a la obra (0 = año de la obra, excluido; referencia = año anterior, -1).
    Los años -3 y -2 comprueban si las calles tratadas ya iban distinto antes de la obra (tendencia previa)."""
    d = panel[panel.grupo.isin(["tratado", "control"])].copy()
    d["rel"] = np.where(d.grupo == "tratado", d["año"] - (d.foto_cb - 1), np.nan)
    d = d[d.groupby("uid")[y].transform("sum") > 0]
    X = pd.get_dummies(d["año"], prefix="a", drop_first=True, dtype=float)
    for r in (-3, -2, 1, 2, 3):
        X[f"rel{r:+d}"] = (d.rel == r).astype(float)
    X = X.loc[:, X.sum() > 0]
    r = ConditionalPoisson(d[y].values, X.values, groups=d.uid.values).fit(disp=0)
    return {c: {"efecto": round(float(np.exp(b)) - 1, 3), "ic95": [round(float(np.exp(b - 1.96 * e)) - 1, 3), round(float(np.exp(b + 1.96 * e)) - 1, 3)],
                "p": round(float(pv), 4), "tramos_tratados": int(d.loc[X[c] == 1, "uid"].nunique())}
            for c, b, e, pv in zip(X.columns, r.params, r.bse, r.pvalues) if c.startswith("rel")}


def imd_anual(path):
    """Media de las IMD mensuales (> 0) por contador en un ODS de Movilidad (mismo criterio que scripts/cribado_eb.py)."""
    partes = []
    for h in pd.read_excel(path, engine="odf", sheet_name=None, header=None).values():
        es_cod = h.apply(lambda c: c.astype(str).str.strip().str.fullmatch(r"P\d+").mean())
        c_cod = es_cod.idxmax()
        filas = h[h[c_cod].astype(str).str.strip().str.fullmatch(r"P\d+")]
        num = filas.drop(columns=c_cod).apply(lambda c: pd.to_numeric(c, errors="coerce").notna().mean())
        partes.append(pd.DataFrame({"cod": filas[c_cod].astype(str).str.strip(), "imd": pd.to_numeric(filas[num[num > .5].index.max()], errors="coerce")}))
    d = pd.concat(partes); d = d[d.imd > 0].groupby("cod").imd.agg(["mean", "size"])
    d = d[d["size"] >= 6]
    return pd.Series(d["mean"].values, index=d.index.str[1:].astype(int))


def contadores(ejes, trat):
    """Contadores del carril bici en tramos tratados (≤ 25 m): ¿había dato antes de la obra?, y cambio de la IMD frente a la
    media de los contadores con dato los cuatro años (índice de la ciudad)."""
    imd = pd.DataFrame({a: imd_anual(ROOT / f"data/raw/intensidades/carril_bici_{a}.ods") for a in AÑOS})
    esp = gpd.read_file(ROOT / "data/raw/siniestros/espiras_bici.geojson").to_crs(25830)
    esp = esp[esp.geometry.notna()].drop_duplicates("idpm")
    esp = esp[esp.idpm.isin(imd.index)]
    j = gpd.sjoin_nearest(esp[["idpm", "geometry"]], ejes[trat][["uid", "foto_cb", "tipnomcalle", "geometry"]], max_distance=BUF, how="inner")
    completos = imd.dropna(); ciudad = completos.mean() / completos.mean()[AÑOS[0]]
    out = []
    for r in j.itertuples():
        f = int(r.foto_cb); serie = imd.loc[r.idpm]
        antes = [a for a in AÑOS if a < f - 1 and pd.notna(serie[a])]; despues = [a for a in AÑOS if a >= f and pd.notna(serie[a])]
        fila = {"idpm": int(r.idpm), "calle": r.tipnomcalle, "obra_hasta": f - 1, "imd": {int(a): (round(float(serie[a])) if pd.notna(serie[a]) else None) for a in AÑOS}}
        if antes and despues:
            rel = (serie[despues].mean() / ciudad[despues].mean()) / (serie[antes].mean() / ciudad[antes].mean())
            fila["cambio_frente_a_ciudad"] = round(float(rel) - 1, 3)
        out.append(fila)
    # casi ningún contador tiene dato de antes de la obra (se instalan con el carril): se compara el crecimiento DESPUÉS
    # (2023 → 2025) de los contadores de tramos con obra hasta 2023 frente al resto (Mann-Whitney, scipy)
    from scipy.stats import mannwhitneyu
    t = {x["idpm"] for x in out if x["obra_hasta"] <= 2023 and x["imd"][2023] and x["imd"][2025]}
    ok = imd.dropna(subset=[2023, 2025]); g = ok[2025] / ok[2023] - 1
    gt, go = g[g.index.isin(t)], g[~g.index.isin(t)]
    crec = {"contadores_tramos_nuevos": len(gt), "mediana_tramos_nuevos": round(float(gt.median()), 3),
            "contadores_resto": len(go), "mediana_resto": round(float(go.median()), 3), "p_mann_whitney": round(float(mannwhitneyu(gt, go).pvalue), 5)}
    return {"en_tramos_tratados": len(out), "con_dato_antes_y_despues": sum("cambio_frente_a_ciudad" in x for x in out),
            "crecimiento_2023_2025": crec, "detalle": out}


def main():
    ejes = gpd.read_file(ROOT / "data/raw/siniestros/ejes.geojson").to_crs(25830)
    ejes = ejes[ejes.length > 10].reset_index(drop=True); ejes["uid"] = ejes.index
    lon = ejes.length
    cb = pd.DataFrame(index=ejes.index)
    redes = {}
    for f in FOTOS:
        redes[f] = red(f)
        zona = gpd.GeoSeries([redes[f].buffer(BUF)], crs=25830)
        cb[f] = ejes.geometry.intersection(zona.iloc[0]).length / lon >= UMBRAL
    nunca = ~cb.any(axis=1)
    siempre = cb[2022]
    # tratado: sin carril en 2022, con él desde una foto y en todas las siguientes
    primera = cb.idxmax(axis=1).where(cb.any(axis=1))
    estable = pd.Series([bool(cb.loc[i, int(p):].all()) if pd.notna(p) else False for i, p in primera.items()], index=cb.index)
    trat = (~siempre) & cb.any(axis=1) & estable
    pierde = cb.any(axis=1) & ~siempre & ~estable
    ejes["grupo"] = np.select([trat, nunca, siempre], ["tratado", "control", "siempre"], "pierde")
    ejes["foto_cb"] = primera.where(trat)
    # control local: a ≤ 300 m de un tramo tratado
    zt = ejes[trat].geometry.buffer(LOCAL).union_all()
    ejes["local"] = nunca & ejes.geometry.intersects(zt)

    # validación: tramos nuevos de OSM (sin carril en 2022) frente a la capa 189 del portal (red actual)
    portal = gpd.read_file(ROOT / "data/raw/siniestros/carriles_bici.geojson").to_crs(25830)
    portal = portal[portal.estado != "8"]                                  # 8 = fuera del término (INC-032)
    zp = portal.geometry.buffer(BUF).union_all()
    nt = ejes[trat]
    en_portal = (nt.geometry.intersection(zp).length / nt.length >= UMBRAL)

    # accidentes
    s = pd.read_csv(ROOT / "data/processed/siniestros_geo.csv", usecols=["fecha", "unidades", "gravedad", "lon", "lat", "metodo"])
    s = s.dropna(subset=["lon", "lat"])
    s["año"] = pd.to_datetime(s.fecha, errors="coerce").dt.year
    s = s[s["año"].isin(AÑOS)]
    u = s.unidades.fillna("").str.upper()
    s["bici"] = u.str.contains("BICI"); s["vmp"] = u.str.contains("VMP") | u.str.contains("PATIN")
    s["bv"] = s.bici | s.vmp; s["otros"] = ~s.bv
    s["bv_her"] = s.bv & (s.gravedad.fillna("") != "SIN HERIDOS")       # un choque bici-patinete cuenta en bici y en vmp
    pts = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs=4326).to_crs(25830)
    asig = gpd.sjoin_nearest(pts, ejes[["uid", "geometry"]], max_distance=MAXD, how="inner")
    asig = asig[~asig.index.duplicated()]
    YS = ["bv", "otros", "bici", "vmp", "bv_her"]
    cnt = asig.groupby(["uid", "año"])[YS].sum().astype(int)
    panel = pd.MultiIndex.from_product([ejes.uid, AÑOS], names=["uid", "año"]).to_frame(index=False)
    panel = panel.merge(cnt.reset_index(), on=["uid", "año"], how="left").fillna({y: 0 for y in YS})
    # vecinos: tramos sin carril a ≤ 300 m de uno tratado, con la fecha del tratado más cercano (para el desplazamiento)
    vec = ejes[ejes["local"]][["uid", "geometry"]]
    cerca = gpd.sjoin_nearest(vec, ejes[trat][["foto_cb", "geometry"]], how="left")
    ejes["foto_vec"] = ejes.uid.map(cerca[~cerca.index.duplicated()].set_index("uid").foto_cb)
    panel = panel.merge(ejes[["uid", "grupo", "foto_cb", "local", "foto_vec"]], on="uid")
    # «después»: años ≥ foto (lo hecho en foto-1 ya está todo el año); el año foto-1 es transición y se quita
    panel["post"] = ((panel.grupo == "tratado") & (panel["año"] >= panel.foto_cb)).astype(int)
    panel = panel[~((panel.grupo == "tratado") & (panel["año"] == panel.foto_cb - 1))]

    res_ev = {y: evento(panel, y) for y in ("bv", "otros")}
    # desplazamiento: ¿bajan los vecinos frente a los controles lejanos?, y el total de la zona (tratados + vecinos)
    lej = panel[(panel.grupo == "control") & ~panel["local"]]
    v = panel[panel["local"]].copy(); v["post"] = (v["año"] >= v.foto_vec).astype(int); v = v[v["año"] != v.foto_vec - 1]
    z = pd.concat([panel[panel.grupo == "tratado"], v])

    def ajusta(datos, y):
        d = datos[datos.groupby("uid")[y].transform("sum") > 0]           # sin accidentes, el tramo no informa
        X = pd.get_dummies(d["año"], prefix="a", drop_first=True, dtype=float); X["post"] = d.post.astype(float)
        if d.post.sum() == 0:
            return None
        r = ConditionalPoisson(d[y].values, X.values, groups=d.uid.values).fit(disp=0)
        k = list(X.columns).index("post"); b, se = r.params[k], r.bse[k]
        return {"efecto": round(float(np.exp(b)) - 1, 3), "ic95": [round(float(np.exp(b - 1.96 * se)) - 1, 3), round(float(np.exp(b + 1.96 * se)) - 1, 3)],
                "p": round(float(r.pvalues[k]), 4), "tramos": int(d.uid.nunique()), "tramos_tratados_con_post": int(d[d.post == 1].uid.nunique()),
                "accidentes": int(d[y].sum())}

    def remuestreo(datos, y, B=499, semilla=127):
        """Margen sin suponer Poisson puro (nota del 08/11/2026): bootstrap por tramos. Se remuestrean tramos enteros con
        reposición, por separado tratados y controles (así cada réplica tiene el mismo número de tratados), y se reajusta el
        mismo modelo. Si los accidentes varían más de lo que supone Poisson (rachas, obras), este margen sale más ancho."""
        d = datos[datos.groupby("uid")[y].transform("sum") > 0]
        rng = np.random.default_rng(semilla)
        por = {g: d[d.uid.isin(u)] for g, u in d.groupby(d.groupby("uid").post.transform("max"))["uid"].unique().items()}
        trozos = {g: dict(tuple(x.groupby("uid"))) for g, x in por.items()}
        coefs = []
        for _ in range(B):
            partes, n = [], 0
            for g, tr in trozos.items():
                ids = list(tr); elegidos = rng.choice(len(ids), len(ids), replace=True)
                for i in elegidos:
                    t = tr[ids[i]].copy(); t["uid"] = n; n += 1; partes.append(t)
            r = pd.concat(partes)
            X = pd.get_dummies(r["año"], prefix="a", drop_first=True, dtype=float); X["post"] = r.post.astype(float)
            try:
                f = ConditionalPoisson(r[y].values, X.values, groups=r.uid.values).fit(disp=0)
                coefs.append(f.params[list(X.columns).index("post")])
            except Exception:
                continue
        c = np.array(coefs)
        lo, hi = np.percentile(c, [2.5, 97.5])
        return {"ic95_remuestreo": [round(float(np.exp(lo)) - 1, 3), round(float(np.exp(hi)) - 1, 3)],
                "p_remuestreo": round(float(min(1, 2 * min((c <= 0).mean(), (c >= 0).mean()))), 4),
                "replicas_validas": int(len(c)), "replicas": B}

    base = panel[panel.grupo.isin(["tratado", "control"])]
    loc = panel[(panel.grupo == "tratado") | panel["local"]]
    res = {}
    for nom, d in (("todos_los_controles", base), ("controles_del_barrio", loc)):
        res[nom] = {y: ajusta(d, y) for y in YS}
        # solo los tramos que en OSM y en el portal coinciden (más fiables)
        ok = set(nt.uid[en_portal.values])
        d2 = d[(d.grupo != "tratado") | d.uid.isin(ok)]
        res[nom + "_solo_validados_portal"] = {y: ajusta(d2, y) for y in ("bv", "otros")}

    # robustez (08/11/2026, fechas comprobadas con noticias): sin reformas de carriles que ya existían (Germans Machado bajó de
    # la acera a la calzada) ni tramos sin fuente de apertura (Cid hacia Xirivella, en OSM en 2025; Serradora; Gonzalo Tejero
    # Langarita y Camp de Túria). Las 9 calles con fecha documentada cuadran con el año de OSM.
    dudosos = set(ejes.uid[(ejes.grupo == "tratado") & (
        ejes.tipnomcalle.isin(["AVINGUDA GERMANS MACHADO", "CARRER SERRADORA", "CARRER GONZALO TEJERO LANGARITA", "CARRER CAMP DE TÚRIA"])
        | ((ejes.tipnomcalle == "AVINGUDA CID") & (ejes.foto_cb == 2026)))])
    res["sin_reformas_ni_tramos_sin_fuente"] = {y: ajusta(base[~base.uid.isin(dudosos)], y) for y in ("bv", "otros", "bv_her")}
    res["vecinos_frente_a_lejanos"] = {y: ajusta(pd.concat([v, lej]), y) for y in ("bv", "otros")}
    res["zona_tratados_y_vecinos_frente_a_lejanos"] = {y: ajusta(pd.concat([z, lej]), y) for y in ("bv", "otros")}
    # márgenes por remuestreo de tramos para las cifras que se publicarían
    for nom, d, ys in (("todos_los_controles", base, ("bv", "otros", "bv_her", "vmp", "bici")), ("controles_del_barrio", loc, ("bv", "otros")),
                       ("sin_reformas_ni_tramos_sin_fuente", base[~base.uid.isin(dudosos)], ("bv",))):
        for y in ys:
            if res[nom].get(y):
                res[nom][y].update(remuestreo(d, y, B=499 if (nom, y) == ("todos_los_controles", "bv") else 199)); print(nom, y, res[nom][y], flush=True)
    res_cont = contadores(ejes, trat)

    # tramos tratados para revisar con noticias
    tr = ejes[trat].copy(); tr["km"] = (tr.length / 1000).round(3); tr["en_portal"] = en_portal.values
    tot = asig.groupby(["uid", "bv"]).size().unstack(fill_value=0).rename(columns={True: "bv", False: "otros"})
    tr = tr.merge(tot, left_on="uid", right_index=True, how="left").fillna({"bv": 0, "otros": 0})
    tr["construido_hasta"] = (tr.foto_cb - 1).astype(int)
    (ROOT / "outputs").mkdir(exist_ok=True)
    tr[["uid", "tipnomcalle", "codvia", "construido_hasta", "km", "en_portal", "bv", "otros"]].sort_values(["construido_hasta", "tipnomcalle"]).to_csv(
        ROOT / "outputs/politicas_carril_bici_tramos.csv", index=False)
    resumen = {
        "tramos": {g: int((ejes.grupo == g).sum()) for g in ("tratado", "control", "siempre", "pierde")},
        "km_tratados_por_año_de_obra": {int(a - 1): round(float(ejes[ejes.foto_cb == a].length.sum() / 1000), 1) for a in sorted(ejes.foto_cb.dropna().unique())},
        "tratados_en_portal": f"{int(en_portal.sum())} de {len(en_portal)} tramos ({en_portal.mean():.0%}); km {nt[en_portal.values].length.sum() / 1000:.1f} de {nt.length.sum() / 1000:.1f}",
        "accidentes_asignados": int(len(asig)), "accidentes_con_coordenadas": int(len(pts)),
        "modelos": res,
        "evento": res_ev,
        "contadores": res_cont,
        "parametros": {"buffer_m": BUF, "umbral": UMBRAL, "max_dist_accidente_m": MAXD, "control_local_m": LOCAL},
    }
    (ROOT / "outputs/politicas_carril_bici.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
