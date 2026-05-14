---
name: equipo-nelson
description: "Equipo de agentes de software para Nelson Acosta: Python/FastAPI backend, React/Vite frontend, Docker, IA."
version: 1.1.0
author: Nelson Acosta + Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [python, fastapi, react, vite, docker, ai, team, backend, frontend, gcp]
    related_skills: [docker-management, writing-plans, subagent-driven-development, test-driven-development, spike]
---

# Equipo Nelson — Agentes de Software

Skill maestra para el equipo de desarrollo de Nelson Acosta.
Stack: Python (FastAPI) + React (Vite) + Docker + IA.

## Los Agentes

### 1. Arquitecto-Backend ("Beto")
- **Rol:** Arquitectura de APIs REST con FastAPI, base de datos, lógica de negocio, integración con modelos de IA
- **Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0/PostgreSQL, Uvicorn, pytest, Alembic
- **Tareas típicas:**
  - Diseñar arquitectura y specs OpenAPI
  - Crear endpoints CRUD
  - Implementar autenticación JWT
  - Integrar modelos de IA (OpenAI, Ollama local, embeddings)
  - Dockerizar servicios Python
  - Tests unitarios y de integración

### 2. Backend-Developer ("Ricky")
- **Rol:** Implementación backend, lógica de negocio, integraciones, mantenimiento de APIs
- **Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0/PostgreSQL, Celery, Redis
- **Tareas típicas:**
  - Implementar endpoints según specs de Beto
  - Repositorios, servicios, modelos ORM
  - Background jobs con Celery
  - Integraciones con terceros
  - Code review y refactor

### 3. Frontend-Developer ("Nico")
- **Rol:** Interfaces web con React 19, Vite 6, TypeScript, Tailwind 4
- **Stack:** React 19+, Vite 6+, TypeScript 5.7+, Tailwind CSS 4+, React Query 5+, Axios, React Router 7+
- **Tareas típicas:**
  - Scaffolding y estructura de proyecto frontend
  - Componentes UI reutilizables
  - Consumo de APIs del backend
  - Routing, auth guards, state management
  - Tests unitarios (Vitest) y E2E (Playwright)
  - Dockerizar build de producción con nginx

### 4. DevOps-Docker ("Diego")
- **Rol:** Docker, docker-compose, CI/CD, despliegue, observabilidad
- **Stack:** Docker, docker-compose, nginx, GitHub Actions, Prometheus, structlog
- **Tareas típicas:**
  - Crear Dockerfiles multistage
  - Orquestar con docker-compose (PostgreSQL, Redis, Qdrant)
  - Configurar redes y volúmenes
  - Health checks, logs estructurados, métricas

### 5. AI-Integration / QA ("Alma")
- **Rol:** Integrar modelos de IA en el stack, RAG, agentes, visión, testing, calidad
- **Stack:** OpenAI API, Ollama, Qdrant, sentence-transformers, Celery + Redis, Playwright
- **Tareas típicas:**
  - Conectar APIs de IA al backend
  - Implementar RAG con vector DB (Qdrant)
  - Embeddings locales y en la nube
  - Agentes autónomos con herramientas
  - Visión por computadora (OCR, detección)
  - Testing E2E y validación de calidad

## Infraestructura de Comunicación

### WhatsApp Gateway (Baileys)
El equipo cuenta con un gateway propio basado en Baileys que permite enviar mensajes de WhatsApp a cualquier número desde scripts Python/Node.js, independientemente de la conexión nativa de Hermes.

**Usos del equipo:**
- **AI News Aggregator**: envía resúmenes de novedades IA automáticamente a socios (Pablo Terian)
- **Notificaciones de sistemas**: alertas de CI/CD, errores de producción, reportes de Alma
- **Broadcasts**: mensajes a múltiples números del equipo desde un solo script

**Contactos configurados:**
| Nombre | Número | Rol |
|--------|--------|-----|
| Pablo Terian | 5493816240691 | Socio |

Ver skill `nelson-whatsapp-gateway` para setup, troubleshooting y API.

## Entorno de Nelson (Este Servidor)

- **OS:** Linux (Ubuntu/Debian)
- **Usuario:** `server` — NO está en grupo `docker`, requiere `sudo` para Docker
- **Clave sudo:** `srv2026`
- **Docker:** V2 (`docker compose`, no `docker-compose`)
- **Puertos usados:** Backend 8000, Frontend 8080 (3000 ocupado), PostgreSQL 5432, Qdrant 6333
- **GCP:** Proyecto `latam-flight-delay`, CLI en `~/google-cloud-sdk/`
- **GPU:** NVIDIA GeForce GTX 1650 Mobile/Max-Q con **4GB GDDR5 VRAM**
- **RAM:** 13GB total
- **Ollama:** Instalado en `/usr/local/bin/ollama`, modelos descargados en `~/.ollama`

Ver `references/docker-setup.md` para comandos exactos y troubleshooting de Docker.
Ver `references/google-cloud-deploy.md` para deploy a Google Cloud.

## Referencias y Templates

| Archivo | Qué contiene |
|---------|--------------|
| `references/docker-setup.md` | Comandos Docker, permisos, puertos, troubleshooting |
| `references/docker-pitfalls.md` | Problemas comunes de Docker en este stack |
| `references/github-cli-setup.md` | Instalar y loguear gh CLI para commits/push/skills |
| `references/skills-from-github.md` | Instalar skills cuando el hub trunca los IDs |
| `references/skill-backup-workflow.md` | Exportar/importar skills custom a repo GitHub. Backup y migración |
| `references/google-cloud-deploy.md` | Deploy a GCP, credenciales, Cloud Run |
| `templates/project-boilerplate.md` | Boilerplate completo del stack (FastAPI + React + Docker) |
| `templates/nginx-frontend.conf` | Config nginx para servir el build de React/Vite |

## Skills del Equipo (Arsenal completo)

### Core / Diseño
- `equipo-nelson` — Esta skill maestra (roles, flujo, preferencias)
- `spec-driven-development` — OpenAPI primero, código después
- `api-design-principles` — REST/GraphQL best practices
- `api-docs-writer` — Documentación automática de APIs

### Backend
- `fastapi` — FastAPI avanzado
- `python-design-patterns` — Repository, Strategy, etc.
- `async-python-patterns` — Asyncio, concurrencia
- `python-project-structure` — Organización de módulos
- `python-testing-patterns` — pytest, fixtures, mocking
- `test-driven-development` — TDD
- `nelson-database` — SQLAlchemy 2.0 + Alembic + PostgreSQL
- `nelson-security` — JWT, OAuth2, CORS, rate limiting

### Frontend
- `nelson-frontend-stack` — React 19 + TS 5.7 + Vite 6 + Tailwind 4
- `nelson-frontend-testing` — Vitest + React Testing Library + Playwright

### IA / RAG / LLM
- `nelson-embeddings` — OpenAI v3 / sentence-transformers / Ollama
- `nelson-vector-databases` — Qdrant + Chroma + Weaviate
- `nelson-rag-pipeline` — Chunking → Retrieval → Generation
- `nelson-llm-generation` — OpenAI, Anthropic, Groq, Ollama. Streaming, retry
- `nelson-document-processing` — PDF, Word, TXT, Markdown parsing

### IA Avanzada
- `nelson-ai-vision` — OCR, object detection, clasificación, LLM multimodal
- `nelson-ai-agents` — Agentes autónomos con herramientas, memoria, ReAct

### Calidad / Prácticas Senior
- `nelson-senior-practices` — Type hints estrictos, clean code, SOLID
- `nelson-code-quality` — Ruff + mypy + pre-commit + ESLint
- `nelson-documentation` — README, API docs, MkDocs

### DevOps
- `docker-management` — Docker containers, compose
- `nelson-observability` — structlog JSON + health checks + Prometheus
- `nelson-background-jobs` — Celery + Redis async
- `nelson-ci-cd` — GitHub Actions
- `nelson-deploy-gcp` — Cloud Run + Cloud SQL + Artifact Registry

### Bootstrap
- `nelson-project-bootstrap` — Genera proyecto completo con las 21+ skills

## Estructura de Proyecto (Template Base)

```
mi-proyecto/
├── specs/                    # OpenAPI specs
│   └── openapi.yaml
├── backend/                  # FastAPI + Python 3.12
│   ├── app/
│   │   ├── api/v1/         # Endpoints REST
│   │   ├── core/           # Config, logging, security
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── schemas/        # Pydantic v2
│   │   ├── repositories/   # Repository pattern
│   │   ├── services/       # Lógica de negocio
│   │   ├── tasks/          # Celery background jobs
│   │   └── tests/          # pytest
│   ├── alembic/              # Migraciones
│   ├── Dockerfile            # python:3.12-slim
│   └── pyproject.toml        # Ruff + mypy + pytest
├── frontend/                 # React 19 + Vite 6 + Tailwind 4
│   ├── src/
│   │   ├── api/            # Axios client
│   │   ├── components/     # UI + layout
│   │   ├── hooks/          # React Query
│   │   ├── lib/            # Utils
│   │   ├── pages/          # Rutas
│   │   ├── test/           # Vitest + MSW
│   │   └── types/          # Tipos compartidos
│   ├── e2e/                  # Playwright
│   ├── Dockerfile            # node:22 + nginx
│   └── nginx.conf
├── scripts/                  # Bootstrap + setup Ollama
├── docker-compose.yml        # Backend + Frontend + DB + Redis + Qdrant
├── .github/workflows/        # CI/CD
├── .env.example
└── README.md
```

## Flujo de Trabajo

### Para migrar skills a máquina nueva o onboarding de equipo:
1. Clonar `nelson-hermes-skills` desde GitHub
2. Correr `./sync-from-repo.sh` para instalar las 22 skills custom
3. Verificar con `hermes skills list | grep nelson`
4. Ver `references/skill-backup-workflow.md` para detalles completos

### Para nuevas features:
1. Nelson describe la feature
2. Se carga la skill `equipo-nelson`
3. Se crea un plan con `writing-plans`
4. Se delega a subagentes por tarea con `subagent-driven-development`
5. Cada agente (Beto, Ricky, Diego) ejecuta su parte
6. Review de calidad y specs
7. Integración y test final

### Comandos rápidos:

```bash
# Crear proyecto nuevo
mkdir mi-proyecto && cd mi-proyecto

# Backend (Beto)
cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic sqlalchemy pytest

# Frontend (Ricky)
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Docker (Diego)
docker-compose up --build
```

## Docker Base

### backend/Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### docker-compose.yml
```yaml
services:
  backend:
    build: ./backend
    container_name: nelson-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - db
    networks:
      - nelson-network

  frontend:
    build: ./frontend
    container_name: nelson-frontend
    ports:
      - "8080:80"
    depends_on:
      - backend
    networks:
      - nelson-network

  db:
    image: postgres:15-alpine
    container_name: nelson-db
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - nelson-network

volumes:
  postgres_data:

networks:
  nelson-network:
    driver: bridge
```

## Preferencias de Comunicación de Nelson

- **Canal preferido:** WhatsApp (no usar markdown, no renderiza bien)
- **Formato preferido:** Audio/voz masculina en español argentino (`es-AR-TomasNeural`)
- **Estilo:** Action-oriented, directo. Nelson quiere ver el plan y ejecutar.
- **Stack:** Python 3.12 + FastAPI backend, React 19 + Vite 6 + Tailwind 4 frontend, Docker, IA/ML
- **Metodología:** Spec-driven development (OpenAPI primero), spikes/POCs antes de builds completos
- **GitHub:** aliagenttucuman@gmail.com, usuario `aliagenttucuman-byte`

> **Importante:** Cuando las respuestas son largas, preferir enviar audio resumido. Nelson puede pedir "mandame audio" cuando no quiere leer texto extenso.

## Preferencias de Workflow

- **Paso a paso, sin apuro.** Nelson prefiere ejecutar las tareas "pasito, pasito", confirmando cada etapa antes de avanzar. NO tirar todo el código o todos los pasos de una sola vez. Esperar su aprobación (“dale”, “vamos con el siguiente”, “ok”) antes de ejecutar el próximo paso.
- **Nadie nos apura.** Si Nelson dice “no hagas nada más hasta que yo te dé la orden”, respetar estrictamente. Quedar en standby.
- **Audio como canal principal.** A menos que pida explícitamente texto, preferir comunicación por audio (TTS).

## Reglas del Equipo

1. **Siempre usar spec-driven development** — OpenAPI primero, código después
2. **Siempre usar plan antes de code** — `writing-plans` primero
3. **Backend expone OpenAPI** — FastAPI genera docs automáticamente en `/docs`
4. **Frontend consume la API** — usando React Query + tipos compartidos desde spec
5. **Todo en Docker** — nada corre local sin container
6. **Código senior** — type hints estrictos, SOLID, docstrings, clean code
7. **Documentación obligatoria** — README, API docs, CHANGELOG. Si no está documentado, no existe
8. **IA como servicio** — cada proyecto tiene componente inteligente
9. **Commits frecuentes** — cada tarea terminada = un commit
10. **Reviews obligatorias** — spec compliance + code quality
11. **Sync al repo solo con info valiosa** — No sincronizar skills ni memoria al repo GitHub en cada cambio menor. **El usuario decide cuándo la información es lo suficientemente valiosa como para hacer backup.** No hacer push automático después de cada actualización de memoria o skill. Esperar indicación explícita del usuario (ej: "guardá esto", "hacé backup", "sync al repo"). Ver `references/skill-backup-workflow.md` para el procedimiento completo.
12. **Naming enterprise para skills** — Preferir nombres técnicos estándar (`document-qa`, `rag-pipeline`) sobre nombres descriptivos casuales (`chat-with-documents`).

## Integración con IA

- Backend expone endpoints `/ai/chat`, `/ai/embed`, `/ai/rag`
- Frontend tiene componente `<ChatIA />` para interactuar
- Vector DB (pgvector o Chroma) para RAG
- Prompts versionados en `backend/app/prompts/`

## Comunicación entre Agentes

Cuando un agente necesita algo de otro:
- Beto (arquitecto backend) genera el OpenAPI schema → Nico (frontend) lo consume
- Diego (DevOps) necesita los puertos y variables → Beto, Ricky y Nico los documentan
- Alma (QA) necesita endpoints → Beto y Ricky los exponen
- Alma (QA) define flujos críticos → Nico escribe tests E2E

## Requisitos Previos Instalados

- **Docker + docker-compose** (V2) — `docker compose` funciona, requiere `sudo`
- **Google Cloud CLI** — en `~/google-cloud-sdk/`, autenticado con `latam-flight-delay`
- **GitHub CLI (gh)** — logueado con `aliagenttucuman@gmail.com`
- **Node.js + npm** — para frontend React/Vite
- **Python 3.12** — para backend FastAPI
- **Ollama** — en `/usr/local/bin/ollama`, modelos en `~/.ollama`
- **GPU NVIDIA** — GTX 1650 4GB VRAM, modelos 3B en GPU, 8B en mix CPU/GPU

Ver `references/github-cli-setup.md` para re-loguear gh si es necesario.
Ver `references/docker-setup.md` para comandos Docker exactos.
Ver `references/ollama-hardware-testing.md` en skill `nelson-llm-generation` para modelos testeados.

## Notas Importantes del Stack

### Memoria persistente de Hermes (MEMORY.md / USER.md)
- **Límite:** 2,200 caracteres por archivo de memoria
- **Si se alcanza el límite:** usar `memory(action="replace", ...)` en vez de `memory(action="add", ...)` para actualizar entradas existentes sin exceder el límite
- **Sincronización:** Solo cuando el usuario indique que la información es valiosa (ver Regla 11 del equipo)

### TypeScript + Vite
El frontend con Vite necesita un archivo `vite-env.d.ts` para que TypeScript reconozca `import.meta.env`:

```typescript
/// <reference types="vite/client" />
```

Sin esto, el build de producción falla con:
```
error TS2339: Property 'env' does not exist on type 'ImportMeta'.
```

### Tailwind CSS 4
Tailwind 4 **no usa** `tailwind.config.js`. La configuración del tema va directamente en CSS:

```css
@import "tailwindcss";

@theme {
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
}
```

### Ollama con VRAM Limitada (4GB)
- Modelos ≤3B (llama3.2:3b, qwen2.5:3b): 100% GPU, <1s respuesta
- Modelos >4GB (llama3.1:8b, llava:7b): Mix 43% CPU / 57% GPU, ~2s respuesta
- Ollama maneja automáticamente la división GPU/CPU
- Ver `references/ollama-hardware-testing.md` en `nelson-llm-generation`

### SQLAlchemy 2.0
Usar estilo declarativo con `Mapped[]` y `mapped_column()`:

```python
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
```

## Próximos Pasos Sugeridos

1. **Bootstrap proyecto** — Nelson describe una idea y se genera el proyecto completo con `nelson-project-bootstrap`
2. **Spec-driven** — Beto escribe la spec OpenAPI en `specs/`
3. **Backend** — Ricky implementa models, schemas, endpoints con FastAPI (según specs de Beto)
4. **Frontend** — Nico crea componentes con React 19 + Tailwind 4, consume la API
5. **IA** — Alma integra RAG, embeddings, LLM generation
6. **Testing** — Tests con pytest + Vitest + Playwright (Nico + Alma)
7. **Deploy** — Diego deploya a Cloud Run con `nelson-deploy-gcp`

Para cualquiera de estos, seguir el flujo: `writing-plans` → `subagent-driven-development`.
