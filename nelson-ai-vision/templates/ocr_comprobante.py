"""
Pipeline OCR + Fallback LLM local para extracción de campos de comprobantes argentinos.
Uso: python3 ocr_comprobante.py [ruta_imagen]
Sin ruta → genera imagen de prueba sintética.
"""

import re
import sys
import json
import requests
import easyocr
from PIL import Image


OLLAMA_URL = "http://localhost:11434/api/generate"
FALLBACK_MODEL = "qwen2.5:3b"

PROMPT_FALLBACK = """Sos un extractor de datos de comprobantes argentinos (facturas, tickets, remitos).
Dado el siguiente texto extraído por OCR, devolvé SOLO un JSON con estos campos:
  fecha, numero_comprobante, monto_total (número), cuit, patente, concepto
Si un campo no está en el texto, poné null. No inventes datos.
Responde ÚNICAMENTE con el JSON, sin explicaciones.

TEXTO OCR:
{texto}

JSON:"""

PATRONES = {
    "fecha": [
        r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b',
        r"\b(\d{1,2})[/\-\.'´`](\d{1,2})[/\-\.'´`](\d{2,4})\b",
        r'\b(\d{1,2})\s+de\s+\w+\s+de\s+(\d{4})\b',
    ],
    "monto_total": [
        r'(?:total|importe|a\s+pagar)[^\d]*\$?\s*([\d\.,]+)',
        r'total[:\s]*\$?\s*([\d\.,]+)',
        r'\$\s*([\d\.,]+)',
    ],
    "numero_comprobante": [
        r'(?:factura|ticket|recibo|comprobante|nro?\.?|n[°ú])[:\s#]*([A-Z0-9]{1,2}[\'`´]?\s*[\-\s]?\d{4,}[\-\s]?\d{4,})',
        r'\b([A-Z]{1,2}[\-\s]?\d{4,}[\-\s]?\d{4,})\b',
        r'N[°o]?\s*[\-:]?\s*(\d{4,})',
    ],
    "cuit": [r'\b(20|23|24|27|30|33|34)[-\.]?\d{8}[-\.]?\d\b'],
    "patente": [r'\b([A-Z]{2,3}[-\s]?\d{3}[-\s]?[A-Z]{0,2}\d{0,3})\b'],
}

CONCEPTOS = [
    'nafta', 'gasoil', 'combustible', 'lubricante', 'aceite',
    'gomería', 'neumatico', 'neumático', 'servicio', 'mantenimiento',
    'reparacion', 'peaje', 'estacionamiento', 'lavado', 'service',
    'seguro', 'patente', 'multa',
]


def extraer_texto(image_path: str) -> list[str]:
    reader = easyocr.Reader(['es', 'en'], gpu=True, verbose=False)
    return reader.readtext(image_path, detail=0, paragraph=False)


def extraer_campos_regex(lineas: list[str]) -> dict:
    texto_completo = ' '.join(lineas).lower()
    texto_orig = ' '.join(lineas)
    resultado = {k: None for k in ["fecha", "monto_total", "numero_comprobante", "cuit", "patente", "concepto_detectado"]}

    for patron in PATRONES["fecha"]:
        m = re.search(patron, texto_orig, re.IGNORECASE)
        if m:
            resultado["fecha"] = m.group(0).strip()
            break

    montos = []
    for patron in PATRONES["monto_total"]:
        for m in re.finditer(patron, texto_completo, re.IGNORECASE):
            try:
                montos.append(float(m.group(1).replace('.', '').replace(',', '.')))
            except:
                pass
    if montos:
        resultado["monto_total"] = max(montos)

    for patron in PATRONES["numero_comprobante"]:
        m = re.search(patron, texto_orig, re.IGNORECASE)
        if m:
            resultado["numero_comprobante"] = m.group(1).strip()
            break

    for patron in PATRONES["cuit"]:
        m = re.search(patron, texto_orig)
        if m:
            resultado["cuit"] = m.group(0).strip()
            break

    for patron in PATRONES["patente"]:
        m = re.search(patron, texto_orig)
        if m:
            resultado["patente"] = m.group(1).strip()
            break

    for concepto in CONCEPTOS:
        if concepto in texto_completo:
            resultado["concepto_detectado"] = concepto
            break

    return resultado


def fallback_llm(lineas: list[str], campos: dict) -> dict:
    faltantes = [k for k, v in campos.items() if v is None and k != 'concepto_detectado']
    if not faltantes:
        return campos
    print(f"  [fallback LLM] completando: {faltantes}")
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": FALLBACK_MODEL,
            "prompt": PROMPT_FALLBACK.format(texto='\n'.join(lineas)),
            "stream": False,
            "options": {"temperature": 0, "num_predict": 256}
        }, timeout=30)
        raw = resp.json()["response"].strip()
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            llm_data = json.loads(json_match.group(0))
            for campo in faltantes:
                if campo in llm_data and llm_data[campo] not in [None, "", "null"]:
                    campos[campo] = llm_data[campo]
    except Exception as e:
        print(f"  [fallback] Error: {e}")
    return campos


def normalizar(campos: dict) -> dict:
    """Limpia artefactos de OCR post-extracción."""
    if campos.get("fecha"):
        campos["fecha"] = re.sub(r"[\'´`]", "", campos["fecha"])
    return campos


def procesar_comprobante(image_path: str) -> dict:
    print(f"[1] OCR: {image_path}")
    lineas = extraer_texto(image_path)
    for l in lineas:
        print(f"  → {l}")
    print("[2] Regex...")
    campos = extraer_campos_regex(lineas)
    faltantes = [k for k, v in campos.items() if v is None]
    if faltantes:
        print("[3] Fallback LLM...")
        campos = fallback_llm(lineas, campos)
    campos = normalizar(campos)
    return campos


if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not image_path:
        from PIL import ImageDraw
        img = Image.new('RGB', (600, 420), color='white')
        draw = ImageDraw.Draw(img)
        for i, linea in enumerate([
            "GOMERIA EL BUEN CAUCHO", "CUIT: 20-34567890-1",
            "Factura B  N 0001-00004523", "Fecha: 21/05/2026",
            "Patente: AD 123 BH", "Concepto: Cambio neumatico",
            "Subtotal: $ 45.000,00", "IVA 21%: $ 9.450,00", "TOTAL: $ 54.450,00",
        ]):
            draw.text((30, 30 + i * 40), linea, fill='black')
        image_path = '/tmp/comprobante_prueba.png'
        img.save(image_path)
        print(f"[INFO] Imagen de prueba: {image_path}")

    campos = procesar_comprobante(image_path)
    print("\n" + "=" * 50)
    print(json.dumps(campos, ensure_ascii=False, indent=2))
