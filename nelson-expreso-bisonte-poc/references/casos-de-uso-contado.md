# Casos de Uso — Módulo Cobranzas Contado
## Relevados con Edith (gerenta cobranzas) — Junio 2026

### Planillas involucradas

| Planilla | Cols | Descripción |
|----------|------|-------------|
| SISTEMA  | 14   | Descarga fresca de Transoft. Fuente de verdad del día. Filtrada por estado=ED antes del merge. |
| INICIAL  | 18   | SISTEMA del día anterior + 4 cols manuales de Edith (JUSTIFICACIÓN, REFERENTE, ESTADO, OBSERVACIÓN) |
| FINAL    | 18   | Merge inteligente. Planilla de trabajo del día. |

Clave única: campo `nro` (ej: A.0053.00111316)

---

### Reglas de merge (CU-01 a CU-09)

**CU-01 Merge principal** — POST /api/v1/excel/merge-contado
- Sube INICIAL + SISTEMA → genera FINAL descargable + persiste en DB automáticamente
- Response headers: X-Stats-Existentes, X-Stats-Nuevos, X-Stats-Eliminados, X-Stats-EstadoCambio, X-Stats-DbSaved
- Si DB falla → igual entrega el Excel (no bloquea)

**CU-02 Existentes** — nro en INICIAL ∩ SISTEMA
- Datos Transoft: actualizados desde SISTEMA
- Campos manuales (JUSTIFICACIÓN, REFERENTE, ESTADO, OBSERVACIÓN): preservados de INICIAL intactos

**CU-03 Nuevos del día** — nro en SISTEMA − INICIAL
- ESTADO: auto-sugerido desde estado Transoft
- REFERENTE: auto-sugerido desde `succobro` (90% correlación directa — regla Edith). Si vacío → queda vacío.
- OBSERVACIÓN: auto-marcado "VER DIF" si importe ≠ saldo
- DIAS_ATRASO: calculado = fecha_hoy − fechaedit

**CU-04 Eliminados** — nro en INICIAL − SISTEMA
- No van a FINAL (cobrados/cerrados)
- Se contabilizan en stats

**CU-05 Alerta cambio de estado**
- Si estado SISTEMA ≠ estado INICIAL para un existente → se marca con flag
- Contabilizado en X-Stats-EstadoCambio

**CU-06 Filtrado estado ED**
- SISTEMA pre-filtrado: solo guías con estado=ED pasan al merge
- Otras matrices manejan el resto de estados

**CU-07 Deduplicación SISTEMA**
- Si mismo `nro` aparece más de una vez en SISTEMA → primera ocurrencia gana

**CU-08 Días de atraso**
- DIAS_ATRASO = fecha_hoy − fechaedit
- Tolerancias: CC = 4 días / resto sucursales = 7 días

**CU-09 VER DIF automático**
- Si importe ≠ saldo → OBSERVACIÓN = "VER DIF" (pago parcial, descuento, o error)

---

### Operaciones de UI/DB (CU-10 a CU-13)

**CU-10 Preview editable** — POST /api/v1/excel/contado/preview
- Sube Excel FINAL → devuelve JSON {columns, rows, _color per row}

**CU-11 Export ediciones** — POST /api/v1/excel/contado/export
- Recibe {columns, rows, original_bytes_b64} → devuelve Excel CONTADO_EDITADO_YYYYMMDD_HHMM.xlsx

**CU-12 Guardar DB** — POST /api/v1/excel/contado/save
- UPSERT en 3 tablas: `guia` (datos Transoft), `contado_anotacion` (campos Edith), `contado_guias` (legacy)

**CU-13 Cargar DB** — GET /api/v1/excel/contado/save
- Devuelve {columns, rows, total, updated_at} desde contado_guias

---

### Columnas del FINAL (orden exacto)

nro | JUSTIFICACIÓN | REFERENTE | ESTADO | OBSERVACIÓN | DIAS_ATRASO |
guiafec | razsocc | clase | fechaedit | sucori | sucdest |
importe | saldo | succobro | tiporec | sucursal | nrogen_a

Campos manuales (Edith): JUSTIFICACIÓN, REFERENTE, ESTADO, OBSERVACIÓN
Calculado: DIAS_ATRASO
Resto: Transoft

---

### DB Schema (PostgreSQL :5435)

```
guia              — datos base Transoft (nro PK, guiafec, razsocc, clase, fechaedit, sucori, sucdest, importe, saldo, succobro, tiporec, sucursal, nrogen_a, estado_actual, ultima_vez_visto, fuente)
contado_anotacion — campos manuales Edith (nro PK, justificacion, referente, estado_gestion, observacion, dias_atraso, updated_at, updated_by)
contado_guias     — tabla legacy todo-en-uno (compatibilidad con versión anterior)
```
