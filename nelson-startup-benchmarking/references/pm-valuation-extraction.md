# Extracción de valuación para Resumen PM (ForestAI)

Caso validado: `PROJECT-CHARTER-v3.md` y PDF equivalente.

## Métricas extraídas

- `mvp_total_investment_usd` ← "INVERSIÓN TOTAL MVP"
- `development_cost_usd` ← "Costo de desarrollo"
- `operational_cost_4m_usd` ← "Costos operativos 4 meses"
- `monthly_avg_usd` ← "Costo mensual promedio"
- `revenue_scenarios[]` ← filas Conservador/Base/Optimista

## Regex robustas (markdown + texto PDF)

- Usar tolerancia por línea: `[^\n]{0,40}` entre etiqueta y `USD`.
- Soportar tablas markdown con pipes opcionales en escenarios.

Ejemplo escenarios:
`\|?\s*(Conservador|Base|Optimista)\s*\|?\s*(\d+) ...`

## Parsing USD recomendado

- Interpretar formato AR `73.960` como `73960` (separador miles).
- Limpiar prefijos/sufijos: `USD`, `$`, `~`, `/mes`.

## Regla de frontend

Si existe `project_valuation`, mostrar esos valores como resumen económico principal.
Si no existe, mostrar mensaje explícito (sin inferir valuación numérica).