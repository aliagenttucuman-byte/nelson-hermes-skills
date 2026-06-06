"""
Script de prueba para Azure AI Foundry — Anthropic Claude.
Uso: export AZURE_ANTHROPIC_API_KEY="<key>" && python3 test-azure-anthropic.py
"""
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


def claude_text(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
    system: Optional[str] = None,
) -> str:
    data = call_claude(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
    )
    content_blocks = data.get("content", [])
    for block in content_blocks:
        if block.get("type") == "text":
            return block.get("text", "")
    return ""


def claude_json(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
    system: Optional[str] = None,
) -> dict:
    full_prompt = (
        f"{prompt}\n\n"
        "Responde EXCLUSIVAMENTE con un objeto JSON válido. "
        "Sin texto adicional, sin markdown, sin explicaciones."
    )
    text = claude_text(full_prompt, model=model, max_tokens=max_tokens,
                       temperature=temperature, system=system)
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)


if __name__ == "__main__":
    print("=== Prueba Azure AI Foundry — Anthropic Claude ===\n")

    for model_name in ["claude-sonnet-4-6", "claude-opus-4-7"]:
        print(f"--- Modelo: {model_name} ---")
        try:
            reply = claude_text("Hola", model=model_name, max_tokens=64)
            print(f"Respuesta: {reply}")
            print(f"Estado: OK")
        except Exception as e:
            print(f"Error: {e}")
        print()

    print("=== Prueba JSON ===")
    try:
        result = claude_json(
            'Dame un JSON con claves "funciona" (boolean) y "modelo" (string)',
            model="claude-sonnet-4-6",
            max_tokens=256,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
