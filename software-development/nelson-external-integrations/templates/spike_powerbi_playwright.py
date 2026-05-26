#!/usr/bin/env python3
"""
Template: Power BI Public Embed → Datos → Reporte Visual
Técnica: Playwright intercepta API WABI interna (sin Azure AD)

USO:
  1. Cambiar EMBED_URL por la URL del tablero público objetivo
  2. python3 spike_powerbi_playwright.py
  3. Los datos quedan en OUTPUT_DIR/qd_*.json + models.json
  4. Procesar con load_query_files() + parse_dsr()
"""

import asyncio, json, os
import pandas as pd

OUTPUT_DIR = './output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ← Cambiar por la URL del embed público objetivo
EMBED_URL = 'https://app.powerbi.com/view?r=TU_TOKEN_BASE64_AQUI'


# ── 1. CAPTURA VIA PLAYWRIGHT ─────────────────────────────────────────────────

async def capture_pbi_data(embed_url: str = EMBED_URL) -> list:
    """Carga el embed y captura todos los querydata via network intercept."""
    from playwright.async_api import async_playwright

    data_files = []
    query_count = [0]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120',
            locale='es-AR',
        )
        page = await context.new_page()

        async def on_response(response):
            url = response.url
            if 'querydata' in url:
                try:
                    body = await response.body()
                    query_count[0] += 1
                    fpath = f'{OUTPUT_DIR}/qd_{query_count[0]}.json'
                    with open(fpath, 'wb') as f:
                        f.write(body)
                    data_files.append(fpath)
                    print(f'  Query {query_count[0]}: {len(body)//1024}KB')
                except Exception as e:
                    print(f'  Error capturando query: {e}')
            elif 'modelsAndExploration' in url or 'conceptualschema' in url:
                try:
                    body = await response.body()
                    with open(f'{OUTPUT_DIR}/models.json', 'wb') as f:
                        f.write(body)
                    print(f'  Models: {len(body)//1024}KB')
                except: pass

        page.on('response', on_response)

        print(f'Cargando: {embed_url[:80]}...')
        try:
            await page.goto(embed_url, wait_until='networkidle', timeout=45000)
        except Exception as e:
            print(f'  Timeout (normal): {e}')

        # Esperar queries lazy (importante: Power BI carga datos de forma asíncrona)
        await asyncio.sleep(8)
        await browser.close()

    return data_files


# ── 2. PARSEAR FORMATO DSR DE POWER BI ────────────────────────────────────────

def parse_dsr(dsr_data: dict, col_names: list) -> pd.DataFrame:
    """
    Convierte el formato DSR comprimido de Power BI a DataFrame.
    
    DSR usa un encoding comprimido:
    - C: array de valores de columnas
    - R: bitmask de columnas que repiten valor anterior (bit i=1 → repetir col i)
    - M0, M1...: valores directos (alternativa a C, usada para KPIs simples)
    """
    ds = dsr_data.get('DS', [])
    if not ds: return pd.DataFrame()
    ph = ds[0].get('PH', [])
    if not ph: return pd.DataFrame()
    dm = ph[0].get('DM0', [])
    if not dm: return pd.DataFrame()

    rows, last_values = [], [None] * len(col_names)

    for item in dm:
        c = item.get('C', [])
        r = item.get('R', 0)

        # PITFALL: algunos items tienen el valor en M0, M1... no en C
        if not c:
            c = [item[f'M{i}'] for i in range(len(col_names)) if f'M{i}' in item]

        current = list(last_values)
        ci = 0
        for i in range(len(col_names)):
            if r and (r >> i) & 1:
                pass  # repetir valor anterior
            elif ci < len(c):
                current[i] = c[ci]
                ci += 1

        last_values = current
        rows.append(dict(zip(col_names, current)))

    return pd.DataFrame(rows)


# ── 3. CARGAR ARCHIVOS CAPTURADOS ─────────────────────────────────────────────

def load_query_files(data_files: list) -> list:
    """Parsea todos los archivos qd_*.json → lista de {columns, df}."""
    datasets = []
    for fpath in sorted(data_files):
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath) as f:
                d = json.load(f)
            results = d.get('results', [])
            if not results: continue
            result_data = results[0].get('result', {}).get('data', {})
            if not result_data: continue
            descriptor = result_data.get('descriptor', {})
            selects = descriptor.get('Select', [])
            col_names = [s.get('Name', f'col_{i}') for i, s in enumerate(selects)]
            dsr = result_data.get('dsr', {})
            df = parse_dsr(dsr, col_names)
            if not df.empty:
                datasets.append({'columns': col_names, 'df': df, 'file': os.path.basename(fpath)})
                print(f'  {os.path.basename(fpath)}: {len(df)} filas × {len(col_names)} cols — {col_names[:3]}')
        except Exception as e:
            print(f'  Error en {os.path.basename(fpath)}: {e}')
    return datasets


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Power BI Public Embed → Datos')
    print('=' * 40)

    # Usar archivos ya capturados si existen
    existing = [f'{OUTPUT_DIR}/qd_{i}.json' for i in range(1, 20)
                if os.path.exists(f'{OUTPUT_DIR}/qd_{i}.json')]

    if not existing:
        print('[1] Capturando datos via Playwright...')
        data_files = asyncio.run(capture_pbi_data())
    else:
        print(f'[1] Usando {len(existing)} archivos ya capturados')
        data_files = existing

    print(f'\n[2] Parseando {len(data_files)} queries...')
    datasets = load_query_files(data_files)

    print(f'\n[3] Datasets disponibles:')
    for i, ds in enumerate(datasets):
        print(f'  [{i}] {ds["file"]}: {len(ds["df"])} filas — {ds["columns"]}')

    print('\nListo. Procesar datasets con pandas a continuación.')
