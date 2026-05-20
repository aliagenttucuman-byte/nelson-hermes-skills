#!/bin/bash
# run-react-doctor.sh — Script estándar del equipo Nelson para ejecutar React Doctor
# Uso: ./run-react-doctor.sh [directorio]

set -e

DIR="${1:-./src}"
REPORT_DIR=".reports"
REPORT_FILE="$REPORT_DIR/react-doctor.json"

echo "🤖⚕️ React Doctor v2 — Diagnóstico automático"
echo "============================================="
echo ""

# Crear directorio de reportes si no existe
mkdir -p "$REPORT_DIR"

# Ejecutar React Doctor
echo "📁 Escaneando: $DIR"
npx react-doctor@latest --dir "$DIR" --format json --output "$REPORT_FILE"

# Verificar si hay errores críticos
if [ -f "$REPORT_FILE" ]; then
  ERRORS=$(grep -c '"severity": "error"' "$REPORT_FILE" || true)
  WARNINGS=$(grep -c '"severity": "warning"' "$REPORT_FILE" || true)
  
  echo ""
  echo "📊 Resultados:"
  echo "  Errores:   $ERRORS"
  echo "  Warnings:  $WARNINGS"
  echo "  Reporte:   $REPORT_FILE"
  echo ""
  
  if [ "$ERRORS" -gt 0 ]; then
    echo "❌ Hay $ERRORS error(es) crítico(s). Corrige antes de continuar."
    exit 1
  else
    echo "✅ Sin errores críticos. Warnings: $WARNINGS"
  fi
else
  echo "⚠️ No se generó el reporte. Verifica que React Doctor esté instalado."
  exit 1
fi
