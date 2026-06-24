#!/usr/bin/env python3
"""
honcho_context_loader.py
Recupera contexto relevante de Honcho al arranque de cada sesión.

Uso:
  python3 honcho_context_loader.py                    # contexto general
  python3 honcho_context_loader.py "bisonte colores"  # semántico por tema
"""
import sys, json, requests
from datetime import date, timedelta

BASE = "http://localhost:8008"
WS   = "alegent-ai"

def get_recent_sessions(days=3):
    today = date.today()
    return [f"session-{(today - timedelta(days=i)).strftime('%Y-%m-%d')}" for i in range(days)]

def get_messages_from_session(session_id, limit=20):
    try:
        r = requests.post(
            f"{BASE}/v3/workspaces/{WS}/sessions/{session_id}/messages/list",
            json={"page": 1, "page_size": limit}, timeout=3
        )
        if r.status_code == 200:
            return r.json().get("items", [])
    except Exception:
        pass
    return []

def dialectic_query(session_id, query, peer_id="jarvis"):
    try:
        r = requests.post(
            f"{BASE}/v3/workspaces/{WS}/sessions/{session_id}/chat",
            json={"query": query, "peer_id": peer_id}, timeout=5
        )
        if r.status_code == 200:
            return r.json().get("content", "")
    except Exception:
        pass
    return ""

def load_context(query=None):
    lines = []
    if query:
        for sid in get_recent_sessions(days=3):
            result = dialectic_query(sid, query)
            if result and result.strip():
                lines.append(f"[Honcho/{sid}] {result.strip()}")
    else:
        for sid in get_recent_sessions(days=2):
            msgs = get_messages_from_session(sid, limit=20)
            for m in msgs[-10:]:
                peer = m.get("peer_id", "?")
                content = m.get("content", "").strip()
                tipo = m.get("metadata", {}).get("tipo", "")
                if content:
                    prefix = f"[{peer}/{tipo}]" if tipo else f"[{peer}]"
                    lines.append(f"{prefix} {content}")

    if not lines:
        return ""
    header = f"=== Contexto Honcho {'— ' + query if query else '(general)'} ===\n"
    return header + "\n".join(lines) + "\n=== Fin contexto Honcho ===\n"

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    ctx = load_context(query)
    print(ctx if ctx else "[Honcho] Sin contexto relevante.")
