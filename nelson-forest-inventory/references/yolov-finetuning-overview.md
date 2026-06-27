# YOLO Fine-tuning Pipeline — Overview (absorbido de nelson-yolov-finetuning)

Skill completa absorbida. Repo: `github.com/aliagenttucuman-byte/yolov-orientacion-poc`
PoC en: `/home/server/proyectos/yolov-orientacion-poc/` — FastAPI :8020 + nginx :9020 + docker-compose.

## Flujo de escalado: Spike → PoC → Proyecto
```
1. SPIKE (brainstorming/) — experimento desechable, valida feasibility (mAP50, dataset size)
2. PoC (proyectos/ + GitHub repo propio) — FastAPI + React + Docker, sin persistencia/auth
3. INTEGRACIÓN (ForestAI) — solo cuando PoC demuestra mAP50 >= 0.65
```

## Arquitectura del pipeline
```
GeoTIFF → tiler.py (tiles 640-1024px, overlap 128px, ExG filter)
        → build_dataset (pseudo-labels ExG + augmentación 4x)
        → trainer.py (YOLO fine-tuning, CPU, 80 epochs)
        → detector.py (inferencia por tile → NMS global)
        → reporter.py (mAP50/P/R + tiles anotados)
```

## Calibración de parámetros por escenario

**Demo stakeholders (conf creíble, no máxima):**
- conf=0.55, iou=0.45, nms_iou=0.40, centroid_dist_px=60, tile_size=1024, overlap=200px
- Resultado verificado: 299 árboles en 9deJulio.rgb.tif ✅ (conf=0.10 → 3.419 ❌ ruido)

**Producción:** conf=0.30–0.40, centroid_dist_px=50–70 + validación de campo (error <15%)

## Modelos soportados
| Key | Weights | Params | Notas |
|-----|---------|--------|-------|
| yolov8n | yolov8n.pt | 3.2M | muy rápido |
| yolo11n | yolo11n.pt | 2.6M | muy rápido |
| yolo11n_forestai | runs/.../best.pt | — | fine-tuned NOA ← mejor detector de copas |
| yolo26n | yolo26n.pt | 5.3M | v8.4.0 nuevo — más conservador que yolo11n |
| yolo26n_especies | yolo26n_especies_noa_v1.pt | — | clasifica ESPECIE, no cuenta árboles |

**CONCEPTO CRÍTICO:** yolo11n_forestai (fine-tuned) detecta 7× más que yolo26n base.
El fine-tuning importa más que la versión del modelo.
yolo26n_especies NO cuenta árboles — clasifica especie de copa ya detectada.

## NMS global post-tiling (criterio dual: IoU + centroides)
```python
def nms_global(detections, iou_threshold=0.40, centroid_dist_px=60):
    # Criterio 1: IoU > threshold → suprimir (mismo árbol en tiles solapados)
    # Criterio 2: distancia centroides < centroid_dist_px → suprimir (misma copa, bboxes desplazados)
    # centroid_dist_px=60 @ 6cm/px ≈ 3.6m (copa única)
    # Subir a 80-100 para quebrachos adultos o eucaliptos
```

## ExG como detector standalone (sin ML)
- exg_threshold=0.12, min_area=400px², max_area=12000px², centroid_dist_px=200
- Resultado: 880 árboles en 9deJulio urbano denso (~6.3s vs ~30-60s YOLO CPU)
- Ver references/yolov-exg-watershed.md para ExG+Watershed (separa copas individuales)

## Pipeline de clasificación de especies NOA
```
DATASET (una vez, Claude): TIF → tiler → yolo26n detecta → species_labeler.py → labels YOLO multi-clase
FINE-TUNING: python3 pipeline/trainer_species.py --data data.yaml --base-model yolo26n.pt
PRODUCCIÓN: yolo26n_especies_noa_v1.pt detecta + clasifica en un solo pass
```
13 clases NOA: Quebracho blanco/colorado, Algarrobo negro/blanco, Cebil colorado, Tipa blanca,
Lapacho rosado, Palo borracho, Cedro tucumano, Horco quebracho, Guarán, Vinal, Otro.

Control VLM: `LABELER_BACKEND=claude` (dataset, default) | `LABELER_BACKEND=openai` (producción)

## Fine-tuning con ultralytics
```python
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
results = model.train(
    data='dataset/data.yaml', epochs=80, imgsz=640, batch=8,
    device='cpu', patience=20, lr0=0.005, flipud=0.5, fliplr=0.5,
    mosaic=0.8, degrees=15, translate=0.1, scale=0.3, exist_ok=True,
)
```
- Resultados verificados v2 (152 imgs, imgsz=640, batch=8): mAP50=0.4804 (39 epochs early stop)
- Para mAP50≥0.65: anotar ~50 tiles con LabelStudio

## Pitfalls clave YOLO
- **tile_size debe coincidir con imgsz de entrenamiento** — usar tile_size=640 con modelos entrenados a 640; tile_size=1024 da 1 copa por tile
- **`docker compose restart` NO aplica cambios de código** — hacer `docker compose build backend` + `up -d`
- **sys.path en yolo_service.py** — usar búsqueda hacia arriba con `Path(__file__).resolve().parents`, NO índice fijo (explota en Docker si la profundidad difiere)
- **overlap float vs int** — frontend manda ratio (0.0-0.5), backend espera píxeles: `Math.round(overlap * tileSize)`
- **TIFs Pix4D subexpuestos** (mean ~60/255) — stretch p2-p98 per-canal en tiler.py antes de guardar JPG
- **gpt-4o-mini con detail:low** no identifica especies NOA — usar Claude Sonnet para generar dataset
- **Campo `confidence` no `conf`** — `run_inference()` usa clave `confidence` en los dicts
- **Scope creep** — cuando Nelson manda imagen "ves? detecta así", diagnosticar primero, implementar solo si dice "dale" explícito
- **yolo26n más conservador que yolo11n** — necesita conf~0.15 para resultados equivalentes a yolo11n@0.25
- **Dockerfile con pipeline de nivel superior** — `COPY pipeline/ /app/pipeline/` desde raíz del proyecto
- **nginx client_max_body_size** — TIFs pesan 200-500MB, agregar `client_max_body_size 500m; proxy_read_timeout 600s;`
- **Upload via Cloudflare tunnel** — quick tunnels dan error genérico "Error de red" para TIFs grandes; usar Tailscale directo
- **ProcessRequest usa `model_key`, no `model`** — mandar `{"model":"yolo26n"}` se ignora silenciosamente
- **`_job_results` es dict en memoria** — se pierde con restart del servidor; re-ejecutar /process si /classify-species da error
- **TS6133 en frontend** — `tsc --noUnusedLocals` activo; eliminar constantes huérfanas antes de `docker compose build frontend`
- **README de Ultralytics va detrás de docs.ultralytics.com** — verificar docs oficial antes de afirmar que un modelo no existe

## Endpoints del backend (prefijo /api/v1/)
- `POST /api/v1/upload` — multipart, guarda con UUID en /tmp/yolov-uploads/
- `POST /api/v1/process` — {job_id, model_key, conf, iou, tile_size, overlap} → pipeline completo
- `POST /api/v1/compare` — corre N modelos sobre el mismo job
- `POST /api/v1/classify-species` — clasifica especie (requiere /process previo)
- `GET /api/v1/tiles/{job_id}/{tile_filename}` — sirve tiles como imágenes

## Agregar modelo nuevo (pasos mínimos)
1. `pipeline/detector.py` — agregar en `SUPPORTED_MODELS`
2. `frontend/src/components/ModelSelector.tsx` — agregar en `MODELS` y `MODEL_DEFAULTS` (con tile_size automático)
3. `docker compose build --no-cache backend` + `up -d --no-deps backend`
4. `curl -s http://localhost:8020/api/v1/health` — verificar que el nuevo key aparece

## Referencias de detalle
- `references/calibracion-parametros-2026-06-11.md` — barrido completo conf/tile_size, parámetros demo ReforestLatam
- `references/yolov-poc-params-calibration.md` — tabla calibración por escenario (urbano/periurbano/rural)
- `references/yolov-benchmark-2026-06-10.md` — resultados detallados v1 vs v2
- `references/yolov-exg-watershed.md` — ExG+Watershed detector sin ML para copas individuales
- `references/species-pipeline-noa.md` — pipeline completo fine-tuning especies NOA
- `references/species-labeling-pipeline.md` — etiquetado automático con Claude/gpt-4o-mini
- `references/species-labeler-vlm-pitfalls.md` — pitfalls VLM (detail:low, Claude vs GPT, TIFs oscuros)
- `references/species-classifier-prod.md` — pipeline producción YOLO+gpt-4o-mini fallback
- `references/species-classifier-noa.md` — código completo clasificador NOA
- `references/species-classifier-design.md` — diseño arquitectura clasificador
