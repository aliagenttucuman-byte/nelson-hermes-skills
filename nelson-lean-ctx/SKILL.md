---
name: nelson-lean-ctx
description: "Lean Cortex (lean-ctx): capa de compresión de contexto para agentes IA. Ahorra tokens en lecturas de archivos y output de shell. Instalado y configurado en el servidor."
version: 1.1.0
author: JARVIS
platforms: [linux]
metadata:
  hermes:
    tags: [lean-ctx, tokens, contexto, mcp, compresión]
---

# Lean Cortex — Compresión de Contexto para el Equipo Nelson

## ¿Qué es?

lean-ctx es un binario Rust que actúa como servidor MCP y capa de shell hooks. Reduce el consumo de tokens al comprimir lecturas de archivos y output de comandos.

- Re-reads de archivos cacheados: ~13 tokens (vs ~2000 nativos)
- git status comprimido: ~120 tokens (vs ~800)
- 62 herramientas MCP disponibles

## Estado actual (servidor ai-server)

- Binario: `/home/server/.local/bin/lean-ctx`
- Versión: 3.6.16
- MCP configurado en: `~/.hermes/config.yaml`
- Shell hooks en: `~/.bashrc`

## Proyectos inicializados con lean-ctx

```
~/jarvis-demo-shell/           → AGENTS.md + .hermes.md
~/brainstorming/2026-05-21-deepagents-spike/  → .hermes.md
~/brainstorming/2026-05-19-forestai-poc/      → .hermes.md
~/brainstorming/2026-05-22-fleet-optimizer/   → .hermes.md
```

## Cómo usar en cada sesión

Los tools MCP se cargan automáticamente al iniciar sesión en Hermes. Usar:

| Tool MCP | En vez de | Ahorro |
|---|---|---|
| `ctx_read(path, mode)` | `read_file` / `cat` | Re-reads ~13 tok |
| `ctx_shell(command)` | `terminal` / bash | Comprime git/npm/docker |
| `ctx_search(pattern, path)` | `search_files` / grep | Resultados compactos |
| `ctx_tree(path, depth)` | `ls` / find | Mapa compacto |

## Inicializar en un proyecto nuevo

```bash
cd ~/brainstorming/NUEVO-PROYECTO
git init  # lean-ctx requiere un repo git para crear AGENTS.md
/home/server/.local/bin/lean-ctx init --agent hermes
```

## Ver ahorro acumulado

```bash
/home/server/.local/bin/lean-ctx gain
/home/server/.local/bin/lean-ctx gain --live  # tiempo real
```

## Diagnóstico

```bash
/home/server/.local/bin/lean-ctx doctor
```

## Integración con Holographic Memory

Son capas complementarias:
- **Holographic**: recuerda QUÉ estamos construyendo (hechos, preferencias, contexto de proyecto)
- **lean-ctx**: comprime CÓMO consumimos tokens al trabajar en ese contexto

No compiten — se potencian mutuamente.

## Daemon como servicio systemd

El daemon corre como servicio systemd de usuario para tracking persistente entre sesiones:

```bash
# Estado
systemctl --user status lean-ctx-daemon
/home/server/.local/bin/lean-ctx serve --status

# Reiniciar
systemctl --user restart lean-ctx-daemon

# Logs
journalctl --user -u lean-ctx-daemon -f
```

Socket: `/home/server/.local/share/lean-ctx/daemon.sock`
Servicio habilitado: arranca automáticamente con el usuario.

## Pitfalls

- lean-ctx requiere que el directorio sea un git repo para crear AGENTS.md. Si no lo es, hacer `git init` primero.
- Los tools MCP se cargan al inicio de sesión. Cambios en config requieren nueva sesión.
- El ahorro en `lean-ctx gain` se va acumulando con el uso — las primeras sesiones muestran 0% porque el caché está vacío.
- El daemon offline (`lean-ctx serve -d`) permite tracking persistente entre sesiones — considerar activarlo como servicio.
