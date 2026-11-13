"""Pruebas del batch del lunes (Reto 04), derivadas de HU-08 y HU-03."""

import json

import joblib
import pandas as pd
import pytest

from src.common import MODEL_META, MODEL_PATH
from src.predict_batch import main, prioritize, score
from src.synthetic import generate_customers

pytestmark = pytest.mark.model


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def meta():
    return json.loads(MODEL_META.read_text())


def test_hu08_lista_respeta_capacidad_orden_y_version(model, meta):
    """HU-08 · La lista tiene como máximo la capacidad, en orden descendente, con la versión."""
    lote = generate_customers(n=400, seed=11).drop(columns=["churn"])
    lista = prioritize(score(lote, model, meta), capacity=50)
    assert len(lista) == 50
    assert lista["churn_probability"].is_monotonic_decreasing
    assert lista["model_version"].notna().all()


def test_hu08_cada_fila_de_la_lista_indica_la_version(tmp_path):
    """HU-08 · Y cada fila indica la versión del modelo que la produjo (solo cuatro columnas)."""
    ruta = tmp_path / "lote_ok.csv"
    generate_customers(n=300, seed=13).drop(columns=["churn"]).to_csv(ruta, index=False)

    assert main([str(ruta), "--out-dir", str(tmp_path), "--capacity", "40"]) == 0

    lista = pd.read_csv(tmp_path / "predictions" / "lote_ok_lista.csv")
    assert list(lista.columns) == ["prioridad", "customer_id", "churn_probability", "model_version"]
    assert lista["model_version"].notna().all()


def test_hu03_lote_invalido_no_genera_predicciones(tmp_path):
    """HU-03 · Dado un lote con "Month-to-month", entonces código 2, no se genera
    reports/predictions/ para ese lote y sí queda el registro del rechazo."""
    lote = generate_customers(n=50, seed=12).drop(columns=["churn"])
    lote.loc[lote.index[0], "contract_type"] = "Month-to-month"
    ruta = tmp_path / "lote_hu03.csv"
    lote.to_csv(ruta, index=False)

    assert main([str(ruta), "--out-dir", str(tmp_path)]) == 2

    assert not list(tmp_path.glob("predictions/lote_hu03*"))
    registro = json.loads((tmp_path / "rejected" / "lote_hu03.json").read_text())
    assert registro["nivel"] == "CRÍTICO-CONTRATO"
    assert lote.loc[lote.index[0], "customer_id"] not in json.dumps(registro)
