# DeepForest — Tuning para Ortomosaicos de Tucumán

## Configuración validada (junio 2026, Parque 9 de Julio)

```python
TILE_SIZE     = 4096   # px — balance detección/velocidad (probado 1024, 2048, 4096)
TILE_OVERLAP  = 256    # px — evita perder copas en bordes entre tiles
score_thresh  = 0.15   # bajo por diferencia de dominio con dataset NEON (bosques EEUU)
```

## Por qué 4096 y no menos
- 1024px: ~110 tiles → muy lento (12x más que 4096), no justifica la mejora marginal
- 2048px: ~28 tiles → balance razonable pero igual lento en CPU
- 4096px: ~15 tiles → tiempo aceptable (~11-15 min en CPU), detección buena con ExG

## ExG (Excess Green Index) — aplicar por tile antes de DeepForest

```python
def _apply_exg(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:,:,0].astype(np.float32), rgb[:,:,1].astype(np.float32), rgb[:,:,2].astype(np.float32)
    exg = 2.0 * g - r - b
    exg_min, exg_max = exg.min(), exg.max()
    exg_norm = ((exg - exg_min) / (exg_max - exg_min) * 255).astype(np.uint8) if exg_max > exg_min else np.zeros_like(r, dtype=np.uint8)
    enhanced = rgb.copy()
    enhanced[:,:,1] = np.clip(rgb[:,:,1] * 0.6 + exg_norm * 0.4, 0, 255).astype(np.uint8)
    enhanced[:,:,0] = np.clip(rgb[:,:,0] * 0.7, 0, 255).astype(np.uint8)
    enhanced[:,:,2] = np.clip(rgb[:,:,2] * 0.7, 0, 255).astype(np.uint8)
    return enhanced
```

Efecto: resalta copas verdes, atenúa suelo y sombra. Mejora detección en dosel continuo.

## NMS post-tiling (eliminar duplicados de tiles solapados)

Ordenar por score desc, suprimir si IoU > 0.5 con algún bbox ya keepeado.
Implementado en `_nms_dataframe()` en `tree_detection.py`.

## Por qué no detecta en ciertas zonas
1. **Dosel continuo** — árboles muy juntos sin bordes visuales entre copas
2. **Subvegetación/arbustos** — verde pero sin forma circular/elíptica de copa
3. **Sombra propia** — copa muy oscura confundida con suelo

## Tiempos reales (imagen 17094×11327 = 193M px, CPU)
- ~15 tiles de 4096px con overlap 256px (step = 3840px)
- ~45 seg/tile en CPU → **~11-15 min total** solo detección
- SAM refinamiento + VLM clasificación adicional encima

## Señal de procesamiento activo
Tiles temporales: `/tmp/tmp*.tif` dentro del container `forestai-poc-backend-1`
```bash
docker exec forestai-poc-backend-1 sh -c "ls /tmp/tmp*.tif 2>/dev/null | wc -l"
```
Si devuelve > 0 → está procesando. Si CPU < 5% y tiles = 0 → terminó o se colgó.

## Watchdog
Cron `forestai-deteccion-watchdog` cada 2 min en `/home/server/.hermes/scripts/forestai_watchdog.sh`
Detecta tiles activos + mide tiempo. Alerta WhatsApp si > 5 min sin terminar.
También notifica cuando la tarea termina.

## Problema Redis URL
La `REDIS_URL` en `.env` puede corromperse si tiene un `@` en la password (eg. email como pass).
Celery interpreta todo lo que sigue al `@` como host → conecta a `gmail.com:6379`.
Fix: sobreescribir con `redis://redis:6379/0` via Python:
```python
import re
content = open('.env').read()
content = re.sub(r'REDIS_URL=.*\n', 'REDIS_URL=redis://redis:6379/0\n', content)
open('.env', 'w').write(content)
```
Luego `docker compose up -d --force-recreate celery_worker backend` (no basta con restart).

## Timeout del spa_proxy
`spa_proxy.py` tiene timeout de `urlopen`. Para análisis largos subir a 3600s:
```python
with urllib.request.urlopen(req, timeout=3600) as resp:
```
El default de 600s corta a los 10 min — el análisis puede durar 15+ min.

## time_limit en Celery task
`analysis_task` debe tener `time_limit=7200, soft_time_limit=6900` para no ser matado:
```python
@celery_app.task(bind=True, time_limit=7200, soft_time_limit=6900)
```
