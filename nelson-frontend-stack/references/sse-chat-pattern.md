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

## ⚠️ Anti-pattern crítico: `async function*` con callback

**Síntoma:** El usuario clickea enviar, el spinner aparece, **nunca llega nada**, no hay error en consola. Backend funciona perfecto (curl directo devuelve tokens). UI queda colgada para siempre.

**Causa real (caso farmacia-poc, 25/06/2026):** la función de la API estaba declarada como **async generator** pero usada con callback + `await`:

```js
// ❌ MAL — el cuerpo NUNCA ejecuta
const api = {
  chat: async function*(message, history, onToken) {   // ← asterisco
    const res = await fetch('/api/chat', {...})
    const reader = res.body.getReader()
    // ...
    onToken(parsed.token)
  }
}

// En el componente:
await api.chat(msg, history, (token) => { ... })   // ← await sobre generator
```

Cuando hacés `await` sobre una función `async function*`, JS te devuelve **el iterator inmediatamente sin ejecutar el cuerpo**. `await` resuelve al instante con el objeto generator. `fetch` jamás se dispara. El callback `onToken` nunca se llama. La UI queda esperando algo que nunca va a venir, sin error ni timeout.

**Fix:** sacar el asterisco. O es generator (y se itera con `for await`), o es async normal (y usa callback). No las dos cosas:

```js
// ✅ BIEN — async function normal con callback
chat: async function(message, history, onToken) {
  const res = await fetch('/api/chat', {...})
  const reader = res.body.getReader()
  // ... loop normal, llamar onToken(token) en cada chunk
}
```

**Cómo detectarlo rápido:**
1. Verificar backend con curl directo — si responde, el bug es 100% frontend.
2. `grep "async function\*" frontend/src/api*` — si aparece y se usa con `await` (no con `for await`), ese es el bug.
3. El bundle minificado puede ocultar el problema (`Dop_OJXz.js` → idéntico tras rebuild si el fuente no cambió).

**Regla:** funciones de SSE con callback son **`async function` normales**, no generators. Los generators son para `for await (const chunk of api.chat(...))`, otra arquitectura entera.

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
