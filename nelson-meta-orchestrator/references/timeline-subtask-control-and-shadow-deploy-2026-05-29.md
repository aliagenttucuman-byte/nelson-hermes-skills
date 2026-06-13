# Timeline persistente + control por subtask + shadow deploy (2026-05-29)

## Resumen
Se validó una mejora operacional del Meta-Orchestrator para dar:
- trazabilidad persistente por run,
- control manual de subtareas en ejecución,
- despliegue de prueba end-to-end sin tocar systemd de producción.

## Backend (orchestrator.py)

### Nuevas tablas SQLite
- `orchestration_events`
  - `id`, `master_id`, `event`, `detail`, `status`, `created_at`
- `subtask_control`
  - `subtask_id`, `master_id`, `control_state`, `updated_at`

### Helpers agregados
- `_log_event(master_id, event, detail, status)`
- `get_timeline(master_id, limit=100)`
- `get_subtasks(master_id)`
- `control_subtask(master_id, subtask_id, action)`

### Integración en loop
- Registrar evento al planificar (`planned`).
- Registrar inicio de ejecución (`execute_started`).
- Registrar resultado de verify (`verify`).
- Registrar cierre (`completed`/`failed`).
- Excluir subtareas `paused`/`cancelled` del runner.

## API (main.py)

### Endpoints nuevos
- `GET /runs/{task_id}/timeline`
- `GET /runs/{task_id}/subtasks`
- `POST /runs/{task_id}/subtasks/{subtask_id}/control`
  - body: `{ "action": "pause|resume|cancel|retry" }`

## Frontend dashboard

Se cableó Orchestrator UI para consumir:
- timeline persistente del backend,
- listado de subtasks con `control_state`,
- acciones de control (pause/resume/cancel/retry).

## Patrón de validación segura (shadow deploy)

### 1) Backend alterno
```bash
cd /home/server/nelson/meta-orchestrator
/home/server/.hermes/hermes-agent/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8754
```

### 2) Dashboard apuntando al backend alterno
```bash
cd /home/server/nelson/orchestrator-dashboard
ORCH_API_URL=http://127.0.0.1:8754 \
ORCH_WS_URL=ws://127.0.0.1:8754 \
npm run dev -- --host 0.0.0.0 --port 5175
```

### 3) Tunnel para QA remoto
```bash
cloudflared tunnel --url http://127.0.0.1:5175
```

### 4) Smoke test E2E
1. `POST /api/orchestrate/plan`
2. `GET /api/orchestrate/runs/{task_id}/timeline`
3. `GET /api/orchestrate/runs/{task_id}/subtasks`
4. `POST /api/orchestrate/runs/{task_id}/subtasks/{subtask_id}/control` con `pause`
5. Releer subtasks y verificar `control_state=paused`

## Resultado esperado
- Se valida funcionalidad completa sin reiniciar `nelson-meta-orchestrator.service` en `8744`.
- Al terminar QA, promover a producción con ventana de cambio y restart controlado.
