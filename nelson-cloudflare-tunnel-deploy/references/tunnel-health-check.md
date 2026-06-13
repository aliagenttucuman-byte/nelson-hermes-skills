# Verificación de tunnels Cloudflare antes de pasar URL

## Regla de oro
**Nunca pasar una URL a Nelson sin verificarla primero desde afuera.**
Los quick tunnels se caen silenciosamente — el log puede mostrar reconexiones
pero la URL vieja ya no responde.

## Rutina de verificación completa

```bash
# 1. Verificar servicio local
curl -s -o /dev/null -w '%{http_code}' http://localhost:PUERTO/health
# Debe ser 200. Si no → problema en el servicio, no en el tunnel.

# 2. Capturar URL actual del tunnel desde el log
URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf_PROYECTO.log | tail -1)
echo "URL: $URL"

# 3. Verificar desde afuera (con DNS override por Tailscale)
DOMINIO=$(echo $URL | sed 's|https://||')
IP=$(dig +short $DOMINIO @1.1.1.1 | head -1)
HTTP=$(curl -sk --resolve $DOMINIO:443:$IP https://$DOMINIO/ -o /dev/null -w '%{http_code}')
echo "HTTP desde afuera: $HTTP"
# 200 → pasar URL. 000 → tunnel caído → regenerar.
```

## Señal de tunnel caído en el log

```
ERR Serve tunnel error error="connection with edge closed" connIndex=0
ERR Connection terminated error="connection with edge closed" connIndex=0
```
Si estos errores aparecen repetidamente por más de 5 minutos → tunnel caído. Regenerar.

## Cuándo se caen los tunnels

- Quick tunnels (sin cuenta) tienen uptime no garantizado.
- Se caen tras varias horas de inactividad o por interrupciones de red.
- El proceso `cloudflared` puede seguir corriendo aunque el tunnel no responda.
- El backend/frontend local puede estar perfecto — el problema es solo el tunnel.

## Regenerar tunnel

```bash
# Matar el viejo (importante — si no, puede generar URL diferente o conflicto)
pkill -f 'cloudflared.*PUERTO'
sleep 1

# Relanzar y capturar nueva URL
cloudflared tunnel --url http://localhost:PUERTO 2>&1 | tee /tmp/cf_PROYECTO.log &
sleep 18
grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf_PROYECTO.log | tail -1
```

## Logs por proyecto (referencia rápida)

| Proyecto | Puerto | Log |
|----------|--------|-----|
| ForestAI | :3010 | /tmp/cf_forestai.log |
| Fleet Optimizer | :8020 | /tmp/cf_fleet.log |
| Orchestrator Dashboard | :5174 | /tmp/cf_orch_dash.log |
| EduAI | :8030 | /tmp/cf_eduplatform.log |

## Sesión de referencia

Detectado 2026-05-30: Tunnel de ForestAI caído desde el día anterior
(log mostraba `connection with edge closed` repetidamente). Backend y frontend
locales respondían 200. Tunnel de Orchestrator Dashboard también caído.
Solución: pkill + relanzar + verificar con curl --resolve antes de pasar URL.
