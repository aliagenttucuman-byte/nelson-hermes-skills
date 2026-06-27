# Demo ReforestLatam — /demo route (2026-06-09)

## URL y acceso

- URL: `http://[host]:3010/demo`
- Archivo: `frontend/src/pages/DemoReforestLatam.tsx`
- Routing en `main.tsx`: `window.location.pathname.startsWith('/demo')` → DemoReforestLatam
- nginx.conf: `location /demo { try_files $uri $uri/ /index.html; }`

## Arquitectura — componente completamente autónomo

`DemoReforestLatam.tsx` es independiente de `TreeDetectionPanel`. Contiene su propio:
- Lógica de upload + polling
- `PolygonCanvas` con hover/selección
- `Tooltip` flotante
- Tabla de especies
- Spinner de loading

**Razón:** cambios en TreeDetectionPanel no rompen la demo. La demo es para stakeholders externos y necesita estabilidad total.

## Reglas de contenido — compliance ReforestLatam

Nelson exige que la demo NO revele los modelos internos (compliance + acuerdos pendientes con ReforestLatam).

NO mostrar en la UI `/demo`:
- "DeepForest", "SAM", "RetinaNet", "VLM", "claude-haiku"
- Pasos del pipeline durante el loading
- Filtros de confianza
- Columna izquierda del TreeDetectionPanel
- Header interno con "DeepForest + SAM · Detección y segmentación de copas"

SÍ mostrar:
- Header limpio: "ForestAI — Detección de Árboles"
- Upload drag & drop
- Spinner doble (🌲) + "Procesando..."
- Stats: árboles detectados, confianza promedio, copas segmentadas
- Canvas con polígonos SAM interactivo
- Tabla de clasificación de especies (sin mencionar VLM)

## Canvas interactivo — hover + selección bidireccional tabla↔canvas

```tsx
// Props del PolygonCanvas en la demo
<PolygonCanvas
  result={result}
  selectedIdx={selectedIdx}           // índice global en result.trees
  onHover={(idx, x, y) => setTooltip(...)}  // tooltip flotante
  onSelect={setSelectedIdx}           // click en copa
/>
```

### Comportamientos:
- **Hover** → tooltip flotante `position: fixed` en `clientX+14, clientY-10` con especie/salud/score
- **Click copa** → se resalta en amarillo (#fefce8) con label encima, o deselecciona si ya estaba
- **Click fila tabla** → `setSelectedIdx(globalIdx)` + `rowRefs[rowIdx].scrollIntoView()`
- **Canvas → tabla**: no hay scroll automático del canvas a la tabla (tabla es lateral)

### Hit-test (ray-casting para polígonos SAM):
```tsx
const pointInPoly = (poly, px, py, sx, sy) => {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i][0]*sx, yi = poly[i][1]*sy;
    const xj = poly[j][0]*sx, yj = poly[j][1]*sy;
    if (yi > py !== yj > py && px < ((xj-xi)*(py-yi))/(yj-yi)+xi) inside = !inside;
  }
  return inside;
};
// Fallback a bbox si no hay polígono SAM
```

### Colores:
- Normal: fill `rgba(16,185,129,0.15)` stroke `rgba(5,150,105,0.8)`
- Hover: fill `rgba(16,185,129,0.4)` stroke `rgba(16,185,129,1)` lw=2.5
- Seleccionado: fill `rgba(251,191,36,0.35)` stroke `rgba(245,158,11,1)` lw=2.5

## Tabla de especies

Filtra árboles con `vlm_species !== "dudoso" && vlm_species != null`.
Muestra: Especie | Salud (badge de color).
Salud colors: saludable=#059669, estresado=#d97706, resto=#dc2626.
Sticky header, scroll vertical, maxHeight 520px.

## PITFALL — Docker build cachea el JS viejo

`docker compose build --no-cache frontend` puede igualmente servir bundle viejo.

Fix confiable — build en host y copiar dist:
```bash
cd /home/server/proyectos/forestai-poc/frontend && npm run build
grep -l "ReforestLatam" dist/assets/*.js  # verificar que está
docker cp dist/. forestai-poc-frontend-1:/usr/share/nginx/html/
docker exec forestai-poc-frontend-1 nginx -s reload
```

## PITFALL — nginx 413 al subir TIFFs grandes

TIFFs de ~60MB superan el límite por defecto de nginx (1MB).

Fix en `frontend/nginx.conf`:
```nginx
server {
    client_max_body_size 500m;
    ...
    location /api {
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        client_max_body_size 500m;
    }
}
```

Aplicar sin reiniciar:
```bash
docker cp frontend/nginx.conf forestai-poc-frontend-1:/etc/nginx/conf.d/default.conf
docker exec forestai-poc-frontend-1 nginx -s reload
# Verificar:
docker exec forestai-poc-frontend-1 nginx -T 2>&1 | grep client_max_body
```

## Resultados verificados sesión 2026-06-09

| Imagen | Dimensiones | Tiles | Árboles | SAM | VLM | Tiempo |
|--------|-------------|-------|---------|-----|-----|--------|
| 9deJulio.rgb.tif | 17094×11327px (193Mpx) | 15 tiles 4096px | 257 | ✅ 257 copas | ✅ 30/257 | ~7 min |
| Avellaneda.rgb.tif | 12622×7887px (99Mpx) | 12 tiles 4096px | 173 | ✅ 173 copas | ✅ 30/173 | ~3 min |

Nota: algunos árboles clasificados como "dudoso" (vlm_confidence=0.0, "no visible tree canopy detected") — el VLM ve crops sin copa clara (bordes de imagen o sombras). La demo filtra estos de la tabla.
