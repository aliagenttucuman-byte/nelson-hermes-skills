---
name: nelson-rag-pipeline
title: RAG Pipeline - Retrieval Augmented Generation
description: Pipeline completa de RAG para el equipo Nelson. Chunking, embeddings, retrieval, re-ranking, generation. Integracion con FastAPI, patrones de prompts, manejo de contexto.
skill: nelson-rag-pipeline
author: equipo-nelson
version: 1.0.0
keywords: [rag, retrieval, llm, prompts, chunking, context, openai, ollama]
dependencies: [nelson-vector-databases, nelson-embeddings]
---

# RAG Pipeline - Equipo Nelson

## Que es RAG

Retrieval Augmented Generation: en vez de preguntarle directo al LLM, primero buscamos documentos relevantes en una base vectorial y se los pasamos como contexto. Asi el LLM responde con datos actualizados y verificables.

## Flujo completo

```
Documentos brutos
       |
       v
  [Chunking]        <-- Dividir en fragmentos semanticos
       |
       v
  [Embeddings]      <-- Convertir a vectores
       |
       v
  [Vector Store]    <-- Guardar en Qdrant
       |
       v
  Query del usuario
       |
       v
  [Embedding query] <-- Mismo modelo
       |
       v
  [Retrieval]       <-- Top-K similares desde Qdrant
       |
       v
  [Re-ranking]      <-- Opcional: mejorar orden
       |
       v
  [Prompt builder]  <-- Contexto + instrucciones + query
       |
       v
  [LLM]             <-- Generar respuesta
       |
       v
  Respuesta + Sources
```

## Componentes

### 1. Chunking

```python
# app/services/chunking.py
from typing import List
import re

def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[dict]:
    """Divide texto en chunks con overlap."""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]

        # Buscar fin de oracion para no cortar a mitad
        if end < text_len:
            last_period = chunk.rfind(".")
            if last_period > chunk_size * 0.7:
                end = start + last_period + 1
                chunk = text[start:end]

        chunks.append({
            "text": chunk.strip(),
            "start": start,
            "end": end,
        })
        start = end - chunk_overlap

    return chunks
```

### 2. Ingestion Pipeline

```python
# app/services/ingestion.py
from app.services.chunking import chunk_text
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore

class IngestionPipeline:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.store = VectorStore()

    def ingest_document(self, doc_id: str, text: str, metadata: dict):
        """Procesar un documento completo."""
        chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)

        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.embed_batch(texts)

        payloads = [
            {
                "text": chunk["text"],
                "doc_id": doc_id,
                "chunk_index": i,
                **metadata,
            }
            for i, chunk in enumerate(chunks)
        ]

        import uuid

        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]

        self.store.upsert(
            collection="documents",
            vectors=embeddings,
            payloads=payloads,
            ids=ids,
        )

        return {"chunks": len(chunks), "doc_id": doc_id}
```

### 3. RAG Service

```python
# app/services/rag.py
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.core.llm import LLMService
from app.core.logging import get_logger

logger = get_logger(__name__)

class RAGService:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.store = VectorStore()
        self.llm = LLMService()

    def ask(self, question: str, filters: dict | None = None, top_k: int = 5) -> dict:
        """Responder pregunta usando RAG."""
        logger.info("rag_query", question=question, filters=filters)

        # 1. Embedding de la pregunta
        query_embedding = self.embedder.embed_single(question)

        # 2. Retrieval
        results = self.store.search(
            collection="documents",
            query_vector=query_embedding,
            limit=top_k,
            filters=filters,
        )

        if not results:
            return {
                "answer": "No encontre informacion relevante para responder.",
                "sources": [],
            }

        # 3. Construir contexto
        context = "\n\n".join(
            f"[Documento {i+1}]\n{r['payload']['text']}"
            for i, r in enumerate(results)
        )

        sources = [
            {
                "id": r["id"],
                "score": r["score"],
                "doc_id": r["payload"].get("doc_id"),
                "source": r["payload"].get("source"),
            }
            for r in results
        ]

        # 4. Prompt
        prompt = self._build_prompt(context, question)

        # 5. Generar
        answer = self.llm.generate(prompt)

        logger.info("rag_answer", question=question, sources_count=len(sources))

        return {"answer": answer, "sources": sources}

    def _build_prompt(self, context: str, question: str) -> str:
        return f"""Eres un asistente util. Responde la pregunta del usuario usando UNICAMENTE la informacion proporcionada en el contexto.
Si la respuesta no esta en el contexto, di "No tengo suficiente informacion para responder."

CONTEXTO:
{context}

PREGUNTA: {question}

RESPUESTA:"""
```

### 4. Endpoint FastAPI

```python
# app/api/v1/rag.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.rag import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])

class AskRequest(BaseModel):
    question: str
    filters: dict | None = None
    top_k: int = 5

class AskResponse(BaseModel):
    answer: str
    sources: list[dict]

@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    rag = RAGService()
    return rag.ask(
        question=request.question,
        filters=request.filters,
        top_k=request.top_k,
    )

@router.post("/ingest")
def ingest(doc_id: str, text: str, metadata: dict | None = None):
    from app.services.ingestion import IngestionPipeline
    pipeline = IngestionPipeline()
    return pipeline.ingest_document(doc_id, text, metadata or {})
```

## Prompt Engineering para RAG

### System prompt efectivo

```
Eres un asistente experto. Sigue estas reglas:
1. Usa SOLO la informacion del contexto proporcionado
2. Si no sabes, di "No lo se" — no inventes
3. Cita las fuentes usando [Doc X]
4. Se conciso y directo
5. Si hay informacion contradictoria, mencionalo
```

### Estrategias avanzadas

| Estrategia | Cuando usar |
|------------|-------------|
| **HyDE** | Query ambigua: generar respuesta hipotetica primero, luego buscar |
| **Re-ranking** | Muchos resultados: usar cross-encoder para reordenar top-100 |
| **Query expansion** | Query corta: generar sinonimos/parafrases y buscar todos |
| **Multi-query** | Pregunta compleja: descomponer en sub-preguntas |
| **Self-correction** | Respuesta dudosa: pedir al LLM que verifique su propia respuesta |

## HyDE (Hypothetical Document Embedding)

```python
def hyde_retrieval(question: str) -> list[dict]:
    # 1. Generar respuesta hipotetica
    hypothetical = llm.generate(f"Responde esta pregunta: {question}")
    
    # 2. Embedding de la respuesta hipotetica (mas rico semanticamente)
    embedding = embedder.embed_single(hypothetical)
    
    # 3. Buscar con ese embedding
    return store.search(collection="documents", query_vector=embedding, limit=5)
```

## Evaluacion de RAG

```python
# Metricas basicas
def evaluate_rag(question: str, expected_answer: str) -> dict:
    result = rag.ask(question)
    
    # Retrieval: encontramos el chunk correcto?
    # Answer: la respuesta es correcta? (LLM-as-judge o similaridad semantica)
    
    return {
        "retrieval_hit": check_chunk_in_sources(expected_answer, result["sources"]),
        "answer_similarity": semantic_similarity(expected_answer, result["answer"]),
    }
```

## Docker Compose con Qdrant + Ollama

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes:
      - qdrant_data:/qdrant/storage

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  qdrant_data:
  ollama_data:
```

## Testing y Validación

Antes de entregar un sistema RAG, validar con un documento de prueba extenso y realizar consultas de diferentes tipos:

### Tipos de pregunta a probar
| Tipo | Ejemplo | Que valida |
|------|---------|-----------|
| **Hecho directo** | "Cuantos dias de vacaciones para 8 anos de antiguedad?" | Retrieval preciso de tabla/dato especifico |
| **Reformulacion** | "Padre por nacimiento de hijo" vs "licencia por paternidad" | Robustez del embedding ante sinonimos |
| **Inferencia** | "Si un empleado tiene calificacion 4.5, cual es su bono?" | Combinacion de retrieval + razonamiento del LLM |
| **Negativa** | "Cual es la politica de viajes al exterior?" | El sistema dice "no se" cuando no hay info |

### Pipeline de prueba recomendado
1. Generar o usar un PDF extenso de prueba (12+ paginas, tablas, datos).
2. Subir via endpoint `/documents/upload` y verificar chunks procesados.
3. Verificar indexacion en Qdrant (`GET /collections/documents`).
4. Ejecutar 4-6 preguntas variadas y verificar que las respuestas citan el documento.
5. Revisar logs del backend para confirmar scores de retrieval > 0.6.

## Checklist

- [ ] Mismo modelo de embedding para ingestion y query
- [ ] Chunk size apropiado (500-1000 tokens typical)
- [ ] Overlap de 10-20% entre chunks
- [ ] Metadata util en payloads (source, date, category)
- [ ] Prompt claro con instrucciones de no alucinar
- [ ] Sources devueltas al frontend para verificacion
- [ ] Rate limiting en endpoints RAG (costoso)
- [ ] Documento de prueba subido y validado antes de entregar

## Pitfalls

- Chunk size muy grande = menos preciso en retrieval
- Chunk size muy chico = pierde contexto
- Modelo de embedding diferente entre index y query = resultados malos
- No filtrar por usuario/tenant = data leakage entre usuarios
- No limitar contexto enviado al LLM = excede ventana de contexto
- No incluir sources = usuario no puede verificar
- **Qdrant point IDs deben ser UUIDs**: strings personalizadas como `doc_123_chunk_0` generan `400 Bad Request`. Usar `uuid.uuid4()` o enteros unsigned.
- **Formulacion de la pregunta importa**: sinonimos o terminos tecnicos pueden no matchar bien con el embedding del chunk. Probar reformulaciones.
- **Scores de retrieval bajos (< 0.6)**: indican que el embedding no esta encontrando chunks relevantes. Revisar chunk size, overlap y calidad del texto extraido.
