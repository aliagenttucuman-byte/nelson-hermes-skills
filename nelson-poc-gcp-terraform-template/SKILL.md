---
name: nelson-poc-gcp-terraform-template
description: Plantilla maestra para arrancar PoCs nuevas del equipo Nelson sobre floci-gcp con Terraform. Un solo `terraform apply` levanta floci + backend FastAPI + frontend React + buckets/Firestore/Secrets. Reusable para farmacia, aerolíneas (LAN), ForestAI, Expreso Bisonte, cualquier vertical. Basada en el patrón validado en farmacia-poc-gcp (commit 53c9594, 2026-06-27). Carga esta skill cuando arrancás una PoC nueva que necesite GCP local + IaC.
when_to_use: Crear PoC nueva GCP local; bootstrap repo con Terraform + floci; replicar el patrón farmacia-poc-gcp; PoC LAN/LATAM (combinar con nelson-lan-airline-poc-stack).
---

# nelson-poc-gcp-terraform-template

Template maestro para PoCs del equipo Nelson. **Un solo `terraform apply`** orquesta floci-gcp + backend + frontend + recursos GCP locales (GCS, Firestore, Secret Manager) usando providers `kreuzwerker/docker` + `hashicorp/google` en paralelo.

## Cuándo usar esta skill

- Arrancás una PoC nueva para Nelson y necesita IA + persistencia + dashboard
- Querés replicar el patrón validado de `farmacia-poc-gcp`
- Cliente quiere ver IaC profesional (Terraform), no docker-compose suelto
- Vas a pasar de PoC local a Cloud Run real sin reescribir nada

**Para PoCs LAN/LATAM (aerolíneas):** cargar también `nelson-lan-airline-poc-stack` que extiende este template con datos BTS/OpenFlights, KPIs CASK/RASK, códigos IATA.

## Arquitectura objetivo

```
terraform apply
      │
      ├─ provider docker      → container floci-gcp:4588 + red + volumen
      ├─ null_resource        → wait healthcheck floci
      ├─ provider google      → bucket GCS + Firestore + Secret Manager (en floci)
      └─ provider docker      → build + run backend container :8030
                                    └─ mount frontend/dist read-only
```

Resultado: backend en `http://localhost:8030`, floci en `:4588`, bucket creado en floci via google provider.

## Estructura del repo

```
{proyecto}/
├── backend/
│   ├── main.py              FastAPI con endpoints + sirve frontend/dist en /
│   ├── gcp_adapters.py      Abstracción GCP (GCP_MODE=local|prod)
│   ├── requirements.txt     fastapi, uvicorn, google-cloud-*
│   ├── Dockerfile           python:3.12-slim, expone 8080
│   └── start.sh
├── frontend/
│   ├── src/                 React 18 + Vite + TS
│   └── dist/                Generado por `npm run build` (mount read-only)
├── terraform/
│   ├── modules/
│   │   ├── floci-docker/    Container floci + network + volumen
│   │   ├── backend-docker/  Build + run backend, triggers filemd5
│   │   ├── bucket-data/     google_storage_bucket
│   │   ├── firestore-collections/  DB (skip en local, floci ya la tiene)
│   │   └── secrets/         Secret Manager (AI_API_KEY)
│   └── environments/
│       ├── local-full/      ⭐ El que levanta TODO
│       ├── local/           Solo recursos GCP (sin containers, opcional)
│       └── prod/            Cloud Run + GCP real
├── docs/
│   ├── END-TO-END.md        Procedimiento real ejecutado con outputs
│   ├── DEPLOY.md            Local vs prod
│   ├── ARCHITECTURE.md      Decisiones técnicas
│   └── PITFALLS.md          Tropezones del stack
├── docker-compose.yml       Alternativa sin Terraform (debug)
├── Makefile                 up/down/build/frontend/tf-*/smoke
├── .env.example
├── .gitignore
└── README.md
```

## Procedimiento de bootstrap (15 minutos)

### 1) Crear repo nuevo

```bash
cd /home/server/proyectos
mkdir -p {proyecto}-gcp/{backend,frontend,terraform/{modules,environments/{local-full,prod}},docs,scripts}
cd {proyecto}-gcp
git init
```

### 2) Copiar template base desde farmacia-poc-gcp

```bash
SRC=/home/server/proyectos/farmacia-poc-gcp
DST=$(pwd)

# Backend skeleton
cp -r $SRC/backend/{gcp_adapters.py,requirements.txt,Dockerfile,start.sh} $DST/backend/
# main.py: copiar como base y adaptar endpoints al vertical
cp $SRC/backend/main.py $DST/backend/main.py

# Terraform modules (TODOS reusables sin tocar)
cp -r $SRC/terraform/modules/{floci-docker,backend-docker,bucket-data,firestore-collections,secrets} $DST/terraform/modules/

# Environment local-full (adaptar nombres de proyecto)
cp $SRC/terraform/environments/local-full/main.tf $DST/terraform/environments/local-full/main.tf

# Docs base
cp $SRC/docs/{DEPLOY.md,ARCHITECTURE.md,PITFALLS.md,END-TO-END.md} $DST/docs/

# Frontend: copiar estructura Vite
cp -r $SRC/frontend/{package.json,vite.config.ts,tsconfig.json,index.html,src} $DST/frontend/

# Tooling raíz
cp $SRC/{Makefile,docker-compose.yml,.env.example,.gitignore,README.md} $DST/
```

### 3) Adaptar al vertical

Buscar y reemplazar el nombre del proyecto en todos los archivos:

```bash
OLD=farmacia-poc
NEW={proyecto-nuevo}  # ej: lan-loadfactor-poc, forestai-monitoring, etc.

grep -rl "$OLD" --include="*.tf" --include="*.md" --include="*.yml" --include="*.json" \
  --include="Dockerfile*" --include="Makefile" --include="*.py" \
  | xargs sed -i "s/$OLD/$NEW/g"
```

### 4) Customizar lo que es específico del vertical

| Archivo | Qué cambiar |
|---|---|
| `backend/main.py` | Endpoints `/api/*`, datos mock, system prompt del chat |
| `frontend/src/` | Vistas del dashboard, KPIs, gráficos |
| `backend/gcp_adapters.py` | NO TOCAR (es genérico) |
| `terraform/modules/*` | NO TOCAR (son genéricos) |
| `terraform/environments/local-full/main.tf` | Nombre del bucket, secrets, project_id |
| `docs/END-TO-END.md` | Re-ejecutar con outputs del nuevo proyecto |

### 5) Build + apply

```bash
cd frontend && npm install && npm run build && cd ..
cd terraform/environments/local-full
terraform init && terraform apply -auto-approve
```

Outputs esperados:

```
backend_url = "http://localhost:8030"
bucket_url  = "gs://{proyecto}-data"
floci_url   = "http://localhost:4588"
Apply complete! Resources: 8 added.
```

### 6) Smoke test obligatorio

```bash
curl -s http://localhost:8030/api/health   # gcp_mode=local, project=floci-local
curl -s http://localhost:8030/api/kpis     # datos del vertical
curl -s http://localhost:4588/health        # floci con servicios running
curl -s "http://localhost:4588/storage/v1/b?project=floci-local" | python3 -m json.tool  # bucket creado
```

### 7) Repo en GitHub

```bash
gh repo create aliagenttucuman-byte/{proyecto}-gcp --private --source=. --remote=origin --push
```

## Componentes clave del template

### gcp_adapters.py (NO TOCAR — capa de abstracción)

```python
# GCP_MODE=local → AnonymousCredentials + custom endpoints a floci
# GCP_MODE=prod  → ADC + googleapis.com
def get_firestore_client(): ...
def get_storage_client(): ...
def get_secret(secret_id): ...
```

Cambiar la variable de entorno `GCP_MODE` es lo único que separa local de prod. Cero cambios de código.

### Módulo `floci-docker` (reusable)

- Pulla imagen `floci/floci-gcp:latest`
- Crea red `{proyecto}-net`
- Crea volumen persistente
- Expone puerto 4588
- Healthcheck container

### Módulo `backend-docker` (reusable)

- `docker_image` con `triggers` `filemd5()` sobre `main.py`, `gcp_adapters.py`, `requirements.txt`, `Dockerfile`
- Mount `frontend/dist` read-only
- Inyecta env vars: `GCP_MODE=local`, `FIRESTORE_HOST=floci-gcp:4588`, `STORAGE_HOST=http://floci-gcp:4588`
- Network = la del floci

### `null_resource.wait_for_floci` (crítico)

```hcl
provisioner "local-exec" {
  command = <<-EOT
    for i in $(seq 1 30); do
      curl -sf http://localhost:4588/health && exit 0
      sleep 2
    done
    exit 1
  EOT
}
```

Sin esto, el provider google intenta crear el bucket antes de que floci escuche. **Es el bug #1 si lo omitís.**

### Environment `local-full/main.tf`

Doble provider:

```hcl
provider "docker" {}  # sin config, daemon local

provider "google" {
  project     = "floci-local"
  credentials = jsonencode({type = "authorized_user"})
  storage_custom_endpoint   = "http://localhost:4588/"
  firestore_custom_endpoint = "http://localhost:4588/"
  # ...
}
```

Orden de dependencias:

```
floci-docker → null_resource → google_storage_bucket → backend-docker
```

## Puertos estándar del equipo (no chocar)

| Servicio | Puerto |
|---|---|
| floci-gcp | 4588 |
| Backend FastAPI | 8030 |
| FreeLLMAPI | 3101 |
| ai-server WhatsApp Gateway | 3001 |
| n8n | 5678 |
| Frontend dev Vite (si separado) | 5173 |

**Si vas a correr múltiples PoCs en paralelo:** cambiá puerto backend (8031, 8032...) y puerto floci (4589, 4590...) en `local-full/main.tf`.

## Para LAN/LATAM (aerolíneas) específicamente

Cuando Nelson dice "PoC para LAN", cargar también:
- `nelson-lan-airline-poc-stack` (datos BTS, KPIs CASK/RASK, IATA codes)
- `nelson-airline-bts-dataset` (descarga + parquet)
- `nelson-airline-delay-prediction` o el modelo que aplique

El template base sigue siendo este. LAN solo cambia:
- Dataset mock en `/api/kpis` → métricas de aerolíneas
- System prompt del chat → contexto operaciones aéreas
- Bucket → almacena parquet de vuelos

## Pasaje a producción GCP real

Cambiás solo el environment:

```bash
cd terraform/environments/prod
cp terraform.tfvars.example terraform.tfvars
# editar project_id, region, billing_account
gcloud auth application-default login
terraform init && terraform apply
```

Los **mismos módulos** `bucket-data`, `firestore-collections`, `secrets` corren contra GCP real. El módulo `cloud-run-backend` reemplaza a `backend-docker`. Cero reescritura.

## Pitfalls del template (descubiertos en farmacia-poc-gcp)

1. **Puerto 4588 ocupado:** Si tenés floci standalone de otro proyecto, `docker stop floci-gcp && docker rm floci-gcp` antes del apply.
2. **Frontend sin buildear:** Olvidás `npm run build` → backend levanta pero `/` da 404. Hacé el build ANTES del apply.
3. **`provider google` antes de floci:** Sin `null_resource.wait_for_floci`, el bucket falla al crear. NO LO OMITAS.
4. **FreeLLMAPI no responde:** Si el proceso host en :3101 está muerto, el chat tira error pero KPIs/data funcionan. No bloquea deploy.
5. **`vite: command not found`:** Si copiaste `node_modules` roto, `rm -rf node_modules && npm install`.
6. **State `local` vs `local-full`:** Si tenés state en `local/` con solo el bucket, NO mezclar con `local-full/`. Son environments separados a propósito.
7. **Backend no reconstruye tras cambios:** Verificar que `triggers` en `backend-docker/main.tf` tenga `filemd5("../../../backend/main.py")` con la ruta relativa correcta.

## Referencias

- Repo de referencia: https://github.com/aliagenttucuman-byte/farmacia-poc-gcp
- Commit del template validado: `53c9594` (2026-06-27)
- Skills relacionadas:
  - `nelson-floci-gcp` — operación del emulador
  - `nelson-gcp-floci-terraform` — fundamentos del patrón
  - `nelson-lan-airline-poc-stack` — extensión para aerolíneas
  - `nelson-terraform-module-patterns` — patterns reusables
  - `nelson-deploy-gcp` — Cloud Run prod
