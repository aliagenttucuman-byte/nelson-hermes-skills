# Azure AI Foundry — Anthropic Claude

Proveedor: Microsoft Azure AI Foundry (acceso a modelos Anthropic Claude via Azure, sin API key propia de Anthropic).

## Endpoint

```
POST https://<tu-recurso>.services.ai.azure.com/anthropic/v1/messages
```

Ejemplo real: `https://yizlafclc001.services.ai.azure.com/anthropic/v1/messages`

## Headers requeridos

| Header | Valor |
|--------|-------|
| `Content-Type` | `application/json` |
| `x-api-key` | `<tu-azure-api-key>` |
| `anthropic-version` | `2023-06-01` |

> **Pitfall:** Azure NO usa `Authorization: Bearer <key>`. Usa `x-api-key`. Si omitís `anthropic-version`, error 400: "anthropic-version: header is required".

## Modelos disponibles

| Modelo | Streaming | Temperatura | Uso |
|--------|-----------|-------------|-----|
| `claude-sonnet-4-6` | Sí | ✅ Sí acepta | Rápido, equilibrado |
| `claude-opus-4-7` | Sí | ❌ NO acepta | Más capaz, más lento |

> **Pitfall:** `claude-opus-4-7` rechaza `temperature` con error 400: "`temperature` is deprecated for this model". No enviar `temperature` para este modelo. `claude-sonnet-4-6` sí lo acepta sin problemas.

## Ejemplo de request (sonnet)

```bash
curl -X POST "https://yizlafclc001.services.ai.azure.com/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $AZURE_ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 256,
    "temperature": 0.1,
    "messages": [{"role": "user", "content": "Hola"}]
  }'
```

## Ejemplo de request (opus — sin temperature)

```bash
curl -X POST "https://yizlafclc001.services.ai.azure.com/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $AZURE_ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-opus-4-7",
    "max_tokens": 256,
    "messages": [{"role": "user", "content": "Hola"}]
  }'
```

## Script cliente Python

```python
import os
import requests
import json
from typing import Optional

BASE_URL = os.getenv("AZURE_ANTHROPIC_BASE_URL",
                     "https://yizlafclc001.services.ai.azure.com/anthropic")
API_KEY = os.getenv("AZURE_ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = os.getenv("AZURE_ANTHROPIC_MODEL", "claude-sonnet-4-6")


def call_claude(
    messages: list[dict],
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
    system: Optional[str] = None,
) -> dict:
    model = model or DEFAULT_MODEL
    url = f"{BASE_URL}/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if system:
        payload["system"] = system

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()
```

## Variables de entorno

```bash
AZURE_ANTHROPIC_BASE_URL=https://yizlafclc001.services.ai.azure.com/anthropic
AZURE_ANTHROPIC_API_KEY=<tu-key>
AZURE_ANTHROPIC_MODEL=claude-sonnet-4-6
```

## Quirks y diferencias vs Anthropic directo

| Aspecto | Anthropic directo | Azure AI Foundry |
|---------|------------------|------------------|
| Auth | `Authorization: Bearer <key>` | `x-api-key: <key>` |
| Header version | Opcional / auto | **Obligatorio** `anthropic-version` |
| Model names | `claude-sonnet-4-20250514` | `claude-sonnet-4-6`, `claude-opus-4-7` |
| Temperatura (opus) | ✅ Sí | ❌ NO |
| Temperatura (sonnet) | ✅ Sí | ✅ Sí |

## Errores comunes

| Código | Error | Fix |
|--------|-------|-----|
| 400 | `anthropic-version: header is required` | Agregar `anthropic-version: 2023-06-01` |
| 400 | `` `temperature` is deprecated for this model `` | Omitir `temperature` para `claude-opus-4-7` |
| 401 | `PermissionDenied` / `Access denied due to invalid subscription key` | Verificar `x-api-key` (no `Authorization`) y que la key corresponda al recurso |
| 404 | `DeploymentNotFound` | El modelo no está deployado en tu recurso Azure (ver discovery abajo) |
| 404 | `Resource not found` desde `/v1/messages` | **Pitfall crítico:** el endpoint OpenAI-style (`/openai/v1/chat/completions`) NO soporta Claude en Azure Foundry. Solo el endpoint Anthropic nativo (`/anthropic/v1/messages`) habla Claude. Si FreeLLMAPI/otra herramienta envía a `/openai/v1/chat/completions`, da 404. |
| 404 | `Resource not found` desde el adapter pero `curl` directo al URL completo da 200 | **Pitfall de path prefix:** Azure Anthropic Foundry requiere `/anthropic` en el path. El adapter concatena `${baseUrl}/v1/messages`, así que si guardaste `baseUrl=https://<resource>.services.ai.azure.com` falta el `/anthropic` y se construye `https://<resource>.services.ai.azure.com/v1/messages` (incorrecto). El `baseUrl` correcto es `https://<resource>.services.ai.azure.com/anthropic`. Verificar con `curl` directo. |

## Discovery de deployments disponibles

Los deployment names en Azure Foundry **no son** los nombres genéricos de Anthropic. `claude-sonnet-4-6` puede existir como modelo público pero NO estar deployado en tu recurso. Para listar los deployments reales:

```bash
curl -sS "https://<resource>.services.ai.azure.com/openai/v1/models" \
  -H "api-key: $AZURE_ANTHROPIC_API_KEY" | python3 -m json.tool
```

Devuelve ~315 deployments. Filtrar por los que tienen `claude` en el id. Catálogo típico en producción (mayo 2026):
- `claude-sonnet-4-6` (preview)
- `claude-sonnet-4-5-20250929` (preview)
- `claude-haiku-4-5-20251001` (preview)
- `claude-opus-4-1-20250805` (preview)
- `claude-opus-4-5-20251101` (preview)
- `claude-opus-4-6`, `claude-opus-4-7`, `claude-opus-4-8` (preview)

Probar cada deployment candidate con un POST mínimo antes de cargarlo en el catálogo:

```bash
for DEPLOY in claude-sonnet-4-6 claude-sonnet-4-5-20250929 claude-haiku-4-5-20251001; do
  RESP=$(curl -sS "$ENDPOINT/anthropic/v1/messages" \
    -H "x-api-key: $KEY" \
    -H "anthropic-version: 2023-06-01" \
    -d "{\"model\":\"$DEPLOY\",\"max_tokens\":3,\"messages\":[{\"role\":\"user\",\"content\":\"x\"}]}" \
    -w "|||%{http_code}" 2>&1)
  CODE=$(echo "$RESP" | grep -oP '\|\|\|\K[0-9]+')
  echo "  $DEPLOY  HTTP $CODE"
done
```

Solo `200` indica que el deployment existe. `404` con `DeploymentNotFound` significa que ese modelo no está deployado en tu recurso.

## Prueba rápida

```bash
export AZURE_ANTHROPIC_API_KEY="<tu-key>"

# Sonnet
python3 -c "
import requests, os
r = requests.post('https://yizlafclc001.services.ai.azure.com/anthropic/v1/messages',
    headers={'Content-Type': 'application/json', 'x-api-key': os.environ['AZURE_ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'},
    json={'model': 'claude-sonnet-4-6', 'max_tokens': 64, 'messages': [{'role': 'user', 'content': 'Hola'}]})
print(r.json()['content'][0]['text'])
"

# Opus (sin temperature)
python3 -c "
import requests, os
r = requests.post('https://yizlafclc001.services.ai.azure.com/anthropic/v1/messages',
    headers={'Content-Type': 'application/json', 'x-api-key': os.environ['AZURE_ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'},
    json={'model': 'claude-opus-4-7', 'max_tokens': 64, 'messages': [{'role': 'user', 'content': 'Hola'}]})
print(r.json()['content'][0]['text'])
"
```
