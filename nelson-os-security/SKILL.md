---
name: nelson-os-security
title: Seguridad del Sistema Operativo - Anomaly Detection & Hardening
description: >
  Monitoreo de seguridad a nivel SO Linux. Detecta intrusiones,
  comportamiento anomalo, conexiones sospechosas, cambios en archivos
  criticos, y escanea vulnerabilidades basicas. Complementa a
  nelson-workflow-security.
skill: nelson-os-security
author: equipo-nelson
version: 1.0.0
keywords: [os-security, linux-hardening, intrusion-detection, anomaly, audit, system-monitor]
dependencies: [nelson-workflow-security]
---

# Nelson - OS Security & Anomaly Detection

## Objetivo
Detectar **accesos no autorizados, comportamiento anomalo y vulnerabilidades** en el servidor Linux donde opera el equipo Nelson. Complementa `nelson-workflow-security` (sanitizacion de outputs) cubriendo la capa del sistema operativo.

## Alcance
- Sesiones y usuarios activos
- Conexiones de red entrantes/salientes
- Procesos sospechosos o desconocidos
- Logs de autenticacion (SSH, sudo, login)
- Cambios en archivos criticos del sistema
- Puertos abiertos y servicios expuestos
- Permisos de archivos sensibles
- Baseline de actividad normal vs. anomala

---

## 1. Revisión de Sesiones y Usuarios

### Quien esta logueado ahora
```bash
who        # usuarios con sesion activa
w          # que estan haciendo
last -a    # ultimos logins
lastb      # intentos de login fallidos
```

### Alerta si:
- Hay usuarios logueados que no deberian estar
- Sesiones desde IPs extranas
- Mas de 1 sesion simultanea del mismo usuario
- `lastb` muestra intentos de fuerza bruta

---

## 2. Conexiones de Red

### Conexiones activas
```bash
ss -tulnp                    # puertos escuchando con procesos
ss -tunap | grep ESTAB       # conexiones establecidas
lsof -i -P -n                # archivos de red abiertos
```

### Alerta si:
- Hay puertos escuchando que no reconocemos
- Conexiones salientes a IPs extranas
- Muchas conexiones simultaneas desde una misma IP
- Procesos desconocidos con sockets abiertos

---

## 3. Procesos y Recursos

### Procesos activos
```bash
ps aux --sort=-%cpu | head -20   # top CPU
ps aux --sort=-%mem | head -20   # top MEM
top -bn1 | head -20              # snapshot
```

### Alerta si:
- Proceso consume 100% CPU de forma sostenida
- Proceso desconocido en el sistema
- Proceso corriendo como root que no deberia
- Mineros de crypto (alto CPU + nombre raro)
- Procesos con nombres que imitan a systemd

### Revisar arbol de procesos de nuestros servicios
```bash
pgrep -a -f "n8n|ollama|hermes|python"  # nuestros servicios
pstree -p | grep -E "n8n|ollama|hermes"
```

---

## 4. Logs de Autenticación

### SSH
```bash
sudo grep "Failed password" /var/log/auth.log 2>/dev/null | tail -20
sudo grep "Accepted password" /var/log/auth.log 2>/dev/null | tail -20
sudo journalctl -u ssh --no-pager -n 50 2>/dev/null
```

### Sudo
```bash
sudo grep "sudo:" /var/log/auth.log 2>/dev/null | tail -20
```

### Alerta si:
- Mas de 5 intentos fallidos de SSH seguidos
- Login exitoso desde IP desconocida
- Uso de sudo a horas raras
- Usuario `server` ejecutando comandos inusuales

---

## 5. Archivos Críticos - Integridad

### Archivos que NUNCA deberian cambiar sin aviso
```bash
# Sistema
/etc/passwd
/etc/shadow
/etc/sudoers
/etc/ssh/sshd_config
~/.ssh/authorized_keys
~/.bashrc
~/.profile

# Servicios
docker-compose.yml
/etc/systemd/system/*.service
```

### Baseline: guardar hashes de archivos criticos
```bash
#!/bin/bash
# generate-baseline.sh
FILES="/etc/passwd /etc/shadow /etc/sudoers /home/server/.bashrc"
for f in $FILES; do
    md5sum "$f" 2>/dev/null
done > /home/server/.baseline_hashes.txt
```

### Verificar cambios
```bash
#!/bin/bash
# check-integrity.sh
md5sum -c /home/server/.baseline_hashes.txt 2>/dev/null | grep -v "OK$"
```

---

## 6. Puertos y Servicios Expuestos

### Que esta escuchando
```bash
sudo ss -tulnp | grep LISTEN
sudo netstat -tulnp 2>/dev/null | grep LISTEN
```

### Nuestros servicios conocidos (whitelist)
- 22    SSH
- 5678  n8n
- 8080  frontend
- 11434 Ollama
- 6333  Qdrant (si corre)

### Alerta si:
- Puerto desconocido escuchando
- Servicio sin firewall expuesto a internet
- Puerto de administracion (22, 5678) accesible desde 0.0.0.0 sin restriccion

---

## 7. Revisión de Permisos

### Archivos que NO deberian ser world-readable
```bash
# Archivos con passwords o claves
find /home/server -name "*.json" -perm -o+r | grep -E "(credential|secret|key|token|env)"
find /home/server -name ".env*" -perm -o+r
ls -la /home/server/.ssh/
ls -la /home/server/.config/
```

### Alerta si:
- `~/.ssh/id_rsa` tiene permisos de lectura para otros
- `.env` es readable por cualquier usuario
- Archivos de credenciales en `/tmp`

---

## 8. Detección de Comportamiento Anómalo

### Baseline de actividad normal del equipo Nelson
Lo que ES normal:
- n8n corriendo en puerto 5678
- Ollama en 11434
- Procesos de Python para Whisper
- SSH desde la IP/local de Tony
- Docker compose para servicios conocidos
- git push al repo nelson-hermes-skills

### Lo que NO es normal (anomalia):
- Proceso de mineria (high CPU + nombre random)
- Conexion reversa a IP externa (backdoor)
- Archivos ejecutables descargados recientemente en `/tmp`
- Cambios en `/etc/passwd` o `~/.ssh/authorized_keys`
- Servicio escuchando en puerto alto (>10000) desconocido
- Usuario nuevo creado sin aviso
- Cron jobs agregados sin autorizacion

## Scripts Ejecutables

Los siguientes scripts estan disponibles en `scripts/`:
- `scripts/os-audit.sh` — Auditoria completa del sistema (usuarios, puertos, procesos, logs)
- `scripts/anomaly-check.sh` — Verificacion contra baseline y deteccion de anomalias
- `scripts/generate-baseline.sh` — Genera hashes MD5 de archivos criticos

### Uso rapido
```bash
# Generar baseline (una sola vez)
bash scripts/generate-baseline.sh

# Audit diario
bash scripts/os-audit.sh

# Chequeo de anomalias
bash scripts/anomaly-check.sh
```

### os-audit.sh - Revisión completa rapida
```bash
#!/bin/bash
echo "=== OS SECURITY AUDIT ==="
echo "Fecha: $(date)"
echo ""

echo "--- Usuarios activos ---"
who
w | head -5

echo ""
echo "--- Logins fallidos recientes ---"
sudo grep "Failed password" /var/log/auth.log 2>/dev/null | tail -5 || echo "No auth.log o sin permisos"

echo ""
echo "--- Puertos escuchando ---"
sudo ss -tulnp | grep LISTEN

echo ""
echo "--- Conexiones establecidas ---"
ss -tunap | grep ESTAB | head -10

echo ""
echo "--- Top procesos CPU ---"
ps aux --sort=-%cpu | head -10

echo ""
echo "--- Procesos desconocidos (no n8n, ollama, python, ssh, docker) ---"
ps aux | grep -v -E "n8n|ollama|python|ssh|docker|systemd|Xorg|gnome|bash|ps|grep|ss|who|w|/usr/sbin" | grep -v "^USER"

echo ""
echo "--- Archivos .env world-readable ---"
find /home/server -name ".env*" -perm -o+r 2>/dev/null

echo ""
echo "--- Cron jobs para usuario server ---"
crontab -l 2>/dev/null || echo "Sin cron jobs"

echo ""
echo "=== FIN AUDIT ==="
```

### anomaly-check.sh - Verificacion contra baseline
```bash
#!/bin/bash
# Compara actividad actual contra baseline

ERRORS=0

# 1. Verificar integridad de archivos criticos
if [ -f /home/server/.baseline_hashes.txt ]; then
    CHANGED=$(md5sum -c /home/server/.baseline_hashes.txt 2>/dev/null | grep -v "OK$" | wc -l)
    if [ "$CHANGED" -gt 0 ]; then
        echo "ALERTA: $CHANGED archivo(s) critico(s) modificados"
        md5sum -c /home/server/.baseline_hashes.txt 2>/dev/null | grep -v "OK$"
        ERRORS=$((ERRORS+CHANGED))
    fi
fi

# 2. Verificar puertos desconocidos
KNOWN_PORTS="22|5678|8080|11434|6333|3000|80|443"
UNKNOWN=$(sudo ss -tulnp | grep LISTEN | grep -v -E "$KNOWN_PORTS" | wc -l)
if [ "$UNKNOWN" -gt 0 ]; then
    echo "ALERTA: $UNKNOWN puerto(s) desconocido(s) escuchando"
    sudo ss -tulnp | grep LISTEN | grep -v -E "$KNOWN_PORTS"
    ERRORS=$((ERRORS+UNKNOWN))
fi

# 3. Verificar intentos SSH fallidos
if [ -f /var/log/auth.log ]; then
    FAILED=$(sudo grep "Failed password" /var/log/auth.log | tail -100 | wc -l)
    if [ "$FAILED" -gt 10 ]; then
        echo "ALERTA: $FAILED intentos SSH fallidos recientes"
        ERRORS=$((ERRORS+1))
    fi
fi

if [ $ERRORS -eq 0 ]; then
    echo "SISTEMA OK - Sin anomalias detectadas"
else
    echo "ANOMALIAS DETECTADAS: $ERRORS"
fi
```

---

## 10. Reglas de Alerta

### Critico (notificar inmediatamente):
- Archivos criticos modificados sin aviso
- Login SSH exitoso desde IP desconocida
- Proceso de mineria o backdoor detectado
- Puerto desconocido expuesto a internet
- Usuario nuevo creado

### Warning (loguear, revisar diariamente):
- Intentos SSH fallidos > 5
- Proceso con alto CPU por mas de 5 min
- Archivo .env world-readable
- Cambios en crontab

---

## 11. Integración con el Flujo Nelson

### Al inicio de cada sesión de trabajo:
1. Ejecutar `os-audit.sh` rapidamente
2. Verificar que servicios conocidos estan OK
3. Chequear que no haya logins sospechosos

### Antes de ejecutar comandos que tocan el sistema:
1. `check-integrity.sh` si modifica archivos criticos
2. Validar que no se exponga nuevo puerto sin firewall

### Periodicamente (una vez por dia):
1. `anomaly-check.sh`
2. Revisar `lastb` para intentos fallidos
3. Verificar permisos de archivos sensibles

---

## Checklist de Hardening

- [ ] SSH solo con key, no password (o password fuerte)
- [ ] Firewall activo (ufw) con solo puertos necesarios
- [ ] Fail2ban para proteccion SSH
- [ ] Archivos de credenciales con permisos 600
- [ ] Baseline de hashes generado
- [ ] Logs de auth monitoreados
- [ ] Servicios no usados deshabilitados
- [ ] Docker no expuesto sin TLS
- [ ] n8n con autenticacion habilitada
- [ ] Ollama solo en localhost (no expuesto)
