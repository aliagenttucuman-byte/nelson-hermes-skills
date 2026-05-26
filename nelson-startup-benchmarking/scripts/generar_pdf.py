"""
Genera un PDF profesional a partir de un archivo Markdown.
Uso: python3 generar_pdf.py input.md output.pdf
Requiere: pip3 install markdown2 weasyprint
"""

import sys
import markdown2
from weasyprint import HTML, CSS

def generar_pdf(md_path: str, pdf_path: str, titulo: str = "Documento"):
    with open(md_path, "r") as f:
        md_content = f.read()

    html_body = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])

    html_full = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>{titulo}</title>
    </head>
    <body>
    {html_body}
    </body>
    </html>
    """

    css = CSS(string="""
    @page {
        size: A4;
        margin: 2cm 2.5cm 2cm 2.5cm;
        @top-center {
            content: \"""" + titulo + """\";
            font-size: 9pt; color: #888;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
        @bottom-right {
            content: "Página " counter(page) " de " counter(pages);
            font-size: 9pt; color: #888;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
    }
    body {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 11pt; color: #1a1a2e; line-height: 1.6;
    }
    h1 { color: #0f3460; font-size: 22pt; border-bottom: 3px solid #0f3460; padding-bottom: 8px; }
    h2 { color: #16213e; font-size: 15pt; border-bottom: 1px solid #e94560; padding-bottom: 4px; margin-top: 28px; }
    h3 { color: #0f3460; font-size: 12pt; margin-top: 20px; }
    h4 { color: #333; font-size: 11pt; margin-top: 16px; }
    table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 10pt; }
    th { background-color: #0f3460; color: white; padding: 8px 10px; text-align: left; }
    td { padding: 6px 10px; border: 1px solid #ddd; }
    tr:nth-child(even) { background-color: #f8f9fa; }
    code, pre { font-family: 'Courier New', monospace; background-color: #f4f4f4; border: 1px solid #ddd; border-radius: 4px; padding: 2px 6px; font-size: 10pt; }
    pre { padding: 12px; white-space: pre-wrap; }
    ul, ol { margin-left: 20px; line-height: 1.8; }
    strong { color: #0f3460; }
    hr { border: none; border-top: 1px solid #e0e0e0; margin: 20px 0; }
    blockquote { border-left: 4px solid #e94560; padding-left: 16px; margin-left: 0; color: #555; font-style: italic; }
    """)

    HTML(string=html_full).write_pdf(pdf_path, stylesheets=[css])
    print(f"PDF generado: {pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 generar_pdf.py input.md output.pdf [Titulo del documento]")
        sys.exit(1)
    titulo = sys.argv[3] if len(sys.argv) > 3 else "Documento — Equipo Nelson"
    generar_pdf(sys.argv[1], sys.argv[2], titulo)
