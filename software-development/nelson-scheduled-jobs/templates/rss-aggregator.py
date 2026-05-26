#!/usr/bin/env python3
"""
Template: RSS/Atom feed aggregator con filtro de keywords.
Uso: copiar, ajustar FEEDS y HIGHLIGHT_KEYWORDS, probar, schedular.
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

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_FILE = os.path.join(DATA_DIR, "seen_articles.json")

FEEDS = [
    {"name": "Example Blog", "url": "https://example.com/feed.xml", "max": 5},
    # {"name": "arXiv cs.AI", "url": "http://export.arxiv.org/rss/cs.AI", "max": 5, "keywords": ["llm", "agent"]},
]

HIGHLIGHT_KEYWORDS = [
    "open source", "new model", "llm", "framework", "benchmark", "training", "inference"
]


def load_seen() -> set:
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f).get("ids", []))
    except Exception:
        return set()


def save_seen(seen: set):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"ids": sorted(seen), "last_run": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def fetch_feed(url: str, timeout: int = 20) -> str:
    req = request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AI-News-Bot)"})
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_feed(xml_text: str, source_name: str) -> list[dict]:
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  Parse error en {source_name}: {e}", file=sys.stderr)
        return articles

    tag = root.tag.lower()
    is_atom = "feed" in tag
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    if is_atom:
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", default="", namespaces=ns)
            link_elem = entry.find("atom:link", ns)
            link = link_elem.get("href", "") if link_elem is not None else ""
            summary = entry.findtext("atom:summary", default="", namespaces=ns) or entry.findtext("atom:content", default="", namespaces=ns)
            published = entry.findtext("atom:published", default="", namespaces=ns) or entry.findtext("atom:updated", default="", namespaces=ns)
            if title:
                articles.append({"title": title.strip(), "link": link.strip(), "summary": summary.strip()[:400], "date": published.strip()[:10]})
    else:
        channel = root.find("channel") or root
        for item in channel.findall("item"):
            title = item.findtext("title", default="")
            link = item.findtext("link", default="")
            description = item.findtext("description", default="")
            pub_date = item.findtext("pubDate", default="")
            if title:
                articles.append({"title": title.strip(), "link": link.strip(), "summary": description.strip()[:400], "date": pub_date.strip()[:10]})

    return articles


def make_id(article: dict) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", article["title"].lower())[:60]


def matches_keywords(article: dict, keywords: list[str] | None) -> bool:
    if not keywords:
        return True
    text = (article["title"] + " " + article["summary"]).lower()
    return any(kw.lower() in text for kw in keywords)


def highlight(text: str) -> str:
    for kw in HIGHLIGHT_KEYWORDS:
        text = re.sub(rf"\b({re.escape(kw)})\b", r"*\1*", text, flags=re.IGNORECASE)
    return text


def main():
    seen = load_seen()
    new_articles = []
    errors = []

    for feed in FEEDS:
        name = feed["name"]
        url = feed["url"]
        max_items = feed.get("max", 5)
        keywords = feed.get("keywords")

        try:
            xml = fetch_feed(url)
        except (HTTPError, URLError, SocketTimeout) as e:
            errors.append(f"  {name}: {e}")
            continue

        articles = parse_feed(xml, name)
        feed_new = []
        for art in articles:
            art_id = f"{name}::{make_id(art)}"
            if art_id in seen or not matches_keywords(art, keywords):
                continue
            seen.add(art_id)
            art["source"] = name
            feed_new.append(art)
            if len(feed_new) >= max_items:
                break

        new_articles.extend(feed_new)
        status = f"{len(feed_new)} nuevos" if feed_new else "sin novedades"
        print(f"  {name}: {status}")

    save_seen(seen)

    if errors:
        print("\n".join(errors))

    if not new_articles:
        print("No hay novedades en este ciclo.")
        return

    new_articles.sort(key=lambda x: x["source"])
    print(f"\n{'='*50}")
    print(f"RESUMEN — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*50}\n")

    current_source = None
    for art in new_articles:
        if art["source"] != current_source:
            current_source = art["source"]
            print(f"\n{current_source}\n{'-'*40}")
        print(f"  • {highlight(art['title'])}")
        if art["link"]:
            print(f"    {art['link']}")
        if art["summary"]:
            clean = re.sub(r"<[^>]+>", "", art["summary"]).replace("\n", " ")
            print(f"    {clean[:200]}...")
        print()

    print(f"\nTotal: {len(new_articles)} artículos nuevos.")


if __name__ == "__main__":
    main()
