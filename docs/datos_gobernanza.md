# Datos y gobernanza (Reto 02)

## 1. Dataset
Fuente · licencia · tamaño · granularidad · diccionario de variables · variable objetivo.

## 1. Ficha técnica recibida

**Conecta Andina S.A. · Jefatura de CRM y Facturación**

**Ficha técnica del extracto CRM-RET · corte 2026-09-30**

| Atributo | Valor |
|---|---|
| Contenido | Clientes residenciales con servicio activo al inicio del periodo histórico, con su desenlace a 30 días |
| Granularidad | Una fila por cliente |
| Formato | CSV, UTF-8, separador coma, primera fila con encabezados |
| Volumen aproximado | 7 000 filas |
| Periodicidad | Corte mensual; el archivo se entrega el quinto día hábil del mes siguiente |
| Completitud | Ninguna columna admite valores vacíos |
| Dueño | Jefatura de CRM y Facturación (canal de soporte: mesa de datos CRM) |
| Uso autorizado | Exclusivamente el proyecto Sistema de Retención Temprana; prohibida la entrega a terceros. Los clientes autorizaron el tratamiento de sus datos para "gestión comercial, fidelización y análisis estadístico" (política de tratamiento de datos de Conecta Andina) |
| Seudonimización | El `customer_id` es un código interno; la tabla de correspondencia con el documento de identidad la custodia Facturación y no se entrega |

| # | Columna | Tipo | Descripción | Dominio documentado |
|---|---|---|---|---|
| 1 | `customer_id` | texto | Código seudonimizado del cliente, formato CNNNN-NNNNNN | Único en el archivo |
| 2 | `tenure_months` | entero | Meses completos desde la activación del servicio hasta la fecha de corte | 0 – 72 (72 es el tope que registra el sistema) |
| 3 | `contract_type` | texto | Modalidad del contrato vigente | `month-to-month`, `one-year`, `two-year` (en minúscula, exactamente así) |
| 4 | `internet_service` | texto | Tecnología de internet contratada | `dsl`, `fiber`, `none` (`none` = solo telefonía) |
| 5 | `payment_method` | texto | Medio de pago registrado | `electronic_check`, `mailed_check`, `bank_transfer`, `credit_card` |
| 6 | `monthly_charges` | decimal | Cargo mensual facturado del plan, en miles de COP | 0 – 500. Tarifas vigentes: los planes de solo telefonía (`none`) cuestan hasta 60 |
| 7 | `support_tickets` | entero | Tickets de soporte abiertos por el cliente en los últimos 90 días | 0 – 50 |
| 8 | `senior_citizen` | entero | 1 si el titular tiene 65 años o más según la fecha de nacimiento registrada | 0, 1 |
| 9 | `churn` | entero | 1 si el cliente canceló el servicio en los 30 días siguientes a la fecha de corte | 0, 1 (históricamente entre 25 % y 30 % de los clientes) |
| 10 | `region` | texto | Departamento de la dirección de instalación | `Quindío`, `Risaralda`, `Caldas`, `Norte del Valle` |
| 11 | `fecha_alta` | fecha AAAA-MM-DD | Fecha de activación del servicio | Anterior o igual a `fecha_corte` |
| 12 | `fecha_corte` | fecha AAAA-MM-DD | Fecha de corte del extracto | 2026-09-30 en todo el archivo |
| 13 | `oferta_retencion_aceptada` | entero | Resultado de la última oferta de retención registrada en el CRM | 0, 1 |

> Esta ficha es la documentación oficial del extracto. Se entrega junto con el archivo `crm_extracto_<equipo>.csv` y describe lo que el sistema de origen debería contener. Las consultas sobre su contenido se dirigen al dueño del dato (mesa de datos CRM).

**Archivo recibido:** `crm_extracto_v4.csv` (variante V4), copiado como `data/raw/crm_extracto.csv` y registrado con DVC (`data/raw/crm_extracto.csv.dvc`, md5 `17bca792551fe4a92d2995ad9ec06827`, 657 548 bytes). No está en el historial de Git.

## 2. Perfil de calidad y brecha con el contrato

Extracto `data/raw/crm_extracto.csv` (V4): **7 042 filas · 13 columnas**. Los porcentajes se calculan sobre las 7 042 filas. Las reglas salen de la ficha técnica (§1). Para las nueve columnas canónicas, los dominios y rangos de la ficha coinciden con los del Contrato §2.1. Para el conteo se leyó el CSV como texto, así que una celda vacía cuenta como nulo.

### 2.1 Perfil (cuatro dimensiones)

| Dimensión | Regla verificada | Resultado (filas y %) | Acción |
|---|---|---|---|
| Completitud | Ninguna columna admite vacíos (ficha, "Completitud") | `monthly_charges`: 56 vacíos (0.80 %). `fecha_alta`: 28 vacíos (0.40 %). Las otras 11 columnas: 0 vacíos | Negociar con el dueño (§4.3) |
| Validez | `contract_type` ∈ {`month-to-month`, `one-year`, `two-year`} en minúscula | 194 filas (2.75 %) con `Month-to-month` (mayúscula inicial) | Negociar (§4.3) |
| Validez | `payment_method` ∈ {`electronic_check`, `mailed_check`, `bank_transfer`, `credit_card`} | 81 filas (1.15 %) con `tarjeta_debito`, un valor que no está en la ficha | Negociar (§4.3) |
| Validez | `tenure_months` entre 0 y 72 | 28 filas (0.40 %) con `-1`. Son las mismas 28 filas que tienen `fecha_alta` vacía | Negociar (§4.3) |
| Validez | `support_tickets` entre 0 y 50 | 13 filas (0.18 %) con `99` | Negociar (§4.3) |
| Validez | `internet_service`, `senior_citizen`, `churn`, `region`, `oferta_retencion_aceptada` en su dominio; `monthly_charges` entre 0 y 500; `customer_id` con formato CNNNN-NNNNNN; fechas en formato AAAA-MM-DD; `fecha_corte` = 2026-09-30 | 0 filas fuera del dominio. `monthly_charges` va de 18.0 a 128.27 | Ninguna |
| Unicidad | Una fila por cliente; `customer_id` único (ficha, "Granularidad") | 42 `customer_id` aparecen 2 veces: 84 filas (1.19 %) involucradas y 42 filas sobrantes (0.60 %). De esos 42: 21 son copias exactas y en los otros 21 las dos filas difieren solo en `monthly_charges` | Negociar (§4.3) |
| Consistencia | RC-3: sin internet (`internet_service = none`) → `monthly_charges` ≤ 60 (ficha, tarifas vigentes) | 17 filas (0.24 %) con cargos entre 76.78 y 92.50 | Negociar (§4.3) |
| Consistencia | `fecha_alta` ≤ `fecha_corte` (ficha) | 20 filas (0.28 %) con `fecha_alta` = 2026-11-15, posterior al corte | Negociar (§4.3) |

En total hay **450 filas distintas (6.39 %) con al menos un defecto**. Solo dos se solapan: las 28 filas con `tenure_months = -1` son las mismas de `fecha_alta` vacía, y una fila sobrante de un duplicado también tiene `Month-to-month`.

### 2.2 Brecha: contrato canónico de la plantilla sobre el extracto crudo

Este es el contrato que trae la plantilla (`training_schema`, antes de modificarlo):

```
$ uv run python -m scripts.validar_contrato v2 data/raw/crm_extracto.csv
[v2] data/raw/crm_extracto.csv: 7042 filas · 13 columnas
  ❌ 7 reglas incumplidas
                   columna                                             regla  filas_afectadas                                                   ejemplos
             contract_type  isin(['month-to-month', 'one-year', 'two-year'])              194                                             Month-to-month
               customer_id                                  field_uniqueness               84
            payment_method isin(['electronic_check', 'mailed_check', 'bank_t...               81                                             tarjeta_debito
           monthly_charges                                      not_nullable               56                                                        nan
             tenure_months                                   in_range(0, 72)               28                                                         -1
           support_tickets                                   in_range(0, 50)               13                                                         99
(entre columnas / esquema)                                  column_in_schema                4 region, fecha_alta, fecha_corte, oferta_retencion_aceptada
```
Código de salida: 1.

**Columnas canónicas (Contrato §2.1):**

| Defecto del perfil | Filas | Regla | ¿Lo detecta el contrato canónico? |
|---|---|---|---|
| `contract_type` = `Month-to-month` | 194 | RC-2 | Sí |
| `customer_id` repetido | 84 (42 sobrantes) | RC-1 | Sí. No distingue 21 copias exactas de 21 con dos cargos distintos |
| `payment_method` = `tarjeta_debito` | 81 | RC-2 | Sí |
| `monthly_charges` vacío | 56 | RC-2 | Sí |
| `tenure_months` = -1 | 28 | RC-2 | Sí |
| `support_tickets` = 99 | 13 | RC-2 | Sí |
| **Sin internet con cargo > 60** | **17** | **RC-3** | **No: la plantilla no implementa RC-3** |
| Tasa de churn | 27.38 % (1 928 de 7 042) | RC-4 | Pasa (entre 0.05 y 0.60) |

**Columnas no canónicas (Contrato §2.3):** el contrato canónico no revisa su contenido. Con RC-5 (`strict=True`) solo detecta que sobran las cuatro (`region`, `fecha_alta`, `fecha_corte`, `oferta_retencion_aceptada`). Por eso no ve `fecha_alta` vacía (28 filas) ni `fecha_alta` posterior al corte (20 filas). Esos dos defectos van a las advertencias del v2 (`contracts/crm_warnings.py`).

### 2.3 ¿Se conoce el lunes a las 06:00, cuando se puntúa el lote? (Contrato §5)

| Columna | ¿Se conoce el lunes 06:00? | Razón |
|---|---|---|
| `customer_id` | Sí | Identificador del CRM. No es variable del modelo |
| `tenure_months` | Sí | Se calcula a la fecha de corte |
| `contract_type` | Sí | Contrato vigente al corte |
| `internet_service` | Sí | Servicio contratado al corte |
| `payment_method` | Sí | Medio de pago registrado al corte |
| `monthly_charges` | Sí | Cargo facturado del plan vigente |
| `support_tickets` | Sí | Tickets de los 90 días anteriores al corte |
| `senior_citizen` | Sí | Sale de la fecha de nacimiento registrada |
| `churn` | **No** | Es la etiqueta: se conoce 30 días después (Contrato §2.1). No viene en el lote (`features_schema` no la incluye) |
| `region` | Sí | Dirección de instalación |
| `fecha_alta` | Sí | Fecha de activación |
| `fecha_corte` | Sí | Es la fecha del extracto |
| `oferta_retencion_aceptada` | **No** | Es el resultado de la oferta de retención. Esa oferta se hace en la campaña, después de la lista del lunes. **Candidata a fuga (§3)** |


## 3. Hallazgos del EDA

La columna `oferta_retencion_aceptada` está excluida del modelo por el contrato §2.3.
El conteo cruzado contra `churn` muestra por qué.

| `oferta_retencion_aceptada` | `churn = 0` | `churn = 1` | Total | Tasa de churn |
|---|---:|---:|---:|---:|
| 1 — aceptó la oferta | 1 039 | 74 | 1 113 | **6,65 %** |
| 0 — no aceptó | 3 675 | 1 854 | 5 529 | **33,53 %** |
| **Observado** | **4 714** | **1 928** | **6 642** | **29,03 %** |

Registros del extracto: 7 042. Los 400 que no aparecen en la tabla corresponden a
filas sin valor en `oferta_retencion_aceptada`.

**Lectura.** Quien aceptó la oferta deserta al 6,65 %; quien no la aceptó, al 33,53 %.
Son 26,88 puntos de diferencia, una razón de 5,04 a 1. Ninguna de las siete features
canónicas se acerca a ese poder de separación.

Esa fuerza es exactamente la señal de alarma. `oferta_retencion_aceptada` no describe
el estado del cliente **antes** de la decisión de contactarlo: registra el desenlace de
la campaña de retención, un hecho posterior al momento en que el SRT tiene que predecir.
El lunes a las 07:00, cuando hay que armar la lista, esa columna todavía está vacía para
los clientes que importan.

Entrenar con ella produciría un `roc_auc` alto en validación y un fracaso en producción:
el modelo no habría aprendido quién está en riesgo, sino quién ya fue tratado con éxito.
Es el caso de fuga descrito en el ML Canvas, bloque 9.

**Consecuencia para el pipeline.** La exclusión queda verificada en `src/features.py`
y cubierta por la regla RC-5 del contrato: ninguna columna fuera de §2.1 entra al modelo.
HU-04 implementa el control.


## 4. Contrato de datos
Implementado en `contracts/churn_contract.py` y verificado en la etapa `validate` de `dvc.yaml`.

| Campo | Tipo | Reglas | Responsable | Acción si falla |
|---|---|---|---|---|
| tenure_months | int | 0–72 | Dueño del CRM | Detener pipeline |
| contract_type | str | {month-to-month, one-year, two-year} | Dueño del CRM | Detener pipeline |
| … | | | | |

## 5. Plan de gobernanza
| Elemento | Decisión |
|---|---|
| Propietario y custodio del dato | |
| Política de acceso | |
| Datos personales y tratamiento (Ley 1581 de 2012) | |
| Versionamiento (DVC y remoto) | |
| Linaje (crudo → validado → train/test → modelo) | `dvc dag` |
| Retención | |
