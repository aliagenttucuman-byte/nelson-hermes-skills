# BigSet — Radar Tecnológico (jun 2026)

Repo: https://github.com/tinyfish-io/bigset
Stars: ~1.377 (4 semanas de vida, muy activo)
Licencia: AGPL-3.0

## Qué es

Convierte una frase en lenguaje natural en un dataset estructurado (CSV/XLSX) con refresco automático.
Usa agentes paralelos: orquestador infiere schema con LLM → sub-agentes investigan entidades en la web.

## Stack

Next.js + Fastify + TypeScript, Convex (DB reactiva), Mastra workflows, Vercel AI SDK, OpenRouter → Claude Sonnet.
Web data: TinyFish APIs (Search + Fetch + Browser).

## CLI (para uso desde agentes autónomos)

```bash
npx @adamexu/bigset
bigset create "AI infrastructure startups hiring engineers" --rows 30 --wait --csv out.csv
bigset list
bigset export <datasetId> --csv out.csv
```

Requiere: TinyFish API key (agent.tinyfish.io) + OpenRouter key.

## Casos de uso para el equipo Nelson

- Monitoreo de precios de LLMs competidores
- Startups del sector forestal/reforestación que contratan
- Empresas del mercado objetivo para AlegentAI
- Market research rápido para propuestas comerciales

## Limitaciones

- 100% TypeScript/Node — sin SDK Python. Integrar vía CLI o REST API del backend local.
- Solo datos públicos (sin login/paywall)
- Alpha — API puede cambiar
- Generación tarda 2-5 min (research real)
- Free tier: 2.500 operaciones/mes

## Veredicto

Vale la pena para market research rápido en demos con clientes. El código fuente es
referencia excelente de arquitectura orquestador + sub-agentes paralelos con herramientas web.
