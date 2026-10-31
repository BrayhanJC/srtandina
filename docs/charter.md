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

    valor esperado de llamar = p × retention_success_rate × customer_value − contact_cost
    p* = contact_cost / (retention_success_rate × customer_value) = 35 / (0.30 × 900) = 35 / 270 ≈ 0.13

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


**Bloque con mayor incertidumbre — recolección de datos (bloque 5).** El efecto de las campañas sobre el resultado observado a T+30 puede introducir sesgo de retroalimentación: los clientes contactados y retenidos podrían parecer de bajo riesgo en datos posteriores. Todavía no se ha cuantificado el efecto causal del contacto ni se dispone de una estrategia validada para corregirlo. En el Reto 02 se distinguirán los estados de contacto en los datos disponibles y, en los Retos 03 y 06, se documentarán las limitaciones del entrenamiento y de la simulación de impacto. Esta es una hipótesis de riesgo, no una medición confirmada.

## 4. KPIs

| Tipo | KPI | Línea base | Meta | Cómo se mide |
|---|---|---|---|---|
| Técnico | `pr_auc` | 0.6627 · `metrics.json`, (provisional) | ≥ 0.66 con el extracto real | `metrics.json` en cada `dvc repro` |
| Negocio (estimado) | `net_savings_vs_random` (ahorro frente a llamar al azar, Contrato §13) | 39 325.89 miles de COP · `metrics.json`, (provisional) | > 0 | `metrics.json` |
| Operación | Lista disponible el lunes a las 07:00 | Sin procedimiento (hoy se arma a mano) | 100 % de las semanas (Contrato §5) | Hora del archivo de la lista |
| Gestión | Tags `rNN` publicados a tiempo | — (primer reto) | 100 % antes de la fecha límite (Contrato §6.2) | Fecha del tag en GitHub |
| Gestión | Tiempo de rollback desde la decisión hasta que `/health` informa la versión de `@previous` (HU-11) | Sin procedimiento | < 30 min | Ensayo cronometrado del Reto 05 |

## 5. Alcance y nivel de madurez MLOps objetivo

### 5.1. Alcance del proyecto

| Incluido | Excluido o extensión opcional |
|---|---|
| Formulación, ML Canvas, KPIs, roles, RACI, backlog y gestión de riesgos (Retos 00–01). | Funcionalidades del catálogo extendido que no forman parte de los Retos 00–07. |
| Ingesta, limpieza, validación y gobernanza del extracto CRM (Reto 02). | Variables adicionales al modelo canónico sin aprobación del contrato. |
| Pipeline reproducible con DVC, experimentos, registro de modelos, quality gate y rollback (Reto 03). | Entrenamiento continuo automático sin intervención humana. |
| Pruebas automatizadas, integración continua y generación de la lista semanal (Reto 04). | Entrega continua y despliegue automático de nuevas versiones. |
| API de predicción, monitoreo, alertas y runbook (Reto 05). | Despliegues shadow y canary. |
| Evaluación económica, equidad y model card (Reto 06). | Extensiones no exigidas para el sistema de referencia. |
| Asistente LLM con evaluación, controles y respaldo (Reto 07). | Funcionalidades de IA generativa fuera de la explicación controlada. |
| Integración, simulacro de incidente y defensa (Proyecto Final, S8). | Funcionalidades no contempladas en el alcance aprobado. |

Las extensiones opcionales no otorgan puntos adicionales (Reto 00 §4.2).

### 5.2. Nivel de madurez MLOps objetivo

| Escala | Nivel objetivo | Características aplicadas al SRT |
|---|---|---|
| Google (0–2) | Nivel 0 avanzado | Entrenamiento reproducible y versionado, pipeline ejecutable, registro de modelos, pruebas y monitoreo, sin entrenamiento continuo autónomo. |
| Microsoft (0–4) | Nivel 2 como referencia funcional | Entrenamiento ejecutable y trazable, seguimiento de experimentos, artefactos versionados y promoción controlada de modelos. |

Se adopta Google nivel 0 avanzado, con prácticas cercanas al nivel 2 de Microsoft, porque el SRT requiere reproducibilidad y controles operativos, pero no necesita entrenamiento continuo autónomo ni despliegue automático de nuevas versiones.

La correspondencia entre ambas escalas es aproximada: no representan niveles técnicamente idénticos.

### 5.3. Justificación mediante los cinco factores

| Factor | Situación en V4 — Hogar fibra premium | Hacia dónde empuja |
|---|---|---|
| Número de modelos | Un modelo de clasificación binaria, con versiones `@challenger`, `@champion` y `@previous` (Contrato §4). | Madurez moderada: registro y control de versiones, sin infraestructura compleja de despliegue. |
| Velocidad de cambio del entorno | El comportamiento de deserción puede cambiar; las etiquetas de `churn` llegan a T+30 (Contrato §§2.1 y 5). | Mayor monitoreo y trazabilidad, sin reentrenamiento automático ante cualquier alerta. |
| Criticidad de la decisión | El SRT prioriza un máximo de 400 contactos semanales, con un valor supuesto de 900 mil COP por cliente y un costo de 35 mil COP por contacto (Contrato §11). | Mayor control de calidad, aprobación humana y capacidad de rollback. |
| Regulación | Tratamiento de datos personales, Ley 1581 de 2012, CONPES 4144 y brecha máxima de recall de 0.10 para `senior_citizen` (Contrato §§2, 9.2 y 11). | Mayor gobernanza, validación bloqueante, evaluación de equidad y supervisión de decisiones críticas. |
| Frecuencia de predicción | Batch semanal los lunes, servicio `/predict` durante la operación y reentrenamiento mensual (Contrato §5). | Automatización de inferencia y monitoreo; control manual de la promoción del modelo. |

### 5.4. Procesos manuales a propósito

| Paso manual | Responsable | Por qué se conserva manual |
|---|---|---|
| Revisar alertas y determinar si se requiere reentrenamiento extraordinario. | Data Scientist / Data Steward. | Una alerta de drift no demuestra por sí sola deterioro del modelo; las etiquetas se reciben a T+30. |
| Revisar el resultado del reentrenamiento mensual programado (primer lunes, 02:00), sin activar manualmente la ejecución prevista. | Data Scientist / Data Steward. | Permite verificar datos, métricas y trazabilidad antes de solicitar la promoción de una versión nueva. La ejecución mensual sigue el calendario del contrato. |
| Aprobar los umbrales del quality gate. | Líder / PO, con aprobación del comité. | Los criterios de calidad deben ser acordados antes de evaluar una promoción (Contrato §9.2). |
| Evaluar y ejecutar la promoción de `@challenger` a `@champion`. | Líder / PO supervisa; ML / MLOps Engineer ejecuta. | Ninguna versión debe llegar a producción sin `gate.json` aprobado y una decisión registrada (Contrato §4). |
| Aprobar `model.decision_threshold`. | Sponsor — Gerencia Comercial. | El umbral responde al valor económico, la capacidad semanal y la política de equidad, no únicamente al desempeño estadístico (Contrato §9.2). |
| Aprobar excepciones de equidad. | Comité, presidido por el docente. | La política V4 establece `recall_gap_senior_citizen ≤ 0.10`; cualquier excepción requiere evaluación y decisión formal (Contrato §§9.2 y 11). |
| Aprobar cambios del contrato de datos. | Dueño del dato — Jefatura de CRM y Facturación. | Impide modificar unilateralmente reglas de calidad, protección y finalidad de los datos (Contrato §9.2). |
| Autorizar el rollback ante incidentes. | Líder / PO; ejecuta ML / MLOps Engineer. | La reversión debe responder a un diagnóstico sustentado y dejar evidencia (Contrato §9.2). |

### 5.5. Decisión de alcance

Para V4 se prioriza un sistema reproducible, probado y monitoreado, con automatización de las tareas operativas repetitivas y aprobación humana de decisiones críticas. Este nivel es suficiente para cumplir los Retos 00–07 y el Proyecto Final sin incorporar entrenamiento continuo automático, despliegues progresivos ni entrega continua, que aumentarían la complejidad sin ser requisitos del alcance.



## 6. Roles, habilidades y RACI

### 6.1. Roles del equipo

| Integrante | Rol principal | Rol secundario |
|---|---|---|
| Jorge Andrés Ángel | Líder / Product Owner | ML / MLOps Engineer |
| Juan Camilo Zuluaga Serna | Data Scientist / Data Steward | ML / MLOps Engineer |
| Brayhan Andrés Jaramillo Castaño | ML / MLOps Engineer | Data Scientist / Data Steward |

### 6.2. Matriz RACI

- A: Responsable final de la decisión.
- R: Responsable de ejecución.
- C: Consultado.
- I: Informado.

| Actividad | Sponsor | Líder/PO | DS/Steward | MLOps | Dueño dato | Comité |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Project Charter y ML Canvas | C | A/R | C | C | C | I |
| Backlog y priorización | I | A/R | C | C |  |  |
| Contrato de datos y sus cambios | I | I | R | C | **A** |  |
| Pipeline de datos y versionado |  | I | C | A/R |  |  |
| Experimentos y selección de modelo |  | I | A/R | C |  |  |
| Umbrales del quality gate `gate.*` | I | **A**¹ | C | R |  | C |
| Umbral de decisión del negocio `model.decision_threshold` | **A** | C | R | I |  |  |
| Brecha de equidad aceptable | I | C | R | I |  | **A** |
| Promoción a @champion | I | **A** | C | R |  |  |
| Despliegue y monitoreo |  | I | C | A/R |  |  |
| Rollback ante incidente | I | **A** | I | R |  |  |
| Envío de datos a un proveedor de LLM externo | **A** | C | C | R | C | C |
| Model card y comunicación de resultados | I | **A** | R | C | I | I |

### 6.3. Gestión de los riesgos del equipo

Se identificaron tres riesgos prioritarios relacionados con la ejecución del proyecto: infraestructura tecnológica insuficiente (R-01), brechas de conocimiento en tecnologías requeridas (R-02) y disponibilidad limitada de tiempo para desarrollar las actividades (R-03).

El Líder / PO coordinará la planificación y el seguimiento de sus respuestas; el MLOps Engineer liderará las verificaciones de infraestructura, y el Data Scientist / Steward contribuirá a las pruebas técnicas y a la transferencia de conocimientos.

Las acciones, disparadores, probabilidades, impactos y estados se documentan en [Registro de riesgos](riesgos.md).


**Nota ¹:** Los umbrales `gate.*` tienen como A al Líder/PO, pero requieren aprobación del Comité (Contrato §9.2). En la fila «Envío de datos a un proveedor de LLM externo», se mantiene al Líder/PO como consultado; la comunicación al equipo se documentará en el registro de decisiones.

## 7. Backlog estimado, Definición de Terminado y cronograma

### 7.1. Backlog de referencia y estimaciones del tablero

El tablero GitHub Projects muestra **HU-01 a HU-17**, todas en estado `Backlog`, con prioridad, talla y estimación; su suma visible es **129 h**. Las siete historias de operación están identificadas con ⚙️. La captura revisada muestra **17 historias sin persona asignada** y **ningún spike visible**. Por ello, la columna «R propuesto» representa planificación del charter y **no asignaciones ya realizadas en GitHub**. Las fases y retos también deben registrarse en el tablero.

| Id | Historia | Prioridad | Fase CRISP-ML(Q) | Talla | GitHub (h) | Reto | R propuesto |
|---|---|---|---|---|---:|---|---|
| HU-01 | Decisión que cambia el SRT y su valor | Alta | Comprensión del negocio y datos | M | 6 | 00–01 | Líder/PO |
| HU-02 | Quién aprueba umbrales, equidad y rollback | Alta | Comprensión del negocio y datos | S | 3 | 01 | Líder/PO |
| HU-03 | Pipeline se detiene con datos inválidos | Alta | Ingeniería de datos | L | 10 | 02 | DS/Steward |
| HU-04 | Excluir fuga de información | Alta | Ingeniería de datos | L | 10 | 02 | DS/Steward |
| HU-05 | Reconstruir el modelo de cualquier tag | Alta | Ingeniería del modelo | M | 6 | 03 | MLOps |
| HU-06 | Comparar al menos tres corridas | Media | Ingeniería del modelo | L | 10 | 03 | DS/Steward |
| HU-07 ⚙️ | Nada llega a `main` sin pruebas y gate | Alta | Evaluación | M | 6 | 04 | Líder/PO, apoyo MLOps |
| HU-08 ⚙️ | Lista de riesgo cada lunes 07:00 | Alta | Despliegue | S | 3 | 04 | MLOps |
| HU-09 ⚙️ | Consultar riesgo en menos de 1 s | Media | Despliegue | M | 6 | 05 | MLOps |
| HU-10 ⚙️ | Reporte de drift por lote | Alta | Monitoreo y mantenimiento | L | 10 | 05 | DS/Steward |
| HU-11 ⚙️ | Rollback en menos de 30 min | Alta | Monitoreo y mantenimiento | S | 3 | 03 y 05 | MLOps, apoyo Líder/PO |
| HU-12 | Ahorro estimado vs. llamar al azar | Alta | Evaluación | L | 10 | 06 | Líder/PO, apoyo DS/Steward |
| HU-13 | Brecha de recall entre grupos | Alta | Evaluación | L | 10 | 06 | DS/Steward |
| HU-14 | Model card con evidencia | Media | Evaluación | L | 10 | 06 | DS/Steward |
| HU-15 | Explicación breve del riesgo (LLM) | Media | Despliegue | M | 6 | 07 | MLOps |
| HU-16 ⚙️ | Prompt solo se publica si pasa evaluación | Media | Monitoreo y mantenimiento | L | 10 | 07 | MLOps |
| HU-17 ⚙️ | Comunicado y post-mortem sin culpables | Alta | Monitoreo y mantenimiento | L | 10 | 05 y Final | Líder/PO |
| **Total HU** | | | | | **129** | | |

**Escala de tallas:** S = 3 h; M = 6 h; L = 10 h; XL = 16 h. **Spike de investigación adicional:** 3 h; no aparece en las 129 h ni está verificado como tarjeta del tablero.

**Tablero:** [agregar aquí la URL específica de GitHub Projects]. Repositorio: https://github.com/BrayhanJC/srtandina.

### 7.2. PERT para las siete historias operativas

Se conserva la estimación de tres puntos del equipo, que representa un cálculo **alternativo de compromiso para esas siete historias**, no horas adicionales a las mismas HU. `Te = (O + 4M + P)/6`.

| Historia | Estimación GitHub (h) | O (h) | M (h) | P (h) | PERT Te (h) |
|---|---:|---:|---:|---:|---:|
| HU-07 ⚙️ | 6 | 4 | 8 | 16 | 8,67 |
| HU-08 ⚙️ | 3 | 3 | 6 | 12 | 6,50 |
| HU-09 ⚙️ | 6 | 4 | 8 | 16 | 8,67 |
| HU-10 ⚙️ | 10 | 4 | 8 | 14 | 8,33 |
| HU-11 ⚙️ | 3 | 4 | 8 | 18 | 9,00 |
| HU-16 ⚙️ | 10 | 3 | 6 | 14 | 6,83 |
| HU-17 ⚙️ | 10 | 2 | 4 | 8 | 4,33 |
| **Subtotal** | **48** | **24** | **48** | **98** | **52,33** |

**Conciliación de cifras:** la estimación del tablero corresponde a **129 h de HU**. Las HU no operativas suman **81 h**; las siete operativas, **48 h**. Al sustituir las 48 h de operaciones por 52,33 h PERT y agregar el spike de 3 h, el **compromiso de planificación con incertidumbre asciende a 136,33 h** (`81 + 52,33 + 3`). Las 129 h del tablero y 136,33 h de planificación **no se contradicen**: corresponden a bases distintas. La decisión del `decision_log.md` que denomina «129 h incluido el spike» debe corregirse, pues el spike no aparece en esa suma.

### 7.3. Capacidad y compromiso

La declaración del equipo de **12, 8 y 8 horas por semana** equivale a 28 h brutas semanales. Los totales suministrados de 96/64/64 h presuponen **8 semanas**; este horizonte debe confirmarse como semanas efectivamente disponibles hasta S8.

| Integrante | h/semana | Semanas asumidas | Horas brutas | Enfoque | Capacidad efectiva |
|---|---:|---:|---:|---:|---:|
| Jorge Andrés Ángel (Líder/PO) | 12 | 8 | 96 | 0,70 | 67,20 h |
| Juan Camilo Zuluaga (DS/Steward) | 8 | 8 | 64 | 0,70 | 44,80 h |
| Brayhan Jaramillo (MLOps) | 8 | 8 | 64 | 0,70 | 44,80 h |
| **Total** | **28** | | **224** | | **156,80 h** |

- **Capacidad efectiva antes de reprocesos:** 156,80 h.
- **Reserva de reprocesos propuesta para aprobación:** 10 h (no confirmada por el equipo).
- **Capacidad neta si se aprueba esa reserva:** 146,80 h.
- **Compromiso de planificación (PERT + spike):** 136,33 h.
- **Holgura condicionada:** 10,47 h (`146,80 − 136,33`).

**Decisión condicionada:** con ocho semanas disponibles y una reserva aprobada de 10 h, el compromiso cabe por 10,47 h. Si el horizonte es menor o se materializan los riesgos R-01 a R-03, se recalcula la capacidad y se documenta cualquier redistribución o recorte de **extensiones opcionales**, sin eliminar las 17 historias canónicas por decisión unilateral. La comparación y su aprobación deben quedar registradas en `docs/decision_log.md`.

### 7.4. Spike de investigación

| Elemento | Definición |
|---|---|
| Pregunta | ¿Puede Ollama con `qwen3:4b` producir explicaciones en menos de 20 s en los computadores del equipo? |
| Tiempo máximo | 3 h, adicionales a las 129 h del tablero |
| Ejecutor propuesto | MLOps Engineer |
| Criterio de salida | Inventario mínimo de equipo y prueba local con tiempos documentados; comprobar si la mediana de respuestas es inferior a 20 s y registrar limitaciones. |
| Decisión informada | Continuar con LLM local si resulta viable o evaluar alternativa permitida; el Sponsor debe autorizar cualquier transmisión a proveedor LLM externo. |
| Estado del tablero | **Pendiente de crear/verificar** como tarjeta independiente. |

### 7.5. Marco de gestión

Se adopta **Kanban + CRISP-ML(Q)**: CRISP-ML(Q) organiza las fases técnicas y Kanban el flujo de trabajo entre encuentros. Cada iteración corresponde a la planificación, ejecución, revisión y entrega de los retos del FDS. Se mantienen planificación inicial breve, seguimiento asíncrono en GitHub Projects y revisión del cumplimiento antes de cada tag. No se exige una ceremonia Scrum diaria presencial; cada integrante actualiza bloqueos, evidencias y cambios mediante tablero y PR revisados.

### 7.6. Definición de Terminado (DoD)

| Criterio | Desde cuándo aplica | Evidencia |
|---|---|---|
| PR revisado por otro integrante antes de integrar a `main`. | Reto 01, para cambios nuevos | PR aprobado y fusionado. |
| `dvc repro` y `dvc.lock` actualizado para cambios del pipeline. | Reto 03 | Ejecución reproducible y archivos versionados. |
| CI en verde. | Reto 04 | Ejecución de GitHub Actions. |
| Decisiones relevantes registradas en `docs/decision_log.md`. | Reto 00 | Entrada fechada con alternativas, responsable y evidencia. |
| Riesgos revisados y actualizados, cuando corresponda. | Reto 01 | `docs/riesgos.md` vigente. |

### 7.7. Cronograma por fin de semana

| FDS | Reto | Responsable de ejecución (R) propuesto | Tag y plazo contractual |
|---|---|---|---|
| 2 | 02 — Gobierno y contrato de datos | DS/Steward | `r02` — 7 días después de FDS 2 |
| 2 | 03 — Reproducibilidad y versionado | MLOps | `r03` — 7 días después de FDS 2 |
| 3 | 04 — Pruebas e integración continua | Líder/PO (secundario MLOps) | `r04` — 7 días después de FDS 3 |
| 3 | 05 — Despliegue, monitoreo y operación | MLOps | `r05` — 7 días después de FDS 3 |
| 4 | 06 — Impacto, equidad y gobernanza | DS/Steward | `r06` — inicio de S8 |
| 4 | 07 — Asistente de explicación con LLM | Líder/PO, apoyo MLOps | `r07` — inicio de S8 |
| 4 / S8 | Proyecto Final — Simulacro y defensa | Líder/PO, con participación de todo el equipo | `final` — S8, antes de la primera defensa según horario acordado |

No se inventan fechas calendario: se consignan los plazos relativos del Contrato §6.2. Antes de la entrega deben quedar efectivamente asignados los responsables de las historias en el tablero.

### 7.8. Historia de mayor incertidumbre

**HU-11 — Rollback en menos de 30 minutos** se propone como historia peor estimada: GitHub le asigna **S = 3 h**, mientras PERT estima **9 h** (O = 4, M = 8, P = 18), una desviación de **+6 h** frente a la talla. La falta de experiencia operativa y la infraestructura limitada pueden ampliar el esfuerzo (R-01 y R-02). Se propone dividirla en preparación de aliases y runbook, prueba de recuperación y ensayo de `/health`; MLOps y Líder/PO trabajarán en pareja en caso de bloqueo. **La elección debe ratificarse en `docs/decision_log.md`** y el resultado real se comprobará en el Reto 05.

## 8. Riesgos principales

Los cinco riesgos de mayor exposición. El registro completo y vivo está en [`riesgos.md`](riesgos.md).

| Id | Categoría | Riesgo | P | I | Exposición | Responsable |
|----|-----------|--------|---|---|------------|-------------|
| R-01 | operación | Infraestructura insuficiente para MLOps, monitoreo y LLM | 4 | 5 | 20 | MLOps |
| R-03 | gestión | Tiempo disponible menor que el backlog comprometido | 5 | 4 | 20 | Líder/PO |
| R-02 | gestión | Habilidad más débil: despliegue y operación de servicios | 4 | 4 | 16 | Líder/PO |
| R-04 | datos | Lote que viola una regla bloqueante del contrato | 4 | 4 | 16 | DS/Steward |
| R-05 | modelo | Clase minoritaria: el modelo no supera gate.recall | 4 | 4 | 16 | DS/Steward |

Registro completo: [docs/riesgos.md](riesgos.md)
