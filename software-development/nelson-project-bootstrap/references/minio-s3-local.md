# MinIO como S3 Local (alternativa a floci/localstack)

## Cuando usar

- floci (local AWS) requiere autenticacion en ghcr.io y falla con `denied`
- localstack es pesado o lento para una PoC simple
- Necesitas S3 local para PoC de RAG, documentos, backups, etc.

## Docker Compose (MinIO)

```yaml
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"   # API S3
      - "9001:9001"   # Consola Web
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

volumes:
  minio-data:
```

## Patron completo: PoC RAG Etapa 1 (MinIO + FastAPI + React)

Estructura usada en la PoC RAG del equipo Nelson (2026-05-13):

```
rag-poc/
├── docker-compose.yml     # minio + backend + frontend
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt   # fastapi uvicorn python-multipart boto3
│   └── main.py            # /health /documents /upload
└── frontend/
    ├── Dockerfile
    ├── package.json       # react react-dom axios vite tailwindcss
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── index.css
        └── App.tsx          # UI subir PDF + listar documentos
```

### docker-compose.yml completo

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
    depends_on:
      minio:
        condition: service_healthy
    volumes:
      - ./backend:/app
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
```

### Backend FastAPI (main.py)

```python
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.config import Config

app = FastAPI(title="RAG PoC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

S3_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:9000")
S3_BUCKET = os.getenv("S3_BUCKET", "rag-documents")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test123456"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    config=Config(signature_version="s3v4"),
)

def init_bucket():
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
    except:
        s3_client.create_bucket(Bucket=S3_BUCKET)

@app.on_event("startup")
async def startup():
    init_bucket()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/documents")
async def list_documents():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
    items = response.get("Contents", [])
    return {"documents": [
        {"key": o["Key"], "size": o["Size"], "last_modified": o["LastModified"].isoformat()}
        for o in items
    ]}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    contents = await file.read()
    s3_client.put_object(
        Bucket=S3_BUCKET, Key=file.filename, Body=contents,
        ContentType="application/pdf",
    )
    return {"message": "Archivo subido correctamente", "filename": file.filename}
```

### Frontend React (App.tsx - resumen)

- Estado: `file`, `uploading`, `message`, `documents[]`
- `useEffect` carga documentos al montar
- Form con `<input type="file" accept=".pdf">`
- POST a `/upload` con `FormData`
- Lista con `map` de documentos (nombre, tamaño, fecha)

URLs despues de `docker compose up`:
- Frontend: http://localhost:8080
- API: http://localhost:8000
- MinIO Consola: http://localhost:9001

## Backend (boto3 contra MinIO)

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="test",
    aws_secret_access_key="test123456",
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

# Crear bucket si no existe
try:
    s3.head_bucket(Bucket="rag-documents")
except:
    s3.create_bucket(Bucket="rag-documents")
```

## Consola Web

URL: http://localhost:9001
Login: test / test123456

## Comparativa

| Feature | floci | MinIO |
|---------|-------|-------|
| Registry | ghcr.io (requiere auth) | Docker Hub (publico) |
| Pesos | Liviano | ~300MB |
| Servicios | S3, Lambda, etc. | Solo S3 |
| Consola UI | No | Si (puerto 9001) |
| Ideal para | Multi-servicio AWS | S3-only, PoC simple |

## Pitfall: permisos Docker

Si `docker compose` falla con `permission denied`:
- Verificar que el usuario esta en el grupo `docker`: `groups`
- Si no, agregar: `sudo usermod -aG docker $USER`
- Luego: `newgrp docker` o reiniciar sesion
- Alternativa: usar `sudo` con password (preguntar a Nelson)

## Pitfall: acceso remoto a PoC

Para que Nelson acceda desde su PC Windows a la PoC corriendo en el servidor Linux:

1. **Tailscale (recomendado, ya configurado en el servidor)**
   - IP del servidor en Tailscale: `100.122.52.55`
   - Nelson instala Tailscale en Windows, loguea con la misma cuenta
   - Accede a: `http://100.122.52.55:8080`
   - No necesita abrir puertos del router

2. **Ngrok (tuneles temporales)**
   - Requiere authtoken de ngrok.com
   - `docker run --rm --network host ngrok/ngrok http 8080`
   - URL publica temporal, util para demos rapidas

3. **NO usar serveo / localtunnel**
   - Son volatiles, se cortan, no confiables para sesiones largas
   - `ssh -R 80:localhost:8080 serveo.net` funciona 30s y muere

Regla: siempre preferir Tailscale para acceso estable entre dispositivos del equipo.
