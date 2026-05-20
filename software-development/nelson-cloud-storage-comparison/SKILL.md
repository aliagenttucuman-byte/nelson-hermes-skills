---
name: nelson-cloud-storage-comparison
description: Comparativa y deploy de emuladores cloud local (FLoCI-AWS, MinIO, FLoCI-Azure) para el equipo Nelson.
category: software-development
tags: [cloud, storage, s3, azure, minio, floci, local-development, rag]
related_skills: [nelson-project-bootstrap, nelson-rag-pipeline, nelson-deploy-gcp]
---

# Comparativa de Storage Local para RAG/Apps

> **Trigger:** Cuando Nelson quiera comparar, evaluar o deployear un backend de storage local para un PoC, RAG o app del equipo.

## Las 3 Opciones

### 1. FLoCI-AWS (S3 emulado)
```yaml
services:
  floci:
    image: floci/floci:latest
    ports: ["4566:4566"]
    environment: [SERVICES=s3]
```
- **SDK:** boto3
- **Persistencia:** ❌ Memoria (se pierde al reiniciar)
- **Ideal para:** Testear código AWS antes de subir a la nube
- **Pitfall:** Los datos se pierden al reiniciar el contenedor

### 2. MinIO (S3 real local)
```yaml
services:
  minio:
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: test
      MINIO_ROOT_PASSWORD: test123456
    command: server /data --console-address ":9001"
```
- **SDK:** boto3 (100% compatible S3)
- **Persistencia:** ✅ Disco (sobrevive reinicios)
- **Ideal para:** Stack local estable, producción on-premise
- **Pitfall:** Necesita credenciales reales (test/test123456 por defecto)

### 3. FLoCI-Azure (Azure Blob Storage emulado)
```yaml
services:
  floci-az:
    image: floci/floci-az:latest
    ports: ["4577:4577"]
    environment: [FLOCI_AZ_STORAGE_MODE=hybrid]
```
- **SDK:** azure-storage-blob
- **Persistencia:** ⚠️ Hybrid (en memoria + flush cada 5s)
- **Ideal para:** Clientes con infraestructura Azure, migraciones futuras
- **Pitfall:** El SDK de Azure Python necesita `from_connection_string()`, no acepta `account_url` + `credential` directo para el emulador

## Tabla Rápida de Decisión

| Si el cliente usa... | Usá | Puerto |
|----------------------|-----|--------|
| AWS | FLoCI-AWS | 4566 |
| On-premise / No define | MinIO | 9000 |
| Azure | FLoCI-Azure | 4577 |

## Connection Strings

### FLoCI-AWS (boto3)
```python
s3 = boto3.client("s3", endpoint_url="http://localhost:4566")
```

### MinIO (boto3)
```python
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="test",
    aws_secret_access_key="test123456",
)
```

### FLoCI-Azure (azure-storage-blob)
```python
from azure.storage.blob import BlobServiceClient
conn_str = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=<AZURE_DEVSTORE_DUMMY_KEY>;"
    "BlobEndpoint=http://localhost:4577/devstoreaccount1;"
)
blob_service = BlobServiceClient.from_connection_string(conn_str)
```

## Pitfalls

1. **FLoCI-AWS pierde datos:** Siempre reindexar después de reiniciar
2. **MinIO sin credenciales:** Sin `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`, no inicia
3. **FLoCI-Azure + SDK Python:** Nunca uses `BlobServiceClient(account_url=..., credential=...)` con el emulador; siempre `from_connection_string()`
4. **Puertos duplicados:** Cada stack necesita sus propios puertos (backend 8000/8001/8002, frontend 8080/8081/8082, qdrant 6333/6335/6337)
5. **Frontend apuntando a localhost con Cloudflare:** `VITE_API_URL` se hornea en el build. El orden CORRECTO es:
   a. Levantar backend primero (`docker compose up -d backend`)
   b. Crear túnel Cloudflare para el backend y capturar su URL pública
   c. Buildear el frontend con esa URL: `docker compose build --build-arg VITE_API_URL=https://XXX.trycloudflare.com frontend`
   d. Levantar el frontend y crear su túnel
   Si se buildea el frontend antes de tener la URL del backend, hay que rebuildearlo con `--no-cache`.
6. **Olvidar agregar skills nuevas al sync script:** Cuando se crea una skill nueva, hay que agregarla al array `SKILLS` de `sync-to-repo.sh` antes de commitear.
7. **`vite-env.d.ts` faltante:** Sin este archivo, el build falla con `Property 'env' does not exist on type 'ImportMeta'`. Siempre incluir en `frontend/src/`:
   ```typescript
   /// <reference types="vite/client" />
   ```

## Demo para Stakeholders (Flujo End-to-End)

Este patrón se usa para mostrarle a Pablo (o cualquier stakeholder) una comparativa tangible de opciones de storage.

### Arquitectura de la Demo

```
Usuario (celular/PC)
    |
    v
Cloudflare Tunnel (URL pública temporal)
    |
    v
[Frontend React]  ←  Vite + Tailwind
    |
    |  fetch()
    v
[Backend FastAPI]
    |
    +--------+--------+--------+
    |        |        |        |
    v        v        v        v
 FLoCI   MinIO   FLoCI-Azure  Qdrant  Ollama
 (S3)    (S3)    (Azure)      (768d)  (llama3.2:3b)
```

### Pasos para Preparar la Demo

1. **Levantar los 3 stacks en paralelo** (usar directorios separados o `-p` distinto):
   ```bash
   # Stack 1: FLoCI-AWS
   cd ~/brainstorming/2026-05-13-rag-poc
   docker compose -p rag-floci -f docker-compose.yml up -d

   # Stack 2: MinIO
   cd ~/brainstorming/2026-05-13-rag-poc-minio
   docker compose -p rag-minio -f docker-compose.yml up -d

   # Stack 3: FLoCI-Azure
   cd ~/brainstorming/2026-05-14-rag-floci-azure
   docker compose -p rag-azure -f docker-compose.yml up -d
   ```

2. **Crear túneles Cloudflare** (uno por frontend y uno por backend):
   ```bash
   # FLoCI
   cloudflared tunnel --url http://localhost:8080 --protocol http2 &
   cloudflared tunnel --url http://localhost:8000 --protocol http2 &

   # MinIO
   cloudflared tunnel --url http://localhost:8081 --protocol http2 &
   cloudflared tunnel --url http://localhost:8001 --protocol http2 &

   # Azure
   cloudflared tunnel --url http://localhost:8082 --protocol http2 &
   cloudflared tunnel --url http://localhost:8002 --protocol http2 &
   ```

3. **Capturar las URLs** que cloudflared imprime en los logs.

4. **Actualizar VITE_API_URL** en cada frontend para que apunte al backend público (NO a localhost):
   ```bash
   # Ejemplo para MinIO
   docker compose -p rag-minio exec frontend sh -c 'echo "VITE_API_URL=https://BACKEND_URL.trycloudflare.com" > /app/.env'
   docker compose -p rag-minio up -d --no-deps --force-recreate frontend
   ```

5. **Subir documentos de prueba** a cada stack (o dejar los que ya están si se usan volúmenes persistentes).

6. **Verificar con el script**:
   ```bash
   FRONTEND_URL=https://XXXX.trycloudflare.com \
   BACKEND_URL=https://YYYY.trycloudflare.com \
   bash verify-rag-deployment.sh
   ```

### Guía de Conversación con el Stakeholder

| Momento | Qué decir | Qué mostrar |
|---------|----------|-------------|
| Intro | "Tenemos 3 opciones de storage para el RAG, cada una con pros y contras" | La tabla comparativa |
| Demo 1 | "Esta es la versión AWS-emulada, ideal si el cliente ya usa AWS" | FLoCI-AWS UI |
| Demo 2 | "Esta es la más estable, los datos sobreviven reinicios" | MinIO UI |
| Demo 3 | "Esta es para clientes Azure, arranca en 100ms" | FLoCI-Azure UI |
| Pregunta | "Subamos un PDF y preguntemos algo" | Subir PDF, hacer pregunta, ver respuesta con fuentes |
| Cierre | "Cualquiera de las 3 funciona. ¿Con qué cliente queremos empezar?" | Tabla de decisión |

### Tabla de Decisión para el Cliente

| Si el cliente... | Recomendación |
|------------------|---------------|
| Ya usa AWS | FLoCI-AWS → migración a S3 real trivial |
| No define cloud / On-premise | MinIO → estable, persistente, open source |
| Ya usa Azure | FLoCI-Azure → misma API, migración trivial |
| Necesita ultra-baja latencia | FLoCI-Azure → ~100ms startup |
| Necesita datos persistentes | MinIO → disco local |

## Comandos Útiles

```bash
# Ver todos los contenedores activos
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Logs de un stack específico
docker logs --tail 30 CONTAINER_NAME

# Ver blobs en FLoCI-Azure
docker exec CONTAINER mc alias set local http://localhost:4577 devstoreaccount1 KEY

# Ver archivos en MinIO
docker exec CONTAINER mc ls local/BUCKET
```

## Referencias
- FLoCI-AWS: https://github.com/floci-io/floci
- FLoCI-Azure: https://github.com/floci-io/floci-az
- MinIO: https://min.io/
- Demo Package: `~/brainstorming/2026-05-14-rag-floci-azure/README.md`
- `templates/demo-package-README.md` — Template reutilizable para armar demo packages de comparativas (con variables {{NOMBRE_PROYECTO}}, {{VARIANTE_A}}, etc.)
- `templates/ai-search-assistant-poc.md` — Template completo: PoC asistente IA con búsqueda web (DuckDuckGo + Ollama + React). Incluye secuencia correcta de deploy con Cloudflare.
- `references/parallel-backend-comparison-mayo-2026.md` (en nelson-rag-pipeline) — Detalles completos del deploy triple con URLs, puertos, problemas encontrados y fixes
