---
name: nelson-data-viz
description: Visualización de datos para el equipo Nelson. Histogramas, distribuciones, gráficos estáticos e interactivos con matplotlib, seaborn y plotly.
title: Visualización de Datos - Histogramas, Gráficos y Dashboards
skill: nelson-data-viz
author: equipo-nelson
version: 1.0.0
keywords: [matplotlib, seaborn, plotly, histogram, chart, dashboard, data-viz, analytics]
dependencies: [nelson-data-science]
---

# Visualización de Datos - Equipo Nelson

> Skills de visualización para análisis, dashboards y reporting. Python-first, 100% local.

## Stack

| Librería | Uso | Instalación |
|----------|-----|-------------|
| **matplotlib** | Gráficos estáticos, publicaciones, PDFs | `pip install matplotlib` |
| **seaborn** | Estadística visual, heatmaps, distribuciones | `pip install seaborn` |
| **plotly** | Gráficos interactivos, HTML, dashboards | `pip install plotly` |
| **pandas** | Manipulación de datos previa | ya incluido en nelson-data-science |

## Patrones de Uso

### 1. Histograma Básico (matplotlib)

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_histogram(data, title, xlabel, bins=50, color='#3b82f6'):
    plt.figure(figsize=(8, 4))
    plt.hist(data, bins=bins, color=color, edgecolor='white', alpha=0.85)
    plt.title(title, fontweight='bold')
    plt.xlabel(xlabel)
    plt.ylabel('Frecuencia')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    return plt.gcf()
```

### 2. Histograma con Estadísticas (seaborn)

```python
import seaborn as sns
import matplotlib.pyplot as plt

def plot_distribution(data, title, xlabel):
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(8, 4))
    
    sns.histplot(data, bins=50, kde=True, color='#3b82f6', ax=ax)
    ax.axvline(np.median(data), color='#ef4444', linestyle='--', label=f'Mediana: {np.median(data):.1f}')
    ax.axvline(np.percentile(data, 95), color='#f59e0b', linestyle=':', label=f'P95: {np.percentile(data, 95):.1f}')
    
    ax.set_title(title, fontweight='bold')
    ax.set_xlabel(xlabel)
    ax.legend()
    plt.tight_layout()
    return fig
```

### 3. Múltiples Histogramas (dashboard estilo)

```python
def plot_multi_histogram(datasets, titles, xlabels, figsize=(14, 4.5)):
    """
    datasets: lista de arrays
    titles: lista de strings
    xlabels: lista de strings
    """
    n = len(datasets)
    fig, axes = plt.subplots(1, n, figsize=figsize)
    colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444']
    
    for i, (data, title, xlabel) in enumerate(zip(datasets, titles, xlabels)):
        ax = axes[i] if n > 1 else axes
        ax.hist(data, bins=50, color=colors[i % len(colors)], edgecolor='white', alpha=0.85)
        ax.axvline(np.median(data), color='#ef4444', linestyle='--', linewidth=2, label=f'Mediana: {np.median(data):.1f}')
        ax.set_title(title, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Frecuencia')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
```

### 4. Guardar y Servir como Imagen

```python
import os

def save_chart(fig, filename, dpi=150, output_dir="/home/server/tmp/histograms"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path
```

### 5. Integración con FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/metrics/histogram")
def get_histogram(metric: str, days: int = 7):
    # Cargar datos
    data = load_metric_data(metric, days)
    
    # Generar gráfico
    fig = plot_distribution(data, f"{metric} - Últimos {days} días", metric)
    path = save_chart(fig, f"{metric}_{days}d.png")
    
    return FileResponse(path)
```

## Dependencias

```toml
# pyproject.toml
"matplotlib>=3.8",
"seaborn>=0.13",
"plotly>=5.18",
"numpy>=1.26",
```

## Checklist

- [ ] Datos limpios (sin NaN) antes de graficar
- [ ] Bins apropiados para el tamaño de muestra (regla de Sturges: `1 + 3.322 * log10(n)`)
- [ ] Líneas de referencia (mediana, media, percentiles) cuando aportan valor
- [ ] Leyendas claras y tamaño de fuente legible
- [ ] Grid sutil para facilitar lectura
- [ ] Tamaño de figura apropiado para el medio (web vs PDF vs presentación)
- [ ] Colores accesibles (WCAG contrast)

## Pitfalls

- `plt.show()` bloquea en servidores sin display. Usar `savefig()` y servir archivos.
- Memory leak: siempre cerrar figuras con `plt.close()` o usar context managers.
- Seaborn modifica estilos globales. Restaurar con `plt.style.use('default')` si se comparte proceso.
- Bins muy finos: ruido visual. Bins muy gruesos: pérdida de información.
