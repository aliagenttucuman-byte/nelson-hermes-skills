---
name: nelson-chat-with-documents
title: Chat con Documentos - RAG completo funcional
description: Sistema completo para cargar documentos PDF/Word/TXT y hacer preguntas sobre su contenido usando RAG. Backend FastAPI, Qdrant, Ollama local. Basado en implementacion real probada en produccion.
skill: nelson-chat-with-documents
author: equipo-nelson
version: 1.0.0
keywords: [rag, chat, documents, pdf, qdrant, ollama, fastapi, ingestion]
dependencies: [nelson-rag-pipeline, nelson-document-processing, nelson-embeddings, nelson-vector-databases, nelson-llm-generation]
---

# Chat con Documentos - Equipo Nelson

> Sistema RAG completo y probado: subís documentos, hacés preguntas, recibís respuestas con fuentes.

## Arquitectura

```
Usuario
  |
  v
[Frontend React] -----> [FastAPI Backend]
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
   [Document]         [Embedding]         [RAG Query]
   [Processor]        [Service]           [Service]
        |                   |                   |
        v                   v                   v
   [Chunks] ---------> [Qdrant] <--------- [Query Embedding]
   [de texto]          [Vector DB]         [Retrieval]
                            |
                            v
                      [LLM Ollama]
                            |
                            v
                      [Respuesta + Sources]
```

## Stack

| Componente | Tecnologia |
|------------|-----------|
| Backend | FastAPI + Python 3.12 |
| Vector DB | Qdrant |
| Embeddings | Ollama + nomic-embed-text (768 dims) |
| LLM Chat | Ollama + llama3.2:3b / gemma3:4b |
| Documentos | pdfplumber, python-docx, beautifulsoup4 |
| Frontend | React 19 + Vite + Tailwind |
| Infra | Docker Compose |

## Servicios Backend

### 1. DocumentProcessor (`app/services/document_processor.py`)

Procesa PDFs, Word, TXT y Markdown. Extrae texto limpio y estructurado.

```python
from app.services.document_processor import DocumentProcessor

processor = DocumentProcessor()
chunks = processor.process(
    file_bytes=file_bytes,
    filename="manual.pdf",
    mime_type="application/pdf",
)
# Devuelve list[DocumentChunk] con text, page, metadata
```

**Soportado:**
- `application/pdf` → pdfplumber (mejor que PyPDF2 para tablas)
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` → python-docx
- `text/plain` → UTF-8 decode
- `text/markdown` → markdown → BeautifulSoup

**Limpieza de texto:**
- Elimina espacios múltiples
- Elimina líneas vacías redundantes
- Mantiene saltos de párrafo

### 2. EmbeddingService (`app/services/embeddings.py`)

Genera embeddings con Ollama local usando `nomic-embed-text`.

```python
from app.services.embeddings import EmbeddingService

embedder = EmbeddingService()
vector = embedder.embed_single("texto")
vectors = embedder.embed_batch(["texto1", "texto2", ...])
```

**Configuración:**
- Modelo: `nomic-embed-text`
- Dimensión: 768
- Mismo modelo para ingestion y query

### 3. VectorStore (`app/services/vector_store.py`)

Conexión a Qdrant. Crea colección automáticamente si no existe.

```python
from app.services.vector_store import VectorStore

store = VectorStore()
store.upsert(vectors=embeddings, payloads=payloads, ids=ids)
results = store.search(query_vector=embedding, limit=5)
```

**IMPORTANTE - IDs en Qdrant:**
Qdrant requiere IDs como **UUID o unsigned integer**. NO acepta strings personalizadas como `doc_manual_chunk_0`.

```python
import uuid
ids = [str(uuid.uuid4()) for _ in chunks]  # Correcto
ids = [f"{doc_id}_chunk_{i}"]              # ERROR: 400 Bad Request
```

**Configuración de colección:**
- Nombre: `documents`
- Vector size: 768
- Distance: Cosine

### 4. IngestionPipeline (`app/services/ingestion.py`)

Pipeline completo: chunking → embeddings → indexación.

```python
from app.services.ingestion import IngestionPipeline

pipeline = IngestionPipeline()
result = pipeline.ingest_document(
    doc_id="doc_manual_rrhh",
    text=texto_completo,
    metadata={"filename": "manual.pdf", "user_id": "123"},
)
# Returns: {"chunks": 37, "doc_id": "doc_manual_rrhh"}
```

**Chunking:**
- Tamaño: 500 caracteres
- Overlap: 50 caracteres (10%)
- Corte inteligente: busca fin de oración para no cortar a mitad

### 5. RAGService (`app/services/rag.py`)

Orquesta la consulta completa.

```python
from app.services.rag import RAGService

rag = RAGService()
response = rag.ask(
    question="¿Cuántos días de vacaciones corresponden?",
    filters=None,
    top_k=5,
)
# Returns: {"answer": "...", "sources": [...]}
```

**Prompt template:**
```
Sos un asistente útil. Respondé la pregunta usando ÚNICAMENTE
la información proporcionada en el contexto.
Si la respuesta no está en el contexto, decí "No tengo suficiente
información para responder."

CONTEXTO:
{context}

PREGUNTA: {question}

RESPUESTA:
```

## Endpoints

### POST `/api/v1/documents/upload`

Sube un documento, lo procesa e indexa.

**Request:** `multipart/form-data` con campo `file`

**Response:**
```json
{
  "doc_id": "doc_manual.pdf",
  "filename": "manual.pdf",
  "chunks_processed": 37,
  "message": "Documento procesado e indexado correctamente"
}
```

**Límites:**
- Max 50MB por archivo
- Mime types validados

### POST `/api/v1/rag/ask`

Hace una pregunta sobre los documentos indexados.

**Request:**
```json
{
  "question": "¿Cuántos días de vacaciones?",
  "filters": null,
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "Según el Documento 1, para empleados con entre 5 y 10 años...",
  "sources": [
    {"id": "uuid", "score": 0.68, "doc_id": "doc_manual.pdf", "source": null}
  ]
}
```

## Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://..."
      - QDRANT_HOST=qdrant
      - LLM_PROVIDER=ollama
      - LLM_MODEL=llama3.2:3b
    depends_on: [db, redis, qdrant]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes:
      - qdrant_storage:/qdrant/storage

  # ... db, redis, frontend
```

## Dependencias Python

Agregar a `pyproject.toml`:
```toml
dependencies = [
    # ... existing deps
    "pdfplumber>=0.11",
    "python-docx>=1.1",
    "markdown>=3.7",
    "beautifulsoup4>=4.12",
]
```

## Testing y Validación

### Prueba 1: Carga de documento
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@documento.pdf"
```
Esperado: `"chunks_processed": N` donde N > 0

### Prueba 2: Consulta simple
```bash
curl -X POST http://localhost:8000/api/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué dice el manual sobre X?", "top_k": 5}'
```
Esperado: Respuesta concreta + array de sources

### Prueba 3: Consulta específica
Formular preguntas específicas que requieran razonamiento sobre los datos.

## Lecciones Aprendidas (Pitfalls)

### 1. Formulación de la pregunta importa MUCHO

| Pregunta | Resultado |
|----------|-----------|
| "¿Cuántos días de licencia por paternidad?" | ❌ "No tengo información" |
| "¿Cuántos días de licencia le corresponden a un padre por el nacimiento de un hijo?" | ✅ "30 días corridos" |

**Por qué:** El embedding de la query debe ser semánticamente similar al de los chunks. Palabras clave distintas pueden mapear a espacios vectoriales diferentes.

**Solución:** Implementar Query Expansion o reformulación automática.

### 2. IDs de Qdrant
Qdrant solo acepta UUIDs o integers. Strings como `doc_id_chunk_0` devuelven 400 Bad Request.

### 3. Chunk size vs precisión
- Chunk muy grande (>1000): menos preciso en retrieval, más contexto
- Chunk muy chico (<200): pierde contexto, más ruido
- **Sweet spot:** 500 chars con 10% overlap

### 4. Mismo modelo de embedding
Usar exactamente el mismo modelo (`nomic-embed-text`) para indexar y para consultar. Cambiar de modelo invalida toda la base vectorial.

### 5. Top-k adecuado
- `top_k=3`: Rápido pero puede omitir contexto relevante
- `top_k=5`: Balance recomendado
- `top_k=8+`: Más completo pero puede incluir ruido y exceder ventana de contexto del LLM

## Recomendaciones de LLM según hardware

Con 4GB VRAM (GTX 1650):

| Modelo | Tamaño | Velocidad | Calidad |
|--------|--------|-----------|---------|
| gemma3:1b | 800MB | ~2.7s | ⭐⭐⭐ Básica |
| llama3.2:3b | 2GB | ~5s | ⭐⭐⭐⭐ Buena |
| qwen2.5:3b | 1.9GB | ~6s | ⭐⭐⭐⭐ Buena |
| gemma3:4b | 3.3GB | ~6.3s | ⭐⭐⭐⭐ Buena |
| llama3.1:8b | 4.9GB | ~2s* | ⭐⭐⭐⭐⭐ Excelente |

*llama3.1:8b usa ~43% CPU + 57% GPU, respuesta más lenta en tokens/seg pero comparable.

**Recomendación:** llama3.2:3b para equilibrio velocidad/calidad. gemma3:1b si se prioriza velocidad extrema.

## Checklist de implementación

- [ ] `pdfplumber` y dependencias en `pyproject.toml`
- [ ] Servicios creados: DocumentProcessor, EmbeddingService, VectorStore, IngestionPipeline, RAGService
- [ ] Endpoints: `/documents/upload` y `/rag/ask`
- [ ] Qdrant configurado con collection `documents`, 768 dims, Cosine
- [ ] IDs de chunks como UUID
- [ ] Docker Compose con Qdrant levantado
- [ ] Ollama corriendo con `nomic-embed-text` y modelo de chat
- [ ] Prueba con PDF real exitosa
- [ ] Respuestas incluyen `sources` para verificación

## Flujo completo de uso

1. Usuario sube PDF vía frontend o curl → `/documents/upload`
2. Backend procesa PDF → extrae texto → chunking → embeddings → Qdrant
3. Usuario hace pregunta → `/rag/ask`
4. Backend: embedding de pregunta → retrieval en Qdrant → construye prompt → LLM genera respuesta → devuelve answer + sources
5. Frontend muestra respuesta con citas a documentos fuente
