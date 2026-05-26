# Copernicus Data Space (CDSE) — Statistical API para NDVI

Verificado en producción, sesión 2026-05-20.

## Autenticación OAuth2

```
POST https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
&username=<email>
&password=<password>
&client_id=cdse-public
```

Respuesta: `{"access_token": "eyJ...", "expires_in": 600, ...}`
Token dura ~10 min — obtener fresh por request (no cachear entre llamadas).

## Statistical API

```
POST https://sh.dataspace.copernicus.eu/api/v1/statistics
Authorization: Bearer <token>
Content-Type: application/json
```

## Respuesta exitosa

```json
{
  "data": [{
    "interval": {"from": "...", "to": "..."},
    "outputs": {
      "ndvi": {
        "bands": {
          "B0": {
            "stats": {
              "min": -0.999,
              "max": 0.965,
              "mean": 0.643,
              "stDev": 0.213,
              "sampleCount": 65536,
              "noDataCount": 0
            }
          }
        }
      }
    }
  }],
  "status": "OK",
  "geometryPixelCount": 65536
}
```

## Errores conocidos y causas

| Error | Causa | Fix |
|-------|-------|-----|
| `data: []` | Rango temporal muy corto (±1 día) | Usar mínimo 30 días |
| `data: []` | `mosaicking: "ORBIT"` en evalscript | Quitar esa línea del setup() |
| `400 exceeds 1500m/px` | `resx: 10` con bbox grande | Usar `width: 256, height: 256` |
| `ValueError: Out of range float` | Stats devuelven NaN/Inf | Filtrar con `math.isfinite()` |
| `{"data":[], "status":"OK"}` | No hay imagen en el rango con <30% nubes | Ampliar rango o subir % nubosidad |

## Notas de integración Python

```python
import math, os, httpx
from datetime import datetime, timedelta

CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_STATS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"

async def _get_cdse_token():
    user = os.environ.get("CDSE_USER")
    password = os.environ.get("CDSE_PASSWORD")
    if not user or not password:
        return None
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                CDSE_TOKEN_URL,
                data={"grant_type": "password", "username": user,
                      "password": password, "client_id": "cdse-public"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
        except Exception:
            return None

def _safe_float(v):
    """Convierte stat value a float seguro para JSON."""
    if v is None:
        return None
    fv = float(v)
    return round(fv, 3) if math.isfinite(fv) else None
```

## TypeScript — interface mínima para el resultado

```typescript
interface SentinelResult {
  available: boolean;
  date: string | null;
  cloud_coverage: number | null;
  source: string;
  product_name?: string;
  message?: string;
  ndvi_mean?: number | null;   // null si no hay imagen o error
  ndvi_min?: number | null;
  ndvi_max?: number | null;
  ndvi_error?: string | null;  // mensaje de error de la Statistical API
}
```

## Render condicional React (patrón correcto)

```tsx
{data.ndvi_mean != null ? (
  <NDVICards mean={data.ndvi_mean} min={data.ndvi_min} max={data.ndvi_max} />
) : (
  <div>{data.ndvi_error || "Sin datos NDVI disponibles"}</div>
)}
```

**NO** usar mensaje hardcodeado de "requiere autenticación" — el backend puede ya tener
las credenciales configuradas y el frontend mostrar un mensaje obsoleto.

## Búsqueda de producto (endpoint público, sin auth)

```
GET https://catalogue.dataspace.copernicus.eu/odata/v1/Products
  ?$filter=Collection/Name eq 'SENTINEL-2'
  AND OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(...)')
  AND Attributes/.../cloudCover lt 30
  &$orderby=ContentDate/Start desc
  &$top=1
  &$expand=Attributes
```

Este endpoint no requiere token. Devuelve metadatos (fecha, producto, nubosidad).
El cálculo de píxeles (NDVI) sí requiere token + Statistical API.
