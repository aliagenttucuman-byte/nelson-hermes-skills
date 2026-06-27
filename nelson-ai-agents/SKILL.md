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

## Patron Event Stream (AgentScope 2.0)

AgentScope introduce un stream de eventos granulares por paso del agente. Permite observar en tiempo real cada fase del loop ReAct: thinking, tool call, tool result, texto delta. Ideal para UI en tiempo real en el dashboard.

```python
# Patrón de consumo del event stream — adaptable a nuestro FastAPI
from enum import Enum
from typing import AsyncGenerator
from dataclasses import dataclass

class EventType(str, Enum):
    REPLY_START          = "reply_start"
    REPLY_END            = "reply_end"
    THINKING_START       = "thinking_start"
    THINKING_DELTA       = "thinking_delta"
    THINKING_END         = "thinking_end"
    TEXT_DELTA           = "text_delta"
    TOOL_CALL_START      = "tool_call_start"
    TOOL_CALL_END        = "tool_call_end"
    TOOL_RESULT_START    = "tool_result_start"
    TOOL_RESULT_END      = "tool_result_end"
    REQUIRE_CONFIRMATION = "require_confirmation"   # Human-in-the-loop
    EXCEED_MAX_ITERS     = "exceed_max_iters"

@dataclass
class AgentEvent:
    type: EventType
    data: dict

# En nuestro executor.py — emitir eventos por SSE al frontend
async def run_agent_stream(task: str) -> AsyncGenerator[AgentEvent, None]:
    yield AgentEvent(type=EventType.REPLY_START, data={"task": task})

    async for step in agent.react_loop(task):
        if step.is_thinking:
            yield AgentEvent(type=EventType.THINKING_DELTA, data={"text": step.text})
        elif step.is_tool_call:
            yield AgentEvent(type=EventType.TOOL_CALL_START, data={"tool": step.tool_name, "args": step.args})
            result = await execute_tool(step.tool_name, step.args)
            yield AgentEvent(type=EventType.TOOL_RESULT_END, data={"result": result})
        elif step.is_text:
            yield AgentEvent(type=EventType.TEXT_DELTA, data={"text": step.text})

    yield AgentEvent(type=EventType.REPLY_END, data={})
```

**Por qué importa para nosotros:** el dashboard ya tiene timeline persistente (SQLite). Conectar el stream de eventos al `_log_event()` del orquestador le da visibilidad en tiempo real por paso, no solo por subtarea completa.

## Patron Permission Engine (Human-in-the-loop)

AgentScope tiene un `PermissionEngine` que pausa la ejecución del agente antes de acciones potencialmente peligrosas y espera confirmación humana. Implementar este patrón en nuestro meta-orquestador para operaciones destructivas.

```python
# app/agents/permissions.py
from enum import Enum
from typing import Callable, Any
from dataclasses import dataclass

class PermissionMode(str, Enum):
    AUTO    = "auto"      # ejecutar sin confirmación
    CONFIRM = "confirm"   # pedir confirmación al usuario
    DENY    = "deny"      # denegar siempre

@dataclass
class PermissionRule:
    tool_name: str
    mode: PermissionMode
    reason: str = ""

class PermissionEngine:
    """Decide si una tool call requiere confirmación humana."""

    DEFAULT_RULES: list[PermissionRule] = [
        # Operaciones destructivas → siempre confirmar
        PermissionRule("delete_file",       PermissionMode.CONFIRM, "operación destructiva"),
        PermissionRule("drop_table",        PermissionMode.CONFIRM, "operación destructiva"),
        PermissionRule("run_migration",     PermissionMode.CONFIRM, "modifica schema de DB"),
        PermissionRule("deploy_production", PermissionMode.CONFIRM, "deploy a producción"),
        PermissionRule("send_email",        PermissionMode.CONFIRM, "comunicación externa"),
        # Lectura y generación → automático
        PermissionRule("read_file",         PermissionMode.AUTO),
        PermissionRule("search_qdrant",     PermissionMode.AUTO),
        PermissionRule("generate_text",     PermissionMode.AUTO),
    ]

    def __init__(self, rules: list[PermissionRule] = None):
        self.rules = {r.tool_name: r for r in (rules or self.DEFAULT_RULES)}

    def check(self, tool_name: str) -> PermissionMode:
        rule = self.rules.get(tool_name)
        if rule:
            return rule.mode
        return PermissionMode.CONFIRM  # default: confirmar si no hay regla

    def requires_confirmation(self, tool_name: str) -> bool:
        return self.check(tool_name) == PermissionMode.CONFIRM


# En el executor — verificar antes de cada tool call
class ToolExecutor:
    def __init__(self, permission_engine: PermissionEngine, notify_fn: Callable):
        self.permissions = permission_engine
        self.notify = notify_fn  # envía evento REQUIRE_CONFIRMATION al frontend

    async def execute(self, tool_name: str, args: dict, task_id: str) -> Any:
        if self.permissions.requires_confirmation(tool_name):
            # Pausar y esperar OK del usuario via WebSocket/SSE
            confirmed = await self.notify({
                "event": "require_confirmation",
                "task_id": task_id,
                "tool": tool_name,
                "args": args,
            })
            if not confirmed:
                raise PermissionDeniedError(f"Usuario denegó ejecución de {tool_name}")

        return await self._run_tool(tool_name, args)
```

**Cuándo usar CONFIRM vs AUTO:**
- CONFIRM: cualquier operación con efecto secundario externo (deploy, email, DB write, delete)
- AUTO: operaciones de lectura, búsqueda, generación de texto local

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

## Herramientas de data collection para agentes

**BigSet** (`references/bigset-radar.md`) — convierte frases en lenguaje natural en datasets CSV/XLSX usando sub-agentes paralelos con búsqueda web. CLI diseñado para ser invocado por agentes autónomos. Stack TS/Node, requiere TinyFish + OpenRouter keys.

## Referencias

- [Extracción de cookies de Epiphany para autenticación de agentes](references/epiphany-cookie-extraction.md) — cómo extraer sesiones de GNOME Web para Playwright y herramientas que requieren auth de Google.
- [Identidad Multi-Plataforma](references/user-identity-multiplatform.md) — arquitectura completa para reconocer al mismo usuario desde WhatsApp, Telegram y Teams usando un canonical_id unificado + Holographic Memory. Incluye pitfall crítico de Teams (`aadObjectId` vs `from.id`), flujos de aprobación, IdentityResolver Python, y deploy de SIE como potenciador.

## Pitfalls

- Nunca ejecutar `eval()` con input del usuario (riesgo de injection)
- Agente puede entrar en loops; siempre max_iterations
- Function calling es mas confiable que parsear texto manualmente
- Memoria crece sin limite; resumir o truncar periodicamente
- Tools lentas bloquean al agente; usar async cuando sea posible
- Costos: cada iteracion es una llamada al LLM; monitorizar tokens
- **Identidad multi-plataforma:** En Teams, NUNCA usar `from.id` (inestable). Siempre `from.aadObjectId` (UUID de Azure AD, inmutable). Ver `references/user-identity-multiplatform.md`.
- **Identidad multi-plataforma:** Sin un Identity Map explícito, el mismo usuario visto desde WhatsApp/Telegram/Teams genera 3 perfiles distintos en Holographic — la memoria no se comparte.

## Orquestacion Multi-Agente con Frameworks Externos

Para workflows de I+D+i o equipos de agents, evaluar frameworks de orquestacion antes de construir custom. Ver referencias:
- `references/multi-agent-frameworks.md` — comparativa de 9 frameworks
- `references/agentscope-integration.md` — integración de AgentScope 2.0 con nuestro stack

### Decision rapida

| Si necesitas... | Usa... |
|-----------------|--------|
| Control total del flujo, estados, loops | **LangGraph** |
| Type-safety, APIs, resultados estructurados | **PydanticAI** |
| Hardware modesto (4GB VRAM), open-source total | **Custom ReAct + FastAPI** |
| Equipo de agents con roles, brainstorming | **CrewAI** (probar con locales primero) |
| RAG complejo, pipelines de documentos | **LlamaIndex Workflows** |
| Automatizaciones, notificaciones, integraciones | **n8n** (complementario) |
| Multi-agente con message hub + MCP + A2A + voz | **AgentScope 2.0** (Alibaba, 26k stars, Apache 2.0) |

### Arquitectura hibrida recomendada (Equipo Nelson)

```
Layer 1: LangGraph → orquesta flujo general
Layer 2: Custom ReAct → ejecuta tareas con Ollama local
Layer 3: n8n → triggers, WhatsApp, conexiones externas
Layer 4: Ollama + Qdrant + FastAPI → infraestructura
```

**Regla:** Empezar con custom ReAct (ya operativo) y migrar a LangGraph solo cuando el flujo requiera estados complejos o ciclos.

## Honcho — Memoria Semántica para JARVIS

Honcho es la capa de memoria semántica de JARVIS. Servicio permanente en ai-server :8008 (Docker). Almacena conversaciones importantes, construye perfil adaptativo de Nelson, recupera contexto por búsqueda semántica usando `text-embedding-3-small`.

**Stack:** honcho-api-1 (:8008) + pgvector/pg15 (127.0.0.1:5434) + redis (127.0.0.1:6381)

**Health check:** `curl http://localhost:8008/health` → `{"status":"ok"}`  
**Acceso Tailscale:** http://100.110.8.13:8008

### Nomenclatura API v3

| Concepto | API v3 |
|---|---|
| App | Workspace |
| User/Agent | Peer |
| Conversación | Session |
| Mensaje | Message |
| Inferencia sobre usuario | Conclusion |

**Workspace JARVIS:** `jarvis-nelson`, Peers: `nelson` + `jarvis`

### Uso rápido

```python
from honcho import Honcho
honcho = Honcho(base_url="http://localhost:8008", workspace_id="jarvis-nelson")
nelson = honcho.peer("nelson")
jarvis = honcho.peer("jarvis")
session = honcho.session("2026-06-12-bisonte-deploy")
# Guardar mensajes importantes
session.add_messages([nelson.message("levantame expreso bisonte"), jarvis.message("backend :9000 ok")])
# Recuperar contexto semántico
context = nelson.chat("qué proyectos estamos trabajando?")
```

Scripts operativos: `~/.hermes/scripts/honcho_store.py` y `~/.hermes/scripts/honcho_context.py`.

### Pitfalls Honcho

- **OpenAI key truncada en docker-compose**: El shell redacta API keys con `***`. El container arranca con `len=13` en vez de 164 → error 401. Fix: usar script Python para leer la key como bytes y reescribir el docker-compose sin pasar por el shell. Luego `docker compose stop api && docker compose rm -f api && docker compose up -d api`.
- **`docker compose restart` NO recarga variables de entorno** — recrear el container con `stop + rm -f + up -d`.
- **Puertos custom**: postgres en 5434 (no 5432 — forestai usa 5433), redis en 6381 (no 6379).
- **`restart: unless-stopped`** en todos los containers — sobreviven reinicios del servidor.
- **Qué guardar**: decisiones de arquitectura, preferencias de Nelson, estado de proyectos activos, correcciones, specs aprobadas. NO guardar saludos, comandos de levantamiento, logs, passwords.

Ver `references/honcho-ops.md` para scripts completos de inyección de key y endpoints API v3.

## Scripts

- `scripts/run-multi-agent-spike.sh` — crea estructura estandar para evaluar un framework multi-agente (LangGraph, CrewAI, PydanticAI, etc.)
- `scripts/test-notebooklm-podcast.py` — spike minimo para generar podcast con NotebookLM y enviarlo por WhatsApp

## References

- `references/multi-agent-frameworks.md` — comparativa de 9 frameworks (LangGraph, CrewAI, AutoGen, Swarm, PydanticAI, LlamaIndex, Temporal, n8n, Custom)
- `references/notebooklm-evaluation.md` — evaluacion de notebooklm-py para generar podcasts/infografias/quizzes desde documentos (ideal para I+D+i)
- `scripts/run-multi-agent-spike.sh` — script para crear spike de evaluacion de framework
- `scripts/test-notebooklm-podcast.py` — script de spike para NotebookLM + WhatsApp
- `references/honcho-ops.md` — Honcho memoria semántica JARVIS: deploy, SDK Python, scripts de store/context, pitfalls de key injection, docker-compose template, API v3 nomenclatura
