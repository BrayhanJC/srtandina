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
from src.common import FEATURES, ID_COL, MODEL_META, MODEL_PATH, REPORTS_DIR


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
    # TODO (Reto 04): implementar con la capacidad de la variante (`business.weekly_capacity`).
    # La lista lleva SOLO lo que el agente necesita: prioridad, customer_id, probabilidad y versión.
    raise NotImplementedError("Reto 04: lista del lunes con la capacidad de la variante")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inferencia batch del lunes")
    parser.add_argument("batch", type=Path)
    parser.add_argument("--out-dir", type=Path, default=REPORTS_DIR)
    args = parser.parse_args(argv)

    batch = pd.read_csv(args.batch)
    try:
        features_schema.validate(batch, lazy=True)
    except pandera.errors.SchemaErrors as err:
        # TODO (Reto 04): dejar registro del rechazo en <out-dir>/rejected/<lote>.json con el nivel
        # CRÍTICO-CONTRATO y las reglas violadas (sin customer_id), sin escribir predicciones.
        print(
            f"[predict] 🛑 CRÍTICO-CONTRATO: el lote viola el contrato "
            f"({len(err.failure_cases)} fallas): no se predice"
        )
        return 2

    meta = json.loads(MODEL_META.read_text())
    scored = score(batch, joblib.load(MODEL_PATH), meta)
    out = args.out_dir / "predictions"
    out.mkdir(parents=True, exist_ok=True)
    columnas = [ID_COL, "churn_probability", "churn_pred", "model_version", "scored_at"]
    scored[columnas].to_csv(out / f"{args.batch.stem}_scored.csv", index=False)
    # TODO (Reto 04): generar <out-dir>/predictions/<lote>_lista.csv con prioritize() y la capacidad.
    print(
        f"[predict] {len(scored)} clientes · {int(scored['churn_pred'].sum())} en riesgo · "
        f"modelo v{meta['model_version']} → {os.path.relpath(out / (args.batch.stem + '_scored.csv'))}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
