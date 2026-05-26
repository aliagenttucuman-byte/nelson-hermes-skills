---
name: nelson-poc-dashboard-ai-chat
description: "PoC dashboard con datos en tiempo real + chat IA enchufado vía NVIDIA NIM. Patrón reutilizable: FastAPI backend con WebSocket, React/Vite frontend, streaming SSE, knowledge base de documentos inyectada al contexto."
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [dashboard, poc, chat, nvidia-nim, fastapi, react, websocket, streaming, knowledge-base]
    related_skills: [nelson-frontend-stack, nelson-llm-generation, nvidia-nim-free-api, nelson-generative-ui]
---

# PoC Dashboard + Chat IA (patrón Nelson)

Patrón probado para construir un dashboard PoC con datos en tiempo real y un asistente IA flotante que tiene acceso a esos datos + knowledge base de documentos.

Usado en: Fleet Optimizer AR (2026-05-22), ForestAI, Agente PM.

**Reference files:**
- `references/fleet-simulation-physics.md` — valores reales de TARA, consumo, cubiertas y vida útil para modelos de camiones AR (reutilizable en cualquier PoC de flota)
- `references/fleet-iot-hardware.md` — stack hardware IoT mínimo para conectar camiones reales: Teltonika FMB920, protocolo J1939, PGN→campo mapping, roadmap de integración, costo por unidad

## Cuándo usar

- Demo para cliente o interno que necesita datos live + consultas en lenguaje natural
- PoC donde el usuario necesita explorar datos sin saber SQL ni dashboards complejos
- Integrar un documento de referencia (manual, spec, metodología) como conocimiento del agente

---

## Estructura del proyecto

```
poc/
├── backend/
│   ├── main.py          ← FastAPI + WebSocket + /api/chat (SSE streaming)
│   ├── requirements.txt
│   └── knowledge/       ← documentos .txt extraídos con pymupdf
└── frontend/
    ├── src/
    │   ├── App.jsx       ← dashboard principal
    │   ├── ChatPanel.jsx ← chat flotante independiente
    │   └── App.css
    └── vite.config.js    ← host: '0.0.0.0' para acceso Tailscale
```

---

## Backend — patrón clave

### WebSocket para datos en tiempo real

```python
@app.websocket("/ws/fleet")
async def ws_fleet(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(get_current_state())
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
```

### Endpoint /api/chat con SSE streaming

```python
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

@app.post("/api/chat")
async def chat(request: ChatRequest):
    fleet_context = build_fleet_context()   # estado actual como string
    kb_section = load_knowledge_base()      # docs inyectados al contexto

    system = f"{SYSTEM_PROMPT}\n\n{fleet_context}\n\n{kb_section}"

    async def stream_tokens():
        response = nvidia_client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "system", "content": system}]
                     + [m.dict() for m in request.messages],
            stream=True,
            max_tokens=1024,
        )
        yield f"data: {json.dumps({'token': ''})}\n\n"
        for chunk in response:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_tokens(), media_type="text/event-stream")
```

### Cargar knowledge base de documentos

```python
# Al inicio del backend — cargar una vez
_KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge")

def load_knowledge_base() -> str:
    parts = []
    if os.path.isdir(_KB_PATH):
        for fname in sorted(os.listdir(_KB_PATH)):
            if fname.endswith(".txt"):
                with open(os.path.join(_KB_PATH, fname), "r") as f:
                    content = f.read()[:8000]  # limitar tokens
                    parts.append(f"=== {fname} ===\n{content}")
    return "\n\n".join(parts)
```

### Extraer PDF a .txt para knowledge base

```bash
python3 -c "
import pymupdf
doc = pymupdf.open('documento.pdf')
text = ''.join(page.get_text() for page in doc)
with open('backend/knowledge/documento.txt', 'w') as f:
    f.write(text)
"
```

---

## Frontend — ChatPanel flotante

### Patrón FAB + panel

- Botón flotante (FAB) fixed bottom-right
- Al hacer click abre el panel de chat
- Panel con: historial de mensajes, sugerencias rápidas, input textarea, botón enviar
- Streaming token a token via SSE

### Conectar al backend dinámicamente (CRÍTICO)

```javascript
// NUNCA hardcodear localhost — no funciona desde otras máquinas
const backendHost = window.location.hostname
const ws = new WebSocket(`ws://${backendHost}:8765/ws/fleet`)
const backendBase = `http://${window.location.hostname}:8765`
```

### Consumir SSE streaming en React

```javascript
const sendMessage = async (text) => {
  setLoading(true)
  const resp = await fetch(`${backendBase}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: [...history, { role: 'user', content: text }] })
  })
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let aiText = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        try {
          const { token } = JSON.parse(line.slice(6))
          aiText += token
          // actualizar mensaje en curso en el estado
        } catch {}
      }
    }
  }
  setLoading(false)
}
```

### vite.config.js — acceso desde red

```javascript
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, host: '0.0.0.0' },
})
```

---

## Modelo NVIDIA recomendado

`meta/llama-3.3-70b-instruct` — rápido, preciso, sin problemas de disponibilidad.

DeepSeek puede estar caído en NVIDIA NIM — siempre tener Llama como fallback.

```python
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/secrets/nvidia_nim_keys.env"))

nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)
```

---

## Simulación física realista (datos de demo creíbles)

Para que el PoC sea convincente, los datos simulados deben tener física real. Ver `references/fleet-simulation-physics.md` para valores de referencia completos.

Patrón clave — consumo dinámico según carga:

```python
# En el worker de simulación (tick cada 30s)
factor_carga = 1 + 0.3 * (truck["peso_carga_kg"] / truck["capacidad_carga_kg"])
consumo_real = truck["consumo_base_l100km"] * factor_carga
km_tick = truck["velocidad"] * 30 / 3600
litros_tick = consumo_real * km_tick / 100
pct_consumido = (litros_tick / truck["tanque_litros"]) * 100
truck["combustible"] = max(0, truck["combustible"] - pct_consumido)
truck["km_total"] += km_tick
truck["cubiertas_km_recorridos"] += km_tick
# Campos derivados para el frontend y el LLM
truck["consumo_actual_l100km"] = round(consumo_real, 1)
truck["autonomia_km"] = round((truck["combustible"] / 100) * truck["tanque_litros"] / consumo_real * 100, 0)
truck["cubiertas_km_restantes"] = round(truck["cubiertas_km_vida"] - truck["cubiertas_km_recorridos"], 0)
truck["vida_util_pct"] = round(truck["km_total"] / truck["vida_util_km"] * 100, 1)
```

Alerta automática de cubiertas críticas:
```python
if truck["cubiertas_km_restantes"] < 5000:
    truck["alerta"] = f"🔴 Cubiertas: {int(truck['cubiertas_km_restantes']):,} km para cambio"
```

---

## Integración de PDF como knowledge base

Flujo: PDF → pymupdf → .txt → inyección al system prompt del LLM.

```python
# Extraer PDF
import pymupdf
doc = pymupdf.open("manual.pdf")
text = "".join(page.get_text() for page in doc)
with open("backend/pm_manual.txt", "w") as f:
    f.write(text)

# Cargar al iniciar el backend (una vez)
_PM_MANUAL_PATH = os.path.join(os.path.dirname(__file__), "pm_manual.txt")
try:
    with open(_PM_MANUAL_PATH, "r", encoding="utf-8") as f:
        PM_MANUAL_CONTENT = f.read()
except Exception:
    PM_MANUAL_CONTENT = ""

# Inyectar al system prompt en cada consulta
pm_section = f"\n\n=== MANUAL DE REFERENCIA ===\n{PM_MANUAL_CONTENT[:8000]}"
system = f"{SYSTEM_PROMPT}\n\n{fleet_context}{pm_section}"
```

Límite recomendado: `[:8000]` chars por documento. Para documentos más grandes usar RAG (`nelson-rag-pipeline`).

---

## Cloudflare Tunnel — Deploy Público del PoC

### Estrategia correcta: UN SOLO PUERTO (FastAPI sirve el frontend)

Cloudflare solo expone una URL. Si el frontend corre en :5173 y el backend en :8765, el WebSocket y los fetch desde el exterior no pueden llegar al backend. La solución es compilar React y servir los archivos estáticos desde FastAPI — un único servicio, un único túnel.

**Paso 1 — URLs dinámicas en el frontend (NUNCA hardcodear puerto)**

```javascript
// WebSocket: detectar https → wss automáticamente
const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
const ws = new WebSocket(`${proto}://${window.location.host}/ws/fleet`)

// REST: rutas relativas, sin puerto
fetch('/api/financiero')
fetch('/api/chat')
```

**Paso 2 — FastAPI sirve el build de React**

```python
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent.parent / "frontend" / "dist"

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback — cualquier ruta devuelve index.html"""
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
```

**Paso 3 — Build del frontend**

```bash
cd poc/frontend && npm run build
# genera dist/ con index.html + assets/
```

**Paso 4 — Lanzar cloudflared apuntando solo al backend**

```bash
pip install aiofiles  # requerido por StaticFiles de FastAPI
pkill -f "cloudflared tunnel" 2>/dev/null
cloudflared tunnel --url http://localhost:8765 --protocol http2 > /tmp/cf_poc.log 2>&1 &
sleep 10 && grep "trycloudflare" /tmp/cf_poc.log | tail -2
# Verificar
curl -s -o /dev/null -w "%{http_code}" https://<url>.trycloudflare.com
```

**Pitfalls:**
- `aiofiles` es necesario para `StaticFiles` de FastAPI — sin él arranca pero falla al servir assets.
- Las rutas `/api/*` y `/ws/*` deben definirse ANTES del mount de StaticFiles o el catch-all `/{full_path}` las intercepta.
- Dos procesos cloudflared generan dos URLs distintas. Siempre `pkill -f cloudflared` antes de relanzar.
- URL efímera — cambia cada vez que el proceso muere. Para URL fija usar Cloudflare Zero Trust con dominio propio.
- WebSocket sobre Cloudflare funciona nativo (soporta WSS) — no requiere configuración extra.
- Verificar URL activa: `grep "trycloudflare" /tmp/cf_poc.log | tail -3`

---

## Pitfalls

### Campos derivados en el context builder para el LLM
El LLM necesita los campos calculados (consumo real, autonomía, cubiertas, vida útil) explícitos en el context string — no puede inferirlos de los datos crudos. Incluirlos en `build_fleet_context()` por cada camión.

### localhost hardcodeado en frontend
Si el frontend usa `ws://localhost:8765` o `http://localhost:8765`, funciona solo en el mismo browser que el servidor. Siempre usar `window.location.hostname` para detectar la IP dinámicamente.

### DeepSeek caído en NVIDIA NIM
`deepseek-ai/deepseek-v4-flash` puede no estar disponible. Fallback: `meta/llama-3.3-70b-instruct`.

### Knowledge base demasiado grande
El manual PM tiene 1588 líneas. Limitar a `[:8000]` chars por documento para no reventar el context window. Para documentos más grandes, considerar RAG con Qdrant (ver `nelson-rag-pipeline`).

### CORS en FastAPI
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Vite hot reload al cambiar ChatPanel.jsx
Vite recarga automáticamente — no hace falta reiniciar el frontend al cambiar el chat.

---

## Sugerencias rápidas en el chat

Diseñar las sugerencias para cubrir los dos ejes del asistente:
- **Datos operativos:** alertas activas, camión más rentable, combustible
- **Marco PM:** matriz de riesgos, KPIs estilo PM, hitos de control semanales

```javascript
const SUGERENCIAS = [
  '¿Qué [entidades] tienen alertas activas?',
  'Armá una matriz de riesgos para [dominio]',
  'Dame un resumen ejecutivo con KPIs estilo PM',
  '¿Qué hitos de control recomendás para esta semana?',
]
```

---

## Checklist de arranque rápido

```bash
# 1. Backend
cd poc/backend
pip install fastapi uvicorn python-multipart openai python-dotenv
python3 -m uvicorn main:app --host 0.0.0.0 --port 8765 &

# 2. Verificar
curl http://localhost:8765/health

# 3. Frontend
cd poc/frontend
npm install
npm run dev &  # escucha en 0.0.0.0:5173

# 4. Acceso desde red
# http://<IP_TAILSCALE>:5173
```
