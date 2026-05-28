# Features implementadas — sesión 2026-05-26 (tarde/noche)

## 1. Flujo plan → confirm en el orquestador

**Antes:** POST /run ejecutaba inmediatamente.
**Ahora:** Dos pasos:
- `POST /plan` → arma el plan, persiste en SQLite con status `pending`, devuelve `task_id`. NO ejecuta nada.
- `POST /run/confirm/{task_id}` → Tony aprueba, recién ahí se ejecuta.
- `POST /run` sigue funcionando (backward compat = `plan` + `execute` en un paso).

Métodos en `orchestrator.py`: `plan()`, `execute()`, `run()` (wrapper).

El frontend muestra un card azul con el plan (categoría, agentes, confianza) y botones "Confirmar y Ejecutar" / "Cancelar".

## 2. DELETE de tareas en task-memory

**Endpoints nuevos en `:8742`:**
- `DELETE /tasks/{task_id}` — elimina tarea + subtareas + artefactos + sesiones en cascada.
- `DELETE /tasks/bulk/{status}` — limpia todas las tareas de un estado dado (`done`, `failed`, `cancelled`, `pending`). Solo tareas root (`parent_task_id IS NULL`), las subtareas se eliminan en cascada.

**Frontend:** cada fila del historial tiene botón papelera (hover). Arriba del historial, botones por estado con color: done=verde, failed=rojo, pending=amarillo, cancelled=gris.

## 3. Chat con JARVIS en el dashboard

**Endpoint:** `POST /chat` en `:8744`
- Recibe `{message, history[]}` (historial últimos 10 mensajes para contexto)
- Ejecuta `hermes -z prompt` como subprocess async
- Devuelve **Server-Sent Events** (SSE) para streaming token a token
- Frontend consume con `ReadableStream`, actualiza burbuja en tiempo real

**PITFALL CRÍTICO:** El servicio systemd no tiene el PATH del usuario. `hermes` no se encuentra.
**Solución:** Usar ruta absoluta `/home/server/.local/bin/hermes` en el subprocess.
Mismo problema con `edge-tts` → usar `/home/server/.hermes/hermes-agent/venv/bin/edge-tts`.

Regla general: en subprocesses lanzados desde uvicorn systemd, SIEMPRE usar rutas absolutas para binarios del usuario.

## 4. TTS de JARVIS en el chat

**Endpoint:** `POST /chat/speak`
- Recibe `{text, voice}` (default `es-AR-TomasNeural`)
- Genera MP3 con edge-tts en tempfile
- Devuelve `FileResponse` con `media_type="audio/mpeg"`

**Frontend:** toggle de audio (icono parlante) en el input del chat.
- OFF → solo texto
- ON → al terminar el streaming, llama a `/api/chat/speak`, crea blob URL, reproduce automático con `new Audio(url).play()`
- Cada mensaje de JARVIS guarda la `audioUrl` para poder reproducir de nuevo con botón "reproducir"

## 5. Documentación automática con capturas

**Endpoint:** `POST /docs/generate`
- Usa Playwright (async_api) con Chromium headless (`--no-sandbox`)
- Viewport 1440×900, device_scale_factor 1.5 para capturas nítidas
- Se autentica automático: fill input[type=password] + click submit + wait 1500ms
- Captura 8 secciones: /, /orchestrator, /chat, /tasks, /budget, /pm, /router, /taxonomy
- Genera HTML completo con capturas embebidas en base64
- Guarda en `/home/server/nelson/meta-orchestrator/docs_output/manual_{ts}.html`

**Endpoint:** `GET /docs/download/{filename}` → descarga el HTML.

Módulo: `nelson_orchestrator/docs_generator.py`

## Proxy vite.config.ts — estado actual

```ts
'/api/tasks'       → :8742/tasks
'/api/route'       → :8743
'/api/taxonomy'    → :8743/taxonomy
'/api/orchestrate' → :8744
'/api/chat'        → :8744/chat
'/api/docs'        → :8744/docs
'/ws'              → ws://:8744 (WebSocket)
```

## PIN del dashboard

Cambiado de `741852` a `123456`. Configurable via `.env.local` → `VITE_DASHBOARD_PIN`.

## Navegación del dashboard (sidebar)

Orden actual: Dashboard → Orquestador → Chat JARVIS → Documentación → Presupuesto → PM Board → Tareas → Router → Taxonomía
