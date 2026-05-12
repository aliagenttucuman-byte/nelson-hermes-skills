---
name: nelson-code-quality
title: Code Quality - Ruff + Black + mypy + pre-commit
description: Calidad de codigo para el equipo Nelson. Ruff como linter y formatter, mypy para type checking, pre-commit hooks, configuracion estandar para Python y TypeScript.
skill: nelson-code-quality
author: equipo-nelson
version: 1.0.0
keywords: [ruff, black, mypy, pre-commit, linting, formatting, quality]
dependencies: [python-project-structure]
---

# Code Quality - Equipo Nelson

## Stack

| Herramienta | Proposito | Version |
|-------------|-----------|---------|
| Ruff | Linter + Formatter (Python) | ^0.9 |
| mypy | Type checking (Python) | ^1.14 |
| pre-commit | Git hooks automaticos | ^4.1 |
| ESLint | Linter (TypeScript/React) | ^9 |
| TypeScript | Type check (frontend) | ^5.7 |

## Ruff (Python)

Ruff reemplaza a flake8, black, isort, pydocstyle y bandit en una sola herramienta.

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
  "E",   # pycodestyle errors
  "F",   # Pyflakes
  "I",   # isort
  "N",   # pep8-naming
  "W",   # pycodestyle warnings
  "UP",  # pyupgrade
  "B",   # flake8-bugbear
  "C4",  # flake8-comprehensions
  "SIM", # flake8-simplify
  "TCH", # flake8-type-checking
  "PTH", # flake8-use-pathlib
  "ERA", # eradicate
  "PLC", "PLE", "PLW", # Pylint
  "RUF", # Ruff-specific
]
ignore = ["E501"]  # line too long (ya manejado por formatter)

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

Comandos:
```bash
ruff check .              # Lintear todo
ruff check --fix .        # Lintear y auto-fixear
ruff format .             # Formatear todo
```

## mypy (Python)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true
```

Comando:
```bash
mypy app/
```

## pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ["--maxkb=500"]
```

Setup:
```bash
pip install pre-commit
pre-commit install        # Instala hooks en el repo
pre-commit run --all-files # Corre todos los hooks
```

## ESLint (Frontend)

```bash
npm install -D eslint @eslint/js typescript-eslint eslint-plugin-react-hooks
```

```js
// eslint.config.js
import js from '@eslint/js';
import ts from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';

export default ts.config(
  js.configs.recommended,
  ...ts.configs.recommended,
  {
    plugins: { 'react-hooks': reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  }
);
```

## Scripts package.json (frontend)

```json
{
  "scripts": {
    "lint": "eslint . --ext ts,tsx",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "typecheck": "tsc --noEmit"
  }
}
```

## GitHub Actions - Quality Gate

```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install ruff mypy
      - run: ruff check backend/
      - run: ruff format --check backend/
      - run: mypy backend/app/

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run typecheck

  alma-reviewer:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Alma 2.0 - Revision semantica
        run: |
          pip install httpx
          python scripts/alma-reviewer.py --diff --json > alma-report.json
      - name: Sensores estructurales
        run: python scripts/nelson-structural-check.py --json > struct-report.json
```

## Alma 2.0 - Sensores Inferenciales (LLM)

Revision semantica con LLM local. Detecta problemas que los linters no ven.

### Instalacion

```bash
# Scripts ya estan en ~/.hermes/scripts/
ln -s ~/.hermes/scripts/alma-reviewer.py ~/.local/bin/alma-reviewer
```

### Uso

```bash
# Revisar un archivo
alma-reviewer app/services/rag_service.py

# Revisar cambios no commiteados (git diff)
alma-reviewer --diff

# Output JSON para CI
alma-reviewer --diff --json
```

### Que detecta

| Categoria | Descripcion |
|-----------|-------------|
| over-engineering | Codigo mas complejo de lo necesario |
| duplication | Codigo duplicado semantico |
| unnecessary | Features que no aportan valor |
| naming | Nombres confusos o genericos |
| clean-code | Funciones largas, muchos parametros |
| error-handling | Excepciones no manejadas |
| inefficiency | Algoritmos ineficientes |

### Configuracion modelo

```bash
# Por defecto usa llama3.1:8b (mas grande, mas lento, mas preciso)
alma-reviewer archivo.py --model llama3.1:8b

# Para revision rapida usar llama3.2:3b
alma-reviewer archivo.py --model llama3.2:3b
```

## Sensores Estructurales (Deterministicos)

Checks rapidos de arquitectura, sin LLM.

### Uso

```bash
# Revisar proyecto actual
nelson-check --root .

# Output JSON
nelson-check --root . --json
```

### Checks incluidos

| Check | Severidad | Descripcion |
|-------|-----------|-------------|
| API importa models | HIGH | Violacion de capas |
| Service importa API | HIGH | Dependencia circular |
| Bare except | HIGH | `except:` sin tipo |
| Funcion muy larga | MEDIUM | >50 lineas |
| Secrets hardcodeados | HIGH | Passwords/tokens en codigo |
| TODO/FIXME | LOW | Codigo con deuda tecnica |
| Sin tests | HIGH | No existe app/tests/ |

## Self-Correction Loops

Cuando un sensor falla, intenta arreglar automaticamente.

### Uso

```bash
# Ver que arreglaria (no toca nada)
nelson-self-fix --root . --dry-run

# Aplicar fixes automaticos
nelson-self-fix --root .
```

### Fixes automaticos

| Problema | Fix aplicado |
|----------|--------------|
| `except:` | `except Exception:` |
| Funcion sin type hints | Agrega `-> None` |
| Imports desordenados | Ejecuta `isort` |

## Pipeline completo de calidad

```bash
# 1. Linters deterministas (rapido)
ruff check --fix .
mypy app/

# 2. Sensores estructurales
nelson-check --root .

# 3. Revision semantica (lento, opcional en CI)
alma-reviewer --diff

# 4. Self-fix
nelson-self-fix --root . --dry-run

# 5. Tests
pytest
```

## Checklist antes de commitear

- [ ] `ruff check --fix .` pasa
- [ ] `ruff format --check .` pasa
- [ ] `mypy app/` pasa
- [ ] `nelson-check --root .` score >= 80
- [ ] `alma-reviewer --diff` sin issues HIGH
- [ ] `npm run lint` pasa (frontend)
- [ ] `npm run typecheck` pasa (frontend)
- [ ] `pytest` pasa (tests)

## Pitfalls

- Ruff es mucho mas rapido que black+flake8, pero asegurate de usar versiones compatibles
- mypy strict puede ser duro al principio; agregar `# type: ignore[code]` con moderacion
- pre-commit solo corre en archivos staged; usar `--all-files` para verificar todo
- Nunca commitear sin correr pre-commit primero
- Alma 2.0 requiere Ollama corriendo localmente; en CI usar un modelo mas ligero o saltar
- Self-fix solo arregla lo seguro; revisar siempre antes de commitear

## Scripts disponibles

Los siguientes scripts estan empaquetados en `scripts/` dentro de esta skill:

- `scripts/alma-reviewer.py` - Alma 2.0, revision semantica con LLM local (Ollama)
- `scripts/nelson-structural-check.py` - Sensores estructurales deterministicos de arquitectura
- `scripts/nelson-self-fix.py` - Auto-correccion de issues comunes (bare excepts, type hints)

## Referencias

- `references/harness-engineering.md` - Concepto de Harness Engineering (Martin Fowler)
  y su aplicacion en el equipo Nelson.
