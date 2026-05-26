# Migración desde LocalStack a robotocore

Fuente: https://github.com/robotocore/robotocore/blob/main/LOCALSTACK.md

## Contexto

LocalStack Community Edition dejó de recibir actualizaciones en marzo 2026. Requiere auth token.
robotocore es la alternativa MIT-licensed, sin registro, sin telemetry.

## Qué conservás (drop-in)

- **Mismo puerto**: 4566 — ningún cambio en clientes
- **Misma config SDK**: `endpoint_url="http://localhost:4566"` funciona igual
- **Mismo manejo de credenciales**: dummy credentials, `AWS_ACCESS_KEY_ID=test`
- **Mismo workflow Docker**: `docker run -p 4566:4566 <imagen>`
- **Todos los ~25 servicios de Community**: cada servicio de LocalStack Community está en robotocore

## Qué ganás

| Feature | LocalStack Community | robotocore |
|---------|---------------------|------------|
| Servicios | ~25 | 147 (38 nativos + 109 Moto-backed) |
| Lambda execution | Sí | Sí (in-process Python) |
| SQS behavioral fidelity | Básica | Real visibility timeouts, PurgeInProgress, DLQ |
| IAM enforcement | No (Pro) | Sí (opt-in: `ENFORCE_IAM=1`) |
| State snapshots | No (Pro: Cloud Pods) | Sí (`/_robotocore/state/save` y `/load`) |
| Chaos engineering | No (Pro) | Sí (`/_robotocore/chaos/rules`) |
| Audit log | No | Sí (`/_robotocore/audit`) |
| Resource browser | No (Pro) | Sí (`/_robotocore/resources`) |
| Auth token | Requerido post-Marzo 2026 | Nunca |
| Licencia | Apache 2.0 (sunsetting) | MIT |

## Qué perdés (honestidad)

- **`localstack` CLI**: no equivalente. Usar `docker run/stop` y `aws --endpoint-url` directamente.
- **`awslocal` wrapper**: usar `export AWS_ENDPOINT_URL=http://localhost:4566` (funciona con cualquier SDK).
- **Cloud Pods** (Pro): robotocore tiene save/load básico, pero no versionado ni colaboración remota.
- **Lambda Docker execution**: LocalStack corre Lambdas en contenedores Docker aislados. robotocore ejecuta Python in-process (más rápido pero sin soporte total de otros runtimes).
- **Ecosistema maduro**: LocalStack tiene integraciones Terraform, plugins CI/CD, Testcontainers. robotocore es nuevo.
- **Web dashboard**: LocalStack Pro tiene dashboard cloud-hosted. robotocore solo tiene API JSON.
- **HTTPS/TLS**: LocalStack soporta TLS. robotocore solo HTTP.
- **`SERVICES` env var**: LocalStack permite habilitar servicios selectivamente. robotocore corre los 147 siempre (los no usados consumen recursos negligible).

## Mapeo de configuración

| LocalStack | robotocore | Notas |
|---|---|---|
| `GATEWAY_LISTEN=:4566` | Default | Mismo puerto |
| `SERVICES=s3,sqs` | Todo siempre on | No hay subconjunto |
| `DEBUG=1` | `ROBOTOCORE_LOG_LEVEL=DEBUG` | |
| `PERSISTENCE=1` | Snapshot API | `POST /_robotocore/state/save` |
| `LAMBDA_EXECUTOR=local` | Default | In-process execution |
| `DEFAULT_REGION` | `AWS_DEFAULT_REGION` | Standard AWS env var |
| `ENFORCE_IAM=1` | `ENFORCE_IAM=1` | Igual |
| `LOCALSTACK_API_KEY` | No necesario | No auth, nunca |
| `LOCALSTACK_HOST` | `AWS_ENDPOINT_URL` | Standard AWS env var |

## Quick migration

```bash
# Antes
docker run -p 4566:4566 localstack/localstack

# Después
docker run -p 4566:4566 jackdanger/robotocore
```

Eso es todo. Mismo puerto, mismo endpoint, mismas credenciales.
