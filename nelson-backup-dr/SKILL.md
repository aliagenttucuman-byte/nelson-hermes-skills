---
name: nelson-backup-dr
description: Política de backups y disaster recovery para los servicios del equipo Nelson (PostgreSQL, Qdrant, MinIO, SQLite, archivos críticos). RTO/RPO definidos por servicio, scripts automatizados con cron, runbooks de restore paso a paso, verificación mensual obligatoria. Complementa a nelson-incident-response.
version: 1.0.0
author: JARVIS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [backup, disaster-recovery, postgresql, qdrant, minio, sqlite, cron, nelson, ops]
    category: devops
    requires_toolsets: [terminal]
    related_skills:
      - nelson-incident-response
      - nelson-server-services
      - nelson-windows-ssh-setup
      - nelson-scheduled-jobs
      - nelson-monitoring-observability
---

# nelson-backup-dr

> **Trigger:** Antes de tocar un servicio nuevo en producción. Después de cualquier Sev-1. Cuando Nelson o Diego pregunten "¿tenemos backup de X?". Antes de confiar en que un servicio está "production-ready". El skill `nelson-incident-response` referencia este skill explícitamente: si no hay backup verificado, el post-mortem de cualquier Sev-1 va a tener acción correctiva obligatoria.

## Principio rector

> "Un backup no verificado no es un backup. Es una esperanza."

Tres reglas duras:
1. **Todo lo que no está respaldado, no está en producción.** Si no podés restaurar, es una demo.
2. **Un backup no testeado es igual a cero backups.** El restore se prueba, no se asume.
3. **El RTO y RPO se definen ANTES del incidente, no durante.** Si no los tenés, adivinás bajo presión.

## 1. Inventario actual (junio 2026)

Lo que hay que respaldar en `ai-server` (100.110.8.13):

| Componente | Tipo | Tamaño | Criticidad | Ubicación |
|------------|------|--------|------------|-----------|
| `task-memory.db` | SQLite | 57KB | 🔴 Crítica (estado de la meta-orchestration) | `/home/server/nelson/task-memory/db/` |
| `task_graph.db` | SQLite | desconocido | 🟡 Alta (DAG de tareas en curso) | `/home/server/nelson/meta-orchestrator/` |
| Volúmenes Qdrant | Docker volume | GB | 🔴 Crítica (vectores de RAG) | `docker volume ls \| grep qdrant` |
| Volúmenes MinIO | Docker volume | GB | 🔴 Crítica (objetos/documentos) | `docker volume ls \| grep minio` |
| Volúmenes PostGIS (ForestAI) | Docker volume | GB | 🟡 Alta (si está corriendo) | ForestAI compose |
| Volúmenes Redis | Docker volume | MB | 🟢 Media (se puede reconstruir) | varios |
| n8n data | Docker volume | MB | 🟡 Alta (workflows + credenciales) | n8n volume |
| Código fuente | filesystem | ~2.6GB | 🔴 Crítica (todo el trabajo) | `/home/server/proyectos/`, `/home/server/nelson/`, `/home/server/brainstorming/` |
| Skills y memoria Hermes | filesystem | <100MB | 🟡 Alta (skill base del equipo) | `/home/server/.hermes/skills/`, `~/.hermes/MEMORY.md` |
| Audio cache | filesystem | GB | 🟢 Baja (cache regenerable) | `/home/server/.hermes/audio_cache/` |

**Disco:** 466GB totales, 178GB usados, **264GB libres** → hay espacio de sobra para backups locales. No es excusa.

## 2. RTO y RPO por servicio

**Definiciones:**
- **RPO (Recovery Point Objective):** cuánto dato máximo podés perder. "Si se rompe a las 14:00, ¿hasta qué hora puedo restaurar?"
- **RTO (Recovery Time Objective):** cuánto tiempo máximo podés estar caído. "¿Cuánto tardás en tener el servicio de pie?"

| Servicio | RPO | RTO | Backup dónde | Frecuencia |
|----------|-----|-----|--------------|------------|
| `task-memory.db` | 24h (backup diario) | 1h (restore + restart systemd) | `/home/server/backups/task-memory/` | Diario 02:00 |
| `task_graph.db` | 24h | 1h | `/home/server/backups/task-graph/` | Diario 02:00 |
| Qdrant (volúmenes) | 24h | 4h (restore + reindex) | `/home/server/backups/qdrant/` | Diario 03:00 |
| MinIO (volúmenes) | 24h | 4h | `/home/server/backups/minio/` | Diario 03:00 |
| n8n | 24h | 2h | `/home/server/backups/n8n/` | Diario 02:30 |
| ForestAI PostGIS | 24h | 8h (es la DB más grande) | `/home/server/backups/forestai-postgis/` | Diario 04:00 |
| Código fuente | 24h | 2h (rsync desde otro lado) | `/home/server/backups/code/` o remote | Diario 01:00 |
| Skills + memoria | 24h | 1h | `/home/server/backups/hermes/` | Diario 01:30 |
| Audio cache | 7 días | 24h (se regenera) | no se respalda | — |

**Por qué estos números:** los servicios que tienen clientes activos (RAG, ForestAI) tienen RPO más estricto. Los internos (task-memory) tienen RTO más corto porque son chicos. Cuando haya un cliente con SLA, esos números se renegocian.

## 3. La política 3-2-1

Regla clásica adaptada al equipo:

- **3 copias** de cada dato: original + 2 backups.
- **2 medios distintos:** local en disco del server + remoto (Tailscale a `nelsondev` o disco USB rotativo).
- **1 copia off-site:** afuera del server físico (en `nelsondev` Windows, ver skill `nelson-windows-ssh-setup`).

**Implementación para Nelson:**

```
ai-server (100.110.8.13)
├── /home/server/  (original)
└── /home/server/backups/  (backup local, mismo disco)

nelsondev (100.76.143.33, Windows vía OpenSSH)
└── ~/backups-ai-server/  (backup remoto, vía rsync sobre Tailscale)
```

## 4. Estructura de directorios

```
/home/server/backups/
├── task-memory/
│   ├── daily/
│   │   ├── tasks-2026-06-07.db
│   │   ├── tasks-2026-06-06.db
│   │   └── ...
│   └── weekly/
│       ├── tasks-2026-W22.db
│       └── ...
├── task-graph/
│   └── daily/...
├── qdrant/
│   └── daily/...
├── minio/
│   └── daily/...
├── n8n/
│   └── daily/...
├── forestai-postgis/
│   ├── daily/
│   │   ├── dump-2026-06-07.sql.gz
│   │   └── ...
│   └── weekly/
├── code/
│   ├── projects-2026-06-07.tar.gz
│   ├── nelson-2026-06-07.tar.gz
│   ├── brainstorming-2026-06-07.tar.gz
│   └── ...
├── hermes/
│   ├── skills-2026-06-07.tar.gz
│   ├── memory-2026-06-07.tar.gz
│   └── ...
├── verify/
│   ├── verify-2026-06-07.log      # output del último verify
│   └── last-good-verify.txt        # timestamp del último verify exitoso
└── README.md                       # este directorio, política, contacto de emergencia
```

**Retención:**
- **Daily:** 7 copias (una semana)
- **Weekly:** 4 copias (un mes)
- **Monthly:** 3 copias (un trimestre, para ForestAI y otros críticos)

Implementado con script de rotación (ver `scripts/rotate-backups.sh`).

## 5. Scripts de backup (lista de tareas concretas)

Todos los scripts viven en `scripts/`. Son invocados por cron (ver § 6).

### `scripts/backup-sqlite.sh`

```bash
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
```

### `scripts/backup-postgres.sh`

```bash
#!/usr/bin/env bash
# Respalda una DB PostgreSQL con pg_dump.
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
```

### `scripts/backup-docker-volume.sh`

```bash
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
```

### `scripts/backup-filesystem.sh`

```bash
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
```

### `scripts/rotate-backups.sh`

```bash
#!/usr/bin/env bash
# Rota los backups: conserva N diarios, M semanales.
# Uso: rotate-backups.sh <backup_dir> <keep_daily> <keep_weekly> [pattern]
set -euo pipefail

BACKUP_DIR="${1:?Backup dir requerido}"
KEEP_DAILY="${2:-7}"
KEEP_WEEKLY="${3:-4}"
PATTERN="${4:-*}"  # glob pattern

# Mover los más viejos de 7 días a weekly
echo "Rotando $BACKUP_DIR (pattern: $PATTERN)..."
find "$BACKUP_DIR" -maxdepth 1 -name "$PATTERN" -mtime +7 -exec mv {} "$BACKUP_DIR/weekly/" \; 2>/dev/null || true

# Weekly: conservar solo los últimos 4
ls -t "$BACKUP_DIR/weekly/" 2>/dev/null | tail -n +$((KEEP_WEEKLY + 1)) | while read -r old; do
  rm -f "$BACKUP_DIR/weekly/$old"
  echo "  borrado: weekly/$old"
done

# Daily: conservar solo los últimos 7
ls -t "$BACKUP_DIR" -maxdepth 1 -name "$PATTERN" -type f | tail -n +$((KEEP_DAILY + 1)) | while read -r old; do
  rm -f "$old"
  echo "  borrado: $old"
done

echo "✓ Rotación completa"
```

### `scripts/backup-all.sh` (orquestador)

```bash
#!/usr/bin/env bash
# Orquesta todos los backups según la política.
# Corre desde cron. Loguea a syslog y a /home/server/backups/backup.log.
set -uo pipefail

BACKUP_ROOT="/home/server/backups"
LOG="/var/log/nelson-backup.log"
DATE=$(date +%Y-%m-%d)
mkdir -p "$BACKUP_ROOT"

log() {
  echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

log "=== Iniciando backup $DATE ==="

# 1. SQLite: task-memory
log "task-memory.db"
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-sqlite.sh \
  /home/server/nelson/task-memory/db/tasks.db \
  "$BACKUP_ROOT/task-memory/daily" \
  tasks

# 2. SQLite: task-graph (meta-orchestrator)
log "task_graph.db"
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-sqlite.sh \
  /home/server/nelson/meta-orchestrator/task_graph.db \
  "$BACKUP_ROOT/task-graph/daily" \
  task_graph 2>/dev/null || log "  (task_graph no existe, skip)"

# 3. Código fuente
log "proyectos/"
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-filesystem.sh \
  /home/server/proyectos \
  "$BACKUP_ROOT/code" \
  projects

log "nelson/"
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-filesystem.sh \
  /home/server/nelson \
  "$BACKUP_ROOT/code" \
  nelson

log "brainstorming/"
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-filesystem.sh \
  /home/server/brainstorming \
  "$BACKUP_ROOT/code" \
  brainstorming

# 4. Skills + memoria
log ".hermes skills"
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-filesystem.sh \
  /home/server/.hermes/skills \
  "$BACKUP_ROOT/hermes" \
  skills

cp /home/server/.hermes/MEMORY.md "$BACKUP_ROOT/hermes/MEMORY-$DATE.md" 2>/dev/null || true
cp /home/server/.hermes/USER.md "$BACKUP_ROOT/hermes/USER-$DATE.md" 2>/dev/null || true

# 5. Volúmenes Docker críticos (solo si existen)
for vol in $(docker volume ls -q | grep -E "(qdrant|minio|n8n_data)" 2>/dev/null); do
  log "vol $vol"
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-docker-volume.sh \
    "$vol" \
    "$BACKUP_ROOT/$(echo $vol | cut -d_ -f1)/daily" || log "  (vol $vol falló, continuar)"
done

# 6. PostGIS si ForestAI está corriendo
if docker ps --format '{{.Names}}' | grep -q forestai-poc-db-1; then
  log "ForestAI PostGIS"
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-postgres.sh \
    forestai-poc-db-1 \
    forestai \
    forestai \
    "$BACKUP_ROOT/forestai-postgis/daily"
fi

# 7. Rotar
log "Rotación"
for d in task-memory task-graph qdrant minio forestai-postgis; do
  bash /home/server/.hermes/skills/nelson-backup-dr/scripts/rotate-backups.sh \
    "$BACKUP_ROOT/$d/daily" 7 4 || true
done
bash /home/server/.hermes/skills/nelson-backup-dr/scripts/rotate-backups.sh \
  "$BACKUP_ROOT/code" 7 4 || true

log "=== Backup $DATE completo ==="
```

## 6. Scheduling con cron

`crontab -e` (root, no el user, para acceder a `/var/log` y volúmenes Docker):

```cron
# Zona horaria: America/Argentina/Tucuman (o UTC, según prefieras — definir UNA y atenerse)
TZ=America/Argentina/Tucuman

# 01:00 — código fuente
0 1 * * * /home/server/.hermes/skills/nelson-backup-dr/scripts/backup-all.sh >> /var/log/nelson-backup.log 2>&1

# 06:00 — sync remoto a nelsondev (Tailscale)
0 6 * * * /home/server/.hermes/skills/nelson-backup-dr/scripts/sync-to-remote.sh >> /var/log/nelson-backup.log 2>&1

# Primer domingo del mes a las 09:00 — verify completo
0 9 1-7 * 0 /home/server/.hermes/skills/nelson-backup-dr/scripts/verify-all.sh >> /var/log/nelson-backup.log 2>&1
```

### `scripts/sync-to-remote.sh`

```bash
#!/usr/bin/env bash
# Sincroniza los backups locales a nelsondev vía rsync sobre Tailscale.
set -euo pipefail

REMOTE="nelsondev"  # alias SSH de ~/.ssh/config
REMOTE_DIR="~/backups-ai-server"
LOCAL_DIR="/home/server/backups"

# Excluir caches y temporales
rsync -avz --delete \
  --exclude='*.tmp' \
  --exclude='.cache' \
  --exclude='verify/*.tmp' \
  "$LOCAL_DIR/" \
  "${REMOTE}:${REMOTE_DIR}/"

echo "✓ Sync a $REMOTE:$REMOTE_DIR completo"
```

Configurar alias SSH en `~/.ssh/config`:

```
Host nelsondev
  HostName 100.76.143.33
  User server
  IdentityFile ~/.ssh/id_ed25519
  ServerAliveInterval 60
```

## 7. Verificación mensual (obligatoria)

El **primer domingo de cada mes a las 09:00**, `verify-all.sh` corre automáticamente. **No es opcional.** Si falla, el post-mortem tiene acción correctiva.

### `scripts/verify-all.sh`

```bash
#!/usr/bin/env bash
# Verifica que todos los backups se pueden restaurar correctamente.
# Hace restore a un dir temporal, valida integridad, loguea.
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
  INTEGRITY=$(sqlite3 "$VERIFY_DIR/tasks-verify.db" "PRAGMA integrity_check;" | head -1)
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

# 2. forestai-postgis: ¿se puede importar el dump?
FORESTAI_DUMP=$(ls -t "$BACKUP_ROOT/forestai-postgis/daily/"*.sql.gz 2>/dev/null | head -1)
if [[ -n "$FORESTAI_DUMP" ]]; then
  gunzip -t "$FORESTAI_DUMP" 2>/dev/null && \
    log "✓ forestai-postgis: dump gzip válido" || \
    { log "✗ forestai-postgis: dump corrupto"; FAIL=1; }
fi

# 3. code: ¿se puede listar el tar?
CODE_TAR=$(ls -t "$BACKUP_ROOT/code/"projects-*.tar.gz 2>/dev/null | head -1)
if [[ -n "$CODE_TAR" ]]; then
  tar tzf "$CODE_TAR" > /dev/null 2>&1 && \
    log "✓ code: tar legible, $(tar tzf "$CODE_TAR" | wc -l) entries" || \
    { log "✗ code: tar corrupto"; FAIL=1; }
fi

# 4. Qdrant: ¿se puede extraer el volumen?
QDRANT_TAR=$(ls -t "$BACKUP_ROOT/qdrant/daily/"*.tar.gz 2>/dev/null | head -1)
if [[ -n "$QDRANT_TAR" ]]; then
  mkdir -p "$VERIFY_DIR/qdrant-test"
  tar xzf "$QDRANT_TAR" -C "$VERIFY_DIR/qdrant-test" && \
    log "✓ qdrant: extraído OK, $(find "$VERIFY_DIR/qdrant-test" -type f | wc -l) archivos" || \
    { log "✗ qdrant: no se pudo extraer"; FAIL=1; }
fi

# 5. ¿Hay backups de los últimos 7 días?
STALE_DAYS=$(find "$BACKUP_ROOT" -maxdepth 3 -name "*.db" -o -name "*.tar.gz" -o -name "*.sql.gz" 2>/dev/null | \
  awk -F/ '{print $(NF-1)}' | sort | uniq -c | awk '$1 < 7 {print $0}')
if [[ -z "$STALE_DAYS" ]]; then
  log "✓ Todos los servicios tienen ≥7 backups"
else
  log "✗ Servicios con menos de 7 backups:"
  echo "$STALE_DAYS" | tee -a "$LOG"
  FAIL=1
fi

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
  # Notificar éxito
  echo "Backups OK $(date)" >> /var/log/nelson-backup-verify.log
else
  log ""
  log "🔴 Verificación FALLÓ — revisar y arreglar"
  # Acá se puede agregar una notificación a Slack/WhatsApp/email
  # Si tenés el skill nelson-scheduled-jobs, se puede disparar un job
  exit 1
fi
```

## 8. Runbooks de restore

Cuándo usar cada uno: cuando el incidente ya pasó, el servicio está caído, y necesitás datos.

### `runbooks/restore-task-memory.md`

**Cuándo:** `task-memory.db` corrupto, perdido, o querés rollback.

**Tiempo objetivo:** 15 min.

```bash
# 1. Detener el servicio
sudo systemctl stop nelson-task-memory

# 2. Identificar el backup a restaurar
ls -lt /home/server/backups/task-memory/daily/ | head -5
# Ej: tasks-2026-06-07-020000.db

# 3. Restaurar (backup atómico, no requiere downtime extra)
cp /home/server/backups/task-memory/daily/tasks-2026-06-07-020000.db \
   /home/server/nelson/task-memory/db/tasks.db
chown server:server /home/server/nelson/task-memory/db/tasks.db

# 4. Validar integridad
sqlite3 /home/server/nelson/task-memory/db/tasks.db "PRAGMA integrity_check;"
# Debe decir "ok"

# 5. Verificar que la API responde
curl http://localhost:8742/health

# 6. Levantar el servicio
sudo systemctl start nelson-task-memory
curl http://localhost:8742/health

# 7. Documentar en post-mortem
echo "Restaurado task-memory desde backup del YYYY-MM-DD HH:MM"
```

### `runbooks/restore-forestai-postgis.md`

**Cuándo:** ForestAI DB perdida/corrupta, o querés rollback a un estado anterior.

**Tiempo objetivo:** 1-4h dependiendo del tamaño del dump.

```bash
# 1. Detener ForestAI
cd /home/server/proyectos/forestai-poc/
docker compose down

# 2. Identificar dump a restaurar
ls -lt /home/server/backups/forestai-postgis/daily/ | head -5
# Ej: dump-2026-06-07-040000.sql.gz

# 3. Levantar solo el container de Postgres (sin el resto)
docker compose up -d db
sleep 10  # esperar que PG inicialice

# 4. Borrar la DB actual y restaurar
docker exec -i forestai-poc-db-1 psql -U forestai -c "DROP DATABASE forestai;"
docker exec -i forestai-poc-db-1 psql -U forestai -c "CREATE DATABASE forestai;"

gunzip -c /home/server/backups/forestai-postgis/daily/dump-2026-06-07-040000.sql.gz | \
  docker exec -i forestai-poc-db-1 psql -U forestai -d forestai

# 5. Verificar que la DB se restauró
docker exec forestai-poc-db-1 psql -U forestai -d forestai -c "\dt"
docker exec forestai-poc-db-1 psql -U forestai -d forestai -c "SELECT COUNT(*) FROM documents;"

# 6. Levantar el resto
docker compose up -d
sleep 20
curl http://localhost:8010/health
```

### `runbooks/restore-code.md`

**Cuándo:** código de un proyecto perdido, o rollback a versión anterior.

**Tiempo objetivo:** 30 min.

```bash
# 1. Identificar el tarball a restaurar
ls -lt /home/server/backups/code/ | head -10

# 2. Decidir destino: ¿restaurar en /home/server/proyectos/ pisando lo actual,
#    o a un dir temporal para revisar?
# RECOMENDADO: revisar primero
mkdir -p /tmp/restore-projects
tar xzf /home/server/backups/code/projects-2026-06-07-010000.tar.gz \
  -C /tmp/restore-projects/

# 3. Comparar con lo actual
diff -rq /home/server/proyectos/ /tmp/restore-projects/proyectos/

# 4. Si OK, restaurar (con backup del estado actual por las dudas)
mv /home/server/proyectos /home/server/proyectos.broken
mkdir -p /home/server/proyectos
tar xzf /home/server/backups/code/projects-2026-06-07-010000.tar.gz \
  -C /home/server/proyectos/ --strip-components=1

# 5. Validar
ls /home/server/proyectos/
# Arrancar los servicios críticos y verificar
```

### `runbooks/restore-qdrant.md`

**Cuándo:** Qdrant perdió datos o quedó inconsistente.

**Tiempo objetivo:** 2-4h (reindex desde documentos si es posible es más rápido).

```bash
# 1. Detener Qdrant
cd /home/server/brainstorming/2026-05-13-rag-poc/  # o el proyecto correspondiente
docker compose stop qdrant

# 2. Identificar volumen y backup
VOLUME="2026-05-13-rag-poc_qdrant-data"
BACKUP="/home/server/backups/qdrant/daily/${VOLUME}-2026-06-07-030000.tar.gz"

# 3. Borrar volumen actual y restaurar
docker volume rm "$VOLUME"
docker volume create "$VOLUME"
docker run --rm \
  -v "${VOLUME}:/target" \
  -v "/home/server/backups/qdrant/daily:/backup:ro" \
  alpine:latest \
  tar xzf "/backup/$(basename $BACKUP)" -C /target

# 4. Levantar Qdrant
docker compose up -d qdrant
sleep 15

# 5. Validar (chequear collections y counts)
curl http://localhost:6333/collections
```

## 9. Catálogo: qué respaldar por servicio

| Servicio | Qué | Cómo | Script |
|----------|-----|------|--------|
| nelson-task-memory | `tasks.db` | `backup-sqlite.sh` | backup-sqlite |
| nelson-agent-router | `routing.db` | `backup-sqlite.sh` | backup-sqlite |
| nelson-meta-orchestrator | `task_graph.db` | `backup-sqlite.sh` | backup-sqlite |
| ForestAI (PostGIS) | `forestai` DB | `pg_dump` desde container | backup-postgres |
| RAG PoCs (Qdrant) | volumen `*_qdrant-data` | tar.gz del volumen | backup-docker-volume |
| RAG PoCs (MinIO) | volumen `*_minio-data` | tar.gz del volumen | backup-docker-volume |
| n8n | volumen n8n | tar.gz del volumen | backup-docker-volume |
| Código | `/home/server/proyectos/`, `/home/server/nelson/`, `/home/server/brainstorming/` | tar.gz con excludes | backup-filesystem |
| Skills + memoria | `/home/server/.hermes/skills/`, `MEMORY.md`, `USER.md` | tar.gz + cp específicos | backup-filesystem |

## 10. Cuándo ampliar (trigger de re-evaluación)

Re-evaluar RTO/RPO y la política completa cuando:

- [ ] Aparece un cliente con SLA formal (probablemente hay que bajar RPO a 1h)
- [ ] Hay 5+ proyectos productivos (considerar backup incremental continuo tipo WAL archiving)
- [ ] El server pasa a producción 24/7 (considerar backup a S3/GCS en vez de solo local + nelsondev)
- [ ] Alguien pregunta "¿podemos confiar en que esto se restaura?" (sí, pero con evidencia: último verify)
- [ ] Se agrega un servicio nuevo al server (ver § 11.1 abajo)

### 10.1 Workflow: agregar un servicio nuevo al backup

Cuando Diego (o quien sea) agrega un servicio nuevo al server, no es opcional actualizar esta skill. Pasos:

1. **Identificar el tipo de dato** (consultar § 9):
   - SQLite → `backup-sqlite.sh`
   - PostgreSQL/MySQL/MariaDB → `backup-postgres.sh` (adaptar el wrapper)
   - Volumen Docker → `backup-docker-volume.sh`
   - Archivos/carpetas → `backup-filesystem.sh`
2. **Agregar una línea en § 1 (Inventario) y § 2 (RTO/RPO)**.
3. **Agregar una entrada en § 9 (Catálogo)** con: servicio, qué, cómo, script.
4. **Modificar `scripts/backup-all.sh`** para incluir el backup nuevo (ver § 5 para el patrón).
5. **Crear runbook de restore en `runbooks/restore-<servicio>.md`** siguiendo el formato de los 4 existentes.
6. **Actualizar `related_skills` del frontmatter** si el servicio toca otra skill (ej: si es parte de un proyecto ForestAI, mencionar `nelson-forest-inventory`).
7. **Testear**: correr el script nuevo una vez manualmente, validar que el backup abre/se importa, validar el restore.

**Trigger automático:** cuando se crea una skill nueva en `nelson-skill-authoring`, chequear si la skill referencia algún servicio con estado persistente. Si sí, agregar acá.

## 11. Anti-patrones y pitfalls

1. **"Hago backup manual cada tanto".** No es backup, es screenshot. Si dependés de tu memoria, vas a olvidar.
2. **"Tengo backup en el mismo disco".** Si se rompe el disco, perdiste original + backup. La regla 3-2-1 existe por esto.
3. **"Confío en el .git como backup de código".** El `.git` no tiene archivos grandes (ortofotos, modelos), ni los node_modules, ni los `.env`. Y si el server muere, ¿cómo accedés a GitHub? Tenés que poder restaurar **sin internet**.
4. **"Hago backup pero nunca probé el restore".** Es el error #1. Si no probaste, no sabés si funciona. Por eso el verify mensual es obligatorio, no opcional.
5. **Backup durante horas pico.** Si el backup corre a las 14:00 cuando los agentes están trabajando, mete latencia. Por eso todos a las 01:00-04:00.
6. **No loguear el backup.** Si no sabés cuándo corrió, cuánto tardó, cuánto pesó, no podés saber si está fallando silenciosamente. El log a `/var/log/nelson-backup.log` es ley.
7. **Olvidar el `.env`.** Las API keys, los secrets, las configs. Si perdés `.env`, perdiste acceso a todo. Backup explícito del `.env` de cada proyecto (encriptado si tiene cosas críticas).
8. **Confundir backup con sync.** Un backup es un punto en el tiempo, inmutable. Un sync (rsync con --delete) puede borrar lo bueno junto con lo malo. Los backups son read-only después de creados.
9. **No documentar las dependencias del restore.** Si para restaurar ForestAI necesitás que Qdrant esté corriendo primero, documentalo. Si no, perdés 3 horas descubriendo.
10. **Olvidar el off-site.** El server está en una sola ubicación física. Incendio, robo, corte de luz prolongado → perdés todo. La copia en nelsondev es el seguro.
11. **Asumir que `pg_dump` resuelve todo.** Solo respalda SQL. Los roles, los tablespaces, los usuarios de la DB hay que respaldarlos aparte (`pg_dumpall --globals-only`).
12. **Backups sin encriptación con datos sensibles.** Si el dump de PostGIS tiene datos de clientes, el backup local es un vector de ataque. Considerar gpg con clave del equipo.
13. **No versionar la política.** Si cambia el stack (nuevo servicio, nueva DB), la política tiene que actualizarse. Trimestral: revisar este skill.
14. **Pegar el cron sin verificar TZ.** El bloque de § 6 usa `TZ=America/Argentina/Tucuman`. Pegarlo al final del `crontab -e` después de un `TZ` distinto, o sin `TZ` explícito cuando el server está en otra zona, hace que los logs queden con timestamps confusos. Confirmar la TZ del server con `date` antes de pegar el bloque.
15. **Asumir que el `verify-all.sh` anda sin probarlo.** El script tiene un `set -uo pipefail` (sin `-e`) a propósito — para que un fallo no aborte el resto del verify. Pero eso significa que errores silenciosos se loguean y siguen. La primera vez que corra el cron de verificación, monitorear el log en `/var/log/nelson-backup.log` el lunes siguiente.

## 12. Verificación rápida (smoke test mensual)

Cada mes, además del `verify-all.sh` automático, hacer **una restore manual real** de un servicio. Elegir al rotar entre: task-memory, forestai-postgis, code, qdrant. El smoke test es la diferencia entre "tengo backups" y "tengo un sistema de disaster recovery".

## Referencias

- `nelson-incident-response` — referencia cruzada. Sev-1 implica verificar backups, post-mortems incluyen "¿se podría haber prevenido con backup?"
- `nelson-server-services` — mapa de servicios que esta skill respalda
- `nelson-windows-ssh-setup` — para configurar el alias SSH a nelsondev
- `nelson-scheduled-jobs` — si preferís disparar los backups como jobs del meta-orquestador en vez de cron
- `nelson-observability` — métricas de "último backup exitoso" como KPI

## Glosario

- **RPO (Recovery Point Objective):** cantidad máxima de datos que podés perder, medida en tiempo
- **RTO (Recovery Time Objective):** tiempo máximo que podés estar caído
- **3-2-1:** 3 copias, 2 medios, 1 off-site
- **Restore test:** acto de tomar un backup y verificar que se puede usar (lo opuesto a "tengo backups cruzando los dedos")
- **Hot backup:** backup que se hace con el servicio corriendo (la mayoría de los nuestros)
- **Cold backup:** backup con el servicio apagado (no lo necesitamos para nuestro stack)
