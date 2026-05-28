#!/bin/bash
# rag-health-monitor.sh — Monitorea salud de los 3 RAGs y auto-recupera si estan caidos
# Cada 5 minutos via cronjob

set -euo pipefail

# Config
BACKENDS=(
  "8000|FLoCI-AWS|2026-05-13-rag-poc"
  "8001|MinIO|2026-05-13-rag-poc-minio"
  "8002|FLoCI-Azure|2026-05-14-rag-floci-azure"
)

LOGFILE="/tmp/rag-health-monitor.log"
ALERT_FILE="/tmp/rag-health-alert.sent"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando check de salud..." >> "$LOGFILE"

for backend in "${BACKENDS[@]}"; do
  IFS='|' read -r PORT NAME PROJECT <<< "$backend"

  if curl -sf "http://localhost:${PORT}/health" > /dev/null 2>&1; then
    echo "[OK] ${NAME} (puerto ${PORT}) responde /health" >> "$LOGFILE"
    # Si habia una alerta previa, limpiarla
    rm -f "${ALERT_FILE}.${NAME}"
  else
    echo "[FAIL] ${NAME} (puerto ${PORT}) NO responde. Intentando reinicio..." >> "$LOGFILE"

    # Intentar reiniciar el backend del proyecto
    if [ -d "${HOME}/brainstorming/${PROJECT}" ]; then
      cd "${HOME}/brainstorming/${PROJECT}"
      # Encontrar el docker-compose file
      if [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
      elif [ -f "docker-compose.minio.yml" ]; then
        COMPOSE_FILE="docker-compose.minio.yml"
      else
        echo "[ERROR] No se encontro docker-compose en ${PROJECT}" >> "$LOGFILE"
        continue
      fi

      docker compose -f "$COMPOSE_FILE" restart backend 2>> "$LOGFILE" || true
      sleep 5

      # Verificar si volvio
      if curl -sf "http://localhost:${PORT}/health" > /dev/null 2>&1; then
        echo "[RECOVERY] ${NAME} recuperado despues de reinicio" >> "$LOGFILE"
        rm -f "${ALERT_FILE}.${NAME}"
      else
        echo "[CRITICAL] ${NAME} sigue caido despues de reinicio" >> "$LOGFILE"
        # Marcar alerta enviada para no spammear
        if [ ! -f "${ALERT_FILE}.${NAME}" ]; then
          echo "ALERT: RAG ${NAME} caido en $(date)" > "${ALERT_FILE}.${NAME}"
          # El cronjob con no_agent=true enviara stdout como mensaje
          echo "[ALERTA] ${NAME} esta caido. Puerto ${PORT} no responde ni despues de reinicio. Revisar manualmente."
        fi
      fi
    else
      echo "[ERROR] Directorio ${PROJECT} no existe" >> "$LOGFILE"
    fi
  fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Check completado" >> "$LOGFILE"
