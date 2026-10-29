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


**Bloque peor justificado y por qué** ("todos están bien justificados" no cuenta):

## 4. KPIs

| Tipo | KPI | Línea base | Meta | Cómo se mide |
|---|---|---|---|---|
| Técnico | `pr_auc` | 0.6627 · `metrics.json`, (provisional) | ≥ 0.66 con el extracto real | `metrics.json` en cada `dvc repro` |
| Negocio (estimado) | `net_savings_vs_random` (ahorro frente a llamar al azar, Contrato §13) | 39 325.89 miles de COP · `metrics.json`, (provisional) | > 0 | `metrics.json` |
| Operación | Lista disponible el lunes a las 07:00 | Sin procedimiento (hoy se arma a mano) | 100 % de las semanas (Contrato §5) | Hora del archivo de la lista |
| Gestión | Tags `rNN` publicados a tiempo | — (primer reto) | 100 % antes de la fecha límite (Contrato §6.2) | Fecha del tag en GitHub |

## 5. Alcance y nivel de madurez MLOps objetivo


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
| Activar y supervisar el reentrenamiento mensual. | Data Scientist / Data Steward. | Permite verificar los datos y registrar la corrida antes de proponer una versión nueva. El pipeline de entrenamiento sigue siendo reproducible. |
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
| Umbral de decisión del negocio `decision_threshold` | **A** | C | R | I |  |  |
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


## 7. Backlog estimado, Definición de Terminado y cronograma

### 7.1. Resumen Historia de Usuario

| Id | Historia | Prioridad | Fase CRISP-ML(Q) | Talla | Estimación (h) | PERT Te (h) |
|----|----------|-----------|------------------|-------|----------------|-------------|
| HU-01 | Decisión que cambia el SRT y su valor | Alta | Comprensión del negocio y los datos | M | 6 | |
| HU-02 | Quién aprueba umbrales, equidad y rollback | Alta | Comprensión del negocio y los datos | S | 3 | |
| HU-03 | Pipeline se detiene con datos inválidos | Alta | Ingeniería de datos | L | 10 | |
| HU-04 | Excluir fuga de información | Alta | Ingeniería de datos | L | 10 | |
| HU-05 | Reconstruir el modelo de cualquier tag | Alta | Ingeniería del modelo | M | 6 | |
| HU-06 | Comparar al menos tres corridas | Media | Ingeniería del modelo | L | 10 | |
| HU-07 ⚙️ | Nada llega a main sin pruebas y gate | Alta | Evaluación | L | 10 | 8.7 |
| HU-08 ⚙️ | Lista de riesgo cada lunes 07:00 | Alta | Despliegue | M | 6 | 6.5 |
| HU-09 ⚙️ | Consultar riesgo en < 1 s | Media | Despliegue | L | 10 | 8.7 |
| HU-10 ⚙️ | Reporte de drift por lote | Alta | Monitoreo y mantenimiento | L | 10 | 8.3 |
| HU-11 ⚙️ | Rollback en < 30 min | Alta | Monitoreo y mantenimiento | L | 10 | 9.0 |
| HU-12 | Ahorro estimado vs. llamar al azar | Alta | Evaluación | L | 10 | |
| HU-13 | Brecha de recall entre grupos | Alta | Evaluación | L | 10 | |
| HU-14 | Model card con evidencia | Media | Evaluación | L | 10 | |
| HU-15 | Explicación breve del riesgo (LLM) | Media | Despliegue | M | 6 | |
| HU-16 ⚙️ | Prompt solo se publica si pasa evaluación | Media | Monitoreo y mantenimiento | M | 6 | 6.8 |
| HU-17 ⚙️ | Comunicado y post-mortem sin culpables | Alta | Monitoreo y mantenimiento | S | 3 | 4.3 |
| SPIKE | ¿Ollama qwen3:4b < 20 s en nuestros equipos? | Alta | Comprensión del negocio y los datos | S | 3 | |
| | **Total** | | | | **139** | **52.3** |

**Tallas:**
- **S** = 3 h 
- **M** = 6 h 
- **L** = 10 h 
- **XL** = 16 h. 

**PERT:** Te = (O + 4·M + P) / 6 (ver tabla de estimación PERT).

**Total comprometido** (Estimación de las historias normales y el spike + PERT de las ⚙️): 84 + 52.3 = **≈136.3 h**.

### 7.2 Estimación PERT — historias de usuario ⚙️

Fórmula: **Te = (O + 4·M + P) / 6**

- **O (optimista):** horas si todo sale bien a la primera.
- **M (más probable):** horas en un caso normal, con algún tropiezo. Pesa 4.
- **P (pesimista):** horas si casi todo sale mal, sin llegar a una catástrofe.
- Se divide entre 6 porque los pesos suman 1 + 4 + 1 = 6 (promedio ponderado).

#### Tabla de estimación

| Id | Historia | Reto | O (h) | M (h) | P (h) | Cálculo | Te (h) |
|----|----------|------|------:|------:|------:|---------|-------:|
| HU-07 ⚙️ | Como Líder, quiero que ningún cambio llegue a main sin pasar pruebas y quality gate, para no degradar producción | 04 | 4 | 8 | 16 | (4 + 4·8 + 16) / 6 = (4 + 32 + 16) / 6 = 52 / 6 | **8.7** |
| HU-08 ⚙️ | Como gerente comercial, quiero la lista de clientes en riesgo cada lunes a las 07:00, para planear la campaña | 04 | 3 | 6 | 12 | (3 + 4·6 + 12) / 6 = (3 + 24 + 12) / 6 = 39 / 6 | **6.5** |
| HU-09 ⚙️ | Como agente, quiero consultar el riesgo de un cliente en menos de un segundo, para usarlo durante la llamada | 05 | 4 | 8 | 16 | (4 + 4·8 + 16) / 6 = (4 + 32 + 16) / 6 = 52 / 6 | **8.7** |
| HU-10 ⚙️ | Como responsable del modelo, quiero un reporte de drift de cada lote, para decidir si reentrenar | 05 | 4 | 8 | 14 | (4 + 4·8 + 14) / 6 = (4 + 32 + 14) / 6 = 50 / 6 | **8.3** |
| HU-11 ⚙️ | Como sponsor, quiero volver a la versión anterior en menos de 30 minutos, para limitar el daño de una mala promoción | 03, 05 | 4 | 8 | 18 | (4 + 4·8 + 18) / 6 = (4 + 32 + 18) / 6 = 54 / 6 | **9.0** |
| HU-16 ⚙️ | Un cambio de prompt solo se publica si pasa su evaluación | 07 | 3 | 6 | 14 | (3 + 4·6 + 14) / 6 = (3 + 24 + 14) / 6 = 41 / 6 | **6.8** |
| HU-17 ⚙️ | Comunicado claro y post-mortem sin culpables | 05, S8 | 2 | 4 | 8 | (2 + 4·4 + 8) / 6 = (2 + 16 + 8) / 6 = 26 / 6 | **4.3** |
| | **Total** | | **24** | **48** | **98** | | **52.3** |

### 7.1. Marco de gestión

Se adopta un marco híbrido Kanban + CRISP-ML(Q), considerando la disponibilidad parcial del equipo, las dependencias técnicas y las fechas de entrega del curso. Cada iteración corresponde al ciclo de planificación, ejecución y revisión de los retos asignados a un FDS. Se conserva una reunión inicial de planificación, seguimiento asincrónico mediante GitHub Projects y revisión previa a cada entrega. Entre fines de semana, las tareas se coordinan mediante el tablero y pull requests, notificando oportunamente los bloqueos de infraestructura, conocimiento o tiempo.

### 7.2. Definición de Terminado (DoD)

| Criterio | Aplicación | Evidencia |
|---|---|---|
| Pull Request revisado por otro integrante antes de integrar a `main`. | Desde Reto 01. | PR aprobado y fusionado. |
| `dvc repro` reproduce el resultado y `dvc.lock` está actualizado. | Desde Reto 03, para cambios que afecten el pipeline. | Pipeline reproducido y archivos versionados. |
| Integración continua (CI) satisfactoria. | Desde Reto 04. | GitHub Actions en verde. |
| Decisiones relevantes registradas en `docs/decision_log.md`. | Desde Reto 00. | Entrada con responsable y evidencia. |
| Registro de riesgos revisado y actualizado según corresponda. | Desde Reto 01. | `docs/riesgos.md` vigente. |

### 7.3. Cronograma por fin de semana

| FDS | Reto | Responsable (R) | Tag y fecha límite |
|---|---|---|---|
| 2 | 02 — Gobierno y contrato de datos | Juan Camilo Zuluaga Serna (DS/Steward) | `r02` — FDS 2 + 7 días |
| 2 | 03 — Reproducibilidad y versionado | Brayhan Andrés Jaramillo Castaño (MLOps) | `r03` — FDS 2 + 7 días |
| 3 | 04 — Pruebas e integración continua | Brayhan Andrés Jaramillo Castaño (MLOps) | `r04` — FDS 3 + 7 días |
| 3 | 05 — Despliegue, monitoreo y operación | Brayhan Andrés Jaramillo Castaño (MLOps) | `r05` — FDS 3 + 7 días |
| 4 | 06 — Impacto, equidad y gobernanza | Juan Camilo Zuluaga Serna (DS/Steward) | `r06` — Inicio S8 |
| 4 | 07 — Asistente de explicación con LLM | Juan Camilo Zuluaga Serna (DS/Steward), con apoyo MLOps | `r07` — Inicio S8 |
| S8 | Proyecto Final — Simulacro y defensa | Jorge Andrés Ángel (Líder/PO), con participación del equipo | `final` — S8, según horario acordado |

Las asignaciones de responsabilidad se revisarán frente a la capacidad real del equipo y las dependencias de cada historia. Las fechas definitivas se completarán cuando se confirme el calendario académico.


## 8. Riesgos principales
Los cinco riesgos de mayor exposición. El registro completo y vivo está en [`riesgos.md`](riesgos.md).
