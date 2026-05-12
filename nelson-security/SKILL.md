---
name: nelson-security
title: Seguridad - Auth JWT + OAuth2 + CORS + Rate Limiting
description: Patrones de seguridad para el equipo Nelson. JWT con python-jose, OAuth2 password flow en FastAPI, CORS, headers de seguridad, rate limiting, hash de passwords con bcrypt.
skill: nelson-security
author: equipo-nelson
version: 1.0.0
keywords: [jwt, oauth2, auth, security, cors, bcrypt, rate-limiting, fastapi]
dependencies: [fastapi, nelson-database]
---

# Seguridad - Equipo Nelson

## Stack

| Capa | Libreria | Version |
|------|----------|---------|
| Hash passwords | bcrypt | ^4.2 |
| JWT | python-jose[cryptography] | ^3.3 |
| Passlib | passlib[bcrypt] | ^1.7 |
| Rate limiting | slowapi | ^0.1 |
| CORS | FastAPI built-in | - |

## Hash de Passwords

```python
# app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

## JWT Tokens

```python
# app/core/jwt.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
```

## OAuth2 Password Flow en FastAPI

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.jwt import decode_token
from app.database import get_db
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token invalido")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido")

    repo = UserRepository(db)
    user = repo.get(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    return user
```

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import verify_password, get_password_hash
from app.core.jwt import create_access_token, create_refresh_token
from app.repositories.user import UserRepository
from app.schemas.auth import Token, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    repo = UserRepository(db)
    user = repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Email o password incorrectos")

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_by_email(user_in.email):
        raise HTTPException(status_code=400, detail="Email ya registrado")

    hashed = get_password_hash(user_in.password)
    user = repo.create({
        "email": user_in.email,
        "hashed_password": hashed,
        "full_name": user_in.full_name,
    })

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
```

## CORS

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "https://tudominio.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
    max_age=600,
)
```

## Headers de Seguridad

```python
# app/main.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## Rate Limiting (slowapi)

```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Uso en endpoint
from fastapi import Request as FastAPIRequest

@app.post("/auth/login")
@limiter.limit("5/minute")
def login(request: FastAPIRequest, ...):
    ...
```

## Dependencias Protegidas

```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")
    ...
```

## Configuracion de Entorno

```
# .env
SECRET_KEY=tu-clave-super-secreta-de-al-menos-32-caracteres
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

## Checklist de Seguridad

- [ ] `SECRET_KEY` minimo 32 chars, nunca hardcodeada
- [ ] Passwords hasheados con bcrypt
- [ ] CORS restrictivo (no `*` en produccion)
- [ ] Rate limiting en auth endpoints
- [ ] Headers de seguridad configurados
- [ ] Refresh tokens con expiracion mas larga que access tokens
- [ ] HTTPS obligatorio en produccion
- [ ] Tokens invalidados al cambiar password

## Pitfalls

- No usar `*` en `allow_origins` en produccion
- `SECRET_KEY` nunca en repos publicos — usar variables de entorno
- Access tokens cortos (15-30 min), refresh tokens largos (7-30 dias)
- No almacenar tokens en `localStorage` si hay XSS risk; usar `httpOnly` cookies
- Siempre validar `token_type == "access"` en endpoints protegidos
