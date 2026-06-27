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

        # 2. Buscar en Qdrant
        search_result = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=5,
        ).points

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

## Patrón Orchestrator + PM Instances (Nelson)

Cuando el chat de JARVIS debe responder con contexto operativo del equipo, priorizar estas fuentes antes de documentos externos:

1. **Task Memory** (`/tasks/history`, `/tasks/pending`)
2. **Timeline del orquestador** (tabla `orchestration_events`)
3. **Subtasks del orquestador** (tabla `task_graph`)
4. **Brainstorming local** (`~/brainstorming/YYYY-MM-DD-*`)
5. **Repos GitHub del equipo** (owners configurables)

### Endpoint recomendado para Resumen PM

Agregar endpoint agregado para el dashboard PM:

- `GET /pm/instances?limit=80`
- Devuelve grupos por tipo (`poc`, `brainstorming`, `github`), conteos y lista unificada ordenada por `updated_at`.

Formato sugerido de salida:

```json
{
  "generated_at": "2026-05-29T23:00:00Z",
  "counts": {"total": 35, "poc": 9, "brainstorming": 17, "github": 9},
  "groups": {"poc": [], "brainstorming": [], "github": []},
  "instances": []
}
```

Esto habilita un **desplegable de instancias en “Resumen PM”** para navegar contexto concreto (PoCs, brainstormings y repos) desde la UI.

### Embeddings fallback para no bloquear PoC

Si falta `OPENAI_API_KEY`, usar embedding local determinístico (hashing trick) para mantener RAG operativo en PoC.

- Mantener la misma dimensión en index/query (ej. 256).
- Normalizar vector para similitud coseno.
- Exponer `embedding_backend` en endpoint de status para observabilidad.

Ver detalle y snippets en `references/orchestrator-rag-pm-instances.md`.

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
    return store.query_points(
        collection="documents",
        query=embedding,
        limit=5,
    ).points
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

## Docker Compose con Qdrant + Ollama (Linux)

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

## Capa de optimización: OptiLLM (opcional)

Para mejorar la calidad de respuestas en queries complejas, se puede
interponer **OptiLLM** entre el backend y Ollama. OptiLLM aplica técnicas
de inferencia-time compute (MCTS, MOA, PlanSearch, etc.) sin cambiar
código del cliente.

```
[RAG FastAPI] --OpenAI API--> [OptiLLM :18000] --OpenAI compatible--> [Ollama :11434/v1]
```

### Cambio mínimo en el backend

```python
# ANTES — directo a Ollama
requests.post("http://ollama:11434/api/generate", json={"model": "llama3.2:3b", ...})

# DESPUÉS — via OptiLLM (drop-in)
from openai import OpenAI
client = OpenAI(base_url="http://optillm:18000/v1", api_key="sk-dummy")
client.chat.completions.create(
    model="moa-llama3.2:3b",  # prefijo = técnica activada
    messages=[{"role": "user", "content": prompt}]
)
```

Ver skill `nelson-optillm` para deploy completo y técnicas disponibles.


**IMPORTANTE — Docker en Linux:** `host.docker.internal` **no funciona por defecto** en Docker Engine para Linux. Usar la IP del bridge `docker0`:
```bash
ip addr show docker0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1
# Tipicamente: 172.17.0.1
```
Y en el docker-compose del backend:
```yaml
environment:
  - OLLAMA_HOST=http://172.17.0.1:11434  # NO host.docker.internal en Linux
```

## PM Portfolio Indexing (Proyectos en Resumen PM)

Cuando el chat/PM debe nutrirse de **proyectos reales** (no solo documentos sueltos), usar este patrón:

1. Un endpoint agregador (`/pm/instances` o equivalente) que devuelva **projects + brainstorming + github** en una lista unificada.
2. Cada item debe incluir campos operativos mínimos:
   - `economic_weight` (score 0-100, bucket, factors)
   - `next_steps` (lista accionable)
   - `updated_at`, `summary`, `type`, `project_status`, `project_kind`
3. Para evitar reindexar todo en cada request:
   - firma local de cambios (`local_signature`) basada en mtimes de proyecto
   - TTL de fuentes remotas (ej. GitHub)
   - caché persistente con `schema_version` para invalidar estructuras viejas
4. Si no hubo cambios: responder desde caché (`from_cache=true`).
5. Si hubo cambios: recalcular counts + payload y persistir.

Esto permite que el selector PM muestre datos reales por proyecto y que JARVIS tenga contexto accionable por selección.

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
   **IMPORTANTE**: Verificar que el PDF tenga texto extractable (no generado con ReportLab Canvas puro, que renderiza texto como vectores). Usar PDFs exportados desde Word/Google Docs o descargados.
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
- [ ] Si el frontend es PM/operativo de Nelson, exponer fuentes como **proyectos** (PoC / Brainstorming / GitHub), no como "instancias"
- [ ] Implementar indexación incremental (cache + signature/mtime) para no reindexar todo en cada request

## Patrón operativo: PM Context Sources (PoC + Brainstorming + GitHub)

Para el dashboard de orquestador de Nelson, el chat y Resumen PM deben consumir un inventario unificado de proyectos de contexto:

1. Escanear fuentes locales (`~/brainstorming`, `~/proyectos`) y agrupar en:
   - `poc`
   - `brainstorming`
2. Obtener repos de GitHub de owners configurables (`PM_GITHUB_OWNERS`).
3. Guardar cache persistente (`pm_instances_cache.json`) con:
   - `local_signature` (hash de nombre+mtime)
   - `github_fetched_ts` (TTL)
   - `counts`, `groups`, `instances/projects`
4. En cada request:
   - Si `local_signature` no cambió y GitHub está fresco: devolver cache (`from_cache=true`, `recalculated=false`).
   - Si cambió algo local o venció TTL: recalcular y persistir (`recalculated=true`).
5. Exponer endpoint de refresh manual (`POST /pm/instances/reindex`) para demos y validación.

Ver referencia: `references/pm-project-sources-incremental-indexing.md`.

- [ ] Exponer estado operacional del RAG (`/chat/rag/status`) y reindex manual (`/chat/rag/reindex`) para diagnósticos rápidos

## Arquitectura PoC Completa (Docker Compose)

Para una demo rapida o PoC que cualquiera pueda levantar:

### Opción A: MinIO (recomendado para PoC estable)

```yaml
services:
  minio:
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: test
      MINIO_ROOT_PASSWORD: test123456
    command: server /data --console-address ":9001"

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: [qdrant-data:/qdrant/storage]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      AWS_ENDPOINT_URL: http://minio:9000
      QDRANT_HOST: http://qdrant:6333
      OLLAMA_HOST: http://172.17.0.1:11434  # Linux: IP del docker0 bridge
    depends_on: [minio, qdrant]  # sin condition: service_healthy porque Qdrant no tiene curl
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports: ["8080:5173"]
    environment:
      VITE_API_URL: http://localhost:8000
    command: npm run dev -- --host 0.0.0.0

volumes:
  qdrant-data:
```

### Opción B: FLoCI (emulador AWS, para testear compatibilidad S3-AWS)

```yaml
services:
  floci:
    image: floci/floci:latest
    ports: ["4566:4566"]
    environment:
      - SERVICES=s3
    volumes:
      - floci-data:/data

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: [qdrant-data:/qdrant/storage]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      AWS_ENDPOINT_URL: http://floci:4566
      AWS_ACCESS_KEY_ID: test
      AWS_SECRET_ACCESS_KEY: test123456
      AWS_REGION: us-east-1
      S3_BUCKET: rag-documents
      QDRANT_HOST: http://qdrant:6333
      OLLAMA_HOST: http://172.17.0.1:11434
    depends_on: [floci, qdrant]
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Opción C: robotocore (emulador AWS completo — recomendado para nuevos proyectos)

```yaml
services:
  robotocore:
    image: jackdanger/robotocore:latest
    ports: ["4566:4566"]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: [qdrant-data:/qdrant/storage]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      AWS_ENDPOINT_URL: http://robotocore:4566
      AWS_ACCESS_KEY_ID: "123456789012"
      AWS_SECRET_ACCESS_KEY: test
      AWS_REGION: us-east-1
      S3_BUCKET: rag-documents
      QDRANT_HOST: http://qdrant:6333
      OLLAMA_HOST: http://172.17.0.1:11434
    depends_on: [robotocore, qdrant]
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Backend Python (boto3) — compatible con todos sin cambios:**
```python
s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),  # http://minio:9000, http://floci:4566 o http://robotocore:4566
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test123456"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    config=Config(signature_version="s3v4"),
)
```

### robotocore vs FLoCI vs MinIO — Cuándo usar cada uno

| Aspecto | robotocore | FLoCI | MinIO |
|---------|------------|-------|-------|
| Qué es | Digital twin AWS (147 servicios) | Emulador AWS (~25 servicios) | S3 real local |
| Persistencia | En memoria + snapshots API | En memoria por defecto | En disco (volumen Docker) |
| Overhead | Medio (Moto-backed) | Mayor (Quarkus native) | Menor (solo S3) |
| Realismo AWS | Muy alto (Moto maintainer) | Alto | Medio (compatible S3) |
| Lambda | Python in-process | Limitado | N/A |
| IAM | Opt-in (`ENFORCE_IAM=1`) | No | No |
| Licencia | MIT | Apache 2.0 | AGPL v3 |
| Ideal para | **Nuevos proyectos AWS**, CI/CD | Legacy / migración futura AWS | Stack local estable |

Para persistencia con FLoCI: agregar `PERSISTENCE=1` como env var y montar volumen en `/app/data`.
Para persistencia con robotocore: usar snapshots API (`POST /_robotocore/state/save`) o preferir MinIO.

### FLoCI-az (Azure equivalent)

FLoCI tiene un **companion para Azure**: [floci-az](https://github.com/floci-io/floci-az) — emulador local de Azure Storage (Blob, Queue, Table) y Azure Functions.

| Aspecto | FLoCI-az | Azurite (oficial) |
|---------|----------|-------------------|
| Servicios | Blob, Queue, Table, Functions | Blob, Queue, Table |
| Puerto | 4577 | 10000-10002 |
| Startup | <100ms | Moderado |
| Functions | ✅ Docker-in-Docker | ❌ |
| Persistencia | memory / hybrid / wal / persistent | File-based |

**Connection string estándar:**
```text
DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=<AZURE_DEVSTORE_DUMMY_KEY>;BlobEndpoint=http://localhost:4577/devstoreaccount1;QueueEndpoint=http://localhost:4577/devstoreaccount1-queue;TableEndpoint=http://localhost:4577/devstoreaccount1-table;
```

**Docker Compose rápido:**
```yaml
services:
  floci-az:
    image: floci/floci-az:latest
    ports:
      - "4577:4577"
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock  # requerido para Azure Functions
```

> Ver `references/floci-az-overview.md` para más detalles.

### Backend FastAPI (RAG completo)

```python
# main.py - endpoints clave
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Guardar en S3 (MinIO)
    s3_client.put_object(Bucket=BUCKET, Key=file.filename, Body=contents)
    # 2. Extraer texto con pdfplumber
    # 3. Chunking con RecursiveCharacterTextSplitter
    # 4. Embeddings con Ollama (nomic-embed-text)
    # 5. Upsert a Qdrant

@app.post("/ask")
async def ask_question(question: dict):
    # 1. Embedding de la pregunta
    # 2. Search en Qdrant (top-5)
    # 3. Construir prompt con contexto
    # 4. Generar con Ollama (llama3.2:3b)
    # 5. Devolver answer + sources
```

### Frontend React (Vite + Tailwind)

Ver `nelson-frontend-stack` para la estructura. UI minima: upload + ask + lista docs.

## Exponer PoC al mundo (demos)

### Opcion A: Cloudflared (quick tunnel, sin cuenta)

Requiere `cloudflared` instalado:
```bash
# Si no esta instalado
curl -L -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb
```

Levantar túneles (uno por servicio). **Importante: usar `--protocol http2` para estabilidad**:
```bash
# Backend (API)
cloudflared tunnel --url http://localhost:8000 --protocol http2

# Frontend (UI)
cloudflared tunnel --url http://localhost:8080 --protocol http2
```

**Automatización con Python (más estable que shell background):**
```python
import subprocess, re, time

proc = subprocess.Popen(
    ['cloudflared', 'tunnel', '--url', 'http://localhost:8000', '--protocol', 'http2'],
    stdout=open('/tmp/cf.log', 'w'),
    stderr=subprocess.STDOUT
)

url = None
for _ in range(30):
    time.sleep(1)
    with open('/tmp/cf.log') as f:
        m = re.search(r'https://[\w-]+\.trycloudflare\.com', f.read())
        if m:
            url = m.group(0)
            break
print(f"Tunnel: {url}")
```

**IMPORTANTE**: Cuando el frontend está expuesto vía Cloudflare, cambiar `VITE_API_URL` en el `docker-compose.yml` del frontend para que apunte a la URL del backend (NO a `localhost`). Luego recrear el contenedor:
```yaml
  frontend:
    environment:
      - VITE_API_URL=https://XXXX-XXXX-XXXX-XXXX.trycloudflare.com
```
```bash
docker compose up -d --no-deps --force-recreate frontend
```

**IMPORTANTE**: Si el frontend usa Vite, agregar `allowedHosts: true` en `vite.config.ts`:
```ts
server: {
  host: '0.0.0.0',
  port: 5173,
  allowedHosts: true,  // <- SIN ESTO cloudflare rechaza con 403
}
```

### Opcion B: Tailscale (recomendado para uso regular)**
- Instalar tailscale en servidor y PC cliente
- Acceder via IP tailscale: `http://100.x.x.x:8080`

**Opcion C: Ngrok (requiere authtoken gratis)**
```bash
ngrok http 8080 --authtoken TU_TOKEN
```

## Pitfalls

- **Caché de portfolio sin versionado de schema**: si agregás campos nuevos (ej. `economic_weight`, `next_steps`) y no invalidás la caché, el frontend puede mostrar “datos vacíos” aunque el backend nuevo esté deployado. Solución: guardar `schema_version` en cache y forzar reindex cuando cambie.
- **Firma local basada solo en mtime de carpeta raíz**: no detecta cambios internos (README/archivos hijos). Solución: usar mtime recursivo acotado (depth 1-2) para construir la `local_signature`.
- **FLoCI no se une automáticamente a la red de Docker Compose**: al reemplazar MinIO por FLoCI en un `docker-compose.yml` existente, el contenedor `floci` a veces no se conecta a la red `default` del proyecto. Esto provoca que el backend no pueda resolver `http://floci:4566` (`Could not resolve host: floci`).
  - **Fix**: hacer un `docker compose down && docker compose up -d` completo (no solo restart) para que Docker Compose vuelva a crear la red y conecte todos los contenedores correctamente.
  - **Verificación**: `docker network inspect <proyecto>_default` debe listar `floci-1` con una IP asignada.
- **Dos stacks Docker Compose en paralelo requieren directorios separados o nombres de proyecto explícitos**: si se quiere correr simultáneamente una versión FLoCI y una versión MinIO del mismo proyecto (por ejemplo, para comparar), no basta con usar `docker compose -f docker-compose.minio.yml up -d` desde el mismo directorio. Docker Compose usa el nombre del directorio como nombre de proyecto, por lo que ambas versiones comparten la misma red y se pisan mutuamente.
  - **Síntoma**: Al levantar la segunda versión, Docker Compose muestra `Recreating` en lugar de `Creating` para los contenedores existentes, y los contenedores de la primera versión desaparecen.
  - **Fix 1 (recomendado)**: Crear un directorio separado para cada versión (ej: `rag-poc/` y `rag-poc-minio/`), copiar el código `backend/` y `frontend/` a ambos, y usar `docker compose up -d` desde cada directorio. Docker Compose asignará nombres de proyecto distintos automáticamente (`rag-poc_default` vs `rag-poc-minio_default`).
  - **Fix 2**: Usar `-p` para forzar nombre de proyecto:
    ```bash
    docker compose -p rag-floci -f docker-compose.yml up -d
    docker compose -p rag-minio -f docker-compose.minio.yml up -d
    ```
  - **Fix 3**: Mapear puertos distintos en cada stack para evitar colisiones (ej: backend FLoCI en 8000, backend MinIO en 8001; frontend FLoCI en 8080, frontend MinIO en 8081).
- **Cloudflared con QUIC es inestable con múltiples túneles**: cuando se levantan 2+ túneles `cloudflared` simultáneos con el protocolo QUIC por defecto, aparecen errores `context canceled` y los túneles no responden desde internet (Error 1033).
  - **Fix**: forzar protocolo HTTP/2 que es más estable:
    ```bash
    cloudflared tunnel --url http://localhost:8000 --protocol http2
    ```
  - **Fix alternativo** (si el entorno lo permite): levantar cada túnel en un proceso background independiente con `subprocess.Popen` desde Python, capturando el log a archivo y extrayendo la URL con regex.
- **`docker compose up -d` detectado como proceso largo en algunos entornos**: ciertos entornos de ejecución rechazan `docker compose up -d` en foreground porque perciben un servidor de larga duración. Usar background mode o ejecutar `docker compose up -d` desde una shell interactiva.
- **Qdrant healthcheck falla (imagen sin curl/wget)**: La imagen `qdrant/qdrant:latest` no incluye `curl` ni `wget`. El healthcheck `curl -f http://localhost:6333/healthz` da `unhealthy`.
  - **Fix rápido**: Eliminar `condition: service_healthy` de los `depends_on` y usar solo `depends_on: [qdrant]` sin condiciones. Esto es lo más simple y confiable.
  - **Fix alternativo** (si se quiere mantener healthcheck): reemplazar el test por un shell con fallback a Python:
    ```yaml
    healthcheck:
      test: ["CMD", "sh", "-c", "wget -qO- http://localhost:6333/healthz || python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:6333/healthz')\""]
      interval: 5s
      timeout: 5s
      retries: 10
    ```
- **Dependencia `langchain-text-splitters` faltante**: En versiones modernas de LangChain, `from langchain_text_splitters import RecursiveCharacterTextSplitter` requiere instalar `langchain-text-splitters` como dependencia separada. Sin ella el backend crashea con `ModuleNotFoundError: No module named 'langchain.text_splitter'`.
- **Qdrant `CollectionInfo` no tiene `vectors_count`**: en versiones nuevas del cliente Qdrant, `get_collection()` devuelve un objeto sin atributo `vectors_count`. Usar solo `points_count`.
  ```python
  info = qdrant.get_collection("documents")
  return {"points_count": info.points_count}  # info.vectors_count NO existe
  ```
- **PDFs generados con ReportLab no tienen texto extraíble**: ReportLab Canvas renderiza texto como paths vectoriales, no como objetos de texto seleccionables. `pdfplumber` (y cualquier extractor basado en objetos de texto) extrae texto vacío (`""` o `None`). El documento se sube a S3, pero no genera chunks en Qdrant porque el pipeline encuentra texto vacío.
  - **Síntoma**: El PDF se sube exitosamente (`"message":"Archivo subido y procesado correctamente"`), pero `GET /stats` muestra `points_count` sin incrementar, y preguntas sobre ese documento responden "No encontré información".
  - **Fix**: Para testing de RAG, usar PDFs reales exportados desde Word, Google Docs, o descargados de internet. Nunca usar ReportLab Canvas para generar PDFs de prueba de RAG. Verificar extractabilidad antes de subir:
    ```bash
    python3 -c "import pdfplumber; pdf = pdfplumber.open('test.pdf'); print(len(pdf.pages[0].extract_text() or ''))"
    # Si devuelve 0, el PDF no es text-extractable
    ```
  - **Alternativa para generar PDFs testeables**: usar `wkhtmltopdf` o exportar desde un procesador de texto real.
- **Vite `.env` no se aplica en contenedor Docker con bind mount**: al crear un archivo `.env` en el host DESPUÉS de que el contenedor ya esté corriendo (por ejemplo, para actualizar `VITE_API_URL` después de obtener una URL de Cloudflare), el bind mount de Docker sí lo refleja en el contenedor, pero **Vite solo lee `.env` al arranque** — no hace hot-reload de variables de entorno. Un `docker restart` del contenedor tampoco basta si la variable fue cambiada en `docker-compose.yml` (Docker conserva las vars del momento de creación).
  - **Síntoma**: El frontend sigue apuntando a `localhost:8000` aunque el archivo `.env` dentro del contenedor muestre la URL pública.
  - **Fix**: `docker compose up -d --no-deps --force-recreate frontend` para recrear el contenedor con las nuevas env vars. Alternativamente, asegurar que `.env` exista en el host ANTES del primer `docker compose up`.
- **Frontend apunta a `localhost` cuando el stack se expone por Cloudflare — el navegador del usuario busca `localhost` en SU máquina**: cuando se exponen servicios con `cloudflared` (o ngrok/tailscale), es fácil olvidar que el `VITE_API_URL` del frontend debe apuntar a la **URL pública del backend**, no a `http://localhost:8000`.
  - **Síntoma**: El usuario abre la UI pública (ej: `https://XXXX.trycloudflare.com`) y ve "No hay documentos subidos todavía" o errores de red, porque el frontend hace `fetch('http://localhost:8000/documents')` desde el navegador del usuario, donde no corre nada en ese puerto.
  - **Fix**: Después de obtener la URL del backend con `cloudflared`, actualizar el `docker-compose.yml` del frontend ANTES de recrear el contenedor:
    ```yaml
    frontend:
      environment:
        - VITE_API_URL=https://BACKEND-XXXX.trycloudflare.com
    ```
    ```bash
    docker compose up -d --no-deps --force-recreate frontend
    ```
  - **Verificación**: desde el navegador (F12 → Network), confirmar que las llamadas a `/documents`, `/stats` y `/ask` van a la URL pública del backend, no a `localhost`.
- **Dos stacks Docker Compose en paralelo con archivos `-f` diferentes pero mismo directorio base**: cuando se quiere correr simultáneamente una versión FLoCI y una versión MinIO (por ejemplo para comparar), ejecutar `docker compose -f docker-compose.minio.yml up -d` desde el mismo directorio base que el `docker-compose.yml` original causa que Docker Compose reutilice el nombre de proyecto (derivado del directorio). Los contenedores del stack anterior se marcan como "orphan" y el segundo stack reemplaza/recreate los del primero.
  - **Síntoma**: `docker ps` muestra contenedores mezclados (`rag-poc-backend-1` y `rag-poc-minio-backend-1` no coexisten; uno reemplaza al otro). Los puertos colisionan o desaparecen.
  - **Fix 1 (recomendado)**: Copiar el proyecto completo a un directorio separado (ej: `cp -r rag-poc/ rag-poc-minio/`) y correr `docker compose up -d` desde cada directorio. Docker Compose asigna nombres de proyecto distintos automáticamente.
  - **Fix 2**: Usar `-p` con nombres de proyecto explícitos:
    ```bash
    docker compose -p rag-floci -f docker-compose.yml up -d
    docker compose -p rag-minio -f docker-compose.minio.yml up -d
    ```
  - **Fix 3**: Mapear puertos distintos en cada stack (backend FLoCI 8000/frontend 8080, backend MinIO 8001/frontend 8081) para evitar colisiones externas, aunque el principal problema es la red Docker interna compartida.
- **No devolver fuentes al frontend en respuestas de chat**: si el backend RAG recupera contexto pero no envía `sources` junto con el resultado final (ej. en SSE `done`), el usuario no puede auditar evidencia y pierde confianza operacional.
  - **Fix**: incluir `sources` + bandera de contexto (`rag_enabled`) en el payload final del stream, y renderizar en UI una sección compacta “Fuentes RAG” (source + score).
- **Falta de credenciales no debe bloquear todo el chat**: en entornos PoC suele faltar `OPENAI_API_KEY`. Si el pipeline depende 100% de embeddings remotos, el chat queda sin RAG aunque haya datos locales disponibles.
  - **Fix**: implementar fallback local determinístico (ej. hashing embeddings) y reportarlo en `GET /chat/rag/status` como `embedding_backend=hashing-local`.
- **Qdrant point IDs deben ser UUIDs**: strings personalizadas como `doc_123_chunk_0` generan `400 Bad Request`. Usar `uuid.uuid4()` o enteros unsigned.
- **Formulacion de la pregunta importa**: sinonimos o terminos tecnicos pueden no matchar bien con el embedding del chunk. Probar reformulaciones.
- **Scores de retrieval bajos (< 0.6)**: indican que el embedding no esta encontrando chunks relevantes. Revisar chunk size, overlap y calidad del texto extraido.
- **Docker build + up en foreground**: `docker compose up -d --build` puede ser detectado como "long-lived process" por algunos entornos. Ejecutar en background o permitir background.
- **Ollama desde contenedor Docker en Linux**: `host.docker.internal` **no funciona** en Docker Engine para Linux. Obtener la IP del bridge `docker0`:
  ```bash
  ip addr show docker0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1
  # Tipicamente: 172.17.0.1
  ```
  Y usar esa IP en `OLLAMA_HOST=http://172.17.0.1:11434`.
- **Ollama debe escuchar en todas las interfaces**: si Ollama solo escucha en `127.0.0.1`, los contenedores Docker no podran conectarse. Verificar con `ss -tlnp | grep 11434` que la columna `Local Address` diga `*:11434` o `0.0.0.0:11434`.
- **Qdrant client API cambió: `search()` → `query_points()`**: en qdrant-client >= 1.13, el método `qdrant.search()` fue reemplazado por `qdrant.query_points()`. El backend crashea con `'QdrantClient' object has no attribute 'search'`.
  ```python
  # Antes (ya no funciona)
  results = qdrant.search(collection_name=COL, query_vector=embedding, limit=5)
  # Ahora
  results = qdrant.query_points(collection_name=COL, query=embedding, limit=5).points
  ```
- **Env vars de Docker no se actualizan con `restart`**: cambiar una variable en `docker-compose.yml` y hacer `docker compose restart servicio` NO aplica el cambio. El contenedor mantiene las variables del momento en que se creó. **Fix**: usar `--force-recreate`:
  ```bash
  docker compose up -d --no-deps --force-recreate frontend
  ```
  O bien hacer `docker compose down && docker compose up -d`.
- **`docker compose up --build -d` detectado como proceso largo**: algunos entornos rechazan `docker compose up --build -d` en foreground porque se percibe como proceso de larga duración. Ejecutar en background o con el flag correspondiente del entorno.

## Retomar proyecto RAG existente

Cuando se retoma un proyecto RAG despues de dias/semanas, seguir este checklist antes de hacer build:

1. **Encontrar el proyecto**: buscar en `~/brainstorming/YYYY-MM-DD-*rag*/` o preguntar al usuario la ubicacion.
2. **Revisar estructura**: confirmar `docker-compose.yml`, `backend/`, `frontend/` estan presentes.
3. **Verificar Ollama**: asegurarse que este corriendo y escuche en red.
   ```bash
   curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"
   ss -tlnp | grep 11434
   ```
4. **Verificar modelos requeridos**: confirmar `nomic-embed-text` y el LLM (ej: `llama3.2:3b`) esten instalados.
5. **Revisar estado Docker**: verificar que no haya contenedores antiguos corriendo que colisionen puertos.
6. **Hacer build y levantar**:
   ```bash
   docker compose up --build -d
   ```
7. **Verificar health endpoints**: `GET /health`, `GET /stats`.
8. **Probar flujo completo**: subir PDF -> hacer pregunta -> ver respuesta + fuentes.

## Referencias

- `references/pm-portfolio-indexing-pattern.md` — Patrón de indexación incremental de proyectos para Resumen PM: cache con schema_version, detección de cambios locales y campos `economic_weight` + `next_steps`.
- `references/retomar-poc-rag-mayo-2026.md` — Flujo concreto de retomada de un proyecto RAG existente, verificacion de Ollama y modelos
- `references/rag-poc-etapa1-etapa2.md` — Detalles de la PoC con etapas 1 y 2 (FastAPI + React + MinIO + Qdrant)
- `references/rag-query-tips.md` — Tips para formular queries efectivas
- `references/meta-orchestrator-chat-rag-qdrant-may-2026.md` — Integración concreta del chat del meta-orchestrator con Qdrant, endpoints `/chat/rag/*`, SSE con `sources`, y fallback `hashing-local` cuando no hay `OPENAI_API_KEY`
- `references/cloudflared-expose-services.md` — Patron para exponer servicios locales via Cloudflared quick tunnel (demos, acceso remoto temporal)
- `references/session-rag-floci-minio-parallel-mayo-2026.md` — Sesion completa: despliegue en paralelo de FLoCI vs MinIO, problema de frontend apuntando a localhost, confusion de directorios Docker Compose, URLs finales y verificacion
- `references/parallel-backend-comparison-mayo-2026.md` — Deploy triple (FLoCI-AWS + MinIO + FLoCI-Azure) en paralelo con demo package para Pablo. Tabla comparativa, URLs publicas, flujo end-to-end, y lecciones para futuras demos comparativas
- `references/agentscope-architecture-reference.md` — AgentScope 2.0 (Alibaba, 26k stars): análisis comparativo vs LangGraph/CrewAI, patrones de Agent Service multi-tenant, Message Hub y Event Stream relevantes para el meta-orquestador de Nelson.
- `templates/docker-compose.minio.yml` — Template Docker Compose para stack RAG con MinIO (puertos alternativos, persistente en disco)
- `scripts/verify-rag-deployment.sh` — Script de verificacion rapida para detectar frontend apuntando a localhost, CORS fallido, o backend sin documentos
- `scripts/rag-health-monitor.sh` — Monitoreo de salud de RAGs en paralelo. Cada 5 min revisa si los backends responden, reinicia automaticamente si estan caidos, y envia alerta si no se recuperan.
- `scripts/sync-skills-to-repo.sh` — Script de sincronizacion de skills locales al repo. Incluye verificacion de que todas las skills esten listadas (usa `comm -23` para detectar faltantes)
- `scripts/sync-to-repo.sh` — Alias corto del script de sincronizacion
