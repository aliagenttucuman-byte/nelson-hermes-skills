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

## Generación de PDF con WeasyPrint (patrón AlegentAI)

Para generar PDFs profesionales desde Markdown — propuestas comerciales, valorización, estrategia:

```bash
# Verificar disponibilidad
python3 -c "import weasyprint, markdown; print('ok')"

# Usar el script reutilizable
python3 ~/.hermes/skills/nelson-documentation/scripts/generar_pdf_weasyprint.py \
  input.md output.pdf "PROPUESTA COMERCIAL" "Junio 2026"
```

Estilo incluido: header AlegentAI azul, tablas con header #0066cc, blockquotes destacados, paginación A4, marca CONFIDENCIAL en footer.

Dependencias: `pip install weasyprint markdown` (ya instaladas en ai-server jun 2026).

⚠️ WhatsApp NO entrega PDFs — siempre enviar por Telegram:
```
MEDIA:/ruta/al/archivo.pdf → target: telegram:Nelson Acosta (dm)
```

Ver script completo: `scripts/generar_pdf_weasyprint.py`

## Generación de .docx con python-docx

Para generar documentos Word (casos de uso, propuestas, especificaciones técnicas):

```bash
python3 -c "from docx import Document; print('ok')"
# Si falla: pip3 install python-docx
```

### PITFALL — python3 -c falla con código complejo (comillas, f-strings)

Al pasar código largo a `python3 -c '...'` los caracteres `'`, `"`, `\n`, y paréntesis
rompen el shell. El síntoma es `syntax error near unexpected token '('`.

**Fix obligatorio**: escribir el código a un archivo `.py` y ejecutarlo:

```python
# Paso 1: write_file a /tmp/gen_documento.py
# Paso 2: terminal("python3 /tmp/gen_documento.py")
```

Nunca intentar pasar código python-docx como argumento inline.

### Patrón básico .docx

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Título centrado
titulo = doc.add_paragraph()
titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = titulo.add_run("TÍTULO")
r.bold = True
r.font.size = Pt(20)
r.font.color.rgb = RGBColor(0x1F, 0x37, 0x64)

# Heading
p = doc.add_heading("Sección", level=1)
if p.runs: p.runs[0].font.color.rgb = RGBColor(0x2E, 0x4A, 0x8C)

# Campo clave: valor
p = doc.add_paragraph()
p.add_run("Campo: ").bold = True  # ERROR: .bold = True no funciona así
# Correcto:
p = doc.add_paragraph()
r = p.add_run("Campo: ")
r.bold = True
p.add_run("valor")

# Bullet
doc.add_paragraph("Ítem", style="List Bullet")

# Tabla
t = doc.add_table(rows=3, cols=3)
t.style = "Table Grid"
t.rows[0].cells[0].text = "Encabezado"

doc.save("/tmp/output.docx")
```

### Colores AlegentAI para documentos Bisonte

- Títulos: `RGBColor(0x1F, 0x37, 0x64)` — azul oscuro
- H2: `RGBColor(0x2E, 0x4A, 0x8C)` — azul medio
- Notas: `RGBColor(0x80, 0x40, 0x00)` — marrón

### PITFALL — heading sin runs visible

`doc.add_heading("Texto", level=1)` puede generar párrafos con `p.runs = []` dependiendo
del template. Siempre verificar `if p.runs:` antes de acceder a `p.runs[0]`.

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

## Pitfalls

- README.md sin quick start = proyecto inusable
- API sin ejemplos en schemas = frontend sufre
- Changelog desactualizado = release notes manual
- Docs en wiki = se pierden con el tiempo, mejor en repo
- Sin `.env.example` = nadie puede levantar el proyecto
