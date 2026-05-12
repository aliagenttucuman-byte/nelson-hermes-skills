---
name: nelson-workflow-security
title: Seguridad Operativa del Flujo de Trabajo
description: >
  Revisa y sanitiza todo output antes de publicar, commitear o entregar.
  Detecta secrets, passwords, tokens, datos sensibles, PII, y comandos
  peligrosos. Aplica al flujo completo del equipo Nelson.
skill: nelson-workflow-security
author: equipo-nelson
version: 1.0.0
keywords: [security, secrets, sanitization, leak-prevention, safe-execution, pii, compliance]
dependencies: []
---

# Nelson - Workflow Security & Leak Prevention

## Objetivo
Garantizar que **nada del trabajo del equipo Nelson se filtre** al exterior de forma accidental: secrets en repos, passwords en logs, datos sensibles en outputs de IA, información interna de negocio expuesta.

## Alcance
Aplica a TODO el flujo de trabajo:
- Generación de código por IA
- Commits y push a GitHub
- Outputs de n8n workflows
- Respuestas de APIs locales
- Logs del sistema
- Conversaciones y documentación

---

## 1. Secret Scanning Pre-Commit

### Antes de CADA commit, validar que NO haya:
- API keys (sk-..., gsk-..., AIza...)
- Tokens de acceso (ghp_..., gho_...)
- Passwords en texto plano
- Connection strings con credenciales
- Private keys (-----BEGIN PRIVATE KEY-----)
- Variables de entorno con valores sensibles en archivos trackeados

### Script pre-commit: check-secrets.sh
```bash
#!/bin/bash
# Ejecutar antes de cada commit

ERRORS=0

# Patrones de secrets
PATTERNS="(sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|password\s*=\s*['\"][^'\"]+['\"]|passwd\s*=\s*['\"][^'\"]+['\"]|token\s*=\s*['\"][^'\"]{20,}['\"])"

# Revisar staged files
FILES=$(git diff --cached --name-only --diff-filter=ACM)

for file in $FILES; do
    if git diff --cached "$file" | grep -Pi "$PATTERNS"; then
        echo "ERROR: Posible secret detectado en $file"
        ERRORS=$((ERRORS+1))
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo "COMMIT BLOQUEADO: $ERRORS secret(s) detectado(s)."
    echo "Usa: git commit --no-verify SOLO si estás seguro."
    exit 1
fi

echo "Secrets check OK"
```

### Instalación como hook
```bash
cp check-secrets.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 2. Sanitización de Outputs de IA

### ANTES de entregar CUALQUIER respuesta al usuario, revisar que NO contenga:
- [ ] Rutas absolutas del sistema (`/home/server/...`)
- [ ] Nombres de usuario reales del sistema
- [ ] IPs internas de la red
- [ ] Nombres de bases de datos reales (si son sensibles)
- [ ] Hostnames internos
- [ ] Stack traces con paths del sistema
- [ ] Variables de entorno con valores
- [ ] Tokens de sesión o cookies

### Reglas de sanitización
```python
def sanitize_output(text: str) -> str:
    import re
    
    # Rutas absolutas del home
    text = re.sub(r'/home/[^/\s]+', '/home/<USER>', text)
    text = re.sub(r'/Users/[^/\s]+', '/Users/<USER>', text)
    
    # IPs privadas
    text = re.sub(r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b', '<INTERNAL_IP>', text)
    
    # Emails reales del dominio interno (si aplica)
    # text = re.sub(r'[\w.-]+@tudominio\.com', '<USER>@tudominio.com', text)
    
    return text
```

---

## 3. Protección de Credenciales en Conversaciones

### NUNCA incluir en respuestas:
- Passwords de sistemas (aunque el usuario lo pida)
- Tokens de API de terceros
- Contenido de archivos `.env`
- Claves privadas o certificados
- Credenciales de bases de datos

### SI el usuario necesita una credencial:
- Indicarle dónde está almacenada (keyring, .env, etc.)
- NUNCA repetir el valor en la conversación
- Sugerir que la revise en su entorno local

---

## 4. Validación Pre-Ejecución de Comandos

### ANTES de ejecutar cualquier comando destructivo, verificar:
- `rm -rf` → Confirmar target, nunca `/` o `~`
- `DROP TABLE` → Confirmar nombre de tabla y backup
- `DELETE FROM` → Confirmar WHERE clause presente
- `docker system prune` → Confirmar intencionalidad
- `git push --force` → Confirmar branch y consecuencias
- Cualquier `sudo` → Validar que sea necesario

### Regla de oro
> Si un comando puede borrar datos o exponer información, **pausar y pedir confirmación explícita**.

---

## 5. Revisión de Workflows n8n

### Antes de activar un workflow, validar:
- [ ] Ningún nodo HTTP Request expone credenciales en URL
- [ ] Los webhooks no tienen datos sensibles en la respuesta
- [ ] Las credenciales de n8n están en el vault, no hardcodeadas
- [ ] El workflow no loguea passwords ni tokens
- [ ] Las respuestas de webhook no incluyen PII sin necesidad

---

## 6. Checklist de Seguridad por Tarea

### Al generar código
- [ ] No hay secrets hardcodeados
- [ ] Las credenciales usan variables de entorno
- [ ] No se loguean passwords ni tokens
- [ ] Los errores no exponen stack traces en producción

### Al sincronizar al repo
- [ ] `check-secrets.sh` pasó sin errores
- [ ] `.env` está en `.gitignore`
- [ ] No hay archivos de credenciales trackeados
- [ ] La memoria no contiene passwords

### Al entregar al usuario
- [ ] El output está sanitizado
- [ ] No hay rutas del sistema expuestas
- [ ] No hay IPs internas
- [ ] No se repiten credenciales del usuario

---

## 7. Reglas de Negocio del Equipo Nelson

### Información que NUNCA se expone:
- Credenciales de GCP (`~/.gcp-service-account.json`)
- Password del sistema (`srv2026`)
- Tokens de GitHub CLI
- API keys de terceros
- Datos personales de clientes
- Estrategias de negocio no públicas

### Información que SÍ se puede compartir:
- Nombres de skills y arquitectura general
- Stack tecnológico
- Buenas prácticas y patrones
- Código fuente de proyectos open-source

---

## Scripts

### validate-safe-to-commit.py
```python
#!/usr/bin/env python3
"""Valida que un archivo sea seguro para commitear."""
import re, sys, os

SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{48}',
    r'ghp_[a-zA-Z0-9]{36}',
    r'AIza[0-9A-Za-z_-]{35}',
    r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    r'password\s*=\s*[\'"][^\'"]+[\'"]',
    r'token\s*=\s*[\'"][^\'"]{20,}[\'"]',
]

def check_file(path: str) -> list:
    issues = []
    with open(path, 'r', errors='ignore') as f:
        content = f.read()
    for pattern in SECRET_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line = content[:match.start()].count('\n') + 1
            issues.append(f"  Line {line}: posible secret ({pattern[:20]}...)")
    return issues

if __name__ == "__main__":
    errors = 0
    for path in sys.argv[1:]:
        issues = check_file(path)
        if issues:
            print(f"ISSUES in {path}:")
            for issue in issues:
                print(issue)
            errors += len(issues)
    if errors:
        print(f"\nFAILED: {errors} issue(s) found")
        sys.exit(1)
    print("SAFE TO COMMIT")
```

### sanitize-response.py
```python
#!/usr/bin/env python3
"""Sanitiza una respuesta antes de entregarla al usuario."""
import re, sys

def sanitize(text: str) -> str:
    # Rutas del sistema
    text = re.sub(r'/home/[^/\s]+', '/home/<USER>', text)
    text = re.sub(r'/Users/[^/\s]+', '/Users/<USER>', text)
    # IPs privadas
    text = re.sub(r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b', '<INTERNAL_IP>', text)
    # Emails del usuario (si son sensibles)
    # text = re.sub(r'[\w.-]+@gmail\.com', '<EMAIL>', text)
    return text

if __name__ == "__main__":
    text = sys.stdin.read()
    print(sanitize(text))
```

---

## Integración con Hermes

### En cada turno, antes de responder al usuario:
1. Revisar si la respuesta contiene rutas del sistema → sanitizar
2. Revisar si contiene IPs internas → sanitizar
3. Revisar si repite alguna credencial que el usuario mencionó → NO repetir
4. Revisar si el output de un comando expone información sensible → sanitizar o advertir

### Al ejecutar comandos destructivos:
1. Detectar si es destructivo (rm, DROP, DELETE, prune, force push)
2. Pedir confirmación explícita antes de ejecutar
3. Loggear la operación para auditoría

---

## Checklist Final

- [ ] `nelson-workflow-security` cargada antes de cada sesión de trabajo
- [ ] Hook pre-commit instalado en repos activos
- [ ] Outputs sanitizados antes de entrega
- [ ] Credenciales nunca repetidas en conversación
- [ ] Comandos destructivos con confirmación
- [ ] Workflows n8n auditados antes de activación
