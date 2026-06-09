---
name: nelson-gemini-live
description: "Gemini Live API — voz + video en tiempo real con latencia ultra baja. WebSocket stateful, barge-in, tool use, 70 idiomas. Casos de uso: inspector de campo ForestAI, agente de voz."
category: equipo-nelson
---

# Gemini Live API — Voz + Video en Tiempo Real

https://github.com/google-gemini/gemini-live-api-examples | Apache 2.0 | 298 stars

## Qué es

API de Google para interacciones multimodales en tiempo real con Gemini. Conexión WebSocket stateful — recibe audio/video/texto en streaming continuo y responde con voz en tiempo real. Latencia comparable a una conversación humana.

## Especificaciones técnicas

| Categoría | Detalle |
|-----------|---------|
| Input | Audio PCM 16-bit, 16kHz, little-endian |
| Input | Imágenes/video JPEG hasta 1FPS |
| Input | Texto |
| Output | Audio PCM 16-bit, 24kHz, little-endian |
| Output | Texto |
| Protocolo | WebSocket stateful (WSS) |

## Features clave

- Barge-in — el usuario interrumpe al modelo en cualquier momento, flujo natural
- Tool use — function calling + Google Search integrado en tiempo real
- Affective dialog — detecta tono del usuario y adapta respuesta
- Audio transcriptions — transcripción automática de input y output
- Proactive audio — control de cuándo responde el modelo
- 70 idiomas — relevante para operaciones LATAM

## Ejemplos disponibles en el repo

| Ejemplo | Stack | Cuándo usar |
|---------|-------|-------------|
| Gen AI SDK Python | Python | Recomendado, más simple |
| Ephemeral tokens + WebSocket raw | JS frontend + Python backend | Control total del protocolo |
| CLI micrófono → voz | Python o Node.js | Prototipo rápido |
| Traducción en tiempo real | Python CLI | Audio en un idioma → respuesta en otro |
| Broadcast multilingüe | Next.js + LiveKit | Producción, múltiples idiomas simultáneos |

## Quick start — Python

```bash
pip install google-genai
export GOOGLE_API_KEY=tu_clave
```

```python
import asyncio
from google import genai

client = genai.Client(api_key="TU_CLAVE")

async def main():
    async with client.aio.live.connect(model="gemini-2.0-flash-live-001") as session:
        await session.send(input="Hola, describí este árbol", end_of_turn=True)
        async for response in session.receive():
            if response.text:
                print(response.text)

asyncio.run(main())
```

## Caso de uso ForestAI — Inspector de campo

El inspector apunta la cámara a un árbol y habla:
"Árbol número 47, copa densa, hojas verdes, sin signos de deterioro visible"

El sistema:
1. Recibe audio en tiempo real → transcribe
2. Recibe frames de video → analiza la copa
3. Llama tool registrar_arbol(id=47, estado="saludable", notas="...") via function calling
4. Confirma por voz: "Árbol 47 registrado. Eucalipto, saludable, confianza 92%"

Sin tocar el celular. Sin tipear. En campo.

## Integración con FastAPI existente (ForestAI)

```python
from fastapi import WebSocket
from google import genai

@app.websocket("/ws/campo")
async def campo_ws(websocket: WebSocket):
    await websocket.accept()
    async with client.aio.live.connect(model="gemini-2.0-flash-live-001") as session:
        while True:
            audio_chunk = await websocket.receive_bytes()
            await session.send(input={"data": audio_chunk, "mime_type": "audio/pcm"})
            async for response in session.receive():
                if response.audio:
                    await websocket.send_bytes(response.audio.data)
```

## Partner integrations relevantes

- LiveKit — WebRTC production-ready, ideal para app mobile de campo
- Pipecat by Daily — pipeline de voz completo, fácil de integrar
- Firebase AI SDK — si se quiere una app mobile nativa

## Aplicaciones en el equipo Nelson

| Proyecto | Caso de uso |
|----------|-------------|
| ForestAI | Inspector de campo — registra árboles por voz + cámara |
| JARVIS | Interfaz de voz alternativa al WhatsApp |
| Meta-orquestador | Agente de voz para reuniones con stakeholders |

## Pitfalls conocidos

- Requiere API key de Google (Google AI Studio — free tier disponible)
- Audio PCM raw — necesita conversión desde WebM/MP3 si viene de browser (usar ffmpeg o AudioWorklet)
- 1FPS para video — no es video fluido, es análisis de frames
- Modelo recomendado: gemini-2.0-flash-live-001 (más rápido, menor latencia)
- WebSocket stateful — si cae la conexión hay que reconectar y reiniciar el contexto

## Próximo paso para ForestAI

Prototipo CLI en Python — simular un inspector de campo que habla y registra árboles. Validar latencia y calidad de transcripción en español antes de invertir en la app mobile.
