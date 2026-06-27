# Prueba de Optimización de Tokens con Headroom

## Objetivo

Validar el ahorro real de tokens en conversaciones con agentes de IA
usando Headroom como proxy de compresión de contexto.

Resultado esperado: 77-85% de reducción en payloads típicos
(logs, JSON masivo, resultados de búsqueda de código).

---

## Stack involucrado

```
Agente (Hermes / Claude Code / SDK)
  └── Headroom Proxy :8787   ← capa de compresión
        └── LLM Provider (Azure / Anthropic / etc.)
```

---

## Pre-requisitos

- Python 3.10+ instalado
- Acceso a un proveedor LLM (Azure Anthropic, Anthropic directo, etc.)
- API key configurada en variable de entorno
- Puerto 8787 libre en el servidor

---

## Paso 1 — Instalación

```bash
pip install 'headroom-ai[all]'
headroom --version
```

---

## Paso 2 — Configuración del proxy (CRITICO)

```bash
mkdir -p ~/.headroom
cat > ~/.headroom/config.yaml << 'EOF'
compress:
  compress_user_messages: true
  protect_recent: 0
  target_ratio: 0.3
EOF
```

Sin este archivo, el proxy NO comprime mensajes de usuario y el ahorro es 0%.

---

## Paso 3 — Variables de entorno

Para Azure Anthropic:
```bash
export ANTHROPIC_TARGET_API_URL=https://<tu-endpoint>.services.ai.azure.com/anthropic/
export ANTHROPIC_API_KEY=<tu-api-key>
export HEADROOM_TELEMETRY=off
```

Para Anthropic directo:
```bash
export ANTHROPIC_API_KEY=<tu-api-key>
export HEADROOM_TELEMETRY=off
```

---

## Paso 4 — Levantar el proxy

```bash
headroom proxy --port 8787 --intercept-tool-results &
sleep 3
curl http://localhost:8787/health
```

El flag `--intercept-tool-results` es IMPORTANTE: sin él, los resultados
de herramientas (grep, bash, SQL) no se comprimen — y son la mayor fuente
de tokens en agentes con herramientas.

---

## Paso 5 — Enchufar el agente al proxy

OPCION A — Hermes Agent (~/.hermes/config.yaml):
```yaml
model:
  provider: custom
  base_url: http://127.0.0.1:8787
  api_mode: anthropic_messages
  api_key: ${ANTHROPIC_API_KEY}
```

OPCION B — Claude Code CLI:
```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude
```

OPCION C — SDK Python:
```python
import anthropic
client = anthropic.Anthropic(
    api_key="tu-key",
    base_url="http://127.0.0.1:8787"
)
```

---

## Paso 6 — Medir el ahorro

```bash
curl -s http://localhost:8787/stats | python3 -m json.tool
```

Campos clave: `tokens_before`, `tokens_after`, `tokens_saved`, `compression_ratio`.

Nota: muestra 0 si no pasó ninguna request todavía — es normal.

---

## Paso 7 — Benchmark con librería (sin proxy)

```python
from headroom import compress
from headroom.compress import CompressConfig

messages = [
    {"role": "user", "content": "buscá todos los archivos con error"},
    {"role": "tool", "content": "<resultado de grep con 500 líneas>"},
]

cfg = CompressConfig(
    compress_user_messages=True,
    protect_recent=0,
    target_ratio=0.3,
)

result = compress(messages, model="claude-sonnet-4-6", config=cfg)
print(f"Ahorro: {result.tokens_saved / result.tokens_before * 100:.1f}%")
```

---

## Resultados de referencia (medidos en entorno real)

| Tipo de payload         | Tokens antes | Tokens después | Ahorro |
|-------------------------|-------------|----------------|--------|
| Búsqueda en código      | 2.027       | 307            | 85%    |
| Logs + traceback        | 1.724       | 402            | 77%    |
| JSON SQL (200 filas)    | 11.842      | 2.738          | 77%    |

---

## Pitfalls conocidos

1. Config.yaml obligatorio — sin él, ahorro = 0%.
2. Proxy debe arrancar ANTES que el agente.
3. No persiste entre reinicios — agregar a systemd o script de inicio.
4. Azure upstream requiere ANTHROPIC_TARGET_API_URL exacta (con barra final).
5. protect_recent: 0 comprime todo — subir a 2-3 si el agente pierde contexto.
6. Stats en cero ≠ proxy roto — solo acumula requests de la sesión actual.

---

## Script de arranque reutilizable (~/.hermes/scripts/headroom_proxy.sh)

```bash
#!/bin/bash
set -e
echo "[headroom] Arrancando proxy en :8787..."
nohup headroom proxy \
  --port 8787 \
  --intercept-tool-results \
  >> /tmp/headroom_proxy.log 2>&1 &
sleep 3
curl -s http://localhost:8787/health && echo " [OK] proxy listo" \
  || echo "[ERROR] proxy no responde"
```

---

## Revertir

```bash
# Cambiar base_url del agente de vuelta al proveedor directo
pkill -f "headroom proxy"
```

---

*Documento generado — junio 2026*
