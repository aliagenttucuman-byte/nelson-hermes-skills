---
name: nelson-llm-generation
title: LLM Generation - OpenCode Zen, OpenAI, Ollama, Anthropic, Groq
description: Integracion con LLMs para el equipo Nelson. Generacion de texto, streaming, manejo de errores, retry con backoff, tracking de tokens/costos. OpenCode Zen (via OpenRouter), OpenAI, Ollama local, Anthropic Claude, Groq.
skill: nelson-llm-generation
author: equipo-nelson
version: 1.1.0
keywords: [llm, opencode, openrouter, openai, ollama, anthropic, claude, groq, streaming, generation, tokens, kimi, minimax]
dependencies: [nelson-rag-pipeline, nelson-optillm]
---

# LLM Generation - Equipo Nelson

## Modelos locales (Ollama) - Recomendados por VRAM

### Con 4GB VRAM (GTX 1650 Mobile/Max-Q)

**Hardware verificado:** NVIDIA GeForce GTX 1650 Mobile/Max-Q, 4096 MiB GDDR5, 13GB RAM sistema.

| Modelo | Tamaño | Uso | VRAM uso | Rendimiento | Comando |
|--------|--------|-----|----------|-------------|---------|
| `llama3.2:3b` | 2.0 GB | **Chat general default** | 100% GPU | ~5s respuesta | `ollama pull llama3.2:3b` |
| `qwen2.5:3b` | 1.9 GB | Código, razonamiento | 100% GPU | ~6s respuesta | `ollama pull qwen2.5:3b` |
| `gemma3:1b` | 800 MB | **Velocidad extrema** | 100% GPU | **~2.7s** respuesta | `ollama pull gemma3:1b` |
| `gemma3:4b` | 3.3 GB | Alternativa Google | 100% GPU (~2.4GB) | ~6s respuesta | `ollama pull gemma3:4b` |
| `nomic-embed-text` | 274 MB | Embeddings | 100% GPU | Instantáneo | `ollama pull nomic-embed-text` |
| `llama3.1:8b` | 4.9 GB | Modelo grande | **43% CPU / 57% GPU** | ~2s respuesta | `ollama pull llama3.1:8b` |
| `llava:7b` | 4.7 GB | **Multimodal** (imágenes) | Mix CPU/GPU | ~2-3s respuesta | `ollama pull llava:7b` |
| `gemma4-e2b-custom`* | 2.62 GB | **Gemma 4 en 4GB** | 100% GPU (~2.9GB) | **~55s** respuesta | Importar GGUF |

> *`gemma4-e2b-custom` requiere descargar el GGUF cuantizado IQ2_M desde Hugging Face e importarlo manualmente a Ollama. No está disponible via `ollama pull`. Ver sección "Importar GGUF a Ollama" y `references/importar-gguf-ollama.md`.
>
> **Comportamiento observado:** Cuando el modelo excede la VRAM disponible, Ollama automáticamente divide la carga entre GPU (lo que entra en VRAM) y CPU (el resto). No es necesario configurar nada. El rendimiento es aceptable para desarrollo (<2s), pero más lento que correr 100% en GPU.
>
> **Tip:** Para desarrollo rápido con 4GB VRAM, usar `llama3.2:3b` o `qwen2.5:3b`. Para máxima calidad, `llama3.1:8b` funciona bien con el mix CPU/GPU.
>
> **Gemma 4:** Disponible en Ollama nativo pero solo en tamaños grandes. La versión `gemma4:e2b` pesa **6.67GB** y no entra en 4GB VRAM. PERO: descargando el GGUF cuantizado `IQ2_M` (2.62GB) desde Hugging Face e importándolo manualmente, **Gemma 4 E2B sí corre en 4GB VRAM** a ~55 segundos por respuesta. Ver `references/gemma4-sizing-discovery.md` y `references/importar-gguf-ollama.md` para el proceso completo.
>
> **Gemma 4 E4B:** La variante E4B (4B params efectivos) **NO entra en 4GB VRAM**. La cuantización más agresiva disponible en Hugging Face (Q2_K) pesa **4.46GB**, que en VRAM se expande a ~5GB+. Límite para 4GB: E2B IQ2_M únicamente. Ver `references/gemma4-sizing-discovery.md`.
>
> **Benchmarks detallados:** Ver [`references/gemma3-benchmarks-4gb-vram.md`](references/gemma3-benchmarks-4gb-vram.md) para tiempos exactos y comparativa completa.

### Con 6GB VRAM (RTX 3050, GTX 1660 Ti, RTX 2060)

| Modelo | Tamaño | Uso | Comando |
|--------|--------|-----|---------|
| `llama3.1:8b` | 4.9 GB | **Mejor chat general** | `ollama pull llama3.1:8b` |
| `mistral:7b` | 4.1 GB | Rápido, buen balance | `ollama pull mistral:7b` |
| `qwen2.5:7b` | 4.4 GB | **Mejor para código** | `ollama pull qwen2.5:7b` |
| `codellama:7b` | 3.8 GB | Especializado código | `ollama pull codellama:7b` |
| `llava:7b` | 4.7 GB | **Multimodal** (imágenes) | `ollama pull llava:7b` |
| `phi3:medium` | 4.0 GB | Razonamiento, Microsoft | `ollama pull phi3:medium` |

### Modelos que NO entran en 6GB

| Modelo | Tamaño | Por qué no |
|--------|--------|-----------|
| `phi4` | ~9 GB | 14B params, necesita 8GB+ |
| `llama3.1:70b` | ~40 GB | Demasiado grande |
| `mixtral:8x7b` | ~26 GB | Modelo MoE |

> **Tip**: Si un modelo es muy grande para tu VRAM, Ollama corre parte en GPU y parte en CPU automaticamente. Pero es más lento.

## Proveedores soportados

| Proveedor | Modelo tipico | Streaming | Costo | Uso ideal |
|-----------|---------------|-----------|-------|-----------|
| **OpenCode Zen** | kimi-k2.6, minimax-m2.7 | Si | $ | **Produccion del equipo** (default) |
| **OpenCode Zen** | claude-3.5-sonnet, gpt-4o | Si | $$-$$$ | Produccion, calidad maxima |
| **OpenAI** | gpt-4o-mini | Si | $$ | Produccion, balance calidad/precio |
| **OpenAI** | gpt-4o | Si | $$$ | Produccion, calidad maxima |
| **Ollama** | llama3.2, qwen2.5 | Si | Gratis | Desarrollo local, privacidad |
| **Anthropic** | claude-3-5-sonnet | Si | $$$ | Razonamiento complejo, coding |
| **Groq** | llama-3.1-70b | Si | $ | Ultra rapido, baja latencia |

> **Default del equipo: OpenCode Zen** para produccion (acceso a 356+ modelos via OpenRouter), **Ollama llama3.2** para desarrollo local.
>
> **OpenCode Zen** es un proxy OpenAI-compatible con BYOK. Da acceso a modelos como Kimi K2.6, MiniMax M2.7, Claude, GPT-4o, etc. La API key funciona via OpenRouter (`https://openrouter.ai/api/v1`). Ver [`references/opencode-zen-setup.md`](references/opencode-zen-setup.md) para detalles completos.
>
> **Nota:** Para la skill de proxy de inferencia local (OptiLLM), ver `nelson-optillm`.

## Importar GGUF a Ollama (modelos personalizados)

Cuando Ollama no tiene la cuantización que necesitás, o querés un modelo que solo existe en Hugging Face como GGUF:

```bash
# 1. Descargar GGUF desde Hugging Face
mkdir -p ~/models/mi-modelo && cd ~/models/mi-modelo
curl -L -o modelo.gguf \
  "https://huggingface.co/usuario/repo/resolve/main/modelo.gguf?download=true"

# 2. Crear Modelfile
cat > Modelfile << 'EOF'
FROM ./modelo.gguf

TEMPLATE """<start_of_turn>user
{{ .System }}
{{ .Prompt }}<end_of_turn>
<start_of_turn>model
"""

PARAMETER stop <end_of_turn>
SYSTEM "Sos un asistente util. Responde siempre en espanol."
EOF

# 3. Importar a Ollama
ollama create nombre-custom -f Modelfile

# 4. Usar
ollama run nombre-custom "Hola"
```

**Cuantizaciones recomendadas por VRAM:**

| VRAM | Cuantización | Tamaño archivo | VRAM real estimada | Nota |
|------|-------------|---------------|-------------------|------|
| 4GB | IQ2_M | ~2.6 GB | ~2.9 GB | Lento pero entra (Gemma 4 E2B) |
| 4GB | Q2_K / Q3_K_S | ~3.0 GB | ~3.3 GB | Balance mejor |
| 6GB | Q4_K_M | ~3.4 GB | ~3.7 GB | Calidad buena |
| 8GB | Q5_K_M / Q6_K | ~4-5 GB | ~4.5-5.5 GB | Calidad alta |

> **Regla de VRAM:** El archivo GGUF ocupa aproximadamente su tamaño de archivo en VRAM, con un factor de expansión de ~1.1x. Ejemplo: archivo de 2.62 GB → ~2.9 GB VRAM. Archivo de 4.46 GB → ~5.0 GB VRAM. Siempre dejar margen: necesitás `archivo_GGUF * 1.1 < VRAM_disponible`.
>
> **Verificación:** Después de importar, correr `ollama ps` y `nvidia-smi` para confirmar que el modelo cargó en GPU y no hizo spill a CPU.

## Servicio LLM

```python
# app/core/llm.py
import os
from typing import AsyncIterator, Iterator
from dataclasses import dataclass
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class LLMService:
    def __init__(self, provider: str = None, model: str = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

        elif self.provider == "opencode-zen":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=settings.OPENCODE_API_KEY,
                base_url="https://openrouter.ai/api/v1",
            )

        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        elif self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=settings.GROQ_API_KEY)

        elif self.provider == "ollama":
            import ollama
            self.client = ollama

        logger.info("llm_service_init", provider=self.provider, model=self.model)

    def generate(self, prompt: str, system: str = None) -> LLMResponse:
        """Generar respuesta sincronica."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        if self.provider in ("openai", "opencode-zen"):
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return LLMResponse(
                content=resp.choices[0].message.content,
                model=resp.model,
                prompt_tokens=resp.usage.prompt_tokens,
                completion_tokens=resp.usage.completion_tokens,
                total_tokens=resp.usage.total_tokens,
            )

        elif self.provider == "anthropic":
            msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
            sys_msg = system or ""
            resp = self.client.messages.create(
                model=self.model,
                messages=msgs,
                system=sys_msg,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return LLMResponse(
                content=resp.content[0].text,
                model=resp.model,
                prompt_tokens=resp.usage.input_tokens,
                completion_tokens=resp.usage.output_tokens,
                total_tokens=resp.usage.input_tokens + resp.usage.output_tokens,
            )

        elif self.provider == "groq":
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return LLMResponse(
                content=resp.choices[0].message.content,
                model=resp.model,
                prompt_tokens=resp.usage.prompt_tokens,
                completion_tokens=resp.usage.completion_tokens,
                total_tokens=resp.usage.total_tokens,
            )

        elif self.provider == "ollama":
            resp = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": self.temperature, "num_predict": self.max_tokens},
            )
            return LLMResponse(
                content=resp["message"]["content"],
                model=self.model,
                prompt_tokens=resp.get("prompt_eval_count", 0),
                completion_tokens=resp.get("eval_count", 0),
                total_tokens=resp.get("prompt_eval_count", 0) + resp.get("eval_count", 0),
            )

        raise ValueError(f"Provider desconocido: {self.provider}")

    async def generate_stream(self, prompt: str, system: str = None) -> AsyncIterator[str]:
        """Generar respuesta en streaming (token por token)."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        if self.provider in ("openai", "opencode-zen"):
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        elif self.provider == "anthropic":
            msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
            sys_msg = system or ""
            with self.client.messages.stream(
                model=self.model,
                messages=msgs,
                system=sys_msg,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        elif self.provider == "groq":
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        elif self.provider == "ollama":
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={"temperature": self.temperature, "num_predict": self.max_tokens},
            )
            for chunk in stream:
                yield chunk["message"]["content"]
```

## Streaming en FastAPI

```python
# app/api/v1/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.llm import LLMService

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def chat_stream(prompt: str):
    llm = LLMService()
    return StreamingResponse(
        llm.generate_stream(prompt, system="Eres un asistente util."),
        media_type="text/event-stream",
    )
```

## Retry con backoff

```python
# app/core/llm.py
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    def generate_with_retry(self, prompt: str, system: str = None) -> LLMResponse:
        return self.generate(prompt, system)
```

## Tracking de costos

```python
# app/core/cost_tracker.py
COSTS_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "llama-3.1-70b": {"input": 0.00059, "output": 0.00079},
    "moonshotai/kimi-k2.6": {"input": 0.000002, "output": 0.000010},
    "minimax/minimax-m2.7": {"input": 0.000002, "output": 0.000010},
}
```
def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = COSTS_PER_1K_TOKENS.get(model, {"input": 0, "output": 0})
    input_cost = (prompt_tokens / 1000) * rates["input"]
    output_cost = (completion_tokens / 1000) * rates["output"]
    return round(input_cost + output_cost, 6)
```

## Configuracion

```
# .env (produccion - OpenCode Zen)
LLM_PROVIDER=opencode-zen
LLM_MODEL=moonshotai/kimi-k2.6
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
OPENCODE_API_KEY=sk-...

# .env (produccion - OpenAI)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
OPENAI_API_KEY=sk-...

# .env (desarrollo local - Ollama, 4GB VRAM)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```
# .env (desarrollo local - alternativa codigo)
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:3b
```

### Recomendacion por hardware

| VRAM | Modelo dev | Modelo prod |
|------|-----------|-------------|
| 4GB | `llama3.2:3b` o `qwen2.5:3b` | **OpenCode Zen** kimi-k2.6 / minimax-m2.7 |
| 6GB | `llama3.1:8b` | **OpenCode Zen** kimi-k2.6 / minimax-m2.7 |
| 8GB+ | `llama3.1:8b` o `mistral:7b` | **OpenCode Zen** kimi-k2.6 / minimax-m2.7 |

## Dependencias

```bash
pip install openai anthropic groq ollama tenacity
```

## Checklist

- [ ] API key configurada para el provider elegido
- [ ] Streaming funciona en frontend (SSE)
- [ ] Retry con backoff activado
- [ ] Costos trackeados por request
- [ ] Rate limiting en endpoints de generacion
- [ ] Fallback a otro provider si el primero falla (opcional)

## Pitfalls

- Streaming SSE requiere `media_type="text/event-stream"` en FastAPI
- Ollama debe estar corriendo localmente (`ollama serve`)
- Anthropic no acepta `system` en `messages`; va como parametro separado
- Groq es muy rapido pero rate limits agresivos (usa backoff)
- Siempre verificar `chunk.choices[0].delta.content` no sea None antes de yield
- Las tags de Ollama pueden pesar más de lo que sugiere el nombre (ej: `gemma4:e2b` pesa 6.67GB, no 4GB). Si no entra en tu VRAM, buscar cuantizaciones GGUF más agresivas en Hugging Face e importarlas manualmente. Ver `references/importar-gguf-ollama.md`
- Si el modelo importado responde basura o repite el prompt, el `TEMPLATE` del Modelfile está mal. Buscar el `chat_template` correcto en la página del modelo en Hugging Face
- **OpenCode Zen / OpenRouter:** Si recibís 401 "Missing Authentication header", verificar que el header `Authorization: Bearer <key>` esté presente. Algunas keys de OpenCode Zen funcionan via OpenRouter (`https://openrouter.ai/api/v1`) pero pueden requerir headers adicionales (`HTTP-Referer`, `X-Title`). Ver `references/opencode-zen-setup.md`
- **OpenCode Zen / OpenRouter:** El listado de modelos (`/v1/models`) puede funcionar mientras que `/v1/chat/completions` da 401 si la key no tiene créditos o permisos. Verificar en el dashboard de OpenCode Zen.
- **OpenCode Zen / OpenRouter:** Los model IDs son del formato `provider/model` (ej: `moonshotai/kimi-k2.6`, `minimax/minimax-m2.7`). No usar nombres cortos.
- **Chat embebido con contexto dinámico:** Ver patrón completo en `references/fleet-chat-assistant-pattern.md`. Puntos clave: usar `window.location.hostname` en el frontend (nunca `localhost` hardcodeado), regenerar contexto en cada request, mandar historial completo al backend, patrón `buffer += lines.pop()` para parsear SSE correctamente.
- **NVIDIA NIM — DeepSeek puede estar caído en free tier:** Si falla, cambiar a `meta/llama-3.3-70b-instruct` — mismo formato OpenAI SDK, validado estable para chat interactivo en español.

## Custom Providers en Hermes Agent

Para conectar endpoints propios o de Azure AI Foundry a Hermes, usar `custom_providers` en `~/.hermes/config.yaml`:

```yaml
custom_providers:
  - name: azure-claude
    base_url: https://<resource>.services.ai.azure.com/anthropic/
    model: claude-sonnet-4-6
    key_env: ANTHROPIC_API_KEY
    api_mode: anthropic_messages
  - name: azure-gpt
    base_url: https://<resource>.cognitiveservices.azure.com/openai/
    model: gpt-5.3-codex
    key_env: AZURE_OPENAI_API_KEY
    api_mode: chat_completions
```

**Uso:**
```bash
hermes chat --provider "custom:azure-claude" --model "claude-sonnet-4-6" -q "Hola"
```

### Proveedor nativo `azure-foundry`

Hermes tiene soporte nativo para Azure AI Foundry:
```bash
hermes config set model.provider azure-foundry
hermes config set model.base_url "https://<resource>.services.ai.azure.com/openai/"
hermes config set model.default "gpt-5.3-codex"
hermes config set model.api_mode codex_responses  # o chat_completions
```

Requiere `AZURE_FOUNDRY_API_KEY` en `~/.hermes/.env`.

### Tabla de compatibilidad Azure x Hermes

| Servicio | Endpoint Azure | `api_mode` | Status con Hermes | Notas |
|----------|---------------|------------|-------------------|-------|
| Claude (Anthropic) | `...azure.com/anthropic/` | `anthropic_messages` | ✅ Funciona | Usar `custom:<name>`, `--model` requerido |
| GPT-4o / GPT-4 | `...azure.com/openai/` | `chat_completions` | ✅ Funciona | Nativo via `azure-foundry` o custom |
| GPT-5.3-Codex | `...azure.com/openai/` | `codex_responses` | ⚠️ Limitado | Azure requiere header `api-key`; Hermes envía `Authorization: Bearer`. Requiere proxy o script intermedio. Ver `references/hermes-azure-responses-api.md` |

### Debuggear endpoints

```bash
# Ver logs de Hermes
grep -i "404\|base_url" ~/.hermes/logs/agent.log | tail -20

# Test directo con curl (Anthropic-style)
curl -s -H "x-api-key: $KEY" -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":1024,"messages":[{"role":"user","content":"OK"}]}' \
  "https://<resource>.services.ai.azure.com/anthropic/v1/messages?api-version=2025-04-15"

# Test directo con curl (Azure Responses API)
curl -s -H "api-key: $KEY" \
  -d '{"model":"gpt-5.3-codex","input":[{"role":"user","content":"OK"}]}' \
  "https://<resource>.cognitiveservices.azure.com/openai/responses?api-version=2025-04-01-preview"
```

> **Nota:** `api_mode` se snapshottea al inicio de la sesión. Cambiarlo mid-session vía `/model` no tiene efecto. Siempre usar `/reset` o reiniciar Hermes después de cambiar `api_mode`.
