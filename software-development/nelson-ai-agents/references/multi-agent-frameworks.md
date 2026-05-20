# Frameworks de Orquestación Multi-Agente (2025)

Referencia comparativa para evaluar frameworks de orquestación de múltiples agentes en el contexto del equipo Nelson (hardware modesto, Ollama local, open-source preferido).

---

## Recomendados

### LangGraph (LangChain)
- **Modelo:** Graph-based state machine (nodes, edges, conditional edges)
- **Local/Ollama:** ✅ Sí
- **Control de flujo:** ⭐⭐⭐⭐⭐
- **Ideal para:** Workflows complejos, iteraciones, RAG avanzado, procesos con estados
- **Notas:** Muy maduro, bien documentado. Requiere curva de aprendizaje media-alta. Es la opción principal para orquestar flujos I+D+i.

### PydanticAI (Pydantic team)
- **Modelo:** Type-safe agent framework con async nativo
- **Local/Ollama:** ✅ Sí
- **Control de flujo:** ⭐⭐⭐☆☆
- **Ideal para:** Devs Python, APIs type-safe, resultados estructurados
- **Notas:** Nuevo (2024+) pero sólido. Ergonomía excelente. Alternativa liviana a LangGraph.

### Custom ReAct + FastAPI + Skills (Equipo Nelson)
- **Modelo:** Patrón ReAct implementado a medida con herramientas del equipo
- **Local/Ollama:** ✅ Sí, funciona en 4GB VRAM
- **Control de flujo:** ⭐⭐⭐⭐⭐ (control total)
- **Ideal para:** Hardware modesto, open-source total, integración con skills existentes
- **Notas:** Base recomendada. Empezar aquí y evaluar LangGraph después.

---

## A Evaluar

### CrewAI
- **Modelo:** Role-based collaborative agents (crew = equipo)
- **Local/Ollama:** ⚠️ Probar con modelos locales primero
- **Curva:** Baja. Sintaxis muy limpia.
- **Notas:** Optimizado para LLMs costosos (GPT-4). Rendimiento con llama3.2:3b no garantizado.

### LlamaIndex Workflows
- **Modelo:** Event-driven workflows
- **Local/Ollama:** ✅ Sí
- **Ideal para:** RAG complejo, pipelines de documentos
- **Notas:** Acoplado a LlamaIndex. Evaluar si el foco es RAG, no orquestación general.

---

## No Recomendados (por ahora)

| Framework | Razón |
|-----------|--------|
| AutoGen (Microsoft) | Overkill, complejo de debuggear, overhead conversacional |
| OpenAI Swarm | Demasiado básico, diseñado para OpenAI API, experimental |
| Temporal | No es específico de IA, infraestructura pesada, overkill |

---

## Matriz Rápida

| Framework | Local | Control | Peso | Recomendación |
|-----------|-------|---------|------|---------------|
| LangGraph | ✅ | Alto | Medio | 🔹 Principal |
| PydanticAI | ✅ | Medio | Liviano | 🔹 Alternativa |
| Custom | ✅ | Alto | Ultra liviano | 🔹 Base |
| CrewAI | ⚠️ | Medio | Medio | 🔸 Evaluar |
| LlamaIndex | ✅ | Medio | Medio | 🔸 Si RAG |
| AutoGen | ✅ | Alto | Pesado | ❌ No |
| Swarm | ❌ | Bajo | Liviano | ❌ No |
| Temporal | N/A | Alto | Pesado | ❌ No |
| n8n | N/A | Bajo | Medio | ✓ Complemento |

---

## Arquitectura Híbrida Propuesta (Equipo Nelson)

```
Layer 1: Orquestador Principal
└── LangGraph → controla flujo general del experimento I+D+i

Layer 2: Agents Individuales
└── Custom ReAct (FastAPI + Skills) → ejecuta tareas con Ollama local

Layer 3: Integraciones
└── n8n → triggers, notificaciones WhatsApp, conexiones externas

Layer 4: Infraestructura
    ├── Ollama (LLMs locales)
    ├── Qdrant (vector DB)
    └── FastAPI (APIs)
```

**Ventaja:** Todo corre en GTX 1650 4GB VRAM + 13GB RAM.

---

*Referencia generada 2025-05-13. Evaluár periodicamente nuevos frameworks.*
