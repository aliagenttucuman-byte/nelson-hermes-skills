# Bisonte — Pitfalls Cloudflare Tunnel

## Pitfall 1: WebSocket con puerto hardcodeado rompe CF

**Síntoma:** HTML carga por CF pero la app no funciona — API calls fallan silenciosamente, WS no conecta.
**Causa:** `useContadoWS.ts` tenía `window.location.hostname + ':9000'`. Desde CF ese puerto no es accesible.

**Fix aplicado en useContadoWS.ts:**
```ts
// MAL — rompe CF y cualquier proxy reverso
const WS_URL = `${proto}://${window.location.hostname}:9000/api/v1/ws/contado`

// BIEN — usa el host completo del browser (funciona local Y por CF)
const WS_URL = `${proto}://${window.location.host}/api/v1/ws/contado`
// window.location.host = hostname + puerto (solo si no es 443/80)
// Por CF: screens-cafe.trycloudflare.com (sin puerto, usa 443)
// Local: localhost:9090
```

**Regla general:** Nunca hardcodear puertos del backend en el frontend. Usar siempre `window.location.host` o `import.meta.env.VITE_API_URL`.

---

## Pitfall 2: Proxy viejo sirve dist anterior después de rebuild

**Síntoma:** Fix aplicado, rebuild OK, pero el browser sigue recibiendo el JS viejo.
**Causa:** spa_proxy.py sirve los archivos del dist en memoria — reiniciarlo es obligatorio.

**Secuencia correcta para fix de frontend con CF activo:**
```bash
# 1. Rebuild
cd /home/server/proyectos/excel-merger-poc/frontend && npm run build

# 2. Reiniciar proxy (CF NO necesita reiniciarse)
kill $(pgrep -f spa_proxy.py)
cd /home/server/proyectos/excel-merger-poc && python3 spa_proxy.py &

# 3. Verificar que el dist nuevo no tiene el bug
grep -r '9000' frontend/dist/assets/ || echo "Fix OK"
```

---

## Pitfall 3: CF no registra requests = túnel caído o DNS muerto

**Síntoma:** URL no resuelve (`ERR_NAME_NOT_RESOLVED`) o log CF no muestra requests entrantes.
**Causa 1:** El proceso cloudflared murió (trycloudflare no garantiza uptime).
**Causa 2:** DNS de Tailscale en ai-server no resuelve externos — no confundir con CF caído.

**Fix:** Regenerar túnel. La URL nueva es válida de inmediato.
```bash
pkill cloudflared
cloudflared tunnel --url http://localhost:9090 --no-autoupdate 2>&1 | tee /tmp/cf_bisonte.log &
grep 'trycloudflare.com' /tmp/cf_bisonte.log  # esperar URL nueva
```

**Nota:** `curl` desde ai-server falla por DNS Tailscale. Usar `--resolve` o `dig @8.8.8.8` para verificar.
```bash
IP=$(dig @8.8.8.8 <subdomain>.trycloudflare.com +short | head -1)
curl --resolve "<subdomain>.trycloudflare.com:443:$IP" https://<subdomain>.trycloudflare.com/
```

---

## Estado de servicios (verificado 2026-06-17)

| Servicio | PID (referencial) | Puerto | Verificar |
|----------|-------------------|--------|-----------|
| Backend FastAPI | ~2565849 | 9000 | `curl localhost:9000/health` |
| SPA Proxy | dinámico | 9090 | `curl localhost:9090/` → HTML |
| CloudFlared | dinámico | — | `cat /tmp/cf_bisonte.log \| grep trycloudflare` |
