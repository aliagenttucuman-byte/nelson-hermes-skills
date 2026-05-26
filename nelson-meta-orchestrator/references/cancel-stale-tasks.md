# Cancelar tareas stale (no existe DELETE)

El endpoint DELETE no existe en task-memory. Para limpiar tareas pending o failed, usar PATCH con status=cancelled.

## Bash

```bash
curl -X PATCH http://localhost:8742/tasks/{task_id}/status \
  -H "Content-Type: application/json" \
  -d '{"status":"cancelled","result_summary":"Limpieza manual"}'
```

## Python (batch)

```python
import json, urllib.request

def cancel_task(task_id, reason="Limpieza manual"):
    data = json.dumps({"status": "cancelled", "result_summary": reason}).encode()
    req = urllib.request.Request(
        f"http://localhost:8742/tasks/{task_id}/status",
        data=data, headers={"Content-Type": "application/json"}, method="PATCH"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

ids = ["<id1>", "<id2>"]
for tid in ids:
    cancel_task(tid)
```

## Verificar limpieza

```bash
curl -s http://localhost:8742/tasks/pending
# Debe devolver []
```

## Endpoints disponibles (openapi)

```
/tasks/
/tasks/pending
/tasks/history
/tasks/{task_id}
/tasks/{task_id}/status        ← PATCH aquí para cancelar
/tasks/{task_id}/subtasks
/tasks/{task_id}/artifacts
/tasks/{task_id}/sessions/start
/tasks/sessions/{session_id}/end
/tasks/{task_id}/sessions
/health
```

No existe /tasks/{id}/delete ni DELETE method en ningún endpoint.
