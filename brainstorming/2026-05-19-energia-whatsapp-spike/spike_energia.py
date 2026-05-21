#!/usr/bin/env python3
"""
Spike: Datos Energéticos Argentina → LLM → Reporte Imagen → WhatsApp
Fuente: API datos.gob.ar - Secretaría de Energía
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as mticker
import numpy as np
import json
import os
import sys
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 1. CARGA Y PROCESAMIENTO DE DATOS ────────────────────────────────────────

def cargar_datos():
    print("📊 Cargando datos...")
    
    df_pet = pd.read_csv(
        os.path.join(DATA_DIR, "petroleo_por_empresa.csv"),
        encoding="utf-8-sig"
    )
    df_gas = pd.read_csv(
        os.path.join(DATA_DIR, "gas_por_empresa.csv"),
        encoding="utf-8-sig"
    )
    
    # Limpiar columnas
    df_pet.columns = df_pet.columns.str.strip()
    df_gas.columns = df_gas.columns.str.strip()
    
    # Parsear fecha
    df_pet['fecha'] = pd.to_datetime(df_pet['indice_tiempo'], errors='coerce')
    df_gas['fecha'] = pd.to_datetime(df_gas['indice_tiempo'], errors='coerce')
    
    # Columna de producción
    col_pet = [c for c in df_pet.columns if 'produccion' in c.lower()][0]
    col_gas = [c for c in df_gas.columns if 'produccion' in c.lower()][0]
    
    df_pet['produccion'] = pd.to_numeric(df_pet[col_pet], errors='coerce').fillna(0)
    df_gas['produccion'] = pd.to_numeric(df_gas[col_gas], errors='coerce').fillna(0)
    
    print(f"  Petróleo: {len(df_pet)} registros | {df_pet['fecha'].min().year} - {df_pet['fecha'].max().year}")
    print(f"  Gas: {len(df_gas)} registros | {df_gas['fecha'].min().year} - {df_gas['fecha'].max().year}")
    
    return df_pet, df_gas

def calcular_kpis(df_pet, df_gas):
    print("🔢 Calculando KPIs...")
    
    # Último mes "completo" (con >= 20 empresas reportando)
    counts_pet = df_pet.groupby('fecha').size()
    fecha_max = counts_pet[counts_pet >= 20].index.max()
    fecha_12m = fecha_max - pd.DateOffset(months=11)
    
    pet_12m = df_pet[df_pet['fecha'] >= fecha_12m]
    gas_12m = df_gas[df_gas['fecha'] >= fecha_12m]
    
    # Top empresas petróleo (últimos 12 meses)
    top_pet = (
        pet_12m.groupby('empresa')['produccion']
        .sum()
        .sort_values(ascending=False)
        .head(8)
    )
    
    # Top empresas gas (últimos 12 meses)
    top_gas = (
        gas_12m.groupby('empresa')['produccion']
        .sum()
        .sort_values(ascending=False)
        .head(8)
    )
    
    # Serie histórica YPF petróleo (mensual)
    ypf_pet = df_pet[df_pet['empresa'].str.contains('YPF', case=False, na=False)]
    ypf_pet_serie = ypf_pet.groupby('fecha')['produccion'].sum().sort_index()
    
    # Serie histórica YPF gas
    ypf_gas = df_gas[df_gas['empresa'].str.contains('YPF', case=False, na=False)]
    ypf_gas_serie = ypf_gas.groupby('fecha')['produccion'].sum().sort_index()
    
    # Total mercado últimos 12 meses
    total_pet_12m = pet_12m.groupby('fecha')['produccion'].sum()
    total_gas_12m = gas_12m.groupby('fecha')['produccion'].sum()
    
    # KPIs YPF
    ypf_pet_ultimo = ypf_pet_serie.iloc[-1] if len(ypf_pet_serie) > 0 else 0
    ypf_pet_anterior = ypf_pet_serie.iloc[-2] if len(ypf_pet_serie) > 1 else ypf_pet_ultimo
    var_pet = ((ypf_pet_ultimo - ypf_pet_anterior) / ypf_pet_anterior * 100) if ypf_pet_anterior > 0 else 0
    
    ypf_gas_ultimo = ypf_gas_serie.iloc[-1] if len(ypf_gas_serie) > 0 else 0
    ypf_gas_anterior = ypf_gas_serie.iloc[-2] if len(ypf_gas_serie) > 1 else ypf_gas_ultimo
    var_gas = ((ypf_gas_ultimo - ypf_gas_anterior) / ypf_gas_anterior * 100) if ypf_gas_anterior > 0 else 0
    
    # Market share YPF — sobre el último mes completo
    mes_exacto_pet = df_pet[df_pet['fecha'] == fecha_max]
    mes_exacto_gas = df_gas[df_gas['fecha'] == fecha_max]
    total_pet_mes = mes_exacto_pet['produccion'].sum()
    total_gas_mes = mes_exacto_gas['produccion'].sum()
    share_pet = (ypf_pet_ultimo / total_pet_mes * 100) if total_pet_mes > 0 else 0
    share_gas = (ypf_gas_ultimo / total_gas_mes * 100) if total_gas_mes > 0 else 0
    
    MESES_ES = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
        'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
        'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
        'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    mes_en = fecha_max.strftime("%B")
    ultimo_mes = f"{MESES_ES.get(mes_en, mes_en)} {fecha_max.year}"
    
    kpis = {
        "ultimo_mes": ultimo_mes,
        "fecha_max": fecha_max,
        "ypf_pet_m3_dia": round(ypf_pet_ultimo, 0),
        "ypf_pet_var_pct": round(var_pet, 1),
        "ypf_gas_mm3_dia": round(ypf_gas_ultimo / 1000, 1),  # a millones m3/día
        "ypf_gas_var_pct": round(var_gas, 1),
        "ypf_share_pet": round(share_pet, 1),
        "ypf_share_gas": round(share_gas, 1),
        "top_pet": top_pet,
        "top_gas": top_gas,
        "ypf_pet_serie": ypf_pet_serie,
        "ypf_gas_serie": ypf_gas_serie,
        "total_pet_12m": total_pet_12m,
        "total_gas_12m": total_gas_12m,
    }
    
    print(f"  Último mes: {ultimo_mes}")
    print(f"  YPF Petróleo: {ypf_pet_ultimo:,.0f} m³/día ({var_pet:+.1f}% vs mes ant.)")
    print(f"  YPF Gas: {ypf_gas_ultimo/1000:.1f} MM m³/día ({var_gas:+.1f}% vs mes ant.)")
    print(f"  Market share petróleo: {share_pet:.1f}%")
    print(f"  Market share gas: {share_gas:.1f}%")
    
    return kpis

# ── 2. GENERACIÓN DEL REPORTE VISUAL ─────────────────────────────────────────

def generar_reporte(kpis) -> str:
    print("🎨 Generando reporte visual...")
    
    # Paleta corporativa YPF-ish
    COLOR_BG = '#0A0E1A'
    COLOR_CARD = '#111827'
    COLOR_YPF = '#00C8FF'       # celeste YPF
    COLOR_ACENTO = '#FF6B35'    # naranja
    COLOR_VERDE = '#00E5A0'     # verde
    COLOR_TEXTO = '#E8EBF0'
    COLOR_SUBTEXTO = '#8892A0'
    COLOR_GRID = '#1E2A3A'
    COLOR_GAS = '#A78BFA'       # violeta para gas
    
    fig = plt.figure(figsize=(12, 16), facecolor=COLOR_BG)
    fig.patch.set_facecolor(COLOR_BG)
    
    gs = GridSpec(
        5, 3,
        figure=fig,
        hspace=0.50,
        wspace=0.35,
        top=0.95, bottom=0.04,
        left=0.07, right=0.97
    )
    
    # ── HEADER ──
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.set_facecolor(COLOR_CARD)
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)
    ax_header.axis('off')
    
    # Línea superior decorativa
    ax_header.axhline(y=0.95, color=COLOR_YPF, linewidth=3, alpha=0.8)
    
    ax_header.text(0.02, 0.72, '⚡ REPORTE ENERGÉTICO ARGENTINA',
                   fontsize=14, fontweight='bold', color=COLOR_YPF,
                   transform=ax_header.transAxes, va='top')
    ax_header.text(0.02, 0.35, 'Producción de Petróleo y Gas · Secretaría de Energía',
                   fontsize=9, color=COLOR_SUBTEXTO,
                   transform=ax_header.transAxes, va='top')
    ax_header.text(0.98, 0.72, f"📅 {kpis['ultimo_mes']}",
                   fontsize=10, color=COLOR_TEXTO,
                   transform=ax_header.transAxes, va='top', ha='right')
    ax_header.text(0.98, 0.35, 'Datos: datos.gob.ar',
                   fontsize=8, color=COLOR_SUBTEXTO,
                   transform=ax_header.transAxes, va='top', ha='right')
    
    # ── KPI CARDS (fila 1) ──
    def kpi_card(ax, titulo, valor, subtitulo, variacion=None, color_val=COLOR_YPF):
        ax.set_facecolor(COLOR_CARD)
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # Borde top
        ax.axhline(y=0.97, color=color_val, linewidth=2.5, alpha=0.9)
        
        ax.text(0.5, 0.88, titulo, fontsize=8, color=COLOR_SUBTEXTO,
                ha='center', va='top', transform=ax.transAxes)
        ax.text(0.5, 0.60, valor, fontsize=18, fontweight='bold',
                color=color_val, ha='center', va='top', transform=ax.transAxes)
        
        if variacion is not None:
            color_var = COLOR_VERDE if variacion >= 0 else COLOR_ACENTO
            signo = '▲' if variacion >= 0 else '▼'
            ax.text(0.5, 0.28, f'{signo} {abs(variacion):.1f}% vs mes ant.',
                    fontsize=8, color=color_var, ha='center', va='top',
                    transform=ax.transAxes)
        
        ax.text(0.5, 0.10, subtitulo, fontsize=7, color=COLOR_SUBTEXTO,
                ha='center', va='top', transform=ax.transAxes)
    
    ax_k1 = fig.add_subplot(gs[1, 0])
    kpi_card(ax_k1,
             'YPF · Petróleo',
             f"{kpis['ypf_pet_m3_dia']:,.0f}",
             'm³/día promedio',
             kpis['ypf_pet_var_pct'],
             COLOR_YPF)
    
    ax_k2 = fig.add_subplot(gs[1, 1])
    kpi_card(ax_k2,
             'YPF · Gas Natural',
             f"{kpis['ypf_gas_mm3_dia']:.1f}",
             'MM m³/día promedio',
             kpis['ypf_gas_var_pct'],
             COLOR_GAS)
    
    ax_k3 = fig.add_subplot(gs[1, 2])
    kpi_card(ax_k3,
             'Market Share YPF',
             f"{kpis['ypf_share_pet']:.0f}%",
             f"petróleo · {kpis['ypf_share_gas']:.0f}% gas",
             None,
             COLOR_VERDE)
    
    # ── SERIE HISTÓRICA YPF PETRÓLEO (fila 2 izq+centro) ──
    ax_serie_pet = fig.add_subplot(gs[2, :2])
    ax_serie_pet.set_facecolor(COLOR_CARD)
    
    serie = kpis['ypf_pet_serie'].iloc[-36:]  # últimos 3 años
    fechas = serie.index
    valores = serie.values
    
    ax_serie_pet.fill_between(fechas, valores, alpha=0.25, color=COLOR_YPF)
    ax_serie_pet.plot(fechas, valores, color=COLOR_YPF, linewidth=2, alpha=0.9)
    ax_serie_pet.scatter(fechas[-1:], valores[-1:], color=COLOR_YPF, s=60, zorder=5)
    
    ax_serie_pet.set_facecolor(COLOR_CARD)
    ax_serie_pet.tick_params(colors=COLOR_SUBTEXTO, labelsize=7)
    ax_serie_pet.spines[:].set_color(COLOR_GRID)
    ax_serie_pet.set_title('YPF — Producción Petróleo (últimos 3 años)',
                           color=COLOR_TEXTO, fontsize=9, pad=6, loc='left')
    ax_serie_pet.set_ylabel('m³/día', color=COLOR_SUBTEXTO, fontsize=7)
    ax_serie_pet.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}k'))
    ax_serie_pet.grid(axis='y', color=COLOR_GRID, linewidth=0.5, alpha=0.7)
    ax_serie_pet.set_xlim(fechas[0], fechas[-1])
    
    # ── TOP 5 EMPRESAS PETRÓLEO — BARRAS (fila 2 der) ──
    ax_top_pet = fig.add_subplot(gs[2, 2])
    ax_top_pet.set_facecolor(COLOR_CARD)
    
    top5_pet = kpis['top_pet'].head(5)
    empresas_short = [e[:18].replace(' S.A.','').replace(' S.R.L.','').strip()
                      for e in top5_pet.index]
    colores_bar = [COLOR_YPF if 'YPF' in e else COLOR_SUBTEXTO
                   for e in top5_pet.index]
    
    bars = ax_top_pet.barh(range(len(top5_pet)), top5_pet.values,
                            color=colores_bar, alpha=0.85, height=0.6)
    ax_top_pet.set_yticks(range(len(top5_pet)))
    ax_top_pet.set_yticklabels(empresas_short, fontsize=7, color=COLOR_TEXTO)
    ax_top_pet.set_title('Top 5 · Petróleo', color=COLOR_TEXTO, fontsize=9, pad=6, loc='left')
    ax_top_pet.set_facecolor(COLOR_CARD)
    ax_top_pet.tick_params(colors=COLOR_SUBTEXTO, labelsize=6)
    ax_top_pet.spines[:].set_color(COLOR_GRID)
    ax_top_pet.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
    ax_top_pet.grid(axis='x', color=COLOR_GRID, linewidth=0.5, alpha=0.7)
    ax_top_pet.invert_yaxis()
    
    # ── SERIE HISTÓRICA YPF GAS (fila 3 izq+centro) ──
    ax_serie_gas = fig.add_subplot(gs[3, :2])
    ax_serie_gas.set_facecolor(COLOR_CARD)
    
    serie_gas = kpis['ypf_gas_serie'].iloc[-36:]
    fechas_gas = serie_gas.index
    valores_gas = serie_gas.values
    
    ax_serie_gas.fill_between(fechas_gas, valores_gas, alpha=0.25, color=COLOR_GAS)
    ax_serie_gas.plot(fechas_gas, valores_gas, color=COLOR_GAS, linewidth=2, alpha=0.9)
    ax_serie_gas.scatter(fechas_gas[-1:], valores_gas[-1:], color=COLOR_GAS, s=60, zorder=5)
    
    ax_serie_gas.set_facecolor(COLOR_CARD)
    ax_serie_gas.tick_params(colors=COLOR_SUBTEXTO, labelsize=7)
    ax_serie_gas.spines[:].set_color(COLOR_GRID)
    ax_serie_gas.set_title('YPF — Producción Gas Natural (últimos 3 años)',
                           color=COLOR_TEXTO, fontsize=9, pad=6, loc='left')
    ax_serie_gas.set_ylabel('m³/día', color=COLOR_SUBTEXTO, fontsize=7)
    max_gas = max(valores_gas) if len(valores_gas) > 0 else 1
    if max_gas > 1e6:
        ax_serie_gas.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}MM'))
    else:
        ax_serie_gas.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}k'))
    ax_serie_gas.grid(axis='y', color=COLOR_GRID, linewidth=0.5, alpha=0.7)
    ax_serie_gas.set_xlim(fechas_gas[0], fechas_gas[-1])
    
    # ── TOP 5 EMPRESAS GAS (fila 3 der) ──
    ax_top_gas = fig.add_subplot(gs[3, 2])
    ax_top_gas.set_facecolor(COLOR_CARD)
    
    top5_gas = kpis['top_gas'].head(5)
    empresas_short_gas = [e[:18].replace(' S.A.','').replace(' S.R.L.','').strip()
                          for e in top5_gas.index]
    colores_bar_gas = [COLOR_GAS if 'YPF' in e else COLOR_SUBTEXTO
                       for e in top5_gas.index]
    
    ax_top_gas.barh(range(len(top5_gas)), top5_gas.values,
                    color=colores_bar_gas, alpha=0.85, height=0.6)
    ax_top_gas.set_yticks(range(len(top5_gas)))
    ax_top_gas.set_yticklabels(empresas_short_gas, fontsize=7, color=COLOR_TEXTO)
    ax_top_gas.set_title('Top 5 · Gas', color=COLOR_TEXTO, fontsize=9, pad=6, loc='left')
    ax_top_gas.set_facecolor(COLOR_CARD)
    ax_top_gas.tick_params(colors=COLOR_SUBTEXTO, labelsize=6)
    ax_top_gas.spines[:].set_color(COLOR_GRID)
    ax_top_gas.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}MM' if x >= 1e6 else f'{x/1000:.0f}k'))
    ax_top_gas.grid(axis='x', color=COLOR_GRID, linewidth=0.5, alpha=0.7)
    ax_top_gas.invert_yaxis()
    
    # ── ANÁLISIS LLM (fila 4) ──
    ax_analisis = fig.add_subplot(gs[4, :])
    ax_analisis.set_facecolor(COLOR_CARD)
    ax_analisis.axis('off')
    ax_analisis.set_xlim(0, 1)
    ax_analisis.set_ylim(0, 1)
    ax_analisis.axhline(y=0.97, color=COLOR_ACENTO, linewidth=2, alpha=0.8)
    ax_analisis.text(0.01, 0.92, '🤖 Análisis JARVIS',
                    fontsize=9, color=COLOR_ACENTO, fontweight='bold',
                    transform=ax_analisis.transAxes, va='top')
    
    # Texto del análisis (generado)
    analisis = generar_analisis_texto(kpis)
    ax_analisis.text(0.01, 0.72, analisis,
                    fontsize=8, color=COLOR_TEXTO,
                    transform=ax_analisis.transAxes, va='top',
                    wrap=True, linespacing=1.5)
    
    # Guardar
    output_path = os.path.join(OUTPUT_DIR, "reporte_energia.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=COLOR_BG, edgecolor='none')
    plt.close()
    
    print(f"  ✅ Reporte guardado: {output_path}")
    return output_path

# ── 3. ANÁLISIS LLM (template inteligente) ───────────────────────────────────

def generar_analisis_texto(kpis) -> str:
    """Genera análisis en lenguaje natural de los KPIs."""
    
    pet = kpis['ypf_pet_m3_dia']
    var_pet = kpis['ypf_pet_var_pct']
    gas = kpis['ypf_gas_mm3_dia']
    var_gas = kpis['ypf_gas_var_pct']
    share_pet = kpis['ypf_share_pet']
    share_gas = kpis['ypf_share_gas']
    mes = kpis['ultimo_mes']
    
    # Determinar tendencia petróleo
    if var_pet > 2:
        tend_pet = f"sube {var_pet:.1f}% — tendencia positiva"
    elif var_pet < -2:
        tend_pet = f"baja {abs(var_pet):.1f}% — atención, revisar causas"
    else:
        tend_pet = f"estable ({var_pet:+.1f}%)"
    
    # Determinar tendencia gas
    if var_gas > 2:
        tend_gas = f"sube {var_gas:.1f}%"
    elif var_gas < -2:
        tend_gas = f"baja {abs(var_gas):.1f}%"
    else:
        tend_gas = f"estable ({var_gas:+.1f}%)"
    
    # Top competidor
    top_competidor = kpis['top_pet'].index[1] if len(kpis['top_pet']) > 1 else "N/A"
    top_competidor_short = top_competidor[:25].replace(' S.A.','').strip()
    top_comp_val = kpis['top_pet'].iloc[1] if len(kpis['top_pet']) > 1 else 0
    brecha = ((kpis['top_pet'].iloc[0] - top_comp_val) / top_comp_val * 100) if top_comp_val > 0 else 0
    
    texto = (
        f"En {mes}, YPF produce {pet:,.0f} m³/día de petróleo ({tend_pet}) y {gas:.1f} MM m³/día de gas ({tend_gas}). "
        f"Mantiene el liderazgo del mercado con {share_pet:.0f}% del petróleo y {share_gas:.0f}% del gas nacional. "
        f"La brecha con {top_competidor_short}, el segundo productor, es de {brecha:.0f}% en petróleo."
    )
    
    return texto

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("⚡ Spike: Datos Energéticos → Reporte Visual")
    print("=" * 55)
    
    df_pet, df_gas = cargar_datos()
    kpis = calcular_kpis(df_pet, df_gas)
    output_path = generar_reporte(kpis)
    
    print("\n" + "=" * 55)
    print(f"✅ SPIKE COMPLETADO")
    print(f"📁 Reporte: {output_path}")
    print("=" * 55)
    
    # Imprimir resumen para WhatsApp
    print("\n📱 RESUMEN PARA WHATSAPP:")
    print(f"⚡ *Reporte Energético Argentina — {kpis['ultimo_mes']}*")
    print(f"")
    print(f"🛢️ *YPF Petróleo:* {kpis['ypf_pet_m3_dia']:,.0f} m³/día")
    signo_pet = "▲" if kpis['ypf_pet_var_pct'] >= 0 else "▼"
    print(f"   {signo_pet} {abs(kpis['ypf_pet_var_pct']):.1f}% vs mes anterior")
    print(f"")
    print(f"💨 *YPF Gas:* {kpis['ypf_gas_mm3_dia']:.1f} MM m³/día")
    signo_gas = "▲" if kpis['ypf_gas_var_pct'] >= 0 else "▼"
    print(f"   {signo_gas} {abs(kpis['ypf_gas_var_pct']):.1f}% vs mes anterior")
    print(f"")
    print(f"📊 *Market Share:* {kpis['ypf_share_pet']:.0f}% petróleo · {kpis['ypf_share_gas']:.0f}% gas")
    print(f"")
    print(f"_Fuente: Secretaría de Energía Argentina_")
    
    return output_path

if __name__ == "__main__":
    main()
