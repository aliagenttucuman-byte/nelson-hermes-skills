---
name: nelson-ci-cd
title: CI/CD - GitHub Actions para Python + React + Docker + GCP
description: Pipeline completa de CI/CD para el equipo Nelson. Lint, test, build Docker, push a Artifact Registry, deploy a Cloud Run. GitHub Actions con workflows reutilizables.
skill: nelson-ci-cd
author: equipo-nelson
version: 1.0.0
keywords: [github-actions, ci, cd, docker, cloud-run, gcp, pipeline]
dependencies: [nelson-code-quality, docker-management]
---

# CI/CD - Equipo Nelson

## Workflows

| Workflow | Trigger | Que hace |
|----------|---------|----------|
| `ci.yml` | Push/PR | Lint, test, typecheck, build |
| `docker.yml` | Push a main | Build imagenes, push a Artifact Registry |
| `deploy.yml` | Push a main (despues de docker) | Deploy a Cloud Run |
| `pr.yml` | Pull Request | Quality gate completo |

## CI - Quality Gate (ci.yml)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt
      - run: pip install ruff mypy pytest
      - run: cd backend && ruff check .
      - run: cd backend && ruff format --check .
      - run: cd backend && mypy app/

  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest -xvs --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://test:test@localhost/testdb
      - uses: codecov/codecov-action@v4
        with: { files: backend/coverage.xml }

  frontend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run typecheck

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test:ci
```

## Docker Build & Push (docker.yml)

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]

env:
  PROJECT_ID: latam-flight-delay
  REGION: us-central1
  REPO: nelson-apps

jobs:
  build-backend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev
      - uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/${{ env.REPO }}/backend:${{ github.sha }}
            ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/${{ env.REPO }}/backend:latest

  build-frontend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev
      - uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/${{ env.REPO }}/frontend:${{ github.sha }}
            ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/${{ env.REPO }}/frontend:latest
```

## Deploy a Cloud Run (deploy.yml)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  workflow_run:
    workflows: ["Docker Build"]
    types: [completed]
    branches: [main]

env:
  PROJECT_ID: latam-flight-delay
  REGION: us-central1

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: nelson-backend
          region: ${{ env.REGION }}
          image: ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/nelson-apps/backend:${{ github.sha }}
          env_vars: |
            DATABASE_URL=${{ secrets.DATABASE_URL }}
            SECRET_KEY=${{ secrets.SECRET_KEY }}

  deploy-frontend:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: nelson-frontend
          region: ${{ env.REGION }}
          image: ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/nelson-apps/frontend:${{ github.sha }}
```

## Secrets necesarios en GitHub

Configurar en: Repo Settings -> Secrets and variables -> Actions

| Secret | Valor |
|--------|-------|
| `GCP_SA_KEY` | JSON key del service account de GCP |
| `DATABASE_URL` | URL de Cloud SQL (con socket o IP privada) |
| `SECRET_KEY` | Clave JWT de produccion |

## Service Account GCP (GitHub Actions)

Roles necesarios:
- Artifact Registry Reader/Writer
- Cloud Run Developer
- Service Account User

```bash
# Crear service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Asignar roles
gcloud projects add-iam-policy-binding latam-flight-delay \
  --member="serviceAccount:github-actions@latam-flight-delay.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding latam-flight-delay \
  --member="serviceAccount:github-actions@latam-flight-delay.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# Crear y descargar key
gcloud iam service-accounts keys create gcp-sa-key.json \
  --iam-account=github-actions@latam-flight-delay.iam.gserviceaccount.com
```

Luego subir el contenido de `gcp-sa-key.json` como secret `GCP_SA_KEY`.

## Estrategia de Branching

```
main     -> Produccion (auto-deploy)
develop  -> Integracion (CI corre, no deploy)
feature/* -> Desarrollo (PR a develop)
hotfix/*  -> Fix urgente (PR directo a main)
```

## Checklist antes de mergear a main

- [ ] CI pasa (lint, test, typecheck)
[ ] PR review aprobado por Beto
- [ ] Spec OpenAPI actualizada (si aplica)
- [ ] CHANGELOG.md actualizado
- [ ] Version bump en `pyproject.toml` y `package.json`

## React Doctor en CI/CD Frontend

Agregar `react-doctor` al pipeline de todos los proyectos con frontend React (ForestAI, Bisonte, etc.). Reporta SOLO los issues nuevos del PR — no los pre-existentes.

```yaml
# En .github/workflows/react-doctor.yml
name: React Doctor
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
permissions:
  contents: read
  pull-requests: write
  issues: write
  statuses: write
concurrency:
  group: react-doctor-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  react-doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0   # OBLIGATORIO para comparar con merge-base
      - uses: millionco/react-doctor@v2
```

También instalar la skill para que los agentes aprendan las reglas:
```bash
cd frontend/
npx react-doctor@latest install
```

Ver `nelson-react-doctor` para detalles completos.

## Pitfalls

- No poner secrets en logs de GitHub Actions
- Cloud Run necesita estar habilitado en GCP antes del primer deploy
- Artifact Registry repo debe existir antes del primer push
- Usar `workflow_run` solo si los workflows estan en la branch default
- Database migrations: correr `alembic upgrade head` como parte del deploy o como job separado
