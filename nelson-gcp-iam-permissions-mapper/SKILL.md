---
name: nelson-gcp-iam-permissions-mapper
description: "Analiza módulos Terraform del equipo Nelson y genera automáticamente la lista de permisos GCP IAM necesarios para deployar en producción. Entrega 3 formatos — roles predefinidos (rápido), custom role con permisos atómicos (least privilege), y comandos gcloud listos para el admin. Incluye script de validación pre-apply. Carga esta skill cuando Nelson necesita pedir permisos al área de cloud/seguridad del cliente."
when_to_use: "Pedir permisos GCP al área de cloud; auditar qué roles necesita una service account; generar custom role least privilege; validar permisos antes de terraform apply; entregar request formal de IAM al admin GCP del cliente; pasar PoC local floci-gcp a producción real."
---

# nelson-gcp-iam-permissions-mapper

Mapea recursos Terraform → permisos GCP IAM necesarios. Cuando Nelson necesita pedirle al área de cloud del cliente que le habiliten permisos para deployar, esta skill genera el request formal en tres formatos para que el admin lo aplique sin pensar.

## Cuándo usar esta skill

- Nelson va a deployar una PoC en GCP real y necesita pedir permisos
- El cliente (LAN, ForestAI, etc.) tiene área de cloud estricta que exige justificación
- Querés validar antes del `terraform apply` que no te van a faltar permisos
- Pasaje de PoC en floci-gcp a producción real (typical handoff)
- Auditoría — qué hace exactamente esta service account

## Inputs esperados

- Directorio `terraform/modules/` del proyecto (ej `farmacia-poc-gcp/terraform/modules/`)
- Opcionalmente `terraform/environments/prod/main.tf` para ver qué módulos se usan en prod
- Nombre del proyecto GCP destino (ej `lan-copilot-prod`)
- Nombre de la service account a usar (ej `tf-deployer`)

## Outputs entregados

1. **Lista de recursos detectados** — tabla con cada `resource` de Terraform y su tipo GCP
2. **Roles predefinidos** — formato rápido, copy-paste para `gcloud`
3. **Custom Role YAML** — least privilege con permisos atómicos
4. **Comandos `gcloud`** — listos para el admin
5. **Script `validate-permissions.sh`** — chequea antes del `terraform apply`
6. **Documento `IAM-REQUEST.md`** — para mandarle al área de cloud del cliente

## Mapeo de recursos Terraform → permisos GCP

### Storage (GCS)

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_storage_bucket` | `roles/storage.admin` | `storage.buckets.create`, `storage.buckets.get`, `storage.buckets.update`, `storage.buckets.delete`, `storage.buckets.getIamPolicy`, `storage.buckets.setIamPolicy` |
| `google_storage_bucket_object` | `roles/storage.objectAdmin` | `storage.objects.create`, `storage.objects.get`, `storage.objects.delete`, `storage.objects.update`, `storage.objects.list` |
| `google_storage_bucket_iam_*` | `roles/storage.admin` | `storage.buckets.getIamPolicy`, `storage.buckets.setIamPolicy` |

### Firestore / Datastore

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_firestore_database` | `roles/datastore.owner` | `datastore.databases.create`, `datastore.databases.get`, `datastore.databases.update`, `datastore.databases.delete`, `appengine.applications.create` (la primera vez) |
| `google_firestore_index` | `roles/datastore.indexAdmin` | `datastore.indexes.create`, `datastore.indexes.get`, `datastore.indexes.delete` |
| `google_firestore_document` | `roles/datastore.user` | `datastore.entities.create`, `datastore.entities.get`, `datastore.entities.update` |

### Secret Manager

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_secret_manager_secret` | `roles/secretmanager.admin` | `secretmanager.secrets.create`, `secretmanager.secrets.get`, `secretmanager.secrets.delete`, `secretmanager.secrets.update`, `secretmanager.secrets.getIamPolicy`, `secretmanager.secrets.setIamPolicy` |
| `google_secret_manager_secret_version` | `roles/secretmanager.admin` | `secretmanager.versions.add`, `secretmanager.versions.access`, `secretmanager.versions.disable`, `secretmanager.versions.destroy` |
| `google_secret_manager_secret_iam_*` | `roles/secretmanager.admin` | `secretmanager.secrets.getIamPolicy`, `secretmanager.secrets.setIamPolicy` |

### Cloud Run

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_cloud_run_v2_service` | `roles/run.admin` | `run.services.create`, `run.services.get`, `run.services.update`, `run.services.delete`, `run.services.getIamPolicy`, `run.services.setIamPolicy` |
| `google_cloud_run_v2_job` | `roles/run.admin` | `run.jobs.create`, `run.jobs.get`, `run.jobs.update`, `run.jobs.delete`, `run.jobs.run` |
| `google_cloud_run_service_iam_*` | `roles/run.admin` | `run.services.getIamPolicy`, `run.services.setIamPolicy` |

### Artifact Registry

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_artifact_registry_repository` | `roles/artifactregistry.admin` | `artifactregistry.repositories.create`, `artifactregistry.repositories.get`, `artifactregistry.repositories.delete`, `artifactregistry.repositories.update`, `artifactregistry.repositories.uploadArtifacts`, `artifactregistry.repositories.downloadArtifacts` |
| Push de imagen Docker | `roles/artifactregistry.writer` | `artifactregistry.repositories.uploadArtifacts` |

### Pub/Sub

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_pubsub_topic` | `roles/pubsub.admin` | `pubsub.topics.create`, `pubsub.topics.get`, `pubsub.topics.delete`, `pubsub.topics.publish` |
| `google_pubsub_subscription` | `roles/pubsub.admin` | `pubsub.subscriptions.create`, `pubsub.subscriptions.get`, `pubsub.subscriptions.delete`, `pubsub.subscriptions.consume` |

### Cloud Scheduler

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_cloud_scheduler_job` | `roles/cloudscheduler.admin` | `cloudscheduler.jobs.create`, `cloudscheduler.jobs.get`, `cloudscheduler.jobs.update`, `cloudscheduler.jobs.delete`, `cloudscheduler.jobs.run` |

### BigQuery

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_bigquery_dataset` | `roles/bigquery.dataOwner` | `bigquery.datasets.create`, `bigquery.datasets.get`, `bigquery.datasets.update`, `bigquery.datasets.delete` |
| `google_bigquery_table` | `roles/bigquery.dataEditor` | `bigquery.tables.create`, `bigquery.tables.get`, `bigquery.tables.update`, `bigquery.tables.delete`, `bigquery.tables.getData`, `bigquery.tables.updateData` |
| `google_bigquery_job` | `roles/bigquery.jobUser` | `bigquery.jobs.create` |

### IAM (siempre necesario para deploys que tocan service accounts)

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_service_account` | `roles/iam.serviceAccountAdmin` | `iam.serviceAccounts.create`, `iam.serviceAccounts.get`, `iam.serviceAccounts.delete`, `iam.serviceAccounts.update` |
| `google_service_account_key` | `roles/iam.serviceAccountKeyAdmin` | `iam.serviceAccountKeys.create`, `iam.serviceAccountKeys.get`, `iam.serviceAccountKeys.delete` |
| `google_project_iam_*` | `roles/resourcemanager.projectIamAdmin` | `resourcemanager.projects.getIamPolicy`, `resourcemanager.projects.setIamPolicy` |
| Cloud Run usa SA propia | `roles/iam.serviceAccountUser` | `iam.serviceAccounts.actAs` |

### Compute / VPC (si aplica)

| Recurso Terraform | Rol predefinido | Permisos atómicos |
|---|---|---|
| `google_compute_network` | `roles/compute.networkAdmin` | `compute.networks.*` |
| `google_compute_subnetwork` | `roles/compute.networkAdmin` | `compute.subnetworks.*` |
| `google_compute_firewall` | `roles/compute.securityAdmin` | `compute.firewalls.*` |
| `google_vpc_access_connector` | `roles/vpcaccess.admin` | `vpcaccess.connectors.*` |

### APIs habilitadas (siempre)

Antes de cualquier `apply` el admin debe habilitar las APIs. Permiso necesario para hacerlo:

| Acción | Rol predefinido | Permisos atómicos |
|---|---|---|
| Habilitar APIs | `roles/serviceusage.serviceUsageAdmin` | `serviceusage.services.enable`, `serviceusage.services.list` |

## Procedimiento de análisis (paso a paso)

### 1) Escanear el directorio de módulos

```bash
PROYECTO_TF_DIR=terraform/modules
grep -rhE "^resource\s+\"(google_|google-beta_)" $PROYECTO_TF_DIR/ \
  | sed -E 's/resource\s+"([^"]+)".*/\1/' \
  | sort -u
```

Esto da la lista única de tipos de recurso GCP usados.

### 2) Identificar también recursos en `environments/prod/`

```bash
grep -rhE "^resource\s+\"(google_|google-beta_)" terraform/environments/prod/ \
  | sed -E 's/resource\s+"([^"]+)".*/\1/' \
  | sort -u
```

### 3) Mapear cada recurso a permisos (usar la tabla de arriba)

### 4) Detectar APIs necesarias del proyecto

Cada recurso GCP requiere una API habilitada. Mapeo:

| Recurso | API a habilitar |
|---|---|
| `google_storage_bucket` | `storage.googleapis.com` |
| `google_firestore_database` | `firestore.googleapis.com` |
| `google_secret_manager_secret` | `secretmanager.googleapis.com` |
| `google_cloud_run_v2_service` | `run.googleapis.com` |
| `google_artifact_registry_repository` | `artifactregistry.googleapis.com` |
| `google_pubsub_topic` | `pubsub.googleapis.com` |
| `google_cloud_scheduler_job` | `cloudscheduler.googleapis.com` |
| `google_bigquery_*` | `bigquery.googleapis.com` |
| `google_service_account` | `iam.googleapis.com` |
| Cualquier IAM binding | `cloudresourcemanager.googleapis.com` |

### 5) Generar `IAM-REQUEST.md` para el cliente

Plantilla en `templates/IAM-REQUEST.md.tpl`. Estructura:

- Contexto del proyecto (qué se va a deployar)
- Service Account propuesta (nombre, email)
- APIs a habilitar
- Roles requeridos (con justificación de cada uno)
- Comandos `gcloud` listos para el admin
- Cómo validar (script `validate-permissions.sh`)

### 6) Generar `validate-permissions.sh`

Script bash que toma la SA y el proyecto, lista los permisos efectivos, y compara con la lista requerida. Si falta alguno, lo reporta con código de salida 1.

## Outputs ejemplo

### Output 1 — lista de roles predefinidos

```text
Roles requeridos para deployar farmacia-poc-gcp en producción:

✅ roles/storage.admin              — para crear/destruir bucket farmacia-poc-data
✅ roles/datastore.owner            — para crear database Firestore
✅ roles/secretmanager.admin        — para gestionar AI_API_KEY
✅ roles/run.admin                  — para deployar Cloud Run
✅ roles/artifactregistry.writer    — para push de imagen Docker
✅ roles/iam.serviceAccountUser     — para que Cloud Run use la SA runtime
✅ roles/serviceusage.serviceUsageAdmin  — para habilitar APIs (puede ser one-shot)
```

### Output 2 — comandos gcloud para el admin

```bash
PROJECT_ID="lan-copilot-prod"
SA_NAME="tf-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 1. Crear la service account
gcloud iam service-accounts create $SA_NAME \
  --display-name="Terraform Deployer" \
  --project=$PROJECT_ID

# 2. Habilitar APIs necesarias
gcloud services enable \
  storage.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  --project=$PROJECT_ID

# 3. Asignar roles a la SA
for ROLE in \
    roles/storage.admin \
    roles/datastore.owner \
    roles/secretmanager.admin \
    roles/run.admin \
    roles/artifactregistry.writer \
    roles/iam.serviceAccountUser
do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="$ROLE"
done

# 4. Generar key (opcional, si el deploy es desde un CI sin Workload Identity)
gcloud iam service-accounts keys create ~/tf-deployer-key.json \
  --iam-account=$SA_EMAIL
```

### Output 3 — Custom Role least privilege

Para áreas de cloud estrictas que prohíben roles predefinidos (porque dan demasiados permisos), generar custom role:

```yaml
# tf-deployer-custom-role.yaml
title: "Terraform Deployer - Farmacia PoC"
description: "Least privilege para deployar el stack farmacia-poc-gcp"
stage: "GA"
includedPermissions:
- storage.buckets.create
- storage.buckets.get
- storage.buckets.update
- storage.buckets.delete
- storage.buckets.getIamPolicy
- storage.buckets.setIamPolicy
- storage.objects.create
- storage.objects.get
- storage.objects.delete
- storage.objects.list
- datastore.databases.create
- datastore.databases.get
- datastore.databases.update
- secretmanager.secrets.create
- secretmanager.secrets.get
- secretmanager.secrets.delete
- secretmanager.versions.add
- secretmanager.versions.access
- secretmanager.versions.destroy
- run.services.create
- run.services.get
- run.services.update
- run.services.delete
- run.services.getIamPolicy
- run.services.setIamPolicy
- artifactregistry.repositories.uploadArtifacts
- artifactregistry.repositories.downloadArtifacts
- iam.serviceAccounts.actAs
- resourcemanager.projects.getIamPolicy
- serviceusage.services.enable
- serviceusage.services.list
```

Aplicar con:

```bash
gcloud iam roles create tfDeployerFarmacia \
  --project=$PROJECT_ID \
  --file=tf-deployer-custom-role.yaml

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="projects/${PROJECT_ID}/roles/tfDeployerFarmacia"
```

### Output 4 — script de validación pre-apply

```bash
#!/bin/bash
# validate-permissions.sh — chequea permisos antes de terraform apply
set -e

PROJECT_ID="${1:?Uso: $0 PROJECT_ID SA_EMAIL}"
SA_EMAIL="${2:?Uso: $0 PROJECT_ID SA_EMAIL}"

REQUIRED_PERMS=(
  storage.buckets.create
  storage.buckets.get
  datastore.databases.create
  secretmanager.secrets.create
  secretmanager.versions.add
  run.services.create
  artifactregistry.repositories.uploadArtifacts
  iam.serviceAccounts.actAs
  resourcemanager.projects.getIamPolicy
)

echo "🔍 Verificando permisos para ${SA_EMAIL} en ${PROJECT_ID}..."
echo

# Impersonar la SA para chequear sus permisos efectivos
RESULT=$(gcloud projects test-iam-permissions "$PROJECT_ID" \
  --permissions="$(IFS=,; echo "${REQUIRED_PERMS[*]}")" \
  --impersonate-service-account="$SA_EMAIL" \
  --format="value(permissions)" 2>/dev/null || true)

MISSING=()
for PERM in "${REQUIRED_PERMS[@]}"; do
  if echo "$RESULT" | tr ';' '\n' | grep -q "^${PERM}$"; then
    echo "✅ $PERM"
  else
    echo "❌ $PERM"
    MISSING+=("$PERM")
  fi
done

echo
if [ ${#MISSING[@]} -eq 0 ]; then
  echo "🎉 Todos los permisos OK. Listo para 'terraform apply'."
  exit 0
else
  echo "⚠️  Faltan ${#MISSING[@]} permisos. Pedir al admin GCP:"
  for P in "${MISSING[@]}"; do echo "  - $P"; done
  exit 1
fi
```

## Documento `IAM-REQUEST.md` para el cliente

Plantilla profesional para pedirle permisos al área de cloud del cliente. Estructura:

```markdown
# Request de IAM — {Proyecto} en {Cliente}

## Contexto

El equipo de Ingeniería de IA va a deployar **{Proyecto}** en el ambiente **{lan-copilot-prod | forestai-prod}** usando Terraform.

## Service Account propuesta

- **Nombre** — `tf-deployer`
- **Email** — `tf-deployer@{PROJECT_ID}.iam.gserviceaccount.com`
- **Propósito** — ejecutar `terraform apply` desde CI o estación de trabajo del desarrollador
- **Duración** — permanente (rota la key cada 90 días)

## APIs a habilitar

| API | Propósito |
|---|---|
| `storage.googleapis.com` | GCS para datasets |
| `firestore.googleapis.com` | Base de datos de aplicación |

## Roles solicitados

| Rol | Justificación |
|---|---|
| `roles/storage.admin` | Crear/destruir bucket de datos del proyecto |
| `roles/datastore.owner` | Inicializar y modificar Firestore |

## Comandos para el admin GCP

(Ver bloque gcloud arriba.)

## Validación

Después de aplicar los permisos, el equipo correrá `./scripts/validate-permissions.sh` y reportará al área de cloud el resultado antes del primer `terraform apply`.

## Política de seguridad

- La key de la SA se almacena en {Vault | GitHub Secrets | 1Password}
- Rotación cada 90 días
- Audit logs de Cloud Audit Logs habilitados
- Acceso de la SA solo a este proyecto (no a otros del cliente)
```

## Patrón típico LAN/LATAM

Cuando es para LAN o LATAM (cargar también `nelson-lan-airline-poc-stack`), el área de cloud suele ser:

- **Estricta** — custom role obligatorio, no roles predefinidos
- **Pide naming convention** — SA debe llamarse `sa-{aerolinea}-{proyecto}-{ambiente}`, ej `sa-latam-copilot-gov-prod`
- **Pide rotación de keys** — 90 días máximo, Workload Identity preferido sobre keys JSON
- **Pide audit** — Cloud Audit Logs activos para todos los recursos
- **Pide labels** — todos los recursos con `equipo=nelson`, `cliente=latam`, `proyecto={vertical}`, `cost-center={cc}`

Aplicar esto en el `IAM-REQUEST.md` cuando es LAN/LATAM.

## Workflow completo (10 minutos)

1. Cargar esta skill + abrir el repo del proyecto
2. Escanear `terraform/modules/` y `terraform/environments/prod/` con los comandos de arriba
3. Mapear cada recurso a su rol predefinido y permisos atómicos
4. Generar `IAM-REQUEST.md` con plantilla
5. Generar `validate-permissions.sh`
6. Generar `tf-deployer-custom-role.yaml` (si es least privilege)
7. Entregar todo al cliente
8. Cuando el admin lo aplica, correr `validate-permissions.sh` para confirmar
9. Ejecutar `terraform apply` con confianza

## Pitfalls

1. **`appengine.applications.create` para Firestore** — la primera vez que se crea Firestore en un proyecto, requiere permiso de App Engine también. Una vez creado, no se vuelve a pedir. Incluir en la lista solo si es proyecto nuevo.
2. **`iam.serviceAccounts.actAs` se olvida** — sin esto, Cloud Run no puede usar su SA runtime. Da error confuso ("permission denied" en deploy de Cloud Run sin decir cuál).
3. **APIs vs roles** — son cosas distintas. El admin necesita `serviceusage.serviceUsageAdmin` para habilitar APIs (one-shot), y la SA del deploy necesita los roles sobre los recursos.
4. **`gcloud projects test-iam-permissions` con `--impersonate-service-account`** — funciona si el caller tiene `iam.serviceAccountTokenCreator` sobre la SA. Si no, devuelve vacío. Diagnóstico — agregar `--log-http` para ver el 403.
5. **Workload Identity Federation** — si el cliente lo exige (LAN, enterprise), no se generan keys JSON. El IAM-REQUEST debe pedir configurar WIF entre GitHub/GitLab y GCP. Skill futura — `nelson-gcp-workload-identity`.
6. **Quotas** — los permisos no incluyen quotas. Si el deploy requiere quotas más altas (ej muchos buckets, mucho CPU en Cloud Run), pedirlas también en el IAM-REQUEST.
7. **Custom Role no se asigna directo** — el flow es 1) crear el custom role en el proyecto, 2) asignar el custom role a la SA. Dos comandos distintos.

## Referencias

- Skills relacionadas
  - `nelson-poc-gcp-terraform-template` — template base que usa esta skill
  - `nelson-deploy-gcp` — Cloud Run prod
  - `nelson-lan-airline-poc-stack` — request específico para LAN
  - `nelson-terraform-module-patterns` — patterns de los módulos analizados
- GCP IAM docs — https://cloud.google.com/iam/docs/understanding-roles
- gcloud test-iam-permissions — https://cloud.google.com/sdk/gcloud/reference/projects/test-iam-permissions
- Catálogo completo de permisos — https://cloud.google.com/iam/docs/permissions-reference
