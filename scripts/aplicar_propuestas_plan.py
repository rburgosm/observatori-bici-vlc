"""Aplica al seguimiento del Plan las propuestas revisadas y aceptadas.

Lee data/processed/plan_seguimiento_propuestas.csv (lo escribe el agente
verificador-plan) y aplica a la BASE (data/processed/observatorio.sqlite, la
fuente de verdad del Plan desde el 06/11/2026) solo las filas con
decision = aceptada, revisado_por y fecha_revision rellenos, y aún sin aplicar
(columna `aplicada` vacía). Valida el esquema y los estados y después escribe
con UPDATE/INSERT en UNA transacción: si una fila incumple una restricción de la
base (estado sin fuente o sin fecha de la fuente, fecha de la fuente posterior a
la comprobación, tipo de fuente fuera del vocabulario…), no se aplica nada.
Hecho el COMMIT, reescribe el volcado data/processed/observatorio_plan.sql (va a
git) y la exportación data/processed/plan_seguimiento.csv (para revisar el diff).

Por defecto es un ensayo (--dry-run): hace lo mismo dentro de la transacción
(así también prueba las restricciones) y la deshace; no escribe nada.
Con --aplicar confirma la transacción, reescribe volcado y CSV y marca las
propuestas con la fecha de aplicación en `aplicada`.

Nombres de campo: las propuestas usan los del CSV exportado (fecha_estado,
comprobado, cita_plan, fuente_url…); `campo` admite también los de la base
fecha_fuente, fecha_comprobacion, ref_plan y texto_plan (se traducen). La fuente
que respalda el estado (fuente_estado_id) se asigna con la regla de la base: la
principal, salvo que sea el propio Plan; entonces, la única URL de la nota.

Qué hace cada tipo:
- cambio_estado: estado = valor_propuesto; fecha_estado = fecha_fuente;
  fuente_url, fuente_tipo y fuente_titulo los de la propuesta.
- nueva_fuente: fuente_url = valor_propuesto; fuente_tipo y fuente_titulo los
  de la propuesta; fecha_estado = fecha_fuente.
- correccion: el campo indicado (nunca id ni estado) = valor_propuesto.
- nueva_actuacion: añade la fila que viene como JSON en valor_propuesto.
- sin_novedad: solo actualiza `comprobado`.
En todos, `comprobado` = fecha_comprobacion de la propuesta.

Si el valor actual del CSV ya no coincide con `valor_actual` de la propuesta
(alguien lo cambió después), la propuesta se salta como conflicto.

Después: make web (reconstruye la base desde el volcado, con lo derivado: junto
a qué lugar o calle cae cada actuación) y revisión del diff antes de publicar.

Uso: .venv/bin/python -I scripts/aplicar_propuestas_plan.py [--aplicar]
"""
import argparse
import datetime as dt
import json
import io
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import construir_sqlite as CS                       # esquema, guardar_actuacion, volcado y exportación

SEGUIMIENTO = CS.PLAN_CSV                           # exportación de la base (no se lee: el estado actual sale de la base)
PROPUESTAS = RAIZ / "data/processed/plan_seguimiento_propuestas.csv"

COLS_SEG = ["id", "accion_plan", "actuacion", "ambito", "lugar", "lon", "lat", "meta", "estado",
            "fecha_estado", "fuente_url", "fuente_tipo", "fuente_titulo", "cita_plan", "nota", "comprobado"]
COLS_PROP = ["propuesta_id", "fecha_comprobacion", "id", "tipo", "campo", "valor_actual", "valor_propuesto",
             "fuente_url", "fuente_tipo", "fuente_titulo", "fecha_fuente", "cita_fuente", "confianza", "motivo",
             "decision", "revisado_por", "fecha_revision"]
ESTADOS = {"sin_info", "anunciada", "en_marcha", "hecha"}
AMBITOS = {"ciudad", "lugar"}
TIPOS = {"cambio_estado", "nueva_fuente", "correccion", "nueva_actuacion", "sin_novedad"}
DECISIONES = {"pendiente", "aceptada", "rechazada"}
CONFIANZAS = {"alta", "media", "baja"}
# Vocabulario único de fuente_tipo (docs/plan_seguimiento.md, sec. 2, regla 5; el mismo del agente verificador-plan).
# «plan» es el propio Plan Director, solo como fuente de una actuación sin otra prueba publicada (o hecha según el Plan).
# La v1 usaba también «otro»; se migró el 04/11/2026 y ya no se admite.
FUENTES_PROP = {"contratacion", "bop", "junta_gobierno", "nota_prensa", "documento_municipal", "prensa",
                "respuesta_movilidad", "plan"}
FUENTES_SEG = FUENTES_PROP
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# campos de la base -> columna del CSV exportado (las propuestas pueden usar cualquiera de los dos)
CAMPO_BASE = {"fecha_fuente": "fecha_estado", "fecha_comprobacion": "comprobado"}


def leer(ruta):
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8")


def validar_propuestas(p):
    errores = []
    faltan = [c for c in COLS_PROP if c not in p.columns]
    if faltan:
        errores.append(f"propuestas: faltan columnas {faltan}")
        return errores
    for col, permitidos in [("tipo", TIPOS), ("decision", DECISIONES), ("confianza", CONFIANZAS),
                            ("fuente_tipo", FUENTES_PROP)]:
        malos = p.loc[~p[col].isin(permitidos), "propuesta_id"].tolist()
        if malos:
            errores.append(f"propuestas: {col} no permitido en {malos}")
    dup = p.loc[p["propuesta_id"].duplicated(), "propuesta_id"].tolist()
    if dup:
        errores.append(f"propuestas: propuesta_id repetido {dup}")
    return errores


def validar_seguimiento(s):
    errores = []
    if list(s.columns) != COLS_SEG:
        errores.append(f"seguimiento: columnas distintas de las esperadas: {list(s.columns)}")
        return errores
    if s["id"].duplicated().any():
        errores.append(f"seguimiento: id repetido {s.loc[s['id'].duplicated(), 'id'].tolist()}")
    if (s["id"] == "").any():
        errores.append("seguimiento: hay filas sin id")
    for col, permitidos in [("estado", ESTADOS), ("ambito", AMBITOS), ("fuente_tipo", FUENTES_SEG)]:
        malos = s.loc[~s[col].isin(permitidos), "id"].tolist()
        if malos:
            errores.append(f"seguimiento: {col} no permitido en {malos}")
    for col in ["fecha_estado", "comprobado"]:
        malos = s.loc[(s[col] != "") & ~s[col].str.match(FECHA), "id"].tolist()
        if malos:
            errores.append(f"seguimiento: {col} sin formato AAAA-MM-DD en {malos}")
    sin_fecha = s.loc[(s["estado"] != "sin_info") & (s["fecha_estado"] == ""), "id"].tolist()
    if sin_fecha:
        errores.append(f"seguimiento: estado distinto de sin_info sin fecha_estado en {sin_fecha}")
    return errores


def aplicar_una(s, r):
    """Aplica la propuesta r sobre s (en sitio). Devuelve (ok, mensaje)."""
    tipo, id_, campo = r["tipo"], r["id"], r["campo"]
    if tipo == "nueva_actuacion":
        try:
            fila = json.loads(r["valor_propuesto"])
        except json.JSONDecodeError as e:
            return False, f"JSON no válido: {e}"
        if sorted(fila) != sorted(COLS_SEG):
            return False, f"la fila nueva no tiene las columnas del seguimiento: {sorted(set(fila) ^ set(COLS_SEG))}"
        if fila["id"] in set(s["id"]):
            return False, f"el id {fila['id']} ya existe"
        fila["comprobado"] = r["fecha_comprobacion"]
        s.loc[len(s)] = [str(fila[c]) for c in COLS_SEG]
        return True, f"nueva actuación {fila['id']} ({fila['estado']})"

    if id_ not in set(s["id"]):
        return False, f"el id {id_} no existe"
    i = s.index[s["id"] == id_][0]

    if tipo == "correccion" and campo in ("ref_plan", "texto_plan"):
        ref, txt = CS.partir_cita(s.at[i, "cita_plan"])
        actual = (ref if campo == "ref_plan" else txt) or ""
        if actual != r["valor_actual"]:
            return False, f"conflicto: {id_}.{campo} ya no vale lo que dice la propuesta"
        nuevo = r["valor_propuesto"] or None
        s.at[i, "cita_plan"] = CS.unir_cita(nuevo, txt) if campo == "ref_plan" else CS.unir_cita(ref, nuevo)
        s.at[i, "comprobado"] = r["fecha_comprobacion"]
        return True, f"{id_}: corrige {campo}"
    campo = CAMPO_BASE.get(campo, campo)

    if tipo == "sin_novedad":
        s.at[i, "comprobado"] = r["fecha_comprobacion"]
        return True, f"{id_}: sin novedad (comprobado {r['fecha_comprobacion']})"

    if campo not in COLS_SEG:
        return False, f"campo desconocido «{campo}»"
    if s.at[i, campo] != r["valor_actual"]:
        return False, f"conflicto: {id_}.{campo} ya no vale lo que dice la propuesta"

    if tipo == "cambio_estado":
        if campo != "estado" or r["valor_propuesto"] not in ESTADOS:
            return False, "cambio_estado debe ir sobre «estado» con un estado permitido"
        if not FECHA.match(r["fecha_fuente"]) or not r["fuente_url"]:
            return False, "cambio_estado sin fecha_fuente o sin fuente_url: sin fuente no hay estado"
        s.at[i, "estado"] = r["valor_propuesto"]
        s.at[i, "fecha_estado"] = r["fecha_fuente"]
        for c in ["fuente_url", "fuente_tipo", "fuente_titulo"]:
            s.at[i, c] = r[c]
        msg = f"{id_}: {r['valor_actual']} → {r['valor_propuesto']} ({r['fecha_fuente']})"
    elif tipo == "nueva_fuente":
        if campo != "fuente_url":
            return False, "nueva_fuente debe ir sobre «fuente_url»"
        s.at[i, "fuente_url"] = r["valor_propuesto"]
        s.at[i, "fuente_tipo"] = r["fuente_tipo"]
        s.at[i, "fuente_titulo"] = r["fuente_titulo"]
        if FECHA.match(r["fecha_fuente"]):
            s.at[i, "fecha_estado"] = r["fecha_fuente"]
        msg = f"{id_}: fuente nueva ({r['fuente_tipo']}, {r['fecha_fuente']})"
    elif tipo == "correccion":
        if campo in ("id", "estado"):
            return False, "una corrección no puede tocar id ni estado (usar cambio_estado)"
        s.at[i, campo] = r["valor_propuesto"]
        msg = f"{id_}: corrige {campo}"
    else:
        return False, f"tipo desconocido {tipo}"
    s.at[i, "comprobado"] = r["fecha_comprobacion"]
    return True, msg


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="ensayo sin escribir (por defecto)")
    g.add_argument("--aplicar", action="store_true", help="escribe los cambios")
    args = ap.parse_args()

    if not CS.DB.exists():
        sys.exit(f"falta {CS.DB.relative_to(RAIZ)}: make sqlite")
    con = sqlite3.connect(CS.DB, isolation_level=None)          # transacción explícita (BEGIN … COMMIT/ROLLBACK)
    con.execute("PRAGMA foreign_keys = ON")
    # la base y su volcado en git tienen que coincidir antes de escribir (si no, make sqlite o construir_sqlite.py --volcar)
    if CS.PLAN_SQL.exists() and CS.volcar_plan(con) != CS.PLAN_SQL.read_bytes().decode("utf-8"):
        sys.exit(f"el Plan de la base no es el de {CS.PLAN_SQL.name}: ejecutar make sqlite (o, si la base es la buena, "
                 "construir_sqlite.py --volcar) y volver a probar")
    # estado actual, de la base, con las columnas del CSV exportado (lo que ven el agente y la persona que revisa)
    s = pd.read_csv(io.StringIO(CS.exportar(con, "data/processed/plan_seguimiento.csv")), dtype=str, keep_default_na=False)
    p = leer(PROPUESTAS)
    if "aplicada" not in p.columns:
        p["aplicada"] = ""

    errores = validar_propuestas(p) + validar_seguimiento(s)
    if errores:
        print("No se aplica nada. Errores de validación previos:")
        print("\n".join(f"- {e}" for e in errores))
        sys.exit(1)

    aceptadas = p[(p["decision"] == "aceptada") & (p["aplicada"] == "")].sort_values("propuesta_id")
    sin_revisor = aceptadas[(aceptadas["revisado_por"] == "") | (aceptadas["fecha_revision"] == "")]
    aceptadas = aceptadas.drop(sin_revisor.index)

    hoy = dt.date.today().isoformat()
    hechas, saltadas = [], []
    antes = s.copy()
    for k, r in aceptadas.iterrows():
        ok, msg = aplicar_una(s, r)
        if ok:
            hechas.append((r["propuesta_id"], r["tipo"], msg))
            p.at[k, "aplicada"] = hoy
        else:
            saltadas.append((r["propuesta_id"], msg))
    # filas nuevas o cambiadas: se escriben en la base (UPDATE o INSERT) en una sola transacción
    viejas = antes.set_index("id")
    cambiadas = [fila for fila in s.to_dict("records")
                 if fila["id"] not in viejas.index or viejas.loc[fila["id"]].to_dict() != {c: fila[c] for c in COLS_SEG if c != "id"}]

    errores = validar_seguimiento(s)
    modo = "APLICAR" if args.aplicar else "ENSAYO (no escribe; usar --aplicar)"
    print(f"Modo: {modo}")
    print(f"Propuestas: {len(p)} en total; pendientes {int((p['decision'] == 'pendiente').sum())}, "
          f"rechazadas {int((p['decision'] == 'rechazada').sum())}, aceptadas sin aplicar {len(aceptadas) + len(sin_revisor)}.")
    if len(sin_revisor):
        print(f"Aceptadas sin revisado_por o fecha_revision (no se aplican): {sin_revisor['propuesta_id'].tolist()}")
    print(f"Se aplican {len(hechas)}:")
    for pid, tipo, msg in hechas:
        print(f"  {pid} [{tipo}] {msg}")
    if saltadas:
        print(f"Se saltan {len(saltadas)}:")
        for pid, msg in saltadas:
            print(f"  {pid}: {msg}")
    if errores:
        print("El resultado no valida; no se escribe nada:")
        print("\n".join(f"- {e}" for e in errores))
        sys.exit(1)
    print("Estados tras aplicar: " + ", ".join(f"{k} {v}" for k, v in s["estado"].value_counts().items()))

    con.execute("BEGIN")
    try:
        for fila in cambiadas:
            # lo derivado de esa actuación (junto a qué lugar o calle cae) se recalcula al reconstruir la base (make sqlite)
            con.execute("DELETE FROM plan_actuacion_lugar WHERE actuacion_id = ?", (fila["id"],))
            con.execute("DELETE FROM plan_actuacion_via WHERE actuacion_id = ?", (fila["id"],))
            CS.guardar_actuacion(con, fila)
        CS.borrar_fuentes_huerfanas(con)
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise sqlite3.IntegrityError(f"claves foráneas rotas: {fk[:3]}")
        # la exportación tiene que dar exactamente las filas aplicadas
        assert CS.exportar(con, "data/processed/plan_seguimiento.csv") == s.to_csv(index=False, lineterminator="\r\n"), \
            "la base no exporta lo aplicado"
    except (sqlite3.IntegrityError, AssertionError) as e:
        con.execute("ROLLBACK")
        print(f"La base rechaza el resultado (restricción incumplida); no se escribe nada: {e}")
        sys.exit(1)
    if not (args.aplicar and hechas):
        con.execute("ROLLBACK")
        print(f"Ensayo: {len(cambiadas)} actuaciones cambiarían en la base y cumplen sus restricciones (transacción deshecha).")
        return
    con.execute("COMMIT")
    escritos = CS.guardar_plan(con)
    p.to_csv(PROPUESTAS, index=False, encoding="utf-8", lineterminator="\r\n")
    print(f"Base actualizada ({len(cambiadas)} actuaciones); reescritos {[x.name for x in escritos]}; "
          f"marcadas {len(hechas)} propuestas como aplicadas ({hoy}).")
    print("Siguiente: make web, revisar el diff (git diff data/processed/plan_seguimiento.csv data/processed/observatorio_plan.sql) "
          "y una fila curada en docs/cambios.csv para toda la revisión.")


if __name__ == "__main__":
    main()
