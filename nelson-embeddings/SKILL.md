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
| `BAAI/bge-m3` (vía SIE) | 1024 | Gratis | Excelente | Multilingüe, dense+sparse, hybrid search con Qdrant |
| `BAAI/bge-reranker-v2-m3` (vía SIE) | — | Gratis | Excelente | Reranker cross-encoder multilingüe |
| `urchade/gliner_multi-v2.1` (vía SIE) | — | Gratis | Muy buena | NER zero-shot ES/EN, extracción de entidades |

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

## SIE — Superlinked Inference Engine (servidor de inferencia local)

SIE es un servidor open source (Apache 2.0) que expone embeddings, reranking y
extracción de entidades via HTTP. Alternativa local/self-hosted a OpenAI embeddings.
Repo: https://github.com/superlinked/sie

```bash
# Deploy en CPU (no requiere GPU para modelos medium)
docker run -d --name sie-server -p 8080:8080 --restart unless-stopped \
  -e SIE_TELEMETRY_DISABLED=1 \
  ghcr.io/superlinked/sie-server:latest-cpu-default

pip install sie-sdk sie-qdrant
```

### Tres funciones de SIE

| Función | Descripción | Modelo recomendado |
|---------|------------|-------------------|
| `encode` | texto → vector dense/sparse | `BAAI/bge-m3` (multilingüe, 1024d, hybrid) |
| `score` | reranking cross-encoder | `BAAI/bge-reranker-v2-m3` |
| `extract` | NER zero-shot sin entrenamiento | `urchade/gliner_multi-v2.1` |

```python
from sie_sdk import SIEClient
from sie_sdk.types import Item

client = SIEClient("http://localhost:8080")

# Embed
result = client.encode("BAAI/bge-m3", Item(text="texto a embeber"))
# result["dense"] → vector 1024d, result["sparse"] → dict índices/valores

# Rerank (cross-encoder: ve query+doc juntos, más preciso que vectores)
scores = client.score(
    "BAAI/bge-reranker-v2-m3",
    Item(text="query"),
    [Item(text=doc, item_id=str(i)) for i, doc in enumerate(docs)]
)
# scores["scores"] → [{"item_id": "0", "score": 0.98, "rank": 0}, ...]

# NER zero-shot
entities = client.extract(
    "urchade/gliner_multi-v2.1",
    Item(text="Trabajando en ForestAI con FastAPI y Docker"),
    labels=["proyecto", "tecnología", "persona", "organización"]
)
# entities["entities"] → [{"text": "ForestAI", "label": "proyecto", "score": 0.94}]
```

### Integración con Qdrant (hybrid search)

```python
from sie_qdrant import SIENamedVectorizer
from qdrant_client.models import SparseVector, PointStruct

vectorizer = SIENamedVectorizer(
    base_url="http://localhost:8080",
    model="BAAI/bge-m3",
    output_types=["dense", "sparse"],
)
named = vectorizer.embed_documents(["texto"])
# → named[0]["dense"] y named[0]["sparse"] listos para Qdrant
```

### Compatibilidad OpenAI drop-in

SIE expone `/v1/embeddings` compatible con OpenAI SDK:
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080", api_key="unused")
resp = client.embeddings.create(model="BAAI/bge-m3", input=["texto"])
```

### Cuándo usar SIE vs otras opciones

| Situación | Recomendación |
|-----------|--------------|
| Producción, máxima calidad, presupuesto OK | OpenAI text-embedding-3-large |
| Self-hosted, multilingüe, hybrid search | SIE + BAAI/bge-m3 |
| Dev local, rápido, sin setup | sentence-transformers all-MiniLM-L6-v2 |
| Reranking de resultados de búsqueda | SIE score + bge-reranker-v2-m3 |
| NER automático de mensajes/docs | SIE extract + gliner_multi-v2.1 |

Agregar `BAAI/bge-m3` a la tabla de modelos del equipo: 1024d, gratis/local vía SIE,
calidad excelente para RAG multilingüe y hybrid search con Qdrant.

## Pitfalls

- OpenAI rate limits: usar batching y backoff exponencial
- all-MiniLM-L6-v2 es multilingue pero mejor en ingles
- Ollama embed es lento para batches; procesar 1 a 1
- No mezclar embeddings de modelos diferentes en la misma coleccion
- text-embedding-3-large es mejor pero 2x mas caro y 2x dimension
- Siempre verificar que los embeddings no sean todos ceros (modelo no cargado)
- SIE: el primer request tarda (descarga el modelo on-demand). Calentar con un request dummy al iniciar el servicio.
- SIE: modelos large (BGE-M3 completo) requieren ~4-8GB RAM. En CPU la latencia es ~200-500ms/doc para dense+sparse.
- SIE reranker: es cross-encoder (ve query+doc juntos) → más preciso que cosine similarity pero más lento. Usar como segunda etapa sobre candidatos pre-filtrados (top-20 → rerank → top-5).
