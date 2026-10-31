"""Etapa de limpieza (Reto 02): aplica los tratamientos negociados con el dueño del dato.

Lee data/raw/crm_extracto.csv y escribe:
  data/processed/clean.csv  → solo las 9 columnas canónicas (contrato §2.1)
  reports/cleaning.json     → conteos por tratamiento, sin identificadores

Ejecutar:  uv run python -m src.clean
"""

import json

import pandas as pd

from src.common import CLEAN_DATA, CRM_EXTRACT, FEATURES, ID_COL, REPORTS_DIR, TARGET

CANONICAS = [ID_COL, *FEATURES, TARGET]

# Columnas que llegan en el extracto y no son canónicas: nombre → razón de la exclusión.
COLUMNAS_EXCLUIDAS: dict[str, str] = {
    "region": "no canónica (Contrato §2.3); no se usa en el modelo (minimización)",
    "fecha_alta": "no canónica (Contrato §2.3); la antigüedad ya está en tenure_months",
    "fecha_corte": "no canónica (Contrato §2.3); constante en todo el extracto, no aporta",
    "oferta_retencion_aceptada": "fuga: se registra tras la campaña, no se conoce el lunes 06:00 (RC-5)",
}


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Devuelve (conjunto limpio, informe). Cada tratamiento actúa sobre el VALOR NEGOCIADO."""
    n0 = len(df)
    informe: dict = {"filas_entrada": n0, "tratamientos": {}}
    t = informe["tratamientos"]
    df = df.copy()

    # 1. Recodificaciones acordadas (un valor concreto → un valor del dominio).
    # Acuerdo #1: "Month-to-month" (mayúscula inicial) es el mismo contrato month-to-month.
    mascara = df["contract_type"] == "Month-to-month"
    t["recodificado_contract_type"] = int(mascara.sum())
    df.loc[mascara, "contract_type"] = "month-to-month"

    # Duplicados de customer_id (acuerdos #6 y #7), calculados sobre el extracto ya recodificado.
    repetido = df[ID_COL].duplicated(keep=False)
    copia_exacta = df.duplicated(keep="first")  # #6: la segunda fila idéntica sobra
    con_dos_cargos = repetido & ~df.duplicated(
        keep=False
    )  # #7: mismo cliente, cargos distintos
    cargo_menor = df["monthly_charges"] < df.groupby(ID_COL)[
        "monthly_charges"
    ].transform("max")

    # 2. Exclusiones acordadas: nombre del tratamiento → máscara de filas a excluir.
    reglas_exclusion: dict[str, pd.Series] = {
        "payment_method_tarjeta_debito": df["payment_method"] == "tarjeta_debito",  # #2
        "monthly_charges_vacio": df["monthly_charges"].isna(),  # #3
        "tenure_months_menos_1": df["tenure_months"] == -1,  # #4 (fecha_alta vacía)
        "support_tickets_99": df["support_tickets"] == 99,  # #5
        "duplicado_copia_exacta": copia_exacta,  # #6
        "duplicado_cargo_menor": con_dos_cargos & cargo_menor,  # #7
        "rc3_sin_internet_cargo_mayor_60": (df["internet_service"] == "none")
        & (df["monthly_charges"] > 60),  # #8
    }
    excluir = pd.Series(False, index=df.index)
    for nombre, mascara in reglas_exclusion.items():
        t[f"excluidas_{nombre}"] = int(
            (mascara & ~excluir).sum()
        )  # cada fila se cuenta una vez
        excluir |= mascara
    df = df[~excluir]

    informe["columnas_excluidas"] = COLUMNAS_EXCLUIDAS
    informe["filas_salida"] = len(df)
    informe["proporcion_descartada"] = round(1 - len(df) / n0, 4)
    df = (
        df[CANONICAS].sort_values(ID_COL).reset_index(drop=True)
    )  # orden fijo: limpieza determinista
    return df, informe


def main():
    df, informe = clean(pd.read_csv(CRM_EXTRACT))
    CLEAN_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_DATA, index=False)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "cleaning.json").write_text(
        json.dumps(informe, indent=2, ensure_ascii=False)
    )
    print(
        f"[clean] {informe['filas_entrada']} → {informe['filas_salida']} filas "
        f"({informe['proporcion_descartada']:.1%} descartado)"
    )


if __name__ == "__main__":
    main()
