---
name: nelson-embeddings
title: Embeddings - Modelos y Servicios de Vectores
description: Modelos de embeddings para el equipo Nelson. OpenAI, sentence-transformers, Ollama local. Comparativa, dimensiones, normalizacion, batching, caching.
skill: nelson-embeddings
author: equipo-nelson
version: 1.0.0
keywords: [embeddings, openai, sentence-transformers, ollama, vectors, similarity, cosine]
dependencies: []
---

# Embeddings - Equipo Nelson

## Que son los embeddings

Representaciones numericas (vectores) de texto que capturan significado semantico. Textos similares tienen vectores cercanos en el espacio.

## Modelos disponibles

| Modelo | Dimension | Costo | Calidad | Uso ideal |
|--------|-----------|-------|---------|-----------|
| `text-embedding-3-large` (OpenAI) | 3072 | $$$ | Mejor | Produccion, calidad maxima |
| `text-embedding-3-small` (OpenAI) | 1536 | $$ | Muy buena | Produccion, balance |
| `text-embedding-ada-002` (OpenAI) | 1536 | $$ | Buena | Legacy, migrar a v3 |
| `all-MiniLM-L6-v2` (sbert) | 384 | Gratis | Buena | Local, rapido, multilingue |
| `all-mpnet-base-v2` (sbert) | 768 | Gratis | Muy buena | Local, mejor calidad sbert |
| `nomic-embed-text` (Ollama) | 768 | Gratis | Buena | Local, open source |
| `BAAI/bge-large-en` | 1024 | Gratis | Excelente | RAG avanzado, re-ranking |

> **Default del equipo: OpenAI text-embedding-3-small** para produccion, **all-MiniLM-L6-v2** para desarrollo local.

## Servicio de Embeddings

```python
# app/services/embeddings.py
import os
from typing import List
import numpy as np
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    def __init__(self, provider: str = None):
        self.provider = provider or settings.EMBEDDING_PROVIDER
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

        elif self.provider == "local":
            from sentence_transformers import SentenceTransformer
            self.client = SentenceTransformer(self.model)

        elif self.provider == "ollama":
            import ollama
            self.client = ollama

        logger.info("embedding_service_init", provider=self.provider, model=self.model)

    def embed_single(self, text: str) -> List[float]:
        """Embedir un solo texto."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embedir batch de textos."""
        if not texts:
            return []

        # Limpiar textos vacios
        texts = [t.strip() for t in texts if t.strip()]

        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [d.embedding for d in response.data]

        elif self.provider == "local":
            embeddings = self.client.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()

        elif self.provider == "ollama":
            results = []
            for text in texts:
                resp = self.client.embed(model=self.model, input=text)
                results.append(resp["embedding"])
            return results

        raise ValueError(f"Provider desconocido: {self.provider}")

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcular similitud coseno entre dos vectores."""
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))
```

## Configuracion

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"   # openai | local | ollama
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    
    # OpenAI
    OPENAI_API_KEY: str | None = None
    
    # Local (sentence-transformers)
    LOCAL_MODEL_PATH: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "nomic-embed-text"

    class Config:
        env_file = ".env"
```

```
# .env (produccion)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
OPENAI_API_KEY=sk-...

# .env (desarrollo local)
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

## Dependencias por provider

```bash
# OpenAI
pip install openai

# Local (sentence-transformers)
pip install sentence-transformers torch

# Ollama
pip install ollama
```

## Caching de embeddings

```python
# app/services/embeddings_cache.py
import hashlib
import json
from functools import lru_cache

class EmbeddingCache:
    def __init__(self, maxsize: int = 10000):
        self.cache = {}
        self.maxsize = maxsize

    def _key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, text: str) -> list[float] | None:
        return self.cache.get(self._key(text))

    def set(self, text: str, embedding: list[float]):
        if len(self.cache) >= self.maxsize:
            # LRU simple: eliminar primer item
            self.cache.pop(next(iter(self.cache)))
        self.cache[self._key(text)] = embedding
```

## Normalizacion

OpenAI embeddings ya vienen normalizados (longitud = 1). Sentence-transformers tambien por defecto. Si usas modelos custom:

```python
def normalize(embedding: list[float]) -> list[float]:
    vec = np.array(embedding)
    return (vec / np.linalg.norm(vec)).tolist()
```

## Batching optimo

| Provider | Batch size ideal | Notas |
|----------|-----------------|-------|
| OpenAI | 100-500 | Rate limit: 3000 req/min |
| Local (GPU) | 32-64 | Depende de VRAM |
| Local (CPU) | 8-16 | Mas chico para no bloquear |
| Ollama | 1 | No soporta batch nativo |

## Comparacion rapida

```python
from app.services.embeddings import EmbeddingService

# OpenAI
svc = EmbeddingService(provider="openai", model="text-embedding-3-small")
emb = svc.embed_single("Hola mundo")
print(len(emb))  # 1536

# Local
svc = EmbeddingService(provider="local", model="all-MiniLM-L6-v2")
emb = svc.embed_single("Hola mundo")
print(len(emb))  # 384

# Ollama
svc = EmbeddingService(provider="ollama", model="nomic-embed-text")
emb = svc.embed_single("Hola mundo")
print(len(emb))  # 768
```

## Checklist

- [ ] Dimension del embedding coincide con la coleccion de Qdrant
- [ ] Mismo provider/modelo para indexacion y query
- [ ] API key configurada si usa OpenAI
- [ ] Modelo local descargado si usa sentence-transformers
- [ ] Ollama corriendo si usa Ollama
- [ ] Caching activado para textos repetidos
- [ ] Batching para ingestion masiva

## Pitfalls

- OpenAI rate limits: usar batching y backoff exponencial
- all-MiniLM-L6-v2 es multilingue pero mejor en ingles
- Ollama embed es lento para batches; procesar 1 a 1
- No mezclar embeddings de modelos diferentes en la misma coleccion
- text-embedding-3-large es mejor pero 2x mas caro y 2x dimension
- Siempre verificar que los embeddings no sean todos ceros (modelo no cargado)
