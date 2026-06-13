# Análisis: Ontos-AI/knowhere (2026-06-10)

URL: https://github.com/Ontos-AI/knowhere

## ¿Qué hace?

Knowledge graph + RAG pipeline. Ingiere documentos → extrae entidades y relaciones
→ construye grafo de conocimiento → responde queries con síntesis multi-fuente.

Foco: representación estructurada del conocimiento (no solo chunks vectoriales).

## Stack

- Python + FastAPI
- Embeddings: sentence-transformers / OpenAI
- Graph store: NetworkX (en memoria, no persistente)
- Vector store: en memoria (FAISS o similar)
- Sin Docker, sin infra seria

## Aciertos técnicos

1. **Síntesis multi-source:** en lugar de top-K chunks sueltos, consolida respuestas
   desde nodos relacionados en el grafo → menos alucinación en dominios estructurados.
2. **Extracción de relaciones:** usa el LLM para extraer triplas (sujeto, relación, objeto)
   — técnica robable para ForestAI cuando se quieran conectar especies/parcelas/inventarios.
3. **API REST limpia:** los endpoints `/ingest`, `/query`, `/graph/neighbors` son
   un buen patrón de interfaz para cualquier RAG con grafo.

## Limitaciones / Riesgos de adopción

- **Sin persistencia real:** el grafo vive en RAM. Restart = datos perdidos.
  Para producción habría que migrar a Neo4j o DGraph — trabajo no trivial.
- **Sin mantenimiento activo:** últimos commits esporádicos, issues sin respuesta.
- **NetworkX no escala:** con +100K nodos se pone lento. No es el cuello de botella
  para PoCs pero sí para producción.
- **Extracción de triplas con LLM es cara y lenta:** cada documento hace N llamadas
  al LLM para extraer relaciones. Costoso en volumen.
- **Sin autenticación, sin rate limiting, sin observabilidad.**

## Veredicto

🟡 **Robar la idea de síntesis multi-fuente y el patrón de extracción de triplas.**

No adoptar el repo directo. El valor está en el diseño conceptual, no en el código.

## Relevancia para el equipo Nelson

- **ForestAI RAG:** el patrón de grafo de conocimiento podría mejorar el RAG de
  especie/parcela/normativa si se implementa sobre Qdrant + Neo4j en lugar de NetworkX.
- **Meta-orquestador:** el grafo de relaciones entre tareas/agentes podría usar
  la misma técnica de extracción de triplas para auto-documentar workflows.
- **Template para PoC de Knowledge Graph:** si Nelson quiere armar un KG PoC,
  este repo es un buen punto de partida para el diseño de API (no para el código).
