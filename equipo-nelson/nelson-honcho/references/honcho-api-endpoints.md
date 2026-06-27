# Honcho v3 API — Endpoints verificados (jun 2026)

## PITFALL CRITICO — GET no funciona en colecciones

GET en `/v3/workspaces`, `/v3/workspaces/{id}/peers`, `/v3/workspaces/{id}/sessions`
devuelve `{"detail": "Method Not Allowed"}`.

Usar POST con body `{"page": 1, "page_size": N}` en el endpoint `/list`:

```bash
# Listar workspaces
curl -s -X POST 'http://localhost:8008/v3/workspaces/list' \
  -H 'Content-Type: application/json' \
  -d '{"page": 1, "page_size": 10}'

# Listar peers de un workspace
curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/peers/list' \
  -H 'Content-Type: application/json' \
  -d '{"page": 1, "page_size": 20}'

# Listar sesiones
curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/sessions/list' \
  -H 'Content-Type: application/json' \
  -d '{"page": 1, "page_size": 10}'

# Listar mensajes de una sesión
curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/sessions/session-2026-06-19/messages/list' \
  -H 'Content-Type: application/json' \
  -d '{"page": 1, "page_size": 50}'
```

## Crear recursos (POST)

```bash
# Crear workspace
curl -s -X POST 'http://localhost:8008/v3/workspaces' \
  -H 'Content-Type: application/json' \
  -d '{"id": "mi-workspace", "metadata": {"descripcion": "..."}}'

# Crear peer
curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/peers' \
  -H 'Content-Type: application/json' \
  -d '{"id": "nuevo-peer", "metadata": {"role": "..."}}'

# Crear sesión (idempotente — no falla si ya existe)
curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/sessions' \
  -H 'Content-Type: application/json' \
  -d '{"id": "session-YYYY-MM-DD", "metadata": {"canal": "whatsapp", "fecha": "YYYY-MM-DD"}}'
```

## Guardar mensajes (batch)

```bash
# Escribir payload a archivo para evitar escaping en curl
cat > /tmp/payload.json << 'EOF'
{
  "messages": [
    {"peer_id": "jarvis", "content": "Mensaje 1", "metadata": {"tipo": "decision"}},
    {"peer_id": "edith", "content": "Mensaje 2", "metadata": {"tipo": "regla-negocio"}}
  ]
}
EOF

curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/sessions/session-2026-06-19/messages' \
  -H 'Content-Type: application/json' \
  -d @/tmp/payload.json
```

## Query semántica (Dialectic)

```bash
curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/sessions/session-2026-06-19/chat' \
  -H 'Content-Type: application/json' \
  -d '{"query": "estado de proyecto bisonte colores excel", "peer_id": "nelson"}'
```

## Workspaces activos (verificado 19/06/2026)

- `jarvis-nelson` — creado 12/06, memoria bilateral JARVIS↔Nelson
- `alegent-ai` — creado 18/06, 6 peers: nelson, edith, pablo, julian, mercedes, jarvis

## Sesiones activas

- `session-nelson-2026-06-18` — 4 mensajes (contexto inicial equipo)
- `session-2026-06-19` — 8 mensajes (trabajo del 19/06: Bisonte colores, bug sucdest, Edith reglas)
