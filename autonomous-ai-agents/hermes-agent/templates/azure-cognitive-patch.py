#!/usr/bin/env python3
"""
Apply / re-apply the Azure Cognitive Services patch to Hermes run_agent.py.

This patch enables Azure AI Foundry GPT-5.x / Codex endpoints at
*.cognitiveservices.azure.com by routing them through openai.AzureOpenAI
with the correct api_version and api-key header.

Usage:
    python3 templates/azure-cognitive-patch.py

Requires: Python 3.10+, run_agent.py must be writable.
"""

import re
import sys
from pathlib import Path

RUN_AGENT = Path.home() / ".hermes" / "hermes-agent" / "run_agent.py"

PATCH_A = '''
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
'''

PATCH_B = '''
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
'''

def main() -> int:
    if not RUN_AGENT.exists():
        print(f"ERROR: {RUN_AGENT} not found", file=sys.stderr)
        return 1

    src = RUN_AGENT.read_text(encoding="utf-8")

    # Already patched?
    if "_is_azure_cognitive_url" in src:
        print("Patch already applied. Nothing to do.")
        return 0

    # Find insertion point A: after _is_azure_openai_url
    # We look for the method end (next def/class at same indent level)
    m = re.search(
        r'(    def _is_azure_openai_url\(self.*?return "openai\.azure\.com" in url\n)',
        src,
        re.DOTALL,
    )
    if not m:
        print("ERROR: could not locate _is_azure_openai_url()", file=sys.stderr)
        return 1

    src = src[: m.end()] + "\n" + PATCH_A + src[m.end() :]

    # Find insertion point B: before "client = OpenAI(**client_kwargs)"
    marker = "        client = OpenAI(**client_kwargs)"
    if marker not in src:
        print("ERROR: could not locate 'client = OpenAI(**client_kwargs)'", file=sys.stderr)
        return 1

    src = src.replace(marker, PATCH_B + marker, 1)

    RUN_AGENT.write_text(src, encoding="utf-8")
    print(f"Patch applied to {RUN_AGENT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
