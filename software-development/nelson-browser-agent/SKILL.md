---
name: nelson-browser-agent
description: "Agente de navegador para el equipo Nelson. Controla Playwright via código generado al vuelo (estilo Webwright de Microsoft). Automatiza tareas web: scraping, form-fill, testing E2E, extracción de datos. Usa Firefox headless por defecto (anti-fingerprinting)."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [playwright, browser, automation, web-agent, scraping, e2e, webwright]
    related_skills: [nelson-ai-vision, nelson-frontend-testing, nelson-spec-driven-workflow, nelson-senior-practices]
---

# Nelson Browser Agent

Skill para convertir a JARVIS en un agente de navegador SOTA, basada en la metodología **Webwright** de Microsoft Research. El agente genera código Python+Playwright al vuelo, lo ejecuta, toma screenshots y se auto-verifica con visión.

## Cuándo usar esta skill

- Automatizar tareas web: búsquedas, filtros, form-fill, extracción de datos
- Testing E2E de PoCs y frontends del equipo
- Scraping estructurado con evidencia visual
- Validar que un deploy funciona en browser real
- Cualquier tarea que requiera "hacer click en cosas"

## Prerrequisitos

```bash
# Instalar Firefox (una vez)
python3 -m playwright install firefox

# Verificar
python3 -m playwright install --list
```

Playwright Python ya está instalado en el servidor. Chromium también disponible como fallback.

## Loop de 5 Pasos (Webwright Style)

```
1. PLAN     → Escribir plan.md con Critical Points (CPs)
2. EXPLORE  → Scripts scratch para descubrir selectores
3. AUTHOR   → final_script.py instrumentado
4. EXECUTE  → Correr y guardar screenshots
5. VERIFY   → Leer PNGs con visión y validar cada CP
```

## Workspace Contract

```
outputs/<task_id>/
├── plan.md                          # CPs y parámetros
├── screenshots/                     # Screenshots de exploración (scratch)
└── final_runs/
    └── run_<N>/
        ├── final_script.py          # Script final instrumentado
        ├── final_script_log.txt     # Log de acciones + dato final
        └── screenshots/
            └── final_execution_<step>_<action>.png
```

## Paso 1: Plan

```markdown
# Task
<descripción verbatim de la tarea>

# Critical Points
- [ ] CP1: <constraint / filtro / selección / dato requerido>
- [ ] CP2: ...

# Parameters (solo en modo CLI)
| name | type | default | descripción |
```

Reglas:
- Un CP por requisito verificable independientemente
- CPs numéricos/fecha deben ser exactos
- CPs de ranking deben referenciar el control real del sitio

## Paso 2: Explorar

```python
# Skeleton de exploración
python3 - <<'PY'
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE = Path("outputs/<task_id>")
SCREENSHOTS = WORKSPACE / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

async def main():
    async with async_playwright() as pw:
        # Firefox por defecto — resiste fingerprinting (Akamai, Cloudflare)
        browser = await pw.firefox.launch(headless=True)
        # Fallback: pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        await page.goto("<URL>", wait_until="domcontentloaded")
        await page.screenshot(path=str(SCREENSHOTS / "explore_1_start.png"))

        print("URL:", page.url)
        print("TITLE:", await page.title())

        # ARIA snapshot para descubrir selectores
        snapshot = await page.locator("body").aria_snapshot()
        print("ARIA:", snapshot[:3000])

        await browser.close()

asyncio.run(main())
PY
```

**Reglas críticas:**
- Siempre `viewport={"width": 1280, "height": 1800}`
- Nunca `page.screenshot(full_page=True)`
- Usar ARIA snapshot para descubrir elementos — más robusto que XPath/CSS
- Firefox primero; si hay errores HTTP2/TLS, usar Chromium

## Paso 3: Targeting de elementos

```python
# Preferir role + name (más estable que CSS selectors)
await page.get_by_role("button", name="Filters").click()
await asyncio.sleep(1)

# Inspeccionar panel tras interacción
panel = page.get_by_role("button", name="Filters").first.locator("..")
print(await panel.aria_snapshot())

# Form fill
await page.get_by_role("textbox", name="Search").fill("término")
await page.get_by_role("checkbox", name="Opción").check()

# Siempre drives interactivos > deep-link URLs (más robusto para CLI)
```

## Paso 4: final_script.py instrumentado

```python
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "."))
RUN_DIR = WORKSPACE / "final_runs" / "run_1"
SCREENSHOTS = RUN_DIR / "screenshots"
LOG_FILE = RUN_DIR / "final_script_log.txt"

SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG_FILE.write_text("")  # reset log

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
    print(msg)

async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        # CP1
        log("step 1 action: navegar a <URL>")
        await page.goto("<URL>", wait_until="domcontentloaded")
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_start.png"))

        # CP2 - interacción
        log("step 2 action: aplicar filtro <X>")
        await page.get_by_role("button", name="Filtro").click()
        await asyncio.sleep(1)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_filter.png"))

        # Dato final
        result = await page.locator(".resultado").inner_text()
        log(f"RESULTADO: {result}")

        await browser.close()

asyncio.run(main())
```

## Paso 5: Auto-verificación con visión

Después de ejecutar, leer cada screenshot con `vision_analyze` y verificar contra los CPs del plan.md:

```
Para cada CP en plan.md:
  1. Identificar screenshot correspondiente
  2. vision_analyze(screenshot, "¿Se cumple CP: <descripción>?")
  3. Si OK → marcar [ ] → [x]
  4. Si FAIL → diagnosticar, fix script, re-ejecutar en run_<N+1>
```

## Modo CLI (Reutilizable)

Cuando el usuario dice "hacelo reutilizable" o "parámetros":

```python
import argparse
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

def buscar_en_sitio(query: str, filtro: str = "todos", max_resultados: int = 10) -> list:
    """Busca en el sitio con los parámetros dados.
    
    Args:
        query: Término de búsqueda.
        filtro: Categoría a filtrar. Default: "todos".
        max_resultados: Máximo de resultados. Default: 10.
    
    Returns:
        Lista de resultados encontrados.
    """
    # implementación...
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="término original")
    parser.add_argument("--filtro", default="todos")
    parser.add_argument("--max-resultados", type=int, default=10)
    args = parser.parse_args()
    
    resultados = buscar_en_sitio(args.query, args.filtro, args.max_resultados)
    print(resultados)
```

## Integración con el Stack Nelson

### Testing E2E de PoCs
```python
# Validar que el frontend de una PoC funciona
await page.goto("http://localhost:3789")  # jarvis-demo-shell
await page.get_by_role("button", name="Enviar").click()
await page.screenshot(path="e2e_test.png")
```

### Con nelson-frontend-testing
Esta skill complementa los unit/integration tests con evidencia visual real en browser.

### Con nelson-ai-vision  
Usar `vision_analyze` para interpretar los screenshots de verificación.

### Con nelson-spec-driven-workflow
En la fase 9 (IMPLEMENTAR), el browser agent puede validar E2E que el frontend cumple la spec.

## Pitfalls

- **Firefox no instalado**: correr `python3 -m playwright install firefox` antes de usar
- **Akamai/Cloudflare**: Firefox resiste mejor que Chromium; si falla Firefox probar `channel="chrome"` con `pw.chromium`
- **Elementos detrás de drawers**: siempre abrir el panel antes del screenshot de verificación
- **full_page=True**: NUNCA usar — causa screenshots gigantes que no se pueden leer bien con visión
- **Deep-link URLs**: evitar para CLIs — usar form fill interactivo que es más robusto
- **asyncio en Jupyter/scripts**: usar `asyncio.run(main())` en scripts standalone
- **Selectores frágiles**: preferir `get_by_role` > `get_by_text` > CSS selector > XPath
- **Timeouts**: agregar `await asyncio.sleep(1)` tras clicks que disparan animaciones/cargas
