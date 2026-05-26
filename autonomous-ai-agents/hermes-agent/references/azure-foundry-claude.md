# Azure AI Foundry — Claude Configuration (Verified Working)

## Overview

Azure AI Foundry hosts Claude models (Sonnet 4, Sonnet 4-6, Opus 4, etc.) on Anthropic-compatible endpoints. Hermes supports these natively via the `anthropic_messages` api_mode with automatic Azure detection.

## Verified Config (2026-05-26)

```yaml
# ~/.hermes/config.yaml
custom_providers:
  - name: azure-claude
    base_url: https://yiazlafoc001.services.ai.azure.com/anthropic/
    model: claude-sonnet-4-6
    key_env: ANTHROPIC_API_KEY
    api_mode: anthropic_messages
```

```bash
# ~/.hermes/.env
ANTHROPIC_API_KEY=<your-azure-api-key>
```

## Usage

```bash
# CLI
hermes chat -m "custom:azure-claude"

# Mid-session switch
/model custom:azure-claude
/reset

# Explicit model override
hermes chat --provider "custom:azure-claude" --model "claude-sonnet-4-6" -q "Hello"
```

## How It Works

Hermes's Anthropic adapter (`agent/anthropic_adapter.py`) auto-detects `azure.com` in the base URL and:

1. Sends `x-api-key` header instead of `Authorization: Bearer`
2. Injects `api-version=2025-04-15` query parameter
3. Uses the Anthropic SDK (not OpenAI SDK)

This is why Azure Claude works while Azure GPT/Codex does not — there is no equivalent adapter for OpenAI-family Azure endpoints.

## Important Notes

- **Start a new session** after changing providers. `api_mode` is snapshotted at startup and does not change mid-session via `/model`.
- The `key_env` variable name (`ANTHROPIC_API_KEY`) can be anything — it just references an env var in `.env`. You could use `AZURE_CLAUDE_KEY` if you prefer.
- The base URL MUST end with `/anthropic/` for the adapter to route correctly.
- If `api_mode` is omitted, Hermes infers it from the URL (detects `/anthropic` suffix → `anthropic_messages`). Setting it explicitly is safer.

## Testing with curl

```bash
curl -s https://<resource>.services.ai.azure.com/anthropic/v1/messages?api-version=2025-04-15 \
  -H "Content-Type: application/json" \
  -H "x-api-key: <YOUR_KEY>" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":50,"messages":[{"role":"user","content":"Say OK"}]}'
```

Expected response: `{"content":[{"type":"text","text":"OK"}],"...":"..."}`

## See Also

- `references/azure-foundry-codex.md` — GPT-5.x / Codex on Responses API (does NOT work yet)
- Custom providers section in SKILL.md — full provider configuration reference