# Web Search desde Docker — Pitfall y Fix

## El problema

DuckDuckGo y SearXNG públicos **bloquean requests desde IPs de containers Docker**:

- `duckduckgo_search` (vieja librería): `RatelimitException: 202 Ratelimit`
- SearXNG instancias públicas: `403 Forbidden` con bot detection JavaScript challenge
- SearXNG local en Docker: `403 Forbidden` — el header `X-Forwarded-For` / `X-Real-IP` no llega correctamente, incluso con:
  ```toml
  # limiter.toml
  [botdetection.ip_lists]
  pass_ip = ["0.0.0.0/0", "::/0"]
  ```
  ```yaml
  # settings.yml
  botdetection:
    ip_limit:
      link_token: false
    ip_lists:
      pass_ip:
        - 0.0.0.0/0
  ```

## Fix probado y funcionando

**Correr el backend como proceso en el HOST, no en Docker.**

```bash
# 1. Crear venv local en la carpeta del proyecto
cd ~/brainstorming/mi-proyecto/backend
python3 -m venv venv

# 2. Instalar dependencias (usar 'ddgs', no 'duckduckgo-search' — fue renombrado)
./venv/bin/pip install ddgs fastapi uvicorn ollama

# 3. Levantar en background
./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8004 > /tmp/backend.log 2>&1 &
```

## API correcta: `ddgs` (no `duckduckgo_search`)

La librería `duckduckgo_search` fue renombrada a `ddgs`:

```python
# ❌ Viejo (bloqueado en Docker además)
from duckduckgo_search import DDGS

# ✅ Nuevo
from ddgs import DDGS
```

Campos que devuelve `ddgs`:
```python
{"title": "...", "href": "...", "body": "..."}
# ojo: el campo URL es "href", no "url"
```

## Uso correcto

```python
from ddgs import DDGS

with DDGS() as d:
    results = list(d.text("mi consulta", max_results=5))
    for r in results:
        print(r["title"], r["href"], r["body"])
```

## Alternativas no probadas (para futuro)

- **Brave Search API**: 2,000 req/mes gratis, no bloquea bots
- **Serper.dev**: 2,500 búsquedas gratis, JSON limpio
- **Tavily API**: pensada para agentes IA, 1,000 req/mes gratis
- Estas sí funcionarían desde Docker porque son APIs con key, no scraping

## Referencia del proyecto

PoC construida: `~/brainstorming/2026-05-16-ai-search-assistant/`
- Backend: proceso host en puerto 8004 con venv local
- Frontend: Docker en puerto 8003 (nginx sirve React build)
- Túneles: cloudflared para URLs públicas temporales
