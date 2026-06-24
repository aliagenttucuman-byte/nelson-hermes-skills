# ForestAI × ReForest Latam — Estrategia Comercial (Junio 2026)

Documento completo en:
`/home/server/brainstorming/2026-06-11-forestai-reforest-latam/ESTRATEGIA-COMERCIAL-REFOREST.md`
PDF en:
`/home/server/brainstorming/2026-06-11-forestai-reforest-latam/ESTRATEGIA-COMERCIAL-REFOREST.pdf`

## Contexto del deal

- **AlegentAI** aporta: ForestAI tech stack (YOLO detección + clasificación especies NOA),
  ~1.000h sweat equity (USD 30K), TRL 5, pipeline funcional sobre GeoTIFF reales.
- **ReForest Latam** aporta: iSeeds biotecnología, flota UAV, proyecto Bolivia 1.240 ha,
  47 especies validadas, MRV funcional, red internacional (COP28, Empresa B, OEA).
- **Gap que cubre ForestAI**: su MRV actual es a nivel lote/especie agregada.
  ForestAI agrega detección árbol-por-árbol + clasificación de especie individual
  → MRV granular apto para créditos de carbono Gold Standard/VCS.

## Opción A — Sociedad

- AlegentAI entra con **25%** de ReForest Latam
- Valuación pre-money implícita: USD 171.000
- Sin capital inicial requerido de ReForest
- Vesting 36m / cliff 6m, veto técnico AlegentAI, IP = sociedad
- Revenue AlegentAI año 2 (base): USD 337.500

## Opción B — Inversión

- ReForest financia **USD 20K–57K**
- AlegentAI retiene **67–85%** de la plataforma ForestAI
- Valuación pre-money ForestAI: USD 90.000 (sweat equity × 3x)
- ROI proyectado para ReForest: 183% en año 2

## Números clave del modelo

| Modelo | Métrica | Resultado |
|--------|---------|-----------|
| yolo26n_especies_noa_v1 | mAP50 Tipa blanca | 0.902 |
| yolo26n_especies_noa_v1 | mAP50 Lapacho | ~0.8 |
| Pipeline completo | Árboles detectados (prueba Avellaneda) | ~1.100 |
| Diferencial | Único modelo NOA con datos aéreos propios | Sin equivalente comercial |

## Argumento de cierre

> "El pipeline funciona hoy sobre datos reales de Tucumán. El modelo de Tipa tiene mAP50=0.902
> entrenado con copas aéreas reales del NOA. No existe otra PoC así en Argentina.
> Treemetrics cobra USD 3.8M/año por algo similar.
> Lo que falta es el vuelo de campo en el área de ReForest para ampliar las especies
> — que es exactamente donde entra el acuerdo."

## Hitos del roadmap conjunto

| Fase | Hito | Plazo |
|------|------|-------|
| 0 | Reunión + firma acuerdo | 15 días |
| 1 | Vuelo campo ReForest para dataset | 30 días |
| 1 | Integración API ForestAI ↔ GIS ReForest | 45 días |
| 1 | Modelo v2 (6 especies: Tipa, Lapacho, Quebracho, Algarrobo, Cebil +1) | 45 días |
| 2 | MRV árbol-por-árbol exportable | 60 días |
| 3 | Primer cliente conjunto con MRV avanzado | 90 días |
