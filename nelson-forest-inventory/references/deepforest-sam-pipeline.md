# DeepForest + SAM — Pipeline de Detección de Copas

Referencia técnica del pipeline Image Analytics implementado en sesión 14.

## Recursos oficiales

- Repo: `github.com/weecology/DeepForest`
- Tutorial SAM: `github.com/weecology/DeepForest-SAM`
- HuggingFace: `huggingface.co/spaces/weecology/deepforest-tutorial6-sam`
- Modelo: `weecology/deepforest-tree` (se descarga automáticamente en primera llamada)

## Instalación

```bash
pip install deepforest>=1.3.3 segment-anything supervision>=0.20.0
# En Docker también agregar:
# torch>=2.0.0 torchvision>=0.15.0 Pillow>=10.0.0
```

## Fase 1 — DeepForest: detección de bounding boxes

```python
from deepforest import main as df_main
from deepforest.utilities import get_data

m = df_main.deepforest()
m.load_model(model_name="weecology/deepforest-tree", revision="main")

# Imagen pequeña (<2000px): predict_image
predictions = m.predict_image(path="imagen.png")

# Imagen grande / ortomosaico / GeoTIFF: predict_tile (tile automático)
predictions = m.predict_tile(path="ortofoto.tif", patch_size=400, patch_overlap=0.05)

# Output: pandas DataFrame con columnas:
#   xmin, ymin, xmax, ymax (px), label ("Tree"), score (0-1)
# Si input es GeoTIFF: GeoDataFrame con columna geometry en coords geográficas
# Guardar GeoPackage: predictions.to_file("resultado.gpkg")
```

## Fase 2 — SAM: segmentación de polígonos por copa

```python
import cv2
import numpy as np
import torch
from segment_anything import sam_model_registry, SamPredictor

# Cargar SAM (model_type: vit_h = más preciso, vit_b = más rápido)
sam_checkpoint = "sam_vit_h_4b8939.pth"  # descargar de meta-research/segment-anything
model_type = "vit_h"
device = "cuda" if torch.cuda.is_available() else "cpu"

sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
sam.to(device=device)
predictor = SamPredictor(sam)

# Preparar imagen
image = cv2.imread("imagen.png")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
predictor.set_image(image)

# Para cada bbox de DeepForest, obtener máscara
masks = []
for _, row in predictions.iterrows():
    input_box = np.array([row["xmin"], row["ymin"], row["xmax"], row["ymax"]])
    mask, score, logit = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=input_box[None, :],   # shape: (1, 4)
        multimask_output=False,
    )
    masks.append(mask[0])  # mask es bool array del mismo tamaño que la imagen

# Output: lista de binary masks — True=árbol, False=fondo
```

## Pipeline combinado completo

```
Imagen (PNG/JPG/GeoTIFF)
  ↓ DeepForest (RetinaNet pre-entrenado NEON)
  → DataFrame: [xmin, ymin, xmax, ymax, score] por árbol
  ↓ SAM (ViT-H, zero-shot)
  → binary mask por cada bbox
  → contorno del polígono de copa (cv2.findContours)
  → GeoJSON polygon si hay georreferencia
```

## Arquitectura de la solapa "Detección IA" en ForestAI

### Backend

```
backend/app/services/tree_detection.py   # lógica: download sample, run model, draw results
backend/app/api/v1/tree_detection.py     # endpoints FastAPI
```

**Endpoints:**
- `POST /api/tree-detection/run` → detección sobre imagen de prueba NEON
- `POST /api/tree-detection/upload` → detección sobre imagen subida por el usuario
- `GET /api/tree-detection/sample-image` → devuelve imagen de prueba sin anotar

**Imagen anotada:** PIL + ImageDraw, bboxes verdes sobre la imagen, devuelta como base64 PNG en el JSON de respuesta.

**Registro en main.py:**
```python
from app.api.v1.tree_detection import router as tree_detection_router
app.include_router(tree_detection_router, prefix="/api")
# → rutas: /api/tree-detection/...
```

### Frontend

```
frontend/src/components/TreeDetectionPanel.tsx
```

**Solapa agregada en App.tsx:**
```typescript
type ViewType = "grid" | "map" | "geo" | "trees";
// Nav tabs: [..., { key: "trees", icon: "🌲", label: "Detección IA" }]
// Render: view === "trees" → <TreeDetectionPanel />
```

**Flujo de UI:**
1. Usuario hace clic en "▶ Correr demo" → POST /api/tree-detection/run
2. Loading spinner con mensaje "La primera vez tarda ~30 seg por descarga del modelo"
3. Resultado: stats (árbol count, confianza promedio, resolución), imagen anotada, tabla top 10 por score
4. DropZone para subir imagen propia (PNG/JPG/TIFF)

## Modelos candidatos comparados (decidido en sesión 14)

| Modelo | Rol en pipeline | Cuándo usarlo |
|--------|-----------------|---------------|
| **DeepForest** | Detección de copas (bboxes) | **AHORA** — pre-entrenado, pip install, CPU ok |
| **SAM** | Segmentación de polígonos | Paso 2 del pipeline — usar con los bboxes de DeepForest |
| YOLOv8 | Detección alternativa / fine-tuning | DESPUÉS — cuando tengamos fotos propias de Pablo |
| Rasterio watershed | Fallback sin GPU | No usar en este módulo — existe en forest_analyzer.py |

**Decisión:** combo DeepForest (detecta) + SAM (refina polígono). YOLOv8 para fase 2 con datos propios.

## Imágenes de prueba públicas (sin registro)

```bash
# OSBS_029.png — Bosque nacional Florida, NEON dataset
wget https://github.com/weecology/DeepForest/raw/main/tests/data/OSBS_029.png

# OSBS_029.tif — mismo pero GeoTIFF con georreferencia
wget https://github.com/weecology/DeepForest/raw/main/src/deepforest/data/OSBS_029.tif

# australia.tif — 1.8cm/px, alta resolución
wget https://github.com/weecology/DeepForest/raw/main/src/deepforest/data/australia.tif
```

## Requerimientos de imagen para producción

- Resolución mínima: 5 cm/pixel (drone a ~80m de altura)
- Formato: GeoTIFF georreferenciado o PNG+GPS
- Óptimo: imagen multiespectral (DJI Phantom 4 Multispectral — agrega NIR para NDVI por copa)
- Solapamiento para ortomosaico: 80% frontal, 60% lateral
- Condiciones de vuelo: día claro, sol alto (evitar sombras largas laterales)
- **CRÍTICO:** definir protocolo de vuelo con Pablo ANTES de desarrollar el pipeline de producción

## Implementación real verificada en sesión 15 (tree_detection.py)

### SAM con `multimask_output=True` — elegir la mejor máscara

```python
from segment_anything import sam_model_registry, SamPredictor

SAM_CHECKPOINT = "/tmp/sam_models/sam_vit_b.pth"  # montado como named volume sam_models:/tmp/sam_models
SAM_MODEL_TYPE = "vit_b"

sam = sam_model_registry[SAM_MODEL_TYPE](checkpoint=SAM_CHECKPOINT)
sam.eval()
predictor = SamPredictor(sam)
predictor.set_image(image_np)  # numpy RGB uint8

for _, row in predictions.iterrows():
    box = np.array([int(row["xmin"]), int(row["ymin"]), int(row["xmax"]), int(row["ymax"])])
    masks, scores_sam, logits = predictor.predict(
        box=box,
        multimask_output=True,   # SAM genera 3 candidatas — elegir la de mayor score
    )
    best_idx = int(np.argmax(scores_sam))
    mask = masks[best_idx]  # bool array H×W
    sam_score = float(scores_sam[best_idx])  # predicted_iou
    stability = _stability(logits[best_idx])  # cálculo local, ver abajo
```

### stability_score — cálculo local verificado (sesión 16)

SAM `predict(multimask_output=True)` devuelve `(masks, scores, logits)`. El `stability_score` oficial
re-thresholdea los logits con ±delta y mide IoU entre ambas máscaras resultantes:

```python
def _stability(mask_logits: np.ndarray, delta: float = 1.0) -> float:
    high = mask_logits > delta
    low  = mask_logits > -delta
    intersection = (high & low).sum()
    union = (high | low).sum()
    return float(intersection / union) if union > 0 else 0.0
```

Valores típicos: estables > 0.90, dudosos 0.70-0.90.

### Criterios de confianza dual — valores recomendados (sesión 16)

| Métrica | Descripción | Threshold recomendado |
|---------|-------------|----------------------|
| `score` (DeepForest) | Confianza del detector RetinaNet | ≥ 0.40 (default 0.10 = muy permisivo) |
| `sam_score` (predicted_iou) | Calidad estimada de la máscara SAM | ≥ 0.85 |
| `stability_score` | Robustez de la máscara ante variaciones | ≥ 0.90 |

Copa **confiable** = pasa los 3. Copa **dudosa** = pasa alguno pero no todos.

### Sliders de confianza en tiempo real — patrón UI (sesión 16)

Tres sliders en el sidebar, uno por métrica. Canvas re-dibuja verde/amarillo sin re-fetch.
Thresholds viven en `useState` del panel principal y se pasan como props a `PolygonCanvas`.
El canvas re-dibuja en el `useEffect` que tiene los thresholds en el dep array.

```tsx
const [thresholdDeep, setThresholdDeep]   = useState(0.4);
const [thresholdSam, setThresholdSam]     = useState(0.85);
const [thresholdStab, setThresholdStab]   = useState(0.9);

// En canvas render:
const isConfident = (t: TreeBox) =>
  t.score >= thresholdDeep &&
  (t.sam_score ?? 1) >= thresholdSam &&
  (t.stability_score ?? 1) >= thresholdStab;

// Color en canvas:
ctx.fillStyle = isConfident(tree) ? "#10b98133" : "#f59e0b33";  // verde o amarillo
ctx.strokeStyle = isConfident(tree) ? "#10b981" : "#f59e0b";
```

Valores iniciales razonables: `thresholdDeep=0.4`, `thresholdSam=0.85`, `thresholdStability=0.9`.
Contador "X / N copas confiables (Y%)" calculado inline con `result.trees.filter(...)`.

### Conversión máscara → polígono simplificado (con cv2 o fallback numpy)

```python
def _mask_to_polygon(mask: np.ndarray) -> list[list[int]]:
    try:
        import cv2
        mask_u8 = mask.astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return []
        c = max(contours, key=cv2.contourArea)
        epsilon = 0.01 * cv2.arcLength(c, True)   # simplificar ~1% del perímetro
        approx = cv2.approxPolyDP(c, epsilon, True)
        return approx.reshape(-1, 2).tolist()      # [[x,y], [x,y], ...]
    except ImportError:
        # Fallback sin cv2: elipse aproximada inscrita en bounding box de la máscara
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not rows.any():
            return []
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        cx, cy = (cmin + cmax) / 2, (rmin + rmax) / 2
        rx, ry = (cmax - cmin) / 2, (rmax - rmin) / 2
        return [[int(cx + rx * np.cos(2*np.pi*i/16)), int(cy + ry * np.sin(2*np.pi*i/16))]
                for i in range(16)]
```

### Dibujo RGBA con overlay semitransparente (máscaras SAM)

```python
def _draw_results_sam(image_path: str, trees: list[dict]) -> bytes:
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_o = ImageDraw.Draw(overlay)

    for tree in trees:
        green = int(100 + 155 * tree.get("score", 1.0))
        poly = tree.get("polygon", [])
        if poly and len(poly) >= 3:
            flat = [(p[0], p[1]) for p in poly]
            draw_o.polygon(flat, fill=(0, green, 80, 60))    # relleno semitransparente
            draw_o.polygon(flat, outline=(0, green, 80, 220)) # contorno sólido
        else:
            # fallback: bbox
            x1, y1, x2, y2 = tree["xmin"], tree["ymin"], tree["xmax"], tree["ymax"]
            for off in range(2):
                ImageDraw.Draw(img).rectangle(
                    [x1-off, y1-off, x2+off, y2+off], outline=(0, green, 80))

    img = Image.alpha_composite(img, overlay).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
```

### Campo `sam_used` en el response

El endpoint ahora devuelve `sam_used: bool` para que el frontend sepa si mostrar "Copas SAM" o "Bboxes DeepForest" como label. Cada árbol incluye `sam_score`, `stability_score`, y `polygon`.

## Pitfalls DeepForest

- Primera llamada a `load_model()` descarga el modelo de HuggingFace (~200MB) — puede tardar 20-30s
- En Docker: el modelo se descarga al directorio de caché de HuggingFace (`~/.cache/huggingface/`). Si el container se destruye, se vuelve a descargar. Para producción, montar volumen en ese path.
- `predict_tile()` es necesario para GeoTIFF grandes — `predict_image()` puede quedarse sin memoria con ortomosaicos
- Output de `predict_image()` puede ser `None` si no detecta nada — siempre chequear antes de iterar
- Para GeoTIFF con CRS: instalar GDAL (en Dockerfile: `apt install gdal-bin` o usar imagen con GDAL pre-instalado). Sin GDAL, solo funciona con PNG/JPG.

## Imágenes NEON incluidas en el paquete (sin descarga extra)

Las imágenes de prueba viven dentro del paquete instalado — disponibles sin internet:

| Archivo | Resolución | Zona | Árboles detectados |
|---------|-----------|------|---------------------|
| `OSBS_029.png` | 400×400 | Florida (NEON) | ~15 |
| `OSBS_029.tif` | 400×400 | Florida + GeoTIFF coords | ~15 |
| `SOAP_031.png` | 400×400 | Sierra Nevada | ~20 |
| `2019_YELL_2_528000_4978000_image_crop2.png` | 2299×2472 | **Yellowstone real** | **46** |

Obtener path desde Python (dentro del container):
```python
import deepforest, os
data_dir = os.path.join(os.path.dirname(deepforest.__file__), "data")
```

La imagen de Yellowstone (15MB) es la más impactante para demos. Copiar al servidor:
```bash
docker cp <backend>:/usr/local/lib/python3.11/site-packages/deepforest/data/2019_YELL_2_528000_4978000_image_crop2.png ~/proyectos/forestai-3d/uploads/samples/
```

---

## Patrón React: preservar estado al cambiar de tab

**Problema:** Conditional rendering desmonta el componente → pierde resultado de detección, loading state, etc.

```tsx
// ❌ MAL — desmonta, pierde estado
{view === "trees" ? <TreeDetectionPanel /> : null}

// ✅ BIEN — siempre montado, visible/oculto con CSS
<div style={{ flex: 1, display: view === "trees" ? "flex" : "none", overflow: "hidden" }}>
  <TreeDetectionPanel />
</div>
<div style={{ flex: 1, display: view === "3d" ? "flex" : "none", overflow: "hidden" }}>
  <Forest3DView />
</div>
```

Aplicar a TODOS los paneles. Beneficio extra: Three.js y MapLibre no se destruyen al cambiar de tab.

---

## Patrón: lifted state para compartir detección con vista 3D

```tsx
// App.tsx
const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
<TreeDetectionPanel onResult={setDetectionResult} />
<Forest3DView detectionResult={detectionResult} onGoDetect={() => setView("trees")} />

// TreeDetectionPanel — exportar tipos + aceptar callback
export interface TreeBox { ... }
export interface DetectionResult { ... }
export default function TreeDetectionPanel({ onResult }: { onResult?: (r: DetectionResult | null) => void }) {
  // llamar onResult?.(data) luego de fetch exitoso
  // llamar onResult?.(null) al inicio de cada fetch
}
```

---

## Vista 3D conectada a detección real

**Conversión bbox → posición 3D (coordenadas normalizadas):**
```typescript
const cx = ((tree.xmin + tree.xmax) / 2 / imgW) * SCENE_SIZE
const cz = ((tree.ymin + tree.ymax) / 2 / imgH) * SCENE_SIZE
const crownRadius = Math.max(0.5, Math.min(4, (bboxW + bboxH) / 4))
```

**Ortofoto anotada como textura del terreno:**
```typescript
const tex = new THREE.TextureLoader().load(`data:image/png;base64,${imageB64}`)
tex.flipY = false  // CRÍTICO: desactivar flip para que coincida con coords de detección
```

Terreno: `<planeGeometry args={[size, size]} />` posicionado en `[size/2, -0.05, size/2]`.

**Colores:**
- Si hay VLM: `saludable=#22c55e, estresado=#eab308, enfermo=#ef4444`
- Fallback por score: `>0.7=#22c55e, >0.5=#eab308, else=#94a3b8`

**EmptyScene:** cuando no hay detección → mostrar mensaje + botón que llama `onGoDetect()` para ir a la tab de detección.

---

## Pitfalls SAM

- **Checkpoint en /tmp/sam_models (named volume) — fix definitivo aplicado sesión 15:** El volume `sam_models` se monta en `/tmp/sam_models` en `docker-compose.yml`. El path correcto es `SAM_CHECKPOINT = "/tmp/sam_models/sam_vit_b.pth"`. Descargar UNA VEZ al volume con `docker exec` y los rebuilds lo preservan. Ver pitfall en SKILL.md para el snippet completo de docker-compose + descarga.

- **ViT-B vs ViT-H:** `vit_b` = 375MB, más rápido, suficiente para copas de árboles. `vit_h` = 2.5GB, más preciso, necesita GPU para ser usable. Para la PoC usar siempre `vit_b`.

- **`multimask_output=True` es mejor que `False`:** Con `False` SAM devuelve UNA máscara "de compromiso". Con `True` devuelve 3 candidatas con scores — tomar la de mayor score. Mejora la calidad del polígono de copa.

- **SAM falla silenciosamente si el checkpoint no existe:** `sam_model_registry[type](checkpoint=path)` no lanza FileNotFoundError útil. Verificar `os.path.exists(checkpoint)` antes de cargar. El service ya tiene `_sam_available()` para esto.

- **Tiempo de carga:** La primera llamada carga SAM en memoria (~1-2s en CPU para vit_b). Subsequent calls reutilizan el mismo predictor si se cachea a nivel módulo (no implementado aún — se recarga por request). Para producción, cachear el `SamPredictor` como singleton.
