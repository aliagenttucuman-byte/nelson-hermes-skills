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

## Dependencias

```bash
pip install pytesseract pillow opencv-python-headless easyocr
pip install ultralytics  # YOLO (pesado, descarga modelos)
pip install openai       # Para vision LLM
# pip install torch torchvision  # Para CLIP (opcional, muy pesado)
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

## Pitfalls

- Tesseract necesita paquetes de idioma (`tesseract-ocr-spa`)
- OpenCV en Docker necesita `libgl1-mesa-glx` (imagen slim no lo tiene)
- YOLO descarga modelos automaticamente (~6MB para nano, ~80MB para large)
- EasyOCR descarga modelos en primer uso (~100MB)
- Imagenes muy grandes (>10MB) pueden causar OOM; redimensionar primero
- GPT-4V es caro; usar Tesseract/OCR local para texto simple, LLM solo para analisis complejo
