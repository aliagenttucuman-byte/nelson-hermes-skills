# Cloudflared: Exposicion Temporal de Servicios Locales

> Patron rapido para exponer servicios locales (APIs, frontends, demos) a internet sin cuenta ni configuracion.

## Cuando usar

- Demo rapida para un socio/asesor que esta en otro lugar
- Probar acceso desde celular a un servicio local
- Sharear una PoC antes de deployarla en produccion
- No requiere cuenta de Cloudflare ni dominio propio

## Limitaciones

- URL efimera: cambia cada vez que se reinicia el tunnel
- Sin garantia de uptime (ToS de Cloudflare lo aclara)
- NO para produccion
- Para uso regular: Tailscale o ngrok con authtoken

## Instalacion

```bash
curl -L -o /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb
```

## Uso basico (1 servicio)

```bash
cloudflared tunnel --url http://localhost:PUERTO
```

La URL aparece en stdout: `https://XXXX-XXXX-XXXX-XXXX.trycloudflare.com`

## Uso con multiples servicios (backend + frontend)

Cada servicio necesita su propio proceso de cloudflared:

```bash
# 1. Backend
nohup cloudflared tunnel --url http://localhost:8000 > /tmp/cf-backend.log 2>&1 &
sleep 8
BACKEND_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf-backend.log | head -1)
echo "Backend: $BACKEND_URL"

# 2. Frontend
nohup cloudflared tunnel --url http://localhost:8080 > /tmp/cf-frontend.log 2>&1 &
sleep 8
FRONTEND_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf-frontend.log | head -1)
echo "Frontend: $FRONTEND_URL"
```

## Frontend apuntando a backend remoto

Cuando el frontend se expone via Cloudflare, sus requests al backend deben ir por la URL publica (no por `localhost`):

```yaml
# docker-compose.yml del frontend
services:
  frontend:
    environment:
      - VITE_API_URL=https://taylor-affects-blog-prospects.trycloudflare.com
```

Luego recrear el contenedor para que tome la nueva env var:
```bash
docker compose up -d --no-deps --force-recreate frontend
```

**Pitfall**: `docker compose restart frontend` NO aplica env vars nuevas. Solo `--force-recreate` o `down && up` funciona.

## Verificacion

```bash
curl -s $BACKEND_URL/health
curl -s $FRONTEND_URL | head -c 100
```

## Alternativas

| Herramienta | Cuenta requerida | URL fija | Mejor para |
|-------------|------------------|----------|------------|
| Cloudflared | No | No | Demos rapidas, ad-hoc |
| Tailscale | Si (gratis) | Si (IP tailscale) | Uso regular entre dispositivos propios |
| ngrok | Si (authtoken) | No (dominio gratis aleatorio) | Demos con webhook inspection |
| Pagekite | No (modo trial) | No | Alternativa ligera |

## Vite + Cloudflare: allowedHosts

Si el frontend usa Vite, Cloudflare tunnel puede rechazar con 403 porque el host no esta en la lista blanca:

```ts
// vite.config.ts
export default {
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,  // Acepta cualquier host (incluyendo *.trycloudflare.com)
  }
}
```

## Systemd auto-start (opcional)

Para que el tunnel se levante automaticamente:

```ini
# ~/.config/systemd/user/cloudflared-rag.service
[Unit]
Description=Cloudflared Tunnel - RAG Frontend
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:8080
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable cloudflared-rag.service
systemctl --user start cloudflared-rag.service
```

## Lecciones de la sesion

- Hermes tool `terminal` rechaza backgrounding con `&` o `nohup`. Usar el parametro `background=true` del tool, o guardar un script `.sh` y ejecutarlo.
- Los logs de cloudflared son la unica forma confiable de extraer la URL. Buscar el patron `https://*.trycloudflare.com`.
- El tunnel tarda ~5-8 segundos en generar la URL despues de iniciar.
