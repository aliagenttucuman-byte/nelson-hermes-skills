# Three.js — Puntos de Extensión en ForestAI

## Estado actual

Three.js ya está enchufado en la solapa **Vista 3D** (`Forest3DView.tsx`) usando `@react-three/fiber` + `@react-three/drei`.
Recibe `detectionResult` de TreeDetectionPanel y renderiza árboles 3D con salud coloreada (VLM → DeepForest fallback).

## Extensiones identificadas (ordenadas por impacto demo)

### 1. Modo vuelo automático (más rápido de implementar)
En `Forest3DView.tsx`, agregar un modo "showcase" con cámara animada que recorre el bosque.
Solo requiere un `useFrame` hook con keyframes circulares + botón toggle.

```tsx
// Dentro de la escena Three.js
useFrame(({ camera, clock }) => {
  if (!autoFly) return;
  const t = clock.getElapsedTime() * 0.3;
  camera.position.set(Math.sin(t) * 30, 15, Math.cos(t) * 30);
  camera.lookAt(0, 0, 0);
});
```

### 2. Terreno 3D desde NDVI Sentinel (más impresionante visualmente)
En `GeoPanel.tsx` / `SentinelTab`, agregar un canvas Three.js que genera un plano con displacement map desde la imagen NDVI.
- Fetch de `/api/geo/sentinel/preview?layer=NDVI` → usar como textura de desplazamiento
- `PlaneGeometry` con segmentos altos + `displacementMap`
- Color verde = vegetación alta, marrón = baja

### 3. Distribución espacial en tiempo real (Trees panel)
En `TreeDetectionPanel.tsx`, mientras corre la detección, mostrar un mini canvas Three.js lateral con puntos 3D que aparecen a medida que se detectan árboles.
- Requiere streaming del endpoint de detección (SSE o polling)
- Puntos coloreados por salud VLM

### 4. Extrusión de polígonos SAM en sidebar de ortofoto
En `DetailSidebar.tsx`, al abrir el detalle de un análisis completado, renderizar los polígonos SAM como extrusiones 3D sobre la imagen.
- Requiere que el backend devuelva polígonos en el response de análisis

### 5. Capa 3D georreferenciada sobre Leaflet (Mapa)
En `MapPanel.tsx`, superponer árboles detectados como puntos 3D posicionados según coordenadas GPS reales.
- Requiere conversión lat/lon → coordenadas Three.js
- Complejidad media-alta por sincronización de proyecciones

## Stack Three.js instalado
```json
"@react-three/fiber": "^8.x",
"@react-three/drei": "^9.x",
"three": "^0.x"
```

## Archivos clave
- `frontend/src/components/Forest3DView.tsx` — escena principal (415 líneas)
- `frontend/src/components/TreeDetectionPanel.tsx` — origen del `detectionResult`
- `frontend/src/App.tsx` línea 665 — montaje de la vista 3D
