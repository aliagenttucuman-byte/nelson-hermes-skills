#!/usr/bin/env python3
"""
ForestAI Smoke Test — corre el pipeline de análisis directo contra GeoTIFF
sin Docker ni BD. Valida que el core funciona end-to-end.
"""
import sys
import time
import json
sys.path.insert(0, "/home/server/proyectos/forestai-poc/backend")

from app.services.forest_analyzer import analyze_ortophoto
from app.services.allometric import classify_species, estimate_biomass, estimate_age

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

    steps_log = []
    def progress_callback(pct, step):
        steps_log.append(f"  [{pct:3d}%] {step}")
        print(f"  [{pct:3d}%] {step}")

    t0 = time.time()
    try:
        trees = analyze_ortophoto(filepath, progress_callback)
        elapsed = time.time() - t0

        if not trees:
            print("⚠️  No se detectaron árboles")
            results_summary.append({"file": name, "trees": 0, "ok": False})
            continue

        # Métricas agregadas
        total_biomass = sum(t["biomass_kg"] for t in trees)
        total_crown = sum(t["crown_area_m2"] for t in trees)
        avg_height = sum(t["height_m"] for t in trees) / len(trees)
        avg_age = sum(t["age_years"] for t in trees) / len(trees)

        species_counts = {}
        for t in trees:
            sp = t["species"]
            species_counts[sp] = species_counts.get(sp, 0) + 1

        confidence_counts = {}
        for t in trees:
            c = t["confidence"]
            confidence_counts[c] = confidence_counts.get(c, 0) + 1

        print(f"\n✅ RESULTADO:")
        print(f"   Árboles detectados: {len(trees)}")
        print(f"   Tiempo de análisis: {elapsed:.2f}s")
        print(f"   Biomasa total:      {total_biomass/1000:.2f} toneladas")
        print(f"   Área de copas:      {total_crown/10000:.4f} ha")
        print(f"   Altura promedio:    {avg_height:.2f} m")
        print(f"   Edad promedio:      {avg_age:.1f} años")
        print(f"   Distribución especies: {species_counts}")
        print(f"   Distribución confianza: {confidence_counts}")

        # Mostrar los 3 árboles más grandes
        top3 = sorted(trees, key=lambda x: x["crown_area_m2"], reverse=True)[:3]
        print(f"\n   Top 3 por área de copa:")
        for t in top3:
            print(f"   - {t['tree_id']}: {t['species']} | {t['crown_area_m2']:.1f}m² copa | {t['height_m']:.1f}m altura | {t['biomass_kg']:.0f}kg biomasa | confianza={t['confidence']}")

        # Verificar que hay coordenadas válidas
        with_coords = [t for t in trees if t["centroid_lat"] != 0 and t["centroid_lon"] != 0]
        print(f"\n   Árboles con coordenadas geográficas: {len(with_coords)}/{len(trees)}")
        if with_coords:
            sample = with_coords[0]
            print(f"   Ejemplo: {sample['tree_id']} @ lat={sample['centroid_lat']:.6f}, lon={sample['centroid_lon']:.6f}")

        results_summary.append({
            "file": name,
            "trees": len(trees),
            "ok": True,
            "elapsed_s": round(elapsed, 2),
            "biomass_tons": round(total_biomass/1000, 2),
            "species": species_counts,
        })

    except Exception as e:
        elapsed = time.time() - t0
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results_summary.append({"file": name, "trees": 0, "ok": False, "error": str(e)})

print(f"\n{'='*60}")
print("📊 RESUMEN SMOKE TEST")
print('='*60)
for r in results_summary:
    status = "✅" if r["ok"] else "❌"
    trees = r.get("trees", 0)
    elapsed = r.get("elapsed_s", "?")
    print(f"{status} {r['file']}: {trees} árboles en {elapsed}s")

all_ok = all(r["ok"] and r["trees"] > 0 for r in results_summary)
print(f"\n{'🟢 SMOKE TEST PASADO' if all_ok else '🔴 SMOKE TEST FALLIDO'}")
