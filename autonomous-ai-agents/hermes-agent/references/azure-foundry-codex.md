# Azure Foundry — Codex / Responses API: diagnóstico y pitfalls

## Contexto

Recurso: `yiazlafoc001` (cognitiveservices.azure.com + services.ai.azure.com)
Stack: Hermes Agent con custom_providers en config.yaml

## El problema del DeploymentNotFound

El endpoint `/openai/deployments/<nombre>/responses` da 404 aunque:
- El modelo aparece en el catálogo `/openai/models`
- El nombre del deployment es correcto

**Causa raíz:** `/openai/models` lista modelos disponibles *globalmente en Azure*, no
los que están deployados en tu recurso específico. Para que funcione el endpoint
`/responses`, el modelo debe estar **explícitamente deployado** en el recurso.

Verificar deployments reales del recurso:
```bash
curl -s "https://<recurso>.cognitiveservices.azure.com/openai/deployments?api-version=2025-04-01-preview" \
  -H "api-key: $API_KEY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])),'deployments')"
```
Si retorna 0 → no hay deployments → ir al portal y crear el deployment.

## URL correcta para Responses API sin deployment explícito

```
POST https://<recurso>.cognitiveservices.azure.com/openai/responses?api-version=2025-04-01-preview
```
(sin `/deployments/<nombre>/` en la ruta)

## Diagnóstico diferencial rápido

| HTTP code | Mensaje | Causa |
|-----------|---------|-------|
| 404 `Resource not found` | `/deployments/<x>/responses` | URL incorrecta o deployment no existe |
| 404 `DeploymentNotFound` | `/openai/responses` | Modelo no deployado en el recurso |
| `"The requested operation is unsupported"` | `/chat/completions` | Deployment existe pero modelo solo soporta Responses API (chat=False) |
| 401 | cualquiera | API key incorrecta o header equivocado |

El mensaje `"The requested operation is unsupported"` en `/chat/completions` es
**buena señal**: confirma que el deployment existe y responde, pero el modelo
(ej: gpt-5.3-codex) solo admite el Responses API.

## Modelos chat=False en Azure Foundry

Estos modelos NO funcionan con `/chat/completions`. Usan el Responses API:
- `gpt-5.3-codex-2026-02-20`
- `gpt-5.3-codex-2026-02-24`  
- `codex-mini-2025-05-16`
- `gpt-5-codex-2025-09-15`
- `o1-pro`, `o3-pro`, `gpt-5-pro` (etc.)

En el catálogo aparecen como `"chat_completion": false, "inference": true`.

## Config Hermes para azure-gpt-codex

```yaml
custom_providers:
  - name: azure-gpt-codex
    base_url: https://yiazlafoc001.cognitiveservices.azure.com/openai/
    model: gpt-5.3-codex-2026-02-20
    key_env: ANTHROPIC_API_KEY
    api_mode: codex_responses
    extra_params:
      api_version: "2025-04-01-preview"
```

El patch en `run_agent.py` detecta URLs `*.cognitiveservices.azure.com` y usa
`AzureOpenAI` con `api_version=2025-04-01-preview` automáticamente.

## Pasos para crear un deployment en el portal

1. portal.azure.com → recurso `yiazlafoc001` → Azure AI Foundry
2. Models + endpoints → Deploy model
3. Buscar el modelo exacto (ej: `gpt-5.3-codex-2026-02-20`)
4. Tipo: **Global Standard** (requerido para Responses API)
5. Nombre del deployment = nombre del modelo (convención del equipo Nelson)
6. Una vez en estado "Succeeded" → probar con curl

## Webwright y Azure Foundry

Webwright usa por defecto `gpt-5.4` como modelo en `image_qa.py`. Cuando se
integra con Azure Foundry, apuntar al endpoint cognitiveservices con el modelo
deployado correspondiente.
