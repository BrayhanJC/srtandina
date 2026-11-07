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

