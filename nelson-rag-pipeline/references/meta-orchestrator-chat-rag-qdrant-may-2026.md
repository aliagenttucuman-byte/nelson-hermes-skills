# Meta-Orchestrator Chat RAG + Qdrant (May 2026)

Implementación aplicada en `/home/server/nelson/meta-orchestrator` para que el chat de JARVIS consulte estado operativo real.

## Objetivo

Conectar el endpoint `/chat` a una capa RAG que recupere contexto desde:
1. Task Memory (`/tasks/history`, `/tasks/pending`)
2. SQLite local del orquestador (`orchestration_events`, `task_graph`)
3. Qdrant como vector store (`jarvis_context`)

## Cambios clave

- Nuevo módulo: `nelson_orchestrator/rag.py`
  - `JarvisRAG.reindex(force=...)`
  - `JarvisRAG.retrieve(query, top_k)`
  - `build_rag_context(query, top_k)`
- Integración en `main.py`:
  - `GET /chat/rag/status`
  - `POST /chat/rag/reindex?force=true|false`
  - `/chat` ahora soporta `use_rag` y `top_k`
  - SSE final incluye `sources` y `rag_enabled`
- Frontend `Chat.tsx`:
  - envía `{ use_rag: true, top_k: 5 }`
  - renderiza “Fuentes RAG” (source + score)

## Decisión de resiliencia

Para evitar bloqueo por credenciales faltantes:
- Si hay `OPENAI_API_KEY`: embeddings remotos (`text-embedding-3-small` por defecto)
- Si NO hay key: fallback `hashing-local` determinístico

Esto permite demos y operación básica sin dependencia externa inmediata.

## Verificación mínima

1. `GET /chat/rag/status` -> `enabled=true`
2. `POST /chat/rag/reindex?force=true` -> `ok=true`, `documents>0`
3. `POST /chat` con `use_rag=true` -> SSE final contiene `sources`
4. UI muestra bloque “Fuentes RAG” en respuestas del asistente

## Notas

- Qdrant local se levantó como contenedor `qdrant-jarvis` en `:6333`.
- El backend del orquestador expone nuevos endpoints solo en el proceso uvicorn reiniciado con el código actualizado.
- Para producción, migrar de `hashing-local` a embeddings reales apenas haya credenciales disponibles.
