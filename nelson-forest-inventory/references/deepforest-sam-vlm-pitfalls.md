# DeepForest + SAM + VLM — Pitfalls y Fixes (caso real Tucumán, jun 2026)

## KPI 1 — Conteo de copas

### score_thresh crítico
DeepForest entrenado en bosques EEUU (NEON dataset). En ortomosaicos Tucumán (6 cm/px):
- Score promedio por copa: 0.15–0.25 (no 0.4+ del entrenamiento EEUU)
- **Usar score_thresh=0.15** para Latinoamérica. Con 0.4 (default): Avellaneda → 3 árboles. Con 0.15 → 71 árboles.

### Umbral de tiling
No usar PIL_MAX_PIXELS (178M) como umbral de tiling. Todo ortomosaico de drone real supera 20M px.
**Usar TILING_THRESHOLD = 20_000_000**. Con tiles de 4096px:
- Avellaneda (12622×7887 = 99M px): 8 tiles → 71 árboles ✅
- 9deJulio (17094×11327 = 193M px): 12 tiles → 154 árboles ✅

```python
PIL_MAX_PIXELS = 178_956_970       # límite PIL
TILING_THRESHOLD = 20_000_000      # >20M px → siempre tile
TILE_SIZE = 4096
```

## KPI 2 — Clasificación de especie (VLM)

### Prioridad de modelos VLM (costo/beneficio)
1. `gpt-4o-mini` (OpenAI) — principal, centavos por ortomosaico, rápido
2. `claude-sonnet-4-6` (Azure AI Foundry) — fallback de calidad
3. OpenCode / NVIDIA — fallback final

### Pitfall: gate de activación del VLM
El código original chequea solo `OPENCODE_API_KEY` o `NVIDIA_API_KEY`.
Al agregar OpenAI como primario, actualizar la condición en `tree_detection.py`:

```python
api_key = (
    os.getenv("OPENAI_API_KEY", "")
    or os.getenv("AZURE_ANTHROPIC_API_KEY", "")
    or os.getenv("OPENCODE_API_KEY", "")
    or os.getenv("NVIDIA_API_KEY", "")
)
```
Sin este fix: VLM silenciosamente skipeado aunque la key esté configurada → 0/N clasificados.

### Pitfall: VLM + tiling + coords globales
Con tiling, las bboxes de árboles tienen coords **globales** sobre el TIFF completo.
El VLM necesita hacer crops sobre una imagen que quepa en RAM. Fix obligatorio:

```python
Image.MAX_IMAGE_PIXELS = None
with Image.open(image_path) as img_full:
    full_w, full_h = img_full.size
    max_dim = 6000
    if full_w > max_dim or full_h > max_dim:
        scale = min(max_dim / full_w, max_dim / full_h)
        img_thumb = img_full.resize(
            (int(full_w * scale), int(full_h * scale)), Image.LANCZOS
        )
        # Escalar coords globales al thumbnail
        trees_for_vlm = [
            {
                "xmin": int(t["xmin"] * scale),
                "ymin": int(t["ymin"] * scale),
                "xmax": int(t["xmax"] * scale),
                "ymax": int(t["ymax"] * scale),
            }
            for t in trees
        ]
    else:
        img_thumb = img_full.copy()
image_np_vlm = np.array(img_thumb.convert("RGB"))
```
Sin este fix: vlm_classifier intenta hacer crops en una imagen que no matchea las coords → 0 clasificados, sin errores visibles en logs.

### vlm_classifier.py — prioridad de backends
```python
if OPENAI_API_KEY:
    # gpt-4o-mini, OpenAI API, image_url con detail="low"
    ...
elif AZURE_ANTHROPIC_BASE_URL and AZURE_ANTHROPIC_API_KEY:
    # claude-sonnet-4-6, endpoint /v1/messages, formato Anthropic nativo
    # Header: x-api-key + anthropic-version: 2023-06-01
    # Imagen: source.type="base64", NO image_url
    ...
else:
    # OpenCode fallback (OpenAI-compatible)
    ...
```
Anthropic nativo y OpenAI tienen formatos de imagen DISTINTOS — no son intercambiables.

## Transporte de TIFFs grandes (30–60MB)

- **Cloudflare tunnel free:** NO funciona para uploads >~10MB desde browser (ERR_SSL_BAD_RECORD_MAC_ALERT)
- **Solución:** Tailscale → proxy SPA en `:3011` → sin límite de tamaño
- `spa_proxy.py` en `:3011`: sirve frontend estático + rutea `/api/*` → `:8010` sin SSL

## Edición de .env con secrets — pitfall del terminal

El terminal enmascara valores con `***` en la salida. Si se usa `sed` inline o `read + write`
con el contenido enmascarado, las passwords quedan como `***` literal.

**Síntoma:** backend crashea con `FATAL: password authentication failed for user "forestai"`.

**Fix:** escribir siempre un script Python a `/tmp/fix.py` y ejecutarlo:
```python
# /tmp/fix_env.py
import re, os
hermes = open(os.path.expanduser('~/.hermes/.env')).read()
proj = open('/path/to/project/.env').read()
# Copiar key completa de hermes a proyecto sin pasar por shell
key = re.search(r'OPENAI_API_KEY=([^\n]+)', hermes).group(1).strip()
proj = re.sub(r'^OPENAI_API_KEY=.*$', f'OPENAI_API_KEY={key}', proj, flags=re.M)
open('/path/to/project/.env', 'w').write(proj)
```
Verificar longitud: `sk-proj-` keys tienen ~164 chars. Si len < 50 → truncada.

## Recreación de containers (docker compose rm)

`docker compose stop + rm -f backend + up` puede romper el network si otros containers
(db, redis) siguen corriendo. El nuevo container backend puede no resolver `db` por hostname.

**Patrón seguro para recargar .env sin romper nada:**
```bash
docker compose up -d --force-recreate backend   # NO usar rm -f
```
Si el backend crashea por DB auth tras recreación:
1. `docker exec forestai-poc-db-1 psql -U forestai -d forestai -c "ALTER USER forestai WITH PASSWORD 'nueva_pass';"`
2. Actualizar DATABASE_URL en `.env` via Python script
3. `docker compose up -d backend`
