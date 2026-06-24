# Headroom — Benchmark en workloads reales del equipo Nelson

**Fecha:** 2026-06-18  
**Versión headroom-ai:** 0.22.4  
**Modelo referencia:** claude-sonnet-4-5-20250929

## Resultados del spike

### Payloads medidos

| Tipo | Descripción | Tokens antes | Tokens después | Ahorro | Transform |
|------|-------------|-------------|----------------|--------|-----------|
| code_search | grep output × 3 (48 líneas de paths+código) | 2.027 | 307 | **85%** | `router:kompress:0.11` |
| logs | uvicorn + traceback × 5 | 1.724 | 402 | **77%** | `router:log:0.25` |
| sql_results | 200 rows JSON indent=2 | 11.842 | 2.738 | **77%** | `router:smart_crusher:0.03` |
| conversación | 8 turns (debugging session) | 1.116 | 918 | **18%** | `router:kompress:0.30` |

### Config default vs config correcta

| Config | code_search | logs | sql_results |
|--------|-------------|------|-------------|
| default | 0% | 0% | 0% |
| `compress_user_messages=True, protect_recent=0` | **85%** | **77%** | **77%** |

**La config default da 0% porque protege mensajes del usuario (`router:protected:user_message`).**  
Para tool outputs siempre usar `compress_user_messages=True`.

## Proyección de costo mensual

Tomando JSON SQL (payload más típico de agentes con DB):
- Sin Headroom: 11.842 tokens/call
- Con Headroom: 2.738 tokens/call
- A $3/MTok, 500 calls/día × 30 días:
  - Sin: ~$534/mes
  - Con: ~$123/mes
  - **Ahorro: ~$411/mes**

## Cuándo usar

| Escenario | Recomendación |
|-----------|---------------|
| JARVIS leyendo archivos/código | lean-ctx (ya integrado) |
| Agente hijo procesando outputs de DB | Headroom proxy |
| Agente hijo analizando logs/tracebacks | Headroom proxy |
| Agente hijo con resultados de búsqueda masivos | Headroom proxy |
| Conversación normal | No necesario |

## Cómo levantar el proxy

```bash
headroom proxy --port 8787 2>&1 | tee /tmp/headroom_proxy.log
# Verificar
curl http://localhost:8787/health
```

Salida esperada al iniciar:
```
URL:          http://127.0.0.1:8787
Mode:         token
Optimization: ENABLED
Routing:
  /v1/messages      → https://api.anthropic.com
  /v1/chat/completions → https://api.openai.com
```

## Uso en agentes hijos

```python
from headroom import compress
from headroom.compress import CompressConfig

def compress_tool_output(tool_output: str) -> str:
    cfg = CompressConfig(compress_user_messages=True, protect_recent=0)
    messages = [{"role": "user", "content": tool_output}]
    result = compress(messages, model="claude-sonnet-4-5-20250929", config=cfg)
    return result.messages[0]["content"]
```

## Arquitectura complementaria con lean-ctx

```
JARVIS
├── lean-ctx → comprime lecturas de archivos, shell outputs (in-process)
└── spawna agente hijo
      └── agente hijo → Headroom :8787 (proxy) → LLM
                         comprime tool outputs masivos antes del LLM
```
