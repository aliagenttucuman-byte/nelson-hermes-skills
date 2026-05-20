#!/usr/bin/env python3
"""
Template: Reporte de Datos Energéticos Argentina → PNG
Fuente: API datos.gob.ar - Secretaría de Energía

USO:
  python3 reporte_energia.py

QUIRKS:
  - datos.gob.ar tiene SSL roto → wget --no-check-certificate
  - Último mes siempre incompleto → usar counts >= 20 para fecha_max
  - Encoding UTF-8 con BOM → utf-8-sig
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Paleta dark mode
COLOR_BG      = '#0A0E1A'
COLOR_CARD    = '#111827'
COLOR_YPF     = '#00C8FF'   # cian
COLOR_GAS     = '#A78BFA'   # violeta
COLOR_VERDE   = '#00E5A0'
COLOR_ACENTO  = '#FF6B35'
COLOR_TEXTO   = '#E8EBF0'
COLOR_SUBTEX  = '#8892A0'
COLOR_GRID    = '#1E2A3A'

MESES_ES = {
    'January':'Enero','February':'Febrero','March':'Marzo','April':'Abril',
    'May':'Mayo','June':'Junio','July':'Julio','August':'Agosto',
    'September':'Septiembre','October':'Octubre','November':'Noviembre','December':'Diciembre'
}

URLS = {
    "petroleo": "https://datos.energia.gob.ar/dataset/590d1284-fd6d-4686-afd8-b3da5d90a6e9/resource/2c1f455e-0103-4d51-8f94-a49c939ac0a1/download/produccin-de-petrleo-promedio-diaria-por-empresa.csv",
    "gas":      "https://datos.energia.gob.ar/dataset/590d1284-fd6d-4686-afd8-b3da5d90a6e9/resource/419094dd-2905-4ac3-9398-e81513013e5e/download/produccin-de-gas-promedio-diaria-por-empresa.csv",
}


def descargar_datos():
    import subprocess
    for nombre, url in URLS.items():
        out = os.path.join(DATA_DIR, f"{nombre}_por_empresa.csv")
        if not os.path.exists(out):
            print(f"  Descargando {nombre}...")
            subprocess.run(
                ["wget", "--no-check-certificate", "--timeout=30", "-q", "-O", out, url],
                check=True
            )


def cargar_df(nombre):
    path = os.path.join(DATA_DIR, f"{nombre}_por_empresa.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df['fecha'] = pd.to_datetime(df['indice_tiempo'], errors='coerce')
    col = [c for c in df.columns if 'produccion' in c.lower()][0]
    df['produccion'] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df


def ultima_fecha_completa(df, umbral=20):
    """Último mes con >= umbral empresas reportando (el más reciente siempre está incompleto)."""
    counts = df.groupby('fecha').size()
    return counts[counts >= umbral].index.max()


def calcular_kpis(df_pet, df_gas):
    fecha_max = ultima_fecha_completa(df_pet)
    fecha_12m = fecha_max - pd.DateOffset(months=11)

    def serie_empresa(df, empresa_substr):
        return df[df['empresa'].str.contains(empresa_substr, case=False, na=False)] \
                 .groupby('fecha')['produccion'].sum().sort_index()

    def top5(df, desde):
        return df[df['fecha'] >= desde].groupby('empresa')['produccion'] \
                 .sum().sort_values(ascending=False).head(5)

    def var_pct(serie):
        if len(serie) >= 2 and serie.iloc[-2] > 0:
            return (serie.iloc[-1] - serie.iloc[-2]) / serie.iloc[-2] * 100
        return 0.0

    ypf_pet = serie_empresa(df_pet, 'YPF')
    ypf_gas = serie_empresa(df_gas, 'YPF')

    mes_pet  = df_pet[df_pet['fecha'] == fecha_max]['produccion'].sum()
    mes_gas  = df_gas[df_gas['fecha'] == fecha_max]['produccion'].sum()

    mes_en = fecha_max.strftime("%B")
    return {
        "ultimo_mes":    f"{MESES_ES.get(mes_en, mes_en)} {fecha_max.year}",
        "fecha_max":     fecha_max,
        "ypf_pet_m3":    round(ypf_pet.iloc[-1], 0),
        "ypf_pet_var":   round(var_pct(ypf_pet), 1),
        "ypf_gas_mm3":   round(ypf_gas.iloc[-1] / 1_000_000, 2),
        "ypf_gas_var":   round(var_pct(ypf_gas), 1),
        "share_pet":     round(ypf_pet.iloc[-1] / mes_pet * 100, 1) if mes_pet > 0 else 0,
        "share_gas":     round(ypf_gas.iloc[-1] / mes_gas * 100, 1) if mes_gas > 0 else 0,
        "top5_pet":      top5(df_pet, fecha_max - pd.DateOffset(months=11)),
        "top5_gas":      top5(df_gas, fecha_max - pd.DateOffset(months=11)),
        "serie_pet":     ypf_pet.iloc[-36:],
        "serie_gas":     ypf_gas.iloc[-36:],
    }


def escala_formatter(valores):
    """Detecta escala automáticamente para evitar bug '0MM'."""
    max_v = max(abs(v) for v in valores if v == v) if len(valores) else 1
    if max_v >= 1e6:
        return mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}MM')
    elif max_v >= 1e3:
        return mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}k')
    else:
        return mticker.FuncFormatter(lambda x, _: f'{x:.0f}')


def kpi_card(ax, titulo, valor, subtitulo, variacion=None, color=COLOR_YPF):
    ax.set_facecolor(COLOR_CARD); ax.axis('off')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axhline(y=0.97, color=color, linewidth=2.5)
    ax.text(0.5, 0.88, titulo,  fontsize=8, color=COLOR_SUBTEX, ha='center', va='top', transform=ax.transAxes)
    ax.text(0.5, 0.60, valor,   fontsize=18, fontweight='bold', color=color, ha='center', va='top', transform=ax.transAxes)
    if variacion is not None:
        col_v = COLOR_VERDE if variacion >= 0 else COLOR_ACENTO
        signo = '▲' if variacion >= 0 else '▼'
        ax.text(0.5, 0.28, f'{signo} {abs(variacion):.1f}% vs mes ant.', fontsize=8, color=col_v,
                ha='center', va='top', transform=ax.transAxes)
    ax.text(0.5, 0.10, subtitulo, fontsize=7, color=COLOR_SUBTEX, ha='center', va='top', transform=ax.transAxes)


def generar_reporte(kpis) -> str:
    fig = plt.figure(figsize=(12, 16), facecolor=COLOR_BG)
    gs  = GridSpec(5, 3, figure=fig, hspace=0.50, wspace=0.35,
                   top=0.95, bottom=0.04, left=0.07, right=0.97)

    # ── Header
    ax_h = fig.add_subplot(gs[0, :])
    ax_h.set_facecolor(COLOR_CARD); ax_h.axis('off'); ax_h.set_xlim(0,1); ax_h.set_ylim(0,1)
    ax_h.axhline(y=0.95, color=COLOR_YPF, linewidth=3)
    ax_h.text(0.02, 0.72, 'REPORTE ENERGETICO ARGENTINA', fontsize=14, fontweight='bold',
              color=COLOR_YPF, transform=ax_h.transAxes, va='top')
    ax_h.text(0.02, 0.35, 'Produccion de Petroleo y Gas  Secretaria de Energia',
              fontsize=9, color=COLOR_SUBTEX, transform=ax_h.transAxes, va='top')
    ax_h.text(0.98, 0.72, kpis['ultimo_mes'], fontsize=10, color=COLOR_TEXTO,
              transform=ax_h.transAxes, va='top', ha='right')
    ax_h.text(0.98, 0.35, 'Fuente: datos.gob.ar', fontsize=8, color=COLOR_SUBTEX,
              transform=ax_h.transAxes, va='top', ha='right')

    # ── KPI cards
    kpi_card(fig.add_subplot(gs[1, 0]), 'YPF · Petroleo',
             f"{kpis['ypf_pet_m3']:,.0f}", 'm3/dia promedio', kpis['ypf_pet_var'], COLOR_YPF)
    kpi_card(fig.add_subplot(gs[1, 1]), 'YPF · Gas Natural',
             f"{kpis['ypf_gas_mm3']:.2f}", 'MM m3/dia promedio', kpis['ypf_gas_var'], COLOR_GAS)
    kpi_card(fig.add_subplot(gs[1, 2]), 'Market Share YPF',
             f"{kpis['share_pet']:.0f}%", f"petroleo  {kpis['share_gas']:.0f}% gas", None, COLOR_VERDE)

    def plot_serie(ax, serie, color, titulo):
        ax.set_facecolor(COLOR_CARD)
        f, v = serie.index, serie.values
        ax.fill_between(f, v, alpha=0.25, color=color)
        ax.plot(f, v, color=color, linewidth=2)
        ax.scatter(f[-1:], v[-1:], color=color, s=60, zorder=5)
        ax.tick_params(colors=COLOR_SUBTEX, labelsize=7)
        [s.set_color(COLOR_GRID) for s in ax.spines.values()]
        ax.set_title(titulo, color=COLOR_TEXTO, fontsize=9, pad=6, loc='left')
        ax.yaxis.set_major_formatter(escala_formatter(v))
        ax.grid(axis='y', color=COLOR_GRID, linewidth=0.5, alpha=0.7)
        ax.set_xlim(f[0], f[-1])
        ax.tick_params(axis='y', colors=COLOR_SUBTEX)

    def plot_top5(ax, top5, color_match, titulo):
        ax.set_facecolor(COLOR_CARD)
        empresas = [e[:18].replace(' S.A.','').replace(' S.R.L.','').strip() for e in top5.index]
        colores  = [color_match if 'YPF' in e else COLOR_SUBTEX for e in top5.index]
        ax.barh(range(len(top5)), top5.values, color=colores, alpha=0.85, height=0.6)
        ax.set_yticks(range(len(top5))); ax.set_yticklabels(empresas, fontsize=7, color=COLOR_TEXTO)
        ax.set_title(titulo, color=COLOR_TEXTO, fontsize=9, pad=6, loc='left')
        ax.tick_params(colors=COLOR_SUBTEX, labelsize=6)
        [s.set_color(COLOR_GRID) for s in ax.spines.values()]
        ax.xaxis.set_major_formatter(escala_formatter(top5.values))
        ax.grid(axis='x', color=COLOR_GRID, linewidth=0.5, alpha=0.7)
        ax.invert_yaxis()

    plot_serie(fig.add_subplot(gs[2, :2]), kpis['serie_pet'], COLOR_YPF,
               'YPF — Produccion Petroleo (ultimos 3 anos)')
    plot_top5(fig.add_subplot(gs[2, 2]),  kpis['top5_pet'],  COLOR_YPF,  'Top 5 · Petroleo')
    plot_serie(fig.add_subplot(gs[3, :2]), kpis['serie_gas'], COLOR_GAS,
               'YPF — Produccion Gas Natural (ultimos 3 anos)')
    plot_top5(fig.add_subplot(gs[3, 2]),  kpis['top5_gas'],  COLOR_GAS,  'Top 5 · Gas')

    # ── Análisis
    ax_a = fig.add_subplot(gs[4, :])
    ax_a.set_facecolor(COLOR_CARD); ax_a.axis('off'); ax_a.set_xlim(0,1); ax_a.set_ylim(0,1)
    ax_a.axhline(y=0.97, color=COLOR_ACENTO, linewidth=2)
    ax_a.text(0.01, 0.92, 'Analisis JARVIS', fontsize=9, color=COLOR_ACENTO,
              fontweight='bold', transform=ax_a.transAxes, va='top')
    p, g = kpis['ypf_pet_m3'], kpis['ypf_gas_mm3']
    vp, vg = kpis['ypf_pet_var'], kpis['ypf_gas_var']
    sp, sg = kpis['share_pet'], kpis['share_gas']
    txt = (f"En {kpis['ultimo_mes']}, YPF produce {p:,.0f} m3/dia de petroleo "
           f"({'sube' if vp>=0 else 'baja'} {abs(vp):.1f}%) y {g:.2f} MM m3/dia de gas "
           f"({'sube' if vg>=0 else 'baja'} {abs(vg):.1f}%). "
           f"Market share: {sp:.0f}% del petroleo y {sg:.0f}% del gas nacional.")
    ax_a.text(0.01, 0.70, txt, fontsize=8, color=COLOR_TEXTO,
              transform=ax_a.transAxes, va='top', linespacing=1.5)

    out = os.path.join(OUTPUT_DIR, "reporte_energia.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=COLOR_BG, edgecolor='none')
    plt.close()
    return out


if __name__ == "__main__":
    descargar_datos()
    df_pet = cargar_df("petroleo")
    df_gas = cargar_df("gas")
    kpis   = calcular_kpis(df_pet, df_gas)
    path   = generar_reporte(kpis)
    print(f"Reporte: {path}")
    print(f"YPF Petroleo: {kpis['ypf_pet_m3']:,.0f} m3/dia ({kpis['ypf_pet_var']:+.1f}%)")
    print(f"YPF Gas:      {kpis['ypf_gas_mm3']:.2f} MM m3/dia ({kpis['ypf_gas_var']:+.1f}%)")
    print(f"Share:        {kpis['share_pet']:.0f}% petroleo, {kpis['share_gas']:.0f}% gas")
