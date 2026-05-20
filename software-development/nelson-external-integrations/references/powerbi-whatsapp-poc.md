# PoC PowerBI → WhatsApp — Notas de sesión 2026-05-19

## Objetivo
Acceder a tableros de energía, extraer KPIs/datos, pasarlos por un LLM para interpretar, y mostrar el resultado como reporte gráfico por WhatsApp.

## Decisión de diseño tomada con Tony

**Spike inicial**: usar datos.gob.ar (gratis, sin credenciales) con datos reales de producción petróleo/gas de Argentina. Mismo contexto que YPF.

**Flow confirmado:**
1. Consumir CSV desde API pública datos.gob.ar
2. Filtrar y calcular KPIs reales (producción, market share YPF, variación mensual)
3. Pasar datos + contexto al LLM → interpretación lenguaje natural + análisis
4. Generar imagen/reporte visual (matplotlib o similar)
5. Enviar imagen + texto por WhatsApp

Esto es similar a un RAG sobre datos energéticos en tiempo real.

## Fuentes encontradas en el spike

### datos.gob.ar (API pública Ministerio de Energía Argentina)
- Base URL: `https://www.datos.gob.ar/api/3/action/`
- Dataset principal: `energia-produccion-petroleo-gas-sesco`
- Datasets relevantes encontrados:
  - Producción petróleo por empresa: `produccin-petrleo-sesco-tight-y-shale-captulo-iv-por-empresa.csv`
  - Producción gas por empresa: `produccin-gas-sesco-tight-y-shale-captulo-iv-por-empresa.csv`
  - Serie histórica por cuenca: `serie-produccion-petroleo-sesco.csv`
  - Producción diaria por empresa: `produccin-de-petrleo-promedio-diaria-por-empresa.csv`
  - Producción diaria por yacimiento: `produccin-de-petrleo-promedio-diaria-por-yacimiento.csv`
  - Reservas petróleo y gas: `energia-reservas-petroleo-gas`

## Path a Phase 2 (PowerBI real YPF)
- Azure AD del tenant YPF
- App Registration con permisos `Report.Read.All`, `Dataset.Read.All`
- MSAL para autenticación
- Power BI REST API v2 para exportar páginas como PNG
- Ver sección "Escenario B" en SKILL.md principal

## Notas adicionales
- Tony confirmó que el flujo de Azure AD sí se va a necesitar para producción
- Prioridad ahora: hacer funcionar el spike con datos abiertos primero
- La idea tiene componente RAG: datos estructurados + LLM = interpretación contextual
- Output esperado: imagen tipo reporte ejecutivo + párrafo de análisis
