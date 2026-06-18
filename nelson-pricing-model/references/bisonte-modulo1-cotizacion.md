# Bisonte Módulo 1 — Cotización real entregada (jun 2026)

Cliente: Expreso Bisonte (Pablo, COO)
Fecha entrega: 2026-06-18
Tipo: PoC → Módulo 1 productivo

## Desglose de horas

| Componente | Actividades | Horas | Rate | Subtotal |
|---|---|---|---|---|
| Relevamiento + análisis | Sesiones con Edith, 13 casos de uso, reglas de negocio | 40h | $30/h | $1.200 |
| Base de datos PostgreSQL | 11 tablas, catálogos, vista auditoría, migraciones | 40h | $30/h | $1.200 |
| Backend FastAPI | 13 endpoints, merge, UPSERT, WebSocket, 5364 líneas | 80h | $30/h | $2.400 |
| Frontend React | Tabla editable 18 cols, upload, WS, download, 2026 líneas | 60h | $30/h | $1.800 |
| Infra + deploy | Tailscale, spa_proxy, Cloudflare, PostgreSQL :5435 | 20h | $30/h | $600 |
| **TOTAL** | | **240h** | $30/h | **$7.200** |

## Suscripción mensual

| Concepto | Costo/mes |
|---|---|
| Servidor (ai-server hosting) | $150 |
| PostgreSQL (backup, monitoreo) | $50 |
| Soporte + mantenimiento | $100 |
| **TOTAL** | **$300/mes** |

## Proyección

- Inversión primeros 6 meses: $9.000
- 10 módulos adicionales estimados: $21.600–$27.600
- Costo decreciente por módulo (infraestructura ya amortizada)

## DB real al momento de entrega

- 376 guías activas
- Saldo pendiente: $80.638.011,97
- 11 tablas PostgreSQL en :5435
- Estados: ED, DT, TT, RL, RT, DO, DI, OB, NR

## Lección de pricing

El módulo tipo "pipeline Excel + DB + frontend editable" cuesta ~$7.200 one-time.
Módulos 2+ sobre la misma infra cuestan $1.200–$3.600 (solo reglas de negocio + UI delta).
Suscripción mínima viable: $300/mes para cliente PyME en servidor compartido.
