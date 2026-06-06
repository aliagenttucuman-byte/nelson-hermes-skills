---
name: nelson-llm-generation
title: LLM Generation - OpenCode Zen, OpenAI, Ollama, Anthropic, Groq, FreeLLMAPI
description: Integracion con LLMs para el equipo Nelson. Generacion de texto, streaming, manejo de errores, retry con backoff, tracking de tokens/costos. OpenCode Zen (via OpenRouter), OpenAI, Ollama local, Anthropic Claude, Groq, FreeLLMAPI proxy multi-provider.
skill: nelson-llm-generation
author: equipo-nelson
version: 1.3.0
keywords: [llm, opencode, openrouter, openai, ollama, anthropic, claude, groq, streaming, generation, tokens, kimi, minimax, azure-foundry, provider-adapter, freellmapi, multi-provider, routing, pociai]
dependencies: [nelson-rag-pipeline, nelson-optillm]
related: [nelson-poc-ai-quickstart, nelson-spec-driven-workflow]
---

# LLM Generation - Equipo Nelson

## Reglas de routing LLM Nelson (cargar primero, 2026-06-06)

Antes de elegir provider/modelo, chequear estas reglas. **No son opcionales** — son cómo JARVIS y los agentes del equipo enrutan requests en el ai-server.

### Para el agente JARVIS / uso personal / Tony

**Siempre Anthropic** vía Azure Foundry:

- Endpoint: `https://yizlafclc001.services.ai.azure.com/anthropic`
- Model: `claude-sonnet-4-6`
- Env var: `AZURE_ANTHROPIC_API_KEY` (en `~/.hermes/.env`)
- Wire format: nativo Anthropic (`x-api-key` + `anthropic-version: 2023-06-01`), no OpenAI-compatible
- Ver [`references/azure-anthropic-foundry.md`](references/azure-anthropic-foundry.md) para detalles, script cliente y quirks

### Para PoCs y otros casos (regla de cascada)

El router FreeLLMAPI intenta en este orden hasta que uno responde. **Por default usar `model="auto"` y dejar al router elegir.** Si necesitás un modelo específico, el orden de preferencia es:

1. **OpenAI directo** (custom provider): `gpt-4o-mini` (default), `gpt-4o`, `o4-mini` (reasoning)
2. **Groq**: `llama-3.3-70b-versatile` (velocidad brutal)
3. **OpenRouter free** (21 modelos autodetectados al cargar key): `qwen/qwen3-coder:free`, `meta-llama/llama-3.3-70b-instruct:free`, etc.
4. **Keyless trial** (Kilo, Pollinations, LLM7) — sin SLA, prompts pueden usarse para training

❌ **OpenCode Zen NO** — key `sk-EASBo2t...5bEtHu` da Cloudflare error 1010 (bloqueada).

### Drop-in: el proxy FreeLLMAPI está en ai-server :3101

No armar abstracciones LLM nuevas en código de agente. El proxy ya es la abstracción:

```python
from openai import OpenAI
client = OpenAI(
    base_url="http://100.110.8.13:3101/v1",
    api_key="freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d",
)
resp = client.chat.completions.create(model="auto", messages=[...])
print("Routed via:", resp._routed_via)  # {platform, model}
```

Setup, endpoints, pitfalls y deploy actual: [`references/freellmapi-deploy-and-usage.md`](references/freellmapi-deploy-and-usage.md).
Build local del proxy (necesario si modificás el código): [`references/freellmapi-local-build.md`](references/freellmapi-local-build.md).

**Para una PoC con IA nueva, cargar también la skill `nelson-poc-ai-quickstart`** que consolida los patrones de cliente, decisión tree por tarea, y template de README.

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

## MarkItDown como capa de ingesta documental

Para pipelines que necesitan pre-procesar documentos antes de enviárselos a un LLM, usar MarkItDown (Microsoft) como primera capa:

```python
from markitdown import MarkItDown
import tempfile
from pathlib import Path

def doc_to_text(file_bytes: bytes, filename: str) -> str:
    """Convertir cualquier documento a texto Markdown para el LLM."""
    md = MarkItDown()
    suffix = Path(filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        result = md.convert(tmp_path)
        return result.text_content or ""
    finally:
        Path(tmp_path).unlink(missing_ok=True)
```

Soporta: PDF, Word, Excel, PPT, HTML, CSV, email (.msg/.eml), YouTube URLs, EPUB, Markdown, TXT.
Pitfall: requiere archivo físico en disco (tempfile), no acepta bytes directamente.
Ver skill `nelson-document-processing` para la implementación completa con fallback pdfplumber.

## Proveedores soportados

| Proveedor | Modelo tipico | Streaming | Costo | Uso ideal |
|-----------|---------------|-----------|-------|-----------|
| **OpenCode Zen** | kimi-k2.6, minimax-m2.7 | Si | $ | **Produccion del equipo** (default) |
| **OpenCode Zen** | claude-3.5-sonnet, gpt-4o | Si | $$-$$$ | Produccion, calidad maxima |
| **OpenAI** | gpt-4o-mini | Si | $$ | Produccion, balance calidad/precio |
| **OpenAI** | gpt-4o | Si | $$$ | Produccion, calidad maxima |
| **Ollama** | llama3.2, qwen2.5 | Si | Gratis | Desarrollo local, privacidad |
| **Anthropic** | claude-sonnet-4-6, claude-opus-4-7, claude-haiku-4-5 | Si | $$$ | Razonamiento complejo, coding. Disponible via Anthropic público O Azure Foundry (single-user, autenticarse con `x-api-key` + `anthropic-version`, path `/anthropic` en baseUrl) |
| **Groq** | llama-3.1-70b | Si | $ | Ultra rapido, baja latencia |
| **Azure AI Foundry** | claude-sonnet-4-6, claude-opus-4-7 | Si | $$-$$$ | Claude via Azure (no API key propia de Anthropic) |
| **FreeLLMAPI proxy (ai-server)** | auto (16 providers, 30+ modelos) | Si | Gratis (free tiers) | **Resiliencia + failover automatico, 1.7B tokens/mes agregados, multi-provider unificado. Deployado en :3101, custom providers via /api/keys/custom** |

> **FreeLLMAPI proxy** está deployado en ai-server (http://100.110.8.13:3101). Apila los free tiers de 16 providers (Google, Groq, Cerebras, SambaNova, NVIDIA, Mistral, OpenRouter, GitHub Models, Cohere, Cloudflare, HF, Z.ai, Ollama Cloud, Kilo, Pollinations, LLM7) detrás de un solo endpoint OpenAI-compatible con failover automático. Drop-in replacement perfecto para los agentes: cambiás `base_url` y listo. Single-user, ToS gris (no para comercial). **Setup completo, URLs, endpoints, pitfalls y deploy actual:** ver [`references/freellmapi-deploy-and-usage.md`](references/freellmapi-deploy-and-usage.md).

> **Azure AI Foundry:** Proporciona acceso a modelos Anthropic Claude via Azure sin necesidad de API key de Anthropic. Requiere `anthropic-version: 2023-06-01` header. El modelo `claude-opus-4-7` **no acepta `temperature`**. Ver [`references/azure-anthropic-foundry.md`](references/azure-anthropic-foundry.md) para detalles completos y script de prueba.

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

## LLM como Generador de Código de DataFrame

Patrón probado del equipo: el usuario describe en lenguaje natural qué quiere hacer con un DataFrame (cruces, filtros, cálculos, agrupaciones) y el LLM genera código Polars ejecutable.

### Prompt Template (seguro)

```python
PROMPT_TEMPLATE = """Sos un experto en análisis de datos con Polars (Python).

Tu tarea es:
1. Entender la intención del usuario (cruces, filtros, cálculos, agrupaciones).
2. Generar UNA ÚNICA expresión de código Python usando Polars (`import polars as pl`) que transforme el DataFrame `df`.
3. La expresión debe devolver un nuevo DataFrame de Polars.
4. No escribas explicaciones. Solo código. No uses markdown.

REGLAS DE SEGURIDAD:
- NO uses `eval()`, `exec()`, `open()`, `os`, `sys`, `subprocess`.
- SOLO usa operaciones de Polars: filtros, joins, groupby, select, with_columns, etc.
- El resultado debe ser un DataFrame de Polars.

ESTRUCTURA DEL DATAFRAME:
{schema_desc}

MUESTRA DE DATOS (primeras {n} filas):
{sample_str}

DESCRIPCIÓN DEL USUARIO DE LO QUE QUIERE HACER:
{user_prompt}

GENERÁ SOLO EL CÓDIGO (una expresión que devuelva el DataFrame transformado):"""
```

### Ejecución segura

```python
import polars as pl

def execute_llm_code(code: str, df: pl.DataFrame) -> pl.DataFrame:
    local_ns = {"pl": pl, "df": df}
    exec(code, {"__builtins__": {}}, local_ns)
    result = local_ns.get("df", df)
    for key, val in local_ns.items():
        if isinstance(val, pl.DataFrame) and key != "df":
            result = val
            break
    return result
```

### Modelo recomendado para esta tarea

| Necesidad | Modelo NVIDIA NIM | Notas |
|-----------|-------------------|-------|
| Código / dataframes | `qwen/qwen3.5-397b-a17b` | Default recomendado. Estable para generar código |
| Docs largos (>50 páginas) | `mistralai/mistral-medium-3.5-128b` | 128K contexto |
| Visión / tablas en imágenes | `meta/llama-3.2-90b-vision-instruct` | Análisis de imágenes |

### Checklist de implementación

- [ ] Prompt incluye esquema + muestra de datos (evita alucinaciones de columnas)
- [ ] Temperatura baja (0.1-0.2) para determinismo en código
- [ ] Namespace aislado sin `__builtins__` (seguridad)
- [ ] Fallback si el código generado falla: devolver df original
- [ ] Limpiar markdown del código generado antes de exec()

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
- **Azure AI Foundry (Anthropic Claude):** No usar `Authorization: Bearer`. Azure requiere `x-api-key: <key>` + `anthropic-version: 2023-06-01`. El modelo `claude-opus-4-7` rechaza `temperature` con error 400; `claude-sonnet-4-6` sí lo acepta. Ver `references/azure-anthropic-foundry.md`
- **FreeLLMAPI / puerto 3001:** El WhatsApp Gateway de Hermes ocupa 3001 en ai-server. Usar siempre `PORT=3101` o superior en `.env` del proxy. El mapping del container es `HOST:3101 → INT:3001`.
- **FreeLLMAPI / `POST /api/keys` no acepta `baseUrl`:** Para cargar OpenAI directo, Anthropic, llama.cpp, vLLM, o cualquier endpoint OpenAI-compatible custom, usar `POST /api/keys/custom` con `{baseUrl, model, displayName, apiKey}`. El endpoint básico es solo para providers nativos del catálogo.
- **FreeLLMAPI / `model: "auto"` cae en reasoning models:** El router prioriza por intelligenceRank, y los modelos top (Nemotron 3 Super, OpenAI o-series, Qwen3-Thinking, DeepSeek-R1) consumen `max_tokens` en razonamiento chain-of-thought. Con `max_tokens: 20` se truncan. Usar `max_tokens: 1000+` o evitar reasoning models para respuestas cortas.
- **FreeLLMAPI / DB persistente:** El volumen `freellmapi-data` guarda users, sessions, keys encriptadas, analytics. Sobrevive a `docker compose down`. Si el user admin se perdió la pass, hay que `docker compose down -v` (nuclear) o recuperarla del password manager.
- **FreeLLMAPI / unified key vs admin token:** Son cosas distintas. `unified key` (`freellmapi-...`) es para clientes del proxy (OpenAI SDK). `admin token` (de `/api/auth/setup` o `/login`) es para gestionar keys/models via API admin. El primero se genera automático en el primer boot; el segundo requiere crear el primer user.
- **FreeLLMAPI / Azure Anthropic `/anthropic` path prefix:** Azure Anthropic Foundry requiere el path `/anthropic` antes de `/v1/messages` (parte del URL del recurso Azure, no de la API Anthropic). Endpoint correcto: `https://<resource>.services.ai.azure.com/anthropic/v1/messages`. Anthropic público (api.anthropic.com) NO requiere ese prefijo. Al cargar como `anthropic` o `custom` con `baseUrl`, el path se preserva verbatim — el usuario debe incluir `/anthropic` en el URL. Si el adapter da 404 "Resource not found" pero un `curl` directo al URL completo da 200, casi siempre es mismatch entre el `baseUrl` guardado y la construcción `baseUrl + /v1/messages` que hace el provider.
- **FreeLLMAPI / discovery de deployments Azure:** Los nombres de deployment en Azure Anthropic Foundry **NO** son los nombres genéricos del modelo. Aunque `claude-sonnet-4-6` exista como modelo público, tu recurso Azure puede no tenerlo deployado. Probar con `GET <baseUrl>/openai/v1/models` con `api-key: <key>` para ver los deployment IDs reales. Catálogo típico: `claude-sonnet-4-6` (preview), `claude-haiku-4-5-20251001`, `claude-opus-4-1-20250805`, `claude-sonnet-4-5-20250929`. No todos los que aparecen en docs de Anthropic están deployados en un recurso Azure dado.
- **FreeLLMAPI / `POST /api/keys` ahora acepta `baseUrl` opcional:** A partir de la integración del provider Anthropic nativo, el schema Zod de `POST /api/keys` se extendió para aceptar `baseUrl` opcional. Solo lo usan los providers que enrutan per-endpoint (`custom` y `anthropic`); el resto lo ignora. Para OpenAI directo sigue siendo más limpio `POST /api/keys/custom` (registra el modelo en el catálogo). Pero `POST /api/keys` con `baseUrl` también funciona y crea una key con `base_url` guardado en la columna correspondiente de `api_keys`.
- **FreeLLMAPI / `claude-sonnet-4-6` con `max_tokens: 20` se trunca en reasoning:** Los modelos Claude con extended thinking habilitado consumen tokens antes de responder. Subir `max_tokens` a 100+ o no usar este modelo para one-word answers.
- **OpenCode Zen key `sk-EASBo2t...5bEtHu` da Cloudflare error 1010:** Bloqueada por Cloudflare a nivel de edge (no es problema de header de auth ni de formato de key). **Descartada del router y de cualquier uso.** Cualquier key con ese error code es inutilizable aunque la key parezca válida en otros lugares. Si `curl` al endpoint con la key da 1010, no cargar al router ni intentar variantes de header (`Authorization`, `x-api-key`, `api-key`, `Basic`) — Cloudflare bloquea antes de que llegue al backend.
- **Regla de routing LLM Nelson (2026-06-06):** Para el agente JARVIS / uso personal, **siempre Anthropic** (Azure Foundry `yizlafclc001.services.ai.azure.com/anthropic`, `claude-sonnet-4-6`, env `AZURE_ANTHROPIC_API_KEY`). Para PoCs, **cascada de fallback en este orden estricto:** (1) OpenAI directo (gpt-4o-mini, gpt-4o, o4-mini vía `custom` provider) → (2) Groq (llama-3.3-70b-versatile) → (3) OpenRouter free (21 modelos autodetectados al cargar key) → (4) Keyless trial (Kilo Gateway, Pollinations, LLM7). **OpenCode Zen NO** (key descartada, ver pitfall arriba).

## Provider adapter pattern (FreeLLMAPI, lessons from Anthropic integration)

**Cuándo aplica:** cuando FreeLLMAPI necesita hablar un protocolo distinto a OpenAI-compatible (Anthropic nativo, Google Gemini, Cohere v1, etc.) y el provider adapter base (`OpenAICompatProvider`) no sirve.

**Patrón del adapter (clase TS):**
1. Extender `BaseProvider` (de `server/src/providers/base.ts`) e implementar `chatCompletion`, `streamChatCompletion`, `validateKey`.
2. Si la wire format difiere del OpenAI shape, hacer mapping bidireccional:
   - **Request:** OpenAI `messages` + `tools` → wire format del provider (ej. Anthropic `system` separado, `tool_use`/`tool_result` blocks).
   - **Response:** wire format → OpenAI `ChatCompletionResponse` shape con `_routed_via: {platform, model}`.
   - **Stream:** mapear eventos SSE del provider (`message_start`, `content_block_delta`, `message_delta`, `message_stop` en Anthropic) → OpenAI `ChatCompletionChunk` con `delta.content` / `delta.tool_calls` y `finish_reason` al final.
3. **No magic rewriting de paths.** El provider concatena `${baseUrl}/v1/messages`. El usuario carga el `baseUrl` correcto incluyendo prefijos necesarios. Documentar en el adapter qué paths asume (ej. Azure Anthropic requiere `/anthropic` en el baseUrl).
4. **Si el provider tiene endpoints con auth distinta** (ej. Anthropic `x-api-key` + `anthropic-version: 2023-06-01`, no `Authorization: Bearer`), implementar `authHeaders(apiKey)` privado.
5. **Per-key baseUrl:** agregar al `resolveProvider(platform, baseUrl)` un branch que use `withBaseUrl(url)` sobre el singleton. Router llama `resolveProvider('anthropic', key.base_url)` por cada key, no el singleton directo. Mismo patrón que `custom`.
6. **Catalog seeding:** el `POST /api/keys` no inserta modelos. Para built-ins seedear en `db/index.ts` (en `migrateModelsV*`); para custom, el dashboard/backend tiene `POST /api/keys/custom` que sí los inserta. Built-ins nuevos requieren migración + rebuild Docker.
7. **Antes de tocar código, validar con `scripts/probe_provider.py`:** corre el flujo de discovery (lista modelos OpenAI-compat, prueba deployment names Anthropic conocidos) sin levantar el router. Imprime qué modelos están vivos y cuáles no. **Si la Azure Anthropic Foundry resource no tiene Claude Opus deployado pero sí Sonnet, esto lo dice antes de que modifiques el adapter.**

**Catálogo real de providers con `baseUrl` per-key:** `custom` (cualquier OpenAI-compat), `anthropic` (público + Azure Foundry). Los demás tienen un único endpoint global registrado en `providers/index.ts`.

**Cómo debuggear un provider nuevo:**
1. Probar el endpoint con `curl` directo (sanity check, evita perder tiempo en código).
2. Probar con un POST simple desde un script Python, logueando el body exacto que envía.
3. Después probar a través del router, logueando `docker logs` para ver `API error 4xx: ...` con el mensaje real del provider.
4. **Si el error genérico "Resource not found" no aparece en docs, casi siempre es path prefix mal armado o deployment name que no existe en el recurso.**
5. **Patrón de diagnóstico rápido:** si el adapter da 404 con `X-Routed-Via: <platform>/<model>` pero `curl` directo al endpoint completo da 200, comparar las dos URLs carácter por carácter. El adapter concatena `${baseUrl}/<path-template>`. Si el provider requiere un prefijo (`/anthropic`, `/v1api`, etc.) que el usuario incluyó en el baseUrl, todo bien. Si el prefijo está en el `path-template` del adapter pero no en el baseUrl, hay mismatch. **Fix:** el baseUrl debe incluir cualquier path que el provider requiera antes de `<path-template>`. En Azure Anthropic: baseUrl = `https://<resource>.services.ai.azure.com/anthropic` (no `...azure.com` solo).
