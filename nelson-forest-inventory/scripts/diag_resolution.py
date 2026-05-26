"""
Diagnóstico de resolución real de los TIFs tras downsampling.
Muestra qué resolución ve el analyzer después del resampleo y qué rango
de copas en m² es válido. Detecta si los parámetros actuales dejarían
pasar blobs imposibles (ej. 359m² → árbol de 26m).

También analiza circularidad y varianza de los blobs detectados para
calibrar los filtros árbol vs pasto (circularity, local_variance).

Uso: python3 scripts/diag_resolution.py [/ruta/a/uploads/]
     python3 scripts/diag_resolution.py [/ruta/a/uploads/] --blobs  # analiza blobs de primer TIF
"""
import rasterio
import rasterio.warp
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
import numpy as np
import cv2
import math
import glob
import sys

UPLOAD_DIR = sys.argv[1] if len(sys.argv) > 1 else "/home/server/proyectos/forestai-poc/uploads"
ANALYZE_BLOBS = "--blobs" in sys.argv
MAX_DIM = 6000
MAX_CROWN_M2 = 80.0
MAX_HEIGHT_M = 16.0

files = glob.glob(f"{UPLOAD_DIR}/*.tif")
if not files:
    print(f"No se encontraron TIFs en {UPLOAD_DIR}")
    sys.exit(1)

for filepath in sorted(files):
    with rasterio.open(filepath) as src:
        orig_w, orig_h = src.width, src.height
        scale = min(MAX_DIM / orig_w, MAX_DIM / orig_h, 1.0)
        out_w = max(1, int(orig_w * scale))
        out_h = max(1, int(orig_h * scale))

        bounds = src.bounds
        crs = src.crs

        width_m = bounds.right - bounds.left
        height_m_geo = bounds.top - bounds.bottom

        if crs and crs.is_geographic:
            center_lat = (bounds.top + bounds.bottom) / 2
            width_m = width_m * 111319 * math.cos(math.radians(center_lat))
            height_m_geo = height_m_geo * 111319

        resolution_m = (width_m / out_w + height_m_geo / out_h) / 2
        resolution_native = (width_m / orig_w + height_m_geo / orig_h) / 2

        max_area_px = MAX_CROWN_M2 / (resolution_m ** 2)
        radius_max = math.sqrt(MAX_CROWN_M2 / math.pi)
        height_max = min(2.5 * radius_max, MAX_HEIGHT_M)

        fname = filepath.split("/")[-1]
        print(f"--- {fname} ---")
        print(f"  Dims: {orig_w}x{orig_h}px → {out_w}x{out_h}px (scale={scale:.3f})")
        print(f"  Res nativa: {resolution_native:.4f}m/px | Res resampleada: {resolution_m:.4f}m/px")
        print(f"  Copa máx ({MAX_CROWN_M2}m²) = {max_area_px:.0f}px² | Altura máx = {height_max:.1f}m")

        # Diagnóstico de blobs imposibles — si se hubiera usado el cap viejo
        old_max_area_px = 120.0 / (resolution_m ** 2)
        old_height = min(2.5 * math.sqrt(120.0 / math.pi), 20.0)
        print(f"  [viejo 120m²] = {old_max_area_px:.0f}px² | altura máx vieja = {old_height:.1f}m")

        if resolution_m > 0.05:
            print(f"  ⚠️  Resolución > 5cm/px tras downsampling — watershed puede fusionar copas cercanas")

        # --- Análisis de blobs con filtros ---
        if ANALYZE_BLOBS and files.index(filepath) == 0:
            print(f"\n  [ANÁLISIS DE BLOBS - calibración filtros árbol vs pasto]")
            if src.count >= 3:
                r = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.average).astype(np.float32)
                g = src.read(2, out_shape=(out_h, out_w), resampling=Resampling.average).astype(np.float32)
                b = src.read(3, out_shape=(out_h, out_w), resampling=Resampling.average).astype(np.float32)
            else:
                gray = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.average).astype(np.float32)
                r = g = b = gray

            def norm(band):
                mn, mx = band.min(), band.max()
                if mx == mn:
                    return np.zeros_like(band, dtype=np.uint8)
                return ((band - mn) / (mx - mn) * 255).astype(np.uint8)

            r8, g8, b8 = norm(r), norm(g), norm(b)
            img_rgb = cv2.merge([b8, g8, r8])

            g_f, r_f, b_f = g.astype(np.float32), r.astype(np.float32), b.astype(np.float32)
            denom = g_f + r_f - b_f
            denom[denom == 0] = 1
            vari = np.clip((g_f - r_f) / denom, -1, 1)
            vari_norm = ((vari + 1) / 2 * 255).astype(np.uint8)

            _, thresh = cv2.threshold(vari_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            veg_fraction = thresh.sum() / (255 * thresh.size)
            if veg_fraction > 0.90:
                p = int(np.percentile(vari_norm, 70))
                _, thresh = cv2.threshold(vari_norm, p, 255, cv2.THRESH_BINARY)

            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel, iterations=1)

            dist_transform = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
            _, sure_fg = cv2.threshold(dist_transform, 0.40 * dist_transform.max(), 255, 0)
            sure_fg = sure_fg.astype(np.uint8)

            sure_bg = cv2.dilate(thresh, kernel, iterations=3)
            unknown = cv2.subtract(sure_bg, sure_fg)
            _, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0
            markers_ws = markers.copy()
            cv2.watershed(img_rgb, markers_ws)

            print(f"  veg_fraction={veg_fraction:.3f}")
            print(f"  {'label':>6} | {'area_m2':>8} | {'circ':>6} | {'variance':>9} | {'pass?':>6}")
            print(f"  {'------':>6} | {'--------':>8} | {'------':>6} | {'---------':>9} | {'------':>6}")

            for label in np.unique(markers_ws):
                if label <= 1:
                    continue
                mask = (markers_ws == label).astype(np.uint8) * 255
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not contours:
                    continue
                cnt = max(contours, key=cv2.contourArea)
                area_px = cv2.contourArea(cnt)
                area_m2 = area_px * (resolution_m ** 2)
                if area_m2 < 1.0 or area_m2 > 150.0:
                    continue
                perim = cv2.arcLength(cnt, True)
                circ = (4 * math.pi * area_px) / (perim ** 2) if perim > 1 else 0
                g_vals = g[mask > 0]
                variance = float(np.var(g_vals)) if len(g_vals) > 3 else 0
                passed = area_m2 <= 80 and area_m2 >= 2 and circ >= 0.15 and variance >= 50
                print(f"  {label:>6} | {area_m2:>8.2f} | {circ:>6.3f} | {variance:>9.1f} | {'✓' if passed else '✗':>6}")
        print()
