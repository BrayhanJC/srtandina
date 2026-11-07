# Bitácora – Reto 03 · Reproducibilidad y versionado (versión lite)


**Variante:** V4 – Hogar fibra premium  
**Fecha de actualización:** 2026-11-06  
**Etiquetas de entrega:** `baseline` (**pendiente**) · `r03`
**Rama de trabajo:** `reto03`  


## 1. Descripción del reto

Hasta el Reto 02, el pipeline de la plantilla entrenaba con datos **sintéticos** (etapa `ingest`), y la limpieza y el contrato de datos eran scripts sueltos que alguien debía acordarse de correr antes. Este reto convierte el SRT en **un modelo que cualquiera reconstruye** y en **una versión `@champion` a la cual volver**:

## 2. Bloque 1 · Pipeline del SRT: del extracto al modelo

### 2.1. Cambios realizados

| Paso | Cambio | Archivo(s) |
|---|---|---|
| 1 | Estado conocido: `git switch reto03`, `uv sync --frozen`, pruebas `-m "not model"` en verde | — |
| 3 | Se retira la etapa sintética con `dvc remove ingest` y se borra la salida `data/raw/churn.csv`. Se conservan `src/ingest.py`, `src/synthetic.py` y la clave `data` de `params.yaml` (contrato §7.1) | `dvc.yaml`, `dvc.lock`, `data/raw/.gitignore` |
| 4 | `prepare` lee el conjunto limpio (`CLEAN_DATA`) en lugar del crudo (`RAW_DATA`) | `src/prepare.py` |
| 5 | `validate` reescrita: aplica las tres partes del contrato v2 y guarda solo conteos por regla, sin `customer_id` | `src/validate.py` |
| 6 | Se declaran las etapas `clean`, `validate` y `prepare`; `train` y `evaluate` no cambian | `dvc.yaml` |

**Partes del contrato v2 que aplica `validate`:**

| Parte del contrato | Archivo evaluado | Si falla |
|---|---|---|
| `training_schema` (RC-1 a RC-5) | `data/processed/clean.csv` | **Bloquea**: no se entrena |
| `discard_ok` (descarte máximo 5 %) | `reports/cleaning.json` | **Bloquea** |
| `warnings_schema` | `data/raw/crm_extracto.csv` | Se registra y se reporta al dueño del dato |

### 2.2. Ejecución completa (`uv run dvc repro --force`)

**Ejecutó:** Jorge Andrés Ángel · **Sistema operativo:** macOS · **Fecha:** 2026-11-06  
**Registro MLflow:** se creó desde cero (`Creating initial MLflow database tables`), así que no quedó ningún `@champion` sintético del Reto 00.

| Etapa | Resultado |
|---|---|
| `clean` | 7.042 → 6.805 filas (**3,4 % descartado**; máximo permitido 5 %) |
| `validate` | ✅ **contrato v2 OK**, con 2 advertencias (ver tabla siguiente) |
| `prepare` | train = 5.444 · test = 1.361 (80/20, semilla 42) |
| `train` | `logistic_regression` registrado como `gpad-churn-model` **v1** (`@challenger`) |
| `evaluate` | Métricas en la sección 2.3 |

**Advertencias del extracto crudo**:

| Regla de advertencia | Filas | Tratamiento |
|---|---:|---|
| `fecha_alta` vacía | 28 | Columna no canónica, excluida por `clean` (la antigüedad ya está en `tenure_months`) |
| `fecha_alta` posterior a `fecha_corte` | 20 | Ídem; se reporta a la Jefatura de CRM y Facturación |

### 2.3. Métricas del baseline (regresión logística, v1)

**Calidad del modelo frente al quality gate** (umbral fijo `gate.eval_threshold = 0.30`):

| Métrica | Valor | Mínimo `gate.*` | ¿Cumple? |
|---|---:|---:|:---:|
| `roc_auc` | 0,8315 | 0,75 | ✅ |
| `recall_at_eval` | 0,7680 | 0,70 | ✅ |
| `precision_at_eval` | 0,5294 | 0,45 | ✅ |

**Métricas al umbral de decisión provisional** (`model.decision_threshold = 0.35`, a ratificar en el Reto 06):

| Métrica | Valor | Lectura |
|---|---:|---|
| `pr_auc` | 0,6484 | Calidad del ranking sobre la clase minoritaria (churn) |
| `precision` | 0,5738 | De cada 100 clientes señalados, ~57 sí se van |
| `recall` | 0,7253 | El modelo encuentra ~73 % de los clientes que se van |
| `f1` | 0,6408 | Balance entre precisión y recall |

**Equidad (política de la variante V4):**

| Métrica | Valor | Máximo permitido (`fairness.max_recall_gap_senior_citizen`) | ¿Cumple? |
|---|---:|---:|:---:|
| `recall_gap_senior_citizen` | 0,0821 | 0,10 | ✅ |

**Negocio** (miles de COP, sobre las 1.361 filas de prueba):

| Métrica | Valor | Lectura |
|---|---:|---|
| `customers_contacted` | 474 | Clientes que la campaña contactaría con el umbral 0,35 |
| `net_savings_model` | 56.850 | Ahorro neto estimado de la campaña dirigida por el modelo (≈ $56,9 M) |
| `net_savings_random` | 18.672,67 | Ahorro si se contactara a la misma cantidad de clientes al azar (≈ $18,7 M) |
| `net_savings_vs_random` | **38.177,33** | **Valor que aporta el modelo frente a no tenerlo (≈ $38,2 M)** |

> **Observación para la decisión de modelo.** Los 474 contactos no están limitados por la capacidad del call center (`business.weekly_capacity = 400` llamadas por semana). Llevada a la escala del conjunto de prueba, esa capacidad es bastante menor que 474. El umbral definitivo se fija en el Reto 06, pero se deja constancia en `docs/decision_log.md`.

## 3. Quién hizo qué

| Integrante | Rol | Aporte en el Reto 03 |
|---|---|---|
| Jorge Andrés Ángel | Líder / PO | Ejecución completa del pipeline (Bloque 1) · _completar_ |
| Juan Camilo Zuluaga Serna | DS / Steward | _completar_ |
| Brayhan Andrés Jaramillo Castaño | ML / MLOps Engineer | Cambios del Bloque 1 (`dvc.yaml`, `src/validate.py`, `src/prepare.py`) · _completar_ |

## 4. Tabla modelos

## Tres corridas y decisión de modelo

Experimento controlado: mismo extracto limpio, misma partición (`split.seed = 42`), mismo entorno (`uv.lock`). Solo cambia `model.type`.

| Corrida (run_id) | Modelo | roc_auc | recall | precision | recall_gap_senior_citizen | customers_contacted | net_savings_vs_random | ¿Pasa el gate? |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `<run_id baseline>` | logistic_regression (baseline, `@champion`) | 0,8315 | 0,7253 | 0,5738 | 0,0821 | 474 | 38.177,33 | ✅ Sí |
| `418dab6648b84cc0b505647bbb26a449` | random_forest | 0,8205 | 0,6747 | 0,5573 | 0,0667 | 454 | 34.535,20 | ❌ No (roc_auc 0,8205 < 0,8215, no regresión) |
| `fc9cd78b0c7c45da843fc9161c52de01` | gradient_boosting | 0,8220 | 0,6827 | 0,5714 | 0,0952 | 448 | 35.791,57 | ✅ Sí (margen 0,0005) |

### Detalle del quality gate

Umbrales de `params.yaml → gate.*`. `recall_at_eval` y `precision_at_eval` se miden al umbral fijo `gate.eval_threshold = 0.30`. La no regresión exige `roc_auc ≥ roc_auc del @champion − 0,01 = 0,8315 − 0,01 = 0,8215`.

| Modelo | roc_auc ≥ 0,75 | recall_at_eval ≥ 0,70 | precision_at_eval ≥ 0,45 | roc_auc ≥ 0,8215 (no regresión) | Resultado |
|---|:---:|:---:|:---:|:---:|:---:|
| logistic_regression | ✅ 0,8315 | ✅ 0,7680 | ✅ 0,5294 | ✅ sin champion previo | ✅ Pasa |
| random_forest | ✅ 0,8205 | ✅ 0,7627 | ✅ 0,5062 | ❌ 0,8205 | ❌ No pasa |
| gradient_boosting | ✅ 0,8220 | ✅ 0,7413 | ✅ 0,5245 | ✅ 0,8220 | ✅ Pasa |

### Lectura de las columnas no técnicas

| Columna | Referencia de la variante V4 | Lectura |
|---|---|---|
| `recall_gap_senior_citizen` | Brecha máxima 0,10 (`fairness.max_recall_gap_senior_citizen`) | Los tres cumplen. Random forest es el más equitativo (0,0667); gradient boosting queda cerca del límite (0,0952). |
| `customers_contacted` | Capacidad de 400 llamadas por semana; en la escala del conjunto de prueba (1.361 de 6.805 clientes, 20 %) son ≈ 80 | Los tres contactan entre 448 y 474, muy por encima de la capacidad. Se debe al umbral provisional 0,35; se ajusta en el Reto 06. |
| `net_savings_vs_random` | Ahorro frente a llamar al azar a la misma cantidad de clientes (miles de COP) | La logística aporta ≈ $2,4 M más que gradient boosting y ≈ $3,6 M más que random forest. |

