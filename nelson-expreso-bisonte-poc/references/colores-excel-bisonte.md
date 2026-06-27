# Reglas de Color — Excel Bisonte Contado

## Bug crítico detectado sesión 19/06/2026

El campo que determina si una guía es de Casa Central es `sucdest` (destino de entrega),
NO `succobro` (sucursal de cobro). Son campos distintos con valores distintos:

- `succobro` = sucursal que cobra → valor típico: "BA", "TUC", etc.
- `sucdest`  = sucursal de destino → valor típico: "CC", "BA", etc.

El código original usaba `succobro` → todas las guías de BA pasaban con tolerancia 7,
ninguna se marcaba como CC → todo aparecía sin rojo o todo rojo dependiendo del default.

## Reglas correctas (confirmadas por Edith, operadora)

| sucdest | Tolerancia DIAS_ATRASO | Regla                          |
|---------|------------------------|--------------------------------|
| CC      | 0                      | Cualquier día de atraso = rojo |
| Resto   | 7                      | Más de 7 días = rojo           |

Columna J = DIAS_ATRASO en el informe de Transoft.

## Reglas de color por celda (NO filas enteras)

1. **DIAS_ATRASO**
   - Rojo si `dias > tolerancia`
   - Amarillo si `dias > tolerancia * 0.7`
   - Verde si `dias >= 0`

2. **OBSERVACIÓN**
   - Rojo si valor == "VER DIF"

3. **fechaedit**
   - Rojo si `DIAS_ATRASO > tolerancia`

## Dónde está la lógica en el código

```
backend/app/services/contado_merger.py

- función _es_rojo_por_atraso(dias_atraso, succobro)  ← parámetro nombrado succobro pero recibe sucdest
- table_to_excel() línea ~570 → Regla 1 DIAS_ATRASO
- table_to_excel() línea ~591 → Regla 3 fechaedit
```

IMPORTANTE: la función `_es_rojo_por_atraso` no se llama desde ningún lugar (línea 147).
La lógica de coloreo está inline en `table_to_excel`. Si se refactoriza, pasar `sucdest`.

## Pitfall proceso viejo

Al reiniciar uvicorn, verificar con `pgrep -a -f 'python.*main'` que el proceso anterior murió.
Si quedó colgado, el nuevo proceso falla con "address already in use" sin error visible en /health —
el health responde OK pero es el proceso VIEJO, sin los cambios nuevos.

```bash
# Kill seguro
pkill -f 'uvicorn' && sleep 2
# Verificar
pgrep -a -f 'python.*main'
```
