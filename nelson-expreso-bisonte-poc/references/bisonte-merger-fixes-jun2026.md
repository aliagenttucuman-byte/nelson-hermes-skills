# Bisonte Merger — Fixes y Pitfalls (jun 2026)

## PITFALL — Prefijos válidos de nro

El merger original solo aceptaba `A.` y `B.`. Transoft también genera `R.` (ej: `R.0009.00107766`).
El footer del informe genera filas con `Fi`, `Fe`, `Pe`, `Or`, `In` — son texto, NO guías.

Prefijos válidos: `A.`, `B.`, `R.`

```python
if nro and str(nro).strip()[:2] in ("A.", "B.", "R."):
```

## PITFALL — ESTADO debe venir siempre de SISTEMA

ESTADO lo pone Transoft, no Edith. Si una guía estaba en INICIAL como TT y cambió a ED en SISTEMA, el merger debe usar ED.

Síntoma: filtro por ED en la app da menos filas que en el Excel de Edith.

Fix en bloque EXISTENTES:
```python
# ESTADO siempre desde SISTEMA
row_data["ESTADO"] = estado_sis
```

MANUAL_COLS que SÍ preservamos: JUSTIFICACIÓN, REFERENTE, OBSERVACIÓN (no ESTADO).

## PITFALL — REFERENTE vacío en EXISTENTES no se auto-sugiere

Los EXISTENTES con REFERENTE=#N/A quedaban vacíos → se perdían al filtrar por REFERENTE=CC.

Fix después de copiar MANUAL_COLS:
```python
if not str(row_data.get("REFERENTE", "") or "").strip():
    succobro_ref = str(r_sis.get("succobro", "") or "").strip().upper()
    if succobro_ref:
        row_data["REFERENTE"] = succobro_ref
        stats["referente_auto"] = stats.get("referente_auto", 0) + 1
```

## PITFALL — Diferencia filtro REFERENTE vs succobro vs sucdest

- Filtro "REFERENTE=CC" → columna REFERENTE (anotación de Edith)
- Filtro "Suc. cobro=CC" → columna `succobro` (Transoft)
- Filtro "Sucdest=CC" → columna `sucdest` (Transoft)

Cuando Edith filtra "CC" en su Excel (columna K = sucdest), en la app es el filtro de Sucdest, no de REFERENTE.

## Colores por celda — reglas activas (jun 2026)

NO pintar filas enteras. Solo celdas:

**Frontend:**
- `OBSERVACIÓN` = "VER DIF" → fondo `#fee2e2`
- `fechaedit` → `#fee2e2` si DIAS_ATRASO > tolerancia (CC=4, resto=7)
- `DIAS_ATRASO` → verde/amarillo/rojo por tolerancia

Requiere `COL_FECHAEDIT` definido:
```typescript
const COL_FECHAEDIT = columns.find((_, i) => colLower[i].includes('fechaedit')) ?? ''
```

En `cellStyle`:
```typescript
const isVerDif = col === COL_OBSERV && String(row[col] ?? '').trim().toUpperCase() === 'VER DIF'
let fechaRojo = false
if (col === COL_FECHAEDIT && COL_FECHAEDIT) {
  const dias = parseInt(String(row[COL_DIAS] ?? ''), 10)
  const succobro = String(row[COL_SUCCOBRO] ?? '').trim().toUpperCase()
  const tolerancia = succobro === 'CC' ? 4 : 7
  if (!isNaN(dias) && dias > tolerancia) fechaRojo = true
}
const cellBg = isVerDif || fechaRojo ? '#fee2e2' : diasBg || undefined
```

## Diagnóstico de diferencias de conteo INICIAL vs FINAL

Cuando la app da menos filas ED que el Excel de Edith:

```python
# Guías que SISTEMA=ED pero INICIAL=otro estado
for nro, r_sis in dict_sis.items():
    if str(r_sis.get('estado') or '').strip().upper() != 'ED': continue
    r_ini = dict_ini.get(nro)
    if not r_ini: continue
    estado_ini = str(r_ini.get('ESTADO') or r_ini.get('estado') or '').strip().upper()
    if estado_ini != 'ED':
        print(f"nro={nro}  INICIAL={estado_ini}  SISTEMA=ED")

# Guías ED en FINAL de Edith pero no en FINAL de app
nros_ed_edith = set(r['nro'] for r in rows_final_edith if estado(r) == 'ED')
nros_ed_app   = set(r['nro'] for r in rows_final_app   if estado(r) == 'ED')
print("Faltantes en app:", nros_ed_edith - nros_ed_app)
```

## Filtros nuevos agregados (jun 2026)

- **sucori** (sucursal origen) — detectado como `colLower[i] === 'sucori'`
- **clase** — detectado como `colLower[i] === 'clase'`

Patrón de detección exacta (no includes, para no fallar con nombres similares):
```typescript
const COL_SUCORI = columns.find((_, i) => colLower[i] === 'sucori') ?? ''
const COL_CLASE  = columns.find((_, i) => colLower[i] === 'clase')  ?? ''
```
