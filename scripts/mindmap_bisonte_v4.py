"""
mindmap_bisonte_v4.py
Genera el mapa mental de la propuesta Bisonte — AlegentAI
5 sucursales | USD 62.400 | Playwright → PNG
"""

import sys
import os

# Asegurar que el directorio de scripts esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from mindmap_html_generator import render_mindmap

# ── Config completo Bisonte ──────────────────────────────────────────────────

config = {
    "title": "Sistema Integral",
    "subtitle": "AlegentAI × Bisonte",
    "center_color": "#1B4F72",
    "bg_color": "#FAF8F5",
    "sections": {
        "top": {
            "color": "#2E8B6E", "light": "#E8F5F0",
            "title": "Modalidades de Contratación",
            "children": [
                {
                    "title": "Opción A — Propietario", "icon": "🔒",
                    "items": [
                        "USD 62.400 total en fases",
                        "30% anticipo + 70% entrega",
                        "Código fuente propio",
                        "Sin costos recurrentes",
                    ]
                },
                {
                    "title": "Opción B — SaaS", "icon": "☁️",
                    "items": [
                        "USD 5.200 / mes",
                        "Contrato mínimo 12 meses",
                        "Actualizaciones incluidas",
                        "Infraestructura en nube",
                    ]
                },
            ]
        },
        "left": {
            "color": "#D94F3D", "light": "#FDECEA",
            "title": "3 Líneas de Trabajo",
            "children": [
                {
                    "title": "L1 — Procesos Excel", "icon": "📊",
                    "items": [
                        "~15 procesos | 5 sucursales",
                        "1.000 hs | USD 30.000",
                        "1–2 procesos / mes",
                    ]
                },
                {
                    "title": "L2 — Auditoría de Flota", "icon": "🚛",
                    "items": [
                        "600 hs | USD 18.000",
                        "Multi-sucursal centralizado",
                        "Alertas preventivas",
                    ]
                },
                {
                    "title": "L3 — Sitrack Tiempo Real", "icon": "📍",
                    "items": [
                        "480 hs | USD 14.400",
                        "Mapa + posición + velocidad",
                        "5 sedes en tiempo real",
                    ]
                },
            ]
        },
        "right": {
            "color": "#2E8B6E", "light": "#E8F5F0",
            "title": "ROI — 3 años",
            "children": [
                {
                    "title": "Inversión total (Op. A)", "icon": "💰",
                    "items": [
                        "USD 62.400 único pago",
                        "Break-even: ~16 meses",
                        "Año 3: +USD 332.700 vs no automatizar",
                    ]
                },
                {
                    "title": "Costo de NO automatizar", "icon": "📉",
                    "items": [
                        "USD 409.500 en 3 años",
                        "1.820 hs/año de la gerente",
                        "Retorno: +533%",
                    ]
                },
            ]
        },
        "bottom_right": {
            "color": "#7A6A52", "light": "#F5F0E8",
            "title": "Consideraciones",
            "children": [
                {
                    "title": "Fuentes de Datos", "icon": "📁",
                    "items": [
                        "Transoft + Sitrack (Excel)",
                        "Sin integración API directa",
                        "Alcance L1 en relevamiento",
                    ]
                },
                {
                    "title": "Cobertura", "icon": "📍",
                    "items": [
                        "5 sucursales",
                        "Tucumán · BsAs · Salta",
                        "Jujuy · Rosario",
                    ]
                },
            ]
        },
    },
    "timeline": {
        "color": "#2E8B6E",
        "stages": [
            ("1", "Relevamiento", "Inicial"),
            ("2", "Desarrollo",   "Módulos 1-2/mes"),
            ("3", "Integración",  "Multi-sede"),
            ("4", "Pruebas y",    "Capacitación"),
            ("5", "Soporte",      "Post-impl."),
        ]
    }
}

# ── Generar ──────────────────────────────────────────────────────────────────

OUTPUT_PATH = "/tmp/bisonte-mindmap-v4.png"

if __name__ == "__main__":
    result = render_mindmap(config, OUTPUT_PATH)
    size_kb = os.path.getsize(result) / 1024
    print(f"\n✅ PNG listo: {result}")
    print(f"   Tamaño: {size_kb:.1f} KB")
