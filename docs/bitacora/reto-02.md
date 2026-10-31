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
