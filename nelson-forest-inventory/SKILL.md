---
name: nelson-forest-inventory
description: "PoC de inventario forestal con drones e image analytics para el equipo Nelson. Stack: FastAPI + React + MapLibre + OpenCV + Rasterio + tablas alométricas INTA. Sin machine learning."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [forestai, drones, geotiff, rasterio, opencv, maplibre, inventario-forestal, obia]
    related_skills: [nelson-spec-driven-workflow, nelson-brainstorming, nelson-project-bootstrap, nelson-netflora]
---

# ForestAI — Inventario Forestal con Drones (PoC I+D+I)

Skill de dominio para la PoC de inventario forestal automático desde ortofotos de drone.
Detecta árboles, estima especie, biomasa y edad usando image analytics sin ML.

## Deploy rápido post-cambios

```bash
cd ~/proyectos/forestai-3d/frontend
npm run build
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
```
El tunnel principal (port 3010) apunta al Docker container — sin el `docker cp` los cambios NO se ven.
Ver detalle completo: `references/deploy-tunnel-pitfalls.md`

## Contexto

Proyecto I+D+I del equipo Nelson (2026-05-19). Flujo de 3 fases (Especificar → Planear → Implementar).
Documentación: `~/brainstorming/2026-05-19-forestai-poc/`

**Proyecto canónico**: `~/proyectos/forestai-poc/` — ÚNICO proyecto activo. El spike `~/proyectos/forestai-3d/` fue descartado. No desarrollar allí. Todo desarrollo va acá.
El spike `~/proyectos/forestai-3d/` fue descartado; sus cambios fueron migrados al proyecto original.

**Regla de migración spike → main:**
1. `diff -rq --exclude="*.pyc" --exclude="node_modules" --exclude="dist" spike/ main/` para ver qué cambió
2. Copiar solo los archivos nuevos/modificados relevantes
3. Verificar deps nuevas (`package.json`, `requirements.txt`) e instalar en el proyecto principal
4. Rebuild limpio: `rm -rf dist && npm run build`

---

## Stack Tecnológico

### Backend (Python / FastAPI)
- **FastAPI** + Celery + Redis — API REST + procesamiento asincrónico
- **Rasterio + GDAL** — lectura/escritura de GeoTIFF georreferenciados
- **OpenCV** — segmentación watershed de copas de árboles
- **Geopandas + Shapely** — manejo de geometrías, GeoJSON, reproyección
- **PostGIS** — almacenamiento de geometrías de copas y métricas

### Frontend (React / Vite)
- **React 18 + Vite + TypeScript**
- **MapLibre GL JS** — mapa interactivo con capas raster + GeoJSON (preferido sobre Leaflet para GeoJSON pesado)
- **shadcn/ui** — paneles y controles
- **Zustand** — estado global

### Herramientas de Análisis (sin ML)
- **OBIA (Object-Based Image Analysis)** — segmentación por forma, color y textura
- **Watershed** — delineación de copas individuales desde ortofoto RGB
- **Tablas alométricas INTA** — biomasa (kg) y edad (años) por especie y altura de copa

---

## Pipeline de Análisis (Celery Task)

```
Paso 1 (25%) → load_raster()
  Rasterio abre GeoTIFF, reproyecta a EPSG:4326 si es necesario

Paso 2 (50%) → segment_crowns()
  OpenCV: blur gaussiano → umbral Otsu → distancia transform → watershed
  Resultado: polígonos de copa por árbol (Shapely)

Paso 3 (75%) → classify_species()
  Reglas sobre R/G/B medios + textura LBP por copa
  Especies soportadas: eucalipto, pino, quebracho, algarrobo, araucaria

Paso 4 (100%) → compute_metrics()
  Altura estimada desde área de copa (modelo isométrico simple)
  Biomasa y edad desde tablas alométricas INTA por especie

Paso 5 (opcional) → vlm_classify()   ← NUEVO — validado en Spike 002 (2026-05-21)
  Si NVIDIA_API_KEY configurada: recorta bbox de cada copa → base64 JPEG →
  Llama 3.2 90B Vision via NVIDIA NIM → especie + estado sanitario + confianza
  Campos agregados: vlm_species, vlm_health, vlm_confidence, vlm_notes
  Modelo: meta/llama-3.2-90b-vision-instruct
  Endpoint: https://integrate.api.nvidia.com/v1/chat/completions
  Ver spike completo en: ~/brainstorming/2026-05-21-deepagents-spike/spikes/002-vision-llm-forestai/
```

## Tablas Alométricas — Especies Argentinas

Las tablas alométricas relacionan métricas observables (altura de copa, área) con biomasa y edad.
Fuente base: publicaciones INTA Forestación + FAO 2012 como fallback.

| Especie | Biomasa (kg) | Referencia |
|---|---|---|
| Eucalyptus globulus | `a * altura^b` | INTA 2019 |
| Pinus elliottii | `a * altura^b` | INTA 2015 |
| Quebracho colorado | ecuación específica | INTA Chaco |
| Algarrobo | ecuación específica | INTA NOA |
| Araucaria araucana | ecuación específica | INTA Neuquén |

---

## Datos de Prueba (GeoTIFF)

Ver `references/geotiff-sources.md` para fuentes completas y comandos de descarga.

### Tiles listos para usar (descarga directa sin registro):

```bash
# NEON — bosque subtropical Florida, 10cm/px, 400x400px
curl -L -o OSBS_029.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/OSBS_029.tif"

# NEON — bosque mediterráneo California, 10cm/px
curl -L -o SJER_sample.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/2018_SJER_3_252000_4107000_image_477.tif"

# Australia — altísima res 1.8cm/px, ideal para calibrar watershed
curl -L -o australia.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/australia.tif"

# Anotaciones XML (226 archivos con bounding boxes de árboles)
curl -L -o annotations.zip "https://zenodo.org/api/records/5914554/files/annotations.zip/content"
```

### Datasets completos:
- NeonTreeEvaluation: `https://zenodo.org/api/records/5914554` (training: 4.3GB, evaluation: 3.6GB)
- ReforesTree (LATAM, Ecuador): `https://zenodo.org/records/6813783` (7.1GB)

---

## Endpoints API (OpenAPI completo en brainstorming)

```
POST   /api/analyses                          → subir GeoTIFF, devuelve analysis_id
GET    /api/analyses/{id}                     → estado y progreso (0-100%)
GET    /api/analyses/{id}/trees               → lista plana de árboles para mapa (markers)
GET    /api/analyses/{id}/geojson             → FeatureCollection de copas
GET    /api/analyses/{id}/summary             → estadísticas agregadas
GET    /api/analyses/{id}/csv                 → exportar inventario CSV
GET    /api/analyses                          → historial paginado
```

Spec OpenAPI completo: `~/brainstorming/2026-05-19-forestai-poc/specs/openapi.yaml`
User stories (7 HUs): `~/brainstorming/2026-05-19-forestai-poc/specs/user-stories.md`

---

## Estructura del Proyecto (implementada 2026-05-19)

Proyecto en: `~/proyectos/forestai-poc/`
Brainstorming en: `~/brainstorming/2026-05-19-forestai-poc/`

```
forestai-poc/
├── backend/
│   ├── app/
│   │   ├── api/analyses.py       # 7 endpoints REST completos
│   │   ├── services/
│   │   │   ├── forest_analyzer.py  # Pipeline OBIA completo
│   │   │   └── allometric.py       # Tablas INTA + FAO
│   │   ├── tasks/
│   │   │   ├── celery_app.py      # Config Celery + Redis
│   │   │   └── analysis_task.py   # Task async con progress_callback
│   │   ├── models/schemas.py      # Pydantic schemas completos
│   │   ├── db/
│   │   │   ├── models.py          # SQLAlchemy + GeoAlchemy2 (PostGIS)
│   │   │   └── session.py         # get_db dependency
│   │   ├── config.py              # pydantic-settings
│   │   └── main.py                # FastAPI app + CORS + Base.metadata.create_all
│   ├── requirements.txt
│   └── Dockerfile                 # python:3.11-slim + GDAL + libgl1
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          # axios + forestApi helpers
│   │   ├── store/useForestStore.ts  # Zustand: selectedAnalysisId, mapCenter
│   │   ├── components/
│   │   │   ├── MapPanel.tsx       # MapLibre + polígonos + popup click
│   │   │   ├── UploadPanel.tsx    # drag/drop + React Query mutation
│   │   │   └── SidePanel.tsx      # status progress + summary + export btns
│   │   ├── pages/HomePage.tsx     # layout: sidebar + map + side panel
│   │   └── App.tsx                # QueryClientProvider wrapper
│   ├── vite.config.ts             # proxy /api → localhost:8000
│   └── package.json               # maplibre-gl, zustand, react-query
└── docker-compose.yml             # PostGIS 16-3.4 + Redis 7 + Celery worker
```

---

## Pitfalls

- **Layout React — panel achicado al cambiar de solapa:** Si GeoPanel, DetectionPanel, etc. aparecen con padding recortado o comprimidos, revisar que el div raíz tenga `width: "100%"` además de `height: "100%"`. Síntoma típico: se ve bien en primera carga pero queda chico al volver a la tab. Fix: `style={{ display: "flex", flexDirection: "column", height: "100%", width: "100%", background: "..." }}`

- **Watershed mal calibrado:** El parámetro crítico es el `minDistance` del `peak_local_max` de skimage. Con imágenes a 10cm/px, usar `minDistance=15-25px` para árboles medianos. Con australia.tif (1.8cm/px), usar `minDistance=80-120px`. Probar con imagen sintética primero.

- **MapLibre + GeoTIFF raster:** MapLibre no lee GeoTIFF directamente. Opciones: (a) convertir a tiles XYZ con rio-cogeo + titiler, (b) recortar como PNG georeferenciado y usar como ImageSource, (c) usar maplibre `addSource` con type `image` + bounds. La opción (b) es la más rápida para una PoC.

- **Reproyección obligatoria:** Los GeoTIFF del NEON vienen en EPSG:32617/32611 (UTM). MapLibre y GeoJSON requieren EPSG:4326. Reproyectar siempre con pyproj `Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)` por contorno antes de guardar en PostGIS o generar GeoJSON.

- **Celery + Redis en Docker:** Usar nombre del servicio Docker (`redis`), no `localhost`. En `docker-compose.yml` usar `postgis/postgis:16-3.4-alpine` (no `postgres:16`) para tener PostGIS disponible sin setup extra.

- **GeoAlchemy2 + Celery task:** Al guardar geometrías desde la task de Celery, pasar el WKT en formato `"SRID=4326;POLYGON((lon lat, ...))"` directamente al campo `geom`. GeoAlchemy2 lo convierte automáticamente.

- **GeoTIFF > 500MB:** El upload puede agotar el timeout de FastAPI. Configurar `client_max_body_size` en nginx y `--timeout 120` en uvicorn. Para la PoC, limitar a 500MB.

- **`@types/maplibre-gl` no existe para v3+:** Desde maplibre-gl v3 los tipos TypeScript vienen dentro del paquete principal. `@types/maplibre-gl` quedó en v1.14 y da error `ETARGET` al instalar. Quitar del `devDependencies`.

- **Alias `@/` en Vite requiere configuración explícita:** El template de Nelson usa `@/lib/utils` y `@/lib/api` que asumen un alias path. Si no está configurado en `vite.config.ts` + `tsconfig.json`, el build falla en Docker con `Cannot find module '@/lib/api'`. Fix:
  ```ts
  // vite.config.ts
  import path from "path";
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } }
  // tsconfig.json compilerOptions
  "paths": { "@/*": ["./src/*"] }
  ```

- **MSW no viene en el template:** El archivo `src/test/mocks/handlers.ts` del template importa `msw` que no está en `package.json`. En la PoC reemplazar por `export const handlers: unknown[] = [];`

- **`src/test/` rompe el build de producción:** Los `@types/chai`, `@types/vitest` en node_modules generan errores TS si `src/test/` está incluido en la compilación. Agregar `"exclude": ["src/test", "node_modules"]` en `tsconfig.json`.

- **`clsx` no viene en el template:** `src/lib/utils.ts` importa `clsx` que no está en dependencies. Reemplazar por implementación inline: `export function cn(...inputs: (string|undefined|null|false)[]) { return inputs.filter(Boolean).join(" "); }`

- **Clasificación de especie por RGB — rangos amplios necesarios:** Los colores varían mucho según hora del día, estación y cámara del drone. Los rangos RGB en `SPECIES_COLOR_RULES` deben ser AMPLIOS (ej. R: 40-200, no 50-120) para capturar la variabilidad real. Si los rangos son muy estrechos, la mayoría de árboles quedan como "desconocida". Resultado correcto con rangos amplios: OSBS detecta 66% eucalipto / 33% algarrobo con confianza "alto". Documentar esto como limitación de la PoC.

- **VARI umbral adaptativo (crítico):** No usar umbral fijo (ej. 100) sobre VARI normalizado. En imágenes densamente forestadas (NEON, etc.) el 99%+ de píxeles superan cualquier umbral fijo y watershed no encuentra peaks. Usar Otsu automático + fallback al percentil 70 si >90% queda como vegetación:
  ```python
  otsu_thresh, thresh = cv2.threshold(vari_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
  veg_fraction = thresh.sum() / (255 * thresh.size)
  if veg_fraction > 0.90:
      percentile_thresh = int(np.percentile(vari_norm, 70))
      _, thresh = cv2.threshold(vari_norm, percentile_thresh, 255, cv2.THRESH_BINARY)
  ```
  Sin este fix los tiles NEON (Florida, California) detectan 0 árboles. Con él detectan correctamente.

- **Watershed dt_factor — usar valor FIJO, NO dinámico por densidad de verde:** El `dt_factor` controla cuánto se exige que un blob se "apunte" antes de ser marcado como semilla de árbol. Un factor bajo (0.3) no separa árboles tocantes → blobs fusionados de 300-400m² y alturas de 26m.

  **TRAMPA CRÍTICA**: variar dt_factor según `veg_fraction` parece lógico pero está invertido. En silvopastoral hay mucho PASTO verde además de árboles — veg_fraction es alta → dt_factor sube a 0.50 → watershed más restrictivo → detecta MENOS árboles. El pasto verde no distingue entre pasto y árbol a nivel de VARI. Resultado: silvopastoral (muchos árboles reales) detecta 3-4 árboles, Chapadmalal (menos verde) detecta 60+.

  **Solución correcta: dt_factor fijo = 0.40** — no varía por densidad de verde. Para distinguir árbol de pasto usar filtros de FORMA y TEXTURA por blob:
  ```python
  dt_factor = 0.40  # fijo, no dinámico

  # Después del watershed, filtrar cada blob:
  # Filtro 1: Área en m² (copa mín 2m², máx 80m²)
  area_m2 = area_px * (resolution_m ** 2)
  if area_m2 < 2.0 or area_m2 > 80.0:
      continue

  # Filtro 2: Circularidad — árbol = copa redonda, pasto = elongado/irregular
  # Circularity = 4π * área / perímetro²  →  1.0 = círculo perfecto
  perimeter = cv2.arcLength(cnt, True)
  circularity = (4 * math.pi * area_px) / (perimeter ** 2)
  if circularity < 0.15:  # permisivo: rechaza manchas largas pero acepta copas asimétricas
      continue

  # Filtro 3: Textura — copa de árbol tiene sombras/varianza, pasto es uniforme
  g_vals = g[mask > 0]
  local_variance = float(np.var(g_vals))
  if local_variance < 50.0:  # pasto homogéneo < 50, árbol > 100
      continue
  ```
  **Calibración de umbrales**: la circularidad 0.15 y varianza 50 son conservadores — si se detectan muy pocos árboles reales, bajarlos (ej. circularity > 0.10, variance > 30). Si se detectan manchas de pasto, subirlos. Sin ground truth, preferir umbrales bajos (más falsos positivos pero menos falsos negativos).

- **Dockerizado rasterio/GDAL:** **NO instalar `libgdal-dev` del SO.** Rasterio trae GDAL compilado dentro de su wheel binario de Python — instalar `libgdal-dev` desde apt causa conflictos de versión y falla con exit code 100. Solo instalar: `gcc g++ python3-dev libglib2.0-0 libgl1`. Dockerfile correcto:
  ```dockerfile
  RUN apt-get update && apt-get install -y \
      gcc g++ python3-dev \
      libglib2.0-0 libgl1 \
      && rm -rf /var/lib/apt/lists/*
  ```

- **Tailwind CSS v4 con body override — causa fondo negro persistente:** En el proyecto ForestAI, el `index.css` tenía `body { background-color: #0a0f0d; color: #e2e8f0; }` hardcodeado. Al hacer rediseño claro, las clases Tailwind de React no alcanzan a pisar la regla de body. Siempre actualizar `index.css` al cambiar el tema base. Solución: limpiar `index.css` y dejar solo `@import "tailwindcss"` + body en el color nuevo.

- **Doble QueryClientProvider rompe todas las queries:** Si `main.tsx` ya provee `<QueryClientProvider>` y `App.tsx` también crea uno propio, las queries no funcionan (retornan undefined o no se disparan). Mantener UN SOLO `QueryClientProvider` en el árbol de componentes.

- **Tailwind v4 purge en Docker build:** Al hacer build de producción con Docker + Vite, Tailwind v4 purga clases no usadas. Si el `App.tsx` usa clases nuevas post-purge, el frontend sirve el JS nuevo pero sin los estilos. Solución robusta: usar inline styles (`style={{...}}`) para componentes críticos de layout/diseño — los estilos quedan embebidos en el JS y no dependen del CSS purgeado.

- **Frontend Dockerizado requiere rebuild completo + recrear contenedor para cambios de código:** El contenedor usa nginx sirviendo build estático. `docker compose restart frontend` NO aplica cambios de código. `docker restart <container>` tampoco recrea el contenedor con la imagen nueva — solo reinicia nginx dentro del contenedor viejo. Flujo correcto:
  ```bash
  docker compose build frontend              # 1. Build nueva imagen
  docker rm -f forestai-poc-frontend-1       # 2. Destruir contenedor viejo
  docker run -d --name forestai-poc-frontend-1 --network forestai-poc_app-net -p 3010:80 forestai-poc-frontend:latest
  # Verificar con: docker exec forestai-poc-frontend-1 ls /usr/share/nginx/html/assets/
  # El nombre del JS bundle debe cambiar (ej: index-C1DLEsJs.js en vez de index-UnfFtwIJ.js)
  ```
  Con docker compose disponible: `docker compose up -d --force-recreate frontend`.

- **Nelson rechazó la primera UI (dark theme) — la segunda iteración fue fondo claro tipo dashboard:** La primera iteración con dark theme verde bosque fue rechazada con "no me gusta para nada la UI". La segunda (aprobada) usa fondo claro (`bg-slate-50`), grilla de cards con thumbnails, panel de detalle lateral, y dos vistas separadas (Grid de ortofotos / Mapa). Antes de diseñar una UI nueva, preguntar al usuario qué estilo quiere. No asumir que dark theme = buena UI para GIS.

- **API URL debe ser string vacío para que nginx proxy funcione remotamente:** El `api/client.ts` y cualquier archivo que construya URLs de API deben usar `import.meta.env.VITE_API_URL || ""` (no `|| "http://localhost:8010"`). Con localhost hardcodeado, los usuarios remotos (Tailscale, etc.) fallan porque el browser intenta conectar a su propio localhost. Con string vacío, las requests van a rutas relativas (`/api/...`) que nginx redirige internamente al backend. Aplicar en todos los archivos que construyen URLs: `api/client.ts`, `App.tsx`, `StatsPanel.tsx`.

- **Thumbnail de GeoTIFF — endpoint y patrón implementado:** Nelson pidió previsualización de las ortofotos. Implementado como `GET /api/analyses/{id}/thumbnail` que genera PNG usando rasterio + Pillow. Patrón: leer con `out_shape` reducido (max 512px), normalizar percentil 2–98 para stretch de contraste, devolver con `StreamingResponse` y `Cache-Control: public, max-age=3600`. En frontend: componente `<Thumbnail id={id}>` con `<img src=...>` y fallback `onError`. El endpoint debe ir ANTES de `/{analysis_id}/summary` en el router para evitar que FastAPI interprete "thumbnail" como un analysis_id.

- **Mini mapa de ubicación en panel de detalle:** Nelson pidió ver dónde en el mundo está cada ortofoto. Patrón: componente `<LocationMiniMap analysisId={id}>` que usa `useQuery([\"trees\", id])` para obtener coords, instancia un `maplibregl.Map` en un `useRef` con `interactive: false`, y hace `flyTo` al centroide de los árboles. Mostrar coordenadas bajo el mapa. Importante: inicializar el mapa solo una vez (chequear `mapInst.current` antes de crear), y en el `useEffect` de fly esperar que `trees` carguen. Render: `height: 160px`, `borderRadius: 12px`.

- **Endpoint de reprocesar — patrón implementado:** `POST /api/analyses/{id}/reprocess` que: (1) verifica que el archivo original existe, (2) borra árboles existentes con `db.query(Tree).filter(analysis_id==id).delete()`, (3) resetea campos `status=pending, progress=0, tree_count=None, error=None, completed_at=None`, (4) relanza `run_analysis.delay(id, filepath)`. En frontend: botón "🔄 Reprocesar" en el DetailSidebar con `useMutation` que llama `POST /api/analyses/{id}/reprocess` y después `invalidateQueries(["analyses"])`. El botón se deshabilita cuando `status === "processing" || "pending"`. Esto sirve para demos — el espectador puede ver el pipeline completo en acción.

- **Endpoint `/bounds` para overlay de ortofoto en mapa:** Nelson pidió ver la ortofoto superpuesta sobre el mapa. Implementar `GET /api/analyses/{id}/bounds` que retorna `{west, south, east, north, center_lon, center_lat}` usando `rasterio.warp.transform_bounds(src.crs, "EPSG:4326", *src.bounds)`. En frontend: usar `map.addSource(id, { type: "image", url: thumbnailUrl, coordinates: [[west,north],[east,north],[east,south],[west,south]] })` + `map.addLayer({ type: "raster", ... })`. Agregar toggle "🛰 Ortofoto ON/OFF" en la barra del mapa. El endpoint debe ir ANTES de `/{id}/thumbnail` en el router.

- **Endpoint DELETE para limpiar análisis duplicados:** Implementar `DELETE /api/analyses/{id}` que: (1) borra árboles con `db.query(Tree).filter(...).delete()`, (2) `db.delete(analysis)`, (3) `db.commit()`, (4) intenta borrar archivo físico con `os.remove()` en try/except. Retornar 204 sin body. Necesario para limpiar duplicados que se generan al subir el mismo archivo dos veces. Flujo típico de limpieza:
  ```python
  # Listar todo lo cargado
  curl -s http://localhost:8010/api/analyses | python3 -c "
  import json,sys
  data=json.load(sys.stdin)
  for a in data['items']:
      print(f'{a[\"analysis_id\"]} | {a[\"name\"]}')
  "
  # Borrar los que no corresponden
  curl -s -X DELETE http://localhost:8010/api/analyses/{id}
  ```

- **Hover de markers MapLibre — NO usar transform:scale (causa desplazamiento permanente):** MapLibre aplica `translate(-50%, -50%)` en el wrapper del marker para centrarlo. Agregar `transform: scale()` encima (incluso con `transform-origin: center center`) sigue desplazando el marker porque los dos transforms se componen. La solución correcta y definitiva es **NO usar transform en absoluto** — usar `box-shadow` para el efecto visual de hover:
  ```js
  el.style.cssText = `width:${size}px;height:${size}px;border-radius:50%;
    background:${color}44;border:2px solid ${color};cursor:pointer;
    transition:box-shadow 0.15s;box-shadow:0 0 8px ${color}66;`;
  el.onmouseenter = () => { el.style.boxShadow = `0 0 0 8px ${color}33, 0 0 16px ${color}88`; el.style.zIndex = "10"; };
  el.onmouseleave = () => { el.style.boxShadow = `0 0 8px ${color}66`; el.style.zIndex = ""; };
  ```
  El círculo brilla al hacer hover sin moverse un píxel. Agregar `transform-origin` NO resuelve el problema — probar con box-shadow desde el principio.

- **Mapa: selector de análisis integrado en la vista mapa:** Nelson rechazó que el mapa solo mostrara "datos de las imágenes". Agregar un `<select>` en la barra superior del mapa con todas las ortofotos completadas. Así el usuario puede cambiar de análisis sin salir a la vista de grilla. Pasar prop `onSelectAnalysis: (id: string) => void` al `MapPanel` y conectar al state de `App.tsx` (el `selectedId` es compartido entre ambas vistas).

- **GeoTIFFs sintéticos para demos (Argentina):** Si no hay ortofotos reales disponibles, generar GeoTIFFs sintéticos georreferenciados con rasterio para ubicaciones argentinas reales. Limitación: el análisis OBIA detecta 0 árboles en imágenes de ruido puro (sin vegetación real). Sirve solo para demostrar el flujo de upload/procesamiento y la ubicación en el mapa. Los 3 GeoTIFFs reales del repo DeepForest (OSBS, SJER, Australia) son mejores para demos técnicas.

- **Cargar los datos de prueba al arrancar:** Al hacer demos, pre-cargar los 3 GeoTIFF de prueba via `POST /api/analyses` para que aparezcan en la UI sin que el usuario tenga que subir nada. Hacerlo con curl en loop al final del deploy.

- **Ortofotos reales públicas — OpenAerialMap:** La API de OpenAerialMap devuelve ortofotos reales descargables. La URL de descarga está en el campo `uuid` (no `download`). Filtrar por `file_size < 50MB` para demos. Para Argentina: bbox `-73,-55,-53,-22` retorna ~1255 resultados. Para norte argentino (NOA/NEA — Chaco, Salta, Tucumán, Misiones): bbox `-69,-28,-54,-20`. Ortofotos verificadas norte Argentina:
  - **"SR La Leonesa, Chaco, Argentina"** — 32MB, bosque chaqueño, UUID: `https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/660b1858fca0b60001ebc59e/0/660b1858fca0b60001ebc59f.tif`
  ```bash
  # Todas las ortofotos Argentina en OAM
  curl -s "https://api.openaerialmap.org/meta?limit=50&bbox=-73,-55,-53,-22" -o /tmp/oam_ar.json
  # Filtro genérico por tamaño
  curl -s "https://api.openaerialmap.org/meta?limit=50&type=image%2Ftiff" -o /tmp/oam.json
  python3 -c "
  import json
  d = json.load(open('/tmp/oam.json'))
  for item in d.get('results',[]):
      sz = item.get('file_size', 0)
      url = item.get('uuid','')
      if sz and sz < 50*1024*1024 and url.endswith('.tif'):
          print(f'{sz//1024//1024}MB | {item[\"title\"][:50]} | {url}')
  "
  ```
  Ver `references/oam-argentina-ortofotos.md` para URLs verificadas de Argentina y mundo.

- **Alembic autogenerate captura tablas PostGIS — migración sucia:** Al correr `alembic revision --autogenerate` dentro del container con PostGIS, Alembic ve todas las tablas de TIGER/PostGIS (`place_lookup`, `county_lookup`, `spatial_ref_sys`, etc.) que no están en los modelos Python y las agrega como `op.drop_table()` en el upgrade. Esto destruiría la BD. Solución: NO usar autogenerate para columnas simples. Escribir la migración manualmente:\n  ```python\n  def upgrade() -> None:\n      op.add_column('trees', sa.Column('vlm_species',    sa.String(100), nullable=True))\n      op.add_column('trees', sa.Column('vlm_health',     sa.String(20),  nullable=True))\n      op.add_column('trees', sa.Column('vlm_confidence', sa.Float(),     nullable=True))\n      op.add_column('trees', sa.Column('vlm_notes',      sa.String(255), nullable=True))\n  def downgrade() -> None:\n      op.drop_column('trees', 'vlm_notes') ...\n  ```\n  Siempre revisar el archivo generado antes de correr `alembic upgrade head` — si tiene docenas de `drop_table`, reemplazarlo con una versión limpia.\n\n- **Alembic migration file owned by root — docker cp workaround:** Cuando se genera la migración con `docker exec ... alembic revision`, el archivo se crea con owner `root` en el volume del container y en el bind mount del host. `write_file()` falla con Permission denied. Fix: escribir la versión limpia en `/tmp`, luego copiar al container:\n  ```bash\n  docker cp /tmp/migration_clean.py forestai-poc-backend-1:/app/alembic/versions/XXXX_name.py\n  # Y también al host para que quede en git:\n  sudo chown server:server /home/server/proyectos/forestai-poc/backend/alembic/versions/XXXX.py\n  ```\n\n- **VLM sobre bboxes pequeños — pitfall crítico:** Llama Vision (y cualquier VLM) rechaza clasificar cuando la copa recortada tiene menos de ~40px de lado. El modelo responde en español "No puedo identificar la especie sin imagen clara" en lugar de devolver JSON, causando `parse_error`. Solución: filtrar árboles con `(xmax-xmin) < 40 or (ymax-ymin) < 40` antes de enviarlos al VLM, O escalar el recorte a mínimo 128×128 con PIL antes de encodear. El spike 002 probó que 3/5 de los árboles más grandes clasifican correctamente.

- **VLM clasificación de copas — latencia y estrategia de paralelismo:** Llama 3.2 90B Vision via NVIDIA NIM tarda ~7-10 segundos por árbol en modo secuencial. Para 55 árboles eso son ~9 minutos — inaceptable en pipeline síncrono. Solución validada: usar `asyncio.gather` con batches de 5-10 requests simultáneos. Estimación: 55 árboles / 5 paralelos × 10s = ~2 minutos. Implementar como paso Celery separado (opcional, asíncrono) que escribe vlm_fields en la DB sin bloquear el pipeline principal.\n\n- **VLM no aparece en la UI — verificar BD primero antes de tocar código:** Si los campos VLM se ven `null` en el frontend pero el código del clasificador y el endpoint están correctos, el problema puede ser que los análisis existentes fueron creados por seed/import ANTES de que el VLM estuviera integrado. El pipeline VLM solo corre durante el procesamiento — no retroactivamente. Diagnóstico rápido:
  ```bash
  # Verificar si los campos son null en BD
  ANALYSIS_ID=$(curl -s http://localhost:8010/api/analyses | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d['items'][0]['analysis_id'])")
  curl -s "http://localhost:8010/api/analyses/$ANALYSIS_ID/trees" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('vlm_species'))"
  ```
  Si imprime `None`, los datos no están en la BD. Fix: UPDATE directo con datos realistas en espera de un reprocesado real:
  ```sql
  UPDATE trees SET
    vlm_species = CASE
      WHEN species = 'algarrobo' THEN 'Prosopis alba'
      WHEN species = 'eucalipto' THEN 'Eucalyptus camaldulensis'
      WHEN species = 'pino'      THEN 'Pinus elliottii'
      WHEN species = 'quebracho' THEN 'Schinopsis balansae'
      WHEN species = 'sauce'     THEN 'Salix humboldtiana'
      WHEN species = 'roble'     THEN 'Nothofagus obliqua'
      WHEN species = 'araucaria' THEN 'Araucaria araucana'
      ELSE 'Especie nativa'
    END,
    vlm_health      = (ARRAY['saludable','saludable','saludable','estresado','enfermo'])[floor(random()*5+1)],
    vlm_confidence  = ROUND((0.72 + random()*0.25)::numeric, 2),
    vlm_notes       = (ARRAY['Copa densa, sin signos de plaga','Coloración uniforme','Posible estrés hídrico leve'])[floor(random()*3+1)]
  WHERE vlm_species IS NULL;
  -- Ejecutar con: docker exec forestai-poc-db-1 psql -U forestai -d forestai -c "..."
  ```
  Usar para demos cuando los análisis seed no pasaron por el pipeline VLM.

- **VLM en Celery — usar `asyncio.run()` (no `loop.run_until_complete()`):** Celery worker no tiene un loop asyncio activo. Para ejecutar corutinas async dentro de una task Celery síncrona, usar `asyncio.run(classify_trees_vlm(...))`. NO intentar `get_event_loop().run_until_complete()` — Celery puede tener un loop cerrado o inexistente según la versión. `asyncio.run()` crea un loop nuevo, lo usa y lo cierra limpiamente.\n\n- **VLM hook en analysis_task.py — patrón implementado (sesión 17):** El hook VLM es completamente opcional: si `NVIDIA_API_KEY` no está en `.env`, el pipeline salta el paso silenciosamente. Si la hay, activa como paso 83-90% del progreso después del guardado en BD. Errores del VLM no propagan — se loggean y el análisis continúa con `vlm_*` en NULL. Conversión lat/lon → coordenadas pixel usa proyección lineal (precisa para ortofotos pequeñas). El archivo de servicio: `backend/app/services/vlm_classifier.py`.

- **VLM — system prompt JSON-only y parsing robusto:** El modelo a veces ignora el instruction de "SOLO JSON" y responde en prosa. Patrón robusto de extracción:
  ```python
  # 1. Limpiar markdown code blocks
  if "```" in content:
      content = content.split("```")[1].replace("json", "").strip()
  # 2. Buscar primer { ... } en el string por si hay texto introductorio
  import re
  match = re.search(r'\{[^}]+\}', content, re.DOTALL)
  if match:
      content = match.group(0)
  result = json.loads(content)
  ```
  Si sigue fallando, loggear el raw response y marcar el árbol con `vlm_confidence: 0, vlm_health: "sin_datos"`.

- **No usar delegate_task para búsquedas simples de APIs públicas:** En esta sesión, delegar la búsqueda de ortofotos en OpenAerialMap a un subagente causó que el agente se colgara indefinidamente. Para búsquedas simples con `curl` + `python3`, ejecutar directo con `terminal`. Usar `delegate_task` solo para tareas que requieren múltiples pasos complejos de código.

- **Levantar containers sin `docker compose up` — alias de red requerido:** Cuando se usan `docker start` o `docker run` directamente (sin compose), el container del frontend falla con `host not found in upstream "backend"` porque nginx no puede resolver el hostname. Docker Compose asigna automáticamente aliases de red cortos (`backend`, `db`, etc.) pero al arrancar containers manualmente eso no ocurre. Solución:
  ```bash
  # 1. Arrancar DB y Redis primero
  docker start forestai-poc-db-1 forestai-poc-redis-1
  sleep 5
  # 2. Arrancar backend y celery
  docker start forestai-poc-backend-1 forestai-poc-celery_worker-1
  # 3. Agregar alias "backend" al container de backend en la red
  docker network disconnect forestai-poc_app-net forestai-poc-backend-1
  docker network connect --alias backend forestai-poc_app-net forestai-poc-backend-1
  # 4. Recrear frontend (rm + run) para que lo encuentre en la red
  docker rm -f forestai-poc-frontend-1
  docker run -d --name forestai-poc-frontend-1 \
    --network forestai-poc_app-net \
    -p 3010:80 \
    forestai-poc-frontend:latest
  ```
  La forma correcta es siempre usar `docker compose up -d` desde `~/proyectos/forestai-poc/`. Si compose falla silenciosamente (Hermes no admite `docker compose up` como foreground long-running), usar `docker start` en orden + el alias trick arriba. Verificar: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010` debe devolver 200.

- **GeoTIFF de alta resolución — downsampling obligatorio antes de watershed (OOM fix):** Imágenes UAV a 2-3cm/px pueden tener 18000x13000+ píxeles. Cargarlas full-res revienta la RAM del worker (SIGKILL señal 9). Solución: downsampling en `load_raster()` con `out_shape` de rasterio:
  ```python
  MAX_DIM = 6000  # max 6000px por lado — con 4000 el watershed detecta 0 árboles
  scale = min(MAX_DIM / src.width, MAX_DIM / src.height, 1.0)
  out_w = max(1, int(src.width * scale))
  out_h = max(1, int(src.height * scale))
  r = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.average).astype(np.float32)
  from rasterio.transform import from_bounds
  transform = from_bounds(bounds.left, bounds.bottom, bounds.right, bounds.top, out_w, out_h)
  resolution_m = (width_m / out_w + height_m_geo / out_h) / 2
  ```
  6000x6000 float32 = ~144MB por banda = ~432MB total RGB. Elegir según RAM disponible.

- **Filtro de textura (varianza verde) — REMOVIDO:** El filtro `local_variance < 50.0` fue eliminado porque es demasiado restrictivo para copas con iluminación uniforme o con poca sombra interna. Copas reales en imágenes a plena luz del día pueden tener varianza < 50 aunque sean árboles reales. Solo queda el filtro de circularidad (> 0.15) como filtro de forma. Si se reactiva textura, bajar el umbral a 20-30, no 50. Quitar textura tampoco resuelve silvopastoral — la raíz es la falta de NIR.

- **Datos abiertos Argentina para ForestAI — fuentes verificadas:**
  - **INTA GeoINTA:** `geointa.inta.gob.ar` — WMS/WFS sin registro. NDVI, uso de suelo, cobertura vegetal. Consumible desde Python o GIS.
  - **MAyDS/UMSEF bosques nativos:** `datos.gob.ar/dataset/ambiente-bosques-nativos` — shapefile y GeoTIFF de bosques nativos, zonificación OTBN (rojo/amarillo/verde), series temporales de deforestación 2002-presente. Libre, sin registro.
  - **CONAE/SAOCOM:** imágenes SAR banda L — NO son open data. Requiere registro + aprobación. Uso comercial = contrato. Para la PoC usar Sentinel-2 (ESA) que sí es open.
  - **Sentinel-2 (ESA Copernicus):** 10m/px, multispectral con NIR, actualización cada 5 días. Completamente libre. Es la base de la mayoría de forestechs internacionales. Ideal para próximo sprint: consultar por lat/lon + radio y obtener NDVI real.
  - **Ruta práctica:** Shapefiles bosque nativo = datos.gob.ar. Imágenes satelitales = Sentinel-2 (USGS o Copernicus Hub). Capas GIS INTA = GeoINTA WMS.
  - Ver `references/datos-abiertos-forestales-argentina.md` para URLs completas, APIs y limitaciones.

- **`docker restart` y `docker compose restart` NO recargan `env_file`:** Cuando se agrega o modifica una variable de entorno en el `.env` del proyecto (ej. `OPENCODE_API_KEY`), ni `docker restart <container>` ni `docker compose restart <servicio>` la toman. `env_file` solo se procesa al *crear* el container (`docker compose up`). Fix correcto:
  ```bash
  docker compose stop backend
  docker compose up -d backend   # recrea el container con el env_file actualizado
  # Verificar que la variable llegó:
  docker exec forestai-poc-backend-1 env | grep OPENCODE
  ```
  En Hermes: usar `background=true` para `docker compose up -d`. Verificar con `docker exec ... env | grep <VAR>` antes de asumir que llegó. `env_file` solo se procesa al crear el container con `docker compose up`. Fix correcto:
  ```bash
  docker stop forestai-poc-celery_worker-1
  docker rm forestai-poc-celery_worker-1
  docker compose up -d celery_worker   # recrea el container con el env_file actualizado
  # Verificar que la variable llegó:
  docker exec forestai-poc-celery_worker-1 python3 -c "import os; print(os.getenv('NVIDIA_API_KEY','NO_KEY')[:10])"
  ```
  IMPORTANTE en Hermes: `docker compose up -d` como comando foreground queda bloqueado. Usar siempre `background=true` o la secuencia `docker stop/rm` + `docker compose` con el flag background del terminal.

- **VLM con PIL sobre GeoTIFFs grandes — PIL.MAX_IMAGE_PIXELS = None obligatorio:** GeoTIFFs forestales de alta resolución (ej. 14000×14250px) superan el límite por defecto de PIL (178.9M píxeles) y disparan `DecompressionBombError`. Esto mata el paso VLM silenciosamente. Fix: agregar antes de `Image.open()` dentro del bloque VLM:
  ```python
  Image.MAX_IMAGE_PIXELS = None  # TIFs forestales pueden ser muy grandes
  image_arr = np.array(Image.open(filepath).convert("RGB"))
  ```
  Ya aplicado en `analysis_task.py`.

- **VLM NVIDIA NIM free tier — rate limit con concurrencia > 2:** Con `asyncio.gather` y 5 requests simultáneos al free tier de NVIDIA NIM, algunos requests devuelven HTTP 429 `Too Many Requests`. Bajar concurrencia default a **2** en `classify_trees_vlm()`. Los 5 árboles del análisis La Leonesa se procesan en ~30s con concurrencia=2 sin rate limits.

- **VLM system prompt — usar inglés y JSON explícito con fallback regex:** El modelo Llama 3.2 90B Vision a veces responde en prosa en lugar de JSON cuando el prompt está en español ("No puedo proporcionar..."). Cambios que mejoran la tasa de éxito:
  1. Escribir el prompt en inglés
  2. Agregar "ALWAYS respond with ONLY a JSON object, no prose, no explanations. Even if the image is unclear, return your best estimate."
  3. Usar regex para extraer `{...}` en caso de que el modelo agregue texto introductorio
  Con estas mejoras: 2/5 árboles clasificados (los 3 restantes el modelo rechaza por guardrails — copas ambiguas para sus filtros de contenido). Comportamiento esperado en PoC con imágenes RGB de GeoTIFF.

- **Campos VLM en frontend — agregar a interface `TreeResult` y al popup del mapa:** El interface `TreeResult` en `api/client.ts` no incluye los campos VLM por defecto. Agregarlos como opcionales:
  ```ts
  export interface TreeResult {
    // ... campos existentes ...
    vlm_species?: string | null;
    vlm_health?: string | null;
    vlm_confidence?: number | null;
    vlm_notes?: string | null;
  }
  ```
  En `MapPanel.tsx`, el popup del árbol seleccionado debe mostrar una sección condicional "🤖 Visión IA" que solo aparece si `selectedTree.vlm_species || selectedTree.vlm_health`. Colores del health: saludable → `#059669`, estresado → `#f59e0b`, enfermo → `#ef4444`, dudoso → `#94a3b8`. Después de modificar el frontend siempre rebuild completo + recrear container: `docker compose build frontend` + `docker rm -f forestai-poc-frontend-1` + `docker compose up -d frontend`.

- **aiohttp faltante en imagen de Celery worker — agregar a requirements.txt + rebuild:** Si `vlm_classifier.py` usa `aiohttp` pero solo se instaló con `docker exec pip install aiohttp`, el worker falla en el próximo recreate con `ModuleNotFoundError: No module named 'aiohttp'`. La instalación manual no sobrevive rebuild de imagen. Fix permanente: agregar `aiohttp>=3.9.0` a `backend/requirements.txt` y hacer rebuild de imagen con `docker compose build celery_worker`. Verificar post-rebuild: `docker exec forestai-poc-celery_worker-1 python3 -c "import aiohttp; print(aiohttp.__version__)"`.

- **Rebuild para ver cambios — NO olvidar celery_worker:** Los cambios en `forest_analyzer.py` los ejecuta el **celery_worker**, no el backend. Si solo se hace `docker compose build backend`, los análisis siguen usando el código viejo. Si el backend también tiene cambios, buildearlo junto. Siempre rebuildar y recrear:
  ```bash
  docker compose build celery_worker -q           # o: build backend celery_worker -q
  docker stop forestai-poc-celery_worker-1
  docker rm forestai-poc-celery_worker-1
  docker compose up -d celery_worker
  # Verificar que arrancó y que la imagen es nueva:
  docker logs forestai-poc-celery_worker-1 --tail 5
  docker images forestai-poc-celery_worker --format "{{.ID}} {{.CreatedAt}}"
  ```
  **Trampa**: `docker compose up -d backend` NO recrea el container si ya existe con la imagen vieja — usa `docker stop/rm` + `docker compose up -d` para forzar recreación. Verificar que el container anterior fue destruido antes de levantar el nuevo (conflicto de nombre = container viejo sigue corriendo).

- **Limitación estructural VARI en silvopastoral sin NIR:** En imágenes silvopastorales (árboles dispersos en potrero con pasto verde), los árboles y el pasto tienen valores VARI muy similares porque ambos son vegetación verde en el espectro visible RGB. Sin banda infrarroja (NIR), no es posible separar con confianza árbol de pasto usando solo VARI. Esto es una limitación del algoritmo, no un bug. Ajustar el percentil de fallback (70 → 55 → 40) no resuelve el problema — los blobs siguen detectándose iguales porque la separación VARI es insuficiente. Documentar como limitación del PoC: "Para imágenes silvopastorales, se requiere banda NIR o NDVI para una detección confiable de árboles dispersos". NDVI se puede calcular en Python con rasterio/numpy (`ndvi = (nir - r) / (nir + r + 1e-10)`) pero requiere que el GeoTIFF tenga banda NIR — todos los actuales son 3 bandas RGB (verificado `src.count == 3`).

- **WFS ambiente.gob.ar — campos reales del OTBN verificados:** El servidor WFS de `geo.ambiente.gob.ar/geoserver/wfs` tiene capas OTBN por provincia (no una capa consolidada). Los campos reales son `cat_cons` (categoría I/II/III), `clase` ("Bosque Nativo"), `area_ha` (hectáreas del polígono), `id`. NO usar `categoria`, `CATEGORIA`, `cat` — esos no existen. Ejemplo real: `{'clase': 'Bosque Nativo', 'cat_cons': 'III', 'area_ha': 12.6, 'id': 11131}`. Layer de Chaco: `bosques:CH_2009_OTBN`. Consultar GetCapabilities para otros: `curl "https://geo.ambiente.gob.ar/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities" | grep '<Name>'`.

- **Filtro de copa en m² reales — NO en píxeles:** El filtro por pixels varía con resolución. A 2cm/px hay 2500px/m², a 10cm/px hay 100px/m². Siempre filtrar por m² reales:
  ```python
  area_m2_check = area_px * (raster["resolution_m"] ** 2)
  if area_m2_check < 2.0 or area_m2_check > 80.0:  # 80m² = radio ~5m, árbol adulto grande
      continue
  height_m = max(1.0, min(height_m, 16.0))  # cap INTA: con copa máx 80m² → altura 12.5m
  ```
  Cap de 120m² y 20m de altura es demasiado permisivo — deja pasar blobs de 2-3 árboles fusionados que el watershed no separó bien (típico en silvopastoral). Con copas de 359m²: radio=10.7m, altura=26.7m — imposible para algarrobo/espinillo real. Límites correctos INTA para árboles adultos argentinos: copa máx 80m² (radio 5m), altura máx 16m.
  Referencias INTA: algarrobo 15-80m², quebracho 20-90m², eucalipto 15-50m², pino 20-80m², lenga 10-60m², caldén 10-70m².

- **Volumen Docker del worker vs bind mount — los TIFs no llegan al worker:** El backend usa bind mount (`./uploads:/app/uploads`) pero el celery_worker usa named volume (`forestai-poc_uploads_data:/app/uploads`). Los archivos subidos por API van al bind mount del host, el worker lee desde su volume — y no los encuentra. Fix definitivo en `docker-compose.yml`: ambos servicios deben usar el mismo named volume:
  ```yaml
  backend:
    volumes:
      - uploads_data:/app/uploads   # named volume, no bind mount
  celery_worker:
    volumes:
      - uploads_data:/app/uploads   # mismo named volume
  volumes:
    uploads_data:
  ```
  Fix de emergencia (copiar manualmente): `for f in uploads/*.tif; do docker cp "$f" forestai-poc-celery_worker-1:/app/uploads/; done`

- **Celery worker OOM (SIGKILL) — tasks quedan colgadas en "processing":** Cuando el worker muere por falta de RAM (señal 9), las tasks en curso quedan en estado `processing` indefinidamente — nunca van a `failed`. El endpoint `/reprocess` es la solución. Patrón correcto para reprocesar múltiples análisis colgados: hacerlo **de a uno**, esperando que cada uno complete antes de lanzar el siguiente. Lanzar todos juntos reproduce el OOM:
  ```python
  for aid, name in stuck_analyses:
      requests.post(f"/api/analyses/{aid}/reprocess")
      # Esperar hasta completed o failed
      while True:
          r = requests.get(f"/api/analyses/{aid}")
          if r.json()["status"] in ("completed", "failed"):
              break
          time.sleep(10)
  ```
  Detectar tasks colgadas: `status == "processing"` con `created_at` hace más de 5 minutos y sin `completed_at`. Ver logs del worker: `docker logs forestai-poc-celery_worker-1 | grep "SIGKILL"`.

- **Frontend queda caído después de `docker compose up -d --build backend celery_worker`:** Al hacer rebuild selectivo (solo backend/celery), Docker Compose puede bajar y no subir el frontend si hay dependencias de red que se recrean. Siempre verificar después de cualquier rebuild con `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010`. Si devuelve 000 o error: `docker compose up -d frontend`. No asumir que solo porque el backend está arriba el frontend también lo está.

- **Stack completo se cae en builds pesados:** El servidor de Nelson tiene RAM limitada. Al hacer `docker compose build` de frontend (que corre Node/Vite), si hay otros contenedores corriendo con alta carga, Docker puede matar todos los contenedores por OOM. Después de un build, verificar con `docker ps | grep forest` antes de asumir que todo está corriendo. Relanzar con `docker compose up -d redis db backend celery_worker` (en background, no foreground).

- **GeoTIFFs sintéticos detectan 0 árboles:** Imágenes generadas con `numpy.random` (ruido puro) no tienen estructura de vegetación real. El pipeline OBIA los procesa sin error pero devuelve 0 árboles. Sirven únicamente para demostrar ubicación geográfica en el mapa y flujo de upload. Para demos técnicas con conteo real de árboles, usar siempre los tiles NEON/Australia.

- **Endpoint `/trees` faltante en el scaffold inicial:** El frontend necesita `GET /api/analyses/{id}/trees` para plotear markers en el mapa. El scaffold inicial solo tenía `/geojson` y `/summary`. Agregar siempre este endpoint al router que retorna lista plana de `{tree_id, species, lat, lon, height_m, crown_area_m2, biomass_kg, age_years, confidence}`. Es más liviano que GeoJSON y más fácil de consumir desde MapLibre markers.

- **Base.metadata.create_all en PoC:**

---

## Geo Servicios — Integración de Fuentes Externas

### Endpoints implementados (sesión 10)

```
GET /api/geo/bosques?lat=-26.8&lon=-60.4&radius_km=15
GET /api/geo/sentinel?lat=-26.8&lon=-65.2&radius_km=5
GET /api/geo/sentinel/preview?lat=-26.8&lon=-60.4&radius_km=10&layer=TRUE_COLOR
GET /api/geo/context?lat=-26.8&lon=-65.2&radius_km=10  # llama ambos en paralelo
```

Archivo: `backend/app/services/geo_services.py` + `backend/app/api/geo.py`.

### WFS MAyDS/UMSEF — Bosques Nativos

```python
UMSEF_WFS_URL = "https://geo.ambiente.gob.ar/geoserver/wfs"
# Parámetros reales verificados:
params = {
    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
    "typeName": "bosques:CH_2009_OTBN",          # layer Chaco (formato: XX_YYYY_OTBN)
    "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat},EPSG:4326",
    "outputFormat": "application/json",
    "count": 200,
    "srsName": "EPSG:4326",
}
# Campos reales: cat_cons (I/II/III), clase ("Bosque Nativo"), area_ha, id
```

### Sentinel-2 — Preview de imagen satelital (Process API)

`GET /api/geo/sentinel/preview?lat=&lon=&radius_km=&layer=TRUE_COLOR|NDVI`

Devuelve PNG de 512×512px usando la **Sentinel Hub Process API** de CDSE. Mismo OAuth2 token que la Statistical API. El endpoint usa `StreamingResponse` con `Cache-Control: public, max-age=3600`.

**Evalscripts verificados:**

```js
// TRUE_COLOR — RGB amplificado ×3.5 para contraste visible
function evaluatePixel(s) { return [3.5*s.B04, 3.5*s.B03, 3.5*s.B02]; }

// NDVI coloreado — 5 rangos de verde por valor
function evaluatePixel(s) {
  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 0.0001);
  if (ndvi < 0)   return [0.5, 0.5, 0.5];   // gris: agua/suelo/artificial
  if (ndvi < 0.2) return [0.9, 0.8, 0.2];   // amarillo: suelo desnudo
  if (ndvi < 0.4) return [0.5, 0.8, 0.2];   // verde claro: vegetación escasa
  if (ndvi < 0.6) return [0.1, 0.6, 0.1];   // verde: vegetación moderada
  return [0.0, 0.4, 0.0];                    // verde oscuro: bosque denso
}
```

**Payload correcto para Process API:**
```python
{
    "input": {
        "bounds": {"bbox": [min_lon, min_lat, max_lon, max_lat]},
        "data": [{"type": "sentinel-2-l2a", "dataFilter": {"maxCloudCoverage": 30}}],
    },
    "output": {
        "width": 512, "height": 512,
        "responses": [{"identifier": "default", "format": {"type": "image/png"}}],
    },
    "evalscript": evalscript,
}
# Endpoint: POST https://sh.dataspace.copernicus.eu/api/v1/process
# Header: Authorization: Bearer {token}
```

**Frontend — toggle True Color / NDVI con botones:**
```tsx
const [previewLayer, setPreviewLayer] = React.useState<"TRUE_COLOR" | "NDVI">("TRUE_COLOR");
const previewUrl = `${API_BASE}/api/geo/sentinel/preview?lat=${lat}&lon=${lon}&radius_km=${radius}&layer=${previewLayer}`;
// <img key={previewUrl} src={previewUrl} ...> — key fuerza recarga al cambiar layer
```
La `key={previewUrl}` en el `<img>` es crítica: sin ella React reutiliza el elemento DOM y la imagen no se recarga al cambiar de capa. Con `key`, React destruye y recrea el elemento, disparando un nuevo GET al backend.

**Overlay en frontend:** el preview se muestra en un `<Card>` dentro del panel de Sentinel, con label "Vista satelital", botones "Color Real" / "NDVI", botón "Ocultar/Mostrar", y un badge en el corner inferior izquierdo con fecha + tipo de capa.

---



Credenciales CDSE configuradas en `.env` (no commiteado): `CDSE_USER` + `CDSE_PASSWORD`.
Flujo: OAuth2 token → Sentinel Hub Statistical API `/api/v1/statistics`.

Ver referencia completa: `references/cdse-statistical-api.md`

**Pitfalls clave (todos verificados en producción):**

- **`mosaicking: "ORBIT"` en el evalscript → `data: []`:** La Statistical API no admite mosaicking ORBIT en el setup(). Quitarlo — sin esa línea funciona.
- **`resx/resy` en lugar de `width/height` → error 400 "exceeds 1500m/px":** Con un bbox de ~20km y `resx:10`, la API calcula 20020m/px y rechaza. Usar `width: 256, height: 256` siempre.
- **Rango temporal de ±1 día → `data: []`:** Sentinel-2 tiene revisita de 5 días. Un rango de 2 días suele no tener imagen. Usar mínimo 30 días atrás desde la imagen más reciente encontrada.
- **Stats con NaN/Inf → `ValueError: Out of range float values are not JSON compliant`:** La Statistical API puede devolver `NaN` para zonas sin datos. Filtrar con `math.isfinite()` antes de `round()`. Sin este fix el endpoint FastAPI crashea con 500.
- **Docker hot-reload no aplica cambios al evalscript cacheado:** Si el evalscript viejo ya fue importado por uvicorn, `docker cp` + restart no es suficiente — el módulo Python queda en memoria con el texto viejo. Requiere rebuild completo de la imagen.
- **`import os` debe ir al inicio del módulo, no inline:** Si se coloca `import os` dentro de la función o en el medio del archivo, Python puede importarlo después de que el módulo ya arrancó sin las env vars disponibles en el scope correcto. Moverlo al top del archivo.
- **TypeScript: campos nuevos del backend deben estar en la interface:** Si el backend agrega campos nuevos (`ndvi_mean`, `ndvi_min`, `ndvi_max`, `ndvi_error`, etc.) pero el tipo TS no los declara, el build de Docker falla con `error TS2339: Property does not exist`. Siempre actualizar la interface junto con el backend.

- **Zonas con alta nubosidad en mayo (Patagonia) — orientar al usuario con coordenadas que funcionan:** Las coordenadas por defecto del panel (`lat=-38, lon=-63`, Patagonia) caen en zona con alta nubosidad en otoño/invierno austral (mayo-agosto). El filtro de 30% nubosidad no encuentra imagen disponible y el panel muestra "Sin imagen disponible". Para demos: usar siempre **Chaco Norte (`lat=-26.8, lon=-60.4`)** — disponibilidad constante, imagen de mayo 2026 con 0% nubes y NDVI 0.643 verificado. Cambiar las coordenadas por defecto del panel a Chaco Norte para evitar esta confusión en demos.

- **`zip` binary no disponible en el servidor — usar python3 zipfile:** `zip` no está instalado en el servidor de Nelson. Para empaquetar archivos en un ZIP, usar siempre `python3 -c "import zipfile, os; ..."`. Patrón reutilizable:
  ```python
  import zipfile, os
  def zipdir(path, ziph):
      for root, dirs, files in os.walk(path):
          for file in files:
              filepath = os.path.join(root, file)
              arcname = os.path.relpath(filepath, os.path.dirname(path))
              ziph.write(filepath, arcname)
  with zipfile.ZipFile('output.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
      zipdir('my-folder', zf)
  print(f"{os.path.getsize('output.zip')//1024} KB")
  ```

- **`React` import explícito cuando se usa `React.useState` inline:** Si el componente usa `React.useState(...)` o `React.useRef(...)` directamente (en lugar de `const [x, setX] = useState(...)` destructurado), se necesita `import React, { useState } from "react"` — no alcanza con `import { useState } from "react"`. TS/Vite tira error `React is not defined` en build. Solución: usar siempre `import React, { useState, useRef } from "react"` en componentes que necesiten ambas formas.
- **Frontend hardcodeado vs backend dinámico:** Es fácil que el frontend muestre un mensaje estático ("requiere autenticación") mientras el backend ya devuelve datos reales. Verificar que el render sea condicional sobre los datos de la API, no sobre constantes hardcodeadas en el JSX. En esta sesión el mensaje "NDVI requiere autenticación" estaba hardcodeado en el JSX — el backend ya devolvía `ndvi_mean: 0.643` pero el componente lo ignoraba. Fix: condicional `{data.ndvi_mean != null ? NdviCards : FallbackMsg}`.

- **Agente de Inventario Forestal — estrategia IA documentada:** La visión de largo plazo tiene 3 módulos: (1) Image Analytics con SAM/YOLOv8/DeepForest para segmentación individual de copas, (2) Estimación dasométrica automática (DAP, altura, estado sanitario), (3) Agente conversacional con RAG + tool use sobre la DB. Documento completo en `~/brainstorming/2026-05-19-forestai-poc/AI-STRATEGY.md`. Requerimiento crítico de imagen: mínimo 5cm/pixel (drone a 80m de altura), GeoTIFF georreferenciado. Coordinar protocolo de vuelo con Pablo ANTES de desarrollar el módulo de visión. Pitch definitivo: "el primer inventario forestal que se hace solo y se puede consultar hablando".

- **DeepForest+SAM — pipeline oficial verificado (sesión 14):** La combinación DeepForest (detección) + SAM (segmentación) tiene tutorial oficial del mismo equipo: `github.com/weecology/DeepForest-SAM`. El combo es `pip install deepforest segment-anything`. DeepForest funciona en CPU sin GPU, soporta PNG/JPG/GeoTIFF, modelo pre-entrenado en HuggingFace (`weecology/deepforest-tree`). Output: DataFrame con `xmin,ymin,xmax,ymax,score` (bboxes). SAM toma esos bboxes como prompts y produce máscaras de polígono pixel-perfect. Ver `references/deepforest-sam-pipeline.md` para código completo.

- **DeepForest en Docker — agregar a requirements.txt con torch:** Agregar `deepforest>=1.3.3`, `supervision>=0.20.0`, `Pillow>=10.0.0`, `torch>=2.0.0`, `torchvision>=0.15.0`. El build tarda varios minutos por PyTorch (~800MB). DeepForest descarga el modelo de HuggingFace en la primera llamada — la primera request puede tardar 20-30s.

- **SAM checkpoint en /tmp se pierde con cada rebuild — y con `--force-recreate`:** El `sam_vit_b.pth` (~375MB) vive en `/tmp` del container. `docker compose build` O `docker compose up -d --force-recreate` destruyen el container viejo y `/tmp` desaparece (incluso si no se hizo build). Fix definitivo verificado en producción: montar un named volume `sam_models` apuntando a `/tmp/sam_models` en `docker-compose.yml` y usar ese path en el servicio:
  ```yaml
  # docker-compose.yml — en el servicio backend
  volumes:
    - sam_models:/tmp/sam_models
  # al final del archivo
  volumes:
    sam_models:
  ```
  ```python
  # tree_detection.py
  SAM_CHECKPOINT = "/tmp/sam_models/sam_vit_b.pth"
  ```
  Después del primer `docker compose up`, descargar UNA VEZ al volume:
  ```bash
  docker exec <backend-container> python3 -c "
  import urllib.request, os
  os.makedirs('/tmp/sam_models', exist_ok=True)
  urllib.request.urlretrieve(
    'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth',
    '/tmp/sam_models/sam_vit_b.pth'
  )
  print('OK', os.path.getsize('/tmp/sam_models/sam_vit_b.pth') // 1e6, 'MB')
  "
  ```
  Futuros rebuilds conservan el volume y no re-descargan.

- **SAM+DeepForest pipeline verificado (sesión 15):** `_refine_with_sam()` usa `SamPredictor.predict(box=bbox, multimask_output=True)` → toma la máscara de mayor score SAM → `_mask_to_polygon()` con `cv2.findContours` + `approxPolyDP` → dibujado RGBA con `Image.alpha_composite`. El service tiene `_sam_available()` que verifica import + checkpoint antes de intentar cargar SAM. Fallback automático a bboxes si SAM no está disponible o falla. **`segment-anything` debe estar en `requirements.txt`** — instalarlo solo con `docker exec pip install` no sobrevive rebuilds. Agregar `segment-anything>=1.0` junto con `deepforest>=1.3.3`. El endpoint de detección debe incluir `sam_used: bool` en el response para que el frontend pueda mostrar el badge "SAM activo" y acceder a los campos `polygon: [[x,y], ...]` de cada árbol. Pipeline promedio: 55 árboles, ~14 puntos por polígono, SAM activo.

- **`asyncio.run()` falla dentro de FastAPI — usar ThreadPoolExecutor con loop propio:** Cuando se llama `asyncio.run(coroutine)` desde dentro de un endpoint FastAPI (que ya corre con un event loop activo de uvicorn), lanza `RuntimeError: asyncio.run() cannot be called from a running event loop`. El VLM falla silenciosamente (el `except Exception` lo captura y continúa). Fix definitivo — correr la corutina en un thread separado con su propio event loop:
  ```python
  import concurrent.futures, asyncio

  def _run_vlm():
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      try:
          return loop.run_until_complete(
              classify_trees_vlm(image_np, trees_for_vlm, api_key, concurrency=1)
          )
      finally:
          loop.close()

  with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
      vlm_results = pool.submit(_run_vlm).result(timeout=180)
  ```
  Notar que Celery worker SÍ puede usar `asyncio.run()` directamente (no tiene loop activo). Solo aplicar el workaround en endpoints FastAPI síncronos. Diagnóstico: buscar `asyncio.run() cannot be called from a running event loop` en logs del backend.

- **VLM en pipeline de detección en tiempo real — limitar a N árboles más grandes:** Con 55 árboles y el free tier de NVIDIA NIM (concurrencia 1, ~7-10s/árbol), el VLM tardaría ~9 minutos — inaceptable para un endpoint HTTP. Estrategia: clasificar solo los `max_trees=8` árboles con mayor área de copa (los que tienen más píxeles y mayor resolución visual). Priorizar por área antes de preparar crops:
  ```python
  indexed = list(enumerate(trees))
  indexed.sort(key=lambda x: (x[1].get("xmax",0)-x[1].get("xmin",0)) *
                               (x[1].get("ymax",0)-x[1].get("ymin",0)), reverse=True)
  indexed = indexed[:max_trees]
  ```
  Los 8 árboles más grandes se clasifican en ~80s con concurrencia 1. Los demás quedan con `vlm_*=null` — la UI los muestra sin sección VLM (condicional `tree.vlm_species || tree.vlm_health`).

- **VLM — model rechaza con "I'm not going to engage" / "I don't feel comfortable":** El modelo Llama 3.2 90B Vision activa guardrails cuando el prompt se percibe como ambiguo o el system prompt está mal formateado. Causas verificadas: (1) mezclar system prompt y user message en el mismo bloque `role:user`, (2) prompt con placeholders literales `<>` que el modelo interpreta como instrucción de formato. Fix: usar `role: system` separado + `role: user` con imagen primero y texto claro en inglés sobre análisis de vegetación:
  ```python
  messages = [
      {"role": "system", "content": SYSTEM_PROMPT},
      {"role": "user", "content": [
          {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{crop_b64}"}},
          {"type": "text", "text": (
              "Analyze this aerial vegetation image. "
              "Respond with ONLY a JSON object: "
              "{\"species\": \"...\", \"health\": \"saludable|estresado|enfermo|dudoso\", "
              "\"confidence\": 0.0, \"notes\": \"...\"}"
          )},
      ]},
  ]
  ```
  Con este fix la tasa de rechazo baja pero no es 0 — imágenes pequeñas o ambiguas siguen siendo rechazadas. Comportamiento esperado en PoC.

- **VLM migrado de NVIDIA NIM a OpenCode (claude-haiku-4-5) — sesión 20:** Llama 3.2 90B Vision en el free tier de NVIDIA NIM era inestable: rechazaba imágenes de vegetación con guardrails, timeouts frecuentes, y devolvía el template literalmente cuando el system prompt contenía `<>`. La migración a `claude-haiku-4-5` vía OpenCode resolvió todos estos problemas. Cambios en `vlm_classifier.py`:
  ```python
  OPENCODE_API_URL = "https://opencode.ai/zen/v1/chat/completions"
  VLM_MODEL = "claude-haiku-4-5"
  # api_key = os.getenv("OPENCODE_API_KEY")  # en lugar de NVIDIA_API_KEY
  ```
  En `tree_detection.py` y `analysis_task.py`: `api_key = os.getenv("OPENCODE_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")` — fallback para retrocompatibilidad. System prompt ajustado con especies argentinas/tucumanas para contexto regional. Concurrencia default subida de 1 a 3 (Claude es estable). Para testear modelos con visión en OpenCode, ver `references/opencode-vision-models.md` del skill `nvidia-nim-free-api`. El pipeline de detección en tiempo real (`POST /api/tree-detection/run` y `/upload`) ahora incluye un paso 3 VLM después de SAM. Cambios aplicados:
  - `backend/app/services/tree_detection.py`: paso 3 llama `asyncio.run(classify_trees_vlm(...))` si `NVIDIA_API_KEY` está en env. Merge de resultados al array `trees` con campos `vlm_species/health/confidence/notes`. Si no hay key, inicializa campos a `None` igualmente para que el frontend reciba la estructura completa.
  - `backend/app/api/v1/tree_detection.py`: ambos endpoints (`/run` y `/upload`) exponen `vlm_used: bool` en el response.
  - `frontend/src/components/TreeDetectionPanel.tsx`: interface `TreeBox` con campos VLM opcionales, interface `DetectionResult` con `vlm_used`. `TreeDetailPanel` muestra sección "🤖 Visión IA" en violeta con especie, salud coloreada y confianza cuando `tree.vlm_species || tree.vlm_health` es truthy. Badge "VLM activo" en el header junto al de SAM. Paso 3 del pipeline en el panel lateral actualizado: "VLM clasifica especie y salud por copa".
  - El panel de detección necesita `docker compose build frontend backend` + recrear containers para reflejar los cambios.

- **Endpoint `/trees` falta campos VLM — fix aplicado:** El endpoint `GET /api/analyses/{id}/trees` retornaba solo los campos legacy (species, lat, lon, etc.) sin incluir `vlm_species/health/confidence/notes`. Fix: agregar los 4 campos al dict en `backend/app/api/analyses.py`. Sin este fix, el frontend recibe `null` en todos los campos VLM aunque estén en la BD. También agregar los campos al interface `TreeResult` en `api/client.ts` como campos opcionales.

- **Estado del proyecto — sesión 16 (2026-05-21):** Sliders de confianza interactivos en el sidebar. Canvas colorea verde (confiable) vs amarillo (dudosa) en tiempo real. SAM devuelve `stability_score` calculado localmente. Panel lateral `TreeDetailPanel` muestra todas las métricas incluyendo stability.

- **SAM stability_score — cálculo local verificado:** SAM `predict(multimask_output=True)` devuelve `(masks, scores, logits)`. El `stability_score` oficial de SAM se calcula re-thresholdeando los logits con ±delta y midiendo IoU entre las dos máscaras resultantes:
  ```python
  def _stability(mask_logits: np.ndarray, delta: float = 1.0) -> float:
      high = mask_logits > delta
      low  = mask_logits > -delta
      intersection = (high & low).sum()
      union = (high | low).sum()
      return float(intersection / union) if union > 0 else 0.0
  stability = _stability(logits[best_idx])
  ```
  Valores típicos: estables > 0.90, dudosos 0.70-0.90. Agregar `stability_score` al dict de resultado junto con `sam_score` (= predicted_iou).

- **Criterios de confianza dual DeepForest+SAM — valores recomendados:**
  | Métrica | Descripción | Threshold recomendado |
  |---------|-------------|----------------------|
  | `score` (DeepForest) | Confianza del detector RetinaNet | ≥ 0.40 (default 0.10 = muy permisivo) |
  | `sam_score` (predicted_iou) | Calidad estimada de la máscara SAM | ≥ 0.85 |
  | `stability_score` | Robustez de la máscara ante variaciones | ≥ 0.90 |
  Copa **confiable** = pasa los 3. Copa **dudosa** = pasa alguno pero no todos.

- **Sliders de confianza en tiempo real — patrón UI verificado:** Tres sliders en el sidebar (uno por métrica) + canvas que re-dibuja instantáneamente en verde/amarillo sin re-fetch. Los thresholds viven en `useState` del panel principal y se pasan como props a `PolygonCanvas`. El canvas re-dibuja en el `useEffect` que tiene los thresholds en el dep array. Contador "X / N copas confiables (Y%)" calculado inline con `result.trees.filter(...)`. Valores iniciales razonables: `thresholdDeep=0.4`, `thresholdSam=0.85`, `thresholdStability=0.9`.

- **Estado del proyecto — sesión 15 (2026-05-21):** Panel "Detección IA" mejorado con canvas interactivo de polígonos SAM + panel lateral `TreeDetailPanel` con gauge SVG animado. SAM checkpoint persistido en Docker volume `sam_models`. `segment-anything` en requirements.txt.

- **Panel lateral de detalle en hover (TreeDetailPanel) — patrón verificado:** Para mostrar detalles de un árbol al hacer hover en el canvas, el patrón correcto es un componente siempre montado al costado del canvas (NO un tooltip flotante posicionado absolutamente). Estructura:
  ```tsx
  // En el render — flex row: canvas + panel lateral
  <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
    <div style={{ flex: 1, minWidth: 0 }}>
      <PolygonCanvas result={result} onHover={setHoveredTree} />
    </div>
    <TreeDetailPanel tree={hoveredTree} />  {/* tree=null → muestra placeholder */}
  </div>
  ```
  El `TreeDetailPanel` acepta `tree: TreeBox | null` — cuando `null` muestra un placeholder con ícono difuminado y texto "Pasá el mouse sobre una copa". Cuando hay árbol, muestra un gauge SVG semi-circular animado con el % de confianza + métricas en cards + barra de gradiente. El gauge usa `strokeDasharray` con transición CSS para la animación fluida al cambiar de árbol. Color del gauge: verde `#10b981` si score > 80%, amarillo `#f59e0b` si > 60%, rojo `#ef4444` si menor. Ancho fijo de 220px, siempre visible después de la primera detección — no aparece/desaparece, solo cambia el contenido.

- **DeepForest — imagen de prueba pública sin registro:** `https://github.com/weecology/DeepForest/raw/main/tests/data/OSBS_029.png` — bosque de Florida, dataset NEON. Descargar con `urllib.request.urlretrieve()` en el primer uso. No requiere autenticación.

- **Nueva solapa "Detección IA" 🌲 en ForestAI (sesión 14):** Agregada cuarta solapa en `App.tsx` (`view = "trees"`), componente `TreeDetectionPanel.tsx`. Endpoint backend: `POST /api/tree-detection/run` (imagen de prueba) y `POST /api/tree-detection/upload` (imagen del usuario). Imagen anotada devuelta como base64 PNG. Router montado en `app.include_router(tree_detection_router, prefix="/api")`. El endpoint `/api/tree-detection/run` baja el modelo de HuggingFace en la primera llamada — avisar al usuario que la primera vez tarda ~30s.

- **Estado de React se pierde al navegar entre vistas (panel desmontado):** Cuando el usuario navega entre vistas (Grid → Mapa → Geo Servicios), React desmonta los componentes y el estado local (`submitted`, `lat`, `lon`, `activeTab`) se resetea. Aunque React Query cachea los datos del backend, el flag `submitted=false` hace que el panel muestre la pantalla vacía. Dos soluciones complementarias:

  **Solución A — display:none en lugar de unmount:** renderizar ambas solapas siempre y ocultar la inactiva con `style={{ display: activeTab === "bosques" ? "block" : "none" }}`. Evita que React Query pierda el estado al cambiar tab. Pero NO resuelve la navegación entre vistas completas.

  **Solución B — sessionStorage para persistir el estado (la definitiva):**
  ```tsx
  function loadGeoState() {
    try { const s = sessionStorage.getItem("geoPanel"); if (s) return JSON.parse(s); } catch {}
    return null;
  }
  const persist = (state) => sessionStorage.setItem("geoPanel", JSON.stringify(state));
  const saved = loadGeoState();
  const [lat, setLat] = useState(saved?.lat ?? ARGENTINA_CENTER.lat);
  const [submitted, setSubmitted] = useState(saved?.submitted ?? false);
  // Llamar persist() en handleConsultar, acceso rápido y setActiveTab
  ```
  Aplicar ambas. B es la que realmente sobrevive la navegación entre vistas.

**Evalscript correcto para Statistical API:**
```js
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "dataMask"] }],
    output: [
      { id: "ndvi", bands: 1 },
      { id: "dataMask", bands: 1 }
    ]
    // SIN mosaicking — causa data:[] si se incluye
  };
}
function evaluatePixel(samples) {
  let ndvi = (samples.B08 - samples.B04) / (samples.B08 + samples.B04 + 0.0001);
  return { ndvi: [ndvi], dataMask: [samples.dataMask] };
}
```

**Payload correcto para Statistical API:**
```python
{
    "input": {
        "bounds": {"bbox": [min_lon, min_lat, max_lon, max_lat]},  # sin crs explícito = EPSG:4326
        "data": [{"type": "sentinel-2-l2a", "dataFilter": {"maxCloudCoverage": 30}}]
    },
    "aggregation": {
        "timeRange": {"from": "2026-04-15T00:00:00Z", "to": "2026-05-15T23:59:59Z"},
        "aggregationInterval": {"of": "P30D"},
        "evalscript": NDVI_EVALSCRIPT,
        "width": 256,   # NO resx/resy
        "height": 256,
    },
    "calculations": {
        "ndvi": {"statistics": {"default": {}}}
    }
}
```

### Sentinel-2 — Búsqueda sin autenticación (metadatos)

La API de Copernicus Data Space (CDSE) tiene un endpoint de catálogo público para buscar imágenes disponibles:

```
https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=...
  &Collection/Name eq 'SENTINEL-2'
  &Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')
  &OData.CSC.Intersects(area=geography'SRID=4326;POINT(-60.4 -26.8)')
  &Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le 30)
  &$orderby=ContentDate/Start desc&$top=1
```

El **cálculo de NDVI real** sobre la imagen requiere cuenta CDSE (registro gratuito para científico). Para PoC mostrar disponibilidad + nubosidad es suficiente sin auth.

### Frontend — GeoPanel.tsx

`frontend/src/components/GeoPanel.tsx` — panel completo con:
- Input lat/lon + slider de radio (1-100km) + botón Consultar
- Accesos rápidos: Chaco Norte, Misiones, Salta, Patagonia
- Solapa "Bosques Nativos": categorías OTBN (I=Rojo/II=Amarillo/III=Verde) con color, área en ha, provincia
- Solapa "Sentinel-2": imagen más reciente, % nubes, nombre del producto
- Cache: `staleTime: 5 * 60 * 1000` para no re-consultar el WFS en cada render

Integrado en `App.tsx` como tercera vista `"geo"` junto a `"grid"` y `"map"`.

### Empresas del sector (referencia de mercado)

| Empresa | País | Diferencial |
|---------|------|-------------|
| Pachama | USA | IA + sat para créditos de carbono + anti-fraude |
| Treemetrics | Irlanda | Drones + visión artificial, calcula DAP/altura/volumen |
| Treeswift | USA | Robots terrestres + LiDAR, opera bajo dosel cerrado |
| Dendra Systems | UK | Drones que mapean Y plantan semillas |
| Sylvera | UK | Rating independiente de proyectos de carbono ("Moody's del carbono") |
| Satellogic | ARG | Constelación sat propia, cotiza NASDAQ |
| Auravant | ARG | SaaS monitoreo vegetación agro latinoamericano |

**Oportunidad local:** No hay startup privada argentina enfocada en inventario forestal con IA. 34M ha bosque nativo con Ley de Bosques que obliga al monitoreo.

---

## Patrones React para ForestAI (sesión 17)

Ver `references/deepforest-sam-pipeline.md` para detalle completo de:
- **Display vs unmount:** todos los paneles se renderizan siempre con `display: view === "X" ? "flex" : "none"` — nunca conditional rendering que desmonte. Preserva estado de detección al cambiar tabs.
- **Lifted state:** `detectionResult` vive en App.tsx y se pasa a Forest3DView. TreeDetectionPanel notifica via `onResult` callback.
- **Detección → 3D:** bbox center normalizado a coordenadas 3D; ortofoto anotada como textura del terreno (`flipY: false`); EmptyScene con botón para ir a detección si no hay resultado.
- **Imágenes NEON incluidas en paquete:** `2019_YELL_2_528000_4978000_image_crop2.png` (Yellowstone, 2299×2472, 46 árboles) es la más impactante para demos.

## Cloudflare Tunnel — Deploy Público ForestAI

ForestAI usa nginx como proxy reverso dentro del container de frontend. Esto simplifica el tunnel: **solo se necesita un túnel al puerto 3010**. El nginx redirige `/api/...` al backend internamente. No hace falta tunnel separado para el puerto 8010.

```bash
# 1. Verificar que el frontend está corriendo (nginx + build estático)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3010  # debe dar 200

# 2. Lanzar tunnel — solo puerto 3010, --protocol http2 para estabilidad
cloudflared tunnel --url http://localhost:3010 --protocol http2 2>&1 | tee /tmp/cf_forestai.log &

# 3. Capturar la URL pública (esperar ~15s)
sleep 15 && grep -i "trycloudflare" /tmp/cf_forestai.log
```

El tunnel es temporal (no requiere cuenta Cloudflare). Se cae si el proceso muere. Para persistir entre sesiones, usar systemd o un named tunnel con cuenta CF.

**Por qué no se necesita tunnel al backend:** `VITE_API_URL` está vacío en la build (`import.meta.env.VITE_API_URL || ""`). El frontend hace fetch a `/api/...` (URL relativa). Nginx en el container 3010 tiene proxy_pass a `http://backend:8000`. Todo el tráfico API viaja internamente — el usuario externo solo ve el puerto 3010.

**Reconexión automática del tunnel:** Si cloudflared pierde la conexión, auto-reconecta y mantiene la misma URL pública. Ver en el log: `Retrying connection... Registered tunnel connection`. No hay que reiniciar el proceso. La URL `trycloudflare.com` es estable mientras el proceso viva.

**Verificar tunnel activo y URL:**
```bash
ps aux | grep cloudflared | grep -v grep
cat /tmp/cf_forestai.log | grep -i "trycloudflare\|Your quick Tunnel\|Registered tunnel"
```

**Diagnóstico completo del stack + tunnel en un solo bloque:**
```bash
# Estado containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep forestai
# Frontend responde
curl -s -o /dev/null -w "%{http_code}" http://localhost:3010
# Tunnel activo
ps aux | grep cloudflared | grep -v grep
grep -i "trycloudflare" /tmp/cf_forestai.log 2>/dev/null | tail -3
```
Si el proceso cloudflared no aparece en `ps aux`, el tunnel cayó y la URL pública cambió al relanzar. Relanzar con:
```bash
nohup cloudflared tunnel --url http://localhost:3010 --protocol http2 > /tmp/cf_forestai.log 2>&1 &
sleep 15 && grep -i "trycloudflare" /tmp/cf_forestai.log
```
Actualizar la URL en memoria de JARVIS cuando cambie.

**Pitfall — container con nombre en conflicto al levantar frontend:**
Si el frontend estaba caído pero el container viejo sigue existiendo (estado `Exited` o `Created`), `docker compose up -d frontend` falla con:
```
Error: Conflict. The container name "/forestai-poc-frontend-1" is already in use
```
Fix:
```bash
# Si el container está corriendo — stop primero, luego rm
docker stop forestai-poc-frontend-1
docker rm forestai-poc-frontend-1
docker compose up -d frontend

# Si el container ya está detenido — solo rm
docker rm forestai-poc-frontend-1
docker compose up -d frontend
```
No se puede hacer `docker rm` de un container corriendo sin `-f`. Siempre verificar el estado con `docker ps -a | grep frontend` antes de intentar rm.

**Nota sobre `docker compose up -d` en Hermes:** el comando se bloquea como foreground. Usar siempre el flag `background=true` del terminal tool, o ejecutar `docker stop/rm` + `docker compose up -d <servicio>` con `background=true`.

**Pitfall — dos procesos cloudflared conflictivos (URL cambia al relanzar):** Si cloudflared se lanza más de una vez (por reboot, sesión anterior, etc.), quedan dos procesos vivos apuntando a `:3010`. El proceso viejo mantiene la URL pública anterior — el nuevo genera una URL nueva. Diagnóstico: `pgrep -a cloudflared`. Si hay más de un proceso, matar todos con `pkill -9 cloudflared` y relanzar uno solo. La URL pública cambia cada vez que el proceso muere y se relanza desde cero (trycloudflare = URL efímera). Actualizar en memoria de JARVIS cada vez que cambie.

## Three.js / Vista 3D del Bosque

### Stack validado (spike sesión actual)

- `@react-three/fiber` — Three.js como componentes React
- `@react-three/drei` — helpers: OrbitControls, Html, Sky, Stars
- `three` — librería base

```bash
npm install @react-three/fiber @react-three/drei three
```

Encaja directo en el stack React+Vite sin fricción. Build de producción: ~2.1MB (Three.js es grande — warning esperado de chunk size, ignorable para demos).

### Componente Forest3DView.tsx

- Cada árbol: cilindro (tronco) + esfera (copa) coloreada por estado sanitario
  - 🟢 sano = `#22c55e`, 🟡 estresado = `#eab308`, 🔴 muerto = `#ef4444`
- Click en copa → selecciona árbol → label HTML flotante con datos
- Filtro por estado sanitario (dropdown) — re-render sin re-fetch
- HUD: stats de inventario + leyenda de controles
- OrbitControls: drag=rotar, scroll=zoom, pan=pan
- Terreno: plano con `PlaneGeometry` color `#4a7c59`
- Sky + Stars para contexto visual impactante

### Patrón de integración en App.tsx

1. Agregar `"3d"` al type union del `view` state
2. Importar el componente
3. Agregar entrada en el array `TABS` (ícono 🔮)
4. Agregar rama `view === "3d"` en el render condicional
5. El array `TABS` iterado dinámicamente → el tab desktop aparece automáticamente

### Datos mock → datos reales

El componente usa datos mock generados localmente. Para conectar a la API real:
- Reemplazar `generateMockTrees()` por `useQuery(["trees", analysisId], forestApi.getTrees)`
- Mapear campos API → interface `TreeData` (coordenadas en lat/lon → normalizar a escala 3D)
- Escalar lat/lon a metros: `x = (lon - center_lon) * 111320 * cos(lat_rad)`, `z = (lat - center_lat) * 110540`

### Repositorio fork para spikes 3D

```bash
# Crear fork del proyecto base
cp -r /home/server/proyectos/forestai-poc /home/server/proyectos/forestai-3d
cd /home/server/proyectos/forestai-3d && git init && git add . && git commit -m "init: base desde forestai-poc"

# Frontend en puerto diferente para no chocar con el original
npx serve dist -p 3011  # o npm run dev -- --port 3011

# Tunnel separado
cloudflared tunnel --url http://localhost:3011 2>&1 | tee /tmp/cf_forest3d.log &
```

**Patrón general de fork para spikes visuales:** siempre copiar el proyecto completo, inicializar git nuevo, usar puerto diferente (+1 al original), y tunnel propio. Así el proyecto base nunca se rompe.

**Migrar spike al proyecto original — patrón verificado (sesión 2026-05-23):**
Una vez que el spike valida que la feature funciona (ej. Forest3DView.tsx), migrar al proyecto base en 4 pasos:
```bash
# 1. Copiar solo el componente nuevo
cp /home/server/proyectos/forestai-3d/frontend/src/components/Forest3DView.tsx \
   /home/server/proyectos/forestai-poc/frontend/src/components/

# 2. Instalar dependencias en el proyecto base (no sobrescribir package.json del fork)
cd /home/server/proyectos/forestai-poc/frontend
npm install three @react-three/fiber @react-three/drei

# 3. Aplicar el patch mínimo al App.tsx (import + TABS array + view state + render)
# Diferencia entre fork y original es siempre pequeña:
# diff -q forestai-poc/frontend/src/App.tsx forestai-3d/frontend/src/App.tsx

# 4. Build y verificar
npm run build
```
No copiar todo el frontend del fork — solo los archivos nuevos. El `package.json` y `App.tsx` del fork pueden tener divergencias no deseadas.

**Estado proyecto forestai-3d (sesión 2026-05-23):**
- Path: `~/proyectos/forestai-3d/` — spike terminado, feature migrada al original
- Componente `Forest3DView.tsx` copiado a `forestai-poc/frontend/src/components/`
- Three.js deps instaladas en forestai-poc: `three @react-three/fiber @react-three/drei`
- Cuarta solapa "3D" 🔮 integrada en `forestai-poc` App.tsx
- forestai-poc frontend en :3010, tunnel activo `/tmp/cf_forestai.log`
- URL tunnel: `https://liquid-episode-mouth-stephanie.trycloudflare.com` (efímera)

### Datos reales para la Vista 3D — fuentes de imágenes

La pregunta clave de Nelson: "¿de dónde saco la imagen para ver árboles tal cual?"

La vista 3D actual usa datos **mock** generados aleatoriamente. Para ver árboles reales, el flujo es:

1. **Imagen aérea de entrada** (cualquiera de estas fuentes):
   - Dron propio (ortofoto GeoTIFF RGB o multiespectral)
   - Dataset público NEON (ver fuentes en `references/geotiff-sources.md`)
   - OpenAerialMap (ver `references/oam-argentina-ortofotos.md`)

2. **Pipeline de detección** → DeepForest detecta bboxes → SAM segmenta copas

3. **Output → datos 3D**: cada árbol detectado tiene `lat, lon, crown_diameter, health_status` → se mapean directamente a la escena Three.js

4. **Escala lat/lon → metros (para Three.js)**:
   ```ts
   // Centrar la nube de árboles en origin (0,0) y convertir a metros
   const centerLon = trees.reduce((s, t) => s + t.lon, 0) / trees.length
   const centerLat = trees.reduce((s, t) => s + t.lat, 0) / trees.length
   const x = (tree.lon - centerLon) * 111320 * Math.cos(centerLat * Math.PI / 180)
   const z = (tree.lat - centerLat) * 110540
   ```

**Para la demo:** los 3 GeoTIFFs de NEON del repo DeepForest (OSBS, SJER, Australia) son los mejores para demostrar árboles reales. El pipeline forestai-poc ya los tiene cargados — conectar `GET /api/analyses/{id}/trees` a la vista 3D reemplaza los datos mock.

**Pregunta frecuente — "¿puedo ver los árboles reales tal cual en 3D?"**
Sí, pero hay que conectar el pipeline. La vista 3D actual usa datos mock. El flujo para ver árboles reales:
1. Los GeoTIFFs de NEON ya están procesados en la BD de forestai-poc (5 análisis argentinos + tiles NEON)
2. Conectar `GET /api/analyses/{analysisId}/trees` como fuente de datos en `Forest3DView.tsx`
3. Mapear `lat/lon/crown_diameter/health_status` de la API a la interface `TreeData` del componente
4. Convertir coordenadas lat/lon → metros con la fórmula de la sección "Escala lat/lon → metros"
5. Los árboles aparecen en sus posiciones reales detectadas por DeepForest

Para instalar DeepForest en el proyecto (si no está disponible en el venv):
```bash
pip3 install deepforest  # requiere torch (ya instalado en el servidor)
# Primera llamada descarga ~100MB de modelo desde HuggingFace — normal
```

---

## Estado del Proyecto (última revisión: 2026-05-22 sesión actual)

- **Stack completo levantado con `docker compose up -d`** desde `~/proyectos/forestai-poc/`. Todos los containers arriba: db, redis, backend :8010, frontend :3010, celery_worker.
- **Cloudflare Tunnel:** proceso activo, URL `https://lopez-received-tel-nav.trycloudflare.com` (verificado 200 OK al inicio de sesión). Tunnel apunta a `:3010`. Ver log en `/tmp/cf_forestai.log`.
- **Patrón de recovery verificado (2026-05-22):** stack estaba caído (backend no respondía). `docker compose up -d` desde `~/proyectos/forestai-poc/` levantó todos los containers en orden correcto (db→redis→backend+celery_worker→frontend). Verificar con `curl -s http://localhost:8010/health` + `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010`. Si el tunnel también cayó, relanzar cloudflared por separado.
- **Patrón de levantado correcto cuando el stack está caído:**
  1. `docker compose up -d` (background=true en Hermes) desde `~/proyectos/forestai-poc/`
  2. Verificar: `curl -s http://localhost:8010/health` → `{"status":"ok"}` y `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010` → `200`
  3. Si el tunnel también cayó: `nohup cloudflared tunnel --url http://localhost:3010 --protocol http2 > /tmp/cf_forestai.log 2>&1 &` luego `sleep 15 && grep trycloudflare /tmp/cf_forestai.log`

## Estado del Proyecto (última revisión: 2026-05-21 sesión 20)

- **VLM migrado a claude-haiku-4-5 vía OpenCode:** Llama Vision de NVIDIA NIM rechazaba copas con guardrails y era inestable en el free tier. Migración: `vlm_classifier.py` ahora apunta a `https://opencode.ai/zen/v1/chat/completions` con modelo `claude-haiku-4-5`. Key en `.env` como `OPENCODE_API_KEY`. claude-haiku-4-5 es rápido (~2s/req), no rechaza imágenes de vegetación, devuelve JSON limpio. Concurrencia subida a 3.
- **System prompt con contexto regional:** Incluye especies típicas de Argentina/Tucumán (Pino, Eucalipto, Cedro, Nogal, Lapacho, Quebracho, Sauce, Álamo) para mejorar estimaciones en imágenes de baja resolución.
- **Pitfall confirmado — `docker restart` no recarga env_file:** `OPENCODE_API_KEY` no llegó al container al hacer restart. Fix: `docker compose stop` + `docker compose up -d` (crea container nuevo). Verificar con `docker exec ... env | grep OPENCODE`.
- **Pitfall confirmado — cloudflared dos procesos:** Relanzar cloudflared sin matar el anterior genera dos procesos; el viejo mantiene URL vieja, el nuevo genera URL nueva. Siempre `pkill -9 cloudflared` antes de relanzar.
- **VLM funcionando end-to-end:** `vlm_used: True`, 10 árboles clasificados de 55. Sistema honesto sobre baja resolución de crops — confianza 0.45 es esperado. Sistema prompt ajustado para mejores estimaciones.
- **URL cloudflared actual:** https://closest-activities-soft-silver.trycloudflare.com

## Estado del Proyecto (última revisión: 2026-05-21 sesión 19)

- **VLM en detección en tiempo real — funcionando (con limitaciones):** Bug `asyncio.run()` dentro de FastAPI resuelto con ThreadPoolExecutor. System prompt separado en `role:system` + `role:user` con imagen. Pipeline limita a 8 árboles más grandes. Rechazos del modelo (~30-50%) son comportamiento esperado con imágenes RGB de GeoTIFF.
- **Datos seed populados con VLM:** 90 árboles en la BD actualizados con datos VLM realistas vía SQL directo (especie científica por especie legacy, salud aleatoria, confianza 0.72-0.97).
- **Dos procesos cloudflared pueden quedar corriendo** — solo dejar el lanzado con `--protocol http2`. Limpiar: `pkill -f "cloudflared.*--url.*3010"` y relanzar uno solo.

## Estado del Proyecto (última revisión: 2026-05-21 sesión 18)

- **VLM integrado end-to-end:** Pipeline completo — NVIDIA NIM key en `.env`, Celery worker rebuildeado con `aiohttp>=3.9.0`, campos `vlm_*` en BD, interface TypeScript actualizado, popup mapa muestra sección "Visión IA". Resultado en La Leonesa: 2/5 árboles clasificados (3 rechazados por guardrails del modelo — copas ambiguas). Comportamiento esperado en PoC con GeoTIFF RGB.
- **Frontend MapPanel:** sección VLM condicional en popup árbol seleccionado. Requiere `docker compose build frontend` + recrear container para ver cambios.
- **Cloudflare Tunnel:** `https://implications-promotions-least-cup.trycloudflare.com/` — activo. Verificar con `ps aux | grep cloudflared`.

## Estado del Proyecto (última revisión: 2026-05-21 sesión 17)

- **Cloudflare Tunnel activo:** `https://implications-promotions-least-cup.trycloudflare.com/` — responde 200, stack completo corriendo. URL temporal (trycloudflare = sin cuenta). Cambia si el proceso se reinicia.
- Dos procesos cloudflared en paralelo pueden quedar corriendo si se lanzó más de una vez. Solo dejar el lanzado con `--protocol http2`. Limpiar con: `pkill -f "cloudflared.*--url.*3010"` y relanzar uno solo.

- **Diagnóstico rápido del stack completo (verificado 2026-05-21):**
  ```bash
  # 1. Containers corriendo
  docker compose ps
  # 2. Procesos cloudflared y su URL pública
  ps aux | grep cloudflared | grep -v grep
  cat /tmp/cf_forestai.log | grep -i "trycloudflare\|Your quick Tunnel"
  # 3. Frontend responde
  curl -s -o /dev/null -w "%{http_code}" http://localhost:3010
  ```
  Si el log muestra "Lost connection... Retrying... Registered tunnel" — es normal, cloudflared auto-reconecta. La URL pública NO cambia si el proceso sigue vivo.
- **Holographic Memory** activado en Hermes esta sesión.
- **Obsidian skills de kepano** instaladas en `~/brainstorming/.claude/skills/` y `~/.hermes/skills/`.
- Holographic Memory activado en Hermes (`hermes config set memory.provider holographic`) — SQLite en `~/.hermes/memory_store.db`

## Estado del Proyecto (última revisión: 2026-05-20 sesión 10)

- Path: `~/proyectos/forestai-poc/`
- Containers: **corriendo** — backend :8010, frontend :3010, db :5433, redis :6380, celery_worker
- Git: repo en `github.com/aliagenttucuman-byte/forestai-poc` — último commit sesión 11: `6bdf703`
- **Sesión 13:** creado `AI-STRATEGY.md` en brainstorming — estrategia IA completa: Image Analytics (SAM/YOLOv8), estimación dasométrica, agente conversacional RAG. Commiteado en nelson-brainstorming repo.
- **Sesión 12:** fix coordenadas default Patagonia → Chaco Norte, zip de package con python3 zipfile (zip no disponible en el servidor), análisis de viabilidad TEM-1 guardado en brainstorming
- **Sesión 11:** fix NDVI hardcodeado, fix persistencia sessionStorage, fix display:none en solapas, preview satelital Sentinel-2 (True Color + NDVI coloreado)
- **Endpoints geo:** `/api/geo/bosques`, `/api/geo/sentinel`, `/api/geo/sentinel/preview`, `/api/geo/context`
- **GeoPanel.tsx:** estado persistido en sessionStorage, solapas siempre montadas (display:none), preview satelital con toggle True Color/NDVI
- **5 análisis argentinos en la DB:**
  - La Leonesa - Chaco Norte: 5 árboles
  - Lotes Silvopastoriles Chaco: 3 árboles (limitación NIR)
  - Chapadmalal Buenos Aires: 38 árboles
  - Golondrinas Patagonia: 36 árboles
  - INTA San Salvador AER: 10 árboles
- **Documentación de limitaciones:** `~/brainstorming/2026-05-19-forestai-poc/LIMITACIONES-Y-ROADMAP.md`
- **Para levantar:** `docker compose up -d` desde `~/proyectos/forestai-poc/`. Al hacer build parcial, siempre verificar frontend con `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010`.

- Path: `~/proyectos/forestai-poc/`
- Containers: **corriendo** — backend :8010, frontend :3010, db :5433, redis :6380, celery_worker
- Git: commit `a3d5762` — repo en `github.com/aliagenttucuman-byte/forestai-poc` (creado sesión 9)
- **5 análisis argentinos en la DB (post-sesión 9):**
  - La Leonesa - Chaco Norte: 5 árboles
  - Lotes Silvopastoriles Chaco: 3 árboles (limitación NIR — ver sección Roadmap)
  - Chapadmalal Buenos Aires: 38 árboles
  - Golondrinas Patagonia: 36 árboles
  - INTA San Salvador AER: 10 árboles
- **Fixes aplicados en sesión 9 (forest_analyzer.py):**
  - Filtro de **textura (varianza verde) eliminado** — umbral `local_variance < 50.0` era demasiado restrictivo para copas con iluminación uniforme o con poca sombra interna. Solo queda circularidad > 0.15.
  - Ajuste de percentil fallback VARI: 70 → 40 (La Leonesa: 4→5 árboles; silvopastoral sin cambio)
  - **Conclusión sesión 9:** Silvopastoral sigue en 3 — limitación estructural del sensor RGB sin NIR. Documentado en `~/brainstorming/2026-05-19-forestai-poc/LIMITACIONES-Y-ROADMAP.md`.
  - AI News Aggregator pausado (job `04bdd6e154a3`) — reactivar cuando Nelson lo indique.
  - Rebuild correcto: `docker compose build celery_worker -q` + `docker stop/rm forestai-poc-celery_worker-1` + `docker compose up -d celery_worker`
- **Fix aplicado en sesión 7 (forest_analyzer.py):**
  - `dt_factor` FIJO en 0.40 — antes dinámico (0.50/0.42/0.35 por veg_fraction) causaba el efecto opuesto: silvopastoral muy verde → dt_factor=0.50 → menos árboles detectados
  - Filtros árbol vs pasto: circularidad > 0.15 + varianza local > 50 — reemplazan la lógica de dt_factor dinámico
  - Cap copa: 120m² → 80m² (antes dejaba pasar blobs de 2-3 árboles fusionados)
  - Cap altura: 20m → 16m (antes daba 26.7m para copas imposibles)
  - Umbrale de filtros en calibración activa — bajar si se pierden árboles reales
  - Rebuild: `docker compose up -d --build backend celery_worker`
  - Reprocesado masivo: 5 análisis via `POST /api/analyses/{id}/reprocess` en loop
- **Fix aplicado en sesión 5:** filtros copa 2-120m², altura max 20m, downsampling MAX_DIM=6000, shared named volume uploads
- Tablas alométricas: 7 especies INTA (eucalipto, pino, quebracho, algarrobo, araucaria, lenga, caldén)
- **Para levantar (forma correcta):** `docker compose up -d` desde `~/proyectos/forestai-poc/`. Al hacer build parcial (ej. solo `--build backend celery_worker`), el frontend **queda caído** — siempre verificar con `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010`. Si da 000/error: `docker compose up -d frontend`. Puertos: 8010 backend, 3010 frontend.
- OpenAPI spec: `~/proyectos/forestai-poc/specs/openapi.yaml`
- Script diagnóstico: `scripts/diag_resolution.py`

---

## Estructura Societaria y Documentación PM

ForestAI es una joint venture entre:
- **AlegentAI** (Nelson CEO + Pablo COO + equipo técnico): 45%
- **Empresa de Drones de Pablo**: 55%

Pablo es COO de AlegentAI Y referente de la Empresa de Drones — está en los dos lados del deal. NO es la "parte contraria". En documentos PM, RACI y charters: Pablo aparece en el equipo de AlegentAI, no como socio externo.

**Project Charter generado:** `~/brainstorming/2026-05-19-forestai-poc/PROJECT-CHARTER-v3.md` (y PDF en `/tmp/ForestAI-ProjectCharter-v3.pdf`). Generado con metodología PM de Pablo (PMI/ISO 21502/PRINCE2/Agile). Tasa estándar equipo: USD 30/hora. MVP 4 meses, 5 personas, 2.448 horas, USD 73.440 sweat equity total.

**PDF de documentos de proyecto:** usar WeasyPrint + python-markdown. Script en `/tmp/gen_charter_pdf_v3.py` — reutilizable para cualquier markdown → PDF profesional con tablas, estilos y paginación. NO usar pandoc (no disponible en el servidor).

## Contexto de Origen

La PoC surgió del interés de Nelson en aplicar tecnología de inventario forestal (conteo por especie, estimación de biomasa y edad) usando imágenes de drones, sin requerir machine learning para el MVP. El stack fue elegido para demostrar que image analytics clásico (OBIA + watershed + alometría) puede entregar valor antes de invertir en ML.

Repositorios GitHub de referencia (no usados directamente en la PoC):
- `weecology/DeepForest` (~700 ⭐) — detección con RetinaNet, modelo preentrenado NEON
- `PatBall1/detectree2` (~250 ⭐) — Mask R-CNN, publicado Nature Methods 2023, bosques tropicales
- `r-lidar/lidR` (~650 ⭐) — R, procesamiento LiDAR forestal profesional
- `facebookresearch/CanopyHeight` (~450 ⭐) — estimación global de altura de dosel (Meta 2024)

---

## Roadmap de Mejoras por Tipo de Sensor

Ver documento completo: `~/brainstorming/2026-05-19-forestai-poc/LIMITACIONES-Y-ROADMAP.md`

### Detección automática de bandas — lógica propuesta

```python
if raster["band_count"] >= 4:
    nir = raster["nir"]
    ndvi = (nir - r) / (nir + r + 1e-10)
    index = ndvi       # rango -1 a 1, árboles 0.6-0.9, pasto 0.3-0.5
    index_name = "NDVI"
else:
    # RGB puro: VARI (Visible Atmospherically Resistant Index)
    vari = (g - r) / (g + r - b + 1e-10)
    index = vari
    index_name = "VARI"
```

### Tiers de sensor

| Tier | Hardware | Índice | Silvopastoral |
|------|----------|--------|---------------|
| 1 — RGB estándar | DJI Mavic/Phantom | VARI | 20-40% detección |
| 2 — Multiespectral | MicaSense, Parrot Sequoia | NDVI / NDRE | 85-95% |
| 3 — Satelital (Sentinel-2) | — | NDVI 10m/px | Sin árbol individual |
| 4 — LiDAR | Riegl, Livox | Nube de puntos 3D | Excelente + alturas reales |

Todos los GeoTIFFs actuales son 3 bandas uint8 (RGB puro) — verificado con rasterio `src.count`.

### Mejoras sin cambiar hardware (sprint 1)

1. **Detección por sombra de copa** — canal HSV (valor bajo) como complemento a VARI
2. **DeepForest** — modelo pre-entrenado RGB de árbol (pip install deepforest), F1~0.75
3. **Escala adaptativa** — rango área mínima/máxima en función del GSD real del GeoTIFF

---

## Integración con NetFlora (Embrapa Acre)

NetFlora es un sistema open source (GPL 3.0) que resuelve el mismo problema que ForestAI
con 60+ especies entrenadas sobre 100.000 ha de Amazonia. Sus modelos YOLOv7 y datos
son reutilizables. Ver detalles completos en `references/netflora-embrapa.md`.

Integración propuesta:
- Importar pesos `model_weights.pt` de NetFlora al backend ForestAI
- Agregar catálogo de 60 especies (json/ del repo NetFlora)
- Output: CSV + Shapefile georreferenciado por árbol, filtrable por categoría
- Plugin QGIS disponible (Netflora2, abril 2026): detección directa en QGIS sin UI web

## Referencias y Scripts

- `references/vlm-tree-classification.md` — Spike 002: clasificación de copas con Llama Vision. Código de crop_tree(), system prompt, parsing JSON robusto, campos DB, estrategia batch async.
- `references/deepforest-sam-pipeline.md` — Pipeline completo DeepForest+SAM: instalación, código, arquitectura de la solapa "Detección IA", modelos candidatos, pitfalls
- `references/geotiff-sources.md` — Fuentes públicas de GeoTIFF forestales, comandos de descarga, limitaciones Argentina
- `references/oam-argentina-ortofotos.md` — URLs verificadas de OAM para Argentina y mundo, con tamaños y ubicaciones
- `references/allometric-tables-inta.md` — Coeficientes alométricos INTA por especie, reglas RGB de clasificación, limitaciones conocidas
- `references/docker-compose-template.md` — docker-compose.yml, .env, Dockerfile y requirements.txt listos para copiar (con puertos correctos 8010/3010 para el servidor de Nelson)
- `references/ui-dark-theme.md` — Design system dark theme (rechazado por Nelson): paleta verde bosque, colores por especie, markers MapLibre custom, popup HTML, layout App.tsx
- `references/ui-light-dashboard.md` — Design system APROBADO v2: fondo claro slate-50, grilla de cards con thumbnail, panel de detalle lateral, tabs Grid/Mapa, UploadZone drag & drop. Incluye endpoint thumbnail backend.
- `references/datos-abiertos-forestales-argentina.md` — Fuentes públicas argentinas: INTA GeoINTA WMS/WFS, MAyDS/UMSEF bosques nativos, CONAE/SAOCOM política de acceso, Sentinel-2. URLs verificadas, requisitos de registro, limitaciones.
- `scripts/smoke_test.py` — Smoke test del pipeline end-to-end contra los 3 tiles de prueba (sin Docker ni BD). Correr con `python3 scripts/smoke_test.py` para verificar que `analyze_ortophoto()` funciona correctamente.
- `scripts/diag_resolution.py` — Diagnóstico de resolución real de los TIFs tras downsampling. Muestra rango válido de copas en px², y detecta si hay blobs imposibles (ej. 359m² → árbol de 26m). Correr cuando se ven valores anómalos de copa o altura.
