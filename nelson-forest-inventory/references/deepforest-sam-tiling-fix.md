# DeepForest + SAM — Fix Tiling para TIFFs Grandes

## KPIs prioritarios para ReforestLatam

1. **Conteo de copas** — cuántos árboles hay en el área
2. **Identificación de especie** — qué árbol es cada copa (NetFlora)

Pipeline: **DeepForest → SAM → NetFlora**

## Stack instalado en forestai-poc-backend-1

| Componente | Versión | Detalle |
|---|---|---|
| deepforest | 2.1.0 | modelo `weecology/deepforest-tree` (se descarga en primer run) |
| segment-anything | 1.0 | SAM ViT-B, checkpoint `/tmp/sam_models/sam_vit_b.pth` |
| NetFlora | YOLOv5 | `/app/netflora_repo/detect.py` — especies tropicales/subtropicales |

Endpoints:
- `POST /api/tree-detection/upload` — multipart, acepta PNG/JPG/TIFF
- `POST /api/tree-detection/run` — demo con imagen NEON incluida en deepforest

## PITFALL CRÍTICO — TIFFs grandes (>178M px) → error 400 "decompression bomb"

PIL rechaza imágenes de más de 178,956,970 px.
Ortomosaicos de drone a 6 cm/px: 17094×11327px = **193M px** → boom.

### Fix aplicado (2026-06-09)

**`backend/app/services/tree_detection.py`:**

```python
PIL_MAX_PIXELS = 178_956_970
TILE_SIZE = 4096

def _tile_and_detect(image_path, model):
    """Divide TIFF en tiles 4096×4096 con rasterio, corre DeepForest en cada
    uno, suma offset de coordenadas globales y consolida en DataFrame único."""
    import rasterio
    from rasterio.windows import Window
    all_rows = []
    with rasterio.open(image_path) as src:
        W, H = src.width, src.height
    for y0 in range(0, H, TILE_SIZE):
        for x0 in range(0, W, TILE_SIZE):
            tw, th = min(TILE_SIZE, W-x0), min(TILE_SIZE, H-y0)
            with rasterio.open(image_path) as src:
                data = src.read([1,2,3], window=Window(x0, y0, tw, th))
            rgb = np.transpose(data, (1,2,0)).astype(np.uint8)
            # guardar tile temp, correr DeepForest, sumar offset
            ...
            preds["xmin"] += x0; preds["xmax"] += x0
            preds["ymin"] += y0; preds["ymax"] += y0
            all_rows.append(preds)
    return pd.concat(all_rows), W, H

def run_tree_detection(image_path=None):
    ...
    Image.MAX_IMAGE_PIXELS = None  # para leer dimensiones sin crash
    with Image.open(image_path) as img: w, h = img.size
    Image.MAX_IMAGE_PIXELS = PIL_MAX_PIXELS  # restaurar

    if w * h > PIL_MAX_PIXELS:
        predictions, w, h = _tile_and_detect(image_path, model)
    else:
        predictions = model.predict_image(path=image_path)
```

**`backend/app/api/v1/tree_detection.py`** — en el endpoint upload, antes de llamar al servicio:
```python
from PIL import Image as _PILImage
_PILImage.MAX_IMAGE_PIXELS = None  # el servicio lo maneja internamente
```

## Datos de ortomosaicos Tucumán (caso real 2026-05-16)

| Archivo | Tamaño | Dimensiones | Bandas | CRS | Resolución | Software |
|---|---|---|---|---|---|---|
| 9deJulio.rgb.tif | 59MB | 17094×11327 | 4 (RGBA) uint8 | EPSG:32720 | ~6 cm/px | Pix4Dfields 2.12.1 |
| Avellaneda.rgb.tif | 36MB | 12622×7887 | 4 (RGBA) uint8 | EPSG:32720 | ~6 cm/px | Pix4Dfields 2.12.1 |

**Son RGB, NO multiespectrales** → NDVI no aplicable. Usar VARI/ExG para índices de vegetación.

## Resultado real con 9deJulio.rgb.tif

- 154 árboles detectados (TIFF completo, tiling automático)
- sam_used=True, sam_score ~0.95, stability_score ~0.98
- Tiempo de procesamiento: ~4.5 minutos (12 tiles de 4096px)
- vlm_species=null (NetFlora no corrió aún — necesita API key o integración directa)

## Notas de integración con la UI

- `TreeDetectionPanel.tsx` ya tiene canvas interactivo con polígonos SAM, hover por copa, sliders de threshold
- La imagen anotada se devuelve como base64 en `annotated_image_b64`
- Para TIFFs grandes la imagen anotada pesa ~247MB en b64 → considerar thumbnail (2048px) para el preview del browser
- El frontend acepta TIFF directo desde file input — no hace falta convertir a JPG antes
