# Template Completo del Proyecto Base

> Este es el template que se genera al ejecutar `nelson-project-bootstrap`.
> Generado y verificado el 2026-05-11.

## Archivos generados

### backend/app/main.py
```python
"""Entrypoint FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
def startup():
    logger.info("app_started", version=settings.APP_VERSION, env=settings.ENV)

@app.get("/")
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION}
```

### backend/app/core/config.py
```python
"""Configuracion de la aplicacion."""

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    APP_NAME: str = "Nelson App"
    APP_VERSION: str = "0.1.0"
    ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    PORT: int = 8000
    
    SECRET_KEY: str = Field(default="change-me-in-production-32-chars")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    DATABASE_URL: str = "postgresql://nelson:secret@db:5432/appdb"
    REDIS_URL: str = "redis://redis:6379/0"
    
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    
    LLM_PROVIDER: Literal["openai", "ollama", "anthropic", "groq"] = "ollama"
    LLM_MODEL: str = "llama3.2:3b"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    
    EMBEDDING_PROVIDER: Literal["openai", "local", "ollama"] = "ollama"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSION: int = 768
    
    LOG_LEVEL: str = "INFO"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### frontend/src/lib/api.ts
```typescript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### frontend/src/index.css (Tailwind 4)
```css
@import "tailwindcss";

@theme {
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  --color-primary-900: #1e3a8a;
}

body {
  margin: 0;
  min-height: 100vh;
  background-color: #0f172a;
  color: #e2e8f0;
  font-family: 'Inter', system-ui, sans-serif;
}
```

### docker-compose.yml
```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://nelson:secret@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_HOST=qdrant
      - LLM_PROVIDER=ollama
      - LLM_MODEL=llama3.2:3b
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
      - qdrant
    networks:
      - app-net

  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - backend
    networks:
      - app-net

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: nelson
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - app-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-net

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - app-net

volumes:
  pgdata:
  qdrant_storage:

networks:
  app-net:
    driver: bridge
```

### .env.example
```
# App
APP_NAME=Nelson App
APP_VERSION=0.1.0
ENV=development
DEBUG=false
PORT=8000

# Security
SECRET_KEY=change-me-in-production-32-chars-min
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Database
DATABASE_URL=postgresql://nelson:secret@db:5432/appdb

# Redis
REDIS_URL=redis://redis:6379/0

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=

# LLM (development: ollama, production: openai)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# API Keys (solo para production)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=

# Embeddings
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768

# Logging
LOG_LEVEL=INFO

# Frontend
VITE_API_URL=http://localhost:8000/api
```

## Stack confirmado

| Capa | Tecnologia | Version |
|------|-----------|---------|
| Backend | Python | 3.12 |
| Backend | FastAPI | 0.115+ |
| Backend | SQLAlchemy | 2.0+ |
| Frontend | React | 19.0 |
| Frontend | TypeScript | 5.7 |
| Frontend | Vite | 6.0 |
| Frontend | Tailwind | 4.0 |
| DB | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Vector DB | Qdrant | latest |
| LLM dev | Ollama | llama3.2:3b |
| LLM prod | OpenAI | gpt-4o-mini |

## Notas de implementacion

1. **Tailwind 4** no usa `tailwind.config.js`. El tema se configura en CSS con `@theme`.
2. **SQLAlchemy 2.0** usa estilo declarativo con `Mapped[]` y `mapped_column()`.
3. **Pydantic v2** con `pydantic-settings` para configuracion desde `.env`.
4. **Ollama** con 4GB VRAM usa modelos chicos (3B) para 100% GPU, o modelos grandes (8B) con mix CPU/GPU.
5. **Alembic** listo para migraciones con `alembic revision --autogenerate`.
6. **structlog** para logging JSON estructurado.
7. **React Query** para estado del servidor en frontend.
8. **MSW** configurado para mocks en tests de frontend.
