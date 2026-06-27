# Pitfall: openpyxl rename in-place al rearmar combinado

Cuando `rearmar_combinado.py` no exista y haya que usar el fallback con `CONTADO_PABLO_RUIZ_origen.xlsx`, NO renombrar sheets con `wb[old].title = new` en-place. openpyxl puede:

- Mantener solo las últimas 2 sheets si los nombres nuevos colisionan parcialmente.
- Producir orden de sheets incorrecto, lo que rompe el upload al backend (que detecta los rows por nombre de sheet case-sensitive).

## Síntoma observado (jun 2026)

Subida al backend devuelve `rows: 403` y `columns: 17` con la primera columna llamada `" Informe: GF Pendientes de Cobro - CONTADO C/ESTADO DE GUIA "`. Eso significa que sobrevivieron solo `CDO TRABAJADA` y `PF TRABAJADA` y se perdieron `CDO Sistema` + `PTE de Fact Sistema`.

## Patrón verificado

Crear Workbook nuevo y copiar fila por fila en el orden deseado:

```python
import os
from openpyxl import load_workbook, Workbook

src = '/home/server/brainstorming/2026-06-03-expreso-bisonte-diccionario-datos-pablo/entregables-xlsx/CONTADO_PABLO_RUIZ_origen.xlsx'
dst = '/tmp/excel-merger/expreso_bisonte_combinado.xlsx'
os.makedirs('/tmp/excel-merger', exist_ok=True)

mapping = {
    'CDO SISTEMA': 'CDO Sistema',
    'PTE DE FACT SISTEMA': 'PTE de Fact Sistema',
    'CDO TRABAJADA': 'CDO TRABAJADA',
    'PF TRABAJADA': 'PF TRABAJADA',
}

src_wb = load_workbook(src)
out = Workbook()
out.remove(out.active)
order = ['CDO Sistema', 'PTE de Fact Sistema', 'CDO TRABAJADA', 'PF TRABAJADA']
rev_map = {v: k for k, v in mapping.items()}
for new_name in order:
    s = src_wb[rev_map[new_name]]
    t = out.create_sheet(new_name)
    for row in s.iter_rows(values_only=True):
        t.append(row)
out.save(dst)

# Verificar antes de subir
assert load_workbook(dst).sheetnames == order
```

Upload exitoso devuelve `rows: 406` y `file_id` válido.
