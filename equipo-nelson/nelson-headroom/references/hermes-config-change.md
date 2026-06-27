# Headroom — Cambio de config en Hermes (2026-06-18)

## Qué se cambió

~/.hermes/config.yaml — base_url cambiada de Azure directo a Headroom proxy:

```yaml
# ANTES
base_url: https://yizlafclc001.services.ai.azure.com/anthropic/

# AHORA
base_url: http://127.0.0.1:8787
```

Headroom proxy actúa como intermediario: JARVIS → Headroom :8787 → Azure Anthropic

## Implicación crítica

Si Headroom se cae, JARVIS no puede hacer llamadas al LLM.
El síntoma es connection refused al intentar cualquier completión.

Fix inmediato:
```bash
bash ~/.hermes/scripts/headroom_proxy.sh
```

Verificar que levantó:
```bash
curl http://localhost:8787/health
```

## Por qué config default del proxy NO ahorra tokens

El proxy Headroom en modo default protege mensajes del usuario (compress_user_messages=false).
Para comprimir agresivamente se necesita ~/.headroom/config.yaml:

```yaml
compress:
  compress_user_messages: true
  protect_recent: 0
  target_ratio: 0.3
```

Sin este archivo, el ahorro es 0% en mensajes del usuario.

## Resultados del spike (2026-06-18)

| Payload | Antes | Después | Ahorro |
|---|---|---|---|
| grep/code search | 2.027 tok | 307 tok | 85% |
| logs + traceback | 1.724 tok | 402 tok | 77% |
| JSON SQL 200 rows | 11.842 tok | 2.738 tok | 77% |

A $3/MTok (Sonnet), 500 calls/día × 30 días → ~$411/mes ahorrado.
