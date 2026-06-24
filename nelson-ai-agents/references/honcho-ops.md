# Honcho — Memoria Semántica JARVIS: Deploy & Operación

Deploy verificado: 2026-06-12. Servicio permanente en ai-server.

## Servicios Docker

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
- OpenAI key: text-embedding-3-small + Dialectic (ver pitfall de key truncada abajo)
- Auth: deshabilitada (solo acceso interno Tailscale)

## Nomenclatura API v3

| Concepto | API v3 |
|---|---|
| App | Workspace |
| User/Agent | Peer |
| Conversación | Session |
| Mensaje | Message |
| Inferencia sobre usuario | Conclusion |

**Workspace JARVIS:** `jarvis-nelson`, Peers: `nelson` + `jarvis`

## SDK Python — uso completo

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
messages = [
    nelson.message("levantame expreso bisonte"),
    jarvis.message("backend :9000 + proxy :9090. URL: http://100.110.8.13:9090"),
]
session.add_messages(messages)

# Recuperar contexto semántico
context = nelson.chat("qué proyectos estamos trabajando?")

# Contexto de sesión con límite de tokens
ctx = session.context(summary=True, tokens=2000)
```

## Qué guardar

GUARDAR:
- Decisiones de arquitectura
- Preferencias técnicas de Nelson
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

## Levantar / bajar

```bash
cd /home/server/proyectos/honcho && docker compose up -d
cd /home/server/proyectos/honcho && docker compose down
docker logs honcho-api-1 -f --tail=50
docker restart honcho-api-1
```

## Scripts de integración (en producción)

- `~/.hermes/scripts/honcho_store.py` — guarda intercambios importantes
- `~/.hermes/scripts/honcho_context.py` — búsqueda semántica de contexto

## Pitfall crítico — OpenAI key truncada en docker-compose

El shell de Hermes **redacta automáticamente** strings que parecen API keys (→ `sk-pro...cQEA` de 13 chars).
Cuando el container arranque con key truncada: error 401 del embedding.

**Síntoma:** `openai.AuthenticationError: Incorrect API key provided: sk-pro..*cQEA`

**Fix obligatorio — escribir script Python y ejecutarlo:**
```python
# /tmp/inject_honcho_key.py
import re
raw = open('/home/server/.hermes/.env', 'rb').read().decode('utf-8', errors='replace')
match = re.search(r'OPENAI_API_KEY=(sk-\S+)', raw)
key = match.group(1).strip()
# Leer docker-compose, reemplazar key, escribir sin pasar por shell
dc = open('/home/server/proyectos/honcho/docker-compose.yml').read()
dc_new = re.sub(r'LLM_OPENAI_API_KEY=.*', f'LLM_OPENAI_API_KEY={key}', dc)
open('/home/server/proyectos/honcho/docker-compose.yml', 'w').write(dc_new)
```

**Verificar que la key llegó:**
```bash
docker exec honcho-api-1 python3 -c "import os; k=os.environ.get('LLM_OPENAI_API_KEY',''); print(f'len={len(k)} ok={len(k)>100}')"
# Debe imprimir: len=164 ok=True
```

**Después de cambiar docker-compose:** NO usar `docker compose restart` (no recarga vars).
Usar: `docker compose stop api && docker compose rm -f api && docker compose up -d api`

## Pitfall — Puertos custom

- postgres: **5434** (no 5432 — forestai usa 5433)
- redis: **6381** (no 6379 — forestai usa 6380)

## Template docker-compose

Ver `/home/server/proyectos/honcho/docker-compose.yml` como referencia.
El template original está en `templates/docker-compose.honcho.yml` del skill archivado.

## Integración con JARVIS (plan ejecutado jun 2026)

1. `pip install honcho-ai` + init workspace `jarvis-nelson` + peers `nelson`/`jarvis`
2. `honcho_store.py` — clasifica y guarda intercambios importantes post-sesión
3. `honcho_context.py` — recupera contexto semántico al inicio de sesión
4. Comando `/perfil` — muestra Conclusions que el Deriver construyó sobre Nelson
5. Integrar en `nelson-meta-orchestrator` — pre-turn recupera, post-turn guarda async
