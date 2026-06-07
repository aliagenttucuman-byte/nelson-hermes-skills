#!/usr/bin/env bash
# Respalda una DB PostgreSQL con pg_dump desde dentro del container.
# Uso: backup-postgres.sh <container_name> <db_name> <user> <backup_dir>
set -euo pipefail

CONTAINER="${1:?Container name requerido}"
DB_NAME="${2:?DB name requerido}"
DB_USER="${3:-postgres}"
BACKUP_DIR="${4:?Backup dir requerido}"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
DEST="${BACKUP_DIR}/dump-${STAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

# pg_dump desde dentro del container (no requiere acceso directo al puerto)
docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$DEST"

# Verificar que el gzip no esté vacío y sea válido
if ! gunzip -t "$DEST" 2>/dev/null; then
  echo "ERROR: backup $DEST corrupto" >&2
  rm -f "$DEST"
  exit 1
fi

echo "✓ $DB_NAME backed up to $DEST ($(du -h "$DEST" | cut -f1))"
