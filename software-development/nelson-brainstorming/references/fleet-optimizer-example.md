# Ejemplo: Fleet Optimizer - Brainstorming 2026-05-13

## Contexto de la Sesión

Tony (Nelson) solicitó un SDD de base para un proyecto de logística de transportes que incluyera:
- Costos y mantenimiento de vehículos
- Cálculos financieros (VAN, TIR) por vehículo/flota
- OpenAPI spec como base para el equipo
- Diferenciador con IA conversacional

## Corrección de Workflow Aplicada

Durante la sesión, Tony corregió el hábito de guardar documentos sueltos en `~/`:

> "vayamos generando mínimo una carpeta, donde esté el archivo, porque las brainstorming van a estar a la orden del día"

**Resultado:** Se estableció la convención `~/brainstorming/YYYY-MM-DD-nombre/`

## Estructura Final de la Carpeta

```
~/brainstorming/2026-05-13-fleet-optimizer/
├── README.md              # Resumen ejecutivo
└── sdd-fleet-optimizer.md  # SDD completo (Domain Model, OpenAPI, Arquitectura)
```

## Diferenciador Identificado

Ningún competidor en LatAm (Samsara, Geotab, Wialon) ofrece:
1. Cálculo de VAN/TIR por vehículo
2. Asistente IA conversacional en español sobre rentabilidad en tiempo real

## Stack Decidido

- Backend: FastAPI + PostgreSQL + TimescaleDB
- Frontend: React 19 + Vite 6 + TypeScript 5.7
- IA: Ollama local + Qdrant (RAG)
- GPS: Google Maps API
- Mensajería: WhatsApp Business API

## Modelo de Negocio SaaS

| Plan | Vehículos | Precio ARS/mes |
|------|-----------|----------------|
| Starter | Hasta 5 | $50.000 |
| Professional | Hasta 20 | $120.000 |
| Enterprise | Ilimitado | $300.000 |

## Roadmap (17 semanas)

1. MVP (CRUD + costos básicos) — 4 semanas
2. Finanzas avanzadas (VAN/TIR) — 3 semanas
3. GPS y tracking — 3 semanas
4. IA y asistente — 3 semanas
5. Mantenimiento y alertas — 2 semanas
6. Multi-cliente y API — 2 semanas

## Lecciones para Futuros Brainstormings

- El usuario prefiere que el SDD incluya fórmulas matemáticas (VAN, TIR) en Python
- OpenAPI 3.1 con endpoints de finanzas (/financial/van, /financial/tir) fue bien recibido
- Incluir tabla comparativa vs competidores agrega valor rápido
