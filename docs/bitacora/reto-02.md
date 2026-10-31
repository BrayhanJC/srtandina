# Bitácora – Reto 02 · Gobierno y contrato de datos (versión lite)

**Asignatura:** Gerencia de Proyectos de Analítica de Datos · Maestría en Ingeniería · Universidad del Quindío  
**Proyecto:** Sistema de Retención Temprana (SRT) – Conecta Andina S. A.  
**Equipo:** Jorge Andrés Ángel · Juan Camilo Zuluaga Serna · Brayhan Andrés Jaramillo Castaño  
**Variante:** V4 – Hogar fibra premium  
**Fecha de actualización:** 2026-10-31  
**Etiqueta de entrega prevista:** `r02` (**pendiente de confirmar publicación**)  
**Repositorio:** https://github.com/BrayhanJC/srtandina

> **Estado de esta bitácora.** Las cifras del perfil, los acuerdos de negociación y las salidas de limpieza y validación proceden de la documentación y las ejecuciones compartidas por el equipo. Las once pruebas automatizadas están aprobadas. Se señalan expresamente como **PENDIENTES DE EVIDENCIA** las comprobaciones cuyo resultado aún no ha sido suministrado: PS-1, prueba de mutación de RC-3 de PS-3, PS-4, PS-5 y publicación de `r02`. No se inventan salidas de consola, aprobaciones ni aportes individuales.

## 1. Contexto y alcance

El reto convierte el extracto CRM-RET de la variante V4 en una fuente gobernada: se perfila su calidad, se documenta la brecha respecto del contrato canónico, se aplican tratamientos negociados con la Jefatura de CRM y Facturación y se verifica un **contrato v2 bloqueante** separado de las **advertencias**. La limpieza produce únicamente las nueve columnas canónicas, evita incluir la variable con fuga en el modelo y registra conteos agregados sin identificadores de clientes.

**Extracto:** `data/raw/crm_extracto.csv`, registrado mediante DVC según la ficha de datos del equipo.  
**Volumen original:** 7.042 filas y 13 columnas.  
**Corte declarado:** 2026-09-30.  
**Salida de limpieza:** `data/processed/clean.csv`, con 6.805 filas y 9 columnas.  
**Reporte agregado:** `reports/cleaning.json`.

Las columnas canónicas son: `customer_id`, `tenure_months`, `contract_type`, `internet_service`, `payment_method`, `monthly_charges`, `support_tickets`, `senior_citizen` y `churn`. Las no canónicas son `region`, `fecha_alta`, `fecha_corte` y `oferta_retencion_aceptada`.

## 2. Perfil de calidad y brecha frente al contrato canónico

### 2.1. Perfil cuantitativo

Los porcentajes se calcularon sobre las **7.042 filas** del extracto original.

| Dimensión | Hallazgo | Filas afectadas | Porcentaje / observación |
|---|---|---:|---|
| Completitud | `monthly_charges` vacío | 56 | 0,80 % |
| Completitud | `fecha_alta` vacía | 28 | 0,40 %; coincide con las filas de `tenure_months = -1` |
| Validez | `contract_type = Month-to-month` | 194 | 2,75 % |
| Validez | `payment_method = tarjeta_debito` | 81 | 1,15 % |
| Validez | `tenure_months = -1` | 28 | 0,40 % |
| Validez | `support_tickets = 99` | 13 | 0,18 % |
| Unicidad | `customer_id` duplicado | 84 | 1,19 % involucradas; 42 filas sobrantes (0,60 %) |
| Consistencia | `internet_service = none` con `monthly_charges > 60` | 17 | 0,24 %; cargos entre 76,78 y 92,50 |
| Consistencia | `fecha_alta` posterior al corte | 20 | 0,28 %; valor reportado 2026-11-15 |

El perfil documenta **450 filas distintas con al menos un defecto (6,39 %)**, teniendo en cuenta los solapamientos identificados. Los duplicados comprenden 21 copias exactas y 21 pares con cargos mensuales diferentes.

### 2.2. ¿Qué defectos del perfil NO detectó el contrato canónico?

Antes de incorporar RC-3, el comando `uv run python -m scripts.validar_contrato v2 data/raw/crm_extracto.csv` reportó **7 reglas incumplidas**. En las columnas canónicas identificó seis tipos de defectos, pero no la inconsistencia que requiere cruzar dos variables.

| Defecto del perfil en columnas canónicas | Filas | Regla | ¿Detectado inicialmente? |
|---|---:|---|---|
| `contract_type = Month-to-month` | 194 | RC-2 | Sí |
| `customer_id` repetido | 84 (42 sobrantes) | RC-1 | Sí |
| `payment_method = tarjeta_debito` | 81 | RC-2 | Sí |
| `monthly_charges` vacío | 56 | RC-2 | Sí |
| `tenure_months = -1` | 28 | RC-2 | Sí |
| `support_tickets = 99` | 13 | RC-2 | Sí |
| **Sin internet con cargo mensual mayor que 60** | **17** | **RC-3** | **No** |

**Respuesta:** la brecha principal del contrato canónico era **RC-3: 17 filas (0,24 %)**. Por separado, `internet_service = none` es un valor permitido y los cargos de 76,78 a 92,50 están dentro del rango general 0–500. La inconsistencia solo se detecta mediante la regla intercolumnas: **sin internet ⇒ cargo mensual ≤ 60**. El contrato v2 incorpora RC-3 tanto en `training_schema` como en `features_schema`.

RC-1 identificaba las 84 filas duplicadas, pero no diferenciaba entre las 21 copias exactas y los 21 pares con dos cargos distintos, distinción necesaria para aplicar los acuerdos de limpieza.

Los defectos no canónicos **`fecha_alta` vacía (28)** y **`fecha_alta` posterior al corte (20)** tampoco eran inspeccionados individualmente por el contrato original; RC-5 solo detectaba la presencia de las cuatro columnas extra. Por decisión negociada, esos dos defectos se registran en `contracts/crm_warnings.py` y sus columnas se excluyen del archivo limpio.

## 3. Negociación con el dueño del dato

**Dueño del dato:** Jefatura de CRM y Facturación de Conecta Andina S. A. Las respuestas de esta tabla son las informadas por el equipo en la ronda de negociación. Su implementación se contrasta con `src/clean.py` y `reports/cleaning.json`.

| # | Defecto / alcance | Filas | Pregunta o criterio consultado | Acuerdo informado por el dueño | Tratamiento implementado | Severidad operativa |
|---|---|---:|---|---|---|---|
| 1 | `contract_type = Month-to-month` | 194 | ¿Equivale al valor canónico en minúscula? | Recodificar | `Month-to-month` → `month-to-month` | RC-2 bloqueante para valores sin recodificar |
| 2 | `payment_method = tarjeta_debito` | 81 | ¿Equivale a un medio autorizado o es nuevo? | Excluir | Excluir filas con ese valor literal | RC-2 bloqueante |
| 3 | `monthly_charges` vacío | 56 | ¿Puede Facturación recuperar el cargo? | Excluir | Excluir filas; no imputar | RC-2 bloqueante |
| 4 | `tenure_months = -1` y `fecha_alta` vacía | 28 | ¿Es un código de antigüedad desconocida? | Excluir | Excluir filas; no sustituir por la antigüedad máxima | RC-2 bloqueante |
| 5 | `support_tickets = 99` | 13 | ¿Representa una cantidad desconocida? | Excluir | Excluir filas; no reemplazar por un valor supuesto | RC-2 bloqueante |
| 6 | Duplicados idénticos de `customer_id` | 21 filas sobrantes | ¿Son copias de la extracción? | Excluir copia repetida | Conservar una fila por cliente | RC-1 bloqueante |
| 7 | Duplicados con cargos distintos | 21 filas sobrantes de 21 pares | ¿Cuál cargo prevalece al corte? | Excluir la fila de menor cargo | Mantener la fila con mayor `monthly_charges` | RC-1 bloqueante |
| 8 | Sin internet con cargo > 60 | 17 | ¿Es incorrecto el servicio o el cargo? | Excluir | Excluir filas que incumplen RC-3 | RC-3 bloqueante |
| 9 | `fecha_alta` posterior al corte | 20 | ¿Cómo reportar la fecha futura? | Generar warning | Conservar filas si las variables canónicas cumplen; reportar advertencia | Advertencia en `crm_warnings.py` |
| 10 | `region`, `fecha_alta`, `fecha_corte`, `oferta_retencion_aceptada` | 4 columnas | ¿Deben entrar al modelo? | Excluir columnas | Eliminar del conjunto limpio; documentar las razones | RC-5 bloqueante sobre el esquema de entrenamiento |

**Nota de consistencia con la tabla de negociación inicial:** el equipo había descrito los casos 1 y 5 como «advertencia (RC-2)» y las columnas extra como «advertencia (RC-5)». Se conserva su **acuerdo de tratamiento**, pero se explicita la severidad ejecutable: **RC-2 y RC-5 son reglas bloqueantes**. Una recodificación o una exclusión negociada evita que el valor inválido llegue al contrato; no convierte el contrato en advertencia. Las advertencias reales son las relacionadas con `fecha_alta` en el extracto crudo.

## 4. Contrato v2 y limpieza implementados

### 4.1. Reglas del contrato

| Regla | Implementación | Comportamiento esperado |
|---|---|---|
| RC-1 | `customer_id` único en `training_schema` | Rechazar identificadores repetidos |
| RC-2 | Tipos, dominios, rangos y prohibición de nulos de las nueve columnas | Rechazar valores fuera del contrato |
| RC-3 | `RC3` en `training_schema` y `features_schema` | Rechazar cargo > 60 si `internet_service = none` |
| RC-4 | Tasa histórica de `churn` entre 0,05 y 0,60 | Rechazar tasa fuera de rango |
| RC-5 | `strict=True` en `training_schema` | Rechazar columnas ajenas a las nueve canónicas |
| Descarte máximo | `MAX_DISCARD_SHARE = 0.05` y `discard_ok(reporte)` | Rechazar proporción de descarte superior a 5 % |
| Advertencias | `warnings_schema` en `contracts/crm_warnings.py` | Reportar altas vacías y altas posteriores al corte |

**Alcance por esquema:** `features_schema` incorpora RC-3 y conserva `strict=False` como en la plantilla de la rama trabajada; RC-5 está demostrado sobre `training_schema`. Antes de utilizar `features_schema` en producción, corresponde decidir y documentar si debe prohibirse específicamente la columna con fuga en las entradas de predicción, ya que `strict=False` no la rechaza por sí solo.

### 4.2. Resultado agregado de `reports/cleaning.json`

| Tratamiento reportado | Filas |
|---|---:|
| `recodificado_contract_type` | 194 recodificadas (no descartadas por esta acción) |
| `excluidas_payment_method_tarjeta_debito` | 81 |
| `excluidas_monthly_charges_vacio` | 56 |
| `excluidas_tenure_months_menos_1` | 28 |
| `excluidas_support_tickets_99` | 13 |
| `excluidas_duplicado_copia_exacta` | 21 |
| `excluidas_duplicado_cargo_menor` | 21 |
| `excluidas_rc3_sin_internet_cargo_mayor_60` | 17 |
| **Total de filas descartadas, sin doble conteo** | **237** |

- **Filas de entrada:** 7.042.
- **Filas de salida:** 6.805.
- **Proporción descartada registrada:** `0.0337` (**3,37 %**).
- **Columnas excluidas:** `region`, `fecha_alta`, `fecha_corte`, `oferta_retencion_aceptada`.
- **Resultado:** el conjunto resultante tiene nueve columnas y pasó la validación v2.

El archivo `src/clean.py` usa reglas específicas para los valores negociados, contabiliza cada fila descartada una sola vez y ordena la salida por identificador para garantizar determinismo. `reports/cleaning.json` registra solo conteos y explicaciones, sin `customer_id`.

## 5. Decisiones técnicas requeridas

### DT-01. Excluir en lugar de imputar valores sin respaldo

**Decisión:** excluir los registros cuyo cargo mensual está ausente, cuya antigüedad tiene el código `-1`, cuyos tickets tienen el código `99` o cuyo medio de pago es `tarjeta_debito`, cuando no existe un mapeo validado. Se recodifica exclusivamente `Month-to-month` porque el dueño confirmó su equivalencia exacta. Los duplicados se tratan conforme al acuerdo de los casos 6 y 7.

**Alternativas consideradas:** imputación con media/mediana/moda, recodificación arbitraria o exclusión por defecto conocido.

**Justificación:** una imputación sin respaldo podría introducir información artificial en variables relevantes para la predicción. La exclusión mantiene explícito el defecto y evita presentar valores supuestos como si fueran observados por el CRM. Su costo se controla mediante el umbral de descarte.

**Riesgo residual:** pérdida de representatividad si los registros excluidos no son aleatorios. Debe evaluarse en etapas posteriores.

**Evidencia:** `src/clean.py`, tabla de negociación y `reports/cleaning.json`.

### DT-02. Presupuesto máximo de descarte del 5 %

**Decisión técnica propuesta:** `MAX_DISCARD_SHARE = 0.05` (5 %). **Pendiente:** documentar la aprobación formal que corresponda en `docs/decision_log.md`.

**Fundamento cuantitativo:** el extracto V4 descartó 237 de 7.042 filas, equivalente a 3,37 %. El límite del 5 % deja **1,63 puntos porcentuales** de margen frente al lote observado y bloquea pérdidas claramente superiores; por ejemplo, un lote con 20 % de descarte debe ser rechazado.

**Alternativas:** límite de 3 %, que rechazaría el lote actual, y límite de 10 %, que toleraría una pérdida más amplia.

**Limitación:** el 5 % es un umbral operacional elegido por el equipo a partir de un solo extracto; debe revisarse con nuevos lotes y con el dueño del dato cuando corresponda.

**Evidencia:** `contracts/churn_contract.py`, `reports/cleaning.json` y `test_descarte_maximo`.

## 6. Fuga de información

**Columna identificada:** `oferta_retencion_aceptada`.

**Razón:** representa el resultado de una oferta de retención hecha en la campaña, que ocurre **después** de la priorización de clientes del lunes a las 06:00. Si el modelo usa este dato para calcular el riesgo previo a la campaña, obtiene información futura e invalida la evaluación predictiva. Por ello se elimina de `clean.csv` mediante `COLUMNAS_EXCLUIDAS` y `training_schema` impide su presencia como columna extra (RC-5).

**Línea de tiempo de disponibilidad:**

```text
Corte CRM (2026-09-30)
        ↓
Lote de puntuación del lunes, 06:00
        ↓
Selección de clientes y campaña de retención
        ↓
Registro de la oferta / aceptación en CRM
        ↓
Observación de churn a 30 días
```

**Cuantificación obligatoria — PENDIENTE DE EVIDENCIA PS-4.** Aunque el perfil general reporta 1.928 casos de abandono de 7.042 (27,38 %), **no se han compartido los conteos ni tasas de churn desagregadas por `oferta_retencion_aceptada`**. Deben obtenerse de forma local, sin imprimir identificadores ni filas individuales:

```bash
uv run python - <<'PY'
import pandas as pd

df = pd.read_csv('data/raw/crm_extracto.csv')
resumen = df.groupby('oferta_retencion_aceptada', dropna=False)['churn'].agg(
    clientes='size', casos_churn='sum', tasa_churn='mean'
)
print(resumen.to_string())
PY
```

| `oferta_retencion_aceptada` | Clientes | Casos churn | Tasa churn |
|---|---:|---:|---:|
| `0` | **PENDIENTE** | **PENDIENTE** | **PENDIENTE** |
| `1` | **PENDIENTE** | **PENDIENTE** | **PENDIENTE** |

**Interpretación por completar:** comparar las dos tasas y explicar su relación con el momento posterior a la decisión. Una asociación fuerte no autoriza usar el campo como predictor; su indisponibilidad temporal ya constituye riesgo de fuga.

## 7. Pruebas del sistema (PS-1 a PS-5)

### PS-1. El extracto no entra al historial de Git

**Estado:** **PENDIENTE DE EVIDENCIA DE TERMINAL.** La ficha del equipo informa que `crm_extracto_v4.csv` fue copiado como `data/raw/crm_extracto.csv` y registrado bajo DVC (`data/raw/crm_extracto.csv.dvc`). También indica que el CSV no está en Git; falta aportar las comprobaciones solicitadas.

**Comandos obligatorios:**

```bash
git status --short data/
git check-ignore -v data/raw/crm_extracto.csv data/processed/clean.csv
git log --all --stat -- '*.csv' | head
```

**Criterios de aceptación:** ambos CSV ignorados, ningún CSV real en el historial de Git y archivo `.dvc` versionable. **Adjuntar las salidas reales** a esta sección antes de cerrar el reto.

### PS-2. La limpieza pasa el v2; el crudo no

**Estado:** **VERIFICADO mediante las ejecuciones suministradas por el equipo.**

**a) Limpieza:**

```text
$ uv run python -m src.clean
[clean] 7042 → 6805 filas (3.4% descartado)
```

**b) Contrato v2 sobre la salida limpia:**

```text
$ uv run python -m scripts.validar_contrato v2 data/processed/clean.csv
[v2] data/processed/clean.csv: 6805 filas · 9 columnas
  ✅ sin fallas
```

**c) Contrato v2 sobre el extracto crudo:**

```text
$ uv run python -m scripts.validar_contrato v2 data/raw/crm_extracto.csv
[v2] data/raw/crm_extracto.csv: 7042 filas · 13 columnas
  ❌ 8 reglas incumplidas
```

| Regla detectada sobre el crudo | Filas afectadas / columnas |
|---|---:|
| `contract_type` fuera del dominio | 194 |
| `customer_id` duplicado | 84 |
| `payment_method` fuera del dominio | 81 |
| `monthly_charges` no nulo | 56 |
| `tenure_months` fuera del rango | 28 |
| **RC-3**: sin internet con cargo mayor a 60 | **17** |
| `support_tickets` fuera del rango | 13 |
| **RC-5**: columnas extra en el esquema | **4 columnas** |

**d) Advertencias sobre el crudo:**

```text
$ uv run python -m scripts.validar_contrato advertencias data/raw/crm_extracto.csv
[advertencias] data/raw/crm_extracto.csv: 7042 filas · 13 columnas
  ❌ 2 reglas incumplidas
```

| Advertencia | Filas afectadas |
|---|---:|
| `fecha_alta` vacía | 28 |
| `fecha_alta` posterior a `fecha_corte` | 20 |

**Interpretación:** el validador muestra las advertencias como reglas incumplidas, pero su tratamiento acordado es **informar al dueño del dato**, no reclasificarlas como nuevas condiciones bloqueantes del conjunto canónico. El control bloqueante está separado en `training_schema` y `discard_ok`.

### PS-3. Las pruebas automatizadas rechazan datos inválidos

**Estado:** **11 PRUEBAS APROBADAS; falta la demostración de mutación de RC-3.**

**Evidencia de ejecución recibida:**

```text
$ uv run pytest tests/test_contract.py -v
collected 11 items

test_valid_data_passes                                    PASSED
test_invalid_values_are_rejected[tenure_months--3]         PASSED
test_invalid_values_are_rejected[contract_type-weekly]     PASSED
test_invalid_values_are_rejected[senior_citizen-2]         PASSED
test_invalid_values_are_rejected[churn-5]                  PASSED
test_duplicate_ids_are_rejected                            PASSED
test_schema_change_scenario_breaks_contract                PASSED
test_rc3_sin_internet_con_cargo_alto_se_rechaza             PASSED
test_rc3_en_features_schema                                PASSED
test_rc5_columna_no_autorizada                              PASSED
test_descarte_maximo                                       PASSED

11 passed in 0.43s
```

Las pruebas se ejecutan con datos sintéticos y verifican, entre otros, que se rechace un cliente sin internet con cargo 90, que el entrenamiento rechace la columna `oferta_retencion_aceptada` y que `discard_ok` acepte 3,37 % y 5 %, pero rechace 20 %.

**Demostración de que RC-3 es efectiva — PENDIENTE DE EVIDENCIA:**

1. Respaldar `contracts/churn_contract.py` **fuera del conjunto de archivos que se van a confirmar**.
2. Quitar **temporalmente** `RC3` de `checks` en `training_schema` (sin eliminar las demás reglas).
3. Ejecutar `uv run pytest tests/test_contract.py::test_rc3_sin_internet_con_cargo_alto_se_rechaza -v`. La prueba debe **fallar** porque el dato inválido ya no se rechaza.
4. Restaurar el archivo original y ejecutar `uv run pytest tests/test_contract.py -v` hasta obtener otra vez **11 passed**.
5. Guardar ambas salidas. **No publicar ni confirmar en Git la versión sin RC-3**.

### PS-4. La fuga, cuantificada

**Estado:** **PENDIENTE DE EVIDENCIA NUMÉRICA.**

- **Campo:** `oferta_retencion_aceptada`.
- **Motivo de fuga:** se registra después del lote del lunes y de la campaña; no es información disponible al predecir.
- **Medida requerida:** cantidad y tasa de `churn` para cada valor del campo.
- **Comando:** figura en la sección 6 de esta bitácora.
- **Resultado y análisis:** completar la tabla de la sección 6 con la salida real, sin mostrar `customer_id`.

### PS-5. La limpieza no esconde un lote corrupto

**Estado:** **PENDIENTE DE EVIDENCIA DE EJECUCIÓN.** Debe demostrarse un caso masivo (por ejemplo, 20 % de cargos nulos) en una **copia temporal del extracto, fuera de `data/raw/` y sin guardarlo en Git**, y que `discard_ok` bloquea el lote.

La siguiente comprobación usa una copia temporal que se elimina al terminar y solo imprime métricas agregadas:

```bash
uv run python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from src.clean import clean
from contracts.churn_contract import discard_ok, training_schema

raw = pd.read_csv('data/raw/crm_extracto.csv')
with TemporaryDirectory(prefix='srt_ps5_') as temporal:
    ruta = Path(temporal) / 'crm_corrupto.csv'
    corrupto = raw.copy()
    indices = corrupto.sample(frac=0.20, random_state=42).index
    corrupto.loc[indices, 'monthly_charges'] = float('nan')
    corrupto.to_csv(ruta, index=False)

    limpio, informe = clean(pd.read_csv(ruta))
    # La validación del esquema por sí sola no sustituye la regla de descarte.
    training_schema.validate(limpio, lazy=True)
    print('Filas iniciales:', informe['filas_entrada'])
    print('Filas resultantes:', informe['filas_salida'])
    print('Proporción descartada:', informe['proporcion_descartada'])
    print('Límite permitido:', 0.05)
    print('¿Se permite continuar?:', discard_ok(informe))
    assert not discard_ok(informe), 'ERROR: no se bloqueó el descarte excesivo'
    print('BLOQUEO POR DESCARTE EXCESIVO: comprobado')
PY
```

**Criterio de aceptación:** la proporción de descarte es mayor que `0.05`, `discard_ok(informe)` devuelve `False` y la ejecución documenta que el lote debe detenerse antes de entrenar o predecir. Adjuntar la salida obtenida. La integración automática de esta regla como etapa `validate` del pipeline se realizará en el Reto 03.

## 8. Gobernanza, privacidad y decisiones pendientes

**Responsables:** Jefatura de CRM y Facturación como **dueño del dato**; Data Scientist / Data Steward como custodio operativo del conjunto bajo DVC en el repositorio. El dueño del dato tiene la autoridad de aprobar cambios al contrato de datos de acuerdo con la RACI del Reto 01.

**Datos personales y minimización:** `customer_id` es un identificador interno seudonimizado y debe mantenerse fuera de reportes públicos de control de calidad. `senior_citizen` es el atributo protegido relevante para las verificaciones de equidad. La clasificación jurídica de los campos y la adecuación de la finalidad autorizada deben quedar justificadas en `docs/datos_gobernanza.md` y, cuando corresponda, consultarse con el responsable de protección de datos.

**Minimización aplicada:** `src/clean.py` elimina `region`, `fecha_alta`, `fecha_corte` y `oferta_retencion_aceptada`, con razones registradas en `COLUMNAS_EXCLUIDAS` y `reports/cleaning.json`.

**Acceso al remoto de datos:** las autorizaciones de lectura/escritura y el remoto DVC deberán documentarse en `docs/datos_gobernanza.md`; su implementación se completa en el Reto 03. No se presume que el remoto ni sus permisos estén configurados.

**Actualizaciones por acreditar:**

- `docs/decision_log.md`: una entrada por tratamiento negociado, más **DT-01** (excluir vs. imputar) y **DT-02** (límite de descarte de 5 %), con responsable y evidencia. **Pendiente de comprobar su versión actualizada**.
- `docs/riesgos.md`: añadir un riesgo nuevo de categoría `datos` o `ética` vinculado con defectos del CRM, fuga, representatividad o pérdida de filas. **Pendiente de comprobar el registro**.
- `docs/datos_gobernanza.md`: completar las cinco decisiones mínimas de gobierno exigidas por la versión lite, el análisis cuantitativo de la fuga y la tabla final de negociación. **Pendiente de verificación integral**.

**Uso de IA generativa:** se utilizó ChatGPT como apoyo de estructuración documental y revisión del contrato y sus pruebas. En esta interacción se trabajó con esquemas, conteos agregados y salidas de consola; **no se compartió el CSV original de clientes**. El uso debe quedar registrado según la política del proyecto.

## 9. Contribuciones del equipo y trazabilidad

La RACI del Reto 01 define los roles primarios. **No se dispone de evidencia suficiente para atribuir tareas ya realizadas a una persona específica**; antes de entregar, los tres integrantes deben completar y respaldar esta tabla con commits, PR o registros de trabajo.

| Integrante | Rol del proyecto | Contribución efectiva en Reto 02 | Evidencia verificable |
|---|---|---|---|
| Jorge Andrés Ángel | Líder / PO | **PENDIENTE DE CONFIRMAR** | Commit / PR / actividad: **PENDIENTE** |
| Juan Camilo Zuluaga Serna | Data Scientist / Data Steward | **PENDIENTE DE CONFIRMAR** | Commit / PR / actividad: **PENDIENTE** |
| Brayhan Andrés Jaramillo Castaño | ML / MLOps Engineer | **PENDIENTE DE CONFIRMAR** | Commit / PR / actividad: **PENDIENTE** |

## 10. Resumen de evidencias y cierre

| Evidencia exigida | Estado actual | Soporte |
|---|---|---|
| Perfil de calidad con cifras y brecha canónica | **Documentado** | `docs/datos_gobernanza.md` §2 y sección 2 de esta bitácora |
| Negociación con el dueño y tratamientos | **Documentado** | Tabla de la sección 3; `src/clean.py` |
| PS-1: CSV bajo DVC y excluido del historial Git | **Pendiente de salida de comandos** | Comandos en §7 PS-1 |
| PS-2: limpio aprobado y crudo rechazado por v2 | **Verificado** | 6.805/9 sin fallas; 7.042/13 con 8 reglas; 2 advertencias |
| PS-3: pruebas RC-3, RC-5 y descarte | **11/11 aprobadas** | `uv run pytest tests/test_contract.py -v` |
| PS-3: falla de RC-3 al retirar temporalmente la regla | **Pendiente** | Prueba de mutación y restauración |
| PS-4: tasas de churn por valor de la fuga | **Pendiente** | Tabla y comando en §6 |
| PS-5: lote corrupto detenido por descarte excesivo | **Pendiente** | Experimento en copia temporal |
| DT-01 y DT-02 registradas en `decision_log.md` | **Pendiente de comprobar** | Registro de decisiones |
| Nuevo riesgo registrado | **Pendiente de comprobar** | `docs/riesgos.md` |
| Cinco elementos mínimos de gobernanza | **Pendiente de completar/verificar** | `docs/datos_gobernanza.md` §5 |
| Participación individual documentada | **Pendiente** | §9 y trazabilidad en Git |
| Etiqueta `r02` publicada | **Pendiente de verificar** | `git ls-remote --tags origin` |

**Conclusión de avance:** la limpieza acordada produce un conjunto de nueve columnas que supera el contrato v2; el extracto crudo es rechazado por ocho reglas, entre ellas RC-3 y RC-5; dos advertencias no canónicas quedan identificadas y las once pruebas automatizadas suministradas aprobaron. La entrega académica completa requiere incorporar las evidencias pendientes señaladas y cerrar formalmente las decisiones de gobierno, antes de publicar `r02`.

**Precaución de entrega:** no confirmar en Git archivos CSV de clientes, copias temporales corruptas ni salidas que contengan `customer_id`. Versionar únicamente código, documentación, archivos `.dvc` y reportes agregados autorizados.
