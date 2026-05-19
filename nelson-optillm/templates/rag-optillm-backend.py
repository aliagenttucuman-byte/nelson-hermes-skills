"""
Template: Backend FastAPI con switch OptiLLM / Ollama directo
Uso: Copiar y adaptar en proyectos RAG del equipo Nelson.

Cuando el equipo migre a modelos grandes (13B+), cambiar
USE_OPTILLM=True y el nombre del modelo.
"""
import os
import requests
from openai import OpenAI
from typing import Optional

# ---------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------

USE_OPTILLM = os.getenv("USE_OPTILLM", "false").lower() == "true"
OPTILLM_URL = os.getenv("OPTILLM_URL", "http://localhost:18000/v1")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Modelo base (cambiar cuando se migre a modelo grande)
BASE_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")

# Si USE_OPTILLM=True, se le agrega prefijo de tecnica (ej: "moa-")
OPTILLM_TECHNIQUE = os.getenv("OPTILLM_TECHNIQUE", "")  # "moa", "mcts", "re2", ""


def get_llm_client():
    """Devuelve cliente OpenAI apuntando a OptiLLM o Ollama segun config."""
    if USE_OPTILLM:
        return OpenAI(base_url=OPTILLM_URL, api_key="sk-dummy")
    return OpenAI(base_url=f"{OLLAMA_URL}/v1", api_key="ollama")


def get_model_name() -> str:
    """Devuelve el nombre completo del modelo para la llamada."""
    if USE_OPTILLM and OPTILLM_TECHNIQUE:
        return f"{OPTILLM_TECHNIQUE}-{BASE_MODEL}"
    return BASE_MODEL


def generate_answer(prompt: str, max_tokens: int = 400, temperature: float = 0.3) -> str:
    """
    Genera respuesta usando el LLM configurado.
    Switch transparente entre Ollama directo y OptiLLM.
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
        # Fallback a Ollama nativo si OptiLLM falla
        if USE_OPTILLM:
            fallback = OpenAI(base_url=f"{OLLAMA_URL}/v1", api_key="ollama")
            response = fallback.chat.completions.create(
                model=BASE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        raise


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
    return {"answer": answer, "model_used": get_model_name(), "via_optillm": USE_OPTILLM}
"""

# ---------------------------------------------------------------------------
# NOTAS PARA EL EQUIPO
# ---------------------------------------------------------------------------

"""
1. Para activar OptiLLM en un proyecto:
   export USE_OPTILLM=true
   export OPTILLM_TECHNIQUE=moa
   export LLM_MODEL=llama3.1:8b

2. Para volver a Ollama directo:
   export USE_OPTILLM=false

3. Cuando lleguen modelos grandes (minimax2.7, kimi2.6, qwen3):
   export LLM_MODEL=<nombre-del-modelo>
   export USE_OPTILLM=true
   export OPTILLM_TECHNIQUE=moa

4. OptiLLM debe estar corriendo en localhost:18000 (ver skill nelson-optillm).
"""
