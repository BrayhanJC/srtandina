"""Pruebas de comportamiento del modelo entrenado (ML Test Score).

No miden exactitud: verifican que el modelo se comporte como el negocio espera.
Se ejecutan después de `dvc repro` (marcador `model`).
"""

import json

import joblib
import pytest

from src.common import FEATURES, METRICS_PATH, MODEL_PATH, load_params
from src.synthetic import generate_customers

pytestmark = pytest.mark.model


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_PATH)


@pytest.fixture
def customer():
    return generate_customers(n=1, seed=99)[FEATURES]


def test_probabilities_are_valid(model):
    X = generate_customers(n=200, seed=5)[FEATURES]
    proba = model.predict_proba(X)[:, 1]
    assert ((proba >= 0) & (proba <= 1)).all()


def test_direction_contract(model, customer):
    """
    HU-07 · Direccionalidad del contrato. Dado un cliente 
    con contrato "two-year", cuando se cambia únicamente su 
    contrato a "month-to-month", su probabilidad de churn es 
    estrictamente mayor.
    """
    monthly, two_year = customer.copy(), customer.copy()
    monthly["contract_type"] = "month-to-month"
    two_year["contract_type"] = "two-year"
    assert model.predict_proba(monthly)[0, 1] > model.predict_proba(two_year)[0, 1]


def test_direction_support_tickets(model, customer):
    """
    HU-07 · Direccionalidad de los tickets. Dado un cliente 
    cualquiera, cuando sus support_tickets pasan de 0 a 8 
    sin cambiar nada más, su probabilidad no disminuye.
    """
    few, many = customer.copy(), customer.copy()
    few["support_tickets"], many["support_tickets"] = 0, 8
    assert model.predict_proba(many)[0, 1] >= model.predict_proba(few)[0, 1]


def test_invariance_to_customer_id(model):
    """Invariancia: el identificador del cliente no debe influir en la predicción."""
    df = generate_customers(n=20, seed=8)
    renamed = df.copy()
    renamed["customer_id"] = "OTRO-ID"
    assert (model.predict_proba(df[FEATURES]) == model.predict_proba(renamed[FEATURES])).all()


def test_metrics_meet_minimum_thresholds():
    """HU-07 · Escenario: umbrales mínimos. Dado el modelo candidato, cuando se evalúa sobre el
    conjunto de prueba, entonces roc_auc, recall y precision superan los valores de gate.*."""
    metrics = json.loads(METRICS_PATH.read_text())
    gate = load_params()["gate"]  # los MISMOS valores que aplica scripts/quality_gate.py
    reglas = {
        "roc_auc": "min_roc_auc",
        "recall_at_eval": "min_recall",
        "precision_at_eval": "min_precision",
    }
    for metrica, clave in reglas.items():
        valor, minimo = metrics[metrica], gate[clave]
        assert valor >= minimo, f"{metrica}={valor} < gate.{clave}={minimo}"
