# Guía para Replicar: Pipeline Power BI Público → Reporte PNG

**Proyecto:** Spike Power BI → WhatsApp  
**Fecha:** 2026-05-19  
**Resultado final:** Extraer datos de cualquier tablero Power BI público (sin credenciales), calcular KPIs y generar reporte PNG dark-mode.

---

## Concepto clave: cómo funciona un embed público de Power BI

Cuando abrís `https://app.powerbi.com/view?r=TOKEN` en el browser, el JS de Power BI hace requests a servidores internos para bajar los datos. Nosotros interceptamos esas requests con un browser headless (Playwright) y extraemos los datos antes de que los renderice en pantalla.

```
Browser headless (Playwright)
       │  abre embed público
       ▼
  Power BI JS carga y pide datos a:
  POST .../querydata   ← interceptamos esto
       │
       ▼
  Archivos JSON con datos crudos (formato DSR)
       │
       ▼
  Parseo Python → pandas DataFrame
       │
       ▼
  KPIs + Reporte PNG
```

**Sin Azure AD. Sin credenciales. Solo la URL pública del embed.**

---

## Requisitos

```bash
pip install playwright pandas matplotlib
python3 -m playwright install chromium
```

---

## Paso 1 — Conseguir la URL del embed público

La URL tiene este formato:
```
https://app.powerbi.com/view?r=BASE64_TOKEN
```

**Cómo encontrarla:**
- Buscar en el sitio web del organismo (gobierno, empresa pública)
- Buscar `app.powerbi.com/view` en el HTML de la página
- Cualquier tablero que no pida login al abrirlo es válido

**Ejemplo real usado en el spike:**  
Tablero de empleo del Ministerio de Trabajo Argentina.

---

## Paso 2 — Capturar los datos con Playwright

El script intercepta todas las responses de tipo `querydata` que dispara Power BI:

```python
from playwright.async_api import async_playwright
import asyncio, json

EMBED_URL = "https://app.powerbi.com/view?r=TU_TOKEN_AQUI"

async def capturar_datos():
    captured = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await browser.new_page()

        async def on_response(response):
            if 'querydata' in response.url:
                try:
                    body = await response.body()
                    captured.append(json.loads(body))
                except:
                    pass

        page.on('response', on_response)
        await page.goto(EMBED_URL, wait_until='networkidle', timeout=45000)
        await asyncio.sleep(8)   # esperar que carguen todos los visuals
        await browser.close()

    return captured

data = asyncio.run(capturar_datos())
```

> **Pitfall:** Siempre esperar 8-10 segundos después de `networkidle`. Sin ese sleep, los visuals no terminan de cargar y faltan queries.

Cada elemento de `data` corresponde a un visual del tablero. Guardarlos como JSON para explorarlos:

```python
for i, d in enumerate(data):
    with open(f'output/qd_{i}.json', 'w') as f:
        json.dump(d, f, indent=2)
```

---

## Paso 3 — Identificar qué contiene cada query

Power BI incluye los nombres de columnas en el descriptor de cada query:

```python
import json

with open('output/qd_0.json') as f:
    raw = json.load(f)

result = raw['results'][0]['result']['data']
descriptor = result['descriptor']['Select']
col_names = [s['Name'] for s in descriptor]
print(col_names)
# Ejemplo: ['Fact_Empleo.Puestos de trabajo', 'Dim_Empresa.Nombre', ...]
```

Hacer esto para cada `qd_*.json` y mapear qué visual es cada uno.

---

## Paso 4 — Parsear el formato DSR de Power BI

Power BI comprime los datos en un formato llamado DSR. Parser completo:

```python
import pandas as pd

def parse_dsr(raw_result):
    result_data = raw_result['results'][0]['result']['data']
    descriptor  = result_data['descriptor']['Select']
    col_names   = [s['Name'] for s in descriptor]

    dsr = result_data['dsr']
    dm  = dsr['DS'][0]['PH'][0]['DM0']

    rows = []
    last_values = [None] * len(col_names)

    for item in dm:
        c = item.get('C', [])
        r = item.get('R', 0)  # bitmask: bit i=1 → repetir valor anterior

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

**Uso:**
```python
df = parse_dsr(data[7])   # el índice 7 tenía datos por departamento
print(df.head())
print(df.shape)
```

---

## Paso 5 — Calcular KPIs

Una vez que tenés el DataFrame, el proceso es el mismo que con cualquier dato pandas:

```python
# Ejemplo con datos de empleo
total_puestos = df['Fact_Empleo.Puestos de trabajo'].sum()
top_departamentos = (
    df.groupby('Dim_Geo.Departamento')['Fact_Empleo.Puestos de trabajo']
    .sum()
    .sort_values(ascending=False)
    .head(5)
)
```

Adaptar según los nombres de columnas del tablero específico.

---

## Paso 6 — Generar el reporte PNG

Mismo motor que el spike de energía (matplotlib GridSpec dark-mode). Solo cambiar los títulos y datos:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

COLOR_BG   = '#0A0E1A'
COLOR_CARD = '#111827'
COLOR_ACC  = '#00C8FF'

fig = plt.figure(figsize=(12, 16), facecolor=COLOR_BG)
gs  = GridSpec(4, 3, figure=fig, hspace=0.50, wspace=0.35)

# ... agregar subplots con KPIs y gráficos ...

plt.savefig('output/reporte_powerbi.png', dpi=150,
            bbox_inches='tight', facecolor=COLOR_BG)
plt.close()
```

---

## Paso 7 — Ejecutar el script completo

```bash
cd ~/brainstorming/2026-05-19-powerbi-whatsapp-spike/
python3 spike_powerbi_full.py
# → genera output/reporte_powerbi.png en ~30 segundos (primera vez)
# → ~3 segundos si los JSON ya están cacheados
```

---

## Pitfalls conocidos

### ❌ No se capturan datos (lista vacía)
**Causa:** El tablero tarda más de lo esperado en cargar los visuals.  
**Solución:** Aumentar el sleep de 8 a 15 segundos.
```python
await asyncio.sleep(15)   # más tiempo para tableros lentos
```

### ❌ Error al parsear DSR: KeyError 'PH'
**Causa:** Algunos visuals de Power BI usan una estructura DSR diferente o devuelven error.  
**Solución:** Envolver el parser en try/except y saltar los que fallen.
```python
try:
    df = parse_dsr(data[i])
except (KeyError, IndexError):
    continue   # ese visual no tiene datos útiles
```

### ❌ `playwright install` tarda mucho o falla
**Causa:** Descarga Chromium (~150MB).  
**Solución:** Correr `python3 -m playwright install chromium --with-deps` con buena conexión. Solo hay que hacerlo una vez.

### ❌ El tablero pide login (no es público)
**Causa:** El embed requiere autenticación Azure AD.  
**Solución:** Este método NO funciona con tableros privados. Para esos casos se necesita Azure App Registration + token OAuth2 (otro flujo).

### ❌ Los datos capturados son del visual de filtros, no datos reales
**Causa:** Power BI incluye queries de los slicers/filtros también.  
**Solución:** Explorar cada `qd_*.json` e identificar cuáles tienen la estructura de datos grande (muchas filas). Los slicers suelen tener 1-2 filas.

---

## Cómo adaptar a otro tablero de Power BI

Lo que NO cambia entre tableros:
- El mecanismo de captura Playwright (Paso 2)
- El parser DSR (Paso 4)
- La estructura del reporte matplotlib (Paso 6)

Lo que SÍ cambia:
- La URL del embed
- Los nombres de columnas (específicos de cada modelo de datos)
- Los KPIs que calculás

**Proceso de adaptación:**
1. Reemplazar `EMBED_URL` con la nueva URL
2. Correr la captura → guardar `qd_*.json`
3. Inspeccionar columnas de cada archivo
4. Reescribir `calcular_kpis()` según las columnas del nuevo modelo
5. Ajustar títulos en el reporte visual

---

## Diferencia con el spike de energía (datos.gob.ar)

| Aspecto | Spike Energía | Spike Power BI |
|---------|--------------|----------------|
| Fuente | CSV directo | Tablero Power BI público |
| Método | `pd.read_csv()` | Playwright + intercepción |
| Formato | CSV estándar | JSON formato DSR |
| Dependencias | pandas, matplotlib | + playwright, chromium |
| Velocidad | ~5 segundos | ~30 segundos (primera vez) |
| Complejidad | Baja | Media |

---

## Archivos del spike

```
spike_powerbi_full.py         ← SCRIPT PRINCIPAL ← USAR ESTE
spike_powerbi_playwright.py   ← versión exploratoria inicial
spike_powerbi_api.py          ← intento vía API REST (requiere Azure AD, no funciona sin credenciales)
output/
  qd_0.json ... qd_8.json     ← datos capturados (generados al correr)
  reporte_powerbi.png         ← reporte generado
```

---

## Dependencias completas

```
playwright>=1.40
pandas>=1.5
matplotlib>=3.6
numpy>=1.23
```

Instalar:
```bash
pip install playwright pandas matplotlib numpy
python3 -m playwright install chromium
```
