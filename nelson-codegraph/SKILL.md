---
name: nelson-codegraph
description: CodeGraph — grafo de conocimiento de código pre-indexado para el equipo Nelson. Reduce tokens, tool calls y costo al trabajar con agentes IA en proyectos grandes. Integrado con Hermes Agent.
category: software-development
tags: [codegraph, mcp, tokens, contexto, agentes, hermes, indexacion, grafo]
related_skills: [nelson-project-bootstrap, nelson-lean-ctx, hermes-agent]
---

# CodeGraph — Grafo de Conocimiento de Código

> **Trigger:** Al inicio de cualquier sesión de desarrollo en un proyecto del equipo. Antes de que Julián o Merceditas trabajen en un codebase. Cuando el contexto de un proyecto grande esté consumiendo demasiados tokens.

## Qué es

CodeGraph pre-indexa el código de un proyecto en un grafo de conocimiento (SQLite local). Cuando el agente necesita entender el codebase, consulta el grafo en vez de hacer grep + Read de archivos — eliminando la mayoría de los tool calls de exploración.

- Repo: https://github.com/colbymchenry/codegraph
- Versión: v0.9.4
- 100% local — nada sale a internet
- MIT license
- Soporte explícito para Hermes Agent

**Benchmarks reales (7 codebases open source):**
- 35% más barato
- 57% menos tokens
- 46% más rápido
- 71% menos tool calls

## Instalación (ya instalado en el servidor)

```bash
# Ya instalado en: /home/server/.local/bin/codegraph
codegraph --version  # 0.9.4

# Si hay que reinstalar:
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
```

## Integración con Hermes (ya configurada)

CodeGraph está registrado como MCP server en `~/.hermes/config.yaml`. Para activarlo en un proyecto hay que indexarlo primero.

```bash
# Inicializar y indexar un proyecto (desde la raíz del proyecto)
cd ~/brainstorming/2026-05-22-fleet-optimizer
codegraph init -i
```

## Comandos Principales

```bash
# Inicializar + indexar en un paso
codegraph init -i [path]

# Solo indexar (si ya fue inicializado)
codegraph index [path]

# Sincronizar cambios (después de editar código)
codegraph sync [path]

# Ver estado del índice
codegraph status [path]

# Buscar símbolos
codegraph query "nombre_funcion_o_clase"

# Contexto para una tarea (lo que usaría el agente)
codegraph context "descripcion de la tarea"

# Ver estructura de archivos indexados
codegraph files [path]

# Quién llama a una función
codegraph callers "nombre_funcion"

# Qué llama una función
codegraph callees "nombre_funcion"

# Impacto de cambiar un símbolo
codegraph impact "nombre_funcion"

# Tests afectados por archivos cambiados
codegraph affected archivo1.py archivo2.py
```

## Flujo de Trabajo Estándar del Equipo

### Al arrancar un proyecto nuevo (nelson-project-bootstrap)

```bash
cd ~/brainstorming/YYYY-MM-DD-nombre-proyecto
codegraph init -i
```

Esto crea `.codegraph/` en el directorio del proyecto con el índice SQLite.

### Al trabajar en un proyecto existente

```bash
# Verificar que el índice esté actualizado
codegraph status

# Si hay cambios desde el último índice
codegraph sync
```

### Al pasar el contexto a Julián o Merceditas (agentes)

Cuando arranco un agente delegado en un proyecto, el MCP de CodeGraph ya le da el grafo automáticamente. No hace falta pasar el contexto manualmente — el agente consulta el grafo.

## Proyectos Indexados

| Proyecto | Path | Archivos | Nodes |
|----------|------|----------|-------|
| fleet-optimizer | ~/brainstorming/2026-05-22-fleet-optimizer | 10 | 134 |
| deepagents-spike | ~/brainstorming/2026-05-21-deepagents-spike | 2 | 42 |

Agregar nuevos proyectos: `codegraph init -i ~/brainstorming/NUEVO-PROYECTO`

## Lenguajes Soportados

TypeScript, JavaScript, Python, Go, Rust, Java, C/C++, C#, Kotlin, Swift, Ruby, PHP, Dart, Lua, Scala, Svelte, Vue y más.

## El Índice (.codegraph/)

- Se crea en la raíz del proyecto
- Agregarlo al `.gitignore` (es local, no se commitea)
- Incluir en `.dockerignore` si hay Docker
- Se actualiza con `codegraph sync` después de cambios

```gitignore
# CodeGraph index
.codegraph/
```

## Pitfalls

1. **Requiere reiniciar Hermes:** Después de la instalación del MCP, iniciar una nueva sesión de Hermes para que cargue el server de CodeGraph.
2. **`init --yes` no existe:** El flag correcto es `-i` para indexar al inicializar, no `--yes`.
3. **Sin archivos de código:** Si el proyecto solo tiene markdown/YAML, el índice queda vacío. CodeGraph necesita código real (Python, TS, JS, etc.).
4. **Sync después de editar:** Si el agente edita archivos, correr `codegraph sync` para mantener el índice actualizado. Sin sync, el grafo muestra el estado anterior.
5. **Directorio correcto:** Siempre correr `codegraph init` desde la raíz del proyecto, no desde un subdirectorio.

## Desinstalar de un proyecto

```bash
codegraph uninit ~/brainstorming/PROYECTO  # Borra .codegraph/
```

## Referencias

- Repo: https://github.com/colbymchenry/codegraph
- Docs: https://colbymchenry.github.io/codegraph/
- npm: https://www.npmjs.com/package/@colbymchenry/codegraph
