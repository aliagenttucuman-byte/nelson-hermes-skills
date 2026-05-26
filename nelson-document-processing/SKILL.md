---
name: nelson-document-processing
title: Document Processing - PDF, Word, TXT, Markdown, Docling
description: Procesamiento de documentos para RAG. Docling (premium) + pdfplumber/python-docx (fallback ligero). PDFs complejos, tablas, OCR, DOCX, PPTX, XLSX, HTML, LaTeX, imagenes.
skill: nelson-document-processing
author: equipo-nelson
version: 1.1.0
keywords: [pdf, word, docx, markdown, parsing, extraction, text, documents, rag, docling, ocr, tables]
dependencies: [nelson-rag-pipeline, nelson-docling]
related_skills: [nelson-docling]
---

# Document Processing - Equipo Nelson

## Proposito

Extraer texto limpio y estructurado de documentos para alimentar el pipeline RAG. Sin esto, el RAG no funciona con documentos reales.

## Dos estrategias

| Estrategia | Cuando usar | Ventajas | Desventajas |
|------------|-------------|----------|-------------|
| **Docling** (premium) | PDFs complejos, tablas, OCR, PPTX, XLSX, HTML, LaTeX, imagenes | Layout + reading order, tablas nativas, OCR built-in, exporta Markdown, 10+ formatos | Mas pesado (~500MB-1GB en Docker), mas lento en primera carga |
| **pdfplumber + python-docx** (fallback ligero) | PDFs simples, DOCX basicos, textos planos | Rapido, ligero, sin modelos ML | Sin layout understanding, tablas basicas, sin OCR, menos formatos |

> **Default del equipo: Docling** para nuevos proyectos. Fallback a pdfplumber si el archivo es simple o si hay restricciones de memoria.

## Estrategia 1: Docling (recomendada)

```python
# app/services/document_processor.py
import io
from typing import List
from dataclasses import dataclass
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DocumentChunk:
    text: str
    page: int
    chunk_index: int
    metadata: dict

class DocumentProcessor:
    def process(self, file_bytes: bytes, filename: str, mime_type: str) -> List[DocumentChunk]:
        """Procesar cualquier documento con Docling."""
        logger.info("processing_document_docling", filename=filename, mime_type=mime_type)

        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.document import ConversionResult

        converter = DocumentConverter()

        # Guardar temporalmente para Docling
        tmp_path = f"/tmp/{filename}"
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        try:
            result = converter.convert(tmp_path)
            md_text = result.document.export_to_markdown()

            # Docling exporta todo el documento como Markdown limpio
            # Opcional: dividir por paginas si el resultado tiene marcadores de pagina
            pages = self._split_by_pages(md_text)

            chunks = []
            for i, page_text in enumerate(pages):
                if not page_text.strip():
                    continue
                chunks.append(DocumentChunk(
                    text=page_text,
                    page=i + 1,
                    chunk_index=i,
                    metadata={
                        "source": filename,
                        "page": i + 1,
                        "type": mime_type.split("/")[-1],
                        "processor": "docling",
                    },
                ))

            logger.info("document_processed_docling", filename=filename, chunks=len(chunks))
            return chunks

        finally:
            # Limpiar archivo temporal
            Path(tmp_path).unlink(missing_ok=True)

    def _split_by_pages(self, md_text: str) -> List[str]:
        """Dividir Markdown de Docling en paginas si hay marcadores."""
        # Docling no siempre incluye marcadores de pagina en el markdown
        # Si el texto es corto, devolver como una sola pagina
        if len(md_text) < 10000:
            return [md_text]
        # Heuristica: dividir por headers de nivel 1 o 2
        import re
        sections = re.split(r'\n(?=#+\s)', md_text)
        return [s.strip() for s in sections if s.strip()]

    def _clean_text(self, text: str) -> str:
        """Limpiar texto extraido."""
        text = " ".join(text.split())
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines).strip()
```

### Docling con OCR (PDFs escaneados)

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True  # Habilitar OCR para PDFs escaneados

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("/tmp/scanned.pdf")
print(result.document.export_to_markdown())
```

### Docling con VLM (GraniteDocling)

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.models.granite_docling_model import GraniteDoclingModel

pipeline_options = PdfPipelineOptions()
pipeline_options.vlm_options = {
    "model": "ibm-granite/granite-docling-258M"
}

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

## Estrategia 2: Fallback ligero (pdfplumber + python-docx)

Para PDFs simples o cuando Docling no este disponible (memoria limitada, contenedores ligeros):

```python
class DocumentProcessor:
    def process(self, file_bytes: bytes, filename: str, mime_type: str) -> List[DocumentChunk]:
        logger.info("processing_document", filename=filename, mime_type=mime_type)

        if mime_type == "application/pdf":
            chunks = self._process_pdf(file_bytes, filename)
        elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            chunks = self._process_word(file_bytes, filename)
        elif mime_type == "text/plain":
            chunks = self._process_text(file_bytes, filename)
        elif mime_type == "text/markdown":
            chunks = self._process_markdown(file_bytes, filename)
        else:
            raise ValueError(f"Formato no soportado: {mime_type}")

        logger.info("document_processed", filename=filename, chunks=len(chunks))
        return chunks

    def _process_pdf(self, file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        import pdfplumber

        chunks = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text or not text.strip():
                    continue

                text = self._clean_text(text)

                chunks.append(DocumentChunk(
                    text=text,
                    page=page_num,
                    chunk_index=page_num - 1,
                    metadata={
                        "source": filename,
                        "page": page_num,
                        "type": "pdf",
                        "processor": "pdfplumber",
                    },
                ))
        return chunks

    def _process_word(self, file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        import docx

        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        text = self._clean_text(text)

        return [DocumentChunk(
            text=text,
            page=1,
            chunk_index=0,
            metadata={"source": filename, "type": "docx", "processor": "python-docx"},
        )]

    def _process_text(self, file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        text = file_bytes.decode("utf-8")
        text = self._clean_text(text)

        return [DocumentChunk(
            text=text,
            page=1,
            chunk_index=0,
            metadata={"source": filename, "type": "txt", "processor": "built-in"},
        )]

    def _process_markdown(self, file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        import markdown
        from bs4 import BeautifulSoup

        md_text = file_bytes.decode("utf-8")
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n\n")
        text = self._clean_text(text)

        return [DocumentChunk(
            text=text,
            page=1,
            chunk_index=0,
            metadata={"source": filename, "type": "markdown", "processor": "markdown"},
        )]

    def _clean_text(self, text: str) -> str:
        """Limpiar texto extraido."""
        text = " ".join(text.split())
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines).strip()
```

## Selector inteligente: Docling vs Fallback

```python
def select_processor(filename: str, mime_type: str, file_size_bytes: int) -> str:
    """Decidir si usar Docling o fallback."""

    # Siempre Docling para estos formatos
    if mime_type in [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",         # XLSX
        "text/html",
        "application/xhtml+xml",
    ]:
        return "docling"

    # Siempre Docling para PDFs escaneados (OCR) o complejos
    if mime_type == "application/pdf":
        # Heuristica: archivos grandes (>5MB) probablemente tienen imagenes/tablas complejas
        if file_size_bytes > 5 * 1024 * 1024:
            return "docling"
        # Si no, fallback es suficiente para textos simples
        return "fallback"

    # DOCX: Docling para complejos, fallback para simples
    if mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        return "docling"  # Docling maneja tablas y layout mejor

    # TXT / Markdown: fallback es suficiente
    if mime_type in ["text/plain", "text/markdown"]:
        return "fallback"

    # Default: intentar Docling primero
    return "docling"
```

## Endpoint de upload (con selector)

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

    # Selector inteligente
    strategy = select_processor(file.filename, file.content_type, len(file_bytes))
    logger.info("processing_strategy", filename=file.filename, strategy=strategy)

    chunks = processor.process(
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
        strategy=strategy,  # "docling" o "fallback"
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
            "processor": strategy,
        },
    )

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "chunks_processed": result["chunks"],
        "strategy": strategy,
        "message": "Documento procesado e indexado correctamente",
    }
```

## Docker Compose

### Con Docling (imagen mas pesada)

```dockerfile
FROM python:3.11-slim

# Dependencias del sistema para Docling (OCR + layout models)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt

```
# Premium: Docling
# docling==2.x  # descomentar cuando se instale

# Fallback ligero
pdfplumber>=0.11.0
python-docx>=1.1.0
markdown>=3.6
beautifulsoup4>=4.12.0

# Base
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.9.0
```

## Tamaños de archivo

| Escenario | Max size | Como |
|-----------|----------|------|
| Desarrollo local | 10MB | FastAPI default |
| Produccion con background jobs | 100MB | Upload a Cloud Storage, procesar async |
| Produccion sin background | 50MB | `max_file_size` en nginx + FastAPI |
| Docling en contenedor limitado | 20MB | Fallback a pdfplumber si no hay memoria suficiente |

## Checklist

- [ ] Docling instalado y funcionando (`docling --version`)
- [ ] OCR funciona para PDFs escaneados (Tesseract instalado)
- [ ] Fallback funciona si Docling no esta disponible
- [ ] Tablas detectadas y formateadas correctamente (en Markdown)
- [ ] Texto limpio (sin espacios multiples, saltos de linea excesivos)
- [ ] Metadatos incluyen: source, page, user_id, mime_type, processor
- [ ] Selector inteligente elige la estrategia correcta
- [ ] Archivos grandes procesados async (background job)
- [ ] Solo usuarios autenticados pueden subir
- [ ] Validar mime_type antes de procesar

## Pitfalls

- **Docling es pesado**: la imagen Docker crece ~500MB-1GB por los modelos de ML. Para contenedores ligeros, usar fallback.
- **Primera carga lenta**: Docling descarga modelos en el primer uso. En produccion, pre-descargarlos en el Dockerfile:
  ```dockerfile
  RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"
  ```
- **PDFs generados con ReportLab no son text-extractables**: ReportLab renderiza texto como graficos vectoriales. pdfplumber devuelve `""`. Docling con OCR o VLM los puede leer.
  - **Sintoma**: Upload exitoso, pero 0 chunks extraidos.
  - **Fix con Docling**: habilitar `do_ocr=True` o usar VLM (`granite-docling-258M`).
  - **Deteccion temprana**: verificar que `stats.points_count` aumento despues de upload.
- **PDFs escaneados**: sin OCR, tanto pdfplumber como Docling devuelven texto vacio. Siempre habilitar OCR para PDFs escaneados.
- **Tesseract no instalado en Docker**: Docling OCR falla silenciosamente si falta `tesseract-ocr`. Instalarlo en el Dockerfile.
- **Memoria en contenedores**: Docling puede usar 2-4GB de RAM para PDFs grandes. Si el contenedor tiene limite, usar fallback.
- **python-docx no extrae imagenes**: solo texto. Para DOCX con imagenes + texto, usar Docling.
- **Siempre limitar tamano de upload** para evitar DoS
- **Codificacion UTF-8 para TXT**: manejar errores de decoding

## Referencias
- Docling: https://github.com/docling-project/docling
- Docling docs: https://docling-project.github.io/docling/
- Skill relacionada: `nelson-docling` — referencias especificas, MCP server, integraciones con LangChain/LlamaIndex
- `nelson-rag-pipeline` — ingestion pipeline que consume los chunks generados aqui
