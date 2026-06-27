# YOLO11 vs ExG+OpenCV Spike — ForestAI (2026-06-10)

## Contexto

Spike iniciado después de evaluar Ultralytics AI in Agriculture:
https://www.ultralytics.com/solutions/ai-in-agriculture

Proyecto: `~/brainstorming/2026-06-10-forestai-yolo11-detection/`

## Motivación

ForestAI usa ExG (Excess Green Index) + OpenCV contornos para detectar árboles.
Limitaciones conocidas:
- Recall bajo en zonas con sombra
- Pierde árboles jóvenes/pequeños
- Rule-based, no aprende de los datos

Ultralytics YOLO11 + SAM 2 ofrece:
- Detección neuronal (95%+ en benchmark agricultura)
- SAM 2: segmentación pixel-a-pixel de copas
- Integración nativa con drones
- Fine-tuning posible con imágenes locales

## Stack instalado

```bash
python3 -m pip install ultralytics  # OK en ai-server
# ultralytics OK — se autoinstaló YOLO11n.pt (~5.4MB) al primer uso
```

## Tiles de prueba disponibles

### Set 1 — ortofoto 055422ad (2cm/px, EPSG:32721)

| Tile    | Offset    | ExG árboles | Veg %  |
|---------|-----------|-------------|--------|
| tile_A  | (500,500) | 38          | 59.6%  |
| tile_B  | (2800,3000)| 12         | 67.6%  |
| tile_C  | (4000,1500)| 22         | 74.0%  |

Path: `spike/data/tiles/*.tif`

### Set 2 — ortofotos Tucumán (6cm/px, EPSG:32720, 4 bandas RGBA)

| Ortofoto    | Dims orig      | ExG árboles (tile centro) | Veg %  |
|-------------|----------------|--------------------------|--------|
| 9deJulio    | 17094×11327    | 56                       | 42.5%  |
| Avellaneda  | 12622×7887     | 96                       | 38.1%  |

Path: `spike/data/tiles_nuevas/*.tif`

**IMPORTANTE:** Los paths en document_cache cambian con cada envío por WhatsApp.
Siempre buscar con: `ls /home/server/.hermes/document_cache/*.tif`

## Resultado Fase 1

### ExG+OpenCV baseline
- Tiempo: 19-65ms por tile (CPU puro)
- ExG threshold: 0.12 (12%)
- Morfología: MORPH_OPEN + MORPH_CLOSE con kernel elíptico 5x5
- Filtro mínimo área: 100px

### YOLO11n pre-trained (COCO)
- YOLO11n.pt: 5.4MB, descarga automática de GitHub
- Resultado: **NO detecta árboles**
  - tile_A: 1 detección — "bear" (oso)
  - tile_B: 0 detecciones
  - tile_C: 1 detección — "umbrella" (paraguas)
- Conclusión esperada: COCO no tiene clases de árboles aéreos → fine-tuning NECESARIO

## Plan fases pendientes

### Fase 2 — Fine-tuning YOLO11n
1. Anotar 50-100 árboles en 5-10 tiles (Label Studio en Docker o semi-auto con ExG)
2. Formato YOLO: `class cx cy w h` (normalizado 0-1)
3. Fine-tuning: `yolo train model=yolo11n.pt data=forest.yaml epochs=50`
4. Evaluar: Precision/Recall/F1 vs ExG baseline

### Fase 3 — SAM 2 para copas
- Usar bboxes YOLO11 como "prompts" para SAM 2
- SAM 2 genera máscaras precisas de copa
- Calcular área de copa más precisa que morfología actual

## Script de comparación reutilizable

```python
# Patrón ExG baseline — reutilizar en futuros spikes
import rasterio, cv2, numpy as np

def exg_detect_tile(tif_path, threshold=0.12, min_area=100):
    with rasterio.open(tif_path) as src:
        img = src.read()  # (C, H, W)
    r = img[0].astype(float); g = img[1].astype(float); b = img[2].astype(float)
    total = r + g + b + 1e-9
    exg = 2*(g/total) - (r/total) - (b/total)
    mask = (exg > threshold).astype(np.uint8)*255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [cnt for cnt in contours if cv2.contourArea(cnt) >= min_area]

# Patrón YOLO11 inference
from ultralytics import YOLO
model = YOLO('yolo11n.pt')  # o 'yolo11n_forestai.pt' post fine-tuning
results = model(bgr_image, verbose=False, conf=0.25)
```

## Pitfalls descubiertos

1. **COLORMAP_RdYlGn no existe en OpenCV** — usar COLORMAP_SUMMER como alternativa para heatmap ExG
2. **Ortofotos RGBA (4 bandas)** — ignorar la 4ta banda (Alpha) al convertir a RGB para YOLO/OpenCV
3. **YOLO11 pre-trained falla silenciosamente** — no da error, detecta clases COCO incorrectas. Siempre verificar `by_class` en output
4. **document_cache paths no son estables** — el hash en el nombre cambia cada vez que Nelson envía el archivo. No hardcodear rutas

## Comparación de enfoques final esperada

| Aspecto        | ExG + OpenCV    | YOLO11 fine-tuned    |
|---------------|-----------------|----------------------|
| Recall sombra  | Bajo            | Alto                 |
| Árboles jóvenes| Limitado        | Mejor                |
| Setup          | Zero            | ~1 semana            |
| Compute        | CPU, ~20ms/tile | CPU lento, GPU ideal |
| Costo          | Free            | Free (OSS)           |
