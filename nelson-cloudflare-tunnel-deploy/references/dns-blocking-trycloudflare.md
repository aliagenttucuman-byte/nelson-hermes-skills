# DNS bloqueando trycloudflare.com — Caso real (2026-06-18)

## Síntoma
El cliente ve: "No se encontró la dirección IP del servidor de screens-cafe-browse-postal.trycloudflare.com — ERR_NAME_NOT_RESOLVED"

El túnel está conectado (los logs de cloudflared muestran la URL), pero el cliente no puede resolver el hostname.

## Causa
El DNS de la red del cliente (corporativa, ISP, o router) bloquea o no resuelve dominios de trycloudflare.com.

## Diagnóstico rápido
Pedirle al cliente que pruebe desde datos móviles (sin WiFi). Si abre en datos pero no en WiFi, el problema es el DNS de esa red específica.

## Soluciones
1. Usar datos móviles para la demo (solución inmediata)
2. Cambiar DNS del equipo a 8.8.8.8 temporalmente
3. Para demos recurrentes: usar túnel con nombre fijo en Cloudflare (requiere cuenta) — la URL es estable y más confiable que trycloudflare

## Nota importante
Desde el servidor ai-server tampoco se puede hacer curl a trycloudflare.com directamente (Tailscale DNS bloquea resolución externa). Workaround: `curl --resolve 'hostname:443:IP' https://hostname/` usando la IP obtenida via `dig @8.8.8.8 hostname +short`.
