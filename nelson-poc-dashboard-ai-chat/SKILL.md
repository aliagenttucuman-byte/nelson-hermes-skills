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
- `references/project-view-pattern.md` — patrón genérico ProjectView para vistas dedicadas por iniciativa (ForestAI, Fleet, etc.) en el orchestrator dashboard: config por proyecto, sidebar con secciones, búsqueda en índice PM
- `references/orchestrator-dashboard-roadmap.md` — roadmap y visión del meta-orchestrator dashboard: PM proactivo, valor total del portafolio, RAG con Qdrant, valorización de JARVIS como miembro del equipo
- `references/pm-valuation-override-pattern.md` — patrón PM para valuación por proyecto con prioridad manual/documentada/auto, endpoints y validación E2E
- `references/pm-valuation-pattern.md` — patrón PM no-estático: valuación por proyecto (`documented|auto`), endpoints de refresh/generación y pitfalls de contaminación cruzada
- `references/pm-executive-summary-pattern.md` — patrón para redibujar Resumen PM por proyecto seleccionado, con ponderación económica condicional y mensaje de “No aplica” cuando no hay señal suficiente
- `references/mobile-responsive-playbook.md` — playbook para adaptar dashboard+chat a móvil (drawer, chat popup, grids, validación)

## Cuándo usar

- Demo para cliente o interno que necesita datos live + consultas en lenguaje natural
- PoC donde el usuario necesita explorar datos sin saber SQL ni dashboards complejos
- Integrar un documento de referencia (manual, spec, metodología) como conocimiento del agente
- **Demo en vivo con prospecto (Gino u otro)** — construir la PoC del sector del cliente durante la reunión misma

## Patrón PoC en vivo para sector específico (demo con prospecto)

Cuando Nelson diga "estamos con [cliente], hacé una PoC de [sector]" — ejecutar TODO de una vez:
1. Backend FastAPI en puerto libre (8030+) con datos mock del sector
2. Frontend React+Vite compilado servido desde FastAPI (un solo puerto)
3. Chat IA con FreeLLMAPI :3101 (modelo meta-llama/llama-4-maverick:free) y contexto del sector inyectado
4. Acceso vía Tailscale — dar URL directa sin preguntar

**Datos mock por sector — qué incluir siempre:**
- KPIs calculados relevantes al sector (ventas, márgenes, alertas)
- Entidades principales del negocio (productos/pacientes/vehículos/etc.)
- Alertas visuales (rojo/amarillo/verde) para llamar la atención en demo
- 20-50 registros — suficiente para parecer real, no tanto como para ser lento

**Sugerencias rápidas del chat — diseñar para el sector:**
- Siempre incluir "¿qué hay que atender urgente?" — funciona en cualquier dominio
- 3-4 preguntas que demuestren que el asistente "entiende el negocio"

**Puerto por defecto para PoCs en vivo:** 8030 (libre en ai-server a jun 2026)

**PoC Farmacia (jun 2026) — referencia:**
`/home/server/proyectos/farmacia-poc/` — backend+frontend React+Vite, puerto 8030
KPIs: ventas día, margen bruto, productos bajo stock, por vencer
Módulos demo: stock con alertas, ventas del día, chat IA con contexto farmacéutico
- PoC en vivo con cliente (Gino, Pablo, stakeholder) — construir dashboard + propuesta comercial simultáneamente en la misma sesión

## PoC en vivo con cliente — patrón Gino (jun 2026)

Cuando Nelson dice "estamos con [cliente] y queremos hacer una PoC", lanzar DOS cosas en paralelo con delegate_task:

1. **PoC técnica** — backend FastAPI con datos mock + frontend HTML standalone (si no hay npm) o React+Vite (si hay npm). Puerto libre, 0.0.0.0, acceso Tailscale.
2. **Propuesta Comercial** — formato PM de Pablo (ver nelson-business-plan). Generarla mientras se construye la PoC.

Entregables al finalizar:
- URL de la PoC lista en Tailscale
- Propuesta Comercial enviada por Telegram (no WhatsApp — no soporta MD/PDF)

Patrón de datos mock para farmacia (reutilizable):
- 50 productos: nombre, laboratorio, categoría, stock actual/mínimo, precio compra/venta, vencimiento, ventas 30 días
- 30 ventas del día: hora, producto, cantidad, importe, responsable
- 5 proveedores con deuda y último pedido
- KPIs: ventas día, margen bruto %, bajo stock, por vencer, rotación

Ver referencia: `/home/server/brainstorming/2026-06-12-farmacia-poc-gino/` — PoC farmacia completa con chat IA en :8030.

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

### Mobile-first hardening (obligatorio en demos operativas)

- Sidebar desktop en `md+`; en móvil usar drawer con overlay y cierre por tap externo.

## Patrón: Vista por Proyecto genérica (ProjectView)

Cuando el dashboard tiene múltiples proyectos principales (ej: ForestAI + Fleet), crear un
componente `ProjectView.tsx` genérico parametrizado por `projectKey`. Cada proyecto tiene config
estática (hitos, stack, keywords para match PM, colores) y data dinámica del backend PM.

```tsx
const PROJECTS: Record<string, ProjectConfig> = {
  forestai: { keywords: ['forest', 'forestai', 'mrv'], milestones: [...], color: 'emerald' },
  fleet:    { keywords: ['fleet', 'sitrack', 'flota'], milestones: [...], color: 'indigo' },
}
export function ForestAIPage() { return <ProjectView projectKey="forestai" /> }
export function FleetPage()    { return <ProjectView projectKey="fleet" />    }
```

Match PM por keywords fuzzy:
```tsx
const match = allProjects.find((p) =>
  cfg.keywords.some((kw) => p.name.toLowerCase().includes(kw))
)
```

## Patrón: Sidebar con secciones (dividers)

Usar array mixto con entradas `{ divider: true, label: 'Sección' }` intercaladas entre rutas:

```tsx
const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { divider: true, label: 'Proyectos' },
  { to: '/forestai', icon: TreePine, label: 'ForestAI' },
  { to: '/fleet',    icon: Truck,    label: 'Fleet Optimizer' },
  { divider: true, label: 'Gestión' },
  { to: '/pm', icon: KanbanSquare, label: 'Resumen PM' },
]

// En el render:
{nav.map((item, idx) => {
  if ('divider' in item) return <div key={idx} className="pt-3 pb-1 px-3">
    <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest">{item.label}</p>
  </div>
  const { to, icon: Icon, label } = item as NavItem
  return <NavLink key={to} to={to} ...>{label}</NavLink>
})}
```
- Top bar móvil con acciones primarias (menú + chat) para evitar FAB superpuesto.
- Chat: desktop flotante, móvil en panel casi fullscreen con insets seguros.
- Espaciado base: `p-3 md:p-6`.
- Grillas base: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` para KPIs/cards.
- Si el chat abre layout equivocado, separar ruta popup (`/chat-popup`) del layout principal.

Ver detalle y checklist en `references/mobile-responsive-playbook.md`.

---

## Modelo NVIDIA recomendado

`meta/llama-3.3-70b-instruct` — rápido, preciso, sin problemas de disponibilidad.

DeepSeek puede estar caído en NVIDIA NIM — siempre tener Llama como fallback.

## PITFALL — Proceso viejo sigue en puerto aunque se lanzó uno nuevo

Si hay dos intentos de levantar el mismo servicio (ej: background process + retry),
el segundo falla silenciosamente y el proceso viejo (con config incorrecta) sigue activo.

**Diagnóstico:**
```bash
ss -tlnp | grep <puerto>    # ver qué PID está escuchando
fuser <puerto>/tcp           # PID directo
```

**Fix — matar el proceso específico:**
```bash
kill -9 <pid_viejo>         # NO usar pkill -f uvicorn genérico (mata otros servicios)
```

## FreeLLMAPI — modelos disponibles (verificar antes de hardcodear)

Antes de hardcodear un modelo en el backend, verificar que existe:
```bash
curl -s http://localhost:3101/v1/models \
  -H 'Authorization: Bearer freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d' \
  | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]"
```

Modelos confiables verificados (jun 2026): `deepseek-ai/deepseek-v4-flash`, `auto`.
Modelos que NO existen en FreeLLMAPI: `meta-llama/llama-4-maverick:free` (da 400 model_not_found).

## PITFALL — modelo no encontrado en FreeLLMAPI

Síntoma: el chat devuelve `{"error": "Model 'X' is not in the catalog"}` via SSE.
Fix: cambiar el modelo en `main.py` a uno de la lista verificada y reiniciar el proceso.

⚠️ Para reiniciar limpio cuando el puerto está ocupado por proceso viejo:
```bash
# Identificar PID y matar
fuser 8030/tcp  # → PID
kill -9 <PID>
sleep 2
# Relanzar
cd /home/server/proyectos/farmacia-poc && python3 -m uvicorn main:app --host 0.0.0.0 --port 8030 > /tmp/farmacia_backend.log 2>&1 &
```
`pkill -f uvicorn` puede no funcionar si hay múltiples instancias — usar `fuser` + `kill -9 PID` específico.

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

## Override Manual de Valuación PM (patrón 2026-05)

Para dashboards PM donde se necesita fijar una valuación de proyecto sin que se pise con recálculos automáticos:

### Backend — endpoints de override

```python
class ProjectValuationOverrideRequest(BaseModel):
    project_id: str
    valuation: Optional[dict] = None

def _load_pm_valuation_overrides() -> dict:
    cache = _load_pm_cache()
    overrides = cache.get("valuation_overrides")
    return overrides if isinstance(overrides, dict) else {}

def _save_pm_valuation_overrides(overrides: dict):
    cache = _load_pm_cache()
    cache["valuation_overrides"] = overrides if isinstance(overrides, dict) else {}
    _save_pm_cache(cache)

@app.post("/pm/projects/valuation/override/set")
def pm_project_set_valuation_override(req: ProjectValuationOverrideRequest, limit: int = 120):
    # ...busca el proyecto, fija mode="manual", guarda en overrides...

@app.post("/pm/projects/valuation/override/clear")
def pm_project_clear_valuation_override(req: ProjectValuationRequest):
    # ...elimina el override, el proyecto vuelve a documentado/auto...
```

**Prioridad de modos aplicada en /pm/instances:**
1. `manual` — override fijado por Tony, no se pisa nunca
2. `documented` — extraído de archivos Charter/Estimación del proyecto
3. `auto` — generado por JARVIS con señales técnicas del repo

### Frontend — hooks y botones

```typescript
// Hooks necesarios
const setOverrideMutation = useSetProjectValuationOverride(120)
const clearOverrideMutation = useClearProjectValuationOverride()

// Botones en el selector de proyectos
<button onClick={() => setOverrideMutation.mutate({ projectId: selected.id, valuation: valuation })}>
  Fijar valuación manual
</button>
<button disabled={!isManualOverride} onClick={() => clearOverrideMutation.mutate(selected.id)}>
  Quitar override manual
</button>
```

**isManualOverride** se deriva de `valuation?.mode === 'manual'` — botón "quitar" solo activo si hay override.

### Pitfall: los overrides sobreviven al reindex
El dict `valuation_overrides` se persiste dentro del cache JSON junto con los datos de proyectos. Al hacer `force_refresh=True`, el override se recarga del cache antes de procesar — no se pierde. Si se quiere resetear todo, usar el endpoint `/override/clear` por proyecto.

---

## Patrón: Override manual de valuación PM

Cuando el usuario quiere fijar una valuación para un proyecto sin que se pise con recálculos automáticos:

### Backend (FastAPI + SQLite cache)

```python
# Tres modos de valuación
# - "documented": extraída de Charter/Estimación real del proyecto
# - "auto": estimada por JARVIS con señales técnicas (LOC, files, kind, score)
# - "manual": fijada por el usuario — NO se pisa con reindex ni generate

# Endpoints nuevos
POST /pm/projects/valuation/override/set   # fija override, persiste en cache
POST /pm/projects/valuation/override/clear # elimina override, vuelve a auto/documented

# Estructura de overrides en cache JSON
{
  "valuation_overrides": {
    "project:fleet-optimizer": { "mode": "manual", "mvp_total_investment_usd": 5374.0, ... }
  }
}
```

Prioridad en `/pm/instances`:
```python
# 1. Si hay override manual → usarlo con mode="manual"
# 2. Si hay datos documentados → mode="documented"  
# 3. Fallback → mode="auto" (estimación genérica)
override_val = overrides.get(str(item.get("id") or ""))
if isinstance(override_val, dict) and override_val:
    manual = dict(override_val)
    manual["mode"] = "manual"
    it["project_valuation"] = manual
    continue
```

### Frontend (React + React Query)

```typescript
// Hooks nuevos
export function useSetProjectValuationOverride(limit = 120) { ... }
export function useClearProjectValuationOverride() { ... }

// Botones en PM
<button onClick={() => setOverrideMutation.mutate({ projectId: selected.id, valuation })}>
  Fijar valuación manual
</button>
<button onClick={() => clearOverrideMutation.mutate(selected.id)} disabled={!isManualOverride}>
  Quitar override manual
</button>

// Badge de fuente en UI
{valuation.mode === 'documented' ? 'Fuente: Documentada'
 : valuation.mode === 'manual'   ? 'Fuente: Manual (fijada)'
 : 'Fuente: Auto JARVIS'}
```

### Cuándo usar este patrón
- El usuario revisó la valuación y quiere "congelarla" antes de una reunión con un stakeholder
- La valuación auto/documented da números que no reflejan negociación real
- Se quiere fijar un reparto 55/45 concreto sobre un número acordado

---

## Patron Chat con TTS toggle (produccion 2026-05)

Para dashboards internos donde el usuario quiere elegir texto vs texto+audio:

```typescript
// Toggle en el frontend
const [audioMode, setAudioMode] = useState(false)

// Al recibir done del SSE:
if (audioMode) {
  const blob = await fetch('/api/chat/speak', { method: 'POST', body: JSON.stringify({ text: fullText }) }).then(r => r.blob())
  const url = URL.createObjectURL(blob)
  setMessages(prev => prev.map(m => m.id === id ? { ...m, audioUrl: url } : m))
  new Audio(url).play()
}
```

Endpoint TTS en FastAPI:
```python
@app.post("/chat/speak")
async def speak(req: SpeakRequest):
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    proc = await asyncio.create_subprocess_exec(
        "edge-tts", "--voice", "es-AR-TomasNeural",
        "--text", req.text[:2000], "--write-media", tmp.name,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    return FileResponse(tmp.name, media_type="audio/mpeg")
```

Pitfall: el proxy `/api/chat` en vite.config cubre `/api/chat/speak` automaticamente
por ser prefijo — no hace falta entrada separada.

### Proxy configurable para backend alterno (entorno de validación)

Para pruebas sin tocar producción, parametrizar el proxy del frontend:

```ts
const orchestratorTarget = process.env.ORCH_API_URL || 'http://localhost:8744'
const orchestratorWsTarget = process.env.ORCH_WS_URL || 'ws://localhost:8744'
```

Esto permite levantar dashboard contra una instancia temporal (ej. `:8754`) sin romper la instancia systemd de producción.

---

## PM Ejecutivo por proyecto (patrón Nelson/Tony)

Cuando el dashboard incluye una vista "Resumen PM", debe comportarse como una consola operativa y no como un reporte estático.

### Reglas clave
1. El selector de proyecto debe redibujar todo el bloque ejecutivo (resumen, acciones, señales económicas).
2. Si no hay evidencia suficiente para ponderación económica, NO inventar score:
   - devolver `economic_weight.score = null`
   - mostrar `economic_weight.message` explicando "No aplica aún"
3. "Próximos pasos" deben salir del proyecto seleccionado (`next_steps`) y usar fallback solo si no hay pasos explícitos.
4. En UI visible para Nelson usar siempre el término "proyectos" (no "instancias").

### Señales mínimas para habilitar score económico
- Proyecto local: combinación de señales técnicas (backend/frontend/docker/readme/tests).
- GitHub: combinación de señales de tracción/actividad (stars/forks/issues/language/pushed_at).
- Si señales < umbral, usar mensaje explícito en lugar de score.

## PM card pattern — valuación de iniciativa (operativo, no estático)

Cuando el dashboard tiene una vista PM con selector de proyectos, usar este patrón para evitar números vagos o contaminados entre proyectos:

1) Backend: producir `project_valuation` por item en `/pm/instances`
- `mode: documented` si hay evidencia financiera en archivos del proyecto (charter, estimación, benchmark, presupuesto).
- `mode: auto` si no existe evidencia suficiente.
- Nunca mezclar fuentes cross-proyecto al extraer valuación documentada.

2) Prioridad de valuación (durable)
- `manual override` > `documented` > `auto`.
- Si existe override manual, no recalcular ni pisar en refresh/reindex.

3) Endpoints recomendados
- `POST /pm/projects/valuation/generate` → recalcula valuación del proyecto seleccionado.
- `POST /pm/projects/valuation/override/set` → fija valuación manual persistente por `project_id`.
- `POST /pm/projects/valuation/override/clear` → quita override y vuelve a flujo normal.

4) UI PM mínima
- Card "Valuación de la iniciativa" con:
  - Valor actual estimado
  - Escenario base (ingreso bruto anual)
  - Reparto 55/45 del escenario base
  - Fuente visible: Documentada / Auto JARVIS / Manual (fijada)
- Botones:
  - "Actualizar datos del PM"
  - "Generar valuación automática"
  - "Fijar valuación manual"
  - "Quitar override manual"

5) Validación E2E recomendada
- Seleccionar proyecto A y B y verificar que cambia la valuación con la selección.
- Set override en A → `mode=manual` tras refresh.
- Clear override en A → vuelve a `documented` o `auto` según evidencia.

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

### Menú con ruido funcional
En paneles operativos, tabs de bajo valor (ej. vistas internas de Tasks/Router) degradan la UX móvil y la velocidad de operación. Mantener navegación enfocada en misión y resumen PM.

---

## Patrón PM Summary (en lugar de Kanban puro)

Cuando el stakeholder pide una vista de gestión tipo PM ejecutivo (como documento de seguimiento), **no usar Kanban como vista principal**. Mantener Kanban opcional si se necesita operación táctica, pero la pantalla principal de `/pm` debe ser un resumen estructurado.

Estructura recomendada de la vista PM:
1. Encabezado de proyecto: nombre, sponsor, PM, estado, progreso, fechas.
2. Tabla de objetivos y KPIs (ID, objetivo, KPI, owner, estado).
3. Hitos y cronograma (fecha objetivo, estado, nota).
4. Riesgos y mitigación (impacto, probabilidad, acción).
5. Resumen económico (plan vs actual vs desvío).
6. Próximas acciones y gobernanza.

Checklist de implementación:
- Renombrar nav de `PM Board` a `Resumen PM` para alinear expectativas.
- Priorizar legibilidad ejecutiva: tablas compactas + status pills.
- Mantener lenguaje de negocio, no términos de implementación interna.
- Validar build final (`npm run build`) antes de exponer demo.

Referencia de layout: `references/pm-summary-structure.md`.

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

---

## Variante: Generative UI con OpenUI Lang (render de componentes React)

Para demos donde el agente no devuelve texto plano sino **componentes React interactivos** (charts, KPIs, tablas) en tiempo real. Útil cuando se quiere impacto visual sin armar un dashboard clásico.

**Instalado en:** `~/jarvis-demo-shell/`

**Cuándo usar esta variante vs. el patrón estándar:**

| Patrón | Cuándo |
|---|---|
| Dashboard + SSE chat (patrón estándar arriba) | Datos siempre visibles, chat como overlay |
| OpenUI Lang (esta variante) | El chat ES la interfaz; el agente decide qué mostrar |

**Límite importante:** OpenUI es **web únicamente**. No renderiza en WhatsApp.

### Estructura del shell OpenUI

```
jarvis-demo-shell/
├── frontend/          ← OpenUI (Next.js) — NUNCA cambia entre proyectos
│   ├── src/app/api/chat/route.ts   ← llama Groq SDK + consulta system prompt
│   └── src/app/layout.tsx          ← incluye polyfill crypto.randomUUID
└── backend/           ← FastAPI Python — cambia por proyecto
    ├── main.py
    ├── routers/chat.py
    └── tools/
        ├── registry.py   ← registro dinámico (ver templates/generative-ui-registry.py)
        ├── demo.py        ← proyecto por defecto
        └── energia.py     ← ejemplo: datos energía
```

### Cómo levantar

```bash
# Backend (evitar 8000/8001/8002 — ocupados por otros servicios)
cd ~/jarvis-demo-shell/backend
python3 -m uvicorn main:app --reload --port 8765 --env-file .env

# Frontend
cd ~/jarvis-demo-shell/frontend
PORT=3789 npm run dev
```

Acceso Tailscale: `http://100.110.8.13:3789`

### Patrón clave del route.ts (OpenUI)

El frontend llama **directamente al SDK de OpenAI** (baseURL=Groq) y solo consulta el backend para el system prompt:

```typescript
const client = new OpenAI({ apiKey: process.env.GROQ_API_KEY, baseURL: "https://api.groq.com/openai/v1" });
const res = await fetch(`${BACKEND_URL}/api/system-prompt`);
const { systemPrompt } = await res.json();
const response = await client.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [{ role: "system", content: systemPrompt }, ...messages],
  stream: true,
});
return new Response(response.toReadableStream(), { ... });
```

**Por qué:** El parser de OpenUI espera el formato del SDK (no SSE crudo). Si se hace proxy al backend que reenvía bytes SSE con prefijo `data:`, el JSON.parse explota.

### OpenUI Lang — componentes válidos (nombres exactos)

`BarChart`, `HorizontalBarChart`, `LineChart`, `AreaChart`, `PieChart`, `RadialChart`, `RadarChart`, `SingleStackedBarChart`, `Series`, `Table`, `Col`, `Card`, `CardHeader`, `Stack`, `Tabs`, `TabItem`, `TextContent`, `TextCallout`, `MarkDownRenderer`

Cualquier otro nombre (ej: `chart`, `kpi`, `tabla`) causa `unknown-component` silencioso — el usuario no ve nada.

### Pitfalls OpenUI

- `crypto.randomUUID` falla en HTTP con IP externa → agregar polyfill en `layout.tsx`
- SSE crudo rompe el parser → usar `response.toReadableStream()` del SDK, nunca proxy de bytes
- `npx @openuidev/cli@latest create` genera `route.ts` con `model: "gpt-5.2"` hardcodeado → reemplazar
- La variable `ACTIVE_PROJECT` en `.env` queda obsoleta con el registro dinámico — todos los proyectos se cargan siempre

### Agregar un proyecto nuevo

1. Crear `backend/tools/mi_proyecto.py` con `@register` — ver `templates/generative-ui-tool.py`
2. El registry lo carga automáticamente al reiniciar (hot reload en dev)
3. El frontend no se toca nunca
