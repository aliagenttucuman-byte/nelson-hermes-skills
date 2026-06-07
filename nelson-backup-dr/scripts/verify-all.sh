#!/usr/bin/env bash
# Verifica que todos los backups se pueden restaurar correctamente.
# Corre desde cron (primer domingo del mes). Loguea resultado.
set -uo pipefail

BACKUP_ROOT="/home/server/backups"
VERIFY_DIR="$BACKUP_ROOT/verify/$(date +%Y-%m-%d)"
LOG="$BACKUP_ROOT/verify/verify-$(date +%Y-%m-%d).log"
LAST_GOOD="$BACKUP_ROOT/verify/last-good-verify.txt"

mkdir -p "$VERIFY_DIR"

log() {
  echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

FAIL=0

log "=== Verificación de backups $(date) ==="

# 1. task-memory: ¿se puede abrir el .db?
TASK_MEM_DB=$(ls -t "$BACKUP_ROOT/task-memory/daily/"*.db 2>/dev/null | head -1)
if [[ -n "$TASK_MEM_DB" ]]; then
  cp "$TASK_MEM_DB" "$VERIFY_DIR/tasks-verify.db"
  INTEGRITY=$(sqlite3 "$VERIFY_DIR/tasks-verify.db" "PRAGMA integrity_check;" 2>/dev/null | head -1)
  COUNT=$(sqlite3 "$VERIFY_DIR/tasks-verify.db" "SELECT COUNT(*) FROM tasks;" 2>/dev/null || echo "ERR")
  if [[ "$INTEGRITY" == "ok" ]] && [[ "$COUNT" != "ERR" ]]; then
    log "✓ task-memory: integridad OK, $COUNT tareas"
  else
    log "✗ task-memory: integrity=$INTEGRITY, count=$COUNT"
    FAIL=1
  fi
else
  log "✗ task-memory: no hay backup"
  FAIL=1
fi

# 2. forestai-postgis: ¿se puede abrir el dump?
FORESTAI_DUMP=$(ls -t "$BACKUP_ROOT/forestai-postgis/daily/"*.sql.gz 2>/dev/null | head -1)
if [[ -n "$FORESTAI_DUMP" ]]; then
  if gunzip -t "$FORESTAI_DUMP" 2>/dev/null; then
    log "✓ forestai-postgis: dump gzip válido"
  else
    log "✗ forestai-postgis: dump corrupto"
    FAIL=1
  fi
else
  log "⚠ forestai-postgis: no hay backup (puede ser normal si ForestAI no está corriendo)"
fi

# 3. code: ¿se puede listar el tar?
CODE_TAR=$(ls -t "$BACKUP_ROOT/code/"projects-*.tar.gz 2>/dev/null | head -1)
if [[ -n "$CODE_TAR" ]]; then
  if tar tzf "$CODE_TAR" > /dev/null 2>&1; then
    ENTRIES=$(tar tzf "$CODE_TAR" | wc -l)
    log "✓ code: tar legible, $ENTRIES entries"
  else
    log "✗ code: tar corrupto"
    FAIL=1
  fi
fi

# 4. Qdrant: ¿se puede extraer el volumen?
QDRANT_TAR=$(ls -t "$BACKUP_ROOT/qdrant/daily/"*.tar.gz 2>/dev/null | head -1)
if [[ -n "$QDRANT_TAR" ]]; then
  mkdir -p "$VERIFY_DIR/qdrant-test"
  if tar xzf "$QDRANT_TAR" -C "$VERIFY_DIR/qdrant-test" 2>/dev/null; then
    FILES=$(find "$VERIFY_DIR/qdrant-test" -type f | wc -l)
    log "✓ qdrant: extraído OK, $FILES archivos"
  else
    log "✗ qdrant: no se pudo extraer"
    FAIL=1
  fi
fi

# 5. ¿Hay backups recientes de los últimos 2 días? (alerta si la cadena se rompió)
TWO_DAYS_AGO=$(date -d '2 days ago' +%Y-%m-%d)
for svc in task-memory code; do
  RECENT=$(find "$BACKUP_ROOT/$svc" -maxdepth 2 -type f -newermt "$TWO_DAYS_AGO" 2>/dev/null | wc -l)
  if [[ "$RECENT" -gt 0 ]]; then
    log "✓ $svc: $RECENT archivos en últimos 2 días"
  else
    log "✗ $svc: sin backups en últimos 2 días"
    FAIL=1
  fi
done

# 6. ¿Hay espacio en disco?
DISK_USAGE=$(df -h /home | tail -1 | awk '{print $5}' | tr -d '%')
if [[ "$DISK_USAGE" -lt 80 ]]; then
  log "✓ Disco en ${DISK_USAGE}%"
else
  log "⚠ Disco en ${DISK_USAGE}% — considerar limpieza"
fi

if [[ $FAIL -eq 0 ]]; then
  log ""
  log "🟢 Verificación EXITOSA"
  date > "$LAST_GOOD"
  echo "Backups OK $(date)" >> /var/log/nelson-backup-verify.log
else
  log ""
  log "🔴 Verificación FALLÓ — revisar y arreglar"
  exit 1
fi
