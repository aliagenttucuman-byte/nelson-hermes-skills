#!/usr/bin/env python3
"""
Export cookies from Epiphany (Gnome Web) to NotebookLM storage_state.json.
Run this on the server after logging into notebooklm.google.com via Epiphany.
"""

import sqlite3
import json
from pathlib import Path


def export_epiphany_cookies(output_path: Path | None = None) -> Path:
    """Export Epiphany cookies for Google/NotebookLM domains."""
    
    src = Path.home() / ".local/share/epiphany/cookies.sqlite"
    if not src.exists():
        raise FileNotFoundError(f"Epiphany cookies not found at {src}")
    
    conn = sqlite3.connect(str(src))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT host, name, value, path, expiry, isSecure, isHttpOnly, sameSite
        FROM moz_cookies
        WHERE host LIKE '%google%' OR host LIKE '%notebooklm%'
    """)
    
    cookies = []
    for row in cursor.fetchall():
        host, name, value, path, expiry, isSecure, isHttpOnly, sameSite = row
        
        sameSite_map = {0: "None", 1: "Lax", 2: "Strict"}
        
        # Epiphany stores expiry in microseconds since epoch; Playwright expects seconds
        if expiry and expiry > 9999999999:
            expires = expiry / 1000000
        else:
            expires = expiry or -1
        
        domain = host if host.startswith('.') else '.' + host
        
        cookies.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": path or "/",
            "expires": expires,
            "httpOnly": bool(isHttpOnly),
            "secure": bool(isSecure),
            "sameSite": sameSite_map.get(sameSite, "Lax")
        })
    
    conn.close()
    
    storage_state = {"cookies": cookies, "origins": []}
    
    out = output_path or (Path.home() / ".notebooklm/profiles/default/storage_state.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(storage_state, indent=2))
    
    print(f"Exported {len(cookies)} cookies to {out}")
    
    key_names = ["SID", "__Secure-1PSID", "HSID", "SSID"]
    found = [c["name"] for c in cookies if c["name"] in key_names]
    print(f"Key cookies: {', '.join(found)}")
    
    return out


if __name__ == "__main__":
    export_epiphany_cookies()
