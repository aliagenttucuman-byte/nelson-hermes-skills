# Executor Real del Meta-Orquestador

Implementado en `/home/server/nelson/meta-orchestrator/nelson_orchestrator/executor.py`

## Estrategia

Cada sub-tarea se lanza como `subprocess.run(["hermes", "--non-interactive", "--", <prompt>])`.
Si hermes no está disponible, cae automáticamente a modo simulación (no falla en dev).

## Parámetros del endpoint /run

```json
{
  "goal": "descripción de la tarea",
  "dry_run": false,     // true = simula sin ejecutar hermes
  "parallel": false     // true = ThreadPoolExecutor (max 3 workers)
}
```

## Mapeo categoría → agente + skills

```python
CATEGORY_AGENT = {
    "BACKEND":  "Julián",
    "FRONTEND": "Mercedes",
    "RAG/AI":   "JARVIS + Julián",
    "SPEC":     "JARVIS",
    "QA":       "Alma",
    "INFRA":    "Diego",
    "DOCS":     "JARVIS",
    "SECURITY": "Ricky",
    "BROWSER":  "Nico",
    "VISION":   "JARVIS",
    "AUDIO":    "JARVIS",
    "EXTERNAL": "Ricky",
    "UNKNOWN":  "JARVIS",
}

CATEGORY_SKILLS = {
    "BACKEND":   ["equipo-nelson", "fastapi", "nelson-senior-practices"],
    "FRONTEND":  ["equipo-nelson", "nelson-frontend-stack", "nelson-senior-practices"],
    "RAG/AI":    ["equipo-nelson", "nelson-rag-pipeline", "nelson-llm-generation"],
    "SPEC":      ["nelson-spec-driven-workflow", "nelson-project-constitution"],
    "QA":        ["equipo-nelson", "python-testing-patterns", "nelson-frontend-testing"],
    "INFRA":     ["equipo-nelson", "docker-management", "nelson-ci-cd"],
    "DOCS":      ["equipo-nelson", "nelson-documentation"],
    "SECURITY":  ["equipo-nelson", "nelson-security", "nelson-workflow-security"],
    "BROWSER":   ["equipo-nelson", "nelson-browser-agent"],
    "VISION":    ["equipo-nelson", "nelson-ai-vision"],
    "AUDIO":     ["equipo-nelson", "nelson-audio-processing"],
    "EXTERNAL":  ["equipo-nelson", "nelson-external-integrations"],
    "UNKNOWN":   ["equipo-nelson"],
}
```

## Prompt que recibe el agente

```
[META-ORQUESTADOR — Sub-tarea automática]

Eres {agente}, agente del equipo Nelson.
Skills relevantes: {skills}

GOAL MAESTRO: {goal_maestro}

TU SUB-TAREA ({categoria}):
{goal_especifico}

Ejecutá esta sub-tarea usando las skills indicadas.
Al finalizar, respondé con un resumen breve del resultado.
```

## Retry policy

- MAX_RETRIES = 2
- Backoff: 5s × intento (5s, 10s)
- Timeout por sub-tarea: 300s (5 minutos)
- Tras 3 fallos: devuelve error, el orquestador lo marca `failed` en task-memory

## Persistencia SQLite

Tabla `task_graph` en `task_graph.db`:
- Cada sub-tarea se guarda con master_id, categoría, status, result, tm_id
- Se inicializa automáticamente al arrancar
- `_load_pending_subtasks(master_id)` recupera pendientes de sesiones anteriores

## Test rápido (dry_run)

```bash
curl -s -X POST http://localhost:8744/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Crear componente React de login", "dry_run": true}' \
  | python3 -m json.tool
```

Resultado esperado: `state: "done"`, sub-tasks con result `"[dry-run] Agente: Mercedes | Categoría: FRONTEND"`

## Verificar persistencia

```bash
python3 -c "
import sqlite3, json
conn = sqlite3.connect('/home/server/nelson/meta-orchestrator/task_graph.db')
rows = conn.execute('SELECT master_id, category, status, result FROM task_graph').fetchall()
[print(r) for r in rows]
"
```
