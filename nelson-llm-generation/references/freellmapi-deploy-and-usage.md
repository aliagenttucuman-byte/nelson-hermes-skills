# FreeLLMAPI — Deploy local + carga de keys + custom providers

Repo: https://github.com/tashfeenahmed/freellmapi
Stack: Node 20+ / Express + React/Vite / SQLite / Docker
License: MIT
Single-user by design (no multi-tenant).

## Cuándo usar este proxy en vez de providers directos

- Querés failover automático entre N providers sin tocar código de agente
- Tenés varias keys free-tier (Groq, OpenRouter free, Cerebras, etc.) y querés
  que se apilen
- Querés un dashboard unificado con analytics, fallback chain reordenable,
  y playground
- No es para producción comercial multi-tenant ni para SLA crítico (depende
  de ToS de free tiers)

## Deploy local (ai-server)

```bash
mkdir -p /home/server/proyectos && cd /home/server/proyectos
git clone https://github.com/tashfeenahmed/freellmapi.git
cd freellmapi

# ENCRYPTION_KEY obligatorio (AES-256-GCM para keys en reposo)
ENCRYPTION_KEY=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
printf "ENCRYPTION_KEY=%s\nPORT=3101\nHOST_BIND=0.0.0.0\nPROXY_RATE_LIMIT_RPM=240\nDASHBOARD_ORIGINS=http://100.110.8.13:3101,http://localhost:3101\n" "$ENCRYPTION_KEY" > .env

docker compose pull
docker compose up -d
```

### Pitfall crítico: PUERTO 3001

**El puerto 3001 está ocupado en ai-server por el WhatsApp Gateway de Hermes**
(`/home/server/brainstorming/2025-05-13-ai-news-aggregator/whatsapp-gateway`,
`node server.js`). Si intentás `PORT=3001` el container falla con
`address already in use`. **Usar 3101 (o cualquier otro) siempre.**

El mapping es `HOST_BIND:PORT_EXT → 3001_INT`. El container sigue
escuchando en 3001 internamente, vos cambiás el host port.

### Verificación post-deploy

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep freellmapi
# Debe decir "(healthy)"

curl -sS http://127.0.0.1:3101/api/ping
# HTTP 200, respuesta vacía
```

### URL y accesso

- Local: `http://127.0.0.1:3101`
- Tailscale (ai-server está en 100.110.8.13): `http://100.110.8.13:3101`
- HTTPS via `tailscale serve`: requiere activar "Serve" en el tailnet
  (1 click en https://login.tailscale.com/f/serve?node=...)

## Setup del admin (primera vez)

El primer boot auto-genera un `unified API key` (en logs:
`Your unified API key: freellmapi-...`). Ese es el bearer token que usan
los clientes para llamar al proxy.

**Pero el admin (dashboard) requiere user/pass separado:**

```bash
# Si la DB está fresca, /api/auth/setup crea el primer admin
curl -X POST http://127.0.0.1:3101/api/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"email":"tu@email.com","password":"minimo-8-chars"}'
# → 201 con {"token": "..."}  (token de sesión, 64 chars)

# Si la DB ya tiene un user (caso típico: ya entraste al dashboard antes):
curl -X POST http://127.0.0.1:3101/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tu@email.com","password":"..."}'
# → 200 con {"token": "..."}  o 401 si pass mal
```

**Pitfall: la DB es persistente en el volumen `freellmapi-data`.** Si
arrancás el container y ves `{"needsSetup": false}` pero no recordás la
pass, hay 2 opciones:
- A) Buscarla (LastPass, bitwarden, lo que uses)
- B) Nuclear: `docker compose down -v && docker compose up -d` (pierde
  todas las keys cargadas y analytics, pero como recién lo deployás no
  perdés nada)

**Verificar sesión:**
```bash
curl http://127.0.0.1:3101/api/auth/status
# → {"needsSetup": false, "authenticated": true|false, "email": "..."}
```

## Cargar keys de providers

**Endpoint básico** (para providers nativos: groq, cerebras, openrouter,
google, **anthropic**, etc.):
```bash
curl -X POST http://127.0.0.1:3101/api/keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "platform": "groq",
    "key": "gsk_...",
    "label": "nelson-groq"
  }'
# → 201 con {id, platform, maskedKey, enabled, ...}
```

A partir de v0.4+, el endpoint básico también acepta `baseUrl` opcional
para providers que enrutan per-endpoint (anthropic, custom):
```bash
# Azure Anthropic Foundry
curl -X POST http://127.0.0.1:3101/api/keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "platform": "anthropic",
    "key": "<azure-anthropic-key>",
    "label": "azure-claude",
    "baseUrl": "https://<resource>.services.ai.azure.com/anthropic"
  }'
```

**Endpoint custom** (alternativa, registra también el modelo en el catálogo):
```bash
curl -X POST http://127.0.0.1:3101/api/keys/custom \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "baseUrl": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "displayName": "GPT-4o mini (OpenAI directo)",
    "apiKey": "sk-proj-..."
  }'
# → 201 con {success, keyId, modelDbId, platform:"custom", ...}
```

### Pitfall: Azure Anthropic requiere `/anthropic` en el baseUrl

El provider adapter Anthropic concatena `${baseUrl}/v1/messages`. El
endpoint correcto en Azure Foundry es:
`https://<resource>.services.ai.azure.com/anthropic/v1/messages`. Por lo
tanto el `baseUrl` que se guarda en el row DEBE incluir `/anthropic`:

```bash
# ✅ Correcto
"baseUrl": "https://<resource>.services.ai.azure.com/anthropic"

# ❌ Da 404 "Resource not found" aunque un curl directo al URL completo funcione
"baseUrl": "https://<resource>.services.ai.azure.com"
```

Si ves 404 en el adapter pero `curl -X POST <url-completo>/v1/messages` con
`x-api-key` da 200, casi siempre es este path prefix faltante.

### Pitfall: NO confundirlos

`POST /api/keys` (schema Zod: `platform`, `key`, `label`, `baseUrl?`) **no
inserta el modelo en el catálogo** — solo crea la key. Para built-ins los
modelos se seedan en migraciones (`migrateModelsV*` en `db/index.ts`).
Para custom, usar `POST /api/keys/custom` que sí registra el modelo.

### Autodetección al cargar key

Al cargar key de un provider nativo, el router **autodetecta
automáticamente** los modelos que esa key habilita. Ej: cargar key de
OpenRouter → aparecen ~21 modelos free ya seeded con `keyCount: 1`. No
hay que agregarlos uno por uno.

Para custom, sí tenés que agregar cada modelo individual con su
`modelId` exacto.

## Uso desde clientes (drop-in OpenAI)

```python
from openai import OpenAI
client = OpenAI(
    base_url="http://100.110.8.13:3101/v1",
    api_key="freellmapi-0b0b..."   # unified key de los logs
)

# Router elige:
resp = client.chat.completions.create(
    model="auto",
    messages=[{"role":"user","content":"hola"}]
)

# Modelo específico:
resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",   # Groq
    messages=[...]
)
```

**Headers de routing útiles** (en la response):
- `X-Routed-Via: <platform>/<model>` — qué provider atendió
- `X-Fallback-Attempts: N` — cuántos fallbacks hubo

```bash
curl http://100.110.8.13:3101/v1/chat/completions \
  -H "Authorization: Bearer $PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"hola"}]}' \
  -D /tmp/h.txt -o /tmp/r.json
grep -i "x-routed-via" /tmp/h.txt
```

### Pitfall: `model: "auto"` y modelos reasoning

El router prioriza por intelligenceRank y fallback chain. Si el modelo
top es de tipo **reasoning** (chain-of-thought: Nemotron 3 Super,
OpenAI o-series, Qwen3-Thinking, DeepSeek-R1), consume `max_tokens` en
"razonamiento" antes de dar el answer. Con `max_tokens: 20` se queda
sin espacio y devuelve un `finish_reason: "length"` con la respuesta
truncada.

**Fix:** subir `max_tokens` a 1000+ en uso real, o evitar el modelo top
reasoning si necesitás respuestas cortas.

## Endpoints disponibles

| Endpoint | Función |
|---|---|
| `GET  /api/ping` | Health check (usado por Docker healthcheck) |
| `GET  /api/auth/status` | Estado setup + sesión |
| `POST /api/auth/setup` | Crear admin (solo si no hay users) |
| `POST /api/auth/login` | Login admin → token |
| `POST /api/auth/logout` | Cerrar sesión |
| `GET  /api/keys` | Listar keys cargadas (masked) |
| `POST /api/keys` | Cargar key de provider nativo |
| `POST /api/keys/custom` | Cargar key + modelo custom con baseUrl |
| `GET  /api/models` | Catálogo de modelos (108+ seeded) |
| `GET  /api/fallback` | Fallback chain actual |
| `POST /v1/chat/completions` | OpenAI-compatible chat |
| `POST /v1/responses` | OpenAI Responses API (Codex CLI shim) |
| `GET  /v1/models` | OpenAI-compatible model list |
| `POST /v1/embeddings` | OpenAI-compatible embeddings (family-based) |

## Capabilities clave

- **Embeddings family-based:** failover solo entre providers del mismo
  modelo (vectores de modelos distintos son incompatibles). Default
  family: `gemini-embedding-001` (3072 dim)
- **Vision routing:** auto-routing a modelos con capacidad de imagen si
  el request incluye `image_url` blocks
- **Tool calling:** round-trip entre providers; Gemini requiere
  traducción a `functionDeclarations`
- **Sticky sessions:** 30 min, evita hallucination spike por switch
  mid-conversation
- **Automatic failover:** hasta 20 intentos en cadena (429/5xx/timeout
  → cooldown + retry)
- **Per-key rate tracking:** RPM/RPD/TPM/TPD por (platform, model, key)
- **Health checks:** cada 5min, marca `healthy / rate_limited /
  invalid / error`

## Deploy actual (ai-server, este setup)

- Repo: `/home/server/proyectos/freellmapi/`
- Container: `freellmapi-freellmapi-1`
- Puerto host: 3101 (interno 3001)
- Volume: `freellmapi_freellmapi-data` → `/app/server/data`
- Admin email: `nelsongacosta@gmail.com` (creado en sesión previa)
- Unified key: ver logs del primer boot (`docker logs freellmapi-... |
  grep "unified API key"`)
- Keys cargadas:
  - id=1 platform=groq key=gsk_...Tw0p
  - id=2 platform=openrouter key=sk-o...2c8a
  - id=3 platform=custom (OpenAI) + 3 modelos (gpt-4o-mini, gpt-4o, o4-mini)
  - autodetectados: ~21 modelos free de OpenRouter + keyless (Kilo,
    OpenCode Zen, Pollinations, LLM7)

## Cooldown — cómo funciona y cómo limpiarlo

El sistema de cooldown tiene **dos capas**:

1. **RAM** (`cooldowns: Map<string, number>` en `services/ratelimit.ts`) — se limpia al reiniciar el container
2. **SQLite** (tabla `rate_limit_cooldowns`) — **persiste entre reinicios** porque el volume es persistente

Cuando un modelo da 400/429/timeout entra en cooldown en ambas capas. `isOnCooldown()` chequea RAM primero; si no está carga de DB.

**Fix para limpiar cooldown de una plataforma:**

```bash
docker exec freellmapi-freellmapi-1 node -e "
const db = require('better-sqlite3')('/app/server/data/freeapi.db');
const r = db.prepare(\"DELETE FROM rate_limit_cooldowns WHERE platform='anthropic'\").run();
console.log('Borrados:', r.changes, 'rows');
db.close();
"
docker restart freellmapi-freellmapi-1 && sleep 8
```

## Rebuild de imagen Docker (cuando se modifica código fuente)

El `dist/` está **embebido en la imagen**, no montado como volumen. `docker restart` corre el binario viejo. Para que un fix sea efectivo:

```bash
cd /home/server/proyectos/freellmapi
npm run build                        # compila TypeScript
docker compose build freellmapi      # embebe dist/ en imagen
docker rm -f freellmapi-freellmapi-1
docker run -d \
  --name freellmapi-freellmapi-1 \
  -p 3101:3101 \
  --env-file /home/server/proyectos/freellmapi/.env \
  -e NODE_ENV=production \
  --mount type=volume,source=freellmapi_freellmapi-data,target=/app/server/data \
  --restart unless-stopped \
  ghcr.io/tashfeenahmed/freellmapi:latest
sleep 10 && curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3101/api/ping
```

**Nota PORT:** El `.env` tiene `PORT=3101`. Si el proceso escucha en 3101 internamente, el mapping es `-p 3101:3101`. Si escucha en 3001 (default Dockerfile), es `-p 3101:3001`. Verificar en `docker logs` qué reporta.

## Deploy actual (ai-server)

- Repo: `/home/server/proyectos/freellmapi/`
- Container: `freellmapi-freellmapi-1`
- Puerto host: 3101
- Volume: `freellmapi_freellmapi-data` → `/app/server/data`
- Admin email: `nelsongacosta@gmail.com`
- Keys cargadas:
  - id=1 platform=groq
  - id=2 platform=openrouter (~21 modelos free autodetectados)
  - id=3 platform=custom (OpenAI) + modelos: gpt-4o-mini, gpt-4o, o4-mini
  - id=5 platform=anthropic (Azure Foundry yizlafclc001.services.ai.azure.com/anthropic)
  - Modelos Anthropic: claude-sonnet-4-6 (id=265), claude-opus-4-7 (id=386)

## Próximos pasos sugeridos (Alegent LLM Router v0.1)

Wrapper Python encima de este proxy que agregue:
- `prefer: "quality" | "speed" | "cost"` → elige el modelo top de la
  categoría
- `task: "code" | "vision" | "reasoning" | "chat"` → capability routing
- Auto-medición de p95 latencia y re-ranking del chain

Tiempo estimado: 1-2 hs. No es necesario forkear FreeLLMAPI.
