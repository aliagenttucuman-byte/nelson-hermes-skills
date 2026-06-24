# YOLO11 + SAM 2 — Spike de Upgrade del Módulo de Detección

**Fecha inicio:** 2026-06-10
**Proyecto:** `~/brainstorming/2026-06-10-forestai-yolo11-detection/`
**Origen:** Ultralytics AI in Agriculture — https://www.ultralytics.com/solutions/ai-in-agriculture

---

## Motivación

ForestAI hoy usa ExG + OpenCV contornos para detectar copas. Limitaciones:
- Recall bajo en zonas con sombra
- Pierde árboles jóvenes con copa pequeña
- Rule-based: no aprende de los datos locales

YOLO11 + SAM 2 de Ultralytics ofrece:
- Detección neuronal entrenada por imagen aérea
- SAM 2: segmentación pixel-a-pixel de copas
- Native drone integration mencionado explícitamente por Ultralytics
- Métricas: 95%+ accuracy crop disease detection (comparable al tree detection)

---

## Fase 1 — Baseline completada (2026-06-10)

### TIFs de referencia disponibles

Ubicados en `/home/server/proyectos/forestai-poc/uploads/`:

| Archivo | Dimensiones | Res | Bandas | CRS | Tamaño |
|---------|-------------|-----|--------|-----|--------|
| `055422ad...tif` | 6325×7011px | 2cm/px | 3 (RGB) | EPSG:32721 | 8.7MB |
| `029a29f5...tif` | 12695×12687px | ~1cm/px | 3 (RGB) | EPSG:4326 | 13.8MB |
| `f96fd29a...tif` | 9307×8056px | 2cm/px | 3 (RGB) | EPSG:32719 | 24.0MB |
| `eb46a038...tif` | 18990×13321px | 2.25cm/px | 3 (RGB) | EPSG:32721 | 32.1MB |
| `b4c61bc0...tif` | 14431×13824px | ~1cm/px | 3 (RGB) | EPSG:4326 | 32.1MB |

**Tiles cortados para el spike** (1024×1024px, desde `055422ad`):
- `tile_A`: offset (500,500) — 59.6% vegetación
- `tile_B`: offset (2800,3000) — 67.6% vegetación
- `tile_C`: offset (4000,1500) — 74.0% vegetación

### Resultados ExG baseline

| Tile | Árboles ExG | Tiempo | Veg% |
|------|-------------|--------|------|
| tile_A | 38 | 65ms | 59.6% |
| tile_B | 12 | 30ms | 67.6% |
| tile_C | 22 | 22ms | 74.0% |

Muy rápido (CPU puro), pero rule-based.

### Resultado YOLO11n pre-trained (COCO)

| Tile | Detecciones | Clases encontradas |
|------|-------------|-------------------|
| tile_A | 1 | bear (!) |
| tile_B | 0 | ninguna |
| tile_C | 1 | umbrella (!) |

**Conclusión esperada:** YOLO11 pre-trained en COCO NO detecta árboles en ortofotos aéreas.
Fine-tuning con imágenes de Tucumán es NECESARIO para comparación real.

---

## Fase 2 — Fine-tuning (PENDIENTE)

### Plan
1. Anotar 50-100 árboles sobre los tiles de Tucumán
   - Opción A: Label Studio en Docker (visual, manual)
   - Opción B: anotaciones semi-automáticas desde ExG (JARVIS genera, Nelson corrige)
2. Fine-tune `yolo11n.pt` (nano, más rápido) sobre esas anotaciones
3. Evaluar: Precision / Recall / F1 sobre tiles de validación

### Formato de anotación YOLO
```
# archivo: tile_A.txt
# clase cx_norm cy_norm w_norm h_norm  (normalizados 0-1)
0 0.423 0.651 0.089 0.094
0 0.201 0.334 0.067 0.071
...
```
Clase 0 = "tree". Solo una clase.

### Comando fine-tuning
```bash
# Desde el directorio del spike
python3 -m ultralytics yolo detect train \
  model=yolo11n.pt \
  data=spike/data/dataset.yaml \
  epochs=50 \
  imgsz=1024 \
  batch=4 \
  project=spike/outputs/fine_tuning \
  name=tucuman_v1
```

### dataset.yaml
```yaml
path: /home/server/brainstorming/2026-06-10-forestai-yolo11-detection/spike/data
train: images/train
val: images/val
nc: 1
names: ['tree']
```

---

## Fase 3 — SAM 2 para copas (PENDIENTE)

Usar detecciones YOLO11 fine-tuned como "prompts" (bounding boxes) para SAM 2.
SAM 2 genera máscaras precisas de copa dentro de cada bbox.

```python
from ultralytics import SAM

model_sam = SAM("sam2.1_b.pt")  # SAM 2.1 base

# Para cada detección YOLO11, pedir máscara a SAM 2
results = model_sam(img_bgr, bboxes=yolo_bboxes)
# results[0].masks → máscaras poligonales por copa
```

### Comparar vs. SAM 1 actual en ForestAI
ForestAI ya usa SAM 1 (`sam_vit_b.pth`) en el pipeline DeepForest → SAM.
SAM 2 es más rápido y más preciso. Evaluar si vale migrar.

---

## Integración en ForestAI (si Fase 2 valida)

Nuevo módulo: `backend/app/services/yolo11_detector.py`
- Misma interfaz que `tree_detection.py` (retorna DataFrame con copas)
- Feature flag: `USE_YOLO11=true` en `.env`
- Mantener ExG+OpenCV como fallback

---

## Scripts del spike

```
spike/
├── 01_baseline_exg.py         ← ExG+OpenCV → JSON ✅ corrido
├── 02_yolo11_pretrained.py    ← YOLO11 COCO → JSON ✅ corrido
├── 03_finetune_yolo11.py      ← Fine-tuning (pendiente Fase 2)
├── 04_sam2_copas.py           ← SAM 2 sobre dets YOLO11 (pendiente Fase 3)
├── 05_metricas_comparacion.py ← Comparación final (pendiente)
├── data/tiles/                ← tile_A/B/C.tif ✅ generados
└── outputs/
    ├── detecciones_exg/       ← ✅ tile_A/B/C_exg.json
    ├── detecciones_yolo11/    ← ✅ tile_A/B/C_yolo11n.json
    └── spike_fase1_resultado.jpg ← ✅ imagen comparativa
```

---

## Pitfall — ultralytics se instala en python3 del sistema (no en venv)

```bash
python3 -m pip install ultralytics
# pip a secas no existe como comando — usar python3 -m pip
```

Verificar instalación:
```bash
python3 -c "from ultralytics import YOLO; print('OK')"
```

## Pitfall — YOLO11 descarga el modelo en el directorio actual

`YOLO('yolo11n.pt')` descarga `yolo11n.pt` en el CWD si no existe.
Si corrés desde `/home/server`, el modelo queda ahí. Moverlo o especificar path absoluto:

```python
model = YOLO('/home/server/.cache/ultralytics/yolo11n.pt')
```

## Pitfall — cv2.COLORMAP_RdYlGn no existe

OpenCV en el servidor no tiene `COLORMAP_RdYlGn`. Usar `COLORMAP_SUMMER` o `COLORMAP_JET` como alternativa para heatmaps de vegetación.

```python
# ❌ cv2.COLORMAP_RdYlGn  — no existe
# ✅ cv2.COLORMAP_SUMMER   — verde→amarillo, legible
# ✅ cv2.COLORMAP_JET      — azul→rojo, clásico
exg_color = cv2.applyColorMap(exg_norm, cv2.COLORMAP_SUMMER)
```

---

## Imagen resultado Fase 1

`spike/outputs/spike_fase1_resultado.jpg` — 2048×3326px
Muestra los 3 tiles con detecciones ExG superpuestas (círculos verdes) + heatmap ExG.
