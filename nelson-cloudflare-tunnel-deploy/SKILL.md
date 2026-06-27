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

## Diagnóstico Rápido Antes de Debuggear el Tunnel

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

## Troubleshooting: UI inaccesible / "sigue caída"

Cuando el dashboard no carga, revisar en este orden ANTES de tocar el tunnel:

```bash
# 1. ¿El backend está corriendo?
curl -sf http://localhost:8000/health && echo "backend OK" || echo "backend DOWN"

# 2. ¿El Vite frontend está corriendo?
curl -sf http://localhost:5174 -o /dev/null -w "HTTP %{http_code}\n"

# 3. ¿El tunnel sigue conectado?
grep -E "Registered tunnel|failed" /tmp/cf_*.log | tail -3
```

El backend caído es la causa más frecuente de "UI que no carga" — el frontend levanta pero sin API no puede hacer nada. Levantar con:

```bash
cd /home/server/nelson/meta-orchestrator
source venv/bin/activate 2>/dev/null || true
# background=true, watch Application startup complete
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

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

**Alternativa más estable:** Acceder por Tailscale directo sin tunnel:
```
http://100.110.8.13:5174   # Dashboard
http://100.110.8.13:8000   # Backend API
```
Tailscale directo es más rápido, sin intermediarios, y sin depender de DNS externo.

## Patrón Alternativo: FastAPI sirviendo el dist (sin nginx)

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

## Variante: FastAPI sirve el dist directamente (sin nginx)

Cuando el backend FastAPI monta el frontend `dist/` como StaticFiles + SPA fallback, no se necesita nginx. Un solo proceso, un solo túnel.

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

## Pitfalls críticos — Servidor estático + Quick Tunnel

### El servidor debe escuchar en 0.0.0.0, NO en 127.0.0.1
Cloudflare a veces conecta vía IPv6 (`::1`). Si el servidor escucha solo en `127.0.0.1`, Cloudflare falla silenciosamente — el túnel aparece como "registrado" en los logs pero no sirve nada.

```bash
# ❌ Falla con Cloudflare (solo IPv4 loopback)
python3 -m http.server 8031           # escucha en 127.0.0.1 por defecto

# ✅ Correcto
python3 -m http.server 8031 --bind 0.0.0.0
```

### No usar --protocol http2 con python http.server
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

## Pitfalls de build

1. **VITE_API_URL vacío en el build:** Si se omite el `ARG` en el Dockerfile, Vite usa el default y las requests van a localhost. Siempre incluir `ARG VITE_API_URL=""`.

2. **Servidor de archivos estáticos pisado por backend en el mismo puerto:** Si se levanta un `python3 -m http.server 8030` para servir HTMLs y luego el backend de la PoC también arranca en :8030, el backend mata al servidor de archivos. Usar un puerto diferente para cada servicio (ej: archivos estáticos en :8031, backend en :8030). Verificar antes con `ss -tlnp | grep 8030`.

3. **Quick tunnels con DNS que no propagan inmediatamente:** Los túneles temporales de trycloudflare.com a veces tardan 30-60 segundos en propagar el DNS. Si el curl desde el servidor falla con "Could not resolve host", es el DNS de Tailscale bloqueando resolución externa (pitfall conocido). Verificar con `dig +short NOMBRE.trycloudflare.com @1.1.1.1` — si resuelve una IP, el túnel existe. El browser del usuario (que no usa Tailscale) lo verá correctamente.

4. **VITE_API_URL vacío en el build:** Si se omite el `ARG` en el Dockerfile

**Síntoma:** El HTML carga, la página aparece, pero la app no funciona — el WS no conecta y las llamadas a la API fallan. No hay error visible para el usuario.

**Causa:** El hook de WebSocket usa `window.location.hostname + ':PUERTO_INTERNO'`. Desde CF, ese puerto interno no es accesible — solo existe el 443 del túnel.

```ts
// ❌ MAL — rompe CF y cualquier reverse proxy
const proto    = window.location.protocol === 'https:' ? 'wss' : 'ws'
const hostname = window.location.hostname
return `${proto}://${hostname}:9000/api/v1/ws/contado`

// ✅ BIEN — usa el host completo del browser (incluye puerto si aplica)
const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
const host  = window.location.host  // "screens-cafe.trycloudflare.com" o "localhost:9090"
return `${proto}://${host}/api/v1/ws/contado`
```

**Regla general:** Nunca hardcodear el puerto del backend en el frontend. `window.location.host` funciona en local Y por CF sin cambios.

**Verificación post-fix:**
```bash
grep -r ':9000\|:8000\|:3000' frontend/dist/assets/*.js | grep -v 'node_modules' | head -5
# Si hay hits → hay puertos hardcodeados → rebuild requerido
```

**IMPORTANTE después de cualquier fix de frontend:**
```bash
# 1. Rebuild
cd frontend && npm run build

# 2. Reiniciar el proxy (sirve el dist nuevo — NO alcanza solo hacer rebuild)
kill $(pgrep -f spa_proxy.py)
cd .. && python3 spa_proxy.py &

# 3. CF NO necesita reiniciarse — sigue apuntando al mismo puerto del proxy
```

---

## Pitfalls de build

0. **WebSocket hardcodeado con hostname:puerto — ROMPE por CF tunnel:**
   Si el frontend tiene `ws://${hostname}:9000/api/v1/ws/...` hardcodeado, el WebSocket intenta conectar al puerto 9000 directamente. Por Cloudflare Tunnel ese puerto no existe — solo hay 443. Fix: usar `window.location.host` (que incluye el puerto del browser) en vez de `hostname` + puerto fijo:
   ```typescript
   // ❌ ROMPE por CF tunnel (puerto 9000 no accesible externamente)
   const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
   return `${proto}://${window.location.hostname}:9000/api/v1/ws/contado`

   // ✅ CORRECTO — usa el mismo host y puerto del browser
   const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
   return `${proto}://${window.location.host}/api/v1/ws/contado`
   ```
   Después del fix: rebuild del frontend + reiniciar el servidor estático/proxy para que sirva el dist nuevo.

1. **VITE_API_URL vacío en el build:**
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

```bash
# Lanzar tunnel para Vite dev server en :5174
cloudflared tunnel --url http://localhost:5174 > /tmp/cf_orch_dash.log 2>&1 &

# Esperar y capturar URL
sleep 8
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_orch_dash.log | tail -1
```

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

Después de relanzar: **mandar la URL nueva por WhatsApp** (texto + audio). Las URLs cambian cada vez que se relanza el tunnel.

### Logs por proyecto

| Proyecto | Puerto | Log |
|---|---|---|
| ForestAI | :3010 | `/tmp/cf_forestai.log` |
| Fleet | :8020 | `/tmp/cf_fleet.log` |
| Orchestrator Dashboard | :5174 | `/tmp/cf_orch_dash.log` |

## Casos de Uso en el Equipo

| Proyecto | Puerto nginx | URL pública | Patrón usado |
|----------|-------------|-------------|--------------|
| ForestAI PoC | 3010 | trycloudflare | Un túnel ✅ |
| Fleet Optimizer | 3010 | trycloudflare | Un túnel ✅ |
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
