---
name: nelson-floci-gcp
description: Emulador local de GCP con floci-gcp para el equipo Nelson. Pub/Sub, Firestore, Cloud Storage, Datastore, Secret Manager. Sin cuenta GCP, sin auth. docker compose up y listo.
category: software-development
tags: [gcp, emulador, pubsub, firestore, cloud-storage, datastore, secret-manager, docker, local-dev, poc]
related_skills: [nelson-project-bootstrap, nelson-deploy-gcp, nelson-cloud-storage-comparison, nelson-background-jobs]
---

# floci-gcp — Emulador Local de GCP

> **Trigger:** Cuando Nelson quiera desarrollar o testear código GCP localmente sin una cuenta real, armar una PoC con servicios GCP, o comparar GCP con AWS/Azure localmente.

## Qué es

floci-gcp es el emulador local de GCP de la familia floci. La misma filosofía que floci-aws (4566) y floci-az (4577): `docker compose up` y tenés GCP en localhost, sin cuenta, sin auth token, sin feature gates.

- Repo: https://github.com/floci-io/floci-gcp
- Puerto: **4588**
- Stack interno: Java 25 + Quarkus 3.x + gRPC/REST en el mismo puerto (ALPN)
- Licencia: MIT
- Versión estable: 0.1.0 (mayo 2026 — proyecto joven, en activo desarrollo)

## Servicios Soportados

| Servicio GCP | Protocolo | Env var para activar |
|---|---|---|
| Pub/Sub | gRPC | `PUBSUB_EMULATOR_HOST` |
| Firestore | gRPC | `FIRESTORE_EMULATOR_HOST` |
| Datastore | gRPC | `DATASTORE_EMULATOR_HOST` |
| Cloud Storage (GCS) | REST XML + REST JSON | `STORAGE_EMULATOR_HOST` |
| Secret Manager | gRPC + REST | `SECRET_MANAGER_EMULATOR_HOST` |

## Quick Start

```yaml
# docker-compose.yml
services:
  floci-gcp:
    image: floci/floci-gcp:latest
    ports:
      - "4588:4588"
    volumes:
      - ./data:/app/data
    environment:
      FLOCI_GCP_HOSTNAME: floci-gcp
      FLOCI_GCP_BASE_URL: http://floci-gcp:4588
```

```bash
docker compose up -d
```

Variables de entorno para el cliente (SDK Python, gcloud CLI, Terraform):

```bash
export PUBSUB_EMULATOR_HOST=localhost:4588
export FIRESTORE_EMULATOR_HOST=localhost:4588
export DATASTORE_EMULATOR_HOST=localhost:4588
export STORAGE_EMULATOR_HOST=http://localhost:4588
export GOOGLE_CLOUD_PROJECT=floci-local
```

## SDK Integration (Python)

### Pub/Sub

```python
from google.cloud import pubsub_v1
import os

os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:4588"
os.environ["GOOGLE_CLOUD_PROJECT"] = "floci-local"

publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

project_path = "projects/floci-local"
topic_path = publisher.topic_path("floci-local", "mi-topic")

# Crear topic
publisher.create_topic(request={"name": topic_path})

# Publicar mensaje
publisher.publish(topic_path, b"Hola desde floci-gcp!")
```

### Firestore

```python
from google.cloud import firestore
import os

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:4588"
os.environ["GOOGLE_CLOUD_PROJECT"] = "floci-local"

db = firestore.Client(project="floci-local")

# Crear documento
doc_ref = db.collection("usuarios").document("nelson")
doc_ref.set({"nombre": "Nelson", "rol": "Líder Técnico"})

# Leer documento
doc = doc_ref.get()
print(doc.to_dict())
```

### Cloud Storage (GCS)

```python
from google.cloud import storage
import os

os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:4588"
os.environ["GOOGLE_CLOUD_PROJECT"] = "floci-local"

client = storage.Client(project="floci-local")

# Crear bucket
bucket = client.create_bucket("mi-bucket-local")

# Subir archivo
blob = bucket.blob("documentos/archivo.txt")
blob.upload_from_string("Contenido del archivo")

# Leer archivo
print(blob.download_as_text())
```

### Secret Manager

```python
from google.cloud import secretmanager
import os

os.environ["GOOGLE_CLOUD_PROJECT"] = "floci-local"
# Secret Manager usa el mismo puerto pero via variable específica

client = secretmanager.SecretManagerServiceClient()

parent = "projects/floci-local"
secret_id = "mi-secret"

# Crear secret
secret = client.create_secret(
    request={
        "parent": parent,
        "secret_id": secret_id,
        "secret": {"replication": {"automatic": {}}},
    }
)

# Agregar versión
client.add_secret_version(
    request={"parent": secret.name, "payload": {"data": b"mi-valor-secreto"}}
)
```

## Docker Compose con Backend Python

Patrón estándar del equipo para PoCs con floci-gcp:

```yaml
services:
  floci-gcp:
    image: floci/floci-gcp:latest
    ports:
      - "4588:4588"
    volumes:
      - gcp_data:/app/data
    environment:
      FLOCI_GCP_HOSTNAME: floci-gcp
      FLOCI_GCP_BASE_URL: http://floci-gcp:4588
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4588/health"]
      interval: 5s
      timeout: 3s
      retries: 10

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      PUBSUB_EMULATOR_HOST: floci-gcp:4588
      FIRESTORE_EMULATOR_HOST: floci-gcp:4588
      DATASTORE_EMULATOR_HOST: floci-gcp:4588
      STORAGE_EMULATOR_HOST: http://floci-gcp:4588
      GOOGLE_CLOUD_PROJECT: floci-local
    depends_on:
      floci-gcp:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  gcp_data:
```

## Modos de Storage

floci-gcp soporta 4 modos de persistencia configurables via `FLOCI_GCP_STORAGE_MODE`:

| Modo | Persistencia | Uso recomendado |
|------|-------------|-----------------|
| `memory` | ❌ Se pierde al reiniciar | Tests unitarios, CI |
| `persistent` | ✅ Disco | PoCs, demos con datos duraderos |
| `hybrid` | ⚠️ RAM + flush periódico | Dev local rápido |
| `wal` | ✅ Write-Ahead Log | Alta durabilidad |

Para PoCs del equipo Nelson, usar `persistent` con volumen Docker:

```yaml
environment:
  FLOCI_GCP_STORAGE_MODE: persistent
volumes:
  - gcp_data:/app/data
```

## Comparativa Familia floci

| Producto | Cloud | Puerto | Servicios |
|---------|-------|--------|-----------|
| floci-aws | AWS | 4566 | S3, SQS, SNS, Lambda, DynamoDB... |
| floci-az | Azure | 4577 | Blob Storage |
| floci-gcp | GCP | 4588 | Pub/Sub, Firestore, GCS, Datastore, Secret Manager |

## Dependencias Python

```bash
pip install \
  google-cloud-pubsub \
  google-cloud-firestore \
  google-cloud-storage \
  google-cloud-datastore \
  google-cloud-secret-manager
```

o en `requirements.txt`:
```
google-cloud-pubsub>=2.21.0
google-cloud-firestore>=2.16.0
google-cloud-storage>=2.17.0
google-cloud-datastore>=2.19.0
google-cloud-secret-manager>=2.20.0
```

## Ideas de PoC para el Equipo Nelson

1. **Pipeline de eventos Pub/Sub** — Publicar eventos de negocio, consumir con worker Python async. Ideal para arquitecturas event-driven.
2. **API FastAPI + Firestore** — CRUD con Firestore como NoSQL. Alternativa local a MongoDB.
3. **Ingestión de documentos en GCS** — Subir PDFs/archivos a bucket local. Enchufable al pipeline RAG.
4. **Pipeline completo GCP** — Pub/Sub (eventos) + Firestore (estado) + GCS (archivos) + Secret Manager (credenciales). Simula un sistema GCP real end-to-end.

## Pitfalls

1. **Proyecto joven (v0.1.0):** Algunas APIs pueden no estar 100% completas. Si algo falla, verificar si es una limitación del emulador. Monitorear el repo para releases.
2. **Puerto en AGENT.md vs README:** El AGENT.md del repo dice puerto 4578, el README dice 4588. Usar el del docker-compose oficial: **4588**.
3. **STORAGE_EMULATOR_HOST necesita http://:** A diferencia de PUBSUB_EMULATOR_HOST (que es `host:port`), STORAGE_EMULATOR_HOST debe incluir el protocolo: `http://localhost:4588`.
4. **Credenciales ficticias:** El SDK de Python puede quejarse si no hay credenciales. Solución: `export GOOGLE_APPLICATION_CREDENTIALS=/dev/null` o usar `google.auth.credentials.AnonymousCredentials()`.
5. **Health check:** Verificar que el endpoint `/health` esté disponible antes de conectar clientes. En docker compose usar `depends_on` con `condition: service_healthy`.
6. **Docker network:** Dentro de docker compose, usar el nombre del servicio (`floci-gcp:4588`), no `localhost:4588`.

## Comandos útiles

```bash
# Levantar y ver logs
docker compose up -d && docker compose logs -f floci-gcp

# Ver estado del emulador
curl http://localhost:4588/health

# Verificar conectividad desde Python
python3 -c "
import os; os.environ['PUBSUB_EMULATOR_HOST']='localhost:4588'
from google.cloud import pubsub_v1
pub = pubsub_v1.PublisherClient()
print('Pub/Sub OK:', pub.list_topics(request={'project': 'projects/floci-local'}))
"

# Bajar y limpiar datos
docker compose down -v
```

## Referencias

- Repo: https://github.com/floci-io/floci-gcp
- Docs: https://floci.io/floci-gcp/
- Docker Hub: https://hub.docker.com/r/floci/floci-gcp
- Familia floci (AWS): https://github.com/floci-io/floci
- floci-az: https://github.com/floci-io/floci-az
