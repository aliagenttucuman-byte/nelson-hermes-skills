# Power BI Public Embed — API WABI Network Intercept

Técnica validada en sesión 2026-05-19. Extrae datos reales de cualquier
embed público de Power BI (app.powerbi.com/view?r=TOKEN) sin Azure AD.

---

## Cómo funciona internamente

Cuando se carga un embed público de Power BI:

1. El browser carga `app.powerbi.com/view?r=BASE64_TOKEN`
2. El JS decodifica el token y descubre el cluster WABI del tenant
3. Hace un GET a `{cluster}/public/reports/{key}/modelsAndExploration` → schema
4. Hace múltiples POSTs a `{cluster}/public/reports/querydata` → datos DSR
5. El JS renderiza el reporte en canvas con los datos recibidos

**Clusters WABI (ejemplos):**
- `wabi-south-central-us-c-primary-api.analysis.windows.net` (tenant Argentina gov)
- `wabi-brazil-south-redirect.analysis.windows.net`
- `wabi-us-north-central-redirect.analysis.windows.net`

El cluster depende del tenant y no es predecible sin cargar el embed.
Por eso usamos Playwright para que el browser lo resuelva solo.

---

## Token base64 — estructura

```
app.powerbi.com/view?r=eyJrIjoiM2Q4MjQ5ODc...
```

Decodificar:
```python
import base64, json
token = "eyJrIjoiM2Q4..."
token += '=' * (4 - len(token) % 4)  # padding
data = json.loads(base64.b64decode(token).decode())
# data = {"k": "report-key", "t": "tenant-id", "c": 4}
# o     {"reportId": "...", "groupId": "...", "key": "..."}
```

Campos posibles: `k` o `reportId` (report key), `t` o `groupId` (tenant/group ID), `c` (cloud: 4=commercial)

---

## Formato DSR (Data Shape Result)

Power BI comprime los datos en formato DSR. Estructura:

```json
{
  "results": [{
    "result": {
      "data": {
        "descriptor": {
          "Select": [
            {"Name": "Tabla.Columna", "Kind": 2, "Format": "#,0"}
          ]
        },
        "dsr": {
          "DS": [{
            "PH": [{
              "DM0": [
                {"S": [...], "C": [valor1, valor2]},
                {"C": [val3]},
                {"R": 1, "C": [val4]}
              ]
            }]
          }]
        }
      }
    }
  }]
}
```

**Reglas del parser DSR:**
- `C`: array de valores para las columnas en orden
- `R`: bitmask — bit i=1 significa "repetir el valor anterior de columna i"
- `M0`, `M1`...: a veces el valor está directamente en estas keys, no en `C` (edge case para filas de 1 valor)
- `S`: schema metadata (solo en primera fila de cada grupo)

**Ejemplo: R=1 (binario 0001) → repetir col 0, leer col 1 nueva**

---

## Embed real del Gobierno Argentino validado

**Ministerio de Trabajo — Empleo registrado:**
```
https://app.powerbi.com/view?r=eyJrIjoiM2Q4MjQ5ODctYzE5MS00MTAyLWI3YWEtMTUwYWMzNWVjZmQyIiwidCI6ImNiODg0ZGI1LTI0ODUtNGY5Yi05MzhlLTNlNjIxZjIyMjU3YiIsImMiOjR9
```

Tenant ID: `cb884db5-2485-4f9b-938e-3e621f22257b` (Gobierno Argentina)
Cluster: `wabi-south-central-us-c-primary-api.analysis.windows.net`

**Datos que contiene:**
| Query | Columnas | Filas | Contenido |
|-------|----------|-------|-----------|
| qd_1 | Fact_Empleo.Puestos de trabajo | 1 | Total nacional: **6,595,449** |
| qd_4 | Fact_Empleo.Sucursales | 1 | Total sucursales |
| qd_5 | Fact_Empleo.Empresas | 1 | Total empresas |
| qd_7 | % Empleo Departamento, IdMapa | 527 | % por departamento |
| qd_8 | Latitud, Longitud, Puestos | 10,000 | Empresas georeferenciadas |

Schema (Entities del modelo):
- `Dim_ActividadesEconomicas` — CLAE 6 dígitos
- `Dim_Empresas` — CUIT, coordenadas
- `Fact_Empleo` — puestos, empleo
- `Dim_Departamentos` — provincia, departamento
- `Dim_Tramos` — tamaño del establecimiento

---

## Por qué urllib directo NO funciona

Intentar hacer las llamadas WABI directamente desde Python falla:
- Sin cookies de sesión de `app.powerbi.com` → `403 Forbidden`
- Sin el handshake inicial del embed JS → `Remote end closed connection`
- Power BI hace fingerprinting del cliente (TLS, headers, orden) → detecta bots

**Solución:** Usar Playwright y dejar que el browser real haga el handshake. Playwright 1.59 + Chromium ya instalado en `/home/server/.cache/ms-playwright/chromium-1217/`.

---

## Script completo reutilizable

Ver: `~/brainstorming/2026-05-19-powerbi-whatsapp-spike/spike_powerbi_full.py`

Funciones clave:
- `capture_pbi_data(embed_url, output_dir)` — Playwright intercept async
- `parse_dsr(dsr_data, col_names)` — DSR → DataFrame
- `load_query_files(data_files)` — cargar y parsear todos los qd_N.json
- `calcular_kpis(datasets)` — extraer métricas clave
- `generar_reporte(kpis, datasets)` — matplotlib dark theme → PNG

---

## Aplicación al caso YPF

Si YPF tiene un tablero publicado como URL pública (`app.powerbi.com/view?r=...`):
1. Copiar esa URL
2. Reemplazar `EMBED_URL` en el script
3. Correr `capture_pbi_data()` → archivos qd_N.json
4. Inspeccionar columnas con `load_query_files()`
5. Adaptar `calcular_kpis()` a las columnas reales del tablero YPF
6. Adaptar `generar_reporte()` con KPIs de energía

Si requiere login corporativo (Azure AD) → ver Escenario B con msal en el skill principal.
