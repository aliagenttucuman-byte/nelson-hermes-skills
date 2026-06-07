#!/usr/bin/env bash
# Respalda un volumen Docker como tar.gz.
# Uso: backup-docker-volume.sh <volume_name> <backup_dir>
set -euo pipefail

VOLUME="${1:?Volume name requerido}"
BACKUP_DIR="${2:?Backup dir requerido}"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
DEST="${BACKUP_DIR}/${VOLUME}-${STAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

# Levanta un container efímero, monta el volumen, lo tara
docker run --rm \
  -v "${VOLUME}:/source:ro" \
  -v "${BACKUP_DIR}:/backup" \
  alpine:latest \
  tar czf "/backup/${VOLUME}-${STAMP}.tar.gz" -C /source .

if [[ ! -s "$DEST" ]]; then
  echo "ERROR: backup $DEST vacío" >&2
  exit 1
fi

echo "✓ $VOLUME backed up to $DEST ($(du -h "$DEST" | cut -f1))"
