# YOLOv PoC — UI para reuniones presenciales con cliente

> Referencia para sesiones donde Nelson avisa "hoy nos juntamos con la gente para mostrarles" o equivalente, y pide rediseño rápido del frontend `yolov-orientacion-poc` antes de la demo. Nelson típicamente avisa con poca anticipación.

## Brief de Nelson — "estilo serio para impresionar"

Cuando Nelson dice "buena UI", "estilo serio", "para impresionar" — apuntar a estética estilo Linear / Vercel / Stripe, NO a demo de hackathon:

- Background con gradient radial sobrio (verde oscuro corporativo → negro azulado), NO flat color
- Hero centrado con título grande (clamp 2-3.25rem), font-weight 800, letterSpacing tight (-0.025em)
- Tipografía Inter (no system-ui pelado) — importarla en el HTML o via CDN si no está
- Branding ForestAI con logo gradient + indicador "Modelo activo" pulsante en navbar
- Stats cards arriba del hero con números reales del PoC: ~275 árboles, 85% precisión, 4 modelos, <3 min inferencia
- Todo centrado horizontalmente, max-width 760-1100px según sección
- Glassmorphism sutil: `background: rgba(15, 23, 42, 0.5); backdrop-filter: blur(8px); border: 1px solid rgba(51, 65, 85, 0.5)`
- Spinner premium con árbol 🌲 en el centro durante procesamiento — no spinner pelado
- Verdes: usar `#16a34a → #15803d → #4ade80 → #86efac` (escala forestal corporativa, NO verde fluo)
- Footer con copyright AlegentAI + año actual

## Path del frontend a editar

`/home/server/proyectos/yolov-orientacion-poc/frontend/src/App.tsx`

Es el archivo único de layout principal. NO tocar componentes hijos (DropZone, ModelSelector, ResultsPanel, TileViewer, ComparePanel, SpeciesPanel) — están bien.

## Workflow de deploy del rediseño

```bash
# 1. Editar App.tsx (o el componente correspondiente)
# 2. Rebuild + restart frontend
cd /home/server/proyectos/yolov-orientacion-poc
docker compose up -d --build frontend nginx

# 3. ALWAYS restart nginx — sin esto pega 502 (pitfall conocido)
sleep 4
docker restart yolov-orientacion-poc-nginx-1

# 4. Verificar
sleep 4
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:9020  # debe dar 200
```

## URL para mostrar

`http://100.110.8.13:9020` (Tailscale, no requiere internet en la reunión)

## Stats reales del modelo (usar en hero cards)

Estos números salen del README del repo + sesiones de fine-tuning:

| Stat | Valor | Fuente |
|------|-------|--------|
| Árboles típicos por ortofoto | ~275 | Ortofoto 9 de Julio fine-tuned |
| Precisión mAP50 | 85% | yolo11n_forestai_v2.pt |
| Modelos comparables | 4 | yolo11n_forestai + yolo11n + yolov8n + exg |
| Tiempo de inferencia | <3 min | CPU, ortofoto típica drone |

## Cliente esperado en estas reuniones

ReForest Latam (CEO Damián Rivadeneira) + Gino + Pablo (COO AlegentAI).
Gap declarado por el cliente: detección de árboles con YOLO sobre drones.
Mostrar el PoC + opciones comerciales (25% equity o USD 20-57K) si pregunta Pablo.

## Compliance — qué NO revelar en la UI

- Modelos internos como nombres técnicos crudos (`yolo26n_especies_noa_v1.pt`) — usar nombres operativos ("Detector NOA", "Clasificador de especies")
- Stack interno (FastAPI, Docker) — el cliente no necesita verlo
- Logs / endpoints técnicos visibles en la UI

## Pitfall — Nelson avisa con poca anticipación

Cuando Nelson tipea "hoy nos juntamos... dame una buena UI", quedan típicamente 30-60 minutos antes de la demo. Estrategia:

1. NO pedir specs detallados — interpretar "serio + centrado + impresionar" como brief completo
2. NO proponer alternativas — entregar una versión directa
3. NO tocar componentes hijos — solo App.tsx para minimizar riesgo de romper
4. ALWAYS hacer el `docker restart nginx` después del build — sino llega a la reunión con 502
5. Mandar la URL final clara al toque — Nelson la copia y abre en su laptop para la demo
