# Reglas de negocio — Coloreo IA Contado Bisonte

Confirmadas por Edith (19/06/2026). Se pinta SOLO la celda que cumple la regla — NUNCA la fila entera.

## Tabla de reglas

| Celda | Regla | Color |
|---|---|---|
| DIAS_ATRASO | > tolerancia | Rojo |
| DIAS_ATRASO | > tolerancia * 0.7 | Amarillo |
| DIAS_ATRASO | >= 0 (en tolerancia) | Verde |
| OBSERVACIÓN | valor == "VER DIF" | Rojo |
| fechaedit | DIAS_ATRASO > tolerancia | Rojo |

## Tolerancia por sucdest (CRÍTICO — no usar succobro)

El campo que define la tolerancia es `sucdest` (sucursal de destino de entrega), NO `succobro` (sucursal de cobro).

- `sucdest == "CC"` → tolerancia = 0 (cualquier DIAS_ATRASO > 0 ya es rojo)
- resto de sucursales → tolerancia = 7 días

### PITFALL clásico
`succobro` suele valer "BA" o "TUC" incluso para guías destinadas a CC.
Si se usa `succobro` para determinar la tolerancia, las guías de CC nunca se pintan rojo.
La función `_es_rojo_por_atraso(dias, sucdest)` debe recibir el campo `sucdest`, no `succobro`.

## Implementación en contado_merger.py

```python
def _es_rojo_por_atraso(dias_atraso, sucdest):
    """
    Tolerancia por sucdest:
    - CC: tolerancia 0 (cualquier atraso = rojo)
    - Resto: tolerancia 7 días
    """
    suc = str(sucdest or "").strip().upper()
    tolerancia = 0 if suc == "CC" else 7
    try:
        return int(dias_atraso) > tolerancia
    except (ValueError, TypeError):
        return False
```

## Aplicación en table_to_excel (descarga)

```python
dias_col_idx     = col_idx("DIAS_ATRASO")
observ_col_idx   = col_idx("OBSERVACIÓN")
fechaedit_col_idx = col_idx("fechaedit")
sucdest_col_idx  = col_idx("sucdest")

for row_idx, row in enumerate(rows, 2):
    dias    = row.get("DIAS_ATRASO")
    sucdest = str(row.get("sucdest", "") or "").strip().upper()
    tolerancia = 0 if sucdest == "CC" else 7

    try:
        dias_int = int(dias)
    except (ValueError, TypeError):
        dias_int = None

    # DIAS_ATRASO
    if dias_col_idx and dias_int is not None:
        if dias_int > tolerancia:
            ws.cell(row=row_idx, column=dias_col_idx).fill = RED_FILL
        elif dias_int > tolerancia * 0.7:
            ws.cell(row=row_idx, column=dias_col_idx).fill = YELLOW_FILL
        else:
            ws.cell(row=row_idx, column=dias_col_idx).fill = GREEN_FILL

    # OBSERVACIÓN — rojo si "VER DIF"
    if observ_col_idx:
        obs = str(row.get("OBSERVACIÓN", "") or "").strip().upper()
        if obs == "VER DIF":
            ws.cell(row=row_idx, column=observ_col_idx).fill = RED_FILL

    # fechaedit — rojo si DIAS_ATRASO supera tolerancia
    if fechaedit_col_idx and dias_int is not None and dias_int > tolerancia:
        ws.cell(row=row_idx, column=fechaedit_col_idx).fill = RED_FILL
```

## Archivos de prueba (19/06/2026)

Edith entregó `IA_CONTADO_1906.xlsx` con:
- Sheet INICIAL: 373 filas x 18 cols
- Sheet SISTEMA: 388 filas x 14 cols

Separados en:
- `test_data/Inicial19_06.xlsx`
- `test_data/Sistema1906.xlsx`
