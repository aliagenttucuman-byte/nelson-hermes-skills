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

## Demo /demo — qué muestra

- Upload drag & drop (PNG, JPG, GeoTIFF)
- Spinner sin mencionar modelos internos
- Canvas con polígonos SAM verdes sobre copas
- Hover → tooltip con especie, salud, score
- Click copa ↔ selección bidireccional en tabla
- Tabla de clasificación de especies (VLM)
- Stats: árboles detectados, confianza promedio, copas segmentadas
- SIN: mencionar DeepForest, SAM, VLM, claude — compliance pendiente con ReforestLatam

## Cambiar tile size

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

## Compliance pendiente

NO revelar ante ReforestLatam:
- Modelos internos (DeepForest, SAM, claude-haiku)
- Stack técnico completo
- Hasta cerrar acuerdo comercial con Gino y ReforestLatam

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

## Contactos

- **Gino**: primera reunión de validación técnica — mostrar ForestAI + Expreso Bisonte
- **ReforestLatam**: cliente objetivo, inventario forestal urbano
- **Pablo**: COO AlegentAI, presente en demos
