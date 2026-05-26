# ForestAI — Vista 3D con Three.js + Zustand

Patrón implementado para conectar la detección real (DeepForest/SAM/VLM) con
la visualización 3D interactiva del bosque. Proyecto: `~/proyectos/forestai-poc/`.

## Dependencias frontend

```bash
npm install three @react-three/fiber @react-three/drei
```

## Flujo de datos

```
TreeDetectionPanel (detección)
  → dispatchTo3D(result)
  → useForestStore.setDetectedTrees(trees3D, w, h)   ← store Zustand compartido
  ← Forest3DView (3D) lee useForestStore.detectedTrees
```

## Store Zustand — campos a agregar

```typescript
// store/useForestStore.ts
export interface DetectedTree {
  id: string; x: number; y: number;
  crown_diameter: number; health_status: string;
  species?: string; score?: number;
  vlm_health?: string | null; vlm_species?: string | null;
}

// Dentro de ForestStore:
detectedTrees: DetectedTree[];
imageWidth: number; imageHeight: number;
setDetectedTrees: (trees: DetectedTree[], w: number, h: number) => void;
clearDetectedTrees: () => void;

// Implementación:
detectedTrees: [],
imageWidth: 0, imageHeight: 0,
setDetectedTrees: (trees, w, h) => set({ detectedTrees: trees, imageWidth: w, imageHeight: h }),
clearDetectedTrees: () => set({ detectedTrees: [], imageWidth: 0, imageHeight: 0 }),
```

## Conversión DetectionResult → DetectedTree[]

```typescript
// En TreeDetectionPanel.tsx — llamar después de cada setResult(data)
const setDetectedTrees = useForestStore((s) => s.setDetectedTrees);

const dispatchTo3D = (r: DetectionResult) => {
  const scale = 60 / Math.max(r.image_width, r.image_height); // normaliza a 60m
  const trees3D = r.trees.map((t, i) => {
    const cx = ((t.xmin + t.xmax) / 2) * scale;
    const cy = ((t.ymin + t.ymax) / 2) * scale;
    const crownPx = Math.max(t.xmax - t.xmin, t.ymax - t.ymin);
    const vlm = t.vlm_health?.toLowerCase() ?? "";
    const health =
      vlm.includes("sano") || vlm.includes("healthy") ? "sano" :
      vlm.includes("estres") || vlm.includes("stress") ? "estresado" :
      vlm.includes("muerto") || vlm.includes("dead") ? "muerto" :
      "unknown";
    return {
      id: `ARB-${String(i + 1).padStart(3, "0")}`,
      x: cx, y: cy,
      crown_diameter: Math.max(0.5, crownPx * scale),
      health_status: health,
      species: t.vlm_species ?? undefined,
      score: t.score,
      vlm_health: t.vlm_health,
    };
  });
  setDetectedTrees(trees3D, r.image_width, r.image_height);
};

// Llamar en AMBOS lugares:
// runSample: const data = await res.json(); setResult(data); dispatchTo3D(data);
// runUpload: const data = await res.json(); setResult(data); dispatchTo3D(data);
```

## Forest3DView — estructura del componente

```typescript
export default function Forest3DView() {
  const detectedTrees = useForestStore((s) => s.detectedTrees)
  const hasTrees = detectedTrees.length > 0

  // Si !hasTrees → mensaje de guía, NO datos mock
  // Si hasTrees  → árboles reales con colores por health_status
  ...
  return (
    <Canvas camera={{ position: [30, 35, 60], fov: 50 }} shadows>
      <Sky ... /><Stars ... />
      {hasTrees && <Terrain size={60} />}
      {filtered.map(tree => <Tree key={tree.id} tree={tree} ... />)}
      <OrbitControls maxPolarAngle={Math.PI / 2.1} />
    </Canvas>
  )
}
```

## Colores por estado sanitario

```typescript
const HEALTH_COLORS = {
  sano: '#22c55e',      // verde
  estresado: '#eab308', // amarillo
  muerto: '#ef4444',    // rojo
  unknown: '#94a3b8',   // gris
}
```

## Patrón de tab en App.tsx

```typescript
// 1. Agregar al array TABS:
{ key: "3d", icon: "🔮", label: "Vista 3D" }

// 2. Extender ViewType:
type ViewType = "grid" | "map" | "geo" | "trees" | "3d"

// 3. Render — IMPORTANTE: necesita fallback explícito al final
} : view === "trees" ? (
  <TreeDetectionPanel />
) : view === "3d" ? (
  <Forest3DView />
) : (
  <TreeDetectionPanel />   // fallback — nunca omitir
)}
```

## Deploy / Tunnel — Pitfalls Críticos

- **El docker frontend tiene su propio `dist/`.** El proyecto usa `docker compose` con un contenedor nginx que sirve la build compilada en imagen. Si reconstruís el frontend localmente, el docker NO se actualiza automáticamente. Para actualizar sin rebuil docker completo:
  ```bash
  # Copiar JS nuevo y index.html al contenedor nginx
  docker cp frontend/dist/assets/index-XYZ.js forestai-poc-frontend-1:/usr/share/nginx/html/assets/
  docker cp frontend/dist/index.html forestai-poc-frontend-1:/usr/share/nginx/html/
  ```
  Verificar: `curl -s http://localhost:3010 | grep "src="` debe mostrar el hash nuevo.

- **Tunnel debe apuntar al puerto del docker nginx (3010), NO a un `npx serve` estático.** El nginx del docker proxea `/api` al backend. Si apuntás el tunnel a un servidor estático (`npx serve dist`), las llamadas a `/api/analyses`, `/api/tree-detection/run`, etc. fallan y las ortofotos no cargan. Verificar que el nginx tenga el bloque `location /api { proxy_pass http://backend:8000/api; }`.

- **Limpiar dist antes de rebuild.** Si hacés `npm run build` sin borrar `dist/` primero, Vite genera un JS nuevo (`index-XYZ.js`) pero el `index.html` viejo puede quedar cacheado en el proceso `serve` anterior. Siempre: `rm -rf dist && npm run build`.
- **Puerto ocupado por proceso viejo.** Si `curl http://localhost:3010` devuelve el HTML con el hash JS viejo aunque mataste el proceso, hay otro servidor (del proyecto anterior) en ese puerto. Usá `fuser -k 3010/tcp` para matarlo, o directamente cambiar a un puerto nuevo (`3012`, `3013`, etc.) y actualizar el tunnel.
- **`npx serve dist` vs `npx serve /ruta/absoluta/dist`.** Cuando se lanza desde un directorio diferente al del proyecto, `serve dist` sirve el `dist/` relativo al CWD, no el del proyecto. Usar siempre ruta absoluta: `npx serve /home/server/proyectos/forestai-poc/frontend/dist -p 3012`.
- **El tunnel de cloudflared no requiere reinicio** si solo cambiás el contenido del directorio — pero sí si cambiás el puerto. Matá el tunnel anterior y levantá uno nuevo si cambiás puerto.
- **Proyecto canónico: `~/proyectos/forestai-poc/`** — el spike `forestai-3d` está descartado. No confundir puertos: forestai-poc usa `:3010`/`:3012`, backend `:8000`.

## Pitfalls

- **No usar datos mock en producción.** Si el store está vacío, mostrar mensaje "Ejecutá una detección primero". Nunca árboles inventados.
- **`Math.max(0.5, crownPx * scale)`** — evita esferas invisibles para copas muy pequeñas en imágenes de alta resolución.
- **`<Html>` de drei para overlays dentro del canvas** — los overlays de React DOM (tooltips, labels) dentro del `<Canvas>` requieren `<Html>` de `@react-three/drei`, no `<div>` directos.
- **Zustand funciona dentro del canvas** — `useForestStore` es accesible desde componentes Three.js (dentro de `<Canvas>`), no hay restricción.
- **`maxPolarAngle={Math.PI / 2.1}`** — impide que la cámara vaya por debajo del terreno.
- **El proyecto original es `forestai-poc`** — no mezclar con `forestai-3d` (spike descartado). Todo el desarrollo va en `~/proyectos/forestai-poc/`.
