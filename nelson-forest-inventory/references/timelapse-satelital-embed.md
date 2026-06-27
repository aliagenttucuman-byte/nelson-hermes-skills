# Timelapse satelital embebido — pitfalls y solución

Aprendido en sesión jun 2026 (PoC yolov-orientacion / ForestAI Histórico).

## El problema

Embeber Google Earth Timelapse en un iframe NO funciona, aunque el `HEAD` salga 200:

- `https://earthengine.google.com/iframes/timelapse_player.html?v=LAT,LON,Z,latLng&t=...`
  → carga el viewer pero queda vacío. El viewer necesita que el host page popule el dataset por JS desde el padre — no es auto-contenido.
- `https://earth.google.com/web/@LAT,LON,...` → tiene `X-Frame-Options: SAMEORIGIN`. Bloqueado.
- `https://earthtime.org/explore` (CMU EarthTime) → embed-friendly (sin X-Frame, sin CSP frame-ancestors) PERO el formato de waypoint no es trivial de construir sin ejecutar su JS.

Conclusión: **NO confiar en deeplinks a viewers de timelapse de terceros**. El `HEAD 200` engaña — el viewer puede cargar y quedar en negro.

## La solución que SÍ funciona: NASA GIBS

Tiles JPEG públicos sin auth, sin CORS, sin X-Frame. Cobertura global desde 2000 (MODIS Terra)
y desde 1984 (Landsat WELD anual).

**Endpoint base**:
```
https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{LAYER}/default/{DATE}/GoogleMapsCompatible_Level9/{Z}/{Y}/{X}.jpg
```

**Capas útiles**:
- `MODIS_Terra_CorrectedReflectance_TrueColor` — diaria, desde 2000-02-24. Mid-year (junio 15)
  da menos nubes en hemisferio sur.
- `Landsat_WELD_CorrectedReflectance_Bands743_Global_Annual` — anual desde 1985 hasta 2014.
- `Landsat_WELD_CorrectedReflectance_Bands157_Global_Annual` — alternativa, también anual.

GetCapabilities completo:
```
https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi?SERVICE=WMTS&REQUEST=GetCapabilities
```

## Implementación: Leaflet vs nativo

Para evitar inflar deps, se puede hacer **sin Leaflet**: grid 3x3 de `<img>` con tile math estándar
(Web Mercator). Componente React puro:

```tsx
function latLonToTile(lat: number, lon: number, z: number) {
  const n = Math.pow(2, z)
  const x = ((lon + 180) / 360) * n
  const latRad = (lat * Math.PI) / 180
  const y = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n
  return { x, y }
}
```

Zoom según extensión del bbox (grados):
- `>8°` → z=5
- `3-8°` → z=6
- `1-3°` → z=7
- `0.4-1°` → z=8
- `<0.4°` → z=9

El archivo completo del componente `NasaTimelapseViewer` quedó en
`yolov-orientacion-poc/frontend/src/components/HistoricoPanel.tsx` — copiar de ahí si se
necesita en otra PoC.

## Pitfalls específicos

1. **El bundle del frontend está en un container Docker.** Editar `frontend/src/**` y `npm run build`
   localmente NO actualiza lo que sirve nginx en :9020. Hay que:
   ```
   docker compose build frontend
   docker compose up -d --force-recreate --no-deps frontend
   ```
   Verificar con `curl http://localhost:9020/index.html | grep index-` que el hash del bundle cambió.

2. **Ctrl+F5 en el navegador del usuario.** El bundle viejo queda cacheado. Avisarle al usuario que
   recargue con cache-bust después de cada deploy.

3. **No usar `~/Templates`-style URLs de Earth Engine como fuente confiable.** Aunque la API del backend
   (`/api/v1/historico/preset/...`) devuelva `timelapse_embed_url`, no significa que el iframe
   renderice. Probar SIEMPRE en navegador real, no solo `curl -I`.

4. **Auto-play**: 900ms entre frames funciona bien con tiles MODIS de 256x256 — cargan en <300ms desde
   el CDN de NASA. Más rápido genera flicker.
