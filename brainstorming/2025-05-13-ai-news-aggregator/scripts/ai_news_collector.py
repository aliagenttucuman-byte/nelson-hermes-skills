#!/usr/bin/env python3
"""
AI News Aggregator para el equipo Nelson.
Lee feeds RSS/Atom de fuentes de IA y genera un resumen diario.
Evita duplicados usando un state file JSON.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from urllib import request
from urllib.error import HTTPError, URLError
from socket import timeout as SocketTimeout

# ── Configuración ────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_FILE = os.path.join(DATA_DIR, "seen_articles.json")

# Feeds a monitorear. Cada uno tiene: nombre, url, max_artículos, keywords opcionales
FEEDS = [
    {"name": "HuggingFace Blog", "url": "https://huggingface.co/blog/feed.xml", "max": 5},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "max": 5},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "max": 5},
    {"name": "LangChain Blog", "url": "https://blog.langchain.dev/rss/", "max": 5},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/", "max": 5},
    {"name": "arXiv cs.AI", "url": "http://export.arxiv.org/rss/cs.AI", "max": 5, "keywords": ["large language", "transformer", "multimodal", "agent", "open source", "benchmark"]},
    {"name": "arXiv cs.LG", "url": "http://export.arxiv.org/rss/cs.LG", "max": 5, "keywords": ["model", "training", "efficient", " distilled", "quantization"]},
    {"name": "arXiv cs.CL", "url": "http://export.arxiv.org/rss/cs.CL", "max": 5, "keywords": ["language model", "translation", "summarization", "retrieval"]},
]

# Keywords globales para resaltar
HIGHLIGHT_KEYWORDS = [
    "open source", "open-source", "released", "launch", "new model",
    "llm", "large language model", "multimodal", "agent", "framework",
    "benchmark", "state-of-the-art", "sota", "training", "inference",
    "quantization", "distillation", "rag", "fine-tuning", "dataset"
]

# ── Utilidades ───────────────────────────────────────────────────────────────


def load_seen() -> set:
    """Carga los IDs de artículos ya vistos."""
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("ids", []))
    except Exception:
        return set()


def save_seen(seen: set):
    """Guarda los IDs de artículos vistos."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"ids": sorted(seen), "last_run": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def fetch_feed(url: str, timeout: int = 20) -> str:
    """Descarga el contenido de un feed."""
    req = request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AI-News-Bot)"})
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_feed(xml_text: str, source_name: str) -> list[dict]:
    """Parsea RSS/Atom y devuelve lista de artículos."""
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  ⚠️ Parse error en {source_name}: {e}", file=sys.stderr)
        return articles

    # Detectar formato
    tag = root.tag.lower()
    is_atom = "feed" in tag

    if is_atom:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        for entry in entries:
            title = entry.findtext("atom:title", default="", namespaces=ns)
            link_elem = entry.find("atom:link", ns)
            link = link_elem.get("href", "") if link_elem is not None else ""
            summary = entry.findtext("atom:summary", default="", namespaces=ns) or entry.findtext("atom:content", default="", namespaces=ns)
            published = entry.findtext("atom:published", default="", namespaces=ns) or entry.findtext("atom:updated", default="", namespaces=ns)
            if title:
                articles.append({"title": title.strip(), "link": link.strip(), "summary": summary.strip()[:400], "date": published.strip()[:10]})
    else:
        # RSS
        channel = root.find("channel")
        if channel is None:
            channel = root
        items = channel.findall("item") if channel is not None else []
        for item in items:
            title = item.findtext("title", default="")
            link = item.findtext("link", default="")
            description = item.findtext("description", default="")
            pub_date = item.findtext("pubDate", default="")
            if title:
                articles.append({"title": title.strip(), "link": link.strip(), "summary": description.strip()[:400], "date": pub_date.strip()[:10]})

    return articles


def make_id(article: dict) -> str:
    """Genera un ID único para un artículo."""
    return re.sub(r"[^a-zA-Z0-9]", "", article["title"].lower())[:60]


def matches_keywords(article: dict, keywords: list[str] | None) -> bool:
    """Verifica si un artículo coincide con keywords (case-insensitive)."""
    if not keywords:
        return True
    text = (article["title"] + " " + article["summary"]).lower()
    return any(kw.lower() in text for kw in keywords)


def highlight(text: str) -> str:
    """Resalta keywords importantes con asteriscos."""
    for kw in HIGHLIGHT_KEYWORDS:
        text = re.sub(rf"\b({re.escape(kw)})\b", r"*\1*", text, flags=re.IGNORECASE)
    return text


# ── Main ─────────────────────────────────────────────────────────────────────


# Destinatarios de WhatsApp para el resumen automático
WHATSAPP_RECIPIENTS = [
    "5493816240691",  # Pablo Terian - Socio
    "5493813022552",  # Faku - Amigo de Tony
]

GATEWAY_URL = "http://localhost:3001"


def send_whatsapp(to: str, message: str):
    """Envía mensaje vía WhatsApp Gateway."""
    try:
        data = json.dumps({"to": to, "message": message}).encode("utf-8")
        req = request.Request(
            f"{GATEWAY_URL}/send",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️ Error enviando a {to}: {e}", file=sys.stderr)
        return None


def main():
    seen = load_seen()
    new_articles = []
    errors = []

    print(f"🔍 Escaneando {len(FEEDS)} fuentes...\n")

    for feed in FEEDS:
        name = feed["name"]
        url = feed["url"]
        max_items = feed.get("max", 5)
        keywords = feed.get("keywords")

        try:
            xml = fetch_feed(url)
        except (HTTPError, URLError, SocketTimeout) as e:
            errors.append(f"  ⚠️ {name}: {e}")
            continue

        articles = parse_feed(xml, name)
        feed_new = []

        for art in articles:
            art_id = f"{name}::{make_id(art)}"
            if art_id in seen:
                continue
            if not matches_keywords(art, keywords):
                continue
            seen.add(art_id)
            art["source"] = name
            feed_new.append(art)
            if len(feed_new) >= max_items:
                break

        new_articles.extend(feed_new)
        status = f"{len(feed_new)} nuevos" if feed_new else "sin novedades"
        print(f"  • {name}: {status}")

    save_seen(seen)

    if errors:
        print("\n".join(errors))

    if not new_articles:
        print("\n📭 No hay novedades en este ciclo.")
        # Aún así notificar que no hay novedades
        for recipient in WHATSAPP_RECIPIENTS:
            send_whatsapp(recipient, "📭 AI News Aggregator\n\nNo hay novedades de IA en este ciclo.")
        return

    # Ordenar por fuente
    new_articles.sort(key=lambda x: x["source"])

    # Generar resumen para consola
    print("\n" + "=" * 50)
    print(f"📰 RESUMEN DE IA — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50 + "\n")

    current_source = None
    for art in new_articles:
        if art["source"] != current_source:
            current_source = art["source"]
            print(f"\n🗞️  {current_source}")
            print("-" * 40)
        title = highlight(art["title"])
        print(f"  • {title}")
        if art["link"]:
            print(f"    🔗 {art['link']}")
        if art["summary"]:
            clean_summary = re.sub(r"<[^>]+>", "", art["summary"]).replace("\n", " ")
            print(f"    📝 {clean_summary[:200]}...")
        print()

    print(f"\n📊 Total: {len(new_articles)} artículos nuevos.")
    print("✅ Listo para su clasificación, señor.")

    # Generar resumen compacto para WhatsApp
    whatsapp_lines = [f"📰 *RESUMEN DE IA* — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"]
    current_source = None
    for art in new_articles:
        if art["source"] != current_source:
            current_source = art["source"]
            whatsapp_lines.append(f"\n🗞️ *{current_source}*")
        title = art["title"]
        whatsapp_lines.append(f"• {title}")
        if art["link"]:
            whatsapp_lines.append(f"  {art['link']}")
    whatsapp_lines.append(f"\n📊 Total: {len(new_articles)} artículos")
    whatsapp_text = "\n".join(whatsapp_lines)

    # Enviar a destinatarios
    print(f"\n📤 Enviando resumen a {len(WHATSAPP_RECIPIENTS)} destinatario(s)...")
    for recipient in WHATSAPP_RECIPIENTS:
        result = send_whatsapp(recipient, whatsapp_text)
        if result and result.get("success"):
            print(f"  ✅ Enviado a {recipient}")
        else:
            print(f"  ⚠️ Falló envío a {recipient}")


if __name__ == "__main__":
    main()
