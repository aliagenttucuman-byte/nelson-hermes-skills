# OpenCode Zen — Configuración Confirmada (Mayo 2026)

## Endpoint

```
Base URL: https://opencode.ai/zen/v1
Chat completions: POST https://opencode.ai/zen/v1/chat/completions
List models:      GET  https://opencode.ai/zen/v1/models
```

## Headers obligatorios

| Header | Valor | Nota |
|--------|-------|------|
| `Authorization` | `Bearer sk-...` | Key del usuario |
| `HTTP-Referer` | URL de la app | Requerido por OpenRouter (backend de Zen) |
| `X-Title` | Nombre de la app | Requerido por OpenRouter |
| `Content-Type` | `application/json` | Estándar |

## Cliente OpenAI SDK (Python)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://opencode.ai/zen/v1",
    api_key=os.getenv("OPENCODE_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://tu-app.com",
        "X-Title": "MiApp",
    },
)

response = client.chat.completions.create(
    model="gpt-5.4-nano",
    messages=[{"role": "user", "content": "Hola"}],
    max_tokens=100,
    temperature=0.3,
)
```

## Modelos probados y estado

| Modelo | Estado | Notas |
|--------|--------|-------|
| `gpt-5.4-nano` | ✅ Funciona | **Default del equipo** — más barato, respuestas concisas |
| `claude-sonnet-4` | ✅ Funciona | Mejor calidad, más caro |
| `kimi-k2.6` | ✅ Funciona | Contexto 262K, bueno para RAGs largos |
| `minimax-m2.7` | ❌ Error | No responde (probado mayo 2026) |
| `deepseek-v4-flash-free` | ⚠️ Vacío | Probablemente rate-limit o sin créditos |
| `qwen3.6-plus-free` | ❌ Error | Falla consistentemente |
| `minimax-m2.5-free` | ❌ Error | Falla consistentemente |
| `gpt-5.4-mini` | ✅ Funciona | Intermedio calidad/precio |
| `claude-haiku-4-5` | ✅ Funciona | Barato, calidad media |

## Variables de entorno (Docker Compose)

```yaml
environment:
  - OPENCODE_API_KEY=${OPENCODE_API_KEY:-}
  - OPENCODE_BASE_URL=${OPENCODE_BASE_URL:-https://opencode.ai/zen/v1}
  - LLM_MODEL=${LLM_MODEL:-gpt-5.4-nano}
  - OPENCODE_REFERER=${OPENCODE_REFERER:-https://github.com/nelson/rag}
  - OPENCODE_TITLE=${OPENCODE_TITLE:-NelsonRAG}
```

## Patrón de fallback en código

```python
from openai import OpenAI

# OpenCode Zen (primera opción)
if os.getenv("OPENCODE_API_KEY"):
    client = OpenAI(
        base_url=os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1"),
        api_key=os.getenv("OPENCODE_API_KEY"),
        default_headers={...},
    )
    model = os.getenv("LLM_MODEL", "gpt-5.4-nano")
else:
    # Fallback a Ollama local
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    model = "llama3.2:3b"
```

## Key aprendizajes de esta sesión

1. **La URL base correcta es `https://opencode.ai/zen/v1`**, no `api.opencode.ai` ni `openrouter.ai` directo.
2. **OpenCode Zen usa OpenRouter como backend** — por eso requiere `HTTP-Referer` y `X-Title`.
3. **Los modelos `-free` no funcionan** en esta cuenta (respuestas vacías o errores). Usar modelos pagos.
4. **`gpt-5.4-nano` es el sweet spot** para producción: funciona, es el más barato, y responde rápido.
5. **Ollama local sigue siendo necesario** para embeddings (`nomic-embed-text`) y como fallback offline.
