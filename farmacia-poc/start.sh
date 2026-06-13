#!/bin/bash
# Inicio del servidor Farmacia PoC
cd /home/server/proyectos/farmacia-poc

echo "🚀 Iniciando Farmacia Dashboard PoC..."
echo "📍 URL: http://100.110.8.13:8030"
echo "📍 URL local: http://localhost:8030"
echo ""

python3 -m uvicorn main:app --host 0.0.0.0 --port 8030 --reload
