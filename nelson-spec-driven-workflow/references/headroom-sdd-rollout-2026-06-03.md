# Headroom rollout para SDD (2026-06-03)

## Contexto

Durante la sesión, Tony corrigió el scope: la evaluación de Headroom debía hacerse a nivel **SDD/JARVIS**, no dentro de la PoC operativa de Excel.

Aprendizaje durable: cuando se evalúan capas de compresión de contexto, primero se decide **ubicación transversal por fase SDD**; luego se baja (o no) a implementaciones de proyectos puntuales.

## Decisión de arquitectura

Aplicación recomendada por fases:

1. Discovery / Relevamiento
2. Verification / QA / Debug
3. (Condicional) revisión de specs

No aplicar en:
- pipelines determinísticos 1:1 auditables
- validaciones/cálculos donde se exige fidelidad cruda completa

## Validación técnica realizada

Se instaló `headroom-ai` y se ejecutó benchmark local orientado a payloads de tool output:

- `qa-log-stacktrace`: 26,095 → 6,886 tokens (73.61% ahorro)
- `discovery-json-rows`: 74,167 → 39,003 tokens (47.41% ahorro)
- promedio: **60.51% ahorro**

## KPI de adopción propuesto

Gate para pasar de piloto a adopción estable:

- ahorro promedio >= 35%
- calidad semántica sin degradación
- sin aumento de retrabajo

## Artefactos de la sesión

- `/home/server/brainstorming/2026-06-03-headroom-sdd-rollout/HEADROOM-SDD-PLAYBOOK-v1.md`
- `/home/server/brainstorming/2026-06-03-headroom-sdd-rollout/CHECKLIST-IMPLEMENTACION-v1.md`
- `/home/server/brainstorming/2026-06-03-headroom-sdd-rollout/scripts/benchmark_headroom_sdd.py`
- `/home/server/brainstorming/2026-06-03-headroom-sdd-rollout/scripts/start_headroom_proxy_sdd.sh`
