# Plan/Confirm Workflow — implementado 2026-05-26

## Motivación

El orquestador ejecutaba goals directamente al recibir `/run`. Nelson quería
revisar el plan antes de ejecutar — ver qué agentes, qué categoría, qué
sub-tareas, y decidir si confirma o cancela.

## Arquitectura del flujo de 2 pasos

```
POST /plan  →  arma plan, persiste en SQLite como 'pending', devuelve task_id
                    ↓ Tony revisa el plan en el dashboard
POST /run/confirm/{task_id}  →  ejecuta el plan ya validado
```

El endpoint `/run` original sigue funcionando (backward compat = plan + execute en un solo paso).

## Backend: orchestrator.py

Se separó el método `run()` en tres métodos:

### `plan(goal, parallel) → OrchestrationResult`
- Rutea el goal via Router :8743
- Crea tarea maestra en Task Memory :8742 **en estado `pending`** (NO `in_progress`)
- Construye sub-tareas y las persiste solo en SQLite (sin registrar en task-memory)
- Devuelve el plan con `task_id` para la confirmación
- NO ejecuta nada

### `execute(master_id, dry_run, parallel) → OrchestrationResult`
- Recupera goal y sub-tareas del SQLite por `master_id`
- Marca tarea maestra como `in_progress`
- Registra sub-tareas en task-memory
- Corre el loop EXECUTE → VERIFY normal
- Notifica a Tony

### `run(goal, dry_run, parallel)` (backward compat)
```python
def run(self, goal, dry_run=False, parallel=False):
    result = self.plan(goal, parallel=parallel)
    if result.error or not result.task_id:
        return result
    return self.execute(result.task_id, dry_run=dry_run, parallel=parallel)
```

### `_build_plan_summary(goal, routing, sub_tasks) → str`
Nuevo helper para el mensaje del plan pendiente:
```
"📋 Plan listo | BACKEND (85%) | agente único | 1 sub-tarea(s) | Agentes: julian | Esperando confirmación de Tony para ejecutar."
```

## Nuevos endpoints en main.py

```python
POST /plan              # PlanRequest(goal, parallel)
POST /run/confirm/{id}  # ConfirmRequest(dry_run, parallel)
POST /run               # RunRequest (backward compat)
```

Schemas nuevos:
```python
class PlanRequest(BaseModel):
    goal:     str
    parallel: bool = False

class ConfirmRequest(BaseModel):
    dry_run:  bool = False
    parallel: bool = False
```

## Frontend: Orchestrator.tsx

Estado nuevo:
```typescript
const [plan, setPlan] = useState<OrchestratorResult | null>(null)    // plan pendiente
const [lastResult, setLastResult] = useState<OrchestratorResult | null>(null)  // resultado final
```

Hooks nuevos en `useOrchestrator.ts`:
```typescript
export function usePlanGoal()   // POST /api/orchestrate/plan
export function useConfirmGoal() // POST /api/orchestrate/run/confirm/{taskId}
```

Nuevo entry en `client.ts`:
```typescript
plan:    (goal: string)   => api.post('/api/orchestrate/plan', { goal }).then(r => r.data),
confirm: (taskId: string) => api.post(`/api/orchestrate/run/confirm/${taskId}`, {}).then(r => r.data),
```

Flujo visual:
1. Input visible → botón "Planificar" (ícono ClipboardList)
2. Al recibir plan → desaparece el input, aparece Card azul con plan + botones
3. Botón "Confirmar y Ejecutar" (verde, ícono PlayCircle) → dispara execute
4. Botón "Cancelar" → limpia el plan, vuelve al input
5. Al finalizar → Card resultado (verde/rojo según estado)

El historial de recientes ahora muestra `pending` en amarillo además de done/failed/in_progress.

## Pitfall crítico

Al recuperar sub-tareas del SQLite en `execute()`, la query buscaba por `master_id`:
```sql
SELECT id, goal, category, agents, confidence, status
FROM task_graph WHERE master_id=?
```
El campo `goal` en las sub-tareas guardadas era el goal del master, no el
de la sub-tarea individual. Esto es correcto — las sub-tareas heredan el goal
del master ya que la descomposición está en `category` y `agents`.

## Archivos modificados

- `/home/server/nelson/meta-orchestrator/nelson_orchestrator/orchestrator.py`
- `/home/server/nelson/meta-orchestrator/main.py`
- `/home/server/nelson/orchestrator-dashboard/src/pages/Orchestrator.tsx`
- `/home/server/nelson/orchestrator-dashboard/src/hooks/useOrchestrator.ts`
- `/home/server/nelson/orchestrator-dashboard/src/api/client.ts`
