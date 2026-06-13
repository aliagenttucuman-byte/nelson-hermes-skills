# White screen en React wizard: checklist de diagnóstico rápido

Contexto recurrente: la UI carga bien, pero al hacer click en una acción (ej. “Generar plan” o “Ejecutar plan”) queda en blanco.

## Señales típicas
- `console`: `Minified React error #31`
- API 4xx/5xx al mismo tiempo (`/api/...`)
- El error aparece recién después de una interacción, no al cargar home.

## Causas encontradas (durables)
1) **Axios mal configurado globalmente**
- Antipatrón:
  - `headers: { 'Content-Type': 'multipart/form-data' }` en el cliente global.
- Efecto:
  - requests JSON se serializan/formatean mal y backend responde 422.
- Fix:
  - quitar header global; enviar `FormData` solo en upload.

2) **Error de backend renderizado como objeto en React**
- Antipatrón:
  - `setError(err.response?.data?.detail || err.message)` y luego render directo.
- Efecto:
  - si `detail` es array/objeto, React revienta con error #31.
- Fix:
  - helper `toErrorMessage(err)` que convierta `detail` a string seguro.

3) **500 real en backend en flujo encadenado**
- Caso observado:
  - merges secuenciales usando referencias de archivo intermedio incorrectas.
- Fix:
  - ejecutar joins sobre `result_df` acumulado y validar keys antes de cada merge.
  - ante inconsistencia, devolver `HTTP 400` amigable en vez de `500`.

## Protocolo de verificación
1. Capturar `console`, `pageerror`, y respuestas API con Playwright.
2. Reproducir click exacto que dispara el blanco.
3. Confirmar endpoint fallando (status + body).
4. Corregir raíz (payload o backend), no parche visual.
5. Reprobar E2E: debe llegar a estado final (ej. “Resultado generado”) sin errores de consola.
