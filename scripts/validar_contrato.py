"""Valida un CSV contra un contrato y resume las fallas por regla, sin identificadores (Reto 02).

  uv run python -m scripts.validar_contrato v1 data/raw/crm_extracto.csv
  uv run python -m scripts.validar_contrato v2 data/processed/clean.csv
  uv run python -m scripts.validar_contrato advertencias data/raw/crm_extracto.csv

Cada nombre corresponde a un esquema del repositorio:
  v1           contracts/crm_contract_v1.py  → v1_documentacion
  v2           contracts/churn_contract.py   → training_schema
  advertencias contracts/crm_warnings.py     → warnings_schema

Código de salida: 0 si el contrato se cumple, 1 si alguna regla falla.
"""

import importlib
import sys

import pandas as pd
import pandera.errors

CONTRATOS = {
    "v1": ("contracts.crm_contract_v1", "v1_documentacion"),
    "v2": ("contracts.churn_contract", "training_schema"),
    "advertencias": ("contracts.crm_warnings", "warnings_schema"),
}


def resumen(schema, df: pd.DataFrame) -> pd.DataFrame | None:
    try:
        schema.validate(df, lazy=True)
        return None
    except pandera.errors.SchemaErrors as err:
        fc = err.failure_cases.copy()
        fc["failure_case"] = fc["failure_case"].map(str)
        de_tabla = fc["schema_context"] == "DataFrameSchema"
        grupos = [(c, k, g) for (c, k), g in fc[~de_tabla].groupby(["column", "check"])]
        grupos += [
            ("(entre columnas / esquema)", k, g)
            for k, g in fc[de_tabla].groupby("check")
        ]
        filas = []
        for columna, check, g in grupos:
            con_fila = g["index"].notna().any()
            # Ni ejemplos de customer_id (dato personal) ni de reglas entre columnas (son filas enteras).
            sin_ejemplos = columna == "customer_id" or (
                con_fila and columna.startswith("(")
            )
            filas.append(
                {
                    "columna": columna,
                    "regla": check,
                    "filas_afectadas": g["index"].nunique() if con_fila else len(g),
                    "ejemplos": (
                        ""
                        if sin_ejemplos
                        else ", ".join(g["failure_case"].unique()[:4])
                    ),
                }
            )
        return pd.DataFrame(filas).sort_values("filas_afectadas", ascending=False)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in CONTRATOS:
        print(
            f"Uso: python -m scripts.validar_contrato {{{'|'.join(CONTRATOS)}}} <archivo.csv>"
        )
        return 2
    nombre, ruta = sys.argv[1], sys.argv[2]
    modulo, esquema = CONTRATOS[nombre]
    try:
        schema = getattr(importlib.import_module(modulo), esquema)
    except (ModuleNotFoundError, AttributeError):
        print(
            f"No se encontró {esquema} en {modulo.replace('.', '/')}.py: créelo antes de validar con '{nombre}'."
        )
        return 2
    df = pd.read_csv(ruta)
    tabla = resumen(schema, df)
    print(f"[{nombre}] {ruta}: {len(df)} filas · {len(df.columns)} columnas")
    if tabla is None:
        print("  ✅ sin fallas")
        return 0
    print(f"  ❌ {len(tabla)} reglas incumplidas")
    print(tabla.to_string(index=False, max_colwidth=60))
    return 1


if __name__ == "__main__":
    sys.exit(main())
