# Rearmar combinado — patrón verificado (jun 2026)

`rearmar_combinado.py` YA NO EXISTE en el repo. Ir directo a este patrón.

## Fuente canónica

`/home/server/brainstorming/2026-06-03-expreso-bisonte-diccionario-datos-pablo/entregables-xlsx/CONTADO_PABLO_RUIZ_origen.xlsx`

Sheets origen (mayúsculas): `CDO SISTEMA`, `CDO TRABAJADA`, `PTE DE FACT SISTEMA`, `PF TRABAJADA`.

## PITFALL crítico — colisión al renombrar in-place

NO hacer esto:
```python
# MAL — produce colisión + sheets perdidas
wb = load_workbook(src)
for old, new in mapping.items():
    wb[old].title = new
for s in list(wb.sheetnames):
    if s not in mapping.values():
        del wb[s]
wb.save(dst)
```

Cuando dos sheets origen mapean a nombres que coinciden con sheets ya presentes, openpyxl renombra duplicado y el `del` borra la equivocada. Resultado verificado: solo 2 de 4 sheets sobreviven.

## Patrón correcto — Workbook nuevo + copy por filas

```python
from openpyxl import load_workbook, Workbook
import os

src = '/home/server/brainstorming/2026-06-03-expreso-bisonte-diccionario-datos-pablo/entregables-xlsx/CONTADO_PABLO_RUIZ_origen.xlsx'
dst = '/tmp/excel-merger/expreso_bisonte_combinado.xlsx'
os.makedirs('/tmp/excel-merger', exist_ok=True)

mapping = {
    'CDO SISTEMA': 'CDO Sistema',
    'PTE DE FACT SISTEMA': 'PTE de Fact Sistema',
    'CDO TRABAJADA': 'CDO TRABAJADA',
    'PF TRABAJADA': 'PF TRABAJADA',
}
order = ['CDO Sistema', 'PTE de Fact Sistema', 'CDO TRABAJADA', 'PF TRABAJADA']
rev = {v: k for k, v in mapping.items()}

src_wb = load_workbook(src)
out = Workbook(); out.remove(out.active)
for new_name in order:
    s = src_wb[rev[new_name]]
    t = out.create_sheet(new_name)
    for row in s.iter_rows(values_only=True):
        t.append(row)
out.save(dst)

# Verificación
assert load_workbook(dst).sheetnames == order
```

## Upload al backend

```python
import requests
with open(dst, 'rb') as f:
    r = requests.post('http://localhost:9000/api/v1/excel/upload',
        files={'file': ('expreso_bisonte_combinado.xlsx', f,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
        timeout=30)
print(r.json())  # rows ~406, sheets_detected con las 4
```
