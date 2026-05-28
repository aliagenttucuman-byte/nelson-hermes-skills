# Servir archivos HTML estáticos vía túnel Cloudflare

## Patrón recomendado: reusar túnel existente

Cuando el entregable es un HTML standalone (sin React router, sin backend propio),
NO crear un túnel nuevo. Copiar el archivo al dist/ de una PoC que ya tenga túnel activo:

```bash
# Identificar túneles activos y sus puertos
grep -h 'Settings.*url' /tmp/cf_*.log | sort -u
# Ej: url:http://localhost:8020 (fleet), url:http://localhost:3010 (forestai)

# Ver qué directorio sirve ese backend
readlink /proc/$(pgrep -f 'uvicorn.*8020')/cwd

# Copiar el HTML al dist
cp /ruta/al/archivo.html /ruta/al/proyecto/frontend/dist/

# URL automática: https://TUNEL-EXISTENTE.trycloudflare.com/archivo.html
```

**Por qué es mejor que crear un túnel nuevo:**
- Los quick tunnels son volátiles — la URL cambia en cada restart
- Aprovechar un túnel ya estable y registrado garantiza continuidad

---

## Si necesitás un servidor nuevo de archivos estáticos

### ⚠️ CRÍTICO: siempre --bind 0.0.0.0

```bash
# MAL — solo escucha IPv4, Cloudflare se conecta por IPv6 → Connection refused
python3 -m http.server 8031

# BIEN — acepta IPv4 e IPv6
python3 -m http.server 8031 --bind 0.0.0.0 --directory /ruta/al/public
```

Sin `--bind 0.0.0.0`, el servidor escucha solo en `127.0.0.1`.
Cloudflare intenta conectarse por IPv6 (`::1`) y falla silenciosamente.
El túnel aparece como "Registered" pero retorna connection refused al browser.

---

## Diagnóstico cuando el túnel "no funciona"

Verificar en orden:

1. **¿El túnel está registrado?**
   ```bash
   grep 'Registered tunnel' /tmp/cf_proyecto.log
   # Debe aparecer: Registered tunnel connection connIndex=0 ...
   ```

2. **¿El servidor local responde?**
   ```bash
   curl -sI http://localhost:PUERTO/archivo.html | head -3
   ```

3. **¿El DNS resuelve? (falla en servidores con Tailscale)**
   ```bash
   dig +short NOMBRE.trycloudflare.com @1.1.1.1
   # Si da IP, el DNS funciona. Si no da nada, esperar propagación (~2 min)
   ```

4. **Verificar que el túnel entrega el archivo end-to-end:**
   ```bash
   IP=$(dig +short NOMBRE.trycloudflare.com @1.1.1.1 | head -1)
   curl -s --resolve NOMBRE.trycloudflare.com:443:$IP \
     https://NOMBRE.trycloudflare.com/archivo.html | wc -c
   # Si da el tamaño correcto → túnel OK, el problema era DNS local del servidor
   ```

5. **Si el curl falla desde el servidor pero funciona desde el browser de Nelson**
   → Es el DNS local del servidor (issue conocido con Tailscale), no un problema del túnel

---

## Múltiples túneles — gestión

```bash
# Ver todos los túneles corriendo
ps aux | grep cloudflared | grep -v grep

# Ver todas las URLs activas
grep -h 'trycloudflare.com' /tmp/cf_*.log | grep -o 'https://[^[:space:]]*' | sort -u

# Matar túnel específico por puerto
pkill -f 'cloudflared.*8031'

# Evitar tener múltiples túneles al mismo puerto (URLs duplicadas confunden)
pkill -f 'cloudflared.*PUERTO' 2>/dev/null; sleep 1
cloudflared tunnel --url http://localhost:PUERTO --protocol http2 2>&1 | tee /tmp/cf_nuevo.log &
```
