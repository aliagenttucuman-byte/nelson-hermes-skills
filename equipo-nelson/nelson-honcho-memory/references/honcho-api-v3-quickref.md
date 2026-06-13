# Honcho API v3 — Quick Reference

Deploy verificado: 2026-06-12 en ai-server :8008

## Nomenclatura v3

| Término viejo | Término v3 |
|---|---|
| App | Workspace |
| User | Peer |
| Session | Session |
| Message | Message |
| MetaMessage / Observation | Conclusion |

## SDK Python — Inicialización

```python
from honcho import Honcho

honcho = Honcho(
    base_url="http://localhost:8008",
    workspace_id="jarvis-nelson"
)

# Peers
nelson = honcho.peer("nelson")
jarvis = honcho.peer("jarvis")

# Sesión
session = honcho.session("2026-06-12-tema")

# Guardar mensajes
from honcho import MessageCreateParams
session.add_messages([
    nelson.message("pregunta o decisión importante"),
    jarvis.message("respuesta con contexto técnico"),
])

# Recuperar contexto semántico del peer
response = nelson.chat("¿qué proyectos tenemos activos?")

# Contexto de sesión con límite de tokens
ctx = session.context(summary=True, tokens=2000)
```

## Endpoints clave

```
GET  /health                                          → {"status":"ok"}
GET  /docs                                            → Swagger UI
POST /v3/workspaces                                   → crear workspace
POST /v3/workspaces/{wid}/peers                       → crear peer
POST /v3/workspaces/{wid}/sessions                    → crear sesión
POST /v3/workspaces/{wid}/sessions/{sid}/messages     → batch de mensajes
POST /v3/workspaces/{wid}/peers/{pid}/chat            → dialectic (streaming)
GET  /v3/workspaces/{wid}/peers/{pid}/representation  → perfil del peer
POST /v3/workspaces/{wid}/peers/{pid}/search          → búsqueda semántica
```

## Arquitectura de procesos

Honcho corre DOS procesos que comparten DB + Redis:
- **API server** — HTTP, dialectic inline, enqueue tasks
- **Deriver worker** — queue consumer, extrae conclusions, genera summaries

El docker-compose levanta ambos via `docker/entrypoint.sh`.

## Variables de entorno críticas

```env
DB_CONNECTION_URI=postgresql+psycopg://postgres:honcho2026@database:5432/postgres
CACHE_URL=redis://redis:6379/0
CACHE_ENABLED=true
AUTH_USE_AUTH=false
LLM_OPENAI_API_KEY=sk-proj-ulsZ...4DcQEA
EMBEDDING_MODEL_CONFIG__TRANSPORT=openai
EMBEDDING_MODEL_CONFIG__MODEL=text-embedding-3-small
DERIVER_ENABLED=true
```

## Puertos en ai-server

| Servicio | Puerto externo |
|---|---|
| API | 0.0.0.0:8008 |
| PostgreSQL 15 + pgvector | 127.0.0.1:5434 |
| Redis | 127.0.0.1:6381 |

Todos tienen `restart: unless-stopped` — sobreviven reinicios del servidor.
