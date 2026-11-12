# Bitácora – Reto 4 · Pruebas e integración continua (versión lite)

## Tabla de trazabilidad

| HU · escenario | Archivo · prueba | Marcador | ¿Pasa? |
|---|---|---|---|
| HU-03 · categoría fuera del dominio (RC-2) | `tests/test_contract.py::test_hu03_categoria_fuera_del_dominio_falla_rc2` | — | |
| HU-03 · … y no se genera `reports/predictions/` | `tests/test_predict_batch.py::…` (bloque 3) | `model` | |
| HU-03 · sin internet con cargo de fibra (RC-3) | `tests/test_contract.py::test_hu03_sin_internet_con_cargo_de_fibra_falla_rc3` | — | |
| HU-07 · direccionalidad del contrato | `tests/test_model_behavior.py::test_direction_contract` | `model` | |
| HU-07 · direccionalidad de los tickets | `tests/test_model_behavior.py::test_direction_support_tickets` | `model` | |
| HU-07 · invariancia al identificador | `tests/test_model_behavior.py::test_invariance_to_customer_id` | `model` | |
| HU-07 · umbrales mínimos | `tests/test_model_behavior.py::test_metrics_meet_minimum_thresholds` | `model` | |

## Quality gate negociado

Variante V4 — Hogar fibra premium: `customer_value` 900, `contact_cost` 35,
`retention_success_rate` 0,30, capacidad 400 llamadas por semana.

Precisión de equilibrio: `contact_cost / (retention_success_rate × customer_value)` =
`35 / (0,30 × 900)` = **0,13**. Por debajo de ese punto, contactar a un cliente cuesta más
de lo que se espera recuperar.

### Evidencia: el modelo vigente frente al gate por defecto

Modelo vigente: regresión logística, baseline del Reto 03 (`@champion`).

| Clave del gate | Métrica | Valor actual | Mínimo por defecto | Margen |
|---|---|---|---|---|
| `min_roc_auc` | `roc_auc` | 0,8315 | 0,75 | +0,0815 |
| `min_recall` | `recall_at_eval` | 0,7680 | 0,70 | +0,0680 |
| `min_precision` | `precision_at_eval` | 0,5294 | 0,45 | +0,0794 |
| `eval_threshold` | umbral fijo de medición | — | 0,30 | — |
| `max_drop_vs_champion` | caída de `roc_auc` frente al `@champion` | — | 0,01 | — |

### Umbrales propuestos

Propuestos por el Líder/PO. **Pendiente de aprobación del comité.** Registrados en
`docs/decision_log.md`.

| Clave | Por defecto | Propuesto | Margen vs. valor actual |
|---|---|---|---|
| `eval_threshold` | 0,30 | 0,30 | sin cambio |
| `min_roc_auc` | 0,75 | 0,78 | 0,0515 |
| `min_recall` | 0,70 | 0,72 | 0,0480 |
| `min_precision` | 0,45 | 0,48 | 0,0494 |
| `max_drop_vs_champion` | 0,01 | 0,01 | sin cambio |
