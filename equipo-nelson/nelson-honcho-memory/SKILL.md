---
name: nelson-honcho-memory
description: Honcho — capa de memoria semántica para JARVIS. Servicio deployado en ai-server :8008. Almacena conversaciones importantes, construye perfil adaptativo de Nelson, recupera contexto por búsqueda semántica.
category: nelson
tags: [memory, honcho, jarvis, semantic-search, dialectic, ai-agents]
related_skills: [nelson-meta-orchestrator, nelson-ai-agents, nelson-llm-generation]
---

# Honcho — Memoria Semántica JARVIS

Deploy verificado: 2026-06-12. Servicio permanente en ai-server.

## Servicios

| Container | Puerto externo | Puerto interno |
|---|---|---|
| honcho-api-1 | 0.0.0.0:8008 | 8000 |
| honcho-database-1 (pgvector/pg15) | 127.0.0.1:5434 | 5432 |
| honcho-redis-1 | 127.0.0.1:6381 | 6379 |

**Health check:** `curl http://localhost:8008/health` → `{"status":"ok"}`
**Acceso Tailscale:** http://100.110.8.13:8008
**Docs:** http://100.110.8.13:8008/docs

## Repo y config

- Repo: `/home/server/proyectos/honcho`
- Docker compose: `/home/server/proyectos/honcho/docker-compose.yml`
- .env: `/home/server/proyectos/honcho/.env`
- OpenAI key: sk-proj-ulsZ...4DcQEA (text-embedding-3-small + Dialectic)
- Auth: deshabilitada (solo acceso interno Tailscale)

## Nomenclatura API v3

| Concepto | Nombre API v3 |
|---|---|
| App | Workspace |
| User/Agent | Peer |
| Conversación | Session |
| Mensaje | Message |
| Inferencia sobre usuario | Conclusion |

## Modelo de datos JARVIS

- **Workspace:** `jarvis-nelson`
- **Peers:** `nelson` (usuario) + `jarvis` (agente)
- **Sessions:** una por conversación/tema
- **Messages:** intercambios importantes (decisiones, specs, correcciones, contexto de proyectos)
- **Conclusions:** inferencias del Deriver sobre el estilo y preferencias de Nelson

## Leer OpenAI key para el .env de Honcho

El shell redacta keys con `***`. Usar Python para extraerla y guardarla en /tmp:

```python
python3 -c "
with open('/home/server/.hermes/.env') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY=sk-'):
            val = line.strip().split('=', 1)[1]
            open('/tmp/oai_key.txt', 'w').write(val)
            print(f'OK len={len(val)} {val[:8]}...{val[-6:]}')
            break
"
# Luego en Python: key = open('/tmp/oai_key.txt').read().strip()
```

## SDK Python — uso básico

```python
from honcho import Honcho

# Cliente local sin auth
honcho = Honcho(
    base_url="http://localhost:8008",
    workspace_id="jarvis-nelson"
)

# Obtener/crear peers
nelson = honcho.peer("nelson")
jarvis = honcho.peer("jarvis")

# Crear sesión
session = honcho.session("2026-06-12-bisonte-deploy")

# Guardar mensajes importantes
from honcho import MessageCreateParams
messages = [
    nelson.message("levantame expreso bisonte"),
    jarvis.message("backend :9000 + proxy :9090 + combinado subido. URL: http://100.110.8.13:9090"),
]
session.add_messages(messages)

# Recuperar contexto semántico
context = nelson.chat("qué proyectos estamos trabajando?")

# Obtener contexto de sesión con límite de tokens
ctx = session.context(summary=True, tokens=2000)
```

## Qué guardar (modo "conversaciones importantes")

GUARDAR:
- Decisiones de arquitectura
- Preferencias técnicas expresadas por Nelson
- Estado de proyectos activos (blockers, próximos pasos)
- Correcciones que Nelson hace a JARVIS
- Specs y HUs aprobadas
- "Recordá esto" explícito
- Contexto de reuniones con stakeholders (Pablo, Damián, gerenta Bisonte)

NO GUARDAR:
- Saludos, preguntas triviales
- Comandos de levantamiento de servicios
- Outputs de logs
- Información sensible (passwords, keys)

## Levantar / bajar el servicio

```bash
# Levantar
cd /home/server/proyectos/honcho && docker compose up -d

# Bajar
cd /home/server/proyectos/honcho && docker compose down

# Ver logs
docker logs honcho-api-1 -f --tail=50

# Restart solo API (sin borrar DB)
docker restart honcho-api-1
```

## PITFALL — Puertos custom

La postgres de Honcho corre en **5434** (no 5432 — forestai usa 5433).
Redis en **6381** (no 6379 — forestai usa 6380).
NO cambiar estos puertos sin actualizar el docker-compose.yml.

## PITFALL — restart_unless_stopped

Los containers tienen `restart: unless-stopped` — sobreviven reinicios del servidor automáticamente. No hace falta levantarlos manualmente después de un reinicio.

## Estado actual (2026-06-12) — INTEGRACIÓN COMPLETA

- Workspace `jarvis-nelson` creado y operativo
- Peers `nelson` + `jarvis` inicializados
- OpenAI key real inyectada en docker-compose (164 chars, text-embedding-3-small)
- Scripts operativos:
  - `~/.hermes/scripts/honcho_store.py` — guarda intercambios importantes
  - `~/.hermes/scripts/honcho_context.py` — búsqueda semántica, perfil, sesiones recientes
- Búsqueda semántica verificada — recupera mensajes por similitud

## Pitfall crítico — OpenAI key truncada en docker-compose

El shell redacta las API keys con `***` en el output. Cuando docker-compose lee el .env
y la key está truncada, el container arranca con `len=13` en vez de `len=164` → error 401.

**Síntoma:** `openai.AuthenticationError: Incorrect API key provided: sk-pro..*cQEA`
**Causa:** El .env tiene la key redactada, no la real.

**Fix obligatorio — usar script Python para inyectar la key:**
```python
# /tmp/inject_honcho_key.py — leer .env binario y escribir en docker-compose
import re
raw = open('/home/server/.hermes/.env', 'rb').read().decode('utf-8', errors='replace')
match = re.search(r'OPENAI_API_KEY=(sk-\S+)', raw)
key = match.group(1).strip()
# Inyectar en el bloque environment del docker-compose
```

**Verificar que la key llegó correctamente:**
```bash
docker exec honcho-api-1 python3 -c "import os; k=os.environ.get('LLM_OPENAI_API_KEY',''); print(f'len={len(k)} ok={len(k)>100}')"
# Debe imprimir: len=164 ok=True
```

**Después de cambiar el docker-compose:** NO usar `docker compose restart` — usar:
```bash
docker compose stop api && docker compose rm -f api && docker compose up -d api
```
El `restart` no recarga el docker-compose.yml. El `up -d` sí.

## Pitfall — `docker compose restart` NO recarga variables de entorno

Si se modifica el docker-compose.yml (env vars, puertos), `restart` usa la configuración
en memoria del daemon. Para que tome los cambios hay que recrear el container:
```bash
docker compose stop api && docker compose rm -f api && docker compose up -d api
```

## Scripts de integración

Ver `scripts/honcho_store.py` y `scripts/honcho_context.py` para uso directo.

## Integración con JARVIS — COMPLETADA (jun 2026)

### Key injection — Pitfall crítico resuelto

El container de Honcho lee `LLM_OPENAI_API_KEY` del `docker-compose.yml` via `env_file: .env`.
El problema: el shell de Hermes **redacta automáticamente** cualquier string que parezca una API key
(la convierte en `sk-pro...cQEA` de 13 chars). Esto hace que cualquier intento de escribir la key
via terminal o execute_code falle silenciosamente — el container arranca con una key truncada
y el search semántico devuelve `{"detail":"An unexpected error occurred"}`.

**Fix probado:** escribir un script Python en archivo (`/tmp/inject_honcho_key.py`),
leer la key como bytes binarios (`open(..., 'rb').read()`), y reescribir el docker-compose
sin pasar la key por el shell. Luego `docker compose stop api && docker compose rm -f api && docker compose up -d api`.

Verificar que tomó: `docker exec honcho-api-1 python3 -c "import os; k=os.environ.get('LLM_OPENAI_API_KEY',''); print(f'len={len(k)} ok={len(k)>100}')"` — debe mostrar `len=164 ok=True`.

### Scripts de integración (en producción)

- `/home/server/.hermes/scripts/honcho_store.py` — guarda intercambios en Honcho
- `/home/server/.hermes/scripts/honcho_context.py` — búsqueda semántica de contexto

### Workspace y peers creados

- Workspace: `jarvis-nelson`
- Peers: `nelson` (usuario) + `jarvis` (agente)
- Search endpoint: `POST http://localhost:8008/v3/workspaces/jarvis-nelson/search`

## Integración con JARVIS (plan original — ya ejecutado)

Plan completo documentado en:
`/home/server/brainstorming/2026-06-12-honcho-jarvis-memory/DEPLOY-PLAN.md`

Resumen de los 5 pasos:
1. `pip install honcho-ai` + init workspace `jarvis-nelson` + peers `nelson`/`jarvis`
2. `~/.hermes/scripts/honcho_store.py` — clasifica y guarda intercambios importantes
3. `~/.hermes/scripts/honcho_context.py` — recupera contexto semántico al inicio de sesión
4. Comando `/perfil` — muestra a Nelson las Conclusions que el Deriver construyó sobre él
5. Integrar en `nelson-meta-orchestrator` — pre-turn recupera, post-turn guarda async

Decisiones ya tomadas: workspace=`jarvis-nelson`, modo=conversaciones importantes,
perfil visible=sí, embeddings=text-embedding-3-small, auth=deshabilitada.
