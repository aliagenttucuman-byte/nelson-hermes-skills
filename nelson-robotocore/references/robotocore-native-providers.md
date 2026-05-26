# robotocore — Native Providers (46 servicios con alta fidelidad)

> Fuente: README.md del repo oficial — https://github.com/robotocore/robotocore
> Verificado: 2026-05-26

Estos servicios son interceptados **directamente por robotocore** (no por Moto), lo que significa comportamiento real, no solo respuestas mockeadas.

## Lista completa de native providers

| Servicio | Notas clave |
|----------|-------------|
| ACM | Certificate management |
| API Gateway v1 | VTL templates, Lambda/Cognito authorizers |
| API Gateway v2 | HTTP API, WebSocket, JWT authorizers |
| AppSync | GraphQL execution |
| Batch | Job queues y compute environments |
| **CloudFormation** | **101 resource types, nested stacks, custom resources** |
| **CloudWatch** | Composite alarms, metric math, Log Insights |
| CloudWatch Logs | Log Insights query engine, metric/subscription filters |
| Cognito User Pools | JWT tokens, user management, triggers |
| Config | Managed rules |
| **DynamoDB** | Full fidelity, streams |
| DynamoDB Streams | Real change capture |
| EC2 | Core compute |
| ECR | Container registry |
| ECS | Task definitions, services, clusters |
| Elasticsearch | Domain management |
| **EventBridge** | **17 target types, input transformer, DLQ, archive/replay** |
| Firehose | Buffered delivery a S3 |
| **IAM** | **Full policy engine, permission boundaries, resource policies** |
| Kinesis | Streams y shard management |
| **Lambda** | **Python 3.8–3.13, Node 18.x/20.x/22.x, versions, aliases, layers, function URLs, destinations** |
| OpenSearch | Domain management |
| Rekognition | Image analysis stubs |
| Resource Groups | Group management |
| Resource Groups Tagging | Cross-service tag queries |
| Route 53 | DNS zones y records |
| **S3** | Presigned URLs (SigV2+V4), multipart, CORS, versioning, object lock, lifecycle |
| Scheduler | EventBridge Scheduler |
| Secrets Manager | Secret rotation y versioning |
| SES | Email sending |
| SES v2 | Email sending (v2 API) |
| **SNS** | Filter policies (all operators), HTTP delivery, FIFO, platform apps |
| **SQS** | **Real visibility timeouts, FIFO dedup, DLQ, long polling** |
| SSM | Parameter Store |
| **Step Functions** | **18 intrinsic functions, JSONata, Map state, callback pattern** |
| STS | AssumeRole, federation, caller identity |
| Support | Trusted Advisor |
| X-Ray | Trace management |

## Servicios Moto-backed más relevantes (112 total)

Account, ACM-PCA, Athena, Auto Scaling, Backup, **Bedrock**, **Bedrock Agent**, CloudFront, CodeBuild, CodePipeline, Cognito Identity, **EKS**, **ElastiCache**, ELB/ELBv2, **EMR**, **Glue**, **KMS**, **RDS**, RDS Data, **SageMaker**, Security Hub, SSO Admin, Transfer, **WAFv2**.

## Por qué importa para el equipo Nelson

- **Agentes IA** → AGENTS.md del repo tiene guía específica para AI agents que usen AWS SDK
- **Lambda real** → se puede testear código de Lambda en local con ejecución verdadera, no solo mock
- **SQS real** → visibility timeouts funcionan igual que AWS (crítico para Celery/workers)
- **Step Functions** → ideal para orquestar flujos multi-paso en local antes de subir a AWS
- **IAM real** → se puede testear policies de seguridad en local (activar con ENFORCE_IAM=1)

## Comparativa directa con FLoCI-AWS (nuestro legacy)

FLoCI-AWS fue útil para empezar. Robotocore lo supera en todo menos en peso (más liviano). Para proyectos nuevos que necesiten Lambda, SQS con comportamiento real, o Step Functions: usar robotocore.

Migración: trivial. Mismo puerto 4566, mismo boto3 config. Solo cambiar la imagen Docker.
