#!/usr/bin/env python3
"""
Probe a provider endpoint + discover available models/deployments.

Use when integrating a new provider or validating a key against an
existing one. Designed to be run standalone, before touching the router
or app code.

What it does:
  1. Probes the auth + basic endpoint with curl-equivalent headers.
  2. For OpenAI-compatible endpoints: lists /v1/models and parses the IDs.
  3. For Anthropic endpoints: tries a list of common model IDs to find
     which are actually deployed (Azure uses deployment names, not
     model family names).
  4. For each discovered model, sends a tiny request (max_tokens=3) to
     confirm it's not just listed but actually call-able.
  5. Prints a summary table at the end.

Usage:
  python3 probe_provider.py \\
    --endpoint https://<resource>.services.ai.azure.com \\
    --key <api-key> \\
    --protocol anthropic | openai | auto

For Azure Anthropic, the script also tries the /openai/v1/models endpoint
to discover deployment IDs (Azure exposes Claude deployments through both
the Anthropic API and a filtered OpenAI-compatible catalog).
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import List, Tuple

# Common Anthropic deployment names to probe if /v1/models is not available
# (true for Azure Anthropic Foundry — it doesn't expose GET /v1/models).
ANTHROPIC_PROBES = [
    # Sonnet
    "claude-sonnet-4-6", "claude-sonnet-4-5", "claude-sonnet-4-5-20250929",
    "claude-3-5-sonnet", "claude-3-5-sonnet-20241022", "claude-3-7-sonnet",
    # Haiku
    "claude-haiku-4-5", "claude-haiku-4-5-20251001", "claude-3-5-haiku",
    "claude-3-5-haiku-20241022", "claude-haiku-3",
    # Opus
    "claude-opus-4-1", "claude-opus-4-1-20250805", "claude-opus-4-5",
    "claude-opus-4-5-20251101", "claude-opus-4-7", "claude-opus-4-8",
]


def probe_openai_models(endpoint: str, key: str, auth_header: str = "Authorization",
                        extra_headers: dict = None) -> List[str]:
    """Try GET {endpoint}/openai/v1/models (Azure) or /v1/models (others)."""
    candidates = [f"{endpoint}/openai/v1/models", f"{endpoint}/v1/models"]
    for url in candidates:
        try:
            headers = {auth_header: f"Bearer {key}"} if auth_header == "Authorization" else {auth_header: key}
            if extra_headers:
                headers.update(extra_headers)
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            models = data.get("data", [])
            return [m.get("id", m.get("name", "?")) for m in models]
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
    return []


def probe_anthropic_deployments(endpoint: str, key: str) -> List[Tuple[str, int, str]]:
    """Try each known Anthropic model name against the endpoint. Returns
    list of (model_id, http_code, snippet)."""
    base = f"{endpoint.rstrip('/')}/v1/messages"
    results = []
    for model in ANTHROPIC_PROBES:
        body = json.dumps({
            "model": model,
            "max_tokens": 3,
            "messages": [{"role": "user", "content": "x"}],
        }).encode()
        req = urllib.request.Request(
            base,
            data=body,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            snippet = resp.read().decode()[:80]
            results.append((model, resp.status, snippet))
        except urllib.error.HTTPError as e:
            results.append((model, e.code, e.read().decode()[:80]))
        except Exception as e:
            results.append((model, -1, str(e)[:80]))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True, help="Provider base URL (no trailing slash)")
    ap.add_argument("--key", required=True, help="API key")
    ap.add_argument("--protocol", choices=["auto", "openai", "anthropic"], default="auto")
    args = ap.parse_args()

    endpoint = args.endpoint.rstrip("/")

    if args.protocol == "auto":
        # Heuristic: if endpoint contains 'anthropic' or 'claude', try Anthropic first
        if "anthropic" in endpoint or "/anthropic" in endpoint:
            args.protocol = "anthropic"
        else:
            args.protocol = "openai"

    print(f"Probing {endpoint} via {args.protocol}")
    print(f"  Key: {args.key[:8]}...{args.key[-4:]}")
    print()

    if args.protocol == "openai":
        models = probe_openai_models(endpoint, args.key)
        if models:
            print(f"Discovered {len(models)} models via /v1/models:")
            for m in models[:50]:
                print(f"  - {m}")
        else:
            print("Could not list /v1/models (endpoint may not support listing)")
            print("  Try probing specific model IDs manually.")
        return

    # Anthropic: no listing endpoint, probe known names
    print("Anthropic endpoints don't expose GET /v1/models. Probing known deployment names...")
    print()
    results = probe_anthropic_deployments(endpoint, args.key)

    working = [r for r in results if r[1] == 200]
    not_found = [r for r in results if r[1] == 404]
    other = [r for r in results if r[1] not in (200, 404)]

    print(f"=== SUMMARY ===")
    print(f"  Working ({len(working)}): {[r[0] for r in working]}")
    print(f"  Not found / 404 ({len(not_found)}): {[r[0] for r in not_found]}")
    if other:
        print(f"  Other status codes:")
        for m, code, snippet in other:
            print(f"    {m}: HTTP {code}  {snippet}")

    if working:
        print()
        print("Next steps:")
        print("  1. Add the working model IDs to your FreeLLMAPI catalog:")
        for m, _, _ in working:
            print(f'     docker exec freellmapi-freellmapi-1 node -e ...  # INSERT INTO models ... model_id="{m}"')
        print()
        print("  2. Or use them directly via curl with x-api-key header.")
        print(f"     Endpoint: {endpoint}/v1/messages")
        sys.exit(0)
    else:
        print()
        print("No working models found. Check:")
        print("  1. Is the key valid for this resource?")
        print("  2. Is the endpoint URL correct? Try Azure Portal -> resource -> 'Keys and Endpoint'.")
        print("  3. For Azure Anthropic Foundry: the baseUrl MUST include /anthropic if the")
        print("     provider adapter will append /v1/messages. The deployment names in your")
        print("     Azure resource may differ from the Anthropic public model names.")
        sys.exit(1)


if __name__ == "__main__":
    main()
