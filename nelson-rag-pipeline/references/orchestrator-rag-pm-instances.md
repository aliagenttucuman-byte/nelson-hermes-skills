# Orchestrator RAG + PM Instances (session note)

## Qué se implementó

Se consolidó un patrón para que JARVIS consulte contexto operativo real y para que PM tenga selector de instancias:

- Chat RAG usa contexto de:
  - Task Memory (`history` y `pending`)
  - Timeline de ejecución (`orchestration_events`)
  - Subtasks (`task_graph`)
- Endpoint nuevo para PM:
  - `GET /pm/instances`
  - agrega PoCs locales, carpetas de brainstorming y repos GitHub.
- UI PM con desplegable:
  - selecciona instancia
  - muestra tipo, resumen, fecha update, path local o URL repo.

## Heurísticas prácticas usadas

### Brainstorming

- Root: `~/brainstorming`
- Incluir solo carpetas con prefijo fecha (`YYYY-MM-DD-*`)
- Excluir `templates` y directorios ocultos
- `summary`: primera línea de `README.md` si existe

### PoCs

- Roots: `~/proyectos`, `~/brainstorming`
- Match de nombre: contiene `poc`, `spike` o `demo`
- Dedupe por path absoluto

### GitHub

- Owners por env var:
  - `PM_GITHUB_OWNERS=aliagenttucuman-byte,aliagenttucuman`
- Consultar ambos endpoints para soportar user/org:
  - `/users/{owner}/repos`
  - `/orgs/{owner}/repos`
- Dedupe por `full_name`

## Contrato recomendado de API

```json
{
  "generated_at": "...Z",
  "counts": {
    "total": 0,
    "poc": 0,
    "brainstorming": 0,
    "github": 0
  },
  "groups": {
    "poc": [],
    "brainstorming": [],
    "github": []
  },
  "instances": []
}
```

## RAG robusto sin credenciales

Para no bloquear PoC cuando no hay key externa:

- Backend `embedding_backend`:
  - `openai` si hay `OPENAI_API_KEY`
  - `hashing-local` si no
- Hashing embedding determinístico:
  - token -> SHA256 -> bucket index + signo
  - normalización L2
- Útil para continuidad funcional del flujo y demos internas.

## Recomendación de UX (PM)

En `Resumen PM`, mostrar selector unificado `[Tipo] Nombre` y panel de detalle:

- tipo
- updated_at
- summary
- path local o link GitHub
- contador total por tipo en cabecera

Esto alinea la vista PM con operación real (no kanban decorativo).