# OpenCode Zen API — Referencia Técnica

Descubierta en sesión mayo 2026. OpenCode Zen es un proxy OpenAI-compatible que da acceso a modelos cloud (Kimi, MiniMax, Claude, GPT) vía una sola API key.

## Endpoint

- **Base URL:** `https://opencode.ai/zen/v1`
- **Chat completions:** `POST https://opencode.ai/zen/v1/chat/completions`
- **List models:** `GET https://opencode.ai/zen/v1/models`

## Headers Requeridos

```
Authorization: Bearer <API_KEY>
HTTP-Referer: https://tu-app.com      # obligatorio para OpenRouter backend
X-Title: TuAppName                    # obligatorio para OpenRouter backend
Content-Type: application/json
```

> **Pitfall:** Sin `HTTP-Referer` y `X-Title`, OpenRouter (backend de Zen) devuelve 401 "Missing Authentication header" aunque la key sea válida.

## Modelos Clave Disponibles

| Modelo ID | Contexto | Precio est. | Uso |
|-----------|----------|-------------|-----|
| `gpt-5.4-nano` | 128K | ~$0.0001/1K tok | **Default producción (más barato)** |
| `claude-sonnet-4` | 200K | ~$0.003/1K tok | Calidad alta |
| `kimi-k2.6` | 262K | ~$0.001/1K tok | Contexto masivo |
| `minimax-m2.7` | 196K | ~$0.001/1K tok | MiniMax |
| `deepseek-v4-flash-free` | ? | $0 | Modelos -free (intermitentes) |

## SDK (OpenAI-compatible)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://opencode.ai/zen/v1",
    api_key=os.getenv("OPENCODE_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://tu-app.com",
        "X-Title": "TuApp",
    },
)

response = client.chat.completions.create(
    model="gpt-5.4-nano",
    messages=[{"role": "user", "content": "Hola"}],
    max_tokens=100,
)
```

## Key Storage

Guardar en `~/secrets/opencode.env` (chmod 600):
```
OPENCODE_API_KEY=sk-xxxxxxxx
OPENCODE_BASE_URL=https://opencode.ai/zen/v1
OPENCODE_MODEL=gpt-5.4-nano
```

## Docker Compose Pitfall

`docker-compose.yml` usa `${OPENCODE_API_KEY:-}` que lee del **shell del host**, no del archivo. Si la variable no está exportada, el contenedor la ve vacía y usa fallback a Ollama.

**Fix:**
```bash
set -a && source ~/secrets/opencode.env && set +a
docker compose up -d
```

O hardcodear en `.env` en el mismo directorio que `docker-compose.yml`.

## Descubrimiento

La URL correcta (`https://opencode.ai/zen/v1`) se encontró inspeccionando código de ejemplo en GitHub (`aliagenttucuman-byte/latam-flight-delay`). Las URLs alternativas (`api.opencode.ai`, `api.opencode.com`) NO funcionan.
