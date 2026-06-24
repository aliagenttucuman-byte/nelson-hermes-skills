# Ortomosaicos Tucumán — Caso Real (Junio 2026)

## Archivos recibidos

| Archivo | Tamaño | Dimensiones | Bandas |
|---|---|---|---|
| `9deJulio.rgb.tif` | 59MB | 17094×11327 px | 4 (RGBA uint8) |
| `Avellaneda.rgb.tif` | 36MB | 12622×7887 px | 4 (RGBA uint8) |

Paths en el server (actualizados 2026-06-10 — usar estos):
- `/home/server/.hermes/document_cache/doc_7a6ea9f8381b_9deJulio.rgb.tif`
- `/home/server/.hermes/document_cache/doc_877ea5356955_Avellaneda.rgb.tif`
- `/home/server/proyectos/forestai-poc/uploads/055422ad-92da-4ac9-8a96-abea4b7629b2.tif`
- `/home/server/proyectos/forestai-poc/uploads/f96fd29a-433d-4d78-9714-24ac1a643225.tif`

**YOLOv fine-tuning:** Para comparativas de modelos YOLO sobre estos TIFs, ver skill
`nelson-yolov-finetuning` y repo `github.com/aliagenttucuman-byte/yolov-orientacion-poc`.
NO mezclar con ForestAI (proyectos separados, objetivos distintos).

## Metadata técnica

- **CRS:** EPSG:32720 (UTM Zona 20S) — correcto para Tucumán
- **Resolución:** ~6 cm/px — excelente para análisis de dosel
- **Software:** Pix4Dfields 2.12.1
- **Fecha vuelo:** 16/05/2026
- **Departamentos:** 9 de Julio y Avellaneda (Tucumán, Argentina)

## IMPORTANTE — Son RGB, NO multiespectrales

Las 4 bandas son RGBA (Red, Green, Blue, Alpha) uint8, NO tienen NIR.
La 4ta banda es **Alpha (transparencia)**, no aporta información espectral útil.
Para mejorar detección de **especies** se necesita drone con sensor multiespectral real (NIR, RedEdge).
Con RGB puro la clasificación por especie depende del VLM (claude-haiku), no del sensor.

Por lo tanto:
- ❌ NDVI no se puede calcular (requiere NIR)
- ❌ EVI no se puede calcular (requiere NIR)
- ❌ La 4ta banda (Alpha) NO mejora la detección — ignorarla
- ✅ VARI (Visible Atmospherically Resistant Index) = (G-R)/(G+R-B)
- ✅ ExG (Excess Green) = 2G - R - B
- ✅ Detección de cobertura de dosel visual
- ✅ Conteo de plantas / árboles por segmentación RGB
- ✅ Análisis de cobertura suelo/vegetación

## KPIs objetivo para ReforestLatam

1. **Conteo de copas** (cuántos árboles hay) → DeepForest
2. **Identificación de especie por copa** → NetFlora (YOLOv5 de Embrapa)

## DeepForest + SAM — Verificado funcionando (2026-06-09)

### Stack instalado en container `forestai-poc-backend-1`

| Componente | Versión | Estado |
|---|---|---|
| deepforest | 2.1.0 | ✅ instalado |
| segment-anything | 1.0 | ✅ instalado |
| SAM checkpoint | sam_vit_b.pth | ✅ en `/tmp/sam_models/` (se pierde con reinicio) |
| NetFlora repo | YOLOv5 custom | ✅ en `/app/netflora_repo/` |

### Pipeline completo

```
TIFF → tile 4096×4096 → DeepForest (bboxes copas) → SAM (polígonos refinados) → NetFlora (especie)
           ↓
    KPI 1: tree_count         +   KPI 2: vlm_species por copa
```

### Resultado real — TIFF completo 9deJulio (tiling automático)

#### Sesión 2026-06-09 (con ExG + NMS + overlap 256px + SAM + VLM)
- **257 árboles detectados** en el TIFF completo (17094×11327px, 15 tiles de 4096px con overlap 256px)
- SAM activo: 257 copas refinadas (tardó ~4 min en CPU)
- VLM (claude-haiku): 30/257 árboles clasificados por especie
- Tiempo total pipeline: **425 segundos (~7 minutos)** en CPU sin GPU
- Task Celery ID: `656d40af-0675-4031-9618-14f0c4af9caf`

#### Sesión anterior (sin ExG, sin NMS, sin overlap)
- **154 árboles detectados** en el TIFF completo (17094×11327px, 12 tiles de 4096px)
- SAM activo: polígonos refinados por copa (sam_score ~0.95, stability ~0.98)
- Tiempo de procesamiento: ~4.5 minutos (CPU, sin GPU)
- VLM/NetFlora: no corrió (sin API key configurada)

### Resultado real — Avellaneda (tiling automático)

- **3 árboles detectados** con score promedio 0.115 (muy bajo)
- Causa probable: modelo DeepForest entrenado en bosques densos de EEUU — detecta poco en campos agrícolas o vegetación baja de Tucumán
- Solución futura: fine-tuning de DeepForest con imágenes locales

### Resultado real — 9deJulio tile central (4096×4096px) [prueba manual previa]

- **18 árboles detectados** en el tile central
- DeepForest score: 0.22–0.42
- SAM sam_score: ~0.96, stability_score: ~0.98 (muy preciso)
- vlm_species: null (NetFlora no corrió en esta prueba)

### TILING AUTOMÁTICO — parámetros actuales (actualizado 2026-06-09)

El backend de ForestAI ya tiene tiling automático en `backend/app/services/tree_detection.py`.

**Parámetros vigentes (actualizado 2026-06-09 sesión 4):**
```python
TILE_SIZE = 2048        # px por tile — mejor detección de árboles chicos
TILE_OVERLAP = 256      # px de overlap entre tiles — evita perder copas en bordes
TILING_THRESHOLD = 20_000_000  # >20Mpx → tiling automático
```

**Historial de decisiones tile size:**
- 4096px (original, sin overlap): ~9 tiles para 9deJulio — rápido pero perdía copas en bordes
- 1024px overlap 128px: ~110 tiles — mejor detección pero ~10x más lento (inviable en demos, descartado)
- 4096px overlap 256px + ExG + NMS: Nelson usó en sesiones 2-3, 173 árboles en Avellaneda, 257 en 9deJulio
- **2048px overlap 256px (actual, sesión 4)**: Nelson eligió para mejorar detección de árboles chicos — ~48 tiles para 9deJulio, estimado 250-350 árboles, ~8-10 min en CPU

**Tiempo real verificado con imagen 9deJulio (193M px, 15 tiles 4096px):** ~10-15 min en CPU.

**FIX DEFINITIVO para timeouts (2026-06-09):** La detección ahora corre async en Celery.
- `POST /upload` devuelve `task_id` inmediato (no bloquea el request HTTP)
- `GET /status/{task_id}` para polling cada 5s desde el frontend
- Task registrado: `app.tasks.tree_detection_task` con `time_limit=7200`
- Si el proceso muere (CPU <1%, tiles con timestamps viejos) → reiniciar container y resubir

**Watchdog:** `/home/server/.hermes/scripts/forestai_watchdog.sh` — cron cada 2 min, alerta WhatsApp si detección >5 min sin terminar.

**Nota para demos:** imagen 9deJulio (17094×11327 = 193Mpx) tarda ~10-15 min con 4096px. 
Con 15 tiles × ~45s/tile en CPU. Advertir al stakeholder antes de lanzar.

**Nota:** el overlap 256px es la mejora real respecto al tiling original (que no tenía overlap). El tamaño 4096px es el mismo de antes pero ahora con ExG + NMS.

Cuando el TIFF supera 20Mpx, `run_tree_detection()` llama a `_tile_and_detect()` que:
1. Divide el TIFF en tiles 2048×2048px con overlap 256px usando rasterio (step = TILE_SIZE - TILE_OVERLAP)
2. Aplica ExG (Excess Green = 2G - R - B) para resaltar vegetación en cada tile
3. Corre DeepForest en cada tile (score_thresh=0.15)
4. Aplica offset de coordenadas al espacio global
5. Ejecuta NMS (IoU > 0.5) para eliminar duplicados del overlap
6. Retorna DataFrame consolidado

Ver `references/deepforest-detection-improvements.md` para detalles de cada mejora.

**Resultado verificado (pre-mejora, tile 4096px):** `9deJulio.rgb.tif` → **154 árboles detectados**.

El endpoint también desactiva `PIL.Image.MAX_IMAGE_PIXELS = None` antes de procesar:
```python
from PIL import Image as _PILImage
_PILImage.MAX_IMAGE_PIXELS = None  # en api/v1/tree_detection.py
```

### PITFALL CRÍTICO — límite de píxeles PIL (ya resuelto en backend)

```
"Image size (193623738 pixels) exceeds limit of 178956970 pixels, could be decompression bomb DOS attack."
```

Los TIFFs de 17094×11327px (193M px) **superan el límite de PIL**. El backend ya lo resuelve con tiling.
Si se procesa manualmente (fuera del endpoint), tilear antes:

```python
import rasterio
from rasterio.windows import Window
from PIL import Image
import numpy as np

SRC = '/path/to/ortomosaico.tif'
with rasterio.open(SRC) as src:
    W, H = src.width, src.height
    cx, cy = W // 2, H // 2
    size = 4096
    x0, y0 = cx - size // 2, cy - size // 2
    window = Window(x0, y0, size, size)
    rgb = np.stack([src.read(1, window=window),
                    src.read(2, window=window),
                    src.read(3, window=window)], axis=-1)

tile_path = '/tmp/tile_center.jpg'
Image.fromarray(rgb).save(tile_path, quality=92)
# Luego subir tile_path al endpoint /api/tree-detection/upload
```

### Endpoints relevantes

| Endpoint | Uso |
|---|---|
| `POST /api/analyses` | Pipeline completo (forest_analyzer.py — OBIA/watershed, fallback sin ML) |
| `POST /api/tree-detection/upload` | **DeepForest + SAM** — usar este para KPI 1+2 |
| `POST /api/netflora/upload` | NetFlora standalone — clasificación de especie |

⚠️ `POST /api/analyses` usa `forest_analyzer.py` (OBIA/watershed sin ML) — puede devolver 0 árboles en TIFFs reales. Para KPIs reales usar `POST /api/tree-detection/upload`.

### forest_analyzer.py — comportamiento con TIFFs grandes

- Hace resampling automático a máx 6000px por lado
- Usa OBIA + watershed en OpenCV, NO DeepForest
- Puede devolver 0 árboles si el campo no tiene vegetación arbórea clara

## PITFALL — Frontend rebuild falla por Docker Hub timeout

### Síntoma
```
failed to solve: node:22-slim: failed to do request: ... dial tcp 54.144.228.94:443: i/o timeout
```
Docker Hub inaccesible desde el server (ocurre esporádicamente).

### Workaround — editar JS minificado directamente en el container
Si solo hay un cambio de texto en el frontend (no código), editar el bundle en el container en lugar de rebuildar:

```bash
# 1. Encontrar el JS bundle
docker exec forestai-poc-frontend-1 find /usr/share/nginx/html/assets -name "*.js"

# 2. Buscar el texto a cambiar
docker exec forestai-poc-frontend-1 sh -c "grep -o '1024.\{0,15\}' /usr/share/nginx/html/assets/index-*.js | head -3"

# 3. Reemplazar con sed (usar caracteres Unicode directamente, no escapes \x)
docker exec forestai-poc-frontend-1 sh -c \
  "sed -i 's/1024×1024 px, overlap 128px/2048×2048 px, overlap 256px/g' \
   /usr/share/nginx/html/assets/index-*.js"

# 4. Verificar
docker exec forestai-poc-frontend-1 sh -c "grep -o '2048.\{0,10\}' /usr/share/nginx/html/assets/index-*.js | head -1"
```

⚠️ Este cambio se pierde al recrear el container. Cuando Docker Hub vuelva a estar accesible, hacer el rebuild real con `docker compose build frontend`.

## PITFALL — Redis URL corrupta en .env (2026-06-09)

### Síntoma
Celery worker no conecta. Logs muestran:
```
consumer: Cannot connect to redis://redis:***@gmail.com:6379//: Error 101 connecting to gmail.com:6379. Network is unreachable.
```
Celery interpreta `redis` como usuario y `gmail.com` como host porque la URL tenía un `@` dentro de la password (ej: una dirección de email como password).

### Diagnóstico
```bash
docker compose logs --tail=30 celery_worker
# Buscar "transport:" en el startup log — muestra la URL real que Celery está usando
```

### Fix
```python
# Pisar la línea REDIS_URL en el .env con Python (el terminal enmascara valores)
import re
with open('/home/server/proyectos/forestai-poc/.env', 'r') as f:
    content = f.read()
new_content = re.sub(r'REDIS_URL=.*\n', 'REDIS_URL=redis://redis:6379/0\n', content)
with open('/home/server/proyectos/forestai-poc/.env', 'w') as f:
    f.write(new_content)
```

### IMPORTANTE: usar `--force-recreate`, no solo `restart`
`docker compose restart` NO toma los nuevos valores del `.env` — el container sigue usando las vars cacheadas.
```bash
docker compose up -d --force-recreate celery_worker backend
```

### Verificación
```bash
docker compose logs --tail=15 celery_worker
# Buscar: "Connected to redis://..." — si aparece, está OK
```

## Acceso desde Windows (nelsondev) por Tailscale

**PITFALL:** El túnel Cloudflare Free falla con TIFFs grandes con error:
```
ERR_SSL_BAD_RECORD_MAC_ALERT
```
Causa: el body del multipart upload se corta en tránsito por límites del túnel free.

**Solución: spa_proxy.py en puerto 3011** — proxy Python puro que:
- Sirve el frontend estático desde `frontend/dist/`
- Rutea `/api/*` → `http://localhost:8010` sin SSL, sin límite de tamaño
- Timeout 600s para uploads largos

Levantar:
```bash
python3 /home/server/proyectos/forestai-poc/spa_proxy.py > /tmp/forestai_proxy.log 2>&1 &
```

Acceder desde Windows (Tailscale):
```
http://100.110.8.13:3011/
```

**PITFALL 2:** Entrar directo a `:3010` (container frontend) falla con:
```
⚠️ Unexpected token '<', "<html> <h"... is not valid JSON
```
Causa: en producción `VITE_API_URL` está vacío → el frontend llama `/api/*` al mismo origen `:3010`, que no tiene backend. **Siempre usar el proxy en :3011.**

## ForestAI SPA Proxy — puerto 3011

```python
import rasterio
import numpy as np

with rasterio.open('ortomosaico.tif') as src:
    r = src.read(1).astype(float)
    g = src.read(2).astype(float)
    b = src.read(3).astype(float)
    alpha = src.read(4)  # máscara válida

# VARI
vari = (g - r) / (g + r - b + 1e-6)

# ExG (Excess Green)
total = r + g + b + 1e-6
exg = 2*(g/total) - (r/total) - (b/total)

# Máscara de vegetación (umbral empírico)
vegetation_mask = exg > 0.1
```

## Apertura con rasterio (ya instalado en el server)

```python
import rasterio
# rasterio==1.4.4 disponible en el sistema
```

## PITFALL — Timeout "timed out is not valid JSON" en frontend

### Síntoma
Después de ~20 min de procesamiento el frontend muestra:
```
Unexpected token 'i', "timed out" is not valid JSON
```

### Causa
El spa_proxy tenía timeout=600s (10 min). Al cortarse, devuelve texto plano "timed out" en lugar de JSON. El frontend intentaba parsearlo como JSON y crasheaba.

### Fix en dos partes

**1. spa_proxy.py** — subir timeout a 3600s (600s era insuficiente para imágenes grandes):
```python
# línea ~37 de spa_proxy.py
with urllib.request.urlopen(req, timeout=3600) as resp:
```

**2. analysis_task.py** — agregar time_limit a Celery:
```python
@celery_app.task(bind=True, time_limit=7200, soft_time_limit=6900)
def run_analysis(self, analysis_id: str, filepath: str):
```

**3. Frontend** — manejar respuesta no-JSON gracefully:
```typescript
if (!res.ok) {
  let errMsg = "Error en el servidor";
  try { const err = await res.json(); errMsg = err.detail || errMsg; }
  catch { errMsg = await res.text().catch(() => errMsg); }
  throw new Error(errMsg);
}
```

Después de editar spa_proxy.py, reiniciarlo:
```bash
pkill -f spa_proxy.py
cd /home/server/proyectos/forestai-poc && python3 spa_proxy.py > /tmp/forestai_proxy.log 2>&1 &
ss -tlnp | grep 3011  # verificar que está escuchando
```

## ARQUITECTURA ASYNC — Fix definitivo para timeouts (2026-06-09)

### Problema raíz
El endpoint `/api/tree-detection/upload` corría síncrono dentro del request HTTP. Con 193M px (~15 tiles × 45s = 11 min), uvicorn/proxy cortaban la conexión antes de terminar. El thread moría silenciosamente dejando tiles `/tmp/tmp*.tif` huérfanos.

### Diagnóstico de proceso zombie
```bash
docker exec forestai-poc-backend-1 sh -c 'ls -la /tmp/tmp*.tif 2>/dev/null'
docker stats --no-stream forestai-poc-backend-1
```
Si los tiles tienen timestamps viejos (>10 min) y CPU < 1% → tarea muerta. Reiniciar el container y volver a subir.

### Fix: Celery async + polling frontend
1. `backend/app/tasks/tree_detection_task.py` — task con `time_limit=7200`
2. Registrado en `celery_app.py` → `include=[..., "app.tasks.tree_detection_task"]`
3. `POST /upload` devuelve `{"task_id": "...", "status": "PENDING"}` inmediato
4. `GET /status/{task_id}` para polling (estados: PENDING → PROGRESS → SUCCESS/FAILURE)
5. Frontend hace polling cada 5s hasta SUCCESS/FAILURE

### Watchdog crontab
Script: `/home/server/.hermes/scripts/forestai_watchdog.sh`
- Cron: cada 2 min, entrega WhatsApp
- Detecta tiles activos en container
- Alerta si supera 5 min sin terminar
- Notifica cuando completa

---

## PITFALL — Modelo DeepForest nunca termina de bajar (protocolo xet de HuggingFace)

### Síntoma
El primer procesamiento tarda eternidad o se cuelga. Al inspeccionar el cache:
```bash
docker exec forestai-poc-celery_worker-1 sh -c \
  "find /root/.cache/huggingface/hub/models--weecology--deepforest-tree -name '*.incomplete'"
# Output: .../d37a7af...incomplete  ← modelo parcial, 0 bytes
```

### Causa
HuggingFace usa el protocolo **xet** (chunked download) para modelos grandes. Sin `HF_TOKEN`, el protocolo falla silenciosamente dejando un `.incomplete` de 0 bytes. Cada vez que se carga el modelo, intenta re-descargarlo (y falla igual).

### Fix — descargar forzando HTTP clásico

```bash
# 1. Limpiar incompletos
docker exec forestai-poc-celery_worker-1 sh -c \
  "find /root/.cache/huggingface -name '*.incomplete' -delete && echo OK"

# 2. Descargar con HF_HUB_DISABLE_XET=1 a un directorio temporal
docker exec forestai-poc-celery_worker-1 python3 -c "
import os
os.environ['HF_HUB_DISABLE_XET'] = '1'
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id='weecology/deepforest-tree', filename='model.safetensors', local_dir='/tmp/deepforest_dl')
print('Descargado en:', path)
"

# 3. Copiar al blob correcto del cache HuggingFace
BLOB='d37a7af0b5ba2754282a80d41b4c7b66e8c7149234df5bf3f41bdaf57d329fc8'
docker exec forestai-poc-celery_worker-1 sh -c "
cp /tmp/deepforest_dl/model.safetensors /root/.cache/huggingface/hub/models--weecology--deepforest-tree/blobs/$BLOB
ls -lh /root/.cache/huggingface/hub/models--weecology--deepforest-tree/blobs/$BLOB
"

# 4. Crear symlink en el snapshot (si no existe)
SNAP='/root/.cache/huggingface/hub/models--weecology--deepforest-tree/snapshots/cc21436bc5d572dde8ff5f93c1e71a32f563cace'
docker exec forestai-poc-celery_worker-1 sh -c "
ln -sf '../../blobs/$BLOB' $SNAP/model.safetensors
ls -la $SNAP
"
```

El modelo pesa ~124MB. Verificar descarga completa:
```bash
docker exec forestai-poc-celery_worker-1 sh -c \
  "ls -lh /root/.cache/huggingface/hub/models--weecology--deepforest-tree/blobs/"
# Debe mostrar: 124M  d37a7af...  (sin .incomplete)
```

### Verificar que carga offline (sin red)
```bash
docker exec forestai-poc-celery_worker-1 timeout 60 python3 -c "
import os
os.environ['HF_HUB_OFFLINE'] = '1'
from deepforest import main as df_main
model = df_main.deepforest()
model.load_model(model_name='weecology/deepforest-tree', revision='main')
print('CARGADO OK')
"
# Debe mostrar: CARGADO OK — sin intentar conexión a HF
```

### IMPORTANTE — el cache vive dentro del container
El path `/root/.cache/huggingface` está **dentro** del container, no en un volumen montado. Si el container se recrea (`--force-recreate` o `docker compose down`), el modelo se pierde y hay que repetir el procedimiento.

**Estado actual (2026-06-09):** el modelo fue descargado manualmente y vive en el container. Verificado cargando en modo offline OK (`HF_HUB_OFFLINE=1`, tipo `RetinaNetHub`). Pero si se recrea el container hay que repetir el fix.

**Solución permanente pendiente** (agregar al `docker-compose.yml`):</p>
```yaml
celery_worker:
  volumes:
    - /home/server/.cache/huggingface:/root/.cache/huggingface
```
Así el cache sobrevive recreaciones del container.

⚠️ **PENDIENTE (2026-06-09):** El volumen NO fue agregado todavía al docker-compose.yml. Si se recrea el container hay que repetir el fix de descarga manual. Agregar el volumen antes de la próxima demo.

```yaml
# docker-compose.yml — agregar bajo celery_worker:
celery_worker:
  volumes:
    - /home/server/.cache/huggingface:/root/.cache/huggingface
```

---

## PITFALL — nginx 413 al subir TIFFs grandes desde la UI

### Síntoma
La UI muestra "⚠️ Error en el servidor" al subir una imagen. En los logs del frontend:
```
client intended to send too large body: 61062424 bytes
POST /api/tree-detection/upload HTTP/1.1" 413
```

### Causa
El nginx del container frontend tiene `client_max_body_size` por defecto (1MB). Los TIFFs de parques (~60MB) lo superan.

### Fix — `frontend/nginx.conf`
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    client_max_body_size 500m;   # ← agregar esto

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;    # ← para procesamiento largo
        proxy_send_timeout 600s;    # ← para uploads grandes
        client_max_body_size 500m;  # ← también aquí
    }
}
```

Recargar sin reiniciar el container:
```bash
docker exec forestai-poc-frontend-1 nginx -s reload
```

⚠️ Este fix ya está aplicado en `frontend/nginx.conf`. Si se reconstruye el container, ya queda incluido.

---

## Pipeline completado — resultados verificados sesión 2026-06-09 (segunda ejecución)

Segunda imagen procesada (más chica) en la misma sesión:
- 62 árboles detectados
- Tiempo total: **38 segundos** (imagen chica, sin tiling)
- SAM=sí, VLM=sí
- Especies identificadas por VLM: Eucalipto (saludable, 0.7), Acacia (estresado, 0.4)

## GPU requerida para procesar en 20 min con tiles de 1024px

Análisis para imagen 9deJulio (17094×11327px):

| Tile size | Tiles totales | Tiempo CPU | Tiempo con GPU |
|-----------|--------------|------------|----------------|
| 4096px (actual) | 15 | ~7 min | ~1 min |
| 2048px | ~45 | ~25 min | ~3 min |
| 1024px | ~345 | ~2.5-3 hs | ~20 min |

GPU mínima recomendada para 1024px en 20 min: **RTX 3070 (8GB VRAM)**
- Factor aceleración DeepForest+SAM en GPU: 10-15x sobre CPU
- Costo cloud (A10): ~$0.75/hora → centavos por imagen

Con tiles más chicos se detectan más árboles pequeños pero NO mejora clasificación de especies (eso depende del VLM, no del tile size).

## PITFALL — Demo /demo muestra texto de modelos internos

Nelson exige que la demo para stakeholders externos (ReforestLatam) NO revele los modelos internos usados (DeepForest, SAM, VLM, claude-haiku). Razón: compliance y acuerdos comerciales pendientes con ReforestLatam.

En la vista `/demo`:
- NO mencionar "DeepForest", "SAM", "RetinaNet", "VLM", "claude-haiku" en ningún texto visible
- NO mostrar pasos del pipeline durante el loading (ni el listado de tecnologías)
- Loading state: solo el spinner doble (🌲 girando) + texto "Procesando..."
- NO mostrar el header interno del TreeDetectionPanel ("DeepForest + SAM · Detección y segmentación de copas")
- NO mostrar columna izquierda (filtros de confianza, pipeline steps, textos explicativos)

Implementado ocultando elementos con CSS en `DemoReforestLatam.tsx`:
```css
/* Ocultar header interno del TreeDetectionPanel */
.demo-wrap > div > div:first-child { display: none !important; }
/* Ocultar columna izquierda */
.demo-wrap > div > div:nth-child(2) > div:first-child { display: none !important; }
```

## Resultados verificados Avellaneda — sesión 2026-06-09 (sesiones 3, 4 y 5)

Imagen: `Avellaneda.rgb.tif` — 12622×7887px, 99.5M px, ~36MB

### Comparativa tile size (misma imagen, mismo parque)

| Configuración | Árboles detectados | Tiles procesados | Tiempo CPU | Observaciones |
|---|---|---|---|---|
| 4096px overlap 256px sin filtro | 173 | 12/12 | ~3 min | Ciudad incluida |
| 2048px overlap 256px sin filtro | 624 | 40/40 | ~3.2 min | Ciudad incluida, ruido |
| 2048px overlap 256px + filtro ExG | 220 | ~12/40 | ~3.5 min | ✅ Solo parque |
| 1024px overlap 128px + filtro ExG | 1067 | ~50/140 | ~10 min estimado | Solo parque, más árboles chicos |

**Conclusión clave:** el filtro ExG (VEG_THRESHOLD=0.12) elimina correctamente los tiles urbanos — de 40 tiles totales solo ~12 tienen vegetación suficiente para procesar. El número real del inventario del parque es **220 árboles** con 2048px+ExG.

### Parámetros actuales (2026-06-09 sesión 5)
```python
TILE_SIZE = 1024               # px por tile
TILE_OVERLAP = 128             # px de overlap (12.5% del tile — misma proporción que 2048+256)
VEG_THRESHOLD = 0.12           # mínimo 12% píxeles verdes (ExG > 20) para procesar tile
```

**Regla de proporción overlap:** mantener overlap/tile_size ≈ 12.5% para que el NMS funcione igual de limpio independientemente del tile size. Cuando se cambia TILE_SIZE, cambiar TILE_OVERLAP proporcionalmente.

### Resultado real con 1024px + overlap 128px + filtro ExG — Avellaneda (sesión 5)

- **1067 árboles detectados** — solo parque, sin ciudad
- ~140 tiles totales → ~50 procesados (resto saltados por ExG)
- SAM refinó 1067 copas (~8 min en CPU)
- VLM clasificó 30 especies
- Tiempo total: **663 segundos (~11 minutos)** en CPU
- Task Celery: `54f44e80-7b78-4beb-aca9-8ddbc19d7a2a`

**Comparativa definitiva Avellaneda:**

| Config | Árboles | Tiles proc/total | Tiempo | Ciudad incluida |
|--------|---------|-----------------|--------|----------------|
| 4096px overlap 256px sin filtro | 173 | 12/12 | 3 min | ✅ sí |
| 2048px overlap 256px sin filtro | 624 | 40/40 | 3.2 min | ✅ sí |
| 2048px overlap 256px + ExG | 220 | ~12/40 | 3.5 min | ❌ no |
| 1024px overlap 128px + ExG | 1067 | ~50/140 | 11 min | ❌ no |

**Conclusión:** 1024px + ExG detecta 5x más árboles que 2048px + ExG dentro del parque. Trade-off: 3x más tiempo. Recomendado para inventario real; usar 2048px para demos rápidas.

### Filtro de vegetación ExG por tile — implementación
```python
def _tile_has_vegetation(rgb: np.ndarray, threshold: float = VEG_THRESHOLD) -> bool:
    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)
    exg = 2.0 * g - r - b
    veg_pixels = np.sum(exg > 20)  # ExG > 20 = verde significativo
    total_pixels = rgb.shape[0] * rgb.shape[1]
    return (veg_pixels / total_pixels) >= threshold
```
Llamar ANTES de ExG enhancement y ANTES de DeepForest. Si retorna False → `continue` (saltear tile).

### Especies identificadas (VLM claude-haiku-4-5)
- Eucalipto — saludable, confianza 0.7
- Jacarandá — saludable, confianza 0.7
- Acacia — estresado, confianza 0.4
- "dudoso" con confianza 0.0 → borde de imagen, sombra, o zona sin copa clara visible

---

## Vista demo para ReforestLatam — ruta /demo

Se agregó una ruta `/demo` al frontend que muestra SOLO el panel de detección con header minimalista y badge ReforestLatam. Sin tocar la UI principal.

- URL: `http://[host]:3010/demo`
- Archivo: `frontend/src/pages/DemoReforestLatam.tsx`
- Routing en `main.tsx`: `window.location.pathname.startsWith('/demo')` → DemoReforestLatam
- nginx.conf: `location /demo { try_files $uri $uri/ /index.html; }`

### PITFALL — Docker build cachea el JS viejo aunque haya nuevos archivos

`docker compose build --no-cache frontend` puede igualmente servir el bundle viejo si el layer `COPY . .` fue cacheado por Docker. El bundle en el container no cambia aunque los archivos fuente sí hayan cambiado.

**Diagnóstico:**
```bash
docker exec forestai-poc-frontend-1 sh -c \
  "grep -rl 'ReforestLatam' /usr/share/nginx/html/assets/*.js || echo 'NO ENCONTRADO'"
```

**Fix — buildar en host y copiar el dist directamente:**
```bash
# 1. Build en el host (más confiable)
cd /home/server/proyectos/forestai-poc/frontend && npm run build

# 2. Verificar que el nuevo código está en el dist
grep -l "ReforestLatam" dist/assets/*.js

# 3. Copiar dist al container y recargar nginx
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
docker exec forestai-poc-frontend-1 nginx -s reload
```

Este workaround es inmediato y no requiere rebuild del container.

### IMPORTANTE — TreeDetectionPanel NO tiene solapas internas

`TreeDetectionPanel` es un panel único sin tabs. Si la demo en `/demo` muestra todas las solapas (Ortofotos, Mapa, Geo, etc.) es porque el App.tsx se está renderizando en lugar de DemoReforestLatam — revisar el routing y el bundle.

## Demo interactiva /demo — canvas con hover + selección bidireccional (sesión 5)

Implementado en `frontend/src/pages/DemoReforestLatam.tsx`:

- **Hover sobre copa** → tooltip flotante (especie, salud, SAM score, confianza DeepForest)
- **Click en copa** → resalta en amarillo con label de especie encima del polígono
- **Click en fila de tabla** → resalta copa correspondiente en canvas + scroll automático
- Bidireccional: tabla→canvas y canvas→tabla completamente sincronizados
- Hit-test de polígonos SAM con ray-casting (point-in-polygon)
- Tabla lateral scrolleable con sticky header, solo muestra árboles con especie identificada (no "dudoso", no null)

### PITFALL — Demo muestra solapas completas de App.tsx
Si `/demo` renderiza la app completa en lugar de DemoReforestLatam, el bundle no se regeneró.
```bash
# Diagnóstico
docker exec forestai-poc-frontend-1 sh -c \
  "grep -rl 'ReforestLatam' /usr/share/nginx/html/assets/*.js || echo 'NO ENCONTRADO'"

# Fix — siempre buildar en host y copiar dist
cd /home/server/proyectos/forestai-poc/frontend && npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
docker exec forestai-poc-frontend-1 nginx -s reload
```

### Regla de seguridad para demo ReforestLatam
NO revelar: DeepForest, SAM, RetinaNet, VLM, claude-haiku, ni pasos del pipeline.
Loading state: solo spinner 🌲 + "Procesando...". Sin textos técnicos.
Razón: compliance y acuerdos comerciales pendientes con ReforestLatam.

## Demo interactiva /demo — canvas con hover + selección bidireccional (sesión 5)


Tres causas principales:

1. **Dosel continuo** — árboles muy juntos sin separación visual entre copas. DeepForest busca copas individuales con sombra propia.
2. **Subvegetación/arbustos** — pasto alto o arbustos densos se ven verde pero no tienen forma circular/elíptica de copa.
3. **Sombra propia** — copas oscuras por sombra interna confundidas con suelo oscuro.

**Mejoras implementadas (2026-06-09):**
- Tile size: 4096→2048px con overlap 256px (copas ocupan más % del frame)
- ExG aplicado a cada tile antes de inferencia (resalta vegetación)
- NMS post-tiling (IoU>0.5) para eliminar duplicados del overlap
