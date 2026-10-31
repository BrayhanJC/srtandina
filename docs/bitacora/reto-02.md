# Bitácora – Reto 02 · Gobierno y contrato de datos (versión lite)

**Equipo:** Jorge Andrés Ángel · Juan Camilo Zuluaga Serna · Brayhan Andrés Jaramillo Castaño · **Variante:** V4 – Hogar fibra premium · **Tag:** `r02` · **Fecha:**

## Respuestas a las preguntas del reto

### ¿Qué defectos del perfil NO detectó el contrato canónico?

Sobre el extracto crudo, el contrato canónico de la plantilla (`training_schema`) falló en 7 reglas. Detectó los defectos de dominio, rango, nulos y unicidad de las columnas canónicas. Estos son los que no detectó:

1. **RC-3, sin internet con cargo mayor a 60: 17 filas (0.24 %).** La plantilla no tiene esa regla entre columnas, así que esos clientes pasarían como válidos.
2. **`fecha_alta` posterior al corte (2026-11-15): 20 filas (0.28 %).** El contrato rechaza la columna completa por estar fuera de la §2.1 (RC-5), pero no mira su contenido.
3. **`fecha_alta` vacía: 28 filas (0.40 %).** Solo aparecen porque esas mismas filas tienen `tenure_months = -1`.
4. **El tipo de duplicado.** El contrato reporta 84 filas con `customer_id` repetido. No distingue las 21 copias exactas de los 21 clientes que tienen dos cargos mensuales distintos, y esa diferencia cambia el tratamiento.
5. **La fuga.** El contrato rechaza `oferta_retencion_aceptada` por estar fuera del esquema, no porque tenga fuga. Si alguien la agregara al modelo canónico, ninguna regla la detendría.

El contrato v2 debe cerrar esta brecha. RC-3 bloquea (en `training_schema` y `features_schema`). Las reglas sobre `fecha_alta` van a `crm_warnings.py` como advertencias, porque `fecha_alta` no es una columna canónica. La regla de descarte máximo evita que la limpieza esconda un lote corrupto.

## Evidencias
| Qué demuestra | Evidencia (ruta, commit, corrida, captura) |
|---|---|
| El extracto está bajo DVC y no en Git | `data/raw/crm_extracto.csv.dvc`; commit "data: extracto CRM bajo DVC" |
| El contrato canónico rechaza el extracto crudo (7 reglas) | Salida de `uv run python -m scripts.validar_contrato v2 data/raw/crm_extracto.csv` en `docs/datos_gobernanza.md` §2.2 |

## Decisiones técnicas requeridas
(Se completa en el punto 3.)

## Reflexión gerencial (5–8 líneas)
(Se completa al final del reto.)
