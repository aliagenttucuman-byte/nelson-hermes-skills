# ForestAI Pipeline — Tuning & Lecciones (Junio 2026)

## Tile Size — Impacto en Detección

| Tile Size | Tiles (12622×7887) | Árboles NMS | Tiempo CPU |
|-----------|-------------------|-------------|------------|
| 4096px    | ~12               | 173         | ~3 min     |
| 2048px    | ~40               | 624         | ~8 min     |
| 1024px    | ~300 (est)        | ~1000+ est  | ~90 min    |

Recomendación: **2048px** es el balance óptimo — 3.6x más detecciones vs 4096, tiempo manejable en CPU.
Con GPU (RTX 3070+) el tiempo baja a <3 min para cualquier tile size.

Para hacer el cambio:
```python
# backend/app/services/tree_detection.py
TILE_SIZE = 2048  # era 4096
```
Reiniciar celery_worker para aplicar: `docker compose restart celery_worker`

---

## Filtro de Vegetación por ExG (anti-detección urbana)

Problema: con tiles de 2048px se detectan árboles en zonas urbanas (edificios, asfalto).
Solución: calcular ExG antes de cada tile y saltear los que no tienen suficiente vegetación.

```python
VEG_THRESHOLD = 0.12  # 12% mínimo de píxeles verdes

def _tile_has_vegetation(rgb: np.ndarray, threshold: float = VEG_THRESHOLD) -> bool:
    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)
    exg = 2.0 * g - r - b
    veg_pixels = np.sum(exg > 20)  # ExG > 20 = verde significativo
    total_pixels = rgb.shape[0] * rgb.shape[1]
    return (veg_pixels / total_pixels) >= threshold
```

Insertar en el loop de tiling justo después de construir el array RGB, antes de `_apply_exg`.
Ajustar `VEG_THRESHOLD` según densidad del parque: 0.10 más permisivo, 0.20 más estricto.
Los tiles saltados se loguean: `Tile (x,y)+w×h → saltado (sin vegetación)`

Próximo paso posible: Enfoque 2 — ROI manual por polígono dibujado en la UI.

---

## GPU Estimación para 20 min con tiles 1024px

Imagen 17094×11327px, tiles 1024px → ~345 tiles.
- CPU: ~2.5-3 horas
- RTX 3060/3070 (8-12GB VRAM): 10-15x speedup → <20 min ✅
- RTX 3090/A10 (24GB): tiles paralelos → 8-10 min ✅
- A10 en cloud (AWS/GCP): ~$0.75/hora → centavos por imagen

Cuello de botella: SAM necesita VRAM suficiente para tiles grandes. 8GB VRAM alcanza para 1024px.

---

## Pitfall — Docker build no actualiza bundle JS

`docker compose build --no-cache` puede igualmente usar layer cache del COPY
si los timestamps no cambiaron entre builds.

**Solución confiable:**
```bash
cd frontend && npm run build
docker cp dist/. <container>:/usr/share/nginx/html/
docker exec <container> nginx -s reload
```
Verificar que el nuevo bundle esté: `docker exec <container> grep -l 'nuevo_texto' /usr/share/nginx/html/assets/*.js`

---

## Pitfall — nginx 413 con ortomosaicos grandes

Ortomosaicos de drone pesan 60-200MB. El nginx del frontend rechaza con 413 por defecto.

```bash
# En nginx.conf — dentro del bloque server {}
client_max_body_size 500m;
```

Aplicar sin reiniciar contenedor:
```bash
docker cp nginx.conf <container>:/etc/nginx/conf.d/default.conf
docker exec <container> nginx -s reload
# Verificar:
docker exec <container> nginx -T | grep client_max_body
```

---

## Pitfall — HuggingFace HEAD requests al inicio de cada task

Cada task celery hace HEAD requests a HF para verificar cache aunque el modelo esté local.
Agrega ~1-2 segundos de latencia por task. No es fatal pero es ruido en los logs.

Fix futuro: agregar en el docker-compose del celery_worker:
```yaml
environment:
  - TRANSFORMERS_OFFLINE=1
  - HF_DATASETS_OFFLINE=1
```

---

## Demo ReforestLatam — Ruta /demo

Patrón para demo limpia sin exponer stack interno (compliance pendiente con ReforestLatam).

### Estructura
- Nueva ruta `/demo` — componente independiente `frontend/src/pages/DemoReforestLatam.tsx`
- NO modificar `App.tsx` — routing por `window.location.pathname` en `main.tsx`
- nginx: agregar `location /demo { try_files $uri $uri/ /index.html; }`

### Qué NO mostrar en demo
- Nombres de modelos: DeepForest, SAM, VLM, claude-haiku
- Scores internos de SAM, stability_score
- Filtros, paneles laterales, solapas de la app principal
- Textos durante el loading (solo spinner)

### Qué SÍ mostrar
- Upload drag & drop centrado
- Spinner doble con 🌲 y "Procesando..."
- Stats: árboles detectados / confianza promedio / copas segmentadas
- Canvas con polígonos SAM (verde translúcido, amarillo para seleccionado)
- Tabla de especies al costado: scrolleable, sticky header, filtrada (sin "dudoso")
- Interactividad bidireccional: hover tooltip en canvas ↔ click en tabla resalta copa

### Canvas interactivo — componente PolygonCanvas
- Hit-test por point-in-polygon para hover y click
- Tooltip flotante con: especie, salud, confianza, SAM score
- Seleccionado: fill amarillo + label con nombre de especie encima
- Hover: fill verde intenso
- Normal: fill verde translúcido

### Tabla especies
- Filtrar vlm_species !== null && !== "dudoso"
- Click en fila → setSelectedIdx(globalIdx) → canvas resalta copa
- Click en copa → scroll a fila correspondiente
- Indicador ▶ en fila seleccionada
