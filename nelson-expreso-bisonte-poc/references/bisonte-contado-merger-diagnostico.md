# Diagnóstico del merger IA CONTADO — jun 2026

## Script de diagnóstico rápido

Cuando los números de filas no coinciden entre la app y el Excel de Edith, correr este análisis:

```python
import openpyxl
from collections import Counter

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

nros_ini = set(dict_ini)
nros_sis = set(dict_sis)

print(f"INICIAL: {len(nros_ini)} filas")
print(f"SISTEMA: {len(nros_sis)} filas")
print(f"Existentes: {len(nros_ini & nros_sis)}")
print(f"Nuevos: {len(nros_sis - nros_ini)}")
print(f"Eliminados: {len(nros_ini - nros_sis)}")

# ED en SISTEMA que en INICIAL tenían otro estado
print("\nGuías que cambiaron a ED (el merger las preservaría con estado viejo SIN el fix):")
for nro, r_sis in dict_sis.items():
    if str(r_sis.get('estado') or '').strip().upper() != 'ED':
        continue
    r_ini = dict_ini.get(nro)
    if not r_ini:
        continue
    estado_ini = str(r_ini.get('ESTADO') or r_ini.get('estado') or '').strip().upper()
    if estado_ini != 'ED':
        print(f"  {nro}  INICIAL={estado_ini} → SISTEMA=ED")

# Prefijos únicos en SISTEMA
prefijos = Counter(r['nro'][:2] for r in dict_sis.values())
print(f"\nPrefijos en SISTEMA: {dict(prefijos)}")
```

## Causas conocidas de discrepancia de filas

| Causa | Síntoma | Fix |
|---|---|---|
| ESTADO no actualizado | Guías que cambiaron a ED no aparecen en filtro ED | ESTADO siempre desde SISTEMA |
| REFERENTE vacío en existentes | Filtro REFERENTE=CC pierde guías | Auto-sugerir desde succobro si REFERENTE vacío |
| Prefijo R. excluido | Guías R.XXXX no aparecen | Agregar R. a prefijos válidos |
| Duplicados en SISTEMA | Filas de más o de menos | Se deduaplica por nro, se queda con primera ocurrencia |

## Resultado verificado con archivos de Edith (jun 2026)

- INICIAL: 369 filas, 52 ED
- SISTEMA: 377 filas, 58 ED (incluyendo 3 duplicados → 55 únicos)
- FINAL esperado: 374 filas, 55 ED
- Filtro ED + REFERENTE=CC: 12 filas (coincide con Excel manual de Edith)

## Prefijos de nro en Transoft

- `A.` — guías normales (mayoría)
- `B.` — guías normales (segunda categoría)
- `R.` — guías tipo R (minoría, ej: R.0009.00107766)
- `Fi`, `Fe`, `Pe`, `Or`, `In` → footer del informe, NO son guías
