# PM Context Sources: indexación incremental (PoC + Brainstorming + GitHub)

Caso de uso: Resumen PM y chat JARVIS en dashboard operativo de Nelson.

## Objetivo
Evitar reindexar todo en cada request y mantener conteos/proyectos actualizados cuando hay cambios reales.

## Esquema recomendado
- Endpoint lectura: `GET /pm/instances` (también puede exponer alias semántico `projects`)
- Endpoint forzado: `POST /pm/instances/reindex`
- Respuesta:
  - `counts`: `{ total, poc, brainstorming, github }`
  - `groups`: listas por tipo
  - `instances` (compat) + `projects` (naming UX)
  - `from_cache`, `recalculated`, `generated_at`

## Regla de indexación
1. Calcular `local_signature` con hash de `{root, name, mtime}` para carpetas en `~/brainstorming` y `~/proyectos`.
2. Mantener caché persistente JSON con:
   - `local_signature`
   - `github_fetched_ts`
   - `counts`, `groups`, `instances`
3. Reusar caché si:
   - `local_signature` no cambió
   - y GitHub sigue dentro del TTL (ej. 300s)
4. Recalcular solo si cambia firma local o vence TTL GitHub.

## UX específica para Nelson
- En PM, mostrar “proyectos” (no “instancias”).
- Tipos esperados: PoC, Brainstorming, GitHub.
- Si no hay datos: mostrar estado explícito (`Cargando proyectos` / `Sin proyectos detectados`).

## Verificación rápida
- Primera llamada: `from_cache=false`, `recalculated=true`.
- Segunda llamada sin cambios: `from_cache=true`, `recalculated=false`.
- Crear carpeta de proyecto nueva y repetir: sube `counts.total` y `recalculated=true`.
