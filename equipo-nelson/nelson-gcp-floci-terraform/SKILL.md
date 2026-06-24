---
name: nelson-gcp-floci-terraform
description: "Spike de prueba: floci-gcp (emulador local GCP en :4588) + Terraform + Terraformer. Valida flujo IaC sin cuenta GCP real. Ideal para desarrollar y testear antes de desplegar en LATAM."
version: 1.0.0
tags: [gcp, terraform, terraformer, floci, emulador, local, spike]
category: equipo-nelson
---

# nelson-gcp-floci-terraform — Spike local

Floci-gcp emula GCP localmente en :4588. Terraform + Terraformer apuntan al emulador en vez de GCP real.
Ideal para desarrollar y validar módulos de infra antes de deployar a LATAM.

## Prerequisitos

1. floci-gcp corriendo en :4588 (ver skill nelson-floci-gcp)
2. Terraform instalado (ver skill nelson-gcp-terraform)
3. Terraformer instalado (ver skill nelson-gcp-terraform)

## Paso 1 — Levantar floci-gcp

```bash
cd /home/server/proyectos/floci-gcp
docker compose up -d
curl http://localhost:4588/health  # debe responder OK
```

## Paso 2 — Configurar entorno para emulador

```bash
export GOOGLE_PROJECT="local-project"
export GOOGLE_OAUTH_ACCESS_TOKEN="fake-token-emulador"
export CLOUDSDK_CORE_PROJECT="local-project"
# Deshabilitar auth real de Google
export GOOGLE_APPLICATION_CREDENTIALS=""
```

## Paso 3 — provider.tf apuntando al emulador

```bash
mkdir -p ~/spike-floci-terraform && cd ~/spike-floci-terraform
```

Crear provider.tf:
```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project                   = "local-project"
  region                    = "us-central1"
  access_token              = "fake-token-emulador"
  skip_in_flight_check      = true

  # Redirigir todos los servicios al emulador
  storage_custom_endpoint           = "http://localhost:4588/"
  pubsub_custom_endpoint            = "http://localhost:4588/"
  cloud_functions_custom_endpoint   = "http://localhost:4588/"
  bigquery_custom_endpoint          = "http://localhost:4588/"
  logging_custom_endpoint           = "http://localhost:4588/"
  monitoring_custom_endpoint        = "http://localhost:4588/"
  secret_manager_custom_endpoint    = "http://localhost:4588/"
}
```

## Paso 4 — main.tf con recursos del spike

```hcl
# GCS Bucket
resource "google_storage_bucket" "test" {
  name          = "local-project-test-bucket"
  location      = "US"
  force_destroy = true
}

# Pub/Sub Topic
resource "google_pubsub_topic" "events" {
  name = "test-events"
}

resource "google_pubsub_subscription" "worker" {
  name  = "test-worker"
  topic = google_pubsub_topic.events.name
  ack_deadline_seconds = 30
}

# Secret Manager
resource "google_secret_manager_secret" "db_pass" {
  secret_id = "db-password"
  replication {
    auto {}
  }
}
```

## Paso 5 — Aplicar

```bash
terraform init
terraform plan
terraform apply -auto-approve
```

## Paso 6 — Terraformer inverso sobre el emulador

Después de crear recursos con Terraform, validar que Terraformer los puede importar:

```bash
mkdir -p ~/spike-terraformer-import && cd ~/spike-terraformer-import

# Provider apuntando al emulador (mismo provider.tf del paso 3)
cp ~/spike-floci-terraform/provider.tf .
terraform init

# Importar los recursos creados
terraformer import google \
  --resources=gcs,pubsub_topic \
  --projects=local-project \
  --regions=us-central1

# Ver lo generado
ls generated/google/
cat generated/google/gcs/main.tf
```

## Flujo completo del spike

```
floci-gcp :4588 (emulador)
    ↑
Terraform apply (crea recursos en emulador)
    ↓
Recursos en floci-gcp
    ↑
Terraformer import (lee recursos, genera .tf)
    ↓
archivos .tf generados (validados, listos para prod)
    ↑
Terraform apply → GCP real (LATAM / LAN Chile)
```

## Verificar recursos creados en floci-gcp

```bash
# Ver buckets GCS
curl http://localhost:4588/storage/v1/b?project=local-project

# Ver topics Pub/Sub  
curl http://localhost:4588/v1/projects/local-project/topics

# Ver secrets
curl http://localhost:4588/v1/projects/local-project/secrets
```

## Script de render del stack completo

Para generar PNG visual del stack lean-ctx + Headroom + Honcho:
```bash
python3 ~/.hermes/skills/equipo-nelson/nelson-headroom/scripts/render_stack_diagram.py
```
Output: /tmp/stack-tokens/stack.png

## Pitfalls

- floci-gcp no implementa todas las APIs de GCP — verificar qué servicios soporta antes del spike
- El provider google v5 puede rechazar el fake-token — si falla, probar con GOOGLE_OAUTH_ACCESS_TOKEN=ya29.fake
- Terraformer necesita terraform init en el directorio de trabajo antes de correr
- Los custom_endpoints del provider deben terminar con / (slash final obligatorio)
- Si Terraform no acepta skip_in_flight_check, removerlo — es opcional
- El bucket name debe ser globalmente único incluso en el emulador para evitar conflictos
- Para Firestore/Datastore usar los env vars específicos: FIRESTORE_EMULATOR_HOST=localhost:4588
