"""Meta de la acción 3.2.2 del Plan Director (−50 % de siniestros con ciclistas o VMP en 2030): senda, banda y juicio anual.

Funciones puras, sin leer datos: las usan scripts/exportar_web.py (con los datos reales) y scripts/comprobar.py
(con un año simulado, para comprobar que el juicio funciona solo cuando se publique un año nuevo).
- Senda: la misma bajada en porcentaje cada año, desde la base hasta la mitad en el año de la meta.
- Banda (desde el 07/11/2026): cifras del año compatibles con la senda teniendo en cuenta el azar del año observado Y el de
  la base (la base es también un recuento, y 2025 es el máximo de la serie). Un año x es compatible si el IC95 de la razón
  x / base (confint_poisson_2indep, score) contiene la razón que marca la senda. Antes solo contaba el azar del año observado
  (poisson.ppf) y daba «compatible» con demasiada facilidad (revisión de datos del 07/11/2026). No incluye la
  sobredispersión (Pearson/gl ≈ 1,28 en los recuentos mensuales): se dice en la web.
- Juicio de un año: «debajo» (por debajo de la banda), «compatible» (dentro) o «encima» (por encima). En la web
  «compatible» se rotula «no se puede descartar que vaya al ritmo», nunca «va al ritmo».
- Comparación con la base: statsmodels.stats.rates.test_poisson_2indep (razón de tasas, prueba score) y su IC95."""
from statsmodels.stats.rates import confint_poisson_2indep, test_poisson_2indep

NIVEL = 0.95
ESTADOS = ("debajo", "compatible", "encima")


def _r4(x): return round(float(x), 4)


def _ic(x, base_suma, base_años, nivel=NIVEL):
    return confint_poisson_2indep(x, 1, base_suma, base_años, method="score", compare="ratio", alpha=1 - nivel)


def banda(mu, base_suma, base_años, nivel=NIVEL):
    """[mínimo, máximo] de los recuentos de un año compatibles con la senda mu frente a la base (suma de base_años años):
    los x cuyo IC de la razón x / base contiene mu / base. Búsqueda binaria (el IC crece con x)."""
    r = mu / (base_suma / base_años)
    def primero(cond, a, b):                     # menor entero en [a, b] que cumple cond (monótona)
        while a < b:
            m = (a + b) // 2
            if cond(m): b = m
            else: a = m + 1
        return a
    tope = int(mu * 4) + 50
    lo = primero(lambda x: _ic(x, base_suma, base_años, nivel)[1] >= r, 0, tope)
    hi = primero(lambda x: _ic(x, base_suma, base_años, nivel)[0] > r, lo, tope) - 1
    return [int(lo), int(hi)]


def juicio(x, mu, base_suma, base_años, nivel=NIVEL):
    """Estado de un año observado x frente a la senda mu: debajo · compatible · encima."""
    lo, hi = banda(mu, base_suma, base_años, nivel)
    return "debajo" if x < lo else "encima" if x > hi else "compatible"


def frente_base(x, base_suma, base_años):
    """Año observado x frente a la base (suma de base_años años): razón de tasas, IC95 y p (test_poisson_2indep)."""
    t = test_poisson_2indep(x, 1, base_suma, base_años, method="score", compare="ratio")
    ic = confint_poisson_2indep(x, 1, base_suma, base_años, method="score", compare="ratio")
    return {"razon": _r4(t.ratio), "ic": [_r4(ic[0]), _r4(ic[1])], "p": _r4(t.pvalue)}


def escenario(tot, años_base, año_meta, nivel=NIVEL):
    """Escenario de la meta con base = media de los años de años_base (un año, o varios para la comprobación).

    tot: {año: siniestros}. La senda arranca en el último año de la base. Devuelve base, meta, senda y banda de cada
    año hasta año_meta, el juicio de cada año con datos posterior a la base y la conclusión (la del último año)."""
    años_base = sorted(años_base); b = años_base[-1]
    suma = sum(tot[a] for a in años_base); base_x = suma / len(años_base)
    base = int(base_x + 0.5); meta = int(base_x / 2 + 0.5); n = año_meta - b       # 750,5 → 751, como Math.round
    mu = {a: base_x * 0.5 ** ((a - b) / n) for a in range(b, año_meta + 1)}
    post = sorted(a for a in tot if a > b)
    jz = {str(a): {"obs": tot[a], "senda": int(mu[a] + 0.5), "banda": banda(mu[a], suma, len(años_base), nivel), "estado": juicio(tot[a], mu[a], suma, len(años_base), nivel),
                   "base": frente_base(tot[a], suma, len(años_base))} for a in post if a <= año_meta}
    ult = max(tot)
    return {"año": b, "años": años_base, "etq": f"{años_base[0]}-{b}" if len(años_base) > 1 else str(b),
            "base": base, "base_x": round(base_x, 1), "meta": meta, "senda_anual": _r4(1 - 0.5 ** (1 / n)),
            "senda": {str(a): int(v + 0.5) for a, v in mu.items()},
            "banda": {str(a): banda(v, suma, len(años_base), nivel) for a, v in mu.items() if a > b},
            "evaluados": post, "juicio": jz, "concl": jz[str(post[-1])]["estado"] if jz else "pendiente",
            "senda_ult": int(mu[ult] + 0.5) if ult in mu else None,
            "sobre": tot[ult] - int(mu[ult] + 0.5) if ult in mu else None,
            # bajada anual necesaria desde el último año con datos hasta la meta (desde el año siguiente)
            "necesaria": _r4(1 - (meta / tot[ult]) ** (1 / (año_meta - ult))) if ult < año_meta else None}


def uso(imd, tot, año_base, año_meta):
    """Panel de uso del carril bici frente a los siniestros (página de método, sección «uso»).

    imd: tabla contador × año con la IMD (solo los contadores con dato todos los años con IMD); tot: siniestros de bici o
    VMP por año. El uso se mide hasta el último año con IMD (a1), que puede ser anterior al último año de siniestros
    (la IMD de Movilidad llega más tarde): los cocientes del último año y los escenarios de 2030 salen de a1, nunca de un
    año sin IMD (pendiente 78: con un 2026 sin IMD salía «NaN»)."""
    años_u = [int(a) for a in imd.columns]; a0, a1 = años_u[0], años_u[-1]
    assert año_base in años_u, "el año base de la meta tiene que tener IMD"
    iu = imd.sum() / imd.sum()[a0] * 100
    años_s = [a for a in sorted(tot) if a >= a0]; s0 = a0          # siniestros con la misma base que el uso
    g = (iu[a1] / 100) ** (1 / (a1 - a0)) - 1 if a1 > a0 else 0.0     # crecimiento anual medio del tráfico
    rB = iu[a1] / iu[año_base]                                          # uso de a1 frente al año base
    u30 = {"igual": _r4(rB), "sigue": _r4(rB * (1 + g) ** (año_meta - a1))}    # uso de año_meta frente al año base
    ant = años_u[-2] if len(años_u) > 1 else None
    return {"uso_n": int(len(imd)), "uso_a0": a0, "uso_a1": a1, "uso_ant": ant,
            "uso_ix": {str(a): round(float(iu[a]), 1) for a in años_u},
            "sin_ix": {str(a): round(tot[a] / tot[s0] * 100, 1) for a in años_s},
            "uso_g": _r4(g), "uso30": u30, "riesgo": {k: _r4(1 - 0.5 / v) for k, v in u30.items()},   # bajada del riesgo por viaje para −50 %
            # variación del último año con IMD, en uso y en siniestros (los mismos dos años)
            "uso_ult": _r4(iu[a1] / iu[ant] - 1) if ant else None, "sin_ult": _r4(tot[a1] / tot[ant] - 1) if ant else None}
