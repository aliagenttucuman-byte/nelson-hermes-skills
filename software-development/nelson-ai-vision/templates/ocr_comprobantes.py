"""
Template: Extractor de campos de comprobantes (Argentina)
Pipeline: EasyOCR → regex → fallback Ollama local
Soporta: JPG, PNG, PDF

Uso:
    python ocr_comprobantes.py imagen.jpg
    python ocr_comprobantes.py factura.pdf
"""
import re
import json
import base64
import os
import tempfile
from pathlib import Path

import easyocr
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
FALLBACK_MODEL = "qwen2.5:3b"  # también funciona llama3.2:3b

PATRONES_OCR = {
    "fecha": [
        r"\b(\d{1,2})[/\-\.'´`](\d{1,2})[/\-\.'´`](\d{2,4})\b",
        r'\b(\d{1,2})\s+de\s+\w+\s+de\s+(\d{4})\b',
    ],
    "monto_total": [
        r'(?:total|importe|a\s+pagar)[^\d]*\$?\s*([\d\.,]+)',
        r'total[:\s]*\$?\s*([\d\.,]+)',
        r'\$\s*([\d\.,]+)',
    ],
    "numero_comprobante": [
        r'(?:factura|ticket|recibo|comprobante|nro?\.?|n[°ú])[:\s#]*([A-Z0-9]{1,2}[\'\s\-]*[\d]{4,}[\-\s]?\d{4,})',
        r'\b([A-Z]{1,2}[\-\s]?\d{4,}[\-\s]?\d{4,})\b',
        r'N[°o]?\s*[\-:]?\s*(\d{4,})',
    ],
    "cuit": [r'\b(20|23|24|27|30|33|34)[-\.]?\d{8}[-\.]?\d\b'],
    "patente": [r'\b([A-Z]{2,3}[-\s]?\d{3}[-\s]?[A-Z]{0,2}\d{0,3})\b'],
}

CONCEPTOS_GASTO = [
    'nafta', 'gasoil', 'combustible', 'lubricante', 'aceite',
    'gomería', 'neumatico', 'neumático', 'servicio', 'mantenimiento',
    'reparacion', 'peaje', 'estacionamiento', 'lavado', 'service',
    'seguro', 'vto', 'multa',
]


def pdf_to_image(pdf_path: str) -> str:
    """Convierte primera página de PDF a PNG usando PyMuPDF. Retorna path de la imagen."""
    import fitz  # pymupdf
    doc = fitz.open(pdf_path)
    page = doc[0]
    mat = fitz.Matrix(2.0, 2.0)  # ~144 DPI — suficiente para OCR
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    doc.close()
    out_path = pdf_path.replace('.pdf', '_ocr_p0.png')
    pix.save(out_path)
    return out_path


def regex_extract(lineas: list) -> dict:
    texto_completo = ' '.join(lineas).lower()
    texto_orig = ' '.join(lineas)
    res = {
        "fecha": None, "monto_total": None, "numero_comprobante": None,
        "cuit": None, "patente": None, "concepto": None,
    }

    # Fecha — limpiar artefactos de comillas/acentos OCR
    for p in PATRONES_OCR["fecha"]:
        m = re.search(p, texto_orig, re.IGNORECASE)
        if m:
            res["fecha"] = re.sub(r"['\"`´]", "", m.group(0).strip())
            break

    # Monto — tomar el mayor valor encontrado (= total)
    montos = []
    for p in PATRONES_OCR["monto_total"]:
        for m in re.finditer(p, texto_completo, re.IGNORECASE):
            try:
                montos.append(float(m.group(1).replace('.', '').replace(',', '.')))
            except Exception:
                pass
    if montos:
        res["monto_total"] = max(montos)

    # Comprobante — corregir O/0 ambiguos
    for p in PATRONES_OCR["numero_comprobante"]:
        m = re.search(p, texto_orig, re.IGNORECASE)
        if m:
            nro = re.sub(r'(?<=[A-Z]{2})O', '0', m.group(1).strip())
            res["numero_comprobante"] = nro
            break

    for p in PATRONES_OCR["cuit"]:
        m = re.search(p, texto_orig)
        if m:
            res["cuit"] = m.group(0).strip()
            break

    for p in PATRONES_OCR["patente"]:
        m = re.search(p, texto_orig)
        if m:
            res["patente"] = m.group(1).strip()
            break

    for c in CONCEPTOS_GASTO:
        if c in texto_completo:
            res["concepto"] = c
            break

    return res


def llm_fallback(lineas: list, campos: dict) -> dict:
    """Completa campos nulos con Ollama local. Zero tokens externos."""
    faltantes = [k for k, v in campos.items() if v is None]
    if not faltantes:
        return campos

    texto = '\n'.join(lineas)
    prompt = f"""Sos un extractor de datos de comprobantes argentinos.
Dado el siguiente texto extraído por OCR, devolvé SOLO un JSON con estos campos:
fecha, numero_comprobante, monto_total (número), cuit, patente, concepto
Si un campo no está, poné null. SOLO JSON, sin explicaciones.

TEXTO OCR:
{texto}

JSON:"""
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": FALLBACK_MODEL, "prompt": prompt,
            "stream": False, "options": {"temperature": 0, "num_predict": 256}
        }, timeout=30)
        raw = resp.json()["response"].strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            llm_data = json.loads(m.group(0))
            for k in faltantes:
                if k in llm_data and llm_data[k] not in [None, "", "null"]:
                    val = llm_data[k]
                    if isinstance(val, str):
                        val = re.sub(r"['\"`´]", "", val).strip()
                    campos[k] = val
    except Exception as e:
        print(f"[LLM fallback error] {e}")
    return campos


def extraer_comprobante(file_path: str) -> dict:
    """
    Pipeline completo. Acepta JPG, PNG, PDF.
    Retorna dict con campos + lineas_ocr + imagen_b64.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    img_path = str(path)
    tmp_img = None

    try:
        if suffix == '.pdf':
            tmp_img = pdf_to_image(str(path))
            img_path = tmp_img
            mime = 'image/png'
            img_bytes = open(img_path, 'rb').read()
        else:
            img_bytes = path.read_bytes()
            mime = 'image/jpeg' if suffix in ['.jpg', '.jpeg'] else 'image/png'

        # OCR — instanciar Reader una vez en producción (es costoso)
        reader = easyocr.Reader(['es', 'en'], gpu=False, verbose=False)
        lineas = reader.readtext(img_path, detail=0, paragraph=False)

        campos = regex_extract(lineas)
        campos = llm_fallback(lineas, campos)

        return {
            "campos": campos,
            "lineas_ocr": lineas,
            "imagen_b64": f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}",
        }
    finally:
        if tmp_img and os.path.exists(tmp_img):
            os.unlink(tmp_img)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python ocr_comprobantes.py <imagen_o_pdf>")
        sys.exit(1)

    resultado = extraer_comprobante(sys.argv[1])
    print("\n=== CAMPOS EXTRAÍDOS ===")
    print(json.dumps(resultado["campos"], indent=2, ensure_ascii=False))
    print(f"\n=== LÍNEAS OCR ({len(resultado['lineas_ocr'])}) ===")
    for l in resultado["lineas_ocr"]:
        print(f"  → {l}")
