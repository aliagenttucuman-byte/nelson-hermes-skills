#!/usr/bin/env bash
# Orquesta todos los backups según la política de nelson-backup-dr.
# Corre desde cron a las 01:00. Loguea a /var/log/nelson-backup.log.
set -uo pipefail

BACKUP_ROOT="/home/server/backups"
LOG="/var/log/nelson-backup.log"
DATE=$(date +%Y-%m-%d)
mkdir -p "$BACKUP_ROOT"

# Asegurar que los subdirs existen
for d in task-memory task-graph qdrant minio forestai-postgis code hermes; do
  mkdir -p "$BACKUP_ROOT/$d/daily"
done

log() {
  echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

log "=== Iniciando backup $DATE ==="

# 1. SQLite: task-memory
if [[ -f /home/server/nelson/task-memory/db/tasks.db ]]; then
  log "task-memory.db"
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-sqlite.sh \
    /home/server/nelson/task-memory/db/tasks.db \
    "$BACKUP_ROOT/task-memory/daily" \
    tasks
fi

# 2. SQLite: task-graph (meta-orchestrator)
if [[ -f /home/server/nelson/meta-orchestrator/task_graph.db ]]; then
  log "task_graph.db"
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-sqlite.sh \
    /home/server/nelson/meta-orchestrator/task_graph.db \
    "$BACKUP_ROOT/task-graph/daily" \
    task_graph
fi

# 3. Código fuente
for src_name in proyectos nelson brainstorming; do
  SRC_PATH="/home/server/$src_name"
  if [[ -d "$SRC_PATH" ]]; then
    log "$src_name/"
    bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-filesystem.sh \
      "$SRC_PATH" \
      "$BACKUP_ROOT/code" \
      "$src_name"
  fi
done

# 4. Skills + memoria
if [[ -d /home/server/.hermes/skills ]]; then
  log ".hermes skills"
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-filesystem.sh \
    /home/server/.hermes/skills \
    "$BACKUP_ROOT/hermes" \
    skills
fi
[[ -f /home/server/.hermes/MEMORY.md ]] && cp /home/server/.hermes/MEMORY.md "$BACKUP_ROOT/hermes/MEMORY-$DATE.md" || true
[[ -f /home/server/.hermes/USER.md ]] && cp /home/server/.hermes/USER.md "$BACKUP_ROOT/hermes/USER-$DATE.md" || true

# 5. Volúmenes Docker críticos
for vol in $(docker volume ls -q 2>/dev/null | grep -E "(qdrant|minio|n8n_data)" || true); do
  # Mapear volumen a categoría
  case "$vol" in
    *qdrant*) CATEGORY="qdrant" ;;
    *minio*)  CATEGORY="minio" ;;
    *n8n*)    CATEGORY="n8n" ;;
    *)        CATEGORY="other" ;;
  esac
  mkdir -p "$BACKUP_ROOT/$CATEGORY/daily"
  log "vol $vol"
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-docker-volume.sh \
    "$vol" \
    "$BACKUP_ROOT/$CATEGORY/daily" 2>&1 | tee -a "$LOG" || log "  (vol $vol falló, continuar)"
done

# 6. PostGIS si ForestAI está corriendo
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q forestai-poc-db-1; then
  log "ForestAI PostGIS"
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-postgres.sh \
    forestai-poc-db-1 \
    forestai \
    forestai \
    "$BACKUP_ROOT/forestai-postgis/daily" 2>&1 | tee -a "$LOG" || log "  (ForestAI dump falló, continuar)"
fi

# 7. Rotar
log "Rotación"
for d in task-memory task-graph qdrant minio n8n forestai-postgis; do
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/rotate-backups.sh \
    "$BACKUP_ROOT/$d/daily" 7 4 2>/dev/null || true
done
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/rotate-backups.sh \
  "$BACKUP_ROOT/code" 7 4 2>/dev/null || true
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/rotate-backups.sh \
  "$BACKUP_ROOT/hermes" 7 4 2>/dev/null || true

log "=== Backup $DATE completo ==="
