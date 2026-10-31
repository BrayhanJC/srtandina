# Bitácora – Reto 02 · Gobierno y contrato de datos (versión lite)

**Equipo:** Jorge Andrés Ángel · Juan Camilo Zuluaga Serna · Brayhan Andrés Jaramillo Castaño · **Variante:** V4 – Hogar fibra premium · **Tag:** `r02` · **Fecha:**

## Respuestas a las preguntas del reto

### ¿Qué defectos del perfil NO detectó el contrato canónico?

El contrato canónico de la plantilla (`training_schema`) falló en 7 reglas sobre el extracto crudo. En las nueve columnas del modelo canónico (Contrato §2.1), el perfil encontró siete defectos. El contrato detectó seis y se le escapó uno:

| Defecto del perfil (columnas canónicas) | Filas | Regla | ¿Lo detectó? |
|---|---|---|---|
| `contract_type` = `Month-to-month` | 194 | RC-2 | Sí |
| `customer_id` repetido | 84 (42 sobrantes) | RC-1 | Sí |
| `payment_method` = `tarjeta_debito` | 81 | RC-2 | Sí |
| `monthly_charges` vacío | 56 | RC-2 | Sí |
| `tenure_months` = -1 | 28 | RC-2 | Sí |
| `support_tickets` = 99 | 13 | RC-2 | Sí |
| **Sin internet con cargo mayor a 60** | **17 (0.24 %)** | **RC-3** | **No** |

**El defecto que no detectó es RC-3: 17 filas (0.24 %).** Todas las reglas de la plantilla miran una columna a la vez. En esas filas, `internet_service = none` es válido y un cargo entre 76.78 y 92.50 también está dentro de 0–500. El error solo aparece al cruzar las dos columnas, y la plantilla no tiene la regla RC-3 que exige el Contrato §2.2. El contrato v2 cierra esta brecha agregando RC-3 a `training_schema` y a `features_schema`.

Sobre RC-1, el contrato detecta las 84 filas, pero no distingue sus dos casos: 21 copias exactas y 21 clientes con dos `monthly_charges` distintos. Esa distinción se resuelve en la negociación, porque cada caso necesita un tratamiento diferente.

Hay defectos del perfil en columnas no canónicas (Contrato §2.3) que quedan fuera de esta comparación: `fecha_alta` vacía (28 filas) y `fecha_alta` posterior al corte (20 filas). El contrato canónico no revisa esas columnas por diseño. Solo exige que no lleguen al modelo (RC-5, `strict=True`), y por eso reporta que sobran las cuatro. Esos defectos no se cierran en `churn_contract.py`. Se registran como advertencias en `contracts/crm_warnings.py`, la parte del v2 que se aplica al extracto crudo.

## Evidencias
| Qué demuestra | Evidencia (ruta, commit, corrida, captura) |
|---|---|
| El extracto está bajo DVC y no en Git | `data/raw/crm_extracto.csv.dvc`; commit "data: extracto CRM bajo DVC" |
| El contrato canónico rechaza el extracto crudo (7 reglas) | Salida de `uv run python -m scripts.validar_contrato v2 data/raw/crm_extracto.csv` en `docs/datos_gobernanza.md` §2.2 |

## Negociación

| # | Defecto | Filas | Pregunta al dueño del dato | Propuesta del equipo (tratamiento) | Severidad en v2 | Respuesta del dueño |
|---|---|---|---|---|---|---|
| 1 | `contract_type` = `Month-to-month` | 194 (2.75 %) | ¿Es el mismo contrato `month-to-month`, solo escrito con mayúscula? | **Recodificar** `Month-to-month` → `month-to-month` | Bloqueante (RC-2) | |
| 2 | `payment_method` = `tarjeta_debito` | 81 (1.15 %) | ¿Es un medio de pago nuevo o equivale a alguno de los cuatro de la ficha? | Si equivale a uno de la ficha: **recodificar** a ese valor. Si es nuevo: **excluir filas**, porque el dominio canónico no se puede ampliar sin cambiar el contrato | Bloqueante (RC-2) | |
| 3 | `monthly_charges` vacío | 56 (0.80 %) | ¿Por qué falta el cargo? ¿Facturación puede entregar el valor? | **Excluir filas** (no imputar) | Bloqueante (RC-2, sin nulos) | |
| 4 | `tenure_months` = -1 con `fecha_alta` vacía (mismas filas) | 28 (0.40 %) | ¿-1 es un código de "fecha de alta desconocida"? | **Excluir filas** o Poner la fecha mas alta | Bloqueante (RC-2) | |
| 5 | `support_tickets` = 99 | 13 (0.18 %) | ¿99 es un código especial (sin dato o error de la mesa de soporte) o un conteo real? | **Excluir filas** (no se reemplaza por otro número) | Bloqueante (RC-2) | |
| 6 | `customer_id` repetido, copias exactas | 21 clientes, 21 filas sobrantes (0.30 %) | ¿Es una duplicación de la extracción? | **Corregir**: dejar una fila por cliente | Bloqueante (RC-1) | |
| 7 | `customer_id` repetido con dos `monthly_charges` distintos (diferencia entre 1.26 y 6.86) | 21 clientes, 42 filas (0.60 %) | ¿Cuál de los dos cargos es el vigente al corte? ¿Hay un criterio (el mayor, el último)? | Si hay un criterio: **corregir** dejando la fila que indique. Si no: **excluir las dos filas** del cliente | Bloqueante (RC-1) | |
| 8 | Sin internet con cargo > 60 (RC-3) | 17 (0.24 %), cargos entre 76.78 y 92.50 | ¿El error está en el servicio (sí tienen internet) o en el cargo? | **Excluir filas** | Bloqueante (RC-3) | |
| 9 | `fecha_alta` posterior al corte (2026-11-15) | 20 (0.28 %) | ¿Por qué el CRM registra altas después del corte? | No se tocan las filas. `fecha_alta` no llega al modelo y su `tenure_months` es válido | **Advertencia** (`crm_warnings.py`) | |
| 10 | Columnas no canónicas: `region`, `fecha_alta`, `fecha_corte`, `oferta_retencion_aceptada` | 4 columnas | Confirmar que no se usan (Contrato §2.3) | **Excluir columnas** (`COLUMNAS_EXCLUIDAS`) | Bloqueante (RC-5) | |