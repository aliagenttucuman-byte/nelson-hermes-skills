---
name: nelson-poc-ai-quickstart
title: PoC con IA - Quickstart (reglas Nelson + FreeLLMAPI + Azure Claude)
description: Quickstart accionable para arrancar una PoC que use IA/LLM. Cubre la regla de routing de Nelson (JARVIS=Anthropic, PoCs=cascada), cómo usar el FreeLLMAPI proxy en ai-server:3101, patrones de cliente (OpenAI SDK), y los pitfalls ya conocidos. Es la primera skill que cargar cuando Tony dice "voy a hacer una PoC con IA".
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [poc, llm, ai, freellmapi, anthropic, azure, claude, openai, groq, openrouter, quickstart, sdd]
    related_skills: [nelson-spec-driven-workflow, nelson-llm-generation, nelson-project-bootstrap, nelson-ai-agents]
---

# PoC con IA — Quickstart Nelson

Reglas y patrones para arrancar una PoC que use IA/LLM. **Primera skill a cargar** cuando Tony dice "voy a hacer una PoC con IA" o "necesito implementar IA".

> **Origen:** consolidado el 2026-06-06 después del deploy de FreeLLMAPI en ai-server con provider Anthropic nativo (Azure Foundry) agregado. Reglas validadas con smoke tests reales.

## Regla de routing LLM Nelson (fija, 2026-06-06)

| Caso | Provider / Modelo | Por qué |
|---|---|---|
| **JARVIS / uso personal / Tony** | **`claude-sonnet-4-6`** (Anthropic Azure Foundry) | Mejor calidad disponible, single deploy verificado |
| **PoC (regla de oro: no usar Claude directo)** | Cascada ver abajo | Optimiza costo + latencia, no satura el deploy Claude |
| **Producción crítica / decisiones** | `claude-sonnet-4-6` (vía FreeLLMAPI) | Solo si la PoC lo amerita; solicitar upgrade de rule |

### Cascada de fallback para PoCs (orden estricto)

El router FreeLLMAPI intenta en este orden hasta que uno responde:

1. **OpenAI directo** (custom provider en el router)
   - `gpt-4o-mini` — default, rápido + capable + barato
   - `gpt-4o` — más capaz
   - `o4-mini` — reasoning
2. **Groq** (`groq` platform)
   - `llama-3.3-70b-versatile` — velocidad brutal (<1s)
3. **OpenRouter free** (autodetectados al cargar key, 21 modelos)
   - `qwen/qwen3-coder:free` (código)
   - `meta-llama/llama-3.3-70b-instruct:free`
   - `nvidia/nemotron-3-super-120b-a12b:free`
   - `openai/gpt-oss-120b:free`
   - `z-ai/glm-4.5-air:free`
   - etc.
4. **Keyless trial** (Kilo Gateway, Pollinations, LLM7)
   - Útiles para bulk / experimentación
   - Sin SLA, los prompts pueden usarse para training

❌ **OpenCode Zen NO** — la key `sk-EASBo2t...5bEtHu` da Cloudflare error 1010 (bloqueada a nivel de edge). Descartada.

## Stack desplegado (no armar nada nuevo)

### FreeLLMAPI Proxy (ai-server :3101)

- **Endpoint:** `http://100.110.8.13:3101` (Tailscale) o `http://127.0.0.1:3101` (local)
- **OpenAI-compat base:** `http://100.110.8.13:3101/v1`
- **Unified API key** (en `docker logs freellmapi-freellmapi-1 | grep "unified API key"`):
  ```
  freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d
  ```
- **Admin dashboard:** `http://100.110.8.13:3101` (login admin separado del unified key)
- **Pitfall crítico: puerto 3001** está ocupado en ai-server por el WhatsApp Gateway de Hermes. FreeLLMAPI corre en 3101.

### Anthropic nativo vía Azure Foundry

Para llamadas **directas** (no vía proxy), usar la key `AZURE_ANTHROPIC_API_KEY` del `.env` y el endpoint:

```
https://yizlafclc001.services.ai.azure.com/anthropic
```

Headers requeridos: `x-api-key` + `anthropic-version: 2023-06-01`. Ver `references/azure-anthropic-foundry.md` para detalles (modelos, quirks, script cliente).

## Patrón de cliente Python (drop-in OpenAI)

**SIEMPRE** usar el OpenAI SDK apuntando al proxy. **Nunca** llamar directo a un provider en código de PoC.

```python
from openai import OpenAI

# Setup una vez
PROXY_URL = "http://100.110.8.13:3101/v1"
PROXY_KEY = "freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d"
client = OpenAI(base_url=PROXY_URL, api_key=PROXY_KEY)

# === CASO 1: Chat general (router elige el mejor disponible) ===
resp = client.chat.completions.create(
    model="auto",   # router elige según chain + health + capabilities
    messages=[{"role": "user", "content": "Decime un chiste corto"}],
    max_tokens=200,
)
print(resp.choices[0].message.content)
print("Routed via:", resp._routed_via)   # ej: {platform:"groq", model:"llama-3.3-70b-versatile"}

# === CASO 2: Código / agente (gpt-4o-mini es el default) ===
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Escribí una función Python que..."}],
    max_tokens=2000,
)

# === CASO 3: Razonamiento profundo (Claude vía proxy) ===
resp = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Analizá críticamente esta propuesta..."}],
    max_tokens=4000,
)

# === CASO 4: Vision (auto-routing filtra a modelos con capacidad) ===
resp = client.chat.completions.create(
    model="auto",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Qué hay en esta imagen?"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        ],
    }],
)

# === CASO 5: Embeddings (family-based, no mezcla modelos) ===
resp = client.embeddings.create(
    model="auto",   # default family: gemini-embedding-001 (3072 dim)
    input=["texto 1", "texto 2"],
)
vectors = [d.embedding for d in resp.data]

# === CASO 6: Tool calling round-trip ===
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    },
}]
first = client.chat.completions.create(
    model="claude-sonnet-4-6",   # Claude maneja tool calling muy bien
    messages=[{"role": "user", "content": "Clima en Tucumán?"}],
    tools=tools,
)
if first.choices[0].message.tool_calls:
    call = first.choices[0].message.tool_calls[0]
    # ejecutar tool
    tool_result = '{"temp_c": 28, "cond": "sunny"}'
    final = client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[
            {"role": "user", "content": "Clima en Tucumán?"},
            first.choices[0].message,
            {"role": "tool", "tool_call_id": call.id, "content": tool_result},
        ],
        tools=tools,
    )
    print(final.choices[0].message.content)
```

## Patrón de cliente Node.js / TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://100.110.8.13:3101/v1",
  apiKey: "freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d",
});

const resp = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "..." }],
  max_tokens: 2000,
});
```

## Patrón con SDK Anthropic nativo (solo si necesitás features no-OpenAI)

Si la PoC requiere features que el adapter Anthropic de FreeLLMAPI no expone (ej. prompt caching, computer use, vision nativa con PDF), ir **directo** a Azure Foundry, no por el proxy:

```python
import os
import requests

resp = requests.post(
    "https://yizlafclc001.services.ai.azure.com/anthropic/v1/messages",
    headers={
        "x-api-key": os.environ["AZURE_ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    },
    json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "..."}],
    },
    timeout=120,
)
resp.raise_for_status()
print(resp.json()["content"][0]["text"])
```

Ver `references/azure-anthropic-foundry.md` (skill `nelson-llm-generation`) para el script cliente completo y quirks.

## Headers de routing útiles (debugging)

En la response del proxy:

| Header | Significado |
|---|---|
| `X-Routed-Via: <platform>/<model>` | Qué provider atendió (ej: `groq/llama-3.3-70b-versatile`) |
| `X-Fallback-Attempts: N` | Cuántos providers se intentaron antes de éxito |

```bash
curl http://100.110.8.13:3101/v1/chat/completions \
  -H "Authorization: Bearer $PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"ping"}]}' \
  -D /tmp/h.txt -o /tmp/r.json
grep -i "x-routed-via" /tmp/h.txt
```

## Decisión tree: ¿qué modelo usar para qué tarea?

```
¿Necesitás razonamiento crítico / decisiones / calidad máxima?
  └─ Sí → claude-sonnet-4-6 (vía proxy o directo Azure)
  └─ No ↓

¿Necesitás código que funcione a la primera?
  └─ Sí → gpt-4o-mini o gpt-4o
  └─ No ↓

¿Necesitás velocidad extrema o bulk processing?
  └─ Sí → llama-3.3-70b-versatile (Groq) o cualquier openrouter:free
  └─ No ↓

¿Querés que el router decida?
  └─ Sí → model="auto" (recomendado para explorar)
  └─ No ↓

¿Razonamiento profundo (chain-of-thought)?
  └─ Sí → o4-mini o claude-sonnet-4-6 con extended thinking
  └─ No → gpt-4o-mini
```

## Reglas de oro (anti-desvíos)

1. **SIEMPRE** vía FreeLLMAPI proxy. Nunca llames directo a un provider en código de PoC.
2. **JARVIS = Anthropic** (claude-sonnet-4-6, baseUrl Azure Foundry). Es la regla fija.
3. **PoC = cascada** (OpenAI → Groq → OpenRouter free → keyless). No uses Claude para una PoC trivial.
4. **`model="auto"`** es tu amigo para explorar. Optimizar después.
5. **NO hardcodear keys.** Vienen del `.env` (`AZURE_ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.) o del router.
6. **NO optimices latencia/costo en la primera versión.** Después del PoC exitoso, mirá el dashboard del proxy.
7. **NO armes una abstracción LLM nueva.** El proxy ya es la abstracción.
8. **NO reinventes failover.** El router ya tiene hasta 20 intentos con cooldown.
9. **NO armes self-hosted LLM (vLLM, Ollama) para producción.** El proxy ya rutea a NVIDIA NIM que es self-hosted del upstream.
10. **NO uses OpenCode Zen.** Key bloqueada por Cloudflare 1010.

## Pitfalls conocidos (al 2026-06-06)

| Pitfall | Fix |
|---|---|
| `model: "auto"` cae en Nemotron/Qwen-Thinking (reasoning) → consume `max_tokens` en chain-of-thought | Subir `max_tokens` a 1000+ o evitar reasoning models para one-word answers |
| `claude-opus-4-7` (Azure) rechaza `temperature` con HTTP 400 | Omitir el campo para ese modelo. `claude-sonnet-4-6` sí lo acepta |
| Endpoint Azure Anthropic requiere `/anthropic` en el path | `baseUrl = https://<resource>.services.ai.azure.com/anthropic` (no `...azure.com` solo) |
| `POST /api/keys` no inserta el modelo en el catálogo (built-ins) | Para built-ins seedear en `db/index.ts` migrate. Para custom usar `POST /api/keys/custom` |
| FreeLLMAPI admin password olvidado | `docker compose down -v && docker compose up -d` (nuclear) o recuperarla del password manager |
| Container FreeLLMAPI da 404 "Resource not found" pero curl directo al URL completo da 200 | Path prefix mal armado. Comparar las dos URLs carácter por carácter. El adapter concatena `${baseUrl}/v1/messages` |
| Provider sin `Authorization: Bearer` (ej. Anthropic `x-api-key`) | El adapter AnthropicProvider ya lo maneja. Si usás SDK directo, ver `references/azure-anthropic-foundry.md` |
| Keys con formato inesperado (gsk_ es Groq, sk-or-v1- es OpenRouter) | El dashboard las detecta por el prefijo. Si tenés dudas, sanity check con curl al endpoint del provider antes de cargar al proxy |

## Quickstart para una PoC nueva (5 pasos)

1. **Verificar acceso al proxy:**
   ```bash
   curl -sS http://100.110.8.13:3101/api/ping
   # HTTP 200 = OK
   ```

2. **Crear carpeta del proyecto** (convención Nelson):
   ```bash
   mkdir -p ~/brainstorming/YYYY-MM-DD-nombre-poc/
   # README.md obligatorio
   ```

3. **Escribir README.md con la hipótesis** (formato Nelson):
   ```markdown
   # [Nombre PoC]
   
   ## Hipótesis
   CREEMOS QUE al [construir X], RESULTARÁ en [output concreto].
   
   ## Stack
   - Backend: Python (FastAPI por default)
   - Frontend: React (Vite por default)
   - LLM: FreeLLMAPI proxy (auto / gpt-4o-mini / claude-sonnet-4-6)
   
   ## Criterios de éxito
   - [ ] 3-5 criterios verificables
   ```

4. **Implementar** siguiendo el flujo I+D+I de `nelson-spec-driven-workflow` (3 fases: Spec → Plan → Implementar, 2-3 días máx).

5. **Smoke test:**
   ```python
   from openai import OpenAI
   client = OpenAI(base_url="http://100.110.8.13:3101/v1",
                   api_key="freellmapi-0b0b33...")
   resp = client.chat.completions.create(
       model="gpt-4o-mini",  # o "auto"
       messages=[{"role":"user","content":"hola"}],
       max_tokens=50,
   )
   print("OK:", resp.choices[0].message.content)
   print("Routed:", resp._routed_via)
   ```

## Endpoints del proxy (referencia rápida)

| Endpoint | Uso |
|---|---|
| `GET /api/ping` | Health check |
| `GET /v1/models` | Listar modelos disponibles (OpenAI-compat) |
| `POST /v1/chat/completions` | Chat con failover automático |
| `POST /v1/embeddings` | Embeddings (family-based) |
| `POST /v1/responses` | Responses API (Codex CLI shim) |
| `GET /api/auth/status` | Estado de sesión admin |
| `POST /api/auth/login` | Login admin (devuelve token) |
| `GET /api/keys` | Listar keys cargadas (masked) |
| `POST /api/keys` | Cargar key (acepta baseUrl opcional) |
| `POST /api/keys/custom` | Cargar key + modelo custom |
| `GET /api/models` | Catálogo FreeLLMAPI completo |

## Próximos pasos opcionales (no urgentes)

- **Alegent LLM Router v0.1** — wrapper Python encima del proxy que agregue `prefer: quality|speed|cost` + `task: code|vision|reasoning|chat` → capability routing explícito. Tiempo: 1-2 hs. No es necesario forkear FreeLLMAPI.
- **PR upstream** del provider Anthropic nativo a `tashfeenahmed/freellmapi`. Contribución limpia, sin dependencias externas.

## Referencias

- `nelson-llm-generation` (skill hermano) — incluye `references/freellmapi-deploy-and-usage.md` y `references/azure-anthropic-foundry.md` con el detalle completo.
- `nelson-spec-driven-workflow` — flujo completo de PoC (3 fases I+D+I).
- `nelson-ai-agents` — para PoCs con agentes multi-paso.
- `nelson-rag-pipeline` — para PoCs con embeddings + RAG.
- FreeLLMAPI repo: https://github.com/tashfeenahmed/freellmapi
