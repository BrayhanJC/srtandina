# Bitácora – Reto 4 · Pruebas e integración continua (versión lite)

## Tabla de trazabilidad

Cada escenario de HU-03 y HU-07 (*Historias y casos de uso*, §4) tiene al menos una prueba
automática que lo cita en su docstring.

| HU · escenario | Archivo · prueba | Marcador | ¿Pasa? |
|---|---|---|---|
| HU-03 · categoría fuera del dominio (RC-2) | `tests/test_contract.py::test_hu03_categoria_fuera_del_dominio_falla_rc2` | — | ✅ |
| HU-03 · … y no se genera `reports/predictions/` | `tests/test_predict_batch.py::…` | `model` | ⏳ bloque 3 |
| HU-03 · sin internet con cargo de fibra (RC-3) | `tests/test_contract.py::test_hu03_sin_internet_con_cargo_de_fibra_falla_rc3` | — | ✅ |
| HU-07 · direccionalidad del contrato | `tests/test_model_behavior.py::test_direction_contract` | `model` | ✅ |
| HU-07 · direccionalidad de los tickets | `tests/test_model_behavior.py::test_direction_support_tickets` | `model` | ✅ |
| HU-07 · invariancia al identificador | `tests/test_model_behavior.py::test_invariance_to_customer_id` | `model` | ✅ |
| HU-07 · umbrales mínimos | `tests/test_model_behavior.py::test_metrics_meet_minimum_thresholds` | `model` | ✅ |
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

## Decisiones técnicas requeridas

### DT-03. Umbrales del gate: ¿ajustados al modelo actual o con margen?

**Opción elegida.** Margen uniforme de aproximadamente 0,05 por debajo del valor actual en
las tres métricas.

**Alternativas consideradas.** Mantener los valores por defecto de la plantilla
(0,75 / 0,70 / 0,45); fijar los mínimos en el valor actual del `@champion`.

**Argumento.** Las dos alternativas fallan por extremos opuestos. Los valores por defecto
dejan una holgura de 0,07 a 0,08 sobre el modelo vigente: el gate pasa siempre y no decide
nada. Fijar los mínimos en el valor actual los vuelve tan estrictos que el próximo
reentrenamiento, aun siendo legítimo, sería rechazado por la variación normal entre cortes
de datos. El margen de ~0,05 absorbe ese ruido sin que el gate deje de discriminar.

El peso de recall y precisión no es simétrico. Perder un desertor cuesta
`retention_success_rate × customer_value` = 270; contactar a un cliente cuesta 35. Con esa
asimetría de 7,7 a 1, en V4 el recall es la métrica que más se exige. La precisión se fija
en 0,48, muy por encima del equilibrio de 0,13: a ese nivel el valor neto esperado por
llamada es `0,48 × 270 − 35` = 94,6.

`eval_threshold` se mantiene en 0,30 porque es el punto fijo con el que se comparan todas
las versiones, no una decisión de negocio. El umbral de decisión lo fija el Sponsor en el
Reto 06 (contrato §4) y no puede hacer fallar el gate.

**¿Qué pasaría si `gate.min_recall` fuera 0,05 menor?** Con 0,67 en lugar de 0,72, el modelo
vigente seguiría pasando con holgura (`recall_at_eval` 0,7680). El problema está del otro
lado: el modelo con regularización fuerte del escenario 2 pierde recall sin que el `roc_auc`
se mueva casi nada, y con el gate en 0,67 **también pasaría**. Bajar 0,05 no vuelve el gate
un poco más permisivo: lo desactiva justo frente al fallo que existe para detectar. La cifra
exacta del modelo degradado se registra en el escenario 2 del bloque 2.
