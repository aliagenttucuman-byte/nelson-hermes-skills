# FLoCI-az: Local Azure Emulator

Repositorio: https://github.com/floci-io/floci-az

## Qué es

FLoCI-az es el equivalente Azure de FLoCI (AWS). Emula servicios de Azure Storage localmente sin necesidad de cuenta ni costos. Es open-source, MIT, y tiene startup <100ms.

## Servicios soportados

| Servicio | Ruta | Operaciones clave |
|----------|------|-------------------|
| Blob Storage | `/{account}/` | Create/delete containers, upload/download/delete blobs, list blobs |
| Queue Storage | `/{account}-queue/` | Create/delete queues, send/receive/peek/delete messages |
| Table Storage | `/{account}-table/` | Create/delete tables, CRUD de entidades |
| Azure Functions | `/{account}-functions/` | Deploy & invoke HTTP-triggered functions (Node, Python, Java, .NET) |

## Connection String

```text
DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=<AZURE_DEVSTORE_DUMMY_KEY>;BlobEndpoint=http://localhost:4577/devstoreaccount1;QueueEndpoint=http://localhost:4577/devstoreaccount1-queue;TableEndpoint=http://localhost:4577/devstoreaccount1-table;
```

## Modos de persistencia

Igual que FLoCI-AWS:

| Modo | Comportamiento | Durabilidad |
|------|---------------|-------------|
| `memory` (default) | Todo en RAM, se pierde al detener | ❌ Ninguna |
| `persistent` | Carga al startup, flush al shutdown | ⚠️ Media |
| `hybrid` | RAM + flush async cada 5s | ✅ Buena |
| `wal` | Write-Ahead Log, cada mutación a disco antes de responder | 💎 Máxima |

Configurar via env var: `FLOCI_AZ_STORAGE_MODE=hybrid`

## Docker Compose

```yaml
services:
  floci-az:
    image: floci/floci-az:latest
    ports:
      - "4577:4577"
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock  # requerido SOLO para Azure Functions
```

> El mount de `/var/run/docker.sock` es necesario solo si se usan Azure Functions (Docker-in-Docker para spawnear runtimes). Para solo Storage, es opcional.

## CLI companion: `azfloci`

Python CLI que actúa como proxy transparente del Azure CLI oficial (`az`). Inyecta connection strings y desactiva SSL verification automáticamente.

```bash
alias az='python3 /path/to/floci-az/azfloci/azfloci.py'
az setup  # Muestra connection string info
```

## Comparación con alternativas

| Feature | FLoCI-az | Azurite (oficial) | Functions Core Tools |
|---------|----------|-------------------|----------------------|
| Blob | ✅ | ✅ | ❌ |
| Queue | ✅ | ✅ | ❌ |
| Table | ✅ | ✅ | ❌ |
| Functions | ✅ | ❌ | ✅ |
| Startup | <100ms | Moderado | Fast |
| Puerto unificado | ✅ (4577) | ❌ (10000-10002) | ❌ |
| License | MIT | MIT | MIT |

## Uso en backend Python (boto3-like)

Aunque FLoCI-az emula Azure, se puede usar el SDK de Azure Storage:

```python
from azure.storage.blob import BlobServiceClient

conn_str = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=<AZURE_DEVSTORE_DUMMY_KEY>;"
    "BlobEndpoint=http://floci-az:4577/devstoreaccount1;"
)

blob_service = BlobServiceClient.from_connection_string(conn_str)
container = blob_service.create_container("rag-documents")
```

## Cuándo usar en el equipo Nelson

- **Si YPF o el cliente usa Azure** (no AWS): FLoCI-az es el emulador local apropiado para desarrollo y testing sin costos.
- **Si se migra de AWS a Azure**: probar compatibilidad con FLoCI-az en paralelo con FLoCI-AWS.
- **Para demos persistentes**: igual que con FLoCI-AWS, preferir `hybrid` o `wal` mode, o usar Azurite si se necesita más madurez.

## Notas

- Stack técnico: Java, Quarkus, Docker-in-Docker para Functions.
- Default port: 4577 (todos los servicios comparten este puerto).
- Default account: `devstoreaccount1` / key fijo (no valida credenciales en modo dev).
- Latest release: https://github.com/floci-io/floci-az/releases/latest
- Docker Hub: https://hub.docker.com/r/floci/floci-az
