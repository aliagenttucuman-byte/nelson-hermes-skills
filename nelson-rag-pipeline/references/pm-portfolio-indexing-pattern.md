# PM Portfolio Indexing Pattern (Proyectos)

Objetivo: que la vista Resumen PM y el chat de JARVIS trabajen con proyectos reales seleccionables, con métricas económicas y próximos pasos por item.

## Endpoint

`GET /pm/instances`

Debe devolver:
- `counts` (total + por grupo + por clase)
- `groups` (`project`, `brainstorming`, `github`)
- `projects` (alias de `instances` para naming de producto)
- flags de cache (`from_cache`, `recalculated`)

## Campos por proyecto

Mínimos recomendados:
- `id`, `type`, `name`, `updated_at`, `summary`
- `project_kind` (`mvp|poc|spike|idea|project`)
- `project_status` (`active|done|idea`)
- `economic_weight`: `{score, bucket, factors}`
- `next_steps`: `string[]`

## Estrategia incremental (una sola indexación + recalculo por cambios)

1. Construir `local_signature` con mtimes recursivos de carpetas de proyectos/brainstorming.
2. Reusar cache si:
   - `schema_version` vigente
   - firma local sin cambios
   - TTL remoto (GitHub) no vencido
3. Recalcular solo cuando cambie alguna condición anterior.
4. Persistir cache con:
   - `schema_version`
   - `generated_at`
   - `local_signature`
   - `github_fetched_ts`
   - payload completo

## Señales económicas sugeridas (heurística)

Para local projects:
- +kind (MVP > PoC > Spike > Idea)
- +status (active/done)
- +estructura (`backend`, `frontend`, `docker`, `tests`, `README`)

Para GitHub:
- stars, forks, open_issues, pushed_at reciente

## Extracción de próximos pasos

Orden de prioridad:
1. Secciones explícitas en README: `Próximos pasos`, `Roadmap`, `TODO`, `Backlog`.
2. Bullets de acción con verbos (`implementar`, `integrar`, `desplegar`, `validar`, etc.).
3. Fallback inferido (si falta documentación):
   - crear README
   - definir deploy reproducible
   - agregar smoke tests

## Verificación rápida

- `GET /pm/instances` dos veces seguidas:
  - 1ra: `recalculated=true`
  - 2da: `from_cache=true`
- modificar un README de proyecto y repetir:
  - debe volver `recalculated=true`
- confirmar que un item devuelve `economic_weight` y `next_steps` no vacíos.
