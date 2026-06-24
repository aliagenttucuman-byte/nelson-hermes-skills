# YOLO11 Fine-Tuning con ExG Pseudo-Labels — ForestAI (Junio 2026)

## Objetivo

Entrenar YOLO11n especializado en detección de copas de árboles en ortofotos RGB de Tucumán,
usando ExG (Excess Green) como generador automático de anotaciones (pseudo-labeling).

---

## Pipeline de datos

### Paso 1 — Generar anotaciones ExG → YOLO

```python
import rasterio, cv2, numpy as np, os

def exg_to_yolo_labels(tile_path, min_area=80, max_area=50000):
    """Genera bounding boxes en formato YOLO desde ExG."""
    with rasterio.open(tile_path) as src:
        data = src.read()
    r = data[0].astype(float)
    g = data[1].astype(float)
    b = data[2].astype(float)
    H, W = r.shape
    total = r + g + b + 1e-9
    exg = 2*(g/total) - (r/total) - (b/total)
    mask = (exg > 0.12).astype(np.uint8)*255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    labels = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        x,y,w,h = cv2.boundingRect(cnt)
        cx_n = (x + w/2) / W
        cy_n = (y + h/2) / H
        w_n  = w / W
        h_n  = h / H
        labels.append(f"0 {cx_n:.6f} {cy_n:.6f} {w_n:.6f} {h_n:.6f}")
    return labels, W, H
```

Parámetros:
- `min_area=120` — filtra ruido (hojas sueltas, reflejos)
- `max_area=30000` — filtra sombras y fondos grandes
- `kernel 7x7` MORPH_OPEN + MORPH_CLOSE — conecta copas fragmentadas

### Paso 2 — Extraer tiles con stride (múltiples por imagen)

```python
tile_size = 1024
stride = 768  # overlap de 256px

for row in range(0, H-tile_size, stride):
    for col in range(0, W-tile_size, stride):
        tile_rgb = rgb[row:row+tile_size, col:col+tile_size]
        boxes = exg_boxes(tile_rgb)
        if len(boxes) < 5:  # skip tiles sin vegetación
            continue
        all_pairs.append((tile_rgb, boxes, f'{name}_r{row//100}_c{col//100}'))
```

Con 4 TIFFs (9deJulio, Avellaneda, tucuman_A, tucuman_C) → 24 tiles base.

### Paso 3 — Augmentación manual (8x)

```python
variants = [
    bgr,                              # original
    cv2.flip(bgr, 1),                 # flip horizontal
    cv2.flip(bgr, 0),                 # flip vertical
    cv2.flip(bgr, -1),                # flip ambos
    cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE),
    cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE),
    np.clip(bgr.astype(float)*1.2, 0, 255).astype(np.uint8),  # +brillo
    np.clip(bgr.astype(float)*0.8, 0, 255).astype(np.uint8),  # -brillo
]
```

Ajuste de boxes para flip/rotate:
```python
def flip_boxes(boxes, flip_code):
    for cx,cy,w,h in boxes:
        if flip_code == 1:  cx = 1.0 - cx
        elif flip_code == 0: cy = 1.0 - cy
        elif flip_code == -1: cx = 1.0 - cx; cy = 1.0 - cy
        yield (cx, cy, w, h)

def rotate90_boxes(boxes, direction='cw'):
    for cx,cy,w,h in boxes:
        if direction == 'cw':    yield (1.0-cy, cx, h, w)
        else:                    yield (cy, 1.0-cx, h, w)
```

24 tiles × 8 augmentaciones = **152 imágenes de train**.

### Paso 4 — Estructura YOLO + data.yaml

```
dataset_v2/
├── images/
│   ├── train/  # 152 imágenes JPG
│   └── val/    # 5 imágenes (originales sin augmentación)
└── labels/
    ├── train/  # .txt con boxes YOLO
    └── val/
```

```yaml
# data.yaml
path: /path/to/dataset_v2
train: images/train
val: images/val
nc: 1
names: ['tree']
```

---

## Fine-tuning YOLO11n

### Configuración v1 (fallida — dataset insuficiente)

```python
model.train(
    data='dataset/data.yaml',
    epochs=50,
    imgsz=1024,   # ← PROBLEMA: muy grande para CPU
    batch=2,      # ← PROBLEMA: batch muy pequeño
    device='cpu',
    ...
)
```

**Resultado v1:**
- mAP50: 0.0017 (inservible)
- mAP50-95: 0.0006
- Detecciones post-entrenamiento: 0 en todos los tiles
- Causa: 5 tiles, imgsz 1024 en CPU, batch=2 → no convergió

### Configuración v2 (correcta — 152 imágenes)

```python
from ultralytics import YOLO

model = YOLO('yolo11n.pt')
results = model.train(
    data='dataset_v2/data.yaml',
    epochs=80,
    imgsz=640,       # ← CLAVE: 640 mucho más eficiente en CPU
    batch=8,         # ← CLAVE: batch mayor = gradientes más estables
    device='cpu',
    project='runs',
    name='forestai_v2',
    patience=20,     # early stopping con más paciencia
    lr0=0.005,       # lr más bajo para evitar divergencia
    lrf=0.01,
    augment=True,    # augmentación interna YOLO además de la manual
    flipud=0.5,      # válido para ortofotos (sin up/down semántico)
    fliplr=0.5,
    mosaic=0.8,
    degrees=15,
    translate=0.1,
    scale=0.3,
    verbose=False,
    exist_ok=True,
)
```

---

## PITFALLS

### PITFALL 1 — Dataset de 5 tiles = inservible para YOLO11

YOLO11 necesita mínimo ~50-100 imágenes de entrenamiento para aprender features.
Con 5 tiles → mAP50 ~0.001, recall ~0%, sin detecciones post-entrenamiento.
**Solución:** extraer múltiples tiles por imagen + augmentación agresiva (8x).

### PITFALL 2 — imgsz 1024 con batch=2 en CPU diverge

Con imgsz=1024 el modelo procesa crops de 1024px. En CPU sin GPU, batch=2 produce
gradientes ruidosos y entrenamiento muy lento (>10 min/epoch para 5 imágenes).
**Solución:** imgsz=640 + batch=8. YOLO redimensiona internamente — no se pierde información.

### PITFALL 3 — Anotaciones ExG tienen ruido significativo

ExG detecta cualquier verde: sombras verdes, auto verde, pasto, techo verde.
Con umbral ExG=0.12, min_area=80, max_area=50000 → ruido significativo en tiles urbanos.
**Mejoras:**
- min_area=120 (más conservador)
- max_area=30000 (excluye sombras grandes)
- kernel 7x7 en lugar de 5x5 (cierra fragmentos de copa mejor)
- Skip tiles con <5 boxes (tiles sin vegetación real)

### PITFALL 4 — Early stopping muy agresivo con patience=15 en dataset chico

Con pocas imágenes, el mAP fluctúa mucho entre epochs. patience=15 dispara
EarlyStopping antes de que el modelo realmente converja.
**Solución:** patience=20 mínimo, 25 preferible.

### PITFALL 5 — imgsz debe matchear el tile_size del dataset

Si entrenas con imgsz=640 pero las imágenes son 1024px, YOLO escala internamente.
Mejor alinear: si los tiles son 1024px, usar imgsz=1024 solo con GPU (batch≥8).
En CPU: forzar imgsz=640 y aceptar el rescaling.

---

## Evaluación post-entrenamiento

```python
# Leer métricas del CSV generado por YOLO
import csv
rows = list(csv.DictReader(open(f'{save_dir}/results.csv')))
best = max(rows, key=lambda r: float(r.get('metrics/mAP50(B)', 0) or 0))
print(f"mAP50:     {float(best['metrics/mAP50(B)']):.4f}")
print(f"mAP50-95:  {float(best['metrics/mAP50-95(B)']):.4f}")
print(f"Precision: {float(best['metrics/precision(B)']):.4f}")
print(f"Recall:    {float(best['metrics/recall(B)']):.4f}")
```

```python
# Comparar detecciones YOLO vs ExG baseline
from ultralytics import YOLO
model = YOLO('runs/forestai_v2/weights/best.pt')
for img_path, name, exg_n in tiles:
    results = model(img_path, verbose=False, conf=0.25)
    n_det = len(results[0].boxes) if results[0].boxes else 0
    delta = n_det - exg_n
    print(f"  {name}: YOLO11={n_det}  ExG={exg_n}  delta={delta:+d}")
```

Umbral mínimo de éxito: **mAP50 > 0.50** para considerar el modelo funcional.

---

## Roadmap YOLO11 fine-tuning ForestAI

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1 | ExG pseudo-labels automáticos | ✅ Implementado |
| 2 | Dataset v2 con augmentación (152 imgs) | ✅ Generado |
| 3 | Fine-tuning v2 (80 epochs, imgsz=640) | 🔄 En curso (CPU) |
| 4 | Validar mAP50 > 0.50 | ⏳ Pendiente |
| 5 | Si no converge: anotación manual con LabelStudio (~50 tiles) | ⏳ Pendiente |
| 6 | Integrar modelo en ForestAI como alternativa a DeepForest | ⏳ Pendiente |

---

## Alternativa si YOLO11 no converge: LabelStudio

Si mAP50 < 0.3 con el dataset v2:
1. Instalar LabelStudio: `pip install label-studio && label-studio start`
2. Exportar tiles JPG como proyecto YOLO en LabelStudio
3. Anotar manualmente ~50 tiles (2-3 horas de trabajo)
4. Re-entrenar con anotaciones manuales (mucho mejor calidad)

LabelStudio soporta formato YOLO nativo en export.

---

## Paths relevantes

- Dataset v2: `/home/server/brainstorming/2026-06-10-forestai-yolo11-detection/spike/dataset_v2/`
- Modelo v1 (fallido): `/home/server/.hermes/hermes-agent/runs/detect/runs/forestai_v1/weights/best.pt`
- Modelo v2 (en training): `spike/runs/forestai_v2/weights/best.pt`
- TIFFs Tucumán: `/home/server/.hermes/document_cache/doc_*_9deJulio.rgb.tif` y `Avellaneda.rgb.tif`
- TIFFs proyecto: `/home/server/proyectos/forestai-poc/uploads/*.tif`
