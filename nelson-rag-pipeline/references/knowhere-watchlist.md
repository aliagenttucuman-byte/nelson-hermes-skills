# Knowhere (Ontos-AI) — Watchlist para RAG estandarizado AlegentAI

**Estado al 2026-06-10:** WATCHLIST — no integrar todavía.
**Brainstorming:** `~/brainstorming/2026-06-10-knowhere-rag-universal/`
**Repo:** https://github.com/Ontos-AI/knowhere

---

## Qué es

Framework Python modular para knowledge management en agentes IA.
Soporta múltiples fuentes (Markdown, PDFs, URLs, JSON/CSV) y múltiples backends:
- Vector stores: Qdrant, Weaviate, ChromaDB, FAISS
- Embedders: OpenAI, HuggingFace, Cohere
- Knowledge graph: NetworkX in-memory (rudimentario)
- MIT license, pip installable (`pip install knowhere`)

## Visión AlegentAI (Nelson + Pablo)

Backend RAG estandarizado para desplegar asistentes por cliente.
Cada empresa carga su contexto (manuales, políticas, productos).
AlegentAI opera el backend, cobra por tenant o por queries.
Onboarding de días en lugar de semanas.

```
[ Cliente A: Docs ]  [ Cliente B: Manuales ]  [ Cliente C: Políticas ]
         ↓                     ↓                        ↓
    [Knowhere SDK — colección por tenant]
         ↓
    [API AlegentAI — FastAPI]
         ↓
    [Chat UI por cliente — white-label]
```

## Por qué NO hoy

| Problema | Detalle |
|----------|---------|
| v0.1.0 Alpha | Auto-clasificado como Alpha en pyproject.toml |
| 30 estrellas, 1 fork | Comunidad mínima |
| Bug packaging | `build-backend = "setuptools.backends.legacy:build"` es INVÁLIDO (issue #6, sin respuesta) |
| Grafo rudimentario | extract_entities() usa regex de palabras capitalizadas, no NER real |
| Sin MCP | No integra con agentes via MCP |
| Sin multi-tenancy | No tiene aislamiento de colecciones por cliente |
| Sin LLM calls | KnowledgeAgent devuelve chunks, no genera respuestas |

## Señales de madurez para revisitar

- [ ] > 200 estrellas en GitHub
- [ ] v0.2.0+ lanzado
- [ ] Issue #6 cerrado (bug de packaging corregido)
- [ ] Soporte MCP
- [ ] NER real en el knowledge graph
- [ ] Aparece en listas curadas (awesome-rag, etc.)

## Comparación con alternativas

| Opción | Stars | Madurez | Pro | Contra |
|--------|-------|---------|-----|--------|
| LangChain | 90k+ | Producción | Maduro, extenso | Overhead, API cambia frecuente |
| LlamaIndex | 35k+ | Producción | RAG-first, completo | Más complejo |
| Knowhere | 30 | Alpha | Simple, modular, limpio | Alpha, bug packaging |
| DIY | - | - | Control total | Tiempo de desarrollo |

## Estado del código revisado (2026-06-10)

- `knowledge_manager.py` (185 líneas): bien estructurado, type hints, limpio
- `knowledge_graph.py` (148 líneas): NetworkX en memoria — NO persistente, entities con regex
- `knowledge_agent.py` (78 líneas): NO llama LLMs, solo retrieval helper
- `chroma_store.py` (102 líneas): usa EphemeralClient por defecto (sin persistencia)
- Tests: 5 archivos de test presentes
- Último commit: 9 jun 2025 (actualización README)
- Commits: 45 totales en ~1 mes (mayo-junio 2025)
