# Pipeline Excel 4 sheets — Cobranzas/Furación (operativo)

Caso de uso: convertir una planilla operativa en un pipeline visible en UI y descargable.

## Input esperado (4 sheets)
- `pendientes_cobro_contado`
- `pendientes_cobro_trabajada`
- `pendientes_facturar`
- `pendientes_facturar_trabajada`

## Reglas aplicadas
1. `envio_id` normalizado como string en todas las hojas.
2. Se arma base de cobranza con merge `contado + trabajada`.
3. Se excluye `incluir_cc = false`.
4. Se excluyen de cobranza los `envio_id` que estén en `pendientes_facturar`.
5. `saldo_pendiente = max(importe_total - monto_cobrado, 0)`.
6. Estado cobro:
   - `cobrado` si saldo 0
   - `parcial` si saldo > 0
7. Transferencias impactan T+1 (`fecha_impacto`).
8. Referente faltante se autoasigna (round-robin).

## Output recomendado
Excel de salida con:
- `pipeline_cobranza`
- `pipeline_facturacion`
- `dashboard` (KPIs)

Y response API para UI:
```json
{
  "ok": true,
  "result": {"file_id": "...", "download_url": "/api/v1/excel/download/..."},
  "kpis": {"cobros_operativos": 0, "pendientes_facturar": 0, "monto_pendiente_total": 0},
  "stages": [{"name": "Insumo Cobranza", "rows": 0}],
  "preview": {"cobranza": [], "facturacion": []}
}
```

## Guardrail JSON (clave)
Al serializar previews de pandas:
- reemplazar `NaN/NaT` por `None`
- convertir fechas/timestamps a `isoformat()`

Si no se hace, FastAPI puede fallar con:
`ValueError: Out of range float values are not JSON compliant`
