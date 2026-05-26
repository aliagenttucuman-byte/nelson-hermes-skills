# Azure AI Foundry — GPT-5.x / Codex Responses API

## Status

✅ **WORKING** with a local patch to `run_agent.py` (applied 2026-05-26, verified on `gpt-5.3-codex`).

The patch detects `*.cognitiveservices.azure.com` URLs and routes them through `openai.AzureOpenAI` with the correct `api_version`, solving the auth-header mismatch and missing `api-version` parameter that caused HTTP 404 on every request.

---

## Verified Endpoints (2026-05-26)

### Claude Sonnet 4-6 — Works natively ✅

No patch needed. Hermes's Anthropic adapter auto-detects `azure.com` and sends `x-api-key` + `api-version=2025-04-15`.

Config:
```yaml
custom_providers:
  - name: azure-claude
    base_url: https://yiazlafoc001.services.ai.azure.com/anthropic/
    model: claude-sonnet-4-6
    key_env: ANTHROPIC_API_KEY
    api_mode: anthropic_messages
```

### GPT-5.3-Codex — Works with patch ✅

Config:
```yaml
custom_providers:
  - name: azure-gpt-codex
    base_url: https://yiazlafoc001.cognitiveservices.azure.com/openai/
    model: gpt-5.3-codex
    key_env: ANTHROPIC_API_KEY
    api_mode: codex_responses
```

Usage:
```bash
hermes chat -m "custom:azure-gpt-codex"
```

---

## The Problem (Pre-Patch)

Azure AI Foundry endpoints at `*.cognitiveservices.azure.com` serving GPT-5.x and Codex models use the **Responses API** (`/openai/responses?api-version=...`). Hermes failed because:

1. **Auth header mismatch** — `openai.OpenAI` sends `Authorization: Bearer <key>`. Azure requires `api-key: <key>`.
2. **Missing `api-version`** — Azure requires `?api-version=2025-04-01-preview`. The OpenAI SDK omits it.

Azure returns **HTTP 404** (not 401/403) when either is missing — a misleading symptom that looks like a routing error.

---

## The Patch

Two changes in `~/.hermes/hermes-agent/run_agent.py`:

### 1. Add detector method (`_is_azure_cognitive_url`)

Inserted near the existing `_is_azure_openai_url()` (around line 3300):

```python
    def _is_azure_cognitive_url(self, base_url: str = None) -> bool:
        """Return True when a base URL targets Azure Cognitive Services / Azure AI.

        These endpoints (``*.cognitiveservices.azure.com``) expose the
        OpenAI Responses API and require ``openai.AzureOpenAI`` with an
        explicit ``api_version`` query parameter.
        """
        if base_url is not None:
            url = str(base_url).lower()
        else:
            url = getattr(self, "_base_url_lower", "") or ""
        return "cognitiveservices.azure.com" in url
```

### 2. Route to `AzureOpenAI` in `_create_openai_client()`

Inserted inside `_create_openai_client()` before the standard `client = OpenAI(**client_kwargs)` line (around line 6370):

```python
        # ------------------------------------------------------------------
        # Azure Cognitive Services / Azure AI Foundry
        # These endpoints require ``openai.AzureOpenAI`` with an explicit
        # ``api_version``.  The SDK appends ``/openai/`` internally, so we
        # strip a trailing ``/openai`` from the configured base_url before
        # passing it as ``azure_endpoint``.
        # ------------------------------------------------------------------
        _base_for_azure = str(client_kwargs.get("base_url", "") or "")
        if self._is_azure_cognitive_url(_base_for_azure):
            from openai import AzureOpenAI
            from urllib.parse import parse_qs, urlparse

            _endpoint = _base_for_azure.rstrip("/")
            if _endpoint.lower().endswith("/openai"):
                _endpoint = _endpoint[:-7]
            _api_version = "2025-04-01-preview"
            if "?" in _base_for_azure:
                _qs = parse_qs(urlparse(_base_for_azure).query)
                if "api-version" in _qs:
                    _api_version = _qs["api-version"][0]
            _azure_kwargs = {
                "azure_endpoint": _endpoint,
                "api_version": _api_version,
                "api_key": client_kwargs.get("api_key", "") or "",
            }
            if "default_headers" in client_kwargs:
                _azure_kwargs["default_headers"] = client_kwargs["default_headers"]
            if "http_client" in client_kwargs:
                _azure_kwargs["http_client"] = client_kwargs["http_client"]
            if "timeout" in client_kwargs:
                _azure_kwargs["timeout"] = client_kwargs["timeout"]
            client = AzureOpenAI(**_azure_kwargs)
            logger.info(
                "AzureOpenAI client created for Cognitive Services (%s, shared=%s) %s",
                reason,
                shared,
                self._client_log_context(),
            )
            return client
```

### Key behaviors of the patch

| Behavior | Why |
|----------|-----|
| Strips trailing `/openai` | Azure OpenAI SDK appends `/openai/` internally; keeping it results in double path segments |
| Extracts `api-version` from query string | Respects any version explicitly set in `base_url` config |
| Default `api_version="2025-04-01-preview"` | Current Azure Foundry Responses API version (verified working) |
| Forwards `default_headers`, `http_client`, `timeout` | Preserves existing client configuration (keepalive, custom headers, timeouts) |
| Logs `AzureOpenAI client created for Cognitive Services` | Confirms in logs that the patch fired |

---

## Curl Verification

### Claude

```bash
curl -s https://yiazlafoc001.services.ai.azure.com/anthropic/v1/messages?api-version=2025-04-15 \
  -H "Content-Type: application/json" \
  -H "x-api-key: <KEY>" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":50,"messages":[{"role":"user","content":"Say OK"}]}'
```

### GPT-5.3-Codex

```bash
curl -s "https://yiazlafoc001.cognitiveservices.azure.com/openai/responses?api-version=2025-04-01-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: <KEY>" \
  -d '{"model":"gpt-5.3-codex","input":[{"role":"user","content":"Say OK"}]}'
```

---

## Debugging 404 Errors — DeploymentNotFound vs Resource Not Found

Azure returns HTTP 404 for two **different** problems — the body reveals which:

| Body | Meaning | Fix |
|------|---------|-----|
| `{"error": {"code": "404", "message": "Resource not found"}}` | Routing error: wrong URL, missing `api-version`, or wrong auth header | Check patch is applied; verify `base_url` and `api_mode` |
| `{"error": {"type": "invalid_request_error", "code": "DeploymentNotFound", "message": "The API deployment for this resource does not exist..."}}` | The model deployment doesn't exist in Azure | Go to Azure Portal → AI Foundry → Deployments and verify the deployment name |

**Key pitfall:** if `DeploymentNotFound` appears even though the patch is applied and the logs show `AzureOpenAI client created for Cognitive Services`, the problem is **not** `api_version` — the patch is working. The model was simply never deployed (or has a different name) on that Azure resource.

**Debugging checklist when you see DeploymentNotFound:**
1. Go to Azure Portal → AI Foundry resource → Deployments
2. Confirm the deployment exists and its status is "Succeeded" (not Pending/Failed)
3. Confirm the deployment **name** exactly matches the `model:` field in `config.yaml` — Azure uses the deployment name as the model name in the URL
4. Confirm the resource has the Responses API enabled (some Cognitive Services resources only have `/chat/completions`)

**Quick curl to test if a deployment exists:**
```bash
curl -s "https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment-name>/responses?api-version=2025-04-01-preview" \
  -H "api-key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"<deployment-name>","input":"ping"}'
```

**Critical distinction: models catalog vs actual deployments**

The endpoint `/openai/models` lists ALL models available in the Azure catalog globally — not just what's deployed on your resource. Seeing a model there does NOT mean it's deployed. The actual deployments endpoint is separate:

```bash
# Lists only models ACTUALLY DEPLOYED on your resource (may return empty!)
curl -s "https://<resource>.cognitiveservices.azure.com/openai/deployments?api-version=2025-04-01-preview" \
  -H "api-key: <KEY>" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Deployments: {len(d.get(\"data\",[]))}')"
```

If this returns `"data": []` (0 deployments), the model was never deployed on your resource — even if it appears in `/openai/models`. You must create the deployment in Azure Portal → AI Foundry → Models + endpoints → Deploy model first.

**Verifying the deployment name vs model name:**
- Azure uses the **deployment name** (not the model ID) in URLs: `/openai/deployments/<deployment-name>/responses`
- If you deploy `gpt-5.3-codex-2026-02-20` with deployment name `my-codex`, the `model:` in config.yaml must be `my-codex`
- Convention: name the deployment identical to the model ID to avoid confusion

**How `chat=False` models behave:**
When querying `/openai/models`, models with `"chat_completion": false` (like all Codex/reasoning variants) require the Responses API (`/responses`), not `/chat/completions`. Calling `/chat/completions` returns `"The requested operation is unsupported"` — this is expected and confirms the deployment exists; it just means you need the Responses API path.

---

## Re-applying After Hermes Update

The patch is local to `~/.hermes/hermes-agent/run_agent.py`. After `hermes update`:

1. Check if the patch is still present: `grep -n "_is_azure_cognitive_url" run_agent.py`
2. If missing, re-apply manually or run the helper script in `templates/azure-cognitive-patch.py`
3. Restart Hermes (new session)

---

## Alternative: Local Proxy (No Source Patch)

If you prefer not to modify Hermes source, a FastAPI proxy still works. See the pre-patch version of this file (git history) for the proxy snippet, or use the patch template.

---

## See Also

- `references/azure-foundry-claude.md` — Azure Claude configuration (no patch needed)
- `templates/azure-cognitive-patch.py` — Re-usable script to apply the patch automatically
- SKILL.md — Custom providers section with full configuration reference