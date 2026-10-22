# Project Charter — Sistema de Retención Temprana (SRT)

> Se inicia en el **Reto 00** (secciones 1–5) y se completa en el **Reto 01** (secciones 6–8).
> Nombres, roles y decisiones según el *contrato del sistema* del curso (§6.1, §9, §11).

## 1. Identificación
- Proyecto: SRT – Conecta Andina S.A.
- Variante (V1–V6) y segmento: v4
- Supuestos de la variante: 

| customer_value | contact_cost | retention_success_rate | capacidad semanal | política de equidad | semilla del extracto |
|---|---|---|---|---|---|
| 900.0 | 35.0 | 0.30 | 400 | ≤ 0.10 | 2029 |

- Equipo y roles principal / secundario (Líder/PO · Data Scientist/Steward · MLOps Engineer):

| Rol Principal | Rol Secundario | Quien lo ejerce |
|---|---|---|
| Data Scientist / Data Steward | ML / MLOps Engineer | Juan Camilo Zuluaga Serna | 
| Líder de proyecto / Product Owner | ML / MLOps Engineer | Jorge Andres Angel | 
| ML / MLOps Engineer | Data Scientist / Data Steward | Brayhan Andres Jaramillo Castaño | 

- Repositorio: https://github.com/BrayhanJC/srtandina

## 2. Problema de negocio y línea base

**Decisión que cambia.** 
Cada lunes a las 07:00, el call center de retención de Conecta Andina decide a cuáles clientes de fibra premium (V4) llamar esa semana, con un tope de 400 llamadas (contrato §5 y §11). El umbral de la lista lo aprueba el Sponsor, la Gerencia Comercial (§9.2). El SRT le entrega al agente una lista ordenada por probabilidad de deserción a 30 días, con los factores que explican cada caso (§1).

**Situación actual y su problema.** 
Hoy los agentes eligen con tres reglas informales: "los que se quejaron", "los de contrato mes a mes" y "los que pagan más" (Reto 00 §2.2, bloque 1). Ninguna cabe en la capacidad ni distingue riesgo real:
- Hay 771 clientes mes a mes en el lote, casi el doble de la capacidad, y solo el 39.7 % de ellos deserta.
- Con cualquiera de las tres reglas, de 400 llamadas solo 165–170 llegan a un desertor (41–43 %). El modelo de referencia llega a 248 (62 %).
- Los desertores que no se quejan ni pagan mucho, los que "desertan en silencio", no entran en ninguna regla.

**Costo de no hacer nada** 
(supuestos V4; lote de referencia = conjunto de prueba de 1 400 clientes, §5 "Tamaño del lote"; cifras en miles de COP, provisionales hasta el Reto 03):
- En cada lote hay 384 clientes que desertan (27.4 %). Sin campaña se pierde un valor de 384 × 900 = **345 600**.
- Con las reglas informales, el ahorro neto de la campaña es de ≈ 30 550–31 900 por lote. Con la lista del modelo es de 52 960.
- Seguir con las reglas deja de ahorrar ≈ **21 000–22 400 por lote semanal**. Supuestos: cada desertor contactado se retiene con probabilidad 0.30 y cada llamada cuesta 35.

**Punto de equilibrio del contacto.**

    **valor esperado de llamar** = p × retention_success_rate × customer_value − contact_cost
    ** p* **= contact_cost / (retention_success_rate × customer_value) = 35 / (0.30 × 900) = 35 / 270 ≈ 0.13

Llamar a un cliente tiene valor esperado positivo si su probabilidad de deserción supera el **13 %**.

**Qué restricción manda: la capacidad.** En el conjunto de prueba (1 400 clientes), **834** tienen probabilidad ≥ p*, y la capacidad es de **400** llamadas, el 28.6 % del lote. Hay más del doble de clientes que valdría la pena llamar de los que caben. La probabilidad del cliente número 400 de la lista es ≈ 0.39, muy por encima de p*. En V4, la restricción económica no es la que limita. Esto sirve como argumento para pedir más capacidad o para justificar que el umbral quede alrededor de 0.39 y no de 0.13.


## 3 ML Canvas (razonamiento de cada bloque)
| Bloque | Canónico (resumen en una línea) | Por qué está así | Qué se rompería si fuera distinto | Adaptación a la variante (V4 – Hogar fibra premium) |
|---|---|---|---|---|
| 1 Propuesta de valor | Lista semanal priorizada y explicada que reemplaza las tres reglas informales | §1 del contrato etiqueta 2 y 3 | Si se entrega solo una probabilidad, el agente no sabe qué hacer con ella y sigue con las reglas informales; el asistente de explicación del Reto 07 pierde su razón de ser | Cliente de alto valor (900) y llamada cara (35): cada llamada desperdiciada y cada desertor no detectado cuestan más que en otros segmentos |
| 2 Tarea de predicción | Clasificación binaria: probabilidad de `churn = 1` en 30 días | §2.1: `churn` "se conoce 30 días después"; §3: EN_RIESGO resulta de aplicar umbral y capacidad a una probabilidad | Con salida 0/1 no se puede ordenar ni cortar la lista en la capacidad (Reto 04); con horizonte de 90 días el monitoreo de desempeño del Reto 05 queda tres meses ciego | No cambia: la tarea y los datos son los mismos para todas las variantes (§11) |
| 3 Decisiones | Llamar en orden descendente desde `model.decision_threshold` hasta la capacidad semanal | §1: capacidad limitada; §9.2: el umbral lo aprueba el Sponsor; §5: la lista va "hasta business.weekly_capacity" | Sin tope, la lista del lunes del Reto 04 tendría 834 clientes sobre p* y el call center solo atiende 400; si el umbral lo fija el Data Scientist se viola §9.2 | Capacidad 400 = 28.6 % de un lote de 1 400. p* = 35 / (0.30 × 900) = 0.13, muy por debajo del cliente nº 400 (p ≈ 0.39): manda la capacidad |
| 4 Haciendo predicciones | Batch el lunes (06:00 lote, 07:00 lista) + API `/predict` en línea, p95 < 300 ms | §5: scoring y lista los lunes; "Diario (continuo): servicio en línea para consultas del call center" | Solo batch: el agente no puede consultar a un cliente que llama a mitad de semana (Reto 05). Solo en línea: nadie arma la lista semanal (Reto 04) | ~400 llamadas/semana ≈ 80 por día hábil: carga baja para la API; el SLO no cambia |
| 5 Recolección de datos | Etiqueta a T + 30; resultado del contacto en el CRM; los contactados contaminan la etiqueta | §3: la etiqueta se observa al cerrar la ventana de 30 días y "los clientes CONTACTADO contaminan la etiqueta (la campaña cambia el desenlace)" | Si se reentrena (Reto 03) sin distinguir esas etiquetas, el modelo aprende que los clientes de alto riesgo "no se van" y les baja el score; la model card del Reto 06 queda incompleta | ~29 % de cada lote se contacta y se retiene el 30 % de los desertores contactados: en V4 la contaminación es alta (ver bloque peor justificado) |
| 6 Fuentes de datos | Extracto de CRM, facturación y soporte (tickets 90 días); dueño: Jefatura de CRM y Facturación; Ley 1581 | §1: el dato tiene dueño; §2.1: `customer_id` es seudónimo y `senior_citizen` atributo protegido; §9.2: "Cambio del contrato de datos → Dueño del dato" | Sin dueño, en el Reto 02 nadie decide los tratamientos de limpieza ni responde por errores del extracto; si se trata `customer_id` como dato común se expone información personal | El extracto de V4 se genera con la semilla 2029 (Reto 02); dueño y reglas de privacidad no cambian |
| 7 Simulación de impacto | Ahorro neto = retenidos × `customer_value` − contactos × `contact_cost`, frente al azar | §7.3: métricas `net_savings_*` "frente a la línea base aleatoria"; §13: línea base = "contactar al azar el mismo número de clientes" | Sin línea base no se sabe si el modelo aporta o si cualquier lista daría lo mismo; el KPI de negocio del Reto 06 no se puede calcular | Desertor contactado: 0.30 × 900 = 270 esperados vs. 35 de costo. `net_savings_vs_random` = 39 325.89 miles de COP (provisional) |
| 8 Construyendo modelos | Reentrenamiento mensual o ante alerta; entra como `@challenger`, pasa a `@champion` solo con gate; `@previous` para rollback | §4: aliases y Precaución: "ninguna versión llega a @champion sin… gate.json con passed: true"; §5: primer lunes del mes, 02:00 | Si la versión nueva reemplaza directo a la de producción (Reto 03), un modelo peor llega sin evidencia y en el incidente del Reto 05 no hay a dónde hacer rollback | No cambia el mecanismo; los umbrales `gate.*` los fija el Líder/PO (§9.2) |
| 9 Features | Las 7 del modelo canónico; nunca `customer_id` ni columnas no canónicas | §2.2 RC-5: "ninguna columna fuera de la §2.1 entra al modelo" (fuga); §2.3: `region`, `fecha_alta`, `fecha_corte`, `oferta_retencion_aceptada` excluidas | Con `oferta_retencion_aceptada` el modelo "ve" el desenlace: ROC-AUC altísimo en el Reto 03 y fracaso en producción; con `customer_id` memoriza clientes en vez de patrones | `senior_citizen` entra como feature pero es atributo protegido: la brecha de recall actual es 0.144, por encima de la política V4 (≤ 0.10); se registra como riesgo para el Reto 06 |
| 10 Monitoreo | Por lote: % en riesgo, drift y contrato; a T + 30: ROC-AUC del periodo; servicio: latencia y errores; negocio: retención y brecha de equidad | §5: el lunes 08:00 solo hay reporte de datos y el desempeño llega a T + 30; §8.1: niveles OK / ALERTA / CRÍTICO; §12 regla 3: "contrato antes de predecir" | Vigilar solo ROC-AUC deja 30 días ciegos; un lote con una columna renombrada se puntuaría y la lista saldría mal (Reto 05) | Se sigue `recall_gap_senior_citizen` frente a 0.10 desde el primer lote, porque en V4 ya parte por encima |


**Bloque peor justificado y por qué** ("todos están bien justificados" no cuenta):

## 4. KPIs
| Tipo | KPI | Línea base | Meta | Cómo se mide |
|---|---|---|---|---|
| Técnico | | | | |
| Negocio (estimado) | | | | |
| Operación | | | | |
| Gestión | | | | |

## 5. Alcance y nivel de madurez MLOps objetivo

## 6. Roles, habilidades y RACI
(Las filas de umbral de decisión, umbrales del gate, brecha de equidad, rollback, cambio del contrato
de datos y envío de datos a un LLM externo tienen el **A** que fija el contrato §9.2.)

## 7. Backlog estimado, Definición de Terminado y cronograma

## 8. Riesgos principales
Los cinco riesgos de mayor exposición. El registro completo y vivo está en [`riesgos.md`](riesgos.md).
