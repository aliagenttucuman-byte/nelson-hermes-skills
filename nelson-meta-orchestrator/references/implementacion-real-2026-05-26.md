# Implementación Real del Meta-Orquestador — 2026-05-26

## Estado actual

El meta-orquestador formal está 100% implementado y corriendo en producción.

| Capa | Servicio | Puerto | Estado |
|------|----------|--------|--------|
| Task Memory | nelson-task-memory | 8742 | ✅ producción (systemd) |
| Agent Router | nelson-agent-router | 8743 | ✅ producción (systemd) |
| Meta-Orchestrator API | nelson-meta-orchestrator | 8744 | ✅ producción (uvicorn bg) |
| Status Dashboard | orchestrator-dashboard | 5174 | ✅ producción (Vite + CF tunnel) |

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
│   ├── orchestrator.py             # MetaOrchestrator — loop maestro COMPLETO
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
 → ROUTE (:8743)
 → CREATE_TASK (:8742 + SQLite)
 → BUILD_SUBTASKS (1 o N según routing)
 → EXECUTE (hermes CLI real, o simulación si no disponible)
 → VERIFY (estructural + keywords + longitud mínima)
 → RETRY (hasta 2 iteraciones si falla y puede_retry)
 → NOTIFY (WhatsApp a Tony via bridge Hermes :3000)
 → DONE / FAILED
```

## Endpoints disponibles

```
POST  /run         → { goal, dry_run?, parallel? } → OrchestrationResult
POST  /route-only  → { goal } → RoutingResult
POST  /estimate    → { goal } → { routing, estimate }
GET   /status      → { pending, history_total, recent }
GET   /health      → { status, dependencies }
```

### Parámetros de /run

- `dry_run: true` → simula sin ejecutar hermes (para tests/demos)
- `parallel: true` → sub-tareas independientes en ThreadPoolExecutor

## Ejemplo de test

```bash
# dry_run=true (simula, verifica, notifica en log)
curl -X POST http://localhost:8744/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Implementar endpoint JWT con FastAPI", "dry_run": true}'

# Producción (ejecuta hermes real)
curl -X POST http://localhost:8744/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Tu goal acá"}'
```

## Notificaciones WhatsApp

El notifier envía a Tony (Nelson Acosta) via el bridge nativo de Hermes (:3000).
Si el gateway WA no está disponible, deja log prominente con el mensaje pendiente.

Formato de notificación exitosa:
```
🤖 Meta-Orquestador — HH:MM
✅ Goal completado
_descripción del goal_
📊 2/2 sub-tareas OK · score 65%
  ✓ [BACKEND] resumen del resultado
  ✓ [SECURITY] resumen del resultado
```

## Verifier — Lógica de evaluación

3 capas en orden:
1. **Estructural**: ¿hay resultado? ¿no está vacío? ¿la tarea no falló?
2. **Keywords**: ¿el resultado menciona términos técnicos esperados para la categoría?
3. **Longitud**: ¿tiene al menos 20 palabras? (evita respuestas superficiales)

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

## Próximos pasos

1. Registrar el orquestador en systemd (requiere sudo — Nelson hacerlo manualmente)
2. WebSocket en el dashboard para ver progreso en tiempo real
3. Autenticación básica al dashboard antes de exposición pública
