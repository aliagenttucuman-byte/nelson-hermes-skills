# Exponer Servicios Locales para Demos Remotas

Patrones probados para hacer accesible un servicio local (localhost:PORT) desde cualquier navegador, sin configurar firewall ni router.

## Cloudflared Quick Tunnel (recomendado, mas estable)

```bash
# Instalar
curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb

# Levantar tunel temporal (no requiere cuenta)
cloudflared tunnel --url http://localhost:8080
# -> genera URL tipo https://xxxx.trycloudflare.com
```

**Persistir con screen:**
```bash
screen -dmS cloudflared bash -c 'cloudflared tunnel --url http://localhost:8080 2>&1 | tee /tmp/cloudflared.log'
# Ver URL:
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cloudflared.log
```

**Notas:**
- No requiere autenticacion ni cuenta.
- URLs son efimeras; cada ejecucion genera una nueva.
- Para produccion/demos estables, usar named tunnels con cuenta Cloudflare.

## Serveo (SSH reverse tunnel)

```bash
ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 serveo.net
# -> genera URL tipo https://xxxx.serveousercontent.com
```

**Ventajas:** No requiere instalar nada (solo SSH).
**Desventajas:** Menos estable; a veces pide confirmacion interactiva.

## Ngrok

```bash
# Requiere authtoken (gratis en ngrok.com)
ngrok http 8080
```

**Ventajas:** Muy estable, dashboard web, permite named URLs con plan pago.
**Desventajas:** Requiere registro y authtoken.

## Localtunnel

```bash
npx localtunnel --port 8080
```

**Ventajas:** Solo requiere Node.js.
**Desventajas:** A veces cae o genera pagina de anuncios.

## Troubleshooting

### Vite dev server bloquea el host (403)

Si el tunel responde `Blocked request. This host is not allowed.`, agregar en `vite.config.ts`:

```ts
export default defineConfig({
  server: {
    host: '0.0.0.0',
    allowedHosts: true,  // o ['xxxx.trycloudflare.com'] para mas restriccion
  },
});
```

### Docker no responde a la IP publica

Si el servicio esta en Docker, verificar que el puerto este mapeado a `0.0.0.0` (no solo `127.0.0.1`).

```yaml
ports:
  - "8080:5173"   # 0.0.0.0:8080 -> contenedor:5173
```

### Firewall del servidor

```bash
# Verificar que el puerto este abierto
sudo ufw status   # o
sudo iptables -L INPUT -n
```

## Recomendacion del equipo Nelson

Para demos rapidas a clientes: **Cloudflared quick tunnel + screen**.
Para demos estables recurrentes: **Ngrok con authtoken** o **Tailscale** (si el cliente tambien lo tiene).
