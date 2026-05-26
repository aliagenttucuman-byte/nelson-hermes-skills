# JARVIS Demo Shell — Arquitectura y flujo de datos

## Flujo completo (validado 2026-05-19)

```
Usuario (browser)
     │
     │ POST /api/chat (Next.js route)
     ▼
frontend/src/app/api/chat/route.ts
     │
     ├─── GET /api/system-prompt ──► FastAPI backend (puerto 8765)
     │                                    │
     │                                    └─► tools/registry.py
     │                                         └─► tools/{ACTIVE_PROJECT}.py
     │                                              └─► get_system_instructions()
     │
     └─── OpenAI SDK (baseURL=Groq)
          POST https://api.groq.com/openai/v1/chat/completions
               │
               │ stream: true
               ▼
          response.toReadableStream()  ← formato que OpenUI parser espera
               │
               ▼
     OpenUI React runtime
          │
          ├─► texto normal → renderiza como markdown
          └─► bloque ```openui ... ``` → renderiza componente React
               ├─► chart  → Recharts
               ├─► kpi    → Card con variación
               └─► tabla  → tabla filtrable
```

## Separación de responsabilidades

| Capa | Responsabilidad | Cambia por proyecto |
|------|----------------|---------------------|
| frontend/src/app/api/chat/route.ts | Streaming + consulta system prompt | NO |
| frontend/src/app/layout.tsx | Polyfill crypto.randomUUID | NO |
| backend/routers/chat.py | Endpoint /api/system-prompt | NO |
| backend/tools/registry.py | Registro dinámico de tools | NO |
| backend/tools/{proyecto}.py | Instrucciones del agente + contexto | SÍ |
| backend/.env (ACTIVE_PROJECT) | Qué proyecto está activo | SÍ |

## Por qué el stream va directo al SDK de OpenAI y no pasa por el backend

El parser de OpenUI (`@openuidev/react-headless`) espera el formato del SDK de OpenAI:
- Objetos JavaScript del SDK, no SSE crudo
- El método `response.toReadableStream()` produce ese formato
- Si el frontend recibe bytes SSE crudos (con prefijo `data: `), el JSON.parse falla

La solución: el backend solo provee configuración (system prompt), el stream de tokens va directo SDK → frontend.

## Modelo de datos del proyecto activo

```python
class BaseTool:
    name: str                    # identificador en .env
    description: str             # humano-legible
    
    def get_system_instructions(self) -> str:
        # Retorna instrucciones para el agente:
        # - Qué sabe el agente (contexto del dominio)
        # - Qué datos tiene disponibles
        # - Qué componentes OpenUI usar y con qué sintaxis
        # - Ejemplos de bloques ```openui```
        ...
```

## Groq + OpenAI SDK — compatibilidad

Groq expone una API compatible con OpenAI. Configuración:

```typescript
const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});
```

Modelo validado: `llama-3.3-70b-versatile` — genera OpenUI Lang correctamente.

## Puertos del servidor (2026-05-19)

| Puerto | Servicio |
|--------|---------|
| 3789 | jarvis-demo-shell frontend (Next.js) |
| 8765 | jarvis-demo-shell backend (FastAPI) |
| 3456 | spike 001-openui (descartable) |
| 8000-8002 | OCUPADOS por otros servicios |
