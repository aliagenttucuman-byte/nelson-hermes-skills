# Implementación Real del Meta-Orquestador — actualizado 2026-05-26

## Estado actual

El meta-orquestador formal está 100% implementado y corriendo en producción.

| Capa | Servicio | Puerto | Estado |
|------|----------|--------|--------|
| Task Memory | nelson-task-memory | 8742 | ✅ producción (systemd) |
| Agent Router | nelson-agent-router | 8743 | ✅ producción (systemd) |
| Meta-Orchestrator API | nelson-meta-orchestrator | 8744 | ✅ producción (systemd) |
| Status Dashboard | orchestrator-dashboard | 5174 | ✅ producción (Vite dev + CF tunnel) |

## Paths en producción

```
/home/server/nelson/task-memory/           → Task Memory API
/home/server/nelson/routing/               → Agent Router API
/home/server/nelson/meta-orchestrator/     → Meta-Orchestrator API
/home/server/nelson/orchestrator-dashboard/ → Dashboard React
```

## Estructura del Meta-Orchestrator

```
meta-orchestrator/
├── main.py                         # FastAPI app, endpoints
├── task_graph.db                   # SQLite: task graph persistente
├── nelson_orchestrator/
│   ├── orchestrator.py             # MetaOrchestrator — plan() + execute() + run()
│   ├── executor.py                 # Ejecución real via hermes CLI
│   ├── verifier.py                 # Verificación de resultados (3 capas)
│   ├── notifier.py                 # Notificación WhatsApp a Tony
│   ├── estimator.py                # Estimación de presupuesto desde goal
│   ├── clients.py                  # HTTP wrappers hacia :8742 y :8743
│   └── models.py                   # OrchestratorState, SubTask, etc.
```

## Loop completo (implementado y verificado)

```
GOAL
 → PLAN (rutea + persiste en pending, devuelve task_id)
 → [Tony revisa y aprueba]
 → EXECUTE (carga plan, marca in_progress, ejecuta via hermes CLI)
 → VERIFY (estructural + keywords + longitud mínima)
 → RETRY (hasta 2 iteraciones si falla y puede_retry)
 → NOTIFY (WhatsApp a Tony via bridge Hermes :3000)
 → DONE / FAILED
```

## Endpoints disponibles

```
POST  /plan                      → { goal, parallel? } → OrchestrationResult (SIN ejecutar)
POST  /run/confirm/{task_id}     → { dry_run?, parallel? } → OrchestrationResult (ejecuta)
POST  /run                       → backward compat: plan + execute en un paso
POST  /route-only                → { goal } → RoutingResult
POST  /estimate                  → { goal } → { routing, estimate }
GET   /status                    → { pending, history_total, recent }
GET   /health                    → { status, dependencies }
WS    /ws                        → WebSocket de eventos
```

Ver references/plan-confirm-pattern-2026-05-26.md para detalle del flujo de dos pasos.

### Parámetros de /run (backward compat)

- `dry_run: true` → simula sin ejecutar hermes (para tests/demos)
- `parallel: true` → sub-tareas independientes en ThreadPoolExecutor

## Notificaciones WhatsApp

El notifier envía a Tony (Nelson Acosta) via el bridge nativo de Hermes (:3000).
Si el gateway WA no está disponible, deja log prominente con el mensaje pendiente.

## Verifier — Lógica de evaluación

3 capas en orden:
1. Estructural: ¿hay resultado? ¿no está vacío? ¿la tarea no falló?
2. Keywords: ¿el resultado menciona términos técnicos esperados para la categoría?
3. Longitud: ¿tiene al menos 20 palabras? (evita respuestas superficiales)

Score final: 0.0–1.0. Umbral de aprobación: ≥0.5 y sin issues críticos.

## Executor — Mapeo categoría → agente

| Categoría | Agente | Skills cargados |
|-----------|--------|-----------------|
| BACKEND   | Julián | equipo-nelson, fastapi, nelson-senior-practices |
| FRONTEND  | Mercedes | equipo-nelson, nelson-frontend-stack |
| RAG/AI    | JARVIS + Julián | nelson-rag-pipeline, nelson-llm-generation |
| SPEC      | JARVIS | nelson-spec-driven-workflow |
| QA        | Alma | python-testing-patterns, nelson-frontend-testing |
| INFRA     | Diego | docker-management, nelson-ci-cd |
| SECURITY  | Ricky | nelson-security, nelson-workflow-security |
