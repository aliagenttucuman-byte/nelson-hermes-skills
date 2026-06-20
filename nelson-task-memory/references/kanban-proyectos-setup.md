# Kanban de proyectos — AlegentAI + LAN LATAM (setup 2026-06-19)

## Boards creados

```bash
hermes kanban boards list
# alegent-ai  — Alegent AI  🤖  #8b5cf6
# lan-latam   — LAN LATAM   ✈️  #0ea5e9
```

## Tareas iniciales cargadas

### Alegent AI
- Bisonte colores Excel por regla de negocio
- Bisonte pipeline deploy productivo
- Bisonte módulo Cuenta Corriente
- ForestAI demo Gino producción
- Infra Honcho sesiones diarias

### LAN LATAM
- Análisis stack GCP + Terraform
- Spike ML finanzas (CASK, RASK, Load Factor)
- Pipeline datos BTS
- Dashboard KPIs operativos

## Comandos clave

```bash
# Ver tareas de un board
hermes kanban --board alegent-ai list
hermes kanban --board lan-latam list

# Crear tarea (con contexto body)
hermes kanban --board alegent-ai create --triage --body "descripción" "Título de la tarea"

# PITFALL: --board va ANTES del subcomando, no después
# ✓ hermes kanban --board alegent-ai list
# ✗ hermes kanban list --board alegent-ai
```

## El kanban de Hermes es un task runner

No es un kanban visual con columnas drag-and-drop.
Es un sistema de colas con workers que ejecutan tareas de forma autónoma.
Para visualizar el estado: `hermes kanban --board <slug> list`

## Contexto de uso

Nelson maneja 3 frentes:
- Alegent AI — técnico (Bisonte, ForestAI, demos, infra)
- LAN LATAM — técnico (finanzas, ML, GCP)
- YPF — gestión de equipo, sin board en Hermes
