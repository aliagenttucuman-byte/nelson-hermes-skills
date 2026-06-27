# Bisonte IA CONTADO — Columnas Técnicas Verificadas (jun 2026)

## Fuente de datos
Archivo: `IA_CONTADO.xlsx` — sheets: INICIAL, SISTEMA, FINAL

## Headers del SISTEMA (CDO Contado de Transoft)
```
nro, guiafec, razsocc, clase, fechaedit, sucori, sucdest,
importe, saldo, succobro, estado, tiporec, sucursal, nrogen_a
```

## Tipos de dato verificados con openpyxl

| Campo     | Tipo en Excel         | Ejemplo                              | Uso en merger         |
|-----------|----------------------|--------------------------------------|----------------------|
| nro       | str                  | 'A.0053.00111316'                    | clave única del merge |
| guiafec   | str (dd/mm/yyyy)     | '27/05/2026'                         | fecha emisión guía    |
| fechaedit | datetime (naive)     | datetime(2026, 6, 11, 10, 56, 37)   | **base DIAS_ATRASO**  |
| estado    | str                  | 'ED', 'DT', 'TT', 'RL', 'RT', etc  | detectar cambio       |
| succobro  | str                  | 'CC', 'BA', 'JU', 'SA', 'RO'       | tolerancia días       |
| importe   | float                | 15400.0                             |                       |
| saldo     | float                | 15400.0                             |                       |

## Regla DIAS_ATRASO
```python
# fechaedit = datetime nativo de openpyxl (sin timezone)
# Usar hora Argentina (UTC-3) para "hoy"
from datetime import datetime, timezone, timedelta
ar_tz = timezone(timedelta(hours=-3))
hoy = datetime.now(ar_tz).date()
dias = (hoy - fechaedit.date()).days
```

**NO usar guiafec** — es la fecha de emisión del viaje, no la fecha de edición en el sistema.
**NO usar date.today()** — el server está en UTC, puede dar un día más que AR.

## Tolerancias de atraso para pintar ROJO
- Casa Central (succobro == 'CC'): > 4 días
- Resto de sucursales: > 7 días

## Estados de guía
| Código | Significado                              |
|--------|------------------------------------------|
| ED     | Entregada pendiente de cobro — único activo en esta matriz |
| DT     | Despachada en tránsito                  |
| TT     | En tránsito                              |
| RL     | Recibida en depósito local              |
| RT     | Retornada                               |
| DO     | Devuelta al origen                      |
| DI     | Documentación incompleta               |
| OB     | Observada                               |
| NR     | No retirada                             |

## Merge INICIAL + SISTEMA = FINAL

| Caso                   | Acción                                              |
|------------------------|-----------------------------------------------------|
| En ambos (existentes)  | Preservar JUSTIF, REFERENTE, ESTADO, OBS de INICIAL |
| Solo en SISTEMA (nuevo)| Campos manuales vacíos (no #N/A)                    |
| Solo en INICIAL (elim) | Descartar (ya cobrado/cerrado)                      |
| Estado cambió          | Campo __estado_sis__ distinto → ROJO en FINAL       |

## PITFALL — extra_cols en merge

Si se elimina la creación de columnas extra en el encabezado pero no se actualiza
`all_cols = FINAL_COLS + extra_cols`, el merger lanza NameError y devuelve HTTP 500.
El fix es `all_cols = FINAL_COLS` cuando no hay columnas extra.

## PITFALL — backend cachea módulos

Uvicorn no recarga módulos en caliente. Después de editar `contado_merger.py`:
```bash
fuser -k 9000/tcp 2>/dev/null
sleep 1
# Levantar con background=True en hermes terminal
```
Verificar siempre con `curl -s http://localhost:9000/health` antes de testear.
