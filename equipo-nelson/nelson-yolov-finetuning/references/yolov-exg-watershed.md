# ExG + Watershed — Detector sin ML para copas individuales

## Por qué Watershed

ExG básico detecta manchas verdes contiguas, no copas individuales.
Un bosque denso → 1 sola detection gigante en lugar de N copas separadas.
Watershed resuelve esto encontrando los "picos" de cada copa dentro de la mancha.

## Código completo (pipeline/exg_detector.py)

```python
import cv2, numpy as np, os, time

def exg_mask(rgb, threshold=0.12):
    r,g,b = rgb[:,:,0].astype(float), rgb[:,:,1].astype(float), rgb[:,:,2].astype(float)
    tot = r + g + b + 1e-9
    exg = 2*(g/tot) - (r/tot) - (b/tot)
    mask = (exg > threshold).astype(np.uint8) * 255
    k_open  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k_open)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close)
    return mask

def watershed_crowns(mask, min_area=400, max_area=15000, min_side=18, max_side=200):
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)
    _, sure_fg = cv2.threshold(dist, 0.35, 1.0, cv2.THRESH_BINARY)
    sure_fg = np.uint8(sure_fg * 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    sure_bg = cv2.dilate(mask, kernel, iterations=2)
    unknown = cv2.subtract(sure_bg, sure_fg)
    _, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[unknown == 255] = 0
    bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    cv2.watershed(bgr, markers)
    boxes = []
    for label in range(2, markers.max() + 1):
        region = (markers == label).astype(np.uint8)
        coords = cv2.findNonZero(region)
        if coords is None: continue
        x, y, w, h = cv2.boundingRect(coords)
        area = w * h
        if area < min_area or area > max_area: continue
        if w < min_side or h < min_side: continue
        if w > max_side or h > max_side: continue
        ratio = w / max(h, 1)
        if ratio > 2.8 or ratio < 0.36: continue
        boxes.append((x, y, x+w, y+h))
    return boxes

def run_exg_inference(tiles, tiles_dir, exg_threshold=0.12, min_area=400, max_area=15000):
    all_detections, t0 = [], time.time()
    for tile in tiles:
        img = cv2.imread(os.path.join(tiles_dir, tile["filename"]))
        if img is None: continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mask = exg_mask(rgb, threshold=exg_threshold)
        boxes = watershed_crowns(mask, min_area=min_area, max_area=max_area)
        for (x1,y1,x2,y2) in boxes:
            all_detections.append({
                "tile_filename": tile["filename"],
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "global_x1": int(tile["x0"])+x1, "global_y1": int(tile["y0"])+y1,
                "global_x2": int(tile["x0"])+x2, "global_y2": int(tile["y0"])+y2,
                "confidence": 0.90,
            })
    return all_detections, time.time() - t0
```

## Integración en yolo_service.py

```python
from pipeline.exg_detector import run_exg_inference

VALID_MODELS = list(SUPPORTED_MODELS.keys()) + ["exg"]

# En run_pipeline():
if model_key == "exg":
    detections_raw, elapsed = run_exg_inference(tiles_meta, tiles_dir)
    detections = nms_global(detections_raw, iou_threshold=nms_iou, centroid_dist_px=centroid_dist_px)
else:
    model = load_model(model_key)
    detections_raw, elapsed = run_inference(...)
    detections = nms_global(...)
```

## Resultados verificados — 9deJulio.rgb.tif (2026-06-11)

| Variante | centroid | árboles | tiempo | observación |
|----------|---------|---------|--------|-------------|
| ExG sin WS | 200 | 880 | 2.4s | cajas grandes, mezcla zonas |
| ExG+WS | 90 | 323 | 6.3s | copas individuales limpias |

## Limitaciones en zona URBANA (9deJulio)

- **Detecta personas con ropa colorida** como vegetación (ropa rosa/rojo → ExG bajo pero verde en contexto)
- **Detecta vehículos** de colores similares al verde
- ExG es un índice de COLOR, no de "árbol" — no tiene concepto de copa arbórea
- **Recomendación:** usar en bosque nativo rural sin infraestructura, NO en ortofotos urbanas

## ModelSelector defaults (frontend)

```typescript
const MODEL_DEFAULTS = {
  yolo11n_forestai: { centroid: 90, conf: 0.65, tile_size: 640  },
  exg:              { centroid: 90, conf: 0.50, tile_size: 1024 },
  yolo11n:          { centroid: 60, conf: 0.25, tile_size: 640  },
  yolov8n:          { centroid: 60, conf: 0.25, tile_size: 640  },
}
function handleModelChange(key) {
  setModelKey(key)
  const d = MODEL_DEFAULTS[key]
  if (d) { setConf(d.conf); setCentroid(d.centroid); setTileSize(d.tile_size) }
}
```

## PITFALL — TypeScript build falla con variables sin usar

`tsc` con `noUnusedLocals` activo rechaza variables declaradas pero no referenciadas.
Si se remueve una constante pero otra la reemplaza, verificar que la vieja esté eliminada.
Error: `TS6133: 'DEFAULT_CONF' is declared but its value is never read`
Fix: borrar la constante del archivo o prefijar con `_`.
