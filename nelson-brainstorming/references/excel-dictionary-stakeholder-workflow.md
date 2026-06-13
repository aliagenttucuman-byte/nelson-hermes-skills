# Excel operativo → diccionario de datos para stakeholders

Caso de uso: Nelson necesita mostrarle a Pablo una base formal de campos (sistema vs trabajada), con trazabilidad y definiciones.

## Flujo recomendado

1) Tomar archivo real de operación (no demo)
- Confirmar tamaño, hojas y volumen.
- Identificar si hay fila de título tipo `Informe: ...` antes del header real.

2) Ingeniería inversa mínima por par de hojas
- `CDO SISTEMA` vs `CDO TRABAJADA`
- `PTE DE FACT SISTEMA` vs `PF TRABAJADA`

Para cada par:
- campos compartidos
- solo en sistema
- solo en trabajada
- diferencias de volumen (filas)

3) Diccionario v1
Por cada hoja, producir tabla:
- Campo
- Tipo inferido
- % no nulo
- Ejemplo real

4) Definiciones funcionales v1
Agregar definición de negocio para campos críticos:
- `nro`
- `REFERENTE`
- `JUSTIFICACIÓN`
- `OBSERVACIÓN` / `OBS CTAS CTES`
- `estado` / `guiaest`
- `dias_sin_c`
- `importe` / `saldo`

5) Empaquetado para reunión
En carpeta fechada de brainstorming guardar:
- `README.md`
- `diccionario-datos-v1-*.md`
- `resumen-ejecutivo-*.md`
- `ingenieria-inversa-campos-*.md`

Luego: commit + push a `main` en `~/brainstorming`.

## Reglas de calidad

- No usar muestras demo para definiciones finales.
- Declarar explícitamente cuando una hoja trabajada NO es transformación 1:1 de la hoja sistema.
- Los conteos deben usar filas útiles reales (sin título/cabecera vacía).
- Dejar próximo paso claro: aprobación de owners y reglas por campo.