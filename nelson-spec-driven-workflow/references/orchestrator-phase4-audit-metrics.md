# Orchestrator Hardening — Fase 4 (auditoría exportable + KPIs agregados)

Uso: cuando el sistema ya tiene timeline/subtasks/gates/handoffs/metrics persistidos y se necesita visibilidad ejecutiva + trazabilidad exportable sin duplicar arquitectura.

## Objetivo
Agregar, sobre el orquestador existente:
1. Export de auditoría por run en `json|csv`
2. Métricas agregadas por ventana temporal `24h|7d`

## Endpoints recomendados

- `GET /metrics/aggregate?window=24h|7d`
- `GET /runs/{task_id}/audit?format=json|csv`

## Contrato mínimo de `/metrics/aggregate`

```json
{
  "window": "24h",
  "generated_at": "...",
  "runs": {
    "started": 0,
    "finished": 0,
    "with_failures": 0,
    "avg_lead_time_sec": 0
  },
  "subtasks": {
    "planned": 0,
    "done": 0,
    "failed": 0,
    "cancelled": 0,
    "retries": 0,
    "completion_rate": 0.0
  },
  "gates": {
    "pass": 0,
    "review": 0,
    "fail": 0,
    "hard_fail": 0
  },
  "handoffs": {
    "total": 0,
    "invalid": 0
  }
}
```

## CSV de auditoría (run)

Usar filas canónicas con `record_type` para mezclar fuentes heterogéneas en un solo export:

- `run_summary`
- `policy`
- `timeline`
- `subtask`
- `gate`
- `handoff`

Columnas recomendadas:
`record_type, run_id, id, timestamp, status, name, detail`

## Pitfalls detectados

1. CSV sin `record_type` vuelve ambiguo el análisis.
2. Métricas acumuladas (sin ventana) pierden valor operativo.
3. Export calculado en frontend es frágil; debe vivir server-side.

## Validación mínima

1. `py_compile` backend
2. `npm run build` frontend
3. Smoke:
   - `/metrics/aggregate?window=24h` → 200
   - `/metrics/aggregate?window=7d` → 200
   - `/runs/{task_id}/audit?format=json` → 200
   - `/runs/{task_id}/audit?format=csv` → 200
4. (Opcional) smoke remoto por túnel expuesto
