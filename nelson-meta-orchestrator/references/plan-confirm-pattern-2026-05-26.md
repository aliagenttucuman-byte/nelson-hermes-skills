# Patrón Plan/Confirm — Implementado 2026-05-26

## Por qué existe

Antes el orquestador ejecutaba todo apenas recibía el goal en /run.
Tony quería ver el plan (agentes, categoría, confianza) antes de disparar la ejecución.
Se implementó el flujo de dos pasos sin romper backward compat.

## Endpoints en producción (:8744)

```
POST  /plan                      → { goal, parallel? } → OrchestrationResult (SIN ejecutar)
POST  /run/confirm/{task_id}     → { dry_run?, parallel? } → OrchestrationResult (ejecuta)
POST  /run                       → backward compat: plan + execute en un paso
POST  /route-only                → solo rutea, no persiste nada
POST  /estimate                  → { goal } → { routing, estimate }
GET   /status                    → { pending, history_total, recent }
GET   /health                    → { status, dependencies }
WS    /ws                        → WebSocket de eventos (heartbeat 30s, ping/pong)
```

## Flujo recomendado (dos pasos)

```
1. POST /plan   → devuelve task_id + resumen del plan, estado queda 'pending'
2. Tony revisa  → ve categoría, agentes, confianza en el dashboard
3. POST /run/confirm/{task_id}  → ejecuta el plan, marca 'in_progress'
```

## Arquitectura interna (orchestrator.py)

```python
class MetaOrchestrator:

    def plan(self, goal, parallel=False) -> OrchestrationResult:
        # 1. Rutea via :8743
        # 2. Crea tarea maestra en task-memory con status='pending' (NO in_progress)
        # 3. Construye subtareas y las guarda en SQLite sin ejecutarlas
        # 4. Retorna plan con task_id para que Tony lo confirme

    def execute(self, master_id, dry_run=False, parallel=False) -> OrchestrationResult:
        # 1. Carga subtareas del SQLite por master_id
        # 2. Marca tarea maestra como 'in_progress'
        # 3. Registra subtareas en task-memory
        # 4. Loop EXECUTE -> VERIFY (hasta MAX_ITER=2)
        # 5. Notifica a Tony via WhatsApp

    def run(self, goal, dry_run=False, parallel=False) -> OrchestrationResult:
        # Backward compat: plan() + execute() encadenados
        result = self.plan(goal, parallel=parallel)
        if result.error or not result.task_id:
            return result
        return self.execute(result.task_id, dry_run=dry_run, parallel=parallel)
```

## Dashboard (React) — cambios asociados

- Botón "Planificar" (antes "Ejecutar") → llama POST /plan
- Aparece card azul con el plan: categoría, agentes, confianza, task_id
- Botones: "Confirmar y Ejecutar" (verde) + "Cancelar" (neutro)
- Al confirmar: POST /run/confirm/{task_id} → card de resultado verde/rojo

Hooks: usePlanGoal(), useConfirmGoal() en useOrchestrator.ts
API: orchestratorApi.plan(goal) + orchestratorApi.confirm(taskId) en client.ts

## Pitfall: execute() reconstruye routing desde subtareas

En execute(), el routing dict se reconstruye desde la primera subtarea del SQLite
(no se guarda el routing original del plan). Para tasks multi-agente, el campo
is_multi_agent se infiere de len(sub_tasks) > 1.

Si se necesita el routing completo original, habría que persistirlo en la tarea
maestra (columna extra en task_graph.db o en task-memory).
