---
name: nelson-server-services
description: Mapa de servicios Docker corriendo en el servidor ai-server (100.110.8.13). Puertos, proyectos de origen y estado.
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [docker, infraestructura, servidor, servicios, nelson]
    category: devops
    requires_toolsets: [terminal]
---

# Mapa de Servicios Docker — ai-server

Servidor: ai-server
IP Tailscale: 100.110.8.13
SSH: ssh server@100.110.8.13 (pass: srv2026)

## Servicios activos (al 2026-05-22)

| Servicio | Puerto Host | Puerto Interno | Imagen | Proyecto origen |
|----------|-------------|----------------|--------|-----------------|
| n8n | 5678 | 5678 | docker.n8n.io/n8nio/n8n:latest | /home/server/n8n-docker/ |
| RAG PoC backend (original) | 8000 | 8000 | 2026-05-13-rag-poc-backend | /home/server/brainstorming/2026-05-13-rag-poc/ |
| RAG PoC MinIO backend | 8001 | 8000 | 2026-05-13-rag-poc-minio-backend | /home/server/brainstorming/2026-05-13-rag-poc-minio/ |
| RAG FLoCI Azure backend | 8002 | 8000 | 2026-05-14-rag-floci-azure-backend | /home/server/brainstorming/2026-05-14-rag-floci-azure/ |
| SearXNG (buscador privado) | 8888 | 8080 | searxng/searxng:latest | /home/server/brainstorming/2026-05-16-ai-search-assistant/ |
| JARVIS Demo Shell frontend | 3789 | — | Node (npm dev) | /home/server/jarvis-demo-shell/frontend/ |
| JARVIS Demo Shell backend | 8765 | — | Python (uvicorn) | /home/server/jarvis-demo-shell/backend/ |
| OpenUI spike (descartable) | 3456 | — | Node (npm dev) | /home/server/spikes/001-openui/genui-chat-app/ |
| ForestAI PoC frontend | 3010 | 80 | Docker (nginx) | /home/server/proyectos/forestai-poc/ — ⚠️ sirve dist compilado, no código fuente |
| ForestAI PoC backend | 8010 | 8000 | Docker (uvicorn) | /home/server/proyectos/forestai-poc/ |
| ForestAI PoC DB (PostGIS) | 5433 | 5432 | postgis/postgis:16-3.4-alpine | /home/server/proyectos/forestai-poc/ |
| ForestAI PoC Redis | 6380 | 6379 | redis:7-alpine | /home/server/proyectos/forestai-poc/ |
| Fleet Optimizer AR backend+frontend | 8020 | — | Python (uvicorn) | /home/server/brainstorming/2026-05-22-fleet-optimizer/poc/backend/ |

## Acceso vía Tailscale

Todos los servicios accesibles desde la red Tailscale:

- n8n: http://100.110.8.13:5678
- RAG PoC: http://100.110.8.13:8000
- RAG MinIO: http://100.110.8.13:8001
- RAG FLoCI Azure: http://100.110.8.13:8002
- SearXNG: http://100.110.8.13:8888
- ForestAI frontend: http://100.110.8.13:3010
- Fleet Optimizer AR: http://100.110.8.13:8020

## Compose files

Cada servicio tiene su docker-compose.yml en el directorio de proyecto:

- /home/server/n8n-docker/docker-compose.yml
- /home/server/brainstorming/2026-05-13-rag-poc/docker-compose.yml
- /home/server/brainstorming/2026-05-13-rag-poc-minio/docker-compose.yml
- /home/server/brainstorming/2026-05-14-rag-floci-azure/docker-compose.yml
- /home/server/brainstorming/2026-05-16-ai-search-assistant/docker-compose.yml
- /home/server/proyectos/forestai-poc/docker-compose.yml  ← ForestAI (backend+celery+frontend+db+redis)

## ⚠️ Pitfall crítico: Docker container ForestAI ≠ código fuente

El container `forestai-poc-frontend-1` sirve un **dist estático**. Editar código en
`~/proyectos/forestai-3d/frontend/src/` NO actualiza lo que ve el usuario. Flujo obligatorio:

```bash
cd ~/proyectos/forestai-3d/frontend
npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
# Luego Ctrl+Shift+R en browser
```

Sin el `docker cp` el build es inútil — el tunnel sigue sirviendo el HTML viejo.

## Fleet Optimizer AR — Deploy sin Docker

Fleet Optimizer sirve el frontend compilado directamente desde FastAPI (StaticFiles mount).
No tiene docker-compose. Para levantar:

```bash
# Asegurarse que el dist está compilado
ls /home/server/brainstorming/2026-05-22-fleet-optimizer/poc/frontend/dist

# Levantar backend (sirve también el frontend)
cd /home/server/brainstorming/2026-05-22-fleet-optimizer/poc/backend
pip install -q -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8020
```

El frontend dist ya existe compilado — no hace falta `npm run build` salvo cambios en el código.

### Módulo OCR de comprobantes de combustible

Fleet Optimizer incluye un módulo de OCR para cargar comprobantes de carga de combustible.
Pipeline: EasyOCR → regex → fallback Ollama local (qwen2.5:3b). Acepta JPG, PNG, PDF.
Campos extraídos: fecha, numero_comprobante, monto_total, cuit, patente, concepto.

Ver skill `nelson-ai-vision` → sección "Extracción de campos de comprobantes" + template `templates/ocr_comprobantes.py`.

Endpoint: `POST /api/ocr` (multipart/form-data, field: `file`).
Respuesta incluye `campos`, `lineas_ocr` e `imagen_b64` para preview en el frontend.

Dependencias adicionales: `easyocr`, `pymupdf` (ya en requirements.txt del backend).

## Comandos útiles

```bash
# Ver todos los servicios corriendo
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

# Logs de un servicio
docker logs --tail 50 -f <nombre-contenedor>

# Reiniciar desde su carpeta de proyecto
cd /home/server/brainstorming/<proyecto>/
docker compose restart

# Estado general
docker system df
```

## Tunnels Cloudflare (exposición pública efímera)

Para exponer servicios locales a internet sin dominio fijo, usar `cloudflared tunnel --url`. Las URLs son efímeras (se renuevan cada pocas horas).

### Patrón para múltiples servicios

Levantar un túnel por servicio. Los logs van a stderr — capturar con `2>&1 | tee`:

```bash
# Levantar N túneles en background, uno por servicio
cloudflared tunnel --url http://localhost:3010 2>&1 | tee /tmp/cf_forestai.log &
cloudflared tunnel --url http://localhost:8020 2>&1 | tee /tmp/cf_fleet.log &
```

Luego extraer las URLs de los logs:
```python
import subprocess, re, time

time.sleep(15)  # Dar tiempo a cloudflared para conectar

for log, name in [('/tmp/cf_forestai.log', 'ForestAI'), ('/tmp/cf_fleet.log', 'Fleet')]:
    r = subprocess.run(['cat', log], capture_output=True, text=True)
    urls = re.findall(r'https://[a-z0-9\-]+\.trycloudflare\.com', r.stdout)
    print(f"{name}: {urls[0] if urls else 'NO URL YET'}")
```

### Pitfalls de cloudflared

- **`cloudflared` sin `2>&1` no loguea nada útil**: los logs van a stderr. Siempre usar `2>&1 | tee /tmp/cf_nombre.log`.
- **URL efímera**: se renueva cada pocas horas. Consultar el log para la URL actual. Si el túnel se cayó, relanzar.
- **Un solo túnel no puede exponer dos puertos**: si hay frontend y backend separados, compilar el frontend y servirlo desde el backend (FastAPI staticfiles mount). Un servicio → un túnel.
- **Conflicto al relanzar**: si cloudflared ya está corriendo en el mismo puerto, matar el proceso viejo con `pkill -9 cloudflared` antes de relanzar.
- **Última URL conocida de ForestAI**: ver memoria del agente — se actualiza en cada sesión.

### ForestAI — puertos
- Frontend: `:3010` (servido por Docker nginx)
- Backend API: `:8010`
- Túnel expone el frontend `:3010`

### Fleet Optimizer AR — puertos
- Backend + frontend estático compilado: `:8020`
- Túnel expone `:8020` directamente

## Servicios systemd (no Docker) — Meta-Agente

Dos servicios del meta-orquestador corren como systemd units (no Docker), usando el venv de Hermes:

| Servicio | Puerto | Ruta | Systemd unit | Descripción |
|----------|--------|------|--------------|-------------|
| nelson-task-memory | 8742 | /home/server/nelson/task-memory/ | nelson-task-memory.service | Memoria persistente de tareas (SQLite + FastAPI) |
| nelson-agent-router | 8743 | /home/server/nelson/routing/ | nelson-agent-router.service | Router declarativo de agentes (keyword scoring + multi-agente) |

```bash
# Verificar estado
sudo systemctl status nelson-task-memory
sudo systemctl status nelson-agent-router

# Health checks
curl http://localhost:8742/health
curl http://localhost:8743/health

# Logs
sudo journalctl -u nelson-task-memory -f
sudo journalctl -u nelson-agent-router -f
```

Ambos arrancan automáticamente con el servidor (enabled). Usan el venv:
`/home/server/.hermes/hermes-agent/venv/bin/uvicorn`

**Pitfall — puerto ocupado antes de systemd start**: si previamente se levantó el servicio
en background con `uvicorn ... &` o `terminal(background=True)`, el puerto queda ocupado
y systemd falla al arrancar. Antes de `systemctl start`, matar el proceso:
```bash
kill $(lsof -ti:8742)  # o usar process(action='kill', session_id=...)
```

## Puertos en uso (al 2026-05-26)

| Puerto | Servicio |
|--------|---------|
| 3010 | ForestAI frontend (Docker) |
| 5678 | n8n |
| 8000-8002 | RAG PoC backends |
| 8010 | ForestAI backend (Docker) |
| 8020 | Fleet Optimizer AR backend (uvicorn directo) |
| 8742 | nelson-task-memory (systemd) |
| 8743 | nelson-agent-router (systemd) |
| 8765 | JARVIS Demo Shell backend |
| 8888 | SearXNG |

## Patrón Cloudflare Tunnel — single service

Cuando el frontend React se compila y lo sirve el propio FastAPI (con `StaticFiles`),
basta **un solo túnel** para exponer todo (frontend + API + WebSocket).

```bash
# Build del frontend
cd frontend && npm run build  # genera dist/

# FastAPI sirve dist/ + la API en el mismo proceso
# En main.py:
# app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
# @app.get("/") → FileResponse("frontend/dist/index.html")
# @app.get("/{full_path:path}") → SPA fallback

# Lanzar túnel (capturar URL en log)
cloudflared tunnel --url http://localhost:PUERTO 2>&1 | tee /tmp/cf_NOMBRE.log &

# Leer URL
grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' /tmp/cf_NOMBRE.log | head -1
```

**Pitfall**: cloudflared escribe a stderr. Sin `2>&1` el log queda vacío y no se puede leer la URL.

## Servicios con tunnel activo (efímeros, se renuevan cada pocas horas)

| Proyecto | Puerto | Log |
|---------|--------|-----|
| ForestAI | 3010 | /tmp/cf_forestai.log |
| Fleet Optimizer AR | 8020 | /tmp/cf_fleet.log |

## Pitfalls

- Puertos 8000, 8001, 8002 siempre ocupados por los backends RAG. Para nuevos servicios Python usar 8765+.
- Los tres backends RAG usan el mismo puerto interno (8000) mapeado a 8000, 8001, 8002 en el host. No mezclar.
- n8n guarda estado en volumen Docker — no hacer prune de volúmenes sin backup.
- SearXNG no requiere auth — no exponer a internet sin VPN/Tailscale.
- Si se agrega un nuevo servicio, actualizar este skill con el puerto y el path del compose.
- **cloudflared logs van a stderr**: siempre redirigir con `2>&1 | tee /tmp/cf_NOMBRE.log`. Sin esto el log queda vacío.
- **URL de cloudflared es efímera**: se renueva cada pocas horas. Para URL fija usar Cloudflare Zero Trust con dominio propio (5 min de setup, cuenta gratis).

## Exponer servicios con Cloudflare Tunnel (efímero)

Para exponer uno o varios servicios a internet sin dominio propio:

```bash
# Un túnel por servicio — cada uno con su log
cloudflared tunnel --url http://localhost:3010 2>&1 | tee /tmp/cf_forestai.log &
cloudflared tunnel --url http://localhost:8020 2>&1 | tee /tmp/cf_fleet.log &

# Leer la URL asignada (esperar ~15s para que negocie)
grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' /tmp/cf_forestai.log
grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' /tmp/cf_fleet.log
```

**Pitfalls cloudflared:**
- cloudflared escribe SOLO a stderr — usar `2>&1 | tee /tmp/cf_X.log` para capturar. Sin `2>&1` el log queda vacío.
- Las URLs son efímeras y se renuevan cada pocas horas — consultarlas desde el log, no hardcodear.
- Para matar todos los túneles activos: `pkill -9 cloudflared`
- Para WebSocket sobre Cloudflare: funciona nativo, no requiere config extra.
- Un túnel = un puerto. Para exponer frontend y backend por separado, lanzar dos procesos cloudflared.
- Si el proyecto sirve frontend desde el mismo FastAPI (StaticFiles), un solo túnel alcanza.
