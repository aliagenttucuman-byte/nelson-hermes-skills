# Pending Triage Checklist (Nelson)

Objetivo: responder "qué quedó pendiente" con evidencia multi-fuente y sin mezclar estado confirmado con hipótesis.

## Fuentes y criterio

1) Task Memory (SQLite/API)
- Confirmado: `pending`, `in_progress`, `failed`.
- Si está vacío: no concluir todavía.

2) TODO runtime
- Confirmado para la sesión actual.

3) Session Search
- Evidencia histórica, potencialmente incompleta.
- Etiquetar como "posible pendiente histórico".

4) Brainstorming docs
- `## Próximos pasos`
- `ideas-pendientes-skills.md`
- Esto es backlog documental (no ejecución activa).

5) Cronjobs
- Revisar `enabled=false` o `state=paused`.
- Reportar como pendiente operativo si corresponde.

## Plantilla de salida breve

- Estado tareas formales
- Pendientes en documentos
- Automatizaciones
- Posibles pendientes históricos

## Nota de calidad

Evitar afirmar "pendiente" si solo existe en transcript parcial sin estado explícito. Marcarlo como indicio y ofrecer verificación inmediata.
