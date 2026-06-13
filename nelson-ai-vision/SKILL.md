---
name: nelson-ai-vision
title: AI Vision - Computer Vision, OCR, Image Analytics
description: Vision por computadora para el equipo Nelson. OCR, extraccion de texto de imagenes, object detection, clasificacion de imagenes, analisis de documentos escaneados. OpenCV, Tesseract, EasyOCR, modelos multimodales.
skill: nelson-ai-vision
author: equipo-nelson
version: 1.0.0
keywords: [vision, ocr, computer-vision, images, opencv, tesseract, easyocr, multimodal]
dependencies: [nelson-llm-generation]
---

# AI Vision - Equipo Nelson

## Casos de uso

- Extraer texto de facturas, DNI, pasaportes, contratos escaneados
- Clasificar imagenes (defectos en productos, categorias, etc.)
- Detectar objetos en imagenes (inventario, seguridad, etc.)
- Analizar imagenes con LLM multimodal (GPT-4V, Claude, Gemini)
- Preprocesamiento de imagenes para mejorar OCR
- **Detección de personas en riesgo en tiempo real** (piletas, piscinas, seguridad pública) — ver `references/drowning-detection-market.md`

## Stack

| Tarea | Libreria / Servicio | Notas |
|-------|---------------------|-------|
| OCR basico | Tesseract (pytesseract) | Gratis, local, 100+ lenguajes |
| OCR avanzado | EasyOCR | Deep learning, mejor accuracy |
| OCR cloud | Google Vision API | Mejor para handwriting, escalable |
| Preprocesamiento | OpenCV (cv2) | Resize, threshold, denoise, deskew |
| Deteccion objetos | YOLOv8 (ultralytics) | Rapido, preciso, local |
| Clasificacion | CLIP (open-clip) | Zero-shot, sin entrenamiento |
| Multimodal LLM | GPT-4o / Claude 3 / Gemini | Preguntarle cosas a la imagen |

## OCR con Tesseract

```python
# app/services/ocr.py
import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import BinaryIO
from app.core.logging import get_logger

logger = get_logger(__name__)

class OCRService:
    def __init__(self, lang: str = "spa+eng"):
        self.lang = lang

    def extract_text(self, image_bytes: bytes) -> str:
        """Extraer texto de imagen."""
        logger.info("ocr_extract", size=len(image_bytes))

        # Preprocesar
        preprocessed = self._preprocess(image_bytes)

        # OCR
        text = pytesseract.image_to_string(preprocessed, lang=self.lang)
        text = text.strip()

        logger.info("ocr_result", length=len(text))
        return text

    def extract_data(self, image_bytes: bytes) -> dict:
        """Extraer texto con metadata (bounding boxes, confianza)."""
        preprocessed = self._preprocess(image_bytes)
        data = pytesseract.image_to_data(
            preprocessed, lang=self.lang, output_type=pytesseract.Output.DICT
        )
        return data

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Preprocesar imagen para mejor OCR."""
        # Bytes -> numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Threshold (binarizacion adaptativa)
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Deskew (enderezar)
        coords = np.column_stack(np.where(binary > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) > 0.5:
            (h, w) = binary.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            binary = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        return binary
```

## OCR con EasyOCR (mejor accuracy)

```python
# app/services/ocr_easy.py
import easyocr

class EasyOCRService:
    def __init__(self, lang_list: list[str] = None):
        self.lang_list = lang_list or ["es", "en"]
        self.reader = easyocr.Reader(self.lang_list)

    def extract_text(self, image_path: str) -> str:
        results = self.reader.readtext(image_path, detail=0)
        return "\n".join(results)
```

## LLM Multimodal (GPT-4o Vision)

```python
# app/services/vision_llm.py
import base64
from openai import OpenAI
from app.config import settings

class VisionLLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        """Preguntarle a un LLM multimodal sobre una imagen."""
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=2048,
        )
        return response.choices[0].message.content

    def extract_invoice_data(self, image_bytes: bytes) -> dict:
        """Extraer datos estructurados de una factura."""
        prompt = """Analiza esta imagen de una factura y extrae:
        - numero_factura
        - fecha
        - total
        - items (lista de productos/servicios con precios)
        - cliente
        Responde SOLO en formato JSON."""

        result = self.analyze_image(image_bytes, prompt)
        # Parsear JSON de la respuesta
        import json
        return json.loads(result)
```

## Object Detection (YOLOv8)

```python
# app/services/object_detection.py
from ultralytics import YOLO
from PIL import Image
import numpy as np

class ObjectDetectionService:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)

    def detect(self, image_bytes: bytes) -> list[dict]:
        """Detectar objetos en imagen."""
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))
        results = self.model(img)

        detections = []
        for box in results[0].boxes:
            detections.append({
                "class": results[0].names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()[0],
            })
        return detections
```

## Clasificacion Zero-Shot (CLIP)

```python
# app/services/image_classifier.py
import torch
import clip
from PIL import Image
from io import BytesIO

class ImageClassifier:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

    def classify(self, image_bytes: bytes, labels: list[str]) -> dict:
        """Clasificar imagen en una de las categorias dadas."""
        img = Image.open(BytesIO(image_bytes))
        image = self.preprocess(img).unsqueeze(0).to(self.device)
        text = clip.tokenize(labels).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(image)
            text_features = self.model.encode_text(text)
            logits_per_image, _ = self.model(image, text)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

        return {label: float(prob) for label, prob in zip(labels, probs)}
```

## Endpoint FastAPI

```python
# app/api/v1/vision.py
from fastapi import APIRouter, UploadFile, File, Depends
from app.services.ocr import OCRService
from app.services.vision_llm import VisionLLMService
from app.api.deps import get_current_user

router = APIRouter(prefix="/vision", tags=["vision"])

@router.post("/ocr")
async def ocr_upload(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
):
    file_bytes = await file.read()
    ocr = OCRService()
    text = ocr.extract_text(file_bytes)
    return {"text": text, "filename": file.filename}

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = "Describe esta imagen en detalle.",
    current_user = Depends(get_current_user),
):
    file_bytes = await file.read()
    vision = VisionLLMService()
    result = vision.analyze_image(file_bytes, prompt)
    return {"analysis": result, "filename": file.filename}

@router.post("/detect")
async def detect_objects(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
):
    from app.services.object_detection import ObjectDetectionService
    file_bytes = await file.read()
    detector = ObjectDetectionService()
    objects = detector.detect(file_bytes)
    return {"objects": objects, "count": len(objects)}
```

## Docker (OpenCV + Tesseract)

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

# Tesseract + OpenCV deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# ... resto del Dockerfile
```

## Pipeline OCR + Fallback LLM local (extracción de comprobantes)

Patrón validado en producción para extracción de campos de comprobantes de flota
(facturas, tickets, remitos argentinos) sin gastar tokens de LLM cloud.

### Arquitectura de dos etapas

```
Imagen → EasyOCR (GPU) → Regex → [si faltan campos] → Ollama local → JSON
```

**Etapa 1 — EasyOCR:** extrae líneas de texto crudo. Corre en GPU GTX 1650,
soporta `['es', 'en']`, descarga modelos en primer uso (~100MB).

**Etapa 2 — Regex:** patrones para fecha, monto_total, numero_comprobante,
cuit, patente, concepto. Cubre el 80% de los casos sin LLM.

**Fallback LLM (Ollama):** solo se llama si quedan campos `null` tras regex.
Modelo recomendado: `qwen2.5:3b` (1.9GB, rápido, muy bueno en JSON estructurado).
Alternativa: `llama3.2:3b`.

### Código del pipeline

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
FALLBACK_MODEL = "qwen2.5:3b"

PROMPT_FALLBACK = """Sos un extractor de datos de comprobantes argentinos.
Dado el siguiente texto extraído por OCR, devolvé SOLO un JSON con estos campos:
  fecha, numero_comprobante, monto_total (número), cuit, patente, concepto
Si un campo no está en el texto, poné null. No inventes datos.
Responde ÚNICAMENTE con el JSON, sin explicaciones.
TEXTO OCR:
{texto}
JSON:"""

def fallback_llm(lineas, campos_incompletos):
    faltantes = [k for k, v in campos_incompletos.items() if v is None]
    if not faltantes:
        return campos_incompletos
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
                campos_incompletos[campo] = llm_data[campo]
    return campos_incompletos
```

### Campos de comprobantes argentinos (patrones regex validados)

```python
PATRONES = {
    "fecha": [
        r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b',
        r"\b(\d{1,2})[/\-\.'´`](\d{1,2})[/\-\.'´`](\d{2,4})\b",  # con comillas OCR
    ],
    "monto_total": [
        r'(?:total|importe|a\s+pagar)[^\d]*\$?\s*([\d\.,]+)',
        r'total[:\s]*\$?\s*([\d\.,]+)',
        r'\$\s*([\d\.,]+)',
    ],
    "numero_comprobante": [
        r'(?:factura|ticket|recibo|comprobante|nro?\.?|n[°ú])[:\s#]*([A-Z0-9]{1,2}[\'`´]?\s*[\-\s]?\d{4,}[\-\s]?\d{4,})',
        r'\b([A-Z]{1,2}[\-\s]?\d{4,}[\-\s]?\d{4,})\b',
    ],
    "cuit": [r'\b(20|23|24|27|30|33|34)[-\.]?\d{8}[-\.]?\d\b'],
    "patente": [r'\b([A-Z]{2,3}[-\s]?\d{3}[-\s]?[A-Z]{0,2}\d{0,3})\b'],
}
```

### Resultado del spike (imagen sintética)

| Campo | Método | Resultado |
|-------|--------|-----------|
| monto_total | regex | ✅ 54450.0 |
| cuit | regex | ✅ 20-34567890-1 |
| patente | regex | ✅ AD 123 BH |
| concepto | regex | ✅ neumatico |
| fecha | LLM fallback | ✅ 21/05/'2026 (requiere limpieza de comilla) |
| numero_comprobante | LLM fallback | ✅ NOOO1-00004523 (O/0 según calidad imagen) |

Spike completo: `~/brainstorming/2026-05-22-fleet-optimizer/spikes/001-ocr-comprobantes/spike.py`

Ver `references/ocr-comprobantes-pipeline.md` para detalles y pitfalls.

## PITFALL — TIFs subexpuestos para VLM (ortofotos drone Pix4Dfields)

Los TIFs exportados por Pix4Dfields tienen mean ~60/255 (muy oscuro).
Las imágenes generadas sin stretch parecen en escala de grises para el VLM
→ gpt-4o-mini devuelve todo "Otro" / no puede clasificar.

**Fix — stretch de contraste p2-p98 per-canal al generar tiles:**
```python
for ch in range(3):
    p2, p98 = np.percentile(rgb[:, :, ch], (2, 98))
    if p98 > p2:
        rgb_stretched[:, :, ch] = np.clip(
            (rgb[:, :, ch].astype(np.float32) - p2) / (p98 - p2) * 255, 0, 255
        ).astype(np.uint8)
    else:
        rgb_stretched[:, :, ch] = rgb[:, :, ch]
rgb = rgb_stretched
```

**Diagnóstico:** `cv2.imread(tile_path).mean()` — si < 80, aplicar stretch.
**Resultado esperado con stretch:** mean ~122/255, VLM clasifica correctamente.

**Cuidado con RGBA:** Pix4Dfields exporta 4 bandas. Leer solo R,G,B con
`src.read([1,2,3])`. Verificar con `src.colorinterp` que sea (red, green, blue, alpha).

## Dependencias

```bash
pip3 install pytesseract pillow opencv-python-headless easyocr
pip3 install ultralytics  # YOLO (pesado, descarga modelos)
pip3 install openai       # Para vision LLM cloud
# pip3 install torch torchvision  # Para CLIP (opcional, muy pesado)
# Ollama (LLM fallback local): instalar desde https://ollama.com
# Modelos recomendados: qwen2.5:3b, llama3.2:3b
```

## Checklist

- [ ] Imagen preprocesada (grayscale, denoise, threshold, deskew)

## Casos de Uso I+D+I

### Detección de Ahogamiento en Piletas

Idea de producto validada en Mayo 2026. Stack: YOLOv8 + MediaPipe Pose + ByteTrack + FastAPI + React. Mercado local virgen en Argentina. Ver `references/drowning-detection-market.md` para investigación competitiva completa, estimativo económico y plan de 3 fases.
- [ ] OCR con idioma correcto (spa+eng para latam)
- [ ] Bounding boxes guardadas si se necesita verificacion visual
- [ ] LLM multimodal para extraccion estructurada (facturas, forms)
- [ ] Limitar tamaño de imagen antes de procesar (resize si >4K)
- [ ] Resultados cacheados por hash de imagen
- [ ] Solo usuarios autenticados pueden subir imagenes

## Detección de personas en tiempo real (piletas / seguridad)

Caso de uso validado para producto en Argentina: sistema de detección de ahogamiento
en piletas públicas, privadas, countries y hoteles. No existe competidor local con IA.

### Stack recomendado

| Componente | Herramienta | Rol |
|-----------|-------------|-----|
| Detección de personas | YOLOv8 / YOLOv11 (Ultralytics) | Detectar cuerpos en frame |
| Estimación de pose | MediaPipe Pose | Detectar postura de peligro (horizontal, inmóvil) |
| Tracking multi-persona | ByteTrack | Saber si persona lleva >20s sin moverse |
| Lógica temporal | LSTM o reglas simples | "Inmóvil >20s bajo agua = alerta" |
| Backend | FastAPI | API de alertas y panel |
| Alertas real-time | WebSocket + Push notifications | Guardavidas / encargado |

### Flujo básico de detección

```python
# Lógica central de detección de ahogamiento
import cv2
from ultralytics import YOLO
import mediapipe as mp
from collections import defaultdict
import time

model = YOLO("yolov8n.pt")
pose = mp.solutions.pose.Pose()

# Tracking: persona_id -> timestamp primera vez inmóvil
immobile_since = defaultdict(lambda: None)
ALERT_THRESHOLD_SECONDS = 20

def analyze_frame(frame, track_results):
    alerts = []
    for box in track_results[0].boxes:
        person_id = int(box.id) if box.id is not None else -1
        # Detectar si está inmóvil bajo agua con pose estimation
        # (simplificado: comparar posición con frame anterior)
        # Si immobile_since[person_id] hace >20s → alerta
        if immobile_since[person_id]:
            elapsed = time.time() - immobile_since[person_id]
            if elapsed > ALERT_THRESHOLD_SECONDS:
                alerts.append({"person_id": person_id, "seconds": elapsed})
    return alerts
```

### Datasets y referencias open source

- Roboflow Universe: buscar "drowning detection" — datasets anotados disponibles
- GitHub: buscar "drowning detection YOLO" — proyectos universitarios de base
- Papers: IEEE "Drowning Detection Using Computer Vision and Deep Learning" (2021-2023)
- arXiv: "Real-time Drowning Detection in Swimming Pools Using Pose Estimation"

### Competidores internacionales

Ver `references/drowning-detection-market.md` para análisis completo de mercado.

---

## VLM para clasificación de imagen por lote (DeepForest + SAM + VLM)

Patrón validado en ForestAI PoC (Mayo 2026): pipeline DeepForest detecta bboxes →
SAM refina en máscaras → VLM clasifica especie/salud por crop de copa.

### Bug crítico: asyncio.run() dentro de FastAPI

FastAPI/uvicorn ya tiene un event loop activo. Llamar `asyncio.run()` desde un
endpoint o servicio sincrónico levanta `RuntimeError: cannot be called from a running event loop`.

**Fix validado — thread separado con loop propio:**

```python
import asyncio
import concurrent.futures

def _run_vlm():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            classify_trees_vlm(image_np, trees, api_key, concurrency=1)
        )
    finally:
        loop.close()

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    vlm_results = pool.submit(_run_vlm).result(timeout=180)
```

Aplica también en Celery workers (mismo problema con event loop). Mismo fix.

### Elección de modelo VLM para visión de imágenes aéreas

Validado contra OpenCode API (Mayo 2026):

| Modelo | Visión OK | Notas |
|--------|-----------|-------|
| claude-haiku-4-5 | ✅ | Más barato, ~2s, JSON limpio |
| claude-sonnet-4 | ✅ | Más potente, más caro |
| claude-opus-4-x | ✅ | El más caro |
| gpt-5.x (nano/mini/pro) | ❌ | El proxy de OpenCode no pasa imágenes (400 vacío) |
| gemini-3.x | ❌ | Error de auth GCP en OpenCode |
| meta/llama-3.2-90b-vision | ⚠️ | Inestable: rechaza crops con frases en lugar de JSON, timeouts frecuentes en free tier NVIDIA NIM |
| minimax, deepseek, etc | ❌ | Sin soporte multimodal |

**Recomendación para ForestAI y proyectos similares:** `claude-haiku-4-5` vía OpenCode.

### Configuración VLM con OpenCode

```python
# Usar la key de OpenCode en lugar de NVIDIA
import aiohttp, base64, json, os, re
from io import BytesIO
from PIL import Image

OPENCODE_BASE_URL = "https://opencode.ai/zen/v1/chat/completions"
VLM_MODEL = "claude-haiku-4-5"

async def classify_one_crop(session, semaphore, api_key, tree_idx, crop_b64):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": VLM_MODEL,
        "messages": [
            {"role": "system", "content": (
                "You are an expert remote sensing analyst specializing in forestry. "
                "Analyze aerial/satellite RGB images of tree canopies. "
                "Respond ONLY with a valid JSON: "
                "{\"species\": \"...\", \"health\": \"saludable|estresado|enfermo|dudoso\", "
                "\"confidence\": 0.0, \"notes\": \"max 10 words\"}"
            )},
            {"role": "user", "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{crop_b64}"}},
                {"type": "text",
                 "text": "Analyze this aerial vegetation image. Respond ONLY with JSON."},
            ]},
        ],
        "max_tokens": 150,
        "temperature": 0.1,
    }
    async with semaphore:
        async with session.post(OPENCODE_BASE_URL, headers=headers,
                                json=payload,
                                timeout=aiohttp.ClientTimeout(total=30)) as resp:
            data = await resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if match:
                return {"tree_idx": tree_idx, "vlm_ok": True,
                        **json.loads(match.group(0))}
            return {"tree_idx": tree_idx, "vlm_ok": False}
```

### Pitfalls de VLM para análisis de copas

- **Llama Vision rechaza crops pequeños en español**: si el bbox tiene <40px de lado, el modelo responde "No puedo identificar" en lugar de JSON. Pre-filtrar con `MIN_CROP_PX = 30` y escalar a min 128×128.
- **Procesar en lotes limitados**: con 55+ árboles, limitar a los 8-10 más grandes por área de copa (priorizar por `(xmax-xmin)*(ymax-ymin)` desc). Evita timeouts en free tier.
- **System prompt con `<>` placeholders confunde al modelo**: si el system message tiene texto como `<species name>`, el modelo lo copia literalmente como respuesta. Usar ejemplos con `"..."` en su lugar.
- **Separar system y user**: enviar el system prompt en `{"role": "system", "content": "..."}` separado del user message con la imagen — no mezclarlos en el content del user.
- **JSON robusto**: siempre usar regex para extraer `{...}` del response. El modelo puede agregar prose antes/después del JSON aunque se le pida JSON puro.

## Agente extractor de campos para comprobantes (Fleet/Logística)

Para carga de comprobantes de gastos de vehículos (tickets de combustible, peajes, movimiento de mercaderías), el stack sin tokens pagos es:

**Etapa 1 — OCR:** EasyOCR extrae el texto crudo de la imagen. Corre en GPU local, soporta español, no requiere entrenamiento. Más preciso que Tesseract en tickets impresos con fuentes variadas.

**Etapa 2 — Extracción de campos:** Un modelo liviano local (Phi-3 mini, Mistral 7B via NVIDIA NIM free tier) recibe el texto crudo y devuelve JSON estructurado. Sin consumo de API paga.

```python
# app/services/comprobante_extractor.py
import easyocr
import json
from openai import OpenAI  # apuntado a modelo local o NVIDIA NIM

reader = easyocr.Reader(['es', 'en'], gpu=True)

EXTRACTION_PROMPT = """
Extraé los siguientes campos del texto de un comprobante. 
Responde SOLO en JSON, sin explicaciones.

Campos:
- tipo_comprobante: (factura | ticket | remito | otro)
- numero: string o null
- fecha: formato YYYY-MM-DD o null
- monto_total: float o null
- concepto: string breve o null
- proveedor: string o null
- patente_vehiculo: string o null (si aparece)

Texto del comprobante:
{texto}
"""

def extract_fields(image_path: str) -> dict:
    # Etapa 1: OCR
    results = reader.readtext(image_path, detail=0)
    texto_crudo = "\n".join(results)
    
    # Etapa 2: extracción con LLM local
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)
    resp = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",  # o phi-3-mini
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(texto=texto_crudo)}],
        max_tokens=512,
        temperature=0,
    )
    return json.loads(resp.choices[0].message.content)
```

**Endpoint FastAPI para comprobantes:**
```python
@router.post("/comprobantes/upload")
async def upload_comprobante(
    file: UploadFile = File(...),
    vehiculo_id: int = Form(...)
):
    # Guardar imagen
    path = f"/tmp/{file.filename}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    
    # Extraer campos
    campos = extract_fields(path)
    campos["vehiculo_id"] = vehiculo_id
    campos["imagen_path"] = path
    
    return campos  # Frontend muestra para confirmar antes de guardar
```

**UX recomendada:** El agente extrae los campos y el usuario los confirma antes de guardar a BD. No guardar automáticamente sin revisión humana.

## Pipeline OCR + LLM Fallback (patrón validado en producción)

Para extracción de campos de documentos (facturas, tickets, remitos) sin gastar tokens externos:

```
Imagen → EasyOCR → Regex → (solo si faltan campos) Ollama local → JSON
```

**Ventaja:** 80-90% de campos se extraen con regex en microsegundos. Ollama solo entra para los que fallan.

### Implementación

```python
import re, json, easyocr, requests

OLLAMA_URL = "http://localhost:11434/api/generate"
FALLBACK_MODEL = "qwen2.5:3b"  # liviano, rápido, excelente en tareas estructuradas

PATRONES = {
    "fecha": [
        r"\b(\d{1,2})[/\-\.'´`](\d{1,2})[/\-\.'´`](\d{2,4})\b",  # acepta comillas OCR
    ],
    "monto_total": [
        r'(?:total|importe)[^\d]*\$?\s*([\d\.,]+)',
        r'\$\s*([\d\.,]+)',
    ],
    "cuit": [r'\b(20|23|24|27|30|33|34)[-\.]?\d{8}[-\.]?\d\b'],
    "patente": [r'\b([A-Z]{2,3}[-\s]?\d{3}[-\s]?[A-Z]{0,2}\d{0,3})\b'],
}

def extraer_campos(lineas):
    # 1. Regex pass
    campos = { ... }  # aplicar PATRONES

    # 2. Limpiar artefactos OCR en fecha (comillas, apóstrofos)
    if campos.get("fecha"):
        campos["fecha"] = re.sub(r"['\"`´]", "", campos["fecha"])

    # 3. Fallback LLM solo para campos None
    faltantes = [k for k, v in campos.items() if v is None]
    if faltantes:
        prompt = f"Extraé del siguiente texto OCR un JSON con: fecha, numero_comprobante, monto_total, cuit, patente, concepto. Solo JSON.\n\n{chr(10).join(lineas)}"
        resp = requests.post(OLLAMA_URL, json={
            "model": FALLBACK_MODEL, "prompt": prompt,
            "stream": False, "options": {"temperature": 0, "num_predict": 256}
        }, timeout=30)
        llm_data = json.loads(re.search(r'\{.*\}', resp.json()["response"], re.DOTALL).group(0))
        for k in faltantes:
            if llm_data.get(k) not in [None, "", "null"]:
                val = llm_data[k]
                if isinstance(val, str):
                    val = re.sub(r"['\"`´]", "", val).strip()
                campos[k] = val
    return campos
```

Ver template completo en `templates/ocr_comprobante_pipeline.py`.

**Endpoint FastAPI listo para copiar:**

```python
@app.post("/api/ocr")
async def ocr_comprobante(file: UploadFile = File(...)):
    import tempfile, os
    import easyocr

    contents = await file.read()
    suffix = Path(file.filename).suffix if file.filename else '.jpg'

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        reader = easyocr.Reader(['es', 'en'], gpu=False, verbose=False)
        lineas = reader.readtext(tmp_path, detail=0, paragraph=False)
        campos = regex_extract(lineas)
        campos = llm_fallback(lineas, campos)

        img_b64 = base64.b64encode(contents).decode()
        mime = "image/jpeg" if suffix.lower() in ['.jpg','.jpeg'] else "image/png"

        return {
            "campos": campos,
            "lineas_ocr": lineas,
            "imagen_b64": f"data:{mime};base64,{img_b64}",
            "filename": file.filename,
        }
    finally:
        os.unlink(tmp_path)
```

**UI React (tab de comprobantes):**
- Drop zone con drag & drop
- Preview de imagen + texto OCR crudo (líneas)
- Campos con tilde ✅ / gris si no detectado
- Badge: "Procesado con EasyOCR + Ollama local · Sin tokens externos"

Ver `templates/ocr_comprobante_pipeline.py` para el pipeline Python completo.

### Artefactos frecuentes de EasyOCR en documentos argentinos

| Artefacto | Causa | Fix |
|-----------|-------|-----|
| `21/05/'2026` | Comilla en año | `re.sub(r"['\"\`´]", "", fecha)` |
| `NOOO1-00004523` | O/0 ambiguos | `re.sub(r'(?<=[A-Z]{2})O', '0', nro)` |
| `BN` en lugar de `B 0001` | Espaciado OCR | Regex con `[\'\s\-]*` entre tipo y número |
| `Concepta` por `Concepto` | Deformación | Usar keywords list en lugar de regex |

## Extracción de campos de comprobantes (facturas, tickets, remitos)

Pipeline validado en Fleet Optimizer AR (Mayo 2026): EasyOCR → regex → fallback LLM local (Ollama).
Ver template en `templates/ocr_comprobantes.py`.

### Arquitectura del pipeline

```
Imagen / PDF  →  PyMuPDF (si PDF)  →  EasyOCR  →  regex  →  Ollama fallback  →  JSON
```

### Campos objetivo (Argentina)

```python
CAMPOS = ["fecha", "numero_comprobante", "monto_total", "cuit", "patente", "concepto"]
```

### PDF → imagen con PyMuPDF (sin dependencias extra)

```python
import fitz  # pymupdf — ya instalado en el servidor

doc = fitz.open(pdf_path)
page = doc[0]
mat = fitz.Matrix(2.0, 2.0)  # 2x zoom ≈ 144 DPI — suficiente para OCR
pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
doc.close()
pix.save(output_png_path)
```

### Regex patterns para comprobantes argentinos

```python
PATRONES_OCR = {
    "fecha": [
        r"\b(\d{1,2})[/\-\.'´`](\d{1,2})[/\-\.'´`](\d{2,4})\b",
        r'\b(\d{1,2})\s+de\s+\w+\s+de\s+(\d{4})\b',
    ],
    "monto_total": [
        r'(?:total|importe|a\s+pagar)[^\d]*\$?\s*([\d\.,]+)',
        r'\$\s*([\d\.,]+)',
    ],
    "numero_comprobante": [
        r'(?:factura|ticket|recibo|N[°o]?)[:\s#]*([A-Z0-9]{1,2}[\s\-]*[\d]{4,}[\-\s]?\d{4,})',
    ],
    "cuit": [r'\b(20|23|24|27|30|33|34)[-\.]?\d{8}[-\.]?\d\b'],
    "patente": [r'\b([A-Z]{2,3}[-\s]?\d{3}[-\s]?[A-Z]{0,2}\d{0,3})\b'],
}
```

### Fallback Ollama para campos no capturados por regex

```python
OLLAMA_URL = "http://localhost:11434/api/generate"

def _llm_fallback(lineas: list, campos: dict, model="qwen2.5:3b") -> dict:
    faltantes = [k for k, v in campos.items() if v is None]
    if not faltantes:
        return campos
    prompt = f"""Sos un extractor de datos de comprobantes argentinos.
Dado el siguiente texto extraído por OCR, devolvé SOLO un JSON con estos campos:
fecha, numero_comprobante, monto_total (número), cuit, patente, concepto
Si un campo no está, poné null. SOLO JSON, sin explicaciones.

TEXTO OCR:
{chr(10).join(lineas)}

JSON:"""
    resp = requests.post(OLLAMA_URL, json={
        "model": model, "prompt": prompt,
        "stream": False, "options": {"temperature": 0, "num_predict": 256}
    }, timeout=30)
    raw = resp.json()["response"]
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        llm_data = json.loads(m.group(0))
        for k in faltantes:
            if k in llm_data and llm_data[k] not in [None, "", "null"]:
                campos[k] = str(llm_data[k]).strip()
    return campos
```

### Limpieza de artefactos OCR comunes

```python
# Comillas/acentos en años: "19/05/'2026" → "19/05/2026"
fecha_clean = re.sub(r"['\"`´]", "", fecha_raw)
# O en ceros: "NOOO1" → "N0001"
nro_clean = re.sub(r'(?<=[A-Z]{2})O', '0', nro_raw)
```

### Endpoint FastAPI completo

```python
@app.post("/api/ocr")
async def ocr_comprobante(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename or 'comprobante'
    suffix = Path(filename).suffix.lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents); tmp_path = tmp.name

    pdf_img_path = None
    try:
        if suffix == '.pdf':
            import fitz
            doc = fitz.open(tmp_path)
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), colorspace=fitz.csRGB)
            doc.close()
            pdf_img_path = tmp_path.replace('.pdf', '_p0.png')
            pix.save(pdf_img_path)
            img_path, img_bytes, mime = pdf_img_path, open(pdf_img_path,'rb').read(), 'image/png'
        else:
            img_path, img_bytes = tmp_path, contents
            mime = "image/jpeg" if suffix in ['.jpg','.jpeg'] else "image/png"

        reader = easyocr.Reader(['es','en'], gpu=False, verbose=False)
        lineas = reader.readtext(img_path, detail=0, paragraph=False)
        campos = _regex_extract(lineas)
        campos = _llm_fallback(lineas, campos)

        return {
            "campos": campos,
            "lineas_ocr": lineas,
            "imagen_b64": f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}",
            "filename": filename,
        }
    finally:
        os.unlink(tmp_path)
        if pdf_img_path and os.path.exists(pdf_img_path): os.unlink(pdf_img_path)
```

### Acepta en el frontend

```jsx
<input type="file" accept="image/*,.pdf" />
```

---

## Pipeline OCR con clasificación dinámica de comprobantes (Fleet / Flota)

Patrón validado en producción para extracción de comprobantes de flota vehicular.

### Arquitectura: Regex → LLM → Merge

```
imagen/PDF → EasyOCR → regex_base (campos universales) → LLM (clasifica tipo + extrae resto) → merge (regex prioridad)
```

**Paso 1 — Regex base (siempre, sin costo):**
- fecha, monto_total, numero_comprobante, cuit, patente
- Rápido, determinístico, nunca alucina

**Paso 2 — LLM (Ollama local, solo si hay faltantes):**
- Clasifica el tipo de documento (`combustible`, `remito`, `peaje`, `multa`, `seguro`, `gomeria`, `mantenimiento`, `estacionamiento`, `factura_general`)
- Extrae los campos específicos de ese tipo
- Modelo: `qwen2.5:3b` (liviano, rápido, bueno para estructurado)
- Prompt único para clasificar Y extraer — un solo call

**Paso 3 — Merge (regex gana):**
- Los campos que regex ya resolvió no se pisan
- El LLM solo completa lo que falta

### PDF → imagen con PyMuPDF (sin pdf2image)

```python
import fitz  # pymupdf — ya instalado como dependencia de otros paquetes

doc = fitz.open(tmp_path)
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), colorspace=fitz.csRGB)  # 2x = ~144 DPI
doc.close()
pix.save(img_path)
```

PyMuPDF está disponible en el servidor y no requiere `pdftoppm`/`poppler`. Usar siempre antes de `pdf2image`.

### Prompt de clasificación + extracción dinámica

El prompt le pasa al LLM:
1. Los tipos disponibles con sus campos
2. Los campos ya resueltos por regex (para no repetirlos)
3. El texto OCR crudo

Respuesta esperada: `{ "tipo": "combustible", "campos": { "litros": "120", ... } }`

### Limpieza de artefactos OCR

EasyOCR introduce comillas y acentos raros en años (`2026` → `'2026`). Limpiar con:
```python
fecha_clean = re.sub(r"['`´\"\\]", "", fecha_raw)
```
Hacer esto tanto en regex como en LLM output.

### Endpoint FastAPI mínimo con soporte JPG/PNG/PDF

```python
@app.post("/api/ocr")
async def ocr_comprobante(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    # PDF → imagen
    if suffix == '.pdf':
        import fitz
        doc = fitz.open(tmp_path)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), colorspace=fitz.csRGB)
        pix.save(img_path)
    # OCR
    reader = easyocr.Reader(['es', 'en'], gpu=False, verbose=False)
    lineas = reader.readtext(img_path, detail=0, paragraph=False)
    campos_regex = _regex_base(lineas)
    llm_result = _llm_classify_and_extract(lineas, campos_regex)
    # ... merge y return
```

### Frontend — mostrar campos dinámicos

El backend devuelve `tipo_label` y `campos` (keys variables según tipo).
El frontend mapea keys → labels con un dict `CAMPO_LABELS` y formatea montos/litros/km.
Incluir barra de completitud: `camposDetectados / totalCampos`.

---

## Double-Pass OCR + LLM (modelos pequeños como qwen2.5:3b)

Cuando el modelo local es pequeño (≤7B), una sola pasada LLM no alcanza para
extraer todos los campos. Patrón probado en Fleet Optimizer (Mayo 2026):

**Pasada 1 — clasificar tipo + extracción genérica:**
```python
def _llm_classify_and_extract(lineas, campos_regex):
    # prompt amplio: detecta el tipo Y extrae lo que puede
    # resultado: {"tipo": "combustible", "campos_llm": {...}}
```

**Pasada 2 — re-parsear solo los campos null con prompt dirigido:**
```python
def _llm_second_pass(lineas, tipo, campos_pendientes):
    """
    Ya conoce el tipo → prompt mucho más corto y específico.
    Incluir FIELD_HINTS por campo para guiar al modelo:
      "litros": "cantidad de litros cargados (número, ej: 120.5)"
    Solo pedir los campos que quedaron null → menor carga cognitiva.
    """
    # usar temperature=0, num_predict=400 (menor que pasada 1)
```

**Trigger:** usar siempre que `campos_null = [c for c, v in campos_finales.items() if v is None]` tenga elementos.

**Estructura del pipeline completo:**
```
EasyOCR → regex_base (fecha, monto, cuit, patente)
  → LLM pasada 1 (clasificar tipo + todos los campos)
  → merge (regex > LLM para campos comunes)
  → LLM pasada 2 (solo campos null, prompt dirigido por tipo)
  → resultado final
```

Ver template completo en `references/double-pass-ocr-pipeline.md`.

## Pitfall CRÍTICO — terminal("cat file") corrompe API keys

**NUNCA leer un archivo con `terminal("cat ...")` para luego reescribirlo.**

El output de `terminal()` censura secretos (`NVIDIA_API_KEY=***`).
Si usás ese output para reescribir el archivo, la línea queda corrupta
y el archivo falla con `SyntaxError: unterminated string literal`.

**Síntoma:** línea como `NVIDIA_API_KEY=os.get...EY")` en el archivo final.

**Solución correcta:**
```python
# Usar Python directo para leer/modificar/escribir
python3 << 'PYEOF'
with open('archivo.py', 'r') as f:
    lines = f.readlines()
# Modificar lines[i] directamente
with open('archivo.py', 'w') as f:
    f.writelines(lines)
PYEOF
```

Nunca usar `execute_code` para leer el archivo con `terminal("cat ...")` y luego
`write_file` — el sandbox también puede censurar valores.

## Pipeline OCR + LLM con doble pasada (documentos de flota)

Patrón probado en Fleet Optimizer para comprobantes argentinos (combustible, remito, peaje, multa, seguro, etc.).

### Arquitectura de tres capas

```
Imagen → EasyOCR (texto crudo) → Regex (campos universales) → LLM pasada 1 (tipo + campos) → LLM pasada 2 (campos null) → campos_finales
```

**Por qué dos pasadas LLM:**
- Modelos chicos (qwen2.5:3b, ollama local) no pueden clasificar el tipo Y extraer todos los campos en un solo prompt
- Pasada 1: clasificar tipo + extraer lo que puede (prompt genérico)
- Pasada 2: ya sabe el tipo → prompt dirigido SOLO a campos null → mejor precisión

### Función second_pass patrón

```python
def _llm_second_pass(lineas: list, tipo: str, campos_pendientes: list) -> dict:
    """Segunda pasada dirigida solo a campos null."""
    if not campos_pendientes:
        return {}

    texto = '\n'.join(lineas)
    schema = TIPO_SCHEMAS[tipo]

    # Hints específicos por campo — clave para modelos chicos
    FIELD_HINTS = {
        "litros": "cantidad de litros cargados (número, ej: 120.5)",
        "precio_por_litro": "precio unitario por litro (número, ej: 1250.00)",
        "tipo_combustible": "diesel, nafta super, nafta premium, GNC, etc.",
        "estacion": "nombre o número de la estación de servicio",
        # ... un hint por campo del schema
    }

    hints_str = '\n'.join(
        f'- {c}: {FIELD_HINTS.get(c, "extraer del texto")}' for c in campos_pendientes
    )

    prompt = f"""Sos un extractor de datos de comprobantes argentinos.
El documento ya fue identificado como: {schema["label"]}

CAMPOS QUE NECESITO EXTRAER:
{hints_str}

TEXTO OCR:
{texto}

Respondé SOLO con JSON plano. null si no aparece.
JSON:"""

    # call a ollama local, timeout=45
    # parsear JSON con re.search(r'\{.*\}', raw, re.DOTALL)
```

### Merge de campos (regex > LLM pasada1 > LLM pasada2)

```python
# Pasada 1 merge
campos_finales = {}
for campo in schema["campos"]:
    if campo in campos_regex and campos_regex[campo] is not None:
        campos_finales[campo] = campos_regex[campo]
    elif campo in campos_llm and campos_llm[campo] not in [None, "", "null"]:
        campos_finales[campo] = campos_llm[campo]
    else:
        campos_finales[campo] = None

# Pasada 2 solo sobre los null
campos_null = [c for c, v in campos_finales.items() if v is None]
if campos_null:
    second_pass = _llm_second_pass(lineas, tipo, campos_null)
    for campo in campos_null:
        val = second_pass.get(campo)
        if val not in [None, "", "null"]:
            campos_finales[campo] = val
```

### Tipos de documentos soportados
`combustible`, `gomeria`, `mantenimiento`, `remito`, `peaje`, `multa`, `seguro`, `estacionamiento`, `factura_general`

Ver implementación completa en `~/brainstorming/2026-05-22-fleet-optimizer/poc/backend/main.py`

---

## Pitfalls

- **execute_code / terminal sanitizan API keys en el output** — si leés un archivo .py con `terminal("cat ...")` o `execute_code`, cualquier valor de variable que parezca una secret (API_KEY, token, etc.) aparece como `***` o truncado. Si luego reescribís el archivo con ese output, la línea queda corrupta. **NUNCA leer archivos con secrets via terminal/execute_code para luego reescribirlos** — usar `read_file` tool directamente y hacer el patch quirúrgico con `sed -i` o Python sobre el archivo.
- Tesseract necesita paquetes de idioma (`tesseract-ocr-spa`)
- OpenCV en Docker necesita `libgl1-mesa-glx` (imagen slim no lo tiene)
- YOLO descarga modelos automaticamente (~6MB para nano, ~80MB para large)
- EasyOCR descarga modelos en primer uso (~100MB)
- Imagenes muy grandes (>10MB) pueden causar OOM; redimensionar primero
- GPT-4V es caro; usar Tesseract/OCR local para texto simple, LLM solo para analisis complejo
- **EasyOCR introduce comillas en años** (`'2026`): siempre limpiar con regex post-OCR
- **PyMuPDF (`fitz`) está disponible sin instalar nada extra** — usarlo para PDF→imagen antes de probar pdf2image
- **qwen2.5:3b** es el mejor modelo local disponible para extracción estructurada (Ollama)
- El campo `gpu=False` en EasyOCR es necesario si CUDA no está configurado para el usuario del proceso; verificar antes de poner `gpu=True`
- **EasyOCR introduce comillas/acentos en números** (`19/05/'2026`) — siempre limpiar con regex antes de guardar
- **Letras O/0 confundidas** en códigos alfanuméricos — aplicar heurística post-OCR
- **PyMuPDF ya viene instalado** en el servidor (no necesita `pdf2image` ni `poppler`)
- **EasyOCR Reader** es pesado de instanciar — en producción, instanciar una vez al startup como singleton, no en cada request
- GPT-4V es caro; usar EasyOCR local + Ollama fallback para extracción de campos sin tokens externos
- Para Ollama fallback: `qwen2.5:3b` es el modelo recomendado — muy bueno en output JSON estructurado, liviano (1.9GB), responde en <3s en este servidor
- **EasyOCR introduce comillas/apostrofes en dígitos** (ej: `'2026` en lugar de `2026`). Los patrones regex de fecha deben incluir variantes con `[/\-\.'´\`]` como separadores, y el LLM fallback también puede resolverlo
- **EasyOCR confunde O con 0** en números de comprobante cuando la calidad de imagen es baja. El fallback LLM mejora este caso pero no lo elimina — la solución definitiva es preprocesar la imagen (contraste, escala)
- **EasyOCR en este servidor corre en CPU** aunque hay GPU: el driver NVIDIA 12020 es incompatible con el torch instalado por easyocr. No bloquea la funcionalidad, solo es más lento (~5s por imagen). Fix: reinstalar torch cu121 después de instalar easyocr
- **pip vs pip3**: en este servidor `pip` no está en PATH, usar siempre `pip3`
- Ver `references/ocr-comprobantes-pipeline.md` para el pipeline completo validado de extracción de comprobantes de flota
- Ver sección VLM arriba para pitfalls específicos de clasificación por lote con LLM
