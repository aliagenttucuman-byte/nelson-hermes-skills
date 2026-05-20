# Verificación de Extractabilidad de Texto en PDFs

## El problema
No todos los PDFs contienen texto extractable. Algunos renderizan el texto como imágenes o gráficos vectoriales, haciendo que pdfplumber/PyPDF2 devuelvan texto vacío.

## Tipos de PDF y su extractabilidad

| Tipo de PDF | Texto extractable | Causa si falla |
|-------------|-------------------|----------------|
| Exportado desde Word/Google Docs | Sí | Texto real embebido |
| Exportado desde LaTeX (pdflatex) | Sí | Texto real embebido |
| Generado con ReportLab Canvas | **No** | Texto renderizado como paths vectoriales |
| Generado con ReportLab Platypus | Parcial | Depende de la configuración |
| Escaneado / Imagen | **No** | Es una imagen, necesita OCR |
| Generado con wkhtmltopdf | Sí | Texto real embebido |
| Generado con WeasyPrint | Sí | Texto real embebido |
| Generado con fpdf2 | Sí | Texto real embebido |

## Verificación rápida

### Con pdfplumber (recomendado)
```python
import pdfplumber

with pdfplumber.open("documento.pdf") as pdf:
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    
    if len(text.strip()) == 0:
        print("❌ PDF no tiene texto extractable")
    else:
        print(f"✅ Texto extraído: {len(text)} caracteres")
```

### Con PyPDF2
```python
from PyPDF2 import PdfReader

reader = PdfReader("documento.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() or ""

if len(text.strip()) == 0:
    print("❌ PDF no tiene texto extractable")
```

### Desde línea de comandos (sin dependencias extra)
```bash
# Si pdftotext está instalado (poppler-utils)
pdftotext documento.pdf - | wc -c
# Si devuelve 0, el PDF no tiene texto

# O con Python si pdfplumber está en el entorno
python3 -c "import pdfplumber; pdf=pdfplumber.open('documento.pdf'); print(sum(len(p.extract_text() or '') for p in pdf.pages))"
```

## Síntomas en el pipeline RAG

Cuando un PDF no es text-extractable:
1. El upload es exitoso (200 OK)
2. El archivo aparece en S3/MinIO/FLoCI
3. `stats.points_count` NO aumenta después del upload
4. Las preguntas sobre ese documento responden "No tengo información"
5. Los logs del backend muestran `text = ""` pero sin error

## Fixes según el caso

### PDF generado dinámicamente para testing
**No usar ReportLab Canvas**:
```python
# ❌ MAL — texto no extractable
from reportlab.pdfgen import canvas
c = canvas.Canvas("output.pdf")
c.drawString(100, 700, "Hola mundo")  # Renderiza como path
```

**Usar alternativas que generen texto real**:
```python
# ✅ BIEN — texto extractable
from fpdf import FPDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Hola mundo", ln=True)
pdf.output("output.pdf")
```

```python
# ✅ BIEN — WeasyPrint
from weasyprint import HTML
HTML(string="<h1>Hola mundo</h1>").write_pdf("output.pdf")
```

### PDF escaneado (imagen)
Requiere OCR antes de indexar:
```python
import pytesseract
from pdf2image import convert_from_path

images = convert_from_path("documento_escaneado.pdf")
text = ""
for image in images:
    text += pytesseract.image_to_string(image, lang="spa") + "\n"
```

## Checklist antes de usar un PDF en RAG

- [ ] Verificar que tiene texto extractable (> 0 caracteres)
- [ ] Si es generado dinámicamente, confirmar que la librería genera texto real
- [ ] Si es escaneado, aplicar OCR primero
- [ ] Después de upload, verificar que `stats.points_count` aumentó
- [ ] Hacer una pregunta de prueba sobre el documento
