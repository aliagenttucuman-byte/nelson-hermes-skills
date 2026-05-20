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

## Servicios activos (al 2026-05-19)

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

## Acceso vía Tailscale

Todos los servicios accesibles desde la red Tailscale:

- n8n: http://100.110.8.13:5678
- RAG PoC: http://100.110.8.13:8000
- RAG MinIO: http://100.110.8.13:8001
- RAG FLoCI Azure: http://100.110.8.13:8002
- SearXNG: http://100.110.8.13:8888

## Compose files

Cada servicio tiene su docker-compose.yml en el directorio de proyecto:

- /home/server/n8n-docker/docker-compose.yml
- /home/server/brainstorming/2026-05-13-rag-poc/docker-compose.yml
- /home/server/brainstorming/2026-05-13-rag-poc-minio/docker-compose.yml
- /home/server/brainstorming/2026-05-14-rag-floci-azure/docker-compose.yml
- /home/server/brainstorming/2026-05-16-ai-search-assistant/docker-compose.yml

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

## Pitfalls

- Puertos 8000, 8001, 8002 siempre ocupados por los backends RAG. Para nuevos servicios Python usar 8765+.
- Los tres backends RAG usan el mismo puerto interno (8000) mapeado a 8000, 8001, 8002 en el host. No mezclar.
- n8n guarda estado en volumen Docker — no hacer prune de volúmenes sin backup.
- SearXNG no requiere auth — no exponer a internet sin VPN/Tailscale.
- Si se agrega un nuevo servicio, actualizar este skill con el puerto y el path del compose.
