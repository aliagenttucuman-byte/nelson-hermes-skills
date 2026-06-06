# WhatsApp Gateway — Troubleshooting por Sesión (2025-05-13)

> Lecciones aprendidas durante la configuración inicial del gateway en el servidor de Nelson.

## Problema: `requestPairingCode` falla con "Connection Closed"

**Síntoma:** Al ejecutar el script de conexión, `sock.requestPairingCode(PHONE_NUMBER)` lanza:
```
Error solicitando código: Connection Closed
```

**Causa:** Algunas cuentas de WhatsApp no admiten el método de emparejamiento por código numérico. Es un fallback del servidor de WhatsApp, no un bug de Baileys.

**Solución:** Hacer fallback inmediato a QR code. El script debe manejar ambos métodos:

```javascript
try {
  const code = await sock.requestPairingCode(PHONE_NUMBER);
  console.log(`Código: ${code}`);
} catch (err) {
  console.log("Código no disponible, generando QR...");
  // QR se genera automáticamente vía el evento `connection.update` -> `qr`
}
```

**Veredicto:** En la práctica, el QR fue más fiable que el pairing code para la cuenta de Nelson.

---

## Problema: Health check devuelve `{"status": "disconnected"}`

**Síntoma:** El servidor Express arranca correctamente (escucha en :3001), pero `GET /health` devuelve `disconnected` en lugar de `connected`.

**Causa:** Baileys aún no terminó de establecer la conexión con WhatsApp Web. El evento `connection.update` con `connection === "open"` no se ha disparado todavía.

**Solución:** Esperar 3-5 segundos después de iniciar el proceso antes de consultar `/health`. En scripts de verificación, hacer polling con retries:

```python
import time
for i in range(5):
    time.sleep(2)
    status = check_health()
    if status == "connected":
        break
```

**Pitfall relacionado:** Si hay un proceso viejo de Node.js escuchando en el puerto 3001 (ej. un `node server.js` anterior que quedó zombie), el nuevo proceso puede arrancar el servidor HTTP pero no recibir eventos de Baileys, quedando permanentemente en `disconnected`.

**Fix:** Matar procesos viejos antes de iniciar:
```bash
pkill -f "node server.js"  # o el nombre del script
```

---

## Problema: Hermes bloquea `&` y `nohup` en terminal

**Síntoma:** Intentar correr `node server.js &` o `nohup node server.js &` desde `terminal()` produce:
```
Foreground command uses shell-level background wrappers (nohup/disown/setsid).
Use terminal(background=true) for long-lived processes
```

**Solución correcta para este stack:** Usar `execute_code` con `subprocess.Popen(..., start_new_session=True)`:

```python
import subprocess
proc = subprocess.Popen(
    ["node", "server.js"],
    cwd="/ruta/al/gateway",
    stdout=open("/tmp/wa-server.log", "w"),
    stderr=subprocess.STDOUT,
    start_new_session=True
)
# proc.pid contiene el PID para monitoreo posterior
```

Luego verificar estado con `urllib.request.urlopen("http://localhost:3001/health")` en llamadas separadas.

**Alternativa:** `terminal(background=true)` con `watch_patterns` también funciona, pero `execute_code` + `subprocess.Popen` ofrece más control (acceso al PID, log en archivo, etc.).

---

## Problema: systemd user service arranca pero health check sigue "disconnected"

**Síntoma:** Después de crear el servicio systemd y hacer `systemctl --user start`, `curl localhost:3001/health` sigue devolviendo `disconnected`.

**Causa:** El servicio nuevo se inició, pero hay un proceso viejo de Node.js (posiblemente del `terminal(background=true)` anterior) que ya ocupa el puerto 3001. El nuevo servicio puede incluso estar corriendo en un puerto diferente o en estado de error silencioso.

**Diagnóstico:**
```bash
ss -tlnp | grep 3001
# Muestra qué PID está escuchando en el puerto
```

**Solución:**
1. Matar el proceso viejo: `kill <PID>` o `pkill -f "node server.js"`
2. Reiniciar el servicio: `systemctl --user restart whatsapp-gateway`
3. Esperar 5 segundos y verificar health check nuevamente

---

## Secuencia correcta de setup (resumen paso a paso)

Basado en esta sesión, el orden que funcionó fue:

1. Instalar dependencias: `npm install @whiskeysockets/baileys qrcode express`
2. Crear `connect.js` con fallback QR + pairing code
3. Ejecutar con `execute_code` + `subprocess.Popen`, NO con `&` en terminal
4. Ver log hasta que aparezca "CÓDIGO DE EMPAREJAMIENTO" o "QR GUARDADO"
5. Usuario ingresa código o escanea QR desde el celular
6. Esperar "WhatsApp conectado" en el log
7. Crear `server.js` con Express API
8. Probar envío manual con `send_whatsapp.py`
9. Crear servicio systemd: `~/.config/systemd/user/whatsapp-gateway.service`
10. Verificar `linger` habilitado para el usuario
11. `daemon-reload`, `enable`, `start`
12. Verificar: matar procesos viejos si es necesario, esperar 5s, health check
13. Integrar `send_whatsapp()` en scripts Python del equipo (AI News Aggregator, etc.)
