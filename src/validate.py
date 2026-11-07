
"""Etapa `validate`: el contrato v2 decide si el pipeline continúa (Reto 03).

Bloqueante: training_schema sobre el conjunto limpio y la regla de
descarte máximo sobre reports/cleaning.json.

Advertencias: warnings_schema sobre el extracto crudo (no detienen nada).

Escribe reports/validation.json con conteos por regla,
sin identificadores ni valores de filas.

Termina con código 1 solo si falla una regla bloqueante.
"""

import json
import sys

import pandas as pd
import pandera.errors

from contracts.churn_contract import discard_ok, training_schema
from contracts.crm_warnings import warnings_schema
from src.common import CLEAN_DATA, CRM_EXTRACT, REPORTS_DIR


def fallas_por_regla(schema, df: pd.DataFrame) -> dict[str, int]:
    """Devuelve {regla: filas afectadas}; vacío si el esquema se cumple."""
    try:
        schema.validate(df, lazy=True)
        return {}

    except pandera.errors.SchemaErrors as err:
        fc = err.failure_cases

        de_tabla = fc["schema_context"] == "DataFrameSchema"

        columna = fc["column"].astype(str).where(
            ~de_tabla, "(tabla)"
        )

        regla = columna + " · " + fc["check"].astype(str)

        return {
            r: (
                int(g["index"].nunique())
                if g["index"].notna().any()
                else len(g)
            )
            for r, g in fc.groupby(regla)
        }


def main() -> int:
    bloqueantes = fallas_por_regla(
        training_schema,
        pd.read_csv(CLEAN_DATA)
    )

    limpieza = json.loads(
        (REPORTS_DIR / "cleaning.json").read_text()
    )

    if not discard_ok(limpieza):
        bloqueantes[
            "descarte máximo · proporcion_descartada"
        ] = limpieza["proporcion_descartada"]

    advertencias = fallas_por_regla(
        warnings_schema,
        pd.read_csv(CRM_EXTRACT)
    )

    resumen = {
        "valid": not bloqueantes,
        "bloqueantes": bloqueantes,
        "advertencias": advertencias
    }

    (REPORTS_DIR / "validation.json").write_text(
        json.dumps(
            resumen,
            indent=2,
            ensure_ascii=False
        )
    )

    for nombre, fallas in (
        ("bloqueante", bloqueantes),
        ("advertencia", advertencias)
    ):
        for r, n in fallas.items():
            print(
                f"[validate] "
                f"{'❌ ' if nombre == 'bloqueante' else '⚠️ '} "
                f"{nombre}: {r} → {n}"
            )

    if bloqueantes:
        print("[validate] ❌ el contrato v2 falló: no se entrena")
    else:
        print("[validate] ✅ contrato v2 OK")

    return 0 if not bloqueantes else 1


if __name__ == "__main__":
    sys.exit(main())
