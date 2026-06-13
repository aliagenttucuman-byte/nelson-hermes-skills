#!/usr/bin/env python3
"""
Script: generate-dashboard-histograms.py
Skill: nelson-data-viz
Genera un dashboard con 3 histogramas estilo Nelson (métricas de sistema).
Uso: python3 generate-dashboard-histograms.py [--output-dir /tmp/histograms]
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import argparse


def main(output_dir: str = "/home/server/tmp/histograms"):
    os.makedirs(output_dir, exist_ok=True)

    # Configurar estilo dark Nelson
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams['font.size'] = 10

    # Generar datos simulados
    np.random.seed(42)

    api_response_times = np.random.gamma(shape=2, scale=50, size=5000) + 100
    product_prices = np.random.lognormal(mean=3.5, sigma=0.6, size=3000)
    user_ages = np.concatenate([
        np.random.normal(25, 5, 1500),
        np.random.normal(45, 8, 1000),
        np.random.normal(65, 6, 500)
    ])
    user_ages = np.clip(user_ages, 18, 90)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    fig.suptitle('Dashboard de Histogramas - Métricas del Sistema',
                 fontsize=14, fontweight='bold', y=1.02)

    # 1. Tiempos de respuesta API
    axes[0].hist(api_response_times, bins=50, color='#3b82f6',
                 edgecolor='white', alpha=0.85)
    axes[0].axvline(np.median(api_response_times), color='#ef4444',
                    linestyle='--', linewidth=2,
                    label=f'Mediana: {np.median(api_response_times):.0f}ms')
    axes[0].axvline(np.percentile(api_response_times, 95), color='#f59e0b',
                    linestyle=':', linewidth=2,
                    label=f'P95: {np.percentile(api_response_times, 95):.0f}ms')
    axes[0].set_title('Tiempos de Respuesta API', fontweight='bold')
    axes[0].set_xlabel('Tiempo (ms)')
    axes[0].set_ylabel('Frecuencia')
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    # 2. Precios de productos
    axes[1].hist(product_prices, bins=40, color='#10b981',
                 edgecolor='white', alpha=0.85)
    axes[1].axvline(np.median(product_prices), color='#ef4444',
                    linestyle='--', linewidth=2,
                    label=f'Mediana: ${np.median(product_prices):.0f}')
    axes[1].set_title('Distribución de Precios', fontweight='bold')
    axes[1].set_xlabel('Precio ($)')
    axes[1].set_ylabel('Frecuencia')
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)

    # 3. Edades de usuarios
    axes[2].hist(user_ages, bins=30, color='#8b5cf6',
                 edgecolor='white', alpha=0.85)
    axes[2].axvline(np.median(user_ages), color='#ef4444',
                    linestyle='--', linewidth=2,
                    label=f'Mediana: {np.median(user_ages):.0f}años')
    axes[2].set_title('Edades de Usuarios', fontweight='bold')
    axes[2].set_xlabel('Edad (años)')
    axes[2].set_ylabel('Frecuencia')
    axes[2].legend(fontsize=8)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = os.path.join(output_dir, "ejemplo_histogramas.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Imagen guardada en: {output_path}")
    print(f"Tamaño: {os.path.getsize(output_path)} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="/home/server/tmp/histograms")
    args = parser.parse_args()
    main(args.output_dir)
