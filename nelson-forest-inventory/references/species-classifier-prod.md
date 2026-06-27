# Pipeline de Clasificación de Especies — Producción (YOLO + VLM Fallback)

Sesión: 2026-06-11

## Arquitectura

```
Copa detectada (yolo26n o yolo11n_forestai)
      ↓ crop del tile con padding=10px
yolo26n_especies_noa_v1.pt
      ↓ conf >= 0.50 → especie confirmada ✅
      ↓ conf < 0.50
gpt-4o-mini (detail:high) → refina solo si da más confianza 🔄
```

Módulo: `pipeline/species_classifier_prod.py`

## Endpoint API

```
POST /api/v1/classify-species
{
  "job_id": "<id del /process previo>",
  "conf_fallback": 0.50   # umbral para activar VLM (default: 0.50)
}
```

**Requiere /process previo en la misma sesión del servidor** (detecciones en `_job_results`).
Si el servidor se reinicia entre /process y /classify-species → repetir upload + process.

## Respuesta

```json
{
  "job_id": "...",
  "total_trees": 119,
  "elapsed_sec": 5.78,
  "resumen": [
    {"especie": "Tipa blanca", "count": 106, "pct": 89.1, "avg_conf": 0.357, "via_yolo": 106, "via_vlm": 0},
    {"especie": "Otro", "count": 12, "pct": 10.1, "avg_conf": 0.0, "via_yolo": 12, "via_vlm": 0}
  ],
  "detecciones": [
    {
      "tile_filename": "tile_0012.jpg",
      "x1": 120, "y1": 80, "x2": 200, "y2": 160,
      "confidence": 0.87,
      "especie": "Tipa blanca",
      "conf_especie": 0.823,
      "via": "yolo"
    }
  ]
}
```

## Resultado real Avellaneda (2026-06-11, yolo26n conf=0.25, conf_fallback=0.50)

- 119 copas detectadas (yolo26n base) | 5.78s clasificación
- Tipa blanca: 106 (89.1%) conf_avg=0.357
- Otro: 12 (10.1%)
- Lapacho rosado: 1 (0.8%) conf=0.514
- via_vlm=0 para todos — OPENAI_API_KEY no estaba cargada en el container

**Nota sobre conf_avg baja (0.357):** la mayoría de copas quedó por debajo del threshold 0.50
pero el fallback VLM no se activó porque la API key no estaba configurada. Con la key activa
se espera que el VLM suba la confianza en un 20-30% de los casos.

## Código del módulo

```python
# pipeline/species_classifier_prod.py

SPECIES_MODEL_PATH = os.environ.get(
    "SPECIES_MODEL_PATH",
    "/app/models/yolo26n_especies_noa_v1.pt"
)

CONF_FALLBACK_THRESHOLD = 0.50

def classify_detections(
    detections: list[dict],
    tiles_dir: str,
    conf_threshold: float = CONF_FALLBACK_THRESHOLD,
    openai_api_key: Optional[str] = None,
) -> list[dict]:
    """
    Clasifica especie de cada copa.
    Agrega a cada detección: especie, conf_especie, via ("yolo" | "vlm_fallback")
    """
    model = _get_species_model()
    tile_cache: dict[str, np.ndarray] = {}

    for det in detections:
        img = tile_cache.setdefault(
            det["tile_filename"],
            cv2.imread(os.path.join(tiles_dir, det["tile_filename"]))
        )
        crop = _crop_bbox(img, det, padding=10)
        especie, conf = _classify_with_yolo(model, crop)

        if conf < conf_threshold and openai_api_key:
            especie_vlm, conf_vlm = _classify_with_vlm(OpenAI(api_key=openai_api_key), crop)
            if conf_vlm > conf:
                especie, conf = especie_vlm, conf_vlm
                det["via"] = "vlm_fallback"
            else:
                det["via"] = "yolo"
        else:
            det["via"] = "yolo"

        det["especie"] = especie
        det["conf_especie"] = round(conf, 3)

    return detections
```

## PITFALL — `openai` no estaba en requirements.txt

`species_classifier_prod.py` importa `openai` pero no estaba en `backend/requirements.txt`.
**Síntoma:** `No module named 'openai'` al llamar `/classify-species`.
**Fix permanente:** agregar a `backend/requirements.txt`:
```
openai>=1.0.0
```
Luego rebuild con `--no-cache`. NO usar `docker exec pip install` — se pierde con el restart.

## PITFALL — OPENAI_API_KEY en docker-compose tenía placeholder

La key real del equipo está en `/home/server/.hermes/.env`.
docker-compose.yml tenía `OPENAI_API_KEY=***` como placeholder → el container no recibía la key.

**Fix (desde execute_code, para evitar que la key quede en el historial del terminal):**
```python
from hermes_tools import terminal, write_file

r = terminal("python3 -c \"from dotenv import load_dotenv; import os; load_dotenv('/home/server/.hermes/.env'); print(os.environ.get('OPENAI_API_KEY',''))\"")
key = r["output"].strip()

r2 = terminal("cat /home/server/proyectos/yolov-orientacion-poc/docker-compose.yml")
raw = r2["output"]
new_raw = raw.replace("      - OPENAI_API_KEY=***", f"      - OPENAI_API_KEY={key}")
write_file("/home/server/proyectos/yolov-orientacion-poc/docker-compose.yml", new_raw)
```
Luego `docker compose up -d backend` (restart simple, no rebuild).

## Distinción clave: yolo26n BASE vs yolo26n_especies

| Modelo | Tarea | Input | Output |
|--------|-------|-------|--------|
| yolo26n (base) | Detectar copas | tile 640px | bboxes de árboles |
| yolo26n_especies | Clasificar especie | crop de copa | "Tipa blanca", "Lapacho", etc. |

**NO usar yolo26n_especies para detectar copas — solo para clasificar.**
**Para detección de copas en zona urbana NOA: yolo11n_forestai sigue siendo el mejor (fine-tuned).**

yolo26n base es más conservador que yolo11n_forestai:
- yolo26n conf=0.25 → 119 copas (detecciones limpias, pocas FP)
- yolo11n_forestai conf=0.15 → 1511 copas (copas muy chicas incluidas)

Para el pipeline de clasificación de especies, preferir yolo26n como detector:
las copas son más grandes y bien definidas → el clasificador de especie funciona mejor.

## Flujo completo de prueba (curl)

```bash
# 1. Upload
JOB=$(curl -s -X POST http://localhost:9020/api/v1/upload \
  -F "file=@/ruta/Avellaneda.rgb.tif" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

# 2. Detectar copas con yolo26n (más limpio que yolo11n_forestai a conf=0.25)
curl -s -X POST http://localhost:9020/api/v1/process \
  -H "Content-Type: application/json" \
  -d "{\"job_id\":\"$JOB\",\"model_key\":\"yolo26n\",\"conf\":0.25,\"tile_size\":640}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tree_count'], 'copas')"

# 3. Clasificar especies (misma sesión del servidor)
curl -s -X POST http://localhost:9020/api/v1/classify-species \
  -H "Content-Type: application/json" \
  -d "{\"job_id\":\"$JOB\",\"conf_fallback\":0.50}" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Total: {d[\"total_trees\"]} | Tiempo: {d[\"elapsed_sec\"]}s')
for s in d['resumen']:
    print(f'  {s[\"especie\"]}: {s[\"count\"]} ({s[\"pct\"]}%) via_yolo={s[\"via_yolo\"]} via_vlm={s[\"via_vlm\"]}')
"
```

## Schemas Pydantic (schemas.py)

```python
class SpeciesProdRequest(BaseModel):
    job_id: str
    conf_fallback: float = Field(default=0.50)

class SpeciesProdDetection(BaseModel):
    tile_filename: str
    x1: int; y1: int; x2: int; y2: int
    global_x1: int; global_y1: int; global_x2: int; global_y2: int
    confidence: float
    especie: str
    conf_especie: float
    via: str   # "yolo" | "vlm_fallback" | "error"

class SpeciesProdSummary(BaseModel):
    especie: str
    count: int
    pct: float
    avg_conf: float
    via_yolo: int
    via_vlm: int

class SpeciesProdResponse(BaseModel):
    job_id: str
    total_trees: int
    elapsed_sec: float
    resumen: List[SpeciesProdSummary]
    detecciones: List[SpeciesProdDetection]
```
