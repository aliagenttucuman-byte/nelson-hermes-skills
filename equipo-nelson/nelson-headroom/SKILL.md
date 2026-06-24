---
name: nelson-headroom
description: "Headroom proxy de compresión de contexto para agentes del equipo Nelson. Ahorra 77-85% de tokens en tool outputs, logs y JSON. Corre en :8787, ruteando a Azure Anthropic."
version: 1.0.0
author: Nelson + JARVIS
---

# Headroom — Compresión de contexto para agentes Nelson

Spike validado: 2026-06-18. Ahorro real medido: 77-85% en payloads típicos.

## IMPORTANTE — JARVIS ya ruteea por Headroom (desde 2026-06-18)

~/.hermes/config.yaml tiene base_url=http://127.0.0.1:8787
Si el proxy no está corriendo, JARVIS no puede hablar con el LLM.
Ver: references/hermes-config-change.md

## Instalación (ya hecha en ai-server)

```bash
pip3 install 'headroom-ai[all]'
```

## Config permanente

Archivo: `~/.headroom/config.yaml`
```yaml
compress:
  compress_user_messages: true
  protect_recent: 0
  target_ratio: 0.3
```

Variables de entorno (en ~/.bashrc):
```bash
export ANTHROPIC_TARGET_API_URL=https://yizlafclc001.services.ai.azure.com/anthropic/
export HEADROOM_TELEMETRY=off
```

## Levantar el proxy

**Preferencia de Nelson: los servicios críticos NO deben caerse — usar systemd, no scripts manuales.**

### Opción recomendada: systemd service (autoreinicio garantizado)

Template canónico: `templates/headroom-proxy.service` (en este skill).

Instalación:
```bash
sudo cp ~/.hermes/skills/equipo-nelson/nelson-headroom/templates/headroom-proxy.service /etc/systemd/system/
sudo touch /var/log/headroom-proxy.log
sudo chown server:server /var/log/headroom-proxy.log
sudo systemctl daemon-reload
sudo systemctl enable headroom-proxy.service   # arranca al boot
sudo systemctl start headroom-proxy.service
sleep 7   # primera ejecución carga ModernBERT, demora ~5-8s
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8787/health   # debe ser 200
```

Verificación de que quedó persistente:
```bash
systemctl is-active headroom-proxy.service   # active
systemctl is-enabled headroom-proxy.service  # enabled
```

Si se cae, `Restart=always RestartSec=5` lo levanta solo. Si se reinicia el server, arranca automáticamente.

### Opción legacy: script manual (sólo para debug)

```bash
bash ~/.hermes/scripts/headroom_proxy.sh
```

O directamente:
```bash
headroom proxy --port 8787 --intercept-tool-results
```

Antes de arrancar manualmente, matar la instancia previa: `pkill -f "headroom proxy"; sleep 2`.
Si ya está corriendo via systemd, NO levantar manual — duplica el proceso y choca el puerto.

Health check: `curl http://localhost:8787/health`
Stats: `curl http://localhost:8787/stats`

### El binario `headroom` no está en PATH por defecto

El script canónico `~/.hermes/scripts/headroom_proxy.sh` falla con
`headroom: command not found` porque el binario vive en el venv de Hermes:
`/home/server/.hermes/hermes-agent/venv/bin/headroom`

Si el script falla, lanzar el proxy manualmente con path absoluto:

```bash
export ANTHROPIC_TARGET_API_URL=https://yizlafclc001.services.ai.azure.com/anthropic/
export HEADROOM_TELEMETRY=off
export PATH="/home/server/.hermes/hermes-agent/venv/bin:$PATH"
headroom proxy --host 127.0.0.1 --port 8787 --intercept-tool-results
```

Fix permanente (recomendado): parchear `~/.hermes/scripts/headroom_proxy.sh`
para que exporte el PATH del venv de Hermes antes del comando `headroom`.
La próxima vez `bash ~/.hermes/scripts/headroom_proxy.sh` sale al toque.

Diagnóstico rápido: si `headroom` falla con "command not found", NO es un
problema de la instalación — es el PATH. `find / -name headroom -executable`
te lo encuentra en el venv.

## Usar en agentes hijos

Para delegate_task o subagentes que usen anthropic SDK:
```python
import anthropic, os
client = anthropic.Anthropic(
    api_key=os.environ["AZURE_ANTHROPIC_API_KEY"],
    base_url="http://127.0.0.1:8787"   # ← proxy en vez de Azure directo
)
```

Para Claude Code / Codex CLI:
```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude
```

## Usar la librería directamente (sin proxy)

Para pipelines Python donde querés comprimir antes de llamar:
```python
from headroom import compress
from headroom.compress import CompressConfig

cfg = CompressConfig(
    compress_user_messages=True,
    protect_recent=0,
    target_ratio=0.3,
)
result = compress(messages, model="claude-sonnet-4-6", config=cfg)
compressed_messages = result.messages
print(f"Ahorro: {result.tokens_saved} tokens ({result.tokens_saved/result.tokens_before*100:.1f}%)")
```

## Resultados del spike (payloads reales del equipo Nelson)

| Tipo de payload | Tokens antes | Tokens después | Ahorro |
|---|---|---|---|
| grep/code search | 2.027 | 307 | 85% |
| logs + traceback | 1.724 | 402 | 77% |
| JSON SQL 200 rows | 11.842 | 2.738 | 77% |

Proyección: 500 calls/día × 30 días @ $3/MTok → ~$411/mes ahorrado.

## Stack completo: lean-ctx + Headroom + Honcho

Cuando Nelson pide documentación del stack de tokens, son 3 capas distintas:
- lean-ctx: compresión in-process de lo que el agente LEE (MCP tools, re-reads cacheados)
- Headroom: compresión del historial antes de enviarlo al LLM (este skill)
- Honcho: memoria semántica — trae solo el contexto relevante por query

NO documentar solo Headroom si Nelson pide el stack completo.
Referencia de doc integrada: `/tmp/stack-tokens/TOKEN_OPTIMIZATION_STACK.md`

## Arquitectura complementaria con lean-ctx

```
JARVIS (lean-ctx activo — comprime reads/shell/search)
  └── spawna agente hijo
        └── agente → Headroom :8787 → Azure Anthropic
```

lean-ctx: comprime lo que JARVIS lee (in-process, 0 latencia)
Headroom: comprime lo que los agentes hijos mandan al LLM (proxy transparente)

## Enchufar JARVIS al proxy (ahorro máximo)

Cambiar base_url en `~/.hermes/config.yaml`:
```yaml
model:
  provider: custom
  base_url: http://127.0.0.1:8787   # ← proxy en vez de Azure directo
  api_mode: anthropic_messages
  api_key: ${AZURE_ANTHROPIC_API_KEY}
```

Para revertir si algo falla:
```yaml
  base_url: https://yizlafclc001.services.ai.azure.com/anthropic/
```

El proxy debe estar corriendo ANTES de que Hermes arranque, sino todas las llamadas fallan.
Script de arranque: `bash ~/.hermes/scripts/headroom_proxy.sh`

## Ver ahorro en tiempo real

```bash
curl -s http://localhost:8787/stats | python3 -m json.tool | grep -E 'tokens|savings|compressed'
```

## Documentación genérica exportable

Para compartir el procedimiento con un cliente o equipo externo sin exponer
nombres internos, usar la plantilla en `references/HEADROOM_TOKEN_OPTIMIZATION.md`.
Cubre: instalación, config, arranque, benchmark, resultados de referencia y pitfalls.
No menciona proyectos ni personas — apta para entregar directamente a stakeholders.

## Stats reales (sesión 2026-06-19)

469 requests, 0 errores, 0 rate limits.
- Tokens enviados: 9.9M
- Tokens ahorrados por compresión: 5.7M (36%)
- Mejor compresión individual: 63.9K → 28.9K (54%)
- Costo sin Headroom: $32.64
- Costo con Headroom: $15.64
- Ahorro compresión: $17.01
- Ahorro prefix cache: $42.12 (84.7% hit rate)
- Total ahorrado: ~$59 en el día

## Stats acumuladas (sesión 2026-06-23)

1264 requests lifetime, 1269 con sesión display, 56.36% savings sesión actual.
- Tokens ahorrados: 16.38M
- Total input tokens: 24.21M
- Costo input: $40.28
- Compresión savings: $49.14
- Proxy status: healthy / ready / anthropic_pre_upstream activo
- Display session (reciente): 15 req, 238K tokens ahorrados, 56.36%

## Arranque permanente via systemd (RECOMENDADO)

El proxy no debe levantarse manualmente — siempre via systemd con `Restart=always`.
Service file en `/etc/systemd/system/headroom-proxy.service`:

```ini
[Unit]
Description=Headroom Proxy - Token compression for Hermes Agent
After=network.target

[Service]
Type=simple
User=server
WorkingDirectory=/home/server
Environment="ANTHROPIC_TARGET_API_URL=https://yizlafclc001.services.ai.azure.com/anthropic/"
Environment="HEADROOM_TELEMETRY=off"
Environment="PATH=/home/server/.hermes/hermes-agent/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/server/.hermes/hermes-agent/venv/bin/headroom proxy --host 127.0.0.1 --port 8787 --intercept-tool-results
Restart=always
RestartSec=5
StandardOutput=append:/var/log/headroom-proxy.log
StandardError=append:/var/log/headroom-proxy.log

[Install]
WantedBy=multi-user.target
```

Install:
```bash
sudo cp headroom-proxy.service /etc/systemd/system/
sudo touch /var/log/headroom-proxy.log && sudo chown server:server /var/log/headroom-proxy.log
sudo systemctl daemon-reload
sudo systemctl enable --now headroom-proxy.service
```

El PATH en Environment= **debe** incluir el venv de Hermes — sino vuelve a fallar `command not found`.

Ver patrón general en skill `nelson-systemd-services`.

## Pitfalls

- Config default del proxy NO comprime user messages — REQUIERE `~/.headroom/config.yaml` con `compress_user_messages: true` y `protect_recent: 0`. Sin este archivo el ahorro es 0%.
- Config default del proxy NO comprime user messages — REQUIERE `~/.headroom/config.yaml` con `compress_user_messages: true` y `protect_recent: 0`. Sin este archivo el ahorro es 0%.
- No hay env vars para compress_user_messages ni protect_recent en el CLI — solo vía config.yaml o librería Python.
- El proxy muere si se reinicia el server — relanzar con `bash ~/.hermes/scripts/headroom_proxy.sh`
- Azure como upstream: usar `ANTHROPIC_TARGET_API_URL` (no --backend bedrock ni openrouter)
- El modelo en las llamadas debe ser el nombre Azure (ej: claude-sonnet-4-6)
- Si JARVIS está enchufado al proxy y el proxy se cae, Hermes pierde conectividad completamente — monitorear con `curl http://localhost:8787/health`
- Al generar diagrama PNG del stack con matplotlib en el servidor: los emojis NO renderizan (sin fuente emoji instalada) — usar texto plano o símbolos ASCII en su lugar
- drawio CLI exporta con `xvfb-run -a drawio --export --format png` pero puede fallar si el .drawio tiene sintaxis compleja — fallback: renderizar con matplotlib directamente
- **config.yaml tiene 3 ocurrencias de base_url** — al parchear la línea de base_url de Hermes, incluir las líneas adyacentes (provider + api_mode) para que el patch sea único.
- **Stats en cero ≠ proxy roto** — el endpoint /stats solo muestra requests que ya pasaron. Normal en proxy recién levantado.
- **El proxy no produce output visible inmediatamente** — usar sleep 3-5 antes de leer el log para ver la URL 127.0.0.1:8787.
- trycloudflare URLs cambian cada vez que se regenera el túnel — ERR_NAME_NOT_RESOLVED significa que el túnel anterior murió, no que el servidor esté caído
- **`headroom: command not found` ≠ instalación rota** — el binario vive en el venv de Hermes (`/home/server/.hermes/hermes-agent/venv/bin/headroom`). Exportar el PATH antes de invocar, o parchar el script canónico `~/.hermes/scripts/headroom_proxy.sh` para que incluya el venv. Sesión 2026-06-23 reprodujo este problema.
- **Health = 200 no garantiza upstream reachable** — el endpoint `/health` reporta `http_client: ready` apenas el proxy arranca, antes de validar conectividad real con Azure. Si JARVIS falla calls, verificar `curl -X POST http://localhost:8787/v1/messages` con un payload mínimo antes de culpar al proxy.
- **Uptime y ready en 0s** = proxy recién levantado, no roto. El sistema completa la inicialización de health checks en ~3-5 segundos.
