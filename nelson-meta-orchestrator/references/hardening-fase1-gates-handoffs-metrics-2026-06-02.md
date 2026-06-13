# Hardening Fase 1 — Gates, Handoffs y Métricas (2026-06-02)

## Señal de usuario que dispara esta guía
El usuario corrigió explícitamente el enfoque: **no duplicar el sistema** (no crear “otro orquestador”), sino evolucionar el `meta-orchestrator` existente de forma incremental.

## Regla operativa (durable)
Antes de proponer arquitectura nueva, hacer chequeo obligatorio:
1. ¿Esto ya existe en el Orchestrator actual?
2. ¿Se puede extender por capas (DB/API/UI) sin romper flujo vigente?
3. ¿La propuesta evita rebrand técnico tipo “v2” innecesario?

Si las respuestas son sí, implementar como hardening incremental.

## Implementación base validada en sesión

### Backend (`meta-orchestrator`)
Se agregaron tablas SQLite:
- `orchestration_gates`
- `orchestration_handoffs`
- `orchestration_metrics`

Se agregaron endpoints:
- `GET /runs/{task_id}/gates`
- `POST /runs/{task_id}/gates/evaluate`
- `GET /runs/{task_id}/handoffs`
- `GET /runs/{task_id}/metrics`

Comportamiento nuevo:
- `execute()` evalúa gates antes de ejecutar subtareas.
- Si hay hard-fail en gates, bloquea ejecución y registra evento.
- Se registra handoff estructurado por subtarea/iteración.
- Métricas de run persistidas: planned/done/failed/cancelled/retries/lead_time.

### Frontend (`orchestrator-dashboard`)
Se incorporó en `Orchestrator`:
- Bloque de `Quality Gates` (pass/review/fail)
- Bloque `KPIs del run`
- Señal de handoffs (contador + último handoff)
- Re-evaluación de gates previa a confirmar ejecución

## Verificación mínima recomendada
1. `python3 -m py_compile main.py nelson_orchestrator/orchestrator.py`
2. Smoke API:
   - `/plan`
   - `/run/confirm/{task_id}` (dry_run)
   - `/runs/{task_id}/gates`
   - `/runs/{task_id}/gates/evaluate`
   - `/runs/{task_id}/handoffs`
   - `/runs/{task_id}/metrics`
3. `npm run build` en dashboard
4. Verificar en UI que no se rompió flujo base Objetivo→Plan→Ejecución→Resultado

## Pitfall capturado
Proponer “nuevo sistema META-Agente” cuando ya hay Orchestrator funcional produce rechazo del usuario y retrabajo.

## Patrón correcto
**Hardening incremental del Orchestrator actual** con fases:
- F1: gates + handoffs + métricas
- F2: contrato estricto de handoff + políticas de transición
- F3: conectores/capabilities + observabilidad avanzada
