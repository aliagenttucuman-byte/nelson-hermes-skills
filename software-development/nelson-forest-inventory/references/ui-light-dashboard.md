# ForestAI UI v2 — Light Dashboard Design System

> El dark theme fue rechazado por Nelson. Esta referencia documenta la UI aprobada.

## Paleta de colores (Tailwind / claro)

```
Fondo general:      bg-slate-50
Cards:              bg-white, border border-slate-200
Sidebar / aside:    bg-white, border-r border-slate-200
Header:             bg-white, border-b border-slate-200, sticky
Acento primario:    emerald-500 / emerald-600
Acento texto:       text-emerald-600
Acento tenue:       bg-emerald-50, bg-emerald-100
```

## Estructura de layout

```
header (sticky, z-40, bg-white)
  logo + tabs (Grid/Mapa) + stats rápidas (total ortofotos, total árboles)

VISTA GRID (default):
  main (flex)
    columna principal (flex-1, overflow-y-auto, p-6)
      UploadZone (drag & drop prominente, rounded-2xl, border-dashed)
      h2 "Ortofotos cargadas"
      grid grid-cols-2 lg:grid-cols-3 gap-4
        AnalysisCard × N   ← thumbnail + nombre + fecha + status + árbol count

    aside detalle (w-80, border-l, cuando hay seleccionado)
      thumbnail grande (aspect-video)
      metadata: nombre, archivo, estado
      StatsPanel (KPIs + especies + exports)
      botón "Ver en mapa"

VISTA MAPA:
  main (flex)
    mini sidebar (w-64) ← lista filtrada solo "completed", con árbol count
    MapPanel (flex-1)   ← igual que v1
```

## AnalysisCard

```tsx
// card con thumbnail real del GeoTIFF
<div className="w-full aspect-video mb-3 rounded-lg overflow-hidden bg-slate-100">
  <img src={`${API}/api/analyses/${id}/thumbnail`} onError={() => setError(true)} />
</div>
<StatusBadge status={a.status} />
// borde emerald-500 al seleccionar: border-2 border-emerald-500 shadow-lg shadow-emerald-100
```

## StatusBadge (colores claros)

```ts
const STATUS = {
  pending:    { label: "En cola",    cls: "bg-amber-100 text-amber-700 border-amber-200" },
  processing: { label: "Analizando", cls: "bg-blue-100 text-blue-700 border-blue-200" },
  completed:  { label: "Listo",      cls: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  failed:     { label: "Error",      cls: "bg-red-100 text-red-700 border-red-200" },
};
```

## UploadZone (label con drag & drop)

```tsx
<label
  className="flex flex-col items-center justify-center gap-3 w-full
             rounded-2xl border-2 border-dashed cursor-pointer transition-all
             border-slate-200 bg-slate-50 hover:border-emerald-300 hover:bg-emerald-50/50
             py-10"
  onDragOver/onDrop/...
>
  <input type="file" accept=".tif,.tiff" className="hidden" />
  <div className="w-14 h-14 rounded-2xl bg-emerald-100 text-2xl">🛰️</div>
  <p>Arrastrá tu ortofoto aquí</p>
  <p className="text-xs text-slate-400">o hacé clic · GeoTIFF (.tif)</p>
</label>
```

## StatsPanel adaptado a fondo claro

```tsx
// Cards de métricas con bg-slate-50 en vez de #162018
<div className="rounded-xl p-3 bg-slate-50 border border-slate-100">
  <p className="text-xl font-bold text-slate-800">...</p>
</div>

// Barra de especie con bg-slate-200 como base
<div className="h-1.5 rounded-full bg-slate-200">
  <div className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-green-400" />
</div>

// Export: usar <a> en vez de <button> para evitar preventDefault al descargar
<a href={...} target="_blank" className="border border-slate-200 text-slate-600 hover:bg-slate-50" />
```

## Endpoint thumbnail backend

```python
@router.get("/{analysis_id}/thumbnail")
def get_thumbnail(analysis_id: str, db: Session = Depends(get_db)):
    # Rasterio: leer a max 512px con out_shape
    scale = min(512 / src.width, 512 / src.height, 1.0)
    # Normalizar con percentil 2-98 para stretch de contraste
    p2, p98 = np.percentile(img_arr[img_arr > 0], (2, 98))
    img_arr = np.clip((img_arr - p2) / max(p98 - p2, 1) * 255, 0, 255).astype(np.uint8)
    # Devolver PNG con cache
    return StreamingResponse(buf, media_type="image/png",
                             headers={"Cache-Control": "public, max-age=3600"})
```

⚠️ Poner este endpoint ANTES de `/{analysis_id}/summary` en el router — de lo contrario FastAPI interpreta la palabra "thumbnail" como un analysis_id y lo enruta incorrectamente.

## ⚠️ Bugs encontrados en segunda iteración y soluciones

### 1. index.css pisaba el fondo con negro
El `index.css` tenía `body { background-color: #0a0f0d; }` del dark theme anterior.
Las clases `bg-slate-50` del nuevo diseño no tienen suficiente especificidad para pisarlo.
**Fix:** Reemplazar `index.css` completamente — dejar solo `@import "tailwindcss"` y el body en claro:
```css
@import "tailwindcss";
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background-color: #f8fafc; color: #1e293b; font-family: 'Inter', system-ui, sans-serif; }
```

### 2. Doble QueryClientProvider
`main.tsx` tenía su propio `<QueryClientProvider client={queryClient}>` y `App.tsx` creaba otro.
Esto hacía que las queries no matchearan el contexto y retornaban undefined.
**Fix:** Eliminar el `QueryClientProvider` de `main.tsx` — solo dejarlo en `App.tsx`. O al revés, pero solo uno.

### 3. Tailwind purge en Docker build
Después de `docker compose build frontend`, clases nuevas en `App.tsx` no aparecían en el CSS generado.
**Fix definitivo:** Cambiar todo a inline styles (`style={{...}}`). Los estilos quedan en el JS bundle y no dependen del purge de Tailwind. Aplica especialmente a componentes de layout principal.

### 4. docker restart no aplica cambios de código
`docker compose restart frontend` solo reinicia el proceso nginx — el HTML/JS/CSS estático es el del build anterior.
**Flujo correcto:**
```bash
docker compose build frontend   # reconstruye imagen con código nuevo
docker restart forestai-poc-frontend-1   # recarga con la imagen nueva
```

## LocationMiniMap — mini mapa de ubicación en DetailSidebar

Componente que muestra dónde en el mundo está la ortofoto. Usar cuando el usuario no sabe la ubicación geográfica del dataset.

```tsx
function LocationMiniMap({ analysisId }: { analysisId: string }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInst = useRef<maplibregl.Map | null>(null);

  const { data: trees } = useQuery({
    queryKey: ["trees", analysisId],
    queryFn: () => forestApi.getTrees(analysisId),
  });

  // Init mapa solo una vez
  useEffect(() => {
    if (!mapRef.current || mapInst.current) return;
    mapInst.current = new maplibregl.Map({
      container: mapRef.current,
      style: { version: 8, sources: { osm: { type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256 } },
        layers: [{ id: "osm", type: "raster", source: "osm" }] },
      center: [0, 0], zoom: 2, interactive: false,
    });
  }, []);

  // Fly al centroide de árboles
  useEffect(() => {
    const map = mapInst.current;
    if (!map || !trees?.length) return;
    const valid = trees.filter(t => t.lat !== 0 && t.lon !== 0);
    if (!valid.length) return;
    const lons = valid.map(t => t.lon), lats = valid.map(t => t.lat);
    const centerLon = (Math.min(...lons) + Math.max(...lons)) / 2;
    const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const el = document.createElement("div");
    el.style.cssText = "width:14px;height:14px;border-radius:50%;background:#10b981;border:2px solid white;box-shadow:0 0 6px rgba(16,185,129,0.6)";
    new maplibregl.Marker({ element: el }).setLngLat([centerLon, centerLat]).addTo(map);
    map.flyTo({ center: [centerLon, centerLat], zoom: 12 });
  }, [trees]);

  return (
    <div>
      <div ref={mapRef} style={{ width: "100%", height: 160, borderRadius: 12, overflow: "hidden" }} />
      <p style={{ fontSize: 11, color: "#64748b", textAlign: "center", marginTop: 4 }}>
        📍 {centerLat}°, {centerLon}°
      </p>
    </div>
  );
}
```

## Endpoint de reprocesar — patrón backend + frontend

```python
# Backend — POST /api/analyses/{id}/reprocess
@router.post("/{analysis_id}/reprocess", status_code=202)
def reprocess_analysis(analysis_id: str, db: Session = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis.filepath or not os.path.exists(analysis.filepath):
        raise HTTPException(404, "Archivo original no encontrado")
    db.query(models.Tree).filter(models.Tree.analysis_id == analysis_id).delete()
    analysis.status = models.AnalysisStatus.pending
    analysis.progress = 0; analysis.current_step = None
    analysis.tree_count = None; analysis.error = None; analysis.completed_at = None
    db.commit()
    run_analysis.delay(str(analysis_id), analysis.filepath)
    return {"analysis_id": analysis_id, "status": "pending"}
```

```tsx
// Frontend — botón en DetailSidebar
const { mutate: reprocess, isPending: reprocessing } = useMutation({
  mutationFn: async () => {
    const r = await fetch(`/api/analyses/${a.analysis_id}/reprocess`, { method: "POST" });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  onSuccess: () => qc2.invalidateQueries({ queryKey: ["analyses"] }),
});

// Botón deshabilitado cuando status === "processing" || "pending"
<button onClick={() => reprocess()} disabled={reprocessing || a.status === "processing" || a.status === "pending"}>
  🔄 Reprocesar
</button>
```

## ### 5. docker rm -f + docker run es más confiable que compose up para recrear

`docker restart` reutiliza el contenedor existente (imagen anterior).
`docker compose restart` también — NO cambia la imagen.
**Flujo correcto cuando compose up no está disponible:**
```bash
docker build -t forestai-poc-frontend:latest ./frontend
docker rm -f forestai-poc-frontend-1
docker run -d --name forestai-poc-frontend-1 --network forestai-poc_app-net -p 3010:80 forestai-poc-frontend:latest
# Verificar que el bundle cambió:
docker exec forestai-poc-frontend-1 ls /usr/share/nginx/html/assets/
```
Con docker compose disponible: `docker compose up -d --force-recreate frontend`.

## Overlay de ortofoto sobre mapa (ImageSource MapLibre)

```tsx
// Usar bounds del endpoint /bounds para superponer thumbnail sobre mapa
const { data: bounds } = useQuery({
  queryKey: ["bounds", analysisId],
  queryFn: async () => {
    const r = await fetch(`/api/analyses/${analysisId}/bounds`);
    return r.json() as Promise<{ west:number; south:number; east:number; north:number }>;
  },
  enabled: !!analysisId,
});

// En useEffect cuando cambia bounds:
map.addSource(`ortho-${analysisId}`, {
  type: "image",
  url: `/api/analyses/${analysisId}/thumbnail?t=${Date.now()}`,
  coordinates: [
    [bounds.west,  bounds.north],  // top-left
    [bounds.east,  bounds.north],  // top-right
    [bounds.east,  bounds.south],  // bottom-right
    [bounds.west,  bounds.south],  // bottom-left
  ],
});
map.addLayer({ id: `ortho-layer-${analysisId}`, type: "raster",
  source: `ortho-${analysisId}`, paint: { "raster-opacity": 0.85 } });
```

⚠️ Limpiar fuentes y capas anteriores antes de agregar (iterar sobre `map.getStyle().layers` y `map.getStyle().sources`).
⚠️ Verificar `map.isStyleLoaded()` antes de addSource — si false, usar `map.once("load", addLayer)`.

## Selector de análisis integrado en la vista mapa

Nelson quiere cambiar de ortofoto sin salir del mapa. Agregar un `<select>` en la barra superior:

```tsx
<select value={analysisId || ""} onChange={e => e.target.value && onSelectAnalysis(e.target.value)}>
  <option value="">— Seleccioná una ortofoto —</option>
  {completed.map(a => (
    <option key={a.analysis_id} value={a.analysis_id}>
      {a.name || a.filename} ({a.tree_count || 0} árboles)
    </option>
  ))}
</select>
```

Pasar prop `onSelectAnalysis: (id: string) => void` al MapPanel. En App.tsx conectar al state compartido `selectedId`.

## Navegación entre vistas (tabs en header)

```tsx
const [view, setView] = useState<"grid" | "map">("grid");

// Al seleccionar una card completed → ir al mapa automáticamente
onSelect={() => { setSelectedId(a.analysis_id); if (a.status === "completed") setView("map"); }}

// Al subir archivo → también ir al mapa
onSuccess={(id) => { setSelectedId(id); setView("map"); }}
```
