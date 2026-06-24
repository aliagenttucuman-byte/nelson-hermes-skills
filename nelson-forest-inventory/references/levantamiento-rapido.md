# ForestAI — Levantamiento Rápido

## Containers Docker

ForestAI usa Docker Compose. Los containers se apagan solos tras días de inactividad.

```bash
cd /home/server/proyectos/forestai-poc
docker compose up -d
# Esperar ~8s a que la DB quede healthy:
sleep 8 && curl -sS http://localhost:8010/health
# Debe responder: {"status":"ok","service":"forestai-backend"}
```

Puertos internos:
- Backend FastAPI: localhost:8010
- Frontend nginx: localhost:3010
- PostGIS DB: localhost:5433
- Redis: localhost:6380
- Celery worker: interno

## Túneles Cloudflare

ForestAI expone 2 túneles separados (frontend + backend). Las URLs cambian con cada reinicio.

```bash
cloudflared tunnel --url http://localhost:3010 > /tmp/cf_forestai_front.log 2>&1 &
cloudflared tunnel --url http://localhost:8010 > /tmp/cf_forestai_back.log 2>&1 &
sleep 10
echo "FRONTEND:"; grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_forestai_front.log | tail -1
echo "BACKEND:";  grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_forestai_back.log | tail -1
```

⚠️ Nunca hardcodear las URLs — siempre leer del log.

## Verificación rápida

```bash
docker compose -f /home/server/proyectos/forestai-poc/docker-compose.yml ps
curl -sS --max-time 5 http://localhost:8010/health
curl -sS --max-time 5 http://localhost:3010/ | head -c 100
```
