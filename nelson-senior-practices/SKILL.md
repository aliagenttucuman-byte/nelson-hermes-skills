---
name: nelson-senior-practices
title: Senior Practices - Clean Code, Type Hints, Arquitectura
description: Buenas practicas de desarrollo senior para el equipo Nelson. Type hints estrictos, clean code, SOLID, docstrings Google-style, manejo de errores, inmutabilidad, inyeccion de dependencias.
skill: nelson-senior-practices
author: equipo-nelson
version: 1.0.0
keywords: [clean-code, type-hints, solid, senior, architecture, best-practices, python]
dependencies: [python-design-patterns, python-project-structure]
---

# Senior Practices - Equipo Nelson

> Codigo como lo escribiria un senior con 17 anos de experiencia.

## Type Hints Estrictos

```python
# ✅ BIEN - Todo tipado, sin Any
from typing import Optional, List, Dict, Protocol
from datetime import datetime

def get_user_by_email(email: str, db: Session) -> Optional[User]:
    ...

def create_items(items: List[ItemCreate], user_id: int) -> List[ItemOut]:
    ...

# ❌ MAL - Any, sin tipos
def process(data: Any) -> Any:
    ...
```

### mypy strict

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
warn_return_any = true
warn_unused_ignores = true
show_error_codes = true
```

## Clean Code

### Nombres

```python
# ✅ BIEN
class InvoiceProcessor:
    def calculate_total_with_tax(self, subtotal: Decimal, tax_rate: Decimal) -> Decimal:
        return subtotal * (1 + tax_rate)

# ❌ MAL
class Proc:
    def calc(self, a, b):
        return a * (1 + b)
```

### Funciones pequenas

```python
# ✅ BIEN - Una responsabilidad
 def validate_email_format(email: str) -> bool:
     pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
     return re.match(pattern, email) is not None

# ❌ MAL - Todo en una funcion gigante
 def process_user(data):
     # validar, guardar, enviar email, loguear...
```

### Early returns

```python
# ✅ BIEN
 def get_user(user_id: int, db: Session) -> User:
     if user_id <= 0:
         raise ValueError("user_id must be positive")

     user = db.get(User, user_id)
     if not user:
         raise HTTPException(status_code=404, detail="User not found")

     if not user.is_active:
         raise HTTPException(status_code=403, detail="User inactive")

     return user

# ❌ MAL - Nesting profundo
 def get_user(user_id: int, db: Session):
     if user_id > 0:
         user = db.get(User, user_id)
         if user:
             if user.is_active:
                 return user
             else:
                 raise HTTPException(403)
         else:
             raise HTTPException(404)
     else:
         raise ValueError()
```

## Docstrings Google Style

```python
def process_document(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
) -> List[DocumentChunk]:
    """Procesar un documento y extraer chunks de texto.

    Args:
        file_bytes: Contenido del archivo en bytes.
        filename: Nombre original del archivo.
        mime_type: Tipo MIME del archivo (ej: 'application/pdf').

    Returns:
        Lista de chunks de texto con metadata.

    Raises:
        ValueError: Si el formato no esta soportado.
        ProcessingError: Si falla la extraccion.

    Example:
        >>> chunks = process_document(b"...", "doc.pdf", "application/pdf")
        >>> print(chunks[0].text)
        "Texto extraido..."
    """
```

## Manejo de Errores

```python
# ✅ BIEN - Excepciones custom, mensajes claros
from fastapi import HTTPException

class BusinessError(Exception):
    """Error de reglas de negocio."""
    pass

class ResourceNotFoundError(BusinessError):
    pass

def get_user(user_id: int) -> User:
    user = repo.get(user_id)
    if not user:
        raise ResourceNotFoundError(f"User with id={user_id} not found")
    return user

# En API layer se traduce a HTTP
@app.get("/users/{user_id}")
def read_user(user_id: int):
    try:
        return get_user(user_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ❌ MAL - Capturar todo, perder info
 try:
     do_something()
 except Exception:
     pass  # Silenciar errores = debugging nightmare
```

## SOLID en Python

### S - Single Responsibility

```python
# ❌ MAL - Hace todo
class UserManager:
    def create_user(self, data): ...
    def send_welcome_email(self, user): ...
    def log_activity(self, action): ...

# ✅ BIEN - Separado
class UserService:
    def create(self, data) -> User: ...

class EmailService:
    def send_welcome(self, user: User) -> None: ...

class AuditService:
    def log(self, action: str, user_id: int) -> None: ...
```

### O - Open/Closed

```python
# ✅ BIEN - Extensible sin modificar
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def send(self, message: str, recipient: str) -> None:
        ...

class EmailNotifier(Notifier):
    def send(self, message: str, recipient: str) -> None:
        ...

class SlackNotifier(Notifier):
    def send(self, message: str, recipient: str) -> None:
        ...

# Uso
notifiers: List[Notifier] = [EmailNotifier(), SlackNotifier()]
for notifier in notifiers:
    notifier.send("Alert!", "team@example.com")
```

### D - Dependency Inversion

```python
# ✅ BIEN - Depender de abstracciones
class UserRepository(Protocol):
    def get(self, id: int) -> Optional[User]: ...
    def create(self, user: UserCreate) -> User: ...

class SQLUserRepository:
    def get(self, id: int) -> Optional[User]: ...

class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

# Testing facil con mock
service = UserService(repo=MockUserRepository())
```

## Inmutabilidad

```python
from dataclasses import dataclass, field
from typing import FrozenSet

@dataclass(frozen=True)
class Config:
    """Configuracion inmutable."""
    name: str
    debug: bool = False
    allowed_hosts: FrozenSet[str] = field(default_factory=frozenset)

# ✅ BIEN - Crear nuevo en vez de mutar
config = Config(name="app", debug=True)
new_config = Config(name="app", debug=False, allowed_hosts={"example.com"})

# ❌ MAL - Mutar estado global
CONFIG["debug"] = True  # Race conditions, side effects
```

## Inyeccion de Dependencias en FastAPI

```python
# app/api/deps.py
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user import UserRepository
from app.services.email import EmailService

def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_email_service() -> EmailService:
    return EmailService()

# Uso
@app.post("/users")
def create_user(
    data: UserCreate,
    repo: UserRepository = Depends(get_user_repo),
    email_svc: EmailService = Depends(get_email_service),
):
    user = repo.create(data)
    email_svc.send_welcome(user)
    return user
```

## Validacion con Pydantic

```python
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
```

## Workflow de sincronizacion al repo

El equipo Nelson mantiene un repo de skills y memoria (`nelson-hermes-skills`).
Regla de oro: **solo sincronizar cuando la informacion sea valiosa o haya cambios importantes**.

- ❌ No sincronizar en cada modificacion menor.
- ✅ Sincronizar cuando: se crea una skill nueva, se descubre un fix no trivial, se actualiza memoria con datos duraderos (hardware, preferencias del usuario, convenciones de proyecto).
- ✅ Dejar que el usuario decida cuando es el momento de hacer backup.
- ✅ Usar los scripts `sync-to-repo.sh` y `sync-from-repo.sh` del repo.

## Regla de los 3 intentos (Workflow con Nelson)

> Frase guia de Nelson: **"Si no podes, no sigas"**. Y: **"Vos tenes que parar solo, y hablar conmigo para que lo revaluemos."**

Cuando un proceso tecnico falla repetidamente, **parar despues de 2-3 intentos y consultar al usuario para revaluar**. No insistir indefinidamente en un approach que no funciona.

```
Intento 1 -> Falla
Intento 2 -> Falla  
Intento 3 -> Aun falla -> PARAR. Informar al usuario y revaluar juntos.
```

**NO hacer:**
- Seguir reintentando el mismo comando 4+ veces sin cambiar el approach
- Probar variaciones infinitas de la misma solucion
- Ocultar los errores o resumirlos demasiado

**SI hacer:**
- Parar solo antes de que el usuario tenga que decirlo
- Informar claramente: que se intento, que fallo, por que se detuvo
- Proponer 1-2 alternativas concretas y pedir decision del usuario
- Dejar que Nelson decida si cambiar de estrategia o seguir

Esto aplica a: builds, deploys, configuraciones de infra, debugging, cualquier proceso que se atasca. Nelson prefiere revaluar a perder tiempo en loops infinitos. La frase "nadie nos apura" aplica: pasito a pasito, con OK explicito en cada etapa significativa.

## Checklist de codigo senior

- [ ] Todas las funciones tienen type hints (sin Any)
- [ ] mypy --strict pasa sin errores
- [ ] Docstrings en todas las funciones publicas
- [ ] Nombres descriptivos (sin abreviaciones crypticas)
- [ ] Funciones con una sola responsabilidad (<20 lineas ideal)
- [ ] Early returns, sin nesting profundo
- [ ] Excepciones custom con mensajes claros
- [ ] No mutar estado global
- [ ] Depender de abstracciones (Protocol/ABC)
- [ ] Pydantic para validacion de inputs
- [ ] Logging estructurado (no print)
- [ ] Tests unitarios con fixtures tipados

## Pitfalls

- `Any` es la excepcion, no la regla
- Funciones de 100+ lineas son un smell
- Excepciones genericas (`except Exception`) ocultan bugs
- Estado mutable compartido entre requests causa race conditions
- Docstrings vacias (`"""TODO""") son peor que nada
- Hardcodear config en vez de inyectarla
