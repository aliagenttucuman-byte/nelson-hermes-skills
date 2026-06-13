"""
mindmap_html_generator.py
Pipeline HTML+CSS → Playwright → PNG para mapas mentales estilo infográfico profesional.
"""

import os
from typing import Any


def generate_mindmap_html(config: dict) -> str:
    """Genera el HTML completo del mapa mental a partir de un config dict."""

    bg_color     = config.get("bg_color", "#FAF8F5")
    center_color = config.get("center_color", "#1B4F72")
    title        = config.get("title", "Mapa Mental")
    subtitle     = config.get("subtitle", "")
    sections     = config.get("sections", {})
    timeline_cfg = config.get("timeline", {})

    # ── helpers ────────────────────────────────────────────────────────────────

    def section_card(sec_key: str) -> str:
        sec = sections.get(sec_key, {})
        if not sec:
            return ""
        color    = sec.get("color", "#555")
        light    = sec.get("light", "#f9f9f9")
        sec_title = sec.get("title", "")
        children  = sec.get("children", [])

        # layout: 'row' para top y bottom_right, 'column' para left y right
        flex_dir = "row" if sec_key in ("top", "bottom_right") else "column"
        gap      = "12px" if flex_dir == "row" else "8px"

        children_html = ""
        for child in children:
            c_title = child.get("title", "")
            icon    = child.get("icon", "")
            items   = child.get("items", [])
            bullets = "".join(
                f'<li style="margin:0 0 3px 0; font-size:11.5px; color:#333; line-height:1.4;">{it}</li>'
                for it in items
            )
            children_html += f"""
            <div style="
                flex:1; min-width:0;
                background:#fff;
                border-radius:10px;
                overflow:hidden;
                box-shadow:0 2px 8px rgba(0,0,0,0.08);
                border:1.5px solid {color}22;
            ">
              <div style="
                  background:{color};
                  padding:7px 10px;
                  display:flex; align-items:center; gap:6px;
              ">
                <span style="font-size:15px;">{icon}</span>
                <span style="
                    color:#fff;
                    font-weight:700;
                    font-size:11px;
                    line-height:1.3;
                ">{c_title}</span>
              </div>
              <div style="padding:8px 10px; background:{light};">
                <ul style="margin:0; padding-left:14px; list-style:disc;">
                  {bullets}
                </ul>
              </div>
            </div>"""

        return f"""
        <div style="
            background:#fff;
            border-radius:14px;
            overflow:hidden;
            box-shadow:0 4px 20px rgba(0,0,0,0.12);
            border:2px solid {color}44;
        ">
          <!-- header de sección -->
          <div style="
              background:{color};
              padding:8px 14px;
          ">
            <span style="
                color:#fff;
                font-weight:800;
                font-size:13px;
                letter-spacing:0.3px;
                text-transform:uppercase;
            ">{sec_title}</span>
          </div>
          <!-- children -->
          <div style="
              display:flex;
              flex-direction:{flex_dir};
              gap:{gap};
              padding:10px;
              background:{bg_color};
          ">
            {children_html}
          </div>
        </div>"""

    # ── timeline ───────────────────────────────────────────────────────────────

    def timeline_html() -> str:
        tl_color = timeline_cfg.get("color", "#2E8B6E")
        stages   = timeline_cfg.get("stages", [])
        items_html = ""
        for i, stage in enumerate(stages):
            num, line1, line2 = stage[0], stage[1], stage[2] if len(stage) > 2 else ""
            is_last = (i == len(stages) - 1)
            connector = "" if is_last else f"""
                <div style="
                    flex:1;
                    height:3px;
                    background:linear-gradient(90deg, {tl_color}88, {tl_color}44);
                    margin-top:-12px;
                    align-self:center;
                "></div>"""
            items_html += f"""
            <div style="display:flex; align-items:flex-start; flex:1;">
              <div style="display:flex; flex-direction:column; align-items:center; min-width:80px;">
                <div style="
                    width:38px; height:38px;
                    border-radius:50%;
                    background:{tl_color};
                    color:#fff;
                    font-weight:800;
                    font-size:16px;
                    display:flex; align-items:center; justify-content:center;
                    box-shadow:0 3px 10px {tl_color}55;
                    flex-shrink:0;
                ">{num}</div>
                <div style="
                    text-align:center; margin-top:5px;
                    font-size:11px; font-weight:700;
                    color:#333; line-height:1.3;
                ">{line1}<br><span style="font-weight:400; color:#666; font-size:10px;">{line2}</span></div>
              </div>
              {connector}
            </div>"""

        return f"""
        <div style="
            background:#fff;
            border-radius:12px;
            padding:14px 20px;
            box-shadow:0 3px 15px rgba(0,0,0,0.10);
            border:2px solid {tl_color}33;
        ">
          <div style="
              font-size:10px; font-weight:700; color:{tl_color};
              letter-spacing:1.5px; text-transform:uppercase;
              margin-bottom:10px;
          ">CRONOGRAMA DE IMPLEMENTACIÓN</div>
          <div style="display:flex; align-items:flex-start; gap:0;">
            {items_html}
          </div>
        </div>"""

    # ── posiciones absolutas ────────────────────────────────────────────────────
    # Canvas 1600×900, hexágono centro en (800, 430)

    top_card          = section_card("top")
    left_card         = section_card("left")
    right_card        = section_card("right")
    bottom_right_card = section_card("bottom_right")
    tl_html           = timeline_html()

    # ── SVG conexiones Bezier ───────────────────────────────────────────────────

    top_color    = sections.get("top",          {}).get("color", "#2E8B6E")
    left_color   = sections.get("left",         {}).get("color", "#D94F3D")
    right_color  = sections.get("right",        {}).get("color", "#2E8B6E")
    br_color     = sections.get("bottom_right", {}).get("color", "#7A6A52")
    tl_color2    = timeline_cfg.get("color", "#2E8B6E")

    svg_connections = f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         style="position:absolute;top:0;left:0;width:1600px;height:900px;z-index:1;pointer-events:none;">
      <!-- → TOP (Modalidades) -->
      <path d="M 800,380 C 800,280 800,180 800,120"
            stroke="{top_color}" stroke-width="8" stroke-opacity="0.45"
            fill="none" stroke-linecap="round"/>
      <!-- → LEFT (3 Líneas) -->
      <path d="M 750,430 C 650,430 540,430 340,430"
            stroke="{left_color}" stroke-width="8" stroke-opacity="0.45"
            fill="none" stroke-linecap="round"/>
      <!-- → RIGHT (ROI) -->
      <path d="M 852,402 C 950,350 1055,300 1130,280"
            stroke="{right_color}" stroke-width="8" stroke-opacity="0.45"
            fill="none" stroke-linecap="round"/>
      <!-- → BOTTOM-RIGHT (Consideraciones) -->
      <path d="M 842,460 C 900,522 985,582 1082,632"
            stroke="{br_color}" stroke-width="8" stroke-opacity="0.45"
            fill="none" stroke-linecap="round"/>
      <!-- → TIMELINE -->
      <path d="M 800,482 C 800,580 800,680 800,822"
            stroke="{tl_color2}" stroke-width="6" stroke-opacity="0.30"
            fill="none" stroke-linecap="round" stroke-dasharray="8,6"/>
    </svg>"""

    # ── hexágono central ────────────────────────────────────────────────────────
    # Clip-path hexágono regular (100×115 px → ratio ~1:1.15)
    hexagon_html = f"""
    <div style="
        position:absolute;
        left:717px; top:372px;
        width:166px; height:118px;
        z-index:10;
        display:flex; align-items:center; justify-content:center;
    ">
      <!-- Hexágono SVG -->
      <svg width="166" height="118" viewBox="0 0 166 118"
           xmlns="http://www.w3.org/2000/svg"
           style="position:absolute;top:0;left:0;">
        <polygon points="83,2 164,30 164,88 83,116 2,88 2,30"
                 fill="{center_color}"
                 stroke="{center_color}" stroke-width="2"/>
        <!-- brillo sutil -->
        <polygon points="83,2 164,30 164,88 83,116 2,88 2,30"
                 fill="url(#hexGrad)"/>
        <defs>
          <linearGradient id="hexGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="0.15"/>
            <stop offset="100%" stop-color="#000000" stop-opacity="0.10"/>
          </linearGradient>
        </defs>
      </svg>
      <!-- texto centrado -->
      <div style="
          position:relative; z-index:2;
          text-align:center; color:#fff;
          padding:4px 8px;
      ">
        <div style="font-size:13px; font-weight:800; line-height:1.2; letter-spacing:0.3px;">
          {title}
        </div>
        <div style="
            font-size:10px; font-weight:400; opacity:0.85;
            margin-top:3px; line-height:1.3; letter-spacing:0.2px;
        ">{subtitle}</div>
      </div>
    </div>"""

    # ── HTML completo ───────────────────────────────────────────────────────────

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1600">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1600px;
    height: 900px;
    overflow: hidden;
    font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
    background: {bg_color};
  }}
  .canvas {{
    position: relative;
    width: 1600px;
    height: 900px;
    background: {bg_color};
    overflow: hidden;
  }}
  /* marca de agua de fondo muy sutil */
  .canvas::before {{
    content: '';
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse 800px 600px at 800px 430px, rgba(27,79,114,0.04) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}
</style>
</head>
<body>
<div class="canvas">

  <!-- 0. Fondo SVG conexiones -->
  {svg_connections}

  <!-- 1. Hexágono central -->
  {hexagon_html}

  <!-- 2. TOP — Modalidades (left=480, top=30, width=640) -->
  <div style="position:absolute; left:480px; top:30px; width:640px; z-index:5;">
    {top_card}
  </div>

  <!-- 3. LEFT — 3 Líneas (left=20, top=200, width=320) -->
  <div style="position:absolute; left:20px; top:200px; width:320px; z-index:5;">
    {left_card}
  </div>

  <!-- 4. RIGHT — ROI (left=1130, top=180, width=350) -->
  <div style="position:absolute; left:1130px; top:180px; width:350px; z-index:5;">
    {right_card}
  </div>

  <!-- 5. BOTTOM-RIGHT — Consideraciones (left=1080, top=600, width=430) -->
  <div style="position:absolute; left:1050px; top:596px; width:430px; z-index:5;">
    {bottom_right_card}
  </div>

  <!-- 6. TIMELINE (left=100, bottom=15, width=1400) -->
  <div style="position:absolute; left:100px; bottom:12px; width:1400px; z-index:5;">
    {tl_html}
  </div>

</div>
</body>
</html>"""

    return html


def render_mindmap(config: dict, output_path: str) -> str:
    """
    Renderiza el mapa mental a PNG usando Playwright (Chromium headless).
    Devuelve output_path si tiene éxito.
    """
    from playwright.sync_api import sync_playwright

    html_content = generate_mindmap_html(config)

    # Guardamos HTML temporal para depuración
    html_path = output_path.replace(".png", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[mindmap] HTML guardado en: {html_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = browser.new_page(
            viewport={"width": 1600, "height": 900}
        )
        # Cargamos desde archivo para evitar límites de URL
        page.goto(f"file://{os.path.abspath(html_path)}")
        # Esperamos que carguen las fuentes y el layout esté estable
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(600)

        page.screenshot(
            path=output_path,
            full_page=False,       # sólo el viewport 1600×900
            type="png",
            clip={"x": 0, "y": 0, "width": 1600, "height": 900}
        )
        browser.close()

    size_kb = os.path.getsize(output_path) / 1024
    print(f"[mindmap] PNG generado: {output_path}  ({size_kb:.1f} KB)")
    return output_path


if __name__ == "__main__":
    # Test rápido con config mínimo
    test_cfg = {
        "title": "Test",
        "subtitle": "Demo",
        "center_color": "#1B4F72",
        "bg_color": "#FAF8F5",
        "sections": {
            "top": {
                "color": "#2E8B6E", "light": "#E8F5F0",
                "title": "Sección TOP",
                "children": [
                    {"title": "Nodo A", "icon": "🔑", "items": ["Item 1", "Item 2"]},
                    {"title": "Nodo B", "icon": "⭐", "items": ["Item 3", "Item 4"]},
                ]
            }
        },
        "timeline": {
            "color": "#2E8B6E",
            "stages": [("1", "Fase 1", "Inicio"), ("2", "Fase 2", "Fin")]
        }
    }
    render_mindmap(test_cfg, "/tmp/mindmap_test.png")
