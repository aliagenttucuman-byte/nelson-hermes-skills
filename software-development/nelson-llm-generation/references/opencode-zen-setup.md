# OpenCode Zen / OpenRouter — Setup y Descubrimiento

> Fecha: 2026-05-15
> Sesion: Descubrimiento de conectividad con API key de Nelson (Tony Stark).
> Status: URL base y listado de modelos confirmados. Chat completions requieren verificacion de creditos/permisos en dashboard.

## Qué es

OpenCode Zen es un proxy OpenAI-compatible con BYOK (bring your own key). En la práctica, la API key del equipo funciona contra el endpoint de **OpenRouter** (`https://openrouter.ai/api/v1`), que es una agregadora de modelos.

Acceso a **356+ modelos** sin necesidad de registrarse en cada provider por separado.

## URL Base

| Endpoint | URL | Status |
|----------|-----|--------|
| OpenRouter API | `https://openrouter.ai/api/v1` | Funciona para listado de modelos |
| OpenCode directo | `https://api.opencode.ai/v1` | Responde 200 pero "Not Found" en chat |

**Conclusión:** Usar `https://openrouter.ai/api/v1` como `base_url` en el SDK de OpenAI.

## Autenticación

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-EASBo2tbnYoiDUKhAqGaam4b3KzeMriB9hAge72K5PF9h5SDHhOl4X6Acf5bEtHu",
    base_url="https://openrouter.ai/api/v1",
)
```

Headers requeridos:
- `Authorization: Bearer <key>`
- Opcional: `HTTP-Referer: https://tusitio.com`
- Opcional: `X-Title: TuApp`

## Listado de Modelos (verificado)

```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENCODE_API_KEY" | python3 -m json.tool
```

**Modelos destacados disponibles:**

| ID | Provider | Contexto | Uso recomendado |
|----|----------|----------|-----------------|
| `moonshotai/kimi-k2.6` | MoonshotAI | 262K | **Default del equipo** — razonamiento, coding, RAG |
| `minimax/minimax-m2.7` | MiniMax | 196K | Alternativa fuerte — agentes, chat |
| `minimax/minimax-m2.5:free` | MiniMax | 196K | **Gratis** — para pruebas |
| `anthropic/claude-3.5-sonnet` | Anthropic | 200K | Calidad máxima, coding |
| `openai/gpt-4o` | OpenAI | 128K | Producción confiable |
| `openai/gpt-4o-mini` | OpenAI | 128K | Económico, rápido |

**Total confirmado:** 356 modelos incluyendo gratis y de pago.

## Chat Completions

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENCODE_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

resp = client.chat.completions.create(
    model="moonshotai/kimi-k2.6",
    messages=[{"role": "user", "content": "Hola"}],
    max_tokens=100,
)
print(resp.choices[0].message.content)
```

## Problemas encontrados y soluciones

### 401 "Missing Authentication header"
- **Causa:** La key funciona para `/models` pero puede fallar para `/chat/completions` si no hay créditos en la cuenta de OpenCode Zen/OpenRouter, o si el header no se envía correctamente.
- **Fix:** Verificar en el dashboard de OpenCode Zen que haya saldo/créditos. Asegurar que el header `Authorization: Bearer <key>` esté exactamente así.

### "Not Found" en api.opencode.ai
- **Causa:** La URL `https://api.opencode.ai/v1/chat/completions` responde HTTP 200 con body "Not Found", no JSON válido.
- **Fix:** Usar `https://openrouter.ai/api/v1` en su lugar.

## Integración con el stack del equipo

En cualquier RAG o backend FastAPI del equipo, cambiar solo:

```python
# Antes (Ollama local)
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# Después (OpenCode Zen)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENCODE_API_KEY"),
)
```

Los embeddings siguen yendo directo a Ollama local (sin cambios).

## Variables de entorno

```bash
# .env
LLM_PROVIDER=opencode-zen
LLM_MODEL=moonshotai/kimi-k2.6
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
OPENCODE_API_KEY=sk-...
```

## Telemetría

Langfuse trackea requests a OpenCode Zen igual que a cualquier provider OpenAI-compatible. Solo cambia el `base_url`.

```python
# Langfuse automático con SDK OpenAI
from langfuse.openai import openai
client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", ...)
```

## Costos estimados (OpenRouter)

| Modelo | Input/1M tokens | Output/1M tokens |
|--------|-----------------|------------------|
| kimi-k2.6 | ~$0.002 | ~$0.010 |
| minimax-m2.7 | ~$0.002 | ~$0.010 |
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |

> Los precios exactos varían. Consultar `/v1/models` para el pricing real de cada modelo.
