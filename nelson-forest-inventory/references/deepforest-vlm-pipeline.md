# DeepForest + SAM + VLM Pipeline — Lecciones jun 2026

## KPIs para ReforestLatam
- KPI 1: Conteo de copas (DeepForest + SAM)
- KPI 2: Identificación de especie por copa (VLM — gpt-4o-mini)

## Resultado real: Avellaneda.rgb.tif (12622×7887px, 36MB, Pix4D 6cm/px)
- 71 árboles detectados con tiling 4096px + score_thresh=0.15
- Especies detectadas: Eucalipto (13), Fresno (4), Jacarandá (3), Pino (2), Sauce (1), Algarrobo (1)
- Tiempo total: ~130s (CPU, sin GPU)

## Score threshold crítico
DeepForest devuelve scores 0.12–0.25 en ortomosaicos latinoamericanos (entrenado en NEON/EEUU).
**SIEMPRE usar score_thresh=0.15 para imágenes de 6cm/px.** Con default 0.4 → 3 árboles. Con 0.15 → 71.
Exponer como slider en UI (default 0.15, rango 0.05–0.5).

## Tiling obligatorio para ortomosaicos
PIL rechaza imágenes >178M px (decompression bomb). DeepForest también falla con ortomosaicos completos.
**Usar TILING_THRESHOLD = 20_000_000 px** — cualquier imagen >20M px se divide en tiles de 4096px.
Avellaneda = 99M px → entra en tiling aunque no supera el límite PIL.

```python
PIL_MAX_PIXELS = 178_956_970
TILING_THRESHOLD = 20_000_000  # >20M px → siempre tile
TILE_SIZE = 4096
```

## VLM para especies (en lugar de NetFlora para Tucumán)
NetFlora = 72 especies amazónicas (Açaí, Paxiúba, Castanheira...). NO aplica para NOA.
Para Tucumán usar VLM genérico por copa recortada.

### Prioridad de backends en vlm_classifier.py
1. OpenAI gpt-4o-mini (OPENAI_API_KEY) — primario, ~centavos por ortomosaico
2. Azure Claude Sonnet 4.6 (AZURE_ANTHROPIC_*) — fallback
3. OpenCode — fallback de último recurso

### Condición de activación (pitfall crítico)
El servicio tree_detection.py tenía hardcodeado `os.getenv("OPENCODE_API_KEY")` — nunca activaba OpenAI.
**La condición correcta:**
```python
api_key = (
    os.getenv("OPENAI_API_KEY", "")
    or os.getenv("AZURE_ANTHROPIC_API_KEY", "")
    or os.getenv("OPENCODE_API_KEY", "")
    or os.getenv("NVIDIA_API_KEY", "")
)
```

### Thumbnail para VLM en TIFFs grandes
No cargar el TIFF completo para los crops — genera OOM. Escalar a max 8000px preservando proporción,
luego escalar coords de bboxes proporcionalmente:
```python
max_dim = 8000
if full_w > max_dim or full_h > max_dim:
    scale = min(max_dim / full_w, max_dim / full_h)
    img_thumb = img_full.resize((int(full_w*scale), int(full_h*scale)), Image.LANCZOS)
    trees_for_vlm = [{"xmin": int(t["xmin"]*scale), ...} for t in trees]
```

### Parámetros VLM óptimos para copas de drone
```python
MIN_CROP_PX = 16    # mínimo para pasar al VLM
TARGET_SIZE = 224   # upscale de crops pequeños
PADDING = 12        # padding alrededor del bbox
concurrency = 4     # gpt-4o-mini aguanta más paralelo que Claude Haiku
max_trees = 30      # top 30 por tamaño de copa
detail = "high"     # mejor resolución por crop
```

### Prompt del sistema (Tucumán)
```
"You analyze aerial/drone RGB crop images of individual tree canopies (top-down view)
from Tucumán, Argentina (subtropical region).
Common species: Eucalipto, Pino, Sauce, Álamo, Tipa, Lapacho, Jacarandá, Cedro,
Quebracho, Algarrobo, Fresno, Acacia.
IMPORTANT: Always make your BEST ESTIMATE — never respond with 'dudoso'.
If uncertain, pick most likely species and set confidence 0.3-0.5.
JSON only: {\"species\": \"...\", \"health\": \"saludable|estresado|enfermo\", \"confidence\": 0.6, \"notes\": \"...\"}"
```

## Cloudflare tunnel — límite de upload
Los TIFFs de 30–60MB fallan con `ERR_SSL_BAD_RECORD_MAC_ALERT` en túneles CF free.
**Solución: usar Tailscale directo + spa_proxy.py en :3011** — sin límite de tamaño.
El SPA proxy sirve frontend estático Y rutea /api/* → backend :8010.
URL Tailscale: http://100.110.8.13:3011/

## uvicorn --reload mata requests largas
El volume mount `./backend:/app` + `command: uvicorn ... --reload` recarga el server
cuando cambia cualquier archivo .py, matando requests en vuelo (curl (52) Empty reply).
**Para producción/demo: quitar --reload, usar --workers 2 --timeout-keep-alive 300.**
```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --timeout-keep-alive 300
```

## Password DB en docker-compose
La password del usuario forestai en pgdata se fija la primera vez que se levanta el container DB.
Si se cambia en docker-compose.yml pero pgdata ya existe, Postgres sigue usando la vieja.
**Fix:** resetear la password vía psql desde dentro del container DB:
```bash
docker exec forestai-poc-db-1 psql -U forestai -d forestai -c "ALTER USER forestai WITH PASSWORD 'nuevapass';"
```
Luego actualizar DATABASE_URL en .env con la misma password.

## Editar .env desde Python (no desde terminal)
El terminal de Hermes enmascara valores de variables sensibles con `***`, lo que rompe
scripts de sed/awk que intentan reemplazar valores. **Siempre editar .env con Python directo:**
```python
path = '/home/server/proyectos/forestai-poc/.env'
with open(path) as f:
    lines = f.readlines()
new_lines = []
for line in lines:
    if line.startswith('DATABASE_URL='):
        new_lines.append('DATABASE_URL=postgresql://forestai:forestai2026@db:5432/forestai\n')
    else:
        new_lines.append(line)
with open(path, 'w') as f:
    f.writelines(new_lines)
```
Verificar con: `any('2026' in line for line in open(path) if 'DATABASE_URL' in line)`

## Por qué DeepForest no detecta en zonas verdes visibles
Tres causas principales en ortomosaicos de parque urbano/campo Tucumán:
1. **Dosel continuo** — árboles muy juntos sin borde visual entre copas
2. **Subvegetación/arbustos** — verde bajo sin forma circular de copa
3. **Sombra propia intensa** — copa cerrada parece suelo oscuro al modelo
Mejora inmediata: reducir tile size a 1024px con overlap para que copas ocupen más % del frame.
