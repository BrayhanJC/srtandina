# Plantilla del SRT – Gerencia de Proyectos de Analítica de Datos (curso por retos)

Repositorio base del **Sistema de Retención Temprana (SRT)** de Conecta Andina S.A., el sistema que
cada equipo construye a lo largo de los **Retos 00–07** y defiende en el **Proyecto Final**
(Maestría en Ingeniería – Universidad del Quindío). Nombres, claves y convenciones siguen el
*contrato del sistema* del curso.

> Esta es la plantilla de la **versión por retos**. La del curso 2026 por entregas sigue en
> `gpad-mlops-template` y no cambia.

Implementa de punta a punta el ciclo de vida de un modelo de **deserción de clientes (churn)**:
datos versionados → contrato de datos → entrenamiento registrado → quality gate → API en Docker → monitoreo de drift → runbook.

Funciona sin descargar nada: los datos se generan sintéticamente (imitando *Telco Customer Churn*).
En el **Reto 02** el equipo recibe el extracto CRM de su variante y en el **Reto 03** reemplaza la
etapa sintética `ingest` por `clean → validate` sobre ese extracto.

| Capacidad | Herramienta | Dónde |
|---|---|---|
| Entorno reproducible | **uv** (`pyproject.toml` + `uv.lock`) | raíz |
| Versionado de datos y pipeline | **DVC** | `dvc.yaml`, `params.yaml`, `dvc.lock` |
| Contrato de datos | **Pandera** | `contracts/` |
| Experimentos y registro de modelos | **MLflow 3** (aliases `@challenger`, `@champion`, `@previous`) | `src/train.py`, `scripts/promote.py` |
| Pruebas | **pytest** (contrato, unitarias, comportamiento del modelo, API) | `tests/` |
| Integración continua | **GitHub Actions** (+ release a GHCR opcional) | `.github/workflows/` |
| Servicio | **FastAPI** + **Docker** | `app/`, `Dockerfile` |
| Monitoreo | **Evidently** (drift), **Prometheus** + **Grafana** (operación) | `monitoring/`, `docker-compose.yml` |
| Asistente de explicación (LLMOps) | **Ollama** (local) o **Claude API**, prompt versionado, guardrails y evaluación | `src/llm_assistant.py`, `src/llm_eval.py`, `prompts/` |
| Documentación de gestión | Charter, gobernanza, model card, runbook, decisiones, post-mortem | `docs/` |

---

## 1. Inicio rápido (5 comandos)

Requisitos: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) y, para la parte de servicio, Docker Desktop.

```bash
git clone <url-de-su-repositorio> && cd <repositorio>
uv sync                                   # crea .venv con Python 3.12 y las versiones exactas de uv.lock
uv run python -m scripts.verificar_entorno   # ¿está todo listo? (Reto P – Preparación del entorno)
uv run dvc repro                          # ingest → validate → prepare → train → evaluate
uv run python -m scripts.promote          # quality gate y promoción a @champion
uv run pytest                             # 29 pruebas
```

> ¿Sin uv? `python -m venv .venv`, active el entorno, `pip install -r requirements.txt` y ejecute los
> mismos comandos sin el prefijo `uv run`.

## 2. El pipeline

```
ingest ──► validate ──► prepare ──► train ──► evaluate
(datos)   (contrato)   (train/test) (MLflow)  (métricas, equidad, impacto)
```

```bash
uv run dvc dag                 # ver el grafo
uv run dvc repro               # re-ejecuta solo lo que cambió
uv run dvc metrics show        # métricas actuales
uv run dvc params diff         # qué parámetros cambiaron vs. el último commit
uv run dvc metrics diff main   # comparar con otra rama o tag
```

Experimente cambiando `params.yaml` (por ejemplo `model.type: random_forest`) y vuelva a ejecutar `dvc repro`.

### Métricas que produce `evaluate` (`metrics.json`)
- **Técnicas:** `roc_auc`, `pr_auc`, `precision`, `recall`, `f1` (con el umbral de decisión `model.decision_threshold`).
- **Calidad para el gate:** `recall_at_eval`, `precision_at_eval` (al umbral fijo `gate.eval_threshold`).
- **Equidad:** `recall_gap_senior_citizen` (diferencia de recall entre grupos).
- **Negocio (estimado):** ahorro neto de la campaña de retención vs. contactar al azar (`business` en `params.yaml`).

## 3. MLflow: experimentos y registro de modelos

Por defecto MLflow guarda todo en `mlflow.db` (local, ignorado por Git).

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5050   # http://localhost:5050
```

Ciclo de vida con **aliases** (MLflow 3 ya no usa *stages*):

| Alias | Significado | Quién lo asigna |
|---|---|---|
| `@challenger` | último modelo entrenado | `src/train.py` |
| `@champion` | modelo aprobado para producción | `scripts/promote.py` (solo si pasa el quality gate) |
| `@previous` | champion anterior, para rollback | `scripts/promote.py` |

> **El gate juzga el modelo, no la decisión.** Recall y precisión del gate se miden al umbral fijo
> `gate.eval_threshold` (0.30), igual para todas las versiones. El umbral de decisión
> (`model.decision_threshold`) lo fija el Sponsor según la capacidad del call center y la equidad
> (Reto 06): moverlo cambia a quién se llama, no si el modelo es bueno.

```bash
uv run python -m scripts.quality_gate        # solo evaluar (reports/gate.json)
uv run python -m scripts.promote             # gate + promoción
uv run python -m scripts.promote --rollback  # volver al champion anterior
```

**Trabajo en equipo:** levante el servidor compartido (`docker compose up -d mlflow`) y registre allí:
`export MLFLOW_TRACKING_URI=http://localhost:5001` (en Windows PowerShell: `$env:MLFLOW_TRACKING_URI="http://localhost:5001"`).
Se usa el puerto 5001 porque en macOS el 5000 está ocupado por AirPlay Receiver.

## 4. Pruebas y CI

```bash
uv run pytest -m "not model"   # contrato y unitarias (no requieren modelo)
uv run pytest -m model         # comportamiento del modelo y API (después de dvc repro)
uv run ruff check .            # estilo
uv run pre-commit install      # verificaciones automáticas en cada commit
```

El workflow `.github/workflows/ci.yml` corre en cada push y pull request: lint → pruebas → `dvc repro` →
quality gate → pruebas del modelo → monitoreo de humo → imagen Docker + prueba de humo.
En los pull requests publica en el resumen del job la **diferencia de métricas y parámetros** con la rama base.

> **Datos en la CI.** Desde el Reto 03 el pipeline lee `data/raw/crm_extracto.csv`. Si el runner no
> puede leer el remoto DVC del equipo, la CI genera un extracto sintético sin defectos con el mismo
> esquema (`scripts/extracto_sintetico.py`): verifica que el pipeline funcione, no la calidad del modelo
> real. Para usar el extracto real en la CI, configure un remoto en la nube y sus credenciales en
> *Secrets* (decisión del Reto 04).
>
> El quality gate en CI solo aplica umbrales absolutos (el registro de MLflow del runner es temporal).
> La comparación contra `@champion` se hace al promover desde el servidor MLflow del equipo.

## 5. Servicio (API) y stack de operación

```bash
uv run uvicorn app.main:app --reload       # API local: http://localhost:8000/docs
cp .env.example .env                       # una sola vez: defina la clave de Grafana (nunca en Git)
docker compose up -d --build               # API + MLflow + Prometheus + Grafana
docker compose down
```

| Servicio | URL |
|---|---|
| API (Swagger) | http://localhost:8000/docs |
| MLflow | http://localhost:5001 |
| Prometheus | http://localhost:9090 |
| Grafana (usuario y clave de `.env`) | http://localhost:3000 → tablero *GPAD – Operación del modelo* |

Endpoints: `GET /health` (versión servida), `POST /predict`, `GET /metrics`.
En el stack Docker cada predicción se guarda en `data/production/predictions.csv` (insumo de monitoreo).

## 6. Monitoreo y simulacro de incidente

```bash
uv run python -m monitoring.make_production_batch --list                 # escenarios
uv run python -m monitoring.make_production_batch --scenario precios     # lote con drift
uv run python -m monitoring.drift_report data/production/batch_precios.csv
uv run python -m monitoring.send_traffic data/production/batch_precios.csv   # tráfico hacia la API
```

| Escenario | Qué simula | Qué lo detecta |
|---|---|---|
| `normal` | mismo proceso del entrenamiento | nada (OK) |
| `precios` | alza de tarifas y migración a fibra | drift de datos (Evidently) |
| `contratos` | captación masiva de clientes nuevos | drift de datos (Evidently) |
| `concepto` | un competidor cambia la relación X → churn (`--with-labels`) | **solo** la caída de desempeño |
| `esquema` | columna renombrada y categoría nueva | contrato de datos (CRÍTICO) |

`drift_report` devuelve código 0 (OK), 1 (ALERTA) o 2 (CRÍTICO). La respuesta a cada nivel está en `docs/runbook.md`.

## 7. Impacto, equidad y explicabilidad (insumos de la model card)

```bash
uv run python -m src.business_analysis                       # ahorro por umbral + sensibilidad a supuestos
uv run python -m src.fairness_report                         # métricas y brechas por grupo (senior_citizen)
uv run python -m src.fairness_report --group internet_service
uv run python -m src.fairness_report --thresholds 0=0.30,1=0.40   # mitigación: umbral por grupo
uv run python -m src.explain                                 # importancia por permutación + coeficientes
```

Resultados en `reports/business/`, `reports/fairness/` y `reports/explain/`: cítelos en `docs/model_card.md`.

## 8. Asistente de explicación con LLM (Reto 07)

Convierte cada predicción en una explicación en lenguaje natural para quien toma la decisión,
con prompt versionado, guardrails, respaldo determinista y evaluación con *quality gate*.
Detalle y riesgos: [`docs/asistente_llm.md`](docs/asistente_llm.md).

```bash
uv run python -m src.llm_assistant --row 0                     # una explicación (proveedor de params.yaml)
uv run python -m src.llm_eval                                   # evaluación + gate + registro en MLflow
uv run python -m src.llm_eval --provider ollama                 # LLM local (ollama pull qwen3:4b)
uv run python -m src.llm_eval --provider anthropic              # Claude API (requiere ANTHROPIC_API_KEY)
```

| Proveedor | Uso | Costo |
|---|---|---|
| `mock` | CI, pruebas y clase sin red (respuesta determinista) | 0 |
| `ollama` | LLM local: los datos no salen del computador | 0 (cómputo propio) |
| `anthropic` | Claude API (`claude-opus-5-5`) | por tokens (`price_per_mtok` en `params.yaml`) |

> La clave de API se lee de la variable de entorno `ANTHROPIC_API_KEY`: **nunca** la escriba en el código,
> en `params.yaml` ni en un *commit* (`.env` está en `.gitignore`).

## 9. Ruta por retos

| Reto | Qué cambia en este repositorio | Tag |
|---|---|---|
| 00 | `params.yaml → business.*` y `business.weekly_capacity` con su variante; `docs/charter.md` §1–5; `docs/decision_log.md` | `r00` |
| 01 | `docs/charter.md` §6–8; `docs/riesgos.md` | `r01` |
| 02 | `dvc add data/raw/crm_extracto.csv`; `contracts/` (v1, v2 bloqueante con RC-1…RC-5, advertencias); `src/clean.py`; `tests/test_contract.py`; `docs/datos_gobernanza.md` | `r02` |
| 03 | `dvc remove ingest`; grafo `clean → validate → prepare → train → evaluate`; remoto DVC; ≥ 3 corridas; aliases; tag `baseline` | `r03` |
| 04 | Pruebas de comportamiento desde las historias; gate negociado; `main` protegida; `src/predict_batch.py` + pruebas | `r04` |
| 05 | `monitoring/prometheus/alerts.yml`; RC-3 en la API; `docs/runbook.md`; rollback cronometrado | `r05` |
| 06 | `model.decision_threshold` aprobado; `fairness.max_recall_gap_senior_citizen`; `reports/business/`, `reports/fairness/`, `reports/explain/`; `docs/model_card.md` | `r06` |
| 07 | `src/llm_assistant.py`, `prompts/explicacion_v2.md`, `reports/llm_eval.json`, `docs/asistente_llm.md` | `r07` |
| S8 | `docs/postmortem.md`, `docs/informe_final.md` | `final` |

Cada reto deja su bitácora en `docs/bitacora/reto-NN.md` (plantilla en `docs/bitacora/plantilla.md`).

> Algunas pruebas de la plantilla son deliberadamente débiles (por ejemplo, la invariancia al
> `customer_id`) y los guardrails del asistente no cubren todo: los retos piden mejorarlas. No es un
> descuido: es material de trabajo.

## 10. Estructura

```
├── app/                    API FastAPI
├── contracts/              contrato de datos (Pandera)
├── data/                   raw/ y processed/ (DVC) · production/ (lotes y log de predicciones)
├── docs/                   charter, riesgos, decisiones, gobernanza, runbook, model card, asistente, post-mortem, informe final, bitacora/
├── models/                 model.joblib (DVC) + model_meta.json (trazabilidad)
├── prompts/                prompts versionados del asistente LLM
├── monitoring/             drift (Evidently), lotes simulados, tráfico, Prometheus, Grafana, MLflow server
├── reports/                validación, curva ROC, matriz de confusión, gate, drift
├── scripts/                quality gate, promoción y rollback
├── src/                    etapas del pipeline
├── tests/                  pytest
├── dvc.yaml  params.yaml   pipeline y parámetros
├── Dockerfile  docker-compose.yml
└── pyproject.toml  uv.lock  requirements.txt
```
