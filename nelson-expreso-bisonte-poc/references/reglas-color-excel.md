# Reglas de coloreo Excel — Contado (verificado con Edith 2026-06-19)

## Principio fundamental
NO pintar filas enteras. Solo la celda que cumple la regla de negocio.

## Reglas por celda

| Celda | Condición | Color |
|---|---|---|
| DIAS_ATRASO | > tolerancia | Rojo |
| DIAS_ATRASO | > tolerancia * 0.7 | Amarillo |
| DIAS_ATRASO | <= tolerancia y >= 0 | Verde |
| OBSERVACIÓN | valor == "VER DIF" | Rojo |
| fechaedit | DIAS_ATRASO > tolerancia | Rojo |

## Tolerancia por sucursal

Campo clave: `sucdest` (sucursal de destino de entrega) — NO usar `succobro`.

- `sucdest == "CC"` → tolerancia = **0** (cualquier guía no entregada el mismo día = rojo)
- Resto de sucursales → tolerancia = **7 días**

## PITFALL crítico — succobro vs sucdest

`succobro` es la sucursal que cobra (ej: "BA", "TUC") — NO determina la tolerancia.
`sucdest` es la sucursal donde se entrega la guía — esta sí determina la tolerancia.

Confundir estos dos campos hace que Casa Central tenga tolerancia incorrecta (4 días en vez de 0).

## PITFALL — proceso viejo corriendo tras fix

Al cambiar código en contado_merger.py y reiniciar uvicorn, verificar que el proceso anterior murió:

```bash
pgrep -a -f 'uvicorn'
# Si hay dos PIDs, matar el viejo explícitamente:
kill <PID_VIEJO>
```

Si el backend viejo sigue corriendo en el puerto 9000, el fix nunca llega a producción y los colores siguen igual.

## Columna J = DIAS_ATRASO

Edith se refiere a "columna J" al hablar de los colores. Corresponde a DIAS_ATRASO en el schema actual.
