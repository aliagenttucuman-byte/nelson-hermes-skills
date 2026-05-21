from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ddgs import DDGS
import ollama
import os

app = FastAPI(title="AI Search Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    answer: str
    sources: list[dict]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    # 1. Buscar con DuckDuckGo desde el host (no Docker)
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

    prompt = f"""Eres un asistente de IA. El usuario preguntó:
"{req.query}"

Basándote en estos resultados de internet, responde en español de forma clara y concisa:

{context}

Respuesta:"""

    # 3. LLM local via Ollama
    response = ollama.chat(
        model="qwen2.5:3b",
        messages=[{"role": "user", "content": prompt}]
    )

    return SearchResponse(
        answer=response["message"]["content"],
        sources=results
    )
