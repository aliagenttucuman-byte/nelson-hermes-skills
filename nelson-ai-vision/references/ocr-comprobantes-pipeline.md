# OCR + Extracción de Campos — Comprobantes de Flota Argentina

Pipeline validado 2026-05-22 para Fleet Optimizer AR.

## Caso de uso

Carga de comprobantes de gastos de flota (facturas, tickets, remitos).
El usuario saca foto del comprobante → el sistema extrae los campos → se guarda en BD.

## Stack elegido

| Componente | Herramienta | Motivo |
|---|---|---|
| OCR | EasyOCR 1.7.2 (`['es','en']`) | Mejor accuracy que Tesseract en texto real, corre local |
| Extracción | Regex (Python `re`) | Cero costo, cubre 80% de casos |
| Fallback | Ollama `qwen2.5:3b` | Local, gratis, excelente en JSON estructurado |

## Campos objetivo

```json
{
  "fecha": "21/05/2026",
  "numero_comprobante": "B-0001-00004523",
  "monto_total": 54450.0,
  "cuit": "20-34567890-1",
  "patente": "AD 123 BH",
  "concepto_detectado": "neumatico"
}
```

## Flujo de decisión

```
imagen
  └─> EasyOCR → lista de líneas
        └─> regex → dict con campos (algunos pueden ser null)
              └─> ¿hay campos null? → sí → Ollama qwen2.5:3b → completar faltantes
                                    → no → devolver dict directo
```

## Artefactos OCR conocidos en comprobantes argentinos

| Artefacto | Ejemplo | Fix |
|---|---|---|
| Apóstrofe en dígitos | `'2026` | Regex con `[/\-\.'´\`]` o LLM fallback |
| O confundida con 0 | `NOOO1` en lugar de `N001` | Imagen de mejor calidad; fallback ayuda |
| Palabras pegadas | `neumaticodelantero` | Normalizar con `re.sub(r'([a-z])([A-Z])', r'\1 \2', texto)` |
| Texto partido | `GOMERIA` / `BUEN CAUCHO` en líneas separadas | Unir líneas contiguas con heurística de distancia vertical |

## Normalización post-extracción recomendada

```python
import re

def normalizar_fecha(fecha_raw: str) -> str:
    """Limpia artefactos de OCR en fechas."""
    if not fecha_raw:
        return None
    # Quitar comillas, apostrofes, backticks
    limpia = re.sub(r"[\'´`]", "", fecha_raw)
    # Normalizar separadores
    limpia = re.sub(r"[\-\.]", "/", limpia)
    return limpia.strip()

def normalizar_monto(monto) -> float:
    """Unifica formato de montos argentinos."""
    if isinstance(monto, (int, float)):
        return float(monto)
    s = str(monto).replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return None
```

## Spike de referencia

Código completo: `~/brainstorming/2026-05-22-fleet-optimizer/spikes/001-ocr-comprobantes/spike.py`

Resultado del spike con imagen sintética:
- 6/6 campos extraídos (4 regex + 2 LLM fallback)
- Tiempo total: ~5-8s (CPU; con GPU compatible ~1-2s)
- Sin tokens cloud consumidos

## Modelos Ollama disponibles en ai-server (2026-05-22)

| Modelo | Tamaño | Uso recomendado |
|---|---|---|
| qwen2.5:3b | 1.9GB | ✅ Extracción de campos (JSON estructurado) |
| llama3.2:3b | 2.0GB | Alternativa general |
| gemma3:1b | 815MB | Más liviano, menos preciso |
| llama3.1:8b | 4.9GB | Alta precisión, más lento |
| llava:7b | 4.7GB | Vision multimodal (imagen → texto directo) |

**Nota**: `llava:7b` puede usarse para saltarse EasyOCR completamente y hacer OCR+extracción en un solo paso con imagen base64. Trade-off: más lento pero más preciso en imágenes complejas.

## Próximos pasos de integración (Fleet Optimizer AR)

1. Endpoint `POST /api/comprobantes/upload` — recibe imagen, devuelve JSON de campos
2. Worker Celery para procesar en background (no bloquear HTTP)
3. UI: modal "Cargar comprobante" con preview de campos extraídos para corrección manual
4. Modelo BD: tabla `Comprobante` con FK a `Vehiculo` (por patente)
