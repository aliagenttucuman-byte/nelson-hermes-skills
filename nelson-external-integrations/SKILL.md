---
name: nelson-external-integrations
description: "Patrones para integrar APIs y servicios externos en el equipo Nelson. Fallback strategy, rate limits, red Docker vs host, y spike obligatorio antes de integrar."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [integrations, external-apis, fallback, docker, networking, nelson]
    related_skills: [nelson-project-constitution, spike, nelson-observability, nelson-senior-practices]
---

# Nelson External Integrations

Patrones para cuando el equipo integra servicios externos: buscadores, APIs de terceros, scraping, LLMs cloud, etc.

**Regla de oro:** Antes de integrar, hacer un spike de 15 minutos en el entorno real.

---

## 1. Spike obligatorio antes de integrar

Antes de que cualquier agente incorpore una librería externa al código base:

```
1. Identificar el entorno donde corre (host o Docker)
2. Instalar la lib en ese entorno
3. Hacer UNA llamada real con datos reales
4. Verificar que devuelve datos útiles (no solo "no crashea")
5. Si pasa → integrar. Si falla → reportar a Tony antes de continuar.
```

**Tiempo máximo del spike:** 15 minutos. Si tarda más, algo está mal.

---

## 2. Docker vs Host para llamadas externas

| Situación | Solución |
|-----------|----------|
| Backend llama a APIs externas (buscadores, scraping, etc.) | Correr en **host** con venv propio |
| Backend solo habla con DB/Redis/otros containers | Docker normal |
| Necesita ambos | `network_mode: host` en docker-compose |

**Por qué:** Las IPs de rangos Docker están bloqueadas por rate limits de muchos servicios (DuckDuckGo, Google Search, etc.). Desde el host con IP real no hay problema.

```yaml
# docker-compose.yml - Si el servicio hace llamadas externas
backend:
  network_mode: host  # ← Usar IP real del host
```

O mejor aún, correr el backend como proceso directo del host:

```bash
# Crear venv del host (fuera de Docker)
python3 -m venv ~/venvs/proyecto-backend
source ~/venvs/proyecto-backend/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --port 8004
```

---

## 3. Patrón de fallback para servicios de búsqueda

Cuando el proyecto necesita búsquedas web, definir proveedores en orden de prioridad:

```python
# app/services/search.py
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class SearchResult:
    title: str
    url: str
    snippet: str

async def search_web(query: str, max_results: int = 5) -> List[SearchResult]:
    """Búsqueda con fallback automático entre proveedores.
    
    Orden: DuckDuckGo → Brave Search → Wikipedia
    """
    providers = [
        _search_duckduckgo,
        _search_brave,
        _search_wikipedia,
    ]
    
    for provider in providers:
        try:
            results = await provider(query, max_results)
            if results:
                logger.info(f"Search OK via {provider.__name__}")
                return results
        except Exception as e:
            logger.warning(f"Search failed via {provider.__name__}: {e}")
            continue
    
    logger.error("All search providers failed")
    return []
```

**Proveedores disponibles (en orden de preferencia):**

| Proveedor | Lib | Costo | Rate Limit | Notas |
|-----------|-----|-------|------------|-------|
| DuckDuckGo | `duckduckgo-search` (ddgs) | Gratis | Bloquea si IP es de DC | Funciona bien desde host |
| Brave Search | API REST | 2000 req/mes gratis | Generoso | Requiere API key |
| Serper.dev | API REST | 2500 búsquedas gratis | Generoso | Requiere API key |
| SearXNG local | Docker | Gratis | Sin límite | Setup propio |
| Wikipedia | `wikipedia` lib | Gratis | Sin límite | Solo Wikipedia |

---

## 4. Logging de integraciones externas

Todo llamado a servicio externo DEBE loguearse:

```python
import time
import logging

logger = logging.getLogger(__name__)

async def call_external_service(url: str, payload: dict) -> dict:
    start = time.time()
    try:
        response = await client.post(url, json=payload)
        elapsed = time.time() - start
        logger.info(
            "external_call",
            extra={
                "url": url,
                "status": response.status_code,
                "elapsed_ms": round(elapsed * 1000),
            }
        )
        return response.json()
    except Exception as e:
        elapsed = time.time() - start
        logger.error(
            "external_call_failed",
            extra={
                "url": url,
                "error": str(e),
                "elapsed_ms": round(elapsed * 1000),
            }
        )
        raise
```

---

## 5. Demo rápida con Cloudflare Tunnel

Para mostrar un proyecto sin deploy real (I+D+I):

```bash
# Instalar cloudflared si no está
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Exponer frontend y backend
cloudflared tunnel --url http://localhost:3000  # Frontend
cloudflared tunnel --url http://localhost:8000  # Backend
```

Genera URLs públicas temporales (duran hasta que se cierra el proceso). Ideal para demos sin infraestructura.

**Regla:** Solo para demos. Nunca en producción.

---

## 6. Checklist de integración (antes de mergear)

- [ ] Spike validado en entorno real (host o Docker)
- [ ] Proveedor principal funciona desde el entorno target
- [ ] Fallback implementado si el servicio puede fallar
- [ ] Logging de cada llamada externa (éxito y error)
- [ ] Variables de entorno para API keys (nunca hardcodeadas)
- [ ] Timeout configurado (nunca esperar infinito)
- [ ] Rate limit documentado en CONSTITUTION o README

---

## Pitfalls

- **DuckDuckGo desde Docker:** Bloquea por IP de datacenter. Correr desde host.
- **ddgs vs duckduckgo_search:** La lib cambió de nombre. Usar `from duckduckgo_search import DDGS` y `ddgs.text()`. Los campos son `href` y `body`, no `url` y `snippet`.
- **SearXNG con bot detection:** Incluso con `pass_ip=true` puede devolver 403. Configurar `limiter.toml` para desactivarlo completamente.
- **Brave Search gratis:** 2000 req/mes. Suficiente para I+D+I, no para producción con tráfico real.
- **Timeouts:** Siempre setear `timeout=10` o similar. Sin timeout, una API lenta bloquea todo el worker.
- **Sync repo: agregar skill nueva a sync-to-repo.sh:** Cada vez que se crea una skill nueva (`skill_manage action=create`), agregarla manualmente al array `SKILLS=()` en `/home/server/repos/nelson-hermes-skills/sync-to-repo.sh` antes de hacer el sync. Si se olvida, la skill no se pushea al repo.
- **Token GitHub expira:** El token personal de GitHub (`ghp_...`) tiene vida limitada. Cuando `gh auth status` muestra "The token in default is invalid", re-autenticar con `gh auth login -h github.com -p https --with-token < ~/secrets/github_token.txt`. El token nuevo se genera en https://github.com/settings/tokens/new (scope: `repo` completo). Para push sin terminal interactiva: `git push "https://$(gh auth token)@github.com/USER/REPO.git" main`. Guardar siempre el token nuevo en `~/secrets/github_token.txt` (chmod 600).
