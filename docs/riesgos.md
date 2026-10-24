# Registro de riesgos

> Se crea en el **Reto 01** y se actualiza en cada reto (contrato §10.2).
> Categorías: `datos` · `modelo` · `operación` · `ética` · `gestión` · `LLM` (negocio → `gestión`; legal o reputacional → `ética`).
> Estados: `abierto` · `mitigado` · `materializado` · `cerrado`.


| Id | Riesgo | Categoría | Prob. (1–5) | Impacto (1–5) | Respuesta | Responsable | Estado |
|---|---|---|---|---|---|---|---|
| R-01 | Infraestructura tecnológica insuficiente para ejecutar los componentes del SRT, especialmente los servicios de MLOps, monitoreo y LLM. | operación | 4 | 5 | Antes del Reto 05, realizar un inventario de equipos, memoria RAM, almacenamiento y recursos disponibles. Ejecutar una prueba de despliegue de los servicios requeridos. Si algún componente no funciona con la infraestructura disponible, documentar la limitación y evaluar una alternativa permitida por el contrato, dejando la decisión en `docs/decision_log.md`. | ML / MLOps Engineer | abierto |
| R-02 | Brechas de conocimiento técnico en herramientas como DVC, MLflow, Docker, integración continua o tecnologías LLM, que pueden generar errores y retrasos. | gestión | 4 | 4 | Antes de iniciar cada reto, identificar las tecnologías desconocidas y asignar una actividad práctica de aprendizaje con una prueba verificable. Si la prueba no se completa, solicitar apoyo técnico, reasignar actividades y registrar el impacto en el cronograma. | Líder / PO | abierto |
| R-03 | Disponibilidad insuficiente de tiempo por compromisos laborales, académicos y personales de los integrantes, que puede impedir finalizar los entregables en las fechas establecidas. | gestión | 5 | 4 | En el Reto 01, calcular la capacidad real del equipo en horas y contrastarla con el backlog estimado. Revisar semanalmente el avance; si las horas comprometidas superan la capacidad disponible, redistribuir tareas y negociar ajustes al alcance permitido antes de la siguiente fecha de entrega. | Líder / PO | abierto |

