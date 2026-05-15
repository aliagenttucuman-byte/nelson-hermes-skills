---
name: spec-driven-development
title: Spec-Driven Development
description: Metodologia spec-first para APIs. OpenAPI como fuente de verdad, generacion automatica de models y types, contract testing.
skill: spec-driven-development
author: equipo-nelson
version: 1.0.0
keywords: [openapi, spec-first, api-design, contract-testing, pydantic, fastapi]
dependencies: [fastapi, api-design-principles, python-testing-patterns]
---

# Spec-Driven Development (SDD)

> Primero la especificacion, despues el codigo. El spec es la fuente de verdad.

## Que es SDD

Spec-Driven Development es una metodologia donde:
1. **Primero** se escribe la especificacion de la API (OpenAPI/Swagger)
2. **Despues** se genera/escribe el codigo a partir de esa spec
3. **Siempre** se valida que el codigo cumpla la spec (contract testing)

Esto previene discrepancias entre lo que prometemos y lo que entregamos.

## Flujo de Trabajo del Equipo

```
Nelson (voz/texto) -> Beto (Arquitecto) escribe spec OpenAPI
                                      |
                                      v
                        Ricky (Backend) genera schemas desde spec
                                      |
                                      v
                        Diego (DevOps) valida contrato en CI
                                      |
                                      v
                        Alma (QA) testea contra la spec
```

## Herramientas Stack

| Proposito | Herramienta | Comando |
|-----------|-------------|---------|
| Escribir specs | YAML/JSON OpenAPI 3.1 | Manual o con ayuda de IA |
| Generar Pydantic models | `datamodel-code-generator` | `datamodel-codegen --input spec.yaml --output models.py` |
| Generar cliente TS | `openapi-typescript` | `npx openapi-typescript spec.yaml -o api.ts` |
| Contract testing | `schemathesis` | `st run spec.yaml --base-url http://localhost:8000` |
| Validar spec | `openapi-spec-validator` | `openapi-spec-validator spec.yaml` |
| Mock server | `prism` | `npx @stoplight/prism-cli mock spec.yaml` |

## Estructura de Archivos

```
project/
├── specs/
│   ├── openapi.yaml          # Spec principal (fuente de verdad)
│   ├── schemas/
│   │   ├── user.yaml
│   │   └── flight.yaml
│   └── paths/
│       ├── users.yaml
│       └── flights.yaml
├── backend/
│   ├── app/
│   │   ├── models.py         # Generado desde spec
│   │   └── main.py           # Implementa endpoints definidos en spec
├── frontend/
│   ├── src/
│   │   └── api/
│   │       └── api.ts        # Generado desde spec (tipos + fetch)
└── tests/
    └── contract/
        └── test_api.py       # Schemathesis tests
```

## Reglas de Oro

1. **Nunca** tocar `models.py` o `api.ts` a mano si fueron generados
2. **Siempre** cambiar la spec primero, regenerar despues
3. **Todo** PR que toca la API debe incluir la spec actualizada
4. **CI** debe fallar si `openapi.yaml` y codigo no coinciden

## FastAPI + SDD

FastAPI es ideal porque:
- Genera OpenAPI automaticamente desde Pydantic models
- PERO en SDD hacemos lo inverso: spec primero, luego models

```python
# En SDD puro:
# 1. Escribis spec/openapi.yaml
# 2. Generas models.py con datamodel-codegen
# 3. Importas esos models en tus endpoints

from fastapi import FastAPI
from app.models import UserCreate, UserResponse  # Generados desde spec

app = FastAPI()

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    ...
```

## Comandos Utiles

```bash
# Instalar herramientas
pip install datamodel-code-generator schemathesis openapi-spec-validator
npm install -g @stoplight/prism-cli openapi-typescript

# Generar models Pydantic desde spec
datamodel-codegen \
  --input specs/openapi.yaml \
  --output backend/app/models.py \
  --output-model-type pydantic_v2.BaseModel

# Generar types TypeScript desde spec
npx openapi-typescript specs/openapi.yaml -o frontend/src/api/api.ts

# Validar spec es valida
openapi-spec-validator specs/openapi.yaml

# Contract testing contra backend corriendo
st run specs/openapi.yaml --base-url http://localhost:8000

# Mock server para frontend mientras backend no esta listo
npx @stoplight/prism-cli mock specs/openapi.yaml
```

## Integracion con Docker

Agregar al `docker-compose.yml`:

```yaml
  prism:
    image: stoplight/prism:5
    command: mock -h 0.0.0.0 /specs/openapi.yaml
    volumes:
      - ./specs:/specs:ro
    ports:
      - "4010:4010"
```

## Checklist antes de implementar

- [ ] Spec OpenAPI escrita y versionada
- [ ] Schemas validados con `openapi-spec-validator`
- [ ] Models Pydantic generados
- [ ] Types TypeScript generados
- [ ] Contract tests pasan contra mock
- [ ] Review de Beto (arquitecto) aprobado

## Adaptación: Spec Kit (GitHub)

Analizamos el toolkit **Spec Kit** de GitHub y mapeamos sus 8 fases a nuestras skills existentes + 3 skills nuevas por crear.

**Resumen del mapeo:**
- `/speckit.constitution` → `nelson-project-constitution` (nueva)
- `/speckit.specify` → `spec-driven-development` (ya existe)
- `/speckit.clarify` → integrar en `spec-driven-development`
- `/speckit.plan` → `writing-plans` (ya existe)
- `/speckit.analyze` → `nelson-spec-analyzer` (nueva)
- `/speckit.tasks` → `subagent-driven-development` (ya existe)
- `/speckit.checklist` → `requesting-code-review` + `nelson-code-quality` (ya existen)
- `/speckit.implement` → `subagent-driven-development` (ya existe)

Ver `references/spec-kit-adaptation.md` para el mapeo completo, lecciones a adoptar, y roadmap de implementación.

## Adaptación: Spec Kit (GitHub)

Analizamos el toolkit **Spec Kit** de GitHub y mapeamos sus 8 fases a nuestras skills existentes + 3 skills nuevas por crear.

**Resumen del mapeo:**
- `/speckit.constitution` → `nelson-project-constitution` (nueva)
- `/speckit.specify` → `spec-driven-development` (ya existe)
- `/speckit.clarify` → integrar en `spec-driven-development`
- `/speckit.plan` → `writing-plans` (ya existe)
- `/speckit.analyze` → `nelson-spec-analyzer` (nueva)
- `/speckit.tasks` → `subagent-driven-development` (ya existe)
- `/speckit.checklist` → `requesting-code-review` + `nelson-code-quality` (ya existen)
- `/speckit.implement` → `subagent-driven-development` (ya existe)

Ver `references/spec-kit-adaptation.md` para el mapeo completo, lecciones a adoptar, y roadmap de implementación.

## Pitfalls

- No mezclar hand-written y generated models en el mismo archivo
- Versionar la spec (`/api/v1`, `/api/v2`) para no romper clientes
- No olvidar ejemplos en la spec (`examples:`) — sirven para mocks y tests
- Si FastAPI auto-genera spec, compararla con la spec fuente de verdad
