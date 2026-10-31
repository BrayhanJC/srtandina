# Datos y gobernanza (Reto 02)

## 1. Dataset
Fuente · licencia · tamaño · granularidad · diccionario de variables · variable objetivo.

## 1. Ficha técnica recibida

Copia fiel de la *Ficha técnica del extracto CRM-RET* entregada por el dueño del dato junto con `crm_extracto_v4.csv`. Se conserva tal como se recibió, aunque los datos la contradigan (las diferencias se reportan en la §2).

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

## 2. Diagnóstico de calidad
| Dimensión | Regla verificada | Resultado | Acción |
|---|---|---|---|
| Completitud | | | |
| Validez | | | |
| Consistencia | | | |
| Unicidad | | | |
| Actualidad | | | |

### 2.1 Resumen

## ❌ 7 reglas incumplidas

| Columna | Regla | Filas afectadas | Ejemplos |
|---|---|---:|---|
| `contract_type` | `isin(['month-to-month', 'one-year', 'two-year'])` | 194 | `Month-to-month` |
| `customer_id` | `field_uniqueness` | 84 | — |
| `payment_method` | `isin(['electronic_check', 'mailed_check', 'bank_transfer', ...])` | 81 | `tarjeta_debito` |
| `monthly_charges` | `not_nullable` | 56 | `NaN` |
| `tenure_months` | `in_range(0, 72)` | 28 | `-1` |
| `support_tickets` | `in_range(0, 50)` | 13 | `99` |
| *(Entre columnas / esquema)* | `column_in_schema` | 4 | `region`, `fecha_alta`, `fecha_corte`, `oferta_retencion_aceptada` |

## 3. Hallazgos del EDA

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
