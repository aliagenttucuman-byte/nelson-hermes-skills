# Reglas de coloreo celda-por-celda — Excel descargado Bisonte

## Principio
NO pintar filas enteras. Solo la celda que cumple la regla.
El Excel descargado debe replicar 1:1 lo que muestra la UI.

## Función que aplica los colores: `table_to_excel()` en contado_merger.py

### Regla 1 — Celda DIAS_ATRASO
Tolerancia por succobro — confirmado con Edith jun 2026:
- CC (Casa Central) → tolerancia = 0 días (cualquier día de atraso = rojo, sin excepción)
- Resto de sucursales → tolerancia = 7 días

| Condición | Color celda |
|-----------|-------------|
| dias > tolerancia | Rojo (#FFFF0000) |
| dias > tolerancia * 0.7 | Amarillo claro (#FFFEF9C3) |
| dias >= 0 | Verde (#FFDCFCE7) |

### Regla 2 — Celda OBSERVACIÓN
- Si el valor es exactamente "VER DIF" → Rojo (#FFFF0000)

### Regla 3 — Celda fechaedit
- Si DIAS_ATRASO > tolerancia → Rojo (#FFFF0000)
- (misma tolerancia que Regla 1)

## Origen de las reglas (UI — ContadoTable.tsx)
```typescript
// Regla 1
const tolerancia = succobro === 'CC' ? 0 : 7   // CC sin tolerancia — Edith jun 2026
if (dias > tolerancia) diasBg = '#fee2e2'        // rojo
else if (dias > Math.floor(tolerancia * 0.7)) diasBg = '#fef9c3'  // amarillo
else if (dias >= 0) diasBg = '#dcfce7'           // verde

// Regla 2
const isVerDif = col === COL_OBSERV && val.trim().toUpperCase() === 'VER DIF'

// Regla 3
if (col === COL_FECHAEDIT && dias > tolerancia) fechaRojo = true
```

## Historial de cambios
- 2026-06-19 v3: CC tolerancia corregida de 4 → 0 días. Edith confirmó:
  "De casa central es inmediato del día anterior" — sin tolerancia.
- 2026-06-19 v2: Se eliminó pintado de filas enteras (pedido de Nelson).
  Antes: fill aplicado a toda la fila según _color (red/yellow/none).
  Ahora: solo celda individual por regla de negocio.
- Corrección previa: se pintaba todo de rojo porque el fill se pasaba
  a write_row() con None — se ignoraba, pero en table_to_excel sí se aplicaba fila entera.

## Pitfall — backend viejo en memoria
Si el fix no toma efecto en la descarga, verificar que el proceso uvicorn
reinició correctamente. El proceso anterior puede quedar zombie con el código viejo:
```bash
pgrep -a -f 'python.*main'   # ver qué PIDs están corriendo
kill <pid_viejo>
# luego levantar con background=true
```
