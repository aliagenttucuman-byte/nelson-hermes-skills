# Bisonte — Esquema de Base de Datos (PostgreSQL :5435)

Estado verificado: 2026-06-17. 11 tablas + 1 vista.

## Tablas

| Tabla | Rol |
|-------|-----|
| `guia` | Registro histórico maestro de todas las guías de Bisonte |
| `contado_guias` | Planilla diaria completa (datos Transoft + anotaciones Edith) |
| `contado_anotacion` | Anotaciones manuales de Edith separadas y trazables |
| `contado_run` | Historial de cada ejecución del merge (quién, cuándo, estadísticas) |
| `cdo_guia` | Cruce CDO Sistema vs Trabajada con diferencias calculadas |
| `pte_fact_guia` | Cruce PTE Facturación Sistema vs Trabajada |
| `cdo_run` | Historial de ejecuciones del cruce CDO/PTE |
| `cat_estado_guia` | Catálogo maestro de estados con descripción y proceso |
| `cat_referente` | Catálogo de referentes (sucursales y comerciales) |
| `cat_sucursal` | Catálogo de sucursales activas |
| `v_guia_cruce` | Vista de auditoría cruzada (guía + contado + CDO + PTE) |

## Clave única del negocio

Campo `nro` — ejemplo: `A.0053.00111316`. Identifica cada guía de forma unívoca en todos los flujos.

## Estados de guías

| Código | Significado |
|--------|-------------|
| ED | En depósito |
| DT | En distribución |
| TT | En tránsito |
| RL | Entregado / cobrado |
| RT | Retornado |
| DO | Devuelto por orden |
| DI | Devuelto incidente |
| OB | Obervación |
| NR | No reclamado |

## Reglas de negocio del merge INICIAL → SISTEMA → FINAL

1. **Existentes** (281 guías): en INICIAL y en SISTEMA → preservar anotaciones de Edith
2. **Nuevos** (93 guías): solo en SISTEMA → JUSTIF=#N/A, REF=#N/A, OBS=#N/A
3. **Eliminados** (88 guías): solo en INICIAL → NO aparecen en FINAL (se cobraron/cerraron)
4. **Alertas** (18 guías): ESTADO cambió entre INICIAL y SISTEMA → marcar para revisión

## Columnas del FINAL (18 total)

Las primeras 14 vienen de Transoft (SISTEMA puro). Las 4 extras las agrega Edith:
- JUSTIFICACIÓN
- REFERENTE (sucursal/comercial: BA, CC, HM, MRA…)
- ESTADO (ED, DT, TT, RL, RT, DO, DI, OB, NR)
- OBSERVACIÓN (VER DIF, RETENCION, SALDO PENDIENTE…)

## Convención de colores en tabla (IMPORTANTE)

**NO pintar filas completas.** Solo pintar la celda/columna correspondiente a la alerta.
- La columna DIAS_ATRASO es la única con coloración automática
- Los registros con cambio de estado (alertas) se marcan en la columna de estado solamente
- Cualquier nueva regla de color → se agrega como columna específica, nunca como row highlight
