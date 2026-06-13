# Meta-Orchestrator Hardening (2026-06-02)

Contexto: usuario pidió explícitamente evitar duplicación de sistemas y evolucionar el Orchestrator existente.

## Decisión central
No crear “v2”. Extender incrementalmente el stack actual:
- Backend: `meta-orchestrator`
- Frontend: `orchestrator-dashboard`

## Patrón aplicado
1) GAP first
- Documentar “actual vs objetivo” antes de tocar arquitectura.

2) Fase 1 (base operativa)
- Tablas: `orchestration_gates`, `orchestration_handoffs`, `orchestration_metrics`.
- Endpoints: gates / handoffs / metrics.
- UI: bloques de Quality Gates + KPIs run.

3) Fase 2 (gobernanza)
- Política declarativa de transición (`allow`, `allow_with_review`, `block`).
- Persistencia policy por run (`orchestration_policy`).
- Handoff contract canónico + validación (`is_valid`, `validation_issues`).

4) Fase 3 (conectividad)
- Registro de conectores con `capabilities`, `fallback`, `required`.
- Endpoint `/connectors`.
- `/health` enriquecido con `connectors_summary`.
- UI: bloque “Conectores (Fase 3)”.

## Verificación mínima por fase
- Backend: `python3 -m py_compile ...`
- Frontend: `npm run build`
- Smoke API: plan, confirm, gates/evaluate, policy, handoffs, metrics, connectors, health
- Confirmar no regresión en flujo existente: goal → plan → execute → timeline/subtasks.

## Pitfalls observados
- No bloquear ejecución por umbrales demasiado agresivos en gate técnico durante rollout inicial.
- Si el policy engine se agrega, siempre exponer endpoint de lectura (`/runs/{task_id}/policy`) para trazabilidad UI/API.
- Añadir features nuevas sin romper semántica del dashboard operativo (action-oriented, lectura rápida).
