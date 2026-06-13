# Criterios de Evaluación de SDKs / Agentes Externos

> Sesion: jun 2026 — evaluacion de CopilotKit para stack Nelson

## Regla de oro del stack Nelson

```
Backend Python (FastAPI)  ←→  Frontend React (Vite)
         ↑                           ↑
         └──────  Meta-Orchestrator  ──────┘
              (centraliza routing, memoria, estados)
```

**Cualquier herramienta que introduzca una capa intermedia propietaria entre FastAPI y React viola esta regla.**

## Checklist de evaluación

| Criterio | ¿Qué verificar? | Red flag |
|----------|----------------|----------|
| **Arquitectura** | ¿Introduce un runtime/proxy/graphql propio entre backend y frontend? | Sí → descartar para stack existente |
| **Backend** | ¿Requiere reemplazar FastAPI por su servidor? | Sí → descartar |
| **Frontend** | ¿Requiere reemplazar React/Vite por su framework? | Sí → descartar |
| **Protocolo** | ¿Usa protocolo propio cerrado o estándar abierto? | Cerrado → riesgo de vendor lock-in |
| **Self-hosted** | ¿Funciona 100% on-premise sin cloud obligatorio? | Cloud-only → descartar para datos sensibles |
| **Stack** | ¿Python backend + React frontend nativos? | TypeScript-only runtime → fricción |
| **Orquestador** | ¿Se integra con el meta-orchestrator o lo reemplaza? | Reemplaza → conflicto |

## Caso de estudio: CopilotKit (jun 2026)

**Qué es:** SDK de 32K ⭐ para "agent-native apps" con chat UI, Generative UI, Human-in-the-loop.

**Arquitectura:**
- Frontend: React hooks (`useAgent`) + componentes chat
- Backend: Runtime GraphQL (self-hosted o su cloud)
- Agente: LangGraph/LangChain/CrewAI vía Python SDK

**Veredicto:** No integrar en proyectos Nelson existentes.

**Por qué:**
1. **Runtime GraphQL propio** entre FastAPI y React → capa extra no necesaria
2. **Backend Python** sí existe, pero conecta a SU runtime, no a nuestro orchestrator
3. **No centraliza** en el meta-orchestrator → fragmenta routing y memoria
4. **Overkill** para pipelines ETL (Expreso Bisonte) o para apps que ya tienen chat JARVIS

**Cuándo SÍ usarlo:** Si algún día hacemos un producto nuevo tipo "app con copilot integrado" desde cero, donde el chat sea la UI principal y no tengamos orchestrator propio.

## Template de respuesta para Nelson

```
"Miré [NOMBRE]. Es [descripción corta].

Veredicto: [SÍ integrar / NO integrar / Spike opcional]

Por qué: [1-2 frases con el criterio que aplica]

Alternativa Nelson: [qué tenemos que ya cubre eso]

Si querés lo pruebo en un spike de 30 min."
```
