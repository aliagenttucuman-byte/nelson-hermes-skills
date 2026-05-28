# Nuevas features implementadas — 2026-05-26

## 1. Flujo Plan → Confirm (dos pasos)

### Por qué
Tony necesita ver el plan antes de ejecutar. Evita que el orquestador dispare agentes en tasks ambiguas.

### Implementación en orchestrator.py

Tres métodos en MetaOrchestrator:
- `plan(goal, parallel)` — rutea + crea tarea maestra en estado 'pending' + guarda subtareas en SQLite SIN ejecutar. Devuelve OrchestrationResult con task_id.
- `execute(master_id, dry_run, parallel)` — recupera subtareas del SQLite, ejecuta el loop EXECUTE→VERIFY, cierra tarea maestra, notifica.
- `run(goal, dry_run, parallel)` — backward compat: llama plan() + execute() en un paso.

### Endpoints nuevos en main.py

```
POST /plan              { goal, parallel? }  → RunResponse con task_id, state='idle'
POST /run/confirm/{id}  { dry_run?, parallel? } → RunResponse con estado final
POST /run               backward compat (no tocar)
```

### Flujo en el dashboard (Orchestrator.tsx)
1. Input de goal → botón "Planificar" → llama POST /plan
2. Aparece card azul con: categoría, agentes, confianza, sub_tasks_count, task_id
3. Botones: "Confirmar y Ejecutar" (verde) / "Cancelar" (gris)
4. Confirmar → llama POST /run/confirm/{task_id} → muestra resultado final

### Pitfall: recuperar goal en execute()
Al ejecutar un plan ya guardado, el goal se recupera de SQLite así:
```sql
SELECT goal FROM task_graph WHERE id=? OR master_id=? LIMIT 1
```
No confiar en que el caller pase el goal — puede no tenerlo.

### Pitfall: routing dict en execute()
El routing dict se reconstruye desde las subtareas recuperadas del SQLite:
```python
routing = {
    "agents": sub_tasks[0].agents,
    "category": sub_tasks[0].category,
    "confidence": sub_tasks[0].confidence,
    "is_multi_agent": len(sub_tasks) > 1
}
```

---

## 2. Borrado de tareas en task-memory (:8742)

### Nuevas funciones en crud.py
- `delete_task(task_id)` — elimina tarea + subtareas + artefactos + sesiones en cascada con 3 queries DELETE anidados
- `delete_tasks_by_status(status)` — busca todas las tasks raíz (parent_task_id IS NULL) con ese estado y llama delete_task() para cada una

### Endpoints en api.py
```
DELETE /tasks/{task_id}       → {"deleted": task_id}
DELETE /tasks/bulk/{status}   → {"deleted_count": N, "status": status}
  estados válidos: done, failed, cancelled, pending
```

**PITFALL CRÍTICO — orden en FastAPI:**
El endpoint `/bulk/{status}` DEBE declararse DESPUÉS de `/{task_id}` en el código. FastAPI matchea rutas en orden de declaración, y si `/bulk/{status}` va primero, la palabra "bulk" se interpreta como un task_id y el endpoint correcto nunca matchea.

### Frontend (Orchestrator.tsx)
- Cada fila del historial tiene un botón papelera (Trash2 de lucide) visible en `group-hover`
- Header del historial tiene 4 botones de limpieza masiva: done (verde), failed (rojo), cancelled (gris), pending (amarillo)
- Hooks: `useDeleteTask()` y `useDeleteBulk()` en useOrchestrator.ts
- API client: `tasksApi.deleteOne(id)` y `tasksApi.deleteBulk(status)` en client.ts

---

## 3. Chat JARVIS via SSE

### Endpoint POST /chat en main.py (:8744)

Request:
```json
{ "message": "texto del usuario", "history": [{"role": "user"|"assistant", "content": "..."}] }
```

Response: Server-Sent Events
```
data: {"chunk": "texto parcial"}
data: {"chunk": "...más texto"}
data: {"done": true, "full": "respuesta completa"}
```

Implementación:
```python
async def stream_response():
    proc = await asyncio.create_subprocess_exec(
        "hermes", "-z", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    async for chunk in proc.stdout:
        text = chunk.decode("utf-8", errors="replace")
        yield f"data: {json.dumps({'chunk': text})}\n\n"
    await proc.wait()
    yield f"data: {json.dumps({'done': True, 'full': full})}\n\n"

return StreamingResponse(stream_response(), media_type="text/event-stream")
```

**Pitfall SSE:** Usar `asyncio.create_subprocess_exec` (no `subprocess.run` que bloquea el event loop de FastAPI). El `StreamingResponse` + async generator es el patrón correcto.

**Pitfall prompt:** El historial se limita a los últimos 10 mensajes para no explotar el contexto de Hermes. El prompt incluye el rol JARVIS/Tony Stark explícito.

### Proxy en vite.config.ts
```js
'/api/chat': { target: 'http://localhost:8744', rewrite: p => p.replace('/api/chat', '/chat'), changeOrigin: true }
```

**PITFALL IMPORTANTE:** Cambios en vite.config.ts requieren reiniciar el proceso Vite. El hot reload NO aplica a la configuración del servidor.

### Frontend Chat.tsx
- Diseño chat estilo WhatsApp: burbujas usuario (derecha, índigo) y JARVIS (izquierda, ámbar)
- Streaming real: cada `data: {chunk}` actualiza el mensaje en tiempo real
- Enter para enviar, Shift+Enter para nueva línea
- Scroll automático al último mensaje con `useRef` + `scrollIntoView`
- Estado `loading` con spinner mientras llega la primera respuesta

### Integración en el dashboard
- Nueva ruta `/chat` en App.tsx
- Nuevo ítem "Chat JARVIS" (MessageSquare icon) en Sidebar.tsx entre Orquestador y Presupuesto
- Proxy `/api/chat` en vite.config.ts

---

## 4. PIN del dashboard

Cambiado de 741852 a **123456**. Vive en `AuthGuard.tsx`:
```ts
const SECRET_PIN = import.meta.env.VITE_DASHBOARD_PIN || '123456'
```
Override con `.env.local` si se quiere uno personalizado sin tocar el código.

---

## 5. Servicio systemd correcto

El nombre es `nelson-meta-orchestrator`, NO `nelson-orchestrator`:
```bash
# CORRECTO
sudo systemctl restart nelson-meta-orchestrator

# INCORRECTO — Unit not found
sudo systemctl restart nelson-orchestrator
```
