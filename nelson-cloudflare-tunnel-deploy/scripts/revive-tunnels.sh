#!/usr/bin/env bash
# revive-tunnels.sh — Revivir túneles Cloudflare caídos para servicios Nelson
# Uso: ./revive-tunnels.sh <puerto> [nombre_proyecto]
# Ejemplo: ./revive-tunnels.sh 3010 forestai

set -euo pipefail

PORT="${1:-}"
PROJECT="${2:-proyecto}"
LOGFILE="/tmp/cf_${PROJECT}.log"

if [[ -z "$PORT" ]]; then
    echo "Uso: $0 <puerto> [nombre_proyecto]"
    echo "Ejemplo: $0 3010 forestai"
    exit 1
fi

# 1. Matar túneles viejos para este puerto
echo "[⚙️] Matando túneles viejos para puerto $PORT..."
pkill -f "cloudflared.*${PORT}" 2>/dev/null || true
sleep 2

# 2. Verificar que el servicio local está vivo
echo "[🔍] Verificando servicio local en :$PORT..."
if ! curl -sf "http://127.0.0.1:${PORT}/" > /dev/null 2>&1; then
    # Intentar health endpoint si el root no responde
    if ! curl -sf "http://127.0.0.1:${PORT}/health" > /dev/null 2>&1; then
        echo "[❌] ERROR: Nada responde en localhost:$PORT"
        echo "    Levantá el servicio primero, después corré este script."
        exit 1
    fi
fi
echo "[✅] Servicio local OK"

# 3. Lanzar nuevo túnel en background
echo "[🚀] Lanzando nuevo túnel Cloudflare..."
nohup cloudflared tunnel --url "http://127.0.0.1:${PORT}" > "$LOGFILE" 2>&1 &
PID=$!

# 4. Esperar a que emita la URL
echo "[⏳] Esperando URL..."
URL=""
for i in {1..15}; do
    sleep 1
    URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$LOGFILE" | tail -1 || true)
    if [[ -n "$URL" ]]; then
        break
    fi
done

if [[ -z "$URL" ]]; then
    echo "[❌] ERROR: No se pudo obtener URL del túnel"
    echo "    Logs: $LOGFILE"
    exit 1
fi

# 5. Verificar que el túnel responde
echo "[🔍] Verificando túnel desde internet..."
if curl -sf --max-time 10 "$URL" > /dev/null 2>&1; then
    echo "[✅] Tunnel activo y verificado"
    echo ""
    echo "🌐 URL pública: $URL"
    echo "📁 Logs:       $LOGFILE"
    echo "🔧 PID:        $PID"
else
    echo "[⚠️] Tunnel creado pero no responde aún (puede tardar 30s en propagar DNS)"
    echo "    URL:  $URL"
    echo "    Logs: $LOGFILE"
fi

# 6. Guardar URL en archivo para referencia rápida
URLFILE="/tmp/cf_${PROJECT}.url"
echo "$URL" > "$URLFILE"
echo "📄 URL guardada en: $URLFILE"
