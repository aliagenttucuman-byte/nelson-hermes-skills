# ForestAI — Estrategia Comercial (referencia sesión 2026-06-11)

Documento completo generado en: `/home/server/brainstorming/2026-06-11-forestai-estrategia-comercial/ESTRATEGIA-COMERCIAL.md`
PDF en: `/home/server/brainstorming/2026-06-11-forestai-estrategia-comercial/ESTRATEGIA-COMERCIAL.pdf`

## Ponderación del proyecto (junio 2026)

- Sweat equity acumulado: ~USD 30.000 (1.000h × USD 30/h)
- TRL: 5 (PoC validada en entorno real — ortofotos Avellaneda, Tucumán)
- Pipeline funcional: upload TIF → detección copas → clasificación especie → resultado
- Modelo fine-tuned: yolo26n_especies_noa_v1 (mAP50=0.762, Tipa blanca=0.902)
- Dato único: único modelo de especies aéreas del NOA entrenado con datos propios del área

## Opción 1 — Sociedad

| Socio | % | Aporte |
|-------|:-:|--------|
| Nelson | 50% | Tech completa, I+D, arquitectura |
| Pablo | 30% | Red comercial, dominio forestal, campo |
| Pool equipo | 20% | Julián + Mercedes + futuro |

Vesting 36m / cliff 6m / IP = sociedad.
Valuación implícita: USD 60K pre-money.
Pablo ya tiene ~USD 8.160 sweat equity → diferencia ~USD 9.840 a cubrir con trabajo futuro.

## Opción 2 — Inversión

| Capital Pablo | Equity Pablo | Nelson | Valuación pre-money |
|:-------------:|:------------:|:------:|:-------------------:|
| USD 20.000 | 15% | 65% | USD 133K |
| USD 30.000 | 20% | 60% | USD 150K |
| USD 50.000 | 25% | 55% | USD 200K |

Uso del capital: vuelo campo (USD 3-5K) + Julián 3m full-time (USD 8.6K) + GPU compute (USD 2K).

## Roadmap en 3 fases

Fase 0 (actual): PoC funcional
Fase 1 (3-4m, USD 20-30K): MVP — modelo v2 (6-8 especies), reporte PDF, 1 cliente piloto
Fase 2 (6-12m, USD 50-80K): tracción — 5-10 clientes, integración créditos carbono
Fase 3 (12-24m): escala regional — Bolivia, Paraguay, Brasil; Serie A USD 500K-1M

## Hitos críticos con owners

| Hito | Owner | Plazo |
|------|-------|-------|
| Vuelo campo monte nativo | Pablo | 30 días |
| Modelo especies v2 (6 clases) | Nelson | 45 días |
| Primer cliente piloto | Pablo | 60 días |

## Mercado objetivo

- TAM Argentina: USD 120M/año (~8M ha forestadas × USD 15/ha)
- SAM (PyME + ONG + drones): USD 18M/año
- SOM año 1-2: USD 180K–480K (3-8 clientes enterprise + 10-20 operadores)

## Argumento de cierre para Pablo

> "El pipeline funciona hoy sobre datos reales de Tucumán. El modelo de Tipa tiene mAP50=0.762
> entrenado con copas aéreas reales del NOA. No existe otra PoC así en Argentina.
> Lo que falta es el vuelo de campo para ampliar las especies y el primer cliente piloto
> — que es exactamente donde entra Pablo."
