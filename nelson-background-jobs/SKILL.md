---
name: nelson-background-jobs
title: Background Jobs - Celery + Redis + FastAPI
description: Procesamiento asincronico para el equipo Nelson. Celery con Redis como broker, tareas en background para ingestion de documentos, envio de emails, notificaciones. Integracion con FastAPI.
skill: nelson-background-jobs
author: equipo-nelson
version: 1.0.0
keywords: [celery, redis, background-jobs, async, tasks, queue, workers]
dependencies: [nelson-database, nelson-document-processing]
---

# Background Jobs - Equipo Nelson

## Proposito

Cuando un usuario sube un PDF de 100 paginas, no puede esperar 30 segundos en la request HTTP. Los background jobs procesan tareas pesadas async: ingestion de documentos, generacion de embeddings, envio de emails, notificaciones.

## Stack

| Componente | Libreria | Version |
|------------|----------|---------|
| Task Queue | Celery | ^5.4 |
| Broker | Redis | ^7 (Docker) |
| Result Backend | Redis | - |
| Monitor | Flower (opcional) | ^2.0 |

## Docker Compose

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  worker:
    build: ./backend
    command: celery -A app.core.celery worker --loglevel=info --concurrency=2
    environment:
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: ${DATABASE_URL}
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - redis
      - db
    volumes:
      - ./backend:/app

  beat:
    build: ./backend
    command: celery -A app.core.celery beat --loglevel=info
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./backend:/app

  # Opcional: monitor
  flower:
    image: mher/flower:latest
    ports:
      - "5555:5555"
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

## Configuracion Celery

```python
# app/core/celery.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "nelson_app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.documents", "app.tasks.notifications"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos maximo por tarea
    worker_prefetch_multiplier=1,  # Fair scheduling
)
```

## Tareas

```python
# app/tasks/documents.py
from app.core.celery import celery_app
from app.services.document_processor import DocumentProcessor
from app.services.ingestion import IngestionPipeline
from app.core.logging import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_document(self, file_bytes: bytes, filename: str, mime_type: str, user_id: int, doc_id: str):
    """Procesar documento en background."""
    try:
        logger.info("processing_document_task", doc_id=doc_id, user_id=user_id)

        # Procesar
        processor = DocumentProcessor()
        chunks = processor.process(file_bytes, filename, mime_type)

        # Ingestar
        ingestion = IngestionPipeline()
        all_text = "\n\n".join(c.text for c in chunks)

        result = ingestion.ingest_document(
            doc_id=doc_id,
            text=all_text,
            metadata={"user_id": str(user_id), "filename": filename},
        )

        # Notificar completado (otra tarea)
        notify_user_complete.delay(user_id, doc_id, result["chunks"])

        return {"status": "completed", "chunks": result["chunks"], "doc_id": doc_id}

    except Exception as exc:
        logger.error("document_processing_failed", doc_id=doc_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)
```

```python
# app/tasks/notifications.py
from app.core.celery import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)

@celery_app.task
def notify_user_complete(user_id: int, doc_id: str, chunks: int):
    """Notificar al usuario que el documento fue procesado."""
    logger.info("notifying_user", user_id=user_id, doc_id=doc_id)
    # Aca iria: email, push notification, websocket, etc.
    # Por ahora solo log
    return {"notified": user_id, "doc_id": doc_id}

@celery_app.task
def cleanup_old_documents(days: int = 30):
    """Tarea periodica: eliminar documentos viejos."""
    from app.database import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        db.execute(text(f"DELETE FROM documents WHERE created_at < NOW() - INTERVAL '{days} days'"))
        db.commit()
        logger.info("cleanup_completed", days=days)
    finally:
        db.close()
```

## Programacion de tareas periodicas (Celery Beat)

```python
# app/core/celery.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(...)

celery_app.conf.beat_schedule = {
    "cleanup-old-docs": {
        "task": "app.tasks.notifications.cleanup_old_documents",
        "schedule": crontab(hour=2, minute=0),  # Todos los dias a las 2 AM
        "args": (30,),
    },
    "health-check": {
        "task": "app.tasks.notifications.health_check_task",
        "schedule": 300.0,  # Cada 5 minutos
    },
}
```

## Endpoint async en FastAPI

```python
# app/api/v1/documents.py
from fastapi import APIRouter, UploadFile, File, Depends
from app.tasks.documents import process_document
from app.api.deps import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
):
    file_bytes = await file.read()
    doc_id = f"doc_{current_user.id}_{file.filename}"

    # Encolar tarea async
    task = process_document.delay(
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
        user_id=current_user.id,
        doc_id=doc_id,
    )

    return {
        "task_id": task.id,
        "doc_id": doc_id,
        "status": "queued",
        "message": "Documento encolado para procesamiento",
    }

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    from app.core.celery import celery_app
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
```

## Monitoreo con Flower

Flower corre en `http://localhost:5555` y muestra:
- Tareas activas, fallidas, exitosas
- Workers conectados
- Colas y throughput
- Retry stats

## Dependencias

```bash
pip install celery[redis] redis flower
```

## Configuracion entorno

```
# .env
REDIS_URL=redis://localhost:6379/0
# o para Docker:
REDIS_URL=redis://redis:6379/0
```

## Comandos utiles

```bash
# Levantar worker
celery -A app.core.celery worker --loglevel=info --concurrency=2

# Levantar scheduler (beat)
celery -A app.core.celery beat --loglevel=info

# Monitoreo
celery -A app.core.celery flower --port=5555

# Limpiar cola
celery -A app.core.celery purge

# Inspeccionar
celery -A app.core.celery inspect active
celery -A app.core.celery inspect stats
```

## Checklist

- [ ] Redis corriendo y accesible
- [ ] Worker levantado y conectado
- [ ] Tareas encoladas desde FastAPI
- [ ] Estado de tareas consultable (`/tasks/{task_id}`)
- [ ] Retry configurado para tareas fallibles
- [ ] Flower accesible para monitoreo
- [ ] Tareas periodicas configuradas en beat_schedule

## Pitfalls

- `file_bytes` en Celery debe ser serializable (bytes lo es, pero objetos UploadFile no)
- Siempre usar `.delay()` o `.apply_async()`, nunca llamar la funcion directamente
- Redis debe tener persistencia si no queres perder tareas en reinicio
- Workers comparten el codigo del backend; si cambias tasks, reinicia workers
- Flower no debe estar expuesto a internet sin auth
- Tasks largos (>5 min) pueden ser killadas por `task_time_limit`
