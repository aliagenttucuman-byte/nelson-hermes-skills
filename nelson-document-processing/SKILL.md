---
name: nelson-document-processing
title: Document Processing - MarkItDown + pdfplumber fallback
description: "Procesamiento de documentos para RAG. 3 capas: MarkItDown (principal, 15+ formatos), Surya (PDFs escaneados, layouts complejos, OCR 90+ idiomas), pdfplumber (fallback tablas nativas)."
skill: nelson-document-processing
author: equipo-nelson
version: 2.0.0
keywords: [pdf, word, docx, markdown, parsing, extraction, text, documents, rag, markitdown, pdfplumber]
dependencies: [nelson-rag-pipeline]
---

# Document Processing - Equipo Nelson

## Propósito

Extraer texto limpio y estructurado de documentos para alimentar el pipeline RAG.

**Arquitectura de tres capas:**
1. **MarkItDown** (Microsoft) — capa principal, soporta 15+ formatos, output siempre Markdown
2. **Surya** (datalab-to/surya) — capa 2 para PDFs escaneados, layouts complejos, tablas y OCR en 90+ idiomas. Supera a Tesseract. Corre 100% local.
3. **pdfplumber** — fallback ligero para PDFs nativos con tablas simples

**Cuándo usar cada capa:**

| Caso | Capa |
|------|------|
| PDF texto nativo, Word, Excel, HTML, CSV | MarkItDown |
| PDF escaneado / fotografiado | Surya OCR |
| Layout complejo (columnas, tablas embebidas) | Surya layout |
| Fórmulas matemáticas | Surya math OCR |
| PDF nativo con tablas simples sin layout | pdfplumber fallback |

## Formatos soportados

| Formato | Capa | Notas |
|---------|------|-------|
| PDF (texto) | MarkItDown | Directo |
| PDF (tablas complejas) | pdfplumber fallback | Mejor fidelidad de tablas |
| PDF (escaneado) | Surya OCR | 90+ idiomas, supera Tesseract, corre local |
| PDF (layout complejo, columnas) | Surya layout | Detecta bloques, tablas embebidas, figuras |
| Fórmulas matemáticas | Surya math OCR | Output LaTeX |
| Word (.docx) | MarkItDown | Reemplaza python-docx |
| Excel (.xlsx) | MarkItDown | Reemplaza pandas/openpyxl |
| PowerPoint (.pptx) | MarkItDown | Reemplaza python-pptx |
| HTML | MarkItDown | Reemplaza BeautifulSoup manual |
| CSV | MarkItDown | Reemplaza pandas |
| Email (.msg, .eml) | MarkItDown | Nativo |
| YouTube URL | MarkItDown | Extrae transcripción automática |
| TXT / Markdown | MarkItDown | Directo |
| EPUB | MarkItDown | Nativo |

## Dependencias

```bash
# Capa 1 — principal
pip install markitdown[all]

# Capa 2 — Surya (OCR + layout para escaneados y layouts complejos)
pip install surya-ocr

# Capa 3 — fallback PDFs nativos con tablas
pip install pdfplumber
```

> Surya descarga modelos de HuggingFace en el primer uso (~1-2GB). Con GPU corre 100+ páginas/min, en CPU ~5-15 seg/página.

## Servicio de Document Processing

```python
# app/services/document_processor.py
import io
import tempfile
from pathlib import Path
from typing import List
from dataclasses import dataclass
from markitdown import MarkItDown
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DocumentChunk:
    text: str
    page: int
    chunk_index: int
    metadata: dict


class DocumentProcessor:
    def __init__(self):
        self._md = MarkItDown()
        self._surya_loaded = False
        self._surya_models = {}

    def _load_surya(self):
        """Lazy-load modelos Surya (pesados, solo cuando se necesitan)."""
        if self._surya_loaded:
            return
        try:
            from surya.ocr import run_ocr
            from surya.model.detection.model import load_model as load_det
            from surya.model.detection.processor import load_processor as load_det_proc
            from surya.model.recognition.model import load_model as load_rec
            from surya.model.recognition.processor import load_processor as load_rec_proc
            self._surya_models = {
                "run_ocr":       run_ocr,
                "det_model":     load_det(),
                "det_processor": load_det_proc(),
                "rec_model":     load_rec(),
                "rec_processor": load_rec_proc(),
            }
            self._surya_loaded = True
            logger.info("surya_models_loaded")
        except Exception as e:
            logger.warning("surya_load_failed", error=str(e))

    def process(self, file_bytes: bytes, filename: str, mime_type: str) -> List[DocumentChunk]:
        """Procesar documento con pipeline de 3 capas."""
        logger.info("processing_document", filename=filename, mime_type=mime_type)
        layer = "markitdown"

        # Capa 1: MarkItDown (texto nativo, Word, Excel, HTML, CSV, etc.)
        text = self._markitdown(file_bytes, filename)

        # Capa 2: Surya (PDFs escaneados, layouts complejos, OCR multilingüe)
        if not text and mime_type == "application/pdf":
            logger.info("fallback_surya", filename=filename)
            text = self._surya_ocr(file_bytes, filename)
            layer = "surya"

        # Capa 3: pdfplumber (fallback ligero para PDFs nativos con tablas)
        if not text and mime_type == "application/pdf":
            logger.info("fallback_pdfplumber", filename=filename)
            text = self._pdfplumber(file_bytes, filename)
            layer = "pdfplumber"

        if not text:
            raise ValueError(f"No se pudo extraer texto de: {filename}")

        text = self._clean_text(text)
        logger.info("document_processed", filename=filename, chars=len(text), layer=layer)

        return [DocumentChunk(
            text=text,
            page=1,
            chunk_index=0,
            metadata={
                "source":    filename,
                "mime_type": mime_type,
                "chars":     len(text),
                "layer":     layer,
            },
        )]

    def _markitdown(self, file_bytes: bytes, filename: str) -> str:
        """Capa 1: MarkItDown. Requiere archivo temporal."""
        try:
            suffix = Path(filename).suffix or ".bin"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            result = self._md.convert(tmp_path)
            return result.text_content or ""
        except Exception as e:
            logger.warning("markitdown_failed", filename=filename, error=str(e))
            return ""
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _surya_ocr(self, file_bytes: bytes, filename: str) -> str:
        """Capa 2: Surya OCR — PDFs escaneados, layouts complejos, 90+ idiomas."""
        try:
            from PIL import Image
            import fitz  # PyMuPDF — convierte páginas PDF a imagen

            self._load_surya()
            if not self._surya_loaded:
                return ""

            # Convertir páginas PDF a imágenes PIL
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            images = []
            for page in doc:
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()

            if not images:
                return ""

            langs = [["es", "en"]] * len(images)  # español + inglés por defecto
            results = self._surya_models["run_ocr"](
                images, langs,
                self._surya_models["det_model"],
                self._surya_models["det_processor"],
                self._surya_models["rec_model"],
                self._surya_models["rec_processor"],
            )

            pages_text = []
            for page_result in results:
                lines = [line.text for line in page_result.text_lines if line.text.strip()]
                pages_text.append("\n".join(lines))

            return "\n\n".join(pages_text)

        except Exception as e:
            logger.warning("surya_ocr_failed", filename=filename, error=str(e))
            return ""

    def _pdfplumber(self, file_bytes: bytes, filename: str) -> str:
        """Capa 3: pdfplumber — fallback para PDFs nativos con tablas."""
        import pdfplumber
        pages_text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for table in page.extract_tables():
                    table_md = "\n".join(
                        " | ".join(str(c) if c else "" for c in row)
                        for row in table
                    )
                    text += f"\n\n[TABLA]\n{table_md}\n[/TABLA]"
                if text.strip():
                    pages_text.append(text)
        return "\n\n".join(pages_text)

    def _clean_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines).strip()
```

## Endpoint de upload

```python
# app/api/v1/documents.py
from fastapi import APIRouter, UploadFile, File, Depends
from app.services.document_processor import DocumentProcessor
from app.services.ingestion import IngestionPipeline
from app.api.deps import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
):
    processor = DocumentProcessor()
    ingestion = IngestionPipeline()

    file_bytes = await file.read()

    chunks = processor.process(
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
    )

    doc_id = f"doc_{current_user.id}_{file.filename}"
    all_text = "\n\n".join(c.text for c in chunks)

    result = ingestion.ingest_document(
        doc_id=doc_id,
        text=all_text,
        metadata={
            "user_id": str(current_user.id),
            "filename": file.filename,
            "mime_type": file.content_type,
        },
    )

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "chunks_processed": result["chunks"],
        "message": "Documento procesado e indexado correctamente",
    }
```

## Docker

```dockerfile
# backend/Dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# PyMuPDF para convertir PDF→imagen antes de Surya
RUN pip install pymupdf surya-ocr
```

> En producción con GPU agregar `torch` con CUDA. Sin GPU Surya es más lento pero funcional.

## Tamaños de archivo

| Escenario | Max size | Cómo |
|-----------|----------|------|
| Desarrollo local | 10MB | FastAPI default |
| Producción con background jobs | 100MB | Upload a Cloud Storage, procesar async |
| Producción sin background | 50MB | `max_file_size` en nginx + FastAPI |

## Web Articles & External Documents

When Nelson shares a link to a research paper, blog post, or web article, use the extraction recipes in `references/web-article-extraction.md`. Covers:
- Preferring `defuddle` skill for clean markdown extraction
- Fallback `curl + python` pattern when browser sandbox fails
- Quick `pymupdf` one-liner for PDFs shared via document upload

## Checklist

- [ ] MarkItDown instalado: `pip install markitdown[all]`
- [ ] Surya instalado: `pip install surya-ocr pymupdf`
- [ ] pdfplumber instalado: `pip install pdfplumber`
- [ ] Texto extraído no vacío (verificar qué capa activó el `layer` en metadata)
- [ ] Texto limpio (sin espacios múltiples, saltos de línea excesivos)
- [ ] Metadatos incluyen: source, mime_type, user_id, layer
- [ ] Archivos grandes procesados async (background job)
- [ ] Solo usuarios autenticados pueden subir
- [ ] Validar mime_type antes de procesar

## Pitfalls

- **MarkItDown requiere archivo físico**: no acepta bytes directamente. Siempre escribir a `tempfile.NamedTemporaryFile` y borrar después.
- **Surya lazy-load**: los modelos pesan ~1-2GB. Cargarlos en el constructor bloquea startup. Usar `_load_surya()` lazy (solo cuando se necesita).
- **Surya requiere PyMuPDF para convertir PDF→imagen**: `pip install pymupdf`. Sin él la capa 2 no puede renderizar páginas.
- **Surya en CPU es lento**: ~5-15 seg/página. Para prod usar GPU o procesar async (Celery). En dev es suficiente para tests rápidos.
- **Surya idiomas**: pasar lista por página. Default `["es", "en"]`. Documentos técnicos en otros idiomas: agregar el código ISO (e.g., `["es", "en", "pt"]`).
- **PDFs escaneados (imágenes)**: MarkItDown y pdfplumber retornan vacío — siempre activarán Surya. Detectar con: si `layer == "surya"` en metadata.
- **PDFs generados con ReportLab Canvas puro**: el texto es paths vectoriales. Ninguna librería extrae texto. Fix: usar `reportlab.platypus` o `fpdf2`.
- **Detección temprana**: después de upload verificar que `stats.points_count` aumentó en Qdrant. Si no → PDF sin texto extractable.
- **pdfplumber en Docker slim**: necesita `libgl1-mesa-glx` en el Dockerfile.
- **Excel con MarkItDown**: convierte a tabla Markdown. Si las celdas tienen fórmulas, extrae el valor calculado, no la fórmula.
- **YouTube URLs**: pasar la URL directamente a `MarkItDown().convert(url)` — extrae la transcripción automática del video.
