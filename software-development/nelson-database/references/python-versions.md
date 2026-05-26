# Versiones de Python - Equipo Nelson

## Version base actual: Python 3.12

El stack backend del equipo Nelson usa Python 3.12 como version base.

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### pyproject.toml

```toml
[project]
requires-python = ">=3.12"
```

### Dependencias tipicas (requirements.txt)

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
python-dotenv>=1.0.0
pytest>=8.3.0
httpx>=0.27.0
```

## Notas

- SQLAlchemy 2.0 requiere Python >= 3.7, pero usamos 3.12 para aprovechar mejoras de performance y sintaxis
- FastAPI con Pydantic v2 tiene mejor performance en Python 3.10+
- `|` syntax para unions (PEP 604) esta disponible nativamente en 3.12
