---
name: nelson-observability
title: Observabilidad - Logging + Health Checks + Metricas
description: Observabilidad para el equipo Nelson. Logging estructurado JSON, health checks detallados, metricas Prometheus, middleware de trazas. Python structlog + FastAPI.
skill: nelson-observability
author: equipo-nelson
version: 1.0.0
keywords: [logging, observability, prometheus, health-checks, structlog, metrics, monitoring]
dependencies: [fastapi]
---

# Observabilidad - Equipo Nelson

## Stack

| Capa | Libreria | Version |
|------|----------|---------|
| Logging | structlog | ^24.4 |
| Health | FastAPI built-in / custom | - |
| Metricas | prometheus-client | ^0.21 |
| Trazas | opentelemetry (opcional) | ^1.29 |

## Logging Estructurado (JSON)

```python
# app/core/logging.py
import structlog
import logging
import sys

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def get_logger(name: str):
    return structlog.get_logger(name)
```

Uso:
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("usuario_creado", user_id=42, email="nelson@example.com")
logger.error("db_connection_failed", retry_count=3, exc_info=True)
```

Output JSON:
```json
{
  "event": "usuario_creado",
  "user_id": 42,
  "email": "nelson@example.com",
  "logger": "app.api.users",
  "level": "info",
  "timestamp": "2026-05-11T18:30:00.000Z"
}
```

## Health Checks

```python
# app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.logging import get_logger
import time

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)

START_TIME = time.time()

@router.get("")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "checks": {"database": "ok"}}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": {"database": "fail"}})

@router.get("/live")
def liveness_check():
    uptime = time.time() - START_TIME
    return {"status": "alive", "uptime_seconds": int(uptime)}
```

## Metricas Prometheus

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

APP_INFO = Info("app_info", "Application info")
APP_INFO.info({"version": "0.1.0", "name": "nelson-backend"})

async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    path = request.url.path
    method = request.method
    status = str(response.status_code)

    REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

    return response
```

Endpoint metrics:
```python
@router.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

## Middleware de Request Logging

```python
# app/main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger = get_logger("http")

    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        query=str(request.query_params),
        client=request.client.host if request.client else None,
    )

    response = await call_next(request)
    duration = (time.time() - start) * 1000

    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration, 2),
    )

    return response
```

## Niveles de Log por Ambiente

```python
# app/config.py
import os

ENV = os.getenv("ENV", "development")

if ENV == "production":
    LOG_LEVEL = "WARNING"
elif ENV == "staging":
    LOG_LEVEL = "INFO"
else:
    LOG_LEVEL = "DEBUG"
```

## Docker Compose (Prometheus + Grafana opcional)

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/health/metrics'
```

## Cloud Run - Logs en GCP

En Cloud Run los logs stdout/stderr se capturan automaticamente en Cloud Logging. Con structlog en JSON, GCP los parsea perfecto y podes filtrar por campos.

Query util en GCP Logs Explorer:
```
resource.type="cloud_run_revision"
jsonPayload.level="error"
jsonPayload.event="db_connection_failed"
```

## Checklist

- [ ] structlog configurado con JSON renderer
- [ ] Health endpoints: `/health`, `/health/ready`, `/health/live`
- [ ] Metrics endpoint: `/health/metrics` (o `/metrics`)
- [ ] Request logging middleware activo
- [ ] LOG_LEVEL configurable por ambiente
- [ ] Nunca loggear PII (emails, passwords, tokens) sin enmascarar

## Pitfalls

- No loggear en loops (inunda los logs)
- No loggear bodies completos de requests en produccion
- structlog + JSON es la mejor combo para Cloud Run/GCP
- Prometheus metrics deben ser unicas por nombre; no crear labels con alta cardinalidad (user_id, email)
