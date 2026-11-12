"""Inferencia batch del lunes (Reto 04): la "I" de la arquitectura FTI. BASE PARA COMPLETAR.

Lo que ya hace esta base:
  1. Valida el lote contra el contrato de datos ANTES de puntuar (contrato §12.3).
  2. Puntúa con el modelo desplegado y aplica el umbral de decisión con el que fue evaluado.
  3. Escribe reports/predictions/<lote>_scored.csv con la versión del modelo en cada fila.

Lo que completa el equipo (Reto 04, bloque 6; ver los TODO):
  - La lista del lunes con la capacidad de su variante (HU-08) → reports/predictions/<lote>_lista.csv
  - El registro del rechazo cuando el lote viola el contrato → reports/rejected/<lote>.json
  - Las pruebas tests/test_predict_batch.py derivadas de HU-08, HU-03 y CU-01

Uso:  python -m src.predict_batch data/production/batch_normal.csv
Código de salida: 0 (lote puntuado) · 2 (CRÍTICO-CONTRATO: el lote no se puntúa).
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
import pandera.errors

from contracts.churn_contract import features_schema
from src.common import FEATURES, ID_COL, MODEL_META, MODEL_PATH, REPORTS_DIR, load_params


def score(batch: pd.DataFrame, model, meta: dict) -> pd.DataFrame:
    """Probabilidad, decisión al umbral del modelo, versión y fecha de puntuación."""
    proba = model.predict_proba(batch[FEATURES])[:, 1]
    threshold = float(meta["decision_threshold"])
    return batch.assign(
        churn_probability=proba.round(4),
        churn_pred=(proba >= threshold).astype(int),
        model_version=meta["model_version"],
        scored_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def prioritize(scored: pd.DataFrame, capacity: int) -> pd.DataFrame:
    """HU-08: clientes en riesgo, en orden descendente, como máximo `capacity`, con prioridad 1..n."""
    en_riesgo = scored[scored["churn_pred"] == 1]  # 1. filtrar: probabilidad >= umbral del modelo
    ordenados = en_riesgo.sort_values("churn_probability", ascending=False, kind="stable")  # 2. ordenar
    lista = ordenados.head(capacity).reset_index(drop=True)  # 3. recortar a la capacidad
    lista.insert(0, "prioridad", range(1, len(lista) + 1))
    return lista[["prioridad", ID_COL, "churn_probability", "model_version"]]  # 4. minimizar


def reglas_violadas(err: pandera.errors.SchemaErrors) -> dict[str, int]:
    """{regla: filas afectadas}, sin valores ni identificadores de las filas (contrato §7.4)."""
    fc = err.failure_cases
    de_tabla = fc["schema_context"] == "DataFrameSchema"  # reglas entre columnas o de toda la tabla
    columna = fc["column"].astype(str).where(~de_tabla, "(tabla)")
    falta = fc["check"] == "column_in_dataframe"  # columna ausente: failure_case es su NOMBRE
    columna = columna.where(~falta, fc["failure_case"].astype(str))
    regla = columna + " · " + fc["check"].astype(str)
    return {
        r: int(g["index"].nunique()) if g["index"].notna().any() else len(g) for r, g in fc.groupby(regla)
    }


def _ruta_legible(p) -> str:
    """Ruta relativa al directorio actual; absoluta si están en unidades distintas (Windows)."""
    try:
        return os.path.relpath(p)
    except ValueError:  # p. ej. tmp_path en C: y el repositorio en D:
        return str(p)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inferencia batch del lunes")
    parser.add_argument("batch", type=Path)
    parser.add_argument("--out-dir", type=Path, default=REPORTS_DIR)
    parser.add_argument("--capacity", type=int, default=None, help="por defecto, business.weekly_capacity")
    args = parser.parse_args(argv)

    batch = pd.read_csv(args.batch)
    try:
        features_schema.validate(batch, lazy=True)
    except pandera.errors.SchemaErrors as err:
        registro = {
            "nivel": "CRÍTICO-CONTRATO",
            "lote": args.batch.name,
            "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
            "filas_del_lote": len(batch),
            "reglas_violadas": reglas_violadas(err),
        }
        rechazos = args.out_dir / "rejected"
        rechazos.mkdir(parents=True, exist_ok=True)
        destino = rechazos / f"{args.batch.stem}.json"
        destino.write_text(json.dumps(registro, indent=2, ensure_ascii=False))
        print(
            f"[predict] 🛑 CRÍTICO-CONTRATO: el lote viola el contrato "
            f"({len(err.failure_cases)} fallas): no se predice → {_ruta_legible(destino)}"
        )
        return 2

    meta = json.loads(MODEL_META.read_text())
    scored = score(batch, joblib.load(MODEL_PATH), meta)
    out = args.out_dir / "predictions"
    out.mkdir(parents=True, exist_ok=True)
    columnas = [ID_COL, "churn_probability", "churn_pred", "model_version", "scored_at"]
    scored[columnas].to_csv(out / f"{args.batch.stem}_scored.csv", index=False)
    capacidad = args.capacity
    if capacidad is None:  # sin --capacity: la capacidad semanal de la variante
        capacidad = load_params()["business"]["weekly_capacity"]
    lista = prioritize(scored, capacidad)
    lista.to_csv(out / f"{args.batch.stem}_lista.csv", index=False)
    print(
        f"[predict] {len(scored)} clientes · {int(scored['churn_pred'].sum())} en riesgo · "
        f"lista {len(lista)}/{capacidad} · modelo v{meta['model_version']} → {_ruta_legible(out)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
