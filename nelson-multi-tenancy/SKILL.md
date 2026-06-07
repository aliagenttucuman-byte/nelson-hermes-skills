---
name: nelson-multi-tenancy
description: Patrones de aislamiento multi-tenant para el stack del equipo Nelson (FastAPI + SQLAlchemy + PostgreSQL + Qdrant + Redis). Tres estrategias comparadas (DB separada, schema separado, row-level con tenant_id), guía de decisión, implementación concreta de tenant_id en cada capa, trampas comunes. Crítico antes de onboardear el 2do cliente RAG.
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [multi-tenant, arquitectura, sqlalchemy, qdrant, postgresql, fastapi, nelson]
    category: software-development
    requires_toolsets: [terminal]
---

# nelson-multi-tenancy

> **Trigger:** Onboarding de un segundo cliente en un mismo servicio (RAG, ForestAI, Excel Merger), o pedido de Nelson para evaluar si la infra actual soporta multi-tenant. Antes de tocar código: leer § 2 (Estrategias) y § 3 (Decisión).

## Principio rector

> "El aislamiento del tenant no es una feature, es un invariante. Si se rompe, el incidente es de los que se cuentan en titulares."

Un solo bug en la capa de aislamiento = cliente A ve datos de cliente B = Sev-1 legal, no técnico.

## 1. El stack del equipo Nelson (a junio 2026)

| Capa | Tecnología | Notas |
|------|-----------|-------|
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 | Repository pattern (ver `nelson-project-bootstrap`) |
| Auth | JWT con python-jose | `nelson-security` |
| DB relacional | PostgreSQL 16 | Alembic para migraciones |
| Vector store | Qdrant | Filtrado por metadata (¡clave para multi-tenant!) |
| Cache/cola | Redis 7 | Cache + broker Celery |
| Background jobs | Celery | Workers separados por ambiente |
| Storage | MinIO o filesystem | Pensar en prefijos por tenant |

**Todas las decisiones de abajo asumen este stack.** Si tu servicio usa otra cosa, traducir.

## 2. Las tres estrategias

### 2.1 DB separada (un PostgreSQL por tenant)

**Qué es:** cada cliente tiene su propia base de datos PostgreSQL completa, con su propio schema migrations, su propio connection pool, y usualmente su propio container/servidor.

```
tenant_a_db  →  postgresql://...tenant_a
tenant_b_db  →  postgresql://...tenant_b
tenant_c_db  →  postgresql://...tenant_c
```

**Pros:**
- Aislamiento físico real. Imposible leak cross-tenant por bug de SQL.
- Backup / restore por cliente trivial (`pg_dump` por DB).
- Cliente "ruidoso" no afecta al resto (lock contention, queries pesadas).
- Compliance: HIPAA, SOC2, datos financieros regulados (ej: Expreso Bisonte).
- Migración por cliente sin coordinar releases entre todos.

**Contras:**
- Costo de infra: N× RAM/CPU del servidor PG. No escala a 50+ tenants baratos.
- Migraciones se ejecutan N veces. Sin automatización es pesadilla.
- Connection pool por app: hay que multiplexar el pool según el tenant del request.
- Métricas y observabilidad: hay que agregar a mano o tener un stack por DB.

**Cuándo elegir:** clientes grandes (>10k usuarios), datos muy sensibles (financiero, salud, legal), SLA diferenciado, 1-15 tenants grandes, regulación estricta.

### 2.2 Schema separado (un DB, un schema por tenant)

**Qué es:** una sola instancia de PostgreSQL, pero cada tenant vive en su propio `schema` (`tenant_a`, `tenant_b`, etc.). `search_path` se setea por conexión.

```
postgres://shared_db
  ├── schema: tenant_a (con todas sus tablas)
  ├── schema: tenant_b
  └── schema: tenant_c
```

**Pros:**
- Aislamiento lógico fuerte: `SET search_path TO tenant_a` por request.
- Una sola DB que mantener, un backup lógico agregado, métricas centralizadas.
- Migración se corre una vez y se aplica a todos los schemas con un loop.
- Más barato que DB separada (1× PG, no N×).

**Contras:**
- Postgres limita la cantidad de schemas por performance a ~5k. Más allá, ver 2.1 o sharding.
- El "ruido" de un tenant (query lenta, table bloat) afecta a todos en la misma DB.
- Connection pool: hay que setear search_path en cada conexión, o usar uno por tenant.
- Backup granular: pg_dump de un schema es posible pero no es atómico con otros schemas.

**Cuándo elegir:** 15-200 tenants medianos, mismos productos, datos sensibles pero no tanto como para DB separada.

### 2.3 Row-level con tenant_id (un DB, un schema, columna tenant_id en cada tabla)

**Qué es:** una sola DB, un solo schema, todas las tablas tienen columna `tenant_id UUID NOT NULL`. Toda query filtra por `tenant_id`. Row-Level Security (RLS) de Postgres como red de seguridad.

```
postgres://shared_db
  └── public
       ├── users (id, tenant_id, email, ...)
       ├── documents (id, tenant_id, content, ...)
       └── ...
```

**Pros:**
- La más barata. Una DB, un schema, un pool, una migración.
- Escala a miles de tenants sin despeinarse (Postgres maneja millones de rows).
- Métricas, observabilidad, backups: todo standard.
- Onboarding de tenant nuevo = 0 infra. Solo crear fila en `tenants` y asignar `tenant_id` en las filas.

**Contras:**
- **El más peligroso.** Un `WHERE` mal escrito = leak. Por eso **RLS de Postgres es obligatorio**, no opcional.
- Compliance/legal: para algunos sectores no alcanza, piden aislamiento físico.
- Migración masiva: cuando un tenant crece mucho, sacarlo a su propia DB es costoso.
- "Vecino ruidoso" sigue siendo un problema (todos comparten recursos).

**Cuándo elegir:** muchos tenants chicos-medianos, mismos productos, datos no ultra-sensibles, equipo pequeño. **Es lo que usa el 80% de SaaS moderno.**

## 3. Guía de decisión

| Pregunta | DB separada | Schema separado | Row-level + RLS |
|----------|:-----------:|:---------------:|:---------------:|
| ¿Clientes son grandes (>10k usuarios)? | ✅ | ⚠️ | ❌ |
| ¿Más de 50 tenants? | ❌ (caro) | ⚠️ (<200) | ✅ |
| ¿Datos regulados (financiero, salud, legal)? | ✅ | ⚠️ | ❌ |
| ¿Mismo producto, mismo modelo, misma UI para todos? | ⚠️ | ✅ | ✅ |
| ¿Equipo chico (<5 devs)? | ❌ | ⚠️ | ✅ |
| ¿Necesitás on/off-boarding instantáneo? | ❌ | ❌ | ✅ |
| ¿SLA diferenciado por cliente? | ✅ | ⚠️ | ⚠️ |

### Reglas de oro

1. **Si tenés menos de 3 tenants, no оптимизés para 100.** Arrancá con row-level + RLS. Migrar después es posible (y difícil).
2. **Si uno de tus clientes es financiero/salud/legal → DB separada o schema separado.** No negocies.
3. **Si todos tus clientes son del mismo vertical y mismo producto → row-level + RLS.**
4. **RLS de Postgres es OBLIGATORIO en row-level.** No es opcional, es la red de seguridad.
5. **Qdrant SIEMPRE filtrá por tenant_id en metadata del payload.** No hay otra forma de aislar vectores.

### Decisión recomendada para el equipo Nelson (a junio 2026)

Teniendo en cuenta:
- Expreso Bisonte: datos financieros/facturación (sensible)
- ForestAI: clientes actuales y ReforestLatam potencial (drones, ortofotos)
- chat-con-documentos: PoC genérica
- Equipo chico (Nelson + 2 agentes IA), tiempo limitado

**Recomendación:** empezar con **row-level + RLS** para todos los servicios nuevos (más barato, más rápido de implementar, escala bien). Marcar como **DB separada** cuando se confirme un cliente financiero grande o de salud. Los RAG PoCs que ya están corriendo se pueden migrar gradualmente — el `tenant_id` se agrega sin romper nada si las queries actuales no filtran (mejor agregar la columna + RLS primero, después purgar las queries sin filtro con tests).

## 4. Implementación por capa (patrón row-level + RLS)

### 4.1 Capa DB: schema y migraciones

**Tabla `tenants` (siempre presente):**

```python
# app/models/tenant.py
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(32), default="active")  # active, suspended, churned
    plan = Column(String(32), default="standard")  # standard, pro, enterprise
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Convención para tablas de tenant:**

```python
# Toda tabla tenant-scoped arranca así
class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    # ... resto de columnas
    __table_args__ = (
        Index("ix_documents_tenant_id_created", "tenant_id", "created_at"),
    )
```

**Regla:** `tenant_id` SIEMPRE primero en índices compuestos. SIEMPRE.

**Alembic — template de migración:**

```python
# alembic/versions/xxxx_add_tenant_id_to_documents.py
def upgrade():
    # 1. Crear tabla tenants si no existe (idempotente)
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("plan", sa.String(32), server_default="standard"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # 2. Backfill tenant_id en tablas existentes
    #    (en desarrollo: asignar todo a un tenant "default")
    op.execute("INSERT INTO tenants (id, slug, name) VALUES (gen_random_uuid(), 'default', 'Default tenant')")
    op.add_column("documents", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE documents SET tenant_id = (SELECT id FROM tenants WHERE slug='default')")
    op.alter_column("documents", "tenant_id", nullable=False)
    op.create_foreign_key("fk_documents_tenant", "documents", "tenants", ["tenant_id"], ["id"])
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])
```

### 4.2 Row-Level Security (la red de seguridad)

**Habilitar RLS y crear política por tabla:**

```sql
-- Para cada tabla tenant-scoped
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Política: solo se ven filas donde tenant_id = el tenant_id de la sesión
CREATE POLICY tenant_isolation ON documents
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**Forzar RLS incluso para el dueño de la tabla (súper usuario y roles con BYPASSRLS lo saltean):**

```sql
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
```

**Pitfall crítico:** los roles de Postgres con `BYPASSRLS` (típicamente el `postgres` user) se saltean RLS. **No usar el `postgres` user desde la app.** Crear un rol dedicado para la app:

```sql
CREATE ROLE app_user NOINHERIT LOGIN PASSWORD '...';
GRANT CONNECT ON DATABASE mydb TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- NO BYPASSRLS — esto es intencional
```

### 4.3 Capa App: setear el tenant por request

**Middleware FastAPI que setea la variable de sesión de Postgres:**

```python
# app/core/tenant_context.py
from contextvars import ContextVar
from uuid import UUID

current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id() -> UUID:
    tid = current_tenant_id.get()
    if tid is None:
        raise RuntimeError("Tenant no seteado. ¿Falta el middleware?")
    return tid
```

```python
# app/middleware/tenant.py
from uuid import UUID
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.tenant_context import current_tenant_id
from app.core.database import set_tenant_on_session
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Setea el tenant_id en la sesión de Postgres antes de que el endpoint corra.
    Lee el tenant del JWT (preferido) o del header X-Tenant-Id (alternativa, menos segura).
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Opción A: del JWT (recomendado)
        tenant_id = None
        user = getattr(request.state, "user", None)
        if user and "tenant_id" in user:
            tenant_id = UUID(user["tenant_id"])

        # Opción B: header explícito (para service-to-service con API key)
        if not tenant_id:
            header_tid = request.headers.get("X-Tenant-Id")
            if header_tid:
                tenant_id = UUID(header_tid)

        if not tenant_id:
            return JSONResponse(
                {"detail": "Tenant no identificado en la request"},
                status_code=400,
            )

        # Setear en ContextVar + sesión de DB
        token = current_tenant_id.set(tenant_id)
        try:
            async with db_session() as session:
                await session.execute(
                    text("SET app.current_tenant_id = :tid"),
                    {"tid": str(tenant_id)},
                )
                # Adjuntar la sesión al request para que el endpoint la reuse
                request.state.db = session
                response = await call_next(request)
                return response
        finally:
            current_tenant_id.reset(token)
```

**Pitfall:** `SET` en Postgres es por sesión. Si usás connection pool, tenés que asegurarte de que la misma sesión se use durante toda la request. Dos opciones:
- Usar `NullPool` y crear conexión por request (caro pero simple)
- Usar `set_session` de SQLAlchemy con un `after_begin` event listener
- Usar SQLAlchemy `Session` con un `event.listens_for(Session, "after_begin")` que ejecute el SET

### 4.4 Capa ORM: tests anti-leak

**Test obligatorio:** intentar leer fila de otro tenant debe fallar.

```python
# app/tests/test_tenant_isolation.py
import pytest
from uuid import uuid4
from app.models import Document, Tenant


async def test_cannot_read_other_tenant_document(db_with_tenant):
    # Tenant A crea un documento
    tenant_a = await create_tenant(slug="a")
    tenant_b = await create_tenant(slug="b")
    doc = await create_document(tenant_id=tenant_a.id, content="secreto A")

    # Tenant B intenta leer TODOS los documentos
    with set_tenant_context(tenant_b.id):
        results = await db.query(Document).all()

    # El doc de A NO debe aparecer
    assert doc.id not in [r.id for r in results]
    assert len(results) == 0


async def test_cannot_update_other_tenant_document(db_with_tenant):
    tenant_a = await create_tenant(slug="a")
    tenant_b = await create_tenant(slug="b")
    doc = await create_document(tenant_id=tenant_a.id, content="secreto A")

    with set_tenant_context(tenant_b.id):
        result = await db.execute(
            update(Document).where(Document.id == doc.id).values(content="hack")
        )
        await db.commit()

    # Verificar que el doc de A sigue intacto
    await set_tenant_context(tenant_a.id)
    fresh = await db.get(Document, doc.id)
    assert fresh.content == "secreto A"  # NO fue modificado


async def test_cannot_delete_other_tenant_document(db_with_tenant):
    # Similar a update, verificar que DELETE no afecta otras filas
    ...
```

**Estos tests son tu CI guard.** Si alguien rompe RLS, fallan antes de llegar a prod.

### 4.5 Capa Qdrant: filtrado por tenant_id

**Qdrant no tiene RLS nativo.** El aislamiento es responsabilidad de la app: filtrá SIEMPRE por `tenant_id` en el payload.

**Schema de collection (punto clave):**

```python
# app/services/vector_store.py
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType, Distance, VectorParams
import uuid

COLLECTION_NAME = "documents"


def init_collection(client: QdrantClient):
    """Idempotente: solo crea si no existe."""
    if COLLECTION_NAME not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

    # Crear índice en el campo tenant_id del payload (clave para performance)
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="tenant_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="tenant_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
```

**Insertar SIEMPRE con tenant_id en el payload:**

```python
def upsert_chunks(client: QdrantClient, tenant_id: uuid.UUID, chunks: list[dict], vectors: list[list[float]]):
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "tenant_id": str(tenant_id),  # OBLIGATORIO en todo punto
                "document_id": chunk["doc_id"],
                "text": chunk["text"],
                "chunk_index": chunk["index"],
                "metadata": chunk.get("metadata", {}),
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
```

**Buscar SIEMPRE con filtro de tenant_id:**

```python
def search(client: QdrantClient, tenant_id: uuid.UUID, query_vector: list[float], top_k: int = 5):
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=Filter(must=[
            FieldCondition(
                key="tenant_id",
                match=MatchValue(value=str(tenant_id)),  # FILTRO OBLIGATORIO
            )
        ]),
        limit=top_k,
    )
    return results


# Helper para que NUNCA se te olvide el filtro
def require_tenant_filter(tenant_id: uuid.UUID) -> Filter:
    """Único punto de creación de Filter. Si lo querés evitar, tenés que pasar por acá."""
    return Filter(must=[
        FieldCondition(key="tenant_id", match=MatchValue(value=str(tenant_id))),
    ])
```

**Alternativa por colección:** en lugar de filtrar por metadata, podés tener una colección por tenant (`documents_tenant_a`, `documents_tenant_b`). Es la versión Qdrant de "schema separado". Úsalo si:
- Tenés pocos tenants grandes
- Querés borrar todo el contenido de un tenant con `delete_collection` (compliance)
- Cada tenant tiene modelos de embeddings diferentes

### 4.6 Capa Storage: prefijos por tenant

**Filesystem o MinIO:**

```python
# Patrón: <bucket>/<tenant_slug>/<resto_del_path>
def tenant_path(tenant_slug: str, *parts: str) -> str:
    """
    >>> tenant_path("expreso_bisonte", "uploads", "factura_001.pdf")
    'expreso_bisonte/uploads/factura_001.pdf'

    Si el tenant_slug viene de input del usuario, validá que no tenga '/' ni '..'
    """
    safe_slug = slugify(tenant_slug)  # ver nelson-security para implementación
    return os.path.join(safe_slug, *parts)
```

**MinIO con pre-signed URLs: el prefijo se valida en el backend antes de generar la URL.**

### 4.7 Capa Celery: tenant en cada task

```python
# app/tasks/document_tasks.py
from app.core.tenant_context import current_tenant_id

@app.task
def process_document(tenant_id: str, document_id: str):
    """El tenant_id va como argumento, no se infiere del contexto."""
    token = current_tenant_id.set(UUID(tenant_id))
    try:
        # ... el job corre con el tenant seteado
        # ... todas las queries a DB y Qdrant filtran por este tenant
        ...
    finally:
        current_tenant_id.reset(token)
```

**Regla:** el tenant SIEMPRE viaja como argumento explícito en tasks. Nunca inferirlo de variables globales en el worker.

## 5. Onboarding y offboarding de tenants

### Onboarding (nuevo cliente)

```python
# scripts/onboard_tenant.py
import argparse
from app.core.database import db_session
from app.models import Tenant
from app.services.vector_store import init_collection_for_tenant

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True, help="expreso_bisonte, forestai, etc.")
    p.add_argument("--name", required=True)
    p.add_argument("--plan", default="standard")
    args = p.parse_args()

    with db_session() as s:
        tenant = Tenant(slug=args.slug, name=args.name, plan=args.plan)
        s.add(tenant)
        s.commit()
        print(f"✓ Tenant creado: {tenant.id}")

    init_collection_for_tenant(tenant.id)
    print(f"✓ Colección Qdrant inicializada para {args.slug}")

if __name__ == "__main__":
    main()
```

### Offboarding (cliente se va, o cumplimiento legal)

**Con row-level:** deshabilitar el tenant + borrar sus filas + opcionalmente borrar de Qdrant.

```python
# scripts/offboard_tenant.py
def offboard(slug: str, delete_data: bool = True):
    with db_session() as s:
        tenant = s.query(Tenant).filter_by(slug=slug).one()

        if delete_data:
            # Borrar todas las filas del tenant (RLS desactivado temporalmente para este script)
            with rls_disabled():
                for model in TENANT_SCOPED_MODELS:
                    s.query(model).filter_by(tenant_id=tenant.id).delete()
            # Borrar vectores de Qdrant
            qdrant.delete(
                collection_name=COLLECTION_NAME,
                points_selector=FilterSelector(filter=Filter(must=[
                    FieldCondition(key="tenant_id", match=MatchValue(value=str(tenant.id)))
                ])),
            )
            # Borrar archivos
            storage.purge_prefix(tenant_path(tenant.slug))

        tenant.status = "churned"
        s.commit()
        print(f"✓ Tenant {slug} dado de baja")
```

## 6. Checklist de seguridad multi-tenant

Antes de mergear a main cualquier cambio que toque datos tenant-scoped:

- [ ] ¿La nueva query filtra explícitamente por `tenant_id`? (o usa el middleware)
- [ ] ¿RLS está habilitada y forzada en la tabla nueva?
- [ ] ¿La búsqueda en Qdrant usa `require_tenant_filter(tenant_id)`?
- [ ] ¿El nuevo endpoint requiere auth (JWT con `tenant_id`)?
- [ ] ¿El nuevo path de storage usa `tenant_path(tenant.slug, ...)`?
- [ ] ¿Si es una task de Celery, recibe `tenant_id` como argumento explícito?
- [ ] ¿Hay un test de aislamiento que verifica que tenant B no ve/modifica datos de tenant A?

**Si contestás "no sé" a alguna → volver a hacerlo, no mergear.**

## 7. Migración gradual de servicios existentes

Para los servicios ya en producción sin multi-tenancy (ej: los RAG PoCs):

1. **Fase 1: agregar columna + RLS sin tocar queries existentes.**
   - Alembic migration: agregar `tenant_id UUID NULL` en cada tabla, crear tabla `tenants`, backfill con un tenant "default", volver NOT NULL.
   - Habilitar RLS con política que filtra por `app.current_tenant_id`. Para que las queries existentes sigan andando, setear el `default` en cada conexión.

2. **Fase 2: introducir el middleware y empezar a setear el tenant en cada endpoint.**
   - Empezar por endpoints read-only.
   - Verificar con tests que el RLS efectivamente filtra.

3. **Fase 3: agregar tests de aislamiento.**
   - Por cada endpoint nuevo, un test que verifica que no hay cross-tenant access.

4. **Fase 4: forzar RLS en CI.**
   - Los tests de aislamiento son parte del pipeline. Si fallan, no se mergea.

5. **Fase 5: segundo cliente real.**
   - Recién ahora se puede onbordar un segundo tenant con confianza.

**No saltearse fases.** Cada fase depende de la anterior.

## Pitfalls

1. **RLS "habilitada" pero no "forzada".** `ENABLE` permite que el dueño de la tabla la ignore si tiene `BYPASSRLS`. Usar `FORCE` para que aplique a todos. Verificar con `SELECT current_user, session_user;` desde la app.
2. **Filtro de Qdrant olvidado.** Es el error #1. La app tiene RLS en DB pero busca en Qdrant sin filtro. Mitigación: helper `require_tenant_filter()` que es la única forma de crear un `Filter`. Buscar y fallar el code review si hay `client.search(...)` sin `require_tenant_filter`.
3. **Tenant en JWT pero no verificado.** Si decodificás el JWT y confiás en el `tenant_id` adentro, alguien con un JWT firmado para tenant A puede venir con uno alterado. **Firmá y verificá** con la clave del backend. Ver `nelson-security`.
4. **Connection pool compartido entre tenants.** Si el pool es compartido y no seteás el `app.current_tenant_id` por request, las queries de un request pueden leer datos de otro. Usar middleware que setea el tenant ANTES de que la sesión se preste.
5. **`SET` con scope equivocado.** `SET app.current_tenant_id` aplica a la sesión, no al schema. Si usás `SET LOCAL` dentro de una transacción, perfecto. Si usás `SET` sin scope, queda para toda la conexión (peligro con pool).
6. **Task de Celery sin tenant_id.** Un worker procesa tareas de muchos tenants. Si la task no recibe el `tenant_id` explícito, no sabe qué contexto setear. Pasarlo siempre como argumento.
7. **Backups filtrados por cliente.** Si tenés un cliente que se va y te pide "borrá todo", necesitás poder borrar selectivamente. Si tenés row-level, OK. Si tenés DB separadas, es `pg_dump` + `drop database`. Si no podés hacerlo, tenés un problema de compliance.
8. **Tests sin RLS activado.** Si los tests corren con un rol que tiene `BYPASSRLS`, los tests de aislamiento pasan pero RLS no está protegiendo nada en prod. Usar el mismo rol de app en CI.
9. **Soft delete sin tenant filter.** `DELETE FROM documents WHERE deleted_at IS NULL AND id = :id` parece seguro, pero si la fila tiene `tenant_id` distinto al del contexto, RLS la hace invisible. El problema es que también oculta el bug. Auditar queries de soft delete.
10. **Asumir que "no tengo multi-tenant" es seguro.** Si dos clientes diferentes suben documentos al mismo RAG PoC, ya son multi-tenant. La pregunta no es si necesitás multi-tenancy, es si lo estás haciendo implícita o explícitamente. **Explícita es más segura.**

## Referencias

- `nelson-security` — JWT, secretos, validaciones
- `nelson-project-bootstrap` — estructura de proyecto base
- `nelson-monitoring-observability` — health checks (incluir `tenant_id` en logs)
- `nelson-rag-pipeline` — pipeline RAG base a multi-tenancy-izar
- `references/decisions/` — ADRs específicos de cada proyecto (cuándo se eligió cada estrategia)
