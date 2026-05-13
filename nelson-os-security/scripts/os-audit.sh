#!/bin/bash
# OS SECURITY AUDIT - Script ejecutable para el equipo Nelson
# Uso: bash scripts/os-audit.sh
# Requiere: sudo para algunos comandos (puertos, logs)

echo "=== OS SECURITY AUDIT ==="
echo "Fecha: $(date)"
echo "Hostname: $(hostname)"
echo ""

echo "--- Usuarios activos ---"
who
echo ""
echo "--- Que estan haciendo ---"
w | head -5
echo ""

echo "--- Ultimos logins ---"
last -a | head -10
echo ""

echo "--- Intentos de login fallidos ---"
if [ -f /var/log/auth.log ]; then
    sudo grep "Failed password" /var/log/auth.log 2>/dev/null | tail -10 || echo "Sin intentos fallidos recientes"
else
    echo "auth.log no disponible"
fi
echo ""

echo "--- Puertos escuchando ---"
if command -v ss >/dev/null 2>&1; then
    sudo ss -tulnp | grep LISTEN 2>/dev/null || ss -tulnp | grep LISTEN
else
    sudo netstat -tulnp 2>/dev/null | grep LISTEN || netstat -tulnp | grep LISTEN
fi
echo ""

echo "--- Conexiones establecidas (top 10) ---"
if command -v ss >/dev/null 2>&1; then
    ss -tunap | grep ESTAB | head -10
else
    netstat -tunap 2>/dev/null | grep ESTAB | head -10
fi
echo ""

echo "--- Top procesos CPU ---"
ps aux --sort=-%cpu | head -10
echo ""

echo "--- Top procesos MEM ---"
ps aux --sort=-%mem | head -10
echo ""

echo "--- Cron jobs para usuario actual ---"
crontab -l 2>/dev/null || echo "Sin cron jobs"
echo ""

echo "--- Archivos .env world-readable ---"
find /home/$USER -name ".env*" -perm -o+r 2>/dev/null | while read f; do
    echo "WARNING: $f es world-readable"
done
echo ""

echo "--- Permisos de ~/.ssh ---"
ls -la ~/.ssh/ 2>/dev/null || echo "No hay directorio .ssh"
echo ""

echo "--- Firewall status ---"
sudo ufw status 2>/dev/null || echo "UFW no instalado o sin permisos"
echo ""

echo "--- Disco ---"
df -h /
echo ""

echo "--- RAM ---"
free -h
echo ""

echo "=== FIN AUDIT ==="
