# PM Summary Structure (Dashboard /pm)

Objetivo: reemplazar la percepción de "kanban técnico" por una vista de gestión de proyecto orientada a stakeholders.

## Secciones mínimas

1) Header ejecutivo
- Proyecto
- Sponsor
- PM responsable
- Estado general
- Progreso (%)
- Fechas (inicio / objetivo)

2) Objetivos + KPI (tabla)
- ID
- Objetivo
- KPI medible
- Owner
- Estado

3) Hitos y cronograma
- Nombre del hito
- Fecha objetivo
- Estado (Completado / En curso / Pendiente)
- Nota

4) Riesgos
- Riesgo
- Impacto
- Probabilidad
- Mitigación

5) Resumen económico
- Ítem
- Plan
- Actual
- Desvío

6) Próximas acciones
- Lista numerada (3-5 acciones concretas)

7) Gobernanza
- Cadencia de seguimiento
- Decisión activa
- Próximo checkpoint

## UX Guidelines

- Usar tablas para lectura rápida y comparación.
- Limitar bloques de texto largo.
- Status con pills semánticos (verde/azul/amarillo/gris).
- Priorizar lenguaje de negocio sobre detalle técnico.

## Migración desde Kanban

- Si hay Kanban existente, mantenerlo como vista secundaria opcional.
- En menú lateral, renombrar etiqueta principal a "Resumen PM".
- Evitar drag-and-drop como interacción principal para stakeholders ejecutivos.

## Verificación

- `npm run build` exitoso.
- Revisar visualmente que la vista se entiende sin contexto técnico previo.
- Confirmar que en demo de 2-3 minutos se recorren objetivos, riesgos y próximos pasos sin entrar a detalle de implementación.
