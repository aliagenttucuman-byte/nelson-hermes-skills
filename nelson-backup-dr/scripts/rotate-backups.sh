#!/usr/bin/env bash
# Rota los backups: conserva N diarios, M semanales.
# Uso: rotate-backups.sh <backup_dir> <keep_daily> <keep_weekly> [pattern]
set -euo pipefail

BACKUP_DIR="${1:?Backup dir requerido}"
KEEP_DAILY="${2:-7}"
KEEP_WEEKLY="${3:-4}"
PATTERN="${4:-*}"

echo "Rotando $BACKUP_DIR (pattern: $PATTERN)..."

# Mover los más viejos de 7 días a weekly
mkdir -p "$BACKUP_DIR/weekly"
find "$BACKUP_DIR" -maxdepth 1 -name "$PATTERN" -mtime +7 -exec mv {} "$BACKUP_DIR/weekly/" \; 2>/dev/null || true

# Weekly: conservar solo los últimos N
if [[ -d "$BACKUP_DIR/weekly" ]]; then
  ls -t "$BACKUP_DIR/weekly/" 2>/dev/null | tail -n +$((KEEP_WEEKLY + 1)) | while read -r old; do
    if [[ -n "$old" ]]; then
      rm -f "$BACKUP_DIR/weekly/$old"
      echo "  borrado: weekly/$old"
    fi
  done
fi

# Daily: conservar solo los últimos N
ls -t "$BACKUP_DIR" -maxdepth 1 -name "$PATTERN" -type f 2>/dev/null | tail -n +$((KEEP_DAILY + 1)) | while read -r old; do
  if [[ -n "$old" ]]; then
    rm -f "$old"
    echo "  borrado: $old"
  fi
done

echo "✓ Rotación completa"
