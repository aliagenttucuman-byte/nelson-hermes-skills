# Expreso Bisonte PoC — Debug de pantalla blanca + 500 al ejecutar plan

## Síntomas observados
- UI cargaba, pero al `Generar plan`/`Ejecutar plan` aparecía pantalla blanca o error React minificado.
- Network mostraba:
  - `422` en `POST /api/v1/excel/plan/suggest`
  - `500` en `POST /api/v1/excel/merge`

## Causa raíz 1 (frontend)
Axios estaba configurado globalmente con:
```ts
headers: { 'Content-Type': 'multipart/form-data' }
```
Eso convirtió requests JSON en multipart, y FastAPI no pudo parsear el body de Pydantic (`model_attributes_type`).

### Fix
- Quitar header global de Axios.
- Dejar que Axios use JSON por defecto.
- Usar `FormData` solo en endpoints de upload.

## Causa raíz 2 (frontend UX)
`setError(err.response?.data?.detail || err.message)` podía recibir `detail` como array de objetos y React intentaba renderizar objeto crudo → `Minified React error #31`.

### Fix
Crear helper `toErrorMessage(err)` que convierta `detail` (`string|object|array`) a string segura antes de renderizar.

## Causa raíz 3 (backend)
Merge encadenado reutilizaba keys de paso anterior sobre DataFrame intermedio sin validar columnas, disparando excepciones no controladas y devolviendo 500.

### Fix
- Validar columnas antes de cada join encadenado.
- Envolver endpoint `/merge` en `try/except`:
  - `HTTPException` se propaga.
  - Excepción inesperada -> `HTTPException(400, mensaje amigable)`.

## Verificación recomendada (rápida)
1. Browser E2E:
   - cargar archivos
   - generar plan
   - ejecutar plan
   - esperar `Resultado generado`
2. API smoke:
   - `POST /api/v1/excel/plan/suggest` devuelve `200`
   - `POST /api/v1/excel/merge` devuelve `200` o `400` explicativo, nunca `500`
3. Console browser sin errores React al mostrar mensajes de error.
