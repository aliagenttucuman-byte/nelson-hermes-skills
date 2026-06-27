#!/bin/bash
# Análisis económico del stack de compresión Nelson (Headroom + lean-ctx + Honcho).
# Uso: bash cost_analysis.sh [server_cost_monthly_usd]
# Default: $50/mes electricidad+amortización ai-server (32GB RAM total)

SERVER_COST=${1:-50}
SERVER_RAM_GB=32

echo "=== Stack de compresión — análisis económico ==="
echo

# 1) Headroom: fuente canónica de métricas
STATS=$(curl -s http://localhost:8787/stats)
if [ -z "$STATS" ]; then
    echo "ERROR: Headroom proxy no responde en :8787"
    exit 1
fi

REQS=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['persistent_savings']['lifetime']['requests'])")
TOKENS_SAVED=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['persistent_savings']['lifetime']['tokens_saved'])")
TOKENS_IN=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['persistent_savings']['lifetime']['total_input_tokens'])")
COST_PAID=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['persistent_savings']['lifetime']['total_input_cost_usd'])")
SAVINGS=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['persistent_savings']['lifetime']['compression_savings_usd'])")

# 2) RAM real del stack
HEADROOM_RAM=$(ps -o rss= -p $(pgrep -f 'headroom proxy' | head -1) 2>/dev/null | awk '{print int($1/1024)}')
LEANCTX_RAM=$(ps -o rss= -p $(pgrep -f 'lean-ctx' | head -1) 2>/dev/null | awk '{print int($1/1024)}')
HONCHO_RAM=$(docker stats honcho-api-1 honcho-database-1 honcho-redis-1 --no-stream --format "{{.MemUsage}}" 2>/dev/null | awk -F'/' '{gsub(/MiB|GiB/,"",$1); sum+=$1} END {print int(sum)}')

TOTAL_RAM=$((HEADROOM_RAM + LEANCTX_RAM + HONCHO_RAM))
INFRA_COST=$(python3 -c "print(round($SERVER_COST * $TOTAL_RAM / 1024 / $SERVER_RAM_GB, 2))")

# 3) Honcho check: workspace creado?
HONCHO_WS=$(curl -s http://localhost:8008/v1/workspaces -H "Authorization: Bearer default" 2>&1 | head -c 100)

echo "RAM del stack: ${TOTAL_RAM} MB (Headroom=${HEADROOM_RAM}, lean-ctx=${LEANCTX_RAM}, Honcho=${HONCHO_RAM})"
echo "Costo infra prorrateado: USD ${INFRA_COST}/mes (base USD ${SERVER_COST}/mes / ${SERVER_RAM_GB}GB RAM)"
echo
echo "=== HEADROOM (lifetime) ==="
python3 <<EOF
reqs, ts, ti, cp, sv = $REQS, $TOKENS_SAVED, $TOKENS_IN, $COST_PAID, $SAVINGS
print(f"Requests:               {reqs:>12,}")
print(f"Tokens input bruto:     {ti:>12,}")
print(f"Tokens ahorrados:       {ts:>12,} ({ts/ti*100:.1f}% del bruto)")
print(f"USD que hubiera pagado: USD {cp+sv:.2f}")
print(f"USD pagado real:        USD {cp:.2f}")
print(f"USD ahorrado:           USD {sv:.2f}")
print(f"Ratio ahorro/costo:     {sv/cp*100:.0f}%")
print()
print(f"Promedio por request:   USD {sv/reqs:.4f}, {ts/reqs:.0f} tokens")
EOF
echo
echo "=== Honcho integration check ==="
if echo "$HONCHO_WS" | grep -q "Not Found\|detail"; then
    echo "WARN: Honcho corriendo pero SIN workspace creado — RAM desperdiciada (~430MB)"
    echo "      Integrar al loop del agente o apagar con: docker compose -f ~/proyectos/honcho/docker-compose.yml stop"
else
    echo "Honcho activo con workspaces."
fi
