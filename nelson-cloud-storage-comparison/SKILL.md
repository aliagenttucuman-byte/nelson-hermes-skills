---
name: nelson-cloud-storage-comparison
description: Comparativa y deploy de emuladores cloud local (robotocore, MinIO, FLoCI-Azure, FLoCI-AWS legacy) para el equipo Nelson.
category: software-development
tags: [cloud, storage, s3, azure, minio, floci, robotocore, local-development, rag]
related_skills: [nelson-project-bootstrap, nelson-rag-pipeline, nelson-deploy-gcp, nelson-robotocore]
---

# Comparativa de Storage Local para RAG/Apps

> **Trigger:** Cuando Nelson quiera comparar, evaluar o deployear un backend de storage local para un PoC, RAG o app del equipo.

## Las 4 Opciones

### 1. robotocore (AWS digital twin — recomendado)
```yaml
services:
  robotocore:
    image: jackdanger/robotocore:latest
    ports: ["4566:4566"]
```
- **SDK:** boto3 (drop-in, mismo que AWS real)
- **Servicios:** 147 (S3, SQS, DynamoDB, Lambda, IAM, etc.)
- **Persistencia:** ⚠️ En memoria por defecto, pero con API de snapshots (`POST /_robotocore/state/save` y `/load`)
- **Ideal para:** Reemplazo permanente y gratuito de LocalStack/FLoCI, CI/CD, tests AWS
- **Pitfall:** No permite habilitar servicios selectivamente (todo siempre on); Lambda solo Python in-process
- **Licencia:** MIT, sin registro, sin telemetry
- **Repo:** https://github.com/robotocore/robotocore

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

### 4. FLoCI-AWS (legacy — emulador AWS clásico)
```yaml
services:
  floci:
    image: floci/floci:latest
    ports: ["4566:4566"]
    environment: [SERVICES=s3]
```
- **SDK:** boto3
- **Servicios:** ~25 (comunidad)
- **Persistencia:** ❌ Memoria (se pierde al reiniciar)
- **Ideal para:** Legacy / stacks que ya usan FLoCI y no justifican migrar
- **Pitfall:** Los datos se pierden al reiniciar el contenedor; menos servicios que robotocore; imagen puede quedar obsoleta

## Tabla Rápida de Decisión

| Si el cliente usa... | Usá | Puerto | Notas |
|----------------------|-----|--------|-------|
| AWS / Reemplazo LocalStack | **robotocore** | 4566 | 147 servicios, MIT, snapshots |
| On-premise / No define | MinIO | 9000 | Persistente, open source |
| Azure | FLoCI-Azure | 4577 | Hybrid, ~100ms startup |
| Legacy FLoCI (ya en uso) | FLoCI-AWS | 4566 | No recomendado para nuevos proyectos |

## Connection Strings

### robotocore (boto3)
```python
import boto3
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="123456789012",  # cualquier string de 12 dígitos = account ID
    aws_secret_access_key="test",
    region_name="us-east-1",
)
```

### FLoCI-AWS (boto3) — legacy
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

1. **robotocore sin snapshot pierde datos:** Igual que FLoCI, es en memoria. Usar `POST /_robotocore/state/save` antes de bajar el contenedor, o montar volumen si la imagen lo soporta
2. **FLoCI-AWS pierde datos:** Siempre reindexar después de reiniciar. Legacy — preferir robotocore para nuevos proyectos
3. **MinIO sin credenciales:** Sin `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`, no inicia
4. **FLoCI-Azure + SDK Python:** Nunca uses `BlobServiceClient(account_url=..., credential=...)` con el emulador; siempre `from_connection_string()`
5. **Puertos duplicados:** Cada stack necesita sus propios puertos (backend 8000/8001/8002/8003, frontend 8080/8081/8082/8083, qdrant 6333/6335/6337/6339)
6. **Frontend apuntando a localhost con Cloudflare:** `VITE_API_URL` se hornea en el build. El orden CORRECTO es:
   a. Levantar backend primero (`docker compose up -d backend`)
   b. Crear túnel Cloudflare para el backend y capturar su URL pública
   c. Buildear el frontend con esa URL: `docker compose build --build-arg VITE_API_URL=https://XXX.trycloudflare.com frontend`
   d. Levantar el frontend y crear su túnel
   Si se buildea el frontend antes de tener la URL del backend, hay que rebuildearlo con `--no-cache`.
7. **Cloudflare Tunnel con nginx como proxy interno — un solo tunnel:** Cuando el frontend tiene nginx que proxea `/api/...` al backend internamente, **no hace falta tunnel separado para el backend**. Solo un tunnel al puerto del nginx (ej. 3010). Las requests llegan al nginx público, que proxea al backend en la red interna Docker. Para que funcione, `VITE_API_URL` debe ser string vacío en el build (URLs relativas). Este patrón es más simple y seguro que dos tunnels separados — el backend queda completamente interno. Contrasta con el patrón de dos tunnels de la RAG PoC donde no había nginx.
   ```bash
   cloudflared tunnel --url http://localhost:3010 --protocol http2 2>&1 | tee /tmp/cf.log &
   sleep 15 && grep -i "trycloudflare" /tmp/cf.log
   ```
8. **Olvidar agregar skills nuevas al sync script:** Cuando se crea una skill nueva, hay que agregarla al array `SKILLS` de `sync-to-repo.sh` antes de commitear.
9. **Editar el skill en el path equivocado — cambios no se sincronizan:** Las skills del equipo existen en DOS paths:
   - `~/.hermes/skills/<nombre>/` (root)
   - `~/.hermes/skills/software-development/<nombre>/` (categoría)
   
   El `sync-to-repo.sh` lee desde `software-development/`. Si editás el root path, los cambios NO llegan al repo GitHub. **Siempre verificar cuál copia estás editando** antes de correr el sync. Si hay duda, usar `diff` para comparar:
   ```bash
   diff ~/.hermes/skills/nelson-rag-pipeline/SKILL.md \
        ~/.hermes/skills/software-development/nelson-rag-pipeline/SKILL.md
   ```
   Y copiar la correcta: `cp ~/.hermes/skills/<name>/SKILL.md ~/.hermes/skills/software-development/<name>/SKILL.md`
10. **`vite-env.d.ts` faltante:** Sin este archivo, el build falla con `Property 'env' does not exist on type 'ImportMeta'`. Siempre incluir en `frontend/src/`:
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
    +--------+--------+--------+--------+
    |        |        |        |        |
    v        v        v        v        v
robotocore MinIO  FLoCI-Azure FLoCI  Qdrant  Ollama
  (AWS)    (S3)    (Azure)   (AWS)   (768d) (llama3.2:3b)
  147 srv  real    hybrid    legacy
```

### Pasos para Preparar la Demo

1. **Levantar los 4 stacks en paralelo** (usar directorios separados o `-p` distinto):
   ```bash
   # Stack 1: robotocore (recomendado)
   cd ~/brainstorming/2026-05-13-rag-poc-robotocore
   docker compose -p rag-robotocore -f docker-compose.yml up -d

   # Stack 2: MinIO
   cd ~/brainstorming/2026-05-13-rag-poc-minio
   docker compose -p rag-minio -f docker-compose.yml up -d

   # Stack 3: FLoCI-Azure
   cd ~/brainstorming/2026-05-14-rag-floci-azure
   docker compose -p rag-azure -f docker-compose.yml up -d

   # Stack 4: FLoCI-AWS (legacy)
   cd ~/brainstorming/2026-05-13-rag-poc
   docker compose -p rag-floci -f docker-compose.yml up -d
   ```

2. **Crear túneles Cloudflare** (uno por frontend y uno por backend):
   ```bash
   # robotocore
   cloudflared tunnel --url http://localhost:8080 --protocol http2 &
   cloudflared tunnel --url http://localhost:8000 --protocol http2 &

   # MinIO
   cloudflared tunnel --url http://localhost:8081 --protocol http2 &
   cloudflared tunnel --url http://localhost:8001 --protocol http2 &

   # Azure
   cloudflared tunnel --url http://localhost:8082 --protocol http2 &
   cloudflared tunnel --url http://localhost:8002 --protocol http2 &

   # FLoCI legacy
   cloudflared tunnel --url http://localhost:8083 --protocol http2 &
   cloudflared tunnel --url http://localhost:8003 --protocol http2 &
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
### Guía de Conversación con el Stakeholder

| Momento | Qué decir | Qué mostrar |
|---------|----------|-------------|
| Intro | "Tenemos 4 opciones de storage para el RAG, cada una con pros y contras" | La tabla comparativa |
| Demo 1 | "Esta es la versión AWS más completa: 147 servicios, gratis para siempre, con snapshots" | robotocore UI |
| Demo 2 | "Esta es la más estable, los datos sobreviven reinicios" | MinIO UI |
| Demo 3 | "Esta es para clientes Azure, arranca en 100ms" | FLoCI-Azure UI |
| Demo 4 | "Esta es la versión legacy que ya teníamos — sigue funcionando pero no la recomendamos para nuevos proyectos" | FLoCI-AWS UI |
| Pregunta | "Subamos un PDF y preguntemos algo" | Subir PDF, hacer pregunta, ver respuesta con fuentes |
| Cierre | "Cualquiera de las 4 funciona. robotocore es la recomendación para nuevos proyectos AWS. ¿Con qué cliente queremos empezar?" | Tabla de decisión |

### Tabla de Decisión para el Cliente

| Si el cliente... | Recomendación |
|------------------|---------------|
| Ya usa AWS / Quiere reemplazar LocalStack | **robotocore** → 147 servicios, MIT, snapshots, drop-in |
| No define cloud / On-premise | MinIO → estable, persistente, open source |
| Ya usa Azure | FLoCI-Azure → misma API, migración trivial |
| Necesita ultra-baja latencia | FLoCI-Azure → ~100ms startup |
| Necesita datos persistentes | MinIO → disco local |
| Ya tiene FLoCI-AWS en producción | FLoCI-AWS (legacy) → mantener, no migrar sin necesidad |

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
- robotocore: https://github.com/robotocore/robotocore
- FLoCI-AWS: https://github.com/floci-io/floci
- FLoCI-Azure: https://github.com/floci-io/floci-az
- MinIO: https://min.io/
- Demo Package robotocore: `~/brainstorming/2026-05-13-rag-poc-robotocore/README.md`
- Demo Package: `~/brainstorming/2026-05-14-rag-floci-azure/README.md`
- `templates/demo-package-README.md` — Template reutilizable para armar demo packages de comparativas (con variables {{NOMBRE_PROYECTO}}, {{VARIANTE_A}}, etc.)
- `templates/ai-search-assistant-poc.md` — Template completo: PoC asistente IA con búsqueda web (DuckDuckGo + Ollama + React). Incluye secuencia correcta de deploy con Cloudflare.
- `references/parallel-backend-comparison-mayo-2026.md` (en nelson-rag-pipeline) — Detalles completos del deploy triple con URLs, puertos, problemas encontrados y fixes
