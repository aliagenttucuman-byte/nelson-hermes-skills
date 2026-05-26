#!/bin/bash
# Generar baseline de hashes para archivos criticos del sistema
# Uso: bash generate-baseline.sh
# Guarda en /home/$USER/.baseline_hashes.txt

FILES="/etc/passwd /etc/shadow /etc/sudoers /etc/ssh/sshd_config"
USER_FILES="$HOME/.bashrc $HOME/.profile $HOME/.ssh/authorized_keys"
OUTPUT="$HOME/.baseline_hashes.txt"

echo "Generando baseline en $OUTPUT..."
> "$OUTPUT"

for f in $FILES; do
    if [ -f "$f" ]; then
        md5sum "$f" >> "$OUTPUT"
        echo "  OK: $f"
    else
        echo "  SKIP: $f no existe"
    fi
done

for f in $USER_FILES; do
    if [ -f "$f" ]; then
        md5sum "$f" >> "$OUTPUT"
        echo "  OK: $f"
    else
        echo "  SKIP: $f no existe"
    fi
done

echo "Baseline generado. Verificar con: md5sum -c $OUTPUT"