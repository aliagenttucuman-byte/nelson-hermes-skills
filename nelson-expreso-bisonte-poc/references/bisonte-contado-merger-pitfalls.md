# Bisonte — Pitfalls del contado_merger.py (jun 2026)

## Columnas del Excel IA_CONTADO

### Sheet SISTEMA (descarga Transoft)
```
nro, guiafec, razsocc, clase, fechaedit, sucori, sucdest, importe, saldo, succobro, estado, tiporec, sucursal, nrogen_a
```

### Sheet INICIAL (trabajo acumulado de Edith — SISTEMA anterior + 4 cols manuales)
```
nro, JUSTIFICACIÓN, REFERENTE, ESTADO, OBSERVACIÓN, guiafec, razsocc, clase, fechaedit,
sucori, sucdest, importe, saldo, succobro, tiporec, sucursal, nrogen_a
```

### Tipos de dato relevantes
- `guiafec`: string `'DD/MM/YYYY'` (fecha de emisión de guía)
- `fechaedit`: `datetime.datetime` con hora (última edición Transoft) — usar ESTE para DIAS_ATRASO
- `estado`: string normalizado (ED, DT, TT, RL, RT, DO, DI, OB, NR)

## DIAS_ATRASO — cálculo correcto

```python
from datetime import datetime, timezone, timedelta

def _calc_dias_atraso(fechaedit):
    if not fechaedit:
        return ""
    try:
        if isinstance(fechaedit, datetime):
            fecha = fechaedit.date()
        elif isinstance(fechaedit, date):
            fecha = fechaedit
        else:
            s = str(fechaedit).strip()
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    fecha = datetime.strptime(s[:10], fmt).date()
                    break
                except ValueError:
                    continue
            else:
                return ""
        # Zona Argentina (UTC-3) — el server corre UTC
        ar_tz = timezone(timedelta(hours=-3))
        hoy = datetime.now(ar_tz).date()
        return (hoy - fecha).days
    except Exception:
        return ""
```

## Bug histórico: extra_cols indefinido

Al sacar columnas extra del header (ESTADO_SISTEMA, ORIGEN), si queda `all_cols = FINAL_COLS + extra_cols`
sin definir `extra_cols`, el merge lanza `NameError` silencioso (HTTP 500 sin mensaje claro).
Fix: `all_cols = FINAL_COLS`.

## PITFALL — /contado/save: rows llegan como dicts, no arrays

El frontend (ContadoTable.tsx) manda las editedRows como lista de objetos JS:
```json
[{ "_row_idx": 0, "_color": "none", "nro": "A.0053.00111316", "REFERENTE": "CC", ... }]
```
NO como lista de arrays `[[val1, val2, ...]]`.

Si el backend hace `row[0]` sobre un dict → `KeyError: 0` → HTTP 500.

Fix: detectar el tipo antes de iterar:
```python
is_dict_rows = len(rows) > 0 and isinstance(rows[0], dict)
val = row.get(col_frontend) if is_dict_rows else row[columns.index(col_frontend)]
```

Campos internos que llegan en el dict pero NO van a la BD: `_row_idx`, `_color`.
El `_COL_MAP` solo mapea columnas de negocio → los campos con `_` se ignoran naturalmente.

## INVESTIGACIÓN ABIERTA — Discrepancia 57 vs 47 filas ED (jun 2026)

### Síntoma
El FINAL de Edith filtrado en Excel muestra 57 filas con estado=ED.
La app (merger INICIAL + SISTEMA) genera un FINAL con solo 47 filas ED. Faltan 10 filas.

### Datos del IA_CONTADO en el server (doc_0233633bf8f6)
- SISTEMA: 377 filas válidas, **58 con estado=ED**
- INICIAL: 369 filas válidas, **52 con estado=ED**
- FINAL (sheet del archivo): 374 filas válidas, **55 con estado=ED**

### Hipótesis a verificar
1. **El INICIAL que sube Nelson a la app ≠ el INICIAL del IA_CONTADO en el server.**
   El INICIAL real podría ser el FINAL de la sesión anterior de Edith (que tiene 57 ED),
   no el INICIAL del IA_CONTADO (52 ED). Si eso es así, la base de comparación es distinta.

2. **Deduplicación por `nro` en SISTEMA borra registros válidos.**
   El merger hace `seen_nros` y descarta duplicados — si Transoft genera dos entradas
   con el mismo `nro` para guías distintas, se pierde la segunda.

3. **`_find_header_row` detecta fila incorrecta en el INICIAL de Edith.**
   Si el archivo de Edith tiene un título en fila 1 y el header en fila 2, pero
   _find_header_row solo busca "nro" en las primeras 5 filas — verificar que no
   haya problema con el caso (mayúsculas) o espacios en el header real.

4. **El campo `estado` en el FINAL de Edith se llama `ESTADO` (mayúsculas).**
   `_sheet_to_dicts` lee los headers tal cual. El merger busca
   `r_ini.get("ESTADO") or r_ini.get("estado")` — si alguna variante falla, el
   registro existente puede no reconocerse y tratarse como eliminado.

### Para diagnosticar
Agregar prints en el merger antes de retornar stats:
```python
ed_ini = sum(1 for r in rows_ini if _normalize_estado(r.get("ESTADO") or r.get("estado")) == "ED")
ed_sis = sum(1 for r in rows_sis if _normalize_estado(r.get("estado")) == "ED")
print(f"[DEBUG] ED en INICIAL: {ed_ini}, ED en SISTEMA: {ed_sis}", flush=True)
print(f"[DEBUG] nros_ini={len(nros_ini)}, nros_sis={len(nros_sis)}, existentes={len(nros_existentes)}, nuevos={len(nros_nuevos)}", flush=True)
```
Luego `grep DEBUG /tmp/excel_backend.log` para ver los conteos reales en la próxima ejecución.

### Siguiente paso (pendiente de Nelson)
Confirmar qué archivo sube como INICIAL — si es el FINAL de la sesión anterior de Edith
o el INICIAL del IA_CONTADO. Eso determina cuál es la fuente correcta de verdad.

---

## PITFALL — backend zombie tras reinicio

Al reiniciar uvicorn para aplicar cambios de código, el proceso anterior puede quedar
corriendo (zombie). El nuevo proceso arranca, detecta el puerto ocupado, y falla — pero
el viejo sigue sirviendo el código desactualizado.

Síntoma: el fix no toma efecto aunque el archivo .py esté actualizado.

Diagnóstico y fix:
```bash
pgrep -a -f 'python.*main'    # ver todos los PIDs de uvicorn corriendo
kill <pid_viejo>              # matar explícitamente por PID
# luego levantar con background=true
```

Nunca usar `pkill -f uvicorn` directo desde terminal foreground — el agente lo interpreta
como proceso de larga duración y rechaza el comando. Usar execute_code con hermes_tools.terminal.

---

## PITFALL — tolerancia CC cambiada a 0 (confirmado Edith jun 2026)

Histórico: tolerancia CC era 4 días en el código inicial.
Corrección: Edith confirmó que CC = 0 tolerancia. "De casa central es inmediato del día anterior."

Búsqueda en código — todos los lugares donde aparece tolerancia:
```bash
grep -n "tolerancia" backend/app/services/contado_merger.py
```
Hay 3+ lugares: función `_es_rojo_por_atraso`, `table_to_excel` Regla 1, `table_to_excel` Regla 3.
Actualizar TODOS cuando cambie la regla.

---

## PITFALL CRITICO — sucdest vs succobro (detectado jun 2026)

Son dos campos distintos con nombres similares. Confundirlos hace que las reglas de
coloreo CC no funcionen — ninguna fila se pinta rojo aunque supere tolerancia.

| Campo      | Significado                        | Ejemplo  |
|------------|------------------------------------|----------|
| `sucdest`  | Sucursal de DESTINO de la guía     | CC, TUC  |
| `succobro` | Sucursal encargada del COBRO       | BA, TUC  |

Regla Edith: la tolerancia aplica según dónde SE ENTREGÓ la guía (sucdest), no dónde
se cobra. Una guía con sucdest=CC y succobro=BA tiene tolerancia 0.

En todo el código de coloreo (UI y Excel), usar SIEMPRE `sucdest`:
```python
sucdest = str(row.get("sucdest", "") or "").strip().upper()
tolerancia = 0 if sucdest == "CC" else 7
```

Al revisar colores que no pintan como se espera, primer check:
```bash
grep -n "succobro\|sucdest" backend/app/services/contado_merger.py | grep toleran
```

---

## SCRIPT — separar Excel combinado en INICIAL + SISTEMA

Cuando Edith pasa un solo archivo con dos sheets, usar `scripts/split_combinado.py`:
```bash
python3 scripts/split_combinado.py /path/IA_CONTADO_DDMM.xlsx /path/salida/
# Genera: Inicial{DD}_{MM}.xlsx  y  Sistema{DDMM}.xlsx
```

---

## Stats verificados con IA_CONTADO.xlsx real (jun 2026)
- 281 existentes con anotaciones preservadas
- 93 nuevos (sin anotaciones)
- 88 eliminados (cobrados/cerrados)
- 114 con cambio de estado (rojo)

## Formato de salida FINAL_COLS
```python
FINAL_COLS = [
    "nro", "JUSTIFICACIÓN", "REFERENTE", "ESTADO", "OBSERVACIÓN",
    "DIAS_ATRASO", "guiafec", "razsocc", "clase", "fechaedit",
    "sucori", "sucdest", "importe", "saldo", "succobro",
    "tiporec", "sucursal", "nrogen_a",
]
```
