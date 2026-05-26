# Levantar stack completo ForestAI + Fleet Optimizer

## Puerto / proceso map

| Puerto | Qué es | Proceso |
|--------|--------|---------|
| 3010 | ForestAI frontend (nginx Docker) | forestai-poc-frontend-1 |
| 8010 | ForestAI backend (FastAPI Docker) | forestai-poc-backend-1 |
| 8020 | Fleet optimizer backend (uvicorn) | manual |
| 3012 | Fleet optimizer frontend (npx serve) | manual |

## Comando completo de arranque

```bash
# 1. Docker containers ForestAI
cd ~/proyectos/forestai-poc && docker compose up -d

# 2. Fleet backend
cd ~/brainstorming/2026-05-22-fleet-optimizer/poc/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8020 &

# 3. Fleet frontend
npx serve /home/server/brainstorming/2026-05-22-fleet-optimizer/poc/frontend/dist -p 3012 &

# 4. Tunnels
cloudflared tunnel --url http://localhost:3010 2>&1 | tee /tmp/cf_forestai.log &
cloudflared tunnel --url http://localhost:8020 2>&1 | tee /tmp/cf_fleet.log &
cloudflared tunnel --url http://localhost:3012 2>&1 | tee /tmp/cf_fleet_frontend.log &

# 5. Esperar y verificar URLs (8-10 seg)
sleep 10
grep trycloudflare /tmp/cf_forestai.log | tail -1
grep trycloudflare /tmp/cf_fleet.log | tail -1
grep trycloudflare /tmp/cf_fleet_frontend.log | tail -1
```

## Deploy de cambios al frontend ForestAI

```bash
cd ~/proyectos/forestai-3d/frontend
npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
# Usuario hace Ctrl+Shift+R
```

## Verificar estado

```bash
docker ps | grep forestai
curl -s http://localhost:8010/health
curl -s http://localhost:8020/health
```
