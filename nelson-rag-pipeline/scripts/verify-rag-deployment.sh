#!/usr/bin/env bash
# Script: verify-rag-deployment.sh
# Verifica que un stack RAG expuesto por Cloudflare esté correctamente configurado.
# Problemas que detecta:
#   1. Frontend apunta a localhost en vez de URL publica del backend
#   2. Backend no responde en la URL publica
#   3. CORS mal configurado (frontend no puede hablar con backend)
#   4. Documentos no visibles desde el backend
#
# Uso:
#   FRONTEND_URL=https://XXXX.trycloudflare.com \
#   BACKEND_URL=https://YYYY.trycloudflare.com \
#   ./scripts/verify-rag-deployment.sh

set -euo pipefail

FRONTEND_URL="${FRONTEND_URL:-}"
BACKEND_URL="${BACKEND_URL:-}"

if [[ -z "$FRONTEND_URL" || -z "$BACKEND_URL" ]]; then
    echo "Usage: FRONTEND_URL=<url> BACKEND_URL=<url> $0"
    echo "Ejemplo:"
    echo "  FRONTEND_URL=https://abc.trycloudflare.com BACKEND_URL=https://xyz.trycloudflare.com $0"
    exit 1
fi

echo "=== Verificacion de deployment RAG ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""

# 1. Backend health
echo "[1/4] Backend health..."
if curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "  OK - Backend responde /health"
else
    echo "  FAIL - Backend NO responde en $BACKEND_URL/health"
fi

# 2. Backend tiene documentos
echo "[2/4] Documentos en backend..."
DOCS=$(curl -sf "$BACKEND_URL/documents" 2>/dev/null || echo '{}')
COUNT=$(echo "$DOCS" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('documents',[])))" 2>/dev/null || echo "0")
if [[ "$COUNT" -gt 0 ]]; then
    echo "  OK - $COUNT documentos encontrados"
else
    echo "  WARN - 0 documentos (puede ser normal si aun no se subio nada)"
fi

# 3. CORS (frontend puede hablar con backend)
echo "[3/4] CORS backend..."
CORS=$(curl -sf -X OPTIONS \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: GET" \
    "$BACKEND_URL/documents" 2>/dev/null | grep -i "access-control-allow-origin" || true)
if [[ -n "$CORS" ]]; then
    echo "  OK - CORS configurado"
else
    echo "  FAIL - CORS no responde o no permitido"
fi

# 4. Frontend sirve HTML y no referencia localhost en el bundle inicial
# (Nota: esto es una verificacion heuristica; la verdadera prueba es abrir el navegador)
echo "[4/4] Frontend HTML..."
HTML=$(curl -sf "$FRONTEND_URL" 2>/dev/null || echo "")
if [[ -n "$HTML" ]]; then
    echo "  OK - Frontend sirve HTML"
    if echo "$HTML" | grep -q "localhost"; then
        echo "  WARN - El HTML contiene 'localhost' — verificar que VITE_API_URL este bien"
    fi
else
    echo "  FAIL - Frontend no responde"
fi

echo ""
echo "=== Resumen ==="
echo "Si hay FAILs, revisar:"
echo "  - Que los túneles de cloudflared esten corriendo"
echo "  - Que VITE_API_URL en docker-compose apunte a BACKEND_URL (no localhost)"
echo "  - Que el backend tenga CORS configurado con el origin del frontend"
