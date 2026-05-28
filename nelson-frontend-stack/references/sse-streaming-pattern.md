# SSE Streaming Pattern — React + FastAPI

## Backend (FastAPI)

```python
from fastapi.responses import StreamingResponse
import asyncio, json

@app.post("/chat")
async def chat(req: ChatRequest):
    async def stream():
        proc = await asyncio.create_subprocess_exec(
            "/ruta/absoluta/al/binario", "-z", prompt,  # RUTA ABSOLUTA bajo systemd
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

## Frontend (React) — fetch nativo, NO Axios

```tsx
const res = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: text, history }),
})

if (!res.ok) throw new Error(`HTTP ${res.status}`)

const reader  = res.body!.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  const lines = decoder.decode(value).split('\n')
  for (const line of lines) {
    if (!line.startsWith('data: ')) continue
    try {
      const parsed = JSON.parse(line.slice(6))
      if (parsed.chunk) {
        // actualizar estado con chunk incremental
        setContent(prev => prev + parsed.chunk)
      }
      if (parsed.done) {
        // finalizar con el texto completo
        setContent(parsed.full)
      }
    } catch { /* ignorar lineas mal formadas */ }
  }
}
```

## Proxy Vite para SSE

```ts
// vite.config.ts — funciona bien con SSE sin config extra
'/api/chat': {
  target: 'http://localhost:8744',
  rewrite: p => p.replace('/api/chat', '/chat'),
  changeOrigin: true,
  // NO agregar ws: true — eso es solo para WebSocket
}
```

## Pitfall: SSE devuelve 200 vacio

Si el endpoint responde 200 pero no llegan chunks:
1. Verificar que el subprocess usa ruta absoluta (PATH incompleto bajo systemd)
2. Verificar que stderr no esta tragando el error: cambiar DEVNULL a PIPE temporalmente
3. Testear el binario con `sudo -u server /ruta/al/binario` para confirmar que funciona

## Toggle audio con TTS

Patron para respuesta con audio opcional:

```tsx
const [audioMode, setAudioMode] = useState(false)

// Al recibir done:
if (audioMode) {
  const audioUrl = await fetchAudio(fullText)  // POST /api/chat/speak
  if (audioUrl) new Audio(audioUrl).play()
}
```
