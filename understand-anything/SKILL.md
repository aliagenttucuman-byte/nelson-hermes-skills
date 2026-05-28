---
name: understand-anything
description: Understand Anything — grafo interactivo de conocimiento de código para el equipo Nelson. Analiza codebases y genera dashboards navegables. Integrado con Hermes Agent como plugin de skills.
category: software-development
tags: [understand, knowledge-graph, dashboard, codebase, arquitectura, analisis, nelson]
related_skills: [nelson-codegraph, nelson-project-bootstrap, nelson-lean-ctx, hermes-agent]
---

# Understand Anything

> **Trigger:** Cuando Nelson o un agente necesita entender la arquitectura de un proyecto antes de trabajar en él. Antes de onboarding de Julián o Merceditas en un proyecto nuevo. Para análisis de impacto de cambios. Para generar documentación de arquitectura.

## Qué es

Understand Anything v2.7.5 genera un knowledge-graph.json interactivo del codebase usando LLM + análisis estático. El dashboard web muestra el grafo con nodos, aristas, layers y guided tour.

- Repo: https://github.com/Lum1104/Understand-Anything
- Instalado en: ~/.understand-anything/repo (v2.7.5)
- Skills en: ~/.hermes/skills/understand-anything/ (symlink)
- MIT license, 100% local

**Pipeline de 7 fases:**
- Fase 0: Pre-flight (full vs incremental)
- Fase 0.5: Ignore config
- Fase 1: Scan (descubre archivos, detecta lenguajes/frameworks)
- Fase 1.5: Batch (agrupa archivos semánticamente)
- Fase 2: Analyze (hasta 5 subagentes concurrentes)
- Fase 3: Architecture (layers)
- Fase 4: Tour (walkthroughs guiados)
- Fase 5: Assembly + Review
- Fase 6: Review (validación)
- Fase 7: Save + Dashboard

## Instalación (ya instalado en el servidor)

```bash
# Verificar instalación
ls ~/.understand-anything/repo/
ls ~/.hermes/skills/understand-anything/

# Si hay que reinstalar desde cero:
curl -fsSL https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/install.sh | bash -s hermes

# Actualizar:
~/.understand-anything/repo/install.sh --update

# Desinstalar:
~/.understand-anything/repo/install.sh --uninstall hermes
```

## Prerequisitos (ya cumplidos en el servidor)

- Node.js >= 22 (servidor: v24.15.0)
- pnpm >= 10 (servidor: v11.4.0)
- Python 3 (servidor: 3.11.15)
- git

## Skills Disponibles

| Skill | Uso |
|-------|-----|
| /understand [path] [flags] | Análisis completo del codebase → knowledge-graph.json |
| /understand-dashboard [path] | Dashboard web interactivo (se auto-lanza después de /understand) |
| /understand-chat "pregunta" | Pregunta libre sobre el codebase |
| /understand-diff | Impacto de cambios actuales (git diff) |
| /understand-explain archivo | Deep-dive en un archivo o función |
| /understand-onboard | Guía de onboarding para el equipo |
| /understand-domain | Extrae dominios de negocio y flujos |
| /understand-knowledge wiki-dir | Analiza un wiki Karpathy-pattern |

## Flags de /understand

```bash
--full              # Rebuild completo ignorando grafo existente
--auto-update       # Activa actualización automática en cada commit
--no-auto-update    # Desactiva actualización automática
--review            # Usa LLM graph-reviewer completo
--language <lang>   # Genera contenido en ese idioma (es, en, zh, etc.)
/ruta/del/proyecto  # Analiza ese directorio en vez del CWD
```

## Flujo de Trabajo Estándar del Equipo

### Al arrancar en un proyecto nuevo

```bash
# Desde la skill en Hermes:
# /understand ~/brainstorming/2026-05-22-fleet-optimizer/poc
# O con flags:
# /understand ~/brainstorming/2026-05-22-fleet-optimizer/poc --language es

# El output queda en:
# ~/brainstorming/2026-05-22-fleet-optimizer/poc/.understand-anything/knowledge-graph.json
```

### Ver el dashboard

El dashboard se auto-lanza después de /understand. También:
```bash
# /understand-dashboard ~/brainstorming/2026-05-22-fleet-optimizer/poc
```

### Preguntar sobre el código

```bash
# /understand-chat "¿Cómo funciona el flujo de autenticación?"
# /understand-chat "¿Qué hace el endpoint /api/vehicles?"
# /understand-explain main.py
```

### Actualización incremental (después de cambios)

```bash
# Si hay cambios desde el último análisis:
# /understand  (detecta automáticamente que es incremental)
# O forzar rebuild completo:
# /understand --full
```

## Output: knowledge-graph.json

Ubicación: `<project-root>/.understand-anything/knowledge-graph.json`

```json
{
  "version": "1.0.0",
  "kind": "codebase",
  "project": {
    "name": "nombre-proyecto",
    "languages": ["Python", "TypeScript"],
    "frameworks": ["FastAPI", "React"],
    "description": "...",
    "analyzedAt": "ISO-timestamp",
    "gitCommitHash": "abc123"
  },
  "nodes": [...],
  "edges": [...],
  "layers": [...],
  "tour": [...]
}
```

Tipos de nodos: file, function, class, module, concept, config, document, service, table, endpoint, pipeline, schema, resource

## Proyectos Analizados

| Proyecto | Path | Estado |
|----------|------|--------|
| fleet-optimizer/poc | ~/brainstorming/2026-05-22-fleet-optimizer/poc | ✅ Analizado (35 nodes, 50 edges, 3 layers, 10 tour steps) — verificado OK 2026-05-28 |

### Verificación rápida del grafo (inline Python)

```python
import json
g = json.loads(open(".understand-anything/knowledge-graph.json").read())
# Ojo: g["project"] puede no tener "languages" si el scanner no lo populó
# Usar .get() siempre:
print(g["project"].get("languages", "n/a"))
print(g["project"].get("frameworks", "n/a"))
print(len(g["nodes"]), "nodos")
print(len(g["edges"]), "aristas")
print([l["name"] for l in g.get("layers", [])])
```

> Pitfall: `g["project"]["languages"]` lanza KeyError si el scanner no detectó lenguajes. Usar siempre `.get("languages", [])`.

### understand-chat inline (sin subagente)

Cuando se ejecuta `/understand-chat` directamente desde Hermes Agent (no delegado):

1. Leer `knowledge-graph.json` completo con `terminal("cat ...")`
2. Parsear con `json.loads()`
3. Filtrar nodos por keywords en `id`, `summary`, `tags`
4. Filtrar edges donde `source` o `target` están en los nodos encontrados
5. Responder con los summaries de nodos + relaciones encontradas

No es necesario correr ningún script externo — el grafo JSON es autocontenido.

Agregar nuevos proyectos corriendo `/understand <path>` desde Hermes.

## Diferencia con CodeGraph

| Feature | understand-anything | nelson-codegraph |
|---------|--------------------|--------------------|
| Dashboard visual | ✅ Interactivo con React Flow | ❌ Solo CLI |
| Multi-agente | ✅ 5 subagentes concurrentes | ✅ SQLite local |
| Lenguajes | 20+ (WASM tree-sitter) | 20+ |
| Incremental | ✅ Git-based | ✅ Sync |
| Costo tokens | Alto (análisis LLM completo) | Bajo (grafo pre-indexado) |

**Recomendación:** Usar understand-anything para onboarding y diseño arquitectónico. Usar nelson-codegraph durante el desarrollo activo para reducir tokens.

## .gitignore del Proyecto

```gitignore
# Understand Anything
.understand-anything/intermediate/
.understand-anything/diff-overlay.json
# El knowledge-graph.json SÍ se puede commitear (es solo JSON)
```

## Pitfalls

1. **Build requerido después de instalar:** El plugin necesita `pnpm build` en `~/.understand-anything/repo/understand-anything-plugin/` — ya hecho en el servidor.
2. **PLUGIN_ROOT lookup:** El skill busca el plugin en ~/.understand-anything-plugin → ~/.hermes/skills/understand-anything/../../ → candidatos. En el servidor usa el symlink en ~/.hermes/skills/understand-anything que apunta a ~/.understand-anything/repo/understand-anything-plugin/skills/.
3. **Solo JSON, sin MCP:** No hay MCP server en este proyecto. Funciona exclusivamente via skills de Hermes.
4. **Proyectos grandes >100 archivos:** El skill avisa y pide confirmación. Mejor scopear a un subdirectorio (ej: /poc en vez de la raíz completa).
5. **node_modules en el path:** Si se analiza la raíz de un frontend, asegurarse de que node_modules esté en .understandignore (se genera automáticamente).
6. **Dashboard requiere puerto libre:** El dashboard web se lanza en un puerto local. Verificar disponibilidad con `ss -tlnp | grep <puerto>`.
11. **`g["project"]["languages"]` puede fallar con KeyError.** El scanner no siempre popula ese campo. Usar `.get("languages", [])` y `.get("frameworks", [])` siempre al leer el grafo.

7. **`ua-inline-validate.cjs` NO existe pre-compilado.** No está en `skills/understand/` ni en ningún path del plugin. El SKILL.md de `/understand` dice que se escribe en `tmp/` en Phase 6 — eso es correcto. Nunca buscar ese archivo en el plugin; siempre escribirlo al momento de ejecutar.
8. **`build-fingerprints.mjs` necesita un JSON de input, NO la raíz del proyecto.** El script tiene firma `node build-fingerprints.mjs <input.json>` con estructura `{ projectRoot, sourceFilePaths[], gitCommitHash }`. Pasarle la ruta del proyecto directamente falla con EISDIR.
9. **Modo directo (no-subagente):** Cuando /understand se ejecuta directamente por Hermes Agent (no vía Claude Code delegation), las fases que dicen "dispatch a subagent" se ejecutan inline. Las fases 3-5 (assemble-reviewer, architecture-analyzer, tour-builder) se implementan directamente escribiendo los JSONs de output manualmente con el LLM, en vez de delegar a subagentes.
10. **Phase 0.5 auto-confirm:** Cuando el usuario especifica explícitamente que NO se espere confirmación (ej: "NO esperar confirmación del usuario — auto-confirmar y continuar"), omitir la espera de confirmación del .understandignore y proceder directamente a Phase 1.

## Desinstalar de un proyecto

```bash
rm -rf <project-root>/.understand-anything/
```

## Referencias

- `references/pipeline-execution-notes.md` — Notas de ejecución del pipeline en Hermes Agent directo (sin Claude Code): estructura de scan-result.json, invocación correcta de build-fingerprints.mjs, cómo manejar fases inline sin subagentes reales, y resultados del análisis de fleet-optimizer/poc.
