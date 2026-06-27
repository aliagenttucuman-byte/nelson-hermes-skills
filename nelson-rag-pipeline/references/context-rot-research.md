# Context Rot: How Increasing Input Tokens Impacts LLM Performance

> Paper de investigación de Chroma (Kelly Hong, Anton Troynikov, Jeff Huber, 2025).
> URL: https://www.trychroma.com/research/context-rot

## Resumen ejecutivo

Los LLMs modernos tienen ventanas de contexto de millones de tokens (Gemini 1.5 Pro: 1M, GPT-4.1: 1M, Llama 4: 10M). Se asume que procesan todo el contexto uniformemente, pero este paper demuestra que **el rendimiento decae de forma no uniforme** a medida que crece el input, incluso en tareas simples.

## Benchmark clásico: Needle in a Haystack (NIAH)

- Es un test de **búsqueda léxica directa**: colocar una frase exacta (needle) en un documento largo (haystack) y pedir que la recupere.
- Los modelos obtienen puntuaciones casi perfectas en NIAH, lo que crea la percepción de que "contexto largo = resuelto".
- **Problema**: NIAH mide una capacidad muy estrecha. No representa el uso real de contexto largo.

## 4 experimentos del paper

| Experimento | Qué mide | Hallazgo clave |
|-------------|----------|----------------|
| **Needle-Question Similarity** | Similitud semántica entre needle y pregunta | A menor similitud, mayor degradación con longitud |
| **Impact of Distractors** | Distractores temáticamente relacionados | Los distractores amplifican el daño cuanto más largo es el input |
| **Needle-Haystack Similarity** | Similitud entre needle y el contenido circundante | El "pajar" no es transparente; su temática afecta el resultado |
| **Haystack Structure** | Estructura narrativa del texto | Desordenar el texto cambia el rendimiento del modelo |

## Conclusión clave

> "Model performance grows increasingly unreliable as input length grows."

El rendimiento decae de forma **no uniforme** a medida que crece el input, incluso en tareas simples.

## Por qué valida RAG

1. **RAG no es opcional, es obligatorio**: No se puede tirar todo en el prompt y confiar. Chunking, embeddings y retrieval selectivo son la única forma de mantener calidad.
2. **La ventana de contexto largo no elimina la necesidad de retrieval**: A mayor contexto, mayor probabilidad de "pérdida de información" en el modelo.
3. **Distractores reales**: En producción hay mucho contenido irrelevante pero temáticamente cercano. El paper muestra que esto degrada el rendimiento significativamente.
4. **Justifica infraestructura de retrieval ante stakeholders**: Puedes citar este paper para explicar por qué invertir en pipeline RAG (Qdrant, embeddings, chunking) en lugar de confiar en contexto largo.

## Implicaciones para el equipo Nelson

- Refuerza nuestra arquitectura de **agentes con memoria persistente y timeline** (SQLite/Qdrant) en lugar de depender del contexto del modelo.
- Validiza el uso de **chunking semántico** y **re-ranking** en nuestros pipelines de documentos.
- Justifica la inversión en **bases vectoriales locales** (Qdrant) en lugar de depender de ventanas de contexto externas.

## Cita BibTeX

```bibtex
@techreport{hong2025context,
  title = {Context Rot: How Increasing Input Tokens Impacts LLM Performance},
  author = {Hong, Kelly and Troynikov, Anton and Huber, Jeff},
  year = {2025},
  month = {July},
  institution = {Chroma},
  url = {https://trychroma.com/research/context-rot},
}
```
