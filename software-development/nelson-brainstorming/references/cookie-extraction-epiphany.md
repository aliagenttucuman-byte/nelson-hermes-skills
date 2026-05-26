# Extracción de Cookies desde Epiphany (GNOME Web)

**Fecha:** 2025-05-13
**Contexto:** NotebookLM spike — necesitábamos extraer cookies de sesión Google desde el navegador GNOME Web para autenticar `notebooklm-py`.
**Autor:** JARVIS

---

## Problema

`notebooklm-py` (wrapper no oficial de Google NotebookLM) requiere autenticación vía cookies de navegador. En un servidor Linux con GNOME/Epiphany, no hay forma headless de hacer login.

## Solución: Extraer cookies de `cookies.sqlite`

Epiphany (GNOME Web) guarda las cookies en:

```
~/.local/share/epiphany/cookies.sqlite
```

Es una base SQLite con tabla `moz_cookies` (formato similar a Firefox).

### Script de extracción

```python
import sqlite3
import json
from pathlib import Path

def extract_epiphany_cookies_for_playwright(
    output_path: Path = None,
    domains: list[str] = None
) -> dict:
    """
    Extrae cookies de Epiphany y las convierte al formato
    Playwright storage_state.json.
    
    Args:
        output_path: donde guardar storage_state.json
        domains: lista de dominios a filtrar (ej: ['%google%', '%notebooklm%'])
    """
    cookies_db = Path.home() / ".local/share/epiphany/cookies.sqlite"
    conn = sqlite3.connect(str(cookies_db))
    cursor = conn.cursor()
    
    # Mapear sameSite de Epiphany a Playwright
    sameSite_map = {0: "None", 1: "Lax", 2: "Strict"}
    
    query = "SELECT host, name, value, path, expiry, isSecure, isHttpOnly, sameSite FROM moz_cookies"
    if domains:
        conditions = " OR ".join(["host LIKE ?" for _ in domains])
        query += f" WHERE {conditions}"
        cursor.execute(query, domains)
    else:
        cursor.execute(query)
    
    playwright_cookies = []
    for row in cursor.fetchall():
        host, name, value, path, expiry, isSecure, isHttpOnly, sameSite = row
        
        # Expiry: Epiphany usa microsegundos, Playwright usa segundos
        if expiry and expiry > 9999999999:
            expires = expiry / 1000000
        else:
            expires = expiry or -1
        
        # Domain: Playwright espera punto inicial para dominios
        domain = host if host.startswith(".") else "." + host
        
        cookie = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": path or "/",
            "expires": expires,
            "httpOnly": bool(isHttpOnly),
            "secure": bool(isSecure),
            "sameSite": sameSite_map.get(sameSite, "Lax")
        }
        playwright_cookies.append(cookie)
    
    conn.close()
    
    storage_state = {
        "cookies": playwright_cookies,
        "origins": []
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(storage_state, f, indent=2)
    
    return storage_state

# Uso
extract_epiphany_cookies_for_playwright(
    output_path=Path.home() / ".notebooklm/profiles/default/storage_state.json",
    domains=["%google%", "%notebooklm%"]
)
```

## Verificación

```bash
# Verificar que el archivo existe
ls ~/.local/share/epiphany/cookies.sqlite

# Verificar cookies clave
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/server/.local/share/epiphany/cookies.sqlite')
c = conn.cursor()
c.execute(\"SELECT name, host FROM moz_cookies WHERE name LIKE '%SID%'\")
for r in c.fetchall():
    print(r)
conn.close()
"
```

## Limitaciones conocidas

| Problema | Causa | Workaround |
|----------|-------|------------|
| Auth expira rápido | Google rota tokens | No hay workaround estable para producción |
| Solo funciona si usuario ya logueado | Requiere sesión activa en Epiphany | Pedir al usuario que abra el sitio y haga login primero |
| No funciona con Chromium/Chrome | Rutas diferentes | Para Chromium usar `rookiepy` o `playwright` directo |

## Otros navegadores

| Navegador | Ruta cookies | Formato |
|-----------|-------------|---------|
| Epiphany | `~/.local/share/epiphany/cookies.sqlite` | SQLite `moz_cookies` |
| Firefox | `~/.mozilla/firefox/*.default/cookies.sqlite` | SQLite `moz_cookies` |
| Chromium | `~/.config/chromium/Default/Cookies` | SQLite (encrypted en Linux) |
| Chrome | `~/.config/google-chrome/Default/Cookies` | SQLite (encrypted en Linux) |

## Referencias

- Repo que lo usa: `notebooklm-py` — https://github.com/teng-lin/notebooklm-py
- Spike donde se probó: `~/brainstorming/2025-05-13-idi-consultora/spike-notebooklm/`
