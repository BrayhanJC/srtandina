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

**Opción elegida.** Margen de aproximadamente 0,05 por debajo del valor actual del
`@champion`, en las tres métricas.

**Alternativas consideradas.** Mantener los valores por defecto de la plantilla
(0,75 / 0,70 / 0,45); fijar los mínimos en el valor actual del `@champion`.

**Argumento.** Las dos alternativas fallan por extremos opuestos. Los valores por defecto
dejan una holgura de 0,07 a 0,08 sobre el modelo vigente: el gate pasa siempre y no llega a
decidir nada. Fijar los mínimos en el valor actual los vuelve tan estrictos que el próximo
reentrenamiento, aun siendo legítimo, quedaría rechazado por la variación normal entre
cortes de datos.

El peso de recall y precisión no es simétrico en V4. Perder un desertor cuesta
`retention_success_rate × customer_value` = 270; contactar a un cliente cuesta 35. Con esa
asimetría de 7,7 a 1, el recall es la métrica que más se exige. La precisión mínima se fija
en 0,48, muy por encima de la precisión de equilibrio de 0,13: a ese nivel el valor neto
esperado por llamada es `0,48 × 270 − 35` = 94,6.

`eval_threshold` se mantiene en 0,30 porque es el punto fijo con el que se comparan todas
las versiones, no una decisión de negocio. El umbral de decisión lo fija el Sponsor en el
Reto 06 (contrato §4) y no puede hacer fallar el gate.

**Límite de este argumento.** El margen de 0,05 es un criterio, no una medición: el equipo
no tiene todavía un estimado de cuánto varían sus métricas entre cortes de datos, porque no
ha reentrenado el mismo modelo con otra partición. La única dispersión observada es la de
`roc_auc` entre los tres modelos del Reto 03 (0,8315 / 0,8220 / 0,8205, unos 0,011), que
mide diferencias entre algoritmos y no entre cortes. Un margen de 0,05 es conservador frente
a esa referencia. Medirlo con dos o tres valores de `split.seed` queda como trabajo
pendiente para fundamentar el umbral con un número propio.

**¿Qué pasaría si `gate.min_recall` fuera 0,05 menor?** Con 0,67 en lugar de 0,72 el modelo
vigente seguiría pasando con holgura (`recall_at_eval` 0,7680). El efecto está del otro
lado: el modelo con regularización fuerte del escenario 2 pierde recall sin que el `roc_auc`
se mueva casi nada, y si su `recall_at_eval` degradado queda por encima de 0,67, el gate lo
deja pasar. Bajar 0,05 no vuelve el gate un poco más permisivo: lo desactiva justo frente al
fallo que existe para detectar. La cifra del modelo degradado se registra en el escenario 2.

### DT-04. ¿Con qué datos corre la CI?

**Opción elegida.** Extracto sintético generado por `scripts/extracto_sintetico.py`. El
paso *Datos del pipeline* de `.github/workflows/ci.yml` intenta primero `dvc pull` y, al
fallar, genera el extracto sintético y marca la corrida con `DATOS_SINTETICOS=1`.

**Alternativas consideradas.** Publicar las credenciales del remoto DVC como *Secrets* del
repositorio para que el runner descargue el extracto real.

**Argumento.** La alternativa no es viable con el remoto actual: `almacen` apunta a una ruta
del sistema de archivos dentro de una carpeta de Google Drive sincronizada en el equipo de
un integrante. Un runner de GitHub no puede alcanzarla, y no hay credencial que lo resuelva;
habría que migrar el remoto a un almacenamiento de red antes de que la pregunta tenga otra
respuesta.

Aun si fuera viable, el equipo elegiría el extracto sintético. El extracto del CRM contiene
datos personales de clientes, y llevarlo al runner lo expondría en registros y artefactos de
la CI, en contra de la minimización que exige la Ley 1581 y del principio del contrato
§12.1 de que el extracto no entra al repositorio.

**Qué verifica realmente la CI así.** Que el pipeline corre de principio a fin en una
máquina limpia; que el contrato rechaza lo que debe rechazar, porque las pruebas de contrato
construyen sus propios lotes y no dependen del extracto; que el modelo se comporta en la
dirección esperada; y que el gate se ejecuta y falla cuando debe.

**Qué riesgo acepta el equipo.** Un "verde engañoso": la CI no puede detectar defectos
nuevos en el extracto real, y las métricas que calcula provienen de otra distribución, de
modo que un gate en verde en la CI no demuestra que el modelo real pase el gate. El propio
workflow lo advierte en el resumen del PR y suprime la comparación con la rama base cuando
los datos son sintéticos. La contención es que el `dvc repro` y el `quality_gate` sobre el
extracto real se ejecutan localmente antes de abrir cada PR, y esa salida se registra en la
bitácora.
