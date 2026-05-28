# Chat JARVIS en Dashboard — implementación 2026-05-26

## Qué se construyó

Chat interactivo con JARVIS dentro del dashboard del meta-orquestador.
Endpoint `/chat` (SSE streaming) + endpoint `/chat/speak` (TTS edge-tts).
Toggle de audio en el frontend (texto solo vs texto + audio).

---

## Backend — main.py (:8744)

### Endpoint `/chat` — SSE streaming

```python
@app.post("/chat")
async def chat(req: ChatRequest):
    # Construye prompt con historial (últimos 10 msgs)
    # Llama a: hermes -z <prompt>
    # Devuelve StreamingResponse con text/event-stream
    # Eventos: {"chunk": "..."} y {"done": True, "full": "..."}
```

**Pitfall:** `hermes -z` es modo oneshot — no mantiene sesión propia.
El historial se pasa manualmenteen el prompt como texto plano.
Límite: últimos 10 mensajes para no inflar el prompt.

### Endpoint `/chat/speak` — TTS

```python
@app.post("/chat/speak")
async def speak(req: SpeakRequest):
    # Voz: es-AR-TomasNeural (JARVIS en castellano)
    # Usa edge-tts --write-media <tmpfile.mp3>
    # Devuelve FileResponse audio/mpeg
```

**Pitfall:** `edge-tts` disponible en `/home/server/.hermes/hermes-agent/venv/bin/edge-tts`.
Verificar con `which edge-tts` antes de asumir que está en PATH global.

**Pitfall:** FileResponse con `background=None` — el archivo tmp no se limpia automáticamente.
Para producción considerar BackgroundTask para cleanup post-envío.

---

## Frontend — Chat.tsx

### Toggle audio
- Botón `Volume2` / `VolumeX` a la izquierda del input
- Estado local `audioMode: boolean`
- Cuando `audioMode=true`: al recibir `done` del SSE, llama a `/api/chat/speak`, crea ObjectURL, reproduce con `new Audio(url).play()`
- Cada mensaje de JARVIS con audio guarda `audioUrl` → botón "reproducir" persistente en la burbuja

### Reproducción
```typescript
const playAudio = (url: string) => {
  if (currentAudio.current) currentAudio.current.pause()
  const audio = new Audio(url)
  currentAudio.current = audio
  audio.play().catch(() => {})
}
```
`currentAudio` ref evita que dos audios se superpongan.

---

## Proxy vite.config.ts

```typescript
'/api/chat': { target: 'http://localhost:8744', rewrite: p => p.replace('/api/chat', '/chat'), changeOrigin: true },
```

Este proxy cubre TANTO `/api/chat` → `/chat` COMO `/api/chat/speak` → `/chat/speak`
porque el rewrite es prefijo. No hace falta una entrada separada para speak.

---

## Navegación

- Ruta: `/chat`
- Sidebar: ícono `MessageSquare` de lucide-react, label "Chat JARVIS"
- Posición: entre Orquestador y Presupuesto
