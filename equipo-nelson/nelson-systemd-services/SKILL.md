---
name: nelson-systemd-services
description: Patrón para correr servicios críticos del equipo Nelson (headroom, lean-ctx, whatsapp-bridge, hermes-gateway, etc.) como units de systemd con autoreinicio. Nelson exige que TODO servicio long-lived esté bajo systemd — nunca como proceso suelto.
category: equipo-nelson
tags: [systemd, services, autoreinicio, ai-server, infra, devops, reliability]
related_skills: [nelson-headroom, nelson-lean-ctx, nelson-whatsapp-gateway, nelson-monitoring-observability]
---

# Servicios systemd — Equipo Nelson

> **Trigger:** Cuando levantes un servicio long-lived nativo (no Docker) en ai-server: headroom proxy, lean-ctx, whatsapp-bridge, hermes-gateway, n8n nativo, FastAPIs custom, bots, agentes meta-orquestador, etc. Sin systemd no se queda — y Nelson exige autoreinicio garantizado.

## Regla del equipo

Nelson lo dijo textual: **"los servicios que vos necesitas siempre tienen que estar disponibles"**. Esto significa:

1. NUNCA dejar un servicio crítico corriendo como proceso suelto (PID huérfano).
2. SIEMPRE systemd con `Restart=always` + `enable` para que arranque al boot.
3. Logs centralizados en `/var/log/` con un archivo por servicio.
4. Dependencias entre servicios declaradas explícitamente (`After=` / `Wants=`).

Si reiniciás el server o un servicio muere, todo se levanta solo en 5-10 segundos.

---

## Template canónico

Path: `/etc/systemd/system/<servicio>.service`

```ini
[Unit]
Description=<descripción humana del servicio>
After=network.target
# Para servicios que dependen de otros:
# After=network.target headroom-proxy.service lean-ctx.service
# Wants=headroom-proxy.service lean-ctx.service

[Service]
Type=simple
User=server
WorkingDirectory=/home/server
# Environment vars necesarias (PATH del venv si aplica):
Environment="PATH=/home/server/.hermes/hermes-agent/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="HOME=/home/server"
# Comando con paths absolutos — nada de "python" pelado:
ExecStart=/home/server/.hermes/hermes-agent/venv/bin/python -m mi_modulo
Restart=always
RestartSec=10
StandardOutput=append:/var/log/<servicio>.log
StandardError=append:/var/log/<servicio>.log

[Install]
WantedBy=multi-user.target
```

---

## Procedimiento de instalación

```bash
# 1. Crear el service file (usar template arriba)
sudo cp /tmp/mi-servicio.service /etc/systemd/system/

# 2. Crear log file con permisos correctos
sudo touch /var/log/mi-servicio.log
sudo chown server:server /var/log/mi-servicio.log

# 3. Recargar systemd
sudo daemon-reload

# 4. Si había un proceso manual corriendo el mismo servicio, matarlo
pkill -f "mi-servicio" 2>/dev/null
sleep 2

# 5. Habilitar (arranca al boot) + arrancar ahora
sudo systemctl enable --now mi-servicio.service

# 6. Verificar
sleep 5
sudo systemctl is-active mi-servicio.service  # → active
sudo systemctl is-enabled mi-servicio.service # → enabled
curl -s http://localhost:<puerto>/health      # si tiene health endpoint
```

---

## Servicios actualmente bajo systemd (ai-server)

| Service | Puerto | Función | Skill relacionada |
|---------|--------|---------|-------------------|
| `headroom-proxy` | 8787 | Compresión tokens LLM | `nelson-headroom` |
| `lean-ctx` | (sock) | Compresión reads in-process | `nelson-lean-ctx` |
| `whatsapp-bridge` | 3000 | Bridge Baileys → Hermes | `nelson-whatsapp-gateway` |
| `hermes-gateway` | — | JARVIS gateway (WhatsApp/Telegram) | — |
| `nelson-agent-router` | — | Router meta-orquestador | `nelson-agent-routing` |
| `nelson-meta-orchestrator` | — | Orquestador del equipo | `nelson-meta-orchestrator` |
| `nelson-task-memory` | — | Memoria de tareas | `nelson-task-memory` |

Para containers Docker: `restart: unless-stopped` cumple la misma función.

---

## Orden de arranque (dependencias)

Cuando un servicio depende de otros, declararlo en `[Unit]`:

```ini
[Unit]
After=network.target headroom-proxy.service lean-ctx.service whatsapp-bridge.service
Wants=headroom-proxy.service lean-ctx.service whatsapp-bridge.service
```

`Wants=` es preferible a `Requires=` — si el dependiente falla, el dependiente principal no falla en cascada.

**Ejemplo real**: `hermes-gateway` (JARVIS) depende de headroom + lean-ctx + whatsapp-bridge. Si reiniciás el server, systemd levanta primero los 3, después JARVIS.

---

## Comandos útiles

```bash
# Ver todos los services del equipo Nelson
sudo systemctl list-unit-files --state=enabled | grep -iE "nelson|hermes|headroom|lean|whatsapp"

# Status detallado de uno
sudo systemctl status <servicio> --no-pager

# Logs en vivo
sudo journalctl -u <servicio> -f
# o si usaste StandardOutput=append:
tail -f /var/log/<servicio>.log

# Restart manual
sudo systemctl restart <servicio>

# Ver dependencias
sudo systemctl list-dependencies <servicio>

# Auditar TODO lo crítico del equipo en una línea:
for s in headroom-proxy lean-ctx whatsapp-bridge hermes-gateway nelson-agent-router nelson-meta-orchestrator nelson-task-memory; do
  active=$(sudo systemctl is-active $s 2>&1)
  enabled=$(sudo systemctl is-enabled $s 2>&1)
  printf "  %-32s %-10s %s\n" "$s" "$active" "$enabled"
done
```

---

## Pitfalls

- **PATH del venv obligatorio**: Si el ExecStart usa un binario instalado en venv (headroom, uvicorn, lean-ctx), el `Environment="PATH=..."` debe incluir el `bin/` del venv ANTES de los paths del sistema. Sin esto: `command not found`. Aplica especialmente a `headroom` cuyo binario vive en `/home/server/.hermes/hermes-agent/venv/bin/`.

- **No matar el proceso actual de JARVIS mientras hay sesión WhatsApp activa**: Si instalás el systemd de `hermes-gateway` y JARVIS ya corre como proceso manual atendiendo una conversación, matar el PID corta la conversación en vivo. Estrategia: instalar + enable el service (queda listo para el próximo boot o cuando el proceso muera naturalmente), no hacer `systemctl start` mientras estés conversando. La próxima vez que se reinicie naturalmente, systemd toma el control.

- **n8n nativo vs n8n Docker en el mismo puerto**: Si tenés n8n corriendo en Docker (`:5678`) y aparte el binario nativo también, va a haber un PID huérfano fallando en bind del puerto. `ps aux | grep n8n` para detectar duplicados — matar el nativo, dejar Docker.

- **`User=server` obligatorio**: Si no lo ponés, systemd corre como root y los archivos generados (logs, sockets, caches en `$HOME`) quedan con ownership root y rompen permisos en la próxima sesión interactiva.

- **`StandardOutput=append:/var/log/...` requiere el archivo precreado**: Sino systemd falla al arrancar con "Permission denied". Siempre `touch` + `chown server:server` antes del `enable --now`.

- **Hot-reload de service files**: Si editás el `.service`, hay que correr `sudo systemctl daemon-reload` antes de `restart`. Olvidarlo deja al service con la config vieja silenciosamente.

- **Healthcheck inmediato falla**: Después de `systemctl start`, esperar 5-10s antes de hacer `curl /health` — el proceso tarda en bindear el puerto. `HTTP 000` no significa que falló: significa que todavía está arrancando.

- **`Restart=always` no compensa errores de config**: Si el servicio crashea por config inválida, systemd lo reinicia en loop infinito. Mirar `journalctl -u <servicio> -n 50` para ver el error real antes de asumir que "anda".

---

## Healthcheck periódico (opcional pero recomendado)

Un cron job cada 5 minutos que avise por WhatsApp si algún servicio crítico está caído y systemd no pudo levantarlo (3 fallos seguidos = problema real):

```bash
# Plantilla básica — adaptar a cronjob del equipo
for s in headroom-proxy lean-ctx whatsapp-bridge hermes-gateway; do
  if ! systemctl is-active --quiet $s; then
    # Notificar via WhatsApp Gateway
    curl -X POST http://localhost:3001/send -d "msg=⚠️ Servicio $s caído"
  fi
done
```

Ver skill `nelson-scheduled-jobs` para integración con cron del equipo.

---

## Cuándo NO usar systemd

- Servicios efímeros (correr una vez, terminar) → usar el cronjob system de Hermes
- Procesos de desarrollo / debugging → `python -m foo` directo está bien
- Tests / spikes → no merece formalizar
- Servicios que ya viven en Docker Compose → `restart: unless-stopped` es equivalente
