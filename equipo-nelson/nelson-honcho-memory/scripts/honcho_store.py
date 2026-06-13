#!/usr/bin/env python3
"""
honcho_store.py — Guarda intercambios importantes de JARVIS en Honcho.

Uso:
  python3 honcho_store.py --session "2026-06-12-bisonte" \
    --user "levantame bisonte" \
    --jarvis "backend :9000 ok. URL: http://100.110.8.13:9090"

  python3 honcho_store.py --session "auto" \
    --user "..." --jarvis "..." \
    --tags "decision,arquitectura"
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://localhost:8008"
WORKSPACE = "jarvis-nelson"


def api(method: str, path: str, data: dict = None) -> dict:
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}


def get_or_create_session(session_id: str) -> str:
    if session_id == "auto":
        session_id = datetime.now().strftime("%Y-%m-%d-%H%M")
    res = api("POST", f"/v3/workspaces/{WORKSPACE}/sessions",
              {"id": session_id, "metadata": {"created_by": "jarvis"}})
    return res.get("id", session_id)


def store(session_id: str, user_msg: str, jarvis_msg: str, tags: list[str] = None):
    sid = get_or_create_session(session_id)
    messages = []
    if user_msg:
        messages.append({"peer_id": "nelson", "content": user_msg, "metadata": {"tags": tags or []}})
    if jarvis_msg:
        messages.append({"peer_id": "jarvis", "content": jarvis_msg, "metadata": {"tags": tags or []}})
    if not messages:
        print("ERROR: no hay mensajes para guardar")
        sys.exit(1)
    res = api("POST", f"/v3/workspaces/{WORKSPACE}/sessions/{sid}/messages", {"messages": messages})
    if "error" in res:
        print(f"ERROR al guardar: {res['error']}")
        sys.exit(1)
    print(f"OK — sesión={sid}, mensajes={len(messages)}")
    return sid


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="auto")
    parser.add_argument("--user", default="")
    parser.add_argument("--jarvis", default="")
    parser.add_argument("--tags", default="")
    args = parser.parse_args()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    store(args.session, args.user, args.jarvis, tags)
