# YOLOv Benchmark — Sesion 2026-06-10

## Contexto

Primera corrida de fine-tuning YOLO11n sobre ortofotos de Tucuman/9deJulio/Avellaneda.
Dataset generado con pseudo-labels ExG. Corrido en CPU (ai-server, sin GPU dedicada).

---

## Experimento v1 — Fallo

**Config:**
- Tiles: 5 (tiles previos del spike ForestAI)
- imgsz: 1024
- batch: 2
- epochs pedidos: 50 / completados: 19 (early stop en patience=15)
- Best epoch: 4

**Resultados:**
- mAP50: 0.0017
- mAP50-95: 0.0006
- Precision: 0.0033
- Recall: 0.0238
- Detecciones en inferencia: 0 (en todos los tiles de validacion)

**Diagnostico:** Dataset insuficiente + batch=2 en CPU = gradiente muy ruidoso.
El modelo aprende cero patrones utiles con solo 5 imagenes.

---

## Experimento v2 — Funciona

**Config:**
- Tiles base: 24 (4 TIFs x 6 tiles cada uno, stride=768, min_boxes=5)
- Imagenes train: 152 (24 tiles x 4 augmentaciones: orig/flipH/flipV/flipHV + extra bright/dark)
  - Nota: el script de augmentacion de esta sesion hizo 8 variantes (incluyo brillo), no 4.
  - El build_dataset.py del repo final hace 4 variantes.
- imgsz: 640
- batch: 8
- epochs pedidos: 80 / completados: 39 (early stop en patience=20)
- Best epoch: 14
- Tiempo total: 0.433 hs (~26 min) en CPU

**Resultados:**
- mAP50: 0.4804
- mAP50-95: 0.1825
- Precision: 0.5753
- Recall: 0.4623

**Detecciones en inferencia (conf=0.25, iou=0.5):**

| Tile | YOLO11 | ExG | Delta |
|------|--------|-----|-------|
| Avellaneda_r0_c69 | 16 | ~20 | -4 |
| 9deJulio_r0_c23 | 6 | ~10 | -4 |
| tucuman_C_r0_c23 | 48 | 45 | +3 |
| Avellaneda_r0_c76 | 16 | ~20 | -4 |
| 9deJulio_r0_c46 | 5 | ~8 | -3 |

**Weights guardados en:** `/home/server/.hermes/hermes-agent/runs/detect/runs/forestai_v2/weights/best.pt`

---

## Comparativa visual (imagen generada)

`/home/server/brainstorming/2026-06-10-forestai-yolo11-detection/spike/resultados_v2/comparativa_exg_vs_yolo11.jpg`

Tile: tucuman_C_r0_c23 (640x640px)
- Panel izquierdo: ExG con 45 bboxes verdes
- Panel derecho: YOLO11 con 48 bboxes naranjas
- Resultado: numeros muy similares, YOLO11 aprende el patron ExG correctamente

---

## Proximos pasos para mAP50 >= 0.65

1. Anotacion manual de 50 tiles con LabelStudio (~3hs labeling)
2. Reemplazar pseudo-labels ExG de train con anotaciones manuales
3. Agregar clase "arbusto" para diferenciarlo del arbol
4. Comparar yolov8n vs yolo11n vs yolov9c con el mismo dataset mejorado (spike 001)

---

## Notas de infraestructura

- La sesion de training del v2 corre en foreground con background process (session_id: proc_6a21eb662d6a)
- Clamping del wait: Hermes limita el wait a 60s aunque se pidan 600s
  - Workaround: usar poll() en loop en lugar de wait() con timeout largo
- Los pesos del v2 estan en el hermes-agent dir (runs/detect/runs/forestai_v2/) no en el repo
  - Mover a /home/server/proyectos/yolov-orientacion-poc/runs/ en la proxima sesion
