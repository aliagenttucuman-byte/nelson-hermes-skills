# DeepForest — Mejoras de Detección (2026-06-09)

## Problema original

El modelo DeepForest entrenado en NEON (bosques EEUU, ~100m altura, copas 3-10m) detecta mal
en ortomosaicos de Tucumán a 6cm/px desde ~50m. Zonas con vegetación evidente devolvían 0 detecciones.

## Causas identificadas

1. **Dosel continuo** — árboles juntos sin separación visual entre copas. DeepForest busca copas individuales con sombra propia.
2. **Subvegetación/arbustos** — pasto alto o arbustos no tienen la forma circular/elíptica esperada.
3. **Sombra propia** — copas oscuras por sombra interna confundidas con suelo oscuro.
4. **Diferencia de dominio** — imágenes de alta resolución con más textura/detalle que el training set.

## Mejoras implementadas en `tree_detection.py`

### 1. ExG (Excess Green Index)

```python
def _apply_exg(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:,:,0].astype(float), rgb[:,:,1].astype(float), rgb[:,:,2].astype(float)
    exg = 2.0 * g - r - b  # rango -255 a +510
    # Normalizar y mezclar con original
    exg_norm = ((exg - exg.min()) / (exg.max() - exg.min()) * 255).astype(np.uint8)
    enhanced = rgb.copy()
    enhanced[:,:,1] = np.clip(rgb[:,:,1]*0.6 + exg_norm*0.4, 0, 255).astype(np.uint8)
    enhanced[:,:,0] = np.clip(rgb[:,:,0]*0.7, 0, 255).astype(np.uint8)
    enhanced[:,:,2] = np.clip(rgb[:,:,2]*0.7, 0, 255).astype(np.uint8)
    return enhanced
```

Aplicado a cada tile ANTES de dárselo a DeepForest. Resalta vegetación aumentando el canal verde.

### 2. Overlap entre tiles

```python
TILE_SIZE = 4096
TILE_OVERLAP = 256
step = TILE_SIZE - TILE_OVERLAP  # = 3840px
```

El tiling original (sin overlap) perdía copas en los bordes de cada tile. Con overlap 256px
las copas del borde aparecen en dos tiles consecutivos → el NMS elimina el duplicado.

### 3. NMS post-tiling

```python
def _nms_dataframe(df, iou_threshold=0.5):
    # Ordena por score desc, suprime bboxes con IoU > 0.5 respecto a bbox mayor score
```

Elimina duplicados generados por el overlap. Sin esto, una copa en el borde aparecía dos veces.

### 4. Tiles residuales pequeños ignorados

```python
if tw < 128 or th < 128:
    continue
```

Evita procesar bordes de 5px que no aportan detecciones y generan warnings.

## Resultado esperado vs realidad

| Config | Tiles | Velocidad | Detección |
|--------|-------|-----------|-----------|
| 4096px sin overlap (original) | 9 | ~4.5 min | Baja |
| 1024px overlap 128px | ~110 | >30 min | Alta pero inviable |
| 2048px overlap 256px | ~25 | ~12 min | Media-alta |
| **4096px overlap 256px + ExG + NMS** | ~9 | ~5 min | Media+ |

| **4096px overlap 256px + ExG + NMS (DEFINITIVO)** | ~15 | ~10-15 min | Media+ |

**Elección final de Nelson (2026-06-09 sesión 3):** 4096px con overlap 256px — confirmado definitivamente después de probar 1024px (demasiado lento) y 2048px (descartado). ExG + NMS compensan la granularidad.

**Tiempo real 9deJulio (193Mpx, ~15 tiles):** ~10-15 min en CPU. Avisar al usuario antes de lanzar.

## Mejoras futuras (no implementadas)

- Fine-tuning con 200-300 copas etiquetadas en ortofotos de Tucumán
- Modelo especializado en vegetación subtropical
- Pre-filtrado por máscara de vegetación (VARI > umbral) antes de tiling
