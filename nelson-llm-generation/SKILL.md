---
name: nelson-llm-generation
title: LLM Generation - OpenAI, Ollama, Anthropic, Groq
description: Integracion con LLMs para el equipo Nelson. Generacion de texto, streaming, manejo de errores, retry con backoff, tracking de tokens/costos. OpenAI, Ollama local, Anthropic Claude, Groq.
skill: nelson-llm-generation
author: equipo-nelson
version: 1.0.0
keywords: [llm, openai, ollama, anthropic, claude, groq, streaming, generation, tokens]
dependencies: [nelson-rag-pipeline]
---

# LLM Generation - Equipo Nelson

## Modelos locales (Ollama) - Recomendados por VRAM

### Con 4GB VRAM (GTX 1650 Mobile/Max-Q)

**Hardware verificado:** NVIDIA GeForce GTX 1650 Mobile/Max-Q, 4096 MiB GDDR5, 13GB RAM sistema.

| Modelo | Tamaño | Uso | VRAM uso | Rendimiento | Comando |
|--------|--------|-----|----------|-------------|---------|
| `llama3.2:3b` | 2.0 GB | **Chat general default** | 100% GPU | <1s respuesta | `ollama pull llama3.2:3b` |
| `qwen2.5:3b` | 1.9 GB | Código, razonamiento | 100% GPU | <1s respuesta | `ollama pull qwen2.5:3b` |
| `gemma2:2b` | 1.6 GB | Eficiente, Google | 100% GPU | <1s respuesta | `ollama pull gemma2:2b` |
| `nomic-embed-text` | 274 MB | Embeddings | 100% GPU | Instantáneo | `ollama pull nomic-embed-text` |
| `llama3.1:8b` | 4.9 GB | Modelo grande | **43% CPU / 57% GPU** | ~1.8s respuesta | `ollama pull llama3.1:8b` |
| `llava:7b` | 4.7 GB | **Multimodal** (imágenes) | Mix CPU/GPU | ~2-3s respuesta | `ollama pull llava:7b` |

> **Comportamiento observado:** Cuando el modelo excede la VRAM disponible, Ollama automáticamente divide la carga entre GPU (lo que entra en VRAM) y CPU (el resto). No es necesario configurar nada. El rendimiento es aceptable para desarrollo (<2s), pero más lento que correr 100% en GPU.

> **Tip:** Para desarrollo rápido con 4GB VRAM, usar `llama3.2:3b` o `qwen2.5:3b`. Para máxima calidad, `llama3.1:8b` funciona bien con el mix CPU/GPU.

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
| **OpenAI** | gpt-4o-mini | Si | $$ | Produccion, balance calidad/precio |
| **OpenAI** | gpt-4o | Si | $$$ | Produccion, calidad maxima |
| **Ollama** | llama3.2, qwen2.5 | Si | Gratis | Desarrollo local, privacidad |
| **Anthropic** | claude-3-5-sonnet | Si | $$$ | Razonamiento complejo, coding |
| **Groq** | llama-3.1-70b | Si | $ | Ultra rapido, baja latencia |

> **Default del equipo: OpenAI gpt-4o-mini** para produccion, **Ollama llama3.2** para desarrollo local.

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

        if self.provider == "openai":
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

        if self.provider == "openai":
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
}

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = COSTS_PER_1K_TOKENS.get(model, {"input": 0, "output": 0})
    input_cost = (prompt_tokens / 1000) * rates["input"]
    output_cost = (completion_tokens / 1000) * rates["output"]
    return round(input_cost + output_cost, 6)
```

## Configuracion

```
# .env (produccion - OpenAI)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...

# .env (desarrollo local - Ollama, 4GB VRAM)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# .env (desarrollo local - alternativa codigo)
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:3b
```

### Recomendacion por hardware

| VRAM | Modelo dev | Modelo prod |
|------|-----------|-------------|
| 4GB | `llama3.2:3b` o `qwen2.5:3b` | OpenAI gpt-4o-mini |
| 6GB | `llama3.1:8b` | OpenAI gpt-4o |
| 8GB+ | `llama3.1:8b` o `mistral:7b` | OpenAI gpt-4o |

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
