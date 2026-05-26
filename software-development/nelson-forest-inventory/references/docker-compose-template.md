# docker-compose.yml — ForestAI PoC

⚠️ **Usar puertos 8010/3010** para no pisar otros proyectos en el servidor
(8000 lo ocupa rag-poc, 3000 lo ocupa Hermes/Tailscale).

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8010:8000"    # ← 8010 externo para no pisar rag-poc (8000)
    env_file: .env
    volumes:
      - ./backend:/app
      - uploads_data:/app/uploads
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-net
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery_worker:
    build: ./backend
    env_file: .env
    volumes:
      - ./backend:/app
      - uploads_data:/app/uploads
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-net
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2

  frontend:
    build: ./frontend
    ports:
      - "3010:80"    # ← 3010 externo para no pisar otros frontends
    depends_on:
      - backend
    networks:
      - app-net

  db:
    image: postgis/postgis:16-3.4-alpine    # ← PostGIS incluido, no postgres:16
    environment:
      POSTGRES_USER: forestai
      POSTGRES_PASSWORD: forestai2026
      POSTGRES_DB: forestai
    ports:
      - "5433:5432"    # ← 5433 para no chocar con postgres local
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - app-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U forestai"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"    # ← 6380 para no chocar con redis local
    networks:
      - app-net

volumes:
  pgdata:
  uploads_data:

networks:
  app-net:
    driver: bridge
```

## .env

```
DATABASE_URL=postgresql://forestai:forestai2026@db:5432/forestai
REDIS_URL=redis://redis:6379/0
SECRET_KEY=forestai-secret-dev-2026
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_MB=500
VITE_API_URL=http://localhost:8010
```

## Dockerfile Backend (CORREGIDO — NO instalar libgdal-dev)

```dockerfile
FROM python:3.11-slim

# ⚠️ NO instalar gdal-bin ni libgdal-dev del SO.
# Rasterio trae GDAL compilado dentro de su wheel binario — instalar libgdal-dev
# causa conflictos de versión y falla con exit code 100 en Docker build.
# Solo se necesita: gcc, python3-dev, libglib2.0-0 (OpenCV), libgl1 (OpenCV).
RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev \
    libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV UPLOAD_DIR=/app/uploads
RUN mkdir -p /app/uploads

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## requirements.txt Backend

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
celery[redis]>=5.3.6
rasterio>=1.3.9
opencv-python-headless>=4.9.0
geopandas>=0.14.3
shapely>=2.0.3
numpy>=1.26.4
pandas>=2.2.1
sqlalchemy>=2.0.29
alembic>=1.13.1
psycopg2-binary>=2.9.9
python-multipart>=0.0.9
pydantic-settings>=2.2.1
geoalchemy2>=0.14.3
scikit-image>=0.22.0
python-dotenv>=1.0.1
pyproj>=3.6.1
```

## Puertos ocupados en ai-server (referencia)

| Puerto | Servicio |
|--------|----------|
| 8000   | rag-poc-backend |
| 8001   | minio-backend |
| 8002   | rag-floci-azure |
| 8888   | searxng |
| 5678   | n8n |
| 6379   | Redis local |
| 5432   | Postgres local |
| **8010** | **forestai-backend** ✅ |
| **3010** | **forestai-frontend** ✅ |
| 5433   | forestai-db |
| 6380   | forestai-redis |
