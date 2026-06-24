# Reglas de coloreo por celda — Bisonte Contado

Verificado con Edith y Pablo el 2026-06-19.
Aplica IGUAL en la UI y en el Excel descargado.

## Tolerancia por sucdest

CAMPO CLAVE: `sucdest` (sucursal de DESTINO de entrega) — NO `succobro` (sucursal de cobro)

En los datos reales: sucdest="CC", succobro="BA" — son DISTINTOS.
Usar succobro da tolerancia incorrecta para guías CC.

| sucdest | Tolerancia (días) |
|---|---|
| CC (Casa Central) | 0 — cualquier día de atraso = rojo |
| Resto de sucursales | 7 días |

## Reglas por celda

NO pintar filas enteras. Solo la celda que cumple la regla.

| Celda | Condición | Color |
|---|---|---|
| DIAS_ATRASO | > tolerancia | Rojo |
| DIAS_ATRASO | > tolerancia * 0.7 | Amarillo |
| DIAS_ATRASO | 0 <= valor <= tolerancia | Verde |
| OBSERVACIÓN | valor.strip().upper() == "VER DIF" | Rojo |
| fechaedit | DIAS_ATRASO > tolerancia | Rojo |

## Implementación en openpyxl (table_to_excel)

```python
def col_idx(name):
    return columns.index(name) + 1 if name in columns else None

dias_col_idx   = col_idx("DIAS_ATRASO")
observ_col_idx = col_idx("OBSERVACIÓN")
fecha_col_idx  = col_idx("fechaedit")
sucdest_col    = "sucdest"  # campo para determinar tolerancia

for row_idx, row in enumerate(rows, 2):
    sucdest = str(row.get("sucdest", "") or "").strip().upper()
    tolerancia = 0 if sucdest == "CC" else 7
    dias = row.get("DIAS_ATRASO")
    try:
        dias_val = float(dias) if dias is not None else None
    except (ValueError, TypeError):
        dias_val = None

    # DIAS_ATRASO
    if dias_col_idx and dias_val is not None:
        if dias_val > tolerancia:
            ws.cell(row=row_idx, column=dias_col_idx).fill = RED_FILL
        elif dias_val > tolerancia * 0.7:
            ws.cell(row=row_idx, column=dias_col_idx).fill = YELLOW_FILL
        else:
            ws.cell(row=row_idx, column=dias_col_idx).fill = GREEN_FILL

    # OBSERVACIÓN
    if observ_col_idx:
        obs = str(row.get("OBSERVACIÓN", "") or "").strip().upper()
        if obs == "VER DIF":
            ws.cell(row=row_idx, column=observ_col_idx).fill = RED_FILL

    # fechaedit
    if fecha_col_idx and dias_val is not None and dias_val > tolerancia:
        ws.cell(row=row_idx, column=fecha_col_idx).fill = RED_FILL
```

## Pitfalls

- El backend viejo puede quedar corriendo tras pkill — verificar con `pgrep -a -f 'python.*main'` y matar por PID antes de relanzar.
- Después de cada fix al código Python, reiniciar uvicorn — el proceso viejo sigue sirviendo el código anterior.
- La columna J del informe de Edith = DIAS_ATRASO.
- Edith compara contra "las del 19" = guías entregadas el día corriente = DIAS_ATRASO == 0.
