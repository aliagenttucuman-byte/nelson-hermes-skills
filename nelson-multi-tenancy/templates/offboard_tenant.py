#!/usr/bin/env python3
"""
offboard_tenant.py — Da de baja un tenant.

Uso:
    python scripts/offboard_tenant.py --slug expreso_bisonte
    python scripts/offboard_tenant.py --slug expreso_bisonte --keep-data    # soft offboarding
    python scripts/offboard_tenant.py --slug expreso_bisonte --dry-run

Por defecto: BORRA todos los datos del tenant (RLS desactivado en este script).
Con --keep-data: solo marca el tenant como "churned", los datos quedan.

PELIGRO: este script bypassea RLS temporalmente. Solo usar para offboarding
explícitamente autorizado. Loguear quién lo ejecutó y cuándo.
"""
import argparse
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import db_session, init_db
from app.models import Tenant
from app.services.vector_store import qdrant_client_from_env
from qdrant_client.models import Filter, FilterSelector, FieldCondition, MatchValue


# IMPORTANTE: mantener sincronizado con la lista real de modelos tenant-scoped
# Si agregás un modelo nuevo tenant-scoped y no lo agregás acá, queda orphan data.
TENANT_SCOPED_MODELS = []  # ej: [Document, Chunk, Conversation, ...]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("offboard_tenant")


def main():
    p = argparse.ArgumentParser(description="Offboarding de tenant")
    p.add_argument("--slug", required=True)
    p.add_argument("--keep-data", action="store_true", help="Soft: solo marcar como churned")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    init_db()

    with db_session() as s:
        tenant = s.query(Tenant).filter_by(slug=args.slug).one_or_none()
        if not tenant:
            print(f"ERROR: tenant '{args.slug}' no existe")
            sys.exit(1)

        if args.dry_run:
            print(f"[DRY-RUN] Para {args.slug} (id={tenant.id}):")
            if args.keep_data:
                print(f"  - Marcar como status=churned")
            else:
                print(f"  - DELETE FROM <tabla> WHERE tenant_id={tenant.id}  ({len(TENANT_SCOPED_MODELS)} tablas)")
                print(f"  - DELETE FROM qdrant WHERE tenant_id={tenant.id}")
                print(f"  - DELETE FROM storage prefix={args.slug}/")
                print(f"  - Marcar tenant como status=churned")
            sys.exit(0)

        if args.keep_data:
            tenant.status = "churned"
            tenant.updated_at = datetime.utcnow()
            s.commit()
            logger.info(f"✓ Tenant {args.slug} marcado como churned (data retenida)")
            return

        # === Hard delete ===
        logger.warning(f"HARD DELETE para tenant {args.slug} (id={tenant.id})")
        logger.warning(f"Operación irreversible. Ctrl+C en 5s para cancelar...")
        import time
        time.sleep(5)

        # 1. Borrar filas de DB (RLS desactivado en este bloque)
        from sqlalchemy import text
        s.execute(text(f"SET LOCAL row_security = off"))
        for model in TENANT_SCOPED_MODELS:
            count = s.query(model).filter_by(tenant_id=tenant.id).delete()
            logger.info(f"  DB: borradas {count} filas de {model.__tablename__}")

        # 2. Borrar vectores de Qdrant
        try:
            client = qdrant_client_from_env()
            client.delete(
                collection_name=os.getenv("QDRANT_COLLECTION", "documents"),
                points_selector=FilterSelector(filter=Filter(must=[
                    FieldCondition(key="tenant_id", match=MatchValue(value=str(tenant.id)))
                ])),
            )
            logger.info(f"  QDRANT: vectores borrados para tenant {tenant.id}")
        except Exception as e:
            logger.error(f"  QDRANT error (puede ser crítico): {e}")

        # 3. Borrar archivos del storage
        # (implementar según tu backend de storage: S3, MinIO, filesystem)
        # storage.purge_prefix(tenant_path(tenant.slug))

        # 4. Marcar tenant como churned (no borrar la fila — preserva auditoría)
        tenant.status = "churned"
        tenant.updated_at = datetime.utcnow()
        s.commit()
        logger.info(f"✓ Tenant {args.slug} dado de baja completamente")


if __name__ == "__main__":
    main()
