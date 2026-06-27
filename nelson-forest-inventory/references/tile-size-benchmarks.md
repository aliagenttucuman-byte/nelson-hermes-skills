# ForestAI — Benchmarks de Tile Size y Filtro ExG

## Imagen de referencia: Parque Avellaneda (12622×7887px = 99.5M px)

| Config | Tiles procesados | Árboles detectados | Tiempo CPU | Notas |
|--------|-----------------|-------------------|------------|-------|
| 4096px sin filtro | 12/12 | 173 | 3 min | incluye ciudad |
| 2048px sin filtro | 40/40 | 624 | 7 min | incluye ciudad |
| 2048px + ExG 12% | ~12/40 | 220 | 3.5 min | solo parque ✅ |
| 1024px + ExG 12% | ~40/140 | 1067 | 11 min | solo parque, máx detalle ✅ |

## Regla de overlap

TILE_OVERLAP = TILE_SIZE / 8

| TILE_SIZE | TILE_OVERLAP |
|-----------|-------------|
| 4096px | 512px |
| 2048px | 256px |
| 1024px | 128px |

Con overlap proporcional el NMS trabaja limpio sin duplicados excesivos.

## Filtro ExG (_tile_has_vegetation)

```python
VEG_THRESHOLD = 0.12  # 12% de píxeles con ExG > 20 para procesar el tile

def _tile_has_vegetation(rgb, threshold=VEG_THRESHOLD):
    r, g, b = rgb[:,:,0].astype(float), rgb[:,:,1].astype(float), rgb[:,:,2].astype(float)
    exg = 2.0 * g - r - b
    veg_pixels = np.sum(exg > 20)  # ExG > 20 = verde significativo
    return (veg_pixels / (rgb.shape[0] * rgb.shape[1])) >= threshold
```

El umbral 20 en ExG separa bien vegetación de asfalto/edificios en imágenes RGB de drone urbano.
El umbral 12% de píxeles verdes funciona para parques urbanos con mezcla ciudad/verde.

## Estimación GPU para procesamiento en <20 minutos

Imagen 12622×7887px, tiles 1024px + ExG:
- CPU (sin GPU): 11 minutos, 1067 árboles
- RTX 3060/3070 (8-12GB VRAM): ~1.5 minutos (factor 7-10x)
- RTX 3090 / A10 (24GB VRAM): ~45 segundos (tiles en paralelo)
- AWS A10 cloud: ~$0.75/hora → centavos por imagen

## Bandas del ortomosaico

Los TIFFs de drone Tucumán tienen 4 bandas RGBA:
- Banda 1: Rojo (R)
- Banda 2: Verde (G)
- Banda 3: Azul (B)
- Banda 4: Alpha (transparencia) — NO es NIR

Para NIR real se necesita sensor multiespectral (MicaSense, Parrot Sequoia).
Con RGB+Alpha solo: ExG es el mejor índice de vegetación disponible.

## Parque 9 de Julio (imagen grande)

17094×11327px = 193M px — requiere PIL decompression bomb fix:
```python
PIL.Image.MAX_IMAGE_PIXELS = 178_956_970  # o None para deshabilitar
```
Con 4096px: 15 tiles, 257 árboles, 7 min CPU.

## Compliance con ReforestLatam

NO mencionar en la demo:
- DeepForest (weecology/deepforest-tree, 124MB, RetinaNet)
- SAM (Segment Anything Model)
- claude-haiku-4-5 (VLM para clasificación de especies)
- Stack técnico completo

Hasta cerrar acuerdo comercial con Gino y ReforestLatam.
