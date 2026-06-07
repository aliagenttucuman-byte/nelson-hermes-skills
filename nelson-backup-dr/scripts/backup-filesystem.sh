#!/usr/bin/env bash
# Respalda un directorio como tar.gz excluyendo caches y node_modules.
# Uso: backup-filesystem.sh <source_dir> <backup_dir> [name]
set -euo pipefail

SOURCE="${1:?Source dir requerido}"
BACKUP_DIR="${2:?Backup dir requerido}"
NAME="${3:-$(basename "$SOURCE")}"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
DEST="${BACKUP_DIR}/${NAME}-${STAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

tar czf "$DEST" \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='dist' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='.mypy_cache' \
  --exclude='.pytest_cache' \
  --exclude='.next' \
  --exclude='.cache' \
  -C "$(dirname "$SOURCE")" \
  "$(basename "$SOURCE")"

echo "✓ $NAME backed up to $DEST ($(du -h "$DEST" | cut -f1))"
