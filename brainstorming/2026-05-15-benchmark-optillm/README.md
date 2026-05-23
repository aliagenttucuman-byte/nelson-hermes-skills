# Benchmark OptiLLM — 15 Mayo 2026

## Resumen ejecutivo

OptiLLM v0.3.15 instalado y corriendo en `localhost:18000` como proxy apuntando a Ollama.
Benchmarks completados con llama3.2:3b y llama3.1:8b en problemas de razonamiento y RAG real.

**Veredicto:** Infraestructura lista. Integración en producción reservada para modelos 13B+.

## Archivos en este directorio

- `benchmark-mayo-2026.md` — Reporte completo con tablas de resultados
- `test_optillm.py` — Script de benchmark matemático (3B)
- `test_optillm_8b.py` — Script de benchmark matemático (8B)
- `test_optillm_rag_real.py` — Script de benchmark con RAG de RRHH
- `optillm_benchmark.json` — Resultados raw del benchmark 3B
- `optillm_benchmark_8b.json` — Resultados raw del benchmark 8B (parcial)
- `optillm_rag_benchmark.json` — Resultados raw del benchmark RAG real

## Skill creada

`nelson-optillm` en `~/.hermes/skills/nelson-optillm/` con:
- SKILL.md (guía completa)
- `references/benchmark-mayo-2026.md`
- `templates/rag-optillm-backend.py` (template FastAPI con switch)

## Próximo paso

Re-evaluar cuando lleguen modelos grandes (minimax2.7, kimi2.6, qwen3, llama3.1:70b).
