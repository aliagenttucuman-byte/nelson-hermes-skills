#!/usr/bin/env python3
"""
Script: Test rápido de modelos disponibles en OpenCode Zen
Uso: python3 test-opencode-models.py
Requiere: OPENCODE_API_KEY en environment o ~/secrets/opencode.env
"""
import os, sys
from pathlib import Path
from openai import OpenAI

# Cargar key desde archivo seguro si no está en env
if not os.getenv("OPENCODE_API_KEY"):
    env_file = Path.home() / "secrets" / "opencode.env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v)

API_KEY = os.getenv("OPENCODE_API_KEY")
if not API_KEY:
    print("ERROR: OPENCODE_API_KEY no encontrada")
    sys.exit(1)

BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={
        "HTTP-Referer": os.getenv("OPENCODE_REFERER", "https://github.com/nelson/rag"),
        "X-Title": os.getenv("OPENCODE_TITLE", "NelsonRAG"),
    },
)

# Modelos a probar
MODELS = [
    ("gpt-5.4-nano", "Producción — más barato"),
    ("gpt-5.4-mini", "Intermedio calidad/precio"),
    ("claude-haiku-4-5", "Barato, calidad media"),
    ("claude-sonnet-4", "Mejor calidad, más caro"),
    ("kimi-k2.6", "Contexto 262K — RAGs largos"),
]

print(f"Testing OpenCode Zen: {BASE_URL}")
print("=" * 60)

for model_id, desc in MODELS:
    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Responde solo: FUNCIONA"}],
            max_tokens=10,
            temperature=0.1,
        )
        text = resp.choices[0].message.content.strip()
        print(f"✅ {model_id:25} | {desc}")
        print(f"   Respuesta: {text[:60]}")
    except Exception as e:
        print(f"❌ {model_id:25} | {desc}")
        print(f"   Error: {str(e)[:80]}")
    print()

print("Done.")
