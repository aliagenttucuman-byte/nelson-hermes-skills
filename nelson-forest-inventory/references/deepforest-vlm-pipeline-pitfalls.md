# DeepForest + VLM Pipeline — Pitfalls y Config Correcta
## Caso real: ortomosaicos Tucumán junio 2026

### Score Threshold para ortomosaicos de alta resolución
DeepForest entrenado en NEON (bosques templados EEUU, ~100m altura). En Pix4D a 6 cm/px:
- Default 0.4 → casi nada detectado (parques urbanos, vegetación mixta)
- **Correcto: 0.15** para ortomosaicos de 5-10 cm/px en Argentina/Latinoamérica
- Exponer slider en UI para ajuste en vivo durante demos con stakeholders

### Tiling obligatorio — umbral 20M px (no 178M)
PIL límite: 178M px. Pix4D 6cm/px genera 99M-193M px fácilmente.
**Sin tiling, DeepForest procesa el TIFF entero y no detecta nada en imágenes drone.**
Avellaneda (12622×7887=99M px): 3 árboles sin tiling → 71 con tiling.

```python
TILING_THRESHOLD = 20_000_000  # forzar tile siempre para ortomosaicos
TILE_SIZE = 4096
```

### VLM para clasificación de especie por copa

**NetFlora NO aplica para Tucumán** — 72 especies amazónicas brasileñas. Usar VLM genérico.

Prioridad de backend (`vlm_classifier.py`):
1. OpenAI gpt-4o-mini (~$0.15/1M tok) — primario, `"detail": "low"`
2. Azure Anthropic Claude Sonnet 4.6 — fallback
3. OpenCode API — último recurso

Parámetros correctos:
```python
MIN_CROP_PX = 16    # copas en thumbnails escalados son pequeñas
TARGET_SIZE = 224   # más contexto visual para el modelo
max_trees   = 30    # clasificar más copas por análisis
concurrency = 4     # gpt-4o-mini aguanta más que haiku
```

Para TIFFs grandes (tiling), bbox coords son globales → hacer thumbnail max 8000px
y reescalar los bboxes antes de recortar:
```python
scale = min(8000/full_w, 8000/full_h)
trees_for_vlm = [{"xmin": int(t["xmin"]*scale), "ymin": int(t["ymin"]*scale),
                   "xmax": int(t["xmax"]*scale), "ymax": int(t["ymax"]*scale)} for t in trees]
```

### Pitfall: activación del VLM (bug original)
El código original solo activaba VLM con `OPENCODE_API_KEY` o `NVIDIA_API_KEY`.
Fix obligatorio en `tree_detection.py`:
```python
api_key = (
    os.getenv("OPENAI_API_KEY", "")
    or os.getenv("AZURE_ANTHROPIC_API_KEY", "")
    or os.getenv("OPENCODE_API_KEY", "")
    or os.getenv("NVIDIA_API_KEY", "")
)
```

### Pitfall: watchfiles mata requests largas
`uvicorn --reload` + watchfiles: si se modifica un .py DURANTE procesamiento de TIFF
(2-5 min), el reload mata la request → `curl: (52) Empty reply from server`.

Solución para pruebas largas:
```bash
docker exec forestai-poc-backend-1 python3 /tmp/mi_script.py
```

### Pitfall: docker compose rm rompe auth Postgres
`docker compose stop + rm -f backend + up` puede romper la red interna.
Síntoma: `FATAL: password authentication failed for user "forestai"`.
- Usar `docker compose restart backend` (no rm)
- Si la password se corrompió: resetear desde dentro del container DB:
```bash
docker exec forestai-poc-db-1 psql -U forestai -d forestai -c \
  "ALTER USER forestai WITH PASSWORD 'forestai2024';"
```
- Actualizar DATABASE_URL en .env via script Python (no sed — el terminal enmascara con ***)

### Pitfall: terminal enmascara secrets con ***
`terminal()` y subprocess enmascaran API keys en stdout como `***`.
Para copiar keys entre archivos: escribir script Python con `write_file()` y ejecutarlo.
Nunca pasar keys por shell inline.

### KPIs validados para ReforestLatam
1. **Conteo de copas**: DeepForest (threshold=0.15) + SAM → polígonos por copa ✅
2. **Clasificación de especie**: VLM (gpt-4o-mini) por crop de copa → JSON especie/salud/conf ✅

Resultados reales caso Tucumán (junio 2026):
- 9deJulio.rgb.tif (17094×11327px, 59MB): 154 árboles
- Avellaneda.rgb.tif (12622×7887px, 36MB): 71 árboles, especies: Eucalipto, Pino, dudoso
