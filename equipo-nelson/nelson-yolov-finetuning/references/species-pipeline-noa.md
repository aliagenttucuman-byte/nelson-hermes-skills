# Pipeline de Fine-tuning de Especies NOA — yolo26n + gpt-4o-mini

Sesión: 2026-06-11

## Objetivo
Fine-tunear yolo26n para detectar Y clasificar 13 especies nativas del NOA/Tucumán
en ortofotos de drone (GeoTIFF RGB, ~6cm/px).

## Arquitectura del pipeline (Opción A — stack propio, NO YOLOv7)

```
GeoTIFF ortofoto
      ↓
tiler.py → tiles 640px + overlap 128px
      ↓
yolo26n (pretrained) → detecciones de copas genéricas
      ↓
NMS global (iou=0.45, centroid=60px)
      ↓
crop_tree() → recorte de cada copa + padding 10px
      ↓
gpt-4o-mini Vision → especie + confianza por copa
      ↓
Filtrar conf_vlm >= 0.30 → descartar etiquetas inseguras
      ↓
Anotaciones YOLO multi-clase → images/ + labels/
      ↓
trainer_species.py → fine-tuning yolo26n (80 epochs, imgsz=640, batch=8, CPU)
```

## Archivos creados (en yolov-orientacion-poc)

| Archivo | Rol |
|---------|-----|
| `pipeline/species_labeler.py` | Detecta copas + clasifica con VLM → genera dataset |
| `dataset/build_species_dataset.py` | Combina múltiples TIFs, split train/val 80/20 |
| `pipeline/trainer_species.py` | Fine-tuning yolo26n multi-clase |

## Especies del NOA configuradas (13 clases)

```python
ESPECIES_NOA = [
    "Quebracho blanco",    # class_id 0
    "Quebracho colorado",  # 1
    "Algarrobo negro",     # 2
    "Algarrobo blanco",    # 3
    "Cebil colorado",      # 4
    "Tipa blanca",         # 5
    "Lapacho rosado",      # 6
    "Palo borracho",       # 7
    "Cedro tucumano",      # 8
    "Horco quebracho",     # 9
    "Guarán",              # 10
    "Vinal",               # 11
    "Otro",                # 12 — catch-all
]
```

## Parámetros calibrados (Avellaneda, 2026-06-11)

- Detección: conf=0.15, iou=0.45, tile=640, overlap=128, centroid=60
- VLM: gpt-4o-mini, detail=low, max_crops_per_tile=15, min_conf_vlm=0.30
- Entrenamiento: epochs=80, batch=8, patience=20, lr0=0.005, device=cpu

## Costo estimado VLM

Avellaneda: 186 copas detectadas / 87 tiles con detecciones
Con max_crops=15 → máx ~87×15 = 1305 crops pero en la práctica muchos tiles tienen < 5 copas.
Costo real estimado: ~$0.02-0.05 por TIF con gpt-4o-mini en detail=low.

## Pitfalls descubiertos en esta sesión

### 1. `confidence` vs `conf` en detecciones
run_inference() devuelve dicts con clave `confidence`, NO `conf`.
```python
# CORRECTO
tile_dets_sorted = sorted(tile_dets, key=lambda d: d.get("confidence", 0.0), reverse=True)
# INCORRECTO — KeyError
tile_dets_sorted = sorted(tile_dets, key=lambda d: d["conf"], reverse=True)
```

### 2. OPENAI_API_KEY — cargar del .env con `source`
```bash
set -a && source /home/server/proyectos/forestai-poc/.env && set +a
python3 pipeline/species_labeler.py ...
```
O en execute_code:
```python
import subprocess
result = subprocess.run(
    "source /home/server/proyectos/forestai-poc/.env && echo $OPENAI_API_KEY",
    shell=True, executable="/bin/bash", capture_output=True, text=True
)
api_key = result.stdout.strip()
```

### 3. Dataset multi-clase requiere >=5 ejemplos por clase
Clases con menos de 5 anotaciones tienen mAP50 cercano a 0.
`build_species_dataset.py` filtra automáticamente: `valid_classes = [e for e in ESPECIES_NOA if total_species.get(e, 0) >= 5]`
Si hay pocas muestras, combinar más TIFs o bajar min_conf_vlm a 0.20.

## Uso rápido

```bash
cd /home/server/proyectos/yolov-orientacion-poc

# 1. Generar dataset desde Avellaneda (test rápido con 3 crops/tile)
set -a && source /home/server/proyectos/forestai-poc/.env && set +a
python3 pipeline/species_labeler.py \
  /home/server/.hermes/document_cache/doc_877ea5356955_Avellaneda.rgb.tif \
  --output /tmp/species_test \
  --conf 0.15 --max-crops 3

# 2. Dataset completo (Avellaneda + 9deJulio)
python3 dataset/build_species_dataset.py \
  --output /tmp/species_dataset_final \
  --max-crops 15

# 3. Entrenar
python3 pipeline/trainer_species.py \
  --data /tmp/species_dataset_final/data.yaml \
  --name yolo26n_especies_noa \
  --epochs 80
```

## Estado (2026-06-11)

- Pipeline creado y lintado ✅
- Bug `confidence` vs `conf` detectado y corregido ✅
- Test con Avellaneda + 3 crops/tile → corriendo al final de la sesión
- Resultados del test y mAP50 pendientes (sesión siguiente)
