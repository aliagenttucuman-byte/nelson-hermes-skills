# AgentScope 2.0 — Referencia de Arquitectura para Multi-Agentes

**Repo:** https://github.com/agentscope-ai/agentscope  
**Stars:** ~26k | **Forks:** ~2.8k | **License:** Apache 2.0 | **Actualizado:** junio 2026  
**Origen:** Alibaba — paper arXiv cs.MA/2402.14034

## Qué es

Framework Python para agentes de IA orientado a producción. A diferencia de LangGraph (grafos de control) o CrewAI (crews rígidas), AgentScope 2.0 **le da autonomía al modelo** para razonar y usar herramientas — diseñado para modelos cada vez más capaces que no necesitan orquestación tan estricta.

## Diferenciadores vs otros frameworks

| Aspecto | AgentScope 2.0 | LangGraph | CrewAI |
|---------|---------------|-----------|--------|
| Control de flujo | Modelo autónomo | Grafos explícitos | Roles/crews definidos |
| Multi-agentes | Message Hub flexible | Nodos conectados | Crews con roles |
| MCP nativo | ✅ | Plugins | Plugins |
| A2A protocol | ✅ | ❌ | ❌ |
| Voz en tiempo real | ✅ | ❌ | ❌ |
| Deploy como servicio | FastAPI multi-tenant | Manual | Manual |
| Fine-tuning built-in | ✅ | ❌ | ❌ |
| Observabilidad | OTel built-in | Externo | Externo |

## Patrones relevantes para el equipo Nelson

### 1. Agent Service (FastAPI multi-tenant/multi-session)
AgentScope incluye un servicio FastAPI listo para producción con multi-tenancy y multi-session. Patrón muy similar al meta-orquestador de Nelson — vale revisarlo como referencia para el loop de decisión maestro.

```bash
git clone https://github.com/agentscope-ai/agentscope
cd agentscope/examples/agent_service
python main.py
```

### 2. Message Hub para orquestación flexible
En vez de hardcodear dependencias entre agentes, los agentes se comunican via un message hub centralizado. Cada agente publica/suscribe mensajes por tipo/topic. Esto desacopla al orquestador de los workers (Julián, Mercedes, etc.).

### 3. Event stream en replies
```python
async for evt in agent.reply_stream(UserMsg("Tony", "Hi!")):
    match evt.type:
        case EventType.TEXT_BLOCK_DELTA: ...
        case EventType.MODEL_CALL_START: ...
```
Útil como referencia para el streaming SSE del chat del orquestador.

### 4. Toolkit modular
```python
toolkit=Toolkit(tools=[Bash(), Grep(), Glob(), Read(), Write(), Edit()])
```
Patrón limpio para componer herramientas por agente — similar a cómo deberían estar separadas las capacidades de Julián (backend) y Mercedes (frontend).

## Puntos a evaluar antes de adoptar

- **Acoplamiento a DashScope/Qwen:** los ejemplos del README están escritos con `DashScopeCredential` y `DashScopeChatModel`. Hay que verificar qué tan limpia es la abstracción para usar OpenAI/Azure (nuestro stack actual).
- **Python 3.11+:** requerido. Nosotros ya estamos ahí.
- **Comunidad principalmente china:** DingTalk como canal principal. Discord existe pero menos activo en español/inglés.

## Recomendación

No reemplazar el meta-orquestador existente. Usar como **referencia de arquitectura** para:
1. Patrón de Agent Service multi-tenant con FastAPI
2. Message Hub para desacoplar agentes
3. Event stream pattern para SSE del chat
4. Toolkit composition por agente especialista
