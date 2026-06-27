# Ultralytics AI in Agriculture — Stack Relevante para ForestAI

Fuente: https://www.ultralytics.com/solutions/ai-in-agriculture
Revisado: 2026-06-10

## Por qué es relevante para ForestAI

Ultralytics (empresa detrás de YOLO) tiene stack nativo para:
- Drone integration (campo explícito en su plataforma)
- Aerial crop monitoring y field mapping
- SAM 2 para segmentación de vegetación a nivel píxel
- Edge deployment (modelos que corren en hardware del drone)

Caso de uso directo: reemplazar/complementar el módulo de detección ExG+DeepForest con
YOLO11 fine-tuneado sobre ortofotos de Tucumán para mejorar recall en árboles pequeños y zonas con sombra.

## Modelos Disponibles

| Modelo     | Uso principal                              | Ventaja para ForestAI                        |
|------------|--------------------------------------------|-----------------------------------------------|
| YOLO11     | Detección de objetos en tiempo real        | Fine-tuning sobre copas de árboles locales    |
| SAM 2      | Segmentación a nivel píxel                 | Polígonos de copa más precisos que SAM1       |
| FastSAM    | Segmentación rápida                        | Alternativa más veloz para demos              |
| RT-DETR    | Detection Transformer alta precisión       | Mejor en objetos pequeños (árboles chicos)    |
| YOLOv8/9   | Generaciones previas, aún soportadas       | Compatibles con pipelines existentes          |

## Stack Actual ForestAI vs Potencial con Ultralytics

```
ACTUAL:
Tile TIFF → ExG filter → DeepForest (RetinaNet) → SAM1 → VLM (claude-haiku)

POTENCIAL:
Tile TIFF → YOLO11 fine-tuned → SAM2 → VLM (claude-haiku)
              ↑ mejor recall        ↑ polígonos más precisos
```

## Métricas Publicadas por Ultralytics (agricultura general)

- Crop disease detection: 95%+ accuracy
- Reducción pesticide: 30%
- Yield prediction improvement: 25%
- Water usage reduction: 20%

Estas métricas son genéricas para agricultura. Para inventario forestal con ortofotos RGB
los números relevantes serían recall de copas — fine-tuning local es necesario.

## Fine-tuning de YOLO11 — Viabilidad

Para ForestAI, el caso ideal es fine-tuning sobre ortofotos de Tucumán (ya disponibles):
- `9deJulio.rgb.tif` y `Avellaneda.rgb.tif` como base de training/validation
- Labels: bounding boxes de copas detectadas por DeepForest (bootstrap labels)
- Ventaja: YOLO11 entrenado en imágenes locales >> DeepForest (entrenado en bosques de EEUU)
- Problema identificado en sesiones previas: Avellaneda solo detectó 3 árboles con DeepForest
  porque el modelo fue entrenado en bosques densos norteamericanos. YOLO11 fine-tuned local
  resolvería esto.

## Acceso

- Ultralytics HUB: https://hub.ultralytics.com/ (free signup)
- Pre-trained models: disponibles en días
- Custom training: 2-8 semanas con datos propios
- API + SDK para integración con sistemas existentes (FastAPI compatible)
- Edge deployment: sí, compatible con hardware de drone

## Integración en Roadmap ForestAI

Roadmap actual: OpenCV5 + Opik + Gemini Live
Agregar: YOLO11 + SAM2 como reemplazo del módulo de segmentación

Prioridad sugerida:
1. Spike: instalar ultralytics, correr YOLO11 preentrenado sobre tile de 9deJulio
2. Evaluar recall vs DeepForest actual (baseline: 257 árboles en 9deJulio con 4096px)
3. Si mejora >20%: considerar fine-tuning con labels bootstrap de DeepForest
4. SAM2 (en vez de SAM1): mejor precisión de polígonos, misma interfaz

## Nota de Compliance

Los modelos DeepForest, SAM, VLM/claude-haiku no se mencionan en la demo ReforestLatam.
Si se integra YOLO11, aplica la misma regla: NO revelar en /demo.
Solo mencionar "visión por computadora avanzada" o "modelos propietarios".
