#!/usr/bin/env python3
"""
AI News Aggregator v2 — Nelson I+D+I
Pasivo + Activo + Personas de referencia
Fuentes: RSS, DDG News, Reddit, Google News, Dev.to, Blogs referentes
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib import request
from urllib.error import HTTPError, URLError
from socket import timeout as SocketTimeout
from html import unescape

# ── Configuración ────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
STATE_FILE = os.path.join(DATA_DIR, "seen_articles_v2.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "daily_digest.md")

# Temas de búsqueda activa
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

# Subreddits a monitorear
SUBREDDITS = [
    "MachineLearning",
    "Python",
    "reactjs",
    "computervision",
    "artificial",
    "LocalLLaMA",
]

# Dev.to tags
DEVTO_TAGS = ["ai", "python", "react", "machinelearning", "opensource", "news"]

# Personas de referencia — sus blogs/URLs
REFERENTS = [
    {"name": "MiduDev", "url": "https://midu.dev/rss.xml", "type": "rss"},
    {"name": "Brais Moure", "url": "https://moure.dev/rss.xml", "type": "rss"},
    {"name": "Fazt", "url": "https://faztweb.com/rss.xml", "type": "rss"},
]

# YouTube channels RSS (channel_id)
YOUTUBE_CHANNELS = [
    {"name": "Two Minute Papers", "channel_id": "UCbfYPyITQ-7l4upoX8nvctg"},
    {"name": "Yannic Kilcher", "channel_id": "UCZHmQk67mSJgfCCTn7xBfew"},
    {"name": "Andrej Karpathy", "channel_id": "UCMLta_WpLYOMEMiOSsKEBIA"},
    {"name": "Sentdex", "channel_id": "UCfzlCWGWYyIQ0aLC5w48gBQ"},
    {"name": "MiduDev YT", "channel_id": "UC8LeXCZOlv71o7CbWznMwSg"},
]

# GitHub Trending — topics/lenguajes a monitorear
GITHUB_TRENDING_LANGS = ["python", "javascript", ""]  # "" = all languages

# RSS pasivo original
PASSIVE_FEEDS = [
    # ── Labs principales ────────────────────────────────────────────────────
    {"name": "HuggingFace Blog", "url": "https://huggingface.co/blog/feed.xml", "max": 5},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "max": 5},
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/rss/research-updates.rss", "max": 5},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "max": 5},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml", "max": 5},
    {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/rss/", "max": 5},
    {"name": "Mistral AI Blog", "url": "https://mistral.ai/news/rss.xml", "max": 5},
    {"name": "Cohere Blog", "url": "https://cohere.com/blog/rss", "max": 5},
    {"name": "Stability AI Blog", "url": "https://stability.ai/blog/rss.xml", "max": 3},
    {"name": "xAI Blog", "url": "https://x.ai/blog/rss.xml", "max": 3},
    # ── Herramientas & frameworks ───────────────────────────────────────────
    {"name": "LangChain Blog", "url": "https://blog.langchain.dev/rss/", "max": 5},
    {"name": "LlamaIndex Blog", "url": "https://medium.com/feed/llamaindex", "max": 4},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/", "max": 5},
    # ── arXiv ──────────────────────────────────────────────────────────────
    {"name": "arXiv cs.AI", "url": "http://export.arxiv.org/rss/cs.AI", "max": 5, "keywords": ["large language", "transformer", "multimodal", "agent", "open source", "benchmark"]},
    {"name": "arXiv cs.LG", "url": "http://export.arxiv.org/rss/cs.LG", "max": 5, "keywords": ["model", "training", "efficient", "distilled", "quantization"]},
    {"name": "arXiv cs.CL", "url": "http://export.arxiv.org/rss/cs.CL", "max": 5, "keywords": ["language model", "translation", "summarization", "retrieval"]},
    {"name": "arXiv cs.CV", "url": "http://export.arxiv.org/rss/cs.CV", "max": 5, "keywords": ["vision", "detection", "segmentation", "image", "video"]},
]

# Keywords globales para scoring
RELEVANCE_KEYWORDS = [
    "open source", "open-source", "released", "launch", "new model", "new framework",
    "llm", "large language model", "multimodal", "agent", "framework",
    "benchmark", "state-of-the-art", "sota", "training", "inference",
    "quantization", "distillation", "rag", "fine-tuning", "dataset",
    "computer vision", "image analytics", "edge ai", "on-device",
    "python", "react", "fastapi", "docker", "kubernetes",
]

# ── Utilidades ───────────────────────────────────────────────────────────────

def load_seen() -> set:
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("ids", []))
    except Exception:
        return set()

def save_seen(seen: set):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"ids": sorted(seen), "last_run": datetime.now(timezone.utc).isoformat()}, f, indent=2)

def article_id(title: str, link: str) -> str:
    """Genera un ID único para evitar duplicados."""
    clean = re.sub(r"\W+", "", (title + link).lower())[:80]
    return clean

def fetch(url: str, timeout: int = 20, headers: dict = None) -> str:
    """HTTP GET robusto."""
    default_headers = {"User-Agent": "Mozilla/5.0 (AI-News-Bot/2.0)"}
    if headers:
        default_headers.update(headers)
    req = request.Request(url, headers=default_headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, SocketTimeout) as e:
        print(f"  ⚠️ Error fetching {url[:60]}...: {e}", file=sys.stderr)
        return ""

def score_relevance(title: str, summary: str = "") -> int:
    """Puntúa relevancia basado en keywords."""
    text = (title + " " + summary).lower()
    score = 0
    for kw in RELEVANCE_KEYWORDS:
        if kw.lower() in text:
            score += 1
    return score

def clean_text(text: str) -> str:
    """Limpia HTML básico."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]

# ── Fuentes de datos ─────────────────────────────────────────────────────────

def fetch_rss_feeds(feeds: list) -> list[dict]:
    """Lee feeds RSS/Atom."""
    articles = []
    for feed in feeds:
        print(f"📡 {feed['name']}...")
        xml = fetch(feed["url"], timeout=15)
        if not xml:
            continue
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml)
        except Exception as e:
            print(f"  ⚠️ Parse error: {e}", file=sys.stderr)
            continue

        tag = root.tag.lower()
        is_atom = "feed" in tag
        entries = []

        if is_atom:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)
            for entry in entries[:feed.get("max", 5)]:
                title = entry.findtext("atom:title", default="", namespaces=ns)
                link_elem = entry.find("atom:link", ns)
                link = link_elem.get("href", "") if link_elem is not None else ""
                summary = entry.findtext("atom:summary", default="", namespaces=ns) or entry.findtext("atom:content", default="", namespaces=ns)
                date = entry.findtext("atom:published", default="", namespaces=ns) or entry.findtext("atom:updated", default="", namespaces=ns)
                if title:
                    articles.append({
                        "title": clean_text(title),
                        "link": link.strip(),
                        "summary": clean_text(summary),
                        "date": date.strip()[:10] if date else "",
                        "source": feed["name"],
                        "section": "RSS Pasivo",
                        "score": score_relevance(title, summary),
                    })
        else:
            channel = root.find("channel") or root
            items = channel.findall("item") if channel is not None else []
            for item in items[:feed.get("max", 5)]:
                title = item.findtext("title", default="")
                link = item.findtext("link", default="")
                desc = item.findtext("description", default="")
                date = item.findtext("pubDate", default="")
                if title:
                    articles.append({
                        "title": clean_text(title),
                        "link": link.strip(),
                        "summary": clean_text(desc),
                        "date": date.strip()[:10] if date else "",
                        "source": feed["name"],
                        "section": "RSS Pasivo",
                        "score": score_relevance(title, desc),
                    })
    return articles

def fetch_ddg_news(topics: list, max_per_topic: int = 5) -> list[dict]:
    """Busca noticias vía DuckDuckGo News."""
    articles = []
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("⚠️ duckduckgo_search no instalado. Saltando DDG News.", file=sys.stderr)
        return articles

    with DDGS() as ddgs:
        for topic in topics:
            print(f"🔍 DDG News: '{topic}'...")
            try:
                results = ddgs.news(keywords=topic, region="wt-wt", safesearch="Off", timelimit="d", max_results=max_per_topic)
                for r in results:
                    title = r.get("title", "")
                    link = r.get("url", "")
                    summary = r.get("body", "")
                    date = r.get("date", "")
                    if title and link:
                        articles.append({
                            "title": clean_text(title),
                            "link": link.strip(),
                            "summary": clean_text(summary),
                            "date": date[:10] if date else "",
                            "source": f"DDG News / {topic}",
                            "section": "Búsqueda Activa",
                            "score": score_relevance(title, summary) + 2,
                        })
            except Exception as e:
                print(f"  ⚠️ DDG error en '{topic}': {e}", file=sys.stderr)
            time.sleep(0.5)
    return articles

def fetch_reddit(subreddits: list, limit: int = 5) -> list[dict]:
    """Lee posts populares de Reddit vía JSON público."""
    articles = []
    for sub in subreddits:
        print(f"👽 Reddit r/{sub}...")
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
        data = fetch(url, timeout=15, headers={"User-Agent": "AI-News-Bot/2.0"})
        if not data:
            continue
        try:
            import json as _json
            payload = _json.loads(data)
            posts = payload.get("data", {}).get("children", [])
            for post in posts:
                p = post.get("data", {})
                title = p.get("title", "")
                link = p.get("url", "")
                permalink = f"https://reddit.com{p.get('permalink', '')}"
                score = p.get("score", 0)
                if title and score > 5:
                    articles.append({
                        "title": clean_text(title),
                        "link": permalink if permalink.startswith("http") else link,
                        "summary": f"Score: {score} | r/{sub}",
                        "date": "",
                        "source": f"Reddit r/{sub}",
                        "section": "Comunidad",
                        "score": score_relevance(title) + (1 if score > 50 else 0),
                    })
        except Exception as e:
            print(f"  ⚠️ Reddit error r/{sub}: {e}", file=sys.stderr)
    return articles

def fetch_devto(tags: list, limit: int = 5) -> list[dict]:
    """Lee artículos de Dev.to por tag."""
    articles = []
    for tag in tags:
        print(f"💻 Dev.to #{tag}...")
        url = f"https://dev.to/api/articles?tag={tag}&per_page={limit}"
        data = fetch(url, timeout=15)
        if not data:
            continue
        try:
            import json as _json
            payload = _json.loads(data)
            for article in payload:
                title = article.get("title", "")
                link = article.get("url", "")
                desc = article.get("description", "") or article.get("body_markdown", "")[:200]
                date = article.get("published_at", "")
                if title:
                    articles.append({
                        "title": clean_text(title),
                        "link": link.strip(),
                        "summary": clean_text(desc),
                        "date": date[:10] if date else "",
                        "source": f"Dev.to #{tag}",
                        "section": "Blogs Técnicos",
                        "score": score_relevance(title, desc) + 1,
                    })
        except Exception as e:
            print(f"  ⚠️ Dev.to error #{tag}: {e}", file=sys.stderr)
    return articles

def fetch_google_news_rss(topics: list, max_per_topic: int = 5) -> list[dict]:
    """Lee Google News RSS por tema."""
    articles = []
    for topic in topics:
        print(f"📰 Google News: '{topic}'...")
        query = topic.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        xml = fetch(url, timeout=15)
        if not xml:
            continue
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml)
            channel = root.find("channel")
            if channel is None:
                continue
            items = channel.findall("item")[:max_per_topic]
            for item in items:
                title = item.findtext("title", default="")
                link = item.findtext("link", default="")
                desc = item.findtext("description", default="")
                date = item.findtext("pubDate", default="")
                if title:
                    articles.append({
                        "title": clean_text(title),
                        "link": link.strip(),
                        "summary": clean_text(desc),
                        "date": date.strip()[:10] if date else "",
                        "source": f"Google News / {topic}",
                        "section": "Búsqueda Activa",
                        "score": score_relevance(title, desc),
                    })
        except Exception as e:
            print(f"  ⚠️ Google News error '{topic}': {e}", file=sys.stderr)
    return articles

def fetch_youtube_channels(channels: list) -> list[dict]:
    """Lee últimos videos de canales YouTube vía RSS."""
    articles = []
    for ch in channels:
        print(f"🎬 YouTube: {ch['name']}...")
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['channel_id']}"
        xml = fetch(url, timeout=15)
        if not xml:
            continue
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "yt": "http://www.youtube.com/xml/schemas/2015",
                "media": "http://search.yahoo.com/mrss/",
            }
            entries = root.findall("atom:entry", ns)
            for entry in entries[:3]:
                title = entry.findtext("atom:title", default="", namespaces=ns)
                video_id = entry.findtext("yt:videoId", default="", namespaces=ns)
                link = f"https://youtube.com/watch?v={video_id}" if video_id else ""
                published = entry.findtext("atom:published", default="", namespaces=ns)
                group = entry.find("media:group", ns)
                desc = ""
                if group is not None:
                    desc = group.findtext("media:description", default="", namespaces=ns) or ""
                if title and link:
                    articles.append({
                        "title": clean_text(title),
                        "link": link,
                        "summary": clean_text(desc[:200]),
                        "date": published[:10] if published else "",
                        "source": ch["name"],
                        "section": "Videos",
                        "score": score_relevance(title, desc) + 2,
                    })
        except Exception as e:
            print(f"  ⚠️ YouTube error {ch['name']}: {e}", file=sys.stderr)
    return articles


def fetch_github_trending(langs: list) -> list[dict]:
    """Scrapea GitHub Trending para obtener repos populares del día."""
    articles = []
    for lang in langs:
        lang_label = lang if lang else "all"
        print(f"🐙 GitHub Trending: {lang_label}...")
        url = "https://github.com/trending"
        if lang:
            url += f"/{lang}"
        url += "?since=daily"
        html = fetch(url, timeout=20)
        if not html:
            continue
        try:
            # Extraer repos: patrón <h2 class="h3 lh-condensed"> o <article>
            # Usamos regex sobre el HTML raw
            # Repos: /owner/name
            repo_pattern = re.compile(
                r'href="/([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-\.]+)"[^>]*class="[^"]*Link[^"]*"'
            )
            desc_pattern = re.compile(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
            star_pattern = re.compile(r'aria-label="(\d[\d,]*) users starred this repository"')

            repos = list(dict.fromkeys(repo_pattern.findall(html)))[:10]
            descs = [clean_text(d) for d in desc_pattern.findall(html)]
            stars = star_pattern.findall(html)

            for i, repo in enumerate(repos[:8]):
                link = f"https://github.com/{repo}"
                desc = descs[i] if i < len(descs) else ""
                star_count = stars[i] if i < len(stars) else ""
                star_suffix = f" ⭐ {star_count} stars hoy" if star_count else ""
                articles.append({
                    "title": f"{repo}{star_suffix}",
                    "link": link,
                    "summary": desc,
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "source": f"GitHub Trending ({lang_label})",
                    "section": "Repositorios",
                    "score": score_relevance(repo, desc) + 3,
                })
        except Exception as e:
            print(f"  ⚠️ GitHub Trending error {lang_label}: {e}", file=sys.stderr)
    return articles


def fetch_referents(referents: list) -> list[dict]:
    """Lee blogs de personas de referencia."""
    articles = []
    for ref in referents:
        print(f"⭐ {ref['name']}...")
        if ref["type"] == "rss":
            xml = fetch(ref["url"], timeout=15)
            if not xml:
                continue
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml)
                channel = root.find("channel") or root
                items = channel.findall("item")[:3] if channel is not None else []
                for item in items:
                    title = item.findtext("title", default="")
                    link = item.findtext("link", default="")
                    desc = item.findtext("description", default="")
                    date = item.findtext("pubDate", default="")
                    if title:
                        articles.append({
                            "title": clean_text(title),
                            "link": link.strip(),
                            "summary": clean_text(desc),
                            "date": date.strip()[:10] if date else "",
                            "source": ref["name"],
                            "section": "Referentes",
                            "score": score_relevance(title, desc) + 3,
                        })
            except Exception as e:
                print(f"  ⚠️ Error {ref['name']}: {e}", file=sys.stderr)
    return articles

# ── Ensamblaje del digest ────────────────────────────────────────────────────

def build_digest(all_articles: list[dict], seen: set) -> str:
    """Genera el Markdown del digest filtrando duplicados."""
    new_articles = []
    for art in all_articles:
        aid = article_id(art["title"], art["link"])
        if aid not in seen:
            new_articles.append((aid, art))
            seen.add(aid)

    if not new_articles:
        return "# 📰 Daily Digest I+D+I\n\n*No hay novedades nuevas en esta corrida.*\n\n_Generado: {}_".format(
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        )

    # Agrupar por sección
    sections = {}
    for aid, art in new_articles:
        sec = art.get("section", "General")
        sections.setdefault(sec, []).append(art)

    # Ordenar por score dentro de cada sección
    for sec in sections:
        sections[sec].sort(key=lambda x: x.get("score", 0), reverse=True)

    lines = [
        "# 📰 Daily Digest I+D+I",
        "",
        f"📅 {datetime.now(timezone.utc).strftime('%A %d %B %Y')} — Fuente: Nelson Server",
        "",
        f"📊 {len(new_articles)} artículos nuevos encontrados",
        "",
        "---",
        "",
    ]

    section_order = ["Búsqueda Activa", "RSS Pasivo", "Videos", "Repositorios", "Comunidad", "Blogs Técnicos", "Referentes", "General"]
    for sec in section_order:
        if sec not in sections:
            continue
        lines.append(f"## {sec}")
        lines.append("")
        for art in sections[sec][:15]:
            score_emoji = "🔥" if art.get("score", 0) >= 5 else "⭐" if art.get("score", 0) >= 3 else "📄"
            lines.append(f"{score_emoji} **[{art['title']}]({art['link']})**")
            if art.get("summary"):
                lines.append(f"> {art['summary'][:200]}")
            lines.append(f"> `Fuente: {art['source']}` | `{art.get('date', 'sin fecha')}`")
            lines.append("")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Generado automáticamente por JARVIS — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")
    lines.append("")
    lines.append("💡 *Para agregar más fuentes, editar `ai_news_collector_v2.py` o pedirle a JARVIS.*")

    return "\n".join(lines)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🤖 AI News Aggregator v2 — Nelson I+D+I")
    print("=" * 60)

    seen = load_seen()
    all_articles = []

    # 1. RSS Pasivo
    print("\n📻 FASE 1: RSS Pasivo")
    all_articles.extend(fetch_rss_feeds(PASSIVE_FEEDS))

    # 2. Búsqueda activa DDG
    print("\n🔎 FASE 2: DuckDuckGo News")
    all_articles.extend(fetch_ddg_news(SEARCH_TOPICS[:5]))

    # 3. Google News RSS
    print("\n📰 FASE 3: Google News")
    all_articles.extend(fetch_google_news_rss(SEARCH_TOPICS[:3]))

    # 4. Reddit
    print("\n👽 FASE 4: Reddit")
    all_articles.extend(fetch_reddit(SUBREDDITS[:4]))

    # 5. Dev.to
    print("\n💻 FASE 5: Dev.to")
    all_articles.extend(fetch_devto(DEVTO_TAGS[:4]))

    # 6. Referentes
    print("\n⭐ FASE 6: Referentes")
    all_articles.extend(fetch_referents(REFERENTS))

    # 7. YouTube videos
    print("\n🎬 FASE 7: YouTube")
    all_articles.extend(fetch_youtube_channels(YOUTUBE_CHANNELS))

    # 8. GitHub Trending
    print("\n🐙 FASE 8: GitHub Trending")
    all_articles.extend(fetch_github_trending(GITHUB_TRENDING_LANGS))

    print(f"\n📦 Total artículos recolectados: {len(all_articles)}")

    digest = build_digest(all_articles, seen)
    save_seen(seen)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"\n✅ Digest guardado en: {OUTPUT_FILE}")
    print(f"📈 Artículos nuevos: {digest.count('**[')}")

if __name__ == "__main__":
    main()
