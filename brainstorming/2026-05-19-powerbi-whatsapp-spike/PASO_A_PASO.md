# Spike 2: Power BI Público → Reporte Visual

**Fecha:** 2026-05-19
**Caso:** Embed público del Ministerio de Trabajo AR → PNG dark-mode
**Archivo principal:** `spike_powerbi_full.py`

---

## ¿Qué hace este spike?

Carga un reporte de Power BI público (app.powerbi.com/view?r=...) usando
un browser headless (Playwright), intercepta los datos que Power BI
descarga internamente, los parsea, y genera el mismo tipo de reporte
visual que el Spike 1.

**Sin Azure AD. Sin credenciales. Solo la URL pública del embed.**

---

## Concepto clave: cómo funciona un embed público de Power BI

Cuando abrís `app.powerbi.com/view?r=TOKEN` en el browser:

```
Browser → carga JS de Power BI
JS decodifica el TOKEN (base64) → obtiene reportId + resourceKey
JS hace requests a servidores WABI (Windows Azure BI):
  GET  /public/reports/{key}/modelsAndExploration  → schema del modelo
  POST /public/reports/querydata                   → datos reales (formato DSR)
```

Nosotros simplemente interceptamos esas requests con Playwright.

---

## Paso a Paso

### PASO 1 — Conseguir la URL del embed público

La URL tiene este formato:
```
https://app.powerbi.com/view?r=BASE64_TOKEN
```

El token decodificado contiene:
```json
{"k": "RESOURCE_KEY", "t": "TENANT_ID", "c": 4}
```

**Cómo encontrar embeds públicos:**
- Buscar en el sitio web del organismo (gobierno, empresa pública, etc.)
- Buscar `app.powerbi.com/view` en el HTML de la página
- Cualquier tablero que no pida login al abrirlo en el browser es válido

---

### PASO 2 — Capturar los datos con Playwright

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox'])

    page = await browser.new_page()

    # Interceptar todas las responses
    async def on_response(response):
        if 'querydata' in response.url:
            body = await response.body()
            # guardar en archivo JSON
            with open(f'output/qd_{n}.json', 'wb') as f:
                f.write(body)

    page.on('response', on_response)

    await page.goto(EMBED_URL, wait_until='networkidle', timeout=45000)
    await asyncio.sleep(8)   # esperar que carguen todos los visuals
    await browser.close()
```

**Archivos resultantes:**
```
output/qd_1.json   → KPI total (ej: total puestos de trabajo)
output/qd_2.json   → fecha de actualización
output/qd_3.json   → conteo de empresas
output/qd_7.json   → datos por departamento (527 filas)
output/qd_8.json   → datos geo con lat/long (10.000 filas)
```

**Pitfall:** Playwright necesita esperar 8-10 segundos después de
`networkidle` para que los visuals terminen de cargar y disparen todas
las queries.

---

### PASO 3 — Parsear el formato DSR de Power BI

Power BI usa un formato comprimido llamado DSR. La estructura es:

```json
{
  "results": [{
    "result": {
      "data": {
        "descriptor": {
          "Select": [
            {"Name": "NombreColumna1"},
            {"Name": "NombreColumna2"}
          ]
        },
        "dsr": {
          "DS": [{
            "PH": [{
              "DM0": [
                {"C": [valor1, valor2]},          // primera fila
                {"C": [valor1], "R": 1},           // R=bitmask de repetidos
                {"M0": 6595449}                    // a veces valor en M0 directo
              ]
            }]
          }]
        }
      }
    }
  }]
}
```

**Parser:**
```python
def parse_dsr(dsr_data, col_names):
    dm = dsr_data['DS'][0]['PH'][0]['DM0']
    rows = []
    last_values = [None] * len(col_names)

    for item in dm:
        c = item.get('C', [])
        r = item.get('R', 0)   # bitmask: bit i=1 → usar valor anterior

        # a veces el valor está en M0, M1... en lugar de C
        if not c:
            c = [item[f'M{i}'] for i in range(len(col_names)) if f'M{i}' in item]

        current = list(last_values)
        ci = 0
        for i in range(len(col_names)):
            if r and (r >> i) & 1:
                pass  # repetir anterior
            elif ci < len(c):
                current[i] = c[ci]
                ci += 1

        last_values = current
        rows.append(dict(zip(col_names, current)))

    return pd.DataFrame(rows)
```

---

### PASO 4 — Identificar qué contiene cada query

Después de parsear, cada archivo tiene columnas descriptivas:

```python
descriptor = result_data['descriptor']['Select']
col_names = [s['Name'] for s in descriptor]
# Ejemplo: ['Dim_Empresas.Latitud', 'Dim_Empresas.Longitud', 'Fact_Empleo.Puestos de trabajo']
```

Mapear por nombre de columna para saber qué hacer con cada dataset.

---

### PASO 5 — Calcular KPIs y generar reporte

Mismo proceso que el Spike 1 desde acá:
- Filtrar el dataset correcto por nombre de columna
- Calcular métricas clave
- Generar PNG con matplotlib GridSpec

```bash
python3 spike_powerbi_full.py
# → genera output/reporte_powerbi.png
```

---

### PASO 6 — Ejecutar

```bash
# Instalar dependencias
pip install playwright pandas matplotlib
python3 -m playwright install chromium

# Correr el spike
cd ~/brainstorming/2026-05-19-powerbi-whatsapp-spike/
python3 spike_powerbi_full.py
```

Primera vez: descarga datos (~20-30 seg por el browser).
Siguientes veces: usa los JSON cacheados (~3 seg).

---

## Para replicar con otro tablero de Power BI

1. Reemplazar `EMBED_URL` con la nueva URL pública
2. Correr el script — captura automática de todos los querydata
3. Inspeccionar los archivos `qd_*.json` para ver qué columnas tienen
4. Ajustar la función `calcular_kpis()` según las columnas del nuevo modelo
5. Ajustar el reporte visual con los nuevos KPIs

**Lo que NO cambia entre tableros:**
- El mecanismo de captura Playwright (pasos 2)
- El parser DSR (paso 3)
- La estructura del reporte matplotlib (paso 5)

**Lo que SÍ cambia:**
- La URL del embed
- Los nombres de columnas (específicos de cada modelo de datos)
- Los KPIs que calculás

---

## Dependencias

```bash
pip install playwright pandas matplotlib
python3 -m playwright install chromium
```

## Archivos del spike

```
spike_powerbi_playwright.py   # versión exploratoria inicial
spike_powerbi_api.py          # intento via API REST (no funciona sin AAD)
spike_powerbi_full.py         # versión final completa ← USAR ESTE
output/
  qd_1.json ... qd_8.json    # datos capturados (no en git)
  reporte_powerbi.png         # reporte generado (no en git)
```
