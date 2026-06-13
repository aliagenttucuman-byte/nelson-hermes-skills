#!/usr/bin/env python3
"""
mindmap_generator.py
Professional infographic-style mind map generator using SVG → PNG.
Author: Hermes Agent / Nous Research

Usage:
    from mindmap_generator import generate_mindmap
    generate_mindmap(config, output_path="/tmp/output.png")
"""

import math
import textwrap
import re
from pathlib import Path


# ─── Colour / Style constants ─────────────────────────────────────────────────

BG_COLOR      = "#FAF8F5"
CENTER_COLOR  = "#1B4F72"
CENTER_TEXT   = "#FFFFFF"
FONT_STACK    = "Arial, Helvetica, sans-serif"

# ─── Layout constants ─────────────────────────────────────────────────────────

WIDTH  = 1600
HEIGHT = 1060   # slightly taller to give room for bottom sections + timeline

CENTER_X = WIDTH  // 2   # 800
CENTER_Y = 480           # geometric center adjusted for timeline at bottom

HEX_SIZE = 92   # radius of hexagon

# Node card dimensions
NODE_W        = 272
NODE_HEADER_H = 48
NODE_ITEM_H   = 20
NODE_PADDING  = 13
NODE_RADIUS   = 11

# Section label pill
SECTION_H      = 38
SECTION_RADIUS = 10

# Timeline
TL_Y      = 920          # centered timeline at fixed y=920
TL_BOX_W  = 186
TL_BOX_H  = 40
TL_RADIUS = 8

# ─── Position offsets per section ─────────────────────────────────────────────

SECTION_POSITIONS = {
    "top":          (CENTER_X,        120),   # Modalidades de Contratación
    "left":         (220,             480),   # 3 Líneas de Trabajo
    "right":        (1380,            380),   # ROI
    "bottom-left":  (280,             HEIGHT - 272),
    "bottom-right": (1200,            760),   # Consideraciones Técnicas
    "bottom":       (CENTER_X,        HEIGHT - 272),
}

BEZIER_ANCHORS = {
    "top":          (CENTER_X,        CENTER_Y - HEX_SIZE - 8),
    "left":         (CENTER_X - HEX_SIZE - 8,  CENTER_Y),
    "right":        (CENTER_X + HEX_SIZE + 8,  CENTER_Y),
    "bottom-left":  (CENTER_X - int(HEX_SIZE * 0.7),  CENTER_Y + int(HEX_SIZE * 0.7)),
    "bottom-right": (CENTER_X + int(HEX_SIZE * 0.7),  CENTER_Y + int(HEX_SIZE * 0.7)),
    "bottom":       (CENTER_X,        CENTER_Y + HEX_SIZE + 8),
}

# Icon substitutes: emoji key → short ASCII symbol drawn as SVG
ICON_LABELS = {
    "📋": "≡",   "🔒": "■",   "☁️": "~",   "⚙️": "*",
    "📊": "#",   "🚛": ">>",  "📡": "o",   "📈": "↑",
    "💰": "$",   "📉": "↓",   "📌": "◆",   "🗃️": "▦",
    "🗺️": "@",   "📐": "△",   "🔧": "+",   "⭐": "★",
    "✅": "✓",   "❌": "✗",   "ℹ️": "i",   "🎯": "●",
}

def icon_label(emoji_str):
    """Convert emoji to a safe ASCII/unicode label for SVG."""
    s = (emoji_str or "").strip()
    return ICON_LABELS.get(s, "•")


# ─── Utilities ────────────────────────────────────────────────────────────────

def lighten(hex_col, factor=0.82):
    h = hex_col.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def darken(hex_col, factor=0.2):
    h = hex_col.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def wrap_text(text, max_chars=34):
    return textwrap.wrap(str(text), width=max_chars) or [""]


def safe_xml(text):
    """Escape XML special chars AND remove non-BMP characters (emoji)."""
    s = str(text)
    # Remove characters that break XML parsers (surrogates, non-printable, emoji)
    s = re.sub(r'[^\u0000-\uD7FF\uE000-\uFFFD]', '', s)
    # Standard XML escaping
    s = (s.replace("&", "&amp;")
          .replace("<", "&lt;")
          .replace(">", "&gt;")
          .replace('"', "&quot;")
          .replace("'", "&apos;"))
    return s


def hexagon_points(cx, cy, size):
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + size * math.cos(angle)
        py = cy + size * math.sin(angle)
        pts.append(f"{px:.2f},{py:.2f}")
    return " ".join(pts)


# ─── SVG building blocks ──────────────────────────────────────────────────────

def build_defs():
    return """\
  <defs>
    <filter id="ns" x="-6%" y="-6%" width="112%" height="112%">
      <feDropShadow dx="0" dy="2" stdDeviation="4"
                    flood-color="#000000" flood-opacity="0.10"/>
    </filter>
    <filter id="hs" x="-18%" y="-18%" width="136%" height="136%">
      <feDropShadow dx="0" dy="5" stdDeviation="9"
                    flood-color="#1B4F72" flood-opacity="0.30"/>
    </filter>
    <marker id="arr" markerWidth="10" markerHeight="7"
            refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#2E8B6E" opacity="0.85"/>
    </marker>
  </defs>"""


def build_background():
    # Subtle grid pattern for professional look
    return f"""\
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG_COLOR}"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#dot)" opacity="0.0"/>"""


def build_center_hex(title_lines, subtitle=None):
    pts_outer = hexagon_points(CENTER_X, CENTER_Y, HEX_SIZE + 10)
    pts_inner = hexagon_points(CENTER_X, CENTER_Y, HEX_SIZE)
    pts_ring  = hexagon_points(CENTER_X, CENTER_Y, HEX_SIZE + 3)

    parts = [
        # Outer glow
        f'<polygon points="{pts_outer}" fill="{CENTER_COLOR}" opacity="0.12" filter="url(#hs)"/>',
        # Ring border
        f'<polygon points="{pts_ring}" fill="none" stroke="{CENTER_COLOR}" stroke-width="3" opacity="0.25"/>',
        # Main hexagon
        f'<polygon points="{pts_inner}" fill="{CENTER_COLOR}" filter="url(#hs)"/>',
    ]

    n = len(title_lines)
    line_h = 22
    total_h = n * line_h
    start_y = CENTER_Y - total_h / 2 + line_h / 2

    for i, line in enumerate(title_lines):
        ty = start_y + i * line_h
        fw = "700" if i == 0 else "600"
        fs = 16 if i == 0 else 14
        parts.append(
            f'<text x="{CENTER_X}" y="{ty:.1f}" '
            f'font-family="{FONT_STACK}" font-size="{fs}" font-weight="{fw}" '
            f'fill="white" text-anchor="middle" dominant-baseline="middle">'
            f'{safe_xml(line)}</text>'
        )

    if subtitle:
        sub_y = CENTER_Y + HEX_SIZE + 18
        parts.append(
            f'<text x="{CENTER_X}" y="{sub_y}" '
            f'font-family="{FONT_STACK}" font-size="11" font-weight="400" '
            f'fill="{CENTER_COLOR}" text-anchor="middle" opacity="0.75">'
            f'{safe_xml(subtitle)}</text>'
        )
    return "\n".join(parts)


def build_bezier(pos, color, stroke_width=9, opacity=0.42):
    ax, ay = BEZIER_ANCHORS[pos]
    sx, sy = SECTION_POSITIONS[pos]

    mx = (ax + sx) / 2
    my = (ay + sy) / 2

    nudge = 0
    if pos in ("top", "bottom"):
        nudge_x, nudge_y = 35, 0
    elif pos in ("left", "right"):
        nudge_x, nudge_y = 0, 35
    elif pos == "bottom-left":
        nudge_x, nudge_y = -20, 20
    elif pos == "bottom-right":
        nudge_x, nudge_y = 20, 20
    else:
        nudge_x, nudge_y = 0, 0

    cp1x = ax + (mx - ax) * 0.55 + nudge_x
    cp1y = ay + (my - ay) * 0.55 + nudge_y
    cp2x = sx - (sx - mx) * 0.55 - nudge_x
    cp2y = sy - (sy - my) * 0.55 - nudge_y

    return (
        f'<path d="M {ax:.1f},{ay:.1f} '
        f'C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {sx:.1f},{sy:.1f}" '
        f'stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" fill="none" opacity="{opacity}"/>'
    )


def node_height(node):
    h = NODE_HEADER_H + NODE_PADDING
    for item in node.get("items", []):
        lines = wrap_text(item, max_chars=29)
        h += len(lines) * NODE_ITEM_H + 3
    h += NODE_PADDING
    return max(h, NODE_HEADER_H + 48)


def build_node(node, rx, ry, color, uid_prefix="n"):
    """Build a single node card at absolute position (rx, ry)."""
    h = node_height(node)
    w = NODE_W
    r = NODE_RADIUS

    raw_icon  = node.get("icon", "")
    raw_title = node.get("title", "")
    items     = node.get("items", [])

    icon_sym  = icon_label(raw_icon) if raw_icon else ""

    clip_id = f"{uid_prefix}_{int(rx)}_{int(ry)}"
    parts = []

    # ── Shadow + white body ──
    parts.append(
        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{w}" height="{h}" '
        f'rx="{r}" ry="{r}" fill="white" filter="url(#ns)"/>'
    )

    # ── Colored header ──
    # Use clipPath to get rounded top only
    parts.append(
        f'<clipPath id="{clip_id}">'
        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{w}" height="{h}" rx="{r}" ry="{r}"/>'
        f'</clipPath>'
    )
    parts.append(
        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{w}" height="{NODE_HEADER_H}" '
        f'fill="{color}" clip-path="url(#{clip_id})"/>'
    )
    # Square off bottom part of header fill
    parts.append(
        f'<rect x="{rx:.1f}" y="{ry + NODE_HEADER_H - r:.1f}" '
        f'width="{w}" height="{r}" fill="{color}"/>'
    )

    # ── Header icon badge ──
    if icon_sym:
        badge_cx = rx + 18
        badge_cy = ry + NODE_HEADER_H / 2
        badge_r  = 12
        parts.append(
            f'<circle cx="{badge_cx:.1f}" cy="{badge_cy:.1f}" r="{badge_r}" '
            f'fill="white" opacity="0.22"/>'
        )
        parts.append(
            f'<text x="{badge_cx:.1f}" y="{badge_cy:.1f}" '
            f'font-family="{FONT_STACK}" font-size="12" font-weight="700" '
            f'fill="white" text-anchor="middle" dominant-baseline="middle">'
            f'{safe_xml(icon_sym)}</text>'
        )
        title_x = rx + 36
        max_chars = 26
    else:
        title_x = rx + 12
        max_chars = 30

    # ── Header title ──
    t_lines = wrap_text(raw_title, max_chars=max_chars)
    if len(t_lines) == 1:
        ty = ry + NODE_HEADER_H / 2
        for tl in t_lines:
            parts.append(
                f'<text x="{title_x:.1f}" y="{ty:.1f}" '
                f'font-family="{FONT_STACK}" font-size="12" font-weight="700" '
                f'fill="white" text-anchor="start" dominant-baseline="middle">'
                f'{safe_xml(tl)}</text>'
            )
    else:
        base_ty = ry + NODE_HEADER_H / 2 - (len(t_lines) - 1) * 7
        for li, tl in enumerate(t_lines):
            parts.append(
                f'<text x="{title_x:.1f}" y="{base_ty + li * 13:.1f}" '
                f'font-family="{FONT_STACK}" font-size="11" font-weight="700" '
                f'fill="white" text-anchor="start" dominant-baseline="middle">'
                f'{safe_xml(tl)}</text>'
            )

    # ── Body items ──
    iy = ry + NODE_HEADER_H + NODE_PADDING
    for item in items:
        lines = wrap_text(item, max_chars=29)
        # Bullet
        parts.append(
            f'<rect x="{rx + 12:.1f}" y="{iy + 5:.1f}" '
            f'width="5" height="5" rx="1" fill="{color}" opacity="0.65"/>'
        )
        for li, line in enumerate(lines):
            parts.append(
                f'<text x="{rx + 23:.1f}" y="{iy + 8:.1f}" '
                f'font-family="{FONT_STACK}" font-size="11" '
                f'fill="#2d2d2d" text-anchor="start" dominant-baseline="middle">'
                f'{safe_xml(line)}</text>'
            )
            iy += NODE_ITEM_H
        iy += 3

    return "\n".join(parts)


def build_section_pill(sx, sy, label, color, pill_w):
    px = sx - pill_w / 2
    py = sy - SECTION_H / 2
    return [
        f'<rect x="{px:.1f}" y="{py:.1f}" '
        f'width="{pill_w:.1f}" height="{SECTION_H}" '
        f'rx="{SECTION_RADIUS}" ry="{SECTION_RADIUS}" '
        f'fill="{color}" opacity="0.93" filter="url(#ns)"/>',
        f'<text x="{sx:.1f}" y="{sy:.1f}" '
        f'font-family="{FONT_STACK}" font-size="14" font-weight="700" '
        f'fill="white" text-anchor="middle" dominant-baseline="middle">'
        f'{safe_xml(label)}</text>',
    ]


def build_section(section):
    pos      = section.get("position", "top")
    color    = section.get("color", "#2E8B6E")
    color_l  = section.get("color_light", lighten(color))
    raw_icon = section.get("icon", "")
    title    = section.get("title", "")
    nodes    = section.get("nodes", [])
    sid      = section.get("id", pos)

    sx, sy = SECTION_POSITIONS[pos]
    icon_s  = icon_label(raw_icon) if raw_icon else ""
    label   = f"[{icon_s}] {title}" if icon_s else title

    pill_w = max(len(label) * 8.5 + 32, 220)

    parts = []
    parts += build_section_pill(sx, sy, label, color, pill_w)

    if not nodes:
        return "\n".join(parts)

    card_heights = [node_height(n) for n in nodes]
    gap = 12

    if pos == "top":
        # Cards spread horizontally ABOVE the label — ensure >= 200px gap between node centres
        n_nodes   = len(nodes)
        min_span  = max(NODE_W * n_nodes + 220 * (n_nodes - 1), NODE_W * n_nodes + 12 * (n_nodes - 1))
        total_w   = max(NODE_W * n_nodes + gap * (n_nodes - 1), min_span)
        start_x   = sx - total_w / 2
        base_y    = sy - SECTION_H / 2 - 14

        for i, (node, ch) in enumerate(zip(nodes, card_heights)):
            nx  = start_x + i * (total_w - NODE_W) / max(n_nodes - 1, 1) if n_nodes > 1 else sx - NODE_W / 2
            ny  = base_y - ch
            # Clamp to top of canvas
            ny  = max(ny, 8)
            parts.append(build_node(node, nx, ny, color, uid_prefix=f"{sid}{i}"))
            ncx = nx + NODE_W / 2
            ncy_bot = ny + ch
            pill_top = sy - SECTION_H / 2
            # Bezier from bottom of node card to top of section pill
            bmx  = (ncx + sx) / 2
            bmy  = (ncy_bot + pill_top) / 2
            cp1x = ncx + (bmx - ncx) * 0.55
            cp1y = ncy_bot + (bmy - ncy_bot) * 0.55
            cp2x = sx - (sx - bmx) * 0.55
            cp2y = pill_top - (pill_top - bmy) * 0.55
            parts.append(
                f'<path d="M {ncx:.1f},{ncy_bot:.1f} '
                f'C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {sx:.1f},{pill_top:.1f}" '
                f'stroke="{color}" stroke-width="9" '
                f'stroke-linecap="round" fill="none" opacity="0.45"/>'
            )

    elif pos == "left":
        # Section pill on far left; nodes to the RIGHT of the pill
        pill_right = sx + pill_w / 2
        node_rx    = pill_right + 18
        total_h    = sum(card_heights) + gap * (len(nodes) - 1)
        start_y    = sy - total_h / 2
        # Clamp to top of canvas
        start_y    = max(start_y, 10)

        for i, (node, ch) in enumerate(zip(nodes, card_heights)):
            ny  = start_y + sum(card_heights[:i]) + gap * i
            ncy = ny + ch / 2
            parts.append(build_node(node, node_rx, ny, color, uid_prefix=f"{sid}{i}"))
            # Bezier connector: from pill right edge to node left edge
            nx_left = node_rx
            bmx  = (pill_right + nx_left) / 2
            bmy  = (sy + ncy) / 2
            cp1x = pill_right + (bmx - pill_right) * 0.55
            cp1y = sy + (bmy - sy) * 0.55
            cp2x = nx_left - (nx_left - bmx) * 0.55
            cp2y = ncy - (ncy - bmy) * 0.55
            parts.append(
                f'<path d="M {pill_right:.1f},{sy:.1f} '
                f'C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {nx_left:.1f},{ncy:.1f}" '
                f'stroke="{color}" stroke-width="9" '
                f'stroke-linecap="round" fill="none" opacity="0.45"/>'
            )

    elif pos == "right":
        # Section pill on far right; nodes to the LEFT of the pill
        pill_left = sx - pill_w / 2
        node_rx   = pill_left - NODE_W - 18
        # Clamp to canvas
        node_rx   = max(node_rx, 10)
        total_h   = sum(card_heights) + gap * (len(nodes) - 1)
        start_y   = sy - total_h / 2
        start_y   = max(start_y, 10)

        for i, (node, ch) in enumerate(zip(nodes, card_heights)):
            ny  = start_y + sum(card_heights[:i]) + gap * i
            ncy = ny + ch / 2
            parts.append(build_node(node, node_rx, ny, color, uid_prefix=f"{sid}{i}"))
            # Bezier connector: from node right edge to pill left edge
            nx_right = node_rx + NODE_W
            bmx  = (nx_right + pill_left) / 2
            bmy  = (ncy + sy) / 2
            cp1x = nx_right + (bmx - nx_right) * 0.55
            cp1y = ncy + (bmy - ncy) * 0.55
            cp2x = pill_left - (pill_left - bmx) * 0.55
            cp2y = sy - (sy - bmy) * 0.55
            parts.append(
                f'<path d="M {nx_right:.1f},{ncy:.1f} '
                f'C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {pill_left:.1f},{sy:.1f}" '
                f'stroke="{color}" stroke-width="9" '
                f'stroke-linecap="round" fill="none" opacity="0.45"/>'
            )

    elif pos in ("bottom-left", "bottom-right", "bottom"):
        # Cards spread horizontally BELOW label, but above timeline
        total_w  = NODE_W * len(nodes) + gap * (len(nodes) - 1)
        start_x  = sx - total_w / 2
        base_y   = sy + SECTION_H / 2 + 10

        for i, (node, ch) in enumerate(zip(nodes, card_heights)):
            nx  = start_x + i * (NODE_W + gap)
            # Clamp to canvas left/right
            nx  = max(nx, 8)
            nx  = min(nx, WIDTH - NODE_W - 8)
            ncx = nx + NODE_W / 2
            parts.append(build_node(node, nx, base_y, color, uid_prefix=f"{sid}{i}"))
            # Bezier from bottom of section pill to top of node card
            pill_bot = sy + SECTION_H / 2
            bmx  = (sx + ncx) / 2
            bmy  = (pill_bot + base_y) / 2
            cp1x = sx + (bmx - sx) * 0.55
            cp1y = pill_bot + (bmy - pill_bot) * 0.55
            cp2x = ncx - (ncx - bmx) * 0.55
            cp2y = base_y - (base_y - bmy) * 0.55
            parts.append(
                f'<path d="M {sx:.1f},{pill_bot:.1f} '
                f'C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {ncx:.1f},{base_y:.1f}" '
                f'stroke="{color}" stroke-width="9" '
                f'stroke-linecap="round" fill="none" opacity="0.45"/>'
            )

    return "\n".join(parts)


def build_timeline(timeline):
    if not timeline:
        return ""
    color  = timeline.get("color", "#2E8B6E")
    stages = timeline.get("stages", [])
    if not stages:
        return ""

    n       = len(stages)
    gap     = 18
    # Total timeline width capped at 1200px, centered on canvas
    total_w = min(n * TL_BOX_W + (n - 1) * (gap + 20), 1200)
    start_x = CENTER_X - total_w / 2
    y       = TL_Y

    light   = lighten(color, 0.9)
    parts   = []

    # Background pill
    strip_h = TL_BOX_H + 22
    strip_x = start_x - 16
    strip_w = total_w + 32
    parts.append(
        f'<rect x="{strip_x:.1f}" y="{y - 11:.1f}" '
        f'width="{strip_w:.1f}" height="{strip_h}" '
        f'rx="14" fill="{light}" opacity="0.55"/>'
    )

    for i, stage in enumerate(stages):
        bx = start_x + i * (TL_BOX_W + gap + 20)
        by = y

        # Box with gradient-like lighter stripe on top
        parts.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" '
            f'width="{TL_BOX_W}" height="{TL_BOX_H}" '
            f'rx="{TL_RADIUS}" fill="{color}" opacity="0.88" filter="url(#ns)"/>'
        )
        # Top highlight stripe
        parts.append(
            f'<rect x="{bx + 2:.1f}" y="{by + 2:.1f}" '
            f'width="{TL_BOX_W - 4}" height="6" '
            f'rx="4" fill="white" opacity="0.18"/>'
        )

        # Phase number badge
        bcx = bx + 15
        bcy = by + TL_BOX_H / 2
        parts.append(
            f'<circle cx="{bcx:.1f}" cy="{bcy:.1f}" r="11" '
            f'fill="white" opacity="0.25"/>'
        )
        parts.append(
            f'<text x="{bcx:.1f}" y="{bcy:.1f}" '
            f'font-family="{FONT_STACK}" font-size="10" font-weight="700" '
            f'fill="white" text-anchor="middle" dominant-baseline="middle">'
            f'{i + 1}</text>'
        )

        # Stage text
        lines = wrap_text(stage, max_chars=18)
        tx  = bx + TL_BOX_W / 2 + 7
        ty0 = by + TL_BOX_H / 2 - (len(lines) - 1) * 6.5
        for li, line in enumerate(lines):
            parts.append(
                f'<text x="{tx:.1f}" y="{ty0 + li * 13:.1f}" '
                f'font-family="{FONT_STACK}" font-size="11" font-weight="600" '
                f'fill="white" text-anchor="middle" dominant-baseline="middle">'
                f'{safe_xml(line)}</text>'
            )

        # Arrow connector
        if i < n - 1:
            ax  = bx + TL_BOX_W + 2
            ay  = by + TL_BOX_H / 2
            ex  = ax + gap + 16
            parts.append(
                f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ex:.1f}" y2="{ay:.1f}" '
                f'stroke="{color}" stroke-width="2.5" opacity="0.8" '
                f'marker-end="url(#arr)"/>'
            )

    return "\n".join(parts)


# ─── Decorative elements ──────────────────────────────────────────────────────

def build_decorations(sections):
    """Subtle background decorations: corner accents, dividers."""
    parts = []

    # Soft corner circles
    for cx, cy, op in [(0, 0, 0.04), (WIDTH, 0, 0.04),
                       (0, HEIGHT, 0.03), (WIDTH, HEIGHT, 0.03)]:
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="180" '
            f'fill="{CENTER_COLOR}" opacity="{op}"/>'
        )

    # Thin horizontal rule between map area and timeline
    rule_y = HEIGHT - 105
    parts.append(
        f'<line x1="60" y1="{rule_y}" x2="{WIDTH - 60}" y2="{rule_y}" '
        f'stroke="#cccccc" stroke-width="1" opacity="0.5"/>'
    )

    # "Timeline" label
    parts.append(
        f'<text x="62" y="{rule_y - 8}" '
        f'font-family="{FONT_STACK}" font-size="10" font-weight="600" '
        f'fill="#888888" text-anchor="start">TIMELINE DEL PROYECTO</text>'
    )

    return "\n".join(parts)


# ─── Main SVG generator ───────────────────────────────────────────────────────

def generate_svg(config: dict) -> str:
    title_raw   = config.get("title", "Mind Map")
    subtitle    = config.get("title_subtitle", None)
    sections    = config.get("sections", [])
    timeline    = config.get("timeline", None)

    title_lines = [l.strip() for l in title_raw.split("\n") if l.strip()]

    parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<style>* {{ font-family: {FONT_STACK}; }}</style>',
        build_defs(),
        f'  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG_COLOR}"/>',
    ]

    # Decorations (behind everything)
    parts.append(build_decorations(sections))

    # Bezier connector lines (behind nodes, in front of background)
    for sec in sections:
        pos   = sec.get("position", "top")
        color = sec.get("color", "#888")
        if pos in BEZIER_ANCHORS:
            parts.append(build_bezier(pos, color))

    # Section content
    for sec in sections:
        parts.append(f'<!-- section {sec.get("id","?")} -->')
        parts.append(build_section(sec))

    # Center hex on top
    parts.append(build_center_hex(title_lines, subtitle))

    # Timeline
    if timeline:
        parts.append(build_timeline(timeline))

    parts.append("</svg>")
    return "\n".join(parts)


# ─── PNG export ───────────────────────────────────────────────────────────────

def generate_mindmap(config: dict,
                     output_path: str = "/tmp/mindmap.png",
                     scale: float = 1.5) -> str:
    """
    Generate a mind map PNG from a config dict.

    Args:
        config:      Mind map configuration dictionary.
        output_path: Destination PNG file path.
        scale:       Output scale factor (1.5 → 2400×1500 px).

    Returns:
        Absolute path to the generated PNG.
    """
    svg_content = generate_svg(config)

    output_path = str(Path(output_path).expanduser().resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Always save SVG alongside for reference / debugging
    svg_path = output_path.replace(".png", ".svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[mindmap] SVG saved: {svg_path}")

    svg_bytes = svg_content.encode("utf-8")

    # ── Backend 1: cairosvg ──
    try:
        import cairosvg
        cairosvg.svg2png(
            bytestring=svg_bytes,
            write_to=output_path,
            output_width=int(WIDTH  * scale),
            output_height=int(HEIGHT * scale),
        )
        print(f"[mindmap] PNG via cairosvg: {output_path}")
        return output_path
    except Exception as e_cairo:
        print(f"[mindmap] cairosvg error: {e_cairo}")

    # ── Backend 2: WeasyPrint ──
    try:
        from weasyprint import HTML as WP_HTML
        import base64
        b64 = base64.b64encode(svg_bytes).decode()
        html = (
            f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<style>@page{{size:{WIDTH}px {HEIGHT}px;margin:0}}'
            f'body{{margin:0;padding:0}}'
            f'img{{display:block;width:{WIDTH}px;height:{HEIGHT}px}}</style></head>'
            f'<body><img src="data:image/svg+xml;base64,{b64}"/></body></html>'
        )
        doc = WP_HTML(string=html)
        # WeasyPrint >= 53 uses write_pdf; PNG via PIL
        pdf_bytes = doc.write_pdf()
        # Convert first PDF page to PNG via pdf2image
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(pdf_bytes, dpi=int(96 * scale))
        pages[0].save(output_path, "PNG")
        print(f"[mindmap] PNG via WeasyPrint+pdf2image: {output_path}")
        return output_path
    except Exception as e_wp:
        print(f"[mindmap] WeasyPrint error: {e_wp}")

    # ── Backend 3: Inkscape CLI ──
    try:
        import subprocess
        result = subprocess.run(
            ["inkscape", svg_path,
             f"--export-png={output_path}",
             f"--export-width={int(WIDTH * scale)}"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and Path(output_path).exists():
            print(f"[mindmap] PNG via Inkscape: {output_path}")
            return output_path
        raise RuntimeError(result.stderr)
    except Exception as e_ink:
        print(f"[mindmap] Inkscape error: {e_ink}")

    # ── Backend 4: PIL placeholder ──
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (int(WIDTH * scale), int(HEIGHT * scale)), BG_COLOR)
        d   = ImageDraw.Draw(img)
        msg = "SVG render failed — see .svg file"
        d.text((int(WIDTH * scale) // 2, int(HEIGHT * scale) // 2),
               msg, fill="#333333", anchor="mm")
        img.save(output_path)
        print(f"[mindmap] PIL placeholder PNG saved: {output_path}")
        return output_path
    except Exception as e_pil:
        raise RuntimeError(
            f"All backends failed:\n"
            f"  cairosvg:   {e_cairo}\n"
            f"  WeasyPrint: {e_wp}\n"
            f"  Inkscape:   {e_ink}\n"
            f"  PIL:        {e_pil}"
        )


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, json

    if len(sys.argv) >= 3:
        with open(sys.argv[1]) as f:
            cfg = json.load(f)
        generate_mindmap(cfg, sys.argv[2])
    else:
        # Quick smoke test
        demo = {
            "title": "Demo\nMind Map",
            "sections": [
                {
                    "id": "top", "position": "top",
                    "color": "#2E8B6E", "color_light": "#E8F5F0",
                    "icon": "📋", "title": "Category A",
                    "nodes": [
                        {"title": "Node 1", "icon": "🔒",
                         "items": ["First item here", "Second item here"]},
                        {"title": "Node 2", "icon": "☁️",
                         "items": ["Third item here"]},
                    ]
                },
                {
                    "id": "left", "position": "left",
                    "color": "#E05A4E", "icon": "⚙️", "title": "Category B",
                    "nodes": [
                        {"title": "Node 3", "icon": "📊",
                         "items": ["Detail A", "Detail B"]},
                    ]
                },
            ],
            "timeline": {
                "color": "#2E8B6E",
                "stages": ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
            }
        }
        generate_mindmap(demo, "/tmp/mindmap_demo.png")
