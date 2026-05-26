# AI News Aggregator v2 — Diseño

> Fecha: 2026-05-18  
> Upgrade del agregador v1 (solo RSS pasivo) a arquitectura pasivo + activo + referentes.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    AI News Aggregator v2                     │
├─────────────────────────────────────────────────────────────┤
│  FASE 1: RSS Pasivo     │ HuggingFace, OpenAI, Google AI,    │
│  (esperar a que publiquen) │ LangChain, Microsoft, arXiv     │
├─────────────────────────────────────────────────────────────┤
│  FASE 2: Búsqueda Activa │ DuckDuckGo News por keywords     │
│  (buscar intencionalmente) │ Google News RSS por tema       │
├─────────────────────────────────────────────────────────────┤
│  FASE 3: Comunidad      │ Reddit: r/MachineLearning,        │
│                         │ r/Python, r/reactjs,               │
│                         │ r/computervision, r/LocalLLaMA     │
├─────────────────────────────────────────────────────────────┤
│  FASE 4: Blogs Técnicos │ Dev.to por tags (ai, python,     │
│                         │ react, machinelearning)            │
├─────────────────────────────────────────────────────────────┤
│  FASE 5: Referentes     │ MiduDev, Brais Moure, Fazt        │
│  (personas de referencia) │ (blogs RSS, YouTube)             │
├─────────────────────────────────────────────────────────────┤
│  FASE 6: Twitter/X      │ INVESTIGACIÓN — requiere API key  │
│  (pendiente)            │ o alternativa Nitter/RSS         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Deduplicación   │ ← State file JSON
                    │ por article_id  │   (title + link hash)
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Scoring         │ ← Keywords de relevancia
                    │ de relevancia   │   (open source, llm, react,
                    │                 │    computer vision, etc.)
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Markdown Digest │ ← Organizado por sección
                    │ con emojis    │   🔥=alto, ⭐=medio, 📄=base
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ WhatsApp        │ ← Solo a Tony (por ahora)
                    │ Gateway         │   POST /send o /send-batch
                    └─────────────────┘
```

## Temas de búsqueda activa

```python
SEARCH_TOPICS = [
    "artificial intelligence",
    "machine learning",
    "computer vision",
    "large language model",
    "Python",
    "React",
    "mobile development",
    "image analytics",
    "edge AI",
    "open source AI",
]
```

## Fuentes y técnicas

| Fuente | Método | Pros | Contras |
|---|---|---|---|
| RSS pasivo | `xml.etree.ElementTree` (stdlib) | Sin rate limits, confiable | Solo reacciona a publicaciones |
| DDG News | `duckduckgo_search.DDGS.news()` | Búsqueda activa por keyword | Rate limit 403 si se spamea |
| Google News | RSS por tema (`news.google.com/rss/search?q=...`) | Sin API key | Links son redirects largos |
| Reddit | `.json` público (`reddit.com/r/{sub}/hot.json`) | JSON nativo, score visible | Puede devolver threads meta |
| Dev.to | API pública (`dev.to/api/articles?tag=...`) | JSON limpio | Limitado a ~30 artículos/tag |
| Referentes | RSS de blogs personales | Contenido curado | URLs de RSS pueden cambiar o no existir |

## Pitfalls descubiertos

1. **DDG News rate limit**: Si se llaman muchas búsquedas seguidas sin delay, DDG devuelve `403 Ratelimit`. Fix: `time.sleep(0.5)` entre búsquedas, o reducir número de topics por corrida.

2. **RSS de referentes da 404**: MiduDev, Brais Moure y Fazt no tienen `/rss.xml` en esas URLs. Hay que investigar el feed real de cada uno (puede ser FeedBurner, Substack, o no tener RSS abierto).

3. **Google News RSS links son redirects**: El `link` de cada item es un URL de tracking de Google, no el link directo al artículo. Para uso interno no importa, pero para scraping directo sí.

4. **Reddit JSON sin User-Agent adecuado**: Reddit bloquea requests sin `User-Agent` realístico. Fix: enviar `"Mozilla/5.0 (AI-News-Bot/2.0)"`.

5. **Twitter/X sin API key**: No hay acceso público a tweets desde 2023. Alternativas a investigar: Nitter (instancias públicas), RSS-Bridge, o xurl skill con login.

## State management

```python
STATE_FILE = "data/seen_articles_v2.json"

def article_id(title: str, link: str) -> str:
    clean = re.sub(r"\W+", "", (title + link).lower())[:80]
    return clean
```

El state guarda IDs de artículos ya vistos. Cada corrida del script carga el state, filtra duplicados, agrega los nuevos, y guarda el state actualizado.

## Scoring de relevancia

```python
RELEVANCE_KEYWORDS = [
    "open source", "released", "launch", "new model",
    "llm", "multimodal", "agent", "framework",
    "benchmark", "sota", "training", "inference",
    "quantization", "distillation", "rag", "fine-tuning",
    "computer vision", "image analytics", "edge ai",
    "python", "react", "fastapi", "docker",
]
```

Cada artículo suma 1 punto por keyword encontrada en título + sumario. Luego se ordena por score descendente dentro de cada sección.

## Formato de salida (Markdown)

```markdown
# 📰 Daily Digest I+D+I

📅 Lunes 18 Mayo 2026 — Fuente: Nelson Server
📊 59 artículos nuevos encontrados

---

## Búsqueda Activa

⭐ **[Título del artículo](https://link.com)**
> Resumen de 200 caracteres...
> `Fuente: DDG News / AI` | `2026-05-18`

## RSS Pasivo
🔥 **[Título arXiv](https://arxiv.org/...)**
...
```

## Estado actual (2026-05-19)

- ✅ Script v2 funcionando: `~/brainstorming/2025-05-13-ai-news-aggregator/scripts/ai_news_collector_v2.py`
- ✅ Cron jobs activos: `afa66f131c92` (0 12,21 UTC) y `04bdd6e154a3` (30 11,20 UTC)
- ✅ Delivery: Tony (origin) + Gabi (5491132438887)
- ✅ 59 artículos en primera corrida (lunes 18/05/2026)

## Próximos pasos pendientes

- [ ] Investigar feeds RSS reales de MiduDev, Brais Moure, Fazt (sus `/rss.xml` dan 404)
- [ ] Probar Nitter o RSS-Bridge para Twitter/X sin API key
- [ ] Agregar YouTube RSS de canales de referencia (`youtube.com/feeds/videos.xml?channel_id=...`)
- [ ] Filtrar threads meta de Reddit (Self-Promotion, Who's Hiring, Daily Threads)
- [ ] Actualizar paquete DDG: `python3 -m pip install ddgs` (reemplaza `duckduckgo_search`)
