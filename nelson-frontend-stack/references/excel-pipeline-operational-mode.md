# Excel Pipeline — Operational UI Mode (sin demo / sin IA)

## Cuándo usar este modo

Usar cuando el usuario ya validó el concepto y pide operar con archivos reales de negocio (cobranzas/facturación), priorizando velocidad y claridad.

## Patrón de pantalla recomendado

- Header corto con objetivo operativo.
- Zona de carga de archivo.
- Un botón principal de ejecución estática.
- Bloque de resultado con:
  - etapas,
  - conteos de filas útiles,
  - descarga de salida.

Evitar en esta vista:
- wizard de ideación,
- selección de modelo LLM,
- prompts libres,
- experimentos demo.

## Regla de conteo que evita discusiones

Para reportes Excel con formato de sistema:
- excluir fila de título (`Informe: ...`),
- excluir cabecera,
- contar solo filas útiles no vacías.

Mostrarlo explícito en UI como "filas útiles".

## Nomenclatura recomendada (cobranzas/pf)

Inputs:
- `CDO Sistema`
- `PTE de Fact Sistema`

Outputs:
- `CDO Trabajada`
- `PF Trabajada`

## Checklist de release

1. La pantalla no muestra textos de demo ni IA.
2. Hay un único CTA principal de ejecución.
3. El conteo visible coincide con filas útiles del archivo real.
4. El output descargable mantiene nombres de hoja esperados por operación.
