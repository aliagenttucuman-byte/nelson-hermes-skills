# Watchdog de operación para quick tunnels (auto-healing)

Objetivo: evitar downtime cuando el stack (backend/frontend/túnel) depende de procesos de dev o quick tunnels efímeros.

## Cuándo aplicarlo
- PoCs en vivo sin credenciales de named tunnel.
- Entornos donde la URL pública puede rotar y hay que mantener servicio disponible.

## Patrón

1) Health contract local
- backend health: `http://127.0.0.1:<backend_port>/health`
- frontend root: `http://127.0.0.1:<frontend_port>/`
- proxy API: `http://127.0.0.1:<frontend_port>/api/.../health`

2) Health público
- `https://<trycloudflare>/api/.../health`

3) Watchdog periódico (cada 2-5 min)
- Si backend cae → restart backend.
- Si frontend cae → restart frontend.
- Si tunnel cae/no responde → relanzar cloudflared.
- Guardar URL pública vigente en archivo de estado (`/tmp/*.url`) para consumo operativo.

## Comandos base

```bash
# backend
uvicorn main:app --host 0.0.0.0 --port 8764

# dashboard dev
ORCH_API_URL=http://localhost:8764 ORCH_WS_URL=ws://localhost:8764 npm run dev -- --host 0.0.0.0 --port 5186

# tunnel
cloudflared tunnel --url http://localhost:5186
```

## Scheduler recomendado
- Cron cada 3 minutos para ejecutar watchdog de una sola corrida.
- El watchdog debe ser idempotente y silencioso cuando no hay acciones.

## Señales de éxito
- `/` y `/api/.../health` devuelven 200 de forma sostenida.
- Si un proceso cae, se recupera automáticamente antes de la siguiente verificación.

## Pitfalls
- No lanzar múltiples `cloudflared` sobre el mismo puerto (siempre limpiar proceso previo).
- No depender de terminal interactiva para estabilidad.
- En quick tunnels, exponer siempre un mecanismo para descubrir la URL actual (log parser o archivo de estado).
