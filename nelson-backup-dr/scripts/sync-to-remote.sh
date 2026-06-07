#!/usr/bin/env bash
# Sincroniza los backups locales a nelsondev vía rsync sobre Tailscale.
# Configurar alias SSH 'nelsondev' en ~/.ssh/config primero.
set -euo pipefail

REMOTE="${1:-nelsondev}"
REMOTE_DIR="${2:-~/backups-ai-server}"
LOCAL_DIR="/home/server/backups"

# Excluir caches y temporales
rsync -avz --delete \
  --exclude='*.tmp' \
  --exclude='.cache' \
  --exclude='verify/*.tmp' \
  "$LOCAL_DIR/" \
  "${REMOTE}:${REMOTE_DIR}/"

echo "✓ Sync a $REMOTE:$REMOTE_DIR completo"
