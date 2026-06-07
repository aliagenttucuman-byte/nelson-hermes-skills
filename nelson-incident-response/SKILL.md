---
name: nelson-incident-response
description: Playbooks, runbooks y protocolo de escalamiento para caídas de servicios en producción del equipo Nelson. Triage en 5 minutos, decisión de severidad, comandos concretos de mitigación por servicio, post-mortem obligatorio. Para Diego (Ops) y JARVIS como primer respondedor.
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [ops, incident, runbook, oncall, escalamiento, nelson]
    category: devops
    requires_toolsets: [terminal]
---

# nelson-incident-response

> **Trigger:** Algo está caído en producción. Se cayó un servicio, un cliente reporta error, un tunnel dejó de responder, o una PoC dejó de andar. Antes de tocar nada: triage 5 minutos, clasificar severidad, ejecutar playbook.

## Principio rector

> "Caída a las 3am ≠ improvisación. Todo incidente tiene playbook, severidad explícita, owner designado y post-mortem escrito en las 24h posteriores."

**La diferencia entre un incidente y un desastre es tener esto escrito antes de que pase.**

## 1. Triage en 5 minutos (checklist universal)

Ejecutar sí o sí, en este orden, reloj corriendo. Esto NO es opcional.

```
[ ] 1. ¿Qué servicio está afectado?          → ver § 4: Servicios críticos
[ ] 2. ¿Es generalizada o aislada?          → ver § 2: Severidad
[ ] 3. ¿Afecta a clientes activos?          → sí = Sev-1 o Sev-2 inmediato
[ ] 4. ¿Hay alerta externa (Uptime, mail)?  → confirmar magnitud
[ ] 5. ¿Quién es el owner del servicio?     → ver § 4 (responsable)
[ ] 6. ¿Mitigación rápida posible?          → ver playbook del servicio
[ ] 7. Decisión: ¿escalar a Tony / Diego?   → ver § 2: Severidad
```

Si en 5 minutos no clasificaste la severidad, **asume Sev-2 y escala**.

## 2. Severidades

| Sev | Definición | Tiempo de respuesta | Escalamiento | Acción |
|-----|-----------|---------------------|--------------|--------|
| **Sev-1** | Servicio caído, afecta a todos los usuarios o a un cliente en producción ahora | Inmediato (<5 min) | Tony + Diego + dueño técnico del servicio | Mitigar ya, comunicar a stakeholders |
| **Sev-2** | Degradación severa, afecta funcionalidad core, varios usuarios impactados | <30 min | Diego + dueño técnico | Mitigar, monitorear, comunicar si >1h |
| **Sev-3** | Bug molesto, workaround existe, no afecta funcionalidad core | <4h | Dueño técnico | Ticket + plan, no mitigue a las apuradas |
| **Sev-4** | Cosmético, mejora, duda | Backlog | Nadie específicamente | Ticket en Kanban, listo |

### Reglas de escalamiento

- **Sev-1** → llamado a Diego (no email). Si Diego no responde en 15 min, escalar a Tony. Si Tony no responde en 15 min, escalar a Pablo si hay cliente afectado.
- **Sev-2** → mensaje a Diego. Si no responde en 30 min, escalar.
- **Sev-3 / Sev-4** → ticket, sin escala.

**Fuera de horario (madrugada, fines de semana):** Sev-1 sigue requiriendo respuesta <5 min. Sev-2 puede esperar al horario laboral salvo que el cliente esté en horario.

## 3. Comunicación durante el incidente

### Canal primario: WhatsApp grupo "Nelson Ops" (crear si no existe)

### Plantilla de mensaje inicial (incidente abierto)

```
🔴 [SEV-N] Servicio: <nombre>
Hora: <HH:MM>  Owner: <nombre>
Síntoma: <una línea, lo que el usuario ve>
Acción inicial: <qué se está haciendo>
ETA mitigación: <cuándo se resuelve o "evaluando">
```

### Plantilla de actualización (cada 30 min o cuando hay cambio)

```
🟡 [SEV-N] <servicio> — <HH:MM>
Estado: <investigando / mitigando / monitoreando / resuelto>
Progreso: <qué se hizo desde último mensaje>
Próximo paso: <qué sigue>
```

### Plantilla de cierre

```
🟢 [SEV-N] <servicio> — RESUELTO
Duración total: <X min>
Causa raíz: <una línea>
Mitigación aplicada: <qué se hizo>
Post-mortem: <link al doc, obligatorio si Sev-1 o Sev-2>
```

## 4. Servicios críticos y playbooks

Mapa de servicios actualizado → ver skill `nelson-server-services`. Aquí van los playbooks específicos.

### 4.1 RAG PoC backends (puertos 8000, 8001, 8002)

**Síntomas típicos:** timeout en /api/query, error 500, "connection refused" en frontend.

**Owner:** Julián (backend senior) / Ricky (dev).

**Triage:**
```bash
ssh server@100.110.8.13  # Tailscale
docker ps --filter "name=rag" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8001/health | jq .
curl -s http://localhost:8002/health | jq .
```

**Mitigación rápida:**
```bash
# Si container está unhealthy, reiniciar
cd /home/server/brainstorming/2026-05-13-rag-poc/
docker compose restart backend

# Si no levanta, ver logs
docker logs --tail 100 -f 2026-05-13-rag-poc-backend-1

# Si persiste, restart completo
docker compose down && docker compose up -d
```

**Causas frecuentes:**
- Falta de memoria OOM → ver `docker stats`, considerar restart con `--memory`
- Vector store (Qdrant) caído → `docker ps | grep qdrant`, reiniciar
- Ollama caído → `docker ps | grep ollama`, reiniciar (modelo se carga en 30-60s)

### 4.2 ForestAI PoC (puertos 3010 frontend, 8010 backend, 5433 PostGIS, 6380 Redis)

**Síntomas típicos:** frontend no carga, /api/analysis falla, ortofoto no renderiza.

**Owner:** Diego (PoC activa) / Beto (arquitectura).

**Triage:**
```bash
docker ps --filter "name=forestai" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
curl -s http://localhost:8010/health
docker exec forestai-poc-db-1 pg_isready -U forestai
docker exec forestai-poc-redis-1 redis-cli ping
```

**Mitigación rápida:**
```bash
cd /home/server/proyectos/forestai-poc/
docker compose restart backend
# Si frontend no actualiza con cambios de código, ver pitfall crítico en nelson-server-services
```

**Causas frecuentes:**
- Frontend sirve dist viejo después de cambios → `npm run build && docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/`
- PostGIS no arranca → `docker logs forestai-poc-db-1` (usualmente volumen corrupto)
- Celery worker colgado → `docker compose restart celery`

### 4.3 Fleet Optimizer AR (puerto 8020)

**Síntomas típicos:** túnel inaccesible, frontend muestra error de carga, OCR no responde.

**Owner:** Julián / Ricky.

**Triage:**
```bash
# Verificar que el proceso uvicorn está corriendo
ps aux | grep -E "uvicorn.*8020" | grep -v grep
curl -s http://localhost:8020/health  # → {"status":"ok","trucks":10}
```

**Mitigación rápida:**
```bash
# Si uvicorn murió, relanzar con Hermes terminal background=True
cd /home/server/brainstorming/2026-05-22-fleet-optimizer/poc/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8020
# Pitfall: usar python3 -m pip, no pip directo
```

**Tunnel Cloudflare caído:**
```bash
pkill -9 cloudflared
cloudflared tunnel --url http://localhost:8020 2>&1 | tee /tmp/cf_fleet.log &
sleep 15
grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' /tmp/cf_fleet.log | head -1
# Comunicar nueva URL a Pablo/cliente
```

### 4.4 n8n (puerto 5678)

**Síntomas típicos:** workflows no se ejecutan, error 502, "workflow not found".

**Owner:** Diego.

**Triage:**
```bash
docker ps --filter "name=n8n"
curl -s http://localhost:5678/healthz
```

**Mitigación rápida:**
```bash
cd /home/server/n8n-docker/
docker compose restart
# Verificar volumen persistente
docker volume ls | grep n8n
```

**Causas frecuentes:**
- Webhook externo caído (no es nuestro problema) → deshabilitar nodo y notificar
- Credencial expirada (OAuth) → reconfigurar en UI de n8n
- DB interna corrupta → restore desde backup del volumen (si existe, ver nelson-backup-dr pendiente)

### 4.5 JARVIS Demo Shell (puertos 3789 frontend, 8765 backend)

**Síntomas típicos:** chat no responde, /api/chat timeout, tunnel caído.

**Owner:** Mercedes (frontend) / Julián (backend).

**Triage:**
```bash
ps aux | grep -E "(vite|uvicorn).*(3789|8765)" | grep -v grep
curl -s http://localhost:8765/health
```

**Mitigación rápida:** reiniciar ambos procesos. Frontend con `npm run dev` en background, backend con uvicorn.

### 4.6 Servicios systemd (nelson-task-memory 8742, nelson-agent-router 8743)

**Síntomas típicos:** meta-orquestador no responde, agentes no se enrutan.

**Owner:** JARVIS (es el dueño técnico del meta-agente).

**Triage:**
```bash
sudo systemctl status nelson-task-memory
sudo systemctl status nelson-agent-router
curl -s http://localhost:8742/health
curl -s http://localhost:8743/health
```

**Mitigación rápida:**
```bash
# Si falló por puerto ocupado (pitfall conocido)
kill $(lsof -ti:8742) 2>/dev/null
kill $(lsof -ti:8743) 2>/dev/null
sudo systemctl restart nelson-task-memory
sudo systemctl restart nelson-agent-router
```

**Causas frecuentes:**
- Puerto ocupado por uvicorn previo en background → matar primero (ver pitfall en nelson-server-services)
- Venv roto → `cd /home/server/.hermes/hermes-agent && source venv/bin/activate && pip install -r requirements.txt`
- DB SQLite corrupto → `sqlite3 /home/server/nelson/task-memory/db/tasks.db "PRAGMA integrity_check;"`

## 5. Post-mortem (obligatorio Sev-1 y Sev-2)

Plantilla en `templates/postmortem-template.md`. Completar dentro de las **24 horas** posteriores al incidente. Sin excepciones.

**Estructura:**
- Resumen ejecutivo (3 líneas)
- Timeline del incidente (UTC, con timestamps de cada acción)
- Causa raíz (no el síntoma, la causa)
- Por qué no lo detectamos antes (gap de monitoreo o proceso)
- Acción correctiva (con owner y fecha)
- Acción preventiva (sistémica, no parche)

## 6. Antes de que pase: preparación

### Documentación obligatoria para cada servicio

- [ ] Owner técnico designado
- [ ] Runbook en este skill o linkeado desde acá
- [ ] Health check expuesto (ver `nelson-monitoring-observability`)
- [ ] Al menos 1 backup verificado (cuando nelson-backup-dr esté listo)
- [ ] Acceso documentado al server (Tailscale, sudo, paths)

### Revisión trimestral

- Todos los servicios del `nelson-server-services` tienen playbook acá
- Los playbooks reflejan el estado real (no quedaron desactualizados)
- Los contactos de escalamiento están vigentes
- Se hizo al menos 1 simulacro de Sev-2

## Pitfalls

1. **Asumir Sev-3 cuando es Sev-1.** "Anda medio lento" puede ser "DB saturada, va a caer en 10 min". Si hay duda, escalar.
2. **Mitigar sin documentar.** Si arreglás algo a las 3am sin anotar, en el post-mortem no vas a saber qué hiciste. Anotá SIEMPRE, en el momento.
3. **Escalar tarde.** Escalar a Tony a los 45 min de un Sev-1 es tarde. Mejor escalear de más y que sea "falsa alarma" que escalear tarde.
4. **No verificar el fix.** "Ya reinicié, debería andar" no es verificación. Probá el endpoint, navegá el flujo del usuario.
5. **Tocar configs de producción sin backup.** Antes de cambiar `.env`, `docker-compose.yml`, nginx config: copia a `*.backup-YYYYMMDD-HHMM`.
6. **Confundir tunnel caído con servicio caído.** Si la URL de Cloudflare dejó de responder, primero `curl localhost:PUERTO` para saber si el servicio está vivo.
7. **No comunicar el cierre.** Si abriste un incidente, cerrá el hilo aunque sea con "falsa alarma, era problema del cliente". El silencio genera ansiedad.
8. **Post-mortem asignado a "después".** Después no existe. 24h, reloj corriendo, en el calendario si hace falta.

## Comandos útiles (cheatsheet)

```bash
# === TRIAJE GENERAL ===
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker stats --no-stream
df -h  # espacio en disco
free -h  # memoria
uptime
ss -tlnp  # puertos escuchando

# === LOGS RÁPIDOS ===
docker logs --tail 100 CONTAINER
docker logs --tail 100 -f CONTAINER  # follow
journalctl -u SERVICE-NAME --since "1 hour ago"

# === REINICIOS ===
docker compose restart SERVICE
sudo systemctl restart SERVICE
pkill -f "uvicorn.*PUERTO"  # último recurso, saber qué se mata

# === TÚNELES ===
pkill -9 cloudflared
cloudflared tunnel --url http://localhost:PUERTO 2>&1 | tee /tmp/cf_NOMBRE.log &
sleep 15
grep -o 'https://[a-z0-9\-]*\.trycloudflare\.com' /tmp/cf_NOMBRE.log | head -1

# === RECURSOS ===
# Matar proceso colgado por PID
ps aux | grep NOMBRE
kill -9 PID
```

## Referencias

- `nelson-server-services` — mapa vivo de puertos y servicios
- `nelson-monitoring-observability` — health checks y logging estructurado (sin esto, no hay señal de incendio)
- `playbooks/forestai.md` — playbook extendido de ForestAI, el servicio más crítico en producción ahora (6 escenarios de mitigación)
- `templates/postmortem.md` — plantilla de post-mortem
- `templates/incident-open.md` / `incident-update.md` / `incident-closed.md` — mensajes pre-armados para WhatsApp

## Pitfall: la skill de monitoring es upstream obligatorio

Esta skill de incident-response **asume que los servicios tienen /health y logging estructurado**. Si los servicios no los tienen, el triage de 5 minutos no detecta nada y el playbook se convierte en "reiniciar cosas a ciegas".

Orden correcto al armar un servicio nuevo:
1. `nelson-monitoring-observability` (health + logging) — primero
2. `nelson-incident-response` (runbook con comandos concretos) — después

Si un servicio no tiene /health, la primera tarea del playbook tiene que ser: "agregar /health, no pelear con la causa raíz del incidente".

## Pitfall: el archivo del roadmap de skills se pierde cada 2-3 semanas

Confirmado: el `ROADMAP_SKILLS.md` original (15 mayo) se perdió, y el meta-orquestador pasó 3 semanas intentando leerlo. Esta skill nació de ese patrón. Lección: el roadmap tiene que vivir en `~/brainstorming/` con sufijo `-v2` cuando se regenera, y la primera skill del TOP se arranca en la misma sesión. Ver `nelson-brainstorming` § "Regenerar roadmaps / archivos perdidos desde sesión search".
