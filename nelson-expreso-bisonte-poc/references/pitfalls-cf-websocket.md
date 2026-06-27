# Pitfalls: Cloudflare Tunnel + WebSocket en Bisonte

## 1. WebSocket hardcodeado con puerto 9000 (RESUELTO 2026-06-18)

**Síntoma:** La app carga por CF pero las llamadas de WebSocket fallan. El frontend muestra "desconectado".

**Causa:** `frontend/src/hooks/useContadoWS.ts` tenía hardcodeado `:9000`:
```ts
// ❌ ROTO — puerto 9000 no accesible externamente
return `${proto}://${hostname}:9000/api/v1/ws/contado`
```

**Fix aplicado:**
```ts
// ✅ CORRECTO — usa el mismo host:puerto del browser
const host = window.location.host
return `${proto}://${host}/api/v1/ws/contado`
```

**Pasos post-fix:**
1. `cd frontend && npm run build`
2. Reiniciar spa_proxy (kill viejo + relanzar)
3. Verificar que el dist nuevo no tiene `9000`: `grep -r '9000' frontend/dist/assets/`

---

## 2. DNS Tailscale bloquea resolución de dominios externos

**Síntoma:** `curl https://xxx.trycloudflare.com` devuelve `Could not resolve host` desde ai-server, pero el túnel está funcionando correctamente.

**Causa:** Tailscale DNS intercepta y no resuelve dominios externos.

**Para testear el túnel desde el mismo server:**
```bash
# Resolver con DNS externo
IP=$(dig @8.8.8.8 xxx.trycloudflare.com +short | head -1)
# Conectar directo por IP
curl --resolve "xxx.trycloudflare.com:443:$IP" https://xxx.trycloudflare.com/
```

**Fix permanente (requiere sudo):**
```bash
sudo resolvectl dns wlo1 8.8.8.8
```

**Regla:** Si `curl` falla pero el CF log dice `Registered tunnel connection`, el túnel está OK. El problema es solo resolución DNS local.

---

## 3. spa_proxy sirve dist viejo después de rebuild

**Síntoma:** El fix del WS está en el código pero la app sigue comportándose igual.

**Causa:** spa_proxy cargó el dist en memoria al arrancar y no recarga automáticamente.

**Fix:** Siempre reiniciar spa_proxy después de un `npm run build`:
```bash
kill $(pgrep -f spa_proxy)
# relanzar en background
python3 /home/server/proyectos/excel-merger-poc/spa_proxy.py &
```
