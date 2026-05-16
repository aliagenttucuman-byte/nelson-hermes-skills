# Template: AI Search Assistant PoC

PoC de asistente IA con búsqueda web en tiempo real. Stack: FastAPI + DuckDuckGo + Ollama (local) + React/Vite. Deployable con FLoCI-AWS + Cloudflare.

## Puertos sugeridos (no pisar RAGs existentes)
- Frontend: 8003
- Backend: 8004
- FLoCI: 4567

## Backend (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from duckduckgo_search import DDGS
import ollama

app = FastAPI(title="AI Search Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    answer: str
    sources: list[dict]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(req.query, max_results=5):
            results.append({"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")})

    context = "\n\n".join([f"Fuente: {r['title']}\nURL: {r['url']}\nContenido: {r['snippet']}" for r in results])
    prompt = f'El usuario preguntó: "{req.query}"\n\nBasándote en estos resultados, responde en español:\n\n{context}\n\nRespuesta:'

    response = ollama.chat(model="qwen2.5:3b", messages=[{"role": "user", "content": prompt}])
    return SearchResponse(answer=response["message"]["content"], sources=results)
```

## requirements.txt
```
fastapi==0.115.0
uvicorn==0.30.6
httpx==0.27.2
duckduckgo-search==6.3.7
ollama==0.3.3
pydantic==2.9.2
```

## Dockerfile backend
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## frontend/src/vite-env.d.ts (OBLIGATORIO)
```typescript
/// <reference types="vite/client" />
```
Sin este archivo el build falla con: `Property 'env' does not exist on type 'ImportMeta'`

## docker-compose.yml
```yaml
services:
  floci:
    image: localstack/localstack:latest
    ports: ["4567:4566"]
    environment: [SERVICES=s3]
    volumes: [floci-data:/var/lib/localstack]

  backend:
    build: ./backend
    ports: ["8004:8000"]
    environment:
      - OLLAMA_HOST=http://host-gateway:11434
    extra_hosts: ["host-gateway:host-gateway"]
    depends_on: [floci]

  frontend:
    build:
      context: ./frontend
      args:
        - VITE_API_URL=__API_URL__   # REEMPLAZAR con URL pública del backend ANTES de buildear
    ports: ["8003:80"]
    depends_on: [backend]

volumes:
  floci-data:
```

## Secuencia de deploy con Cloudflare (IMPORTANTE)

```bash
# 1. Buildear y levantar backend primero
docker compose build backend
docker compose up -d backend floci
sleep 5 && curl http://localhost:8004/health  # verificar

# 2. Crear túnel para el backend y capturar URL
cloudflared tunnel --url http://localhost:8004 > /tmp/cf-backend.log 2>&1 &
sleep 15
BACKEND_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cf-backend.log | head -1)
echo "Backend URL: $BACKEND_URL"

# 3. Reemplazar __API_URL__ y buildear frontend
sed -i "s|__API_URL__|$BACKEND_URL|g" docker-compose.yml
docker compose build frontend

# 4. Levantar frontend y crear su túnel
docker compose up -d frontend
cloudflared tunnel --url http://localhost:8003 > /tmp/cf-frontend.log 2>&1 &
sleep 15
FRONTEND_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cf-frontend.log | head -1)
echo "Frontend URL: $FRONTEND_URL"
```
