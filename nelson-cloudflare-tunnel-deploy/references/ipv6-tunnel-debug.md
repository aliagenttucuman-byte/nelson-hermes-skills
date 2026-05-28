# Debug: Cloudflare Tunnel no sirve contenido (IPv4/IPv6)

## Síntoma
- `cloudflared` log muestra `Registered tunnel connection ... protocol=http2` → OK
- `curl https://NOMBRE.trycloudflare.com/` devuelve vacío o timeout
- `curl http://localhost:PUERTO/` funciona perfecto localmente

## Causa raíz
El servidor local escucha solo en `127.0.0.1` (IPv4 loopback). Cloudflare intenta conectarse
por IPv6 (`::1`) internamente y falla. El túnel queda registrado pero no puede llegar al proceso.

## Diagnóstico rápido
```bash
# Ver en qué interfaz escucha el servidor
ss -tlnp | grep PUERTO
# Si dice 127.0.0.1:PUERTO → problema confirmado
# Si dice 0.0.0.0:PUERTO   → escucha bien en todas las interfaces
```

## Fix
```bash
# Matar el servidor viejo
kill $(lsof -ti:PUERTO)

# Relanzar con 0.0.0.0
python3 -m http.server PUERTO --bind 0.0.0.0 --directory public &

# Para uvicorn
uvicorn challenge.api:app --host 0.0.0.0 --port PUERTO
```

## Verificación del túnel cuando DNS local falla (Tailscale)
Con Tailscale, el DNS puede no resolver `*.trycloudflare.com` desde el servidor.
Esto NO afecta a usuarios externos. Para probar el túnel desde el servidor:

```bash
IP=$(dig +short NOMBRE.trycloudflare.com @1.1.1.1 | head -1)
curl --resolve NOMBRE.trycloudflare.com:443:$IP https://NOMBRE.trycloudflare.com/health
# Respuesta OK → túnel funciona. El problema era solo DNS local.
```

## Sesión de referencia
Detectado 2026-05-28 al exponer página HTML estática con `python3 -m http.server`
sin `--bind 0.0.0.0`. El túnel aparecía como conectado en los logs pero no servía.
