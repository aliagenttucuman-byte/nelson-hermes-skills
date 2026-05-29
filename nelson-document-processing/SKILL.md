---
name: nelson-document-processing
title: Document Processing - MarkItDown + pdfplumber fallback
description: Procesamiento de documentos para RAG. MarkItDown como capa principal (PDF, Word, Excel, PPT, HTML, CSV, email, YouTube). pdfplumber como fallback para PDFs con tablas complejas o escaneados con OCR.
skill: nelson-document-processing
author: equipo-nelson
version: 2.0.0
keywords: [pdf, word, docx, markdown, parsing, extraction, text, documents, rag, markitdown, pdfplumber]
dependencies: [nelson-rag-pipeline]
---

# Document Processing - Equipo Nelson

## Propósito

Extraer texto limpio y estructurado de documentos para alimentar el pipeline RAG.

**Arquitectura de dos capas:**
1. **MarkItDown** (Microsoft) — capa principal, soporta 15+ formatos, output siempre Markdown
2. **pdfplumber** — fallback para PDFs con tablas complejas o cuando MarkItDown retorna vacío

## Formatos soportados

| Formato | Capa | Notas |
|---------|------|-------|
| PDF (texto) | MarkItDown | Directo |
| PDF (tablas complejas) | pdfplumber fallback | Mejor fidelidad de tablas |
| PDF (escaneado) | Tesseract OCR | MarkItDown no hace OCR nativo |
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
# Capa principal
pip install markitdown[all]

# Fallback PDFs con tablas
pip install pdfplumber

# OCR para PDFs escaneados (opcional)
apt-get install -y tesseract-ocr
pip install pytesseract
```

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

    def process(self, file_bytes: bytes, filename: str, mime_type: str) -> List[DocumentChunk]:
        """Procesar cualquier documento y devolver chunks de texto."""
        logger.info("processing_document", filename=filename, mime_type=mime_type)

        # Intentar con MarkItDown primero
        text = self._markitdown(file_bytes, filename)

        # Fallback: pdfplumber para PDFs con tablas o si MarkItDown retorna vacío
        if not text and mime_type == "application/pdf":
            logger.info("markitdown_empty_fallback_pdfplumber", filename=filename)
            text = self._pdfplumber(file_bytes, filename)

        if not text:
            raise ValueError(f"No se pudo extraer texto de: {filename}")

        text = self._clean_text(text)
        logger.info("document_processed", filename=filename, chars=len(text))

        return [DocumentChunk(
            text=text,
            page=1,
            chunk_index=0,
            metadata={
                "source": filename,
                "mime_type": mime_type,
                "chars": len(text),
            },
        )]

    def _markitdown(self, file_bytes: bytes, filename: str) -> str:
        """Convertir a Markdown via MarkItDown. Usa archivo temporal."""
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

    def _pdfplumber(self, file_bytes: bytes, filename: str) -> str:
        """Fallback: extraer texto + tablas con pdfplumber."""
        import pdfplumber

        pages_text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                tables = page.extract_tables()
                for table in tables:
                    table_md = "\n".join(
                        " | ".join(str(cell) if cell else "" for cell in row)
                        for row in table
                    )
                    text += f"\n\n[TABLA]\n{table_md}\n[/TABLA]"
                if text.strip():
                    pages_text.append(text)

        return "\n\n".join(pages_text)

    def _clean_text(self, text: str) -> str:
        """Limpiar texto extraído."""
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
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
```

## Tamaños de archivo

| Escenario | Max size | Cómo |
|-----------|----------|------|
| Desarrollo local | 10MB | FastAPI default |
| Producción con background jobs | 100MB | Upload a Cloud Storage, procesar async |
| Producción sin background | 50MB | `max_file_size` en nginx + FastAPI |

## Checklist

- [ ] MarkItDown instalado: `pip install markitdown[all]`
- [ ] Texto extraído no vacío (verificar fallback activado si es PDF)
- [ ] Texto limpio (sin espacios múltiples, saltos de línea excesivos)
- [ ] Metadatos incluyen: source, mime_type, user_id
- [ ] Archivos grandes procesados async (background job)
- [ ] Solo usuarios autenticados pueden subir
- [ ] Validar mime_type antes de procesar

## Pitfalls

- **MarkItDown requiere archivo físico**: no acepta bytes directamente. Siempre escribir a `tempfile.NamedTemporaryFile` y borrar después.
- **PDFs escaneados (imágenes)**: MarkItDown y pdfplumber retornan vacío. Necesita Tesseract. Detectar con: si `chunks == 0` después de ambas capas → activar OCR.
- **PDFs generados con ReportLab Canvas puro**: el texto es paths vectoriales, no objetos texto. Ninguna librería lo extrae. Fix: usar `reportlab.platypus` o `fpdf2`/`weasyprint`.
- **Detección temprana**: después de upload verificar que `stats.points_count` aumentó en Qdrant. Si no → PDF sin texto extractable.
- **pdfplumber en Docker slim**: necesita `libgl1-mesa-glx` en el Dockerfile.
- **Excel con MarkItDown**: convierte a tabla Markdown. Si las celdas tienen fórmulas, extrae el valor calculado, no la fórmula.
- **YouTube URLs**: pasar la URL directamente a `MarkItDown().convert(url)` — extrae la transcripción automática del video.
