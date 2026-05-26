---
name: nelson-robotocore
description: Emulador AWS local robotocore para el equipo Nelson. Drop-in replacement de LocalStack/FLoCI-AWS con 158 servicios, 10.200+ operaciones, MIT license, snapshots. Built entirely with AI.
category: software-development
tags: [cloud, aws, robotocore, localstack, emulator, s3, boto3, docker, rag]
related_skills: [nelson-cloud-storage-comparison, nelson-rag-pipeline, nelson-project-bootstrap]
---

# robotocore — AWS Digital Twin

> **Trigger:** Cuando Nelson necesite emular servicios AWS localmente: S3, SQS, DynamoDB, Lambda, IAM, etc.

## Qué es

robotocore es un **digital twin de AWS**: un servidor local que responde fielmente a llamadas reales de la API AWS. Apunta cualquier SDK de AWS a `http://localhost:4566` y se comporta como AWS. Gratis, MIT license, sin registro, sin telemetry.

- **158 servicios, 10.200+ operaciones** (S3, SQS, DynamoDB, Lambda, IAM, STS, Step Functions, EventBridge, etc.)
  - **46 Native providers** — robotocore los intercepta directamente: Lambda real, SQS visibility real, IAM policy engine, CloudFormation 101 resource types, EventBridge 17 target types, Step Functions con JSONata, etc.
  - **112 Moto-backed** — reenvío a Moto con formato de respuesta AWS correcto
- **Mismo puerto** que LocalStack/FLoCI: **4566**
- **Misma config boto3**: `endpoint_url="http://localhost:4566"`
- **Snapshots**: API para guardar/cargar estado (`/_robotocore/state/save` y `/load`)
- **Built on Moto**: proyecto maduro, no fork de LocalStack
- **Built entirely with AI** (por Jack Danger, maintainer de Moto) — todos los prompts guardados en `prompts/`
- **AGENTS.md** específico para agentes IA que interactúen con él

## Docker Compose

```yaml
services:
  robotocore:
    image: jackdanger/robotocore:latest
    ports:
      - "4566:4566"
    # environment:
    #   - ENFORCE_IAM=1  # opcional: forzar IAM
```

## Quick Start

```bash
# Levantar
docker run -d -p 4566:4566 --name robotocore jackdanger/robotocore:latest

# Verificar health
curl -s http://localhost:4566/_robotocore/health | python3 -m json.tool

# Sanity check: quién soy
python3 -c "
import boto3
sts = boto3.client('sts', endpoint_url='http://localhost:4566',
                   aws_access_key_id='123456789012',
                   aws_secret_access_key='test',
                   region_name='us-east-1')
print(sts.get_caller_identity())
"
```

## boto3 Connection

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="123456789012",      # 12 dígitos = account ID
    aws_secret_access_key="test",           # cualquier string no vacío
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

# Crear bucket y subir archivo
s3.create_bucket(Bucket="rag-documents")
s3.put_object(Bucket="rag-documents", Key="doc.pdf", Body=open("doc.pdf", "rb"))
```

## Snapshots (persistencia manual)

robotocore es en memoria por defecto. Para no perder datos entre reinicios:

```bash
# Guardar estado
curl -X POST http://localhost:4566/_robotocore/state/save

# Cargar estado
curl -X POST http://localhost:4566/_robotocore/state/load
```

**Pitfall:** Si el contenedor se destruye sin guardar snapshot, se pierde todo. Para stacks críticos, preferir **MinIO** (persistencia nativa en disco).

## Comparativa rápida: robotocore vs FLoCI-AWS vs MinIO

| | robotocore | FLoCI-AWS | MinIO |
|---|---|---|---|
| Servicios | **158** (10.200+ ops) | ~25 | 1 (S3) |
| Native providers | **46** (Lambda real, IAM real, SQS real, CF) | Limitado | N/A |
| Moto-backed | 112 | N/A | N/A |
| Persistencia | Snapshots (manual) | ❌ Ninguna | ✅ Disco nativo |
| Licencia | MIT | Apache 2.0 | AGPL v3 |
| Registro | No | No | No |
| Lambda | Python + Node 18/20/22 real | Sí (limitado) | N/A |
| IAM | Opt-in (`ENFORCE_IAM=1`) | No | No |
| Step Functions | 18 intrinsic fn, JSONata, Map | No | N/A |
| EventBridge | 17 target types, DLQ, archive/replay | No | N/A |
| AGENTS.md | ✅ Guía específica para IA agents | No | No |
| Built with AI | ✅ 100% (prompts públicos) | No | No |
| Recomendación | **Nuevos proyectos / agentes IA** | Legacy | Stack estable |

## Pitfalls

1. **Todo siempre encendido:** No hay `SERVICES=s3,sqs`. Los 147 servicios corren siempre (consume recursos mínimos los no usados).
2. **Lambda soporta Python + Node.js:** Python 3.8–3.13 y Node 18.x/20.x/22.x. Go/Java sin plena fidelidad aún.
3. **Sin TLS:** Solo HTTP. No usar en producción expuesta a internet.
4. **Sin dashboard web:** Solo API JSON en `/_robotocore/resources`. LocalStack Pro tiene UI cloud-hosted.
5. **Snapshots ≠ Cloud Pods:** robotocore tiene save/load básico, pero no versionado ni colaboración remota como LocalStack Pro.

## En un stack RAG (docker-compose.yml)

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

volumes:
  qdrant-data:
```

## Referencias
- Repo: https://github.com/robotocore/robotocore
- LOCALSTACK.md (migración desde LocalStack): https://github.com/robotocore/robotocore/blob/main/LOCALSTACK.md
- AGENTS.md (guía para agentes AI): https://github.com/robotocore/robotocore/blob/main/AGENTS.md
- Skill relacionada: `nelson-cloud-storage-comparison` — comparativa completa con MinIO, FLoCI-Azure y FLoCI-AWS

## Archivos de soporte (en esta skill)
- `references/robotocore-snapshot-api.md` — Detalle completo de la API de snapshots (save/load/health/resources), workflow recomendado y comparativa con FLoCI-AWS y MinIO
- `references/robotocore-localstack-migration.md` — Comparativa completa de migración desde LocalStack: qué se conserva, qué se gana, qué se pierde, mapeo de config
- `references/robotocore-native-providers.md` — Lista completa de los 46 native providers con notas de fidelidad, y comparativa directa con FLoCI-AWS por qué importa para el equipo Nelson
- `scripts/robotocore-health-check.sh` — Script de verificación rápida: health endpoint, STS GetCallerIdentity, y flujo S3 completo (create bucket + list + delete)
