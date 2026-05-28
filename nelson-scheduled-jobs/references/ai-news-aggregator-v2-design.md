# AI News Aggregator v2 — Diseño y Fuentes

Script: `/home/server/brainstorming/2025-05-13-ai-news-aggregator/scripts/ai_news_collector_v2.py`
Output: `/home/server/brainstorming/2025-05-13-ai-news-aggregator/data/daily_digest.md`
State: `/home/server/brainstorming/2025-05-13-ai-news-aggregator/data/seen_articles_v2.json`

## Arquitectura

8 fases en secuencia, cada una con su fuente. Deduplicación por ID hash `title+link` entre corridas.

```
FASE 1: RSS Pasivo      → Labs (HuggingFace, OpenAI, Anthropic, Google, DeepMind, Meta, Mistral, Cohere, Stability, xAI)
                          Frameworks (LangChain, LlamaIndex, Microsoft Research)
                          arXiv (cs.AI, cs.LG, cs.CL, cs.CV) con filtro keywords
FASE 2: DDG News        → SEARCH_TOPICS (10 temas), timelimit="d" (solo hoy), time.sleep(0.5) entre búsquedas
FASE 3: Google News RSS → Mismos tópicos, via RSS de news.google.com/rss/search?q=...
FASE 4: Reddit          → r/MachineLearning, r/Python, r/reactjs, r/computervision, r/artificial, r/LocalLLaMA
FASE 5: Dev.to          → tags: ai, python, react, machinelearning, opensource, news
FASE 6: Referentes      → MiduDev, Brais Moure, Fazt (RSS — verificar URLs periódicamente, dan 404 a veces)
FASE 7: YouTube RSS     → Two Minute Papers, Yannic Kilcher, Andrej Karpathy, Sentdex, MiduDev YT
                          URL: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
FASE 8: GitHub Trending → python, javascript, all (via scraping HTML de github.com/trending?since=daily)
```

## Secciones del digest

Orden fijo: Búsqueda Activa → RSS Pasivo → Videos → Repositorios → Comunidad → Blogs Técnicos → Referentes → General

Máx 15 artículos por sección, ordenados por score de relevancia.

## Scoring

Función `score_relevance(title, summary)`: cuenta ocurrencias de RELEVANCE_KEYWORDS en el texto.
- DDG News: +2 bonus (búsqueda activa, más relevante)
- Dev.to: +1 bonus
- Referentes: +3 bonus
- YouTube: +2 bonus
- GitHub Trending: +3 bonus

## Cron job

- Job ID: `04bdd6e154a3`
- Schedule: `30 11,20 * * *` (11:30 y 20:30 UTC = 8:30 y 17:30 ARG)
- Deliver: `origin` (solo Nelson)
- Delivery externo (Gabi, Pablo, Faku): el prompt del cron llama a `send_whatsapp.py` via gateway Baileys en localhost:3001

## Formato del mensaje externo (texto plano, sin markdown)

```
📰 AI News I+D+I — [fecha]
[N] artículos nuevos

🔥 Highlights
• [titulo] → [link]
(máx 5 noticias)

🎬 Videos nuevos
• [titulo] — [canal] → [link youtube]
(máx 3)

🐙 Repos del día
• [owner/repo] → [link github]
(máx 5)

📄 Más noticias
• [titulo] → [link]
(máx 5)

_JARVIS — Nelson I+D+I_
```

## Pitfalls de fuentes

- **RSS referentes (MiduDev, Brais Moure, Fazt)**: URLs `/rss.xml` pueden dar 404. Verificar periódicamente.
- **DDG News rate limit**: Más de 2-3 llamadas seguidas sin pausa → 403. Fix: `time.sleep(0.5)`.
- **GitHub Trending scraping**: El HTML de github.com/trending usa clases CSS que GitHub cambia sin aviso. Si deja de parsear repos, revisar los patrones regex de `repo_pattern` y `desc_pattern`.
- **YouTube RSS namespace**: El feed de YouTube usa tres namespaces (`atom`, `yt`, `media`). Siempre parsear con el dict de namespaces completo. El videoId está en `yt:videoId`, no en `atom:link`.
- **arXiv RSS**: Los ítems de arXiv incluyen markup HTML en el `<description>`. Limpiar con `clean_text()` antes de mostrar.
