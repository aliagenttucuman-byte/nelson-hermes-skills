# Bisonte Contado — Fixes y Pitfalls del Merger (jun 2026)

## FIX — Prefijos de nro válidos: no solo A. y B.

El SISTEMA de Transoft puede tener guías con prefijo `R.` además de `A.` y `B.`.
El filtro en `_sheet_to_dicts` debe aceptar los tres:

```python
if nro and str(nro).strip()[:2] in ("A.", "B.", "R."):
```

Las filas con prefijos `Fi`, `Fe`, `Pe`, `Or`, `In` son el footer del informe — NO son guías.
Si aparecen nuevos prefijos en el futuro, agregarlos a esa tupla.

---

## FIX — ESTADO en EXISTENTES debe venir de SISTEMA, no del INICIAL

El ESTADO lo pone Transoft, no Edith. Si una guía cambia de TT→ED en Transoft entre el
INICIAL y el SISTEMA, el merger debe reflejar ese cambio.

Síntoma: el Excel de Edith muestra más filas ED que la App (ej: 55 vs 47).
Causa: 8 guías tenían estado diferente en INICIAL (TT, RL) y cambiaron a ED en SISTEMA.
El merger las preservaba con estado viejo → el filtro ED del frontend las perdía.

Fix en el bloque de EXISTENTES de `contado_merger.py`, después de copiar MANUAL_COLS:
```python
# ESTADO siempre desde SISTEMA (lo pone Transoft, no Edith)
row_data["ESTADO"] = estado_sis
```

---

## FIX — REFERENTE vacío en EXISTENTES debe auto-sugerirse desde succobro

Síntoma: filtro REFERENTE=CC muestra menos filas en la App que en el Excel de Edith (ej: 8 vs 12).
Causa: guías que cambiaron de estado (TT/RL→ED) tenían REFERENTE=#N/A en el INICIAL.
El merger las limpiaba a vacío sin sugerir el succobro.

Fix en el bloque de EXISTENTES, después de sobreescribir ESTADO:
```python
# REFERENTE: si viene vacío del INICIAL → auto-sugerir desde succobro
if not str(row_data.get("REFERENTE", "") or "").strip():
    succobro_ref = str(r_sis.get("succobro", "") or "").strip().upper()
    if succobro_ref:
        row_data["REFERENTE"] = succobro_ref
        stats["referente_auto"] = stats.get("referente_auto", 0) + 1
```

---

## FIX — Colores por columna: NO pintar filas enteras

REGLA EXPLÍCITA (Nelson, jun 2026): nunca `COLOR_STYLE[row._color]` en el `<tr>` o en
el `<td>` del número de fila. Solo colorear celdas específicas.

Columnas con color activo:
- `OBSERVACIÓN` → rojo (`#fee2e2`) si el valor es "VER DIF"
- `fechaedit` → rojo si DIAS_ATRASO > tolerancia (CC=4, resto=7)
- `DIAS_ATRASO` → verde/amarillo/rojo según tolerancia

Patrón en `cellStyle` de `ContadoTable.tsx`:
```typescript
const COL_FECHAEDIT = columns.find((_, i) => colLower[i].includes('fechaedit')) ?? ''

const isVerDif = col === COL_OBSERV &&
  String(row[col] ?? '').trim().toUpperCase() === 'VER DIF'

let fechaRojo = false
if (col === COL_FECHAEDIT && COL_FECHAEDIT) {
  const dias = parseInt(String(row[COL_DIAS] ?? ''), 10)
  const succobro = String(row[COL_SUCCOBRO] ?? '').trim().toUpperCase()
  const tolerancia = succobro === 'CC' ? 4 : 7
  if (!isNaN(dias) && dias > tolerancia) fechaRojo = true
}

const cellBg = isVerDif || fechaRojo ? '#fee2e2' : diasBg || undefined
return { ...(cellBg ? { background: cellBg } : {}), ... }
```

El `<td>` del número de fila NO lleva color:
```tsx
<td style={{ padding: '0.2rem 0.4rem', border: '1px solid #e2e8f0', color: '#94a3b8', ... }}>
```

---

## Botones de PRIORIDAD — ELIMINADOS (jun 2026)

Los botones 1️⃣ Sin asignar / 2️⃣ Rojos / 3️⃣ Ver diferencia / 4️⃣ Retenciones y los badges
de conteo (Rojos, Amarillos, Sin asignar) confunden a los usuarios operativos.
Nelson los eliminó en jun 2026. Solo mantener contadores: Total y Visibles.
NO agregarlos de vuelta sin pedido explícito.

---

## Diagnóstico — diferencia de conteo entre Excel de Edith y App

Cuando el conteo de ED (u otro estado) no coincide:

1. Verificar prefijos de nro aceptados (`A.`, `B.`, `R.`)
2. Verificar guías EXISTENTES con ESTADO diferente en INICIAL vs SISTEMA
   → el merger debe usar SISTEMA como fuente de verdad para ESTADO
3. Verificar REFERENTE vacío en EXISTENTES que cambiaron de estado
   → auto-sugerir desde succobro igual que los NUEVOS
4. Verificar duplicados en SISTEMA (se deduplica por nro, primera ocurrencia)

Script de diagnóstico rápido:
```python
import openpyxl

def load_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    header_row = None
    for r in range(1, 6):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if v and str(v).strip().lower() == 'nro':
                header_row = r
                break
        if header_row:
            break
    headers = [str(ws.cell(header_row, c).value or '').strip() for c in range(1, ws.max_column + 1)]
    rows = []
    for r in range(header_row + 1, ws.max_row + 1):
        row = {headers[c-1]: ws.cell(r, c).value for c in range(1, ws.max_column + 1)}
        nro = str(row.get('nro') or '').strip()
        if not nro or nro[:2] not in ('A.', 'B.', 'R.'):
            continue
        row['nro'] = nro
        rows.append(row)
    return {r['nro']: r for r in rows}

dict_ini = load_rows('INICIAL.xlsx')
dict_sis = load_rows('SISTEMA.xlsx')

nros_existentes = set(dict_ini) & set(dict_sis)
for nro in sorted(nros_existentes):
    e_ini = str(dict_ini[nro].get('ESTADO') or dict_ini[nro].get('estado') or '').upper()
    e_sis = str(dict_sis[nro].get('estado') or '').upper()
    if e_ini != e_sis:
        ref = str(dict_ini[nro].get('REFERENTE') or '').strip()
        print(f"{nro}: INICIAL={e_ini} → SISTEMA={e_sis}  REF={ref or '(vacío)'}")
```

---

## Nuevos filtros en ContadoTable (jun 2026)

Filtros agregados: sucori (📍 Suc. origen), clase (📦 Clase).
Patrón de detección de columna:
```typescript
const COL_SUCORI = columns.find((_, i) => colLower[i] === 'sucori') ?? ''
const COL_CLASE  = columns.find((_, i) => colLower[i] === 'clase') ?? ''
```
Valores únicos dinámicos + select condicional al igual que sucDest y sucCobro.
