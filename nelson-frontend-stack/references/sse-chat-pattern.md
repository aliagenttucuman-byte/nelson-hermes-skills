# Patron SSE Chat con streaming en React

## Backend (FastAPI)

```python
from fastapi.responses import StreamingResponse
import asyncio, json

@app.post("/chat")
async def chat(req: ChatRequest):
    async def stream():
        proc = await asyncio.create_subprocess_exec(
            "hermes", "-z", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        full = ""
        async for chunk in proc.stdout:
            text = chunk.decode("utf-8", errors="replace")
            full += text
            yield f"data: {json.dumps({'chunk': text})}\n\n"
        await proc.wait()
        yield f"data: {json.dumps({'done': True, 'full': full})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
```

**Pitfall:** Usar `asyncio.create_subprocess_exec`, NO `subprocess.run` (bloquea el event loop).

## Frontend (React + fetch nativo)

```tsx
const send = async () => {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text, history }),
  })

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const raw = decoder.decode(value)
    const lines = raw.split('\n')

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const parsed = JSON.parse(line.slice(6))
        if (parsed.chunk) {
          // actualizar estado con el chunk parcial
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, content: accumulated + parsed.chunk }
              : m
          ))
        }
        if (parsed.done) {
          // mensaje completo
        }
      } catch { /* ignorar lineas mal formadas */ }
    }
  }
}
```

**Por que fetch y no Axios:** Axios no soporta streaming nativo. Para SSE, usar siempre `fetch` + `response.body.getReader()`.

## Proxy Vite para SSE

```ts
// vite.config.ts
'/api/chat': {
  target: 'http://localhost:8744',
  rewrite: p => p.replace('/api/chat', '/chat'),
  changeOrigin: true
  // No agregar headers de buffering — Vite pasa el stream tal cual
}
```

## UX del chat

- Burbujas: usuario derecha (indigo), asistente izquierda (ambar/oro para JARVIS)
- Estado `loading` con spinner mientras llega el primer chunk
- Scroll automatico con `useRef` + `scrollIntoView({ behavior: 'smooth' })`
- Enter para enviar, Shift+Enter para nueva linea
- Deshabilitar input mientras `busy === true`
- Mensaje de bienvenida hardcodeado como primer mensaje del estado inicial
