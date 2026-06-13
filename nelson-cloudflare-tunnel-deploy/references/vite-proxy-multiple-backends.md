# Vite Preview + Proxy a Múltiples Backends — Orchestrator Dashboard

> Reference session: 2026-06-03. Problema: URL pública del orchestrator-dashboard caída.

## Arquitectura

El orchestrator-dashboard no usa nginx ni Docker. Es un proyecto Vite/React que:

1. Se buildea a `dist/` (`npm run build`)
2. Se sirve con `npx vite preview --host 0.0.0.0 --port <PORT>`
3. El `vite.config.ts` define proxies internos a 3 backends independientes

```
Usuario / Browser
    |
    v
Cloudflare Tunnel → https://XXXX.trycloudflare.com
    |
    v
Vite Preview Server (:5174, :5177, :5180, etc.)
    |
    +-- /*                  → serve dist/index.html (SPA fallback)
    +-- /assets/*           → serve dist/assets/ (StaticFiles)
    +-- /api/tasks/*        → proxy a http://localhost:8742 (Task Memory)
    +-- /api/route/*        → proxy a http://localhost:8743 (Agent Router)
    +-- /api/taxonomy       → proxy a http://localhost:8743
    +-- /api/orchestrate/*  → proxy a http://localhost:8744 (Meta Orchestrator)
    +-- /api/chat/*         → proxy a http://localhost:8744 (JARVIS chat)
    +-- /api/docs/*         → proxy a http://localhost:8744
    +-- /ws                 → proxy WS a ws://localhost:8744
```

## vite.config.ts (extracto relevante)

```typescript
const orchestratorTarget = process.env.ORCH_API_URL || 'http://localhost:8744'
const orchestratorWsTarget = (process.env.ORCH_WS_URL || 'ws://localhost:8744')

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5174,
    allowedHosts: true,
    proxy: {
      '/api/tasks':      { target: 'http://localhost:8742', rewrite: p => p.replace('/api/tasks', '/tasks'),    changeOrigin: true },
      '/api/route':      { target: 'http://localhost:8743', rewrite: p => p.replace('/api/route', ''),          changeOrigin: true },
      '/api/taxonomy':   { target: 'http://localhost:8743', rewrite: p => p.replace('/api/taxonomy', '/taxonomy'), changeOrigin: true },
      '/api/orchestrate':{ target: orchestratorTarget, rewrite: p => p.replace('/api/orchestrate', ''),    changeOrigin: true },
      '/api/chat':        { target: orchestratorTarget, rewrite: p => p.replace('/api/chat', '/chat'),       changeOrigin: true },
      '/api/docs':        { target: orchestratorTarget, rewrite: p => p.replace('/api/docs', '/docs'),        changeOrigin: true },
      '/ws':             { target: orchestratorWsTarget,  ws: true, rewriteWsOrigin: true },
    },
  },
})
```

## Diagnóstico paso a paso (cuando "no funciona la URL")

### Paso 1: ¿Los backends están vivos?

```bash
curl -s http://127.0.0.1:8742/health  # Task Memory
curl -s http://127.0.0.1:8743/health  # Agent Router
curl -s http://127.0.0.1:8744/health  # Meta Orchestrator
```

Si alguno falla → el problema es el backend, no el túnel. Levantar el servicio.

### Paso 2: ¿Vite preview está corriendo?

```bash
ss -tlnp | grep -E ':(5173|5174|5175|5176|5177|5178|5180)'
ps aux | grep "vite preview"
```

Si no hay proceso → levantar:
```bash
cd /home/server/nelson/orchestrator-dashboard
npx vite preview --host 0.0.0.0 --port 5174 &
```

### Paso 3: ¿El proxy funciona localmente?

```bash
# Debe devolver HTML del SPA
curl -s http://127.0.0.1:5174/ | head -5

# Debe devolver JSON del backend (a través del proxy)
curl -s http://127.0.0.1:5174/api/orchestrate/health
curl -s http://127.0.0.1:5174/api/tasks/
```

Si el HTML funciona pero el proxy no → revisar `vite.config.ts` (puertos, rewrites).

### Paso 4: ¿El túnel está conectado?

```bash
pgrep -af 'cloudflared.*5174'   # o el puerto que corresponda
grep -E 'Registered tunnel|trycloudflare.com' /tmp/cf_orch_dash.log | tail -5
```

Si no hay proceso o no muestra "Registered tunnel" → relanzar:
```bash
pkill -f 'cloudflared.*5174'
sleep 2
cloudflared tunnel --url http://127.0.0.1:5174 > /tmp/cf_orch_dash.log 2>&1 &
sleep 8
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_orch_dash.log | tail -1
```

### Paso 5: ¿La URL pública responde?

```bash
# Desde cualquier máquina externa (o con DNS override):
curl -s https://XXXX.trycloudflare.com/ | head -5
curl -s https://XXXX.trycloudflare.com/api/orchestrate/health
```

## Sesiones de logs por componente

| Servicio | Puerto | Log típico |
|---|---|---|
| Task Memory | 8742 | — |
| Agent Router | 8743 | — |
| Meta Orchestrator | 8744 | — |
| Vite Preview | 5174 (configurable) | — |
| Cloudflare Tunnel | — | `/tmp/cf_orch_dash.log` |

## Fix aplicado en sesión 2026-06-03

**Síntoma:** Nelson reportó "no funciona la url". La URL anterior (`vacations-founded-belkin-designs.trycloudflare.com`) estaba caída.

**Diagnóstico:**
1. El backend en :8744 respondía health OK
2. El túnel apuntaba a :8744 (backend directo), no al frontend
3. El frontend (vite preview) corría en :5177, no en :5174
4. Al apuntar el túnel a :8744, el browser recibía `{"detail":"Not Found"}` (respuesta de FastAPI, no del SPA)

**Fix:**
1. Matar túnel viejo: `pkill -f 'cloudflared.*8744'`
2. Levantar Vite preview en :5180: `npx vite preview --host 0.0.0.0 --port 5180`
3. Verificar proxy local:
   - `curl http://127.0.0.1:5180/` → HTML ✓
   - `curl http://127.0.0.1:5180/api/orchestrate/health` → JSON ✓
4. Crear nuevo túnel apuntando a :5180
5. Nueva URL: `https://checking-trusts-blond-firewall.trycloudflare.com`

## Diferencia clave: ¿Túnel al backend o al frontend?

| Escenario | ¿A dónde apunta el túnel? | ¿Por qué? |
|---|---|---|
| nginx → backend | :3010 (nginx) | nginx sirve estáticos + proxy a backend |
| FastAPI sirve dist | :8000 (FastAPI) | Un solo proceso, un solo puerto |
| Vite preview + proxy | :5174 (Vite preview) | Vite sirve dist + proxy a múltiples backends |
| Backend expuesto directo | :8744 (FastAPI) | SOLO si no hay frontend (API pura) |

**Regla de oro:** Si hay un frontend SPA, el túnel va al **servidor del frontend** (nginx, Vite preview, o FastAPI con StaticFiles), nunca al backend directo.
