#!/usr/bin/env python3
"""
ForestAI Smoke Test — corre el pipeline end-to-end contra GeoTIFF locales.
Sin Docker ni BD. Valida que analyze_ortophoto() funciona correctamente.

Uso:
  cd /home/server
  python3 ~/.hermes/skills/software-development/nelson-forest-inventory/scripts/smoke_test.py
  # O desde el proyecto:
  python3 ~/brainstorming/2026-05-19-forestai-poc/smoke_test.py

Prerequisitos:
  pip3 install rasterio opencv-python-headless geopandas shapely pyproj scikit-image numpy pillow

Resultado esperado:
  ✅ OSBS_029 (Florida):     12 árboles en ~0.1s
  ✅ SJER_sample (California): 1 árbol  en ~0.02s
  ✅ australia:              23 árboles en ~0.1s
  🟢 SMOKE TEST PASADO
"""
import sys
import time

# Ajustar path al proyecto
sys.path.insert(0, "/home/server/proyectos/forestai-poc/backend")

from app.services.forest_analyzer import analyze_ortophoto

DATA_DIR = "/home/server/brainstorming/2026-05-19-forestai-poc/data"
TEST_FILES = {
    "OSBS_029 (Florida)": f"{DATA_DIR}/OSBS_029.tif",
    "SJER_sample (California)": f"{DATA_DIR}/SJER_sample.tif",
    "australia": f"{DATA_DIR}/australia.tif",
}

results_summary = []

for name, filepath in TEST_FILES.items():
    print(f"\n{'='*60}")
    print(f"🌲 Analizando: {name}")
    print(f"   Archivo: {filepath}")
    print('='*60)

    def progress_callback(pct, step):
        print(f"  [{pct:3d}%] {step}")

    t0 = time.time()
    try:
        trees = analyze_ortophoto(filepath, progress_callback)
        elapsed = time.time() - t0

        if not trees:
            print("⚠️  No se detectaron árboles")
            results_summary.append({"file": name, "trees": 0, "ok": False})
            continue

        total_biomass = sum(t["biomass_kg"] for t in trees)
        total_crown = sum(t["crown_area_m2"] for t in trees)
        avg_height = sum(t["height_m"] for t in trees) / len(trees)
        avg_age = sum(t["age_years"] for t in trees) / len(trees)
        species_counts = {}
        for t in trees:
            species_counts[t["species"]] = species_counts.get(t["species"], 0) + 1
        confidence_counts = {}
        for t in trees:
            confidence_counts[t["confidence"]] = confidence_counts.get(t["confidence"], 0) + 1

        print(f"\n✅ RESULTADO:")
        print(f"   Árboles detectados:    {len(trees)}")
        print(f"   Tiempo de análisis:    {elapsed:.2f}s")
        print(f"   Biomasa total:         {total_biomass/1000:.2f} toneladas")
        print(f"   Área de copas:         {total_crown/10000:.4f} ha")
        print(f"   Altura promedio:       {avg_height:.2f} m")
        print(f"   Edad promedio:         {avg_age:.1f} años")
        print(f"   Distribución especies: {species_counts}")
        print(f"   Distribución confianza:{confidence_counts}")

        top3 = sorted(trees, key=lambda x: x["crown_area_m2"], reverse=True)[:3]
        print(f"\n   Top 3 por área de copa:")
        for t in top3:
            print(f"   - {t['tree_id']}: {t['species']} | {t['crown_area_m2']:.1f}m² copa | "
                  f"{t['height_m']:.1f}m altura | {t['biomass_kg']:.0f}kg biomasa | "
                  f"confianza={t['confidence']}")

        with_coords = [t for t in trees if t["centroid_lat"] != 0 and t["centroid_lon"] != 0]
        print(f"\n   Árboles con coordenadas: {len(with_coords)}/{len(trees)}")
        if with_coords:
            s = with_coords[0]
            print(f"   Ejemplo: {s['tree_id']} @ lat={s['centroid_lat']:.6f}, lon={s['centroid_lon']:.6f}")

        results_summary.append({
            "file": name, "trees": len(trees), "ok": True,
            "elapsed_s": round(elapsed, 2),
            "biomass_tons": round(total_biomass/1000, 2),
            "species": species_counts,
        })

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results_summary.append({"file": name, "trees": 0, "ok": False, "error": str(e)})

print(f"\n{'='*60}")
print("📊 RESUMEN SMOKE TEST")
print('='*60)
for r in results_summary:
    status = "✅" if r["ok"] else "❌"
    print(f"{status} {r['file']}: {r.get('trees',0)} árboles en {r.get('elapsed_s','?')}s")

all_ok = all(r["ok"] and r["trees"] > 0 for r in results_summary)
print(f"\n{'🟢 SMOKE TEST PASADO' if all_ok else '🔴 SMOKE TEST FALLIDO'}")
sys.exit(0 if all_ok else 1)
