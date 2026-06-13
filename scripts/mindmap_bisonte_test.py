#!/usr/bin/env python3
"""
mindmap_bisonte_test.py
Generates the updated AlegentAI × Bisonte mind map infographic.
Output: /tmp/bisonte-mindmap-v3.png
"""

import sys
import os

# Allow running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mindmap_generator import generate_mindmap

config = {
    "title": "Sistema Integral\nAlegentAI × Bisonte",
    "title_subtitle": None,

    "sections": [

        # ── TOP — Modalidades de Contratación (verde) ──────────────────────
        {
            "id": "top",
            "position": "top",
            "color": "#2E8B6E",
            "color_light": "#E8F5F0",
            "icon": "📋",
            "title": "Modalidades de Contratación",
            "nodes": [
                {
                    "title": "Opción A: Sistema Propietario",
                    "icon": "🔒",
                    "items": [
                        "USD 62.400 total en fases",
                        "Pago: 30% anticipo + 70% entrega",
                        "Código fuente propio del cliente",
                        "Sin costos recurrentes tras entrega",
                    ]
                },
                {
                    "title": "Opción B: SaaS",
                    "icon": "☁️",
                    "items": [
                        "USD 5.200 / mes",
                        "Contrato: Mínimo 12 meses",
                        "Actualizaciones y soporte incluido",
                        "Infraestructura en la nube",
                    ]
                },
            ]
        },

        # ── LEFT — 3 Líneas de Trabajo (coral) ────────────────────────────
        {
            "id": "left",
            "position": "left",
            "color": "#E05A4E",
            "color_light": "#FDECEA",
            "icon": "⚙️",
            "title": "3 Líneas de Trabajo",
            "nodes": [
                {
                    "title": "L1 — Procesos Excel",
                    "icon": "📊",
                    "items": [
                        "~15 procesos identificados",
                        "5 sucursales alcanzadas",
                        "Frecuencia: 1-2 procesos/mes",
                        "USD 30.000 — 900 hs estimadas",
                    ]
                },
                {
                    "title": "L2 — Auditoría de Flota",
                    "icon": "🚛",
                    "items": [
                        "600 hs estimadas",
                        "Cobertura multi-sucursal",
                        "USD 18.000",
                    ]
                },
                {
                    "title": "L3 — Sitrack Tiempo Real",
                    "icon": "📡",
                    "items": [
                        "480 hs estimadas",
                        "5 sedes integradas",
                        "USD 14.400",
                    ]
                },
            ]
        },

        # ── RIGHT — ROI 3 años (verde) ──────────────────────────────────────
        {
            "id": "right",
            "position": "right",
            "color": "#2E8B6E",
            "color_light": "#E8F5F0",
            "icon": "📈",
            "title": "ROI — 3 años",
            "nodes": [
                {
                    "title": "Inversión (Opción A)",
                    "icon": "💰",
                    "items": [
                        "Total: USD 62.400",
                        "Break-even: ~16 meses",
                    ]
                },
                {
                    "title": "Sin automatización — 3 años",
                    "icon": "📉",
                    "items": [
                        "Costo estimado: USD 409.500",
                        "Diferencia vs inversión: USD 332.700",
                        "Retorno: +533% sobre inversión",
                    ]
                },
            ]
        },

        # ── BOTTOM-RIGHT — Consideraciones (beige/gris) ────────────────────
        {
            "id": "bottom-right",
            "position": "bottom-right",
            "color": "#7B8C6E",
            "color_light": "#EAF0EA",
            "icon": "📌",
            "title": "Consideraciones Técnicas",
            "nodes": [
                {
                    "title": "Fuentes de Datos",
                    "icon": "🗃️",
                    "items": [
                        "Transoft + Sitrack (exportación Excel)",
                        "Sin acceso API directo",
                        "Alcance L1: definido en relevamiento",
                    ]
                },
                {
                    "title": "Cobertura Geográfica",
                    "icon": "🗺️",
                    "items": [
                        "5 sucursales operativas",
                        "Tucumán — Buenos Aires",
                        "Salta — Jujuy — Rosario",
                    ]
                },
            ]
        },

    ],

    # ── Timeline ────────────────────────────────────────────────────────────
    "timeline": {
        "color": "#2E8B6E",
        "stages": [
            "Relevamiento",
            "Desarrollo módulos",
            "Integración multi-sede",
            "Pruebas y Capacitación",
            "Soporte Post-impl.",
        ]
    }
}

if __name__ == "__main__":
    output = "/tmp/bisonte-mindmap-v3.png"
    result = generate_mindmap(config, output_path=output, scale=1.5)

    import os
    size_kb = os.path.getsize(result) / 1024
    print(f"\n✅ Mapa mental generado exitosamente:")
    print(f"   Ruta:  {result}")
    print(f"   Tamaño: {size_kb:.1f} KB")
