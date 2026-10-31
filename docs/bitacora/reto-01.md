# Bitácora — Reto 01

**Proyecto:** SRT, Conecta Andina S.A. — V4 Hogar fibra premium.  
**Fuentes:** `docs/charter.md`, `docs/riesgos.md`, `docs/decision_log.md` y especificación del Reto 01 (lite).  
**Alcance de evidencia:** respuestas PS-1 y cálculos documentados; las ejecuciones y aprobaciones pendientes se señalan como tales.

## 1. PS-1 — Prueba de incidentes con RACI

| Caso | Quién decide (A) | Quién ejecuta (R) | Quién se informa (I) | Respuesta prevista |
|---|---|---|---|---|
| Lunes 07:10: lote incumple regla bloqueante | **Dueño del dato** si es necesario decidir un cambio contractual; la regla existente es bloqueante y no requiere autorización para detener el lote. | **DS/Steward** | **Líder/PO** (escalamiento), **Sponsor** (I en fila del contrato) | Bloquear scoring y lista, registrar `CRÍTICO-CONTRATO`, reportar anomalía al Dueño del dato. RACI: contrato de datos; R-04. |
| Martes: API supera 10 % de errores | **Líder/PO**, autorización de rollback | **MLOps** | **Sponsor** | Restaurar `@previous` y comprobar `/health` en menos de 30 min desde la decisión. RACI: rollback; HU-11. |
| `@challenger` mejora ROC-AUC, pero viola equidad | **Comité** define brecha aceptable; **Líder/PO** decide promoción sujeta a gate y política. | **DS/Steward** evalúa y **MLOps** solo ejecuta si se aprueba. | **Sponsor** (fila equidad) | No promover con brecha superior a 0,10; elevar evidencia al Comité. RACI: equidad y promoción; R-06. |
| DS propone Claude API con extracto | **Sponsor**, autorización de envío externo | **MLOps** solo tras autorización | **Líder/PO** (I en RACI actualizada) | No transmitir información antes de autorización y revisión de campos; excluir `customer_id` y `senior_citizen`. RACI: proveedor LLM externo. |

**Evidencia PS-1:** respuestas de simulación preparadas; confirmar realización de la prueba oral de menos de dos minutos por caso si fue solicitada en sesión.

## 2. PS-2 — Capacidad y compromiso

### 2.1. Estimación de trabajo

| Concepto | Horas |
|---|---:|
| HU-01 a HU-17 en tablero GitHub (sin spike) | 129,00 |
| Diez HU no operativas | 81,00 |
| Siete HU operativas, estimación GitHub | 48,00 |
| Siete HU operativas, PERT que sustituye las 48 h | 52,33 |
| Spike adicional, máximo | 3,00 |
| **Compromiso total de planificación** | **136,33** |

**No se suman 129 y 52,33:** PERT reemplaza las 48 h operativas ya incluidas en las 129 h. Tablero informado: https://github.com/users/BrayhanJC/projects/1 (verificar acceso, campos de fase/operación y asignaciones).

### 2.2. Capacidad actualizada (escenario de cinco semanas)

| Integrante | Horas/semana originales | Semanas | Brutas | Enfoque | Efectivas |
|---|---:|---:|---:|---:|---:|
| Jorge Andrés Ángel | 12 | 5 | 60 | 0,70 | 42,00 |
| Juan Camilo Zuluaga | 8 | 5 | 40 | 0,70 | 28,00 |
| Brayhan Jaramillo | 8 | 5 | 40 | 0,70 | 28,00 |
| **Total** | **28** | | **140** | | **98,00** |

| Indicador | Horas |
|---|---:|
| Efectivas (28 × 5 × 0,70) | 98,00 |
| Reserva de reprocesos propuesta | −20,00 |
| **Netas** | **78,00** |
| Compromiso total | 136,33 |
| **Déficit inicial** | **−58,33** |

**Resultado PS-2:** el compromiso **no cabe** en la capacidad del escenario actualizado. La reserva y las cinco semanas vienen de `reto01-correcciones.md`; ratificar la aprobación y fecha real. La propuesta de aumentar horas a 15/11/11 por semana no se trata como aprobada. En ese escenario hipotético habría **109,50 h netas**; incluso si HU-01/HU-02 (9 h) se verifican como terminadas, quedarían **127,33 h pendientes**, todavía con déficit de **17,83 h**. No se recortan criterios de las 17 HU. Ver alternativas y responsable en `docs/charter.md` §7.3.1 y riesgo R-03.

## 3. PS-3 — Cobertura de riesgos

**Conteo esperado del archivo revisado** (no afirmar que es salida real de terminal):

```text
datos      1
modelo     1
operación  1
ética      1
gestión    2
LLM        1
```

Ejecutar desde la raíz del repositorio y adjuntar la **salida literal**:

```bash
for c in datos modelo operación ética gestión LLM; do
  printf "%-10s " "$c"
  grep -cE "\|[[:space:]]*$c[[:space:]]*\|" docs/riesgos.md
done
```

**Salida real:** [pendiente de pegar]. **Criterio:** ninguna categoría puede tener conteo cero.

## 4. Historia de mayor riesgo de subestimación

**HU-11**, rollback menor a 30 min, es la propuesta mejor sustentada: talla de GitHub **3 h**, PERT **9 h** (O=4; M=8; P=18), diferencia **+6 h**. Depende de disponibilidad de infraestructura, registro `@previous`, runbook y ensayo cronometrado (R-01, R-02). **Medida:** subdividir en aliases/runbook, recuperación y verificación `/health`; MLOps trabaja con apoyo del Líder/PO. **Ratificación del equipo:** [fecha y evidencia por completar].

## 5. Quién hizo qué

| Integrante | Rol | Aporte verificado | Evidencia real |
|---|---|---|---|
| Jorge Andrés Ángel | Líder/PO | [describir solo trabajo realizado] | [hash commit, PR o acta] |
| Juan Camilo Zuluaga Serna | DS/Steward | [describir solo trabajo realizado] | [hash commit, PR o acta] |
| Brayhan Andrés Jaramillo Castaño | MLOps | [describir solo trabajo realizado] | [hash commit, PR o acta] |

## 6. Evidencias y cierre

- [ ] Confirmar aprobación y fecha real de cinco semanas y reserva de 20 h.
- [ ] Decidir formalmente la respuesta al déficit; actualizar estimaciones y tablero sin suprimir historias ni mínimos contractuales.
- [ ] Confirmar asignación de HU-01 a HU-17 en GitHub Projects, campos de fase CRISP-ML(Q), siete etiquetas `operación` y tarjeta del spike (18 ítems esperados).
- [ ] Adjuntar captura vigente del tablero, verificando permisos de acceso del docente.
- [ ] Ejecutar PS-3 y pegar salida literal.
- [ ] Completar contribuciones con evidencia real.
- [ ] Ratificar HU-11 y registrar decisiones y uso de IA en `decision_log.md`.
- [ ] Confirmar `r00` y publicar `r01` solo tras cerrar las evidencias.
