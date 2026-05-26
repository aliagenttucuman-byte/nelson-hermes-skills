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

## Comparativa: Un Túnel vs Dos Túneles

| Aspecto | Un túnel (nginx) | Dos túneles |
|---------|-----------------|-------------|
| Backend expuesto | ❌ No | ✅ Sí (público) |
| Complejidad | Baja | Alta |
| VITE_API_URL | `""` (relativo) | URL pública del backend |
| Orden de deploy | Build → levantar → un túnel | Build → levantar → túnel backend → build frontend → túnel frontend |
| Seguridad | Mejor | Peor |
| Rebuild por URL cambiada | No | Sí (VITE_API_URL se hornea) |

## Pitfalls

1. **VITE_API_URL vacío en el build:** Si se omite el `ARG` en el Dockerfile, Vite usa el default y las requests van a localhost. Siempre incluir `ARG VITE_API_URL=""`.
2. **Trailing slashes en proxy_pass:** `proxy_pass http://backend:8000/;` (con `/` al final) es distinto de `proxy_pass http://backend:8000;`. Con `/`, nginx elimina el prefix `/api/` antes de pasar al backend. Sin `/`, el backend recibe `/api/health` en vez de `/health`.
3. **CORS no necesario:** Con este patrón, frontend y backend comparten el mismo dominio. No hace falta configurar CORS. Si antes tenías CORS y ahora no funciona, revisá que el backend no esté rechazando requests del mismo origen.
4. **cloudflared no está instalado:** `sudo apt install cloudflared` o descargar binario desde https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
5. **nginx no sirve el frontend correctamente:** Asegurarse de que `try_files $uri $uri/ /index.html;` esté presente. Sin esto, las rutas de React Router (ej. `/dashboard`) devuelven 404.
6. **Logs de cloudflared:** Si no funciona, revisar `/tmp/cf_proyecto.log`. Errores comunes: puerto ocupado, cloudflared no encontrado, rate limit de Cloudflare.

## Comandos Útiles

```bash
# Ver túneles activos
ps aux | grep cloudflared

# Matar un túnel específico
kill $(pgrep -f "cloudflared.*3010")

# Ver logs del túnel
tail -f /tmp/cf_proyecto.log

# Rebuild solo el frontend (si cambió código)
docker compose build --no-cache frontend
docker compose up -d --no-deps frontend

# Verificar nginx config dentro del container
docker exec PROYECTO-frontend-1 nginx -t
```

## Casos de Uso en el Equipo

| Proyecto | Puerto nginx | URL pública | Patrón usado |
|----------|-------------|-------------|--------------|
| ForestAI PoC | 3010 | trycloudflare | Un túnel ✅ |
| Fleet Optimizer | 3010 | trycloudflare | Un túnel ✅ |
| AI News Aggregator | — | — | No expuesto (cronjob) |
| JARVIS Demo Shell | 3789 | — | Local only |

## Referencias

- Cloudflare Tunnel docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- nginx proxy_pass: https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass
- Vite env variables: https://vitejs.dev/guide/env-and-mode.html
- Skill: nelson-forest-inventory (patrón original de ForestAI con este deploy)
