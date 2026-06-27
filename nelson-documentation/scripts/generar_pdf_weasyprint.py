#!/usr/bin/env python3
"""
Genera PDF profesional desde un archivo Markdown usando WeasyPrint.
Uso: python3 generar_pdf_weasyprint.py <input.md> <output.pdf> [titulo] [subtitulo]

Estilo AlegentAI: header con logo de texto, tablas con header azul,
blockquotes destacados, paginación A/A, marca CONFIDENCIAL en footer.
"""
import sys
import markdown
import weasyprint
from pathlib import Path

MD_PATH = sys.argv[1] if len(sys.argv) > 1 else "input.md"
PDF_PATH = sys.argv[2] if len(sys.argv) > 2 else MD_PATH.replace(".md", ".pdf")
TITULO = sys.argv[3] if len(sys.argv) > 3 else "Documento"
SUBTITULO = sys.argv[4] if len(sys.argv) > 4 else ""

md_text = Path(MD_PATH).read_text(encoding="utf-8")
html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<style>
  @page {{
    size: A4;
    margin: 2.2cm 2.5cm 2.2cm 2.5cm;
    @bottom-right {{
      content: "Pág. " counter(page) " / " counter(pages);
      font-size: 9pt; color: #888;
    }}
    @bottom-left {{
      content: "CONFIDENCIAL — AlegentAI — 2026";
      font-size: 8.5pt; color: #aaa;
    }}
  }}
  body {{
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 10.5pt;
    color: #1a1a2e;
    line-height: 1.65;
  }}
  .header {{
    border-bottom: 3px solid #0066cc;
    padding-bottom: 14px;
    margin-bottom: 26px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }}
  .company-name {{ font-size: 24pt; font-weight: 800; color: #0066cc; letter-spacing: -1px; }}
  .company-tagline {{ font-size: 9pt; color: #666; margin-top: 3px; }}
  .doc-badge {{
    background: #0066cc; color: white; padding: 6px 14px;
    border-radius: 4px; font-size: 9pt; font-weight: 600; text-align: center;
  }}
  .doc-date {{ text-align: right; font-size: 8.5pt; color: #888; margin-top: 4px; }}
  h1 {{ font-size: 19pt; color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 8px; margin-top: 4px; }}
  h2 {{ font-size: 13.5pt; color: #003d99; border-left: 4px solid #0066cc; padding-left: 10px; margin-top: 30px; page-break-after: avoid; }}
  h3 {{ font-size: 11pt; color: #1a1a2e; margin-top: 18px; page-break-after: avoid; }}
  p {{ margin: 6px 0 10px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 9pt; page-break-inside: avoid; }}
  th {{ background-color: #0066cc; color: white; padding: 8px 10px; text-align: left; font-weight: 700; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #dde3ed; vertical-align: top; }}
  tr:nth-child(even) td {{ background-color: #f4f7fb; }}
  tr:last-child td {{ border-bottom: 2px solid #0066cc; }}
  blockquote {{
    border-left: 4px solid #0066cc; background: #f0f5ff;
    margin: 12px 0; padding: 10px 16px; color: #333;
    font-size: 10pt; border-radius: 0 4px 4px 0;
  }}
  blockquote strong {{ color: #003d99; }}
  code {{ background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-size: 9pt; }}
  ul, ol {{ margin: 6px 0 10px 0; padding-left: 22px; }}
  li {{ margin: 4px 0; }}
  hr {{ border: none; border-top: 1px solid #dde3ed; margin: 22px 0; }}
  .footer {{
    margin-top: 40px; border-top: 2px solid #0066cc; padding-top: 10px;
    font-size: 8.5pt; color: #888; text-align: center;
  }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="company-name">AlegentAI</div>
    <div class="company-tagline">Inteligencia Artificial aplicada a negocios · Tucumán, Argentina</div>
  </div>
  <div>
    <div class="doc-badge">{TITULO.upper()}</div>
    <div class="doc-date">{SUBTITULO or 'Junio 2026'} · CONFIDENCIAL</div>
  </div>
</div>

{html_body}

<div class="footer">
  AlegentAI — aliagenttucuman@gmail.com | Nelson Acosta (CEO/Tech Lead) · Pablo (COO/Comercial) · Tucumán, Argentina<br/>
  Documento confidencial — No distribuir sin autorización
</div>
</body>
</html>"""

pdf = weasyprint.HTML(string=html, base_url="/").write_pdf()
Path(PDF_PATH).write_bytes(pdf)
print(f"PDF generado: {PDF_PATH} ({len(pdf):,} bytes)")
