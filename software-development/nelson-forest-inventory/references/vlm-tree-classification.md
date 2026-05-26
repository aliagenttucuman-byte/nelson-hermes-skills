# VLM Tree Crown Classification — Spike 002 + Producción (2026-05-21)

## Pipeline validado

```
DeepForest/SAM bboxes → crop_tree() → base64 JPEG → Llama 3.2 90B Vision → JSON (species, health, confidence, notes)
```

Spike completo: `~/brainstorming/2026-05-21-deepagents-spike/spikes/002-vision-llm-forestai/main.py`
Servicio de producción: `~/proyectos/forestai-poc/backend/app/services/vlm_classifier.py`

## Resultados en OSBS_029 (Osceola National Forest, Florida)

- 55 árboles detectados por DeepForest+SAM
- Top 5 clasificados: 3/5 correctos (Pinus sp., saludable)
- 2/5 fallaron por bbox pequeño (< 40px de lado)
- Latencia promedio: 10.22s por árbol (secuencial)

## Servicio de producción — vlm_classifier.py

El servicio está en `backend/app/services/vlm_classifier.py`. Función principal:

```python
async def classify_trees_vlm(
    image: np.ndarray,        # RGB uint8 (H, W, 3)
    trees: List[Dict],        # cada dict con xmin/ymin/xmax/ymax en pixels
    api_key: str,
    concurrency: int = 5,
) -> List[Dict]:
    """
    Clasifica copas en paralelo. Retorna lista con campos vlm_* por árbol.
    Árboles con copa < MIN_CROP_PX (30px) se marcan vlm_ok=False y se omiten.
    """
```

Constantes clave:
- `MIN_CROP_PX = 30` — copas más chicas se omiten
- `TARGET_SIZE = 128` — crops pequeños se escalan a este mínimo
- `PADDING = 10` — pixels extra alrededor del bbox
- `VLM_MODEL = "meta/llama-3.2-90b-vision-instruct"`

## Integración en Celery (analysis_task.py)

El hook VLM está en el task principal después del guardado de árboles (paso 83-90%):

```python
# --- Clasificación VLM (opcional) ---
nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
if nvidia_key:
    progress_callback(83, "Clasificando árboles con Vision LLM...")
    try:
        image_arr = np.array(Image.open(filepath).convert("RGB"))
        H, W = image_arr.shape[:2]

        # Convertir lat/lon → coordenadas pixel (proyección lineal, OK para ortofotos pequeñas)
        lats = [t["centroid_lat"] for t in trees_data]
        lons = [t["centroid_lon"] for t in trees_data]
        lat_min, lat_max = min(lats), max(lats)
        lon_min, lon_max = min(lons), max(lons)

        trees_px = []
        for t in trees_data:
            import math
            r_deg = math.sqrt(t.get("crown_area_m2", 16)) / 111_000
            lat_range = lat_max - lat_min or 1e-6
            lon_range = lon_max - lon_min or 1e-6
            cx = int((t["centroid_lon"] - lon_min) / lon_range * (W - 1))
            cy = int((1 - (t["centroid_lat"] - lat_min) / lat_range) * (H - 1))
            r_px = max(15, int(r_deg / lon_range * W))
            trees_px.append({
                "xmin": max(0, cx - r_px), "ymin": max(0, cy - r_px),
                "xmax": min(W, cx + r_px), "ymax": min(H, cy + r_px),
            })

        # asyncio.run() — NO loop.run_until_complete() en Celery
        vlm_results = asyncio.run(classify_trees_vlm(image_arr, trees_px, nvidia_key))

        # Actualizar BD con resultados
        db_trees = db.query(models.Tree).filter(models.Tree.analysis_id == analysis_id).all()
        tree_by_id = {t.id: t for t in db_trees}
        for vlm in vlm_results:
            if not vlm.get("vlm_ok"):
                continue
            idx = vlm["tree_idx"]
            tree_id = f"{analysis_id[:8]}-{trees_data[idx]['tree_id']}"
            if tree_id in tree_by_id:
                db_t = tree_by_id[tree_id]
                db_t.vlm_species    = vlm.get("vlm_species")
                db_t.vlm_health     = vlm.get("vlm_health")
                db_t.vlm_confidence = vlm.get("vlm_confidence")
                db_t.vlm_notes      = vlm.get("vlm_notes")
        db.commit()

    except Exception as vlm_exc:
        # VLM es OPCIONAL — no fallar el análisis por esto
        logging.getLogger(__name__).warning(f"VLM failed (non-fatal): {vlm_exc}")
        progress_callback(90, "VLM: clasificación omitida (ver logs)")
```

## Columnas DB (Tree model) — migración a6d2596b90d9

```python
vlm_species     = Column(String(100), nullable=True)  # "Pinus sp."
vlm_health      = Column(String(20),  nullable=True)  # "saludable|estresado|enfermo|dudoso"
vlm_confidence  = Column(Float,       nullable=True)  # 0.0-1.0
vlm_notes       = Column(String(255), nullable=True)  # "Copa densa y simétrica"
```

Migración manual (no autogenerate — ver pitfall Alembic PostGIS):
```python
def upgrade() -> None:
    op.add_column('trees', sa.Column('vlm_species',    sa.String(100), nullable=True))
    op.add_column('trees', sa.Column('vlm_health',     sa.String(20),  nullable=True))
    op.add_column('trees', sa.Column('vlm_confidence', sa.Float(),     nullable=True))
    op.add_column('trees', sa.Column('vlm_notes',      sa.String(255), nullable=True))
```

## System prompt y parsing JSON robusto

```python
SYSTEM_PROMPT = """Sos un experto forestal. Analizás recortes de imágenes aéreas de copas de árboles tomadas con drone.
Para cada imagen respondé SOLO con un JSON válido con estas claves:
{"species": "nombre (ej: Pinus sp., Eucalyptus sp., Desconocida)", "health": "saludable|estresado|enfermo|dudoso",
 "confidence": 0.0-1.0, "notes": "observación breve (max 15 palabras)"}
No respondas nada fuera del JSON."""

# Parsing robusto — el modelo a veces ignora "SOLO JSON"
content = data["choices"][0]["message"]["content"].strip()
if "```" in content:
    content = content.split("```")[1].replace("json", "").strip()
match = re.search(r'\{[^}]+\}', content, re.DOTALL)
if match:
    content = match.group(0)
result = json.loads(content)
```

## Pitfalls

- **Crops pequeños → prosa en lugar de JSON:** Si bbox < ~40px, el modelo responde "No puedo identificar..."
  en lugar de JSON. Filtrar antes de enviar (`MIN_CROP_PX = 30`).
- **asyncio.run() en Celery (NO loop.run_until_complete()):** Celery puede tener loop cerrado.
  `asyncio.run()` crea uno nuevo, lo usa y lo cierra limpiamente.
- **aiohttp debe estar en requirements.txt:** No instalarlo solo con `docker exec pip install`.
  Agregar `aiohttp>=3.9.0` a `requirements.txt` y hacer rebuild de imagen.
- **NVIDIA_API_KEY en .env — requiere `docker compose up -d` para recargar:**
  `docker restart` NO recarga `env_file`. Stop+rm+up para que el worker tome la variable nueva.
- **Conversión lat/lon → pixel solo es precisa para ortofotos chicas:** Para ortofotos grandes o
  con proyección compleja, usar la transformada rasterio (`~transform * (lon, lat)`).

## Configuración

- `NVIDIA_API_KEY` en `~/proyectos/forestai-poc/.env`
- Key almacenada en `~/secrets/nvidia_nim_keys.env`
- Si la key no está, el pipeline salta el paso VLM silenciosamente (los campos vlm_* quedan NULL)
