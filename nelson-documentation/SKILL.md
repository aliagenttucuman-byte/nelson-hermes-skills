---
name: nelson-documentation
title: Documentation - README.md, API Docs, MkDocs
description: Documentacion profesional para el equipo Nelson. README.md estructurado, docstrings, API docs con Redoc/Swagger, documentacion de proyecto con MkDocs. Ningun proyecto sin docs.
skill: nelson-documentation
author: equipo-nelson
version: 1.0.0
keywords: [documentation, readme, mkdocs, api-docs, redoc, swagger, docs]
dependencies: [api-docs-writer, spec-driven-development]
---

# Documentation - Equipo Nelson

> Regla de oro: Si no esta documentado, no existe.

## README.md Template

Cada proyecto DEBE tener un README.md con esta estructura:

```markdown
# Nombre del Proyecto

> One-liner descriptivo del proyecto.

## 🚀 Quick Start

```bash
git clone https://github.com/user/repo.git
cd repo
cp .env.example .env
# Editar .env con tus variables

docker compose up --build -d
```

Accede a:
- API: http://localhost:8000/docs
- Frontend: http://localhost:8080
- Health: http://localhost:8000/health

## 📝 Descripcion

Parrafo descriptivo de que hace el proyecto, para quien es,
y que problema resuelve.

## 🎢 Arquitectura

```
[Diagrama simple ASCII o link a imagen]
```

## 📁 Estructura

```
.
├── backend/          # FastAPI + Python 3.12
├── frontend/         # React 19 + Vite 6
├── specs/            # OpenAPI specs
├── docker-compose.yml
└── .github/          # CI/CD workflows
```

## 🛠 Stack Tecnologico

| Capa | Tecnologia |
|------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 |
| Frontend | React 19, TypeScript 5.7, Tailwind 4 |
| DB | PostgreSQL 16 |
| Vector DB | Qdrant |
| Cache | Redis |
| Deploy | Google Cloud Run |

## 📚 API Documentation

- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc
- OpenAPI spec: `./specs/openapi.yaml`

## 🧪 Testing

```bash
# Backend
cd backend && pytest -xvs

# Frontend
cd frontend && npm run test:ci

# E2E
cd frontend && npm run test:e2e
```

## 📝 Environment Variables

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://... |
| SECRET_KEY | JWT secret | super-secret-32-chars |
| OPENAI_API_KEY | OpenAI API key | sk-... |

Ver `.env.example` para lista completa.

## 📝 Changelog

Ver [CHANGELOG.md](./CHANGELOG.md)

## 👨‍💻 Equipo

| Rol | Responsable |
|-----|-------------|
| Arquitecto | Beto |
| Backend | Ricky |
| Frontend | [Nombre] |
| DevOps | Diego |
| QA | Alma |

## 📄 License

[MIT](LICENSE)
```

## CHANGELOG.md

```markdown
# Changelog

## [Unreleased]

## [0.1.0] - 2026-05-11

### Added
- Auth JWT con login/register
- CRUD de documentos
- Pipeline RAG basico
- Frontend con chat streaming
- Deploy a Cloud Run

### Fixed
- Health check timeout en Cloud Run cold start
```

Formato: [Keep a Changelog](https://keepachangelog.com/)

## API Docs Automaticas

FastAPI genera automaticamente:

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Nelson API",
    description="API del proyecto Nelson",
    version="0.1.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # Redoc
    openapi_url="/openapi.json",
)
```

Accesible en:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

### Tags descriptivos

```python
@app.get("/users", tags=["users"])
def list_users():
    ...

@app.post("/rag/ask", tags=["rag"])
def ask_question():
    ...
```

### Ejemplos en schemas

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    email: EmailStr = Field(examples=["nelson@example.com"])
    password: str = Field(examples=["SecurePass123!"])
```

## MkDocs (Documentacion de proyecto)

```bash
pip install mkdocs mkdocs-material
mkdocs new docs
```

```yaml
# mkdocs.yml
site_name: Nelson Docs
theme:
  name: material
  palette:
    scheme: slate
    primary: indigo
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Architecture: architecture.md
  - API: api.md
  - Deployment: deployment.md
```

```markdown
# docs/index.md
# Bienvenido al Proyecto Nelson

## Como empezar

1. Clonar repo
2. Copiar `.env.example` a `.env`
3. `docker compose up --build -d`
```

```bash
mkdocs serve   # Dev server
mkdocs build   # Build static site
mkdocs gh-deploy  # Deploy a GitHub Pages
```

## Docstrings como Documentacion

```python
"""Modulo de autenticacion.

Este modulo maneja:
- Registro de usuarios
- Login con JWT
- Refresh tokens
- Logout

Example:
    >>> from app.services.auth import AuthService
    >>> auth = AuthService()
    >>> token = auth.login("user@test.com", "pass")
"""
```

## Checklist de Documentacion

- [ ] README.md con Quick Start funcional
- [ ] `.env.example` con todas las variables explicadas
- [ ] CHANGELOG.md con versiones
- [ ] API docs automaticas (Swagger/Redoc)
[ ] Docstrings en funciones publicas
- [ ] Architecture Decision Records (ADRs) para decisiones importantes
- [ ] MkDocs o similar para docs extensas
- [ ] Diagrama de arquitectura (ASCII, SVG o Excalidraw)
- [ ] Guia de contribucion (CONTRIBUTING.md)
- [ ] License file

## Generación de PDF desde Markdown (WeasyPrint)

Cuando Nelson pide un documento formal (charter, propuesta, reporte) para compartir con terceros, WhatsApp no renderiza `.md` — hay que generar PDF.

**Stack probado y funcional en ai-server:**
```bash
# weasyprint y markdown ya instalados en el venv de hermes
python3 /tmp/gen_pdf.py
```

**Patrón estándar (escribir a /tmp/gen_pdf.py primero, luego ejecutar):**
```python
import markdown
from weasyprint import HTML

with open("/ruta/al/documento.md", "r") as f:
    md_content = f.read()

html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: Arial, sans-serif; font-size: 11px; margin: 2cm; color: #222; line-height: 1.5; }
  h1 { font-size: 18px; color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 6px; }
  h2 { font-size: 14px; color: #1a5276; margin-top: 20px; border-bottom: 1px solid #aed6f1; padding-bottom: 3px; }
  h3 { font-size: 12px; color: #2471a3; margin-top: 12px; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10px; }
  th { background-color: #1a5276; color: white; padding: 5px 8px; text-align: left; }
  td { border: 1px solid #d5d8dc; padding: 4px 8px; }
  tr:nth-child(even) td { background-color: #f2f3f4; }
  blockquote { background: #eaf2ff; border-left: 4px solid #2471a3; padding: 8px 12px; margin: 10px 0; }
  @page { margin: 1.5cm; }
</style>
</head>
<body>
""" + html_body + """
</body>
</html>"""

HTML(string=html).write_pdf("/tmp/output.pdf")
print("OK")
```

**CRÍTICO — escribir el script a archivo, NO pasar como string a terminal:**
- `terminal("python3 -c '...script...'")` falla con backslashes en CSS (SyntaxError)
- La solución correcta: `write_file(content=script, path="/tmp/gen_pdf.py")` → `terminal("python3 /tmp/gen_pdf.py")`

**Flujo completo:**
1. Generar el `.md` en `~/brainstorming/...`
2. Escribir el script de conversión a `/tmp/gen_pdf.py`
3. `python3 /tmp/gen_pdf.py` → genera `/tmp/NombreDoc.pdf`
4. `MEDIA:/tmp/NombreDoc.pdf` en la respuesta a Nelson

## Pitfalls

- README.md sin quick start = proyecto inusable
- API sin ejemplos en schemas = frontend sufre
- Changelog desactualizado = release notes manual
- Docs en wiki = se pierden con el tiempo, mejor en repo
- Sin `.env.example` = nadie puede levantar el proyecto
