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

## Importar workflows programáticamente (sin UI)

Cuando el browser no está disponible (servidor headless), importar y activar workflows via CLI:

### Paso 1 — Importar via n8n CLI
```bash
# Copiar el JSON al container y importar
docker cp /tmp/mi_workflow.json n8n:/tmp/mi_workflow.json
docker exec n8n n8n import:workflow --input=/tmp/mi_workflow.json
```

El JSON debe tener un campo `"id"` (string alfanumérica) o falla con:
```
SQLITE_CONSTRAINT: NOT NULL constraint failed: workflow_entity.id
```
Fix: agregar `"id": "abcdef1234567890"` (16 chars hex) al JSON antes de importar.

Si el JSON tiene `"active": true`, n8n lo ignora al importar y lo deja inactivo de todas formas.

### Paso 2 — Activar via sqlite3 (node.js)
n8n no tiene `sqlite3` ni `python3` en el container, pero sí tiene `node` con el módulo `sqlite3` de n8n disponible:

```javascript
// /tmp/activate.js
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.run("UPDATE workflow_entity SET active=1 WHERE id=?", ['MI_WORKFLOW_ID'], function(err) {
  if(err) console.error(err);
  else console.log('Activado, rows:', this.changes);
  db.close();
});
```

```bash
docker cp /tmp/activate.js n8n:/tmp/activate.js
docker exec n8n node /tmp/activate.js
# Reiniciar para que n8n registre el scheduler del workflow activo
cd ~/n8n-docker && docker compose restart n8n
```

### Verificar workflows importados
```bash
docker exec n8n n8n export:workflow --all --output=/tmp/exported.json 2>&1
docker exec n8n node -e "
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.all('SELECT id, name, active FROM workflow_entity', (err,rows) => {
  rows.forEach(r => console.log(r.id, r.active ? '✅' : '❌', r.name));
  db.close();
});
"
```

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

## Credenciales actualizadas (sesión 2026-06-09)

- **Email:** nelsongacosta@gmail.com
- **Password:** BuenosAires435!
- **UI:** http://100.110.8.13:5678/

(Nota: el docker-compose tiene N8N_BASIC_AUTH_* pero esas variables son ignoradas en modo user-management. Usar el email/password registrado al hacer setup inicial.)

## Patrón: Health Server Python como proxy para n8n

El nodo `n8n-nodes-base.executeCommand` **NO existe en n8n v2.20.6**. Intentar importar un workflow con ese nodo da:
```
Unrecognized node type: n8n-nodes-base.executeCommand
```

**Solución validada**: levantar un mini servidor HTTP Python en el host que ejecuta los comandos de sistema y devuelve JSON. n8n lo consulta via HTTP Request nativo.

```python
# /home/server/n8n-docker/health_server.py — puerto 9099
import subprocess, json, psutil
from http.server import HTTPServer, BaseHTTPRequestHandler

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
    except:
        return "0"

def safe_int(val):
    try:
        return int(val.split()[0])
    except:
        return 0

def get_metrics():
    cpu  = str(round(psutil.cpu_percent(interval=None), 1))  # interval=None evita bloqueo
    ram  = str(round(psutil.virtual_memory().percent, 1))
    disk = str(round(psutil.disk_usage("/").percent, 1))
    forestai = run("docker ps --filter name=forestai-poc --filter status=running --format '{{.Names}}' | wc -l")
    bisonte  = run("ss -tlnp 2>/dev/null | grep ':9000' | wc -l")
    whatsapp = run("ss -tlnp 2>/dev/null | grep ':3001' | wc -l")
    alerts = []
    if float(cpu) > 80: alerts.append(f"CPU: {cpu}% > 80%")
    if float(ram) > 85: alerts.append(f"RAM: {ram}% > 85%")
    if float(disk) > 80: alerts.append(f"Disco: {disk}% > 80%")
    if safe_int(forestai) == 0: alerts.append("ForestAI Docker CAIDO")
    if safe_int(bisonte) == 0:  alerts.append("Expreso Bisonte :9000 CAIDO")
    if safe_int(whatsapp) == 0: alerts.append("WhatsApp Gateway :3001 CAIDO")
    return {"status": "alert" if alerts else "ok", "alerts": alerts,
            "metrics": {"cpu": cpu, "ram": ram, "disk": disk},
            "services": {"forestai_docker": safe_int(forestai),
                         "bisonte_9000": safe_int(bisonte), "whatsapp_3001": safe_int(whatsapp)}}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        data = json.dumps(get_metrics()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

HTTPServer(("0.0.0.0", 9099), Handler).serve_forever()
```

**Pitfall crítico — `psutil.cpu_percent(interval=1)` bloquea el HTTP thread**: usar siempre `interval=None` para no bloquear. Con interval=1, el servidor acepta la conexión pero nunca responde (curl da exit 52 / empty reply).

**Pitfall — awk con escapes en raw strings Python**: los comandos awk con `printf "%.0f"` generan `backslash not last character` cuando se definen con `r"""..."""`. Usar `psutil` directamente para CPU/RAM/disco — es más limpio y no tiene problemas de escaping.

Desde n8n, el nodo HTTP Request apunta a `http://172.17.0.1:9099/` (IP del host desde Docker).

## Activar workflows en n8n programáticamente

### El problema con `n8n import:workflow`
Importar via CLI marca el workflow como "draft" aunque tenga `active: true` en el JSON. n8n **no lo activa al reiniciar** — solo activa los que pasaron por la UI o la REST API.

### Flujo correcto para activar via REST (sin UI)

```bash
# 1. Login con cookie
curl -s -c /tmp/n8n_cookies.txt -X POST http://localhost:5678/rest/login \
  -H 'Content-Type: application/json' \
  -d '{"emailOrLdapLoginId":"nelsongacosta@gmail.com","password":"BuenosAires435!"}'

# 2. Obtener versionId del workflow
VID=$(curl -s -b /tmp/n8n_cookies.txt http://localhost:5678/rest/workflows/WORKFLOW_ID \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['versionId'])")

# 3. Activar con versionId
curl -s -b /tmp/n8n_cookies.txt \
  -X POST "http://localhost:5678/rest/workflows/WORKFLOW_ID/activate" \
  -H 'Content-Type: application/json' \
  -d "{\"versionId\":\"$VID\"}"
```

**Pitfall**: el endpoint `/activate` requiere el `versionId` — sin él devuelve `{"code":"invalid_type",...,"path":["versionId"]}`. Y el versionId solo aparece en `data.versionId` dentro de la respuesta de GET del workflow individual.

### Activar via SQLite (alternativa sin REST)
```javascript
// docker cp script.js n8n:/tmp/ && docker exec n8n node /tmp/script.js
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.run("UPDATE workflow_entity SET active=1 WHERE id=?", ['WORKFLOW_ID'], function(err) {
  console.log('activado, rows:', this.changes);
  db.close();
});
```
Después de editar la DB directamente, reiniciar n8n: `cd ~/n8n-docker && docker compose restart n8n`.
**Nota**: n8n puede ignorar el flag de la DB al cargar si el workflow tiene issues de validación internos. La REST API es más confiable.

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

## Pipeline LinkedIn con n8n

n8n tiene nodo nativo de LinkedIn. Permite publicar posts en cuentas personales y company pages usando OAuth2 oficial.

### Prerequisito crítico: LinkedIn Developer App

1. Crear app en https://developer.linkedin.com
2. Agregar producto **"Share on LinkedIn"** (solicitar en pestaña Products)
3. Esperar aprobación del scope `w_member_social` — puede tardar días
4. Con aprobación: los endpoints `/rest/posts` y `/rest/documents` quedan habilitados

### Credenciales necesarias

- **Client ID**: visible en la pantalla principal de la app (ej: `77djcvwzhlbcak`)
- **Client Secret**: pestaña Auth → Primary Client Secret → icono ojo para mostrarlo. Formato: cadena alfanumérica larga sin guiones

**PITFALL CRÍTICO**: El token con formato `WPL_AP1.XXXX.YYYY==` NO es el Client Secret. Es un access token de sesión. El Client Secret está en Auth → Primary Client Secret y tiene formato distinto (sin `WPL_AP1`).

### Flujo OAuth2 para n8n

1. En n8n: Credentials → New → LinkedIn OAuth2 API
2. Pegar Client ID y Client Secret
3. Redirect URI debe ser: `https://oauth.n8n.io/oauth2/callback` (o la URL de tu instancia)
4. Agregar esa Redirect URI en la app de LinkedIn Developer (Auth → OAuth 2.0 settings)
5. Autorizar la conexión — LinkedIn pedirá login y permisos

### Workflow típico: Fuente → IA → LinkedIn

```
Cron / Webhook → HTTP Request (fuente de contenido RSS/API) 
→ Code Node (formatear/procesar con IA vía Ollama) 
→ LinkedIn (Create Post)
```

### Operaciones del nodo LinkedIn en n8n

- `Create Post` — texto simple o con imagen
- `Create Post with Image` — subir imagen + texto
- `Get Person` — perfil del usuario autenticado
- Versión de API: `202401`

### Alternativa sin n8n: Python directo

```python
import requests

def post_to_linkedin(access_token: str, person_urn: str, text: str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "author": f"urn:li:person:{person_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    )
    return r.json()
```

### Rate limits LinkedIn API

- 100 requests/día en plan básico
- 500 requests/día con verificación adicional
- 1 post cada 10 segundos por miembro
- Access token: válido 60 días, necesita refresh manual

### Lo que hay que EVITAR

- `linkedin-api` (pip) — usa cookies de sesión, riesgo alto de ban
- Selenium/Playwright — LinkedIn detecta bots activamente
- Usar email/password directamente — violación de ToS

## Pitfalls

1. **Docker requiere sudo.** Si el usuario no esta en el grupo `docker`, todos los comandos necesitan `sudo`. Usar: `echo 'PASSWORD' | sudo -S docker compose up -d` para evitar prompts interactivos.

2. **`docker compose up -d` es un proceso largo.** Algunas herramientas de terminal lo detectan como foreground process. Si falla, usar `background=true` o separar en: `docker compose pull` (foreground) y luego `docker compose up -d` (background).

3. **Primera vez tarda.** La primera ejecucion descarga la imagen (~400MB). No interrumpir. Verificar progreso con `sudo docker logs -f n8n`.

4. **Verificacion post-instalacion.** Siempre correr el script de verificacion despues de levantar: [`scripts/verify-n8n.sh`](scripts/verify-n8n.sh). Comprueba que el container esta Up, el health endpoint responde `{"status":"ok"}`, y la home page devuelve HTTP 200.

5. **NO instalar nodos custom dentro del contenedor Docker.** Instalar paquetes como `n8n-nodes-opencode` via `npm install` dentro del container genera problemas de permisos (root vs node). El contenedor corre como usuario `node` pero `npm install` como `root` deja archivos inaccesibles. Solucion: **usar el nodo HTTP Request nativo de n8n** en lugar de nodos custom. Es mas simple y no requiere instalacion.

6. **Simplificar cuando el usuario lo pida.**

7. **Importar workflow via API requiere API key, no basic auth.** La API REST de n8n en `/api/v1/workflows` requiere header `X-N8N-API-KEY`. Las variables `N8N_BASIC_AUTH_*` del docker-compose NO sirven para autenticar la API. Para obtener una API key: Settings → API → Create API Key en la UI de n8n.

8. **`docker inspect` redacta las variables de entorno.** `docker inspect n8n` y `docker exec n8n env` muestran `***` para variables sensibles. No se pueden recuperar programáticamente — pedirlas al usuario directamente.

9. **Desde n8n, localhost NO apunta al host.** Usar `172.17.0.1` para llegar a servicios del host desde dentro del container. Verificar: `docker exec n8n wget -qO- http://172.17.0.1:3001/health`.

 Si el usuario dice "simplifica" o muestra frustracion con pasos complejos, reducir a la solucion minima viable. No explicar teorias extensas ni dar multiples opciones. Ir directo a lo que funciona.

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
- `templates/health_server.py` — Mini servidor HTTP Python (puerto 9099) que expone métricas del sistema como JSON. Workaround validado para reemplazar el nodo `executeCommand` que no existe en n8n v2.20.6.
- `templates/monitor-servidor-workflow.json` — Workflow de monitoreo de servidor listo para importar. Consulta el health_server cada 5 minutos, filtra alertas y manda WhatsApp via gateway Baileys.
- `templates/monitor-servidor-whatsapp.json` — Workflow de monitoreo cada 5 min: chequea CPU (>80%), RAM (>85%), Disco (>80%), ForestAI Docker, Bisonte :9000, WhatsApp GW :3001. Solo alerta cuando hay problema. WA via `172.17.0.1:3001/send`. ID activo en prod: `8316487bc6e44b9c`.
- `templates/reporte-semanal-servicios.json` — Workflow n8n listo para importar: trigger lunes 9AM → health checks en paralelo (ForestAI, n8n, WA Gateway) → resumen en JS → envío WhatsApp a Nelson. Usar como base para otros reportes periódicos.

## Referencias de soporte

- `references/linkedin-api-pipeline.md` — App LinkedIn creada (Alegent AI investigations), flujo OAuth2 completo, endpoints, pitfalls, estado del pipeline al 2026-05-31.

## LinkedIn Feed Pipeline

Pipeline para publicar contenido en LinkedIn desde cuenta personal vía API oficial.
Archivos en `~/brainstorming/2026-05-31-linkedin-feed-pipeline/`.

Documentación completa, quirks del Client Secret (formato WPL_AP1) y flujo OAuth2:
→ `references/linkedin-api-oauth2.md`

**App registrada:** Alegent AI investigations (Client ID: 77djcvwzhlbcak)
**Producto aprobado:** Share on LinkedIn (w_member_social) ✅

## LinkedIn Feed Pipeline

Pipeline para publicar posts en LinkedIn desde cuenta personal via API oficial.
Ver detalles completos en [`references/linkedin-oauth2-pipeline.md`](references/linkedin-oauth2-pipeline.md).

Resumen del flujo:
1. Crear app en LinkedIn Developer con producto "Share on LinkedIn" (w_member_social)
2. Levantar servidor OAuth2 FastAPI en :8090
3. Exponer con túnel Cloudflare — registrar ESA URL como redirect_uri en LinkedIn Developer
4. Autenticar una vez → tokens guardados en `auth/tokens.json`
5. Publicar con `publisher.py` o via n8n nodo LinkedIn

**Pitfall clave:** redirect_uri del .env DEBE coincidir exactamente con la registrada en LinkedIn Developer. Si el túnel se reinicia (nueva URL), actualizar ambos lugares.

## Recursos

- URL local: http://localhost:5678
- Documentacion: https://docs.n8n.io/
- Workflow templates: https://n8n.io/workflows/
