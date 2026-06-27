---
name: nelson-forestai-demo
description: Levantar y operar la demo ForestAI para reuniones con Gino y ReforestLatam. Detección de árboles en ortomosaicos con DeepForest + SAM + VLM. Demo limpia en /demo.
category: equipo-nelson
---

# ForestAI Demo — Levantar y operar

## Arranque rápido

### Solo ForestAI
```bash
bash /home/server/.hermes/scripts/forestai_demo_up.sh
```

### ForestAI + Expreso Bisonte (demo con Gino)
```bash
bash /home/server/.hermes/scripts/demo_gino_up.sh
```

Verifica, levanta ambos stacks y entrega URLs listas. Listo en ~15 segundos.
El túnel Cloudflare de Bisonte se regenera automáticamente si murió.

## URLs

| URL | Uso |
|-----|-----|
| `http://100.110.8.13:3010` | App completa (interna) |
| `http://100.110.8.13:3010/demo` | Demo limpia para ReforestLatam ← esta |
| `http://100.110.8.13:8010/docs` | API docs |

## Proyecto

```
/home/server/proyectos/forestai-poc/
```

Docker Compose — 5 servicios: `backend :8010`, `frontend :3010`, `celery_worker`, `db :5433`, `redis :6380`

## Config activa del pipeline

| Parámetro | Valor | Archivo |
|-----------|-------|---------|
| TILE_SIZE | 1024px | `backend/app/services/tree_detection.py:186` |
| TILE_OVERLAP | 128px | `backend/app/services/tree_detection.py:187` |
| VEG_THRESHOLD | 0.12 (12%) | `backend/app/services/tree_detection.py:188` |
| Filtro ExG | activado | `_tile_has_vegetation()` |
| SAM | activado | celery_worker |
| VLM | claude-haiku-4-5 | clasifica 30 árboles por imagen |

## Resultados reales — Parque Avellaneda (12622×7887px)

| Config | Árboles | Tiempo CPU | Notas |
|--------|---------|------------|-------|
| 4096px sin filtro | 173 | 3 min | incluye ciudad |
| 2048px sin filtro | 624 | 7 min | incluye ciudad |
| 2048px + ExG | 220 | 3.5 min | solo parque ✅ |
| 1024px + ExG | 1067 | 11 min | solo parque, máx detalle ✅ |

## Demo /demo — features UI activas

- Upload drag & drop (PNG, JPG, GeoTIFF hasta 500MB)
- Spinner solo con "Procesando..." — sin mencionar modelos
- Canvas con polígonos SAM verdes sobre copas detectadas
- Hover sobre copa → tooltip flotante con especie, salud, score
- Click en copa → resalta en amarillo + nombre encima
- Click en fila de tabla → resalta copa correspondiente en canvas (bidireccional)
- Tabla scrolleable con sticky header: especie, salud, confianza, score DeepForest
- Stats: árboles detectados, confianza promedio, copas segmentadas
- SIN columna izquierda (filtros, pipeline, parámetros técnicos)

## Monitoreo de pipeline en tiempo real

```bash
docker logs -f forestai-poc-celery_worker-1 2>&1
```

Watch patterns útiles: `received`, `Tile`, `SAM`, `Pipeline completado`, `FAILURE`, `ERROR`

Para verificar que el worker tomó cambios de config (tile size, filtro):
```bash
docker logs --since=30s forestai-poc-celery_worker-1 2>&1 | tail -5
```

Para verificar CPU/RAM durante SAM (puede tardar ~10 min con 1000+ copas en CPU):
```bash
docker stats forestai-poc-celery_worker-1 --no-stream --format "CPU: {{.CPUPerc}} | RAM: {{.MemUsage}}"
```

PITFALL: después de cambiar TILE_SIZE o TILE_OVERLAP en tree_detection.py, siempre reiniciar el worker:
```bash
cd /home/server/proyectos/forestai-poc && docker compose restart celery_worker
```
Si no se reinicia, el worker sigue usando el código anterior en memoria.

```bash
# Editar TILE_SIZE y TILE_OVERLAP en:
nano /home/server/proyectos/forestai-poc/backend/app/services/tree_detection.py

# Reiniciar worker para aplicar:
cd /home/server/proyectos/forestai-poc && docker compose restart celery_worker
```

Regla: TILE_OVERLAP = TILE_SIZE / 8

## Si el frontend no muestra cambios (build viejo)

```bash
cd /home/server/proyectos/forestai-poc/frontend
npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
docker exec forestai-poc-frontend-1 nginx -s reload
```

IMPORTANTE: `docker compose build frontend` usa cache y no refleja cambios. Usar `npm run build` + `docker cp` directo.

## Demo /demo — qué NO mostrar (compliance)

- NO mencionar modelos internos: DeepForest, SAM, claude-haiku, VLM
- NO mencionar stack técnico completo
- Spinner de loading: solo el círculo girando + "Procesando..." — sin pasos ni nombres de modelos
- Header: solo "ForestAI — Detección de Árboles", sin subtítulos con nombres de algoritmos
- Columna izquierda (filtros, pipeline, parámetros): OCULTA en /demo
- Aclaración: compliance pendiente hasta cerrar acuerdo con Gino y ReforestLatam

## Tile size — tabla de referencia real (Parque Avellaneda 12622×7887px)

| TILE_SIZE | TILE_OVERLAP | Árboles | Tiempo CPU | Notas |
|-----------|-------------|---------|------------|-------|
| 4096px | 256px | 173 | 3 min | incluye ciudad |
| 2048px | 256px | 624 | 7 min | incluye ciudad |
| 2048px | 256px | 220 | 3.5 min | + filtro ExG, solo parque |
| 1024px | 128px | 1067 | 11 min | + filtro ExG, solo parque ✅ config activa |

Regla de overlap: TILE_OVERLAP = TILE_SIZE / 8

## Filtro ExG — cómo funciona

Función `_tile_has_vegetation()` en `tree_detection.py`:
- Calcula ExG = 2G - R - B por pixel
- Si % de pixels con ExG > 0 es menor a VEG_THRESHOLD (12%) → tile saltado
- Log: "saltado (sin vegetación: X%)" para tiles urbanos
- Solo procesa tiles con vegetación suficiente → cero detecciones en asfalto/edificios

Cambiar umbral: `VEG_THRESHOLD = 0.12` en tree_detection.py (línea ~188)

## nginx client_max_body_size

Configurado a 500MB — soporta imágenes de drone grandes (verificado con 61MB TIFF).
Config en: `/home/server/proyectos/forestai-poc/frontend/nginx.conf`
Para reactivar después de restart: `docker cp nginx.conf forestai-poc-frontend-1:/etc/nginx/conf.d/default.conf && docker exec forestai-poc-frontend-1 nginx -s reload`

## Puntos de venta para la demo

- Detección automática de árboles en ortomosaicos de drone
- Filtro de vegetación ExG — solo procesa zonas verdes, ignora ciudad
- Segmentación de copa exacta árbol por árbol (polígono, no bbox)
- Clasificación de especies con IA (Eucalipto, Jacarandá, Acacia, etc.)
- Estado de salud: saludable / estresado / deteriorado
- Escala: imagen de 193M px procesada sin GPU
- Con GPU (RTX 3070): 11 min → ~1.5 min

## Tecnologías a evaluar — Roadmap

### OpenCV 5 (junio 2025)
https://opencv.org/opencv-5/

Relevancia directa para ForestAI:

- **UMat heterogéneo** — un solo código corre en CPU, CUDA, OpenCL o Vulkan sin cambiar pipeline. Cuando llegue la GPU, el salto es transparente. Hoy habría que reescribir partes del tiling y ExG.
- **DNN module mejorado** — transformers + INT8 quantization nativos. Evaluar si reemplaza SAM por algo más liviano integrado directo en OpenCV, sin depender de PyTorch/HuggingFace.
- **20-40% más rápido en CPU** — las transformaciones de ExG y tiling que hoy corren en numpy se pueden portar a OpenCV 5 y ganar rendimiento sin hardware nuevo.
- **Nuevos algoritmos de segmentación** — evaluar si hay alternativa a SAM más liviana para segmentación de copas.

Acción: cuando se avance hacia producción con GPU, migrar pipeline de tiling+ExG a OpenCV 5 UMat y benchmarkear vs implementación actual.

### Opik — Evaluación de LLMs (open-source)
https://github.com/comet-ml/opik — 5.1k stars, Apache 2.0, self-hosted vía Docker.

Relevancia directa para ForestAI:

- **Tracing del VLM**: loggear cada llamada a claude-haiku (prompt, respuesta, tokens, latencia, costo) con `@opik.track`. Hoy no tenemos visibilidad de qué tan bien clasifica especies.
- **LLM-as-a-Judge**: evaluar automáticamente si las clasificaciones de especies son correctas, detectar hallucinations, medir confianza real vs reportada.
- **Dataset de evaluación**: armar un dataset de árboles etiquetados manualmente (Eucalipto, Jacarandá, Acacia) y benchmarkear el VLM contra ground truth.
- **Experimentos**: comparar versiones de prompt o modelos (haiku vs sonnet) en el mismo dataset y ver cuál clasifica mejor.
- **Self-hosted**: `pip install opik && opik server install` — sin cloud externo, datos de ReforestLatam no salen del servidor.

Acción: integrar Opik en el pipeline VLM de ForestAI antes de la propuesta formal a ReforestLatam — necesitamos poder mostrar métricas de calidad del clasificador de especies.

### Gemini Live API (Google)
https://github.com/google-gemini/gemini-live-api-examples | 298 stars

Relevancia directa para ForestAI — interfaz de voz + video en campo:

- **Inspector de campo**: el operador habla con el sistema mientras apunta la cámara a un árbol — registra especie, salud, observaciones por voz sin tocar el celular
- **Barge-in**: puede interrumpir al modelo en cualquier momento — flujo natural en campo
- **Video en tiempo real**: recibe JPEG hasta 1FPS — podría analizar la copa mientras el inspector la encuadra
- **Tool use**: function calling integrado — el agente puede actualizar el inventario directamente mientras el inspector habla
- **70 idiomas** — relevante para operaciones en distintos países de LATAM
- **WebSocket stateful** — integra con el backend FastAPI existente

Acción: evaluar para la versión mobile/campo de ForestAI — el inspector levanta datos con voz + cámara, el sistema detecta y registra en tiempo real.

## Configuración activa del pipeline (validada sesión 2026-06-09)

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| TILE_SIZE | 1024px | Mejor detección de copas pequeñas |
| TILE_OVERLAP | 128px | 12.5% del tile — NMS limpio |
| VEG_THRESHOLD | 12% (0.12) | ExG filter — saltea ciudad/asfalto |

### Comparativa de configuraciones probadas

| Config | Árboles | Tiempo | Notas |
|--------|---------|--------|-------|
| 4096px sin filtro | 173 | 3 min | Incluye ciudad |
| 2048px sin filtro | 624 | 7 min | Incluye ciudad |
| 2048px + ExG | 220 | 3.5 min | Solo parque ✅ |
| 1024px + ExG | 1067 | 11 min | Solo parque, máxima detección ✅ |

**Regla de overlap**: mantener overlap al 12.5% del tile. Si tile=2048 → overlap=256. Si tile=1024 → overlap=128. Así el NMS trabaja consistente sin importar el tile size.

**Por qué 1024px es mejor**: DeepForest ve cada árbol con más píxeles → menos falsos negativos en copas medianas y pequeñas. Con GPU el tiempo bajaría a ~1-2 min.

## Filtro ExG — lógica de vegetación

El filtro `_tile_has_vegetation()` calcula ExG = 2G - R - B > 0 por píxel. Si menos del `VEG_THRESHOLD`% del tile es vegetación, el tile se saltea completamente. Esto elimina detecciones en asfalto, edificios y zona urbana.

Los logs muestran "saltado (sin vegetación)" para tiles urbanos y solo procesan los tiles del parque.

## Compliance pendiente

NO revelar ante ReforestLatam:
- Modelos internos (DeepForest, SAM, claude-haiku)
- Stack técnico completo
- Hasta cerrar acuerdo comercial con Gino y ReforestLatam

## PITFALL — Scope creep al analizar tiles problemáticos

Cuando Nelson comparte una screenshot de la demo con detección errónea (ej: "detecta así... no está bien"),
la respuesta correcta es:

1. Analizar visualmente la imagen
2. Dar diagnóstico conciso en audio: "detectó 1 árbol en un tile con 10+, el problema es el modelo fine-tuned con dataset pequeño"
3. Proponer solución brevemente (ExG, recalibrar conf, etc.)
4. **Esperar que Nelson diga "dale" antes de tocar código**

NO implementar el detector completo + service refactor + UI changes + rebuilds Docker sin confirmación.
Nelson dijo "se ensució mucho esto" cuando JARVIS se lanzó a implementar sin esperar OK.

---

## PITFALL — nginx client_max_body_size se pierde en restart

Síntoma: imágenes grandes (>1MB) devuelven 413 Request Entity Too Large.
Causa: el contenedor nginx no monta el nginx.conf del host — usa la imagen embebida.
Fix (ya en demo_gino_up.sh automáticamente):
```bash
docker cp /home/server/proyectos/forestai-poc/frontend/nginx.conf \
  forestai-poc-frontend-1:/etc/nginx/conf.d/default.conf
docker exec forestai-poc-frontend-1 nginx -s reload
```

## PITFALL — docker compose build frontend no refleja cambios de código

Síntoma: cambios en `.tsx` no aparecen en el browser después de `docker compose build`.
Causa: Docker cachea el layer `COPY . .` y no detecta los cambios.
Fix correcto:
```bash
cd /home/server/proyectos/forestai-poc/frontend
npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
docker exec forestai-poc-frontend-1 nginx -s reload
```
NUNCA usar `docker compose build --no-cache` para esto — tarda 3 min y da el mismo resultado.

## PITFALL — cambios en tree_detection.py requieren restart del worker

El celery worker carga el código al arrancar — no hay hot reload.
Después de cualquier cambio en `backend/app/services/tree_detection.py`:
```bash
cd /home/server/proyectos/forestai-poc && docker compose restart celery_worker
```

## YOLOv ForestAI — proyecto paralelo (yolov-orientacion-poc)

Repo separado con modelos YOLO fine-tuned para detección de copas. Complementa ForestAI (DeepForest) con enfoque YOLO.

```
/home/server/proyectos/yolov-orientacion-poc/
```

### Levantar

```bash
cd /home/server/proyectos/yolov-orientacion-poc
docker compose up --build -d
# Esperar ~30s al build, luego:
docker restart yolov-orientacion-poc-nginx-1  # fix 502 — ver pitfall abajo
```

### URLs

| URL | Uso |
|-----|-----|
| `http://100.110.8.13:9020` | App completa (nginx proxy) |
| `http://100.110.8.13:8020/docs` | API docs (FastAPI) |

### Modelos entrenados disponibles

| Modelo | Path | Uso |
|--------|------|-----|
| `yolo11n_forestai_v2.pt` | `models/` | Detección de copas NOA/Tucumán (recomendado demo) |
| `yolo26n_especies_noa_v1.pt` | `models/` | Clasificación de especies NOA |

### Pipeline

GeoTIFF → tiler (640px, overlap 128px) → YOLO inference por tile → NMS global → species classifier → FastAPI :8020 → React UI

### Detectores disponibles

| Detector | Descripción |
|----------|-------------|
| `yolo11n_forestai` | Fine-tuned NOA/Tucumán — recomendado |
| `yolo11n` | YOLO11n base (no fine-tuned) |
| `yolov8n` | YOLOv8n base |
| `exg` | ExG + Watershed — sin ML |

### Docker Compose — 3 servicios

| Servicio | Puerto | Rol |
|----------|--------|-----|
| backend | :8020 | FastAPI + YOLO inference |
| frontend | :80 (interno) | React/Vite estático en nginx |
| nginx | :9020 → :80 | Proxy unifica API + UI |

### PITFALL — nginx 502 Bad Gateway tras docker compose up

Síntoma: `curl localhost:9020` devuelve 502 aunque backend y frontend estén up.
Causa: nginx resuelve DNS de los contenedores al arrancar — si los otros contenedores no estaban listos, cachea la resolución fallida.
Fix:
```bash
docker restart yolov-orientacion-poc-nginx-1
# esperar 3s y verificar
curl -s -o /dev/null -w "%{http_code}" http://localhost:9020  # debe dar 200
```

### UI para reuniones presenciales con cliente

Cuando Nelson pida rediseño urgente del frontend para una demo presencial ("hoy nos juntamos...", "dame una buena UI", "estilo serio para impresionar"), ver `references/yolov-poc-ui-reuniones-clientes.md` — brief de estilo, stats reales para hero cards, workflow de deploy y pitfalls de timing.

### Diferencias con ForestAI (forestai-poc)

| Aspecto | ForestAI | YOLOv PoC |
|---------|----------|-----------|
| Modelo | DeepForest (pretrained) | YOLOv fine-tuned |
| Labels | Pre-entrenado NEON | ExG pseudo-labels |
| Segmentación | SAM (polígonos) | Bounding boxes |
| Puertos | :3010/:8010 | :9020/:8020 |
| Objetivo | Producción/demos | Investigación/comparativa |

## Contactos

- **Gino**: primera reunión de validación técnica — mostrar ForestAI + Expreso Bisonte
- **ReforestLatam**: cliente objetivo, inventario forestal urbano
- **Pablo**: COO AlegentAI, presente en demos
