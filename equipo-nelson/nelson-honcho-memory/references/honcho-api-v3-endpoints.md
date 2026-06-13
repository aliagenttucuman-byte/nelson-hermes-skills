# Honcho API v3 — Endpoints de referencia

Base URL: `http://localhost:8008` (ai-server) o `http://100.110.8.13:8008` (Tailscale)
Auth: deshabilitada en deploy de ai-server (`AUTH_USE_AUTH=false`)

## Health

```
GET /health  → {"status": "ok"}
GET /metrics → Prometheus metrics
```

## Workspaces

```
POST   /v3/workspaces                         → crear workspace
POST   /v3/workspaces/list                    → listar workspaces
PUT    /v3/workspaces/{wid}                   → actualizar
DELETE /v3/workspaces/{wid}                   → eliminar
POST   /v3/workspaces/{wid}/search            → búsqueda semántica global
GET    /v3/workspaces/{wid}/queue/status      → estado de la cola de procesamiento
POST   /v3/workspaces/{wid}/schedule_dream    → forzar ciclo de razonamiento Dialectic
```

## Peers (antes "Users")

```
POST   /v3/workspaces/{wid}/peers             → crear peer
POST   /v3/workspaces/{wid}/peers/list        → listar peers
PUT    /v3/workspaces/{wid}/peers/{pid}       → actualizar peer
POST   /v3/workspaces/{wid}/peers/{pid}/sessions     → sesiones del peer
POST   /v3/workspaces/{wid}/peers/{pid}/chat         → chat con Dialectic (streaming)
POST   /v3/workspaces/{wid}/peers/{pid}/representation → representación/memoria actual
GET    /v3/workspaces/{wid}/peers/{pid}/card          → peer card (perfil)
PUT    /v3/workspaces/{wid}/peers/{pid}/card          → actualizar peer card
GET    /v3/workspaces/{wid}/peers/{pid}/context       → contexto completo del peer
POST   /v3/workspaces/{wid}/peers/{pid}/search        → búsqueda semántica sobre el peer
```

### Chat con Dialectic — teoría de la mente

```python
# Alice pregunta SOBRE Bob (teoría de la mente):
response = alice.chat("¿Qué sabe alice de bob?", target=bob)

# Nelson pregunta sobre sí mismo:
perfil = nelson.chat(
    "Describí mi estilo de trabajo, preferencias técnicas y patrones de decisión",
    target=nelson
)
```

## Sessions

```
POST   /v3/workspaces/{wid}/sessions                          → crear sesión
POST   /v3/workspaces/{wid}/sessions/list                     → listar sesiones
PUT    /v3/workspaces/{wid}/sessions/{sid}                    → actualizar
DELETE /v3/workspaces/{wid}/sessions/{sid}                    → eliminar
POST   /v3/workspaces/{wid}/sessions/{sid}/clone              → clonar sesión
POST   /v3/workspaces/{wid}/sessions/{sid}/peers              → agregar peers
PUT    /v3/workspaces/{wid}/sessions/{sid}/peers              → actualizar peers
DELETE /v3/workspaces/{wid}/sessions/{sid}/peers              → quitar peers
GET    /v3/workspaces/{wid}/sessions/{sid}/peers              → listar peers de sesión
GET    /v3/workspaces/{wid}/sessions/{sid}/peers/{pid}/config → config del peer en sesión
PUT    /v3/workspaces/{wid}/sessions/{sid}/peers/{pid}/config → actualizar config
GET    /v3/workspaces/{wid}/sessions/{sid}/context            → contexto (con límite de tokens)
GET    /v3/workspaces/{wid}/sessions/{sid}/summaries          → resúmenes generados
POST   /v3/workspaces/{wid}/sessions/{sid}/search             → búsqueda semántica en sesión
```

## Messages

```
POST   /v3/workspaces/{wid}/sessions/{sid}/messages           → crear batch (hasta 100 mensajes)
POST   /v3/workspaces/{wid}/sessions/{sid}/messages/upload    → subir archivo como mensaje
POST   /v3/workspaces/{wid}/sessions/{sid}/messages/list      → listar mensajes (paginado)
GET    /v3/workspaces/{wid}/sessions/{sid}/messages/{mid}     → obtener mensaje
PUT    /v3/workspaces/{wid}/sessions/{sid}/messages/{mid}     → actualizar mensaje
```

## Conclusions (antes "MetaMessages/Observations")

Las Conclusions son inferencias que el Deriver extrae automáticamente de los mensajes.
También se pueden crear manualmente.

```
POST   /v3/workspaces/{wid}/conclusions                       → crear conclusión manual
POST   /v3/workspaces/{wid}/conclusions/list                  → listar conclusiones
POST   /v3/workspaces/{wid}/conclusions/query                 → búsqueda semántica
DELETE /v3/workspaces/{wid}/conclusions/{cid}                 → eliminar
```

## Keys (JWT scoped)

```
POST /v3/keys  → crear JWT con scope específico (útil si se habilita auth)
```

## Webhooks

```
POST/GET/DELETE /v3/workspaces/{wid}/webhooks/...
```

## Curl de referencia rápida

```bash
# Health
curl http://localhost:8008/health

# Crear workspace
curl -X POST http://localhost:8008/v3/workspaces \
  -H "Content-Type: application/json" \
  -d '{"name": "jarvis-nelson"}'

# Crear peer
curl -X POST http://localhost:8008/v3/workspaces/jarvis-nelson/peers \
  -H "Content-Type: application/json" \
  -d '{"id": "nelson"}'

# Crear sesión
curl -X POST http://localhost:8008/v3/workspaces/jarvis-nelson/sessions \
  -H "Content-Type: application/json" \
  -d '{"id": "2026-06-12-bisonte"}'

# Agregar mensajes
curl -X POST http://localhost:8008/v3/workspaces/jarvis-nelson/sessions/2026-06-12-bisonte/messages \
  -H "Content-Type: application/json" \
  -d '[
    {"peer_id": "nelson", "content": "necesito levantar bisonte con los sheets cargados"},
    {"peer_id": "jarvis", "content": "listo, todo levantado, URL: http://100.110.8.13:9090"}
  ]'

# Perfil de Nelson via Dialectic
curl -X POST http://localhost:8008/v3/workspaces/jarvis-nelson/peers/nelson/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Describí el estilo de trabajo y preferencias técnicas de Nelson"}'
```
