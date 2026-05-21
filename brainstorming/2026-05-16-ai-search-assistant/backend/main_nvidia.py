from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ddgs import DDGS
from openai import OpenAI
import os

app = FastAPI(title="AI Search Assistant — NVIDIA NIM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# NVIDIA NIM — Mistral Medium 3.5 128B (128K contexto, free tier)
nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)
MODEL = "mistralai/mistral-medium-3.5-128b"

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    answer: str
    sources: list[dict]
    model_used: str

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    # 1. Buscar con DuckDuckGo
    results = []
    with DDGS() as d:
        for r in d.text(req.query, max_results=5):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })

    if not results:
        raise HTTPException(status_code=503, detail="No se obtuvieron resultados de búsqueda")

    # 2. Contexto para el LLM
    context = "\n\n".join([
        f"Fuente: {r['title']}\nURL: {r['url']}\nContenido: {r['snippet']}"
        for r in results
    ])

    # 3. NVIDIA Mistral Medium
    response = nvidia_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Sos un asistente de IA experto. Respondé en español argentino de forma clara, precisa y concisa, basándote únicamente en las fuentes proporcionadas. Si las fuentes no tienen información suficiente, indicalo."
            },
            {
                "role": "user",
                "content": f"Pregunta del usuario: {req.query}\n\nFuentes de internet:\n{context}\n\nRespondé de forma clara y útil:"
            }
        ],
        temperature=0.6,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content

    return SearchResponse(
        answer=answer,
        sources=results,
        model_used=MODEL
    )
