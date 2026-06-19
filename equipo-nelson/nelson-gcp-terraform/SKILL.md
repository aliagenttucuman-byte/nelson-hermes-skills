---
name: nelson-gcp-terraform
description: "Terraform + Terraformer para infraestructura GCP real del equipo Nelson. Deploy de Cloud Run, Cloud SQL, GCS, Pub/Sub, IAM. Usado en proyecto LAN Chile / LATAM."
version: 1.0.0
tags: [gcp, terraform, terraformer, infra, cloud-run, latam]
category: equipo-nelson
---

# nelson-gcp-terraform

## Qué hace cada herramienta

Terraform: IaC declarativo — definís los recursos en .tf y los crea/actualiza/destruye en GCP real.
Terraformer: Terraform INVERSO — lee infra existente en GCP y genera los archivos .tf automáticamente.

Flujo normal:    .tf --> terraform apply --> GCP
Flujo inverso:   GCP existente --> terraformer import --> .tf + .tfstate

## Instalación

### Terraform
```bash
curl -LO https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform version
```

### Terraformer (solo GCP)
```bash
curl -LO https://github.com/GoogleCloudPlatform/terraformer/releases/download/0.8.24/terraformer-google-linux-amd64
chmod +x terraformer-google-linux-amd64
sudo mv terraformer-google-linux-amd64 /usr/local/bin/terraformer
terraformer version
```

## Estructura de proyecto Terraform GCP

```
infra/
  main.tf          # recursos principales
  variables.tf     # variables
  outputs.tf       # outputs
  provider.tf      # config del provider google
  terraform.tfvars # valores concretos (NO commitear si tiene secrets)
  modules/
    cloud-run/
    cloud-sql/
    gcs/
```

## provider.tf base (GCP real)

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "mi-proyecto-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

## Recursos GCP más usados en el stack Nelson/LATAM

### Cloud Run (APIs FastAPI)
```hcl
resource "google_cloud_run_v2_service" "api" {
  name     = "bisonte-api"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/bisonte-api:latest"
      ports { container_port = 9000 }
      env {
        name  = "DATABASE_URL"
        value = "postgresql://${var.db_user}:${var.db_pass}@${var.db_host}:5432/${var.db_name}"
      }
    }
  }
}
```

### Cloud SQL (PostgreSQL)
```hcl
resource "google_sql_database_instance" "main" {
  name             = "bisonte-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"  # dev; prod: db-n1-standard-2
    backup_configuration { enabled = true }
  }
  deletion_protection = false  # true en prod
}
```

### GCS Bucket
```hcl
resource "google_storage_bucket" "assets" {
  name          = "${var.project_id}-assets"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}
```

### Pub/Sub
```hcl
resource "google_pubsub_topic" "events" {
  name = "bisonte-events"
}

resource "google_pubsub_subscription" "worker" {
  name  = "bisonte-worker"
  topic = google_pubsub_topic.events.name
  ack_deadline_seconds = 60
}
```

## Terraformer — importar infra existente

```bash
# Crear directorio de trabajo con provider
mkdir -p ~/terraformer-work && cd ~/terraformer-work

cat > main.tf << 'EOF'
terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}
EOF

terraform init

# Importar recursos específicos
terraformer import google \
  --resources=compute_instance,gcs,pubsub_topic,cloud_run_service,sql_database_instance \
  --projects=MI_PROJECT_ID \
  --regions=us-central1

# Revisar lo generado
ls generated/google/
cat generated/google/cloud_run_service/main.tf
```

## Comandos Terraform esenciales

```bash
terraform init          # inicializar + descargar providers
terraform plan          # ver cambios sin aplicar
terraform apply         # aplicar cambios (pide confirmación)
terraform apply -auto-approve  # sin confirmación (CI/CD)
terraform destroy       # destruir todo
terraform output        # ver outputs
terraform state list    # listar recursos en state
terraform import google_storage_bucket.assets mi-bucket  # importar recurso existente
```

## Variables típicas (variables.tf)

```hcl
variable "project_id" { type = string }
variable "region"     { default = "us-central1" }
variable "db_user"    { type = string, sensitive = true }
variable "db_pass"    { type = string, sensitive = true }
variable "db_host"    { type = string }
variable "db_name"    { type = string }
```

## Pitfalls

- Nunca commitear terraform.tfvars con secrets — usar Secret Manager o CI/CD env vars
- El backend GCS para tfstate requiere que el bucket exista antes de terraform init
- Terraformer genera archivos con referencias hardcodeadas — revisar y parametrizar antes de usar en prod
- Cloud Run requiere habilitar la API: gcloud services enable run.googleapis.com
- deletion_protection=true en prod para Cloud SQL — no se puede destruir por accidente
- Terraformer necesita el provider plugin instalado localmente antes de correr (terraform init primero)
