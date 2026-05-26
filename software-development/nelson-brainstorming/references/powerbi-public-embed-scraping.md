# Power BI Embed Público → Datos → Reporte PNG

**Spike:** `~/brainstorming/2026-05-19-powerbi-whatsapp-spike/`  
**Script principal:** `spike_powerbi_full.py`  
**Fecha validado:** 2026-05-19

---

## Concepto clave

Cualquier tablero `app.powerbi.com/view?r=TOKEN` que no pida login puede ser interceptado.
El JS de Power BI hace requests internas a endpoints WABI (`/querydata`) con los datos reales.
Playwright las captura antes de que el browser las renderice.

```
Browser headless → embed público → Power BI JS → POST .../querydata
                                                          ↓ interceptamos
                                               JSON formato DSR → pandas
```

---

## Dependencias

```bash
pip install playwright pandas matplotlib numpy
python3 -m playwright install chromium
```

---

## Patrón de captura

```python
from playwright.async_api import async_playwright
import asyncio, json

EMBED_URL = "https://app.powerbi.com/view?r=TU_TOKEN"

async def capturar():
    captured = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'])
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
        await asyncio.sleep(8)   # ← crítico: esperar que carguen todos los visuals
        await browser.close()
    return captured
```

---

## Parser DSR (formato interno Power BI)

```python
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

        if not c:
            c = [item[f'M{i}'] for i in range(len(col_names)) if f'M{i}' in item]

        current = list(last_values)
        ci = 0
        for i in range(len(col_names)):
            if r and (r >> i) & 1:
                pass
            elif ci < len(c):
                current[i] = c[ci]
                ci += 1

        last_values = current
        rows.append(dict(zip(col_names, current)))

    return pd.DataFrame(rows)
```

---

## Identificar columnas de cada query

```python
result_data = raw['results'][0]['result']['data']
col_names = [s['Name'] for s in result_data['descriptor']['Select']]
print(col_names)
```

Hacer esto para cada `qd_*.json` para mapear qué visual es cada uno.

---

## Pitfalls

| Error | Causa | Solución |
|-------|-------|----------|
| Lista vacía capturada | Tablero tarda más de lo esperado | Subir sleep a 15 segundos |
| KeyError 'PH' en parser | Visual sin datos o estructura DSR diferente | try/except en el parser, skip si falla |
| `playwright install` falla | Red lenta o sin deps del sistema | `python3 -m playwright install chromium --with-deps` |
| Tablero pide login | No es embed público, requiere Azure AD | Este método no aplica, necesita OAuth2 AAD |
| qd_*.json son de filtros, no datos | Los slicers también disparan querydata | Filtrar por shape: datasets con >10 filas son los que interesan |

---

## Lo que NO cambia entre tableros

- Mecanismo de captura Playwright
- Parser DSR

## Lo que SÍ cambia

- URL del embed
- Nombres de columnas
- KPIs a calcular

---

## Diferencia vs datos.gob.ar directo

| Aspecto | CSV directo | Power BI embed |
|---------|-------------|----------------|
| Método | `pd.read_csv()` | Playwright + intercepción |
| Formato | CSV | JSON DSR |
| Deps extra | ninguna | playwright + chromium |
| Velocidad | ~5 seg | ~30 seg (1ra vez) |

---

## Para el caso Power BI corporativo YPF (post-PoC)

El flow es idéntico pero con autenticación:
1. Azure AD App Registration → token OAuth2
2. Power BI REST API: `POST /reports/{id}/ExportTo` → PDF/PNG
3. Alternativa: Playwright con login AAD → screenshot del tablero

El motor de análisis + envío WA es el mismo, solo cambia la fuente.
