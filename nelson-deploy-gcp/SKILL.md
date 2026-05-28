---
name: nelson-deploy-gcp
title: Deploy GCP - Cloud Run + Cloud SQL + Artifact Registry
description: Deploy a Google Cloud Platform para el equipo Nelson. Cloud Run para containers, Cloud SQL PostgreSQL, Artifact Registry, Load Balancer, Cloud DNS. Configuracion de service accounts y networking.
skill: nelson-deploy-gcp
author: equipo-nelson
version: 1.0.0
keywords: [gcp, cloud-run, cloud-sql, artifact-registry, deploy, google-cloud]
dependencies: [docker-management, nelson-ci-cd]
---

# Deploy GCP - Equipo Nelson

## Stack GCP

| Servicio | Uso | Tier |
|----------|-----|------|
| Cloud Run | Backend + Frontend containers | Free tier (2M requests/mes) |
| Cloud SQL | PostgreSQL managed | db-f1-micro (free tier) |
| Artifact Registry | Docker images | 0.5GB storage free |
| Cloud DNS | Dominio custom | Pago por uso |
| Secret Manager | Secrets (DB, JWT) | Free tier 6 secret versions |
| Cloud Build | Build nativo (alternativa a GH Actions) | 120 min/dia free |

## Pre-requisitos

1. Proyecto GCP creado: `latam-flight-delay`
2. Billing habilitado (obligatorio, pero free tier cubre)
3. APIs habilitadas:

```bash
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable servicenetworking.googleapis.com
```

## Cloud SQL (PostgreSQL)

```bash
# Crear instancia (free tier: db-f1-micro, 1 vCPU, 0.6GB RAM)
gcloud sql instances create nelson-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB \
  --storage-auto-increase \
  --availability-type=ZONAL \
  --no-backup \
  --root-password=TU_PASSWORD_SEGURA

# Crear database
gcloud sql databases create appdb --instance=nelson-db

# Crear usuario
gcloud sql users create nelson_app \
  --instance=nelson-db \
  --password=OTRA_PASSWORD_SEGURA

# Obtener connection name (para Cloud Run)
gcloud sql instances describe nelson-db --format='value(connectionName)'
# Resultado: latam-flight-delay:us-central1:nelson-db
```

Conexion desde Cloud Run (Unix Socket):
```
postgresql://USER:PASS@/DB_NAME?host=/cloudsql/CONNECTION_NAME
```

## Artifact Registry

```bash
# Crear repositorio Docker
gcloud artifacts repositories create nelson-apps \
  --repository-format=docker \
  --location=us-central1 \
  --description="Imagenes del equipo Nelson"

# Auth local
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## Secret Manager

```bash
# Guardar secrets
echo -n "postgresql://..." | gcloud secrets create database-url --data-file=-
echo -n "tu-secret-key-jwt" | gcloud secrets create jwt-secret-key --data-file=-

# Permitir que Cloud Run lea secrets
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Deploy Cloud Run (Backend)

```bash
# Build y push local
cd backend
docker build -t us-central1-docker.pkg.dev/latam-flight-delay/nelson-apps/backend:latest .
docker push us-central1-docker.pkg.dev/latam-flight-delay/nelson-apps/backend:latest

# Deploy
gcloud run deploy nelson-backend \
  --image us-central1-docker.pkg.dev/latam-flight-delay/nelson-apps/backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets DATABASE_URL=database-url:latest,SECRET_KEY=jwt-secret-key:latest \
  --set-env-vars ENV=production,LOG_LEVEL=INFO \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --min-instances 0 \
  --timeout 300 \
  --port 8000
```

Con Cloud SQL conectado:
```bash
gcloud run deploy nelson-backend \
  ... \
  --add-cloudsql-instances latam-flight-delay:us-central1:nelson-db \
  --set-env-vars DATABASE_URL="postgresql://USER:PASS@/appdb?host=/cloudsql/latam-flight-delay:us-central1:nelson-db"
```

## Deploy Cloud Run (Frontend)

```bash
cd frontend
docker build -t us-central1-docker.pkg.dev/latam-flight-delay/nelson-apps/frontend:latest .
docker push us-central1-docker.pkg.dev/latam-flight-delay/nelson-apps/frontend:latest

gcloud run deploy nelson-frontend \
  --image us-central1-docker.pkg.dev/latam-flight-delay/nelson-apps/frontend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=https://nelson-backend-xxx-uc.a.run.app \
  --memory 256Mi \
  --cpu 1 \
  --max-instances 5
```

## Dominio Custom

```bash
# Mapear dominio a Cloud Run
gcloud run domain-mappings create \
  --service nelson-backend \
  --domain api.tudominio.com \
  --region us-central1

# Configurar DNS con los records que te da GCP
gcloud run domain-mappings describe --domain api.tudominio.com --region us-central1
```

## Costos Free Tier (aprox mensual)

| Servicio | Free Tier | Uso tipico |
|----------|-----------|------------|
| Cloud Run | 2M req, 360K GB-sec, 180K vCPU-sec | ~$0 |
| Cloud SQL | db-f1-micro + 10GB | ~$0 (siempre free tier) |
| Artifact Registry | 0.5GB storage | ~$0 |
| Secret Manager | 6 active versions | ~$0 |
| Egress | 1GB/mes | ~$0 |

**Total estimado: $0-5/mes** (dependiendo del trafico)

## Comandos utiles

```bash
# Ver logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=nelson-backend" --limit=50

# Ver metrics
gcloud monitoring metrics list | grep run

# Escalar manualmente
gcloud run services update nelson-backend --max-instances=20 --region=us-central1

# Rollback
gcloud run services update-traffic nelson-backend --to-revisions=LATEST=100 --region=us-central1

# Obtener URL
gcloud run services describe nelson-backend --region=us-central1 --format='value(status.url)'
```

## Checklist antes de deploy

- [ ] Cloud SQL instancia creada y accesible
- [ ] Secrets creados en Secret Manager
- [ ] Service account tiene permisos correctos
- [ ] Imagen Docker buildada y pusheada
- [ ] Variables de entorno configuradas
- [ ] Health checks responden OK localmente
- [ ] Base de datos migrada (`alembic upgrade head`)

## Pitfalls

- **Entrenar modelo ML en startup de Cloud Run → timeout en Free Tier**: el entrenamiento toma 25s+ y Cloud Run Free Tier tiene límite de startup. Siempre pre-entrenar en build time dentro del Dockerfile con `RUN python scripts/train_model.py` y guardar el pkl. En runtime solo cargar con `joblib.load()` — startup < 1s. Ver nelson-data-science pitfall #1.
- Cloud Run cold start: usar `--min-instances=1` si la latencia importa
- Cloud SQL connection: usar Unix socket `/cloudsql/...`, no IP publica
- No exponer Cloud SQL a internet (0.0.0.0/0)
- Secrets nunca en variables de entorno plain; usar Secret Manager
- Cloud Run es stateless: no guardar archivos locales, usar Cloud Storage
- Max request size en Cloud Run: 32MB (para uploads)
