---
name: nelson-terraform-module-patterns
description: Patterns reusables de Terraform validados en farmacia-poc-gcp (commit 53c9594). Doble provider (kreuzwerker/docker + hashicorp/google), null_resource healthcheck para ordenar dependencies, filemd5 triggers para auto-rebuild de imágenes, environments local-full vs prod sin reescribir módulos, force_destroy condicional. Carga esta skill cuando escribís módulos TF nuevos para el equipo Nelson o auditás los existentes.
when_to_use: Escribir módulo Terraform nuevo; entender por qué falla el orden de creación de recursos; agregar healthcheck previo a un provider; auto-rebuild de imagen al cambiar código; reusar módulos en local vs prod.
---

# nelson-terraform-module-patterns

Catálogo de **patterns Terraform** descubiertos y validados en el deploy de farmacia-poc-gcp. Cada pattern viene con código real, el problema que resuelve, y dónde NO usarlo.

## Pattern 1 — Doble provider (Docker + Google) en el mismo apply

**Problema:** Querés que un solo `terraform apply` levante containers (docker daemon) **y** recursos GCP (en floci o real).

**Solución:**

```hcl
terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
    google = { source = "hashicorp/google",   version = "~> 5.0" }
  }
}

# Provider docker: sin config, usa /var/run/docker.sock
provider "docker" {}

# Provider google: con custom_endpoints apuntando a floci en local
provider "google" {
  project     = "floci-local"
  credentials = jsonencode({ type = "authorized_user" })
  
  storage_custom_endpoint        = "http://localhost:4588/"
  firestore_custom_endpoint      = "http://localhost:4588/"
  secret_manager_custom_endpoint = "http://localhost:4588/"
  cloud_run_v2_custom_endpoint   = "http://localhost:4588/"
}
```

En `environments/prod/main.tf`, el provider google es estándar (sin custom_endpoints, con ADC):

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
  # credenciales via ADC
}
```

**Donde NO usarlo:** si el proyecto es 100% cloud, no necesitás `kreuzwerker/docker`.

## Pattern 2 — `null_resource` healthcheck para ordenar providers

**Problema:** Terraform crea recursos en paralelo. El `provider google` intenta crear el bucket en floci **antes** de que el container floci-gcp esté escuchando en :4588. Falla.

**Solución:**

```hcl
module "floci" {
  source = "../../modules/floci-docker"
  # crea el container floci
}

resource "null_resource" "wait_for_floci" {
  depends_on = [module.floci]
  
  provisioner "local-exec" {
    command = <<-EOT
      echo "Esperando a que floci-gcp esté healthy..."
      for i in $(seq 1 30); do
        if curl -sf http://localhost:4588/health > /dev/null; then
          echo "✅ floci-gcp listo (intento $i)"
          exit 0
        fi
        sleep 2
      done
      echo "❌ floci-gcp no respondió en 60s"
      exit 1
    EOT
  }
  
  triggers = {
    floci_container_id = module.floci.container_id  # re-corre si floci se recrea
  }
}

module "bucket_data" {
  source     = "../../modules/bucket-data"
  depends_on = [null_resource.wait_for_floci]   # ⭐ acá la magia
  # ...
}
```

**Por qué funciona:** `depends_on` fuerza el orden. Sin esto, Terraform paraleliza y rompe.

**Donde NO usarlo:** si el provider tiene healthcheck nativo (no es el caso de google con custom_endpoints).

## Pattern 3 — `filemd5()` triggers para rebuild automático

**Problema:** Cambiás `backend/main.py`, querés que el próximo `terraform apply` re-buildee la imagen y reemplace el container. Sin trigger, Terraform no se da cuenta.

**Solución:**

```hcl
resource "docker_image" "backend" {
  name = "farmacia-poc-backend:latest"
  
  build {
    context    = "${path.module}/../../../backend"
    dockerfile = "Dockerfile"
    tag        = ["farmacia-poc-backend:latest"]
  }
  
  triggers = {
    main_py         = filemd5("${path.module}/../../../backend/main.py")
    gcp_adapters_py = filemd5("${path.module}/../../../backend/gcp_adapters.py")
    requirements    = filemd5("${path.module}/../../../backend/requirements.txt")
    dockerfile      = filemd5("${path.module}/../../../backend/Dockerfile")
  }
}

resource "docker_container" "backend" {
  image = docker_image.backend.image_id   # ⭐ cambia cuando la imagen cambia
  name  = "farmacia-poc-backend"
  # ...
}
```

**Por qué funciona:** `image_id` cambia cuando `triggers` detecta cambio en cualquier archivo → Terraform recrea el container.

**Donde NO usarlo:** si tu backend está en Cloud Run con CI/CD vía gcloud builds, ahí el trigger es el push a git, no `filemd5`.

## Pattern 4 — Environments `local-full` vs `prod` sin duplicar módulos

**Problema:** Querés probar local y deployar a prod sin mantener dos sets de módulos.

**Solución:** Estructura

```
terraform/
├── modules/           ⭐ Módulos PURAMENTE reusables, sin asumir env
│   ├── bucket-data/
│   ├── firestore-collections/
│   ├── secrets/
│   ├── cloud-run-backend/   (solo para prod, no se usa en local)
│   ├── floci-docker/        (solo para local, no se usa en prod)
│   └── backend-docker/      (solo para local, no se usa en prod)
└── environments/
    ├── local-full/
    │   └── main.tf    # llama: floci-docker + null_resource + bucket + backend-docker
    ├── local/
    │   └── main.tf    # llama: solo bucket + secrets (sin containers)
    └── prod/
        └── main.tf    # llama: bucket + firestore + secrets + cloud-run-backend
```

Los módulos `bucket-data`, `firestore-collections`, `secrets` son **idénticos** entre local y prod. Los providers (custom_endpoint o no) los inyecta el environment.

**Donde NO usarlo:** si tu prod es completamente distinto (otro cloud), ahí sí dividir.

## Pattern 5 — `force_destroy` condicional por environment

**Problema:** En local querés `terraform destroy` que borre todo. En prod querés que falle si el bucket tiene datos.

**Solución en el módulo:**

```hcl
# modules/bucket-data/variables.tf
variable "force_destroy" {
  type    = bool
  default = false
}

# modules/bucket-data/main.tf
resource "google_storage_bucket" "data" {
  name          = var.name
  location      = var.location
  force_destroy = var.force_destroy   # ⭐
  
  versioning { enabled = true }
}
```

En el environment:

```hcl
# environments/local-full/main.tf
module "bucket_data" {
  source        = "../../modules/bucket-data"
  force_destroy = true   # local: ok borrar
}

# environments/prod/main.tf
module "bucket_data" {
  source        = "../../modules/bucket-data"
  force_destroy = false  # prod: protegido
}
```

## Pattern 6 — Mount bind-only para frontend buildeado

**Problema:** Frontend React se buildea fuera de Terraform (`npm run build`). Querés que el backend sirva el `dist/` sin meterlo en la imagen Docker.

**Solución:**

```hcl
resource "docker_container" "backend" {
  name  = "farmacia-poc-backend"
  image = docker_image.backend.image_id
  
  mounts {
    type     = "bind"
    target   = "/app/frontend/dist"
    source   = abspath("${path.module}/../../../frontend/dist")
    read_only = true
  }
  
  # ...
}
```

Backend FastAPI:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="/app/frontend/dist", html=True), name="frontend")
```

**Ventaja:** rebuild de imagen del backend no requiere rebuild del frontend, y viceversa.

**Donde NO usarlo:** en prod en Cloud Run el bind mount no funciona. Ahí copiás `dist/` dentro de la imagen en el Dockerfile.

## Pattern 7 — Outputs útiles del environment

Siempre exportar las URLs reales para que el usuario las copie:

```hcl
# environments/local-full/outputs.tf
output "backend_url" {
  value       = "http://localhost:${var.backend_port}"
  description = "Dashboard + API"
}

output "floci_url" {
  value       = "http://localhost:4588"
  description = "Emulador GCP"
}

output "bucket_url" {
  value       = "gs://${module.bucket_data.bucket_name}"
  description = "Bucket GCS en floci"
}
```

Tras el apply:

```
backend_url = "http://localhost:8030"
bucket_url  = "gs://farmacia-poc-data"
floci_url   = "http://localhost:4588"
```

Nelson ve la URL y entra al toque.

## Pattern 8 — `labels` consistentes (cost tracking)

Todo recurso GCP del equipo Nelson debe tener:

```hcl
labels = {
  equipo   = "nelson"
  proyecto = var.proyecto      # "farmacia-poc"
  stack    = "gcp-floci"        # o "gcp-prod"
  cliente  = var.cliente        # opcional: "lan", "forestai", "expreso-bisonte"
}
```

En prod permite filtrar costos en Billing Reports por proyecto/cliente.

## Pattern 9 — Network compartida por nombre

**Problema:** Backend y floci están en containers separados. Necesitan comunicarse por nombre, no por IP.

**Solución:**

```hcl
# modules/floci-docker/main.tf
resource "docker_network" "net" {
  name   = "${var.proyecto}-net"
  driver = "bridge"
}

resource "docker_container" "floci_gcp" {
  name     = "${var.proyecto}-floci-gcp"
  networks_advanced { name = docker_network.net.name }
}

# modules/backend-docker/main.tf (recibe network_name como variable)
resource "docker_container" "backend" {
  name = "${var.proyecto}-backend"
  networks_advanced { name = var.network_name }
  
  env = [
    "FIRESTORE_HOST=${var.floci_container_name}:4588",  # resuelve por DNS interno docker
  ]
}
```

En el environment:

```hcl
module "backend" {
  source                = "../../modules/backend-docker"
  network_name          = module.floci.network_name
  floci_container_name  = module.floci.container_name
  depends_on            = [null_resource.wait_for_floci]
}
```

**Beneficio:** backend usa `floci-gcp:4588` (no `localhost:4588`), no se rompe si cambia el puerto host.

## Pattern 10 — `terraform fmt` + `terraform validate` en pre-commit

Agregar a `.git/hooks/pre-commit` (o usar pre-commit framework):

```bash
#!/bin/bash
find terraform -name "*.tf" | while read f; do
  terraform fmt "$f" || exit 1
done

cd terraform/environments/local-full
terraform validate || exit 1
```

Evita commits con TF inválido o sin formatear.

## Anti-patterns (NO HACER)

### ❌ `count` y `for_each` mezclados en el mismo módulo

Difícil de razonar. Usar uno u otro por recurso, no ambos.

### ❌ `provisioner "local-exec"` para lógica de negocio

Solo para healthchecks y setup mínimo. Si necesitás "lógica", usá `external` data source o sacalo de Terraform.

### ❌ Hardcodear `floci-local` como project_id en módulos

Pasarlo como variable. Que el environment decida.

### ❌ Olvidarte de `depends_on` con providers cruzados

Terraform NO sabe que `provider google` necesita que el container `provider docker` esté listo. Vos se lo decís.

### ❌ State compartido entre `local-full` y `prod`

NUNCA. Cada environment con su backend de state separado. Local puede ser local (`terraform.tfstate`), prod debería ir a GCS:

```hcl
# environments/prod/backend.tf
terraform {
  backend "gcs" {
    bucket = "lan-tfstate"
    prefix = "lan-copilot-gov-poc"
  }
}
```

## Validación rápida de un módulo nuevo

Checklist antes de mergear:

- [ ] Variables tipadas con `type` y `description`
- [ ] Outputs con `description`
- [ ] `terraform fmt` clean
- [ ] `terraform validate` OK
- [ ] Funciona en `local-full` (apply + destroy completo)
- [ ] Tiene labels estándar
- [ ] Si crea recursos cloud, soporta `force_destroy` variable
- [ ] README.md del módulo con un ejemplo de uso

## Referencias

- Template base: `nelson-poc-gcp-terraform-template`
- Floci-gcp: `nelson-floci-gcp`
- GCP Terraform fundamentals: `nelson-gcp-floci-terraform`, `nelson-gcp-terraform`
- Repo de referencia: https://github.com/aliagenttucuman-byte/farmacia-poc-gcp
- Commit con todos estos patterns aplicados: `53c9594`
