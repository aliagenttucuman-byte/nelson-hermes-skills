---
name: nelson-cloudflare-tunnel-deploy
description: Deploy de PoCs con un solo túnel Cloudflare (patrón nginx → backend). Más simple, más seguro, sin túnel separado para el backend.
category: software-development
tags: [cloudflare, tunnel, deploy, nginx, frontend, backend, poc, expose]
related_skills: [nelson-project-bootstrap, nelson-frontend-stack, nelson-forest-inventory]
---

# Deploy con Cloudflare Tunnel — Patrón Unificado

> **Trigger:** Cuando Nelson quiera mostrarle una PoC a Pablo o a un stakeholder desde fuera de la red local.

## El Patrón

En lugar de crear **dos túneles** (uno para frontend, otro para backend), usamos **un solo túnel** al puerto del nginx.

El frontend se buildea con `VITE_API_URL=""` (URLs relativas). El nginx proxy internamente las requests `/api/` al backend. El túnel expone solo el nginx.

```
Usuario (celular/PC)
    |
    v
Cloudflare Tunnel → https://XXXX.trycloudflare.com
    |
    v
nginx (:3010 o el puerto que sea)
    |
    +-- /api/*  →  proxy_pass a backend (:8000)
    +-- /*      →  serve frontend static files
```

**Ventajas:**
- Un solo túnel que administrar
- El backend queda completamente interno — no expuesto a internet
- Más simple, menos puntos de fallo
- `VITE_API_URL` vacío → URLs relativas → el navegador resuelve contra el mismo dominio

## Docker Compose (Patrón Estándar)

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      LOG_LEVEL: INFO
    # No expuesto al exterior — solo dentro de la red Docker

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: ""           # ← STRING VACÍO = URLs relativas
    ports:
      - "3010:80"
    depends_on:
      - backend
    # nginx proxy interno:
    #   location /api/ { proxy_pass http://backend:8000/; }
    #   location / { try_files $uri $uri/ /index.html; }

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  ollama_data:
  qdrant_data:
```

## nginx.conf (Dentro del Contenedor Frontend)

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback — React/Vite router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API al backend (nombre del servicio en docker-compose)
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Frontend Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## Pasos de Deploy

### 1. Build y levantar el stack

```bash
cd ~/brainstorming/YYYY-MM-DD-proyecto
docker compose up -d --build
```

### 2. Verificar que todo funcione localmente

```bash
curl http://localhost:8000/health
curl http://localhost:3010        # Debe servir el frontend
```

### 3. Crear el túnel Cloudflare

```bash
cloudflared tunnel --url http://localhost:3010 --protocol http2 2>&1 | tee /tmp/cf_proyecto.log &
```

### 4. Capturar la URL pública

```bash
sleep 15
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_proyecto.log | head -1
# Resultado: https://abc123.trycloudflare.com
```

### 5. Verificar desde fuera

```bash
curl https://abc123.trycloudflare.com
# Debe mostrar el frontend

curl https://abc123.trycloudflare.com/api/health
# Debe mostrar el health check del backend (vía nginx proxy)
```

## Variante: FastAPI sirve el dist directamente (sin nginx)

Cuando el backend es FastAPI y el frontend es una SPA buildeada, se puede evitar nginx montando el `dist/` como `StaticFiles` y añadiendo un middleware SPA fallback. El tunnel apunta al puerto de FastAPI directamente.

```python
# main.py
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIST = Path(__file__).parent / ".." / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIST)), name="static")

@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)
    if (response.status_code == 404
        and not request.url.path.startswith("/api")
        and not request.url.path.startswith("/assets")):
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index), media_type="text/html")
    return response
```

**Cuándo usarlo:** PoCs simples donde no querés Docker. Un solo proceso, un solo puerto, un solo tunnel.
**Cuándo NO:** producción real, o cuando el frontend necesita nginx para configuración de caché/headers.

**CRÍTICO:** Buildear el frontend con `VITE_API_URL=` (vacío) para que las requests sean URLs relativas.
El browser resuelve `/api/...` contra el mismo dominio del tunnel → funciona sin CORS.

```bash
# Build correcto para este patrón
echo "VITE_API_URL=" > frontend/.env
cd frontend && npm run build
# Verificar que no hay localhost hardcodeado:
grep -o 'localhost' dist/assets/*.js | wc -l  # debe ser 0
```

## Comparativa: Un Túnel vs Dos Túneles

| Aspecto | Un túnel (nginx) | Dos túneles |
|---------|-----------------|-------------|
| Backend expuesto | ❌ No | ✅ Sí (público) |
| Complejidad | Baja | Alta |
| VITE_API_URL | `""` (relativo) | URL pública del backend |
| Orden de deploy | Build → levantar → un túnel | Build → levantar → túnel backend → build frontend → túnel frontend |
| Seguridad | Mejor | Peor |
| Rebuild por URL cambiada | No | Sí (VITE_API_URL se hornea) |

## Diagnostic Rápido Antes de Debuggear el Tunnel

**Regla:** Si el frontend carga pero la app no funciona, verificar el BACKEND primero, no el tunnel.

```bash
# 1. ¿Backend vivo?
curl -sf http://localhost:8000/health && echo "OK" || echo "CAÍDO"

# 2. ¿Frontend vivo?
curl -sf http://localhost:5174 -o /dev/null -w "%{http_code}"

# 3. ¿Tunnel conectado?
grep -E "Registered tunnel|trycloudflare.com" /tmp/cf_*.log | tail -3
```

Si el backend está caído, levantarlo es el fix — el tunnel puede estar perfecto.

```bash
# Levantar backend del orquestador
cd /home/server/nelson/meta-orchestrator
source venv/bin/activate 2>/dev/null || true
python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/orchestrator_backend.log 2>&1 &
sleep 5 && curl -sf http://localhost:8000/health
```

### Tunnel "vivo" pero UI rota — patrón SPA-proxy (un solo puerto)

Cuando un proyecto usa el patrón **un solo puerto con proxy SPA** (ej. Expreso Bisonte: FastAPI/uvicorn en `:9000` + mini-proxy Python en `:9090` que sirve dist + proxyea `/api/*` al backend), un solo túnel apunta al proxy. Síntomas típicos de falla:

- El túnel responde con el HTML del SPA pero las llamadas API devuelven 404 o el HTML mismo.
- El usuario ve la app cargada pero ningún botón funciona.
- Nelson reporta "la URL no funciona" / "está caída" aunque el túnel esté técnicamente vivo.

**Árbol de decisión (ejecutar en este orden):**

```bash
# 1. ¿El cloudflared está vivo y a qué puerto apunta?
ps -ef | grep cloudflared | grep -v grep
# → Buscar la línea: cloudflared tunnel --url http://localhost:PUERTO

# 2. ¿Ese puerto está escuchando?
ss -tlnp | grep PUERTO
#   Si NO aparece → el proceso destino está caído, levantarlo
#   Si aparece → seguir paso 3

# 3. ¿El puerto es el SPA-proxy o el backend real?
#   Si es el SPA-proxy (ej. :9090 con script spa_proxy.py), el proxy redirige /api/* al backend real (otro puerto, ej. :9000).
#   Verificar que el backend real también escucha:
ss -tlnp | grep PUERTO_BACKEND_REAL
#   Si el backend real no escucha → levantarlo, el proxy solo no sirve

# 4. Verificar el prefijo de rutas del backend
curl -s http://localhost:PUERTO_BACKEND/openapi.json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(p) for p in d['paths']]"
#   Pitfall frecuente: las rutas son /api/v1/... no /api/... Si el frontend llama /api/health y el backend expone /api/v1/health,
#   todas las llamadas fallan con 404 (y el SPA-proxy devuelve el HTML del index como fallback → la URL parece "viva pero rota").
```

**Caso real Expreso Bisonte (junio 2026):**
- cloudflared apuntaba a `:9090` (SPA-proxy)
- SPA-proxy proxyeaba `/api/*` a `:9000` (FastAPI backend)
- Backend tenía rutas en `/api/v1/excel/*` no `/api/excel/*`
- Resultado: el browser veía el HTML del SPA, las llamadas a `/api/...` devolvían 404 con fallback al `index.html`, y Nelson reportó "la URL no funciona"
- Fix: confirmar prefijo real con `openapi.json` y ajustar el frontend (o reescribir las rutas)

**Pitfall crítico:** el SPA-proxy hace fallback a `index.html` para cualquier ruta que no sea `/api/*` y no exista como archivo estático. Eso significa que un 404 del backend se "esconde" devolviendo el HTML del frontend — el usuario ve la app pero sin datos. **Siempre probar endpoints API con `curl` directo al backend real, no solo a la URL del tunnel.**

## PITFALL — Cloudflare Quick Tunnel limita uploads a ~100MB

Los quick tunnels (trycloudflare.com sin cuenta) rechazan uploads grandes con un error de red genérico en el browser — el XHR dispara `onerror` en vez de dar un HTTP 413. El backend y nginx pueden estar perfectos.

**Síntoma:** "Error de red al subir archivo" en el frontend, pero `curl` directo al :9020 devuelve 200 OK.

**Diagnóstico:**
```bash
# Verificar que el backend funciona directo (sin tunnel)
curl -X POST http://localhost:9020/api/v1/upload \
  --form "file=@/ruta/al/archivo.tif" \
  -w "\nHTTP %{http_code}\n" --max-time 30 -s | tail -3
# Si devuelve 200 → el problema es Cloudflare, no el stack
```

**Fix:** usar acceso directo por Tailscale — sin límite de tamaño:
```
http://100.110.8.13:9020   ← IP del ai-server en Tailscale
```

**Nota:** La IP Tailscale del ai-server es `100.110.8.13`, NO `100.76.143.33` (esa es la del nelsondev/cliente).

---

## Fix: DNS de Tailscale Bloquea cloudflared

**Síntoma:** `dial tcp: lookup api.trycloudflare.com on 127.0.0.53:53: no such host` — pero `dig api.trycloudflare.com @8.8.8.8` resuelve bien.

**Causa:** El servidor usa el DNS de Tailscale (100.100.100.100) que no resuelve dominios externos. El resolver local (systemd-resolved en 127.0.0.53) depende de Tailscale.

**Fix rápido (sin reiniciar servicios):**

```bash
# 1. Resolver la IP con DNS externo
dig api.trycloudflare.com @8.8.8.8 +short
# → 104.16.231.132

# 2. Agregar al /etc/hosts temporal
echo "srv2026" | sudo -S bash -c 'echo "104.16.231.132 api.trycloudflare.com" >> /etc/hosts'

# 3. Relanzar cloudflared — ahora resuelve
cloudflared tunnel --url http://localhost:5174 > /tmp/cf_orch_dash.log 2>&1 &
```

**Fix permanente (no pierde entre reinicios):**

```bash
# Deshabilitar DNS override de Tailscale
echo "srv2026" | sudo -S tailscale set --accept-dns=false

# Agregar 8.8.8.8 como DNS en la interfaz de red con default route
IFACE=$(ip route show default | awk '{print $5}' | head -1)
echo "srv2026" | sudo -S resolvectl dns $IFACE 8.8.8.8
echo "srv2026" | sudo -S resolvectl default-route $IFACE true
```

**Nota:** Con `--accept-dns=false`, Tailscale MagicDNS sigue funcionando (resolución de otros nodos de la red), pero el DNS global queda en manos de la interfaz de red normal.

## Diagnostic Rápido Antes de Debuggear el Tunnel

**Regla:** Si el frontend carga pero la app no funciona, verificar el BACKEND primero, no el tunnel.

```bash
# 1. ¿Backend vivo?
curl -sf http://localhost:8000/health && echo "OK" || echo "CAÍDO"

# 2. ¿Frontend vivo?
curl -sf http://localhost:5174 -o /dev/null -w "%{http_code}"

# 3. ¿Tunnel conectado?
grep -E "Registered tunnel|trycloudflare.com" /tmp/cf_*.log | tail -3
```

Si el backend está caído, levantarlo es el fix — el tunnel puede estar perfecto.

```bash
# Levantar backend del orquestador
cd /home/server/nelson/meta-orchestrator
source venv/bin/activate 2>/dev/null || true
python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/orchestrator_backend.log 2>&1 &
sleep 5 && curl -sf http://localhost:8000/health
```

### Tunnel "vivo" pero UI rota — patrón SPA-proxy (un solo puerto)

Cuando un proyecto usa el patrón **un solo puerto con proxy SPA** (ej. Expreso Bisonte: FastAPI/uvicorn en `:9000` + mini-proxy Python en `:9090` que sirve dist + proxyea `/api/*` al backend), un solo túnel apunta al proxy. Síntomas típicos de falla:

- El túnel responde con el HTML del SPA pero las llamadas API devuelven 404 o el HTML mismo.
- El usuario ve la app cargada pero ningún botón funciona.
- Nelson reporta "la URL no funciona" / "está caída" aunque el túnel esté técnicamente vivo.

**Árbol de decisión (ejecutar en este orden):**

```bash
# 1. ¿El cloudflared está vivo y a qué puerto apunta?
ps -ef | grep cloudflared | grep -v grep
# → Buscar la línea: cloudflared tunnel --url http://localhost:PUERTO

# 2. ¿Ese puerto está escuchando?
ss -tlnp | grep PUERTO
#   Si NO aparece → el proceso destino está caído, levantarlo
#   Si aparece → seguir paso 3

# 3. ¿El puerto es el SPA-proxy o el backend real?
#   Si es el SPA-proxy (ej. :9090 con script spa_proxy.py), el proxy redirige /api/* al backend real (otro puerto, ej. :9000).
#   Verificar que el backend real también escucha:
ss -tlnp | grep PUERTO_BACKEND_REAL
#   Si el backend real no escucha → levantarlo, el proxy solo no sirve

# 4. Verificar el prefijo de rutas del backend
curl -s http://localhost:PUERTO_BACKEND/openapi.json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(p) for p in d['paths']]"
#   Pitfall frecuente: las rutas son /api/v1/... no /api/... Si el frontend llama /api/health y el backend expone /api/v1/health,
#   todas las llamadas fallan con 404 (y el SPA-proxy devuelve el HTML del index como fallback → la URL parece "viva pero rota").
```

**Caso real Expreso Bisonte (junio 2026):**
- cloudflared apuntaba a `:9090` (SPA-proxy)
- SPA-proxy proxyeaba `/api/*` a `:9000` (FastAPI backend)
- Backend tenía rutas en `/api/v1/excel/*` no `/api/excel/*`
- Resultado: el browser veía el HTML del SPA, las llamadas a `/api/...` devolvían 404 con fallback al `index.html`, y Nelson reportó "la URL no funciona"
- Fix: confirmar prefijo real con `openapi.json` y ajustar el frontend (o reescribir las rutas)

**Pitfall crítico:** el SPA-proxy hace fallback a `index.html` para cualquier ruta que no sea `/api/*` y no exista como archivo estático. Eso significa que un 404 del backend se "esconde" devolviendo el HTML del frontend — el usuario ve la app pero sin datos. **Siempre probar endpoints API con `curl` directo al backend real, no solo a la URL del tunnel.**
## DNS de Tailscale bloqueando Cloudflare Tunnel

Cuando el servidor usa Tailscale y `cloudflared` falla con `no such host` para `api.trycloudflare.com`, el problema es que systemd-resolved usa el DNS de Tailscale (`100.100.100.100`) como default y no resuelve dominios externos.

**Diagnóstico:**
```bash
resolvectl query api.trycloudflare.com  # "Name not found" = problema DNS
dig api.trycloudflare.com @8.8.8.8 +short  # Debe devolver IPs
ip route show default  # Ver qué interfaz tiene la ruta default
```

**Fix permanente en la sesión:**
```bash
# 1. Desactivar DNS override de Tailscale
sudo tailscale set --accept-dns=false

# 2. Agregar 8.8.8.8 a la interfaz con default route (ej: wlo1)
sudo resolvectl dns wlo1 8.8.8.8 192.168.100.1

# 3. Si sigue fallando — workaround con /etc/hosts (temporal)
IP=$(dig api.trycloudflare.com @8.8.8.8 +short | head -1)
echo "$IP api.trycloudflare.com" | sudo tee -a /etc/hosts
```
## Alternativa más estable: Acceder por Tailscale directo sin tunnel

```
http://100.110.8.13:5174   # Dashboard
http://100.110.8.13:8000   # Backend API
```

Tailscale directo es más rápido, sin intermediarios, sin depender de DNS externo, y la URL **nunca cambia** (es la IP Tailscale del nodo). Para servicios **single-user / desarrollo interno / PoC del equipo Nelson**, es la opción preferida. Solo usar Cloudflare Tunnel cuando:
- El destinatario NO está en la red Tailscale (ej: stakeholder externo, demo público)
- Se necesita HTTPS con dominio propio (no IP cruda)
- El servicio debe sobrevivir a que el servidor se desconecte de Tailscale

**Servicios deployados accesibles por Tailscale directo** (ver `nelson-server-services` para el mapa completo):
- ForestAI frontend: http://100.110.8.13:3010
- Fleet Optimizer AR: http://100.110.8.13:8020
- FreeLLMAPI dashboard: http://100.110.8.13:3101
- Meta-Orchestrator: http://100.110.8.13:8744
- JARVIS Demo Shell: http://100.110.8.13:3789

**Patrón de decisión rápido:**
- ¿El usuario es Nelson o alguien en su tailnet? → Tailscale directo
- ¿Es un stakeholder externo? → Cloudflare Tunnel ephemeral (y mandar URL nueva por WhatsApp)
- ¿Necesita HTTPS sin tunnel? → `tailscale serve` o `tailscale funnel`
## Patrón Alternativo A: FastAPI sirve el dist (sin nginx)

Cuando el backend FastAPI ya existe y el frontend se buildea como SPA estática, no hace falta nginx ni Docker. FastAPI puede servir el `dist/` directamente.

```python
# main.py — FastAPI sirve el frontend dist
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIST = Path(__file__).parent / ".." / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)
    if (response.status_code == 404
            and not request.url.path.startswith("/api")
            and not request.url.path.startswith("/assets")):
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index), media_type="text/html")
    return response
```

El túnel apunta directo al puerto del backend (ej. `:8030`). Sin nginx. Sin Docker.

```
Tunnel → :8030 (FastAPI)
            ├── /api/*    → routers
            ├── /assets/* → StaticFiles (dist/assets/)
            └── /*        → SPA fallback → index.html
```

**Requisito crítico:** el frontend DEBE buildear con `VITE_API_URL=""` (string vacío). Ver pitfall #1.

## Patrón Alternativo B: Mini-proxy Python (SPA + backend en un solo puerto)

Para PoCs donde el backend es **Next.js / uvicorn en un puerto distinto al del frontend build**, se puede evitar configurar nginx con un mini-proxy Python de ~80 líneas. Sirve el `dist/` como static + proxyea `/api/*` al backend real. Un solo puerto, un solo túnel.

```python
# spa_proxy.py — junto al dist del frontend
import http.server
import urllib.request
import os

FRONTEND_DIST = "/path/to/frontend/dist"
BACKEND_URL = "http://localhost:9000"   # backend real
PORT = 9090                              # puerto que ve el túnel

class SPAProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIST, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._proxy("GET")
        # SPA fallback: cualquier ruta sin archivo existente -> index.html
        rel = self.path.lstrip("/").split("?")[0]
        if rel and not os.path.exists(os.path.join(FRONTEND_DIST, rel)):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"): return self._proxy("POST")
        self.send_error(404)
    # do_PUT / do_DELETE / do_PATCH / do_OPTIONS análogos

    def _proxy(self, method):
        cl = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(cl) if cl > 0 else None
        req = urllib.request.Request(BACKEND_URL + self.path, data=body, method=method)
        for h, v in self.headers.items():
            if h.lower() not in ("host", "content-length"):
                req.add_header(h, v)
        with urllib.request.urlopen(req, timeout=60) as resp:
            self.send_response(resp.status)
            for h, v in resp.getheaders():
                if h.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(h, v)
            self.end_headers()
            self.wfile.write(resp.read())

with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), SPAProxyHandler) as httpd:
    httpd.serve_forever()
```

**Uso real (Expreso Bisonte, 2026-06-08):**
```bash
# Backend real en :9000
cd /home/server/proyectos/excel-merger-poc/backend
uvicorn app.main:app --host 0.0.0.0 --port 9000 &

# Proxy SPA en :9090 (este script)
python3 spa_proxy.py &

# Túnel al proxy, no al backend
cloudflared tunnel --url http://localhost:9090 > /tmp/cf_expreso.log 2>&1 &
```

```
Tunnel → :9090 (spa_proxy)
            ├── /api/*  →  http://localhost:9000/api/*  (backend real)
            ├── /assets/* → static files
            └── /*        → SPA fallback → index.html
```

**Cuándo usarlo vs el patrón A (FastAPI monta el dist):**
- Usar **B** cuando el backend no es FastAPI (Next.js, Flask, uvicorn separado, o servicio externo) o cuando no querés modificar el código del backend para servir estáticos.
- Usar **A** cuando el backend es FastAPI y podés modificarlo (más limpio, sin proceso extra).

**Cuándo NO usar B:** producción real (sin HTTPS termination, sin caché headers, sin rate limiting). Solo para PoCs.

**Diagnóstico clave cuando B falla:** el proxy NO tiene health endpoint en `/health` (devuelve index.html). Para chequear backend, pegale directo a `:9000`. Para chequear el proxy, mirá los logs del proceso Python.

## Patrón Alternativo: FastAPI sirve el dist directamente (sin nginx)

Cuando el backend FastAPI monta el frontend `dist/` como StaticFiles + SPA fallback, no se necesita nginx. Un solo proceso, un solo puerto, un solo tunnel.

```python
# main.py
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIST = BASE_DIR / ".." / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith("/api"):
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file), media_type="text/html")
    return response
```

Deploy:
```bash
# Build frontend con URL relativa (CRÍTICO)
cd frontend && echo "VITE_API_URL=" > .env && npm run build

# Levantar solo el backend — sirve todo
ANTHROPIC_API_KEY=xxx uvicorn main:app --host 0.0.0.0 --port 8030

# Un solo túnel al backend
cloudflared tunnel --url http://localhost:8030 --protocol http2 2>&1 | tee /tmp/cf_proyecto.log &
```

**Ventaja vs nginx:** Cero archivos extra. Ideal para PoCs rápidas.
**Desventaja:** El SPA fallback por middleware es menos eficiente que nginx `try_files`. Para producción real, usar nginx.

## Patrón Alternativo 2: Python mini-proxy para SPA + API separadas (sin Docker, sin nginx, sin FastAPI-as-server)

Cuando el proyecto tiene **dos procesos independientes** (backend uvicorn en un puerto, frontend Vite preview/dist servido por otro proceso en OTRO puerto) y no querés tocar el código del backend para que sirva el dist, un mini-proxy Python de ~80 líneas resuelve todo.

**Cuándo aplica:**
- El `vite.config.ts` tiene `preview.port` distinto al puerto del backend (caso típico: frontend en :5178, backend en :8000)
- El cliente API del frontend usa `baseURL: '/api/v1'` (URL relativa, sin localhost hardcodeado)
- No querés modificar el backend para servir el dist
- No tenés nginx ni caddy instalado y no querés instalarlos

**El script** (template en `templates/spa_proxy.py`):

```python
"""
Mini-proxy para SPA + API separadas.
Sirve el frontend dist (con SPA fallback) + proxyea /api/* al backend.
Un solo puerto → un solo tunnel.
"""
import http.server, socketserver, urllib.request, os, sys

FRONTEND_DIST = "/ruta/al/frontend/dist"
BACKEND_URL = "http://localhost:9000"  # puerto del backend uvicorn
PORT = 9090  # puerto del proxy (≠ puerto del backend)

class SPAProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIST, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy("GET"); return
        # SPA fallback: si el path no es un archivo del dist, servir index.html
        rel = self.path.lstrip("/").split("?")[0]
        if rel and not os.path.exists(os.path.join(FRONTEND_DIST, rel)):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy("POST"); return
        self.send_error(404)

    # Repetir do_PUT / do_DELETE / do_PATCH igual que do_POST

    def _proxy(self, method):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        target = BACKEND_URL + self.path
        req = urllib.request.Request(target, data=body, method=method)
        for h, v in self.headers.items():
            if h.lower() not in ("host", "content-length"):
                req.add_header(h, v)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                for h, v in resp.headers.items():
                    if h.lower() not in ("transfer-encoding", "content-encoding", "connection"):
                        self.send_header(h, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as e:
            payload = e.read() if e.fp else b""
            self.send_response(e.code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), SPAProxyHandler) as httpd:
        httpd.serve_forever()
```

**Deploy:**

```bash
# 1. Backend (ya corriendo)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9000 &

# 2. Frontend dist ya compilado (NO necesita vite preview corriendo)
ls frontend/dist/index.html  # debe existir

# 3. Mini-proxy en :9090
python3 spa_proxy.py &

# 4. Un solo tunnel al proxy
cloudflared tunnel --url http://localhost:9090 2>&1 | tee /tmp/cf_proyecto.log &
sleep 12
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_proyecto.log | head -1
```

**Verificación end-to-end** (importante porque la URL es efímera):

```bash
URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_proyecto.log | head -1)
IP=$(dig +short $(echo $URL | cut -d/ -f3) @1.1.1.1 | head -1)
curl -s --resolve $(echo $URL | cut -d/ -f3):443:$IP "$URL" -o /dev/null -w "HTTP %{http_code}\n"
curl -s --resolve $(echo $URL | cut -d/ -f3):443:$IP "$URL/api/v1/health"  # o algún endpoint del backend
```

**Ventajas vs FastAPI-sirviendo-dist:**
- Cero cambios al código del backend
- Funciona aunque el backend no sea FastAPI (cualquier HTTP server)
- El script de 80 líneas es trivial de auditar

**Ventajas vs nginx/caddy:**
- Sin instalación adicional
- Sin configuración de proxy_pass, try_files, CORS
- Cero archivos extra en el repo (un solo `spa_proxy.py`)

**Cuándo NO usarlo:**
- Si ya tenés nginx/caddy y podés agregar un config
- Si el backend es FastAPI y podés modificarlo (mejor patrón "Alternativo 1" arriba)
- Producción real con carga (Python http.server no es performante)

## Preferencia de estilo (Nelson): cuando piden "mandame una URL", ejecutar y entregar, NO analizar

**Lección observada el 2026-06-07:** al pedir "mándame una URL" para Expreso Bisonte, JARVIS entró en modo análisis ("¿qué patrón usar? ¿qué archivo leer? ¿qué dependencias tiene?"). Nelson cortó con "No importa, no evalúes nada.. mándale la URL de expresión bisonte".

**Regla para futuras sesiones:**

Cuando Nelson pide **explícitamente** "mandame una URL" / "necesito una URL" / "armame el tunnel":
1. NO comparar opciones
2. NO preguntar "¿qué patrón preferís?"
3. NO evaluar dependencias
4. Elegir el patrón más simple y rápido (típicamente: tunnel al puerto que ya está sirviendo algo)
5. Levantar y entregar la URL en el mismo turno
6. Si el patrón simple no funciona, iterar — pero no abrir el menú de opciones

Si el patrón simple no es viable (puerto no escucha, frontend SPA necesita proxy a backend separado, etc.), **resolvelo internamente sin preguntar**, y al final entregá la URL.

Este principio aplica a TODO pedido que incluya "URL", "tunnel", "exponelo", "armame el deploy" en esta skill y en `nelson-server-services`.

## Pitfall — Cloudflare Quick Tunnel límite de upload (~100MB)

Cloudflare impone un límite de ~100MB en uploads via quick tunnels (sin cuenta). Cuando el archivo supera ese límite, el XHR del browser dispara `onerror` con el mensaje genérico "Error de red" — no hay un 413 ni un mensaje claro. El backend y nginx pueden estar perfectos.

**Diagnóstico:**
```bash
# Verificar que el upload funciona directo (sin tunnel)
curl -X POST http://localhost:PUERTO/api/v1/upload \
  --form "file=@/ruta/al/archivo.tif" \
  -w "\nHTTP %{http_code}\n" --max-time 30 -s | tail -3
# Si da 200 → el problema es Cloudflare, no el backend
```

**Alternativas cuando el archivo supera 100MB:**
1. **Tailscale directo** — `http://IP_TAILSCALE:PUERTO` (sin intermediario, sin límite). Verificar antes que Tailscale esté activo en el cliente: `tailscale status` debe mostrar el nodo del cliente como conectado (no `-` ni `offline`).
2. **Endpoint de carga local** — agregar `GET /api/v1/local-files` que lista TIFs disponibles en el server y `POST /api/v1/load-local` que los copia al UPLOAD_DIR sin pasar por el browser. El usuario selecciona en la UI en vez de subir.
3. **Cuenta Cloudflare con túnel autenticado** — sube el límite pero requiere setup.

**Pitfall Tailscale como fallback:** antes de darle al usuario una IP Tailscale, verificar que su nodo aparece como activo:
```bash
tailscale status | grep "nelsondev\|NOMBRE_CLIENTE"
# ✅ OK: "100.76.143.33  nelsondev  ...  windows  -" con conexión activa
# ❌ Caído: aparece "offline" o "-" como estado
```
Si el cliente está offline, Tailscale no es un fallback válido.

## Tailscale: IP del server vs IP del cliente

La IP de Tailscale del servidor es **100.110.8.13** (ai-server), no 100.76.143.33 (nelsondev/Windows).
Cuando Nelson quiere acceder directo sin tunnel usar `http://100.110.8.13:PUERTO`.
`tailscale ip -4` en el server confirma la IP correcta.

Cuando `tailscale status` muestra el nodo remoto como `-` (sin conexión activa), no significa
que Tailscale esté caído en ese nodo — puede ser que esté conectado pero idle. Confirmar con ping
o simplemente intentar acceder por HTTP.

## Límite de upload en Quick Tunnels (Cloudflare Free)

Cloudflare quick tunnels (trycloudflare.com) tienen un límite efectivo de ~100MB en uploads.
El XHR dispara `onerror` genérico ("Error de red al subir archivo") — no da 413.
El nginx y el backend pueden estar perfectos; el corte lo hace Cloudflare antes.

**Diagnóstico:** probar el upload directo por red local:
```bash
curl -X POST http://localhost:PUERTO/api/v1/upload \
  --form "file=@/ruta/archivo.tif" -w "\nHTTP %{http_code}\n" --max-time 60 -s | tail -3
# Si responde 200 → el problema es Cloudflare, no el stack
```

**Solución preferida:** usar Tailscale directo (sin Cloudflare):
```
http://100.110.8.13:PUERTO   ← IP Tailscale del ai-server
```
Sin límite de tamaño, más rápido, sin intermediarios.

**Ojo con la IP:** la IP Tailscale del AI-SERVER es 100.110.8.13, NO 100.76.143.33 (esa es nelsondev).

---

## PITFALL — Quick Tunnels limitan uploads a ~100MB

Cloudflare free quick tunnels rechazan uploads grandes con un error genérico.
El XHR dispara `onerror` ("Error de red") sin dar HTTP status — no es un 413 visible.

**Síntoma:** archivo de 36-60MB da "Error de red al subir archivo" desde el browser.
El backend y nginx están perfectos — `curl` directo devuelve 200.

**Fix inmediato:** usar acceso directo por Tailscale (sin tunnel):
```
http://IP_TAILSCALE_SERVER:PUERTO
# Ej: http://100.110.8.13:9020
```

**Fix alternativo:** endpoint de carga local — el archivo ya está en el server,
la UI lo selecciona por nombre sin upload. Útil para demos repetidas con los mismos TIFs.

**Verificación:** si `curl --form "file=@archivo.tif" http://localhost:PUERTO/api/upload` 
devuelve 200 pero el browser falla → es Cloudflare limitando el upload, no el backend.

---

## Pitfalls críticos — Servidor estático + Quick Tunnel

### Tunnel al puerto equivocado del Orchestrator (confusión 5180 vs 8744)

El orchestrator tiene **dos puertos activos** y es fuente frecuente de confusión:
- **:8744** = Backend FastAPI (`main.py` uvicorn)
- **:5180** = Vite preview del dashboard frontend (con proxies a 8742/8743/8744 en `vite.config.ts`)

**Síntoma:** El usuario dice "no funciona la URL del orchestrator" y el túnel apunta a :8744. El navegador muestra JSON de API (`{"detail":"Not Found"}`) en vez del dashboard React.

**Fix:** Siempre tunelar el **frontend (5180)**, no el backend (8744). El frontend tiene los proxies:
```ts
// vite.config.ts del dashboard
proxy: {
  '/api/orchestrate': { target: 'http://localhost:8744', ... },
  '/api/chat':        { target: 'http://localhost:8744', ... },
  '/api/tasks':       { target: 'http://localhost:8742', ... },
  '/api/route':       { target: 'http://localhost:8743', ... },
}
```

```bash
# ✅ Correcto
curl -s http://127.0.0.1:5180 | head -3   # Debe devolver HTML del dashboard
cloudflared tunnel --url http://127.0.0.1:5180

# ❌ Incorrecto — devuelve JSON de API, no UI
cloudflared tunnel --url http://127.0.0.1:8744
```

**Verificación rápida:**
```bash
ss -tlnp | grep -E '5180|8744'
# 5180 = node/vite → tunelar aquí
# 8744 = python/uvicorn → no tunelar directo
```

### El servidor debe escuchar en 0.0.0.0, NO en 127.0.0.1
Cloudflare a veces conecta vía IPv6 (`::1`). Si el servidor escucha solo en `127.0.0.1`, Cloudflare falla silenciosamente — el túnel aparece como "registrado" en los logs pero no sirve nada.

```bash
# ❌ Falla con Cloudflare (solo IPv4 loopback)
python3 -m http.server 8031           # escucha en 127.0.0.1 por defecto

# ✅ Correcto
python3 -m http.server 8031 --bind 0.0.0.0
```

### No tunelar al backend directo cuando el frontend tiene proxies en Vite
El orchestrator-dashboard (y cualquier proyecto Vite con `server.proxy`) espera que el browser hable con el frontend, y el frontend reenvía internamente a los backends. Si se crea el túnel apuntando directo al backend (ej. `:8744`), el frontend nunca se sirve y las rutas `/api/*` no existen en el backend puro.

**Síntoma:** `curl https://XXXX.trycloudflare.com/` devuelve `{"detail":"Not Found"}` (respuesta del FastAPI backend, no del frontend). El dashboard no carga.

**Fix:** Tunelar al puerto del Vite preview (donde corre `npx vite preview`), no al backend. Verificar:
```bash
# ¿El frontend responde HTML en el puerto de preview?
curl -s http://127.0.0.1:5174/ | head -5   # debe ser <!doctype html>

# ¿El proxy funciona?
curl -s http://127.0.0.1:5174/api/orchestrate/health  # debe responder JSON del backend
```
Si el primer curl devuelve HTML y el segundo JSON → el proxy está bien, tunelar a :5174.

### Vite preview no está corriendo — se cayó o nunca se levantó
El `vite preview` es un proceso Node que se puede matar, cerrar, o nunca iniciar. El túnel queda apuntando a un puerto vacío.

**Síntoma:** `curl https://XXXX.trycloudflare.com/` timeout o connection refused. Los logs de cloudflared muestran `connection refused`.

**Diagnóstico:**
```bash
ss -tlnp | grep :5174   # ¿Hay algo escuchando?
ps aux | grep "vite preview"  # ¿El proceso existe?
```

**Fix:**
```bash
cd /home/server/nelson/orchestrator-dashboard
npx vite preview --host 0.0.0.0 --port 5174 &
sleep 3
curl -s http://127.0.0.1:5174/ | head -3  # verificar
```
Luego relanzar el túnel apuntando al puerto del preview.
`python3 -m http.server` devuelve HTTP/1.0 — Cloudflare con `--protocol http2` puede tener problemas. Omitir el flag y dejar que cloudflared auto-negocie.

### Quick Tunnels son inestables — nunca son la solución definitiva
Los quick tunnels (sin cuenta) tienen uptime no garantizado, se caen solos y cambian URL en cada restart. Para Nelson:
- **Para mostrar una PoC**: aprovechar un túnel ya activo y estable (Fleet :8020, ForestAI :3010) copiando el HTML al directorio `dist/` que ya sirve ese proceso.
- **Para servir un SPA React**: levantar el backend FastAPI con `StaticFiles` montado — no usar `python http.server` (HTTP/1.0, sin keep-alive).

### Verificar el túnel desde afuera, no desde el servidor
El DNS de Tailscale en el servidor no resuelve dominios `trycloudflare.com`. Usar `dig @1.1.1.1` para verificar:
```bash
# Verificar resolución externa
dig +short nombre.trycloudflare.com @1.1.1.1

# Verificar que el túnel responde (con DNS override)
curl -s --resolve nombre.trycloudflare.com:443:$(dig +short nombre.trycloudflare.com @1.1.1.1 | head -1) \
  https://nombre.trycloudflare.com/ | wc -c
```
Si este comando devuelve bytes, el túnel FUNCIONA aunque el servidor no pueda resolver el dominio.

### No crear múltiples túneles al mismo puerto
Si se re-lanza cloudflared sin matar el anterior, quedan dos procesos apuntando al mismo puerto. El segundo falla o compite. Siempre:
```bash
pkill -f "cloudflared.*PUERTO" && sleep 1
# luego lanzar el nuevo
```

### El SPA React necesita un servidor real, no http.server
`python3 -m http.server` no maneja SPA routing — rutas como `/dashboard` devuelven 404. Para servir el dist de Vite en desarrollo rápido:
```bash
# Opción 1: npx serve (maneja SPA con --single)
npx serve dist/ -p 8031 --single

# Opción 2: FastAPI con StaticFiles (producción)
app.mount("/", StaticFiles(directory="dist", html=True), name="static")
```

### Pitfall — Uploads grandes fallan con ERR_SSL_BAD_RECORD_MAC_ALERT

Archivos >30MB enviados como multipart/form-data por quick tunnel fallan con:
```
ERR_SSL_BAD_RECORD_MAC_ALERT
```
El body se corta en tránsito. Cloudflare free tunnels tienen restricciones no documentadas para uploads grandes.

**Solución:** Usar acceso directo por Tailscale + SPA Proxy local:
```bash
# Levantar spa_proxy.py en un puerto accesible por Tailscale
python3 spa_proxy.py > /tmp/proxy.log 2>&1 &
# Desde Windows (nelsondev): http://100.110.8.13:PUERTO/
```
El spa_proxy.py de Python puro no tiene límite de body y timeout de 600s.

Para ForestAI específicamente: puerto 3011, `python3 /home/server/proyectos/forestai-poc/spa_proxy.py`



1. **VITE_API_URL vacío en el build:** Si se omite el `ARG` en el Dockerfile, Vite usa el default y las requests van a localhost. Siempre incluir `ARG VITE_API_URL=""`.

2. **Servidor de archivos estáticos pisado por backend en el mismo puerto:** Si se levanta un `python3 -m http.server 8030` para servir HTMLs y luego el backend de la PoC también arranca en :8030, el backend mata al servidor de archivos. Usar un puerto diferente para cada servicio (ej: archivos estáticos en :8031, backend en :8030). Verificar antes con `ss -tlnp | grep 8030`.

3. **Quick tunnels con DNS que no propagan inmediatamente:** Los túneles temporales de trycloudflare.com a veces tardan 30-60 segundos en propagar el DNS. Si el curl desde el servidor falla con "Could not resolve host", es el DNS de Tailscale bloqueando resolución externa (pitfall conocido). Verificar con `dig +short NOMBRE.trycloudflare.com @1.1.1.1` — si resuelve una IP, el túnel existe. El browser del usuario (que no usa Tailscale) lo verá correctamente.

4. **VITE_API_URL vacío en el build:** Si se omite el `ARG` en el Dockerfile

2. **VITE_API_URL vacío en el build:**
   Si el `.env` tiene `VITE_API_URL=http://localhost:8030`, Vite lo hornea en el JS. Desde el tunnel, el browser del usuario hace fetch a su propio `localhost` → falla silenciosamente.
    - **Fix `.env`:** `VITE_API_URL=` (vacío, sin valor)
    - **Diagnóstico:** `grep -o '"http://localhost' frontend/dist/assets/index-*.js | wc -l` → si > 0 el valor está horneado, rebuild requerido.
   - **Fix `client.ts`:** el fallback debe ser `|| ''` no `|| 'http://localhost:8030'`
   - **Verificación post-build:** `grep -o 'localhost' frontend/dist/assets/*.js | wc -l` — debe ser 0 o solo hits de librerías internas
   - Si el subagente genera el `.env`, revisarlo antes de hacer `npm run build`
2. **Subagente genera DATA_DIR apuntando mal:** Un pitfall observado cuando subagentes crean routers FastAPI — tienden a poner `Path(__file__).parent.parent.parent / "data"` en vez de la ruta correcta. Siempre verificar con `ls` que `DATA_DIR` resuelve al directorio real antes de levantar.

3. **Trailing slashes en proxy_pass:** `proxy_pass http://backend:8000/;` (con `/` al final) es distinto de `proxy_pass http://backend:8000;`. Con `/`, nginx elimina el prefix `/api/` antes de pasar al backend. Sin `/`, el backend recibe `/api/health` en vez de `/health`.
3. **CORS no necesario:** Con este patrón, frontend y backend comparten el mismo dominio. No hace falta configurar CORS. Si antes tenías CORS y ahora no funciona, revisá que el backend no esté rechazando requests del mismo origen.
4. **cloudflared no está instalado:** `sudo apt install cloudflared` o descargar binario desde https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
5. **nginx no sirve el frontend correctamente:** Asegurarse de que `try_files $uri $uri/ /index.html;` esté presente. Sin esto, las rutas de React Router (ej. `/dashboard`) devuelven 404.
6. **Logs de cloudflared:**
7. **Tunnel caído en modo dev:** Si Nelson reporta que la UI no responde, el proceso Vite puede seguir vivo pero el tunnel se cayó. Verificar con `ps aux | grep vite` y relanzar. Siempre mandar la URL nueva por WhatsApp — cambia en cada reinicio. Si no funciona, revisar `/tmp/cf_proyecto.log`. Errores comunes: puerto ocupado, cloudflared no encontrado, rate limit de Cloudflare.
8. **DNS systemd-resolved no resuelve `api.trycloudflare.com` (servidores con Tailscale):** El DNS de Tailscale (100.100.100.100) puede capturar todo el tráfico DNS pero no resolver dominios externos. Síntoma: `failed to request quick Tunnel: dial tcp: lookup api.trycloudflare.com on 127.0.0.53:53: no such host`. Fix inmediato vía `/etc/hosts`:
   ```bash
   # Verificar que 8.8.8.8 sí lo resuelve
   dig api.trycloudflare.com @8.8.8.8 +short   # → 104.16.231.132
   
   # Agregar al /etc/hosts del servidor
   echo "104.16.231.132 api.trycloudflare.com" | sudo tee -a /etc/hosts
   ```
   Fix más durable (desactivar DNS override de Tailscale):
   ```bash
   sudo tailscale set --accept-dns=false
   # O forzar DNS en la interfaz con default route (ver con: ip route show default)
   sudo resolvectl dns wlo1 8.8.8.8 192.168.100.1
   ```
   ⚠️ La IP en /etc/hosts puede quedar stale — si vuelve a fallar días después, regenerar con `dig @8.8.8.8 +short`.

## Verificar que el tunnel realmente sigue vivo — no confiar en la URL en memoria

Antes de pasar una URL a Nelson, SIEMPRE verificar que el proceso cloudflared esté corriendo Y que la URL responda:

```bash
# 1. Ver si el proceso existe
ps aux | grep cloudflared | grep -v grep

# 2. Ver la URL actual del log (puede haber cambiado)
grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf_PROYECTO.log | tail -1

# 3. Verificar que responde desde afuera (el servidor no puede resolver trycloudflare.com por Tailscale)
curl -sk --resolve DOMINIO.trycloudflare.com:443:$(dig +short DOMINIO.trycloudflare.com @1.1.1.1 | head -1) \
  https://DOMINIO.trycloudflare.com/ -o /dev/null -w '%{http_code}'
# → 200 = funciona | 000 = tunnel caído o URL expirada
```

> **Pitfall real:** Un tunnel puede tener una URL en el log de una sesión anterior, con el proceso muerto. El log persiste, el proceso no. Siempre verificar `ps aux` primero.
> Si el `http_code` es `000`, el tunnel está caído aunque el proceso figure en ps — relanzar.

## Tunnels caídos — diagnóstico rápido con curl externo

Antes de cualquier investigación, verificar si el tunnel responde desde afuera:

```bash
# Si DNS local no resuelve (Tailscale), resolver con 1.1.1.1 y forzar via --resolve
IP=$(dig +short NOMBRE.trycloudflare.com @1.1.1.1 | head -1)
curl -sk --resolve NOMBRE.trycloudflare.com:443:$IP https://NOMBRE.trycloudflare.com/ -o /dev/null -w '%{http_code}'
# 200 → tunnel vivo. 000 → tunnel caído → regenerar.
```

**Síntoma de tunnel caído:** el log muestra `connection with edge closed` y `ERR` repetidos, aunque eventualmente intente reconectar. Si lleva horas así, la URL ya no responde — regenerar.

**Causa común:** los quick tunnels (trycloudflare.com) tienen uptime no garantizado. Se caen solos, especialmente tras varias horas. No son un error del servidor local — el backend/frontend puede estar perfecto.

**Rutina de verificación antes de pasar URL a Nelson:**
```bash
# 1. Verificar que el servicio local responde
curl -s -o /dev/null -w '%{http_code}' http://localhost:PUERTO/health

# 2. Verificar que el tunnel responde desde afuera (con DNS override)
IP=$(dig +short NOMBRE.trycloudflare.com @1.1.1.1 | head -1)
curl -sk --resolve NOMBRE.trycloudflare.com:443:$IP https://NOMBRE.trycloudflare.com/ -o /dev/null -w '%{http_code}'
# Solo pasar la URL si ambos dan 200
```

## Tunnels que se caen solos (sin reinicio del proceso)

Los quick tunnels de trycloudflare.com pueden caerse incluso cuando `cloudflared` sigue corriendo.
El proceso aparece en `ps aux` y el log dice `Registered tunnel connection`, pero `curl` devuelve `000`.

**Diagnóstico definitivo:**
```bash
# 1. Verificar que el proceso existe
ps aux | grep cloudflared | grep -v grep

# 2. Leer URL actual del log
grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf_PROYECTO.log | tail -1

# 3. Probar desde afuera (no usar curl directo — DNS Tailscale falla)
IP=$(dig +short NOMBRE.trycloudflare.com @1.1.1.1 | head -1)
curl -sk --resolve NOMBRE.trycloudflare.com:443:$IP https://NOMBRE.trycloudflare.com/ -o /dev/null -w '%{http_code}'
# 000 o 52x = túnel caído. 200 = funcionando.
```

**Fix cuando la URL devuelve 000:**
```bash
pkill -f 'cloudflared.*PUERTO'
sleep 1
cloudflared tunnel --url http://localhost:PUERTO 2>&1 | tee /tmp/cf_PROYECTO.log &
sleep 18
grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf_PROYECTO.log | tail -1
```

**Pitfall:** No basta con que el proceso esté vivo — el edge de Cloudflare puede cerrar la
conexión sin matar el proceso local. Siempre verificar con `curl --resolve` antes de reportar
la URL al usuario.

## OAuth2 con Cloudflare Quick Tunnel — Problema de URL efímera

Cuando se usa un quick tunnel para el callback de OAuth2 (LinkedIn, Google, GitHub), la URL cambia en cada reinicio del tunnel. Esto rompe el flujo porque la redirect_uri registrada en el proveedor queda inválida.

**Síntoma:** Error "The redirect_uri does not match the registered value" en LinkedIn/Google.

**Regla:** Levantar el servidor OAuth ANTES que el tunnel, y NO reiniciar el tunnel durante el flujo.

```bash
# 1. Levantar servidor OAuth en background
cd /ruta/al/proyecto && python3 server.py &

# 2. Verificar que está corriendo
curl -s -o /dev/null -w "%{http_code}" http://localhost:8090  # debe ser 200

# 3. Levantar tunnel y capturar URL
cloudflared tunnel --url http://localhost:8090 2>&1 | tee /tmp/cf_oauth.log &
sleep 8
URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_oauth.log | tail -1)
echo "Redirect URI: $URL/callback"

# 4. Registrar $URL/callback en el proveedor (LinkedIn, Google, etc.)
# 5. Actualizar .env del proyecto con la misma URL
sed -i "s|REDIRECT_URI=.*|REDIRECT_URI=$URL/callback|" auth/.env

# 6. Reiniciar servidor para que lea la nueva redirect_uri
pkill -9 -f "server.py"; sleep 1
cd /ruta/al/proyecto && python3 server.py &

# 7. Verificar scopes en la URL generada
curl -s http://localhost:8090 | grep -o 'scope=[^&"]*'
```

**Pitfall crítico:** Si el servidor se reinicia, releer el .env con la redirect_uri nueva. Si se reinicia el tunnel, hay que actualizar la redirect_uri en el proveedor OAuth OTRA VEZ. Para evitar esto, no reiniciar el tunnel durante el flujo de autenticación.

**Solución definitiva:** Para OAuth2 en producción, usar un dominio propio con tunnel nombrado (no quick tunnel). La URL queda fija.

## Patrón de Regeneración Rápida (Túneles Caídos)

Cuando Nelson reporta que una URL no responde, el flujo de recuperación es:

```bash
# 1. Verificar qué servicios están vivos localmente
curl -sf http://localhost:PUERTO/health && echo "OK" || echo "CAÍDO"

# 2. Matar túneles viejos de ese puerto (evitar duplicados)
pkill -f "cloudflared.*PUERTO"
sleep 2

# 3. Verificar que el puerto quedó libre
ss -tlnp | grep :PUERTO

# 4. Relanzar tunnel en background
cloudflared tunnel --url http://127.0.0.1:PUERTO > /tmp/cf_proyecto.log 2>&1 &
sleep 10

# 5. Extraer nueva URL
URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_proyecto.log | tail -1)
echo "Nueva URL: $URL"

# 6. Verificar desde el servidor (con DNS override si Tailscale)
curl -s --max-time 15 "$URL/health"
```

**Cuando hay múltiples servicios (ej. ForestAI frontend + backend):**
Si el proyecto tiene frontend y backend en puertos separados y necesitan URLs independientes:

```bash
# Frontend (3010)
cloudflared tunnel --url http://127.0.0.1:3010 > /tmp/cf_fe.log 2>&1 &

# Backend (8010)
cloudflared tunnel --url http://127.0.0.1:8010 > /tmp/cf_be.log 2>&1 &

# Esperar y extraer ambas URLs
sleep 10
FE_URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_fe.log | tail -1)
BE_URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_be.log | tail -1)
```

**Nota:** El patrón preferido del equipo es **un solo túne al nginx** (ver sección "El Patrón" arriba). Solo usar múltiples túneles cuando el proyecto ya está corriendo con frontend/backend separados (ej. Docker Compose ya levantado) y no se puede reconfigurar nginx.

## Verificar Túnel antes de Notificar a Nelson

Nunca mandar una URL sin verificar primero:

```bash
# Verificar que responde (usando resolve si Tailscale bloquea DNS)
if curl -s --max-time 15 "$URL" | grep -q "DOCTYPE\|html\|json"; then
    echo "✅ URL válida"
else
    echo "❌ URL no responde"
fi
```

## Relanzar tunnel cuando la URL caduca (trycloudflare)

Las URLs de trycloudflare.com son efímeras — si el proceso muere, la URL cambia. Patrón de relanzado:

```bash
# Matar tunnel viejo
pkill -f "cloudflared.*PUERTO"
sleep 1

# Relanzar en background
cloudflared tunnel --url http://localhost:PUERTO > /tmp/cf_proyecto.log 2>&1 &

# Esperar y capturar nueva URL
sleep 8
grep -E "https://.*trycloudflare" /tmp/cf_proyecto.log | tail -1
```

Siempre mandar la nueva URL al usuario (WhatsApp) apenas esté disponible.

6. **Logs de cloudflared:** Si no funciona, revisar `/tmp/cf_proyecto.log`. Errores comunes: puerto ocupado, cloudflared no encontrado, rate limit de Cloudflare.
7. **Servidor escuchando solo en IPv4 loopback — Cloudflare falla por IPv6:** Si el servidor local está levantado con `python3 -m http.server` sin `--bind` o con `--bind 127.0.0.1`, Cloudflare intenta conectarse por IPv6 (`::1`) y falla silenciosamente. El túnel aparece como conectado en los logs (`Registered tunnel connection`) pero no sirve contenido. **Fix: siempre levantar con `--bind 0.0.0.0`:**
   ```bash
   # ❌ Falla con Cloudflare (solo escucha en 127.0.0.1)
   python3 -m http.server 8030
   
   # ✅ Correcto — escucha en todas las interfaces
   python3 -m http.server 8030 --bind 0.0.0.0 --directory public
   
   # Para uvicorn: --host 0.0.0.0 (ya es el default en docker pero no en dev local)
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
8. **Verificar túnel cuando DNS local no resuelve trycloudflare.com (Tailscale):** Con Tailscale activo, `curl https://NOMBRE.trycloudflare.com` falla con "Could not resolve host" desde el servidor. Esto no afecta al usuario final (su browser resuelve bien por internet). Para verificar desde el servidor:
   ```bash
   # Resolver con 1.1.1.1 de Cloudflare directamente
   curl --resolve NOMBRE.trycloudflare.com:443:$(dig +short NOMBRE.trycloudflare.com @1.1.1.1 | head -1) \
     https://NOMBRE.trycloudflare.com/ruta-de-prueba
   # Si responde OK → el túnel funciona, el problema es solo DNS local
6. **Logs de cloudflared:** Si no funciona, revisar `/tmp/cf_proyecto.log`. Errores comunes: puerto ocupado, cloudflared no encontrado, rate limit de Cloudflare.

7. **Servidor escuchando solo en IPv4 — Cloudflare conecta por IPv6 y falla silenciosamente:** Si el servidor usa `python3 -m http.server` sin `--bind` o `uvicorn --host 127.0.0.1`, Cloudflare intenta por `::1` y no responde. El túnel aparece registrado en logs (`Registered tunnel connection`) pero las requests dan timeout. Fix: siempre `--bind 0.0.0.0` o `--host 0.0.0.0`. Verificar: `ss -tlnp | grep PUERTO` debe mostrar `0.0.0.0:PUERTO`. Diagnóstico: `curl -v http://localhost:PUERTO` — si dice `connect to ::1 failed: Connection refused` con fallback a 127.0.0.1, el servidor no está en 0.0.0.0.

8. **Puerto de archivos estáticos pisado por backend:** Si se levanta `python3 -m http.server 8030` para servir HTMLs y luego el backend arranca en :8030, el backend mata al servidor de archivos. Usar puertos separados (ej: estáticos en :8031, backend en :8030). Verificar antes: `ss -tlnp | grep 8030`.

9. **DNS de Tailscale bloquea resolución de quick tunnels:** `dig +short NOMBRE.trycloudflare.com` puede fallar desde el servidor por el DNS de Tailscale. Verificar con `dig +short NOMBRE.trycloudflare.com @1.1.1.1` — si resuelve una IP, el túnel está activo y el browser del usuario (sin Tailscale) lo ve correctamente.

## Servir archivos estáticos simples (sin Docker)

Para compartir un HTML/página de análisis sin levantar Docker:

```bash
# CORRECTO — bind en 0.0.0.0 para que Cloudflare pueda conectarse por IPv6
cd /directorio/con/htmls
python3 -m http.server 8031 --bind 0.0.0.0
# Luego: cloudflared tunnel --url http://localhost:8031 2>&1 | tee /tmp/cf_static.log &

# INCORRECTO — por defecto solo escucha en 127.0.0.1, Cloudflare falla silenciosamente
python3 -m http.server 8031
```

**Alternativa más robusta:** copiar el HTML al `dist/` de un proyecto que ya tiene túnel activo:

```bash
# Identificar túneles activos y sus puertos
grep -h 'trycloudflare.com' /tmp/cf_*.log | grep -o 'https://[^[:space:]]*' | sort -u
grep -h 'url:http' /tmp/cf_*.log | sort -u

# Copiar el HTML al dist del proyecto con túnel activo (ej: Fleet en :8020)
cp mi-pagina.html /home/server/brainstorming/PROYECTO/poc/frontend/dist/
# URL resultante: https://XXXX.trycloudflare.com/mi-pagina.html
```

## Pitfalls Extra (servidor de estáticos)

- **Python http.server + Cloudflare IPv6:** El servidor por defecto solo escucha en `127.0.0.1`. Cloudflare intenta conectar por IPv6 (`::1`) y falla. El túnel aparece como "connected" en los logs pero las requests no llegan. Fix: `--bind 0.0.0.0`.
- **Quick Tunnels cambian URL en cada restart:** Preferir reutilizar el túnel de un proyecto ya activo copiando el archivo al `dist/` de ese proyecto.
- **DNS del servidor no resuelve trycloudflare.com:** Problema con Tailscale. Verificar desde el servidor con: `curl --resolve DOMINIO:443:$(dig +short DOMINIO @1.1.1.1 | head -1) https://DOMINIO/ruta`. El túnel funciona normalmente desde browsers externos.
- **Puerto pisado:** Si el backend del proyecto arranca en el mismo puerto que el servidor de estáticos, el servidor de estáticos muere. Usar puerto distinto (8031, 8032).

## Pitfall Crítico: Frontend Docker + nginx requiere REBUILD COMPLETO de la imagen

Cuando el frontend se sirve mediante nginx dentro de un contenedor Docker (patrón multi-stage build: builder → nginx), **no alcanza con hacer `npm run build` en el host**. El contenedor tiene copiados los archivos estáticos en el momento del build de la imagen. Cualquier cambio en el código fuente requiere reconstruir la imagen completa.

**Síntoma:** El usuario reporta "no veo los cambios" aunque el build local funcionó y el contenedor está corriendo. Los archivos dentro del contenedor son de una fecha anterior a la modificación.

**Diagnóstico:**
```bash
# Verificar fecha de los assets dentro del contenedor
docker exec PROYECTO-frontend-1 ls -la /usr/share/nginx/html/assets/
# Si la fecha es vieja → la imagen tiene archivos obsoletos

# Comparar con dist local
ls -la frontend/dist/assets/
```

**Fix completo (obligatorio):**
```bash
cd ~/proyectos/PROYECTO

# 1. Build local (verifica TypeScript + Vite)
cd frontend && npm run build && cd ..

# 2. Reconstruir la imagen del frontend SIN cache
docker compose build --no-cache frontend

# 3. Destruir el contenedor viejo y recrearlo con la nueva imagen
docker compose stop frontend
docker compose rm -f frontend
docker compose up -d frontend

# 4. Verificar que los assets son nuevos
docker exec PROYECTO-frontend-1 ls -la /usr/share/nginx/html/assets/

# 5. Forzar refresh del navegador (Ctrl+F5)
```

**Alternativa para desarrollo rápido (sin rebuild Docker):**
Si se está iterando mucho, levantar Vite en modo dev directo en el host (`npm run dev -- --host`) y apuntar el tunnel a ese puerto en vez de al nginx Docker. Cuando los cambios estén listos, recién ahí hacer el build + rebuild Docker para producción/demo.

## Comandos Útiles

```bash
# Ver túneles activos
ps aux | grep cloudflared

# Matar un túnel específico
pkill -f "cloudflared.*3010"

# Ver logs del túnel
tail -f /tmp/cf_proyecto.log

# Rebuild solo el frontend (si cambió código)
docker compose build --no-cache frontend
docker compose up -d --no-deps frontend

# Verificar nginx config dentro del container
docker exec PROYECTO-frontend-1 nginx -t
```

## Patrón: Tunnel para Dev Server (sin Docker/nginx)

Cuando el frontend corre en modo dev (Vite), no hay nginx. El tunnel va directo al puerto de Vite.

### Vite preview + trycloudflare (pitfall real)

En Vite moderno, `vite preview` puede bloquear hosts externos por seguridad. Con quick tunnel aparece:
`Blocked request. This host ("...trycloudflare.com") is not allowed.`

**Fix en `vite.config.ts`:**

```ts
export default defineConfig({
  server: {
    host: '0.0.0.0',
    proxy: { '/api': 'http://localhost:9000' }
  },
  preview: {
    host: '0.0.0.0',
    allowedHosts: ['.trycloudflare.com'],
    proxy: { '/api': 'http://localhost:9000' }
  }
})
## Patrón: Tunnel para Dev Server (sin Docker/nginx)

Cuando el frontend corre en modo dev (Vite), no hay nginx. El tunnel va directo al puerto de Vite.

```bash
# Lanzar tunnel para Vite dev server en :5174
cloudflared tunnel --url http://localhost:5174 > /tmp/cf_orch_dash.log 2>&1 &

# Esperar y capturar URL
sleep 8
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_orch_dash.log | tail -1
```

### `tailscale serve` requiere enable en tailnet (pitfall 2026-06-06)

Para evitar Cloudflare Tunnel y usar HTTPS nativo de Tailscale, intentamos `tailscale serve`:

```bash
tailscale serve --bg --https=3101 --set-path=/ http://localhost:3101
```

**Síntoma:** Devuelve `Serve is not enabled on your tailnet.` + URL `https://login.tailscale.com/f/serve?node=XXX` que requiere que Nelson habilite Serve en el admin console. El comando no tira error explícito, pero **timeout silencioso** esperando la URL que nunca se asigna.

**Workaround:** Mientras Nelson no habilite Serve, usar:
- HTTP plano en IP Tailscale: `http://100.110.8.13:3101` (cifrado punto-a-punto de Tailscale, sirve para la mayoría de los casos)
- Cloudflare Tunnel ephemeral (válido cuando se necesita HTTPS público)
- nginx + certbot si se requiere HTTPS sin Tailscale (más overhead)

**Decisión práctica:** Para servicios single-user en ai-server (FreeLLMAPI, dashboards internos, PoCs), HTTP por Tailscale es la opción preferida. URL estable (no cambia como trycloudflare), sin DNS externos, sin configuración.

## Patrón: Vite Preview con Proxy a Múltiples Backends (Orchestrator Dashboard)

El **orchestrator-dashboard** usa `vite preview` (no nginx) y el `vite.config.ts` define **proxies internos** a 3 backends distintos:

```typescript
// vite.config.ts — proxies del orchestrator-dashboard
export default defineConfig({
  server: {
    proxy: {
      '/api/tasks':      { target: 'http://localhost:8742', rewrite: p => p.replace('/api/tasks', '/tasks'),    changeOrigin: true },
      '/api/route':      { target: 'http://localhost:8743', rewrite: p => p.replace('/api/route', ''),          changeOrigin: true },
      '/api/orchestrate':{ target: 'http://localhost:8744', rewrite: p => p.replace('/api/orchestrate', ''),    changeOrigin: true },
      '/api/chat':        { target: 'http://localhost:8744', rewrite: p => p.replace('/api/chat', '/chat'),       changeOrigin: true },
      '/ws':             { target: 'ws://localhost:8744',  ws: true },
    },
  },
})
```

**Arquitectura:**
```
Usuario
   |
   v
Cloudflare Tunnel → https://XXXX.trycloudflare.com
   |
   v
Vite Preview (:5174 o el que sea)
   ├── /api/tasks/*   → proxy a http://localhost:8742 (Task Memory)
   ├── /api/route/*   → proxy a http://localhost:8743 (Agent Router)
   ├── /api/orchestrate/* → proxy a http://localhost:8744 (Meta Orchestrator)
   ├── /api/chat/*    → proxy a http://localhost:8744 (Chat/JARVIS)
   ├── /ws            → proxy WS a ws://localhost:8744
   └── /*             → serve dist/ (SPA React)
```

**Deploy:**
```bash
cd /home/server/nelson/orchestrator-dashboard

# Build si es necesario
npm run build

# Levantar preview (no dev server — preview sirve el dist/)
npx vite preview --host 0.0.0.0 --port 5174 &

# Verificar que los proxies funcionan antes de tunelar
curl -s http://127.0.0.1:5174/api/orchestrate/health   # debe responder el orchestrator
curl -s http://127.0.0.1:5174/api/tasks/                # debe responder task-memory

# Tunelar al Vite preview (NO al backend 8744)
cloudflared tunnel --url http://127.0.0.1:5174 > /tmp/cf_orch_dash.log 2>&1 &
sleep 8
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_orch_dash.log | tail -1
```

**Crítico:** El túnel apunta al puerto del **Vite preview**, no al backend directo. El backend (8744) debe estar vivo y respondiendo en localhost para que el proxy funcione. Si `curl http://127.0.0.1:5174/api/orchestrate/health` falla, el problema está en el backend o en los proxies de vite.config.ts, no en el túnel.

**Verificación end-to-end:**
```bash
# 1. ¿Backend 8744 vivo?
curl -s http://127.0.0.1:8744/health

# 2. ¿Vite preview proxy funciona?
curl -s http://127.0.0.1:5174/api/orchestrate/health

# 3. ¿Túnel responde?
curl -s https://XXXX.trycloudflare.com/api/orchestrate/health
```

Si (1) funciona pero (2) no → revisar `vite.config.ts` y que el preview esté en el puerto correcto.
Si (2) funciona pero (3) no → el túnel se cayó, relanzar.

### Verificación proactiva antes de reuniones con Pablo

Nelson lleva demos en vivo a reuniones presenciales con Pablo (COO/socio). Los tunnels se caen solos — SIEMPRE verificar ANTES de que salga a la reunión:

```bash
# Diagnóstico rápido de todos los tunnels activos
for log in /tmp/cf_forestai.log /tmp/cf_fleet.log /tmp/cf_orch_dash.log; do
  name=$(basename $log .log)
  url=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' $log 2>/dev/null | tail -1)
  if [ -n "$url" ]; then
    ip=$(dig +short ${url#https://} @1.1.1.1 | head -1)
    code=$(curl -sk --resolve ${url#https://}:443:$ip $url/ -o /dev/null -w '%{http_code}' 2>/dev/null)
    echo "$name: $url → HTTP $code"
  else
    echo "$name: SIN URL"
  fi
done
```

Si alguno devuelve `000` o no tiene URL → está caído → regenerar antes de que salga Nelson.

### Tunnel caído — procedimiento de recuperación

Los tunnels de trycloudflare.com son efímeros y pueden caerse. Cuando Nelson reporta que la UI no responde:

```bash
# 1. Verificar que el proceso frontend sigue vivo
ps aux | grep -E "vite|node.*PUERTO" | grep -v grep
ss -tlnp | grep PUERTO

# 2. Si el proceso vive pero el tunnel no:
pkill -f "cloudflared.*PUERTO"
sleep 1
cloudflared tunnel --url http://localhost:PUERTO > /tmp/cf_PROYECTO.log 2>&1 &
sleep 8
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_PROYECTO.log | tail -1
```

**Script automatizado:** `scripts/revive-tunnels.sh` en este skill. Uso:
```bash
./revive-tunnels.sh 3010 forestai   # Revive túnel para ForestAI
./revive-tunnels.sh 5180 orchestrator  # Revive túnel para orchestrator dashboard
```
El script mata túneles viejos, verifica que el servicio local esté vivo, lanza nuevo túnel, espera la URL, verifica desde internet, y guarda la URL en `/tmp/cf_{proyecto}.url`.

Después de relanzar: **mandar la URL nueva por WhatsApp** (texto + audio). Las URLs cambian cada vez que se relanza el tunnel.

### Logs por proyecto

| Proyecto | Puerto | Log |
|---|---|---|
| ForestAI | :3010 | `/tmp/cf_forestai.log` |
| Fleet | :8020 | `/tmp/cf_fleet.log` |
| Orchestrator Dashboard | :5174 | `/tmp/cf_orch_dash.log` |
| YoloV PoC | :9020 | `/tmp/cf_yolov.log` |

### Recuperación automática por watch_pattern

Cuando Hermes detecta que un tunnel caído via `watch_patterns`, el procedimiento es:

```bash
# 1. Matar proceso viejo del puerto específico
pkill -f 'cloudflared.*PUERTO' 2>/dev/null; sleep 1

# 2. Relanzar en background con watch_patterns para capturar la nueva URL
# terminal(background=true, watch_patterns=["trycloudflare.com"])
cloudflared tunnel --url http://localhost:PUERTO 2>&1 | tee /tmp/cf_proyecto.log

# 3. En follow-up terminal (no en background), capturar y verificar
sleep 5 && grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_proyecto.log | tail -1
curl -s -o /dev/null -w "%{http_code}" https://NUEVA-URL --max-time 10
```

**Nota:** El comando `pkill` + `sleep` debe ir en una terminal separada ANTES del background, o combinado en un solo background=false call antes de lanzar el background process. No usar `&&` con `&` en el mismo comando (Hermes lo rechaza).

### Patrón de diagnóstico rápido multi-servicio

Antes de regenerar una URL, verificar en este orden:

```bash
# 1. ¿El servicio local responde?
curl -s -o /dev/null -w '%{http_code}' http://localhost:PUERTO/health

# 2. ¿El proceso del tunnel sigue vivo?
ps aux | grep 'cloudflared.*PUERTO' | grep -v grep

# 3. ¿La URL anterior sigue activa desde afuera?
curl -sk --resolve NOMBRE.trycloudflare.com:443:$(dig +short NOMBRE.trycloudflare.com @1.1.1.1 | head -1) \
  https://NOMBRE.trycloudflare.com/ -o /dev/null -w '%{http_code}'
# 000 = tunnel caído → regenerar; 200 = tunnel OK, problema en otro lado
```

**Patrón observado en sesiones:** los tunnels se caen solos (proceso muere) pero el servicio
local sigue corriendo. El diagnóstico correcto es verificar PRIMERO el proceso cloudflared,
no el servicio. Si `ps aux | grep cloudflared` no muestra el proceso → regenerar URL
con `terminal(background=True)` + `watch_patterns=["trycloudflare.com"]`.

## Síntoma frecuente: tunnel aparece en log pero da HTTP 000

El proceso cloudflared puede morirse dejando el log con la URL del tunnel anterior.
Siempre verificar con curl antes de pasar la URL a Nelson:

```bash
url="https://NOMBRE.trycloudflare.com"
ip=$(dig +short ${url#https://} @1.1.1.1 | head -1)
curl -sk --resolve ${url#https://}:443:$ip $url/ -o /dev/null -w '%{http_code}'
# Si devuelve 000 → tunnel caído → regenerar
```

Ver `references/tunnel-health-check.md` — rutina completa de verificación + señales de tunnel caído.

## Casos de Uso en el Equipo

| Proyecto | Puerto nginx | URL pública | Patrón usado |
|----------|-------------|-------------|--------------|\n| ForestAI PoC | 3010 | trycloudflare | Un túnel ✅ |
| Fleet Optimizer | 3010 | trycloudflare | Un túnel ✅ |
| YoloV PoC | 9020 | trycloudflare | Un túnel ✅ |
| AI News Aggregator | — | — | No expuesto (cronjob) |
| JARVIS Demo Shell | 3789 | — | Local only |

## Patrón alternativo: FastAPI sirve el SPA directamente (sin nginx)

Para PoCs donde no vale la pena Docker+nginx. FastAPI monta el `dist/` del frontend
y agrega un middleware de SPA fallback. Un solo proceso, un solo puerto, un solo tunnel.
Ver detalle completo en `references/fastapi-spa-no-nginx.md`.

## Referencias

- Cloudflare Tunnel docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- nginx proxy_pass: https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass
- Vite env variables: https://vitejs.dev/guide/env-and-mode.html
- Skill: nelson-forest-inventory (patrón original de ForestAI con este deploy)
- `references/static-html-serving.md` — Servir HTML standalone sin Docker: reusar túnel existente, diagnóstico IPv6, verificación end-to-end con dig + curl resolve
- `references/ipv6-tunnel-debug.md` — diagnóstico y fix del bug servidor IPv4-only + Cloudflare IPv6
- `references/nelson-project-ports.md` — Puertos de todos los proyectos conocidos (Orchestrator, ForestAI, Fleet), reglas de qué puerto tunelar, comandos de verificación y levantamiento
- `references/vite-proxy-multiple-backends.md` — Patrón específico del orchestrator-dashboard: Vite preview con proxies a múltiples backends (8742, 8743, 8744). Diagnóstico paso a paso cuando "no funciona la URL".
- `references/watchdog-quick-tunnel-ops.md` — patrón de operación estable con quick tunnel + watchdog + scheduler (auto-healing)
- `references/vite-preview-trycloudflare.md` — fix de `Blocked request ... host is not allowed` en `vite preview` detrás de quick tunnel
- `references/orchestrator-dashboard-quick-tunnel.md` — runbook específico para exponer la UI del dashboard del meta-orchestrator (Vite :5174 + API :8744)
- **Skill relacionada:** `nelson-server-services/references/llm-proxy-deploy-pattern.md` — Patrón para deployar OpenAI-compatible LLM proxies (FreeLLMAPI, LiteLLM). Caso real: FreeLLMAPI deployado en :3101 con failover de 16 providers. Cuando un nuevo servicio LLM-related va al server, ese reference es el complemento de este skill.
