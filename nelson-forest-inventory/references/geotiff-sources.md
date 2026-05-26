# Fuentes de GeoTIFF Forestales — Referencia

Ver también: `nelson-brainstorming/references/forestai-geotiff-sources.md` para la versión completa con comandos detallados.

## Resumen rápido

| Fuente | URL | Res | Registro | Anotaciones | Tamaño |
|---|---|---|---|---|---|
| NeonTreeEvaluation tiles | github.com/weecology/DeepForest (src/deepforest/data/) | 10cm | No | Sí (XML) | ~600KB/tile |
| NeonTreeEvaluation completo | zenodo.org/records/5914554 | 10cm | No | Sí (XML) | 4.3GB training |
| ReforesTree Ecuador | zenodo.org/records/6813783 | 4-5cm | No | Sí (GeoJSON) | 7.1GB |
| OpenAerialMap | openaerialmap.org | Variable | No | No | Variable |
| USGS NAIP | earthexplorer.usgs.gov | 60cm | Sí (simple) | No | ~500MB/tile |
| IGN Argentina | mapa.ign.gob.ar | 50cm | Sí | No | Variable |

## Comandos de descarga directa (tiles chicos, sin registro)

```bash
DATA_DIR=~/brainstorming/2026-05-19-forestai-poc/data
mkdir -p $DATA_DIR && cd $DATA_DIR

# Tile Florida subtropical (10cm, 400x400px)
curl -L -o OSBS_029.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/OSBS_029.tif"

# Tile California mediterráneo (10cm, 400x400px)
curl -L -o SJER_sample.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/2018_SJER_3_252000_4107000_image_477.tif"

# Tile Australia (1.8cm, 750x708px — mejor para calibrar watershed)
curl -L -o australia.tif "https://raw.githubusercontent.com/weecology/DeepForest/main/src/deepforest/data/australia.tif"

# 226 anotaciones XML con bounding boxes de árboles
curl -L -o annotations.zip "https://zenodo.org/api/records/5914554/files/annotations.zip/content"
unzip annotations.zip
```

## Inspección rápida de un GeoTIFF

```python
import rasterio

with rasterio.open('archivo.tif') as src:
    print(f'{src.width}x{src.height}px | {src.count} bandas | CRS:{src.crs} | res:{abs(src.transform.e):.4f}m/px')
```

## Listar archivos de un record Zenodo

```bash
curl -s "https://zenodo.org/api/records/{ID}" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
  [print(f['key'], round(f['size']/1024/1024,1), 'MB') for f in d.get('files',[])]"
```

## OpenAerialMap — API para ortofotos reales pequeñas

Base de datos global de imágenes aéreas open data. Útil para demos con imágenes reales.

```bash
# Buscar ortofotos < 20MB
curl -s "https://api.openaerialmap.org/meta?limit=50&type=image%2Ftiff" -o /tmp/oam.json
python3 -c "
import json
d = json.load(open('/tmp/oam.json'))
for item in d.get('results',[]):
    sz = item.get('file_size', 0)
    url = item.get('uuid','')   # IMPORTANTE: URL está en 'uuid', NO en 'download'
    if sz and sz < 20*1024*1024 and url.endswith('.tif'):
        print(f'{sz//1024//1024}MB | {item[\"title\"][:50]} | {url}')
"
```

URLs probadas y funcionales (mayo 2026):
- 5MB Bricenio Ecuador: `https://oin-hotosm-temp.s3.amazonaws.com/572b2552cd0663bb003c32a2/0/572b25b82b67227a79b4fbf1.tif`
- 14MB Tacloban Filipinas: `https://oin-hotosm-temp.s3.amazonaws.com/1/0/55c36a162b67227a79b4f4d9.tif`
- 15MB Rumicucho Ecuador: `https://oin-hotosm-temp.s3.amazonaws.com/58d86fafca8ed70011209f81/0/113fb2f2-d8dc-425a-97c2-20050a580192.tif`

**Nota:** No son ortofotos forestales — son de zonas urbanas/rurales de operaciones humanitarias. Para demos de árboles usar los tiles NEON. Para demos de "ortofoto real georreferenciada" cualquiera sirve.

## Limitaciones Argentina

No existe repositorio público robusto de ortofotos de drone para árboles individuales en Argentina.
- IGN 50cm: útil para contexto regional, no para árbol individual
- MAyDS Bosques: solo Landsat/Sentinel (10-30m), no útil
- INTA: publicaciones esporádicas en Zenodo, buscar `Argentina forest drone`
- ReforesTree (Ecuador) es la mejor aproximación regional disponible
