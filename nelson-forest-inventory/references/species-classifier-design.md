# Species Classifier — Diseño e Implementación (2026-06-10)

## Motivación

YOLO detecta copas (one-class). Para identificar especie + salud sin anotar 1326 crops
individualmente, combinamos:
- LLM Vision por tile (barato, contextual) 
- CLIP clustering (agrupa copas similares visualmente)

## Flujo detallado

### Step 1: LLM Vision por tile (gpt-4o-mini)
- Sample N tiles (default 20, configurable 10/20/30/50)
- Prioriza tiles con más detecciones
- Resize a max 800px antes de enviar
- Prompt: lista completa de especies del NOA + instrucción de respuesta JSON array
- Output: `[{species, health, confidence, zone, notes}]` por tile
- Concurrencia: 5 requests paralelos con semáforo asyncio

### Step 2: CLIP embeddings de crops
- Crop de cada bbox con padding=10px
- Resize a 224px si más chico
- openai/clip-vit-base-patch32 local (huggingface transformers)
- Fallback si CLIP no disponible: histograma color RGB (12 features)
- Normalización L2

### Step 3: Clustering + asignación
- HDBSCAN (min_cluster_size = max(2, N//10)) — fallback KMeans k=5
- Para cada cluster: votar especie más frecuente de los tiles que contienen esos crops
- Label -1 (noise HDBSCAN) → "No clasificado"

## Archivos clave

```
pipeline/species_classifier.py     ← pipeline completo
backend/app/api/v1/process.py      ← endpoint /classify
backend/app/models/schemas.py      ← ClassifyRequest/Response, SpeciesSummary
backend/app/services/yolo_service.py  ← _job_results cache
frontend/src/components/SpeciesPanel.tsx  ← UI
frontend/src/api/client.ts         ← classifySpecies()
```

## ClassifyResponse

```json
{
  "job_id": "...",
  "total_trees": 1326,
  "classified_trees": 890,
  "n_clusters": 7,
  "tiles_sampled": 20,
  "elapsed_sec": 45.2,
  "species_summary": [
    {
      "species": "Quebracho blanco",
      "count": 423,
      "pct": 31.9,
      "avg_confidence": 0.72,
      "health_saludable": 380,
      "health_estresado": 35,
      "health_enfermo": 8
    }
  ]
}
```

## Costo estimado gpt-4o-mini

- 20 tiles × ~800px → ~800 tokens input/imagen (detail=high)
- 20 tiles × ~300 tokens output
- Total: ~22,000 tokens ≈ $0.013 por clasificación completa

## Dependencias nuevas en requirements.txt

```
aiohttp>=3.9
transformers>=4.40
torch>=2.0
scikit-learn>=1.4
hdbscan>=0.8
```

## Decisión: gpt-4o-mini vs gpt-4o

Nelson eligió gpt-4o-mini (mismo que ForestAI vlm_classifier.py).
Razón: costo/beneficio. Para copas de árboles desde arriba, la resolución
reducida de mini es suficiente para distinguir especies por color/textura/forma.
