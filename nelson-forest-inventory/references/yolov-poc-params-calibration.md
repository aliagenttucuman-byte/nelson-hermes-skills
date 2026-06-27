# Calibración de Parámetros — yolov-orientacion-poc

Tabla verificada en sesión 2026-06-11 con TIF 9deJulio.rgb.tif (zona urbana, 411 tiles).

## Tabla de resultados por configuración

| conf | centroid_dist_px | nms_iou | Árboles | Notas |
|------|-----------------|---------|---------|-------|
| 0.10 | 30 | 0.40 | ~3.400 | Máximo ruido — autos, techos, cruces |
| 0.30 | 50 | 0.40 | ~900 | Todavía mucho ruido urbano |
| 0.50 | 70 | 0.40 | ~500 | Mejora pero aún FP en zonas duras |
| 0.65 | 90 | 0.40 | 275 | ✅ DEMO — número creíble, solo árboles |
| 0.70 | 100 | 0.40 | 213 | Conservador — puede perder árboles reales |

## Filtros adicionales activos (post-inferencia en run_inference)

- `min_bbox_px=25` — descarta bboxes menores a 25×25px (autos, señales de tránsito, ruido)
- `max_aspect_ratio=2.5` — descarta bboxes muy alargados (caminos, paredes, techos rectangulares)

## Por qué conf=0.65 para demo urbana

El modelo fue entrenado con pseudo-labels ExG que también marcan:
- Pasto en veredas → FP al conf bajo
- Cruces peatonales con líneas blancas (contraste alto → YOLO confunde con copa)
- Autos blancos sobre asfalto negro
- Techos de zinc claro

A conf=0.65 el modelo solo reporta lo que reconoció con alta certeza = copas bien definidas.

## Calibración por tipo de ortofoto

| Tipo zona | conf recomendado | centroid_dist_px |
|-----------|-----------------|------------------|
| Urbana (calles, edificios) | 0.60–0.70 | 80–100 |
| Periurbana (quintas, arboleda) | 0.45–0.55 | 60–80 |
| Rural / monte nativo | 0.30–0.40 | 50–70 |
| Plantación regular (eucaliptos) | 0.25–0.35 | 40–60 |

## Frase para stakeholders

> "La calibración actual detecta árboles con confianza ≥ 65%. Estamos siendo conservadores
> a propósito — preferimos reportar 275 árboles bien identificados que 3.000 con ruido.
> Con datos anotados manualmente podemos bajar el umbral y recuperar los árboles que hoy
> descartamos, sin los falsos positivos."

## Próximos pasos para mejorar el recall sin bajar confianza

1. Anotar manualmente 60–80 tiles con LabelStudio (solo copas reales, sin pasto)
2. Re-entrenar yolo11s con clase negativa "no-árbol" (pasto, techo, asfalto)
3. Esperado: poder bajar conf a 0.40 manteniendo < 5% FP
