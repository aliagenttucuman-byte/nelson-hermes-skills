# Cloudflare Quick Tunnel — límite de 100MB en uploads

## Síntoma

El XHR del frontend dispara `onerror` genérico → "Error de red al subir archivo".
El nginx y el backend están perfectos — `curl localhost:PUERTO/api/upload` devuelve 200.

## Causa

Los quick tunnels de trycloudflare.com tienen un límite de ~100MB por request.
Los TIFs de ortofotos pesan 30-500MB → Cloudflare corta la conexión silenciosamente.
No hay código HTTP útil — el browser solo ve que la conexión se cerró.

## Fixes

1. **Acceso por Tailscale (recomendado para demos con Nelson)**
   - ai-server Tailscale IP: `100.110.8.13`
   - URL: `http://100.110.8.13:PUERTO`
   - Sin límite de tamaño, más rápido, sin intermediarios

2. **Endpoint de carga local**
   - `GET /api/v1/local-files` lista TIFs disponibles en el server
   - `POST /api/v1/load-local` con `{filename}` carga sin upload HTTP
   - Útil cuando el TIF ya está en el server de otras sesiones

3. **Pre-subir con SCP antes de la demo**
   ```bash
   scp archivo.tif server@100.110.8.13:/tmp/yolov-uploads/
   ```

## Diagnóstico rápido

```bash
# Verificar que es Cloudflare y no el backend
curl -X POST http://localhost:9020/api/v1/upload \
  --form "file=@/path/to/archivo.tif" \
  -w "\nHTTP %{http_code}\n" --max-time 60

# Si devuelve 200 → el problema es Cloudflare
# Si devuelve 413 → ajustar client_max_body_size en nginx
```

## Nota sobre IPs Tailscale

- ai-server: `100.110.8.13` ← servidor donde corren las PoCs
- nelsondev: `100.76.143.33` ← PC de Nelson (Windows)
No confundir — el servidor es el .13.
