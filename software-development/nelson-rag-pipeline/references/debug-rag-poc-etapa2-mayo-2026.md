# Debug Session: RAG PoC Etapa 2 — Mayo 2026

## Situación
Retomando proyecto RAG PoC existente (`~/brainstorming/2026-05-13-rag-poc/`). Código completo (FastAPI + React + MinIO + Qdrant + Ollama) pero nunca se había hecho el build de Docker con la Etapa 2.

## Problemas encontrados y fixes

### 1. Qdrant healthcheck falla: `curl` no disponible en la imagen
**Síntoma**: `docker compose up --build -d` falla con:
```
dependency failed to start: container 2026-05-13-rag-poc-qdrant-1 is unhealthy
```
**Causa**: La imagen `qdrant/qdrant:latest` no incluye `curl` ni `wget`. El healthcheck usa `curl -f http://localhost:6333/healthz`.
**Fix**: Simplificar `depends_on` eliminando `condition: service_healthy`:
```yaml
depends_on:
  - minio
  - qdrant
```
En vez de:
```yaml
depends_on:
  minio:
    condition: service_healthy
  qdrant:
    condition: service_healthy
```

### 2. `ModuleNotFoundError: No module named 'langchain.text_splitter'`
**Síntoma**: Backend crashea en startup.
**Causa**: En versiones nuevas de LangChain, `RecursiveCharacterTextSplitter` requiere el paquete `langchain-text-splitters` como dependencia separada.
**Fix**:
```txt
# requirements.txt
langchain-text-splitters
```
Y cambiar el import:
```python
# Antes (ya no funciona)
from langchain.text_splitter import RecursiveCharacterTextSplitter
# Ahora
from langchain_text_splitters import RecursiveCharacterTextSplitter
```

### 3. Qdrant client API cambió: `search()` → `query_points()`
**Síntoma**: Endpoint `/ask` devuelve error 500:
```json
{"detail": "'QdrantClient' object has no attribute 'search'"}
```
**Causa**: qdrant-client >= 1.13 deprecó `search()` en favor de `query_points()`.
**Fix**:
```python
# Antes
results = qdrant.search(
    collection_name=COLLECTION_NAME,
    query_vector=query_embedding,
    limit=5,
)
# Ahora
results = qdrant.query_points(
    collection_name=COLLECTION_NAME,
    query=query_embedding,
    limit=5,
).points
```

### 4. `host.docker.internal` no funciona en Linux
**Síntoma**: Backend no puede conectar a Ollama desde el contenedor.
**Causa**: `host.docker.internal` solo funciona por defecto en Docker Desktop (Mac/Windows). En Docker Engine Linux no existe.
**Fix**: Usar la IP del bridge `docker0`:
```bash
ip addr show docker0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1
# Típicamente: 172.17.0.1
```
En `docker-compose.yml`:
```yaml
environment:
  - OLLAMA_HOST=http://172.17.0.1:11434
```

### 5. `CollectionInfo` no tiene atributo `vectors_count`
**Síntoma**: Endpoint `/stats` devuelve error 500.
**Fix**: Usar solo `points_count`:
```python
info = qdrant.get_collection(COLLECTION_NAME)
return {
    "collection": COLLECTION_NAME,
    "points_count": info.points_count,
    # "vectors_count": info.vectors_count,  # NO existe en versiones nuevas
}
```

### 6. Env vars de Docker no se actualizan con `docker compose restart`
**Síntoma**: Cambiar `VITE_API_URL` en `docker-compose.yml` y hacer `docker compose restart frontend` no aplica el cambio.
**Fix**: Usar `--force-recreate` o hacer `down` + `up`:
```bash
docker compose up -d --no-deps --force-recreate frontend
```

### 7. Docker build detectado como "long-lived process"
**Síntoma**: El tool `terminal` rechaza `docker compose up --build -d` en foreground.
**Fix**: Ejecutar en background:
```bash
docker compose up --build -d  # foreground → rechazado
# background:
nohup docker compose up --build -d > /tmp/build.log 2>&1 &
# o usar el tool con background=true
```

## URLs de acceso remoto (Cloudflared)
Levantados con éxito:
```bash
# Backend
curl -L -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb
cloudflared tunnel --url http://localhost:8000
# URL: https://taylor-affects-blog-prospects.trycloudflare.com

# Frontend
cloudflared tunnel --url http://localhost:8080
# URL: https://banana-basis-mining-inputs.trycloudflare.com
```

## Verificación final exitosa
```bash
curl -s https://taylor-affects-blog-prospects.trycloudflare.com/health
# → {"status":"ok"}

curl -s -X POST https://taylor-affects-blog-prospects.trycloudflare.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿De qué trata este documento?"}'
# → {"answer":"...", "sources":[...]}
```

## Estado final del proyecto
- Docker Compose: 4 servicios (MinIO, Qdrant, Backend, Frontend)
- Ollama: corriendo en host, accesible desde contenedores
- Modelos: `nomic-embed-text` + `llama3.2:3b`
- Acceso remoto: URLs Cloudflare funcionando
- Documento de prueba: 35 chunks indexados, respuestas con fuentes
