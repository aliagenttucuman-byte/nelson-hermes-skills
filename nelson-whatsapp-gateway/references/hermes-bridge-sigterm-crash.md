# Problema conocido: Bridge de Hermes cae con SIGTERM (code -15)

> Documentado: 2026-05-15. Patrón recurrente observado en producción.

## Síntoma

El bridge nativo de WhatsApp de Hermes (puerto 3000) se cae repetidamente con error:
```
WhatsApp bridge process exited unexpectedly (code -15)
```

`code -15` = SIGTERM. El proceso Node.js del bridge recibe una señal de terminación desde afuera, NO un crash interno.

## Contexto de arquitectura

Hay DOS procesos de Baileys corriendo simultáneamente en el mismo servidor:

| Servicio | Puerto | Script | Sesión | Propósito |
|----------|--------|--------|--------|-----------|
| **Gateway standalone** | 3001 | `server.js` (custom) | `auth/` | Envío programático desde scripts Python |
| **Bridge de Hermes** | 3000 | `bridge.js` (interno de Hermes) | `~/.hermes/whatsapp/session/` | Polling de mensajes entrantes para Hermes |

## Observaciones clave

- El **gateway standalone (3001) permanece estable** durante horas/días.
- El **bridge de Hermes (3000) se cae cada ~1-2 horas** con SIGTERM.
- No hay logs de crash en el bridge — termina limpiamente con SIGTERM.
- systemd mata el cgroup del gateway cuando el proceso principal (Python) detecta el bridge caído y hace shutdown graceful.

## Hipótesis de causa raíz

1. **Conflicto de sesión:** Ambos procesos de Baileys podrían estar compitiendo por el mismo state de WhatsApp Web. Aunque usan directorios de auth diferentes (`auth/` vs `~/.hermes/whatsapp/session/`), WhatsApp Web en el servidor de Meta podría estar invalidando una sesión cuando detecta otra conexión concurrente desde la misma IP/cuenta.

2. **systemd cgroup kill:** Cuando el adaptador Python detecta que el bridge salió, marca el error como fatal y hace shutdown del gateway completo. systemd mata todo el cgroup, incluyendo procesos hijos.

3. **OOM o watchdog del sistema:** Aunque no hay evidencia de OOM en logs.

## Diagnóstico rápido

```bash
# Verificar estado del bridge de Hermes
curl -s http://localhost:3000/health
# Esperado: {"status":"connected","queueLength":0}
# Si falla o queueLength > 0 → bridge caído o atascado

# Verificar gateway standalone
curl -s http://localhost:3001/health
# Esperado: {"status":"connected"}

# Ver logs recientes del gateway de Hermes
journalctl --user -u hermes-gateway --since "30 minutes ago" --no-pager

# Buscar el patrón SIGTERM
grep "code -15" ~/.hermes/logs/*.log

# Ver procesos node relacionados
ps aux | grep -E "node.*bridge|node.*server"
```

## Solución temporal: monitoreo + reinicio automático

Mientras no se resuelva la causa raíz, implementar un health-check script que corra cada 2-3 minutos vía cron:

```bash
#!/bin/bash
# ~/.hermes/scripts/whatsapp-bridge-health.sh
if ! curl -sf http://localhost:3000/health > /dev/null 2>&1; then
    echo "$(date): Bridge de Hermes caído, reiniciando..."
    systemctl --user restart hermes-gateway.service
fi
```

Agregar a crontab:
```bash
*/3 * * * * /home/server/.hermes/scripts/whatsapp-bridge-health.sh >> /home/server/.hermes/logs/bridge-health.log 2>&1
```

## Solución permanente (pendiente de investigación)

- Separar completamente las sesiones: usar diferentes números de teléfono para gateway vs bridge, O
- Migrar el bridge de Hermes a usar el gateway standalone (3001) en vez de levantar su propio proceso de Baileys, O
- Configurar el gateway standalone como "external bridge" del adaptador Python de Hermes (puente 3000 apuntando a 3001).

## Diferencia clave para recordar

> **Gateway (3001) = envío. Bridge (3000) = recepción.**  
> Si solo necesitás enviar mensajes (como el 90% de los casos del equipo), el gateway en 3001 es suficiente y estable.  
> Si el bridge en 3000 se cae, los mensajes entrantes (de Tony a JARVIS) dejan de funcionar, pero los envíos salientes siguen andando.

## Historial de instancias

- 2026-05-15 13:05: Crash, reinicio manual por usuario.
- 2026-05-15 15:30: Crash + reconexión automática.
- 2026-05-15 16:40: Crash, reinicio manual por JARVIS.
- Patrón: ~cada 1-2 horas durante uso activo.
