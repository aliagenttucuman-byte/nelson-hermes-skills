# Deploy a Google Cloud

Guía paso a paso para deployar el stack Nelson (FastAPI + React + PostgreSQL) a Google Cloud.

## Requisitos previos

- Tener cuenta de Google Cloud con facturación habilitada (o plan free)
- Proyecto creado en Google Cloud Console
- Service account con permisos de Cloud Run, Container Registry, Cloud SQL

## 1. Instalar Google Cloud CLI

```bash
curl -sSLo /tmp/gcloud.tar.gz \
  "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz"
tar -xzf /tmp/gcloud.tar.gz -C $HOME
$HOME/google-cloud-sdk/install.sh --quiet --path-update=true
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
```

## 2. Autenticar con Service Account

Guardar el archivo JSON de credenciales:
```bash
# Guardar en ~/.gcp-service-account.json
gcloud auth activate-service-account --key-file=$HOME/.gcp-service-account.json
gcloud config set project latam-flight-delay
```

**Nota:** Si sale error "Cloud Resource Manager API has not been used", habilitarla desde:
https://console.developers.google.com/apis/api/cloudresourcemanager.googleapis.com/overview

## 3. Build y push de imágenes

```bash
# Backend
cd backend
gcloud builds submit --tag gcr.io/latam-flight-delay/nelson-backend .

# Frontend
cd ../frontend
gcloud builds submit --tag gcr.io/latam-flight-delay/nelson-frontend .
```

## 4. Deploy Backend a Cloud Run

```bash
gcloud run deploy nelson-backend \
  --image gcr.io/latam-flight-delay/nelson-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://...
```

## 5. Deploy Frontend a Cloud Run / Firebase

Opcion A - Cloud Run:
```bash
gcloud run deploy nelson-frontend \
  --image gcr.io/latam-flight-delay/nelson-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

Opcion B - Firebase Hosting:
```bash
npm install -g firebase-tools
firebase login
cd frontend && npm run build
firebase init hosting
firebase deploy
```

## 6. Base de datos (Cloud SQL)

Crear instancia PostgreSQL:
```bash
gcloud sql instances create nelson-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create appdb --instance=nelson-db
gcloud sql users create user --instance=nelson-db --password=password
```

Conectar Cloud Run a Cloud SQL:
```bash
gcloud run services update nelson-backend \
  --add-cloudsql-instances=latam-flight-delay:us-central1:nelson-db
```

## Notas de entorno de Nelson

- Docker requiere `sudo` (usuario no está en grupo docker)
- Puerto 3000 suele estar ocupado; usar 8080 para frontend
- `docker compose` (con espacio) no `docker-compose`
