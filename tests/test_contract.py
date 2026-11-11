
"""Pruebas del contrato de datos: los datos válidos pasan y los inválidos se detectan."""

import pandera.errors
import pytest

from contracts.churn_contract import discard_ok, features_schema, training_schema
from src.synthetic import generate_customers


def test_valid_data_passes(sample_df):
    training_schema.validate(sample_df, lazy=True)


@pytest.mark.parametrize(
    "column, bad_value",
    [
        ("tenure_months", -3),
        ("contract_type", "weekly"),
        ("senior_citizen", 2),
        ("churn", 5),
    ],
)
def test_invalid_values_are_rejected(sample_df, column, bad_value):
    df = sample_df.copy()
    df[column] = df[column].astype(object)
    df.loc[df.index[0], column] = bad_value
    with pytest.raises(pandera.errors.SchemaErrors):
        training_schema.validate(df, lazy=True)


def test_duplicate_ids_are_rejected(sample_df):
    df = sample_df.copy()
    df.loc[df.index[1], "customer_id"] = df.loc[df.index[0], "customer_id"]
    with pytest.raises(pandera.errors.SchemaErrors):
        training_schema.validate(df, lazy=True)


def test_schema_change_scenario_breaks_contract():
    """El escenario 'esquema' del simulacro debe ser detectado por el contrato."""
    batch = generate_customers(n=300, seed=3, scenario="esquema")
    with pytest.raises(pandera.errors.SchemaErrors):
        features_schema.validate(batch, lazy=True)


def test_rc3_sin_internet_con_cargo_alto_se_rechaza(sample_df):
    df = sample_df.copy()
    i = df.index[0]
    df.loc[i, "internet_service"] = "none"
    df.loc[i, "monthly_charges"] = 90.0

    with pytest.raises(pandera.errors.SchemaErrors):
        training_schema.validate(df, lazy=True)


def test_rc3_en_features_schema(sample_df):
    df = sample_df.copy()
    i = df.index[0]
    df.loc[i, "internet_service"] = "none"
    df.loc[i, "monthly_charges"] = 90.0
    df = df.drop(columns=["customer_id", "churn"])

    with pytest.raises(pandera.errors.SchemaErrors):
        features_schema.validate(df, lazy=True)


def test_rc5_columna_no_autorizada(sample_df):
    df = sample_df.copy()
    df["oferta_retencion_aceptada"] = 1

    with pytest.raises(pandera.errors.SchemaErrors):
        training_schema.validate(df, lazy=True)


def test_descarte_maximo():
    assert discard_ok({"proporcion_descartada": 0.0337})
    assert discard_ok({"proporcion_descartada": 0.05})
    assert not discard_ok({"proporcion_descartada": 0.20})


def test_hu03_categoria_fuera_del_dominio_falla_rc2(sample_df):
    """HU-03 · Dado un lote con contract_type = "Month-to-month", cuando se valida el contrato
    bloqueante, entonces la validación falla con la regla RC-2 (dominio de contract_type)."""
    lote = sample_df.drop(columns=["churn"])
    lote.loc[lote.index[0], "contract_type"] = "Month-to-month"
    
    with pytest.raises(pandera.errors.SchemaErrors) as exc:
        features_schema.validate(lote, lazy=True)
        
    fallas = exc.value.failure_cases
    rc2 = fallas[(fallas["column"] == "contract_type") & fallas["check"].astype(str).str.startswith("isin")]
    assert len(rc2) == 1, f"se esperaba una falla de RC-2 en contract_type; hubo:\n{fallas}"


def test_hu03_sin_internet_con_cargo_de_fibra_falla_rc3(sample_df):
    """HU-03 · Dado un cliente sin internet con cargo de 90, cuando se valida, falla RC-3."""
    df = sample_df.copy()
    idx = df.index[df["internet_service"] == "none"][0]
    df.loc[idx, "monthly_charges"] = 90.0
    
    with pytest.raises(pandera.errors.SchemaErrors) as exc:
        training_schema.validate(df, lazy=True)
        
    assert "RC-3" in exc.value.failure_cases["check"].astype(str).str.cat(sep=" ")