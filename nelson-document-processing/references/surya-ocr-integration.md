# Integración Surya OCR como Capa 2

## Contexto

Surya es un OCR de código abierto (mit license) que soporta 90+ idiomas y supera a Tesseract en precisión. Corre 100% local en CPU o GPU.

## Pipeline actual (v3)

1. **Capa 1: MarkItDown** — PDFs nativos, Word, Excel, HTML, CSV, YouTube
2. **Capa 2: Surya OCR** — PDFs escaneados, layouts complejos, fórmulas matemáticas (LaTeX), 90+ idiomas
3. **Capa 3: pdfplumber** — fallback para tablas simples en PDFs nativos

## Instalación

```bash
pip install surya-ocr pymupdf
```

Modelos pesan ~1-2GB y se descargan en primer uso (lazy-load).

## Patrón de lazy-load en servicio

```python
class DocumentProcessor:
    def __init__(self):
        self._surya = None

    def _load_surya(self):
        if self._surya is None:
            from surya.recognition import RecognitionPredictor
            from surya.detection import DetectionPredictor
            self._surya = {
                "recognition": RecognitionPredictor(),
                "detection": DetectionPredictor(),
            }
        return self._surya
```

**Por qué:** evita bloquear el startup del servicio FastAPI mientras se cargan modelos de 2GB.

## Uso con PyMuPDF para renderizar PDF

```python
def _surya_ocr(self, file_path: str) -> str:
    import fitz  # PyMuPDF
    from PIL import Image

    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pages.append(img)

    surya = self._load_surya()
    predictions = surya["recognition"](pages, surya["detection"])
    return "\n\n".join(p.text for p in predictions)
```

## Metadatos de capa

Cada resultado incluye qué capa procesó el documento:

```python
return ProcessingResult(
    text=text,
    metadata={
        "layer": "surya",  # markitdown | surya | pdfplumber
        "has_text": len(text) > 50,
        ...
    }
)
```

## Tabla de decisión de capa

| Formato | Capa recomendada | Notas |
|---------|-----------------|-------|
| PDF nativo (texto seleccionable) | MarkItDown | Rápido, fiable |
| PDF escaneado (imágenes) | Surya OCR | 90+ idiomas, supera Tesseract |
| PDF layout complejo, columnas | Surya layout | Detecta bloques, tablas, figuras |
| Fórmulas matemáticas | Surya math OCR | Output LaTeX |
| Word, Excel, HTML, CSV | MarkItDown | Nativo |
| PDF con tablas simples | pdfplumber | Fallback liviano |

## Docker

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*
```

No necesita `tesseract-ocr` (lo eliminamos del Dockerfile).

## Pitfalls

- **Surya lazy-load:** primer request con OCR puede tardar 10-30s mientras descarga modelos. Considerar precarga en startup si el servicio es crítico.
- **PyMuPDF + Surya:** PyMuPDF renderiza cada página como imagen. PDFs de muchas páginas consumen RAM. Para PDFs >50 páginas, procesar en batches.
- **Idiomas:** Surya auto-detecta idioma pero se puede forzar con `langs=["es", "en"]`.
- **Fallback:** si Surya falla (OOM, modelo corrupto), caer a pdfplumber para PDFs nativos, o reportar error para escaneados.
