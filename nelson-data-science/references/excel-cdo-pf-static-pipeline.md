# Pipeline estático CDO/PF (sin IA)

Objetivo: reproducir el flujo operativo de `CDO Trabajada` y `PF Trabajada` usando solo reglas Python determinísticas.

## Inputs esperados
- `CDO Sistema` (origen cobranzas)
- `PTE de Fact Sistema` (origen facturación)

Alias de compatibilidad aceptables en PoC:
- `pendientes_cobro_contado`
- `pendientes_facturar`

## Reglas de negocio implementadas
1. **No CC**: excluir envíos marcados para no entrar en cuenta corriente.
2. **Bloqueo por facturación**: si un envío aparece en pendientes de facturar, no entra al circuito de cobro.
3. **Parciales/saldo**:
   - usar `saldo` si existe,
   - si no, derivar `saldo_pendiente = importe - cobro`.
4. **Transferencias T+1**: impacto al día siguiente para medios de pago con texto `transfer`.
5. **Asignación de referente**: completar faltantes con round-robin sobre pool configurable.
6. **Priorización**: ordenar por mayor saldo pendiente.

## Salidas
- Hoja `CDO Trabajada`
- Hoja `PF Trabajada`
- Hoja `KPIs` (opcional para control diario)

## Contrato API sugerido
`POST /api/v1/excel/pipeline/static`

Body mínimo:
```json
{
  "file_id": "<id_excel_subido>",
  "assignment_pool": ["Edith", "Referente 2", "Referente 3"]
}
```

Response mínima:
- `result.file_id`
- `result.download_url`
- `stages[]`
- `preview.cdo_trabajada[]`
- `preview.pf_trabajada[]`

## Validación recomendada
- Comparar contra trabajadas manuales solo como QA (conteo de filas, totales de saldo, envíos bloqueados por PF).
- No usar hojas trabajadas como input del pipeline productivo.
