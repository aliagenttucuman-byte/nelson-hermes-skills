# Patrón: Chat Embebido con Contexto en Tiempo Real

Validado en FleetOptimizer PoC (2026-05-22). Asistente IA flotante que responde
preguntas sobre datos vivos del sistema — sin RAG, solo inyección de contexto en
el system message de cada request.

## Arquitectura

```
[React FAB/Panel] --POST /api/chat--> [FastAPI] --stream--> [NVIDIA NIM Llama 3.3 70B]
                        ^
                  build_context()  ← datos frescos en cada request
```

## Backend mínimo (FastAPI + NVIDIA NIM)

```python
import os, json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from typing import List

app = FastAPI()
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

def build_context() -> str:
    """Snapshot del estado actual — llamar en cada request para datos frescos."""
    # Ejemplo: estado de flota, métricas, DB query, etc.
    return "=== ESTADO ACTUAL ===\n" + json.dumps(get_current_state())

SYSTEM_PROMPT = """Sos JARVIS, asistente del sistema X.
Tenés acceso al estado en tiempo real. Respondé con datos concretos.
Idioma: español argentino. Tono: directo y profesional."""

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    context = build_context()
    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{context}"}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    async def generate():
        try:
            stream = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",  # DeepSeek suele fallar en free tier
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Frontend React — consumir SSE

```jsx
const sendMessage = async (userMsg) => {
  // IMPORTANTE: usar window.location.hostname, nunca 'localhost' hardcodeado
  // Si el frontend se sirve desde IP X, localhost no llega al backend.
  const backendBase = `http://${window.location.hostname}:8765`

  const newHistory = [...messages, { role: 'user', content: userMsg }]
  setMessages([...newHistory, { role: 'assistant', content: '' }])

  const res = await fetch(`${backendBase}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: newHistory }),
  })

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()  // guardar línea incompleta para el próximo chunk

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6)
      if (data === '[DONE]') break
      try {
        const { token, error } = JSON.parse(data)
        if (token) {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              role: 'assistant',
              content: updated[updated.length - 1].content + token,
            }
            return updated
          })
        }
      } catch {}
    }
  }
}
```

## Pitfalls críticos

1. **`localhost` hardcodeado en fetch/WebSocket**: Si el usuario accede desde otra IP,
   `localhost` apunta a su máquina, no al servidor. Siempre usar `window.location.hostname`.

2. **DeepSeek en free tier puede estar caído**: Cambiar a `meta/llama-3.3-70b-instruct`
   como primer fallback — mismo formato OpenAI SDK, validado estable.

3. **Contexto fresco vs cache**: `build_context()` se llama en cada POST, no al arrancar.
   Así los datos siempre reflejan el estado actual sin necesidad de invalidar cache.

4. **Historial completo al backend**: Mandar todos los mensajes anteriores + el nuevo,
   no solo el último. El modelo necesita el contexto de la conversación.

5. **`buffer += lines.pop()`**: Patrón correcto para SSE con chunks que pueden partir
   una línea en dos. Sin esto se pierden tokens al parsear JSON incompleto.

## Modelo de NVIDIA recomendado para chat

`meta/llama-3.3-70b-instruct` — buena calidad en español, streaming estable,
funciona cuando DeepSeek falla. Temperature 0.7, max_tokens 1024 para chat interactivo.
