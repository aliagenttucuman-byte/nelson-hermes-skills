#!/bin/bash
# Verificar que n8n esta corriendo y responde
set -e

echo "=== Verificando n8n ==="
echo "1. Container status:"
sudo docker ps | grep n8n || { echo "ERROR: n8n no esta corriendo"; exit 1; }

echo ""
echo "2. Health check HTTP:"
curl -s http://localhost:5678/healthz | grep -q "ok" && echo "OK - healthz responde" || echo "FAIL - healthz no responde"

echo ""
echo "3. Home page HTTP:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "OK - HTTP 200"
else
    echo "FAIL - HTTP $HTTP_CODE"
fi

echo ""
echo "=== Listo ==="
