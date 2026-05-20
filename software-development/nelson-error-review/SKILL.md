---
name: nelson-error-review
description: >
  Revisión de errores y detección de anomalías en flujos de trabajo,
  APIs y generación de código. Valida salidas, monitorea logs y alerta
  cuando algo falla o se comporta de forma anómala.
category: software-development
tags: [errors, debugging, monitoring, validation, anomaly-detection]
author: JARVIS
version: 1.0.0
---

# Nelson - Error Review & Anomaly Detection

## Objetivo
Detectar, revisar y reportar errores en tiempo real en los flujos de trabajo del equipo Nelson: n8n, Ollama, generación de código, APIs y sistema.

## Flujo de Trabajo

### 1. Revisión de Estado de Servicios
```bash
# Verificar que n8n responde
curl -s http://localhost:5678/healthz | grep -q ok && echo "n8n OK" || echo "n8n FAIL"

# Verificar Ollama
curl -s http://localhost:11434/api/tags | grep -q name && echo "Ollama OK" || echo "Ollama FAIL"

# Verificar espacio en disco
df -h / | tail -1 | awk '{print $5}' | sed 's/%//' | { read p; [ $p -gt 90 ] && echo "DISCO CRÍTICO: ${p}%" || echo "Disco OK: ${p}%"; }

# Verificar memoria
free -m | awk 'NR==2{printf "RAM usada: %.1f%%\n", $3*100/$2}'
```

### 2. Revisión de Logs de n8n
```bash
# Si n8n corre en Docker
docker logs n8n --tail 50 2>&1 | grep -i -E "(error|fail|exception|crash)"

# Si corre como servicio systemd
journalctl -u n8n --no-pager -n 50 | grep -i -E "(error|fail|exception)"
```

### 3. Validación de Respuestas de API
Antes de entregar una respuesta al usuario, validar:
- HTTP status code (2xx = OK, 4xx/5xx = error)
- JSON bien formado
- Campos esperados presentes
- No hay mensajes de error en el cuerpo

### 4. Revisión de Código Generado por IA
Antes de entregar código:
- Sintaxis válida (python -m py_compile)
- Sin imports faltantes
- Sin variables indefinidas
- Sin bucles infinitos obvios
- Indentación correcta

### 5. Detección de Anomalías
Marcadores de anomalía:
- Tiempo de respuesta > 30s en APIs locales
- Uso de RAM > 90%
- Uso de disco > 90%
- GPU no disponible cuando debería estarlo
- n8n workflow con más de 3 fallos consecutivos
- Ollama devolviendo respuestas vacías o errores

## Scripts de Monitoreo

### health-check.sh
```bash
#!/bin/bash
# Health check completo del sistema Nelson

ERRORS=0

# n8n
if ! curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo "ERROR: n8n no responde"
    ERRORS=$((ERRORS+1))
fi

# Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "ERROR: Ollama no responde"
    ERRORS=$((ERRORS+1))
fi

# Disco
DISK=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK" -gt 90 ]; then
    echo "WARNING: Disco al ${DISK}%"
fi

# RAM
RAM=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$RAM" -gt 90 ]; then
    echo "WARNING: RAM al ${RAM}%"
fi

if [ $ERRORS -eq 0 ]; then
    echo "Sistema OK"
else
    echo "ERRORES DETECTADOS: $ERRORS"
fi
```

### validate-code.py
```python
#!/usr/bin/env python3
"""Valida código Python generado por IA."""
import py_compile
import sys
import ast

def validate_code(code: str) -> dict:
    result = {"valid": True, "errors": []}
    
    # Sintaxis
    try:
        ast.parse(code)
    except SyntaxError as e:
        result["valid"] = False
        result["errors"].append(f"SyntaxError: {e}")
        return result
    
    # Compilación
    try:
        compile(code, '<string>', 'exec')
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"CompileError: {e}")
    
    return result

if __name__ == "__main__":
    code = sys.stdin.read()
    result = validate_code(code)
    print("VALID" if result["valid"] else "INVALID")
    for err in result["errors"]:
        print(f"  - {err}")
```

## Integración con n8n

Agregar un nodo HTTP Request al final de cada workflow que haga POST a un webhook de monitoreo:
```json
{
  "workflow_name": "generar-codigo",
  "status": "success|error",
  "duration_ms": 1234,
  "output_preview": "..."
}
```

## Alertas

Cuando se detecta un error o anomalía:
1. Loggear con timestamp
2. Notificar al usuario si es crítico
3. Intentar recovery automático (restart service, retry, etc.)
4. Documentar en log para análisis posterior

## Reglas de Negocio

- Todo código generado por IA DEBE pasar validación antes de entrega
- Toda respuesta de API DEBE verificar status code
- Todo servicio crítico (n8n, Ollama) DEBE tener health check cada 5 min
- Anomalías menores se loguean, críticas se alertan inmediatamente
