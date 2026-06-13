# Timeline persistente + control de sub-tareas (sesión 2026-05-29)

## Qué se agregó

1. Persistencia de eventos por run en SQLite:
   - Tabla `orchestration_events`
   - Índice `idx_events_master`
2. Control manual por sub-tarea:
   - Tabla `subtask_control`
   - Índice `idx_control_master`
   - Estados: `active | paused | cancelled`
3. Helpers backend en `orchestrator.py`:
   - `_log_event(master_id, event, detail, status)`
   - `get_timeline(master_id, limit)`
   - `get_subtasks(master_id)`
   - `control_subtask(master_id, subtask_id, action)`

## Endpoints HTTP nuevos

- `GET /runs/{task_id}/timeline`
- `GET /runs/{task_id}/subtasks`
- `POST /runs/{task_id}/subtasks/{subtask_id}/control`
  - body: `{ "action": "pause|resume|cancel|retry" }`

## Semántica de ejecución relevante

- Antes de ejecutar un batch, consultar `subtask_control`.
- Si `control_state=paused`, excluir temporalmente la sub-tarea del batch.
- Si `control_state=cancelled`, marcar `TaskStatus.CANCELLED` y no ejecutar.
- `retry` debe volver la sub-tarea a `pending` y limpiar `result/error`.

## Verificación recomendada cuando no se puede reiniciar servicio

1. `python -m py_compile` para validar sintaxis backend.
2. `FastAPI TestClient` para validar endpoints nuevos de forma local al proceso.
3. Flujo mínimo:
   - `POST /plan`
   - `GET /runs/{task_id}/timeline`
   - `GET /runs/{task_id}/subtasks`
   - `POST /runs/{task_id}/subtasks/{subtask_id}/control` con `pause`
   - reconsultar subtasks y comprobar `control_state=paused`

## Dashboard (proxy de desarrollo)

Para evitar acoplamiento duro al puerto del orchestrator en dev:
- usar variables de entorno para proxy:
  - `ORCH_API_URL` (default `http://localhost:8744`)
  - `ORCH_WS_URL` (default `ws://localhost:8744`)

Esto permite probar backends alternos sin tocar código TS.