---
name: nelson-vector-databases
title: Bases de Datos Vectoriales - Qdrant, Chroma, Weaviate
description: Bases de datos vectoriales para el equipo Nelson. Qdrant como principal (open source, Rust, rapido), Chroma para prototipos, Weaviate como alternativa. Docker, SDK Python, patrones de uso.
skill: nelson-vector-databases
author: equipo-nelson
version: 1.0.0
keywords: [qdrant, chroma, weaviate, vector-database, embeddings, similarity-search, ann]
dependencies: [nelson-database]
---

# Bases de Datos Vectoriales - Equipo Nelson

## Comparativa

| BD Vectorial | Uso ideal | Pros | Contras |
|--------------|-----------|------|---------|
| **Qdrant** | Produccion, alto throughput | Rust, rapido, filtrado hibrido, cloud managed | Mas recursos que Chroma |
| **Chroma** | Prototipos, local, embeddable | Zero config, SQLite por defecto, facil | No escala bien en produccion |
| **Weaviate** | Graph + vector, modular | GraphQL nativo, modulos NLP integrados | Mas complejo, mas recursos |

> **Default del equipo: Qdrant**. Chroma solo para spikes/prototipos.

## Qdrant

### Docker local

```yaml
# docker-compose.yml (agregar al proyecto)
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"      # REST API
      - "6334:6334"      # gRPC
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333

volumes:
  qdrant_storage:
```

### SDK Python

```bash
pip install qdrant-client
```

### Patron de uso completo

```python
# app/services/vector_store.py
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)
from app.config import settings

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

    def create_collection(self, name: str, vector_size: int = 1536):
        """Crear coleccion si no existe."""
        if not self.client.collection_exists(name):
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(self, collection: str, vectors: list[list[float]], payloads: list[dict], ids: list[str]):
        """Insertar o actualizar vectores."""
        points = [
            PointStruct(id=id_, vector=vec, payload=payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=collection, points=points)

    def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        """Buscar similares con filtrado opcional."""
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]

    def delete_by_filter(self, collection: str, key: str, value: str):
        """Eliminar puntos por metadata."""
        self.client.delete(
            collection_name=collection,
            points_selector=Filter(
                must=[FieldCondition(key=key, match=MatchValue(value=value))]
            ),
        )
```

Uso:
```python
store = VectorStore()
store.create_collection("documents", vector_size=1536)

# Insertar
store.upsert(
    collection="documents",
    vectors=[[0.1, 0.2, ...]],  # embeddings
    payloads=[{"text": "contenido", "source": "manual.pdf", "page": 1}],
    ids=["doc_1"],
)

# Buscar
results = store.search(
    collection="documents",
    query_vector=[0.1, 0.2, ...],  # embedding de la query
    limit=5,
    filters={"source": "manual.pdf"},  # Filtrado hibrido
)
```

### Filtrado hibrido (vector + metadata)

Qdrant permite combinar busqueda vectorial con filtros exactos. Esto es clave para RAG con restricciones:

```python
# Solo buscar en documentos de cierto usuario y tipo
results = store.search(
    collection="documents",
    query_vector=query_embedding,
    filters={"user_id": "42", "doc_type": "contrato"},
)
```

## Chroma (prototipos)

```bash
pip install chromadb
```

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("docs")

collection.add(
    documents=["texto 1", "texto 2"],
    metadatas=[{"source": "a"}, {"source": "b"}],
    ids=["1", "2"],
)

results = collection.query(
    query_texts=["query"],
    n_results=5,
    where={"source": "a"},
)
```

## Weaviate (alternativa)

```bash
pip install weaviate-client
```

```python
import weaviate
client = weaviate.Client("http://localhost:8080")
```

## Configuracion de entorno

```
# .env
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=          # Solo para Qdrant Cloud
```

## Qdrant Cloud (produccion)

```python
client = QdrantClient(
    url="https://tu-cluster.cloud.qdrant.io",
    api_key="tu-api-key",
)
```

## Checklist

- [ ] Coleccion creada con vector_size correcto (depende del modelo de embeddings)
- [ ] Distance: COSINE para OpenAI, DOT para sentence-transformers normalizados
- [ ] Payload indexado si se usa filtrado frecuente
- [ ] Backups configurados en produccion
- [ ] Qdrant Cloud o cluster propio con replicacion

## Pitfalls

- Vector size debe coincidir EXACTAMENTE con el modelo de embeddings (1536 OpenAI, 768 all-MiniLM, etc.)
- No usar Chroma en produccion con concurrencia alta (SQLite locks)
- Qdrant gRPC es mas rapido que REST para bulk operations
- Siempre indexar campos de payload usados en filtros
- embeddings de query y documentos deben venir del MISMO modelo
