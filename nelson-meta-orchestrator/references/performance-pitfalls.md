# Performance Pitfalls — Meta-Orchestrator Backend

## Pitfall: rglob("*") sin filtros en directorios de proyecto

**Síntoma:** El endpoint `/pm/instances` se cuelga por minutos al recalcular el índice de proyectos. No responde ni da timeout.

**Causa raíz:** La función `_dir_latest_mtime(path, max_depth=2)` usa `path.rglob("*")` que recorre **todos los archivos recursivamente**, incluyendo `node_modules`, `venv`, `.git`, `dist`, `build`, `.next`, `target`, `vendor`, `__pycache__`.

**Impacto:** Con proyectos que tienen dependencias (node_modules de React, venv de Python), el scan puede tardar minutos en lugar de milisegundos.

**Fix:** Agregar un `SKIP_DIRS` set que se chequee antes de procesar cada path:

```python
SKIP_DIRS = {"node_modules", "venv", ".venv", "__pycache__", ".git", "dist", "build", ".next", "target", "vendor"}

for child in path.rglob("*"):
    if any(part in SKIP_DIRS for part in child.parts):
        continue
    # ... resto del procesamiento
```

**Resultado medido:**
- Antes: timeout (no responde)
- Después: 350ms para 22 instancias (3 proyectos + 10 brainstormings + 9 repos GitHub)

## Generalización: cualquier scan de filesystem en el orquestador

Siempre aplicar filtros de directorios pesados cuando se escanea recursivamente. Los directorios de dependencias, caches y build artifacts son los primeros candidatos a excluir.

## Patrón de profiling rápido

```bash
time curl -s "http://localhost:8744/pm/instances?limit=10" | python3 -m json.tool | head -30
```

Si tarda más de 2 segundos, hay un problema de scan de filesystem o de cálculo de firma (`_local_projects_signature`).
