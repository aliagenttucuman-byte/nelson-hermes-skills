#!/usr/bin/env bash
# Respalda un SQLite con .backup (atómico, no requiere downtime).
# Uso: backup-sqlite.sh <db_path> <backup_dir> [name]
set -euo pipefail

DB_PATH="${1:?Path al .db requerido}"
BACKUP_DIR="${2:?Dir de backup requerido}"
NAME="${3:-$(basename "$DB_PATH" .db)}"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
DEST="${BACKUP_DIR}/${NAME}-${STAMP}.db"

mkdir -p "$BACKUP_DIR"
# .backup es atómico: no rompe la DB aunque haya escrituras concurrentes
sqlite3 "$DB_PATH" ".backup '$DEST'"

# Verificar integridad del backup
INTEGRITY=$(sqlite3 "$DEST" "PRAGMA integrity_check;" | head -1)
if [[ "$INTEGRITY" != "ok" ]]; then
  echo "ERROR: backup $DEST falló integrity_check: $INTEGRITY" >&2
  rm -f "$DEST"
  exit 1
fi

echo "✓ $NAME backed up to $DEST ($(du -h "$DEST" | cut -f1))"
