---
name: nelson-codebase-memory-mcp
description: "CodebaseMemoryMCP (CBM): grafo de código pre-indexado para el equipo Nelson. Reduce tokens ~80% en call chains. Instalación, uso, pitfalls y benchmark real medido en farmacia-poc-gcp."
version: 1.0.0
author: Nelson Acosta
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [code-intelligence, MCP, performance, nelson]
    related_skills: [native-mcp, nelson-codegraph, nelson-meta-orchestrator]
---

# CodebaseMemoryMCP (CBM) para el equipo Nelson

Code intelligence basado en grafo. Indexa un repo una vez, después responde queries de "qué llama a qué", "rutas HTTP", "dónde se define X" sin que el LLM lea código.

## Cuándo usar CBM (no grep)

USAR CBM cuando la pregunta involucra **estructura cruzada**:
- "Qué funciones llama `/api/chat`" → `trace_path` / `search_graph`
- "Qué rutas HTTP expone el backend" → `search_graph(node_type=Route)`
- "Quién importa `gcp_adapters`" → `query_graph` con edge IMPORTS
- "Dame el snippet de `save_event`" → `get_code_snippet` (sin abrir el archivo)
- Refactor: "qué se rompe si renombro X" → `trace_path` reverso

USAR grep/ripgrep cuando:
- Búsqueda de string literal único ("TODO", regex)
- Una sola pasada sin seguir referencias
- Archivos no-código (markdown, configs)

**Benchmark real (farmacia-poc-gcp, 27/06/2026):**
- Query "call chain de `/api/chat`": CBM **1.045 tokens** vs grep+cat **5.255 tokens** → **80% reducción**
- Index time: 149ms (445 nodos, 749 edges)
- hermes-agent: 14.5s para 75.782 nodos / 337.318 edges

## Instalación

```bash
# 1. Binario C estático (254 MB)
curl -L https://github.com/codebase-memory-mcp/releases/latest/download/codebase-memory-mcp-linux-x64 \
  -o ~/.local/bin/codebase-memory-mcp
chmod +x ~/.local/bin/codebase-memory-mcp

# 2. mcp SDK Python (Hermes ya lo trae)
pip install mcp  # solo si falta

# 3. Verificar
codebase-memory-mcp --version  # → 0.8.1
codebase-memory-mcp --help     # muestra los 14 tools
```

## Integración con Hermes (native MCP client)

Agregar en `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  cbm:
    command: "/home/server/.local/bin/codebase-memory-mcp"
    args: []
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

Restart Hermes. Los 14 tools aparecen como `mcp_cbm_*`:
- `mcp_cbm_index_repository`
- `mcp_cbm_search_graph`
- `mcp_cbm_trace_path`
- `mcp_cbm_get_code_snippet`
- `mcp_cbm_query_graph`
- `mcp_cbm_search_code`
- `mcp_cbm_list_projects`
- `mcp_cbm_index_status`
- `mcp_cbm_detect_changes`
- `mcp_cbm_manage_adr`
- `mcp_cbm_get_graph_schema`
- `mcp_cbm_ingest_traces`
- `mcp_cbm_delete_project`
- ~~`mcp_cbm_get_architecture`~~ ⚠️ (ver pitfall 1)

## Indexar un repo nuevo

```bash
codebase-memory-mcp cli index_repository '{"repo_path": "/home/server/proyectos/mi-poc"}'
```

El nombre del proyecto se deriva del path: `/home/server/proyectos/farmacia-poc-gcp` → `home-server-proyectos-farmacia-poc-gcp`.

DB local en `~/.cache/codebase-memory-mcp/<nombre-proyecto>.db`.

Re-index incremental: vuelve a ejecutar `index_repository` con el mismo path. CBM hashea los archivos y solo reprocesa los cambiados.

## Workflow recomendado para PoCs nuevas del equipo

1. **Bootstrap** del repo (skill `nelson-project-bootstrap` o `nelson-poc-gcp-terraform-template`)
2. **Primer index** después del primer commit
3. **Cron diario** (3 AM) reindexa todos los repos activos — script `~/.hermes/scripts/cbm-reindex.sh`
4. **Antes de empezar tarea compleja**: query a CBM en lugar de leer 10 archivos
5. **Después de refactor grande**: index manual + verificar grafo

## Repos del equipo Nelson actualmente indexados

| Repo | Nodos | Edges | Notas |
|------|-------|-------|-------|
| farmacia-poc-gcp | 445 | 749 | PoC GCP+Terraform validada |
| hermes-agent | 75.782 | 337.318 | Hermes Agent completo |
| forestai-poc | 711 | 1.488 | PoC drones forestales |
| chat-con-documentos | 367 | 691 | PoC RAG |

Lista actualizada: `codebase-memory-mcp cli list_projects "{}"`

## Cron diario (auto-reindex)

Script: `~/.hermes/scripts/cbm-reindex.sh`
Job ID: `f52bb9b098e0` (schedule `0 3 * * *`)
Silencioso si OK, alerta si error (watchdog pattern).

Para agregar un repo nuevo al cron, editar el array `REPOS` del script.

## Pitfalls

### 1. `get_architecture` se cuelga
La tool `get_architecture(aspects=['all'])` ejecuta ~56s sin output útil. Es un bug conocido v0.8.1. **No usarla.** Para entender la arquitectura usar:
- `search_graph(node_type="Route")` → endpoints HTTP
- `search_graph(node_type="Class")` → clases principales
- `query_graph` con edges IMPORTS para ver módulos top-level

### 2. El nombre del proyecto se deriva del path
Si movés el repo de carpeta, CBM lo indexa como proyecto nuevo. Borrá el viejo con `delete_project` para no acumular.

### 3. Categoría en `skill_manage` mete el archivo en gitignore
Cuando creés esta skill (u otras), no uses `category=software-development` — esa carpeta está en .gitignore del repo nelson-hermes-skills. Las skills nelson-* viven en la **raíz** de `~/.hermes/skills/`.

### 4. `args: []` obligatorio en config Hermes
El YAML de `mcp_servers.cbm` necesita `args: []` explícito aunque esté vacío — sin esa línea algunos parsers fallan silenciosamente.

### 5. `sampling.enabled: false` por seguridad
CBM no necesita acceso al LLM del agente. Dejar `false` evita que cualquier tool del server pueda iniciar llamadas LLM no auditadas.

### 6. Memoria al indexar repos grandes
hermes-agent tarda 14.5s y usa ~7 GB RAM transitorios. En máquinas con < 8 GB libre considerar excluir el repo del cron y reindex manual.

### 7. node_modules y venvs se excluyen automáticamente
CBM excluye `.git`, `node_modules`, `__pycache__`, `venv`, `dist/`, etc. No hace falta `.cbmignore`. Si querés excluir algo más, hay que rebuildear desde fuente.

## Tools clave (referencia rápida)

```bash
# Listar proyectos
codebase-memory-mcp cli list_projects "{}"

# Buscar nodos por tipo
codebase-memory-mcp cli search_graph '{"project":"home-server-proyectos-farmacia-poc-gcp","node_type":"Route"}'

# Trace de qué llama a qué (3 hops)
codebase-memory-mcp cli trace_path '{"project":"...","source":"chat","max_depth":3}'

# Snippet directo
codebase-memory-mcp cli get_code_snippet '{"project":"...","function":"save_event"}'

# Detectar cambios sin reindexar
codebase-memory-mcp cli detect_changes '{"project":"..."}'

# Estado del índice
codebase-memory-mcp cli index_status '{"project":"..."}'
```

## Team-shared graph (opt-in)

CBM permite exportar `graph.db.zst` al repo para que otro dev no tenga que reindexar. Workflow:

1. `codebase-memory-mcp cli export_artifact '{"project":"...","output":"./.cbm/graph.db.zst"}'`
2. Commitear `.cbm/graph.db.zst` (gitignored opcional)
3. Al clonar: `codebase-memory-mcp cli import_artifact '{"input":"./.cbm/graph.db.zst"}'`

Para el equipo Nelson: activado en farmacia-poc-gcp como referencia.

## Recomendación de uso en meta-orquestador Nelson

Cuando el meta-orquestador detecta tarea de tipo:
- "explicame cómo funciona X en el repo"
- "qué se rompe si cambio Y"
- "dónde se usa la función Z"
- "lista las rutas HTTP del backend"

→ **primer paso**: query a CBM. Si CBM no resuelve, fallback a grep/cat.

Esto reduce drasticamente el contexto del agente especialista (Julián backend, Mercedes frontend) y mejora calidad de respuesta.
