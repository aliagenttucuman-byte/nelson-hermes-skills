# Troubleshooting: WhatsApp Messages Stop Arriving

## Síntoma
El gateway responde `{"status":"connected"}` en `/health` pero los mensajes no llegan a destino, o dejaron de llegar después de un tiempo.

## Diferenciar gateway vs bridge vs origen

El sistema tiene DOS servicios separados:

| Servicio | Puerto | Propósito | Cómo testear |
|----------|--------|-----------|--------------|
| **Baileys Gateway** (custom) | 3001 | Envío programático desde scripts Python/Node | `curl -X POST http://localhost:3001/send -d '{"to":"549...","message":"test"}'` |
| **Hermes Bridge** | 3000 | Conexión nativa de Hermes con WhatsApp, polling de mensajes entrantes | `curl http://localhost:3000/health` → revisar `queueLength` |

### Paso 1: Verificar que el gateway puede enviar
```bash
curl -s -X POST http://localhost:3001/send \
  -H "Content-Type: application/json" \
  -d '{"to": "5493816240691", "message": "Test directo"}'
```
Si responde `{"success":true,...}` → el gateway funciona. El problema está **antes** (script que genera el mensaje) o **después** (destinatario no recibe por bloqueo).

### Paso 2: Verificar queue del bridge de Hermes
```bash
curl -s http://localhost:3000/health
```
Si `queueLength > 0` → mensajes entrantes están atascados esperando ser consumidos por el adaptador Python. Eso significa que Hermes no está leyendo el polling. Reiniciar Hermes, no el gateway.

### Paso 3: Verificar logs del aggregator / cronjob
```bash
journalctl --user -u whatsapp-gateway --since "6 hours ago"
systemctl --user status whatsapp-gateway
```
Buscar último mensaje `📤 Enviado a ...` en los logs. Si no hay mensajes recientes, el script que dispara el envío (ej. `ai_news_collector.py`) no se ejecutó o falló silenciosamente.

### Paso 4: Verificar cronjob
```bash
# Listar jobs de Hermes cron
hermes cron list
# o si usa systemd timer:
systemctl --user list-timers
```
Revisar `last_run_at` y `last_status`. Si `last_status` no es `ok`, el script del job falló.

## Patrones normales en logs de Baileys (no son error)

Estos mensajes aparecen constantemente y NO indican problema:

```
stream errored out (code 503)        → WhatsApp reinició el socket, reconexión automática
Connection Terminated                 → WebSocket cerrado por inactividad, reconecta solo
uploading pre-keys / uploaded pre-keys → Rotación de claves E2EE, automático
handled 0 offline messages            → No había mensajes pendientes, ok
```

## Patrones que SÍ son problemas

```
Cannot find package 'link-preview-js'  → Dependencia faltante. Reinstalar: npm install
Not connected to WhatsApp              → Sesión corrupta. Limpiar auth/ y re-vincular.
Logged out                             → WhatsApp desvinculó el dispositivo. Re-generar QR.
```

## Flujo de diagnóstico rápido

```
¿curl a 3001/send funciona?
  ├─ SÍ → El gateway está bien. ¿Hay mensajes recientes en journalctl?
  │       ├─ SÍ → ¿Llegaron al celular? Si no, posible bloqueo/ban temporal
  │       └─ NO → El script emisor no corrió. Revisar cronjob/script.
  └─ NO → Gateway caído. Revisar auth/, reconectar, o reiniciar systemd.
```

## Comandos útiles

```bash
# Estado completo del gateway
systemctl --user status whatsapp-gateway

# Reiniciar gateway
systemctl --user restart whatsapp-gateway

# Ver auth/session
ls -la ~/brainstorming/.../whatsapp-gateway/auth/
ls -la ~/.hermes/whatsapp/session/

# Procesos node relacionados
ps aux | grep -E "node.*server|node.*bridge"

# Test envío batch
python3 send_whatsapp.py --to pablo --message "Test" --batch
```