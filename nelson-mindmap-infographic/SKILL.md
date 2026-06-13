---
name: nelson-mindmap-infographic
description: "Genera mapas mentales estilo infografico profesional para el equipo Nelson. Hexagono central, secciones coloreadas, curvas Bezier organicas, timeline horizontal. Backends: HTML+Playwright (recomendado) y SVG manual."
triggers:
  - mapa mental
  - mindmap
  - infografico
  - diagrama de propuesta
version: "1.0.0"
---

# nelson-mindmap-infographic

## Estilo de referencia

Infografico profesional con:
- Fondo: #FAF8F5 (beige calido)
- Hexagono central: #1B4F72 (azul marino), texto blanco Bold, centrado en el canvas
- Secciones: rectangulos redondeados, header coloreado + body blanco con bullets
- Paleta: verde #2E8B6E (finanzas/modalidades), coral #D94F3D (trabajo/operativo), marron #7A6A52 (tecnico)
- Conectores: Bezier curves, stroke-width 9px, opacity 0.45, stroke-linecap round
- Tipografia: system-ui / sans-serif, Bold / SemiBold / Regular
- Timeline: badges circulares numerados + flechas, centrado en la parte inferior
- Canvas: 1600x900px landscape

## Scripts disponibles

```
~/.hermes/scripts/mindmap_html_generator.py   # Motor principal HTML+Playwright (recomendado)
~/.hermes/scripts/mindmap_bisonte_v4.py        # Ejemplo completo propuesta Bisonte
~/.hermes/scripts/mindmap_generator.py         # Motor SVG manual (alternativo)
~/.hermes/scripts/mindmap_bisonte_test.py      # Ejemplo SVG manual
```

## Uso basico

```python
import sys
sys.path.insert(0, '/home/server/.hermes/scripts')
from mindmap_html_generator import render_mindmap

config = {
    "title": "Titulo Central",
    "subtitle": "Subtitulo opcional",
    "center_color": "#1B4F72",
    "bg_color": "#FAF8F5",
    "sections": {
        "top": {
            "color": "#2E8B6E",
            "light": "#E8F5F0",
            "title": "Seccion Superior",
            "children": [
                {
                    "title": "Nodo hijo",
                    "icon": "icon",
                    "items": ["bullet 1", "bullet 2"]
                }
            ]
        },
        "left": {},
        "right": {},
        "bottom_right": {}
    },
    "timeline": {
        "color": "#2E8B6E",
        "stages": [
            ("1", "Etapa 1", "desc"),
            ("2", "Etapa 2", "desc")
        ]
    }
}

output_path = render_mindmap(config, "/tmp/mi-mindmap.png")
```

## Posiciones de secciones (canvas 1600x900, hexagono en 800,430)

| Seccion | left | top | Ancho recomendado |
|---------|------|-----|-------------------|
| top | 480 | 30 | 640px (2 hijos side-by-side) |
| left | 20 | 200 | 320px (hijos apilados) |
| right | 1130 | 180 | 340px (hijos apilados) |
| bottom_right | 1080 | 600 | 380px (hijos side-by-side) |

## Curvas Bezier desde hexagono (centro 800,430)

```
TOP:          M 800,390 C 800,300 800,200 800,120
LEFT:         M 755,430 C 650,430 520,430 340,430
RIGHT:        M 845,405 C 950,360 1050,310 1130,280
BOTTOM_RIGHT: M 840,465 C 900,530 980,580 1080,630
TIMELINE:     M 800,480 C 800,580 800,680 800,850
```

## Workflow completo

1. Definir el config con los datos del proyecto
2. Ejecutar render_mindmap() para generar PNG en /tmp/
3. Inspeccionar con vision_analyze para verificar calidad visual
4. Ajustar posiciones/colores si es necesario
5. Enviar por Telegram con send_message()

## Pitfalls conocidos

- Playwright required: pip install playwright && playwright install chromium
- Google Fonts no funciona en SVG con cairosvg: usar system-ui como fallback
- Emojis en SVG con cairosvg pueden romper el parser XML: usar simbolos ASCII
- Secciones con muchos hijos generan desequilibrio visual: compensar moviendo hexagono a (850,430)
- Layout asimetrico es natural cuando LEFT tiene 3 hijos y RIGHT tiene 2

## Mejora pendiente v2

Migrar a D3.js force-directed graph para layout radial automatico y simetrico.
Evita calculo manual de coordenadas, conectores siempre proporcionales.
Script: usar d3-hierarchy con layout radial + Playwright para capturar.

## Dependencias

```bash
pip install playwright cairosvg pillow
playwright install chromium
```
