# Datos Abiertos Forestales — Argentina

Fuentes verificadas para integración en ForestAI. Investigadas en sesión 2026-05-20.
Actualizada con campos WFS reales (sesión 10, 2026-05-20).

---

## MAyDS / UMSEF — Bosques Nativos Argentina ⭐ IMPLEMENTADO

**Portal:** https://www.argentina.gob.ar/ambiente/bosques/umsef  
**Descarga directa:** https://datos.gob.ar/dataset/ambiente-bosques-nativos  
**WFS:** `https://geo.ambiente.gob.ar/geoserver/wfs`  
**Registro:** No requerido — acceso público  
**Uso comercial:** Permitido (datos públicos del Estado)

### Capas OTBN reales (verificadas via GetCapabilities)

Las capas OTBN son **por provincia**, no hay una capa consolidada nacional.
Formato de nombre: `bosques:{SIGLA_PROVINCIA}_{AÑO}_OTBN`

```
bosques:CH_2009_OTBN   → Chaco
bosques:FO_2012_OTBN   → Formosa
bosques:SA_2009_OTBN   → Salta
bosques:MI_2009_OTBN   → Misiones
bosques:JU_2009_OTBN   → Jujuy
bosques:TU_2009_OTBN   → Tucumán
# etc. — consultar GetCapabilities para lista completa
```

Para consultar capas disponibles:
```bash
curl -s "https://geo.ambiente.gob.ar/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities" \
  | grep -o '<Name>[^<]*</Name>' | grep -iE "bosque|otbn|nativo"
```

### Campos reales de las features OTBN (verificado con Chaco)

```python
# Ejemplo de feature real del WFS:
feat["properties"] == {
    "clase": "Bosque Nativo",    # siempre este string si es bosque
    "cat_cons": "III",            # I / II / III (NO "categoria" ni "cat")
    "area_ha": 12.6,              # área del polígono en hectáreas
    "id": 11131                   # ID interno
}

# OTBN categorías:
# I / "Rojo"   → Alto valor conservación, tala prohibida
# II / "Amarillo" → Mediana restricción
# III / "Verde" → Aprovechamiento permitido bajo condiciones
```

### Código de consulta por bbox

```python
import httpx, asyncio

async def query_otbn(lat, lon, radius_km):
    bbox = f"{lon - radius_km/111},{lat - radius_km/111},{lon + radius_km/111},{lat + radius_km/111}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get("https://geo.ambiente.gob.ar/geoserver/wfs", params={
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeName": "bosques:CH_2009_OTBN",   # cambiar por provincia
            "bbox": f"{bbox},EPSG:4326",
            "outputFormat": "application/json",
            "count": 200, "srsName": "EPSG:4326",
        })
    data = r.json()
    features = data.get("features", [])
    # Parsear campo cat_cons, no categoria
    categorias = []
    for feat in features:
        props = feat["properties"]
        cat = props.get("cat_cons")   # ← campo correcto
        clase = props.get("clase", "")
        area_ha = props.get("area_ha")
        if cat and clase == "Bosque Nativo":
            categorias.append({"cat": cat, "area_ha": area_ha})
    return categorias
```

### Detectar bosque nativo sin capa consolidada

```python
# Fallback: si hay features OTBN con clase "Bosque Nativo", hay bosque
tiene_bosque = any(
    feat["properties"].get("clase") == "Bosque Nativo"
    for feat in features
)
```

---

## Sentinel-2 (ESA Copernicus) — Búsqueda SIN autenticación

### Catálogo público CDSE (sin token)

```python
import httpx, asyncio

async def buscar_sentinel(lat, lon):
    """Busca imagen S2 más reciente con <30% nubes. NO requiere auth."""
    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    params = {
        "$filter": (
            "Collection/Name eq 'SENTINEL-2' and "
            "Attributes/OData.CSC.StringAttribute/any("
            "  att:att/Name eq 'productType' and "
            "  att/OData.CSC.StringAttribute/Value eq 'S2MSI2A') and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;POINT({lon} {lat})') and "
            "Attributes/OData.CSC.DoubleAttribute/any("
            "  att:att/Name eq 'cloudCover' and "
            "  att/OData.CSC.DoubleAttribute/Value le 30)"
        ),
        "$orderby": "ContentDate/Start desc",
        "$top": 1,
        "$expand": "Attributes",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
    data = r.json()
    if data.get("value"):
        item = data["value"][0]
        return {
            "available": True,
            "date": item["ContentDate"]["Start"][:10],
            "product_name": item["Name"],
            # cloud_coverage en Attributes
        }
    return {"available": False}
```

### NDVI con Sentinel-2 (requiere cuenta CDSE gratuita)

```python
import rasterio
import numpy as np

with rasterio.open("T20JMR_B08.jp2") as nir_src:
    nir = nir_src.read(1).astype(np.float32)
with rasterio.open("T20JMR_B04.jp2") as red_src:
    red = red_src.read(1).astype(np.float32)

ndvi = (nir - red) / (nir + red + 1e-10)
# Árboles maduros: NDVI 0.6-0.9
# Pasto: 0.3-0.5
# Suelo: 0.1-0.2
```

**Resolución Sentinel-2:** 10m/px — no alcanza para contar árboles individuales,
pero sí para NDVI zonal y comparar con detección RGB de drones.

### NDVI en Python — aplica a cualquier imagen con NIR

```python
# Para GeoTIFFs de drone multiespectral (4+ bandas):
if src.count >= 4:
    nir = src.read(4).astype(np.float32)  # banda 4 = NIR en MicaSense
    red = src.read(3).astype(np.float32)
    ndvi = (nir - red) / (nir + red + 1e-10)
    index_name = "NDVI"
else:
    # RGB puro: usar VARI como aproximación
    r, g, b = src.read(1), src.read(2), src.read(3)
    vari = (g - r) / (g + r - b + 1e-10)
    index_name = "VARI"
```

---

## INTA — GeoINTA

**Portal:** https://geointa.inta.gob.ar  
**Endpoints:**
```
WMS: https://geointa.inta.gob.ar/geoserver/wms
WFS: https://geointa.inta.gob.ar/geoserver/wfs
```

**Capas útiles:** NDVI, uso del suelo, cobertura vegetal, aptitud forestal.

**Nota:** Para incendios forestales, usar NASA FIRMS directamente — no integrar en ForestAI (fuera de scope del inventario).

---

## CONAE — SAOCOM (SAR banda L) — NO usar en PoC

**Tipo:** Radar SAR — penetra nubes y dosel  
**Acceso:** NO open data. Registro + aprobación institucional. Comercial = contrato.  
**Para PoC ForestAI:** Usar Sentinel-2, no SAOCOM.

---

## Resumen de Acceso

| Fuente | Dato | Libre | Registro | Uso comercial |
|--------|------|-------|----------|---------------|
| datos.gob.ar/UMSEF | Shapefiles bosques nativos + OTBN | Sí | No | Sí |
| geo.ambiente.gob.ar WFS | Capas OTBN en tiempo real | Sí | No | Sí |
| INTA GeoINTA WMS/WFS | Capas agro + cobertura | Sí | No (básico) | Verificar |
| Sentinel-2 ESA (búsqueda) | Metadatos + disponibilidad | Sí | No | Sí |
| Sentinel-2 ESA (descarga) | Imágenes multiespectrales NIR | Sí | Gratuito | Sí |
| CONAE SAOCOM | Imágenes SAR | No | Sí + aprobación | Contrato |

---

## Empresas del sector (referencia mercado, investigado 2026-05-20)

| Empresa | País | Diferencial |
|---------|------|-------------|
| Pachama | USA | IA + sat para créditos de carbono + anti-fraude |
| Treemetrics | Irlanda | Drones + visión artificial, calcula DAP/altura/volumen en plantaciones |
| Treeswift | USA | Robots terrestres + LiDAR, opera bajo dosel cerrado |
| Dendra Systems | UK | Drones que mapean Y plantan semillas, monitorea supervivencia |
| Sylvera | UK | Rating independiente proyectos de carbono ("Moody's del carbono") |
| Planet Labs | USA | 200 satélites, foto todo el planeta cada día |
| Satellogic | ARG | Constelación sat propia, cotiza NASDAQ |
| Auravant | ARG | SaaS monitoreo vegetación agro latinoamericano |

**Oportunidad Argentina:** No hay startup privada local en inventario forestal con IA.
34M ha bosque nativo con Ley 26.331 que obliga al monitoreo. Las internacionales tienen
poca presencia. Espacio para combinar tecnología con conocimiento regulatorio argentino.
