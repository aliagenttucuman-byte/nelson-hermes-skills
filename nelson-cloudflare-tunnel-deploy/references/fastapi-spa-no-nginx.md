# FastAPI como servidor SPA (sin nginx, sin Docker) — Patrón PoC

Alternativa al patrón nginx+Docker para PoCs rápidas donde el backend FastAPI
sirve directamente el `dist/` del frontend React. Un solo proceso, un solo puerto.

## Cuándo usar
- PoC que necesita desplegarse rápido sin Docker
- Demo interna o para stakeholders donde no importa la arquitectura de producción
- El backend ya corre en el servidor (uvicorn directo, no container)

## Estructura
```
proyecto/
├── backend/
│   ├── main.py           ← sirve /api + SPA fallback
│   ├── routers/
│   └── data/
└── frontend/
    └── dist/             ← buildear antes de levantar backend
        ├── index.html
        └── assets/
```

## main.py — patrón SPA completo

```python
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent
FRONTEND_DIST = BASE_DIR / ".." / "frontend" / "dist"

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# Routers API
app.include_router(api_router, prefix="/api")

# Servir assets estáticos del frontend
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# SPA fallback: cualquier ruta no-API devuelve index.html
@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if (
        response.status_code == 404
        and not path.startswith("/api")
        and not path.startswith("/assets")
        and not path.startswith("/health")
    ):
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file), media_type="text/html")
    return response
```

## VITE_API_URL
Dado que frontend y backend comparten dominio y puerto:
```
# frontend/.env
VITE_API_URL=http://localhost:8030   # en dev
# En producción con tunnel: dejar vacío o usar URL relativa
```

## Secuencia de deploy

```bash
# 1. Build frontend
cd frontend && npm run build

# 2. Levantar backend (que sirve el dist/)
cd ../backend
ANTHROPIC_API_KEY=xxx python3 -m uvicorn main:app --host 0.0.0.0 --port 8030 --reload &

# 3. Tunnel (un solo tunnel al puerto del backend)
cloudflared tunnel --url http://localhost:8030 --protocol http2 2>&1 | tee /tmp/cf_proyecto.log &
sleep 15
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_proyecto.log | head -1
```

## Pitfalls
- El middleware SPA fallback debe ir DESPUÉS de montar `/assets` para no interceptar assets
- Si el frontend usa React Router, todas las rutas del cliente deben pasar por index.html (el fallback lo maneja)
- Para development, el frontend puede correr en :5173 con proxy Vite apuntando al backend en :8030 — el patrón SPA es solo para el build final
- Variables de entorno `VITE_*` se hornean en el build — si cambia la URL del backend hay que re-buildear

## Comparativa con patrón nginx

| Aspecto | FastAPI SPA | nginx + Docker |
|---------|------------|----------------|
| Complejidad | Mínima | Media |
| Proceso | 1 (uvicorn) | 2 (backend + nginx) |
| Config extra | 0 | nginx.conf + Dockerfile |
| Producción | No recomendado | Sí |
| PoC/Demo | ✅ Ideal | Funciona pero overkill |
