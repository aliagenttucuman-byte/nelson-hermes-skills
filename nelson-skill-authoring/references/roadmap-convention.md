# Convención del ROADMAP de skills pendientes

> Ubicación: `~/brainstorming/YYYY-MM-DD-skills-faltantes-roadmap-v2/README.md`
> Skill padre: `nelson-skill-authoring` (Paso 5 del workflow)

## Estructura del README

El ROADMAP sigue siempre este esqueleto. No innovar — la consistencia es lo que hace que el cron semanal pueda parsearlo.

```markdown
# Roadmap de Skills Faltantes — Equipo Nelson (vN)

> Regenerado el YYYY-MM-DD. [Razón si aplica: "El archivo original se perdió..."]

## Principio rector
> "Comer de a poco. No arrancar todo junto. Cuando terminemos una tarea, consultar este roadmap."

Una skill por sprint (o menos). No abrir más de una a la vez. Marcar estado al cerrar.

## Estados
- 🔴 Pendiente (no arrancada)
- 🟡 En curso
- 🟢 Hecha (mergeada y usada)
- ⚪ Cancelada / absorbida

## Backlog completo

### <Área 1> (responsables)
| Skill | Estado | Descripción | Prioridad |
|-------|--------|-------------|-----------|

### <Área 2> (responsables)
| Skill | Estado | Descripción | Prioridad |
...

## TOP 3 críticas (marcadas 🔴)
1. ...
2. ...
3. ...

## Reglas de uso del roadmap
- Antes de empezar una skill, marcar como 🟡 en este README.
- Al cerrar, marcar como 🟢 y mover el detalle a `skills-done/`.
- Skills canceladas: dejar razón en este README.
- Cualquier agente que abra una tarea debe chequear este roadmap primero.

## Histórico
- YYYY-MM-DD: ...
- YYYY-MM-DD (sesión N): ...

## Sesiones de referencia
- `<session_id>` — descripción corta
```

## Áreas canónicas (no renombrar)

- Pablo (Comercial)
- Gino + Luigi (Gestión de proyectos) — sub-áreas pueden ser "Gino" o "Luigi" si la skill es solo de uno
- Diego (Ops / Infraestructura)
- Tony + I+D+I (Innovación / PoCs)
- Post-venta / Customer Success
- JARVIS / Agentes

## Caso perdido: cómo recrearlo (ya pasó en mayo 2026)

El ROADMAP original (`2026-05-15-skills-faltantes-roadmap/ROADMAP_SKILLS.md`) se perdió. El cron semanal lo buscó 2+ viernes seguidos. La reconstrucción tomó 5 minutos:

1. `session_search query="skills pendientes OR skill pendiente OR crear skill OR nuevo skill"` → 5 resultados, los más útiles los del cron `cron_2272f51eb985_...`
2. Cada cron semanal tiene un resumen que reconstruyó el backlog desde memoria
3. El README nuevo se arma copiando la estructura de la última versión buena + actualizando estados

**Prevención:** no hay forma de evitar que se pierda, pero podemos hacer que sea fácil de recrear. La skill nelson-skill-authoring apunta a este archivo explícitamente.

## Estados de patch frecuente

| Acción | Dónde patchear |
|--------|----------------|
| Marcar skill como 🟡 al empezar | Este README, columna "Estado" |
| Marcar como 🟢 al cerrar | Este README, columna "Estado" + línea en "Histórico" |
| Agregar skill nueva al backlog | Tabla del área correspondiente |
| Cancelar skill | Cambiar estado a ⚪, agregar nota de razón en Histórico |

NO crear un ROADMAP paralelo en otra ubicación. Si tenés 2, perdés la fuente de verdad.
