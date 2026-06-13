# PM Resumen Operativo + Valuación por Proyecto (patrón reusable)

Objetivo: que la vista PM del dashboard no muestre datos estáticos, sino datos reales por proyecto seleccionado, con fallback automático cuando no existe documentación financiera.

## Modelo recomendado

Cada proyecto debe exponer en `/pm/instances`:

- `project_valuation.mode`: `documented | auto`
- `project_valuation.mvp_total_investment_usd`
- `project_valuation.development_cost_usd`
- `project_valuation.operational_cost_4m_usd`
- `project_valuation.monthly_avg_usd`
- `project_valuation.revenue_scenarios[]`
- `project_valuation.source_files[]`

## Reglas de generación

1) Intentar `documented` primero:
- Buscar Charter / Estimación / Benchmark dentro del path del proyecto seleccionado.
- Parsear montos y escenarios con regex tolerante (tablas markdown + texto corrido).

2) Si no hay documentación suficiente, generar `auto`:
- Basado en señales reales: tipo, estado, score técnico, backend/frontend/docker/tests.
- Ajustar por tamaño real del código (`size_files`, `size_loc`) excluyendo: `.git`, `node_modules`, `dist`, `build`, `.codegraph`, `venv`, `.venv`, `__pycache__`.
- Usar tasa configurable (base usada: USD 30/h).

3) UI PM:
- Mostrar siempre “Tipo de valuación” (documentada vs automática).
- Si no hay valuación aún, botón `Generar valuación automática` en contexto del proyecto seleccionado.
- Botón `Actualizar datos del PM` para forzar reindex.

## Endpoints sugeridos

- `GET /pm/instances?limit=&force_refresh=`
- `POST /pm/instances/reindex`
- `POST /pm/projects/valuation/generate` con `{ project_id }`

## Pitfalls críticos

- **Contaminación cruzada de valuación**: no mezclar documentos de otros proyectos al inferir un proyecto.
  - Fix: restringir parsing documental al `path` del proyecto seleccionado.
- **force_refresh incompleto**: reindex debe recalcular local+github cuando se fuerza.
- **Fallback engañoso**: no mostrar números heurísticos como si fueran reales sin etiquetar modo `auto`.

## Señales de UX esperadas

- Cambiar proyecto => redibujo completo de KPIs, hitos, riesgos, valuación y próximos pasos.
- Filtros genéricos (`tipo`, `estado`, `search`) sobre la misma estructura de datos.
- Mensajes accionables, no bloqueantes: si falta valuación documentada, ofrecer generación automática en un click.
