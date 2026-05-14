#!/bin/bash
# run-multi-agent-spike.sh
# Crea estructura estandar para evaluar un framework multi-agente.
# Uso: ./run-multi-agent-spike.sh <nombre-framework>

set -e

FRAMEWORK=${1:-"langgraph"}
SPIKE_DIR="spikes/$(date +%Y%m%d)-${FRAMEWORK}-eval"

echo "Creando spike para: $FRAMEWORK"
mkdir -p "$SPIKE_DIR"

cat > "$SPIKE_DIR/README.md" << 'EOF'
# Spike: Evaluacion de <FRAMEWORK>

**Fecha:** YYYY-MM-DD
**Framework:** <NOMBRE>
**Objetivo:** Validar si este framework sirve para orquestar agents del area I+D+i

## Hipotesis

> "<FRAMEWORK> puede orquestar un workflow de I+D+i con 3 agents (Backend, Frontend, QA) usando Ollama local."

## Criterios de evaluacion

- [ ] Funciona con modelos locales (Ollama)
- [ ] Control de flujo suficiente (secuencia, condicionales, loops)
- [ ] Auth estable (no expira cada 30 min)
- [ ] Documentacion clara
- [ ] Tiempo de setup < 1 hora

## Setup

```bash
# Instalar
pip install <framework>

# Verificar
python3 -c "import <framework>; print('OK')"
```

## Spike

```python
# TODO: implementar spike minimo
```

## Verdict

- **VALIDATED** / **PARTIAL** / **INVALIDATED**
- **Razones:**
- **Recomendacion:**
EOF

sed -i "s/<FRAMEWORK>/${FRAMEWORK}/g" "$SPIKE_DIR/README.md"
sed -i "s/<NOMBRE>/${FRAMEWORK}/g" "$SPIKE_DIR/README.md"

cat > "$SPIKE_DIR/test_spike.py" << 'EOF'
"""Spike minimo para evaluar framework multi-agente."""
import asyncio

async def main():
    print("TODO: Implementar spike")

if __name__ == "__main__":
    asyncio.run(main())
EOF

echo "Spike creado en: $SPIKE_DIR"
echo "Proximos pasos:"
echo "  1. cd $SPIKE_DIR"
echo "  2. Editar test_spike.py"
echo "  3. Completar README.md con verdict"
