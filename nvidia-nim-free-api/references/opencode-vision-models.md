# OpenCode Vision Models — Test Results (Mayo 2026)

Testeados contra `https://opencode.ai/zen/v1/chat/completions` con imagen PNG base64.
Task: clasificar color de pixel / analizar imagen de vegetación aérea.

## Modelos con visión FUNCIONAL

| Modelo | Latencia | Notas |
|--------|----------|-------|
| `claude-haiku-4-5` | ~2s | ✅ Más barato. JSON limpio. Recomendado para lotes. |
| `claude-sonnet-4` | ~3s | ✅ Más potente. Bueno para análisis detallado. |
| `claude-sonnet-4-5` | ~3s | ✅ Similar a sonnet-4. |
| `claude-opus-4-1` | ~5s | ✅ El más caro. Reservar para casos complejos. |

## Modelos SIN visión en OpenCode

| Modelo | Error | Causa |
|--------|-------|-------|
| `gpt-5.x` (nano, mini, pro, etc) | HTTP 400 — body vacío | Proxy de OpenCode no pasa imágenes a GPT |
| `gemini-3.x-flash`, `gemini-3.1-pro` | HTTP 401 | Error de credenciales GCP en el proxy |
| `minimax-m2.5` | HTTP 400 — "does not support multimodal" | Explícito |
| `deepseek-v4-flash-free`, `qwen3.x` | No testeado | Modelos de texto puro |

## Configuración para usar visión vía OpenCode

```python
import os
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/secrets/opencode.env"))

OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY")
OPENCODE_BASE_URL = "https://opencode.ai/zen/v1/chat/completions"
VLM_MODEL_VISION = "claude-haiku-4-5"  # El más barato con visión
```

El payload sigue el formato OpenAI estándar con `image_url` — compatible 1:1.

## Catálogo completo (Mayo 2026)

```
claude-opus-4-7, claude-opus-4-6, claude-opus-4-5, claude-opus-4-1
claude-sonnet-4-6, claude-sonnet-4-5, claude-sonnet-4
claude-haiku-4-5
gemini-3.5-flash, gemini-3.1-pro, gemini-3-flash
gpt-5.5, gpt-5.5-pro, gpt-5.4, gpt-5.4-pro, gpt-5.4-mini, gpt-5.4-nano
gpt-5.3-codex-spark, gpt-5.3-codex
gpt-5.2, gpt-5.2-codex
gpt-5.1, gpt-5.1-codex-max, gpt-5.1-codex, gpt-5.1-codex-mini
gpt-5, gpt-5-codex, gpt-5-nano
grok-build-0.1
glm-5.1, glm-5
minimax-m2.7, minimax-m2.5
kimi-k2.6, kimi-k2.5
qwen3.6-plus, qwen3.5-plus
big-pickle
deepseek-v4-flash-free, qwen3.6-plus-free, minimax-m2.5-free, nemotron-3-super-free
```
