#!/bin/bash
# ForestAI Detection Watchdog
# Monitorea si hay una deteccion activa y avisa si se cuelga > 5 min
# Señal de procesamiento: archivos /tmp/tmp*.tif dentro del container backend

STATE_FILE="/tmp/forestai_watchdog_state"
TIMEOUT_SECONDS=300  # 5 minutos

# Verificar si hay tiles temporales activos (señal de procesamiento)
TILES_ACTIVE=$(docker exec forestai-poc-backend-1 sh -c "ls /tmp/tmp*.tif 2>/dev/null | wc -l" 2>/dev/null | tr -d '[:space:]')
TILES_ACTIVE=${TILES_ACTIVE:-0}

NOW=$(date +%s)

if [ "$TILES_ACTIVE" -gt 0 ]; then
    # Procesando — registrar timestamp de inicio si no existe
    if [ ! -f "$STATE_FILE" ]; then
        echo "$NOW" > "$STATE_FILE"
        exit 0  # silencio — acaba de arrancar
    fi

    START=$(cat "$STATE_FILE")
    ELAPSED=$(( NOW - START ))

    if [ "$ELAPSED" -gt "$TIMEOUT_SECONDS" ]; then
        MINUTES=$(( ELAPSED / 60 ))
        echo "⚠️ ForestAI COLGADO — lleva ${MINUTES} minutos procesando sin responder. Tiles activos: ${TILES_ACTIVE}. Reiniciás los containers?"
    fi
    # Dentro del timeout → silencio
else
    # No hay procesamiento activo
    if [ -f "$STATE_FILE" ]; then
        START=$(cat "$STATE_FILE")
        ELAPSED=$(( NOW - START ))
        MINUTES=$(( ELAPSED / 60 ))
        if [ "$ELAPSED" -gt 60 ]; then
            echo "✅ ForestAI — detección completada en ~${MINUTES} minutos."
        fi
        rm -f "$STATE_FILE"
    fi
    # Sin estado previo → silencio total
fi
