---
name: nelson-document-processing
title: Document Processing - PDF, Word, TXT, Markdown
description: Procesamiento de documentos para RAG. Extraccion de texto desde PDFs, Word, TXT, Markdown. Limpieza, metadatos, manejo de tablas e imagenes. PyPDF, pdfplumber, python-docx.
skill: nelson-document-processing
author: equipo-nelson
version: 1.0.0
keywords: [pdf, word, docx, markdown, parsing, extraction, text, documents, rag]
dependencies: [nelson-rag-pipeline]
---

# Document Processing - Equipo Nelson

## Proposito

Extraer texto limpio y estructurado de documentos para alimentar el pipeline RAG. Sin esto, el RAG no funciona con documentos reales.

## Formatos soportados

| Formato | Libreria | Extraccion |
|---------|----------|------------|
| PDF | pdfplumber | Texto, tablas, coordenadas |
| PDF (alt) | PyPDF2 | Texto simple |
| Word | python-docx | Texto, parrafos, tablas |
| TXT | built-in | Texto plano |
| Markdown | markdown | Texto renderizado |
| CSV/Excel | pandas | Tablas |

> **Default del equipo: pdfplumber** para PDFs (mejor extraccion de tablas y layout).

## Servicio de Document Processing

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
        """Procesar cualquier documento y devolver chunks de texto."""
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

                # Limpiar texto
                text = self._clean_text(text)

                chunks.append(DocumentChunk(
                    text=text,
                    page=page_num,
                    chunk_index=page_num - 1,
                    metadata={
                        "source": filename,
                        "page": page_num,
                        "type": "pdf",
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
            metadata={"source": filename, "type": "docx"},
        )]

    def _process_text(self, file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        text = file_bytes.decode("utf-8")
        text = self._clean_text(text)

        return [DocumentChunk(
            text=text,
            page=1,
            chunk_index=0,
            metadata={"source": filename, "type": "txt"},
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
            metadata={"source": filename, "type": "markdown"},
        )]

    def _clean_text(self, text: str) -> str:
        """Limpiar texto extraido."""
        # Eliminar espacios multiples
        text = " ".join(text.split())
        # Eliminar lineas vacias multiples
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        return text.strip()
```

## Extraccion avanzada de PDFs (con tablas)

```python
def _process_pdf_with_tables(self, file_bytes: bytes, filename: str) -> List[DocumentChunk]:
    import pdfplumber

    chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Texto del cuerpo
            text = page.extract_text() or ""

            # Tablas como texto estructurado
            tables = page.extract_tables()
            for table in tables:
                table_text = "\n".join(
                    " | ".join(str(cell) if cell else "" for cell in row)
                    for row in table
                )
                text += f"\n\n[TABLA]\n{table_text}\n[/TABLA]"

            if not text.strip():
                continue

            text = self._clean_text(text)
            chunks.append(DocumentChunk(
                text=text,
                page=page_num,
                chunk_index=page_num - 1,
                metadata={"source": filename, "page": page_num, "type": "pdf", "has_tables": len(tables) > 0},
            ))
    return chunks
```

## Endpoint de upload

```python
# app/api/v1/documents.py
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
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

    # Leer archivo
    file_bytes = await file.read()

    # Procesar
    chunks = processor.process(
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
    )

    # Ingestar a Qdrant (chunking + embeddings)
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

## Docker Compose (con pdfplumber)

```dockerfile
# backend/Dockerfile (agregar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
```

## Dependencias

```bash
pip install pdfplumber python-docx markdown beautifulsoup4
```

## Tamaños de archivo

| Escenario | Max size | Como |
|-----------|----------|------|
| Desarrollo local | 10MB | FastAPI default |
| Produccion con background jobs | 100MB | Upload a Cloud Storage, procesar async |
| Produccion sin background | 50MB | `max_file_size` en nginx + FastAPI |

## Checklist

- [ ] pdfplumber extrae texto legible del PDF
- [ ] Tablas detectadas y formateadas
- [ ] Texto limpio (sin espacios multiples, saltos de linea excesivos)
- [ ] Metadatos incluyen: source, page, user_id, mime_type
- [ ] Archivos grandes procesados async (background job)
- [ ] Solo usuarios autenticados pueden subir
- [ ] Validar mime_type antes de procesar

## Pitfalls

- PDFs escaneados (imagenes) no tienen texto: necesitan OCR (Tesseract / pytesseract)
- pdfplumber necesita libgl1 en Docker (imagen slim no lo tiene)
- Archivos Word con muchas imagenes pueden ser muy pesados en memoria
- Siempre limitar tamaño de upload para evitar DoS
- Codificacion UTF-8 para TXT; manejar errores de decoding
