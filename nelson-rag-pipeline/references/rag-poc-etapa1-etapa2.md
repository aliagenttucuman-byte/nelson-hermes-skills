# RAG PoC - Estructura completa (Etapa 1 + 2)

Esta referencia documenta la PoC construida el 2026-05-13 para el equipo Nelson.
Arquitectura: FastAPI backend + React frontend + MinIO (S3) + Qdrant + Ollama.

## Estructura de carpetas

```
rag-poc/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── index.css
        └── App.tsx
```

## docker-compose.yml

```yaml
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=test
      - MINIO_ROOT_PASSWORD=test123456
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 10

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - AWS_ENDPOINT_URL=http://minio:9000
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test123456
      - AWS_REGION=us-east-1
      - S3_BUCKET=rag-documents
      - QDRANT_HOST=http://qdrant:6333
      - OLLAMA_HOST=http://host.docker.internal:11434
    depends_on:
      minio:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    volumes:
      - ./backend:/app
    extra_hosts:
      - "host.docker.internal:host-gateway"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "8080:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0

volumes:
  minio-data:
  qdrant-data:
```

## Backend (main.py)

```python
import os
import io
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.config import Config
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import requests

app = FastAPI(title="RAG PoC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 (MinIO)
s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_ENDPOINT_URL", "http://localhost:9000"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test123456"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    config=Config(signature_version="s3v4"),
)
BUCKET = os.getenv("S3_BUCKET", "rag-documents")

# Qdrant
qdrant = QdrantClient(os.getenv("QDRANT_HOST", "http://localhost:6333"))
COLLECTION = "rag_documents"

# Ollama
OLLAMA = os.getenv("OLLAMA_HOST", "http://localhost:11434")
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA)

# Chunking
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)


def init():
    try: s3_client.head_bucket(Bucket=BUCKET)
    except: s3_client.create_bucket(Bucket=BUCKET)
    try: qdrant.get_collection(COLLECTION)
    except: qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )

@app.on_event("startup")
async def startup(): init()

@app.get("/health") async def health(): return {"status": "ok"}

@app.get("/documents")
async def list_docs():
    r = s3_client.list_objects_v2(Bucket=BUCKET)
    items = r.get("Contents", [])
    return {"documents": [{"key": o["Key"], "size": o["Size"],
             "last_modified": o["LastModified"].isoformat()} for o in items]}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo PDF")
    contents = await file.read()
    s3_client.put_object(Bucket=BUCKET, Key=file.filename, Body=contents,
                         ContentType="application/pdf")
    await process_pdf(file.filename, contents)
    return {"message": "Subido y procesado", "filename": file.filename}

async def process_pdf(filename: str, contents: bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t: text += t + "\n"
    if not text.strip(): return
    chunks = splitter.split_text(text)
    points = []
    for i, chunk in enumerate(chunks):
        vec = embeddings.embed_query(chunk)
        points.append(PointStruct(
            id=str(uuid.uuid4()), vector=vec,
            payload={"text": chunk, "document": filename, "chunk_index": i}
        ))
    if points: qdrant.upsert(collection_name=COLLECTION, points=points)

@app.post("/ask")
async def ask(q: dict):
    query = q.get("question", "").strip()
    if not query: raise HTTPException(400, "Pregunta vacia")
    q_emb = embeddings.embed_query(query)
    hits = qdrant.search(collection_name=COLLECTION, query_vector=q_emb, limit=5)
    if not hits:
        return {"answer": "No encontre info relevante.", "sources": []}
    ctx = "\n\n".join([f"[{h.payload['document']}]\n{h.payload['text']}" for h in hits])
    prompt = f"""Responde usando UNICAMENTE la info del contexto.
CONTEXTO:\n{ctx}\n\nPREGUNTA: {query}\n\nRESPUESTA:"""
    r = requests.post(f"{OLLAMA}/api/generate",
                      json={"model": "llama3.2:3b", "prompt": prompt,
                            "stream": False, "options": {"temperature": 0.3}},
                      timeout=60)
    answer = r.json().get("response", "Sin respuesta").strip()
    sources = [{"document": h.payload["document"], "score": h.score,
                "text": h.payload["text"][:200]+"..."} for h in hits]
    return {"answer": answer, "sources": sources}

@app.get("/stats")
async def stats():
    info = qdrant.get_collection(COLLECTION)
    return {"collection": COLLECTION, "points_count": info.points_count,
            "vectors_count": info.vectors_count}
```

## Backend requirements.txt

```
fastapi
uvicorn[standard]
python-multipart
boto3
pdfplumber
langchain
langchain-community
langchain-ollama
qdrant-client
requests
```

## Frontend vite.config.ts

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,  // <- IMPORTANTE para cloudflared/ngrok
  },
})
```

## Comandos

```bash
# Build e iniciar todo
cd rag-poc
docker compose up -d --build

# Verificar salud
curl http://localhost:8000/health
curl http://localhost:8000/documents
curl http://localhost:8000/stats

# Exponer via cloudflared (en servidor)
screen -dmS tunnel bash -c 'cloudflared tunnel --url http://localhost:8080'
sleep 8
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/tunnel.log
```

## Notas

- `extra_hosts` en backend es necesario para que Docker vea Ollama en el host.
- MinIO console: http://localhost:9001 (test / test123456)
- Qdrant dashboard: http://localhost:6333/dashboard
