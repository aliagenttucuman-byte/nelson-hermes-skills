# White screen + 422 + React #31 (FastAPI + React + Axios)

## Síntoma
- UI queda en blanco al ejecutar acción.
- Console: `Minified React error #31`.
- Network: `POST ... 422` en endpoint que esperaba JSON.

## Causa típica
1. Cliente Axios configurado globalmente con:
   `headers: { 'Content-Type': 'multipart/form-data' }`
2. Endpoints JSON (Pydantic/FastAPI) reciben body como form-data y responden 422.
3. Frontend intenta renderizar `error.response.data.detail` (array/objeto) directamente como string en JSX/state.

## Fix de bajo riesgo
1. Quitar `Content-Type` global del cliente Axios.
2. Usar multipart solo en requests de upload (`FormData`).
3. Normalizar errores antes de setear estado/UI:
   - si `detail` es array → join de `msg`
   - si es objeto → `JSON.stringify` o `detail.msg`
   - fallback a `err.message`

## Verificación
- `plan/suggest` y `merge` responden 200 con JSON válido.
- No hay `Minified React error #31` en consola.
- UI mantiene render incluso ante errores funcionales (400 controlados).