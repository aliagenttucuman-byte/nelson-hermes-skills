# Systemd Deploy — Meta-Orquestador (2026-05-26)

## Estado final del stack

Todos los servicios del meta-orquestador corren como systemd services con restart automatico:

| Puerto | Servicio                         | Estado   |
|--------|----------------------------------|----------|
| :8742  | nelson-task-memory.service       | active   |
| :8743  | nelson-agent-router.service      | active   |
| :8744  | nelson-meta-orchestrator.service | active   |

El dashboard (Vite + CF tunnel) corre aparte en :5174.

## Procedimiento de instalacion

Script en `/home/server/nelson/meta-orchestrator/install-service.sh`

```bash
echo 'srv2026' | sudo -S bash /home/server/nelson/meta-orchestrator/install-service.sh
```

El script copia el `.service` a `/etc/systemd/system/`, hace `daemon-reload`, `enable` y `restart`.

## Pitfall: Address already in use al instalar

**Problema:** Al correr `install-service.sh`, el servicio falla con `[Errno 98] address already in use`.

**Solucion:**
```bash
fuser -k 8744/tcp 2>&1
sleep 2
echo 'srv2026' | sudo -S systemctl restart nelson-meta-orchestrator
```

Regla: antes de instalar un systemd service, verificar `ss -tlnp | grep 8744`.

## PITFALL CRITICO: subprocesses desde systemd no tienen PATH del usuario

**Problema:** El servicio corre con `User=server` pero el PATH del proceso NO incluye `~/.local/bin` ni venvs del usuario. Subprocesses como `hermes -z` o `edge-tts` fallan silenciosamente.

**Sintoma tipico:** Endpoint SSE devuelve HTTP 200 pero no llegan chunks de datos al frontend. El streaming queda colgado.

**Solucion:** SIEMPRE usar rutas absolutas en subprocesses lanzados desde uvicorn/systemd:

```python
# MAL - no encontrado en systemd
proc = await asyncio.create_subprocess_exec("hermes", "-z", prompt, ...)
proc = await asyncio.create_subprocess_exec("edge-tts", "--voice", ...)

# BIEN - rutas absolutas
proc = await asyncio.create_subprocess_exec(
    "/home/server/.local/bin/hermes", "-z", prompt, ...)
proc = await asyncio.create_subprocess_exec(
    "/home/server/.hermes/hermes-agent/venv/bin/edge-tts", "--voice", ...)
```

**Binarios conocidos del stack Nelson:**
- hermes CLI: `/home/server/.local/bin/hermes`
- edge-tts: `/home/server/.hermes/hermes-agent/venv/bin/edge-tts`

Regla general: cualquier binario instalado en el home del usuario requiere ruta absoluta cuando lo invoca un servicio systemd.

## Limpieza de tareas

Desde 2026-05-26 hay endpoints DELETE en task-memory:
- `DELETE /tasks/{task_id}` — elimina tarea + subtareas en cascada
- `DELETE /tasks/bulk/{status}` — limpia todas las del estado dado (done/failed/cancelled/pending)

Antes de esta sesion, la unica forma era PATCH a status=cancelled.

## Estado del dashboard (post sesion 2026-05-26)

- PIN cambiado de `741852` a `123456`
- Nuevas paginas: Chat JARVIS (/chat), Documentacion (/docs)
- Flujo orquestador: POST /plan -> revisar -> POST /run/confirm/{task_id}
- Proxy vite: /api/chat -> :8744/chat, /api/docs -> :8744/docs

## Evoluciones pendientes (next sprint)

1. WebSocket broadcast desde dentro del loop -> dashboard en tiempo real
2. Endpoint `/tasks/{id}/replay` -> re-correr tarea fallida
3. Endpoint `/send-media` en gateway Baileys para audios OGG nativos
