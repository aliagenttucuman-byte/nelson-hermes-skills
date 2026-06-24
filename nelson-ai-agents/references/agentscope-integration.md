# AgentScope 2.0 — Integración con el Equipo Nelson

## Qué es AgentScope

Framework multi-agente de Alibaba (Apache 2.0, 26k stars). Foco: dejar que el modelo razone y use herramientas con más autonomía, sin forzar grafos rígidos como LangGraph o crews estructuradas como CrewAI.

**Stack:** Python 3.11+, FastAPI service multi-tenancy, message hub, MCP nativo, A2A built-in, voz en tiempo real.

## Características clave que adoptamos

### 1. Event Stream granular

Cada paso del loop ReAct emite un evento tipado:
- `THINKING_START/THINKING_DELTA/THINKING_END`
- `TOOL_CALL_START/TOOL_CALL_END`
- `TOOL_RESULT_START/TOOL_RESULT_END`
- `REQUIRE_CONFIRMATION` (human-in-the-loop)
- `EXCEED_MAX_ITERS`

**Por qué importa:** el dashboard del meta-orchestrator ya tiene timeline persistente en SQLite. Conectar el event stream permite visibilidad en tiempo real por paso, no solo por subtarea completa.

### 2. PermissionEngine

Reglas por tool: `AUTO` (ejecutar sin confirmar), `CONFIRM` (pausar y esperar OK del usuario), `DENY` (rechazar siempre).

Default rules:
- CONFIRM: `delete_file`, `drop_table`, `run_migration`, `deploy_production`, `send_email`
- AUTO: `read_file`, `search_qdrant`, `generate_text`

**Por qué importa:** operaciones destructivas en el meta-orchestrator deben pedir confirmación antes de ejecutar, especialmente en producción.

### 3. Message Hub para multi-agente

Los agentes se comunican via un hub central (pub/sub) en lugar de acoplarse directamente. Esto permite:
- Agregar/quitar agentes sin cambiar el código de los demás
- Observar todas las comunicaciones para debugging
- Broadcast de eventos a todos los agentes suscritos

**Patrón:** similar a nuestro WebSocket manager en `main.py`, pero a nivel de agente.

### 4. MCP nativo + A2A

- **MCP (Model Context Protocol):** integrado nativamente. No necesita wrapper adicional.
- **A2A (Agent-to-Agent protocol):** protocolo estándar para que agentes de diferentes frameworks se comuniquen.

**Por qué importa:** nuestro meta-orchestrator ya usa FastAPI + WebSocket. Integrar MCP nativo reduce complejidad de conexión con herramientas externas.

## Diferencias con nuestro stack

| Aspecto | AgentScope | Equipo Nelson (actual) |
|---------|-----------|----------------------|
| Orquestación | Message hub + reasoning autónomo | DAG + batches + routing declarativo |
| Modelo default | Qwen (DashScope) | OpenAI / Azure / Claude |
| Deploy | FastAPI multi-tenancy | FastAPI single-tenant |
| Tracing | OTel nativo | Timeline SQLite (manual) |
| Voz | Integrada en tiempo real | No implementado |
| Comunidad | Principalmente china (DingTalk) | Discord propio |

## Cómo usar como referencia (no reemplazo)

**No reemplazamos nuestro meta-orchestrator.** Lo usamos como referencia de arquitectura para mejoras concretas:

1. **Event Stream →** conectar con `_log_event()` del orquestador para visibilidad por paso
2. **PermissionEngine →** agregar reglas de confirmación antes de tool calls destructivos
3. **OTel Tracing →** implementar spans por task/batch (ya agregado a skill)
4. **Message Hub →** evaluar si nuestro WebSocket manager puede evolucionar a pub/sub de agentes

## Instalación para evaluación

```bash
pip install agentscope
```

**Atención:** los ejemplos del README están muy acoplados a DashScope (Qwen). Hay que verificar qué tan limpia es la abstracción para usar OpenAI/Azure como tenemos nosotros.

## Paper de referencia

arXiv: cs.MA/2402.14034
