---
name: nelson-docling
description: Docling para el equipo Nelson. Parser de documentos premium de IBM — PDFs complejos, tablas, OCR, PPTX, XLSX, HTML, LaTeX, imagenes. Exporta a Markdown limpio para RAG.
category: software-development
tags: [docling, pdf, parsing, ocr, document-processing, rag, ibm, markdown, tables]
related_skills: [nelson-document-processing, nelson-rag-pipeline]
---

# Docling - Parser de Documentos Premium

> **Trigger:** Cuando Nelson necesite extraer texto estructurado de documentos complejos (PDFs con tablas, escaneados, PPTX, XLSX, HTML, LaTeX, imagenes) para RAG o agentes AI.

## Qué es

Docling es un parser de documentos open source de IBM, bajo Linux Foundation AI & Data. Convierte documentos de múltiples formatos a representaciones estructuradas (Markdown, JSON, DocTags) con understanding avanzado de layout, tablas, formulas, codigo e imagenes.

- **60k+ estrellas** en GitHub
- **MIT license**
- **OCR built-in** para PDFs escaneados (usa Tesseract)
- **VLM support** (GraniteDocling 258M) para PDFs complejos
- **MCP server** para integración con agentes AI
- **Plug-and-play** con LangChain, LlamaIndex, Haystack, Crew AI

## Formatos soportados

| Formato | Soportado | Notas |
|---------|-----------|-------|
| PDF | ✅ | Layout, tablas, formulas, codigo, OCR |
| DOCX | ✅ | Texto, tablas, imagenes |
| PPTX | ✅ | Diapositivas como secciones |
| XLSX | ✅ | Hojas como tablas Markdown |
| HTML | ✅ | Incluyendo scraping |
| LaTeX | ✅ | Papers académicos |
| Imagenes (PNG, JPEG, TIFF) | ✅ | OCR + VLM |
| Audio (WAV, MP3) | ✅ | ASR (transcripcion) |
| WebVTT | ✅ | Subtitulos |
| TXT / Markdown | ✅ | Texto plano |
| USPTO patents | ✅ | Esquema XML específico |
| JATS articles | ✅ | Papers biomédicos |
| XBRL | ✅ | Reportes financieros |

## Quick Start

### Instalación

```bash
pip install docling
```

> Requiere Python 3.10+. Soporta x86_64 y arm64 (Apple Silicon, AWS Graviton).

### CLI

```bash
# Convertir un PDF a Markdown
docling https://arxiv.org/pdf/2206.01062

# Usar VLM (GraniteDocling) para PDFs complejos
docling --pipeline vlm --vlm-model granite_docling https://arxiv.org/pdf/2206.01062
```

### Python

```python
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"
converter = DocumentConverter()
result = converter.convert(source)

# Exportar a Markdown
md = result.document.export_to_markdown()
print(md)

# Exportar a JSON estructurado
json_data = result.document.export_to_dict()
```

## OCR para PDFs escaneados

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("/tmp/scanned.pdf")
print(result.document.export_to_markdown())
```

**Pitfall:** Si Tesseract no está instalado, OCR falla silenciosamente y devuelve texto vacío.

## VLM: GraniteDocling

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.vlm_options = {
    "model": "ibm-granite/granite-docling-258M"
}

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("/tmp/complex.pdf")
print(result.document.export_to_markdown())
```

**Ventaja:** Mejor que OCR para PDFs con layout irregular, diagramas, formulas matemáticas.

## Integración con LangChain

```python
from langchain_docling import DoclingLoader

loader = DoclingLoader("https://arxiv.org/pdf/2408.09869")
docs = loader.load()

# docs es una lista de Document de LangChain, listos para vectorizar
for doc in docs:
    print(doc.page_content)
    print(doc.metadata)
```

## Integración con LlamaIndex

```python
from llama_index.readers.docling import DoclingReader

reader = DoclingReader()
docs = reader.load_data("/tmp/document.pdf")

# docs es una lista de Document de LlamaIndex
```

## MCP Server para Agentes AI

Docling expone un MCP server para que agentes AI puedan convertir documentos directamente:

```bash
# Instalar MCP server
pip install docling[mcp]

# Levantar servidor
python -m docling.mcp
```

Desde un agente (ej. DeepAgents, Crew AI):
```python
# El agente puede llamar a la tool "convert_document" de Docling
# Params: path o URL del documento
# Returns: Markdown estructurado
```

Ver skill `nelson-mcp` para más detalles sobre Model Context Protocol.

## Docker

```dockerfile
FROM python:3.11-slim

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
RUN pip install --no-cache-dir docling

# Pre-descargar modelos para evitar downloads en runtime
RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

COPY . .
CMD ["python", "main.py"]
```

## Pitfalls

1. **Primera carga lenta:** Docling descarga modelos (~200-500MB) en el primer uso. En Docker, pre-descargar con `RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"`.
2. **Tesseract obligatorio para OCR:** Sin `tesseract-ocr` instalado, los PDFs escaneados devuelven texto vacío.
3. **Memoria:** PDFs grandes (100+ páginas) pueden consumir 2-4GB de RAM. En contenedores con límite, usar fallback (pdfplumber).
4. **No es real-time:** un PDF de 50 páginas puede tardar 10-30 segundos. Procesar async en background jobs.
5. **Imagen Docker pesada:** ~1-1.5GB con todos los modelos. Para microservicios ligeros, separar el servicio de parsing en su propio contenedor.
6. **Python 3.9 no soportado:** desde v2.70.0, Docling requiere Python 3.10+.
7. **LangChain integration en beta:** `langchain-docling` puede cambiar API. Fijar versión en `requirements.txt`.

## Comparativa: Docling vs Stack actual (pdfplumber)

| Feature | Docling | pdfplumber |
|---------|---------|------------|
| PDF layout understanding | ✅ | ❌ |
| Tablas estructuradas | ✅ Avanzado | ⚠️ Básico |
| OCR escaneados | ✅ Built-in | ❌ (requiere Tesseract manual) |
| PPTX | ✅ | ❌ |
| XLSX | ✅ | ❌ |
| HTML / LaTeX | ✅ | ❌ |
| Formulas matemáticas | ✅ | ❌ |
| Export Markdown | ✅ | ❌ |
| Peso Docker | ~1-1.5GB | ~100MB |
| Velocidad | Lento (ML) | Rápido |
| Memoria | 2-4GB | <500MB |

## Cuándo usar Docling vs Fallback

| Situación | Usar |
|-----------|------|
| PDF con tablas complejas | **Docling** |
| PDF escaneado (imagen) | **Docling + OCR** |
| PPTX / XLSX | **Docling** |
| HTML / LaTeX | **Docling** |
| PDF texto simple (<5MB) | Fallback (pdfplumber) |
| DOCX simple | Fallback (python-docx) |
| Memoria limitada (<1GB) | Fallback |
| Necesita respuesta en <2s | Fallback |

## Referencias
- Docling repo: https://github.com/docling-project/docling
- Docs: https://docling-project.github.io/docling/
- arXiv paper: https://arxiv.org/abs/2408.09869
- GraniteDocling VLM: https://huggingface.co/ibm-granite/granite-docling-258M
- MCP server: https://docling-project.github.io/docling/usage/mcp/
- Skill `nelson-document-processing` — servicio completo con selector inteligente Docling vs Fallback
