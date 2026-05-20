# AI News Aggregator — Delivery Pattern

## Arquitectura de delivery

El AI News Aggregator v2 entrega contenido diferenciado:

| Destinatario | Canal | Contenido |
|---|---|---|
| Nelson | Hermes (`deliver: origin`) | Audio TTS + texto con links |
| Gabi (5491132438887) | Gateway Baileys 3001 | Texto con links |
| Pablo (5493816240691) | Gateway Baileys 3001 | Texto con links |
| Faku (5493813022552) | Gateway Baileys 3001 | Texto con links |

## Formato del mensaje externo

```
📰 AI News I+D+I — [fecha]
[N] artículos nuevos

🔥 Highlights
• [titulo] → [link]
(máx 5 noticias, score más alto)

🎬 Videos nuevos
• [titulo] — [canal] → [link youtube]
(máx 3 videos)

🐙 Repos del día
• [owner/repo] → [link github]
(máx 5 repos)

📄 Más noticias
• [titulo] → [link]
(máx 5 adicionales)

_JARVIS — Nelson I+D+I_
```

## Fuentes del script v2 (al 2026-05-19)

| Fase | Fuente | Tipo |
|---|---|---|
| 1 | RSS Pasivo (HuggingFace, OpenAI, Google AI, LangChain, arXiv) | RSS/Atom |
| 2 | DuckDuckGo News | Búsqueda activa |
| 3 | Google News RSS | Búsqueda activa |
| 4 | Reddit (r/MachineLearning, r/Python, r/reactjs, r/LocalLLaMA...) | JSON público |
| 5 | Dev.to por tags | API REST |
| 6 | Referentes (MiduDev, Brais Moure, Fazt) | RSS |
| 7 | YouTube RSS (Two Minute Papers, Yannic Kilcher, Karpathy, Sentdex, MiduDev) | Atom |
| 8 | GitHub Trending (Python, JS, all) | HTML scraping |

## Notas de implementación

- YouTube: usa `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
- GitHub Trending: scraping con regex sobre HTML raw (patrón `Link` en href). Frágil si GitHub cambia su HTML.
- Script: `/home/server/brainstorming/2025-05-13-ai-news-aggregator/scripts/ai_news_collector_v2.py`
- Output: `/home/server/brainstorming/2025-05-13-ai-news-aggregator/data/daily_digest.md`
- State (dedup): `/home/server/brainstorming/2025-05-13-ai-news-aggregator/data/seen_articles_v2.json`
- Cron job ID: `04bdd6e154a3`, schedule `30 11,20 * * *`
