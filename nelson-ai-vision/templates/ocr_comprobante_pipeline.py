"""
Pipeline OCR + LLM Fallback para comprobantes argentinos.
Stack: EasyOCR (local) → Regex → Ollama qwen2.5:3b (fallback)

Campos extraídos: fecha, numero_comprobante, monto_total, cuit, patente, concepto
Sin tokens externos. Corre 100% local.

Validado en producción: Fleet Optimizer AR, Mayo 2026.
"""

import re
import sys
import json
import base64
import requests
import easyocr
from pathlib import Path


OLLAMA_URL = "http://localhost:11434/api/generate"
FALLBACK_MODEL = "qwen2.5:3b"

PATRONES = {
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


def ocr_extraer_lineas(image_path: str) -> list[str]:
    """Extrae líneas de texto. gpu=False evita UserWarning en servidor con CUDA 12.2."""
    reader = easyocr.Reader(['es', 'en'], gpu=False, verbose=False)
    return reader.readtext(image_path, detail=0, paragraph=False)


def regex_extract(lineas: list) -> dict:
    texto_completo = ' '.join(lineas).lower()
    texto_orig = ' '.join(lineas)
    res = {
        "fecha": None, "monto_total": None, "numero_comprobante": None,
        "cuit": None, "patente": None, "concepto": None
    }

    for p in PATRONES["fecha"]:
        m = re.search(p, texto_orig, re.IGNORECASE)
        if m:
            # Limpiar artefactos de comillas OCR
            res["fecha"] = re.sub(r"['\"`´]", "", m.group(0).strip())
            break

    montos = []
    for p in PATRONES["monto_total"]:
        for m in re.finditer(p, texto_completo, re.IGNORECASE):
            try:
                montos.append(float(m.group(1).replace('.', '').replace(',', '.')))
            except:
                pass
    if montos:
        res["monto_total"] = max(montos)

    for p in PATRONES["numero_comprobante"]:
        m = re.search(p, texto_orig, re.IGNORECASE)
        if m:
            # Limpiar O/0 ambiguos tras letras
            nro = re.sub(r'(?<=[A-Z]{2})O', '0', m.group(1).strip())
            res["numero_comprobante"] = nro
            break

    for p in PATRONES["cuit"]:
        m = re.search(p, texto_orig)
        if m:
            res["cuit"] = m.group(0).strip()
            break

    for p in PATRONES["patente"]:
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
    """Completa campos faltantes con Ollama. Solo se invoca si hay None."""
    faltantes = [k for k, v in campos.items() if v is None]
    if not faltantes:
        return campos

    texto = '\n'.join(lineas)
    prompt = (
        "Sos un extractor de datos de comprobantes argentinos.\n"
        "Dado el siguiente texto extraído por OCR, devolvé SOLO un JSON con estos campos:\n"
        "fecha, numero_comprobante, monto_total (número), cuit, patente, concepto\n"
        "Si un campo no está, poné null. SOLO JSON, sin explicaciones.\n\n"
        f"TEXTO OCR:\n{texto}\n\nJSON:"
    )

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": FALLBACK_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 256}
        }, timeout=30)
        raw = resp.json()["response"].strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            llm_data = json.loads(m.group(0))
            for k in faltantes:
                if llm_data.get(k) not in [None, "", "null"]:
                    val = llm_data[k]
                    if isinstance(val, str):
                        val = re.sub(r"['\"`´]", "", val).strip()
                    campos[k] = val
    except Exception as e:
        print(f"[fallback error] {e}")

    return campos


def procesar_comprobante(image_path: str) -> dict:
    """Pipeline completo. Retorna campos extraídos + líneas OCR."""
    lineas = ocr_extraer_lineas(image_path)
    campos = regex_extract(lineas)
    campos = llm_fallback(lineas, campos)
    return {"campos": campos, "lineas_ocr": lineas}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Uso: python ocr_comprobante_pipeline.py /ruta/imagen.jpg")
        sys.exit(1)
    resultado = procesar_comprobante(path)
    print(json.dumps(resultado["campos"], ensure_ascii=False, indent=2))
    print(f"\n[{len(resultado['lineas_ocr'])} líneas OCR extraídas]")
