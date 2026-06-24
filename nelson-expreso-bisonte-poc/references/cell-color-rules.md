# Reglas de Color por Celda — Bisonte CONTADO (Edith + sesión 2026-06-19)

## Reglas confirmadas por Edith (operación real)

### Tolerancia por sucdest (NO succobro)
- `sucdest == "CC"` → tolerancia = 0 días (cualquier atraso = rojo, sin excepciones)
- Cualquier otra sucursal → tolerancia = 7 días
- **ERROR FRECUENTE**: usar `succobro` en vez de `sucdest`. Una guía entregada en CC puede tener `succobro="BA"` — eso da falsos negativos. El campo correcto es `sucdest`.

### Columnas con color en UI y en Excel descargado (1:1)

| Columna | Condición | Color |
|---------|-----------|-------|
| DIAS_ATRASO | > tolerancia(sucdest) | 🔴 Rojo |
| DIAS_ATRASO | > tolerancia * 0.7 | 🟡 Amarillo |
| OBSERVACIÓN | valor == "VER DIF" (strip, upper) | 🔴 Rojo |
| fechaedit | DIAS_ATRASO > tolerancia | 🔴 Rojo |

### Regla de Nelson (explícita, sesión 2026-06-19)
> "no pintemos filas enteras, sino pintemos la columna correspondiente a la regla"

**NUNCA pintar la fila entera.** Solo la celda específica que cumple la regla.

## Implementación openpyxl (patrón correcto)

```python
# Precalcular índices 1-based UNA VEZ fuera del loop
def col_idx(name):
    return columns.index(name) + 1 if name in columns else None

dias_col_idx  = col_idx("DIAS_ATRASO")
obs_col_idx   = col_idx("OBSERVACIÓN")
fecha_col_idx = col_idx("fechaedit")
suc_col_idx   = col_idx("sucdest")  # para determinar tolerancia

# Fills reutilizables
RED_FILL    = PatternFill(fill_type="solid", fgColor="FFC7CE")
YELLOW_FILL = PatternFill(fill_type="solid", fgColor="FFEB9C")

# Dentro del loop de filas
for row_idx, row in enumerate(rows, 2):
    # Escribir toda la fila primero
    for col_i, col_name in enumerate(columns, 1):
        ws.cell(row=row_idx, column=col_i, value=row.get(col_name))

    # Después aplicar colores por celda según regla
    sucdest = str(row.get("sucdest") or "").strip().upper()
    tolerancia = 0 if sucdest == "CC" else 7
    
    try:
        dias = int(float(str(row.get("DIAS_ATRASO", 0) or 0)))
    except:
        dias = 0

    if dias_col_idx:
        if dias > tolerancia:
            ws.cell(row=row_idx, column=dias_col_idx).fill = RED_FILL
        elif dias > tolerancia * 0.7:
            ws.cell(row=row_idx, column=dias_col_idx).fill = YELLOW_FILL

    if obs_col_idx:
        obs = str(row.get("OBSERVACIÓN", "") or "").strip().upper()
        if obs == "VER DIF":
            ws.cell(row=row_idx, column=obs_col_idx).fill = RED_FILL

    if fecha_col_idx and dias > tolerancia:
        ws.cell(row=row_idx, column=fecha_col_idx).fill = RED_FILL
```

## Pitfall: proceso que corre con código viejo

Al reiniciar backend después de un fix, verificar que no quedó el proceso anterior:
```bash
pgrep -a -f 'uvicorn'   # ver PID real
kill <PID>              # matar el correcto
# Luego levantar nuevo proceso
```
`pkill -f uvicorn` puede fallar silenciosamente si el proceso tiene permisos distintos. Usar `pgrep` primero para confirmar el PID y matarlo por número.
