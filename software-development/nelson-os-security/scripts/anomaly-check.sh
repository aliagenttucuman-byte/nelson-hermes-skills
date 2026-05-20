#!/bin/bash
# Anomaly check - Compara actividad actual contra baseline del equipo Nelson
# Uso: bash anomaly-check.sh

ERRORS=0
KNOWN_PORTS="22|5678|8080|11434|6333|3000|80|443"

echo "=== ANOMALY CHECK ==="
echo "Fecha: $(date)"
echo ""

# 1. Verificar integridad de archivos criticos
if [ -f /home/$USER/.baseline_hashes.txt ]; then
    echo "--- Verificando integridad de archivos criticos ---"
    CHANGED=$(md5sum -c /home/$USER/.baseline_hashes.txt 2>/dev/null | grep -v "OK$" | wc -l)
    if [ "$CHANGED" -gt 0 ]; then
        echo "ALERTA: $CHANGED archivo(s) critico(s) modificado(s)"
        md5sum -c /home/$USER/.baseline_hashes.txt 2>/dev/null | grep -v "OK$"
        ERRORS=$((ERRORS+CHANGED))
    else
        echo "OK: Archivos criticos sin cambios"
    fi
else
    echo "INFO: No hay baseline. Generar con: bash generate-baseline.sh"
fi
echo ""

# 2. Verificar puertos desconocidos
echo "--- Puertos escuchando ---"
if command -v ss >/dev/null 2>&1; then
    UNKNOWN=$(sudo ss -tulnp 2>/dev/null | grep LISTEN | grep -v -E "$KNOWN_PORTS" | wc -l)
    if [ "$UNKNOWN" -gt 0 ]; then
        echo "ALERTA: $UNKNOWN puerto(s) desconocido(s) escuchando"
        sudo ss -tulnp 2>/dev/null | grep LISTEN | grep -v -E "$KNOWN_PORTS"
        ERRORS=$((ERRORS+UNKNOWN))
    else
        echo "OK: Solo puertos conocidos activos"
    fi
else
    echo "ss no disponible"
fi
echo ""

# 3. Verificar intentos SSH fallidos
echo "--- Intentos SSH fallidos ---"
if [ -f /var/log/auth.log ]; then
    FAILED=$(sudo grep "Failed password" /var/log/auth.log 2>/dev/null | tail -100 | wc -l)
    if [ "$FAILED" -gt 10 ]; then
        echo "ALERTA: $FAILED intentos SSH fallidos recientes"
        ERRORS=$((ERRORS+1))
    else
        echo "OK: $FAILED intentos fallidos (umbral: 10)"
    fi
else
    echo "auth.log no disponible"
fi
echo ""

# 4. Verificar procesos desconocidos (whitelist del equipo Nelson)
echo "--- Procesos no whitelisteados ---"
WHITELIST="n8n|ollama|python|ssh|docker|systemd|Xorg|gnome|bash|ps|grep|ss|who|w|/usr/sbin|tailscale|dbus|network|cron|login|rsyslog|acpid|avahi|bluetooth|irqbalance|polkit|rtkit|snapd|udisks|upower|accounts-daemon|at-spi|colord|evolution|gsd|packagekit|pulseaudio|switcheroo|fwupd|ModemManager|wpa_supplicant|hermes|nginx|postgres|redis|qdrant"
SUSPICIOUS=$(ps aux | grep -v -E "$WHITELIST" | grep -v "^USER" | grep -v "^root" | grep -v "^$" | wc -l)
if [ "$SUSPICIOUS" -gt 0 ]; then
    echo "WARNING: $SUSPICIOUS proceso(s) no en whitelist:"
    ps aux | grep -v -E "$WHITELIST" | grep -v "^USER" | grep -v "^root" | grep -v "^$" | head -5
fi
echo ""

# 5. Verificar firewall
if command -v ufw >/dev/null 2>&1; then
    echo "--- Firewall ---"
    STATUS=$(sudo ufw status 2>/dev/null | head -1)
    if echo "$STATUS" | grep -q "inactive"; then
        echo "WARNING: Firewall UFW INACTIVO"
        ERRORS=$((ERRORS+1))
    else
        echo "OK: Firewall activo"
    fi
fi
echo ""

# 6. Verificar uso de recursos
echo "--- Recursos ---"
CPU_HIGH=$(ps aux --sort=-%cpu | awk 'NR==2{print $3}' | sed 's/,/./')
RAM_PCT=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
echo "CPU top proceso: ${CPU_HIGH}%"
echo "RAM usada: ${RAM_PCT}%"
if (( $(echo "$CPU_HIGH > 90" | bc -l) )); then
    echo "ALERTA: Proceso con CPU > 90%"
    ERRORS=$((ERRORS+1))
fi
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "SISTEMA OK - Sin anomalias detectadas"
else
    echo "ANOMALIAS DETECTADAS: $ERRORS"
fi
echo "=== FIN ==="
