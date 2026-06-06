# Web Article Extraction — Receta Rápida

> Cuando Nelson comparte un link a un paper/blog/página de research y hay que analizarlo.

## Preferencia de herramientas (ordenado)

1. **Defuddle skill** (`skill_view(name='defuddle')`) — extrae markdown limpio de páginas web. Ideal si el sitio no requiere JS complejo.
2. **curl + python (BeautifulSoup / html.parser)** — fallback cuando el browser agent no levanta (sandbox issues en Linux/AppArmor).
3. **Browser agent** (`nelson-browser-agent`) — solo si la página requiere interacción (login, clicks, scroll infinito).

## Patrón curl + python (copiar y pegar)

```bash
# Descargar HTML
curl -sL "https://URL_AQUI" > /tmp/article.html

# Extraer texto con python
python3 -c "
from bs4 import BeautifulSoup
with open('/tmp/article.html') as f:
    soup = BeautifulSoup(f, 'html.parser')
# Quitar scripts/estilos
for tag in soup(['script','style','nav','header','footer']):
    tag.decompose()
text = soup.get_text(separator='\n')
# Limpiar líneas vacías
lines = [l.strip() for l in text.splitlines() if l.strip()]
print('\n'.join(lines[:500]))  # primeros 500 párrafos
"
```

## Patrón pymupdf terminal (PDFs rápidos)

Cuando Nelson sube un PDF y hay que ver el contenido sin instalar nada extra:

```bash
python3 -c "
import pymupdf
doc = pymupdf.open('/ruta/al/archivo.pdf')
text = ''
for page in doc:
    text += page.get_text()
print(text[:8000])  # primeros 8000 chars
print('\n--- TOTAL PAGES:', len(doc), '---')
"
```

## Pitfalls

- **Chrome sandbox en Linux:** `browser_navigate` puede fallar con "No usable sandbox" en Ubuntu 23.10+ o contenedores. Fix: preferir curl+python o defuddle.
- **HTML con mucho JS:** curl devuelve HTML crudo que puede no tener el contenido dinámico. En ese caso, browser agent es inevitable.
- **PDFs escaneados:** `pymupdf` devuelve texto plano; si el PDF es imagen, usar capa 2 (Surya OCR) del DocumentProcessor.

## Ejemplo de sesión

Sesión 2026-06-01: Nelson compartió `https://www.trychroma.com/research/context-rot`.
Browser falló por sandbox. Se usó `curl -sL | head -n 200` + extracción manual del texto del artículo del HTML. Resultado: análisis completo del paper "Context Rot" de Chroma.
