"""Contrato v2 · ADVERTENCIAS sobre el extracto crudo (Reto 02).

Reglas que NO detienen el pipeline: se registran y se reportan al dueño del dato. Se aplican al
extracto crudo (data/raw/crm_extracto.csv), por eso pueden usar columnas no canónicas.

Validar:  uv run python -m scripts.validar_contrato advertencias data/raw/crm_extracto.csv
"""

import pandera.pandas as pa

warnings_schema = pa.DataFrameSchema(
    columns={
        # Columnas que usan sus reglas, por ejemplo:
        "fecha_alta": pa.Column(str, nullable=True),
        "fecha_corte": pa.Column(str),
    },
    checks=[
        # Advertencia 1: fecha de alta ausente (28 filas en el perfil V4).
        # No es bloqueante aquí porque fecha_alta no forma parte del esquema canónico.
        pa.Check(
            lambda df: df["fecha_alta"].notna(),
            error="ADVERTENCIA: fecha_alta vacía",
        ),
        # Advertencia 2: alta posterior al corte (20 filas en el perfil V4).
        pa.Check(
            lambda df: df["fecha_alta"].isna() | (df["fecha_alta"] <= df["fecha_corte"]),
            error="fecha_alta posterior a fecha_corte",
        ),
        # Agreguen aquí las demás advertencias que negocien.
    ],
    strict=False,  # el extracto trae más columnas: aquí no se exige el modelo canónico
    coerce=True,
    name="crm_warnings",
)
