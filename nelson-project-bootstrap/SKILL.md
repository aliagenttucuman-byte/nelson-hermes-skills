---
name: nelson-project-bootstrap
title: Project Bootstrap - Scaffold completo de nuevo proyecto
description: Skill maestra para crear nuevos proyectos del equipo Nelson. Genera scaffold completo backend+frontend+devops desde cero usando todas las skills del equipo.
skill: nelson-project-bootstrap
author: equipo-nelson
version: 1.0.0
keywords: [bootstrap, scaffold, template, new-project, generator]
dependencies: [equipo-nelson, nelson-project-constitution, nelson-spec-driven-workflow, spec-driven-development, nelson-frontend-stack, nelson-database, nelson-security, nelson-code-quality, nelson-ci-cd, nelson-observability, nelson-deploy-gcp, nelson-frontend-testing, nelson-spec-analyzer]
---

# Project Bootstrap - Equipo Nelson

> Crear un proyecto completo en minutos. Solo necesitas un nombre y una idea.

## Template GitHub

El template base esta publico en:
**https://github.com/aliagenttucuman-byte/nelson-template**

## Scripts incluidos

- `scripts/nelson-new-project.py` — Agente automatico de bootstrap. Clona template, inicializa git, ajusta nombres, crea .env.

## Regla de Oro del Stack

- **Backend:** Siempre **Python**
- **Frontend:** Siempre **React**

El lenguaje y framework base son **innegociables** para todos los equipos (Central e I+D+I). Lo que puede variar son librerías y frameworks *dentro* de ese stack.

## Flujo de Bootstrap (actualizado 2026-05-14)

```
FASE 0: Tony dice "Nuevo proyecto"
    ↓
FASE 1: `nelson-project-constitution` → Crear CONSTITUTION.md
    ↓
FASE 2: `spec-driven-development` → Escribir OpenAPI spec
    ↓
FASE 3: Clarificar con Tony
    ↓
FASE 4: `writing-plans` → Plan técnico
    ↓
FASE 5: `nelson-spec-analyzer` → Revisar coherencia
    ↓
FASE 6: `subagent-driven-development` → Breakdown de tareas
    ↓
FASE 7: `requesting-code-review` → Checklist de calidad
    ↓
FASE 8: Implementar con agentes (Beto, Ricky, Nico, Diego, Alma)
    ↓
DONE: Proyecto en producción
```

**Gobernado por:** `nelson-spec-driven-workflow` (skill maestra del flujo SDD completo)

## Como usar

### Modo automatico (recomendado)

```bash
# Tony dice: "Necesito un proyecto para gestion de inventario"
# Ejecutar:
nelson-new-project "Gestion de Inventario"

# Listo. El agente hace TODO solo:
# 1. Clona el template desde GitHub
# 2. Renombra la carpeta
# 3. Inicializa git nuevo
# 4. Ajusta nombres en archivos
# 5. Crea .env desde .env.example
# 6. Commits iniciales
# 7. Te dice donde esta y como levantarlo
```

### Manual (si queres control total)

```bash
# 1. Clonar template
git clone https://github.com/aliagenttucuman-byte/nelson-template.git mi-proyecto

# 2. Inicializar como proyecto nuevo
cd mi-proyecto
rm -rf .git
git init
git add -A
git commit -m "init: mi-proyecto"

# 3. Configurar
cp .env.example .env

# 4. Levantar
docker compose up --build -d
```

## Que hace el agente automatico

```bash
$ nelson-new-project "Chat con Documentos"

📦 Clonando template para 'Chat con Documentos'...
🔄 Inicializando git...
⚙️  Configurando proyecto...

✅ Proyecto 'Chat con Documentos' creado en: /home/server/proyectos/chat-con-documentos

📁 Estructura:
   Backend:  /home/server/proyectos/chat-con-documentos/backend
   Frontend: /home/server/proyectos/chat-con-documentos/frontend
   Specs:    /home/server/proyectos/chat-con-documentos/specs

🚀 Para levantar:
   cd /home/server/proyectos/chat-con-documentos
   docker compose up --build -d

📋 URLs:
   API Docs: http://localhost:8000/docs
   Frontend: http://localhost:8080
```

## Estructura generada (template actualizado 2026-05-11)

```
{project-name}/
├── backend/              # FastAPI + Python 3.12
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/       # Endpoints REST (auth, health, etc)
│   │   │   └── deps.py   # get_db, get_current_user, oauth2
│   │   ├── core/
│   │   │   ├── config.py     # pydantic-settings, .env
│   │   │   ├── logging.py    # structlog JSON
│   │   │   └── security.py   # bcrypt, JWT encode/decode
│   │   ├── models/
│   │   │   ├── base.py       # DeclarativeBase + TimestampMixin
│   │   │   └── user.py       # User model
│   │   ├── schemas/
│   │   │   ├── user.py       # UserCreate, UserOut (Pydantic)
│   │   │   └── auth.py       # Token, LoginRequest schemas
│   │   ├── repositories/
│   │   │   └── base.py       # BaseRepository generico
│   │   ├── services/         # Logica de negocio
│   │   ├── tasks/            # Background jobs (Celery)
│   │   ├── tests/
│   │   │   └── conftest.py   # Fixtures pytest
│   │   └── main.py           # FastAPI app, CORS, routers
│   ├── alembic/              # Migraciones DB
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── Dockerfile            # Multistage python:3.12-slim
│   ├── pyproject.toml        # Ruff + mypy + pytest config
│   └── alembic.ini
├── frontend/             # React 19 + Vite 6 + Tailwind 4
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts     # Axios instance con interceptores
│   │   ├── components/
│   │   │   ├── ui/           # Button, Input, etc
│   │   │   └── layout/       # Layout, Navbar, Sidebar
│   │   ├── hooks/
│   │   │   └── useAuth.ts    # React Query hooks
│   │   ├── lib/
│   │   │   └── utils.ts      # cn() utility
│   │   ├── pages/
│   │   │   └── HomePage.tsx  # Rutas principales
│   │   ├── context/          # AuthContext, ThemeContext
│   │   ├── types/
│   │   │   └── index.ts      # Tipos compartidos
│   │   ├── test/
│   │   │   └── mocks/        # MSW handlers
│   │   ├── App.tsx
│   │   ├── main.tsx          # React Query + Router setup
│   │   ├── index.css         # Tailwind 4: @import "tailwindcss"
│   │   └── vite-env.d.ts
│   ├── e2e/
│   │   └── example.spec.ts   # Playwright E2E
│   ├── Dockerfile            # Multistage node:22 + nginx
│   ├── nginx.conf            # Proxy /api al backend
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── specs/                # OpenAPI specs
│   ├── openapi.yaml          # Spec base con health + auth
│   ├── schemas/
│   └── paths/
├── scripts/              # Scripts de utilidad
│   ├── bootstrap.sh          # Setup completo automatizado
│   └── setup-ollama.sh       # Descarga modelos Ollama
├── docker/               # Config extra Docker
├── .github/
│   └── workflows/
│       └── ci.yml            # Lint + Test + Build + Deploy
├── docker-compose.yml    # Backend + Frontend + DB + Redis + Qdrant
├── .env.example
├── .pre-commit-config.yaml
├── .gitignore
└── README.md             # Quick start, stack, URLs
```
```

## Referencias adicionales

- `references/integrating-new-tools.md` — Patrón probado para evaluar e integrar herramientas nuevas al stack (investigar → comparar → integrar → sync). Basado en integraciones de robotocore y Docling.
- `references/windows-python-path.md` — Fix para Python Microsoft Store en Windows
- `references/web-search-docker-pitfall.md` — DuckDuckGo rate-limit desde containers Docker
- `references/minio-s3-local.md` — Alternativa liviana a floci/localstack para S3 local

## Archivos generados automaticamente

### backend/pyproject.toml

```toml
[project]
name = "{project-name}"
version = "0.1.0"
description = "{project-description}"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "pydantic[email]>=2.9",
    "pydantic-settings>=2.6",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "alembic>=1.13",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "structlog>=24.4",
    "python-multipart>=0.0.17",
    "python-dotenv>=1.0",
    "qdrant-client>=1.12",
    "openai>=1.54",
    "ollama>=0.4",
    "redis>=5.2",
    "celery>=5.4",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "ruff>=0.9",
    "mypy>=1.14",
    "pre-commit>=4.1",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "TCH", "PTH", "RUF"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["app/tests"]
asyncio_mode = "auto"
```

### frontend/package.json (resumen)

```json
{
  "name": "{project-name}-frontend",
  "version": "0.1.0",
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.1.0",
    "@tanstack/react-query": "^5.64.0",
    "axios": "^1.7.0",
    "tailwindcss": "^4.0.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "vitest": "^3.0.0",
    "@playwright/test": "^1.50.0",
    "@testing-library/react": "^16.2.0"
  }
}
```

### docker-compose.yml (con Redis + Qdrant)

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://nelson:secret@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_HOST=qdrant
      - LLM_PROVIDER=ollama
      - LLM_MODEL=llama3.2:3b
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
      - qdrant
    networks:
      - app-net

  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - backend
    networks:
      - app-net

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: nelson
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - app-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-net

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - app-net

volumes:
  pgdata:
  qdrant_storage:

networks:
  app-net:
    driver: bridge
```

## Flujo de Bootstrap

```bash
# 1. Nelson dice el nombre y descripcion del proyecto
# 2. Hermes ejecuta esta skill
# 3. Se genera toda la estructura de carpetas y archivos
# 4. Se instalan dependencias (pip install, npm install)
# 5. Se inicializa git y se hace primer commit
# 6. Se levanta docker-compose para verificar
# 7. Se muestra URL de health check y frontend
```

## Scripts de utilidad incluidos

### scripts/bootstrap.sh
Setup completo automatizado:
```bash
#!/bin/bash
set -e
echo "🚀 Bootstrap del proyecto"
cp .env.example .env
cd backend && pip install -e ".[dev]" && cd ..
cd frontend && npm install && cd ..
pre-commit install || echo "pre-commit no instalado, saltando"
docker compose up --build -d
echo "✅ Listo! API: http://localhost:8000/docs | Frontend: http://localhost:8080"
```

### scripts/setup-ollama.sh
Descarga modelos recomendados segun VRAM:
```bash
#!/bin/bash
ollama pull llama3.2:3b   # 4GB VRAM - chat general
ollama pull qwen2.5:3b    # 4GB VRAM - codigo
ollama pull nomic-embed-text  # embeddings
ollama pull llama3.1:8b   # 6GB+ VRAM - calidad
ollama pull llava:7b      # vision/multimodal
```

## Comando para bootstrap

```bash
# Ejecutado por Hermes automaticamente
cd ~
mkdir -p {project-name}
cd {project-name}

# Generar todos los archivos...

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic init alembic

# Frontend
cd ../frontend
npm install

# Git
cd ..
git init
git add .
git commit -m "feat: bootstrap proyecto {project-name}"

# Docker
docker compose up --build -d
```

## Skills involucradas en el bootstrap

| Orden | Skill | Que aporta |
|-------|-------|-----------|
| 0 | `nelson-spec-driven-workflow` | Flujo maestro SDD de 8 fases |
| 1 | `nelson-project-constitution` | Principios, stack, reglas del proyecto |
| 2 | `equipo-nelson` | Define roles y responsabilidades |
| 3 | `spec-driven-development` | Estructura specs/ y OpenAPI base |
| 4 | `nelson-spec-analyzer` | Revisa coherencia spec vs plan |
| 5 | `nelson-database` | Models, SQLAlchemy, Alembic setup |
| 6 | `nelson-security` | Auth JWT, middleware, deps |
| 7 | `nelson-frontend-stack` | React 19, Vite 6, Tailwind 4 |
| 8 | `nelson-code-quality` | Ruff, mypy, pre-commit config |
| 9 | `nelson-frontend-testing` | Vitest, Playwright setup |
| 10 | `nelson-observability` | Logging, health, metrics |
| 11 | `nelson-ci-cd` | GitHub Actions workflows |
| 12 | `nelson-deploy-gcp` | Config de deploy lista |
| 13 | `docker-management` | Dockerfiles y compose |
| 14 | `api-design-principles` | Convenciones de API |
| 15 | `python-testing-patterns` | Tests backend |
| 16 | `nelson-embeddings` | Servicio de embeddings |
| 17 | `nelson-vector-databases` | Qdrant config |
| 18 | `nelson-rag-pipeline` | Pipeline RAG completa |
| 19 | `nelson-llm-generation` | LLM streaming, OpenAI/Ollama |
| 20 | `nelson-document-processing` | PDF/Word parsing |
| 21 | `nelson-background-jobs` | Celery + Redis async |
| 22 | `nelson-ai-vision` | OCR, image analytics |
| 23 | `nelson-ai-agents` | Agentes autonomos con herramientas |
| 24 | `nelson-senior-practices` | Type hints estrictos, clean code, SOLID |
| 25 | `nelson-documentation` | README, API docs, MkDocs |
| 26 | `nelson-data-science` | ML, XGBoost, Optuna, feature engineering |

## Checklist post-bootstrap

- [ ] `CONSTITUTION.md` creado y aprobado por Tony (Fase 1)
- [ ] `docker compose up --build -d` levanta sin errores
- [ ] `curl http://localhost:8000/api/v1/health` devuelve OK
- [ ] Frontend accesible en `http://localhost:8080`
- [ ] API Docs en `http://localhost:8000/docs`
- [ ] Qdrant Dashboard en `http://localhost:6333/dashboard`
- [ ] Login/register funcionan (endpoints auth)
- [ ] Tests backend pasan: `cd backend && pytest`
- [ ] Tests frontend pasan: `cd frontend && npm run test -- --run`
- [ ] Pre-commit hooks instalados: `pre-commit install`
- [ ] Repo Git inicializado con primer commit
- [ ] `.env` creado desde `.env.example`
- [ ] Modelos Ollama descargados (opcional): `./scripts/setup-ollama.sh`

## Pitfalls

## Pitfalls

- **`zip` binary no disponible en el servidor:** Usar siempre `python3 -c "import zipfile, os; ..."` para comprimir. Patrón: `with zipfile.ZipFile('out.zip', 'w', zipfile.ZIP_DEFLATED) as zf: [zf.write(f, arcname) for f in files]`.
- No olvidar crear `.env` real desde `.env.example` despues del bootstrap
- Si el puerto 8000 o 8080 estan ocupados, cambiar en docker-compose.yml. El servidor ya tiene ocupados: 8000 (rag-poc), 8001, 8002, 5678 (n8n). Usar 8010+ para proyectos nuevos.
- Alembic necesita `DATABASE_URL` seteada para crear la primera migracion
- En Windows, los paths de volumen en docker-compose pueden necesitar ajustes
- **Subagents miscalculate `Path(__file__).parent` depth in nested routers:** When a subagent creates `backend/routers/modules.py`, correct traversal to `backend/data/` is `.parent.parent / "data"` (routers/ → backend/ → data/). Subagents consistently generate `.parent.parent.parent` (one extra level). Always verify DATA_DIR paths post-subagent. Sanity check: count `.parent` calls vs directory depth.
- **Windows + Python Microsoft Store:** `pip install` no agrega Scripts al PATH. Si `comando` no se encuentra, usar `python -m comando` o agregar manualmente: `C:\\Users\\<Usuario>\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.12_...\\LocalCache\\local-packages\\Python312\\Scripts`. Ver referencia `references/windows-python-path.md`.
- Tailwind 4 no usa `tailwind.config.js`; la config va en CSS con `@theme`
- Para 4GB VRAM, usar `llama3.2:3b` o `qwen2.5:3b` en dev (entran enteros en GPU)
- Para modelos grandes (>4GB), Ollama usa mix CPU/GPU automaticamente
- **S3 local:** Si floci/localstack fallan por auth del registry, usar MinIO como alternativa liviana y publica. Ver referencia `references/minio-s3-local.md`.
- **Web scraping / búsqueda desde Docker:** DuckDuckGo y SearXNG públicos bloquean requests desde IPs de containers Docker (rate limit 202, 403 bot detection). SearXNG local tampoco ayuda — el bot detection de SearXNG da 403 incluso con `pass_ip: 0.0.0.0/0` y `limiter.toml`. **Fix probado:** correr el backend como proceso en el HOST con un venv local (`python3 -m venv venv && ./venv/bin/pip install ddgs fastapi uvicorn ollama`), no en Docker. DuckDuckGo acepta requests desde la IP real del servidor. Ver `references/web-search-docker-pitfall.md`.
- **`@types/maplibre-gl` no existe para v3+:** Desde maplibre-gl v3 los tipos vienen dentro del paquete principal. No agregar `@types/maplibre-gl` a devDependencies — da `ETARGET` en npm ci.
- **Alias `@/` requiere configuración explícita:** El template usa `@/lib/utils` y `@/lib/api` pero el alias no está configurado en Vite ni tsconfig. En Docker el build falla con `Cannot find module '@/lib/api'`. Fix en `vite.config.ts`: `resolve: { alias: { "@": path.resolve(__dirname, "./src") } }` y en `tsconfig.json`: `"paths": { "@/*": ["./src/*"] }`.
- **MSW no viene en el template:** `src/test/mocks/handlers.ts` importa `msw` que no está instalado. En PoC reemplazar por `export const handlers: unknown[] = [];`
- **`src/test/` rompe el build de producción TypeScript:** Los `@types/chai` y `@types/vitest` en node_modules generan errores si `src/test/` está incluido en la compilación de producción. Agregar `"exclude": ["src/test", "node_modules"]` en `tsconfig.json`.
- **`clsx` no viene en el template base:** `src/lib/utils.ts` importa `clsx` pero no está en `package.json`. Reemplazar por: `export function cn(...inputs: (string|undefined|null|false)[]) { return inputs.filter(Boolean).join(" "); }`
- **`useAuth.ts` del template importa `@/lib/api`:** El hook de auth del template usa la API interna del template. En proyectos que no usan auth, reemplazar por stub: `export function useAuth() { return { data: null, isLoading: false }; }`
  - `src/hooks/useAuth.ts` importa `@/lib/api` (alias no configurado) → reemplazar por stub
  - `src/test/mocks/handlers.ts` importa `msw` (no en package.json) → reemplazar por `export const handlers: unknown[] = [];`
  - `src/lib/utils.ts` importa `clsx` (no en dependencies) → reemplazar por `inputs.filter(Boolean).join(" ")`
  - Agregar `"exclude": ["src/test"]` en `tsconfig.json` para que `@types/chai` no rompa el build de producción
- **`@types/maplibre-gl` no existe para v4:** maplibre-gl v3+ incluye tipos propios. No agregar `@types/maplibre-gl` a devDependencies — da error `ETARGET notarget` en `npm ci`.
- **Alias `@/` requiere config explícita:** Si se usan imports `@/lib/...` hay que declarar el alias en `vite.config.ts` (`resolve.alias`) Y en `tsconfig.json` (`compilerOptions.paths`). Sin ambos, `npm run build` falla con `Cannot find module`.
- **Web scraping / búsqueda desde Docker:** DuckDuckGo y SearXNG públicos bloquean requests desde IPs de containers Docker (rate limit 202, 403 bot detection). SearXNG local tampoco ayuda — el bot detection de SearXNG da 403 incluso con `pass_ip: 0.0.0.0/0` y `limiter.toml`. **Fix probado:** correr el backend como proceso en el HOST con un venv local (`python3 -m venv venv && ./venv/bin/pip install ddgs fastapi uvicorn ollama`), no en Docker. DuckDuckGo acepta requests desde la IP real del servidor. Ver `references/web-search-docker-pitfall.md`.
