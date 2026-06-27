# DeepForest — Pitfalls para Ortomosaicos de Tucumán

## 1. score_thresh crítico
DeepForest entrenado en NEON dataset (bosques EEUU, copas grandes bien separadas).
Ortomosaicos Tucumán a 6 cm/px → domain shift → scores bajos (~0.12–0.20).

**SIEMPRE usar score_thresh=0.15** (default 0.4 filtra casi todo):
```python
model.config["score_thresh"] = 0.15
```
Resultado real: Avellaneda con 0.4 → 3 árboles. Con 0.15 → 21+ árboles por tile central.

## 2. Tiling automático para TIFFs grandes
PIL rechaza imágenes > 178M px (PIL.DecompressionBombError).
- 9deJulio.rgb.tif: 17094×11327 = 193M px → NECESITA tiling
- Avellaneda.rgb.tif: 12622×7887 = 99.5M px → borderline

Fix en `tree_detection.py`:
```python
PIL_MAX_PIXELS = 178_956_970
TILE_SIZE = 4096

needs_tiling = (w * h) > PIL_MAX_PIXELS
if needs_tiling:
    predictions, w, h = _tile_and_detect(image_path, model)
```

`_tile_and_detect()`:
- Usa rasterio.Window para leer tiles sin cargar el TIFF completo
- Suma offset (x0, y0) a cada bbox antes de consolidar en DataFrame global
- Guarda tile como PNG temporal → DeepForest → elimina
- 9deJulio completo (12 tiles): 154 árboles, ~4.5 min en CPU

En el **endpoint de upload** (api/v1/tree_detection.py), agregar ANTES de llamar al servicio:
```python
from PIL import Image as _PILImage
_PILImage.MAX_IMAGE_PIXELS = None  # el servicio lo maneja con tiling
```

## 3. Upload vía Cloudflare vs Tailscale
Cloudflare free tunnel: ERR_SSL_BAD_RECORD_MAC en uploads > ~10MB.
**Regla: TIFFs grandes siempre por Tailscale.**

Acceso: `http://100.110.8.13:3011/` (spa_proxy.py :3011)
spa_proxy.py rutea /api/* → backend :8010 sin límite de tamaño (timeout=600s).

CF tunnel sirve solo para: demo UI sin uploads, imágenes pequeñas (< 5MB).

## 4. NetFlora — solo Amazonía
NetFlora (Embrapa/JBS, 72 especies) entrenado exclusivamente en Amazonía Occidental.
Especies detectables: Açaí, Paxiúba, Burití, Copaíba, Cedro, Samaúma, Castanheira...

Tucumán nativo: Quebracho, Tipa, Cebil, Lapacho, Algarrobo, Palo Blanco → NO en catálogo.
Uso válido: demo conceptual del pipeline de detección de especies.
NO usar como KPI real de especie para proyectos tucumanos.

## 5. KPI 2 — Identificación de especie para Tucumán
Opciones reales ordenadas por factibilidad:
1. **VLM por copa** (Claude Vision / GPT-4o): recortar cada copa detectada por SAM,
   preguntar "¿qué especie de árbol es esta copa vista desde drone en Tucumán, Argentina?"
   Ya integrado en pipeline (campo vlm_species en TreeBox). Falta API key en server.
   Costo: ~$0.01-0.05 por imagen procesada.
2. **NetFlora como proxy**: muestra categorías aunque no sean exactas. Útil para demo.
3. **Fine-tune DeepForest**: requiere dataset etiquetado de especies tucumanas. Meses + recursos.

## 6. Datos de los ortomosaicos reales (junio 2026)
| Campo | 9deJulio.rgb.tif | Avellaneda.rgb.tif |
|-------|-----------------|-------------------|
| Tamaño | 59MB | 36MB |
| Dimensiones | 17094×11327px | 12622×7887px |
| Bandas | 4 (RGBA) uint8 | 4 (RGBA) uint8 |
| CRS | EPSG:32720 | EPSG:32720 |
| Resolución | ~6 cm/px | ~6 cm/px |
| Software | Pix4Dfields 2.12.1 | Pix4Dfields 2.12.1 |
| Fecha vuelo | 16/05/2026 | 16/05/2026 |
| Tipo área | Zona tucumana | Parque urbano arbolado |
| Árboles detectados | 154 (threshold 0.15) | 21+ por tile central |

Bandas RGB+alpha: NDVI no aplicable. VARI/ExG posibles para índices de vegetación visual.
