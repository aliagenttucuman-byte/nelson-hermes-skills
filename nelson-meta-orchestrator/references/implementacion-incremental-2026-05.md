# Implementación incremental del Meta-Orquestador (mayo 2026)

## Qué ya existe y funciona hoy

- **JARVIS como orquestador manual**: el loop GOAL→DECOMPOSE→ASSIGN→EXECUTE→VERIFY
  ya ocurre via `delegate_task` + `subagent-driven-development`. No hay que construir
  el engine desde cero.
- **nelson-task-memory** (implementado 2026-05-26): servicio FastAPI + SQLite corriendo
  en `localhost:8742`. Systemd: `nelson-task-memory.service`. Repo:
  `aliagenttucuman-byte/nelson-task-memory`.

## Las 5 skills del meta-agente (creadas esta sesión)

Todas en `software-development/` del repo de skills:

| Skill | Rol |
|-------|-----|
| `nelson-meta-orchestrator` | Loop maestro, state machine, routing table |
| `nelson-task-memory` | Persistencia SQLite entre sesiones |
| `nelson-agent-routing` | Router declarativo, 12 categorías, LLM fallback |
| `nelson-eval-harness` | Score 0-100 por dimensión, gates de calidad |
| `nelson-context-handoff` | HandoffPacket Pydantic, 4 patrones |

## Qué falta construir para formalización completa

1. **Router declarativo** (`nelson-agent-routing`) — script Python que dado un
   input retorna qué agente/skill usar. Hoy JARVIS lo hace por intuición.
2. **Dashboard de estado React** — UI web para que Tony vea tareas en curso,
   pendientes y fallidas sin preguntar a JARVIS.

## Orden de construcción recomendado

```
Task Memory (✅ done) → Router declarativo → Dashboard React
```

## Pitfall descubierto: GitHub bloquea archivos > 100 MB

Durante el push del commit de skills, `.curator_backups/*/skills.tar.gz` (152 MB)
bloqueó el push. Solución:
```bash
git rm --cached .curator_backups/FECHA/skills.tar.gz
echo "*.tar.gz" >> .gitignore
echo "*.tar" >> .gitignore
git add .gitignore
git commit --amend --no-edit
git push
```
Agregar al `.gitignore` del repo de skills para evitar que vuelva a pasar.
