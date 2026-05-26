# Azure Responses API + Hermes — Notas de sesión

## Contexto
Sesión: 2026-05-26. Intentando conectar dos endpoints de Azure AI Foundry a Hermes Agent:
1. **Azure Claude** (`claude-sonnet-4-6`) via `...azure.com/anthropic/`
2. **Azure GPT-5.3-Codex** via `...azure.com/openai/responses`

## Azure Claude — ✅ Funciona

Config en `~/.hermes/config.yaml`:
```yaml
custom_providers:
  - name: azure-claude
    base_url: https://yiazlafoc001.services.ai.azure.com/anthropic/
    model: claude-sonnet-4-6
    key_env: ANTHROPIC_API_KEY
    api_mode: anthropic_messages
```

Comando:
```bash
hermes chat -q "Hola" --provider "custom:azure-claude" --model "claude-sonnet-4-6"
```

**Trick descubierto:**
- El header `anthropic-version` es requerido por Azure (aunque la key sea de Azure)
- Hermes lo maneja correctamente cuando `api_mode: anthropic_messages`
- Sin `--model "claude-sonnet-4-6"`, Hermes envía el modelo default (`kimi-k2.6`) y Azure responde `DeploymentNotFound`

## Azure GPT-5.3-Codex — ⚠️ No funciona directo

### El problema
Azure Responses API (`/openai/responses?api-version=2025-04-01-preview`) requiere:
- Header `api-key: <key>` (formato Azure)
- Body con campo `input` en vez de `messages`
- Respuesta en formato "response" (no "chat.completion")

Hermes, con `api_mode: codex_responses`, intenta usar el SDK de Codex que espera formato OpenAI `Authorization: Bearer <key>`. Azure rechaza esto con 404.

### Logs de Hermes
```
provider=azure-foundry base_url=https://yiazlafoc001.cognitiveservices.azure.com/openai
model=gpt-5.3-codex
API call failed (attempt 1/3): HTTP 404: Resource not found
```

### Test con curl que SÍ funciona
```bash
curl -s -H "Content-Type: application/json" \
  -H "api-key: <AZURE_KEY>" \
  -d '{"model":"gpt-5.3-codex","input":[{"role":"user","content":"OK"}]}' \
  "https://yiazlafoc001.cognitiveservices.azure.com/openai/responses?api-version=2025-04-01-preview"
```

### Opciones para resolver

**Opción A — Proxy local (recomendada para equipo Nelson)**
Levantar un microservicio FastAPI que:
1. Reciba llamadas OpenAI-compatible de Hermes (`Authorization: Bearer`)
2. Re-escriba el header a `api-key`
3. Traduzca `messages` → `input`
4. Re-escriba la respuesta de "response" → "chat.completion"

**Opción B — Usar `/chat/completions` en vez de `/responses`**
Verificar si Azure permite exponer GPT-5.3-Codex via el endpoint tradicional. Si el deployment en Azure AI Foundry está configurado como "Chat completions", el endpoint sería:
```
...azure.com/openai/chat/completions?api-version=2024-10-21
```

**Opción C — Script wrapper**
Python script que use `requests` directamente al endpoint de Azure y exponga una API OpenAI-compatible localmente.

## Código de resolución del credential pool

Hermes guarda custom providers en `~/.hermes/auth.json` bajo la key `custom:<name>`. El pool se usa cuando se pasa `--provider custom:<name>`.

Para debuggear por qué una key no se encuentra:
```bash
# Ver si el provider existe en el pool
cat ~/.hermes/auth.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.get('credential_pool', {}).keys()))"

# Ver logs
hermes doctor
grep -i "base_url\|provider\|api_key" ~/.hermes/logs/agent.log | tail -30
```

## Decision tree: qué usar

```
¿Endpoint es Anthropic en Azure?
  SÍ → custom_providers con api_mode: anthropic_messages → ✅ Funciona

¿Endpoint es OpenAI /chat/completions en Azure?
  SÍ → custom_providers con api_mode: chat_completions → ✅ Funciona

¿Endpoint es /responses en Azure?
  SÍ → Hermes no soporta nativamente → Opción A/B/C → ⚠️ Requiere workaround
```

## Pitfalls

- `api_mode` se snapshottea al inicio de la sesión. Cambiarlo vía `/model` no funciona. Usar `/reset` o reiniciar Hermes.
- El nombre del modelo en `--model` debe coincidir exactamente con el deployment name en Azure. Hermes no hace mapping automático.
- Si `auth.json` tiene entradas stale (ej: key marcada como `exhausted`), Hermes puede fallar silenciosamente. Limpiar con `hermes auth reset <provider>`.
- Para Azure Claude, la key puede reutilizar `ANTHROPIC_API_KEY` en `.env` (misma key para ambos endpoints si Azure usa la misma subscription key).
