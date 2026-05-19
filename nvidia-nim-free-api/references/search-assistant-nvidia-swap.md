# Search Assistant — Swap Ollama → NVIDIA Mistral

Sesión 2026-05-16. El AI Search Assistant corría con `qwen2.5:3b` local via Ollama.
Se swapió el LLM a Mistral Medium 3.5 128B de NVIDIA NIM sin tocar el resto del código.

## Resultado
- Latencia: ~7-12s por query (aceptable para I+D+I)
- Calidad de respuesta: notablemente superior al modelo 3B local
- Fuentes citadas correctamente con datos reales (INDEC, Infobae, etc.)
- Cero cambio de infraestructura: solo cambió el cliente OpenAI

## Fragmento clave (main_nvidia.py)

```python
from openai import OpenAI

nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)
MODEL = "mistralai/mistral-medium-3.5-128b"

response = nvidia_client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "Sos un asistente..."},
        {"role": "user", "content": f"Pregunta: {query}\n\nFuentes:\n{context}"}
    ],
    temperature=0.6,
    max_tokens=1024,
)
answer = response.choices[0].message.content
```

## Patrón general: swap drop-in de Ollama a NVIDIA

1. Cambiar `from ollama import ...` → `from openai import OpenAI`
2. Instanciar cliente con `base_url=NVIDIA_BASE_URL` y key de `~/secrets/nvidia_nim_keys.env`
3. Cambiar `ollama.chat(model=..., messages=...)` → `client.chat.completions.create(...)`
4. El campo de respuesta pasa de `response["message"]["content"]` → `response.choices[0].message.content`

Archivo resultante: `~/brainstorming/2026-05-16-ai-search-assistant/backend/main_nvidia.py`
