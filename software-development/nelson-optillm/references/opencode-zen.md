# OpenCode Zen — Referencia Técnica

## Descubrimiento (sesión mayo 2026)

OpenCode Zen es un proxy OpenAI-compatible descubierto a través del repo
https://github.com/aliagenttucuman-byte/latam-flight-delay (archivo `challenge/ai_insights.py`).

## URL Base

```
https://opencode.ai/zen/v1/chat/completions
```

El endpoint `/models` también funciona:
```
https://opencode.ai/zen/v1/models
```

## Headers Requeridos

```
Authorization: Bearer <API_KEY>
HTTP-Referer: <cualquier URL válida>
X-Title: <nombre de app>
Content-Type: application/json
```

Sin `HTTP-Referer` y `X-Title`, algunos requests pueden fallar.

## Modelos Disponibles (41 totales)

Lista completa obtenida el 15/may/2026:

| ID | Nombre | Contexto | Notas |
|----|--------|----------|-------|
| claude-opus-4-7 | Claude Opus 4.7 | ? | |
| claude-opus-4-6 | Claude Opus 4.6 | ? | |
| claude-opus-4-5 | Claude Opus 4.5 | ? | |
| claude-opus-4-1 | Claude Opus 4.1 | ? | |
| claude-sonnet-4-6 | Claude Sonnet 4.6 | ? | |
| claude-sonnet-4-5 | Claude Sonnet 4.5 | ? | |
| **claude-sonnet-4** | **Claude Sonnet 4** | ? | ✅ Mejor calidad probada |
| claude-haiku-4-5 | Claude Haiku 4.5 | ? | ✅ Funciona, económico |
| gemini-3.1-pro | Gemini 3.1 Pro | ? | |
| gemini-3-flash | Gemini 3 Flash | ? | |
| gpt-5.5 | GPT 5.5 | ? | |
| gpt-5.5-pro | GPT 5.5 Pro | ? | |
| gpt-5.4 | GPT 5.4 | ? | |
| gpt-5.4-pro | GPT 5.4 Pro | ? | |
| gpt-5.4-mini | GPT 5.4 Mini | ? | ❌ Error en test |
| **gpt-5.4-nano** | **GPT 5.4 Nano** | ? | ✅ **Más barato que funciona** |
| gpt-5.4-nano | GPT 5.4 Nano | ? | ✅ Funciona |
| gpt-5.3-codex-spark | GPT 5.3 Codex Spark | ? | |
| gpt-5.3-codex | GPT 5.3 Codex | ? | |
| gpt-5.2 | GPT 5.2 | ? | |
| gpt-5.2-codex | GPT 5.2 Codex | ? | |
| gpt-5.1 | GPT 5.1 | ? | |
| gpt-5.1-codex-max | GPT 5.1 Codex Max | ? | |
| gpt-5.1-codex | GPT 5.1 Codex | ? | |
| gpt-5.1-codex-mini | GPT 5.1 Codex Mini | ? | |
| gpt-5 | GPT 5 | ? | |
| gpt-5-codex | GPT 5 Codex | ? | |
| gpt-5-nano | GPT 5 Nano | ? | |
| glm-5.1 | GLM 5.1 | ? | |
| glm-5 | GLM 5 | ? | ❌ No respondió |
| minimax-m2.5 | MiniMax M2.5 | ? | |
| **kimi-k2.6** | **Kimi K2.6** | **262K** | ✅ Funciona, contexto enorme |
| kimi-k2.5 | Kimi K2.5 | ? | |
| qwen3.6-plus | Qwen 3.6 Plus | ? | |
| qwen3.5-plus | Qwen 3.5 Plus | ? | |
| big-pickle | Big Pickle | ? | |
| deepseek-v4-flash-free | DeepSeek V4 Flash (free) | ? | ❌ Vacío (rate limit?) |
| qwen3.6-plus-free | Qwen 3.6 Plus (free) | ? | ❌ Error |
| minimax-m2.5-free | MiniMax M2.5 (free) | ? | ❌ No respondió |
| ring-2.6-1t-free | Ring 2.6 1T (free) | ? | No testeado |
| trinity-large-preview-free | Trinity Large Preview (free) | ? | No testeado |
| nemotron-3-super-free | Nemotron 3 Super (free) | ? | No testeado |

## Tests Realizados (15/may/2026)

### Claude Sonnet 4
```
Input: "Hola, quien sos? Responde en 2 oraciones."
Output: "Hola, soy Claude, un asistente de inteligencia artificial creado por Anthropic. Estoy aquí para ayudarte con preguntas, conversaciones y diversas tareas que puedas necesitar."
Status: ✅ OK
```

### Kimi K2.6
```
Input: "Hola, quien sos? Responde en 2 oraciones."
Output: "Soy un asistente de inteligencia artificial creado por Moonshot AI. Estoy aquí..." (truncó por max_tokens)
Status: ✅ OK
```

### GPT 5.4 Nano
```
Input: "Hola, quien sos? 1 oracion."
Output: "Hola, soy ChatGPT, un asistente de IA creado por OpenAI."
Status: ✅ OK
```

### MiniMax M2.7
```
Input: "Hola, quien sos? Responde en 2 oraciones."
Output: ERROR (modelo no encontrado con ese ID)
Status: ❌ Falló
Nota: En OpenCode Zen el ID es `minimax-m2.5`, no `minimax-m2.7`. En OpenRouter sí existe `minimax/minimax-m2.7`.
```

### Modelos -free
```
deepseek-v4-flash-free: Vacío (posible rate limit)
qwen3.6-plus-free: Error
minimax-m2.5-free: No respondió
Status: ❌ Ninguno funció en test rápido
```

## Integración con SDK OpenAI

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://opencode.ai/zen/v1",
    api_key=os.getenv("OPENCODE_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://tu-app.com",
        "X-Title": "MiApp"
    }
)

response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[{"role": "user", "content": "Hola"}]
)
```

## Relación con OpenRouter

- La **misma API key** funciona para **listar modelos** en OpenRouter:
  `https://openrouter.ai/api/v1/models`
- OpenRouter expone **356 modelos** y sí muestra pricing.
- Pero el **chat completions** debe ir por `opencode.ai/zen/v1`, NO por `openrouter.ai`.
- OpenCode Zen parece ser un wrapper/whitelabel de OpenRouter con subset de modelos (41 vs 356).

## Pricing

- El endpoint `/models` de OpenCode Zen **no expone pricing** (devuelve N/A).
- Para estimar costos, usar OpenRouter como referencia.
- Modelos `-free` existen en el catálogo pero **no funcionaron** en tests (posible rate limit o créditos insuficientes).

## Key Guardada en Servidor

`/home/server/secrets/opencode.env` — permisos 600.
