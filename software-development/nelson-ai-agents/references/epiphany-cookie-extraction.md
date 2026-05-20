# Extracción de Cookies de Epiphany (GNOME Web) para Playwright

**Contexto:** El usuario navega con Epiphany (GNOME Web, también llamado "Web") en su servidor Linux con Gnome. Necesitamos extraer su sesión autenticada para usarla con herramientas de automatización como Playwright, `notebooklm-py`, u otros scrapers/agentes.

**Fecha:** 2025-05-13
**Skill relacionada:** nelson-ai-agents

---

## Ubicación de la Base de Cookies

```
~/.local/share/epiphany/cookies.sqlite
```

## Estructura de la Tabla

Epiphany usa el formato de Firefox (`moz_cookies`), no el de Chromium:

```sql
Tabla: moz_cookies
Columnas: id, name, value, host, path, expiry, lastAccessed, isSecure, isHttpOnly, sameSite
```

> **Pitfall:** La tabla se llama `moz_cookies`, no `cookies`. Si haces `SELECT * FROM cookies` falla con "no such table".

## Mapeo a Playwright storage_state.json

Epiphany guarda:
- `host`: dominio (ej: `.google.com`)
- `expiry`: timestamp en **microsegundos** desde epoch (no segundos)
- `sameSite`: entero (0=None, 1=Lax, 2=Strict)

Playwright espera:
- `domain`: igual que `host`
- `expires`: timestamp en **segundos** desde epoch (o -1 para sesión)
- `sameSite`: string ("None", "Lax", "Strict")

## Script Python de Conversión

```python
import sqlite3
import json
from pathlib import Path

def export_epiphany_cookies_to_playwright(output_path: str):
    """Exporta cookies de Epiphany (GNOME Web) a formato Playwright."""
    cookies_db = Path.home() / ".local/share/epiphany/cookies.sqlite"
    conn = sqlite3.connect(str(cookies_db))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT host, name, value, path, expiry, isSecure, isHttpOnly, sameSite
        FROM moz_cookies
        WHERE host LIKE '%google%' OR host LIKE '%notebooklm%'
    """)
    rows = cursor.fetchall()
    conn.close()
    
    playwright_cookies = []
    sameSite_map = {0: "None", 1: "Lax", 2: "Strict"}
    
    for host, name, value, path, expiry, isSecure, isHttpOnly, sameSite in rows:
        # Epiphany guarda expiry en microsegundos
        if expiry and expiry > 9999999999:
            expires = expiry / 1000000
        else:
            expires = expiry or -1
        
        cookie = {
            "name": name,
            "value": value,
            "domain": host if host.startswith('.') else '.' + host,
            "path": path or "/",
            "expires": expires,
            "httpOnly": bool(isHttpOnly),
            "secure": bool(isSecure),
            "sameSite": sameSite_map.get(sameSite, "Lax")
        }
        playwright_cookies.append(cookie)
    
    storage_state = {
        "cookies": playwright_cookies,
        "origins": []
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(storage_state, f, indent=2)
    
    return len(playwright_cookies)

# Uso
# export_epiphany_cookies_to_playwright("~/.notebooklm/profiles/default/storage_state.json")
```

## Verificación

```bash
notebooklm auth check --test --json
```

Debe retornar:
```json
{
  "status": "ok",
  "checks": {
    "storage_exists": true,
    "json_valid": true,
    "cookies_present": true,
    "sid_cookie": true,
    "token_fetch": true
  }
}
```

## Limitaciones Conocidas

1. **Las cookies expiran.** Google puede invalidar la sesión después de varias peticiones. No es una solución durable para producción.
2. **Solo funciona si el usuario ya está logueado** en Epiphany. No reemplaza al login manual.
3. **Servicios que detectan automatización** (como Google con Playwright/Chromium) pueden bloquear el login. En esos casos, la extracción de cookies es la única alternativa viable en servidor sin navegador visible.

## Aplicaciones

- `notebooklm-py` (autenticación Google sin login manual)
- Playwright con sesión persistente
- Scrapers que necesitan sesión autenticada
- Agentes de IA que interactúan con servicios web de Google

---

*Referencia generada durante spike de NotebookLM — Equipo Nelson*
