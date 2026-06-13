#!/usr/bin/env python3
"""
honcho_context.py — Recupera contexto semántico de Honcho para JARVIS.

Uso:
  python3 honcho_context.py --query "expreso bisonte"
  python3 honcho_context.py --perfil          # muestra el perfil que Honcho infirió de Nelson
  python3 honcho_context.py --recent 5        # últimas 5 sesiones
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
    except Exception as e:
        return {"error": str(e)}


def buscar(query: str, top_k: int = 5):
    """Búsqueda semántica en el workspace."""
    res = api("POST", f"/v3/workspaces/{WORKSPACE}/search",
              {"query": query, "top_k": top_k})
    if "error" in res:
        print(f"ERROR: {res['error']}")
        return

    items = res.get("results", res.get("items", []))
    if not items:
        print("Sin resultados para:", query)
        return

    print(f"\n=== Contexto semántico para: '{query}' ===\n")
    for i, item in enumerate(items, 1):
        content = item.get("content", item.get("message", {}).get("content", ""))
        peer = item.get("peer_id", item.get("message", {}).get("peer_id", "?"))
        score = item.get("score", 0)
        session = item.get("session_id", "")
        print(f"[{i}] ({peer}) score={score:.3f} session={session}")
        print(f"    {content[:200]}")
        print()


def perfil():
    """Muestra el perfil/card que Honcho infirió de Nelson."""
    # Representation (perfil inferido)
    res = api("GET", f"/v3/workspaces/{WORKSPACE}/peers/nelson/representation")
    print("\n=== Perfil inferido de Nelson ===\n")
    if "error" not in res:
        content = res.get("content", res.get("representation", json.dumps(res, indent=2)))
        print(content)
    else:
        print("Sin perfil todavía (se construye con el tiempo):", res.get("error"))

    # Conclusions
    res2 = api("GET", f"/v3/workspaces/{WORKSPACE}/conclusions/list")
    conclusions = res2.get("items", [])
    if conclusions:
        print(f"\n=== Conclusiones del Deriver ({len(conclusions)}) ===\n")
        for c in conclusions[:10]:
            print(f"• {c.get('content', '')}")


def recientes(n: int = 5):
    """Muestra las últimas N sesiones."""
    res = api("GET", f"/v3/workspaces/{WORKSPACE}/sessions/list")
    sessions = res.get("items", [])
    if not sessions:
        print("No hay sesiones guardadas aún.")
        return

    print(f"\n=== Últimas {min(n, len(sessions))} sesiones ===\n")
    for s in sessions[:n]:
        sid = s.get("id", "?")
        created = s.get("created_at", "")[:10]
        print(f"• {sid} ({created})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="", help="Búsqueda semántica")
    parser.add_argument("--perfil", action="store_true", help="Mostrar perfil de Nelson")
    parser.add_argument("--recent", type=int, default=0, help="Ver N sesiones recientes")
    args = parser.parse_args()

    if args.perfil:
        perfil()
    elif args.recent:
        recientes(args.recent)
    elif args.query:
        buscar(args.query)
    else:
        parser.print_help()
