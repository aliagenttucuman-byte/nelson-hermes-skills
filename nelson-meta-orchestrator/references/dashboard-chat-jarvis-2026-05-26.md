# Dashboard Chat JARVIS — Implementación 2026-05-26

## Qué se construyó

Integración de chat directo con JARVIS dentro del dashboard del meta-orquestador.

### Endpoints nuevos en :8744

| Endpoint | Método | Descripción |
|---|---|---|
| `/chat` | POST | SSE streaming — llama a `hermes -z` con historial |
| `/chat/speak` | POST | TTS con edge-tts → devuelve MP3 |
| `/plan` | POST | Fase 1: arma plan sin ejecutar, devuelve `task_id` |
| `/run/confirm/{task_id}` | POST | Fase 2: ejecuta plan ya aprobado por Tony |

### Flujo de chat con streaming

```python
# El endpoint usa asyncio subprocess + SSE
proc = await asyncio.create_subprocess_exec(
    "/home/server/.local/bin/hermes", "-z", prompt,  # ← ruta ABSOLUTA
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.DEVNULL,
)
async for chunk in proc.stdout:
    yield f"data: {json.dumps({'chunk': text})}\n\n"
yield f"data: {json.dumps({'done': True, 'full': full})}\n\n"
```

### TTS con edge-tts

```python
proc = await asyncio.create_subprocess_exec(
    "/home/server/.hermes/hermes-agent/venv/bin/edge-tts",  # ← ruta ABSOLUTA
    "--voice", "es-AR-TomasNeural",
    "--text", text[:2000],
    "--write-media", tmp_path,
)
return FileResponse(tmp_path, media_type="audio/mpeg")
```

## PITFALL CRÍTICO: PATH en servicios systemd

**Problema:** El servicio systemd corre sin el PATH completo del usuario.
`hermes` y `edge-tts` no están en el PATH del servicio aunque sí en el del usuario.

**Síntoma:** El endpoint devuelve 200 con SSE pero no llegan chunks — el proceso
subprocess silencia stderr y nunca produce stdout porque no encuentra el binario.

**Solución:** Usar siempre rutas absolutas en subprocesses dentro de servicios systemd:
- hermes: `/home/server/.local/bin/hermes`
- edge-tts: `/home/server/.hermes/hermes-agent/venv/bin/edge-tts`

**Alternativa:** Agregar `Environment=PATH=/home/server/.local/bin:...` en el .service

## Proxy Vite → servicios backend

```ts
// vite.config.ts — el orden importa: más específico primero
'/api/chat':        { target: 'http://localhost:8744', rewrite: p => p.replace('/api/chat', '/chat') },
'/api/orchestrate': { target: 'http://localhost:8744', rewrite: p => p.replace('/api/orchestrate', '') },
```

`/api/chat/speak` queda cubierto por el mismo proxy de `/api/chat` → `/chat/speak`. ✓

## Flujo plan→confirm en el orquestador

**Antes:** `/run` → ejecutaba inmediatamente sin mostrar el plan.
**Ahora:** 
1. Frontend llama `/plan` → backend rutea, arma subtareas en SQLite, devuelve plan con `task_id`
2. UI muestra card azul con agentes, categoría, confianza
3. Tony confirma → frontend llama `/run/confirm/{task_id}` → ejecuta
4. `/run` sigue existiendo para backward compat (plan + execute en un paso)

## Delete de tareas (task-memory :8742)

Endpoints nuevos agregados a `task_memory/api.py`:

```
DELETE /tasks/{task_id}         → cascada: subtareas + artefactos + sesiones
DELETE /tasks/bulk/{status}     → limpia todas las tareas de un estado
```

Estados permitidos para bulk delete: `done`, `failed`, `cancelled`, `pending`

## Dashboard UI — novedades

- **Chat JARVIS** en `/chat`: burbujas, streaming visible, toggle audio (VolumeX/Volume2)
- **Historial con delete**: botón papelera por fila (hover) + botones bulk por estado
- **Flujo planificar→confirmar** en Orquestador
- **PIN cambiado** a `123456` (era `741852`)
