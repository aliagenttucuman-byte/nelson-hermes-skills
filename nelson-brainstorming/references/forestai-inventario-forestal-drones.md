# ForestAI — Inventario Forestal con Drones: Conocimiento de Dominio

Generado en sesión 2026-05-19. PoC activa en `~/brainstorming/2026-05-19-forestai-poc/`.

---

## Problema / Hipótesis

Es posible hacer inventario forestal automatizado (conteo por especie, biomasa, edad estimada)
a partir de imágenes de drone usando image analytics clásico (sin ML), combinando:
- OpenDroneMap para fotogrametría (ortofoto + CHM)
- Segmentación OBIA/watershed para delineación de copas
- Reglas de color/textura para clasificación de especie
- Tablas alométricas del INTA para biomasa y edad

---

## Stack Tecnológico Validado (PoC sin ML)

### Pipeline Principal
```
Fotos drone → OpenDroneMap → Ortofoto GeoTIFF + CHM
→ Rasterio/OpenCV (watershed segmentation)
→ Tablas alométricas INTA (biomasa + edad)
→ GeoJSON de inventario
→ MapLibre GL JS (mapa interactivo)
```

### Backend
- FastAPI + Celery + Redis (procesamiento async — ortofotos pueden ser >500MB)
- Rasterio + GDAL — lectura y procesamiento GeoTIFF
- OpenCV — watershed segmentation de copas
- Geopandas + Shapely — geometrías y GeoJSON
- PostgreSQL + PostGIS — almacenamiento espacial

### Frontend
- React 18 + Vite + TypeScript
- **MapLibre GL JS** (no Leaflet — mejor performance con GeoJSON pesado de polígonos)
- shadcn/ui + Zustand

### Por qué no ML en la PoC
El criterio fue: validar el valor del análisis image analytics puro primero, antes de complejizar con entrenamiento. Si la PoC funciona sin ML, el resultado es más explicable y más rápido de buildear en 2 días.

---

## Google Earth Engine — Rol Correcto

GEE NO procesa directamente imágenes de drone propias. Es para imágenes satelitales (Sentinel, Landsat).

**Flujo correcto con drones:**
1. Procesar fotos en OpenDroneMap → ortofoto
2. Subir ortofoto como asset a GEE (si se quiere análisis regional)
3. GEE sirve para: contexto regional, NDVI temporal con Sentinel-2, validación satelital

**GEE no es el punto de entrada — es el ambiente de análisis regional.**

---

## Repositorios GitHub Clave

| Proyecto | URL | Estrellas | Descripción |
|---|---|---|---|
| DeepForest | github.com/weecology/DeepForest | ~700 | Detección de copas con RetinaNet. Modelo preentrenado incluido. |
| detectree2 | github.com/PatBall1/detectree2 | ~250 | Mask R-CNN via Detectron2. Nature Methods 2023. Bosques tropicales. |
| NeonTreeEvaluation | github.com/weecology/NeonTreeEvaluation | ~100 | Benchmark oficial ITC detection. RGB + LiDAR + hiperspectral. |
| lidR | github.com/r-lidar/lidR | ~650 | Estándar industrial LiDAR en R. CHM, biomasa, ITC segmentation. |
| CanopyHeight (Meta) | github.com/facebookresearch/CanopyHeight | ~450 | Altura dosel global con DL. Sentinel-2 + GEDI. Modelo preentrenado. |
| ReforesTree | github.com/gbelouze/reforesTree | ~80 | Conteo árboles en Ecuador con drone RGB. Dataset incluido. |

---

## Datasets Públicos

| Dataset | URL | Descripción |
|---|---|---|
| NEON Tree Crowns | zenodo.org/record/3765872 | 10K+ anotaciones, RGB+LiDAR+hiper, 22 sitios EEUU |
| TreeSatAI | zenodo.org/record/6780578 | 50K patches, 15 especies, Alemania |
| ReforesTree | github.com/gbelouze/reforesTree | Drones RGB, Ecuador, reforestación |
| NEON AOP | data.neonscience.org | 81 sitios EEUU, datos anuales, libre acceso |

---

## Técnicas de Análisis sin ML

### Segmentación OBIA (Object-Based Image Analysis)
- Segmentar por forma + color en lugar de pixel a pixel
- QGIS + Orfeo Toolbox o SAGA para esto
- Python: OpenCV watershed para delineación de copas

### Estimación de Especie por Reglas
- Tono de verde + textura rugosa = especie A
- Copa circular + color claro = especie B
- No es 100% automático, pero con reglas calibradas funciona para PoC
- Si el drone es multiespectral (MicaSense), la clasificación mejora significativamente

### Biomasa sin ML
- Del CHM (Canopy Height Model) se extrae altura de cada árbol
- Altura + especie + tabla alométrica INTA = biomasa estimada
- Tablas alométricas: publicaciones.inta.gob.ar

### Edad de Árboles (la más difícil)
- **No existe modelo DL específico para esto**
- Aproximación: altura de copa + especie + ecuaciones alométricas por región
- Es indirecto pero funciona en la práctica
- Para Argentina: usar tablas INTA por especie nativa/exótica

---

## Decisiones de Arquitectura Tomadas

| Decisión | Razón |
|---|---|
| No incluir OpenDroneMap en PoC | Simplificar: usuario sube ortofoto ya procesada |
| MapLibre sobre Leaflet | Mejor performance con GeoJSON pesado de polígonos de copas |
| Celery + Redis obligatorio | Ortofotos >500MB, no bloquear la UI |
| No ML en PoC | Validar valor del análisis primero, más explicable y más rápido |
| PostGIS para almacenamiento | Datos espaciales nativos — GeoJSON, polígonos, bbox |

---

## Criterio de Éxito PoC (6 puntos)

1. Subir ortofoto GeoTIFF desde frontend → funciona end-to-end
2. Mapa muestra polígonos de copas detectadas encima de la ortofoto
3. Click en árbol → especie estimada, altura, área de copa, biomasa, edad
4. Panel resumen → total árboles, biomasa total, distribución por especie
5. Exportar inventario como CSV o GeoJSON
6. Procesamiento asincrónico → UI no se congela

---

## Papers de Referencia

- Ball et al. 2023 (detectree2) — Nature Methods
- Weinstein et al. 2020 (DeepForest) — Methods Ecol Evol
- Lang et al. 2023 (ETH, canopy height 1m global) — Nature Ecology
- Tolan et al. 2024 (Meta, very high res canopy) — Remote Sensing
- Ahlswede et al. 2023 (TreeSatAI benchmark) — Remote Sensing

---

## Alcance Futuro (post-PoC)

- Integrar OpenDroneMap para procesar fotos crudas de drone
- ML para clasificación de especies (fine-tuning EfficientNet con TreeSatAI)
- Integración Google Earth Engine para contexto regional
- LiDAR support (lidR pipeline)
- Autenticación multi-tenant para múltiples clientes forestales
