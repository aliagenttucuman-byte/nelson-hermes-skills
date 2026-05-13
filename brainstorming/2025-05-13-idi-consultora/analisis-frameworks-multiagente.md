# Análisis Comparativo: Frameworks de Orquestación Multi-Agente

**Fecha:** 2025-05-13
**Autor:** JARVIS / Equipo Nelson
**Estado:** Borrador para revisión
**Contexto:** Área de I+D+i de la consultora

---

## Resumen Ejecutivo

Nelson (Tony Stark) pregunta qué framework de orquestación multi-agente podemos adoptar además de LangGraph. Este documento compara las opciones actuales (2025) considerando el contexto específico del equipo:

- **Recursos limitados:** GTX 1650 4GB VRAM, 13GB RAM, Ollama local
- **Preferencia open-source:** Evitar dependencias pagas si hay alternativas
- **Stack actual:** Python/FastAPI, React, Docker, n8n
- **Metodología:** Spec-driven development, pasito a pasio
- **Equipo:** 3 agentes I+D+i (Backend, Frontend, QA) + JARVIS

---

## 1. Opciones Evaluadas

### 1.1 LangGraph (LangChain)

| Atributo | Valor |
|----------|-------|
| **Autor** | LangChain / LangGraph team |
| **Modelo** | Graph-based state machine |
| **Madurez** | ⭐⭐⭐⭐⭐ Muy maduro |
| **Curva aprendizaje** | Media-Alta |
| **Open-source** | ✅ Sí (MIT) |

**Pros:**
- Control total del flujo (nodes, edges, conditional edges)
- Persistencia de estado integrada
- Soporta ciclos, loops, human-in-the-loop
- Integración nativa con LangChain
- Muy documentado, comunidad grande

**Contras:**
- Verboso para casos simples
- Curva de aprendizaje notable
- Overhead si solo necesitas orquestación simple

**Ideal para:** Workflows complejos, agentes que necesitan iterar mucho, RAG avanzado, procesos con estados.

**Nuestro veredicto:** ✅ **Recomendado** para el área I+D+i. Ya usamos LangChain en otros skills.

---

### 1.2 CrewAI

| Atributo | Valor |
|----------|-------|
| **Autor** | João Moura |
| **Modelo** | Role-based collaborative agents |
| **Madurez** | ⭐⭐⭐⭐☆ Maduro |
| **Curva aprendizaje** | Baja |
| **Open-source** | ✅ Sí (MIT) |

**Pros:**
- Sintaxis muy limpia y declarativa
- Roles definidos (researcher, writer, etc.)
- Interacción agente-a-agente automática
- Popular y bien documentado

**Contras:**
- Menos control del flujo exacto
- Optimizado para LLMs costosos (GPT-4) — rendimiento con modelos locales no garantizado
- Menos flexible que LangGraph para lógica compleja

**Ideal para:** Equipos de agentes con roles claros, brainstorming automático, tareas colaborativas tipo "crew".

**Nuestro veredicto:** ⚠️ **Evaluar** con modelos locales primero. Muy buena ergonomía pero puede no funcionar bien con llama3.2:3b.

---

### 1.3 AutoGen (Microsoft)

| Atributo | Valor |
|----------|-------|
| **Autor** | Microsoft Research |
| **Modelo** | Conversational agents |
| **Madurez** | ⭐⭐⭐⭐☆ Maduro |
| **Curva aprendizaje** | Alta |
| **Open-source** | ✅ Sí (MIT) |

**Pros:**
- Agents conversan entre sí (group chat)
- Human-in-the-loop nativo
- Code execution integrado (pueden ejecutar código)
- Muy flexible y poderoso

**Contras:**
- Complejo de debuggear
- Overhead conversacional (mucho "ruido" entre agents)
- Documentación densa
- Puede ser overkill para nuestro caso

**Ideal para:** Coding agents, debugging automático, equipos de agents que discuten soluciones.

**Nuestro veredicto:** ❌ **No recomendado** para empezar. Muy pesado, overkill. Reevaluar en el futuro.

---

### 1.4 OpenAI Swarm

| Atributo | Valor |
|----------|-------|
| **Autor** | OpenAI |
| **Modelo** | Lightweight orchestration |
| **Madurez** | ⭐⭐☆☆☆ Experimental |
| **Curva aprendizaje** | Baja |
| **Open-source** | ✅ Sí (MIT) |

**Pros:**
- Ultra liviano
- Handoffs entre agents muy simples
- Fácil de entender
- Código oficial OpenAI

**Contras:**
- Muy básico (intencionalmente)
- Diseñado para OpenAI API
- No es para producción compleja
- Poco maduro

**Ideal para:** Prototipos rápidos, demos, handoffs simples tipo "triaje".

**Nuestro veredicto:** ❌ **No recomendado**. Demasiado básico y acoplado a OpenAI.

---

### 1.5 PydanticAI

| Atributo | Valor |
|----------|-------|
| **Autor** | Pydantic team (Samuel Colvin) |
| **Modelo** | Type-safe agent framework |
| **Madurez** | ⭐⭐⭐☆☆ Nuevo pero sólido |
| **Curva aprendizaje** | Media |
| **Open-source** | ✅ Sí (MIT) |

**Pros:**
- Type-safe nativo (integra Pydantic)
- Resultados estructurados garantizados
- Ergonomía Python excelente
- Soporta múltiples LLMs (incluyendo locales vía ollama)
- Async nativo

**Contras:**
- Nuevo (2024+) — ecosistema en crecimiento
- Orientado a devs Python
- Menos "visibilidad" que LangGraph

**Ideal para:** Devs Python, APIs type-safe, agents que devuelven estructuras complejas.

**Nuestro veredicto:** ✅ **Recomendado** como alternativa liviana a LangGraph. Excelente para nuestro stack Python.

---

### 1.6 LlamaIndex Workflows

| Atributo | Valor |
|----------|-------|
| **Autor** | LlamaIndex team |
| **Modelo** | Event-driven workflows |
| **Madurez** | ⭐⭐⭐☆☆ En crecimiento |
| **Curva aprendizaje** | Media |
| **Open-source** | ✅ Sí (MIT) |

**Pros:**
- Integración RAG nativa
- Event-driven (async por diseño)
- Bueno para pipelines de datos

**Contras:**
- Acoplado a LlamaIndex
- Menos generalista que LangGraph
- Curva de aprendizaje si no usás LlamaIndex

**Ideal para:** RAG complejo, pipelines de documentos, agents sobre data privada.

**Nuestro veredicto:** ⚠️ **Evaluar** si el foco es RAG. Para I+D+i general, mejor LangGraph.

---

### 1.7 Temporal

| Atributo | Valor |
|----------|-------|
| **Autor** | Temporal Technologies |
| **Modelo** | Durable execution |
| **Madurez** | ⭐⭐⭐⭐⭐ Enterprise |
| **Curva aprendizaje** | Alta |
| **Open-source** | ✅ Sí (MIT) |

**Pros:**
- Tolerante a fallos (durable)
- Escalable horizontalmente
- Enterprise-grade
- Soporta long-running workflows

**Contras:**
- No es específico de IA/agentes
- Infraestructura pesada (necesita servidor Temporal)
- Overkill para nuestro escenario actual

**Ideal para:** Workflows críticos, enterprise, procesos que duran horas/días.

**Nuestro veredicto:** ❌ **No recomendado** por ahora. Demasiado pesado.

---

### 1.8 n8n + AI Nodes

| Atributo | Valor |
|----------|-------|
| **Autor** | n8n |
| **Modelo** | Visual workflow + AI nodes |
| **Madurez** | ⭐⭐⭐⭐☆ Maduro |
| **Curva aprendizaje** | Baja |
| **Open-source** | ✅ Fair-code |

**Pros:**
- Ya lo tenemos instalado
- Visual / Low-code
- Muchas integraciones nativas
- Fácil para no-devs

**Contras:**
- Limitado para agents complejos
- No es un framework de agents propiamente dicho
- Vendor lock

**Ideal para:** Automatizaciones, integraciones entre servicios, workflows simples.

**Nuestro veredicto:** ✅ **Complementario**. Seguir usando para integraciones, pero no como orquestador principal de agents I+D+i.

---

### 1.9 Custom / Equipo Nelson (ReAct + FastAPI + Skills)

| Atributo | Valor |
|----------|-------|
| **Autor** | Nosotros |
| **Modelo** | ReAct pattern + FastAPI + Skills |
| **Madurez** | ⭐⭐☆☆☆ En construcción |
| **Curva aprendizaje** | Baja (lo hacemos a medida) |
| **Open-source** | ✅ 100% nuestro |

**Pros:**
- Control total sobre el código
- Ultra ligero (funciona con 4GB VRAM)
- Open-source total
- Spec-driven development nativo
- Integración perfecta con nuestras skills

**Contras:**
- Lo construimos nosotros (más tiempo inicial)
- Menos comunidad
- Responsabilidad de mantenimiento

**Ideal para:** Nuestro contexto específico, recursos limitados, control total.

**Nuestro veredicto:** ✅ **Base recomendada**. Empezar con nuestro custom y evaluar integración con LangGraph después.

---

## 2. Matriz Comparativa

| Framework | Control Flujo | Local/Ollama | Curva | Peso | Open Source | Recomendación |
|-----------|-------------|--------------|-------|------|-------------|---------------|
| **LangGraph** | ⭐⭐⭐⭐⭐ | ✅ Sí | Media | Medio | ✅ | 🔹 **Principal** |
| **CrewAI** | ⭐⭐☆☆☆ | ⚠️ Probar | Baja | Medio | ✅ | 🔸 Evaluar |
| **AutoGen** | ⭐⭐⭐⭐☆ | ✅ Sí | Alta | Pesado | ✅ | ❌ No ahora |
| **Swarm** | ⭐⭐☆☆☆ | ❌ OpenAI | Baja | Liviano | ✅ | ❌ No |
| **PydanticAI** | ⭐⭐⭐☆☆ | ✅ Sí | Media | Liviano | ✅ | 🔹 **Alternativa** |
| **LlamaIndex** | ⭐⭐⭐☆☆ | ✅ Sí | Media | Medio | ✅ | 🔸 Si RAG |
| **Temporal** | ⭐⭐⭐⭐⭐ | N/A | Alta | Pesado | ✅ | ❌ No ahora |
| **n8n** | ⭐☆☆☆☆ | N/A | Baja | Medio | ✅ | 🔸 Complemento |
| **Custom** | ⭐⭐⭐⭐⭐ | ✅ Sí | Baja | Ultra liviano | ✅ | 🔹 **Base** |

---

## 3. Propuesta de Arquitectura Híbrida

Dado el contexto del equipo, propongo una **arquitectura híbrida**:

```
Layer 1: Orquestador Principal
├── LangGraph (para workflows complejos y estado persistente)
│   → Controla el flujo general del experimento I+D+i
│   → Define: Backend Agent → QA Agent → Decisión
│
Layer 2: Agents Individuales
├── Custom ReAct (FastAPI + Skills)
│   → Cada agente ejecuta sus tareas con herramientas propias
│   → Integra Ollama local para inferencia
│
Layer 3: Integraciones
├── n8n (para triggers, notificaciones, conexiones externas)
│   → WhatsApp alerts, RSS, calendar, etc.
│
Layer 4: Infraestructura
    ├── Ollama (LLMs locales)
    ├── Qdrant (vector DB)
    └── FastAPI (APIs)
```

**Ventajas de esta híbrida:**
1. **LangGraph** maneja la orquestación de alto nivel (qué agente hace qué, y cuándo)
2. **Custom ReAct** ejecuta las tareas con nuestras skills y Ollama local
3. **n8n** conecta todo con el mundo exterior (WhatsApp, RSS, etc.)
4. Todo corre en hardware modesto (GTX 1650 + 13GB RAM)

---

## 4. Roadmap de Adopción

| Fase | Duración | Acción |
|------|----------|--------|
| **1. Base** | 1-2 días | Custom ReAct ya operativo (skill `nelson-ai-agents`) |
| **2. Evaluación** | 1 día | Probar CrewAI y PydanticAI con llama3.2:3b local |
| **3. LangGraph** | 2-3 días | Implementar orquestación de experimentos con LangGraph |
| **4. Integración** | 1 día | Conectar LangGraph + Custom Agents + n8n |
| **5. Producción** | Continuo | Spike registry, métricas, iteración |

---

## 5. Próximos Pasos

1. **Aprobar** este análisis (Nelson + Pablo)
2. **Probar** CrewAI con un spike real (1 experimento simple)
3. **Probar** PydanticAI con un spike real
4. **Decidir** si adoptamos LangGraph como orquestador principal o seguimos con custom
5. **Documentar** la decisión como skill del equipo

---

*Documento generado por JARVIS — Equipo Nelson*
