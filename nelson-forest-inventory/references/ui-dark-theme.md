# ForestAI UI — Dark Theme Design System

## Paleta de colores

```css
/* index.css */
@import "tailwindcss";

@theme {
  --color-forest-400: #4ade80;
  --color-forest-500: #22c55e;
  --color-forest-600: #16a34a;
  --color-surface-900: #0a0f0d;   /* fondo principal */
  --color-surface-800: #0f1710;   /* sidebar / cards */
  --color-surface-700: #162018;   /* cards internas */
  --color-surface-600: #1e2d22;   /* borders, hover */
  --color-surface-500: #2a3d2e;   /* scrollbar thumb */
}
```

## Colores por especie (MapLibre markers)

```ts
const SPECIES_COLORS: Record<string, string> = {
  eucalipto:   "#4ade80",   // verde claro
  pino:        "#86efac",   // verde pálido
  quebracho:   "#f59e0b",   // ámbar
  algarrobo:   "#a78bfa",   // violeta
  araucaria:   "#38bdf8",   // celeste
  desconocida: "#94a3b8",   // gris
};
```

## Estructura de layout (App.tsx)

```
header (h-14, bg #0a0f0d, border-b #1e2d22)
  logo + badges + UploadPanel button

main (flex, overflow-hidden)
  sidebar (w-72, shrink-0)
    SidePanel     ← lista de análisis con status dots
    StatsPanel    ← KPIs + distribución especies + export buttons

  MapPanel (flex-1)
    maplibre-gl
    overlay: sin análisis / loading spinner
    badge: total árboles (top-left)
    leyenda especies (bottom-left)
```

## Status dots en SidePanel

```ts
const statusConfig = {
  pending:    { dot: "bg-yellow-400 forest-pulse", text: "text-yellow-400" },
  processing: { dot: "bg-blue-400 forest-pulse",   text: "text-blue-400"   },
  completed:  { dot: "bg-green-400",               text: "text-green-400"  },
  failed:     { dot: "bg-red-400",                 text: "text-red-400"    },
};
```

Animación CSS para `forest-pulse`:
```css
@keyframes forestPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.forest-pulse { animation: forestPulse 2s cubic-bezier(0.4,0,0.6,1) infinite; }
```

## Markers MapLibre (custom DOM elements)

No usar el Marker default — crear `div` custom por especie:

```ts
const el = document.createElement("div");
el.style.cssText = `
  width:${size}px; height:${size}px;
  border-radius:50%;
  background:${color}33;        /* color + 20% opacity */
  border:2px solid ${color};
  box-shadow: 0 0 8px ${color}66;
  cursor:pointer;
  transition:all 0.15s ease;
`;
el.onmouseenter = () => { el.style.transform = "scale(1.4)"; };
el.onmouseleave = () => { el.style.transform = "scale(1)"; };
```

Tamaño del marker proporcional al área de copa:
```ts
const size = Math.max(12, Math.min(28, (tree.crown_area_m2 || 4) * 3));
```

## Popup MapLibre (dark theme)

```ts
const popup = new maplibregl.Popup({ offset: 15, closeButton: false })
  .setHTML(`
    <div style="background:#0f1710;color:#e2e8f0;padding:10px 12px;
                border-radius:8px;border:1px solid #2a3d2e;
                min-width:160px;font-family:Inter,sans-serif">
      <div style="font-weight:700;color:${color};font-size:13px">${tree.tree_id}</div>
      <!-- datos del árbol -->
    </div>
  `);
```

## Pitfalls UI

- **MapLibre inicialización en React:** Usar `useRef` para el container y otro `useRef` para la instancia del mapa. Verificar `if (!mapRef.current || mapInstance.current) return` en el `useEffect` de inicialización para evitar doble-mount con React StrictMode.
- **Limpiar markers al cambiar análisis:** Guardar markers en `useRef<maplibregl.Marker[]>` y llamar `.remove()` en cada uno antes de plotear los nuevos.
- **`fitBounds` con un solo árbol:** Agregar padding mínimo (0.001 grados) a los bounds para que el zoom no quede extremo. `maxZoom: 18` evita que los tiles satelitales se pixelen.
- **OSM como basemap (sin API key):** Usar tiles OSM estándar para desarrollo. Para producción considerar MapTiler o Stadia (gratuitos con key, mejor calidad satelital).
