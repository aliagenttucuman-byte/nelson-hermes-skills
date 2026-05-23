# ForestAI PoC — Inventario Forestal con Drones e Image Analytics

**Fecha:** 2026-05-19
**Equipo:** Tony (líder) + JARVIS
**Tipo:** PoC I+D+I — flujo de 3 fases (Especificar → Planear → Implementar)
**Estado:** ESPECIFICANDO

---

## ¿Qué queremos probar?

**Hipótesis:** Es posible construir un sistema web funcional que, a partir de una ortofoto de drone (imagen aérea georreferenciada), realice de forma automática:
- Detección y conteo de árboles individuales por segmentación de copa
- Clasificación por especie (basada en reglas de color/textura, sin ML)
- Estimación de biomasa usando ecuaciones alométricas del INTA
- Estimación de edad aproximada por altura de copa + especie

Todo esto expuesto en una interfaz web interactiva con mapa, sin requerir machine learning ni licencias pagas.

---

## Stack Tecnológico

### Backend (Python / FastAPI)
- **FastAPI** — API REST + WebSocket para progreso
- **Rasterio + GDAL** — lectura y procesamiento de GeoTIFF
- **OpenCV** — segmentación watershed de copas
- **Geopandas + Shapely** — manejo de geometrías y GeoJSON
- **Celery + Redis** — procesamiento asincrónico de imágenes pesadas
- **Pandas** — cálculo de métricas e inventario final

### Frontend (React / Vite)
- **React 18 + Vite + TypeScript**
- **MapLibre GL JS** — mapa interactivo con capas GeoJSON
- **shadcn/ui** — panel de métricas y controles
- **Zustand** — estado global

### Herramientas de Análisis (sin ML)
- **OBIA (Object-Based Image Analysis)** — segmentación por forma y color
- **Watershed** — delineación de copas individuales
- **Índices de vegetación** — NDVI si el drone es multiespectral; análisis RGB si no
- **Tablas alométricas INTA** — biomasa y edad por especie y altura

### Infraestructura
- Docker + docker-compose
- PostgreSQL + PostGIS (datos espaciales del inventario)

---

## Criterio de Éxito

La PoC es exitosa si:

1. **Subir una ortofoto** (GeoTIFF) desde el frontend funciona end-to-end
2. **El mapa muestra los polígonos** de copas detectadas encima de la ortofoto
3. **Click en un árbol** muestra: especie estimada, altura, área de copa, biomasa estimada, edad estimada
4. **Panel de resumen** muestra: total de árboles, biomasa total, distribución por especie
5. **Exportar inventario** como CSV o GeoJSON funciona
6. **El procesamiento es asincrónico** (la UI no se congela mientras procesa)

---

## Alcance MVP (PoC, no producción)

### INCLUYE
- Upload de ortofoto GeoTIFF ya procesada (no incluye fotogrametría ODM en esta PoC)
- Segmentación de copas por watershed (OpenCV)
- Clasificación por reglas simples de color RGB (verde claro, verde oscuro, tonos)
- Tablas alométricas de 3 a 5 especies típicas argentinas (eucalipto, pino, quebracho, algarrobo, araucaria)
- Mapa interactivo con capas: ortofoto + polígonos de copas
- Inventario exportable

### EXCLUYE (para versión futura)
- Procesamiento de fotos crudas del drone (fotogrametría OpenDroneMap)
- Machine learning para clasificación de especies
- Integración con Google Earth Engine
- LiDAR (solo RGB en esta PoC)
- Autenticación de usuarios
- Multi-tenant

---

## Fuentes y Referencias

- DeepForest: github.com/weecology/DeepForest (referencia, no se usa en PoC)
- detectree2: github.com/PatBall1/detectree2 (referencia, no se usa en PoC)
- lidR: github.com/r-lidar/lidR (referencia R, no se usa en PoC)
- Tablas alométricas INTA: publicaciones.inta.gob.ar
- NEON Tree Crown Dataset: zenodo.org/record/3765872 (para validación futura)
- OpenDroneMap: opendronemap.org (integración futura)

---

## Estructura del Proyecto

```
forestai-poc/
├── backend/          # FastAPI + procesamiento
│   ├── app/
│   │   ├── api/      # Endpoints REST
│   │   ├── services/ # Lógica de negocio (segmentación, alométricas)
│   │   ├── models/   # Schemas Pydantic
│   │   └── tasks/    # Celery tasks
│   └── Dockerfile
├── frontend/         # React + MapLibre
│   ├── src/
│   │   ├── components/  # Map, TreePanel, Summary
│   │   ├── pages/       # Upload, Dashboard
│   │   └── store/       # Zustand
│   └── Dockerfile
├── docker-compose.yml
└── docs/
    ├── openapi.yaml
    └── user-stories.md
```

---

## Historial de Decisiones

| Fecha | Decisión | Razón |
|---|---|---|
| 2026-05-19 | No usar ML en PoC | Validar valor del análisis image analytics puro primero |
| 2026-05-19 | No integrar ODM en PoC | Simplificar: el usuario sube ortofoto ya procesada |
| 2026-05-19 | MapLibre en vez de Leaflet | Mejor performance con GeoJSON pesado de polígonos |
| 2026-05-19 | Tablas alométricas INTA | Referencia oficial argentina, aplica a especies nativas |
| 2026-05-19 | Celery + Redis para procesamiento | Las ortofotos pueden ser >500MB, no bloquear la UI |

---

## Notas

- Esta PoC usa el **flujo I+D+I simplificado** (3 fases, 2 días máximo)
- Si funciona y Tony da OK → el equipo Central la rebuild desde cero con flujo SDD completo
- Archivado en: `~/brainstorming/2026-05-19-forestai-poc/`
