---
name: nelson-yolov-finetuning
title: YOLO Fine-tuning sobre Ortofotos
description: "Fine-tuning de modelos YOLO (v8/v9/v11) para deteccion de arboles en ortofotos aereas. Pipeline completo: TIF -> tiles -> pseudo-labels ExG -> augmentacion -> entrenamiento -> comparativa."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [yolo, ultralytics, fine-tuning, ortofotos, forestai, deteccion-arboles, computer-vision]
    related_skills: [nelson-forest-inventory, nelson-ai-vision, spike]
---

# YOLO Fine-tuning sobre Ortofotos — Equipo Nelson

Skill de dominio para el PoC `yolov-orientacion-poc`. Cubre el pipeline completo
de fine-tuning de modelos YOLO sobre ortofotos de drone para deteccion de copas de arboles.

Repo: `github.com/aliagenttucuman-byte/yolov-orientacion-poc`

PoC en: `/home/server/proyectos/yolov-orientacion-poc/`
Stack: backend FastAPI :8020 + nginx :9020 + docker compose
Acceso interno: `http://100.110.8.13:9020` (Tailscale ai-server)

---

## Calibración de parámetros por escenario

**REGLA CLAVE:** conf bajo → números grandes pero con ruido (autos, techos, cruces peatonales).
Para demos con stakeholders siempre preferir números creíbles sobre números altos.

### Demo para stakeholders (ReforestLatam, inversores)
- **Objetivo:** conteo creíble, no máximo. 200-400 bien > 3.000 con ruido.
- conf: **0.55** — balance entre detección y precisión
- iou: 0.45 — NMS estándar por tile
- nms_iou: 0.40 — NMS global post-tiling
- centroid_dist_px: **60** — fusiona duplicados de la misma copa
- tile_size: **1024px** ← NO 640px — ver pitfall copas grandes abajo
- overlap: 200px (20% de 1024)

**Resultado verificado 2026-06-11 en TIF 9deJulio.rgb.tif:**
- conf=0.55, tile=1024, centroid=60 → **299 árboles** ✅
- conf=0.10, tile=640 → 3.419 árboles ❌ (ruido: autos, techos, cruces)
- conf=0.65, tile=640 → 294 árboles (pierde copas grandes)

Resultado verificado en 9deJulio.rgb.tif (zona urbana): **275 árboles** con estos parámetros.

### Producción (inventario real)
- conf: 0.30–0.40, iou: 0.45, nms_iou: 0.40, centroid_dist_px: 50–70
- Requiere validación de campo (error target < 15%)

### Demo máxima (para mostrar volumen bruto antes de calibrar)
- conf: 0.10, iou: 0.30 → muchos FP pero impresiona visualmente
- NO usar para reuniones con clientes técnicos

---

## Flujo de escalado: Spike → PoC → Proyecto

Nelson escala en 3 pasos claramente separados — nunca mezclar fases:

```
1. SPIKE (brainstorming/)
   └── experimento desechable, sin repo propio, sin UI
   └── valida feasibility (mAP50, dataset size, modelo)

2. PoC (proyectos/ + GitHub repo propio)
   └── FastAPI + React + Docker — ejecutable manualmente
   └── Operador sube TIF, elige modelo, ve resultados
   └── Sin persistencia, sin auth, sin tests

3. INTEGRACIÓN (ForestAI u otro proyecto productivo)
   └── Solo cuando la PoC demuestra mAP50 >= 0.65
   └── Código nuevo, no copy-paste del spike
```

**Señal de transición:** cuando Tony dice "quiero poder ejecutarlo manualmente"
o "quiero subir un archivo y ver los resultados" → saltar directo a PoC con UI.
No quedarse en CLI scripts.

## Arquitectura del pipeline

```
GeoTIFF (ortofoto)
      |
      v
 tiler.py        tiles 640-1024px + overlap 128px + ExG filter
      |
      v
 build_dataset   pseudo-labels ExG + augmentacion 4x (flips)
      |
      v
 trainer.py      YOLO fine-tuning (ultralytics, CPU, 80 epochs)
      |
      v
 detector.py     inferencia por tile -> NMS global
      |
      v
 reporter.py     bar chart mAP50/P/R + tiles anotados
```

---

## ExG como detector standalone (sin ML)

ExG puede usarse directo como detector de copas, no solo como generador de pseudo-labels.
Útil cuando el modelo fine-tuned está sin calibrar o detecta mal (como autos, cruces).

**Integración como model_key `"exg"` en el service:**

```python
# pipeline/exg_detector.py — detector completo
def run_exg_inference(tiles, tiles_dir, exg_threshold=0.12, min_area=400, max_area=40000):
    # itera tiles, aplica ExG, devuelve misma estructura que run_inference()
    # confidence fijado en 0.90 (ExG no tiene score)
    ...

# yolo_service.py — branch en run_pipeline()
VALID_MODELS = list(SUPPORTED_MODELS.keys()) + ["exg"]

if model_key == "exg":
    detections_raw, elapsed = run_exg_inference(tiles_meta, tiles_dir)
    detections = nms_global(detections_raw, iou_threshold=nms_iou, centroid_dist_px=centroid_dist_px)
else:
    model = load_model(model_key)
    detections_raw, elapsed = run_inference(...)
    detections = nms_global(...)
```

**Parámetros recomendados para ExG demo:**
- exg_threshold: 0.12 — umbral vegetación
- min_area: 400px² — copa mínima ~20×20px (~copa < 1.2m a 6cm/px = ruido)
- max_area: **12000px²** — copa máxima ~110×110px (árbol adulto grande)
  ⚠️ NO usar 40000px² — deja pasar zonas de pasto/vegetación continua como "copa"
- centroid_dist_px: **200** para zona urbana densa (880 árboles en 9deJulio)
  - 150 → 1.177 árboles (aún con duplicados)
  - 120 → 1.427 árboles (demasiados)

**Síntoma de max_area mal calibrado:** aparecen 3-4 bounding boxes gigantes sobre el tile
que cubren zonas de bosque continuo o pasto, en vez de copas individuales.

**Resultados verificados en 9deJulio.rgb.tif (con max_area=12000, min_area=400):**
- centroid=90 → 1.801 árboles (demasiados)
- centroid=150 → 1.177 árboles
- centroid=200 → **880 árboles** ← número razonable para zona urbana densa ✅

**Comparativa de velocidad vs YOLO en CPU:**
- ExG: ~2.4s para 141 tiles
- YOLO11n fine-tuned: 30-60s para los mismos tiles

**Ventajas vs YOLO fine-tuned:**
- No detecta autos ni techos (filtra por aspect ratio)
- Velocidad: ~2.4s para 141 tiles (vs 30–60s YOLO en CPU)
- No requiere modelo pre-entrenado

**Limitaciones:**
- No distingue árbol de arbusto o pasto (igual que pseudo-labels)
- Umbral ExG sensible a la hora del día (sombras cambian el verde)
- Sin score de confianza real (fijado en 0.90 para compatibilidad con la UI)

---

## Pseudo-labels con ExG (Excess Green)

ExG es el metodo de auto-anotacion. No requiere anotacion manual.

```python
def exg_boxes(rgb, min_area=120, max_area=30000):
    r = rgb[:,:,0].astype(float)
    g = rgb[:,:,1].astype(float)
    b = rgb[:,:,2].astype(float)
    H, W = r.shape
    tot = r + g + b + 1e-9
    exg = 2*(g/tot) - (r/tot) - (b/tot)
    mask = (exg > 0.12).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < min_area or a > max_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        boxes.append(((x+w/2)/W, (y+h/2)/H, w/W, h/H))
    return boxes
```

**Parametros clave:**
- `exg > 0.12` — umbral de vegetacion (12% normalizado)
- `min_area=120` — descarta manchas de ruido muy pequeñas
- `max_area=30000` — descarta zonas de vegetacion continua (no son copas individuales)
- Kernel morfologico `MORPH_ELLIPSE (7,7)` — conecta pixeles de la misma copa

**Limitaciones del ExG como pseudo-labeler:**
- Introduce ~20-30% de ruido (FP: sombras, cespedes, arbustos)
- No distingue arbol de arbusto o pasto
- Funciona bien con ortofotos RGB de alta resolucion (~6cm/px)
- Para mejor calidad: LabelStudio con 50 tiles manuales sube mAP50 de 0.48 a 0.7+

---

## Dataset compartido

Todos los spikes usan el mismo dataset base para resultados comparables.

```bash
# Construir una sola vez
python dataset/build_dataset.py

# Con TIFs especificos
python dataset/build_dataset.py --tifs /ruta/a.tif /ruta/b.tif
```

**TIFs disponibles en el server:**
- `/home/server/.hermes/document_cache/doc_7a6ea9f8381b_9deJulio.rgb.tif`
- `/home/server/.hermes/document_cache/doc_877ea5356955_Avellaneda.rgb.tif`
- `/home/server/proyectos/forestai-poc/uploads/055422ad-92da-4ac9-8a96-abea4b7629b2.tif`
- `/home/server/proyectos/forestai-poc/uploads/f96fd29a-433d-4d78-9714-24ac1a643225.tif`

**Configuracion del dataset:**
```python
TILE_SIZE   = 640     # imgsz estandar YOLO
STRIDE      = 480     # overlap de 160px
MIN_BOXES   = 5       # descartar tiles sin arboles
MAX_TILES_PER_TIF = 8 # evitar overfitting a una sola imagen
RANDOM_SEED = 42

# Augmentaciones aplicadas (4x por tile):
# orig, flipH, flipV, flipHV
```

---

## Fine-tuning con ultralytics

```python
from ultralytics import YOLO

model = YOLO('yolo11n.pt')
results = model.train(
    data='dataset/data.yaml',
    epochs=80,
    imgsz=640,
    batch=8,
    device='cpu',
    patience=20,
    lr0=0.005,
    flipud=0.5,
    fliplr=0.5,
    mosaic=0.8,
    degrees=15,
    translate=0.1,
    scale=0.3,
    exist_ok=True,
)
```

**Modelos soportados (ultralytics):**

| Key | Base weights | Params | Velocidad CPU | Release |
|-----|-------------|--------|---------------|---------|
| yolov8n | yolov8n.pt | 3.2M | muy rapido | v8.3.x |
| yolov8s | yolov8s.pt | 11M | rapido | v8.3.x |
| yolov9c | yolov9c.pt | 25M | medio | v8.3.x |
| yolo11n | yolo11n.pt | 2.6M | muy rapido | v8.3.x |
| yolo11s | yolo11s.pt | 9.4M | rapido | v8.3.x |
| yolo12n | yolo12n.pt | ? | ? | v8.3.x |
| yolo26n | yolo26n.pt | 5.3MB | ~6.5s CPU | v8.4.0 ← NUEVO |
| yolo26n_especies_noa | runs/species/.../best.pt | — | — | fine-tuned NOA |
- Default en UI: conf=0.15, tile=640, centroid=60
- Release v8.4.0 — la doc oficial docs.ultralytics.com ya lo muestra como modelo de referencia
  pero el README del repo aún muestra YOLO11. El .pt se descarga de GitHub releases v8.4.0.
- YOLO26n es más conservador que yolo11n — necesita conf más baja para resultados equivalentes
- Default en UI: conf=0.15, tile=640, centroid=60
- yolo26n más conservador que yolo11n: necesita conf~0.15 para resultados equivalentes a yolo11n@0.25

## Pipeline de Fine-tuning por Especie (yolo26n + Claude + gpt-4o-mini)

### Arquitectura dual VLM
```
Dataset (una vez): Claude Sonnet via Azure Anthropic
  TIF → tiles (con stretch p2-p98) → yolo26n detecta copas
  → recorta copa con padding → Claude clasifica especie → labels YOLO multi-clase

Producción: gpt-4o-mini (barato, rápido)
  Copa detectada → gpt-4o-mini clasifica especie en tiempo real
```

**Por qué Claude para dataset y no gpt-4o-mini:**
- gpt-4o-mini (detail:low o detail:high) retorna "Otro" confianza 0.5 para todas las copas del NOA
- Claude usa contexto geográfico tucumano y distingue: Tipa blanca (0.42-0.52), Lapacho rosado
- Para dataset (una sola vez): Claude. Para inferencia en producción: gpt-4o-mini

### Control del backend VLM
```bash
LABELER_BACKEND=claude python3 pipeline/species_labeler.py ...   # default, dataset
LABELER_BACKEND=openai python3 pipeline/species_labeler.py ...   # producción
```

### Archivos del pipeline de especies
- `pipeline/species_labeler.py` — detecta + recorta + clasifica con VLM, genera dataset YOLO
- `dataset/build_species_dataset.py` — combina múltiples TIFs, split train/val, data.yaml
- `pipeline/trainer_species.py` — fine-tunea yolo26n con clases de especies

### Pitfall — TIF subexpuesto (Pix4D, mean ~60/255)
Los TIFs de Pix4D con 4 bandas (RGBA) salen oscuros sin normalización.
tiler.py aplica stretch p2-p98 por canal antes de guardar el tile JPG.
Sin esto el VLM ve imagen grisácea y clasifica todo como "Otro".
Fix ya aplicado en tiler.py — no tocar.

### Pitfall — campo "confidence" no "conf" en detecciones
`run_inference()` devuelve dicts con key `"confidence"`, NO `"conf"`.
Siempre usar `d.get("confidence", 0.0)` al ordenar/filtrar detecciones.

### Especies NOA/Tucumán (13 clases)
Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco,
Cebil colorado, Tipa blanca, Lapacho rosado, Palo borracho,
Cedro tucumano, Horco quebracho, Guarán, Vinal, Otro

### Resultados dataset Avellaneda (2026-06-11, Claude, min_conf_vlm=0.30)
- Tipa blanca: 117 | Lapacho rosado: 4 | Otro descartados: 23
- 144 VLM calls, 786s (~5.5s/call Claude vs ~1.5s/call gpt-4o-mini)
- Zona urbana → Tipa blanca dominante. Para Quebracho/Algarrobo/Cebil → TIFs de monte nativo

### Modelo entrenado: yolo26n_especies_noa_v1
- Base: yolo26n.pt (v8.4.0), 2 clases activas (Tipa blanca, Lapacho rosado)
- mAP50 epoch 28: 0.321 — entrenamiento en CPU, ~30-40 min total

**Cómo verificar si un modelo nuevo de Ultralytics existe:**
1. Revisar docs.ultralytics.com (fuente primaria — va adelante del README)
2. Intentar `YOLO("yolo26n.pt")` — si descarga, existe
3. README de GitHub puede mostrar versión anterior

| yolo26n_especies | models/yolo26n_especies_noa_v1.pt | 5.2M | ~6.5s/run CPU | v8.4.0, fine-tuned NOA |

**yolo26n_especies_noa_v1 — calibración Avellaneda (2026-06-11):**
- conf=0.25, tile=640, centroid=60
- mAP50=0.762 | Tipa blanca=0.902 | Lapacho rosado=0.623
- Default en UI: conf=0.25, tile=640, centroid=60
- Aparece en la doc oficial docs.ultralytics.com como modelo de referencia en todos los ejemplos Python
- El .pt se descarga desde GitHub releases v8.4.0 (5.3MB): `YOLO("yolo26n.pt")` funciona
- El README del repo todavía mostraba YOLO11 como "latest" — la doc oficial va adelante del README
- También existe yolo12n (carpeta en cfg/models/ del repo)
- Para agregar a la PoC: 1 línea en `SUPPORTED_MODELS` de detector.py + entry en MODELS y MODEL_DEFAULTS del frontend + rebuild --no-cache
- Usar `pip install -U ultralytics` para asegurarse de tener v8.4.0+
- Agregado a la PoC en sesión 2026-06-11 — ver sección "Agregar modelo nuevo" más abajo

**Tiempo estimado en CPU (ai-server, sin GPU):**
- yolo11n, 80 epochs, 152 imgs, imgsz=640 → ~26 min (0.43 hs)
- Early stopping tipico a epoch 39-40 con patience=20

---

## NMS global post-tiling

Critico para eliminar duplicados cuando los tiles se solapan.

```python
def nms_global(detections, iou_threshold=0.5):
    """Mismo patron que ForestAI._nms_dataframe."""
    dets = sorted(detections, key=lambda d: d["confidence"], reverse=True)
    keep = []
    suppressed = set()
    for i, d in enumerate(dets):
        if i in suppressed:
            continue
        keep.append(d)
        ax1,ay1,ax2,ay2 = d["global_x1"],d["global_y1"],d["global_x2"],d["global_y2"]
        area_a = max(0,ax2-ax1)*max(0,ay2-ay1)
        for j in range(i+1, len(dets)):
            if j in suppressed:
                continue
            b = dets[j]
            bx1,by1,bx2,by2 = b["global_x1"],b["global_y1"],b["global_x2"],b["global_y2"]
            ix1,iy1 = max(ax1,bx1),max(ay1,by1)
            ix2,iy2 = min(ax2,bx2),min(ay2,by2)
            inter = max(0,ix2-ix1)*max(0,iy2-iy1)
            if inter == 0:
                continue
            area_b = max(0,bx2-bx1)*max(0,by2-by1)
            iou = inter/(area_a+area_b-inter) if (area_a+area_b-inter)>0 else 0
            if iou > iou_threshold:
                suppressed.add(j)
    return keep
```

---

## Resultados verificados (sesion 2026-06-10)

### v1 — dataset pequeño (5 tiles, imgsz=1024, batch=2)
- mAP50: **0.0017** — modelo no aprendio
- Causa: dataset insuficiente + batch muy pequeño en CPU

### v2 — dataset aumentado (152 imgs, imgsz=640, batch=8)
- Epochs: 39 (early stop)
- Best epoch: 14
- **mAP50: 0.4804**
- Precision: 0.5753 / Recall: 0.4623
- Detecciones en tile Tucuman: YOLO11=48 vs ExG=45 (delta +3, ~7%)

**Leccion v1 vs v2:**

| Factor | v1 (fallo) | v2 (funciona) |
|--------|-----------|---------------|
| Imagenes train | 5 | 152 |
| imgsz | 1024 | 640 |
| batch | 2 | 8 |
| mAP50 | 0.0017 | 0.4804 |

**Para llegar a mAP50 >= 0.65:** anotar manualmente ~50 tiles con LabelStudio.

---

## Uso rapido

```bash
cd /home/server/proyectos/yolov-orientacion-poc

make dataset                                            # una sola vez
make compare TIF=/ruta/ortofoto.tif                    # train + infer + plot
make infer TIF=/ruta/ortofoto.tif                      # solo inferencia
make report                                            # ver leaderboard
```

---

## PoC con UI — patrón verificado

Cuando Tony dice "quiero ejecutar manualmente / subir ortofotos y ver resultados",
la estructura es FastAPI + React + docker-compose. No es solo un script CLI.
Siempre repo separado de ForestAI — "no mezclemos" es orden directa.

```
yolov-poc/
├── pipeline/          # tiler.py, detector.py, trainer.py, reporter.py (reutilizable)
├── backend/           # FastAPI :8020
│   └── app/
│       ├── api/v1/    # upload.py, process.py, results.py
│       ├── services/  # yolo_service.py (orquesta pipeline)
│       └── models/    # schemas.py (Pydantic v2)
├── frontend/          # React + Vite + Tailwind :3020
│   └── src/
│       ├── components/ # DropZone, ModelSelector, ResultsPanel, TileViewer, ComparePanel
│       ├── api/        # client.ts (fetch wrapper)
│       └── types/      # index.ts
├── docker-compose.yml  # backend + frontend + nginx :9020
├── nginx.conf          # /api/ → backend, / → frontend, client_max_body_size 500m
└── CONSTITUTION.md
```

**Puertos verificados en producción (2026-06-10):**
- backend: `0.0.0.0:8020` (FastAPI, expuesto directo también para debug)
- nginx: `0.0.0.0:9020` (punto de entrada principal, el que se tunneliza)
- Repo: `/home/server/proyectos/yolov-orientacion-poc`
- Tunnel log: `/tmp/cf_yolov.log`
- Cloudflare URL apunta a **:9020** (nginx), NO al backend :8020

**Endpoints críticos del backend:**
- `POST /api/v1/upload` — multipart, guarda con UUID en `/tmp/yolov-uploads/`
- `POST /api/v1/process` — `{job_id, model_key, conf, iou, tile_size, overlap}` → corre pipeline completo
- `POST /api/v1/compare` — corre N modelos sobre el mismo job y compara
- `GET /api/v1/tiles/{job_id}/{tile_filename}` — sirve tiles generados como imágenes

## PITFALL — ProcessRequest usa `model_key`, no `model`

El schema Pydantic del backend usa el campo `model_key`, NO `model`.
Mandar `{"model":"yolo26n"}` → el campo se ignora silenciosamente → usa el default `yolo11n_forestai`.
Curl correcto:
```bash
curl -s -X POST http://localhost:9020/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"job_id":"<id>","model_key":"yolo26n","conf":0.15,"tile_size":640}'
```

**Síntoma:** la respuesta devuelve `"model_key":"yolo11n_forestai"` aunque mandaste otro modelo.

## PITFALL — Rutas del backend usan prefijo `/api/v1/`, no `/api/`

`API_PREFIX = "/api/v1"` en main.py. nginx pasa `/api/` al backend pero las rutas internas son `/api/v1/`.
Llamar a `/api/health` o `/api/process` da 404.
Rutas correctas:
```bash
POST http://localhost:9020/api/v1/upload
POST http://localhost:9020/api/v1/process
POST http://localhost:9020/api/v1/classify-species   # nuevo endpoint
POST http://localhost:9020/api/v1/compare
GET  http://localhost:9020/api/v1/health
```
Para descubrir rutas: `curl -s http://localhost:9020/api/v1/health` o revisar main.py.
Un 405 Method Not Allowed en GET significa que la ruta EXISTE (espera otro método) — útil para verificar.

## PITFALL — `/classify-species` requiere `/process` previo en la MISMA sesión del servidor

`_job_results` es un dict en memoria del proceso uvicorn. Si el servidor se reinicia,
las detecciones se pierden. El flujo siempre debe ser:

1. `POST /api/v1/upload` → job_id
2. `POST /api/v1/process` con ese job_id → detecciones quedan en `_job_results[job_id]`
3. `POST /api/v1/classify-species` con el mismo job_id → accede a las detecciones en memoria

Si hay un rebuild/restart entre pasos 2 y 3, hay que repetir upload + process.

---

**PITFALL crítico — sys.path en yolo_service.py:**
El servicio necesita importar `pipeline.*` que está un nivel arriba del backend.
NO usar `parents[N]` con índice fijo — explota en Docker si la profundidad difiere.
Usar búsqueda hacia arriba:

```python
import sys
from pathlib import Path

def _find_pipeline_root() -> Path:
    if (Path("/app") / "pipeline").is_dir():   # Docker
        return Path("/app")
    for parent in Path(__file__).resolve().parents:
        if (parent / "pipeline").is_dir():     # dev local
            return parent
    return Path(__file__).resolve().parent

_root = str(_find_pipeline_root())
if _root not in sys.path:
    sys.path.insert(0, _root)

from pipeline.tiler import generate_tiles
from pipeline.detector import load_model, run_inference, nms_global
```

**PITFALL — Dockerfile con pipeline de nivel superior:**
El `COPY pipeline/` debe estar en el Dockerfile con contexto desde la raíz del proyecto:
```dockerfile
# context: . (raíz del proyecto)
COPY backend/ /app/backend/
COPY pipeline/ /app/pipeline/   # ← copiado explícitamente
```

**PITFALL — nginx client_max_body_size:**
Los TIFs de ortofotos pueden pesar 200-500MB. Sin esto el upload da 413:
```nginx
client_max_body_size 500m;
proxy_read_timeout 600s;   # el procesamiento puede tardar varios minutos en CPU
proxy_send_timeout 600s;
```

**Frontend — TileViewer con Canvas:**
Los tiles se sirven como JPG sin bboxes. El frontend dibuja los bboxes en Canvas sobre
la imagen cargada. No necesita que el backend genere las imágenes anotadas:
```tsx
// canvas ref + useEffect que dibuja sobre img.onload
const ctx = canvas.getContext('2d')
ctx.drawImage(img, 0, 0)
detections.forEach(d => {
  ctx.strokeStyle = '#22c55e'
  ctx.strokeRect(d.x1, d.y1, d.x2-d.x1, d.y2-d.y1)
})
```

**Modo comparativa:**
`POST /api/v1/compare` acepta `{job_id, models: ["yolov8n","yolo11n"]}`.
Reutiliza los tiles ya generados (se generan una sola vez por job_id).
Cada modelo procesa los mismos tiles — resultados comparables.

---

## PITFALL — Upload via Cloudflare tunnel falla con "Error de red"

Los TIFs de ortofotos pesan 30-60MB+. Cloudflare quick tunnels tienen límite ~100MB, pero el XHR del browser dispara `onerror` genérico ("Error de red al subir archivo") en lugar de un 413. El backend y nginx están bien — el problema es Cloudflare.

**Diagnóstico rápido:**
```bash
# Upload directo sin tunnel → debe dar 200
curl -X POST http://localhost:9020/api/v1/upload \
  --form "file=@/ruta/ortofoto.tif" \
  -w "\nHTTP %{http_code}\n" --max-time 30 -s | tail -3
```

**Alternativas:**
1. Tailscale directo `http://100.110.8.13:9020` — pero verificar antes que el nodo cliente esté conectado (`tailscale status`)
2. Endpoint `/api/v1/load-local` que lista TIFs del server para seleccionar sin upload

## PITFALL — Frontend manda overlap como ratio (float) pero backend espera píxeles (int)

El slider de overlap en el ModelSelector usa valores 0.0–0.5 (ratio).
El schema Pydantic del backend espera `overlap: int` en píxeles.
Pydantic rechaza con 422 → frontend muestra "[object Object]" en el error.

**Fix en buildReq:**
```typescript
overlap: Math.round(overlap * tileSize)  // convierte 0.2 → 128px para tileSize=640
```

**Síntoma:** "Error durante el procesamiento [object Object]" en la UI.
**Diagnóstico rápido:** `docker compose logs backend --tail=20` — buscar `422 Unprocessable Entity`.

---

## PITFALL — TileViewer con `.slice(0, 12)` hardcodeado

El componente `TileViewer.tsx` puede tener un `.slice(0, 12)` en `groupByTile()`.
Con 1000+ árboles y 50+ tiles, solo muestra 12. El conteo total es correcto pero la grilla se ve incompleta.

**Fix:** eliminar el `.slice()` y agregar paginación (PAGE_SIZE = 24):
```typescript
const PAGE_SIZE = 24
const allTiles = groupByTile(result.detecciones)
const totalPages = Math.ceil(allTiles.length / PAGE_SIZE)
const tiles = allTiles.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
```
Agregar botones Anterior / Siguiente. Sin paginación, el browser intenta renderizar todos los canvas a la vez y se cuelga.

---

## Plan de mejora real — de PoC a producción (mAP50 0.48 → 0.65+)

Capturado en sesión 2026-06-11 para presentación ReforestLatam.

### Problema raíz
mAP50=0.48 porque los pseudo-labels ExG no distinguen árbol de arbusto/pasto/sombra.
El modelo aprende a imitar ExG, no a reconocer copas reales.

### FASE 1 — Datos (2 semanas)
- Anotar manualmente 50–80 tiles con LabelStudio
- Solo copas bien definidas, descartar arbustos y bordes difusos
- Esto solo ya lleva mAP50 a 0.65+

### FASE 2 — Modelo (1 semana)
- Re-entrenar yolo11s (no nano) con tiles anotados + pseudo-labels filtrados
- Agregar clase negativa "no-árbol" con ejemplos de pasto/sombra
- Target: yolo11s con 9.4M params vs actual 2.6M

### FASE 3 — Post-proceso (implementado en sesión 2026-06-11)
- Fusión por centroides (ver sección anterior)
- Filtro de tamaño mínimo de copa: descartar bboxes < 20×20px (ruido)

### FASE 4 — Validación de campo
- Comparar conteo modelo vs conteo manual en parcela conocida
- Target: error < 15%

---

## PITFALL — tile_size debe matchear el imgsz de entrenamiento del modelo

El modelo `yolo11n_forestai` fue entrenado con `imgsz=640`. Si se procesa con
`tile_size=1024`, el modelo ve copas demasiado pequeñas en relación al tile y
solo detecta **1 copa por tile** (la más prominente). Se pierden el 90% restante.

**Parámetros calibrados confirmados para yolo11n_forestai (9deJulio, 2026-06-11):**
```
tile_size=640, conf=0.65, centroid=90 → 275 árboles  ✅ (demo clásica ReforestLatam)
tile_size=640, conf=0.55, centroid=90 → 438 árboles  ✅ (captura copas grandes también)
tile_size=640, conf=0.45, centroid=90 → 633 árboles  (algo de ruido urbano)
tile_size=640, conf=0.35, centroid=90 → 924 árboles  ❌ demasiado ruido
tile_size=1024, conf=0.65             → 161 árboles  ❌ modelo underperforms (ve copas demasiado pequeñas)
tile_size=1024, conf=0.45             → 401 árboles  (conf compensado pero sucio)
```

**DEFAULT ACTUAL PARA UI:** conf=0.55, tile=640, centroid=90
→ Captura copas grandes que a conf=0.65 se perdían. 438 árboles en 9deJulio.

**Regla:** siempre usar `tile_size == imgsz` del entrenamiento. Para modelos fine-tuned
con el pipeline estándar del equipo: `tile_size=640`.

---

## PITFALL — NMS global post-tiling: IoU no alcanza para copas grandes

El NMS clásico (solo IoU) falla cuando dos detecciones de la misma copa grande tienen
superposición baja (bbox izq vs bbox der de la misma copa → IoU bajo → no se suprimen).

**Fix implementado:** NMS con criterio dual en `detector.py`:
1. IoU > threshold → suprimir (mismo árbol en tiles solapados)
2. Distancia entre centroides < `centroid_dist_px` → suprimir (misma copa, bboxes desplazados)

```python
def nms_global(detections, iou_threshold=0.40, centroid_dist_px=60):
    # criterio 1: IoU
    if iou_val > iou_threshold: suppress
    # criterio 2: distancia entre centroides
    dist = sqrt((acx-bcx)**2 + (acy-bcy)**2)
    if dist < centroid_dist_px: suppress
```

`centroid_dist_px=60` @ 6cm/px ≈ 3.6m — copa única.
Subir a 80-100 para quebrachos adultos o eucaliptos.

---

## PITFALL — Modelo detecta objetos urbanos (autos, cruces peatonales, techos)

El modelo fine-tuned con pseudo-labels ExG aprendió "zonas verdes" en general.
En ortofotos urbanas con calles, cruces y autos, el modelo detecta todo lo que tenga
textura similar a vegetación (capós blancos con sombra, franjas de cruce, bordes de techo).

**Síntoma:** 3.000+ detecciones, tiles con autos o cruces marcados como "árboles".

**Fix triple en `run_inference()`:**
```python
# 1. Conf alta (≥ 0.50 para zonas urbanas)
# 2. Filtro tamaño mínimo — autos y cruces son pequeños
if w < 25 or h < 25: continue
# 3. Filtro aspect ratio — copas son ~circulares
ratio = w / max(h, 1)
if ratio > 2.5 or ratio < 0.4: continue
```

Autos: bbox ~30×15px (ratio 2.0 → pasa el filtro de ratio pero cae por conf alta).
Cruces peatonales: bbox muy alargado → ratio > 2.5 → filtrado.
Copas: ratio 0.7–1.4, tamaño 40–200px → pasan todos los filtros.

---

## PITFALL — nms_iou y iou son el MISMO parámetro en el código original

El código original usaba `iou` tanto para el NMS de YOLO por tile como para el NMS global
post-tiling. Son cosas distintas:
- `iou`: controla NMS dentro de un tile (ultralytics interno)
- `nms_iou`: controla NMS global entre tiles solapados

Separarlos permite afinar cada uno independientemente. Si el usuario dice "sigue habiendo
duplicados entre tiles" → bajar `nms_iou`. Si dice "dentro del mismo tile hay duplicados"
→ bajar `iou`.

---

## PITFALL — overlap float vs int (422 Unprocessable Entity)

El frontend maneja `overlap` como ratio (0.0–0.5) pero el backend schema espera píxeles enteros.
Si el frontend manda `overlap: 0.2` directamente → Pydantic 422.

**Fix en buildReq (ModelSelector.tsx):**
```tsx
overlap: Math.round(overlap * tileSize)   // 0.2 * 640 = 128px ✓
```
Nunca pasar el ratio crudo al backend.

---

## PITFALL — TileViewer hardcodeado a 12 tiles

El componente `TileViewer.tsx` tenía `.slice(0, 12)` en `groupByTile()`.
Con 1326 detecciones mostraba solo 12 tiles. Fix: eliminar el slice y agregar paginación.

**Patrón de paginación recomendado:**
```tsx
const PAGE_SIZE = 24
const allTiles = groupByTile(result.detecciones)
const totalPages = Math.ceil(allTiles.length / PAGE_SIZE)
const tiles = allTiles.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
```
Mostrar contador "Mostrando X–Y de Z" + botones Anterior/Siguiente.
Sin paginación el browser intenta renderizar cientos de canvas simultáneamente → UI lenta o colgada.

---

## Clasificación de Especies + Salud (LLM Vision + CLIP + HDBSCAN)

Pipeline implementado en `pipeline/species_classifier.py`. Flujo combinado:

```
Tiles existentes (ya generados por YOLO)
      |
      v
Step 1: gpt-4o-mini Vision por tile (sample_tiles=20 default)
        → especie + salud + confianza por zona del tile
      |
      v
Step 2: CLIP embeddings de crops individuales (bbox de cada árbol)
        → openai/clip-vit-base-patch32 local (fallback: histograma color)
      |
      v
Step 3: HDBSCAN clustering (fallback: KMeans)
        → votar especie del tile LLM → asignar a cada cluster → cada árbol
```

**Endpoint:** `POST /api/v1/classify` — requiere que el job haya sido procesado con `/process` primero.
**Cache:** `_job_results` en `yolo_service.py` guarda las detecciones del último `/process` en memoria.
**Frontend:** `SpeciesPanel.tsx` — aparece debajo de ResultsPanel después de procesar.

**Modelo LLM:** `gpt-4o-mini` (mismo que ForestAI vlm_classifier.py — mejor costo/beneficio).
**OPENAI_API_KEY:** inyectar en docker-compose como `${OPENAI_API_KEY}` desde `.env` de forestai-poc o del host.

**Especies del NOA/Tucumán configuradas:**
Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco,
Cebil colorado, Horco quebracho, Tipa blanca, Lapacho rosado,
Palo borracho, Guarán, Cedro tucumano, Vinal.

**PITFALL — overlap float vs int:**
El frontend maneja `overlap` como ratio (0.0–0.5) pero el backend espera píxeles enteros.
Fix en `buildReq()` de `ModelSelector.tsx`:
```ts
overlap: Math.round(overlap * tileSize)  // 0.2 * 640 = 128px ✓
```

**PITFALL — TileViewer hardcodeado a 12 tiles:**
`groupByTile()` tenía `.slice(0, 12)` — eliminarlo y agregar paginación con PAGE_SIZE=24.

**PITFALL — upload error por Cloudflare:**
Quick tunnels limitan uploads a ~100MB. Los TIF del NOA pesan 36-60MB y a veces falla el XHR
con "Error de red" genérico. Solución: acceso directo por Tailscale `http://100.110.8.13:9020`.

**PITFALL — docker build con torch+transformers:**
El rebuild del backend tarda varios minutos. Lanzar con `terminal(background=true)`.

## Filtros post-inferencia en run_inference (sesión 2026-06-11)

El modelo fine-tuned con ExG sobre zonas urbanas detecta autos, techos, cruces peatonales
porque ExG también los marcó como "verde" durante el entrenamiento.
Solución: filtrar **antes del NMS global**, directamente en `run_inference()`.

```python
def run_inference(
    model, tiles, tiles_dir,
    conf=0.25, iou=0.45, imgsz=640,
    min_bbox_px: int = 25,        # descarta ruido pequeño (autos, señales)
    max_aspect_ratio: float = 2.5, # descarta objetos alargados (caminos, paredes)
) -> tuple[list[dict], float]:
    ...
    for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0].numpy().astype(int)
        w, h = x2 - x1, y2 - y1

        # Filtro 1 — tamaño mínimo
        if w < min_bbox_px or h < min_bbox_px:
            continue

        # Filtro 2 — aspect ratio (copas son ~circulares)
        ratio = w / max(h, 1)
        if ratio > max_aspect_ratio or ratio < (1 / max_aspect_ratio):
            continue
        ...
```

**Parámetros:**
- `min_bbox_px=25` — a 6cm/px son copas < 1.5m de diámetro → probablemente ruido
- `max_aspect_ratio=2.5` — caminos, paredes, techos rectangulares se eliminan

**Impacto verificado:** en zona urbana (9deJulio.rgb.tif) baja de ~3.400 a ~275 detecciones
combinado con conf=0.65 y centroid_dist_px=90.

---

## NMS mejorado — fusión por centroides (sesión 2026-06-11)

El NMS estándar solo suprime por IoU. Copas grandes se detectan varias veces
con bboxes levemente desplazados que tienen IoU bajo → no se suprimen → inflación del conteo.

**Fix: agregar criterio de distancia entre centroides en `nms_global()`:**

```python
def nms_global(
    detections: list[dict],
    iou_threshold: float = 0.40,
    centroid_dist_px: int = 40,
) -> list[dict]:
    ...
    acx, acy = (ax1+ax2)/2, (ay1+ay2)/2  # centroide A
    for j in range(i+1, len(dets)):
        ...
        # Criterio 1 — IoU (igual que antes)
        iou_val = inter / union if union > 0 else 0
        if iou_val > iou_threshold:
            suppressed.add(j); continue
        # Criterio 2 — distancia centroides
        bcx, bcy = (bx1+bx2)/2, (by1+by2)/2
        dist = ((acx-bcx)**2 + (acy-bcy)**2) ** 0.5
        if dist < centroid_dist_px:
            suppressed.add(j)
```

**Calibración de `centroid_dist_px`:**
- 40px @ 6cm/px = ~2.4m → copas medianas (algarrobos, cebiles)
- 60px @ 6cm/px = ~3.6m → copas grandes (quebrachos adultos, eucaliptos)
- 80px @ 6cm/px = ~4.8m → árboles muy grandes / ortofotos de baja resolución

**El parámetro debe exponerse en el schema Pydantic y propagarse:**
`ProcessRequest.centroid_dist_px → process.py → yolo_service.py → nms_global()`

---

## Parámetros calibrados para demo (ReforestLatam / stakeholders)

Objetivo: conteo creíble, no máximo. Mejor 200 bien que 800 con ruido.

```python
conf             = 0.30   # certeza media-alta, descarta falsos positivos de pasto/sombra
iou              = 0.45   # NMS estándar por tile
nms_iou          = 0.40   # NMS global post-tiling
centroid_dist_px = 50     # fusiona copas duplicadas a menos de ~3m
tile_size        = 640
overlap          = 128    # 20% de 640px
```

**UI de demo:** exponer solo el slider de `conf` como control principal.
Los parámetros avanzados (nms_iou, centroid) bajo un toggle colapsado "Parámetros avanzados".
Evita confundir a stakeholders con demasiados controles.

---

## PITFALL — `docker compose restart` NO aplica cambios de código (pipeline copiado en build)

El pipeline (`pipeline/`) se **copia** en el Docker build — no es un volumen montado.
Si se modifica `pipeline/exg_detector.py` o `yolo_service.py` en el host, `restart` no sirve.
**Hay que reconstruir la imagen y recrear el contenedor:**

```bash
docker compose build backend            # re-copia los archivos
docker compose stop backend
docker compose rm -f backend
docker compose up -d backend            # lanza con la imagen nueva
```

Verificar con `curl -s http://localhost:9020/api/v1/health` que aparezca el nuevo model_key.

**Síntoma de que el contenedor usa la imagen vieja:** model_key nuevo no aparece en `models_available` aunque el código en host está correcto.

---

## PITFALL — model_key custom no se refleja hasta rebuild `--no-cache`:
Si se agrega un model_key nuevo al `MODELS` dict de `detector.py` (ej: `yolo11n_forestai`),
el contenedor sigue usando la imagen anterior — el cambio no se aplica aunque el archivo en host esté correcto,
porque el pipeline se COPIA en el build (no es un volumen montado).
Error síntoma: `model_key 'yolo11n_forestai' no válido. Opciones: ['yolov8n', ...]`
**Fix:**
```bash
docker compose build --no-cache backend && docker compose up -d --no-deps backend
```
Verificar que el nuevo key aparece después con:
```bash
curl -s http://localhost:8020/api/v1/health
# debe mostrar: {"status":"ok","models_available":["yolov8n","yolov8s","yolov9c","yolo11n","yolo11s","yolo11n_forestai"]}
```

**PITFALL — rutas del backend tienen prefijo `/api/v1/`, no `/api/`:**
Verificar las rutas reales antes de hacer curl:
```bash
curl -s http://localhost:8020/ | python3 -m json.tool  # muestra health path real
# o
curl -s http://localhost:8020/openapi.json | python3 -c "import json,sys; [print(p) for p in json.load(sys.stdin)['paths']]"
```

---

## Pipeline de clasificación de especies — LLM Vision + CLIP + HDBSCAN

Flujo implementado encima de YOLO para identificar especie y salud sin mandar 1 request por árbol:

```
Tiles existentes (ya generados por YOLO)
      |
      v
Step 1: LLM Vision (gpt-4o-mini) sobre muestra de tiles
        → prompt con especies del NOA (quebracho, algarrobo, cebil, etc.)
        → devuelve lista [{species, health, confidence, zone}] por tile
      |
      v
Step 2: CLIP embeddings de crops individuales (bbox) → clustering HDBSCAN/KMeans
      |
      v
Step 3: Votar especie del cluster con LLM results del tile
        → cada árbol queda con species + health + cluster_id
```

**Por qué este flujo:** 1326 árboles × 1 LLM call = caro y lento. Con 20 tiles se infiere la composición del rodal y CLIP agrupa el resto.

**Parámetros del endpoint `/api/v1/classify`:**
- `sample_tiles`: cuántos tiles analizar con LLM (default 20, máx 100)
- `max_crops_per_tile`: crops CLIP por tile (default 15)
- `concurrency`: requests paralelos al LLM (default 5)

**Especies NOA/Tucumán en el prompt:**
Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco, Cebil colorado, Horco quebracho, Tipa blanca, Lapacho rosado, Palo borracho, Guarán, Cedro tucumano, Vinal.

**PITFALL — _job_results cache en memoria:**
El endpoint `/classify` necesita las detecciones del `/process` anterior. `run_pipeline()` debe guardar el resultado en `_job_results[job_id]` después de ejecutar. Sin esto, classify no puede acceder a las detecciones.

```python
# En yolo_service.py
_job_results: dict = {}  # job_id → dict con detecciones raw

def run_pipeline(...):
    ...
    result = { "job_id": ..., "detecciones": detections, ... }
    _job_results[job_id] = result   # ← guardar para classify
    return result
```

**PITFALL — overlap float vs int:**
El frontend maneja overlap como ratio (0.0-0.5) pero el backend Pydantic espera `int` (píxeles). Convertir en `buildReq`:
```typescript
overlap: Math.round(overlap * tileSize)  // 0.2 * 640 = 128px
```

**PITFALL — TileViewer con .slice(0, 12) hardcodeado:**
El componente mostraba solo los primeros 12 tiles. Con 1326 árboles distribuidos en muchos tiles, se perdían la mayoría. Solución: paginación con `PAGE_SIZE = 24` y botones Anterior/Siguiente.

**PITFALL — variable TypeScript no usada rompe build Docker (TS6133):**
`tsc --noUnusedLocals` está activo en el tsconfig del frontend. Si declarás una const y después la reemplazás por otra (ej: `FIXED_TILE_SIZE` → `tileSize` del estado), el build falla con:
```
error TS6133: 'FIXED_TILE_SIZE' is declared but its value is never read.
```
Eliminar la const huérfana antes de hacer `docker compose build frontend`.
Patrón recurrente: refactor de una constante global a un state que queda la vieja declarada.

**Dependencias nuevas para species_classifier:**
```
aiohttp>=3.9
transformers>=4.40
torch>=2.0
scikit-learn>=1.4
hdbscan>=0.8
```
El build de Docker con torch tarda ~3 minutos. Lanzar siempre con `background=true`.

**OPENAI_API_KEY en docker-compose:**
```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```
Exportar antes del build/up: `export OPENAI_API_KEY=$(grep OPENAI_API_KEY /ruta/.env | cut -d= -f2)`

**Ver `references/species-classifier-noa.md` para el código completo del pipeline.**

## PITFALL — mAP50 cerca de cero, modelo no detecta nada

1. **Dataset muy pequeño** (< 20 imgs) → aumentar con augmentacion manual (flips + rotaciones)
2. **imgsz=1024 + batch=2 en CPU** → usar imgsz=640, batch=8
3. **pseudo-labels ruidosas** → kernel morfologico mas agresivo (7x7) + min_area=120
4. **lr0 muy alto** → usar lr0=0.005 en lugar del default 0.01

## PITFALL — EarlyStopping muy temprano (epoch 4-5)

Significa que las pseudo-labels tienen demasiado ruido. Opciones:
1. Subir patience=30
2. Subir umbral ExG a 0.15
3. Bajar lr0=0.001

## PITFALL — overlap float vs int: frontend manda ratio, backend espera píxeles

El slider de overlap en el frontend maneja un ratio (0.0–0.5), pero el schema Pydantic del backend
espera un entero en píxeles (`overlap: int`). Si se manda `overlap: 0.2`, Pydantic devuelve 422
y el frontend muestra "[object Object]" como mensaje de error (porque el error es un objeto JSON,
no un string).

**Fix en `buildReq` del ModelSelector:**
```typescript
function buildReq(modelKey: string): ProcessRequest {
  return {
    job_id: jobId!,
    model_key: modelKey,
    conf,
    iou,
    tile_size: tileSize,
    overlap: Math.round(overlap * tileSize),  // ← convertir ratio → píxeles
  }
}
```

**Señal de diagnóstico:** `422 Unprocessable Entity` en los logs del backend → siempre es mismatch
de tipos en el body del request. Verificar con `docker compose logs backend --tail=20`.

**Señal del frontend:** `[object Object]` en el mensaje de error → el `catch` recibe un objeto JSON
en vez de un string. El handler de error necesita extraer `detail` del body antes de mostrarlo.

## PITFALL — Coordenadas locales vs globales post-tiling

Las detecciones YOLO son locales al tile. Hay que trasladar al espacio global:
```python
gx1 = tile["x0"] + local_x1   # CORRECTO
gy1 = tile["y0"] + local_y1
```
Sin esto el NMS global no funciona y se pierden detecciones en bordes de tiles.

## Pipeline de clasificación de especie + salud (GPT-4o + CLIP + HDBSCAN)

ForestAI usa SAM para contornear copas + LLM vision para especie y salud.
Para replicarlo en la PoC sin 1326 requests individuales, combinar:

**Estrategia: LLM por tile (opción 4) + CLIP clustering (opción 2)**

```
Tiles existentes
      |
      v
GPT-4o Vision por tile → {especie, confianza, salud} por zona
      |
      v
CLIP embeddings de cada crop (bbox ya detectado por YOLO)
      |
      v
HDBSCAN clustering sobre embeddings
      |
      v
Asignar especie del LLM al cluster más cercano → cada árbol tiene especie + salud
```

**Ventaja:** O(N_tiles) requests al LLM en vez de O(N_árboles). Con 51 tiles vs 1326 árboles = 96% menos costo.

**Especies NOA/Tucumán para el prompt:**
Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco,
Cebil colorado, Horco quebracho, Tipa blanca, Lapacho rosado, Palo borracho, Guarán.

**Módulo:** `pipeline/species_classifier.py`
- Step 1: `classify_tile_llm(tile_path, species_list)` → GPT-4o vision
- Step 2: `embed_crops_clip(crops)` → embeddings locales
- Step 3: `cluster_and_assign(embeddings, llm_results)` → HDBSCAN

**OPENAI_API_KEY:** disponible en `/home/server/proyectos/forestai-poc/.env`. Agregar al docker-compose del backend como env var.

---

## PITFALL — Barrido de parámetros: respuesta grande rompe el parser JSON

Cuando se barre conf bajo (ej: 0.10–0.30) sobre un TIF grande, el backend devuelve miles
de detecciones en el JSON. Leer con `curl -s ... | python3 -c "..."` falla porque el output
supera el buffer del subprocess (~20KB) y el JSON se corta.

**Síntoma:** `json.JSONDecodeError: Invalid control character at: line 1 column 20001`

**Fix:** pedir solo el resumen con `| python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tree_count'])"`
o usar el endpoint con conf alto primero para acotar el volumen antes de bajar.

**Patrón de barrido correcto:**
```python
# En execute_code — no tiene el problema de buffer
import json
from hermes_tools import terminal

body = json.dumps({...})  # json.dumps escapa correctamente
r = terminal(f"curl -s -X POST http://localhost:8020/api/v1/process -H 'Content-Type: application/json' -d '{body}'", timeout=120)
data = json.loads(r["output"])
print(data["tree_count"])  # solo el número, no las detecciones
```

---

## ⚠️ PITFALL — Scope creep: diagnosticar primero, implementar solo si Nelson dice "dale"

**Señal real:** Nelson dijo "se ensució mucho esto" después de que JARVIS creó
`exg_detector.py` + patcheó `yolo_service.py` + agregó selector en frontend + 4 Docker
rebuilds encadenados — cuando el ask original era solo "qué opinas del tile con 1 detección".

Nelson manda la imagen, dice "ves? detecta así... no está bien". Eso es invitación a
DIAGNOSTICAR, no a implementar. Diagnosticar primero, pedir "dale" explícito, luego hacer.

**Protocolo correcto ante problema de detección visual:**
1. `vision_analyze` el tile
2. Diagnóstico en 2-3 líneas (causa + solución propuesta)
3. Preguntar: "¿lo implemento?"
4. **Solo si Nelson dice "dale" o equivalente → implementar**

**El "dale" es obligatorio.** Nelson manda audios cortos y va directo. Si no dijo
"dale" / "hacelo" / "sí" → no implementar.

**Síntomas de scope creep en este dominio:**
- Más de 2 archivos nuevos para un diagnóstico visual
- Docker rebuild sin confirmación explícita
- Nelson dice "se ensució" / "se complicó" / "para" / "tranqui"

---

## ExG + Watershed — detector sin ML para copas individuales (2026-06-11)

Ver `references/yolov-exg-watershed.md` (en nelson-forest-inventory) para código completo.

**Problema:** ExG sin Watershed detecta manchas verdes continuas (grupos de copas), no copas individuales.
Cajas enormes de 40000px² que cubren bosques enteros → inútiles para demo.

**Solución — Distance Transform + Watershed:**
```python
dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
_, sure_fg = cv2.threshold(dist_norm, 0.35, 1.0, cv2.THRESH_BINARY)
# sure_bg = dilate(mask, 11×11)
# markers = connectedComponents(sure_fg) + 1; markers[unknown] = 0
cv2.watershed(bgr_from_mask, markers)
# cada label=región watershed → bbox individual
```

**Filtros obligatorios por bbox:**
- `min_area=400, max_area=15000` px² — copa mínima ~20×20px, máxima ~122×122px
- `aspect_ratio: 0.36 < w/h < 2.8` — copas son ~circulares

**Parámetros de inferencia calibrados (9deJulio, 1024px tiles):**
- model_key: `"exg"`, centroid_dist_px: `90`, tile_size: `1024`, overlap: `128`
- Resultado: **323 árboles**, 6.3 segundos, sin GPU

**UI ModelSelector — defaults automáticos por modelo (incluye tile_size):**
Cuando el usuario cambia el selector, conf, centroid Y tile_size se ajustan solos:
```typescript
const MODEL_DEFAULTS: Record<string, { centroid: number; conf: number; tile_size: number }> = {
  yolo11n_forestai: { centroid: 90, conf: 0.55, tile_size: 640  },
  exg:              { centroid: 90, conf: 0.50, tile_size: 1024 },
  yolo11n:          { centroid: 60, conf: 0.25, tile_size: 640  },
  yolov8n:          { centroid: 60, conf: 0.25, tile_size: 640  },
}
function handleModelChange(key: string) {
  setModelKey(key)
  const d = MODEL_DEFAULTS[key]
  if (d) { setConf(d.conf); setCentroid(d.centroid); setTileSize(d.tile_size) }
}
// En handleProcess:
overlap: Math.round(DEFAULT_OVERLAP * tileSize)  // usa tileSize del estado, no hardcodeado
```
⚠️ NO declarar `FIXED_TILE_SIZE` como constante si después se usa `tileSize` del estado — TypeScript TS6133 rompe el build Docker.



## CONCEPTO CRÍTICO — yolo26n base NO es mejor detector de copas que yolo11n_forestai

yolo26n es el nuevo modelo BASE de Ultralytics (v8.4.0). Sin fine-tuning en ortofotos NOA,
detecta MUCHO MENOS que el modelo fine-tuneado:

| Modelo | Árboles (conf=0.15) | Fine-tuned NOA |
|--------|:-------------------:|:--------------:|
| yolo26n (base) | 208 | No |
| yolo11n_forestai | 1511 | Sí |

yolo26n_especies es el fine-tuned de CLASIFICACIÓN de especie — NO un mejor detector de copas.
Para detectar copas en ortofotos del NOA: yolo11n_forestai sigue siendo el mejor modelo.
Para clasificar la especie de una copa ya detectada: yolo26n_especies.

**Error común a evitar:** pensar que "yolo26 > yolo11" en este contexto. En detección de copas,
el fine-tuning importa más que la versión del modelo base.

---

## Comparativa yolo26n vs yolo11n en Avellaneda (2026-06-11)

Parámetros: conf=0.25, tile=640, overlap=128, centroid=60

| Modelo             | Árboles | Tiempo | Notas                          |
|--------------------|---------|--------|--------------------------------|
| yolo11n            | 187     | 6.6s   | conf=0.25                      |
| yolo26n            | 114     | 6.7s   | conf=0.25 — más conservador    |
| yolo26n            | 208     | 10.8s  | conf=0.15 — sweet spot         |
| yolo11n_forestai   | 1511    | 10.8s  | conf=0.15 — fine-tuned NOA     |

yolo26n base (sin fine-tuning) detecta menos que yolo11n al mismo conf — es más conservador.
Para resultados equivalentes a yolo11n@0.25, usar yolo26n@0.15.
Velocidad idéntica a yolo11n en CPU (~6-10s/204 tiles).
Fine-tuning hace la mayor diferencia: yolo11n_forestai detecta 7x más que yolo26n base.

---

## Fine-tuning para clasificación de especies NOA (yolo26n + gpt-4o-mini)

Pipeline implementado en sesión 2026-06-11 para entrenar yolo26n con clases de especies
nativas del NOA/Tucumán, al estilo NetFlora pero con nuestro stack.

### Archivos creados
- `pipeline/species_labeler.py` — detecta copas con yolo26n, recorta, clasifica con gpt-4o-mini, genera dataset YOLO multi-clase
- `dataset/build_species_dataset.py` — combina múltiples TIFs, hace split train/val 80/20, genera data.yaml
- `pipeline/trainer_species.py` — fine-tunea yolo26n con las 13 clases de especies NOA

### Especies NOA/Tucumán (13 clases)
Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco,
Cebil colorado, Tipa blanca, Lapacho rosado, Palo borracho, Cedro tucumano,
Horco quebracho, Guarán, Vinal, Otro (catch-all)

### Uso rápido
```bash
cd /home/server/proyectos/yolov-orientacion-poc
set -a && source /home/server/proyectos/forestai-poc/.env && set +a

# Paso 1: generar dataset con auto-etiquetado VLM
python3 dataset/build_species_dataset.py \
  --tifs /ruta/Avellaneda.rgb.tif /ruta/9deJulio.rgb.tif \
  --output /tmp/species_dataset_final \
  --max-crops 15 --min-conf-vlm 0.30

# Paso 2: fine-tunear yolo26n
python3 pipeline/trainer_species.py \
  --data /tmp/species_dataset_final/data.yaml \
  --epochs 80 --batch 8 --device cpu
```

### PITFALL — campo `confidence` no `conf` en detecciones
`run_inference()` devuelve dicts con clave `confidence`, no `conf`.
Al ordenar por confianza usar `d.get("confidence", 0.0)`.
Campos disponibles: tile_filename, x1, y1, x2, y2, global_x1, global_y1, global_x2, global_y2, confidence.

### PITFALL — TIFs subexpuestos: tiles salen oscuros para VLM
Los TIFs de Pix4Dfields tienen mean ~60/255 → tiles muy oscuros → gpt-4o-mini no puede
clasificar especie y devuelve todo "Otro".
**Fix: stretch de contraste p2-p98 per-canal al generar tiles (implementado en tiler.py):**
```python
for ch in range(3):
    p2, p98 = np.percentile(rgb[:, :, ch], (2, 98))
    if p98 > p2:
        rgb_stretched[:, :, ch] = np.clip(
            (rgb[:, :, ch].astype(np.float32) - p2) / (p98 - p2) * 255, 0, 255
        ).astype(np.uint8)
```
Con stretch: mean ~122/255 → imagen correctamente iluminada → VLM clasifica bien.
**Síntoma:** 100% de copas clasificadas como "Otro". Verificar con `img.mean()` sobre un tile.

### PITFALL — TIF con 4 bandas (RGBA): leer solo R,G,B
Pix4Dfields exporta RGBA. El tiler lee `range(1, min(src.count, 3) + 1)` → correcto.
Verificar con `src.colorinterp` que sea (red, green, blue, alpha).

### Costo VLM estimado
- 167 copas × gpt-4o-mini low-detail ≈ $0.005 (menos de 1 centavo por ortofoto)
- Tiempo: ~267s para 167 copas en Avellaneda (secuencial, sin async)
- Para reducir: `--max-crops 3` por tile en test, `--max-crops 15` en producción

## Fine-tuning yolo26n para especies NOA (sesión 2026-06-11)

Pipeline completo creado en la PoC para entrenar yolo26n como clasificador de especies nativas:

Archivos creados:
- `pipeline/species_labeler.py` — detecta copas con yolo26n, recorta, clasifica con gpt-4o-mini, genera labels YOLO multi-clase
- `dataset/build_species_dataset.py` — combina múltiples TIFs, split train/val 80/20, genera data.yaml
- `pipeline/trainer_species.py` — fine-tuning yolo26n con 13 clases NOA

Clases NOA: Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco, Cebil colorado, Tipa blanca, Lapacho rosado, Palo borracho, Cedro tucumano, Horco quebracho, Guarán, Vinal, Otro.

**PITFALL — TIFs Pix4D subexpuestos (mean ~60/255):**
Los TIFs de Avellaneda y 9deJulio (Pix4D, RGBA) tienen valores medios bajos (~60).
Sin corrección, los tiles salen oscuros y el VLM no puede clasificar.
Fix en `tiler.py` — stretch de contraste p2-p98 per-canal antes de guardar el JPG:
```python
for ch in range(3):
    p2, p98 = np.percentile(rgb[:, :, ch], (2, 98))
    if p98 > p2:
        rgb[:, :, ch] = np.clip(
            (rgb[:, :, ch].astype(float) - p2) / (p98 - p2) * 255, 0, 255
        ).astype(np.uint8)
```
Con el stretch: mean sube a ~121 y el VLM ve colores reales.

**PITFALL — campo `confidence` no `conf` en detecciones:**
`run_inference()` devuelve dicts con clave `confidence`, no `conf`.
Al ordenar por confianza: `sorted(dets, key=lambda d: d.get("confidence", 0.0), reverse=True)`

**PITFALL — VLM clasifica todo como "Otro" en zona urbana:**
Copas vistas desde arriba en zona urbana son difíciles de clasificar por especie.
Si los tiles están oscuros/grises el VLM no tiene información de color → todo "Otro".
Solución: stretch de contraste en tiler.py (ver arriba) + crops con padding suficiente (≥10px).

## Fine-tuning multi-clase para especies del NOA (yolo26n + VLM)

Pipeline implementado en sesión 2026-06-11. Archivos creados:
- `pipeline/species_labeler.py` — detecta copas con yolo26n, recorta, clasifica con VLM
- `dataset/build_species_dataset.py` — combina múltiples TIFs, split train/val
- `pipeline/trainer_species.py` — fine-tunea yolo26n con 13 clases de especies NOA

13 clases: Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco,
Cebil colorado, Tipa blanca, Lapacho rosado, Palo borracho, Cedro tucumano,
Horco quebracho, Guarán, Vinal, Otro.

### PITFALL — campo `confidence` no `conf` en detecciones
`run_inference()` devuelve dicts con clave `confidence`, NO `conf`.
Al ordenar por score: `sorted(dets, key=lambda d: d.get("confidence", 0.0), reverse=True)`

### PITFALL — TIFs subexpuestos: tiles salen oscuros (mean ~60/255)
El TIF de Avellaneda (Pix4Dfields) tiene valores de píxel bajos aunque colorinterp
es R,G,B,Alpha en orden correcto. Sin corrección, los tiles salen grises/oscuros
y el VLM no puede identificar nada.
**Fix obligatorio en tiler.py** — stretch de contraste p2-p98 por canal antes de guardar:
```python
for ch in range(3):
    p2, p98 = np.percentile(rgb[:, :, ch], (2, 98))
    if p98 > p2:
        rgb[:, :, ch] = np.clip(
            (rgb[:, :, ch].astype(np.float32) - p2) / (p98 - p2) * 255, 0, 255
        ).astype(np.uint8)
```
Sin esto: mean ~60. Con esto: mean ~121 — correcto.

### PITFALL — gpt-4o-mini con `detail:low` no clasifica especies desde vista aérea
Con `detail:low` el modelo comprime demasiado la imagen → responde "Otro" en el 100%
de los casos, incluso con crops de 600x500px. 
Con `detail:high` mejora pero sigue sin suficiente conocimiento botánico del NOA.
**Claude Sonnet** (vision_analyze) identifica correctamente (Cebil colorado ~45%,
Horco quebracho ~30%) en los mismos crops.
→ Usar Azure Anthropic Claude Sonnet para clasificación de especies NOA, NO gpt-4o-mini.
→ Alternativa: prior geográfico fuerte + VLM confirma/descarta (zona urbana Tucumán
  → Tipa blanca, Lapacho, Palo borracho son las más probables).

### Calibración VLM para especies NOA
- `detail:low` → todo "Otro", inútil
- `detail:high` + gpt-4o-mini → "Otro" con confianza 0.5, no sirve
- Claude Sonnet (vision) → Cebil colorado 45% / Horco quebracho 30% — usar este

---

## CONCEPTO CLAVE — Detección de copas vs Clasificación de especie (NO confundir)

Dos tareas completamente distintas con modelos distintos:

| Tarea | Modelo | Responde | Output |
|-------|--------|----------|--------|
| Detección de copas | yolo11n_forestai / yolo26n | ¿Dónde están los árboles? ¿Cuántos? | bboxes + conteo |
| Clasificación de especie | yolo26n_especies / VLM | ¿Qué especie es esta copa? | etiqueta + confianza |

**yolo26n_especies NO cuenta árboles — recibe un recorte de copa ya detectada y dice qué especie es.**

Pipeline correcto:
```
yolo11n_forestai (o yolo26n) → detecta N copas
      ↓ para cada copa (crop del tile)
yolo26n_especies → clasifica especie ("Tipa blanca", "Lapacho", etc.)
      ↓ si conf < threshold
gpt-4o-mini → fallback VLM refina la especie
```

**Error común a evitar:** usar yolo26n como "mejor modelo de detección de copas".
yolo26n sin fine-tuning es más conservador que yolo11n_forestai (208 vs 1511 árboles a conf=0.15).
Para detección de copas en ortofotos NOA: yolo11n_forestai (fine-tuned) sigue siendo el mejor.
yolo26n_especies es el fine-tuned de CLASIFICACIÓN, no de detección.

---

## Clasificador de especies en producción — YOLO26n + gpt-4o-mini fallback

Pipeline de inferencia liviano para producción (sin Claude, sin dataset generation):

```
Copa detectada (yolo26n)
      ↓
yolo26n_especies clasifica → conf >= 0.50 → especie confirmada ✅
      ↓ conf < 0.50
gpt-4o-mini (detail:high) refina → usa VLM solo si da más confianza 🔄
```

Módulo: `pipeline/species_classifier_prod.py`
```python
from pipeline.species_classifier_prod import classify_detections

detections = classify_detections(
    detections=job_dets,
    tiles_dir="/tmp/yolov-uploads/.../tiles",
    conf_threshold=0.50,          # umbral para activar fallback VLM
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
)
# Cada detección queda con: especie, conf_especie, via ("yolo" | "vlm_fallback")
```

**Log de telemetría:** `[species_prod] 208 copas — YOLO: 195 | VLM fallback: 13`

**Ventaja vs pipeline previo:** no requiere CLIP ni HDBSCAN ni requests por tile.
Cada copa se procesa de forma independiente, solo las inciertas van al LLM.

**Costo estimado:** si el 10-20% de copas necesita fallback → ~20-40 calls gpt-4o-mini
por ortofoto → fracción de centavo.

## YOLO26n — nuevo modelo base (v8.4.0, sesión 2026-06-11)

- El README de github.com/ultralytics/ultralytics puede mostrar YOLO11 como "latest"
  mientras la doc oficial docs.ultralytics.com ya usa YOLO26.
- El .pt se descarga desde GitHub releases v8.4.0 (5.3MB).
- Verificado: `YOLO("yolo26n.pt")` descarga y carga correctamente.
- Calibración sobre Avellaneda (conf comparada con yolo11n):
  - conf=0.25 → 114 árboles (yolo11n da 187 al mismo conf — yolo26n es más conservador)
  - conf=0.15 → 184 árboles ← sweet spot, equipara yolo11n@0.25
  - conf=0.10 → 251 árboles (empieza ruido)
- Default en UI: conf=0.15, tile=640, centroid=60
- Velocidad CPU: ~6.5s sobre Avellaneda (igual que yolo11n)
- Para usar: `pip install -U ultralytics` para asegurar v8.4.0+

## Pipeline de clasificación de especies NOA — yolo26n + Claude + gpt-4o-mini

Flujo en dos etapas separadas (dataset vs producción):

```
ETAPA 1 — Generación de dataset (una sola vez, con Claude)
  TIF ortofoto
    → tiler.py (tile_size=640, overlap=128, stretch contraste p2-p98)
    → yolo26n detecta copas (conf=0.15)
    → nms_global (centroid_dist_px=60)
    → species_labeler.py → Claude Sonnet clasifica cada copa
    → dataset YOLO multi-clase (images/ + labels/ + data.yaml)

ETAPA 2 — Entrenamiento fine-tuning
  python3 pipeline/trainer_species.py --data data.yaml --base-model yolo26n.pt

ETAPA 3 — Inferencia en producción (barata, rápida)
  yolo26n_especies_noa_v1.pt detecta + clasifica en un solo pass
  (gpt-4o-mini como fallback VLM por copa si se quiere descripción adicional)
```

### Módulos creados (2026-06-11)
- `pipeline/species_labeler.py` — detecta copas + clasifica con Claude/gpt-4o-mini
- `dataset/build_species_dataset.py` — combina múltiples TIFs, split train/val 80/20
- `pipeline/trainer_species.py` — fine-tuning yolo26n multi-clase

### Backend VLM controlado por env var
```bash
LABELER_BACKEND=claude   # default — Azure Anthropic Claude Sonnet (dataset)
LABELER_BACKEND=openai   # gpt-4o-mini (producción, más barato)
```
Claude requiere `AZURE_ANTHROPIC_API_KEY` + `AZURE_ANTHROPIC_BASE_URL` del .env de forestai-poc.
Si no están configurados, fallback automático a gpt-4o-mini.

### Resultados verificados (Avellaneda.rgb.tif, 2026-06-11)
- 144 copas clasificadas con Claude → Tipa blanca: 117, Lapacho rosado: 4
- Fine-tuning yolo26n 80 epochs CPU, ~35 min
- **mAP50: 0.762** — Tipa blanca: 0.902 | Lapacho rosado: 0.623
- Modelo guardado: `models/yolo26n_especies_noa_v1.pt`
- Model key en PoC: `yolo26n_especies`

### Especies NOA configuradas (13 clases)
Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco,
Cebil colorado, Tipa blanca, Lapacho rosado, Palo borracho, Cedro tucumano,
Horco quebracho, Guarán, Vinal, Otro

### PITFALL — gpt-4o-mini con detail:low no identifica especies aéreas
Con `detail: low`, gpt-4o-mini comprime demasiado y responde "Otro" para todo.
Con `detail: high` mejora pero sigue sin conocimiento botánico del NOA.
**Claude Sonnet es el único modelo que identificó correctamente** (Tipa blanca, Cebil colorado)
con razonamiento botánico real. Usar Claude para generar dataset, gpt-4o-mini solo para
inferencia en producción donde la clase ya está entrenada en el modelo YOLO.

### PITFALL — TIFs urbanos solo tienen Tipa blanca
Avellaneda y 9deJulio son zona urbana → predomina Tipa blanca.
Para entrenar Quebracho, Algarrobo, Cebil → necesitar TIF de monte nativo (zona rural/reserva).
Dataset desbalanceado (117 Tipa vs 4 Lapacho) → modelo sesgado hacia Tipa.

### PITFALL — Stretch de contraste obligatorio en tiler.py para VLM
Los TIFs de Pix4D tienen mean ~60/255 (muy oscuros). Sin stretch el VLM ve imágenes
casi negras e identifica todo como "Otro".
**Fix en tiler.py:** stretch per-canal p2-p98 antes de guardar el JPEG:
```python
for ch in range(3):
    p2, p98 = np.percentile(rgb[:, :, ch], (2, 98))
    if p98 > p2:
        rgb_stretched[:, :, ch] = np.clip(
            (rgb[:, :, ch].astype(np.float32) - p2) / (p98 - p2) * 255, 0, 255
        ).astype(np.uint8)
```
Después del fix: mean ~121/255 → colores naturales → VLM clasifica correctamente.
**Síntoma sin fix:** VLM responde "Otro" para todas las copas, imagen parece gris/oscura.

### PITFALL — Banda alpha en TIF Pix4D (4 bandas RGBA)
Pix4Dfields genera TIFs con 4 bandas (R, G, B, Alpha). El tiler lee `min(src.count, 3)`
bandas → lee correctamente R,G,B. El alpha se ignora. Verificar con:
```python
src.colorinterp  # debe mostrar red, green, blue, alpha
```

---

## PITFALL — README del repo va detrás de la doc oficial (verificar ambos)

El README de github.com/ultralytics/ultralytics puede mostrar YOLO11 como "latest"
mientras la doc oficial en docs.ultralytics.com ya usa el siguiente modelo (ej: YOLO26).
Antes de afirmar que un modelo no existe, verificar:
1. docs.ultralytics.com (fuente primaria)
2. github.com/.../releases (confirmar descarga del .pt)
3. Intentar `YOLO("yolo26n.pt")` — si descarga, existe.

En sesión 2026-06-11: README mostraba YOLO11, docs mostraba YOLO26, el .pt se descargó ok.

**PITFALL — run_inference devuelve `confidence`, NO `conf`**

El dict de cada detección usa la clave `confidence` (no `conf`).
Al ordenar o acceder el score de una detección usar siempre:
```python
score = det.get("confidence", 0.0)   # ✅
score = det["conf"]                   # ❌ KeyError
```
Campos completos que devuelve run_inference:
`tile_filename, x1, y1, x2, y2, global_x1, global_y1, global_x2, global_y2, confidence`
los ejemplos Python, y el .pt se descargó correctamente desde v8.4.0 (5.3MB).
El repo cfg/models/ llegaba hasta yolo12 — pero la doc ya estaba en yolo26.

## Agregar modelo nuevo a la PoC — pasos mínimos (sin romper nada)

Cuando aparece un nuevo modelo base (ej: yolo26n), el cambio es quirúrgico:

1. `pipeline/detector.py` — agregar en `SUPPORTED_MODELS`:
   ```python
   "yolo26n": "yolo26n.pt",   # v8.4.0
   ```
2. `frontend/src/components/ModelSelector.tsx` — agregar en `MODELS` y `MODEL_DEFAULTS`:
   ```typescript
   { key: 'yolo26n', label: 'YOLO26n base (v8.4.0 — nuevo)' },
   // defaults:
   yolo26n: { centroid: 60, conf: 0.25, tile_size: 640 },
   ```
3. Rebuild con `--no-cache` (el pipeline se copia en build, no es volumen):
   ```bash
   docker compose build --no-cache backend && docker compose up -d --no-deps backend
   docker compose build --no-cache frontend && docker compose up -d --no-deps frontend
   ```
4. Verificar que el nuevo key aparece en el health:
   ```bash
   curl -s http://localhost:8020/api/v1/health
   ```

El .pt se descarga automáticamente en el primer uso — no hay que copiarlo manualmente.
ultralytics lo baja desde github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt.

---

## Fine-tuning para especies del NOA (yolo26n + VLM auto-labeling)

Pipeline implementado en sesión 2026-06-11. Objetivo: fine-tunear yolo26n con clases
de especies nativas del NOA (no solo "árbol genérico").

### Flujo
```
GeoTIFF ortofoto
      ↓
yolo26n detecta copas (conf=0.15, tile=640)
      ↓
pipeline/species_labeler.py
  → recorta cada copa (con padding=10px)
  → clasifica especie con VLM (Claude para dataset, gpt-4o-mini para producción)
  → guarda anotaciones YOLO multi-clase
      ↓
dataset/build_species_dataset.py
  → combina múltiples TIFs
  → split train/val 80/20
  → data.yaml con 13 clases NOA
      ↓
pipeline/trainer_species.py
  → fine-tunea yolo26n con clases de especies
  → guarda best.pt en runs/species/yolo26n_especies_noa/
```

### Especies del NOA configuradas (13 clases)
Quebracho blanco, Quebracho colorado, Algarrobo negro, Algarrobo blanco,
Cebil colorado, Tipa blanca, Lapacho rosado, Palo borracho, Cedro tucumano,
Horco quebracho, Guarán, Vinal, Otro

### Archivos clave
- `pipeline/species_labeler.py` — etiquetado automático con VLM
- `pipeline/trainer_species.py` — fine-tuning yolo26n multi-clase
- `dataset/build_species_dataset.py` — construcción dataset combinado

### Backend VLM: Claude para dataset, gpt-4o-mini para producción
**Claude Sonnet (Azure Anthropic)** para generar el dataset de entrenamiento:
- Identifica Tipa blanca con confianza 0.42-0.52 en zona urbana de Tucumán ✅
- gpt-4o-mini con detail:low responde siempre "Otro" — inútil para etiquetado
- gpt-4o-mini con detail:high también responde "Otro" — no tiene conocimiento botánico del NOA
- Controlado por env var `LABELER_BACKEND=claude` (default) o `LABELER_BACKEND=openai`

**gpt-4o-mini** para inferencia en producción (barato, rápido, ya integrado).

### Resultados Avellaneda (test con 3 crops/tile, min_conf_vlm=0.30)
- 144 copas etiquetadas, 786s (~13 min)
- Tipa blanca: 117 | Lapacho rosado: 4 | Otro: 23
- Dataset muy desbalanceado — necesita TIFs de monte nativo para Quebracho/Algarrobo/Cebil

### Fuentes de datos para ampliar dataset de especies NOA

**iNaturalist** (API pública, sin auth):
```bash
# Contar observaciones con foto en Argentina (place_id=7190)
curl -s "https://api.inaturalist.org/v1/observations?taxon_id=902968&quality_grade=research&photos=true&place_id=7190&per_page=1"
```

Taxon IDs verificados para especies NOA:
| Especie | taxon_id | Obs Argentina |
|---------|----------|---------------|
| Quebracho colorado (Schinopsis lorentzii) | 902968 | ~205 |
| Algarrobo blanco (Prosopis alba) | 1493104 | ~372 |
| Algarrobo negro (Prosopis nigra) | 1493150 | ~178 |
| Cebil colorado (Anadenanthera colubrina) | 430643 | ~130 |
| Tipa blanca (Tipuana tipu) | 121264 | ~220 |
| Lapacho rosado (Handroanthus impetiginosus) | 281274 | ~39 |

**LIMITACIÓN CRÍTICA:** Las fotos de iNaturalist son vistas laterales desde el suelo, NO copas aéreas.
No sirven directamente para entrenar el clasificador de especies (que recibe crops de copas desde drone).
Uso posible: preentrenar en textura/color de follaje → fine-tune final con tiles de drone etiquetados por campo.

**Fuente ideal (no encontrada en repositorios públicos):**
Inventario de campo con coordenadas GPS de árboles identificados + TIF del mismo sector.
Cruzando shapefile con coordenadas conocidas sobre el TIF → etiquetas gratis sin VLM.

**CONICET Digital (ri.conicet.gov.ar):** bloquea scraping/curl, requiere navegador con JS.
API OAI-PMH responde pero no tiene datasets de imágenes drone del NOA.

### PITFALL — Zona urbana sola = dataset desbalanceado
Avellaneda y 9deJulio son parques urbanos → 80%+ Tipa blanca.
Para entrenar un modelo multi-especie útil se necesitan TIFs de:
- Monte nativo: Quebracho, Algarrobo, Cebil, Horco quebracho
- Yungas: Cedro, Lapacho, Guarán
Sin eso el modelo solo aprende a detectar Tipa blanca.

### PITFALL — TIF subexpuesto → tiles oscuros → VLM clasifica mal
Los TIF de Pix4D con 4 bandas (RGBA) suelen tener mean ~62/255.
Sin stretch de contraste los tiles salen muy oscuros y el VLM ve todo grisáceo.
**Fix en tiler.py:** stretch per-canal p2-p98 antes de guardar el JPG:
```python
for ch in range(3):
    p2, p98 = np.percentile(rgb[:, :, ch], (2, 98))
    if p98 > p2:
        rgb_stretched[:, :, ch] = np.clip(
            (rgb[:, :, ch].astype(np.float32) - p2) / (p98 - p2) * 255, 0, 255
        ).astype(np.uint8)
```
Con stretch: mean ~121/255, colores naturales ✅
Sin stretch: mean ~62/255, imagen oscura grisácea ❌

### PITFALL — Campo `confidence` no `conf` en detecciones
`run_inference()` devuelve dicts con clave `"confidence"`, NO `"conf"`.
Al ordenar detecciones por confianza:
```python
# CORRECTO
sorted(tile_dets, key=lambda d: d.get("confidence", 0.0), reverse=True)
# FALLA con KeyError
sorted(tile_dets, key=lambda d: d["conf"], reverse=True)
```

### PITFALL — Identificación de especie desde copa aérea tiene límites reales
Vista cenital no permite ver corteza, hoja individual, flor ni tronco.
Solo se puede distinguir: textura del follaje, color, forma de copa, tamaño.
Confianza máxima realista: 0.4-0.6 para especies comunes del NOA.
Para dataset de entrenamiento esto es suficiente — no se necesita certeza perfecta.

## PITFALL — Diferencia entre el spike y ForestAI

Este PoC es INVESTIGACION, no produccion. No mezclar codigo con ForestAI.
ForestAI usa DeepForest (pretrained). Este PoC fine-tunea YOLO localmente.
Objetivos distintos, repos distintos.

## Endpoint `/classify-species` — pipeline prod (YOLO + gpt-4o-mini fallback)

Endpoint nuevo agregado en sesión 2026-06-11. Diferente al `/classify` viejo (CLIP+HDBSCAN+GPT):

```
POST /api/v1/classify-species
Body: { "job_id": "...", "conf_fallback": 0.50 }

Requiere: /process previo en la MISMA sesión del servidor (detecciones en _job_results)
Devuelve: resumen por especie + via (yolo | vlm_fallback) + cada detección enriquecida
```

**Flujo:**
1. `POST /api/v1/upload` → job_id
2. `POST /api/v1/process` con `model_key: "yolo26n"` → copas detectadas en `_job_results`
3. `POST /api/v1/classify-species` → clasifica especie de cada copa

**Resultado Avellaneda (2026-06-11, yolo26n conf=0.25, classify-species conf_fallback=0.50):**
- 119 copas detectadas | 5.78s clasificación
- Tipa blanca: 106 (89.1%) conf_avg=0.357 | Otro: 12 | Lapacho rosado: 1
- via_vlm=0 porque OPENAI_API_KEY no estaba configurada → conf_avg baja (fallback no activó)

**PITFALL — `openai` no estaba en requirements.txt:**
`species_classifier_prod.py` importa `openai` pero no estaba en `backend/requirements.txt`.
Síntoma: `ImportError: No module named 'openai'` al llamar `/classify-species`.
Fix permanente: agregar `openai>=1.0.0` a `backend/requirements.txt` + rebuild con `--no-cache`.
NO hacer `docker exec ... pip install openai` — se pierde con el próximo restart.

**PITFALL — OPENAI_API_KEY del .hermes/.env es una project key (`sk-pro...`) distinta a la del equipo:**
La key en `/home/server/.hermes/.env` es la key personal de Hermes (`sk-pro...`).
La API de OpenAI rechaza esta key para llamadas desde otros proyectos (401 Incorrect API key).
Para los PoCs del equipo usar la key correcta — buscarla en `/home/server/proyectos/forestai-poc/.env`
o pedirla a Nelson directamente. NO usar la key de `.hermes/.env` para calls de ForestAI.

**PITFALL — OPENAI_API_KEY en docker-compose tenía placeholder `***`:**
La key real hay que leerla del .hermes/.env y escribirla en docker-compose.yml.
Proceso (desde execute_code):
```python
from hermes_tools import terminal, write_file
r = terminal("python3 -c \"from dotenv import load_dotenv; import os; load_dotenv('/home/server/.hermes/.env'); print(os.environ.get('OPENAI_API_KEY',''))\"")
key = r["output"].strip()
# leer docker-compose con terminal cat, reemplazar en Python, write_file
```
Luego `docker compose up -d backend` (restart simple, no rebuild).

Ver `references/species-classifier-prod.md` para código completo del pipeline de producción (YOLO+gpt-4o-mini fallback).
Ver `references/yolov-benchmark-2026-06-10.md` para resultados detallados.
Ver `references/species-labeling-pipeline.md` para pipeline completo de etiquetado con Claude.
Ver `references/calibracion-parametros-2026-06-11.md` para barrido completo de conf/tile_size y parámetros fijados para demo ReforestLatam.
Ver `references/yolov-poc-params-calibration.md` para tabla de calibración de parámetros por escenario (demo urbana, periurbana, rural) y frase sugerida para stakeholders.
Ver `references/species-pipeline-noa.md` para el pipeline completo de fine-tuning de especies NOA (yolo26n + gpt-4o-mini), archivos creados, parámetros calibrados y pitfalls.
Ver `references/yolov-exg-watershed.md` para código completo de ExG+Watershed + resultados 2026-06-11 + ModelSelector defaults.
Ver `references/species-labeler-vlm-pitfalls.md` para pitfalls completos del pipeline de auto-etiquetado VLM (detail:low, gpt-4o-mini vs Claude, TIFs subexpuestos, campo confidence vs conf).
Ver `references/species_data.json` para el código completo del pipeline de clasificación.
