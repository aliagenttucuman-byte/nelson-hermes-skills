# Estado del sistema en producción — 2026-05-26

## Servicios systemd activos

| Servicio | Puerto | Estado | Descripción |
|---|---|---|---|
| nelson-task-memory | :8742 | active (running) | SQLite task_graph.db, REST API |
| nelson-agent-router | :8743 | active (running) | Router de goals → agentes |
| nelson-meta-orchestrator | :8744 | active (running) | Loop GOAL→ROUTE→EXECUTE→VERIFY→NOTIFY |

Dashboard: :5174 (Vite + CF tunnel). PIN: 123456.

## Endpoints activos en :8744

- POST /run — ejecuta inmediatamente (backward compat)
- POST /plan — arma plan, persiste con status pending, devuelve task_id
- POST /run/confirm/{task_id} — Tony aprueba, recien ahi ejecuta
- GET /ws — WebSocket live feed
- POST /chat — SSE streaming con hermes -z
- POST /chat/speak — TTS edge-tts, devuelve MP3
- POST /docs/generate — genera HTML manual con Playwright (WIP)
- GET /docs/download/{filename}

## Endpoints activos en :8742

- GET/POST /tasks
- DELETE /tasks/{task_id} — cascada
- DELETE /tasks/bulk/{status}
- PATCH /tasks/{id}/status

## PITFALL CRITICO: PATH en systemd

Subprocesses lanzados desde uvicorn/systemd no tienen ~/.local/bin en PATH.
Usar siempre rutas absolutas:
- hermes: /home/server/.local/bin/hermes
- edge-tts: /home/server/.hermes/hermes-agent/venv/bin/edge-tts
