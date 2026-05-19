"""
Template: Backend FastAPI con switch multi-backend (OpenCode Zen / Ollama / OptiLLM)
Uso: Copiar y adaptar en proyectos RAG del equipo Nelson.

Default: OpenCode Zen API con gpt-5.4-nano (mas barato, mejor calidad que local)
Fallback: Ollama local (llama3.2:3b) si no hay internet o API key
Experimental: OptiLLM proxy para optimizacion de inferencia (modelos grandes 13B+)
"""
import os
import requests
from openai import OpenAI
from typing import Optional

# ---------------------------------------------------------------------------
# CONFIGURACION — Leida de environment variables
# ---------------------------------------------------------------------------

# Seleccion de backend: "opencode" | "ollama" | "optillm"
LLM_BACKEND = os.getenv("LLM_BACKEND", "opencode").lower()

# --- OpenCode Zen (default) ---
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "gpt-5.4-nano")  # Mas barato, calidad OK

# --- Ollama local ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# --- OptiLLM proxy ---
OPTILLM_URL = os.getenv("OPTILLM_URL", "http://localhost:18000/v1")
OPTILLM_MODEL = os.getenv("OPTILLM_MODEL", "llama3.2:3b")
OPTILLM_TECHNIQUE = os.getenv("OPTILLM_TECHNIQUE", "")  # "moa", "mcts", "re2", ""


def get_llm_client() -> OpenAI:
    """Devuelve cliente OpenAI segun el backend configurado."""
    if LLM_BACKEND == "opencode":
        if not OPENCODE_API_KEY:
            raise ValueError("OPENCODE_API_KEY no configurada. Seteala en environment.")
        return OpenAI(
            base_url=OPENCODE_BASE_URL,
            api_key=OPENCODE_API_KEY,
            default_headers={
                "HTTP-Referer": os.getenv("OPENCODE_REFERER", "https://github.com/nelson/rag"),
                "X-Title": os.getenv("OPENCODE_TITLE", "NelsonRAG"),
            },
        )
    elif LLM_BACKEND == "optillm":
        return OpenAI(base_url=OPTILLM_URL, api_key="sk-dummy")
    else:  # ollama
        return OpenAI(base_url=f"{OLLAMA_URL}/v1", api_key="ollama")


def get_model_name() -> str:
    """Devuelve el nombre del modelo segun backend."""
    if LLM_BACKEND == "opencode":
        return OPENCODE_MODEL
    elif LLM_BACKEND == "optillm" and OPTILLM_TECHNIQUE:
        return f"{OPTILLM_TECHNIQUE}-{OPTILLM_MODEL}"
    elif LLM_BACKEND == "optillm":
        return OPTILLM_MODEL
    return OLLAMA_MODEL


def generate_answer(
    prompt: str,
    max_tokens: int = 400,
    temperature: float = 0.3,
    fallback: bool = True,
) -> str:
    """
    Genera respuesta usando el LLM configurado.
    Si fallback=True y OpenCode Zen falla, prueba Ollama local.
    """
    client = get_llm_client()
    model = get_model_name()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if fallback and LLM_BACKEND == "opencode":
            # Fallback a Ollama local
            fallback_client = OpenAI(base_url=f"{OLLAMA_URL}/v1", api_key="ollama")
            response = fallback_client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        raise


# ---------------------------------------------------------------------------
# HEALTH CHECK — Para monitorear disponibilidad de backends
# ---------------------------------------------------------------------------

def health_check() -> dict:
    """Devuelve estado de todos los backends."""
    result = {
        "backend_active": LLM_BACKEND,
        "model_active": get_model_name(),
        "backends": {},
    }

    # OpenCode Zen
    try:
        oc_client = OpenAI(base_url=OPENCODE_BASE_URL, api_key=OPENCODE_API_KEY or "test")
        oc_client.models.list(timeout=5)
        result["backends"]["opencode"] = "ok"
    except Exception:
        result["backends"]["opencode"] = "unavailable"

    # Ollama
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        result["backends"]["ollama"] = "ok" if r.status_code == 200 else "error"
    except Exception:
        result["backends"]["ollama"] = "unavailable"

    # OptiLLM
    try:
        r = requests.get(f"{OPTILLM_URL}/models", timeout=3)
        result["backends"]["optillm"] = "ok" if r.status_code == 200 else "error"
    except Exception:
        result["backends"]["optillm"] = "unavailable"

    return result


# ---------------------------------------------------------------------------
# EJEMPLO DE USO EN ENDPOINT /ask DE UN RAG
# ---------------------------------------------------------------------------

"""
from fastapi import FastAPI

app = FastAPI()

@app.post("/ask")
async def ask(question: dict):
    query = question.get("question", "").strip()
    context = retrieve_context(query)  # tu funcion de vector search

    prompt = f\"\"\"Basandote UNICAMENTE en la siguiente informacion:

{context}

PREGUNTA: {query}

RESPUESTA:\"\"\"

    answer = generate_answer(prompt)
    return {
        "answer": answer,
        "model_used": get_model_name(),
        "backend": LLM_BACKEND,
    }

@app.get("/health")
async def health():
    return health_check()
"""

# ---------------------------------------------------------------------------
# CONFIGURACION POR ENVIRONMENT
# ---------------------------------------------------------------------------

"""
# === PRODUCCION (OpenCode Zen, mas barato) ===
export LLM_BACKEND=opencode
export OPENCODE_API_KEY=sk-xxxxxxxx
export OPENCODE_BASE_URL=https://opencode.ai/zen/v1
export OPENCODE_MODEL=gpt-5.4-nano
export OPENCODE_REFERER=https://tu-app.com
export OPENCODE_TITLE=TuApp

# === DESARROLLO LOCAL (Ollama, gratis) ===
export LLM_BACKEND=ollama
export OLLAMA_MODEL=llama3.2:3b

# === EXPERIMENTAL (OptiLLM con modelos grandes) ===
export LLM_BACKEND=optillm
export OPTILLM_MODEL=llama3.1:8b
export OPTILLM_TECHNIQUE=moa

# Fallback automatico: si opencode falla, vuelve a ollama local (por defecto True)
"""
