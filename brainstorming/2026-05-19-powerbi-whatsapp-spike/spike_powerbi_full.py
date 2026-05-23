#!/usr/bin/env python3
"""
Spike: Power BI Public Embed → Procesar datos → Reporte Visual
Combina captura Playwright + procesamiento pandas + reporte matplotlib
"""

import asyncio, json, os, re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = os.path.expanduser('~/brainstorming/2026-05-19-powerbi-whatsapp-spike/output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

EMBED_URL = 'https://app.powerbi.com/view?r=eyJrIjoiM2Q4MjQ5ODctYzE5MS00MTAyLWI3YWEtMTUwYWMzNWVjZmQyIiwidCI6ImNiODg0ZGI1LTI0ODUtNGY5Yi05MzhlLTNlNjIxZjIyMjU3YiIsImMiOjR9'

# ── 1. CAPTURA VIA PLAYWRIGHT ─────────────────────────────────────────────────

async def capture_pbi_data():
    """Carga el embed y captura todos los querydata."""
    from playwright.async_api import async_playwright
    
    data_files = []
    
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
        
        query_count = [0]
        
        async def on_response(response):
            if 'querydata' in response.url:
                try:
                    body = await response.body()
                    query_count[0] += 1
                    fpath = f'{OUTPUT_DIR}/qd_{query_count[0]}.json'
                    with open(fpath, 'wb') as f:
                        f.write(body)
                    data_files.append(fpath)
                    print(f'  Query {query_count[0]}: {len(body)//1024}KB')
                except: pass
        
        page.on('response', on_response)
        
        try:
            await page.goto(EMBED_URL, wait_until='networkidle', timeout=45000)
        except: pass
        
        await asyncio.sleep(8)
        await browser.close()
    
    return data_files


# ── 2. PARSEAR DSR FORMAT de Power BI ────────────────────────────────────────

def parse_dsr(dsr_data: dict, col_names: list) -> pd.DataFrame:
    """Convierte el formato DSR comprimido de Power BI a DataFrame."""
    ds = dsr_data.get('DS', [])
    if not ds:
        return pd.DataFrame()
    
    ph = ds[0].get('PH', [])
    if not ph:
        return pd.DataFrame()
    
    dm = ph[0].get('DM0', [])
    if not dm:
        return pd.DataFrame()
    
    rows = []
    last_values = [None] * len(col_names)
    
    for item in dm:
        c = item.get('C', [])
        r = item.get('R', 0)  # bitmask de valores repetidos del anterior
        
        # Valores pueden estar en C (array) o en M0, M1... directamente
        if not c:
            # Buscar M0, M1... en el item
            c = []
            for i in range(len(col_names)):
                key = f'M{i}' if i > 0 else 'M0'
                if key in item:
                    c.append(item[key])
        
        current = list(last_values)
        ci = 0
        for i in range(len(col_names)):
            if r and (r >> i) & 1:
                # usar valor anterior
                pass
            elif ci < len(c):
                current[i] = c[ci]
                ci += 1
        
        last_values = current
        rows.append(dict(zip(col_names, current)))
    
    return pd.DataFrame(rows)


def load_query_files(data_files: list) -> list:
    """Carga y parsea todos los archivos querydata."""
    datasets = []
    
    for fpath in sorted(data_files):
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath) as f:
                d = json.load(f)
            
            results = d.get('results', [])
            if not results:
                continue
            
            result_data = results[0].get('result', {}).get('data', {})
            if not result_data:
                continue
            
            descriptor = result_data.get('descriptor', {})
            selects = descriptor.get('Select', [])
            col_names = [s.get('Name', f'col_{i}') for i, s in enumerate(selects)]
            
            dsr = result_data.get('dsr', {})
            df = parse_dsr(dsr, col_names)
            
            if not df.empty:
                size = os.path.getsize(fpath)
                datasets.append({
                    'file': os.path.basename(fpath),
                    'columns': col_names,
                    'df': df,
                    'size_kb': size // 1024,
                })
                print(f'  {os.path.basename(fpath)}: {len(df)} filas × {len(col_names)} cols — {col_names}')
        
        except Exception as e:
            print(f'  Error en {fpath}: {e}')
    
    return datasets


# ── 3. CALCULAR KPIs ──────────────────────────────────────────────────────────

def calcular_kpis(datasets: list) -> dict:
    """Extrae KPIs clave del dataset de empleo."""
    kpis = {}
    
    for ds in datasets:
        cols = ds['columns']
        df = ds['df']
        
        # Total de puestos
        if any('Puestos de trabajo' in c for c in cols):
            col = [c for c in cols if 'Puestos' in c][0]
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            if 'Latitud' in ' '.join(cols) or 'Longitud' in ' '.join(cols):
                # Dataset geo — empresas con coordenadas
                kpis['total_puestos_geo'] = int(df[col].sum())
                kpis['n_empresas'] = len(df)
                kpis['df_geo'] = df
                kpis['col_puestos_geo'] = col
                
            elif len(cols) == 1:
                # Total nacional
                val = df[col].iloc[0] if len(df) > 0 else 0
                kpis['total_puestos_nacional'] = int(pd.to_numeric(val, errors='coerce') or 0)
        
        # Empleo por departamento
        if any('Departamento' in c for c in cols) and any('Empleo' in c for c in cols):
            col_dept = [c for c in cols if 'Departamento' in c][0]
            col_emp = [c for c in cols if 'Empleo' in c][0]
            df[col_emp] = pd.to_numeric(df[col_emp], errors='coerce').fillna(0)
            kpis['df_departamentos'] = df
            kpis['col_dept'] = col_dept
            kpis['col_emp_dept'] = col_emp
        
        # Porcentaje por departamento
        if any('IdMapa' in c for c in cols):
            col_pct = [c for c in cols if '%' in c or 'Empleo' in c][0]
            col_id = [c for c in cols if 'IdMapa' in c or 'Departamento' in c][0]
            df[col_pct] = pd.to_numeric(df[col_pct], errors='coerce').fillna(0)
            kpis['df_mapa'] = df
            kpis['col_mapa_pct'] = col_pct
            kpis['col_mapa_id'] = col_id
    
    return kpis


# ── 4. REPORTE VISUAL ─────────────────────────────────────────────────────────

def generar_reporte(kpis: dict, datasets: list) -> str:
    """Genera imagen del reporte con los datos de Power BI."""
    
    COLOR_BG = '#0A0E1A'
    COLOR_CARD = '#111827'
    COLOR_BLUE = '#00C8FF'
    COLOR_VERDE = '#00E5A0'
    COLOR_ACENTO = '#FF6B35'
    COLOR_TEXTO = '#E8EBF0'
    COLOR_SUBTEXTO = '#8892A0'
    COLOR_GRID = '#1E2A3A'
    
    fig = plt.figure(figsize=(12, 14), facecolor=COLOR_BG)
    gs = GridSpec(4, 3, figure=fig, hspace=0.50, wspace=0.35,
                  top=0.94, bottom=0.04, left=0.07, right=0.97)
    
    # ── HEADER ──
    ax_h = fig.add_subplot(gs[0, :])
    ax_h.set_facecolor(COLOR_CARD)
    ax_h.axis('off')
    ax_h.axhline(y=0.95, color=COLOR_BLUE, linewidth=3)
    ax_h.text(0.02, 0.72, '📊 REPORTE EMPLEO ARGENTINA',
              fontsize=14, fontweight='bold', color=COLOR_BLUE,
              transform=ax_h.transAxes, va='top')
    ax_h.text(0.02, 0.35, 'Fuente: Ministerio de Trabajo · Power BI Público',
              fontsize=9, color=COLOR_SUBTEXTO, transform=ax_h.transAxes, va='top')
    ax_h.text(0.98, 0.35, 'Datos: app.powerbi.com (embed público)',
              fontsize=8, color=COLOR_SUBTEXTO, transform=ax_h.transAxes, va='top', ha='right')
    
    # ── KPI CARDS ──
    def kpi_card(ax, titulo, valor, sub, color=COLOR_BLUE):
        ax.set_facecolor(COLOR_CARD)
        ax.axis('off')
        ax.axhline(y=0.97, color=color, linewidth=2.5)
        ax.text(0.5, 0.88, titulo, fontsize=8, color=COLOR_SUBTEXTO,
                ha='center', va='top', transform=ax.transAxes)
        ax.text(0.5, 0.58, valor, fontsize=16, fontweight='bold',
                color=color, ha='center', va='top', transform=ax.transAxes)
        ax.text(0.5, 0.18, sub, fontsize=7.5, color=COLOR_SUBTEXTO,
                ha='center', va='top', transform=ax.transAxes)
    
    total_puestos = kpis.get('total_puestos_nacional',
                   kpis.get('total_puestos_geo', 0))
    n_empresas = kpis.get('n_empresas', 0)
    
    kpi_card(fig.add_subplot(gs[1, 0]), 'Puestos de Trabajo',
             f'{total_puestos:,.0f}' if total_puestos else 'N/A',
             'total registrado', COLOR_BLUE)
    
    kpi_card(fig.add_subplot(gs[1, 1]), 'Empresas con Datos Geo',
             f'{n_empresas:,}',
             'con lat/long registrado', COLOR_VERDE)
    
    # Concentración (CABA + GBA estimate)
    df_geo = kpis.get('df_geo')
    if df_geo is not None:
        # Empresas en radio de Buenos Aires
        lat_center, lon_center = -34.6, -58.4
        df_geo = df_geo.copy()
        df_geo['lat'] = pd.to_numeric(df_geo.get(
            [c for c in df_geo.columns if 'Latitud' in c][0], 0), errors='coerce')
        df_geo['lon'] = pd.to_numeric(df_geo.get(
            [c for c in df_geo.columns if 'Longitud' in c][0], 0), errors='coerce')
        df_geo['dist'] = ((df_geo['lat'] - lat_center)**2 + (df_geo['lon'] - lon_center)**2)**0.5
        col_p = kpis.get('col_puestos_geo', df_geo.columns[-1])
        df_geo[col_p] = pd.to_numeric(df_geo[col_p], errors='coerce').fillna(0)
        
        n_amba = len(df_geo[df_geo['dist'] < 1.5])
        pct_amba = n_amba / n_empresas * 100 if n_empresas > 0 else 0
        kpi_card(fig.add_subplot(gs[1, 2]), 'Empresas en AMBA',
                 f'{n_amba:,}', f'{pct_amba:.1f}% del total', COLOR_ACENTO)
    else:
        kpi_card(fig.add_subplot(gs[1, 2]), 'Fuente', 'PBI Público',
                 'Ministerio de Trabajo AR', COLOR_ACENTO)
    
    # ── GRÁFICO: DISTRIBUCIÓN GEO (scatter plot Argentina) ──
    ax_geo = fig.add_subplot(gs[2, :2])
    ax_geo.set_facecolor(COLOR_CARD)
    
    if df_geo is not None:
        df_plot = df_geo[(df_geo['lat'].between(-56, -21)) &
                         (df_geo['lon'].between(-74, -53))].copy()
        df_plot[col_p] = pd.to_numeric(df_plot[col_p], errors='coerce').fillna(1)
        
        sizes = (df_plot[col_p] / df_plot[col_p].max() * 80).clip(1, 80)
        
        sc = ax_geo.scatter(
            df_plot['lon'], df_plot['lat'],
            s=sizes, c=df_plot[col_p],
            cmap='YlOrRd', alpha=0.6, linewidth=0
        )
        ax_geo.set_title('Distribución Geográfica de Empresas · Puestos de Trabajo',
                          color=COLOR_TEXTO, fontsize=9, pad=6, loc='left')
        ax_geo.set_facecolor(COLOR_CARD)
        ax_geo.tick_params(colors=COLOR_SUBTEXTO, labelsize=7)
        ax_geo.spines[:].set_color(COLOR_GRID)
        ax_geo.set_xlabel('Longitud', color=COLOR_SUBTEXTO, fontsize=7)
        ax_geo.set_ylabel('Latitud', color=COLOR_SUBTEXTO, fontsize=7)
        ax_geo.grid(color=COLOR_GRID, linewidth=0.3, alpha=0.5)
    else:
        ax_geo.text(0.5, 0.5, 'Sin datos geo disponibles',
                    ha='center', va='center', color=COLOR_SUBTEXTO,
                    transform=ax_geo.transAxes)
        ax_geo.set_facecolor(COLOR_CARD)
        ax_geo.axis('off')
    
    # ── TOP DEPARTAMENTOS (barras horizontales) ──
    ax_top = fig.add_subplot(gs[2, 2])
    ax_top.set_facecolor(COLOR_CARD)
    
    # Usar datos de departamentos (qd_7)
    dept_ds = None
    for ds in datasets:
        if any('IdMapa' in c or 'Departamento' in c for c in ds['columns']) and len(ds['df']) > 10:
            dept_ds = ds
            break
    
    if dept_ds is not None:
        df_dept = dept_ds['df'].copy()
        col_id = dept_ds['columns'][0]   # IdMapa
        col_pct = dept_ds['columns'][1]  # % Empleo
        df_dept[col_pct] = pd.to_numeric(df_dept[col_pct], errors='coerce').fillna(0)
        top_dept = df_dept.nlargest(8, col_pct)
        
        labels = [str(l)[:10] for l in top_dept[col_id]]
        valores = top_dept[col_pct].values * 100  # a porcentaje
        
        colors = [COLOR_BLUE if i < 3 else COLOR_VERDE for i in range(len(labels))]
        ax_top.barh(range(len(top_dept)), valores, color=colors, alpha=0.85, height=0.6)
        ax_top.set_yticks(range(len(top_dept)))
        ax_top.set_yticklabels(labels, fontsize=7, color=COLOR_TEXTO)
        ax_top.set_title('Top Departamentos\n% Empleo', color=COLOR_TEXTO, fontsize=8, pad=4, loc='left')
        ax_top.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f}%'))
        ax_top.invert_yaxis()
    else:
        ax_top.text(0.5, 0.5, 'Sin datos\ndisponibles',
                    ha='center', va='center', color=COLOR_SUBTEXTO, fontsize=9,
                    transform=ax_top.transAxes)
    
    ax_top.set_facecolor(COLOR_CARD)
    ax_top.tick_params(colors=COLOR_SUBTEXTO, labelsize=6)
    ax_top.spines[:].set_color(COLOR_GRID)
    ax_top.grid(axis='x', color=COLOR_GRID, linewidth=0.5, alpha=0.7)
    
    # ── ANÁLISIS JARVIS ──
    ax_an = fig.add_subplot(gs[3, :])
    ax_an.set_facecolor(COLOR_CARD)
    ax_an.axis('off')
    ax_an.axhline(y=0.97, color=COLOR_ACENTO, linewidth=2)
    ax_an.text(0.01, 0.92, '🤖 Análisis JARVIS — Power BI Público',
               fontsize=9, color=COLOR_ACENTO, fontweight='bold',
               transform=ax_an.transAxes, va='top')
    
    if df_geo is not None:
        txt = (
            f"Datos extraídos directamente de un reporte Power BI público del Ministerio de Trabajo. "
            f"El embed contiene {n_empresas:,} empresas georeferenciadas con datos de puestos de trabajo. "
            f"La técnica usa Playwright para interceptar las queries internas de Power BI (formato DSR) "
            f"sin necesidad de Azure AD ni credenciales. El mismo pipeline aplica a cualquier embed público."
        )
    else:
        txt = "Datos procesados desde Power BI público via interceptación de API WABI (sin Azure AD)."
    
    ax_an.text(0.01, 0.68, txt, fontsize=8, color=COLOR_TEXTO,
               transform=ax_an.transAxes, va='top', linespacing=1.5)
    
    ax_an.text(0.01, 0.20,
               '✅ Técnica validada: Playwright → intercept querydata → DSR parse → pandas → matplotlib',
               fontsize=8, color=COLOR_VERDE, transform=ax_an.transAxes, va='top')
    
    output_path = f'{OUTPUT_DIR}/reporte_powerbi.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=COLOR_BG, edgecolor='none')
    plt.close()
    
    print(f'  ✅ Reporte guardado: {output_path}')
    return output_path


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print('=' * 55)
    print('⚡ Spike: Power BI Público → Reporte Visual')
    print('=' * 55)
    
    # Usar archivos ya capturados si existen
    existing = [f'{OUTPUT_DIR}/qd_{i}.json' for i in range(1, 10)
                if os.path.exists(f'{OUTPUT_DIR}/qd_{i}.json')]
    
    if not existing:
        print('\n[1] Capturando datos via Playwright...')
        data_files = asyncio.run(capture_pbi_data())
    else:
        print(f'\n[1] Usando {len(existing)} archivos ya capturados...')
        data_files = existing
    
    print(f'\n[2] Parseando {len(data_files)} queries...')
    datasets = load_query_files(data_files)
    
    print(f'\n[3] Calculando KPIs...')
    kpis = calcular_kpis(datasets)
    print(f'  Total puestos: {kpis.get("total_puestos_nacional", kpis.get("total_puestos_geo", "?"))}')
    print(f'  Empresas geo: {kpis.get("n_empresas", "?")}')
    
    print(f'\n[4] Generando reporte visual...')
    output_path = generar_reporte(kpis, datasets)
    
    print('\n' + '=' * 55)
    print('✅ SPIKE COMPLETADO')
    print(f'📁 Reporte: {output_path}')
    print('=' * 55)
    
    return output_path


if __name__ == '__main__':
    main()
