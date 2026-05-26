#!/bin/bash
# Secret scanning pre-commit
# Uso: bash check-secrets.sh [archivos...]
# Si no se pasan archivos, revisa los staged files de git

ERRORS=0

# Patrones de secrets
PATTERNS="(sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|password\s*=\s*['\"][^'\"]+['\"]|passwd\s*=\s*['\"][^'\"]+['\"]|token\s*=\s*['\"][^'\"]{20,}['\"]|SECRET_KEY\s*=\s*['\"][^'\"]+['\"]|DATABASE_URL.*://.*:.*@)"

if [ $# -eq 0 ]; then
    FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null)
    if [ -z "$FILES" ]; then
        echo "No hay archivos staged. Uso: bash check-secrets.sh <archivo1> [archivo2] ..."
        exit 0
    fi
else
    FILES="$@"
fi

for file in $FILES; do
    if [ ! -f "$file" ]; then
        continue
    fi
    MATCHES=$(grep -Pin "$PATTERNS" "$file" 2>/dev/null)
    if [ -n "$MATCHES" ]; then
        echo "ERROR: Posible secret detectado en $file"
        echo "$MATCHES" | head -5
        ERRORS=$((ERRORS+1))
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "COMMIT BLOQUEADO: $ERRORS problema(s) detectado(s)."
    echo "Revisar los archivos arriba antes de commitear."
    echo "Para forzar (NO recomendado): git commit --no-verify"
    exit 1
fi

echo "Secrets check OK"