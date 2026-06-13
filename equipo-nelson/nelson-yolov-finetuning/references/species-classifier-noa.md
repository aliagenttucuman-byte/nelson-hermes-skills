# Species Classifier NOA — pipeline completo

Implementado en `pipeline/species_classifier.py` en el repo `yolov-orientacion-poc`.

## Arquitectura

```
tiles_dir (JPGs generados por YOLO)
    │
    ├── Step 1: LLM Vision por tile (sample_tiles=20)
    │     gpt-4o-mini → [{species, health, confidence, zone}]
    │     Tiles priorizados por cantidad de detecciones
    │
    ├── Step 2: CLIP embeddings de crops
    │     openai/clip-vit-base-patch32 (local, vía transformers)
    │     Fallback: histograma de color HSV si CLIP no disponible
    │     → embeddings normalizados (n_crops, 512)
    │
    └── Step 3: Clustering + asignación
          HDBSCAN → KMeans fallback
          Voto por cluster usando tile_species del Step 1
          → cada det: {species, health, species_confidence, cluster_id}
```

## Endpoint

```
POST /api/v1/classify
{
  "job_id": "uuid-del-proceso",
  "sample_tiles": 20,
  "max_crops_per_tile": 15,
  "concurrency": 5
}
```

Respuesta:
```json
{
  "job_id": "...",
  "total_trees": 1326,
  "classified_trees": 480,
  "n_clusters": 7,
  "tiles_sampled": 20,
  "elapsed_sec": 42.3,
  "species_summary": [
    {
      "species": "Quebracho blanco",
      "count": 312,
      "pct": 23.5,
      "avg_confidence": 0.72,
      "health_saludable": 280,
      "health_estresado": 25,
      "health_enfermo": 7
    }
  ]
}
```

## System prompt para tiles (NOA)

```
You are an expert remote sensing analyst specializing in NOA forestry.
You analyze top-down aerial/drone RGB tile images from Tucumán, Argentina.
Known species: Quebracho blanco, Quebracho colorado, Algarrobo negro,
Algarrobo blanco, Cebil colorado, Horco quebracho, Tipa blanca,
Lapacho rosado, Palo borracho, Guarán, Cedro tucumano, Vinal.
Respond ONLY with JSON array:
[{"species": "...", "health": "saludable|estresado|enfermo",
  "confidence": 0.7, "zone": "NW|NE|SW|SE|CENTER", "notes": "..."}]
```

## Pitfalls

- **_job_results cache**: classify necesita las detecciones del último /process. `run_pipeline()` debe guardar en `_job_results[job_id]`.
- **asyncio dentro de FastAPI sync**: usar `asyncio.run()` en `classify_species_sync()`. FastAPI corre los endpoints sync en threadpool, no hay loop activo.
- **CLIP descarga modelo la primera vez**: ~350MB. El primer classify tarda más. Usar `transformers` no `openai-clip`.
- **HDBSCAN con pocos puntos**: si hay < 10 crops, min_cluster_size puede crear cluster único. Usar `min(2, n//10)`.
- **TypeScript: variable no usada rompe build**: tsc strict mode. No pasar props que no se usan en el componente.

## Frontend — SpeciesPanel

Aparece después de ResultsPanel cuando `appState === 'done'`.
Selector de sample_tiles (10/20/30/50) → botón verde → loading 30-90s → tabla de composición del rodal.

Color coding salud:
- saludable: #22c55e
- estresado: #f59e0b  
- enfermo: #ef4444
