#!/usr/bin/env python3
"""
onboard_tenant.py — Da de alta un tenant nuevo.

Uso:
    python scripts/onboard_tenant.py --slug expreso_bisonte --name "Expreso Bisonte SA"
    python scripts/onboard_tenant.py --slug forestai --name "ForestAI" --plan pro

Requiere:
    - DATABASE_URL en env o .env
    - QDRANT_URL en env o .env
    - Tabla `tenants` ya creada (migración 0001)

Idempotente: si el slug ya existe, no hace nada y avisa.
"""
import argparse
import os
import sys
import uuid
from datetime import datetime

# Ajustar import path según estructura del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import db_session, init_db
from app.models import Tenant
from app.services.vector_store import (
    init_qdrant_indexes_for_tenant,
    qdrant_client_from_env,
)


def main():
    p = argparse.ArgumentParser(description="Onboarding de tenant")
    p.add_argument("--slug", required=True, help="Identificador URL-safe único (ej: expreso_bisonte)")
    p.add_argument("--name", required=True, help="Nombre legible del cliente")
    p.add_argument("--plan", default="standard", choices=["standard", "pro", "enterprise"])
    p.add_argument("--dry-run", action="store_true", help="Solo muestra qué haría")
    args = p.parse_args()

    # Validar slug
    if not args.slug.replace("_", "").replace("-", "").isalnum():
        print(f"ERROR: slug '{args.slug}' debe ser alfanumérico con guiones o guiones bajos")
        sys.exit(1)

    if args.dry_run:
        print(f"[DRY-RUN] Crearía tenant:")
        print(f"  slug:  {args.slug}")
        print(f"  name:  {args.name}")
        print(f"  plan:  {args.plan}")
        sys.exit(0)

    init_db()

    with db_session() as s:
        existing = s.query(Tenant).filter_by(slug=args.slug).one_or_none()
        if existing:
            print(f"⚠ Tenant con slug '{args.slug}' ya existe (id={existing.id}, status={existing.status})")
            sys.exit(0)

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=args.slug,
            name=args.name,
            plan=args.plan,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        s.add(tenant)
        s.commit()
        tenant_id = tenant.id
        print(f"✓ Tenant creado:")
        print(f"  id:    {tenant_id}")
        print(f"  slug:  {tenant.slug}")
        print(f"  name:  {tenant.name}")
        print(f"  plan:  {tenant.plan}")

    # Inicializar índices de Qdrant para este tenant
    try:
        client = qdrant_client_from_env()
        init_qdrant_indexes_for_tenant(client, tenant_id)
        print(f"✓ Índices de Qdrant listos para {args.slug}")
    except Exception as e:
        print(f"⚠ Error inicializando Qdrant (no crítico si es offline): {e}")

    print(f"\nSiguiente paso:")
    print(f"  1. Crear usuario admin para este tenant (ver scripts/create_user.py)")
    print(f"  2. Subir documentos de prueba")
    print(f"  3. Verificar aislamiento con tests/test_tenant_isolation.py")


if __name__ == "__main__":
    main()
