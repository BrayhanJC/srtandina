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

### Variabilidad entre semillas de partición

Reentrenamiento del mismo modelo cambiando solo `split.seed` (`dvc exp run -S split.seed=…`).
Salida completa en `reports/semillas.csv`.

| `split.seed` | `roc_auc` | `recall_at_eval` | `precision_at_eval` | `recall_gap_senior_citizen` |
|---|---|---|---|---|
| 42 | 0,8315 | 0,7680 | 0,5294 | 0,0821 |
| 7 | 0,8258 | 0,7733 | 0,5390 | 0,0167 |
| 123 | 0,8304 | 0,7360 | 0,5257 | 0,0296 |
| 2031 | 0,8316 | 0,7493 | 0,5425 | 0,0773 |
| **Peor valor** | **0,8258** | **0,7360** | **0,5257** | — |
| **Dispersión** | 0,0058 | 0,0373 | 0,0168 | — |

Caída máxima de `roc_auc` frente al `@champion` (0,8315) entre semillas: **0,0057**.

### Umbrales aprobados

Aprobados por el comité el 2026-11-11. Registrados en `docs/decision_log.md`.

| Clave | Por defecto | Aprobado | Peor semilla | Margen |
|---|---|---|---|---|
| `eval_threshold` | 0,30 | 0,30 | — | sin cambio |
| `min_roc_auc` | 0,75 | 0,78 | 0,8258 | 0,0458 |
| `min_recall` | 0,70 | 0,70 | 0,7360 | 0,0360 |
| `min_precision` | 0,45 | 0,48 | 0,5257 | 0,0457 |
| `max_drop_vs_champion` | 0,01 | 0,020 | caída máx. 0,0057 | 0,0143 |

## Escenarios de rechazo

| Escenario | Enlace al PR | Paso que falló | Tiempo hasta detectar | Decisión |
|---|---|---|---|---|
| 1 · contrato relajado | #26 | Pruebas unitarias y de contrato de datos | 7 s | Cerrado sin fusionar |
| 2 · modelo degradado (`C` = 0.0002) | #28 | Quality gate | 38 s | Cerrado sin fusionar |

### Escenario 2: dos intentos

El primer intento (`model.logistic_regression.C` = 0.0005) **pasó el gate**. Se repitió con
una regularización más fuerte (`C` = 0.0002), que es la corrida registrada en el PR #28.

| | `@champion` | `C` = 0.0005 | `C` = 0.0002 | Mínimo del gate |
|---|---|---|---|---|
| `roc_auc` | 0,8315 | 0,8075 | 0,8015 | 0,78 |
| `recall_at_eval` | 0,7680 | 0,7067 | **0,5920** | 0,70 |
| `precision_at_eval` | 0,5294 | 0,5176 | 0,5522 | 0,48 |
| `recall_gap_senior_citizen` | 0,0821 | 0,0784 | 0,1227 | 0,10 (política de V4, fuera del gate) |
| Resultado del gate | — | aprobado, código 0 | **rechazado, código 1** | — |

Caída de `roc_auc` frente al `@champion`: 0,0240 con `C` = 0.0005 y 0,0300 con `C` = 0.0002.
La regla `max_drop_vs_champion` (0,020) no se evaluó en ninguno de los dos intentos: el
registro de MLflow no tiene el alias `@champion` y el gate reporta `sin champion previo`.
En la CI esa regla tampoco aplica, porque el registro del runner está vacío.

**Qué significa que el gate acordado no detuviera el primer intento.** El gate midió bien:
`recall_at_eval` 0,7067 supera el mínimo de 0,70, y la aritmética es correcta. El problema
no está en la regla sino en dónde quedó el mínimo, y la razón es estructural. El mínimo se
fijó en 0,70 para absorber la variabilidad entre cortes de datos, que medimos en 0,0373.
Pero ese mismo espacio es donde cabe una degradación real: entre la peor semilla legítima
(0,7360) y el modelo con `C` = 0.0005 (0,7067) hay apenas 0,024. Una sola métrica con un
piso absoluto no puede separar ruido de deterioro cuando ambos tienen el mismo orden de
magnitud.

La regla que sí los distingue es `max_drop_vs_champion`, porque compara contra el modelo
vigente en lugar de contra un piso fijo: la caída de 0,0240 del primer intento supera el
0,020 acordado. No se evaluó porque el alias `@champion` no está en el registro, y en la CI
nunca se evalúa porque el registro del runner está vacío. De ahí se sigue que la CI es
estructuralmente más permisiva que una verificación local completa: allá el único blindaje
son los mínimos absolutos, que son justamente los que este caso atravesó.

El segundo intento deja un hallazgo adicional: con `C` = 0.0002 la brecha de recall en
`senior_citizen` sube a 0,1227, por encima del límite de 0,10 que fija V4, y el gate la
aprueba porque no tiene ninguna regla de equidad. Un modelo puede incumplir la política de
equidad del contrato y pasar el gate sin que nadie se entere.
