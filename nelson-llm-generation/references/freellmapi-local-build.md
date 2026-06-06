# FreeLLMAPI — Build local + deploy (workflow completo)

**Origen:** workflow validado el 2026-06-06 al agregar el provider Anthropic nativo al fork local de `tashfeenahmed/freellmapi` en `ai-server`. La imagen pre-built de DockerHub quedó desactualizada en 2 min — esto es el procedimiento que sí funciona.

## TL;DR

| Paso | Comando | Tiempo |
|---|---|---|
| 1. Editar código | `cd /home/server/proyectos/freellmapi && $EDITOR <archivo>` | variable |
| 2. Instalar deps | `npm ci` | ~30s (la primera vez ~3min) |
| 3. Build local | `npm run build` | ~10-15s |
| 4. Rebuild Docker | `docker compose up -d --build` | ~2 min |
| 5. Verificar | `docker ps` + `curl /api/ping` | ~3s |

**Tiempo total end-to-end:** ~3 min después del primer build.

## Por qué build local y no `docker compose pull`

La imagen `ghcr.io/tashfeenahmed/freellmapi:latest` de DockerHub queda desactualizada apenas el upstream hace un commit (es rebuild automática por el maintainer). Si modificás el código y hacés `docker compose pull && docker compose up -d`, **estás corriendo la imagen vieja, no tu código**.

El `docker-compose.yml` del repo tiene `build: { context: ., dockerfile: Dockerfile }`, así que `docker compose up -d --build` usa el código local y buildea la imagen. Esto es lo correcto.

## Paso a paso

### 1. Clonar (solo primera vez)

```bash
mkdir -p /home/server/proyectos && cd /home/server/proyectos
git clone https://github.com/tashfeenahmed/freellmapi.git
cd freellmapi
```

Si ya tenés el repo y querés sync con upstream:

```bash
cd /home/server/proyectos/freellmapi
git fetch origin
git status   # ver si hay cambios locales sin commit
# Si hay cambios: git stash, git pull, git stash pop
```

### 2. Instalar dependencias

```bash
cd /home/server/proyectos/freellmapi
npm ci
```

`npm ci` (no `npm install`) hace install determinístico desde `package-lock.json` — es lo que el Dockerfile usa. La primera vez baja todos los paquetes + compila `better-sqlite3` (módulo nativo con `node-gyp`). Builds subsiguientes son instantáneos.

**Pitfall:** `npm ci` falla si el `package-lock.json` no está sincronizado con `package.json`. Si pasa, `rm package-lock.json && npm install && npm ci` (regenerar lock).

### 3. Build local (TypeScript compile + Vite build del cliente)

```bash
npm run build
```

Esto corre en secuencia:
- `tsc` (server) — compila TypeScript a `server/dist/`
- Vite build (client) — compila React a `client/dist/`

Si solo modificaste código del server:
```bash
npm run build:server
```

Si solo modificaste el cliente:
```bash
npm run build:client  # (ojo: el script se llama `build:client`, no `build -w client`)
```

Verificar que `server/dist/index.js` existe:
```bash
ls -la server/dist/index.js client/dist/index.html
```

### 4. Build de la imagen Docker

```bash
cd /home/server/proyectos/freellmapi
docker compose up -d --build
```

El Dockerfile es multi-stage:
1. `deps` — `npm ci` (instala dev + prod deps)
2. `build` — copia código, corre `npm run build`, hace `npm prune --omit=dev`
3. `runtime` — copia solo `node_modules` ya pruneado + `server/dist` + `client/dist` + volumen `/app/server/data`

Tarda ~2 min la primera vez (compila better-sqlite3 desde fuente en el stage deps). Builds subsiguientes son más rápidos porque Docker cachea las capas.

**Pitfall:** si el healthcheck sigue diciendo "healthy" después del `up -d --build`, esperar 30s. El healthcheck corre cada 30s, así que puede tardar hasta 1 minuto en reflejar el estado real.

### 5. Verificación

```bash
# Container healthy?
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep freellmapi
# Debe decir "(healthy)" en Status

# API responde?
curl -sS -o /dev/null -w "HTTP %{http_code} en %{time_total}s\n" http://127.0.0.1:3101/api/ping
# HTTP 200 en <5ms

# Logs del container (errores de runtime, health check)
docker logs --tail 30 freellmapi-freellmapi-1

# Probar un chat completion real
PROXY_KEY="freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d"
curl -X POST http://127.0.0.1:3101/v1/chat/completions \
  -H "Authorization: Bearer $PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"ping"}],"max_tokens":10}'
```

## Iteración rápida (modificar y redeployar en <1 min)

```bash
# 1. Editar (vim, vscode, lo que uses)
vim /home/server/proyectos/freellmapi/server/src/providers/anthropic.ts

# 2. Rebuild server (rápido, no necesita Docker)
cd /home/server/proyectos/freellmapi && npm run build:server

# 3. Forzar recreación del container
docker compose up -d --force-recreate --no-deps freellmapi

# 4. Verificar logs
docker logs --tail 30 freellmapi-freellmapi-1
```

**Truco:** `--no-deps` evita que Docker toque otros containers del compose. `--force-recreate` mata el container viejo y arranca el nuevo (necesario porque el build reemplazó la imagen y Docker a veces no se da cuenta).

## Troubleshooting

### Container no arranca con "address already in use"

```bash
ss -tlnp | grep 3001
```

Si está ocupado por otro proceso, ver `references/azure-anthropic-foundry.md` sección "Pitfall: puerto 3001" o cambiar `PORT` en `.env` a 3101+.

### Build falla con "tsc: not found"

```bash
cd /home/server/proyectos/freellmapi
npm ci  # re-instala deps (incluye typescript)
```

### "Cannot find module 'better-sqlite3'"

`better-sqlite3` es un módulo nativo que necesita compilar. En el Dockerfile se compila con `python3 make g++`. Si `npm ci` se queja:

```bash
# Ubuntu/Debian
sudo apt-get install python3 make g++

# Rebuild
cd /home/server/proyectos/freellmapi
rm -rf node_modules package-lock.json
npm install
npm run build
docker compose up -d --build
```

### Health check sigue "starting" indefinidamente

El healthcheck corre cada 30s. Si después de 2 min sigue "starting":

```bash
docker logs freellmapi-freellmapi-1 | tail -50
```

Probable causa: error de runtime (import path mal, schema Zod roto, etc.). El log lo dice.

### El cambio no se refleja después de redeploy

Causa típica: el container viejo sigue corriendo con la imagen anterior. Forzar recreación:

```bash
docker compose up -d --force-recreate --no-deps freellmapi
```

Si sigue roto, **verificar que el build local terminó sin errores**:

```bash
cd /home/server/proyectos/freellmapi
npm run build:server 2>&1 | tail -20
# Debe terminar sin "error TS..."
```

### DB persistente borrada por accidente

```bash
# El volumen freellmapi-data vive en:
docker volume inspect freellmapi_freellmapi-data

# Si se borró (docker compose down -v), hay que re-setup el admin:
curl -X POST http://127.0.0.1:3101/api/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"email":"tu@email.com","password":"minimo-8-chars"}'
```

## Cuándo NO buildear local

Si solo querés **reiniciar** el container sin cambios de código:

```bash
docker compose restart freellmapi
```

Si querés **bajar la última imagen pre-built** y arrancar (sin cambios locales):

```bash
docker compose pull
docker compose up -d
```

Si querés **editar y rebuild** (cambio de código en server/client):

```bash
# El flujo completo de arriba
npm ci && npm run build && docker compose up -d --build
```

## Variables de entorno (.env)

El `.env` no se commitea (está en `.gitignore`). El template es `.env.example`. Variables mínimas:

```bash
ENCRYPTION_KEY=<64-char-hex>   # obligatorio, AES-256-GCM para keys en reposo
PORT=3101                       # default 3001, pero ese está ocupado en ai-server
HOST_BIND=0.0.0.0               # para que Tailscale (100.110.8.13) pueda llegar
PROXY_RATE_LIMIT_RPM=240        # default 120
DASHBOARD_ORIGINS=http://100.110.8.13:3101,http://localhost:3101
```

Generar `ENCRYPTION_KEY`:

```bash
ENCRYPTION_KEY=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
```

## Resumen de comandos (cheat sheet)

```bash
# === Editar + deploy ===
cd /home/server/proyectos/freellmapi
$EDITOR server/src/...  # tu cambio
npm run build:server                       # compila TS
docker compose up -d --force-recreate --no-deps freellmapi  # redeploy
docker logs --tail 30 freellmapi-freellmapi-1  # ver logs

# === Solo restart (sin cambios) ===
docker compose restart freellmapi

# === Status ===
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep freellmapi
curl -sS http://127.0.0.1:3101/api/ping

# === Pull imagen upstream nueva ===
cd /home/server/proyectos/freellmapi
git stash  # si hay cambios locales
git pull
git stash pop  # si querés recuperarlos
docker compose pull
docker compose up -d
```

## Por qué no forkear el repo

Si lo único que modificás es agregar un provider adapter o un fix chico, **no forkees**. Hacé el cambio en el fork local (`/home/server/proyectos/freellmapi/.git` apunta al repo upstream). El commit queda en tu working tree como cambio no pusheado, y si después querés compartirlo, recién ahí fork + push + PR.

Si el cambio es grande (multi-archivo, afecta migraciones, etc.), **fork sí o sí** porque mantener un patch grande contra upstream es un infierno.

## Referencias

- FreeLLMAPI repo: https://github.com/tashfeenahmed/freellmapi
- Deploy completo + setup admin + carga de keys: `references/freellmapi-deploy-and-usage.md`
- Azure Anthropic Foundry: `references/azure-anthropic-foundry.md`
- Provider adapter pattern: skill `nelson-llm-generation` → "Provider adapter pattern (FreeLLMAPI, lessons from Anthropic integration)"
