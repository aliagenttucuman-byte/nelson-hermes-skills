# Flujo plan → confirm en el orquestador — 2026-05-26

## Motivación

Nelson quiere VER el plan antes de ejecutarlo.
El endpoint `/run` original ejecutaba todo de una sola vez — sin revisión.

## Nuevo flujo de dos pasos

```
POST /plan   →  devuelve plan + task_id  (no ejecuta nada, tarea queda en "pending")
POST /run/confirm/{task_id}  →  ejecuta el plan aprobado
```

El endpoint `/run` original se conservó para backward compat — internamente hace `plan` + `execute`.

## Orchestrator: métodos nuevos

- `plan(goal, parallel)` → rutea, crea tarea maestra en "pending", guarda subtareas en SQLite, devuelve plan sin ejecutar
- `execute(master_id, dry_run, parallel)` → recupera subtareas del SQLite, marca "in_progress", corre el loop EXECUTE→VERIFY
- `run(goal, ...)` → backward compat, llama plan + execute

## Pitfall: routing en execute()

Al ejecutar un plan existente, el `routing` dict se reconstruye desde las subtareas del SQLite
(no desde el router de nuevo). Esto evita que un cambio en el router entre plan y ejecución
cambie el plan que Tony aprobó.

## Frontend: estados del card

1. Input visible → usuario escribe goal
2. Al planificar → input se oculta, aparece card azul con plan (categoría, agentes, confianza, task_id)
3. Botones: "Confirmar y Ejecutar" (verde) o "Cancelar"
4. Al ejecutar → card azul desaparece, aparece card resultado (verde/rojo según outcome)

## Delete de tareas (agregado en la misma sesión)

### Backend — task-memory (:8742)

Dos endpoints nuevos en `api.py` + lógica en `crud.py`:

```
DELETE /tasks/{task_id}      → borra tarea + subtareas + artefactos + sesiones en cascada
DELETE /tasks/bulk/{status}  → borra todas las tareas raíz con ese estado
```

Estados permitidos para bulk: `done`, `failed`, `cancelled`, `pending`.

### Frontend — Orchestrator.tsx

- Cada fila del historial: botón papelera visible al hover (`group` + `opacity-0 group-hover:opacity-100`)
- Header del historial: 4 botones (done/failed/cancelled/pending) con colores por estado
  - done → emerald, failed → red, pending → yellow, cancelled → slate
