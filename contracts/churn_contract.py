"""Contrato de datos ejecutable (Pandera).

Traduce a reglas verificables el contrato acordado con el dueño del dato (docs/datos_gobernanza.md).
Si los datos no cumplen, el pipeline se detiene antes de entrenar.

Hay dos esquemas:
- `features_schema`: lo que el modelo necesita para predecir (sirve también para lotes de producción).
- `training_schema`: features + variable objetivo + identificador único (datos de entrenamiento).
"""

import pandera.pandas as pa

from src.common import CATEGORIES

_features = {
    "tenure_months": pa.Column(int, pa.Check.in_range(0, 72)),
    "contract_type": pa.Column(str, pa.Check.isin(CATEGORIES["contract_type"])),
    "internet_service": pa.Column(str, pa.Check.isin(CATEGORIES["internet_service"])),
    "payment_method": pa.Column(str, pa.Check.isin(CATEGORIES["payment_method"])),
    "monthly_charges": pa.Column(float, pa.Check.in_range(0, 500)),
    "support_tickets": pa.Column(int, pa.Check.in_range(0, 50)),
    "senior_citizen": pa.Column(int, pa.Check.isin([0, 1])),
}

# RC-3: los clientes sin internet solamente pueden tener cargos de hasta 60.
# Los nulos se controlan por RC-2; aquí se ignoran para no duplicar fallas.
RC3 = pa.Check(
    lambda df: (
        df["monthly_charges"].isna()
        | (df["internet_service"] != "none")
        | (df["monthly_charges"] <= 60)
    ),
    error="RC-3: sin internet con cargo mayor a 60",
)

# Propuesta técnica: 5 %, superior a 3,37 % observado en el extracto V4.
# Requiere registro y validación de la decisión con el dueño del dato.
MAX_DISCARD_SHARE = 0.05


def discard_ok(cleaning_report: dict) -> bool:
    """Bloquea lotes con una proporción de descarte superior al límite."""
    return cleaning_report["proporcion_descartada"] <= MAX_DISCARD_SHARE


features_schema = pa.DataFrameSchema(
    columns=_features,
    checks=[RC3],
    strict=False,  # se permiten columnas adicionales (ej. customer_id, churn)
    coerce=True,
    name="churn_features",
)

training_schema = pa.DataFrameSchema(
    columns={
        "customer_id": pa.Column(str, unique=True),
        **_features,
        "churn": pa.Column(int, pa.Check.isin([0, 1])),
    },
    checks=[
        RC3,
        # Regla de negocio: la tasa de churn histórica debe ser plausible.
        pa.Check(lambda df: 0.05 <= df["churn"].mean() <= 0.60, error="tasa de churn fuera de rango"),
    ],
    strict=True,
    coerce=True,
    name="churn_training",
)
