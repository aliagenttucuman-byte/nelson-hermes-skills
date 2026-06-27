# YOLOv PoC — ExG + Watershed Crown Detector (2026-06-11)

Repo: `github.com/aliagenttucuman-byte/yolov-orientacion-poc`
Backend: FastAPI :8020 (Docker)
Frontend: React+Vite (Docker, nginx :9020 via Tailscale)

## Problema raíz: fine-tuned YOLO no sirve para la demo

`yolo11n_forestai` (fine-tuned sobre ortofotos NOA/Tucumán) detecta 1 copa por tile
con confianza 89-93%, ignorando las otras 10-14 copas visibles en el mismo tile.
Causa: dataset de entrenamiento pequeño y ruidoso — el modelo no aprendió a separar copas.

**No vale la pena seguir ajustando el fine-tuned sin más datos de entrenamiento.**

## Solución: ExG + Watershed como detector sin ML

### Pipeline
```
RGB tile → ExG mask → Morphological open/close → Distance Transform → Watershed → bboxes
```

### ExG (Excess Green)
```python
tot = r + g + b + 1e-9
exg = 2*(g/tot) - (r/tot) - (b/tot)
mask = (exg > 0.12).astype(uint8) * 255
```
Umbral 0.12 empírico sobre RGB uint8 de ortofotos Tucumán.

### Watershed para separar copas dentro de una mancha verde
```python
# Distance transform — picos = centros de copas
dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
_, sure_fg = cv2.threshold(dist_norm, 0.35, 1.0, cv2.THRESH_BINARY)
# sure_bg = dilatación de mask (kernel 11x11)
# markers = connectedComponents(sure_fg) + 1
# markers[unknown] = 0
cv2.watershed(bgr_from_mask, markers)
```

**Pitfall:** ExG sin Watershed detecta manchas verdes completas (grupos de copas) → cajas
enormes que no sirven. El Watershed es obligatorio para separar copas individuales.

### Filtros de calidad por bbox resultante
```python
min_area  = 400    # px² — descarta ruido (<20x20px)
max_area  = 15000  # px² — copa máxima ~122x122px (árbol adulto grande)
min_side  = 18     # px
max_side  = 200    # px
aspect_ratio: 0.36 < w/h < 2.8   # copas ~circulares
```

### Parámetros de inferencia calibrados (9deJulio, tile 1024px)
```json
{
  "model_key": "exg",
  "tile_size": 1024,
  "overlap": 128,
  "centroid_dist_px": 90,
  "nms_iou": 0.40
}
```
→ **323 árboles** en TIF 9deJulio (17094×11327px), 6.3 segundos, sin GPU.

## UI — ModelSelector con defaults automáticos por modelo

`frontend/src/components/ModelSelector.tsx`:

```typescript
const MODEL_DEFAULTS = {
  yolo11n_forestai: { centroid: 60,  conf: 0.65 },
  yolo11n:          { centroid: 60,  conf: 0.25 },
  yolov8n:          { centroid: 60,  conf: 0.25 },
  exg:              { centroid: 90,  conf: 0.50 },
}

function handleModelChange(key: string) {
  setModelKey(key)
  const d = MODEL_DEFAULTS[key]
  if (d) { setConf(d.conf); setCentroid(d.centroid) }
}
```

Cuando el usuario cambia el selector, los sliders de conf y centroid se actualizan solos.
**No hay que tocar parámetros manualmente — solo elegir el modelo y dar a Detectar.**

## Modelos disponibles en la UI

| model_key | Label | Uso |
|---|---|---|
| yolo11n_forestai | YOLO11n ForestAI (fine-tuned) | Referencia, no usar en demo |
| yolo11n | YOLO11n base | Comparativa |
| yolov8n | YOLOv8n base | Comparativa |
| exg | ExG — Excess Green (sin ML) | ✅ Recomendado para demo |

## Docker rebuild pattern (sin --no-cache, cache útil para deps)

```bash
# Build sin invalidar layer de deps (más rápido)
docker compose build backend

# Recrear container (restart no aplica nueva imagen)
docker compose stop backend && docker compose rm -f backend
docker compose up -d backend

# Verificar que el nuevo código está activo
sleep 4 && curl -s http://localhost:9020/api/v1/health | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d['status'], d['models_available'])"
```

**Pitfall:** `docker compose restart` NO aplica la nueva imagen — usa `stop + rm -f + up -d`.

## Resultados comparativos sobre 9deJulio.rgb.tif

| Detector | Árboles | Tiempo | Notas |
|---|---|---|---|
| yolo11n_forestai conf=0.65 | ~275 | ~15s | 1 copa/tile, falsos positivos |
| yolo11n conf=0.25 tile=640 | 452 | ~30s | Mezcla todo (autos, estructuras) |
| yolov8n conf=0.25 tile=640 | 380 | ~30s | Idem |
| exg (sin Watershed) max_area=40k | 1801 | 2.4s | Masas verdes, no copas |
| exg (sin Watershed) max_area=12k | 880 | 2.4s | Mejor pero aún masas |
| **exg + Watershed** centroid=90 | **323** | **6.3s** | ✅ Copas individuales limpias |

## Pitfalls conocidos

1. **ExG detecta pasto y techos verdes** — el Watershed ayuda pero el filtro de aspect_ratio
   es clave. Copas tienen ratio ~1:1; techos son rectangulares.

2. **Rebuild del frontend cacheado** — si el selector no aparece en la UI, hacer hard refresh
   (Ctrl+Shift+R). El JS buildeado está en el container Docker, no en el filesystem del host.

3. **`docker compose build` cacheado** — si se agrega un archivo nuevo a `pipeline/`, el layer
   `COPY pipeline/ ./pipeline/` puede no invalidarse. Usar `--no-cache` solo si hay dudas.
   Verificar con: `docker exec container grep -r "nuevo_modulo" /app/pipeline/`

4. **centroid_dist muy bajo = duplicados** — con tile overlap=128px y centroid=60px, la misma
   copa puede aparecer 2x en tiles adyacentes. Para ExG usar ≥90px.
