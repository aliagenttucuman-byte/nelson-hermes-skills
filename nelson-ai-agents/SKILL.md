---
name: nelson-ai-agents
title: AI Agents - Agentes Autonomos con Herramientas y Memoria
description: Agentes de IA autonomos para el equipo Nelson. Agentes con herramientas (tools), memoria a largo plazo, planning, reflexion. ReAct pattern, function calling, multi-agent workflows.
skill: nelson-ai-agents
author: equipo-nelson
version: 1.0.0
keywords: [agents, react, tools, function-calling, memory, planning, autonomous, workflow]
dependencies: [nelson-llm-generation, nelson-rag-pipeline]
---

# AI Agents - Equipo Nelson

## Que es un agente

Un agente de IA es un sistema que:
1. Recibe un objetivo o pregunta
2. **Piensa** (planning, razonamiento)
3. **Actua** (llama herramientas, busca info, ejecuta codigo)
4. **Observa** (resultados de las acciones)
5. **Itera** hasta resolver el objetivo

## Patron ReAct (Reasoning + Acting)

```
Pregunta: Cual es el clima en Buenos Aires y deberia llevar paraguas?

Thought: Necesito saber el clima actual en Buenos Aires.
Action: get_weather(location="Buenos Aires")
Observation: {"temp": 22, "condition": "lluvia", "humidity": 85}

Thought: Esta lloviendo y la humedad es alta. Deberia llevar paraguas.
Final Answer: Si, lleva paraguas. Estan pronosticadas lluvias con 85% de humedad.
```

## Agente con herramientas

```python
# app/agents/base.py
from typing import Callable, Any
from dataclasses import dataclass
from app.core.llm import LLMService
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., Any]
    parameters: dict  # JSON schema

class Agent:
    def __init__(self, llm: LLMService = None):
        self.llm = llm or LLMService()
        self.tools: dict[str, Tool] = {}
        self.memory: list[dict] = []

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def run(self, query: str, max_iterations: int = 10) -> str:
        """Ejecutar agente con ReAct."""
        self.memory.append({"role": "user", "content": query})

        for i in range(max_iterations):
            # Construir prompt con tools disponibles
            prompt = self._build_prompt()

            # LLM decide: Thought / Action / Final Answer
            response = self.llm.generate(prompt)
            self.memory.append({"role": "assistant", "content": response})

            # Parsear respuesta
            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()

            if "Action:" in response:
                action_str = response.split("Action:")[-1].split("\n")[0].strip()
                result = self._execute_action(action_str)
                self.memory.append({"role": "user", "content": f"Observation: {result}"})
                continue

        return "No pude completar la tarea en el tiempo permitido."

    def _build_prompt(self) -> str:
        tools_desc = "\n".join(
            f"{name}: {tool.description}\nParameters: {tool.parameters}"
            for name, tool in self.tools.items()
        )

        history = "\n".join(
            f"{m['role']}: {m['content']}" for m in self.memory
        )

        return f"""Eres un agente util. Tienes acceso a estas herramientas:
{tools_desc}

Usa el formato:
Thought: [tu razonamiento]
Action: [nombre_tool(param1=val1, param2=val2)]
Observation: [resultado]
...
Final Answer: [respuesta al usuario]

Historial:
{history}

Thought:"""

    def _execute_action(self, action_str: str) -> str:
        """Parsear y ejecutar action."""
        import re
        match = re.match(r'(\w+)\((.*)\)', action_str)
        if not match:
            return "Error: formato invalido"

        tool_name, args_str = match.groups()
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: tool '{tool_name}' no existe"

        # Parsear args simple
        kwargs = {}
        if args_str:
            for pair in args_str.split(","):
                k, v = pair.split("=")
                kwargs[k.strip()] = v.strip().strip('"\'')

        try:
            result = tool.func(**kwargs)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
```

## Registro de herramientas

```python
# app/agents/tools.py
from app.agents.base import Tool
from app.services.rag import RAGService
from app.services.weather import WeatherService

def get_tools() -> list[Tool]:
    rag = RAGService()
    weather = WeatherService()

    return [
        Tool(
            name="search_documents",
            description="Buscar informacion en documentos del usuario",
            func=lambda query, user_id: rag.ask(query, filters={"user_id": user_id}),
            parameters={"query": "str", "user_id": "str"},
        ),
        Tool(
            name="get_weather",
            description="Obtener clima actual de una ciudad",
            func=lambda location: weather.get(location),
            parameters={"location": "str"},
        ),
        Tool(
            name="calculate",
            description="Evaluar expresion matematica",
            func=lambda expression: eval(expression),  # Cuidado en prod!
            parameters={"expression": "str"},
        ),
    ]
```

## FastAPI endpoint para agente

```python
# app/api/v1/agent.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.agents.base import Agent
from app.agents.tools import get_tools
from app.api.deps import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentRequest(BaseModel):
    query: str

@router.post("/run")
def run_agent(request: AgentRequest, current_user = Depends(get_current_user)):
    agent = Agent()
    for tool in get_tools():
        # Inyectar user_id en tools que lo necesitan
        if "user_id" in tool.parameters:
            original = tool.func
            tool.func = lambda **kwargs: original(user_id=str(current_user.id), **kwargs)
        agent.register_tool(tool)

    result = agent.run(request.query)
    return {"result": result, "steps": len(agent.memory)}
```

## Memoria a largo plazo

```python
# app/agents/memory.py
from app.services.vector_store import VectorStore
from app.services.embeddings import EmbeddingService

class AgentMemory:
    """Memoria semantica del agente usando vector DB."""

    def __init__(self):
        self.store = VectorStore()
        self.embedder = EmbeddingService()

    def remember(self, conversation_id: str, text: str, metadata: dict):
        """Guardar memoria."""
        embedding = self.embedder.embed_single(text)
        self.store.upsert(
            collection="agent_memory",
            vectors=[embedding],
            payloads=[{"text": text, **metadata}],
            ids=[f"{conversation_id}_{hash(text)}"],
        )

    def recall(self, query: str, conversation_id: str = None, limit: int = 5) -> list[str]:
        """Recuperar memorias relevantes."""
        embedding = self.embedder.embed_single(query)
        filters = {"conversation_id": conversation_id} if conversation_id else None
        results = self.store.search(
            collection="agent_memory",
            query_vector=embedding,
            limit=limit,
            filters=filters,
        )
        return [r["payload"]["text"] for r in results]
```

## Multi-agent workflow

```python
# app/agents/orchestrator.py
class Orchestrator:
    """Orquesta multiples agentes especializados."""

    def __init__(self):
        self.researcher = Agent()  # Busca info
        self.writer = Agent()      # Escribe respuestas
        self.critic = Agent()      # Revisa calidad

    def run(self, task: str) -> str:
        # Paso 1: Researcher investiga
        research = self.researcher.run(f"Investiga sobre: {task}")

        # Paso 2: Writer redacta
        draft = self.writer.run(f"Escribe basado en esta investigacion: {research}")

        # Paso 3: Critic revisa
        critique = self.critic.run(f"Revisa este texto y sugiere mejoras: {draft}")

        # Paso 4: Writer mejora
        final = self.writer.run(f"Mejora este texto segun estas sugerencias: {critique}\n\nTexto original: {draft}")

        return final
```

## Function Calling nativo (OpenAI)

```python
# Alternativa moderna: usar function calling nativo de OpenAI
from openai import OpenAI

class FunctionCallingAgent:
    def __init__(self):
        self.client = OpenAI()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Obtener clima",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                        },
                        "required": ["location"],
                    },
                },
            }
        ]

    def run(self, query: str):
        messages = [{"role": "user", "content": query}]

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if message.tool_calls:
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                result = self.execute_tool(function_name, arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })

            # Segunda llamada con resultados
            final = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return final.choices[0].message.content

        return message.content
```

## Verificación

- [ ] Agente tiene objetivo claro y herramientas relevantes
- [ ] Max iterations para evitar loops infinitos
- [ ] Memoria persistente entre conversaciones
- [ ] Logs de cada Thought/Action/Observation
- [ ] Timeout en ejecucion de tools
- [ ] Validar inputs de tools (no ejecutar codigo arbitrario)
- [ ] Fallback si el agente no puede resolver

## Referencias

- [Extracción de cookies de Epiphany para autenticación de agentes](references/epiphany-cookie-extraction.md) — cómo extraer sesiones de GNOME Web para Playwright y herramientas que requieren auth de Google.

## Pitfalls

- Nunca ejecutar `eval()` con input del usuario (riesgo de injection)
- Agente puede entrar en loops; siempre max_iterations
- Function calling es mas confiable que parsear texto manualmente
- Memoria crece sin limite; resumir o truncar periodicamente
- Tools lentas bloquean al agente; usar async cuando sea posible
- Costos: cada iteracion es una llamada al LLM; monitorizar tokens

## Orquestacion Multi-Agente con Frameworks Externos

Para workflows de I+D+i o equipos de agents, evaluar frameworks de orquestacion antes de construir custom. Ver referencia comparativa en `references/multi-agent-frameworks.md`.

### Decision rapida

| Si necesitas... | Usa... |
|-----------------|--------|
| Control total del flujo, estados, loops | **LangGraph** |
| Type-safety, APIs, resultados estructurados | **PydanticAI** |
| Hardware modesto (4GB VRAM), open-source total | **Custom ReAct + FastAPI** |
| Equipo de agents con roles, brainstorming | **CrewAI** (probar con locales primero) |
| RAG complejo, pipelines de documentos | **LlamaIndex Workflows** |
| Automatizaciones, notificaciones, integraciones | **n8n** (complementario) |

### Arquitectura hibrida recomendada (Equipo Nelson)

```
Layer 1: LangGraph → orquesta flujo general
Layer 2: Custom ReAct → ejecuta tareas con Ollama local
Layer 3: n8n → triggers, WhatsApp, conexiones externas
Layer 4: Ollama + Qdrant + FastAPI → infraestructura
```

**Regla:** Empezar con custom ReAct (ya operativo) y migrar a LangGraph solo cuando el flujo requiera estados complejos o ciclos.

## Scripts

- `scripts/run-multi-agent-spike.sh` — crea estructura estandar para evaluar un framework multi-agente (LangGraph, CrewAI, PydanticAI, etc.)
- `scripts/test-notebooklm-podcast.py` — spike minimo para generar podcast con NotebookLM y enviarlo por WhatsApp

## References

- `references/multi-agent-frameworks.md` — comparativa de 9 frameworks (LangGraph, CrewAI, AutoGen, Swarm, PydanticAI, LlamaIndex, Temporal, n8n, Custom)
- `references/notebooklm-evaluation.md` — evaluacion de notebooklm-py para generar podcasts/infografias/quizzes desde documentos (ideal para I+D+i)
- `scripts/run-multi-agent-spike.sh` — script para crear spike de evaluacion de framework
- `scripts/test-notebooklm-podcast.py` — script de spike para NotebookLM + WhatsApp
