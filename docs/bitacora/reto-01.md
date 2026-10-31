# Bitácora — Reto 01

**Proyecto:** Sistema de Retención Temprana (SRT) — Conecta Andina S.A.  
**Variante:** V4 — Hogar fibra premium  
**Referencia:** Reto 01 (versión lite), Contrato del sistema y `docs/charter.md`.  
**Estado:** Estimaciones conciliadas con la captura del tablero y protocolo PS-1 alineado con la RACI corregida; faltan aprobación de supuestos de capacidad y evidencias de ejecución.

## 1. PS-1. Prueba de incidentes (RACI)

Las respuestas siguientes se basan en la RACI registrada en `docs/charter.md` §6.2. Representan el protocolo definido por el equipo, no incidentes ocurridos.

| Caso hipotético | Quién decide (A) | Quién ejecuta (R) | Quién se informa (I) | Respuesta y referencia |
|---|---|---|---|---|
| **1. Lunes 07:10:** el lote incumple una regla bloqueante. | **Dueño del dato**, si se requiere decidir un cambio al contrato de datos. | **DS/Steward** valida, detiene el lote y escala el incumplimiento. | **Líder/PO** y **Sponsor**, como escalamiento operativo; el Sponsor figura como I en la fila del contrato. | No generar lista con el lote inválido; registrar regla y evidencia, activar `CRÍTICO-CONTRATO` y consultar al Dueño del dato. RACI: «Contrato de datos y sus cambios»; riesgo R-04. |
| **2. Martes:** la API supera el 10 % de errores tras la promoción. | **Líder/PO**, sobre rollback. | **MLOps Engineer** realiza reversión y verificación. | **Sponsor**, según la fila «Rollback ante incidente». | Diagnosticar, obtener decisión de rollback, restaurar `@previous` y verificar que `/health` informe la versión restaurada en **menos de 30 minutos desde la decisión**. RACI: «Rollback ante incidente»; HU-11. |
| **3. `@challenger`** mejora ROC-AUC, pero supera la brecha de equidad. | **Comité**, respecto a la brecha aceptable; **Líder/PO** conserva la A de promoción. | **DS/Steward** calcula/documenta la brecha; **MLOps** ejecutaría una promoción solo si estuviera autorizada. | **Sponsor**, de acuerdo con la fila «Brecha de equidad aceptable». | No promover mientras incumpla `recall_gap_senior_citizen ≤ 0.10`, salvo decisión formal de la autoridad competente y cumplimiento del gate. RACI: «Brecha de equidad aceptable» y «Promoción a @champion»; R-06. |
| **4. Se propone utilizar Claude API** con datos del extracto. | **Sponsor**, autoridad sobre el envío a un proveedor LLM externo. | **MLOps Engineer**, solo después de autorización. | **Líder/PO**, marcado como **I** en la RACI corregida; **DS/Steward, Dueño del dato y Comité** figuran como consultados (**C**). | No enviar datos sin autorización; revisar campos, privacidad y restricciones; excluir `customer_id` y `senior_citizen`. RACI: «Envío de datos a un proveedor de LLM externo». |

**Nota para PS-1:** La respuesta del caso 4 se corresponde con la RACI del `charter.md` corregido: Sponsor (A), MLOps (R) y Líder/PO (I). En el caso 1, el Dueño del dato es A para **cambios del contrato**; la invalidación del lote y su escalamiento son una acción operativa que ejecuta DS/Steward, sin modificar unilateralmente el contrato.

## 2. PS-2. Capacidad frente al backlog

### 2.1. Estimaciones verificadas en captura de GitHub Projects

La vista **Team items** permite observar **17 HU** (HU-01 a HU-17) en estado Backlog, con tallas, prioridad y un **Estimate acumulado de 129 h**. Las siete HU operativas están señaladas con ⚙️. En esa captura aparece **«No Assignees: 17»**; no se observa tarjeta del spike ni se verifican los campos de reto y fase CRISP-ML(Q).

| Concepto | Horas | Origen |
|---|---:|---|
| 10 historias no operativas | 81,00 | Suma de estimaciones GitHub |
| 7 historias operativas | 48,00 | Suma de estimaciones GitHub |
| **Subtotal HU del tablero** | **129,00** | Captura Team items |
| 7 historias operativas mediante PERT | 52,33 | Tabla `charter.md` §7.2 |
| Spike Ollama adicional | 3,00 | Planificación; pendiente de crear en tablero |
| **Compromiso de planificación** | **136,33** | **81 + 52,33 + 3** |

Las 129 h son la suma visible del tablero **sin spike**. Las 136,33 h no se suman a las 129 h; reemplazan las 48 h operativas por el cálculo PERT y agregan el spike. La decisión del 2026-10-26 ya fue **corregida en la versión `decision_log_corregido_r01.md`**: distingue 129 h de GitHub y 136,33 h de planificación. Verificar que esa versión reemplace el archivo del repositorio.

### 2.2. Capacidad declarada

Los valores de 96/64/64 h corresponden a las horas brutas de **ocho semanas supuestas** y no al número de semanas. Debe confirmarse que las ocho semanas son realmente útiles hasta S8.

| Integrante | Horas/semana | Semanas asumidas | Horas brutas | Enfoque | Capacidad efectiva |
|---|---:|---:|---:|---:|---:|
| Jorge Andrés Ángel — Líder/PO | 12 | 8 | 96 | 0,70 | 67,20 h |
| Juan Camilo Zuluaga — DS/Steward | 8 | 8 | 64 | 0,70 | 44,80 h |
| Brayhan Jaramillo — MLOps | 8 | 8 | 64 | 0,70 | 44,80 h |
| **Total** | **28** | | **224** | | **156,80 h** |

**Fórmula:** `(12 + 8 + 8) × 8 × 0,70 = 156,80 h`.

### 2.3. Comparación y decisión condicionada

| Indicador | Horas |
|---|---:|
| Capacidad efectiva previa a reprocesos | 156,80 |
| Reserva de reprocesos **propuesta, pendiente de aprobación** | 10,00 |
| Capacidad neta si se aprueba la reserva | 146,80 |
| Compromiso con PERT y spike | 136,33 |
| **Holgura condicionada** | **10,47** |

**Resultado PS-2:** Con **8 semanas efectivas** y **reserva de 10 h aprobada**, el compromiso cabe en la capacidad (`136,33 ≤ 146,80`). Este es un resultado **condicionado**, no una verificación de calendario. Si las semanas efectivas son menores, la holgura cambia y se debe replantear la planificación. Registrar la decisión definitiva y cualquier recorte de extensiones opcionales en `docs/decision_log.md`.

**Evidencia:** captura del tablero Team items aportada por el equipo; añadir la URL real de GitHub Projects y, si se requiere, imagen en `docs/bitacora/evidencias/`.

## 3. PS-3. Cobertura de categorías de riesgos

El archivo `docs/riesgos.md` recibido contiene siete riesgos y cubre las seis categorías obligatorias. El siguiente es el **conteo de la revisión documental** del archivo proporcionado; no es una salida capturada de la terminal del repositorio.

```text
datos      1
modelo     1
operación  1
ética      1
gestión    2
LLM        1
```

Ejecutar desde la raíz del repositorio el comando de la guía y pegar debajo su salida real:

```bash
for c in datos modelo operación ética gestión LLM; do
  printf "%-10s " "$c"
  grep -cE "\|[[:space:]]*$c[[:space:]]*\|" docs/riesgos.md
done
```

**Salida real PS-3:** [pegar resultado de la terminal].  
**Resultado:** pendiente de ejecución/verificación en el repositorio; el criterio de aceptación es que ningún conteo sea cero.

## 4. Historia con mayor incertidumbre

**Propuesta para validación por el equipo:** **HU-11 — Rollback en menos de 30 minutos**.

| Parámetro PERT | Horas |
|---|---:|
| Optimista (O) | 4 |
| Más probable (M) | 8 |
| Pesimista (P) | 18 |
| Tiempo esperado `Te=(O+4M+P)/6` | **9.0** |

**Por qué puede desbordarse:** su talla real en el tablero es **S = 3 h**, mientras PERT estima **9 h**; esa diferencia de **6 h** es la mayor subestimación positiva del tablero entre las historias operativas. Además, depende de infraestructura de servicios disponible, registro y restauración de `@previous`, y conocimiento de despliegue y operación (riesgos R-01 y R-02). El rango O–P de **14 h** refleja una incertidumbre relevante, aunque no demuestra por sí solo que sea la historia peor estimada.

**Acción elegida para proponer:** dividir la historia en preparación de aliases y runbook, ensayo de recuperación y verificación cronometrada de `/health`; ejecutar en pareja Líder/PO + MLOps, registrar bloqueos y realizar el ensayo en Reto 05. Si se supera la meta, corregir el procedimiento y registrar la desviación.

**Validación del equipo:** [fecha, responsables y enlace a decisión/evidencia].

## 5. Contribuciones del equipo

Registrar únicamente el trabajo efectivamente realizado, con commits, PR, capturas o actas verificables.

| Integrante | Rol | Actividades realmente realizadas | Evidencia |
|---|---|---|---|
| Jorge Andrés Ángel | Líder/PO | [completar] | [commit / PR / acta] |
| Juan Camilo Zuluaga Serna | DS/Steward | [completar] | [commit / PR / acta] |
| Brayhan Andrés Jaramillo Castaño | MLOps Engineer | [completar] | [commit / PR / acta] |

## 6. Pendientes para cerrar el Reto 01

- [ ] Confirmar que las **8 semanas** usadas en PS-2 son efectivamente disponibles hasta S8.
- [ ] Aprobar o ajustar la **reserva propuesta de 10 h** para reprocesos.
- [x] Conciliar **129 h del tablero** con **136,33 h PERT + spike** (cálculo documentado).
- [ ] Incorporar en el repositorio la versión corregida de `docs/decision_log.md` (129 h GitHub / 136,33 h de planificación).
- [ ] Crear/verificar la tarjeta del spike, los responsables y las fases CRISP-ML(Q) en GitHub Projects.
- [ ] Pegar la **salida real** de PS-3.
- [ ] Validar HU-11 como historia peor estimada y registrar la decisión.
- [ ] Completar contribuciones con evidencias verificables.
- [ ] Verificar tablero y publicación del tag `r01` cuando el conjunto esté listo.
