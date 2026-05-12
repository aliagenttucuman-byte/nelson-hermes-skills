---
name: nelson-database
title: Base de Datos - SQLAlchemy 2.0 + Alembic + PostgreSQL
description: Patrones de base de datos para el equipo Nelson. SQLAlchemy 2.0 estilo declarativo, Alembic para migraciones, PostgreSQL, connection pooling, transacciones, repositorios.
skill: nelson-database
author: equipo-nelson
version: 1.0.0
keywords: [sqlalchemy, alembic, postgresql, database, orm, migrations, repository-pattern]
dependencies: [python-design-patterns]
---

# Base de Datos - Equipo Nelson

## Stack

| Capa | Libreria | Version |
|------|----------|---------|
| ORM | SQLAlchemy | ^2.0 |
| Migrations | Alembic | ^1.13 |
| Driver | psycopg2-binary | ^2.9 |
| Async (opcional) | asyncpg | ^0.29 |

## SQLAlchemy 2.0 - Estilo Declarativo

```python
# app/models/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

```python
# app/models/user.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
```

## Configuracion de Engine y Session

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # Verifica conexion antes de usar
    pool_size=10,                # Conexiones mantenidas
    max_overflow=20,             # Conexiones extra bajo carga
    echo=False,                  # True solo en debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Repository Pattern

```python
# app/repositories/base.py
from typing import Generic, TypeVar, Type
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, obj_in: dict) -> T:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
```

```python
# app/repositories/user.py
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        from sqlalchemy import select
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()
```

## Alembic - Setup y Workflow

```bash
# Inicializar (una sola vez por proyecto)
cd backend
alembic init alembic

# Editar alembic.ini:
# sqlalchemy.url = postgresql://user:pass@localhost/dbname

# Editar alembic/env.py para importar Base y target_metadata
from app.models.base import Base
target_metadata = Base.metadata
```

### Comandos diarios

```bash
# Crear migracion despues de cambiar models
alembic revision --autogenerate -m "add users table"

# Aplicar migraciones
alembic upgrade head

# Un paso atras
alembic downgrade -1

# Ver historia
alembic history --verbose
```

## Uso en FastAPI (Dependency Injection)

```python
# app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserOut  # Pydantic schemas

app = FastAPI()

@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    return repo.create(user.model_dump())

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Transacciones

```python
# Explicita cuando necesitas rollback controlado
try:
    db.begin()
    repo.create(data)
    repo.create(otro_data)
    db.commit()
except Exception:
    db.rollback()
    raise
```

## Docker Compose (PostgreSQL)

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: nelson
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nelson"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## Pitfalls

- **Nunca** hacer `Base.metadata.create_all()` en produccion — usar Alembic
- `pool_pre_ping=True` es obligatorio en cloud para detectar conexiones rotas
- Evitar N+1 queries usando `selectinload` o `joinedload`
- Separar `models/` (SQLAlchemy) de `schemas/` (Pydantic) — no mezclar
- No pasar objetos ORM directamente a la respuesta HTTP; convertir a Pydantic
