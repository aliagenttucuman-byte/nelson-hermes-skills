# Puertos y túneles de los proyectos conocidos de Nelson

Tabla rápida de referencia para no confundir puertos cuando Nelson pide "levantar X proyecto" o "la URL no funciona".

| Proyecto | Servicio | Puerto local | ¿Túnel? | Notas |
|----------|----------|-------------|---------|-------|
| **Orchestrator Dashboard** | Frontend (Vite preview) | 5180 | ✅ | Tiene proxies a APIs en vite.config.ts — tunnel aquí |
| **Orchestrator API** | Backend FastAPI | 8744 | ❌ | No tunelar directo — el frontend ya proxya |
| **ForestAI PoC** | Frontend (nginx) | 3010 | ✅ | Docker compose, sirve el dist de React |
| **ForestAI PoC** | Backend FastAPI | 8010 | ✅ | A veces se necesita túnel separado para API directa |
| **Fleet Optimizer** | Frontend | 8020 | ✅ | (verificar si sigue activo) |
| **Task Memory** | API | 8742 | ❌ | Solo interno |
| **Agent Router** | API | 8743 | ❌ | Solo interno |

## Regla de oro: ¿A qué puerto le hago túnel?

```
Si el proyecto tiene nginx frontend → túnel al puerto del nginx
Si el proyecto es Vite dev server → túnel al puerto de Vite preview
Si el proyecto es solo backend FastAPI → túnel al puerto de uvicorn
Si el proyecto es solo archivos estáticos → túnel al puerto de http.server
```

## Orchestrator — Caso especial

El orchestrator tiene **dos puertos** y es fuente frecuente de confusión:

- **:8744** = Backend FastAPI con endpoints `/health`, `/plan`, `/run`, `/chat/*`
- **:5180** = Vite preview del dashboard frontend con `proxy:` en `vite.config.ts`

El dashboard (frontend) tiene proxies configurados:
```ts
// vite.config.ts
proxy: {
  '/api/tasks':      { target: 'http://localhost:8742', ... },
  '/api/route':      { target: 'http://localhost:8743', ... },
  '/api/orchestrate':{ target: 'http://localhost:8744', ... },
  '/api/chat':        { target: 'http://localhost:8744', ... },
}
```

**Por eso siempre tunelar el FRONTEND (5180), no el backend (8744).**
Si tunneleás 8744 directo, el usuario ve JSON de API en vez del dashboard.

### Verificar que el dashboard está corriendo

```bash
ss -tlnp | grep 5180   # Debe mostrar node/vite escuchando
curl -s http://127.0.0.1:5180 | head -5   # Debe devolver HTML del dashboard
curl -s http://127.0.0.1:5180/api/orchestrate/health   # Proxy → backend OK
```

### Si el usuario dice "no funciona la URL del orchestrator"

```bash
# 1. Verificar TÚNEL viejo
grep 'trycloudflare.com' /tmp/cf_orch_dash.log 2>/dev/null

# 2. Verificar que Vite sigue vivo
ps aux | grep -E 'vite.*preview|node.*vite' | grep -v grep
ss -tlnp | grep 5180

# 3. Si Vite vivo pero tunnel caído → matar y relanzar
pkill -f 'cloudflared.*5180'
sleep 2
cloudflared tunnel --url http://127.0.0.1:5180 > /tmp/cf_orch_dash.log 2>&1 &
sleep 8
grep -oE 'https://[\w-]+\.trycloudflare\.com' /tmp/cf_orch_dash.log | tail -1
```

## ForestAI — Stack Docker confirmado

Ubicación: `/home/server/proyectos/forestai-poc/`

```yaml
# docker-compose.yml (resumen de puertos expuestos)
backend:     ports: ["8010:8000"]
frontend:    ports: ["3010:80"]   # nginx sirve React dist
redis:       ports: ["6380:6379"]
db:          ports: ["5433:5432"]  # PostgreSQL + PostGIS
```

### Levantar ForestAI

```bash
cd /home/server/proyectos/forestai-poc
docker compose up -d --build
# Tarda ~3-5 min (descarga PyTorch, transformers, etc.)
```

### Verificar salud

```bash
curl -s http://127.0.0.1:3010/ | head -5      # Frontend nginx
curl -s http://127.0.0.1:8010/health          # Backend FastAPI
```

### Crear túneles para ForestAI

```bash
# Frontend
cloudflared tunnel --url http://127.0.0.1:3010 > /tmp/cf_forestai_fe.log 2>&1 &
sleep 8
grep -oE 'https://[\w-]+\.trycloudflare\.com' /tmp/cf_forestai_fe.log | tail -1

# Backend (si necesita API directa)
cloudflared tunnel --url http://127.0.0.1:8010 > /tmp/cf_forestai_be.log 2>&1 &
sleep 8
grep -oE 'https://[\w-]+\.trycloudflare\.com' /tmp/cf_forestai_be.log | tail -1
```

## Múltiples túneles simultáneos

Cuando Nelson pide levantar varios proyectos a la vez:

```bash
# Ver túneles existentes
ps aux | grep cloudflared | grep -v grep

# Matar túneles conflictivos (mismo puerto)
pkill -f 'cloudflared.*5180' 2>/dev/null
pkill -f 'cloudflared.*3010' 2>/dev/null
pkill -f 'cloudflared.*8010' 2>/dev/null
sleep 2

# Lanzar nuevos en background con logs separados
cloudflared tunnel --url http://127.0.0.1:5180 > /tmp/cf_orch.log 2>&1 &
cloudflared tunnel --url http://127.0.0.1:3010 > /tmp/cf_forestai_fe.log 2>&1 &
cloudflared tunnel --url http://127.0.0.1:8010 > /tmp/cf_forestai_be.log 2>&1 &

# Esperar y extraer URLs
sleep 10
echo "=== Orchestrator ==="
grep -oE 'https://[\w-]+\.trycloudflare\.com' /tmp/cf_orch.log | tail -1
echo "=== ForestAI FE ==="
grep -oE 'https://[\w-]+\.trycloudflare\.com' /tmp/cf_forestai_fe.log | tail -1
echo "=== ForestAI BE ==="
grep -oE 'https://[\w-]+\.trycloudflare\.com' /tmp/cf_forestai_be.log | tail -1
```

**Importante:** Cada túnel necesita su propio archivo de log. No reusar `/tmp/cf_proyecto.log` para todo.
