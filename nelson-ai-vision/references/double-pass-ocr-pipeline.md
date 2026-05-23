# Double-Pass OCR + LLM Pipeline

Patrón implementado en Fleet Optimizer (Mayo 2026) para extraer campos
completos de comprobantes argentinos usando un modelo local pequeño (qwen2.5:3b).

## Problema

Con un modelo ≤7B y un prompt que pide clasificar tipo Y extraer todos los
campos dinámicos en una sola pasada, el modelo satura y deja campos null
que están presentes en el texto OCR.

## Solución: 2 pasadas LLM

### Pasada 1 — clasificar + extracción amplia

```python
def _llm_classify_and_extract(lineas: list, campos_regex: dict) -> dict:
    tipos_disponibles = ', '.join(TIPO_SCHEMAS.keys())
    schema_str = '\n'.join(
        f'- {k}: {", ".join(v["campos"])}' for k, v in TIPO_SCHEMAS.items()
    )
    ya_resueltos = {k: v for k, v in campos_regex.items() if v is not None}

    prompt = f"""Sos un agente extractor de datos de comprobantes argentinos de flota vehicular.

TIPOS DE DOCUMENTOS disponibles: {tipos_disponibles}
CAMPOS POR TIPO:
{schema_str}
CAMPOS YA EXTRAÍDOS (no los repitas):
{json.dumps(ya_resueltos, ensure_ascii=False)}

TEXTO OCR DEL COMPROBANTE:
{chr(10).join(lineas)}

Respondé SOLO con JSON: {{"tipo": "<tipo>", "campos": {{...}}}}
JSON:"""

    # model: qwen2.5:3b, temperature: 0, num_predict: 512
```

### Pasada 2 — solo campos null, prompt dirigido

```python
FIELD_HINTS = {
    "litros":            "cantidad de litros cargados (número, ej: 120.5)",
    "precio_por_litro":  "precio unitario por litro (número, ej: 1250.00)",
    "tipo_combustible":  "diesel, nafta super, nafta premium, GNC, etc.",
    "estacion":          "nombre o número de la estación de servicio",
    "tipo_trabajo":      "descripción del trabajo realizado en gomería",
    "cantidad_cubiertas":"número de cubiertas/neumáticos",
    "medida_cubierta":   "medida del neumático, ej: 295/80R22.5",
    "descripcion_trabajo":"descripción del service o mantenimiento",
    "km_vehiculo":       "kilometraje del vehículo al momento del service",
    "repuestos":         "lista de repuestos utilizados",
    "conductor":         "nombre completo del conductor",
    "origen":            "lugar/ciudad de origen del traslado",
    "destino":           "lugar/ciudad de destino del traslado",
    "descripcion_carga": "tipo o descripción de la mercadería",
    "bultos":            "cantidad de bultos, cajas o unidades",
    "peso_kg":           "peso total en kilogramos",
    "ruta":              "número o nombre de la ruta (ej: RN9, Autopista Rosario)",
    "categoria_vehiculo":"categoría del vehículo en el peaje (ej: categoría 3, camión)",
    "concesionaria":     "nombre de la empresa concesionaria del peaje",
    "infraccion":        "descripción de la infracción",
    "articulo":          "artículo del código de tránsito infringido",
    "organismo":         "organismo que emitió la multa (municipio, provincia, etc.)",
    "fecha_vencimiento": "fecha de vencimiento de pago (formato DD/MM/AAAA)",
    "numero_poliza":     "número de póliza del seguro",
    "compania":          "nombre de la compañía aseguradora",
    "vigencia_desde":    "fecha de inicio de la cobertura",
    "vigencia_hasta":    "fecha de fin de la cobertura",
    "cobertura":         "tipo de cobertura (responsabilidad civil, todo riesgo, etc.)",
    "hora_entrada":      "hora de entrada al estacionamiento",
    "hora_salida":       "hora de salida del estacionamiento",
    "direccion":         "dirección del estacionamiento o cochera",
    "descripcion":       "descripción general del gasto o servicio",
}

def _llm_second_pass(lineas: list, tipo: str, campos_pendientes: list) -> dict:
    if not campos_pendientes:
        return {}

    schema = TIPO_SCHEMAS[tipo]
    hints_str = '\n'.join(
        f'- {c}: {FIELD_HINTS.get(c, "extraer del texto")}' for c in campos_pendientes
    )

    prompt = f"""Sos un extractor de datos de comprobantes argentinos.
El documento ya fue identificado como: {schema["label"]}

CAMPOS QUE NECESITO EXTRAER (los demás ya están resueltos):
{hints_str}

TEXTO OCR:
{chr(10).join(lineas)}

- Respondé SOLO con JSON plano.
- Si un campo no aparece en el texto, poné null.
- Para números devolvé solo el número, sin símbolos.

JSON:"""

    # model: qwen2.5:3b, temperature: 0, num_predict: 400 (menor que pasada 1)
```

### Orchestración en el endpoint

```python
@app.post("/api/ocr")
async def ocr_comprobante(file: UploadFile = File(...)):
    # ... OCR, regex_base ...

    # Pasada 1
    llm_result = _llm_classify_and_extract(lineas, campos_regex)
    tipo = llm_result["tipo"]
    campos_llm = llm_result["campos_llm"]

    # Merge 1: regex > LLM
    campos_finales = {}
    for campo in schema["campos"]:
        if campo in campos_regex and campos_regex[campo] is not None:
            campos_finales[campo] = campos_regex[campo]
        elif campo in campos_llm and campos_llm[campo] not in [None, "", "null"]:
            campos_finales[campo] = campos_llm[campo]
        else:
            campos_finales[campo] = None

    # Pasada 2: solo campos null
    campos_null = [c for c, v in campos_finales.items() if v is None]
    if campos_null:
        second_pass = _llm_second_pass(lineas, tipo, campos_null)
        for campo in campos_null:
            val = second_pass.get(campo)
            if val not in [None, "", "null"]:
                campos_finales[campo] = val
```

## Tipos de documentos soportados

| Tipo | Label | Campos clave |
|------|-------|-------------|
| combustible | ⛽ Carga de Combustible | litros, precio_por_litro, tipo_combustible, estacion |
| gomeria | 🔧 Gomería / Neumáticos | tipo_trabajo, cantidad_cubiertas, medida_cubierta |
| mantenimiento | 🛠️ Mantenimiento / Service | descripcion_trabajo, km_vehiculo, repuestos |
| remito | 📦 Remito / Traslado | origen, destino, conductor, bultos, peso_kg |
| peaje | 🛣️ Peaje | ruta, categoria_vehiculo, concesionaria |
| multa | 🚨 Multa / Infracción | infraccion, articulo, organismo, fecha_vencimiento |
| seguro | 🛡️ Seguro | numero_poliza, compania, vigencia_desde, vigencia_hasta, cobertura |
| estacionamiento | 🅿️ Estacionamiento | hora_entrada, hora_salida, direccion |
| factura_general | 🧾 Factura General | fallback para lo no identificado |

## Campos comunes via regex (siempre más confiables que LLM)

| Campo | Patron |
|-------|--------|
| fecha | `\b(\d{1,2})[/\-\.](...)` |
| monto_total | `total[:\s]*\$?\s*([\d\.,]+)` |
| numero_comprobante | `(?:factura\|ticket\|nro?)[:\s#]*([A-Z0-9-]+)` |
| cuit | `\b(20\|23\|27\|30\|33\|34)[-.]?\d{8}[-.]?\d\b` |
| patente | `\b([A-Z]{2,3}[-\s]?\d{3}[-\s]?[A-Z]{0,2}\d{0,3})\b` |

Regex tiene SIEMPRE prioridad sobre el LLM para estos campos.
