# Pipeline de Etiquetado de Especies NOA — Referencia Técnica

Sesión: 2026-06-11. Resultado: dataset Avellaneda con 2 clases, mAP50=0.762.

## Flujo completo

```bash
# 1. Generar dataset con Claude (una sola vez)
cd /home/server/proyectos/yolov-orientacion-poc
set -a && source /home/server/proyectos/forestai-poc/.env && set +a

python3 pipeline/species_labeler.py \
  /ruta/ortofoto.tif \
  --output /tmp/species_dataset \
  --conf 0.15 --tile-size 640 --max-crops 3 --min-conf-vlm 0.30

# 2. (Opcional) Combinar múltiples TIFs
python3 dataset/build_species_dataset.py \
  --tifs /ruta/a.tif /ruta/b.tif \
  --output /tmp/species_dataset_final

# 3. Entrenar
python3 pipeline/trainer_species.py \
  --data /tmp/species_dataset/data.yaml \
  --base-model yolo26n.pt \
  --epochs 80 --batch 8 --patience 20 --device cpu \
  --name yolo26n_especies_noa_v1

# 4. Copiar modelo a la PoC
cp runs/species/yolo26n_especies_noa_v1/weights/best.pt \
   /home/server/proyectos/yolov-orientacion-poc/models/yolo26n_especies_noa_v1.pt

# 5. Rebuild Docker para que el nuevo model_key quede disponible
docker compose build --no-cache backend frontend
docker compose up -d
```

## Variables de entorno requeridas
```
OPENAI_API_KEY          # siempre requerido (fallback)
AZURE_ANTHROPIC_API_KEY # para LABELER_BACKEND=claude
AZURE_ANTHROPIC_BASE_URL=https://yizlafclc001.services.ai.azure.com/anthropic
AZURE_ANTHROPIC_MODEL=claude-sonnet-4-6
LABELER_BACKEND=claude  # default
```

## Parámetros clave de species_labeler.py

| Parámetro | Default | Descripción |
|---|---|---|
| conf | 0.15 | Confianza detección yolo26n |
| tile_size | 640 | Tamaño tile (debe = imgsz del modelo) |
| max_crops_per_tile | 3 | Límite VLM calls por tile (controla costo) |
| min_conf_vlm | 0.30 | Umbral mínimo confianza VLM para incluir en dataset |
| overlap | 128 | Overlap entre tiles (20% de 640) |
| centroid_dist_px | 60 | NMS global por centroide |

## Resultados Avellaneda (zona urbana)
- TIF: 36MB, 12622×7887px, 6cm/px, RGBA Pix4D
- 147 tiles generados (con stretch contraste)
- 153 copas detectadas con yolo26n conf=0.15
- 144 copas clasificadas por Claude Sonnet
- Distribución: Tipa blanca=117, Lapacho rosado=4, Otro=23
- Tiempo etiquetado Claude: ~13 min (786s)
- Tiempo entrenamiento CPU 80 epochs: ~35 min

## Resultado fine-tuning
```
mAP50:      0.762
mAP50-95:   0.518
Tipa blanca:    mAP50=0.902 (117 muestras)
Lapacho rosado: mAP50=0.623 (4 muestras)
Speed: 65.7ms inference/imagen en CPU
```

## Limitaciones conocidas
1. Dataset urbano → solo detecta Tipa blanca y Lapacho en zona urbana
2. Para Quebracho/Algarrobo/Cebil necesitar TIF de monte nativo
3. Claude va lento (~5-6s/copa) vs gpt-4o-mini (~0.5s) — usar solo para dataset
4. Lapacho con solo 4 muestras → mAP50 aceptable pero necesita más datos

## Próximo paso para mejorar
- Conseguir TIF de zona de monte nativo (campo, reserva, lote forestal)
- Correr species_labeler.py sobre ese TIF
- Mezclar datasets con build_species_dataset.py
- Re-entrenar con 5+ clases → target mAP50 >= 0.80
