---
name: nelson-honcho
description: "Honcho memoria persistente multi-usuario para el equipo Nelson. Workspace alegent-ai con peers nelson/edith/pablo/julian/mercedes/jarvis. API :8008."
version: 1.0.0
---

# Honcho — Memoria persistente equipo Nelson

Ya instalado y corriendo en ai-server como container Docker.

## Estado actual

Container: honcho-api-1 — puerto 8008
DB: honcho-database-1 (pgvector pg15) — puerto 5434 interno
Redis: honcho-redis-1 — puerto 6381 interno

Workspace: alegent-ai
Peers: nelson, edith, pablo, julian, mercedes, jarvis

## Endpoints clave

Base URL: http://localhost:8008

GET  /health                                           -- health check
GET  /v3/workspaces/{ws}/peers                        -- listar peers
POST /v3/workspaces/{ws}/sessions                     -- crear sesión
GET  /v3/workspaces/{ws}/sessions/{id}/messages       -- listar mensajes
POST /v3/workspaces/{ws}/sessions/{id}/messages       -- insertar mensajes (batch)
GET  /v3/workspaces/{ws}/sessions/{id}/context        -- contexto resumido
POST /v3/workspaces/{ws}/sessions/{id}/chat           -- query semántico (Dialectic)

## Insertar mensajes (correcto)

Body siempre como { "messages": [...] } — MessageBatchCreate

```python
import requests

BASE = "http://localhost:8008"
WS   = "alegent-ai"

requests.post(f"{BASE}/v3/workspaces/{WS}/sessions/{session_id}/messages", json={
    "messages": [
        {"content": "texto", "peer_id": "jarvis", "metadata": {"type": "context"}},
    ]
})
```

## Crear sesión nueva

```python
session = requests.post(f"{BASE}/v3/workspaces/{WS}/sessions", json={
    "id": f"session-nelson-{fecha}",
    "metadata": {"canal": "whatsapp", "fecha": fecha}
}).json()
session_id = session["id"]
```

## Consulta semántica (Dialectic)

```python
r = requests.post(f"{BASE}/v3/workspaces/{WS}/sessions/{session_id}/chat", json={
    "query": "¿Cuál es el estado del proyecto Bisonte?",
    "peer_id": "nelson"
})
contexto = r.json()["content"]
```

## Estado actual del workspace alegent-ai

Workspace: alegent-ai (creado 2026-06-18)
Peers: nelson, edith, pablo, julian, mercedes, jarvis
Sesión inicial: session-nelson-2026-06-18 (4 mensajes de contexto del equipo)

## Complementariedad con Headroom

Honcho y Headroom se complementan — no compiten:
- Honcho resuelve QUÉ recordar (trae contexto relevante de sesiones anteriores)
- Headroom resuelve CÓMO mandarlo (comprime ese contexto antes de enviarlo al LLM)
- lean-ctx resuelve lo que JARVIS lee in-process

Flujo completo:
Honcho trae contexto → lean-ctx lo comprime al leerlo → JARVIS procesa → Headroom comprime el mensaje → Azure Anthropic responde



JARVIS (lean-ctx activo — comprime reads/shell/search in-process)
  └── Headroom proxy :8787 → Azure Anthropic (77-85% ahorro en tool outputs)
        └── Honcho :8008 (memoria semántica persistente multi-usuario)

Flujo: Honcho provee QUÉ recordar, Headroom comprime CÓMO mandarlo al LLM.

## Enchufe nativo Hermes (activado 2026-06-19)

Hermes tiene un plugin memory nativo para Honcho en `plugins/memory/honcho/`.
Se configura con `~/.hermes/honcho.json`:

```json
{
  "baseUrl": "http://localhost:8008",
  "enabled": true,
  "workspace": "alegent-ai",
  "aiPeer": "jarvis",
  "peerName": "nelson",
  "pinPeerName": true,
  "saveMessages": true,
  "writeFrequency": "async",
  "dialecticReasoningLevel": "low",
  "dialecticMaxChars": 800,
  "recallMode": "hybrid",
  "sessionStrategy": "per-directory"
}
```

PITFALL: el campo correcto es `baseUrl` (camelCase) y `workspace` (no `workspace_id`).
El config `memory.provider: holographic` en config.yaml DEBE quedarse así — honcho.json
es adicional y NO reemplaza el provider de memoria nativa.

Verificar que el plugin lee bien la config:
```bash
cd ~/.hermes/hermes-agent && python3 -c "
import sys; sys.path.insert(0, '.')
from plugins.memory.honcho.client import HonchoClientConfig, get_honcho_client
cfg = HonchoClientConfig.from_global_config()
client = get_honcho_client(cfg)
print('base_url:', client.base_url)
print('workspace_id:', cfg.workspace_id)
print('peer_name:', cfg.peer_name)
"
```

## Enchufe de arranque de sesión

`~/.hermes/scripts/honcho_context_loader.py` — recupera contexto de Honcho al inicio.

```bash
# General (últimas 48hs)
python3 ~/.hermes/scripts/honcho_context_loader.py

# Con query semántico específico
python3 ~/.hermes/scripts/honcho_context_loader.py "bisonte colores excel tolerancia"
```

El `.hermes.md` del proyecto Bisonte apunta a este script para carga automática.

Crons activos:
- 23:30 — `honcho-daily-context-save` — JARVIS guarda resumen del día
- 06:00 — `honcho-context-refresh` — regenera archivo de contexto diario

## Kanban boards del equipo (creados 2026-06-19)

Dos boards en `hermes kanban` para organizar proyectos:

```bash
hermes kanban --board alegent-ai list   # Bisonte, ForestAI, infra, demos
hermes kanban --board lan-latam list    # ML finanzas, GCP, dashboards LAN
```

Crear tarea:
```bash
hermes kanban --board alegent-ai create --triage --body "descripción" "Título tarea"
```

## Pitfalls (descubiertos en spike 2026-06-18)

- MessageCreate requiere content + peer_id como campos obligatorios — metadata es opcional
- El endpoint POST /messages acepta SOLO MessageBatchCreate — body siempre es `{"messages": [...]}`
  NO existe endpoint para mensaje individual — siempre batch aunque sea 1 solo mensaje
- GET /messages devuelve `total` pero puede mostrar 0 aunque haya items — usar `items[]` para verificar
- POST /sessions/{id}/peers falla con array — los peers van directo en la creación de sesión o por separado como objeto
- Session id es opcional en create — si no se pasa, se autogenera UUID
- Los peers deben existir en el workspace ANTES de agregarlos a una sesión
- El workspace "alegent-ai" y los peers nelson/edith/pablo/julian/mercedes/jarvis YA EXISTEN — no recrear
- Auth está deshabilitado en el container actual (AUTH_USE_AUTH=off) — no se necesita token

## Verificación rápida

```bash
curl http://localhost:8008/health

# PITFALL: GET en /workspaces y /peers devuelve "Method Not Allowed"
# Usar POST /list para listar recursos:
curl -s -X POST 'http://localhost:8008/v3/workspaces/list' \
  -H 'Content-Type: application/json' \
  -d '{"page": 1, "page_size": 10}'

curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/peers/list' \
  -H 'Content-Type: application/json' \
  -d '{"page": 1, "page_size": 20}'

curl -s -X POST 'http://localhost:8008/v3/workspaces/alegent-ai/sessions/list' \
  -H 'Content-Type: application/json' \
  -d '{"page": 1, "page_size": 10}'
```

## Trigger: "te pasé X hace unos días / antes / hace un rato"

Cuando Nelson dice frases tipo:
- "te pasé el token / el link / el archivo hace unos días"
- "te lo dije antes"
- "ya hablamos de esto"
- "hace un rato me mostraste X"

**NO preguntar de nuevo.** Es Honcho — buscar primero. Patrón:

```python
# 1. Query semántico en sesiones recientes
import requests
BASE = "http://localhost:8008"
WS = "alegent-ai"

# Listar sesiones recientes
sessions = requests.post(f"{BASE}/v3/workspaces/{WS}/sessions/list",
                         json={"page": 1, "page_size": 50}).json()["items"]

# Probar dialectic chat en la sesión más probable
for s in sessions[:7]:  # últimas ~7 sesiones
    r = requests.get(f"{BASE}/v3/workspaces/{WS}/sessions/{s['id']}/messages",
                     params={"page": 1, "page_size": 100})
    for msg in r.json().get("items", []):
        content = msg.get("content", "")
        if any(k in content.lower() for k in ["<keywords del request>"]):
            # Found it
            pass

# 2. Si no aparece en Honcho, buscar en filesystem
# Credenciales/tokens viven en /home/server/secrets/
# Configs en /home/server/.hermes/ o ~/.config/
```

**Anti-patrón explícito (corregido por Nelson 2026-06-24):**
Pedirle a Nelson "regeneralo y pasámelo de nuevo" cuando el dato ya está guardado.
Eso lo frustra porque rompe la promesa de memoria persistente del stack.

## Regla de oro: qué va en MEMORY.md vs Honcho

JARVIS tiene dos memorias persistentes con propósitos distintos. NO mezclar.

**MEMORY.md (slot chico ~2.2k chars, inyectado en CADA turno):**
Solo facts críticos de runtime que se usan literalmente cada conversación:
- Credenciales operativas (IPs Tailscale, puertos, sudo passwords, logins de n8n)
- Identidades de bots y aprobaciones (Telegram bot ID, usuarios aprobados)
- Convenciones recurrentes (formato HU "CREEMOS QUE", paths de repos activos)
- Pitfalls que matan el flujo si se olvidan (no venv en Bisonte, reiniciar spa_proxy)
- Preferencias de estilo de comunicación del usuario
- Contratos activos / datos legales en curso

**Honcho (recuperable por query semántico, sin costo en cada turno):**
TODO lo demás:
- Evaluaciones de tecnologías y tools (Hyperframes, NeMo, Unlimited-OCR, etc.)
- Decisiones de diseño históricas y rationale
- Brainstormings y spikes
- Notas de reuniones con stakeholders
- Estado de proyectos y roadmaps
- Aprendizajes técnicos no triviales
- Contexto de prospectos comerciales (sin nombres propios en MEMORY.md por default)

**Síntoma de error:** si veo "MEMORY.md está al 95%+", comprimí o moví entradas en lugar de
guardarlas en Honcho. Acción correcta: identificar qué entrada NO es runtime crítico,
guardarla en Honcho con `peer_id: jarvis` + metadata `tipo: <categoría>`, y removerla
de MEMORY.md.

**Patrón para guardar tech eval en Honcho:**
```python
sid = "session-tech-stack-eval"  # sesión persistente del workspace alegent-ai
mensajes = [{
    "peer_id": "jarvis",
    "content": "EVAL TECH: <nombre> — <descripción + URLs + casos uso AlegentAI>",
    "metadata": {"tipo": "tech-eval", "tecnologia": "<slug>", "prioridad": "alta|media|baja", "fecha": "YYYY-MM-DD"}
}]
```

Recuperar después:
```python
r = requests.post(f"{BASE}/v3/workspaces/{WS}/sessions/{sid}/chat",
                  json={"query": "qué evaluamos sobre <topic>", "peer_id": "nelson"})
```

## Estrategia de ahorro de tokens con Honcho

Honcho + Headroom son complementarios:
- Honcho decide QUÉ contexto recuperar (query semántica, solo lo relevante)
- Headroom comprime CÓMO se manda al LLM (77-85% de reducción)

Flujo óptimo:
1. Al arrancar sesión → query semántica a Honcho por tema actual → ~500 tokens de contexto preciso
2. Durante sesión → guardar eventos clave al momento (bug resuelto, regla de negocio, decisión)
3. A las 23:30 → cron guarda resumen comprimido del día (5-15 mensajes, <100 tokens c/u)

Cron configurado: job `honcho-daily-context-save` a las 23:30 UTC todos los días.
Script: `~/.hermes/scripts/honcho_daily_save.sh`

> Ver `references/honcho-api-endpoints.md` para endpoints curl verificados — GET en colecciones NO funciona, usar POST /list.

## Guardar mensajes (batch — único método válido)

```python
# CRITICO: el body SIEMPRE es {"messages": [...]} — no existe endpoint individual
import json, tempfile

mensajes = [
    {"peer_id": "jarvis", "content": "...", "metadata": {"tipo": "decision"}},
    {"peer_id": "edith", "content": "...", "metadata": {"tipo": "regla-negocio"}},
]

with open("/tmp/honcho_payload.json", "w") as f:
    json.dump({"messages": mensajes}, f)

# Usar archivo temporal para evitar problemas de escaping en curl
terminal(f"curl -s -X POST '{BASE}/v3/workspaces/{WS}/sessions/{SID}/messages' "
         f"-H 'Content-Type: application/json' -d @/tmp/honcho_payload.json")
```
