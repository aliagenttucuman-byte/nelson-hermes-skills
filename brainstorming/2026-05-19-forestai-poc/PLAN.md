# ForestAI PoC — Plan de Implementación

**Fecha:** 2026-05-19
**Tipo:** Flujo I+D+I simplificado (máx 2 días)
**Stack:** FastAPI + React 18 + MapLibre + Celery + Redis + PostGIS

---

## Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (React + Vite + TypeScript)                           │
│                                                                 │
│  UploadPage          DashboardPage                             │
│  └─ DropZone         ├─ MapView (MapLibre GL JS)               │
│     └─ ProgressBar   │   ├─ OrthoLayer (GeoTIFF raster)        │
│                      │   └─ TreeLayer (GeoJSON polígonos)       │
│                      ├─ TreePanel (detalle al click)            │
│                      └─ SummaryPanel (totales + especies)       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP REST
┌────────────────────────────────▼────────────────────────────────┐
│  BACKEND (FastAPI)                                              │
│                                                                 │
│  routers/analyses.py    services/forest_analyzer.py            │
│  routers/trees.py       services/allometric.py                 │
│  routers/export.py      services/geojson_builder.py            │
│                                                                 │
│  tasks/analysis_task.py  (Celery)                              │
│  └─ 1. load_raster()    → Rasterio lee GeoTIFF                │
│  └─ 2. segment_crowns() → OpenCV watershed                     │
│  └─ 3. classify_species() → reglas RGB                         │
│  └─ 4. compute_metrics() → tablas alométricas INTA             │
│  └─ 5. build_geojson()  → Geopandas → FeatureCollection        │
└────────────┬──────────────────────────┬────────────────────────┘
             │                          │
┌────────────▼──────────┐  ┌────────────▼────────────┐
│  PostgreSQL + PostGIS │  │  Redis (Celery broker)  │
│  analyses table       │  │  + result backend       │
│  trees table          │  └─────────────────────────┘
│  (geometría EPSG:4326)│
└───────────────────────┘
```

---

## Orden de Implementación

### TAREA 1 — Scaffold + Infraestructura Base
**Responsable:** JARVIS
**Tiempo estimado:** 2-3 horas
**Bloquea:** Todo lo demás

Subtareas:
- `docker-compose.yml`: FastAPI + React + PostgreSQL + Redis + pgAdmin
- Scaffold backend: estructura de carpetas, main.py, config, CORS
- Scaffold frontend: Vite + React 18 + TypeScript + shadcn/ui setup
- Migraciones Alembic: tabla `analyses` + tabla `trees` con geometría PostGIS
- Health check endpoints: `GET /health`

Criterio de done:
- `docker-compose up` levanta todos los servicios sin errores
- `GET http://localhost:8000/health` responde 200
- `GET http://localhost:3000` muestra la app React vacía

---

### TAREA 2 — Pipeline de Análisis (Backend Core)
**Responsable:** JARVIS
**Tiempo estimado:** 4-5 horas
**Depende de:** TAREA 1

Subtareas:
- `POST /api/analyses`: upload de GeoTIFF, validación, guardado, encolar Celery task
- `GET /api/analyses/{id}`: polling de estado + progreso
- `GET /api/analyses`: listado con paginación
- Celery task `analyze_ortophoto`:
  - Paso 1 (25%): `load_raster()` con Rasterio — lee GeoTIFF, reproyecta a EPSG:4326
  - Paso 2 (50%): `segment_crowns()` con OpenCV — blur gaussiano + watershed + contornos
  - Paso 3 (75%): `classify_species()` — reglas sobre R/G/B medios + textura (LBP)
  - Paso 4 (100%): `compute_metrics()` — tablas alométricas por especie → biomasa + edad
- `services/allometric.py`: tablas hardcodeadas para 5 especies (eucalipto, pino, quebracho, algarrobo, araucaria)

Criterio de done:
- Subir un GeoTIFF de prueba → task se ejecuta → BD tiene filas en `trees`
- El polling muestra 4 pasos de progreso correctamente

---

### TAREA 3 — Endpoints de Resultados + Exportación (Backend)
**Responsable:** JARVIS
**Tiempo estimado:** 2-3 horas
**Depende de:** TAREA 2

Subtareas:
- `GET /api/analyses/{id}/geojson`: construir FeatureCollection desde PostGIS
- `GET /api/analyses/{id}/summary`: agregar stats por especie, biomasa total, área total
- `GET /api/analyses/{id}/trees/{tree_id}`: detalle individual con color profile
- `GET /api/analyses/{id}/export?format=csv|geojson`: generación y descarga

Criterio de done:
- El GeoJSON tiene polígonos válidos en EPSG:4326
- El summary muestra distribución correcta por especie
- El CSV se descarga con headers correctos

---

### TAREA 4 — Frontend: Mapa + Upload + Panel
**Responsable:** JARVIS
**Tiempo estimado:** 4-5 horas
**Depende de:** TAREA 1 (scaffold), paralelo a TAREA 2-3

Subtareas:
- `UploadPage`: drag & drop de GeoTIFF + barra de progreso (polling cada 2s)
- `DashboardPage`: layout de 2 columnas (mapa izquierda, panel derecha)
- `MapView`: MapLibre GL JS con:
  - Capa raster: ortofoto como ImageSource georreferenciada
  - Capa vector: polígonos de copas con color por especie
  - Click en polígono → muestra panel de detalle del árbol
- `SummaryPanel`: total árboles, biomasa total, tabla de especies con barras de porcentaje
- `TreePanel`: ficha del árbol clickeado (especie, altura, biomasa, edad, confianza)
- Botón "Exportar CSV" y "Exportar GeoJSON"

Criterio de done:
- Subir ortofoto desde UI → ver progreso → ver mapa con árboles → click → ver ficha
- Los datos del panel coinciden con los del API

---

### TAREA 5 — Integración Final + Demo Data
**Responsable:** JARVIS
**Tiempo estimado:** 1-2 horas
**Depende de:** TAREAS 2, 3, 4

Subtareas:
- GeoTIFF de prueba: descargar muestra pública de NEON o generar sintética con Rasterio
- Ajustar parámetros del watershed para que detecte árboles razonablemente en la muestra
- Calibrar reglas de clasificación de especie con colores reales
- README de ejecución en el repo: `docker-compose up` + instrucciones de uso
- Screenshot / video de demo para Tony

Criterio de done:
- Demo funciona end-to-end con el GeoTIFF de prueba
- Tony ve el resultado y da OK o feedback

---

## Dependencias entre Tareas

```
TAREA 1 (scaffold)
    ├── TAREA 2 (pipeline backend)
    │       └── TAREA 3 (endpoints resultados)
    │               └── TAREA 5 (integración + demo)
    └── TAREA 4 (frontend)  ─────────────────────┘
```

TAREA 2 y TAREA 4 son **parcialmente paralelizables** (frontend puede avanzar con mocks mientras el backend no está listo).

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Watershed segmenta mal las copas | Media | Ajustar parámetros: blur kernel, umbral de distancia. Probar con imágenes sintéticas primero. |
| GeoTIFF de prueba no disponible | Baja | Generar ortofoto sintética con Rasterio: círculos verdes = árboles simulados |
| MapLibre no renderiza el raster del GeoTIFF | Media | Convertir ortofoto a tiles COG (Cloud Optimized GeoTIFF) con rio-cogeo, o usar PNG recortado como fallback |
| Celery + Redis no levanta limpio en docker | Baja | Usar flower para debug; fallback a background thread si el tiempo apremia |
| Tablas alométricas no disponibles online | Baja | Usar valores de literatura estándar (FAO 2012) como fallback |

---

## Stack de Dependencias

### Backend (requirements.txt)
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
celery[redis]>=5.3.6
rasterio>=1.3.9
opencv-python-headless>=4.9.0
geopandas>=0.14.3
shapely>=2.0.3
numpy>=1.26.4
pandas>=2.2.1
sqlalchemy>=2.0.29
alembic>=1.13.1
psycopg2-binary>=2.9.9
python-multipart>=0.0.9
pydantic-settings>=2.2.1
```

### Frontend (package.json clave)
```
react 18, vite, typescript
maplibre-gl ^4.x
@shadcn/ui
zustand ^4.x
axios
```

---

## Estructura de Carpetas del Repo

```
forestai-poc/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analyses.py
│   │   │   ├── trees.py
│   │   │   └── export.py
│   │   ├── services/
│   │   │   ├── forest_analyzer.py   ← watershed + clasificación
│   │   │   ├── allometric.py        ← tablas INTA
│   │   │   └── geojson_builder.py   ← FeatureCollection
│   │   ├── tasks/
│   │   │   └── analysis_task.py     ← Celery task
│   │   ├── models/
│   │   │   └── schemas.py           ← Pydantic
│   │   ├── db/
│   │   │   ├── models.py            ← SQLAlchemy
│   │   │   └── migrations/          ← Alembic
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.tsx
│   │   │   ├── TreePanel.tsx
│   │   │   ├── SummaryPanel.tsx
│   │   │   └── UploadDropzone.tsx
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx
│   │   │   └── DashboardPage.tsx
│   │   ├── store/
│   │   │   └── analysisStore.ts     ← Zustand
│   │   ├── api/
│   │   │   └── client.ts            ← axios wrapper
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── brainstorming/                   ← specs + docs
    └── (symlink a ~/brainstorming/2026-05-19-forestai-poc/)
```

---

## Definition of Done (PoC I+D+I)

- [ ] `docker-compose up` levanta todo sin errores manuales
- [ ] Subir GeoTIFF de prueba desde la UI funciona
- [ ] Mapa muestra la ortofoto + polígonos de copas
- [ ] Click en árbol muestra la ficha correcta
- [ ] Panel de resumen muestra totales correctos
- [ ] Exportar CSV descarga un archivo válido
- [ ] Tony vio la demo y dio OK (o feedback concreto)
