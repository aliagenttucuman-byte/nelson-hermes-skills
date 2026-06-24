---
name: nvidia-nim-free-api
description: "NVIDIA NIM Free API: acceso a modelos de IA de primer nivel sin costo. DeepSeek V4, Qwen3.5 397B, Llama Vision 90B, Mistral Medium, Nemotron, GLM-5.1. Compatible con OpenAI SDK. Keys en ~/secrets/nvidia_nim_keys.env."
version: 2.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [nvidia, nim, llm, free-api, openai-compatible, inference, modelos, gratis, vision, thinking]
    related_skills: [nelson-llm-generation, nelson-optillm, spike, nelson-ai-vision]
---

# NVIDIA NIM Free API

Acceso gratuito a modelos de IA de primer nivel via NVIDIA NIM.
Compatible con OpenAI SDK — solo cambiás `base_url` y `api_key`.

**Keys guardadas en:** `~/secrets/nvidia_nim_keys.env`
**Base URL:** `https://integrate.api.nvidia.com/v1`
**Generar más keys:** https://build.nvidia.com → botón "Generate API Key" por modelo

---

## Catálogo de modelos (clasificado por uso)

### Chat / Razonamiento general

| Modelo | Notas |
|--------|-------|
| `minimaxai/minimax-m2.7` | Chat rápido, 8K output |
| `meta/llama-3.3-70b-instruct` | **Default del equipo para chat grounded sobre contexto estructurado.** OpenAI SDK directo, sin parámetros raros. Bajo costo de latencia, buen seguimiento de system prompt con instrucciones estrictas ("NO inventes datos, citá solo los del contexto"). Usado en ForestAI/yolov para chat IA sobre métricas Hansen GFC. |

### Razonamiento avanzado / Thinking mode

| Modelo | Thinking param | Notas |
|--------|----------------|-------|
| `qwen/qwen3.5-397b-a17b` | `"chat_template_kwargs":{"enable_thinking":True}` via requests | MoE 397B, potentísimo |
| `google/gemma-4-31b-it` | `NVIDIA_KEY_GEMMA4_31B` | `"chat_template_kwargs":{"enable_thinking":True}` via requests | 16K output |
| `z-ai/glm-5.1` | `NVIDIA_KEY_GLM5` | `extra_body={"chat_template_kwargs":{"enable_thinking":True,"clear_thinking":False}}` | Muestra reasoning |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | `NVIDIA_KEY_NEMOTRON_OMNI` | `extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384}` | 65K output |

### Coding

| Modelo | Key env var | Notas |
|--------|-------------|-------|
| `qwen/qwen3-coder-480b-a35b-instruct` | `NVIDIA_KEY_QWEN3_CODER` | 480B, mejor para coding complejo. Latencia alta |

### Documentos largos / RAG

| Modelo | Key env var | Notas |
|--------|-------------|-------|
| `mistralai/mistral-medium-3.5-128b` | `NVIDIA_KEY_MISTRAL_MEDIUM` | 128K contexto, `reasoning_effort=high` via requests |

### Visión / Multimodal

| Modelo | Key env var | Notas |
|--------|-------------|-------|
| `meta/llama-3.2-90b-vision-instruct` | `NVIDIA_KEY_LLAMA_VISION` | Análisis de imágenes, tablas, diagramas. **Solución para RAG-Anything sin GPU 8GB+** |

---

## Snippets por categoría

### Chat estándar (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="os.getenv("NVIDIA_API_KEY")"  # DeepSeek V4 Pro
)

completion = client.chat.completions.create(
    model="deepseek-ai/deepseek-v4-pro",
    messages=[{"role": "user", "content": "Tu pregunta acá"}],
    temperature=1,
    top_p=0.95,
    max_tokens=16384,
    stream=True
)

for chunk in completion:
    if chunk.choices and chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

---

### DeepSeek V4 Flash — Thinking mode (extra_body)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="os.getenv("NVIDIA_API_KEY")"
)

completion = client.chat.completions.create(
    model="deepseek-ai/deepseek-v4-flash",
    messages=[{"role": "user", "content": "Tu pregunta acá"}],
    temperature=1,
    top_p=0.95,
    max_tokens=16384,
    extra_body={"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}},
    stream=True
)

for chunk in completion:
    if not getattr(chunk, "choices", None):
        continue
    delta = chunk.choices[0].delta
    reasoning = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
    if reasoning:
        print(reasoning, end="")
    if delta.content is not None:
        print(delta.content, end="")
```

---

### Qwen 3.5 397B — Thinking mode (requests directo)

```python
import requests

headers = {
    "Authorization": "Bearer os.getenv("NVIDIA_API_KEY")",
    "Accept": "text/event-stream"
}

payload = {
    "model": "qwen/qwen3.5-397b-a17b",
    "messages": [{"role": "user", "content": "Tu pregunta acá"}],
    "max_tokens": 16384,
    "temperature": 0.60,
    "top_p": 0.95,
    "top_k": 20,
    "stream": True,
    "chat_template_kwargs": {"enable_thinking": True},
}

response = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers=headers, json=payload, stream=True
)
for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

---

### Gemma 4 31B — Thinking mode (requests directo)

```python
import requests

headers = {
    "Authorization": "Bearer os.getenv("NVIDIA_API_KEY")",
    "Accept": "text/event-stream"
}

payload = {
    "model": "google/gemma-4-31b-it",
    "messages": [{"role": "user", "content": "Tu pregunta acá"}],
    "max_tokens": 16384,
    "temperature": 1.0,
    "top_p": 0.95,
    "stream": True,
    "chat_template_kwargs": {"enable_thinking": True},
}

response = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers=headers, json=payload, stream=True
)
for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

---

### GLM-5.1 — Thinking mode (muestra reasoning completo)

```python
from openai import OpenAI
import sys

_C = "\033[90m" if sys.stdout.isatty() else ""
_R = "\033[0m" if sys.stdout.isatty() else ""

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="os.getenv("NVIDIA_API_KEY")"
)

completion = client.chat.completions.create(
    model="z-ai/glm-5.1",
    messages=[{"role": "user", "content": "Tu pregunta acá"}],
    temperature=1,
    max_tokens=16384,
    extra_body={"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}},
    stream=True
)

for chunk in completion:
    if not getattr(chunk, "choices", None):
        continue
    delta = chunk.choices[0].delta
    if getattr(delta, "reasoning_content", None):
        print(f"{_C}{delta.reasoning_content}{_R}", end="")
    if delta.content:
        print(delta.content, end="")
```

---

### Nemotron Omni 30B — Thinking + reasoning_budget

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="os.getenv("NVIDIA_API_KEY")"
)

completion = client.chat.completions.create(
    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    messages=[{"role": "user", "content": "Tu pregunta acá"}],
    temperature=0.6,
    top_p=0.95,
    max_tokens=65536,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": True},
        "reasoning_budget": 16384
    },
    stream=True
)

for chunk in completion:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    if getattr(delta, "reasoning_content", None):
        print(delta.reasoning_content, end="")
    if delta.content is not None:
        print(delta.content, end="")
```

---

### Mistral Medium 3.5 — 128K contexto, reasoning_effort (requests)

```python
import requests

headers = {
    "Authorization": "Bearer os.getenv("NVIDIA_API_KEY")",
    "Accept": "text/event-stream"
}

payload = {
    "model": "mistralai/mistral-medium-3.5-128b",
    "reasoning_effort": "high",
    "messages": [{"role": "user", "content": "Tu pregunta acá"}],
    "max_tokens": 16384,
    "temperature": 0.70,
    "stream": True
}

response = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers=headers, json=payload, stream=True
)
for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

---

### Llama 3.2 90B Vision — análisis de imágenes (requests + base64)

```python
import requests, base64

def read_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

headers = {
    "Authorization": "Bearer os.getenv("NVIDIA_API_KEY")",
    "Accept": "text/event-stream"
}

payload = {
    "model": "meta/llama-3.2-90b-vision-instruct",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describí esta imagen en detalle."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{read_b64('/ruta/a/imagen.jpg')}"}
            }
        ]
    }],
    "max_tokens": 512,
    "temperature": 1.0,
    "stream": True
}

response = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers=headers, json=payload, stream=True
)
for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

---

## Integración con proyectos del equipo

```python
# app/core/nvidia_config.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.expanduser("~/secrets/nvidia_nim_keys.env"))

BASE_URL = "https://integrate.api.nvidia.com/v1"

MODELS = {
    # Chat general
    "deepseek_pro":  ("deepseek-ai/deepseek-v4-pro",                     os.getenv("NVIDIA_KEY_DEEPSEEK_V4_PRO")),
    "minimax":       ("minimaxai/minimax-m2.7",                           os.getenv("NVIDIA_KEY_MINIMAX_M2_7")),
    # Thinking
    "deepseek_flash":("deepseek-ai/deepseek-v4-flash",                   os.getenv("NVIDIA_KEY_DEEPSEEK_V4_FLASH")),
    "qwen397b":      ("qwen/qwen3.5-397b-a17b",                          os.getenv("NVIDIA_KEY_QWEN35_397B")),
    "gemma4":        ("google/gemma-4-31b-it",                           os.getenv("NVIDIA_KEY_GEMMA4_31B")),
    "glm5":          ("z-ai/glm-5.1",                                    os.getenv("NVIDIA_KEY_GLM5")),
    "nemotron":      ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",   os.getenv("NVIDIA_KEY_NEMOTRON_OMNI")),
    # Coding
    "qwen_coder":    ("qwen/qwen3-coder-480b-a35b-instruct",             os.getenv("NVIDIA_KEY_QWEN3_CODER")),
    # RAG / docs largos
    "mistral":       ("mistralai/mistral-medium-3.5-128b",               os.getenv("NVIDIA_KEY_MISTRAL_MEDIUM")),
    # Visión
    "llama_vision":  ("meta/llama-3.2-90b-vision-instruct",              os.getenv("NVIDIA_KEY_LLAMA_VISION")),
}

def get_client(model_key: str) -> tuple[OpenAI, str]:
    model_name, api_key = MODELS[model_key]
    return OpenAI(base_url=BASE_URL, api_key=api_key), model_name
```

---

## Guía de elección rápida

| Necesidad | Modelo recomendado |
|-----------|--------------------|
| Chat/agentes rápido | `deepseek_pro` |
| **Chat grounded sobre contexto fijo (RAG corto, datos preconfigurados)** | **`meta/llama-3.3-70b-instruct`** — sigue system prompt al pie, no aluciona si le decís "solo los datos del contexto" |
| Razonamiento paso a paso | `deepseek_flash` (thinking) o `qwen397b` |
| Coding / generación de código / dataframes | `qwen397b` (default del equipo) |
| Análisis de imágenes/tablas/diagramas | `llama_vision` |
| RAG sobre docs largos (>50 páginas) | `mistral` (128K ctx) |
| Coding complejo / arquitectura | `qwen_coder` (480B) |
| Razonamiento + outputs muy largos | `nemotron` (65K out) |

---

## Generar más keys

1. Ir a https://build.nvidia.com
2. Buscar el modelo
3. Click "Generate API Key"
4. Guardar en `~/secrets/nvidia_nim_keys.env`
5. Actualizar esta skill

---

## REGLA DE ORO — Nunca hardcodear keys en código

Las keys NUNCA van hardcodeadas en snippets, skills, ni archivos de código que se suban a un repo.
Siempre usar variables de entorno:

```python
import os
api_key = os.getenv("NVIDIA_API_KEY")  # cargada desde ~/secrets/nvidia_nim_keys.env
```

Las keys reales viven ÚNICAMENTE en `~/secrets/nvidia_nim_keys.env` (permisos 600, fuera del repo).

**Pitfall real:** En la sesión 2026-05-16 se hardcodearon 9 keys en la skill y se pushearon a GitHub.
GitGuardian lo detectó en minutos. Se debió limpiar el historial con git-filter-repo y revocar todas las keys. Costo: 30 minutos de trabajo y keys comprometidas.

---

## Pitfalls

- **Gemma4, Qwen3.5, Mistral Medium necesitan `requests` directo:** Tienen parámetros extra que el SDK de OpenAI puede ignorar. Usar `requests.post` para esos.
- **DeepSeek V4 Flash thinking:** El campo de reasoning puede llamarse `reasoning` o `reasoning_content` según el chunk. Checar ambos con `getattr`.
- **Qwen3-coder 480B:** Latencia alta en primer token. No usar para chat interactivo.
- **Llama Vision:** Imágenes en base64 dentro del payload. Max 512 tokens por defecto en el ejemplo — aumentar para análisis detallados.
- **Free tier:** Rate limit y cuota mensual. Para producción, upgradar o rotar keys.
- **DeepSeek V4 Flash y GLM-5.1 comparten key** en los snippets originales — pueden ser la misma key de NIM que sirve múltiples modelos. Si da 401, generar key nueva desde la página del modelo.
- **Nemotron Omni:** `reasoning_budget` controla cuántos tokens dedica al thinking interno. 16384 es el sweet spot calidad/velocidad.
- **Patrón "NIM primario + Groq fallback":** Para servicios en producción donde el chat no puede caer, hacer try/except sobre NIM y caer a Groq Llama 3.3 70B con la misma key. Ambos sirven `llama-3.3-70b-versatile` (Groq) / `meta/llama-3.3-70b-instruct` (NIM) con interfaces OpenAI-compatibles. Código de referencia: `yolov-orientacion-poc/backend/app/api/v1/historico.py`.
