# Incremental hardening del Orchestrator (jun 2026)

Contexto durable: el usuario pidió explícitamente NO duplicar sistemas ni crear “Orchestrator v2”.
La evolución correcta es hardening incremental sobre el Orchestrator existente.

## Principio rector
- Reutilizar loop actual (plan → confirm → execute → verify).
- Agregar capas sin romper endpoints/flujos existentes.
- Validar con compile + smoke E2E antes de promover.

## Capa 1 (Fase 1): Gates + Metrics + Handoffs (base)

### Persistencia SQLite añadida
- `orchestration_gates`
- `orchestration_handoffs`
- `orchestration_metrics`

### Endpoints añadidos
- `GET /runs/{task_id}/gates`
- `POST /runs/{task_id}/gates/evaluate`
- `GET /runs/{task_id}/handoffs`
- `GET /runs/{task_id}/metrics`

### Comportamiento
- `execute()` evalúa gates antes de ejecutar subtareas.
- Si hay hard gate en fail, bloquea ejecución y registra evento.
- Se guardan handoffs por subtarea ejecutada.
- Se calculan KPIs básicos por run (planned/done/failed/cancelled/retries/lead_time).

## Capa 2 (Fase 2): Policy declarativa + validación estricta de handoff

### Persistencia SQLite añadida
- `orchestration_policy`

### Endpoint añadido
- `GET /runs/{task_id}/policy`

### Política declarativa (v1.0.0)
Decisiones posibles:
- `allow`
- `allow_with_review`
- `block`

Reglas iniciales:
- hard fail => `block`
- soft review => `allow_with_review`
- resto => `allow`

### Contrato de handoff canónico
Campos obligatorios:
- `run_id`, `subtask_id`, `phase`, `category`, `agents`, `status`, `timestamp`
- `done` debe tener `result`
- `failed` debe tener `error`

`GET /runs/{task_id}/handoffs` devuelve además:
- `is_valid`
- `validation_issues`

## Patrón de validación recomendado
1. `python3 -m py_compile ...`
2. Smoke TestClient:
   - `/plan`
   - `/run/confirm/{task_id}`
   - `/runs/{task_id}/gates/evaluate`
   - `/runs/{task_id}/policy`
   - `/runs/{task_id}/handoffs`
   - `/runs/{task_id}/metrics`
3. Frontend: `npm run build`

## Pitfall duradero
- No lanzar “sistema paralelo” para nuevas capacidades del meta-agente.
- Si falta algo (gates, policy, observabilidad), se integra por capas en el Orchestrator actual.