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
    # "<columna_no_canonica>": "<razón>",
}


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Devuelve (conjunto limpio, informe). Cada tratamiento actúa sobre el VALOR NEGOCIADO."""
    n0 = len(df)
    informe: dict = {"filas_entrada": n0, "tratamientos": {}}
    t = informe["tratamientos"]
    df = df.copy()

    # 1. Recodificaciones acordadas (un valor concreto → un valor del dominio).
    #    Ejemplo de la forma (reemplácelo por sus acuerdos):
    #    mascara = df["<columna>"] == "<valor_acordado>"
    #    t["recodificado_<columna>"] = int(mascara.sum())
    #    df.loc[mascara, "<columna>"] = "<valor_del_dominio>"

    # 2. Exclusiones acordadas: nombre del tratamiento → máscara de filas a excluir.
    reglas_exclusion: dict[str, pd.Series] = {
        # "<motivo>": df["<columna>"] == <valor_acordado>,
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
