---
name: nelson-meta-orchestrator
description: "Meta-orquestador del equipo AI de Nelson. Define el loop de decisión maestro: descomponer un goal, asignar subtareas a los agentes correctos, ejecutar en el orden adecuado, verificar resultados e iterar hasta la entrega. Es el cerebro que coordina a Julián, Mercedes, Beto, Ricky, Nico, Diego, Alma y JARVIS."
tags: [orchestrator, meta-agent, multi-agent, workflow, sdd, nelson]
related_skills:
  - nelson-spec-driven-workflow
  - nelson-ai-agents
  - nelson-task-memory
  - nelson-agent-routing
  - subagent-driven-development
  - nelson-eval-harness
---

# Nelson Meta-Orchestrator

## ¿Qué es esto?

El Meta-Orchestrator es el agente maestro del equipo AI de Nelson. No escribe código directamente — su trabajo es **pensar, descomponer, delegar y verificar**. Recibe un goal de Tony (o del sistema), lo rompe en subtareas, decide qué agente hace qué, en qué orden, con qué contexto, y no descansa hasta que el resultado esté entregado y verificado.

El Meta-Orchestrator codifica el loop de decisión central:

```
GOAL → DECOMPOSE → ASSIGN → EXECUTE → VERIFY → ITERATE → DONE
```

Cuando algo falla, no entra en pánico: aplica el patrón de retry correspondiente, escala si es necesario, y actualiza el estado del sistema.

Este skill vive encima del `nelson-spec-driven-workflow`: las fases de SDD (Spec, Design, Implementation, Verification) son el **mapa de ruta**; el Meta-Orchestrator es el **conductor del auto**.

---

## El Loop de Orquestación

### Pseudocódigo maestro

```python
def meta_orchestration_loop(goal: str, context: dict) -> DeliveryResult:
    state = MetaAgentState.IDLE
    task_graph = None
    results = {}
    retries = {}

    # --- FASE 1: DECOMPOSE ---
    state = MetaAgentState.DECOMPOSING
    task_graph = decompose_goal(goal, context)
    # task_graph es un DAG: nodos = subtareas, aristas = dependencias

    if not task_graph.is_valid():
        state = MetaAgentState.FAILED
        raise OrchestrationError("No se pudo descomponer el goal en subtareas válidas")

    # --- FASE 2: ASSIGN ---
    state = MetaAgentState.ASSIGNING
    assignments = {}
    for task in task_graph.nodes:
        agent = route_to_agent(task)
        assignments[task.id] = agent
        task.assigned_to = agent.name

    # --- FASE 3: EXECUTE ---
    state = MetaAgentState.EXECUTING
    execution_plan = build_execution_plan(task_graph)  # respeta dependencias

    for batch in execution_plan.batches:
        # batch = grupo de tareas que pueden correr en paralelo
        batch_results = execute_batch(batch, assignments)

        for task_id, result in batch_results.items():
            if result.is_failure():
                retry_result = handle_failure(
                    task=task_graph.get(task_id),
                    result=result,
                    retries=retries
                )
                if retry_result.is_failure():
                    state = MetaAgentState.FAILED
                    raise OrchestrationError(f"Tarea {task_id} falló tras reintentos")
                results[task_id] = retry_result
            else:
                results[task_id] = result

    # --- FASE 4: VERIFY ---
    state = MetaAgentState.VERIFYING
    verification = verify_delivery(goal, results, context)

    if not verification.passed:
        if verification.can_iterate:
            # Iterar: crear nuevas tareas para los gaps encontrados
            gap_tasks = verification.get_gap_tasks()
            task_graph.add_tasks(gap_tasks)
            state = MetaAgentState.EXECUTING  # volver a ejecutar
            # (en implementación real: loop recursivo con profundidad máxima)
        else:
            state = MetaAgentState.FAILED
            raise OrchestrationError(f"Verificación falló: {verification.failures}")

    # --- DONE ---
    state = MetaAgentState.DONE
    return DeliveryResult(
        goal=goal,
        results=results,
        verification=verification,
        task_graph=task_graph
    )
```

### Invariantes del loop

- **Nunca saltar la verificación.** Ejecutado != entregado.
- **El task graph es inmutable hasta VERIFY.** No agregar tareas mid-execution.
- **Cada tarea tiene exactamente un agente asignado.** Ambigüedad = bug del orchestrator.
- **El contexto viaja completo a cada agente.** No asumir que el agente "ya sabe".

---

## Descomposición de Goals

### Patrones de descomposición

#### Patrón 1: Por capa de stack

Para goals que tocan múltiples capas del sistema. El corte es vertical por responsabilidad.

```
Goal: "Agregar módulo de notificaciones"

Subtareas:
  T1: [Beto]    Diseñar arquitectura del módulo (schema, eventos, contratos)
  T2: [Julián]  Implementar backend: modelos, endpoints FastAPI, lógica de negocio
  T3: [Mercedes] Implementar frontend: componentes React, estado, UI
  T4: [Diego]   Configurar infraestructura: cola de mensajes, workers
  T5: [Alma]    Escribir suite de tests e2e
  T6: [JARVIS]  Code review y verificación final

Dependencias: T1 → {T2, T3, T4} → T5 → T6
```

#### Patrón 2: Por fase SDD

Para features nuevas desde cero. Sigue el flujo del `nelson-spec-driven-workflow`.

```
Goal: "Nueva feature X"

  FASE SPEC:
    T1: [JARVIS]  Escribir spec funcional + casos de uso
    T2: [Beto]    Revisar y aprobar spec

  FASE DESIGN:
    T3: [Beto]    Diseñar arquitectura técnica
    T4: [Julián]  Diseñar contratos de API (OpenAPI)
    T5: [Mercedes] Diseñar wireframes / componentes

  FASE IMPLEMENTATION:
    T6: [Ricky]   Implementar backend
    T7: [Nico]    Implementar frontend
    T8: [Diego]   Preparar infra / CI

  FASE VERIFICATION:
    T9: [Alma]    QA: tests funcionales + regresión
    T10: [JARVIS] Review final + entrega

Dependencias: {T1,T2} → {T3,T4,T5} → {T6,T7,T8} → {T9} → T10
```

#### Patrón 3: Por tipo de cambio (hotfix / refactor / bug)

Para cambios urgentes o acotados. Minimalista.

```
Goal: "Bugfix: endpoint /users/me retorna 500"

  T1: [Ricky]  Diagnosticar causa raíz (leer logs, reproducir)
  T2: [Ricky]  Implementar fix
  T3: [Alma]   Verificar fix + test de regresión
  T4: [Diego]  Deploy a staging y producción

Dependencias: T1 → T2 → T3 → T4
```

#### Patrón 4: Spike técnico / investigación

Para decisions de arquitectura o evaluación de tecnologías.

```
Goal: "Evaluar si migramos de REST a GraphQL"

  T1: [Beto]   Analizar pros/contras en contexto del proyecto
  T2: [Julián] Spike: implementar 1 endpoint en GraphQL
  T3: [Nico]   Spike: consumir desde React con Apollo
  T4: [Beto]   Consolidar hallazgos y recomendar decisión

Dependencias: T1 → {T2, T3} → T4
```

### Reglas de descomposición

1. **Una tarea = un agente = un resultado verificable.** Si una tarea necesita dos agentes, rompela.
2. **Granularidad mínima:** una tarea no debería durar más de 2 horas de trabajo de agente.
3. **Granularidad máxima:** no atomizar tanto que el overhead de coordinación supere el trabajo.
4. **Contexto explícito:** cada tarea debe incluir el contexto necesario (no asumir que el agente leyó la tarea anterior).
5. **Output definido:** antes de asignar, sabés qué va a producir la tarea (archivo, endpoint, decisión, etc.).

---

## Tabla de Routing de Agentes

| Agente   | Rol                        | Tipo de tarea                                                                 | Stack / Dominio                          |
|----------|----------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **Julián**   | Backend Senior         | Diseño de APIs, modelos SQLAlchemy, lógica de negocio compleja, performance   | Python, FastAPI, PostgreSQL, Pydantic    |
| **Ricky**    | Backend Dev            | Implementación de endpoints, CRUD, integraciones, fixes de backend            | Python, FastAPI, SQLAlchemy              |
| **Mercedes** | Frontend Senior        | Arquitectura de componentes React, estado global, design system, UX           | React, TypeScript, Zustand/Redux         |
| **Nico**     | Frontend Dev           | Implementación de componentes, páginas, formularios, llamadas a API           | React, TypeScript, CSS/Tailwind          |
| **Beto**     | Arquitecto             | Decisiones técnicas, diseño de sistemas, contratos entre servicios, ADRs      | Agnóstico de stack, foco en estructura   |
| **Diego**    | DevOps                 | Docker, CI/CD, despliegues, infra, monitoreo, variables de entorno            | Docker, GitHub Actions, cloud            |
| **Alma**     | QA                     | Tests unitarios, integración, e2e, regresión, validación de criterios         | pytest, Playwright, testing en general   |
| **JARVIS**   | Orchestrator / Senior  | Code review, specs, coordinación técnica, verificación de entrega             | Full stack awareness                     |
| **Julián+JARVIS** | IOT              | Arduino, ESP32, MQTT, sensores, telemetría                                    | nelson-iot-arduino-spike                 |
| **JARVIS**   | AUTOMATION             | n8n workflows, triggers, automatización de procesos                           | nelson-automation-n8n                    |
| **JARVIS+Nelson** | DOMAIN          | ForestAI, MRV carbono, NetFlora, índices multiespectrales, Fleet forestal     | nelson-forestai-roadmap, nelson-mrv-reports, nelson-netflora |
| **Nico**     | SCRAPING               | Sitrack, portales web, extracción de datos de flota                           | nelson-sitrack-scraper, nelson-browser-agent |

### Reglas de routing

```python
def route_to_agent(task: Task) -> Agent:
    keywords = task.get_keywords()

    # Reglas de prioridad (orden importa)
    if task.type == TaskType.ARCHITECTURE or "diseño de sistema" in keywords:
        return agents.BETO

    if task.type == TaskType.SPEC or task.type == TaskType.REVIEW:
        return agents.JARVIS

    if task.type == TaskType.QA or task.type == TaskType.TESTING:
        return agents.ALMA

    if task.type == TaskType.DEVOPS or any(k in keywords for k in ["deploy", "docker", "ci", "infra"]):
        return agents.DIEGO

    # Backend: senior vs dev según complejidad
    if task.layer == Layer.BACKEND:
        if task.complexity >= Complexity.HIGH or task.type == TaskType.DESIGN:
            return agents.JULIAN
        else:
            return agents.RICKY

    # Frontend: senior vs dev según complejidad
    if task.layer == Layer.FRONTEND:
        if task.complexity >= Complexity.HIGH or task.type == TaskType.DESIGN:
            return agents.MERCEDES
        else:
            return agents.NICO

    # Fallback: JARVIS decide
    return agents.JARVIS
```

### Cuándo usar JARVIS vs agente especializado

- **JARVIS** cuando: la tarea cruza múltiples capas, es una decisión de criterio, necesita contexto global del proyecto, o es un review/verificación.
- **Agente especializado** cuando: la tarea está claramente acotada a una capa y no requiere perspectiva global.

---

## Ejecución Paralela vs Secuencial

### El grafo de dependencias decide

La ejecución es paralela siempre que las dependencias lo permitan. El Meta-Orchestrator construye un DAG y ejecuta en batches:

```python
def build_execution_plan(task_graph: DAG) -> ExecutionPlan:
    """
    Topological sort + agrupación en batches paralelos.
    Batch N contiene todas las tareas cuyos predecesores
    están en batches anteriores.
    """
    batches = []
    remaining = set(task_graph.nodes)
    completed = set()

    while remaining:
        # Tareas listas: todas sus dependencias ya completadas
        ready = {
            task for task in remaining
            if all(dep in completed for dep in task.dependencies)
        }
        if not ready:
            raise CircularDependencyError("Ciclo detectado en el task graph")

        batches.append(list(ready))
        completed.update(ready)
        remaining -= ready

    return ExecutionPlan(batches=batches)
```

### Reglas de paralelización

**Ejecutar en paralelo cuando:**
- Las tareas no comparten estado mutable
- No hay dependencia de datos entre ellas
- Son en capas independientes (ej: backend + frontend + infra simultáneos)
- El riesgo de conflicto es bajo (archivos distintos, módulos distintos)

**Ejecutar secuencialmente cuando:**
- Una tarea produce el input de otra (contrato de API → implementación)
- Hay riesgo de conflicto de archivos o migraciones de DB
- La tarea anterior puede invalidar la siguiente (ej: cambio de schema)
- La tarea requiere verificación humana antes de continuar

**Ejemplo de plan de ejecución:**
```
Batch 1 (paralelo): [T1: Beto-arquitectura]
Batch 2 (paralelo): [T2: Julián-API design, T5: Mercedes-UI design]
Batch 3 (paralelo): [T3: Ricky-backend impl, T6: Nico-frontend impl, T4: Diego-infra]
Batch 4 (secuencial): [T7: Alma-QA]
Batch 5 (secuencial): [T8: JARVIS-review]
```

### Límite de paralelismo

No lanzar más de **4 agentes en paralelo** a menos que el sistema lo soporte explícitamente. El overhead de coordinación y los conflictos de contexto aumentan con la concurrencia.

---

## Manejo de Fallos y Patrones de Retry

### Taxonomía de fallos

```python
class FailureType(Enum):
    AGENT_ERROR        = "error del agente (bug, contexto insuficiente)"
    CONTEXT_MISSING    = "falta información para ejecutar la tarea"
    DEPENDENCY_FAILED  = "una tarea previa falló y bloquea esta"
    SPEC_AMBIGUOUS     = "la spec es ambigua, el agente no puede decidir"
    VERIFICATION_FAIL  = "el output no cumple los criterios de aceptación"
    TIMEOUT            = "la tarea excedió el tiempo esperado"
    CONFLICT           = "conflicto con otra tarea (archivos, schema, etc.)"
```

### Estrategias de retry

```python
def handle_failure(task: Task, result: FailureResult, retries: dict) -> TaskResult:
    failure_type = classify_failure(result)
    attempt = retries.get(task.id, 0)

    if attempt >= MAX_RETRIES:
        return escalate_to_human(task, result)

    retries[task.id] = attempt + 1

    match failure_type:
        case FailureType.CONTEXT_MISSING:
            # Enriquecer contexto y reintentar con el mismo agente
            enriched_context = gather_missing_context(task, result)
            return retry_task(task, enriched_context, same_agent=True)

        case FailureType.SPEC_AMBIGUOUS:
            # Escalar a JARVIS para clarificar spec antes de reintentar
            clarification = ask_jarvis_to_clarify(task.spec)
            task.spec = clarification
            return retry_task(task, same_agent=True)

        case FailureType.AGENT_ERROR:
            # Primer intento: mismo agente. Segundo: agente alternativo
            if attempt == 0:
                return retry_task(task, same_agent=True)
            else:
                alt_agent = get_alternative_agent(task.assigned_to)
                return retry_task(task, agent=alt_agent)

        case FailureType.VERIFICATION_FAIL:
            # Crear tarea de corrección explícita
            fix_task = create_fix_task(task, result.verification_failures)
            return execute_single_task(fix_task)

        case FailureType.CONFLICT:
            # Serializar: esperar a que la tarea conflictiva termine
            wait_for_conflict_resolution(result.conflicting_task)
            return retry_task(task, same_agent=True)

        case FailureType.TIMEOUT:
            # Descomponer la tarea en subtareas más pequeñas
            subtasks = decompose_further(task)
            return execute_batch(subtasks, assignments)

        case _:
            return escalate_to_human(task, result)
```

### Política de escalación

| Intentos | Acción                                      |
|----------|---------------------------------------------|
| 1        | Retry con contexto enriquecido              |
| 2        | Retry con agente alternativo o spec aclarada |
| 3        | Escalar a JARVIS para diagnóstico           |
| 4+       | Escalación a Tony / pausa para input humano |

### Fail-fast vs fail-safe

- **Fail-fast** en tareas bloqueantes (ej: diseño de arquitectura): si Beto no puede entregar el diseño, no tiene sentido que Ricky empiece a implementar. Detener el batch.
- **Fail-safe** en tareas no bloqueantes (ej: tests adicionales de Alma): marcar como pendiente, continuar con el flujo principal, revisar al final.

---

## Integración con Nelson Spec-Driven Workflow

El Meta-Orchestrator mapea cada fase del SDD a responsabilidades de agentes:

### Fase SPEC

```
Responsable principal: JARVIS
Participantes: Beto (revisión técnica), Tony (aprobación)

Tareas típicas:
  - Escribir spec funcional (user stories, casos de uso, criterios de aceptación)
  - Definir contratos de datos (inputs/outputs de la feature)
  - Documentar constraints y dependencias

Gate de salida: spec aprobada por Tony y Beto antes de continuar
```

### Fase DESIGN

```
Responsable principal: Beto
Participantes: Julián (API design), Mercedes (UI/UX design)

Tareas típicas:
  - ADR (Architecture Decision Record) si hay decisión técnica nueva
  - Diseño de schema de DB (si aplica)
  - Contratos de API: OpenAPI spec
  - Diseño de componentes frontend: árbol de componentes, flujo de estado

Gate de salida: todos los contratos definidos y aprobados
           → Ricky y Nico pueden empezar en paralelo sin bloquearse
```

### Fase IMPLEMENTATION

```
Backend: Ricky (implementación) + Julián (revisión de código)
Frontend: Nico (implementación) + Mercedes (revisión de código)
Infra: Diego

Regla crítica: implementar contra los contratos definidos en DESIGN,
               no rediseñar durante la implementación.

Si aparece un gap en el diseño → volver a DESIGN, no improvisar.
```

### Fase VERIFICATION

```
Responsable principal: Alma
Participantes: JARVIS (review final), Diego (deploy a staging)

Criterios de verificación:
  - Todos los tests pasan (unit + integration + e2e)
  - Criterios de aceptación de la spec cumplidos
  - No hay regresiones
  - Performance dentro de los límites definidos

Gate de salida: JARVIS firma la entrega → Tony recibe el resultado
```

### Handoff entre fases

```python
def can_advance_phase(current_phase: Phase, results: dict) -> bool:
    match current_phase:
        case Phase.SPEC:
            return results["spec"].approved_by_tony and results["spec"].reviewed_by_beto
        case Phase.DESIGN:
            return (results["api_contracts"].complete
                    and results["db_schema"].complete
                    and results["ui_design"].complete)
        case Phase.IMPLEMENTATION:
            return (results["backend"].builds_clean
                    and results["frontend"].builds_clean
                    and results["tests"].unit_pass)
        case Phase.VERIFICATION:
            return results["qa"].all_criteria_met and results["review"].approved
```

---

## Ejemplo Completo: De Goal a Entrega

### Escenario: Tony pide "Agregar sistema de notificaciones push"

```
INPUT: Tony → "Necesito notificaciones push para los usuarios cuando
               les llega un mensaje nuevo. Web y mobile."
```

#### Paso 1: Recepción y contextualización

```python
context = {
    "project": "nelson-app",
    "stack": {"backend": "FastAPI/Python", "frontend": "React"},
    "existing_modules": ["auth", "users", "messages"],
    "constraints": ["no introducir nueva infra de pago", "compatible con PWA"]
}
goal = "Implementar sistema de notificaciones push (web + mobile)"
```

#### Paso 2: Descomposición (DECOMPOSING)

```
T1  [Beto]      Diseñar arquitectura: FCM vs Web Push API, schema de suscripciones
T2  [JARVIS]    Escribir spec: casos de uso, criterios de aceptación, contratos
T3  [Julián]    Diseñar API: endpoints de suscripción, envío, historial (OpenAPI)
T4  [Mercedes]  Diseñar UI: componente de permisos, badge de notificaciones
T5  [Ricky]     Implementar backend: modelos, endpoints, integración FCM
T6  [Diego]     Configurar: service worker en build, variables FCM, CI
T7  [Nico]      Implementar frontend: hook useNotifications, UI components
T8  [Alma]      Tests: unit backend, integración API, e2e flujo completo
T9  [JARVIS]    Review final + verificación de criterios de aceptación

Dependencias:
  {T1, T2} → T3
  {T1, T2} → T4
  T3 → T5
  T4 → T7
  {T5, T6} → T8
  T7 → T8
  T8 → T9
```

#### Paso 3: Plan de ejecución (ASSIGNING + plan)

```
Batch 1 (paralelo):   T1 (Beto), T2 (JARVIS)
Batch 2 (paralelo):   T3 (Julián), T4 (Mercedes)
Batch 3 (paralelo):   T5 (Ricky), T6 (Diego), T7 (Nico)
Batch 4 (secuencial): T8 (Alma)
Batch 5 (secuencial): T9 (JARVIS)
```

#### Paso 4: Ejecución (EXECUTING)

```
[Batch 1]
  Beto entrega: ADR con decisión FCM + schema de tabla push_subscriptions
  JARVIS entrega: spec con 8 user stories y criterios de aceptación

[Batch 2]
  Julián entrega: openapi.yaml con /subscriptions, /notifications/send, /notifications/history
  Mercedes entrega: árbol de componentes + diseño de PermissionPrompt y NotificationBadge

[Batch 3]
  Ricky entrega: PushSubscription model, 3 endpoints FastAPI, FCM client wrapper
  Diego entrega: service worker configurado, Dockerfile actualizado, secrets en CI
  Nico entrega: useNotifications hook, PermissionPrompt component, badge en header

[Batch 4]
  Alma ejecuta:
    - 12 tests unitarios backend → 11/12 pasan
    - T_012 falla: endpoint /notifications/history retorna 422 con user sin suscripción
    → handle_failure: FailureType.VERIFICATION_FAIL
    → crea T5b: [Ricky] fix handle empty subscription case in history endpoint
    → T5b ejecuta → fix implementado → Alma re-corre → 12/12 pasan
    - Tests e2e → 5/5 pasan

[Batch 5]
  JARVIS revisa:
    - Criterios de aceptación: 8/8 cumplidos ✓
    - Code quality: sin issues críticos ✓
    - Performance: latencia de envío < 200ms ✓
    → DELIVERY APPROVED
```

#### Paso 5: Entrega (DONE)

```
OUTPUT → Tony:
  "Sistema de notificaciones push implementado.
   - Backend: 3 endpoints nuevos en /api/v1/notifications
   - Frontend: componente de permisos + badge en tiempo real
   - Infra: FCM configurado, service worker activo
   - Tests: 17 tests, todos verdes
   - Docs: spec actualizada en /docs/notifications.md"
```

---

## Máquina de Estados del Meta-Agente

### Estados

```
┌─────────────────────────────────────────────────────────────┐
│                    META-AGENT STATE MACHINE                  │
│                                                              │
│   ┌──────┐                                                   │
│   │ IDLE │ ◄─────────────────────────────────────┐          │
│   └──┬───┘                                       │          │
│      │ receive_goal()                            │ reset()  │
│      ▼                                           │          │
│   ┌────────────┐   decomposition_failed()   ┌────┴────┐     │
│   │DECOMPOSING │ ──────────────────────────►│ FAILED  │     │
│   └──────┬─────┘                            └────┬────┘     │
│          │ decomposition_ok()                    │          │
│          ▼                                       │          │
│   ┌──────────┐   assignment_failed()             │          │
│   │ASSIGNING │ ──────────────────────────────────┤          │
│   └────┬─────┘                                   │          │
│        │ all_assigned()                          │          │
│        ▼                                         │          │
│   ┌──────────┐   unrecoverable_failure()         │          │
│   │EXECUTING │ ──────────────────────────────────┤          │
│   └────┬─────┘                                   │          │
│        │ all_batches_complete()                  │          │
│        ▼                                         │          │
│   ┌──────────┐   verification_failed_no_retry()  │          │
│   │VERIFYING │ ──────────────────────────────────┘          │
│   └────┬─────┘                                              │
│        │ verification_passed()    gaps_found()              │
│        │                          ──────────────►EXECUTING  │
│        ▼                                                     │
│   ┌──────┐                                                   │
│   │ DONE │                                                   │
│   └──────┘                                                   │
└─────────────────────────────────────────────────────────────┘
```

### Definición de estados

| Estado        | Descripción                                                            | Acciones válidas                              |
|---------------|------------------------------------------------------------------------|-----------------------------------------------|
| `IDLE`        | Esperando un goal. Estado inicial y post-reset.                        | `receive_goal()` → DECOMPOSING                |
| `DECOMPOSING` | Analizando el goal, construyendo el task graph.                        | `decomposition_ok()` → ASSIGNING              |
|               |                                                                        | `decomposition_failed()` → FAILED             |
| `ASSIGNING`   | Mapeando cada tarea al agente correspondiente.                         | `all_assigned()` → EXECUTING                  |
|               |                                                                        | `assignment_failed()` → FAILED                |
| `EXECUTING`   | Corriendo los batches del execution plan. Maneja retries internamente. | `all_batches_complete()` → VERIFYING          |
|               |                                                                        | `unrecoverable_failure()` → FAILED            |
| `VERIFYING`   | Alma + JARVIS verifican que el output cumple los criterios.            | `verification_passed()` → DONE                |
|               |                                                                        | `gaps_found()` → EXECUTING (iteración)        |
|               |                                                                        | `verification_failed_no_retry()` → FAILED     |
| `DONE`        | Entrega completada. Resultado disponible para Tony.                    | `reset()` → IDLE                              |
| `FAILED`      | Fallo no recuperable. Requiere intervención humana.                    | `reset()` → IDLE (después de intervención)    |

### Persistencia de estado

El estado del Meta-Orchestrator **debe persistirse** en `nelson-task-memory` después de cada transición. Si el proceso se cae en EXECUTING, debe poder retomar desde el último batch completado, no desde cero.

Además de checkpoints en task-memory, para operación real conviene persistir eventos finos por run (timeline) y estado de control por sub-tarea (pause/resume/cancel/retry). Ver referencia: `references/timeline-subtask-control-2026-05-29.md`.

```python
def transition(self, new_state: MetaAgentState, data: dict = None):
    self.state = new_state
    self.task_memory.save_checkpoint({
        "state": new_state,
        "task_graph": self.task_graph.serialize(),
        "results": self.results,
        "timestamp": datetime.utcnow().isoformat()
    })
```

---

## Operación en caliente: timeline persistente + control manual de subtareas

Desde esta sesión, el patrón recomendado para evolución segura del orquestador incluye dos piezas:

1) Timeline persistente por run (SQLite)
- Tabla `orchestration_events` con eventos `planned`, `execute_started`, `verify`, `completed/failed`, `subtask_control`.
- Cada transición relevante debe llamar `_log_event(...)`.
- Esto evita perder trazabilidad cuando la UI se recarga o cambia de sesión.

2) Control manual de subtareas
- Tabla `subtask_control` con `control_state` (`active`, `paused`, `cancelled`).
- API de control por subtask: `pause`, `resume`, `cancel`, `retry`.
- En el loop de ejecución, filtrar por `control_state` antes de ejecutar.

Endpoints de operación (FastAPI):
- `GET /runs/{task_id}/timeline`
- `GET /runs/{task_id}/subtasks`
- `POST /runs/{task_id}/subtasks/{subtask_id}/control`

Regla de implementación:
- `cancel` debe marcar subtask en `cancelled` y excluirla de ejecución.
- `retry` debe limpiar `result/error` y volver `status=pending`.

### Shadow deploy sin tocar producción

Cuando no se puede reiniciar systemd de producción (falta sudo o ventana de cambio), validar cambios así:

1. Levantar backend parcheado en puerto alterno (ej. `8754`).
2. Levantar dashboard con proxy al backend alterno usando env vars:
   - `ORCH_API_URL=http://127.0.0.1:8754`
   - `ORCH_WS_URL=ws://127.0.0.1:8754`
3. Exponer dashboard por Cloudflare quick tunnel y validar E2E.

Esto reduce riesgo: se prueba todo el circuito UI+API sin impactar el servicio principal (`8744`).

Ver runbook detallado en `references/timeline-subtask-control-and-shadow-deploy-2026-05-29.md`.

## API operativa recomendada (timeline + control de subtareas)

Para operación real desde dashboard, exponer endpoints de observabilidad y control fino por run:

- `GET /runs/{task_id}/timeline` → eventos persistentes de la ejecución.
- `GET /runs/{task_id}/subtasks` → subtareas con `control_state`.
- `POST /runs/{task_id}/subtasks/{subtask_id}/control` con acción `pause|resume|cancel|retry`.

Patrón de persistencia:
- Tabla `orchestration_events` para timeline.
- Tabla `subtask_control` para estado manual por subtask.
- Loggear eventos en hitos: `planned`, `execute_started`, `verify`, `completed|failed`, `subtask_control`.

Regla operativa:
- Antes de ejecutar batch, leer `control_state` y excluir `paused/cancelled`.
- `cancelled` debe reflejarse en `TaskStatus.CANCELLED` para evitar ejecución accidental.

Referencia completa: `references/timeline-subtask-control.md`.

## Agregar categorías al executor.py

Cuando hay un nuevo dominio de tareas no cubierto por las categorías existentes, agregar en `/home/server/nelson/meta-orchestrator/nelson_orchestrator/executor.py`:

**1. En `CATEGORY_SKILLS`:**
```python
"IOT":        ["equipo-nelson", "nelson-iot-arduino-spike", "nelson-external-integrations"],
"AUTOMATION": ["equipo-nelson", "nelson-automation-n8n", "nelson-background-jobs"],
"DOMAIN":     ["equipo-nelson", "nelson-forestai-roadmap", "nelson-mrv-reports", "nelson-netflora"],
"SCRAPING":   ["equipo-nelson", "nelson-browser-agent", "nelson-sitrack-scraper"],
```

**2. En `KEYWORD_SKILLS`** (para inferencia automática por keywords del goal):
```python
"iot":      "nelson-iot-arduino-spike",
"n8n":      "nelson-automation-n8n",
"mrv":      "nelson-mrv-reports",
"sitrack":  "nelson-sitrack-scraper",
```

**3. En `CATEGORY_AGENT`** (para logging):
```python
"IOT":        "Julián + JARVIS",
"AUTOMATION": "JARVIS",
"DOMAIN":     "JARVIS + Nelson",
"SCRAPING":   "Nico",
```

**4. En el docstring inicial** — actualizar el mapa de categorías.

**Verificar compilación:**
```bash
python3 -m py_compile nelson_orchestrator/executor.py && echo "OK"
```

Las categorías activas al 2026-05-31: BACKEND, FRONTEND, RAG/AI, SPEC, QA, INFRA, DOCS, SECURITY, BROWSER, VISION, AUDIO, EXTERNAL, IOT, AUTOMATION, DOMAIN, SCRAPING, UNKNOWN.

## Evolución incremental (anti-duplicación)

Cuando el usuario pida “llevarlo a META-Agente completo”, la acción correcta es **extender el Orchestrator existente** y no crear una plataforma paralela.

Regla operativa:
1. Auditar gap sobre la base actual.
2. Definir hardening por fases (gates, handoff, policy, observabilidad).
3. Implementar en el repo actual con backward compatibility.
4. Validar compile + smoke E2E antes de rollout.

Referencia de implementación real: `references/incremental-hardening-gates-handoffs-policy-2026-06.md`

## Hardening incremental del Orchestrator (regla Tony)

Cuando el usuario pida evolucionar el sistema META-Agente, **no crear un sistema paralelo** ni re-brandear como “v2” si ya existe una base funcional.

Regla operativa:
1. Auditar primero lo existente (endpoints, tablas, UI, hooks).
2. Publicar GAP "actual vs objetivo".
3. Implementar por fases sobre el repo actual (hardening incremental).
4. Validar E2E por fase sin romper plan/confirm/execute/timeline/subtasks.

Frase gatillo del usuario que activa esta regla:
- “no quiero que hagamos las cosas 2 veces”

Aplicación recomendada (orden):
- Fase 1: gates + handoff base + métricas run
- Fase 2: política declarativa de transición + validación estricta de handoff
- Fase 3: registro de conectores con capabilities/fallback + health summary

Ver detalle implementado en: `references/meta-orchestrator-hardening-2026-06-02.md`

## Pitfalls (No cagarse en estas)

### 0. Duplicar el sistema en vez de endurecer el existente

**Problema:** crear un “Orchestrator v2” paralelo cuando el orquestador actual ya tiene loop, timeline, control de subtareas y dashboard.

**Regla:** aplicar mejoras como **hardening incremental** sobre el repo actual. Reusar primero, extender después. Evitar rebranding técnico o caminos duplicados.

Referencia de implementación validada: `references/meta-orchestrator-hardening-2026-06-02.md`.

### 0. Duplicar el orquestador (prohibido)

**Problema:** Proponer "Orchestrator v2" o sistema paralelo cuando el actual ya cubre el flujo base.

**Impacto:** retrabajo, desalineación con Tony y pérdida de foco operativo.

**Regla:** evolución incremental sobre el repo actual. Antes de diseñar algo nuevo, auditar: qué existe, qué falta, y cómo extender DB/API/UI sin romper plan→confirm→execute→verify.

Referencia práctica: `references/hardening-fase1-gates-handoffs-metrics-2026-06-02.md`.

### 1. El God Task

**Problema:** Una tarea tan grande que no tiene un output verificable claro.
```
MAL:  T1: [Ricky] "Implementar todo el backend del módulo de pagos"
BIEN: T1: [Ricky] "Implementar endpoint POST /payments con validación Stripe webhook"
     T2: [Ricky] "Implementar endpoint GET /payments/{id} con autorización por user_id"
```

### 2. Contexto incompleto en la tarea

**Problema:** El agente arranca sin saber qué ya existe, qué se decidió antes, o cuáles son los contratos.

```python
# MAL:
task = Task("Implementar frontend de notificaciones", agent=NICO)

# BIEN:
task = Task(
    description="Implementar componente NotificationBadge en el header",
    agent=NICO,
    context={
        "api_contract": "GET /api/v1/notifications/unread-count",
        "design_spec": designs["NotificationBadge"],
        "existing_header_component": "src/components/Header.tsx",
        "state_management": "Zustand, store en src/stores/notifications.ts"
    }
)
```

### 3. Paralelizar cuando no se debe

**Problema:** Lanzar implementación de backend y frontend antes de que los contratos de API estén cerrados. Resultado: Nico implementa contra una API que Ricky cambió.

**Regla:** Los contratos de API son el contrato entre backend y frontend. Si no están firmados, no hay paralelismo entre ellos.

### 4. Saltarse el gate de DESIGN

**Problema:** Pasar directo de SPEC a IMPLEMENTATION para "ir más rápido". Resultado: Ricky y Nico implementan cosas incompatibles y hay que tirar trabajo.

**Regla:** Nunca. El gate de DESIGN existe para eso. Es más rápido diseñar bien que refactorizar.

### 5. Verificación superficial

**Problema:** JARVIS hace "review" mirando si el código compila. No verifica los criterios de aceptación de la spec.

**Regla:** La verificación final debe referenciar explícitamente cada criterio de aceptación de la spec y confirmar que está cumplido.

### 6. Ignorar el estado persistido

**Problema:** Si el orquestador se reinicia, vuelve a ejecutar tareas que ya estaban completas.

**Regla:** Siempre cargar el checkpoint de `nelson-task-memory` al iniciar. Si hay tareas `DONE` en el checkpoint, no re-ejecutarlas.

### 7. Escalar a humano demasiado tarde

**Problema:** El orquestador reintenta 5 veces antes de escalar. Tony pierde tiempo esperando.

**Regla:** Si en el intento 3 no hay progreso visible, escalar de inmediato. El tiempo de Tony vale más que el orgullo del sistema.

### 8. Mezclar roles de agentes

**Problema:** Pedirle a Nico que también diseñe la arquitectura del estado global porque "es frontend".

**Regla:** El routing es por expertise, no por disponibilidad. Si Nico está libre y Mercedes está ocupada, la decisión de arquitectura la espera a Mercedes o la toma JARVIS, pero no la hace Nico.

### 9. Task graph sin persistencia

**Problema:** El task graph vive solo en memoria. Si algo explota, se pierde todo el estado.

**Regla:** Serializar el task graph a `nelson-task-memory` después de cada modificación (creación, asignación, completado de tarea).

### 11. Ejecutar sin respetar control manual de sub-tareas

**Problema:** El operador pausa/cancela una sub-tarea pero el loop de ejecución igual la procesa en el siguiente batch.

**Regla:** Antes de cada iteración de EXECUTING, leer control por sub-tarea y filtrar:
- `paused` -> no ejecutar en ese ciclo
- `cancelled` -> marcar `TaskStatus.CANCELLED` y excluir
- `retry` -> volver a `pending` limpiando `result/error`

Usar endpoint explícito de control y dejar rastro en timeline persistente.

### 13. No expandir categorías del executor cuando crece el dominio

**Problema:** El executor tiene categorías hardcodeadas. Cuando el equipo agrega skills de nuevos dominios (IoT, automatización, ForestAI, Fleet), el routing va a UNKNOWN en vez del agente correcto.

**Regla:** Cuando se crean 2+ skills de un dominio cohesivo, agregar la categoría al executor. Criterio: ¿hay un agente natural responsable? ¿hay keywords propias que aparecen en goals reales? Si sí a ambas → nueva categoría. Siempre correr `py_compile` después del patch.

Ver: `references/executor-routing-expansion-2026-05-31.md`

## Capa de memoria semántica — Honcho (pendiente integración)

Honcho deployado en ai-server :8008 como servicio permanente (2026-06-12).
Plan de integración: `nelson-honcho-memory` skill + `/home/server/brainstorming/2026-06-12-honcho-jarvis-memory/DEPLOY-PLAN.md`

Cuando Nelson diga "integremos Honcho", cargar skill `nelson-honcho-memory` y ejecutar los 5 pasos:
1. `pip install honcho-ai` + init workspace `jarvis-nelson` + peers `nelson`/`jarvis`
2. `~/.hermes/scripts/honcho_store.py` — guarda intercambios importantes post-turn
3. `~/.hermes/scripts/honcho_context.py` — recupera contexto semántico pre-turn
4. Comando para mostrar Conclusions (perfil adaptativo de Nelson)
5. Integrar en el loop JARVIS (pre-turn: recuperar, post-turn: guardar async)

### 14. Vista de proyecto sin match en índice PM

**Problema:** La página de ForestAI o Fleet muestra todo vacío porque el nombre en el índice PM no coincide con los keywords del config.

**Regla:** Los keywords del `ProjectConfig` deben ser substrings del nombre real de la instancia PM (lowercase). Verificar con "Actualizar datos del PM" primero, luego ajustar keywords.

Ver: `references/dashboard-project-view-pattern-2026-05-31.md`

### 12. Timeline solo en memoria de UI

**Problema:** El dashboard muestra eventos locales, pero al refrescar se pierde trazabilidad.

**Regla:** Exponer timeline persistente por run (`/runs/{task_id}/timeline`) y consumirlo como fuente principal. La UI local puede actuar solo como fallback temporal.

---

## Referencias de implementación reciente

- `references/mission-mode-timeline-controls-2026-05-29.md` — patrón aplicado para evolucionar el dashboard al Modo Misión y preparar timeline persistente + control de subtareas en backend.

## Resumen PM como agrupador de proyectos (regla operativa)

Cuando el usuario diga "Resumen PM", esa solapa debe actuar como **agrupador de trabajos** (no solo estado de runs):
- Ideas y brainstormings
- PoCs y spikes
- MVPs
- Repositorios GitHub del equipo
- Proyectos en curso o terminados

### Contrato recomendado para `/pm/instances`

- Mantener `instances` por compatibilidad, pero exponer también `projects` (naming del usuario).
- Entregar conteos agregados y por clase:
  - `counts.total`, `counts.project`, `counts.brainstorming`, `counts.github`
  - `counts.by_kind` (mvp/poc/spike/idea/project)
  - `counts.by_status` (active/done/idea)
- Cada item de proyecto local debería incluir:
  - `project_kind` (mvp/poc/spike/idea/project)
  - `project_status` (active/done/idea)

### Indexación incremental (no recalcular siempre)

Aplicar caché persistente y recalcular solo cuando cambie algo:
1. Calcular firma local (`local_signature`) con carpeta + `mtime` en `~/proyectos` y `~/brainstorming`.
2. Si la firma no cambió, reusar inventario local desde caché.
3. GitHub refrescar por TTL (`PM_GITHUB_REFRESH_SECONDS`) y no en cada request.
4. Si cambia un proyecto/carpeta: reindexar, incorporar el dato nuevo y recalcular conteos.
5. Exponer flags diagnósticos en respuesta:
   - `from_cache`
   - `recalculated`

### Endpoint de control

Agregar endpoint de forcing:
- `POST /pm/instances/reindex`

Útil para demos/soporte cuando el usuario pide "actualizá ya".

## Referencias de implementación

- `references/implementacion-real-2026-05-26.md` — Primera implementación real del orquestador
- `references/executor-real-diseno.md` — Diseño detallado del executor con hermes CLI
- `references/dashboard-chat-jarvis-2026-05-26.md` — Dashboard + chat JARVIS integrado
- `references/executor-routing-expansion-2026-05-31.md` — **Expansión de categorías IOT/AUTOMATION/DOMAIN/SCRAPING + keywords ForestAI/Fleet**
- `references/dashboard-project-view-pattern-2026-05-31.md` — **Patrón ProjectView por proyecto con hitos + valuación dinámica + sidebar con dividers**

## Contexto estratégico

ForestAI y Fleet Optimizer son los **dos productos principales de la consultora AlegentAI** (Tony + Pablo). No son PoCs descartables — son los productos que generan ingresos reales. El dashboard del orquestador es el **panel de mando ejecutivo** donde Tony y Pablo ven el estado de ambas iniciativas: valuación económica, hitos, próximos pasos, y pueden lanzar tareas al orquestador desde adentro.

Lo que diferencia a AlegentAI de una consultora que manda PowerPoints: un **sistema vivo** que opera, aprende y muestra resultados en tiempo real. Cada skill que se agrega, cada categoría del executor, cada feature del dashboard — todo alimenta ese sistema.

## Categorías del Executor (routing real)

Las categorías de CATEGORY_SKILLS del executor real están documentadas en
[`references/executor-categorias-2026-05-31.md`](references/executor-categorias-2026-05-31.md).

Categorías activas: BACKEND, FRONTEND, RAG/AI, SPEC, QA, INFRA, DOCS, SECURITY,
BROWSER, VISION, AUDIO, EXTERNAL, **IOT**, **AUTOMATION**, **DOMAIN**, **SCRAPING**, UNKNOWN.

Las nuevas (IOT/AUTOMATION/DOMAIN/SCRAPING) cubren los dominios reales de ForestAI y Fleet.

## Performance y Scalability

El orquestador escanea directorios de proyectos locales y brainstormings para el Resumen PM. El scan recursivo sin filtros puede colgarse minutos si recorre `node_modules`, `venv`, `.git`, etc.

Ver referencia completa: `references/performance-pitfalls.md`

Reglas rápidas:
- **Siempre filtrar directorios pesados** antes de `rglob("*")`
- **Medir con `time curl`** antes y después del fix
- **TTL de caché** (24h para GitHub, firma local para locales) reduce recálculos

### 11. Escaneo recursivo de filesystem sin filtros

**Problema:** Una función que calcula el mtime más reciente de un directorio usando `path.rglob("*")` sin filtros recorre `node_modules`, `.git`, `.venv`, `dist`, `build`, etc. En proyectos con dependencias, esto tarda minutos y causa timeouts en endpoints como `/pm/instances`.

**Síntoma:** El endpoint `/pm/instances` se cuelga o devuelve timeout. El servidor parece congelado mientras calcula la firma de proyectos locales.

**Fix:** Agregar `SKIP_DIRS` estándar antes del bucle `rglob`:
```python
SKIP_DIRS = {"node_modules", "venv", ".venv", "__pycache__", ".git", "dist", "build", ".next", "target", "vendor"}

def _dir_latest_mtime(path: Path) -> float:
    latest = 0.0
    for child in path.rglob("*"):
        # Saltar directorios pesados
        if any(skip in child.parts for skip in SKIP_DIRS):
            continue
        if child.is_file():
            latest = max(latest, child.stat().st_mtime)
    return latest
```

**Resultado:** El tiempo de respuesta baja de minutos a ~350ms.

**Regla:** Cualquier escaneo recursivo de filesystem en producción debe tener filtros de directorios. Nunca confiar en `rglob("*")` sin excluir artefactos de build y dependencias.

---

## OTel Tracing nativo (patrón AgentScope)

AgentScope define su `Task` con campos `blocks` y `blocked_by` para representar el DAG de dependencias directamente en el modelo. Adoptamos este patrón en nuestro task graph para eliminar la necesidad de un objeto DAG separado.

```python
# nelson_orchestrator/models.py — Task enriquecida con patrón AgentScope
from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime
import uuid

class Task(BaseModel):
    """Tarea del meta-orquestador con dependencias nativas (patrón AgentScope)."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    subject: str                          # nombre corto: "backend-auth"
    description: str                      # qué hay que hacer exactamente
    assigned_to: str                      # nombre del agente
    layer: str = ""                       # "backend" | "frontend" | "infra" | "qa" | "arch"
    complexity: int = 1                   # 1=low, 2=medium, 3=high
    state: Literal[
        "pending", "in_progress", "completed", "failed", "cancelled", "paused"
    ] = "pending"
    control_state: Literal[
        "active", "paused", "cancelled", "retry"
    ] = "active"

    # DAG de dependencias — patrón AgentScope
    blocks: list[str] = Field(default_factory=list)      # IDs que YO bloqueo
    blocked_by: list[str] = Field(default_factory=list)  # IDs que me bloquean a MÍ

    # Contexto explícito para el agente
    context: dict[str, Any] = Field(default_factory=dict)
    expected_output: str = ""             # descripción del output esperado

    # Metadata de ejecución
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    result: str = ""
    error: str = ""
    owner: str | None = None             # orquestación padre si es sub-tarea

def is_ready(task: Task, completed_ids: set[str]) -> bool:
    """Una tarea está lista si todos sus bloqueantes están completados."""
    return all(dep in completed_ids for dep in task.blocked_by)

def build_batches(tasks: list[Task]) -> list[list[Task]]:
    """Topological sort → batches paralelos. Algoritmo Kahn."""
    remaining = {t.id: t for t in tasks}
    completed: set[str] = set()
    batches = []

    while remaining:
        ready = [t for t in remaining.values() if is_ready(t, completed)]
        if not ready:
            raise ValueError("Ciclo detectado en el task graph")
        batches.append(ready)
        for t in ready:
            completed.add(t.id)
            del remaining[t.id]

    return batches
## Convenciones del Equipo Nelson

- **IDs de tareas:** formato `{módulo}-{número}`, ej: `NOTIF-001`, `NOTIF-002`
- **Checkpoints:** guardar en `nelson-task-memory` con key `orchestrator::{goal_hash}::checkpoint`
- **Logs de orquestación:** formato estructurado JSON con campos `timestamp`, `state`, `task_id`, `agent`, `action`, `result`
- **Máximo de iteraciones:** 3 ciclos VERIFYING → EXECUTING antes de escalar a Tony
- **Timeout por tarea:** 2 horas de trabajo de agente. Si supera, FailureType.TIMEOUT
- **Idioma de specs y tasks:** castellano técnico (este documento es el ejemplo)
- **UX operativa del dashboard:** en la vista Orchestrator, el bloque de entrada de objetivo (`Objetivo de misión`) va al inicio del flujo, antes de tarjetas de diagnóstico/telemetría.
- **Prioridad de fuentes para valuación ejecutiva en cards de proyecto:** `project > github > brainstorming` para evitar que spikes/ideas pisen la valuación del producto principal.
- **El orchestrator no implementa.** Si el Meta-Orchestrator se encuentra escribiendo código de negocio, algo salió mal en la descomposición.

Referencia de implementación: `references/dashboard-flow-and-valuation-priority-2026-06-02.md`

## Resumen PM como agrupador de proyectos

Cuando el usuario pida "Resumen PM", tratar la solapa como **agrupador de trabajos** (no solo runs del orquestador):
- Proyectos en `~/proyectos` (incluye PoC, Spike, MVP, ideas y activos)
- Brainstormings en `~/brainstorming/YYYY-MM-DD-*`
- Repositorios GitHub del equipo

### Contrato recomendado para `/pm/instances`

- Mantener `instances` por compatibilidad y exponer `projects` como alias principal.
- Entregar `counts.total`, `counts.project`, `counts.brainstorming`, `counts.github`.
- Agregar clasificación:
  - `counts.by_kind` (mvp/poc/spike/idea/project)
  - `counts.by_status` (active/done/idea)
- Cada proyecto local debe incluir `project_kind` y `project_status`.

### Indexación incremental

No recalcular siempre:
1. Persistir caché de inventario PM (ej. `pm_instances_cache.json`).
2. Calcular `local_signature` con carpetas + mtimes de `~/proyectos` y `~/brainstorming`.
3. Si la firma no cambia, reutilizar inventario local.
4. Refrescar GitHub por TTL (`PM_GITHUB_REFRESH_SECONDS`) en vez de cada request.
5. Exponer flags diagnósticos: `from_cache` y `recalculated`.

### Endpoint de control

- `POST /pm/instances/reindex` para forzar recalculo cuando Tony lo pide.

## Pitfall específico de despliegue alterno

Si el dashboard alterno (ej. `:5175`) muestra `Error cargando proyectos PM`, verificar que su backend alterno (ej. `:8754`) esté activo.
Validar siempre ambos caminos:
- `http://127.0.0.1:<frontend>/api/orchestrate/pm/instances`
- `http://127.0.0.1:<backend>/pm/instances`
