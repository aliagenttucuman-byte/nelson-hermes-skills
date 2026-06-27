# WebSocket Cloudflare Fix — Bisonte

## Problema
El hook `useContadoWS.ts` tenía el WS hardcodeado a `hostname:9000`.
Funciona en local pero rompe desde CF/internet porque ese puerto no es accesible externamente.

## Fix aplicado (2026-06-18)

Archivo: `frontend/src/hooks/useContadoWS.ts`

```typescript
// MAL — rompe desde Cloudflare/internet
const WS_URL = (() => {
  const proto    = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const hostname = window.location.hostname
  return `${proto}://${hostname}:9000/api/v1/ws/contado`
})()

// BIEN — usa el mismo host+puerto del browser (funciona local y CF)
const WS_URL = (() => {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host  = window.location.host  // hostname + puerto del browser
  return `${proto}://${host}/api/v1/ws/contado`
})()
```

## Pasos después del fix
1. `cd frontend && npm run build`
2. `cp -r dist/* ../backend/app/static/`
3. Matar spa_proxy viejo: `kill $(pgrep -f spa_proxy)`
4. Relanzar: `python3 spa_proxy.py &`

## Pitfall: spa_proxy no recarga en caliente
El spa_proxy sirve el dist que había al momento de arrancar.
Después de cualquier `npm run build` hay que reiniciar el proxy manualmente.

## Síntoma de diagnóstico
- La página carga (HTML OK) pero las llamadas a la API fallan
- ERR_NAME_NOT_RESOLVED desde internet → problema de DNS/CF, no de código
- WebSocket falla silenciosamente → revisar este fix primero
