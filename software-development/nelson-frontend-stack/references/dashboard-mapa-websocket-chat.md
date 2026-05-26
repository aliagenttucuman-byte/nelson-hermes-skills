# Template: Dashboard React con Mapa + WebSocket + Chat IA

Estructura base validada en FleetOptimizer PoC (2026-05-22).
Dark theme, Leaflet + WebSocket en tiempo real + panel chat NVIDIA NIM.

## Stack

- React 18 + Vite
- `react-leaflet` + `leaflet` (mapa OpenStreetMap)
- `recharts` (gráficos)
- `lucide-react` (iconos)
- WebSocket nativo para datos live
- Fetch SSE para chat streaming

## Fix Leaflet icons (obligatorio con Vite)

```js
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})
```

Sin esto los marcadores no se renderizan (imágenes 404).

## WebSocket con reconexión automática

```jsx
const wsRef = useRef(null)

useEffect(() => {
  const connect = () => {
    // CRÍTICO: usar window.location.hostname, no 'localhost'
    const ws = new WebSocket(`ws://${window.location.hostname}:8765/ws/data`)
    wsRef.current = ws
    ws.onmessage = (e) => setData(JSON.parse(e.data))
    ws.onclose = () => setTimeout(connect, 2000)  // reconexión automática
  }
  connect()
  return () => wsRef.current?.close()
}, [])
```

## Marcadores dinámicos por estado (Leaflet divIcon)

```js
const ICONS = {
  active: L.divIcon({
    html: `<div style="background:#22c55e;width:28px;height:28px;border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);font-size:14px;">🚛</div>`,
    className: '', iconSize: [28, 28], iconAnchor: [14, 14],
  }),
  stopped: L.divIcon({
    html: `<div style="background:#ef4444;width:28px;height:28px;border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                border:2px solid white;font-size:14px;">🚛</div>`,
    className: '', iconSize: [28, 28], iconAnchor: [14, 14],
  }),
}
```

## Backend FastAPI — WebSocket que hace push cada N segundos

```python
@app.websocket("/ws/data")
async def data_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = json.dumps(get_current_state(), default=str)
            await websocket.send_text(payload)
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        pass
```

## Instalación

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install leaflet react-leaflet recharts lucide-react
```

## Pitfalls

- `window.location.hostname` en todos los fetch/WebSocket — nunca `localhost` hardcodeado
- Leaflet icons fix es obligatorio con Vite (ver arriba)
- `z-index: 1` en `.leaflet-container` para que no tape los modales/panels flotantes
- El panel chat flotante necesita `z-index: 1000` para estar encima del mapa
