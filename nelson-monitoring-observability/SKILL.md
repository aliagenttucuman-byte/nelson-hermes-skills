---
name: nelson-monitoring-observability
description: Observabilidad mínima para PoCs del equipo Nelson. Logging estructurado, health checks, Docker healthcheck, métricas básicas. Python/FastAPI.
category: software-development
tags: [observabilidad, logging, health-check, prometheus, docker, fastapi, python, poc]
related_skills: [nelson-project-bootstrap, nelson-frontend-stack, nelson-ci-cd]
---

# Observabilidad para PoCs — Equipo Nelson

> **Trigger:** Al crear un nuevo backend para un PoC. Siempre incluir logging estructurado y health checks desde el día 1.

## Principio

Un PoC sin observabilidad es un cajón negro. Pablo no puede ver si funciona. No sabemos si se rompió. Agregar logging y health checks al final es más caro que desde el inicio.

Regla del equipo: **todo backend FastAPI tiene /health y logging estructurado.**

---

## 1. Logging Estructurado (Python)

### Opción A: logging estándar + JSONFormatter (mínimo)

```python
# backend/app/core/logging.py
import logging
import sys
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))
    root.handlers = [handler]
    
    # Reducir ruido de librerías
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

### Opción B: structlog (recomendado para proyectos > PoC)

```python
# backend/app/core/logging.py
import structlog
import logging


def setup_logging(level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
```

Uso en endpoints:

```python
from fastapi import Request
import structlog

logger = structlog.get_logger()

@app.get("/api/users")
async def list_users(request: Request):
    logger.info("list_users_called", path=request.url.path, method="GET")
    # ...
```

---

## 2. Health Checks

### Endpoint /health (obligatorio en todo PoC)

```python
# backend/app/api/health.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import time

router = APIRouter()

_start_time = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    version: str
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    checks = {
        "api": "ok",
        # Agregar checks específicos del PoC:
        # "database": check_db(),
        # "ollama": check_ollama(),
        # "qdrant": check_qdrant(),
    }
    
    all_ok = all(v == "ok" for v in checks.values())
    
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        uptime_seconds=round(time.time() - _start_time, 2),
        version="0.1.0",
        checks=checks,
    )
```

### En main.py:

```python
from app.api import health

app.include_router(health.router, tags=["health"])
```

---

## 3. Docker Healthcheck

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Healthcheck: FastAPI debe responder en /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

En docker-compose.yml:

```yaml
services:
  backend:
    build: ./backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

---

## 4. Métricas Básicas (Opcional, para PoCs avanzados)

```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter("http_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_DURATION = Histogram("http_request_duration_seconds", "Request duration", ["method", "endpoint"])


async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)
    
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    return response


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Agregar al main:

```python
app.middleware("http")(metrics_middleware)
```

Dependencias:
```
prometheus-client>=0.20.0
```

---

## 5. Estructura de Carpetas Recomendada

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging.py      ← setup_logging()
│   │   └── config.py       ← pydantic-settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py       ← /health endpoint
│   │   └── ...             ← otros routers
│   └── ...
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

---

## 6. Docker Compose Completo (Patrón Estándar)

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      LOG_LEVEL: INFO
      ENV: production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    depends_on:
      ollama:
        condition: service_started
      qdrant:
        condition: service_started

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  ollama_data:
  qdrant_data:
```

**Nota:** `depends_on` con `condition: service_healthy` requiere Docker Compose v2.20+ o la opción `--compatibility`.

---

## Pitfalls

1. **No loggear en producción con print():** Siempre usar logging estructurado. Los logs de print no tienen timestamp, nivel, ni son parseables.
2. **Exponer /metrics sin auth:** En producción real, proteger `/metrics` con auth o no exponerlo públicamente. En PoCs locales, no importa.
3. **Health check que depende de DB externa:** Si el health check falla cuando la DB está caída, Docker reiniciará el container. Considerar si queremos eso o si el health check solo chequea que la API responda.
4. **Falta de `start_period`:** Sin start_period, Docker marca el container como unhealthy durante el startup de FastAPI. Siempre incluir `start_period: 10s` mínimo.
5. **Logging de credenciales:** Nunca loggear headers de auth, tokens, ni contraseñas. Usar filtros si es necesario.
6. **Uvicorn logs duplicados:** Si usás `logging.basicConfig()` y `uvicorn.run()`, los logs pueden salir duplicados. Desactivar `uvicorn.access` o configurar el handler de uvicorn.

---

## Comandos Útiles

```bash
# Ver logs estructurados en tiempo real
docker compose logs -f backend | jq .

# Ver health de un container
docker inspect --format='{{.State.Health.Status}}' CONTAINER_NAME

# Forzar health check manual
docker exec CONTAINER_NAME curl -f http://localhost:8000/health

# Métricas Prometheus (si están habilitadas)
curl http://localhost:8000/metrics
```

---

## Referencias

- structlog docs: https://www.structlog.org/
- prometheus_client: https://github.com/prometheus/client_python
- FastAPI logging: https://fastapi.tiangolo.com/advanced/logging/
