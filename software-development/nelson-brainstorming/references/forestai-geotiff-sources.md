# Fuentes de GeoTIFF Forestales — Datos de Prueba

Descubierto durante la PoC ForestAI (2026-05-19). Para proyectos de inventario forestal con drones.

## Fuentes con descarga directa (sin registro)

### NeonTreeEvaluation — MEJOR PARA ARRANCAR
- **URL:** https://zenodo.org/records/5914554
- **API Zenodo:** `curl -s 'https://zenodo.org/api/records/5914554'` para listar archivos
- **Archivos:** `annotations.zip` (548KB, 226 XML con bounding boxes), `training.zip` (4.3GB), `evaluation.zip` (3.6GB)
- **Resolución:** 10 cm/pixel RGB
- **CRS:** EPSG:32617 (UTM zona 17N)
- **Tamaño tiles:** 400x400 px cada tile
- **Anotaciones:** Bounding boxes XML de árboles individuales (formato Pascal VOC)
- **Tiles de prueba chicos (directo de DeepForest):**
  ```bash
  curl -L -o OSBS_029.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/OSBS_029.tif"
  curl -L -o SJER_sample.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/2018_SJER_3_252000_4107000_image_477.tif"
  curl -L -o australia.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/australia.tif"
  ```
- **Nota:** `australia.tif` tiene 1.8 cm/pixel (muy alta resolución, ideal para watershed)

### ReforesTree — MEJOR PARA LATAM
- **URL:** https://zenodo.org/records/6813783
- **Archivo:** `reforesTree.zip` (7.1 GB)
- **Tipo:** Drone UAV, Ecuador, reforestación tropical
- **Resolución:** 4-5 cm/pixel RGB
- **Anotaciones:** Polígonos GeoJSON de copas individuales + especie + biomasa
- **Acceso:** Directo desde Zenodo sin registro

## Fuentes con exploración interactiva

### OpenAerialMap
- **URL:** https://map.openaerialmap.org
- Navegar mapa → click en imagen → descargar GeoTIFF directo
- Calidad variable; buscar zonas boscosas (Costa Rica, Colombia, Brasil tienen buena cobertura)

### USGS EarthExplorer (NAIP USA)
- **URL:** https://earthexplorer.usgs.gov
- Registro simple. Resolución 60cm/pixel. 4 bandas (RGBI). Cubre todo USA.
- No ideal para árbol individual pero útil para contexto regional.

## Argentina — Limitaciones conocidas

- **IGN:** mapa.ign.gob.ar — ortoimagen 50cm/px de Argentina, requiere registro, no pensado para árbol individual
- **MAyDS Bosques:** bosques.ambiente.gob.ar — solo Landsat/Sentinel (10-30m), no útil para detección de árboles
- **INTA:** publicaciones en Zenodo esporádicas, buscar `Argentina forest drone` en Zenodo
- **Conclusión:** No existe repositorio LATAM público robusto con ortofotos de drone de alta res para árboles. ReforesTree (Ecuador) es la mejor opción regional disponible.

## Cómo inspeccionar un GeoTIFF con Python

```python
import rasterio

with rasterio.open('archivo.tif') as src:
    print(f'Dimensiones: {src.width}x{src.height}')
    print(f'Bandas: {src.count}')
    print(f'CRS: {src.crs}')
    print(f'Resolución: {abs(src.transform.e):.4f} m/px')
    print(f'Bounds: {src.bounds}')
```

## Cómo listar archivos de un record Zenodo via API

```bash
curl -s 'https://zenodo.org/api/records/{RECORD_ID}' | \
  python3 -c "import json,sys; data=json.load(sys.stdin); \
  [print(f['key'], round(f['size']/1024/1024,1), 'MB', f['links']['self']) \
  for f in data.get('files',[])]"
```

## Datos de prueba descargados para ForestAI PoC

Ubicación: `~/brainstorming/2026-05-19-forestai-poc/data/`

| Archivo | Origen | Res | Tamaño | Notas |
|---|---|---|---|---|
| OSBS_029.tif | NEON Florida | 10cm | 594KB | 400x400px, bosque subtropical |
| SJER_sample.tif | NEON California | 10cm | 522KB | 400x400px, bosque mediterráneo |
| australia.tif | DeepForest | 1.8cm | 1.6MB | 750x708px, muy alta res |
| annotations.zip | NeonTreeEvaluation | — | 548KB | 226 XMLs Pascal VOC con bounding boxes |
