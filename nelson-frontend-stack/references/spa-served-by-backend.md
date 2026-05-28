# SPA Servida por Backend

Patrón donde el frontend React se buildea a `dist/` y el backend (FastAPI u otro)
lo sirve como archivos estáticos + catch-all para SPA routing.

## Cuándo usar

- PoC o demo donde no hay nginx ni CDN
- Backend en puerto único (ej: 8030), frontend en `http://localhost:8030`
- Simplificar infra: un solo proceso, un solo puerto

## vite.config.ts

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { host: '0.0.0.0', port: 5173, allowedHosts: true },  // solo dev
  build: { outDir: 'dist' },
})
```

## .env

```
VITE_API_URL=http://localhost:8030
```

## FastAPI — servir dist/ + catch-all

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# ... registrar routers de API primero ...

# Luego montar el frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend/dist")

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=f"{FRONTEND_DIR}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = os.path.join(FRONTEND_DIR, "index.html")
        return FileResponse(index)
```

## Workflow de build

```bash
# 1. En frontend/
npm run build   # genera dist/

# 2. Backend levanta y sirve dist/
uvicorn app.main:app --reload --port 8030

# 3. Acceder a http://localhost:8030 → carga React SPA
# 4. Las llamadas /api/... van al backend directamente
```

## Pitfalls

- Los routers de API deben registrarse ANTES de montar los estáticos
- El catch-all `/{full_path:path}` debe ser la última ruta
- Cambios en el frontend requieren re-build (no hot reload en prod)
- En dev usar `npm run dev` (puerto 5173) con proxy de Vite o CORS en backend
