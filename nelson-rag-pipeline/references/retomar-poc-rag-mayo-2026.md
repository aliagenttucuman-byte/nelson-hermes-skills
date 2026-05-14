# Retomada de PoC RAG - Sesion 14 Mayo 2026

## Contexto
Nelson y Luis habian armado un PoC de RAG con:
- FastAPI + React + MinIO (S3 local) + Qdrant + Ollama
- Exposicion publica via Cloudflared tunnel
- Embeddings: `nomic-embed-text` via Ollama
- LLM: `llama3.2:3b` via Ollama

El proyecto estaba en: `/home/server/brainstorming/2026-05-13-rag-poc/`

## Estado al retomar
- Docker containers estaban abajo (`docker compose ps` vacio)
- Codigo completo (Etapa 1 y 2) ya estaba escrito
- Ollama corria en host Linux escuchando en `*:11434`
- Modelos disponibles: `nomic-embed-text:latest`, `llama3.2:3b`, `qwen2.5:3b`, etc.

## Flujo de retomada ejecutado

### 1. Encontrar proyecto
```bash
find /home/server -maxdepth 3 -type d -name "*rag*" -o -name "*RAG*"
```
Resultado: `/home/server/brainstorming/2026-05-13-rag-poc/`

### 2. Verificar estructura
```bash
ls /home/server/brainstorming/2026-05-13-rag-poc/
# docker-compose.yml, backend/, frontend/
```

### 3. Verificar Ollama
```bash
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"
# Verificar que nomic-embed-text y llama3.2:3b esten presentes

ss -tlnp | grep 11434
# Debe decir *:11434 (no 127.0.0.1:11434)
```

### 4. Docker build
```bash
cd /home/server/brainstorming/2026-05-13-rag-poc && docker compose up --build -d
```
Nota: en este entorno se detecto como proceso largo, se ejecuto en background.

## Arquitectura del proyecto

### docker-compose.yml
- minio: puertos 9000, 9001
- qdrant: puertos 6333, 6334
- backend: puerto 8000, depende de minio y qdrant
- frontend: puerto 8080 (mapeado a 5173 de Vite)

### Variables clave del backend
- AWS_ENDPOINT_URL=http://minio:9000
- QDRANT_HOST=http://qdrant:6333
- OLLAMA_HOST=http://host.docker.internal:11434

### Endpoints del backend
- `GET /health` - healthcheck
- `GET /documents` - listar documentos en S3
- `POST /upload` - subir PDF, extraer texto, chunking, embeddings, indexar en Qdrant
- `POST /ask` - hacer pregunta, buscar en Qdrant, generar respuesta con LLM
- `GET /stats` - estadisticas de la coleccion Qdrant

### Chunking
- RecursiveCharacterTextSplitter
- chunk_size=500, chunk_overlap=50
- Modelo embedding: nomic-embed-text (768 dimensiones)

### Prompt para respuesta
```
Basandote UNICAMENTE en la siguiente informacion de los documentos, responde la pregunta de forma clara y concisa.

INFORMACION DE LOS DOCUMENTOS:
{context}

PREGUNTA: {query}

RESPUESTA:
```

## Lecciones de esta sesion

1. Siempre verificar que Ollama escuche en `*:11434` antes de hacer Docker build. Si escucha en `127.0.0.1:11434` solo, los contenedores no pueden conectarse.
2. Verificar modelos disponibles (`nomic-embed-text` y el LLM) antes de build para evitar errores en runtime.
3. El flujo de retomar un proyecto RAG es: encontrar -> revisar estructura -> verificar Ollama/modelos -> revisar estado Docker -> build -> testear.
4. El proyecto se guarda en `~/brainstorming/YYYY-MM-DD-nombre-proyecto/` segun convencion establecida.
