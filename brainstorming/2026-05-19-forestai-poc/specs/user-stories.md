# ForestAI PoC — User Stories

**Formato:** CREEMOS QUE / RESULTARÁ EN / CRITERIOS DE ACEPTACIÓN (estándar equipo Nelson)
**Fecha:** 2026-05-19

---

## HU-01 — Subir ortofoto para análisis

CREEMOS QUE al construir un endpoint que reciba una ortofoto GeoTIFF desde el frontend
y la encole para procesamiento asincrónico,
lograremos iniciar el pipeline de inventario forestal sin bloquear la interfaz del usuario.

RESULTARÁ EN un endpoint `POST /api/analyses` que acepte un archivo GeoTIFF,
lo almacene temporalmente, y devuelva un `analysis_id` con estado `pending`.

CRITERIOS DE ACEPTACIÓN:
- Dado un archivo GeoTIFF válido, cuando se hace POST /api/analyses, entonces se recibe `analysis_id` y status `pending` en menos de 3 segundos
- Dado un archivo que no es GeoTIFF, cuando se intenta subir, entonces se recibe error 422 con mensaje claro
- Dado un archivo mayor a 500MB, cuando se intenta subir, entonces se recibe error 413 con mensaje de límite
- Si el servidor cae durante el procesamiento, el job queda en estado `failed` y es recuperable (no se pierde el archivo)

---

## HU-02 — Seguimiento del procesamiento en tiempo real

CREEMOS QUE al exponer un endpoint de polling que informe el estado y progreso del análisis,
lograremos que el usuario vea el avance sin que la UI se congele ni tenga que recargar la página.

RESULTARÁ EN un endpoint `GET /api/analyses/{id}` que devuelva estado actual,
porcentaje de progreso, y mensaje descriptivo del paso en curso.

CRITERIOS DE ACEPTACIÓN:
- Dado un `analysis_id` válido, cuando se consulta GET /api/analyses/{id}, entonces se recibe `status`, `progress` (0-100) y `current_step`
- Los estados posibles son: `pending`, `processing`, `completed`, `failed`
- El progreso se actualiza con granularidad de al menos 4 pasos: carga → segmentación → clasificación → métricas
- Si el análisis falla, el campo `error` contiene un mensaje legible para el usuario
- El endpoint responde en menos de 500ms en todos los casos

---

## HU-03 — Ver mapa interactivo con árboles detectados

CREEMOS QUE al devolver los polígonos de copas detectadas como GeoJSON georreferenciado,
lograremos que el frontend los superponga sobre la ortofoto en el mapa interactivo.

RESULTARÁ EN un endpoint `GET /api/analyses/{id}/geojson` que devuelva un FeatureCollection
GeoJSON con un Feature por árbol detectado, incluyendo todas sus métricas como propiedades.

CRITERIOS DE ACEPTACIÓN:
- Dado un análisis `completed`, cuando se solicita el GeoJSON, entonces se recibe un FeatureCollection válido con geometrías Polygon en CRS EPSG:4326
- Cada Feature incluye propiedades: `tree_id`, `species`, `crown_area_m2`, `height_m`, `biomass_kg`, `age_years`, `confidence`
- Dado un análisis `pending` o `processing`, cuando se solicita el GeoJSON, entonces se recibe error 409 con mensaje "análisis en progreso"
- El GeoJSON se sirve en menos de 2 segundos para inventarios de hasta 1000 árboles
- Las coordenadas son correctas y los polígonos no se superponen entre sí

---

## HU-04 — Ver métricas de un árbol individual

CREEMOS QUE al exponer un endpoint con el detalle de un árbol específico,
lograremos que el usuario haga click en cualquier árbol del mapa y vea su ficha completa.

RESULTARÁ EN un endpoint `GET /api/analyses/{id}/trees/{tree_id}` que devuelva
todas las métricas calculadas para ese árbol individual.

CRITERIOS DE ACEPTACIÓN:
- Dado un `tree_id` válido, cuando se consulta el endpoint, entonces se reciben todas las métricas: especie, altura, área de copa, biomasa, edad estimada, coordenadas del centroide
- Dado un `tree_id` inexistente, entonces se recibe error 404
- La fuente de la tabla alométrica usada queda registrada en la respuesta (ej: "INTA 2019 - Eucalyptus globulus")
- El campo `confidence` indica el nivel de certeza de la clasificación de especie (bajo/medio/alto)
- Tiempo de respuesta menor a 300ms

---

## HU-05 — Ver panel de resumen del inventario

CREEMOS QUE al devolver un resumen agregado del inventario completo,
lograremos que el usuario tenga una visión ejecutiva del bosque analizado en segundos.

RESULTARÁ EN un endpoint `GET /api/analyses/{id}/summary` que devuelva estadísticas
agregadas del inventario: conteos, totales y distribuciones por especie.

CRITERIOS DE ACEPTACIÓN:
- Dado un análisis `completed`, cuando se solicita el summary, entonces se recibe: total de árboles, biomasa total en toneladas, área total de copas en hectáreas, distribución por especie (nombre + cantidad + % del total)
- Los valores de biomasa se expresan en kg por árbol y toneladas en total
- La distribución por especie lista todas las especies detectadas ordenadas por cantidad descendente
- El área de cobertura total se calcula como unión de polígonos (sin solapamiento)
- Tiempo de respuesta menor a 500ms

---

## HU-06 — Exportar inventario

CREEMOS QUE al ofrecer descarga del inventario en formatos estándar,
lograremos que el usuario pueda usar los datos en herramientas externas como QGIS, Excel o SIG forestales.

RESULTARÁ EN endpoints de exportación que devuelvan el inventario completo en CSV y GeoJSON.

CRITERIOS DE ACEPTACIÓN:
- `GET /api/analyses/{id}/export?format=csv` devuelve un CSV con una fila por árbol y columnas: tree_id, species, crown_area_m2, height_m, biomass_kg, age_years, lat, lon
- `GET /api/analyses/{id}/export?format=geojson` devuelve el GeoJSON completo descargable
- El Content-Type y Content-Disposition son correctos para trigger de descarga en el browser
- Los archivos exportados contienen metadatos de la sesión: fecha de análisis, nombre de archivo original, total de árboles
- Dado formato no soportado, se recibe error 400 con lista de formatos válidos

---

## HU-07 — Listar análisis históricos

CREEMOS QUE al guardar y listar los análisis realizados,
lograremos que el usuario pueda volver a consultar inventarios anteriores sin reprocesar.

RESULTARÁ EN un endpoint `GET /api/analyses` que liste todos los análisis con su estado y metadata.

CRITERIOS DE ACEPTACIÓN:
- El endpoint devuelve lista de análisis ordenados por fecha descendente
- Cada item incluye: `analysis_id`, `filename`, `status`, `created_at`, `tree_count` (si completado)
- La lista soporta paginación con parámetros `limit` y `offset`
- Un análisis `failed` aparece en la lista con su mensaje de error
- Tiempo de respuesta menor a 500ms para hasta 100 análisis

---

## Notas de Clarificación

- **Especie por reglas RGB:** En la PoC, la clasificación se basa en histograma de color y textura de la copa. No es ML. Especies soportadas inicialmente: eucalipto, pino, quebracho, algarrobo, araucaria.
- **Ortofoto asumida:** El usuario ya tiene la ortofoto procesada (GeoTIFF con referencia espacial). No incluimos fotogrametría en la PoC.
- **Sin auth en PoC:** No hay autenticación de usuarios. Todos los análisis son accesibles por `analysis_id`.
- **CRS de entrada:** Se acepta cualquier CRS válido en el GeoTIFF; el sistema reproyecta a EPSG:4326 internamente.
