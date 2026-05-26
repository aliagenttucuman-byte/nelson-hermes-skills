---
name: nelson-automation-n8n
title: Automatizacion con n8n
published: true
description: n8n como motor de automatizacion para el equipo Nelson. Workflows para procesar datos, integrar APIs, webhooks, scheduled jobs y conectar con el stack existente (FastAPI, RAG, LLMs).
category: software-development
author: JARVIS
tags: [n8n, automation, workflow, webhook, cron, integration]
---

# Automatizacion con n8n - Equipo Nelson

## Descripcion

n8n es la plataforma de automatizacion elegida para el equipo Nelson. Corre en Docker local, se conecta con las APIs del equipo, bases de datos, LLMs y servicios externos.

## Instalacion

### Docker Compose (ya instalado)

Ver template listo para copiar en [`templates/docker-compose.yml`](templates/docker-compose.yml).

```yaml
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_SECURE_COOKIE=false
      - GENERIC_TIMEZONE=America/Argentina/Buenos_Aires
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - n8n-network

volumes:
  n8n_data:

networks:
  n8n-network:
    driver: bridge
```

**Importante:** `N8N_SECURE_COOKIE=false` es obligatorio para acceder via HTTP (no HTTPS). Sin esta variable, n8n rechaza las cookies en navegadores modernos.

### Primera ejecucion: crear usuario owner

En versiones recientes de n8n, `N8N_BASIC_AUTH` fue eliminado. La primera vez que se accede a http://localhost:5678, n8n pide crear un usuario owner/admin. Completar el formulario con los datos del usuario (email, nombre, password). Este usuario sera el unico administrador.

### Comandos utiles

```bash
# Levantar
cd ~/n8n-docker && sudo docker compose up -d

# Ver logs
sudo docker logs -f n8n

# Backup datos
sudo docker exec n8n tar czf /tmp/n8n-backup.tar.gz /home/node/.n8n
sudo docker cp n8n:/tmp/n8n-backup.tar.gz ~/backups/
```

## Workflows tipicos para el equipo

### 1. Webhook -> Procesar -> Guardar en DB

**Caso de uso:** Recibir datos de un formulario o API externa.

```
Webhook (POST) -> Code Node (validar) -> PostgreSQL Insert -> Response
```

### 2. Scheduled Job -> Scraping -> Notificacion

**Caso de uso:** Monitorear paginas de clientes, precios, disponibilidad.

```
Cron (cada hora) -> HTTP Request -> Code Node (parsear) -> If (cambio?) -> Telegram/Slack
```

### 3. Documento -> RAG Pipeline

**Caso de uso:** Subir documento a n8n, procesarlo con el pipeline RAG del equipo.

```
Webhook (archivo) -> HTTP Request (a API de document-processing) -> Qdrant Insert -> Slack confirmacion
```

### 4. Alerta -> LLM -> Accion

**Caso de uso:** Recibir alerta de sistema, analizar con LLM, ejecutar accion.

```
Webhook (alerta) -> HTTP Request (a Ollama/Gemma) -> Switch (clasificacion) -> Accion correspondiente
```

## Credenciales comunes

| Servicio | Tipo | Configuracion |
|----------|------|---------------|
| PostgreSQL | Postgres | host: db, port: 5432 |
| Qdrant | HTTP Request | host: localhost:6333 |
| Ollama | HTTP Request | host: host.docker.internal:11434 |
| Telegram | Telegram | Bot Token |
| SMTP | SMTP | Para emails |

## Integracion con el stack del equipo

### Conectar n8n con Ollama (LLMs locales)

1. En n8n crear nodo HTTP Request
2. Method: POST
3. URL: `http://host.docker.internal:11434/api/generate`
4. Body (JSON):
```json
{
  "model": "llama3.2:3b",
  "prompt": "{{ $json.texto }}",
  "stream": false
}
```

### Conectar n8n con APIs del equipo

Las APIs FastAPI del equipo se acceden desde n8n via:
- `http://host.docker.internal:8000` (backend)
- `http://host.docker.internal:8080` (frontend)

## Plan de Automatización de la Consultora (Workfows Prioritarios)

Este plan documenta los workflows clave para transformar la consultora en una máquina de automatización. Principio: si una tarea se repite más de 2 veces por semana, debe estar automatizada.

### Workflows Prioritarios

#### 1. Onboarding de Nuevo Proyecto
**Trigger:** Tony dice "empezamos proyecto X" o email con subject "[NUEVO PROYECTO]"
**Acciones:**
1. Crear carpeta `~/brainstorming/YYYY-MM-DD-nombre-proyecto/`
2. Generar `README.md` con template estándar
3. Crear repo en GitHub (si aplica)
4. Generar scaffold con `nelson-project-bootstrap`
5. Enviar confirmación a Tony por WhatsApp
**Tiempo ahorrado:** ~30 min/proyecto

#### 2. Reporte Semanal Automático
**Trigger:** Lunes 9:00 AM (America/Argentina)
**Acciones:**
1. Contar commits de la semana
2. Listar proyectos activos
3. Verificar estado de servicios (RAGs, Ollama, n8n)
4. Generar resumen breve
5. Enviar a Pablo por WhatsApp
**Tiempo ahorrado:** ~45 min/semana

#### 3. Monitoreo de Servicios + Alerta
**Trigger:** Cada 5 minutos (ya implementado como cronjob `rag-health-monitor`)
**Acciones:**
1. Revisar /health de cada RAG
2. Si caído: reiniciar contenedor automáticamente
3. Si sigue caído: alerta escalonada (Tony → Pablo)
**Mejoras con n8n:** Dashboard visual, historial de uptime, MTTR

#### 4. Nuevo Lead/Prospecto
**Trigger:** Formulario web o email a contacto
**Acciones:**
1. Extraer datos del lead
2. Guardar en Airtable/Notion (CRM)
3. Notificar a Luigi
4. Enviar auto-reply al prospecto

#### 5. Backup Automático de Skills y Memoria
**Trigger:** Sábados 2:00 AM
**Acciones:**
1. Ejecutar `sync-to-repo.sh`
2. Ejecutar `git push`
3. Si falla: reintentar o notificar a Tony

#### 6. Recolección de Tech News
**Trigger:** Diario 9:00 AM y 6:00 PM
**Acciones:**
1. Scrapear fuentes IA
2. Generar resumen con TTS
3. Enviar a Tony por WhatsApp
**Estado:** ✅ Ya implementado (cronjob `ai-news-aggregator`)

#### 7. Recordatorio de Pagos
**Trigger:** 5 días antes de vencimiento
**Acciones:**
1. Revisar Airtable/Notion de facturación
2. Enviar recordatorio al cliente
3. Si vence sin pago: escalar a Luigi y Pablo

### Roadmap de Implementación

| Fase | Workflows | Esfuerzo | Impacto |
|------|-----------|----------|---------|
| Fase 1 (esta semana) | Monitoreo + Reporte semanal | 2-3h | Alto |
| Fase 2 (próxima semana) | Onboarding + Backup auto | 3-4h | Alto |
| Fase 3 (próximo mes) | Leads + Facturación + Dashboard | 5-6h | Medio |

## Cuándo usar n8n vs cronjobs de Hermes

**Regla práctica:** Si el workflow conecta 3 o más sistemas distintos, usar n8n. Si es un script simple con un trigger de tiempo, usar cronjob de Hermes — es más directo y sin overhead.

| Tarea | Herramienta correcta | Motivo |
|-------|---------------------|--------|
| Backup semanal de skills a GitHub | Cronjob Hermes | Script simple, un solo sistema |
| Monitoreo de servicios + reinicio | Cronjob Hermes | Script bash, no requiere integraciones |
| Tech news diario | Cronjob Hermes | Ya implementado, funciona |
| Reporte semanal para Pablo | n8n | GitHub + WhatsApp + estado servicios = 3+ sistemas |
| Gestión de leads | n8n | Email + CRM + WhatsApp + cliente = 4+ sistemas |
| Onboarding de proyecto | n8n | GitHub + WhatsApp + filesystem + Gino = multi-sistema |

**Pitfall:** No usar n8n para tareas que un cronjob Hermes resuelve en 30 minutos. El overhead de configurar un workflow visual no se justifica para automatizaciones simples.

## Estado del servidor (2026-05-21)

- n8n v2.20.6 corriendo en Docker, puerto 5678, uptime estable
- Basic auth activa — sin API key no se puede consultar la API REST
- Para habilitar API key: Settings → API en la UI de n8n (http://localhost:5678)
- Sin API key, la API REST retorna: `{"message":"'X-N8N-API-KEY' header required"}`
- Vault Obsidian de Nelson: `~/brainstorming/` (tiene `.obsidian/`)
- n8n_data volume: `/var/lib/docker/volumes/n8n-docker_n8n_data/_data`

## Buenas practicas

- **Siempre** usar error handlers en cada workflow
- **Nunca** hardcodear credenciales, usar n8n credentials store
- **Backup** semanal de `n8n_data` volume
- **Versionar** workflows exportandolos a JSON y guardandolos en Git
- **Documentar** cada workflow con descripcion clara

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| n8n no arranca | `sudo docker logs n8n` |
| No llegan webhooks | Verificar firewall, puerto 5678 |
| No conecta a localhost | Usar `172.17.0.1` (ver nota abajo) |
| Workflow lento | Verificar recursion infinita |
| Sign in pide email/password (no basic auth) | Ver sección de autenticación abajo |

### Autenticación: email vs basic auth

Las versiones recientes de n8n usan **user management con email** por defecto — `N8N_BASIC_AUTH_USER/PASSWORD` del docker-compose YA NO funcionan como credenciales de login en la UI.

Para recuperar el email del owner registrado:

```bash
docker exec n8n printenv N8N_BASIC_AUTH_USER N8N_BASIC_AUTH_PASSWORD
# Solo muestra las vars del compose — no son las credenciales de la UI

# Para ver el email real del owner en la base SQLite:
docker exec n8n sqlite3 /home/node/.n8n/database.sqlite \
  "SELECT email, firstName, lastName FROM user LIMIT 5;" 2>/dev/null
# Si usa PostgreSQL externo, consultar la tabla user del postgres
```

Si se olvidó la contraseña, resetear vía variables de entorno al levantar el contenedor:
```yaml
environment:
  - N8N_USER_MANAGEMENT_DISABLED=true   # deshabilita auth temporalmente
```
O bien usar la API con la cookie de sesión activa si hay una sesión abierta.

## Credenciales n8n (instancia del equipo)

n8n está en modo **user management** con autenticación por email — NO basic auth aunque el docker-compose tenga variables `N8N_BASIC_AUTH_*`. Esas variables son ignoradas una vez que se completa el setup inicial.

- **Email:** aliagenttucuman@gmail.com (cuenta "Tony Stark")
- **Contraseña:** nelson2026
- **UI:** http://100.110.8.13:5678/

### Reset de contraseña (si se olvida)

n8n no tiene `sqlite3` adentro del contenedor. El flujo correcto:

```bash
# 1. Copiar la DB fuera del contenedor
docker cp n8n:/home/node/.n8n/database.sqlite /tmp/n8n.sqlite

# 2. Usar Python para actualizar el hash bcrypt
python3 -c "
import sqlite3, bcrypt
new_pass = 'nueva_password'
hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt(10)).decode()
conn = sqlite3.connect('/tmp/n8n.sqlite')
cur = conn.cursor()
cur.execute('UPDATE user SET password = ? WHERE email = ?', (hashed, 'aliagenttucuman@gmail.com'))
conn.commit()
print('Rows updated:', cur.rowcount)
conn.close()
"

# 3. Devolver la DB al contenedor y reiniciar
docker cp /tmp/n8n.sqlite n8n:/home/node/.n8n/database.sqlite && docker restart n8n

# 4. Verificar que levantó bien
sleep 5 && curl -s http://localhost:5678/healthz
```

### Ver email registrado (si se olvida el email también)

```bash
docker cp n8n:/home/node/.n8n/database.sqlite /tmp/n8n.sqlite
python3 -c "
import sqlite3
conn = sqlite3.connect('/tmp/n8n.sqlite')
cur = conn.cursor()
cur.execute('SELECT email, firstName, lastName FROM user')
for row in cur.fetchall(): print(row)
conn.close()
"
```

## Pitfalls de red: host.docker.internal NO funciona en este setup

**`host.docker.internal` NO está configurado en el Docker de este servidor.** Usar siempre la IP del gateway de Docker:

```
172.17.0.1
```

Verificar desde dentro del contenedor:
```bash
docker exec n8n wget -qO- http://172.17.0.1:3001/health
# debe responder {"status":"connected"}
```

Esto afecta a TODOS los nodos HTTP Request que apunten a servicios del host:
- WhatsApp Gateway: `http://172.17.0.1:3001`
- ForestAI Backend: `http://172.17.0.1:8010`
- FastAPI genérico: `http://172.17.0.1:8000`

## Pitfalls del nodo Merge en n8n 2.20

El nodo `n8n-nodes-base.merge` con `typeVersion: 3` falla con:
```
Cannot read properties of undefined (reading 'execute')
```

**Workaround:** En lugar de correr checks en paralelo + merge, **encadenar los checks en secuencia**. El nodo Code al final puede leer cada nodo previo por nombre con `$('Nombre Nodo').first().json`. Ejemplo:

```
Trigger → Check A → Check B → Check C → Code (lee los 3) → Acción
```

En el nodo Code:
```js
const a = $('Check A').first().json;
const b = $('Check B').first().json;
const c = $('Check C').first().json;
```

## Resetear contraseña de n8n (cuando el usuario no la recuerda)

n8n usa `user management` con email/password (no basic auth). La contraseña está hasheada en SQLite con bcrypt. Para resetear:

```python
import sqlite3, bcrypt, subprocess

# Copiar DB del contenedor
subprocess.run(["docker", "cp", "n8n:/home/node/.n8n/database.sqlite", "/tmp/n8n.sqlite"])

# Actualizar password
new_pass = "nelson2026"
hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt(10)).decode()
conn = sqlite3.connect('/tmp/n8n.sqlite')
cur = conn.cursor()
cur.execute('UPDATE user SET password = ? WHERE email = ?', (hashed, 'aliagenttucuman@gmail.com'))
conn.commit()
conn.close()

# Devolver DB al contenedor y reiniciar
subprocess.run(["docker", "cp", "/tmp/n8n.sqlite", "n8n:/home/node/.n8n/database.sqlite"])
subprocess.run(["docker", "restart", "n8n"])
```

Email de la cuenta: `aliagenttucuman@gmail.com` (cuenta Tony Stark).

## Pitfalls

1. **Docker requiere sudo.** Si el usuario no esta en el grupo `docker`, todos los comandos necesitan `sudo`. Usar: `echo 'PASSWORD' | sudo -S docker compose up -d` para evitar prompts interactivos.

2. **`docker compose up -d` es un proceso largo.** Algunas herramientas de terminal lo detectan como foreground process. Si falla, usar `background=true` o separar en: `docker compose pull` (foreground) y luego `docker compose up -d` (background).

3. **Primera vez tarda.** La primera ejecucion descarga la imagen (~400MB). No interrumpir. Verificar progreso con `sudo docker logs -f n8n`.

4. **Verificacion post-instalacion.** Siempre correr el script de verificacion despues de levantar: [`scripts/verify-n8n.sh`](scripts/verify-n8n.sh). Comprueba que el container esta Up, el health endpoint responde `{"status":"ok"}`, y la home page devuelve HTTP 200.

5. **NO instalar nodos custom dentro del contenedor Docker.** Instalar paquetes como `n8n-nodes-opencode` via `npm install` dentro del container genera problemas de permisos (root vs node). El contenedor corre como usuario `node` pero `npm install` como `root` deja archivos inaccesibles. Solucion: **usar el nodo HTTP Request nativo de n8n** en lugar de nodos custom. Es mas simple y no requiere instalacion.

6. **Simplificar cuando el usuario lo pida.** Si el usuario dice "simplifica" o muestra frustracion con pasos complejos, reducir a la solucion minima viable. No explicar teorias extensas ni dar multiples opciones. Ir directo a lo que funciona.

## Template: Reporte Semanal con Health Checks

Workflow listo para importar: [`templates/reporte-semanal-workflow.json`](templates/reporte-semanal-workflow.json).

Patrón: `Schedule (lunes 9AM) → 3x HTTP health checks en paralelo → Code (generar resumen) → HTTP Request (WA gateway /send)`.

- Todos los health checks usan `continueOnFail: true` para que el resumen se genere aunque algún servicio esté caído
- El nodo Code arma el mensaje con emojis ✅/❌ por servicio
- Envía al número de Nelson via gateway Baileys en `host.docker.internal:3001`
- Archivo también en `/home/server/n8n-docker/reporte-semanal.json`

Para adaptar: cambiar URLs de health checks, número de destino, y lista de proyectos activos en el nodo Code.

## Integracion con OpenCode (via HTTP Request)

Ver workflow listo para importar: [`templates/opencode-workflow.json`](templates/opencode-workflow.json).

En lugar del nodo custom problematico, usar el nodo **HTTP Request** nativo:

1. OpenCode server debe estar corriendo en el host: `opencode serve --port 4096`
2. Desde n8n, crear nodo HTTP Request:
   - Method: `POST`
   - URL: `http://host.docker.internal:4096/api/v1/chat`
   - Body (JSON):
```json
{
  "prompt": "={{ $json.body.prompt }}"
}
```
3. Procesar la respuesta con un nodo Code o Set.

Ejemplo de workflow:
```
Webhook (prompt) -> HTTP Request (OpenCode) -> Code (parsear respuesta) -> Response
```

## Benchmarks de LLMs locales (equipo Nelson)

Hardware de referencia: NVIDIA GTX 1650 Mobile 4GB VRAM, 13GB RAM.

| Modelo | Parametros | Tamanio GGUF | VRAM usada | Tiempo respuesta* | Recomendacion |
|--------|-----------|-------------|------------|-------------------|---------------|
| llama3.2:3b | 3B | ~2.0 GB | ~2.0 GB | ~4.3s | ✅ Uso diario |
| qwen2.5:3b | 3B | ~1.9 GB | ~1.9 GB | ~6.3s | ✅ Uso diario |
| gemma3:1b | 1B | ~800 MB | ~800 MB | ~2.7s | ✅ Rapido, basico |
| gemma3:4b | 4B | ~3.3 GB | ~2.4 GB | ~6.3s | ✅ Mas capacidad |
| gemma4-e2b IQ2_M | 2.3B efectivos | 2.62 GB | ~2.9 GB | ~55s | ⚠️ Thinking mode, lento |
| gemma4-e4b Q2_K | 4B efectivos | 4.46 GB | >4 GB | N/A | ❌ No entra en 4GB VRAM |

*Tiempo medido con la misma pregunta: "Ventajas de Docker en 2 oraciones". Cuantizacion mas agresiva = mas lento.

**Conclusion para el equipo:** Usar llama3.2:3b o qwen2.5:3b para automatizaciones rapidas en n8n. Gemma 4 E2B solo si se necesita explicitamente el thinking mode y se tolera la latencia.

**Para importar modelos custom a Ollama (ej: Gemma 4 desde Hugging Face):** ver [`references/ollama-custom-gguf-import.md`](references/ollama-custom-gguf-import.md).

## Templates

- `templates/reporte-semanal-servicios.json` — Workflow n8n listo para importar: trigger lunes 9AM → health checks en paralelo (ForestAI, n8n, WA Gateway) → resumen en JS → envío WhatsApp a Nelson. Usar como base para otros reportes periódicos.

## Recursos

- URL local: http://localhost:5678
- Documentacion: https://docs.n8n.io/
- Workflow templates: https://n8n.io/workflows/
