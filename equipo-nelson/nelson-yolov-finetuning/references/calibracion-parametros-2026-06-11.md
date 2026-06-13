# Calibración de Parámetros — Sesión 2026-06-11 (actualizado sesión 2026-06-11 tarde)

## TIF de referencia
- Archivo: `doc_7a6ea9f8381b_9deJulio.rgb.tif`
- Tipo: ortofoto urbana/periurbana, ciudad 9 de Julio, NOA
- Resolución: ~6cm/px
- Tiles con tile=640: ~536 tiles | con tile=1024: ~141 tiles

---

## ⭐ Parámetros calibrados DEMO ReforestLatam (confirmado 2026-06-11)

```
model_key        = yolo11n_forestai
conf             = 0.65
iou              = 0.45
nms_iou          = 0.40
centroid_dist_px = 90
tile_size        = 640     ← CLAVE: 640, no 1024
overlap          = 128     (20% de 640)
```
**Resultado: 275 árboles** ✅ — número calibrado y verificado para presentación

---

## Barrido de tile_size (conf=0.65, centroid=90, modelo: yolo11n_forestai)

| tile_size | árboles | observación |
|-----------|---------|-------------|
| **640**   | **275** | ✅ calibrado para demo — sweet spot |
| 512       | 320     | más ruido de bordes |
| 1024      | 161     | modelo no detecta bien, ve 1 copa por tile |

**Por qué tile_size=640 es el correcto:** el modelo fue entrenado con imgsz=640. Con tiles de
1024px el campo visual es demasiado grande y el modelo fue calibrado para ver copas a escala 640px.
Con 1024px detecta solo 1 copa por tile (la más prominente) y se pierden el resto.

---

## Barrido de conf con tile=640px

| conf | árboles | observación |
|------|---------|-------------|
| 0.25 | 975 | mucho ruido urbano |
| 0.35 | 633 | aún con autos y techos |
| 0.45 | 401 | borde razonable |
| **0.65** | **275** | ✅ demo calibrada |

---

## Barrido ExG+Watershed (tile=1024, centroid variable)

| model_key | centroid_dist | árboles | observación |
|-----------|--------------|---------|-------------|
| exg (sin watershed) | 90  | 1801 | excesivo |
| exg (sin watershed) | 150 | 1177 | aún alto |
| exg (sin watershed) | 200 | 880  | razonable pero cajas grandes |
| exg (watershed)     | 90  | 323  | copas individuales limpias |
| exg (watershed)     | 90  | 449  | (UI con centroid=60 por bug de default) |

**ExG+Watershed limitaciones en zona urbana:**
- Detecta personas en ropa rosa/roja como "vegetación verde"
- Detecta vehículos de color similar al verde
- No distingue árbol de arbusto
- Útil para bosques nativos con poca infraestructura urbana, no para demo 9deJulio

---

## Parámetros ModelSelector.tsx — defaults por modelo (UI, sesión 2026-06-11)

```typescript
const MODEL_DEFAULTS = {
  yolo11n_forestai: { centroid: 90,  conf: 0.65, tile_size: 640  },
  yolo11n:          { centroid: 60,  conf: 0.25, tile_size: 640  },
  yolov8n:          { centroid: 60,  conf: 0.25, tile_size: 640  },
  exg:              { centroid: 90,  conf: 0.50, tile_size: 1024 },
}
```
Al cambiar el selector de modelo, conf + centroid + tile_size se ajustan solos.

---

## PITFALL — `docker compose restart` no aplica cambios de pipeline

El pipeline (`pipeline/`) se **copia** en el Docker build. `restart` solo reinicia el proceso
dentro del contenedor existente — no actualiza los archivos copiados.

**Patrón correcto para aplicar cambios de código:**
```bash
docker compose build backend
docker compose stop backend && docker compose rm -f backend
docker compose up -d backend
# verificar:
sleep 4 && curl -s http://localhost:9020/api/v1/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['models_available'])"
```

**Síntoma:** model_key nuevo (`exg`) no aparece en `models_available` aunque el código en host está correcto.

---

## Conclusiones

1. **Para demo ReforestLatam:** siempre usar `yolo11n_forestai` con tile=640, conf=0.65 → 275 árboles
2. **ExG+Watershed**: funciona para bosque rural, no para zona urbana densa (ruido de vehículos y personas)
3. **tile=1024 con yolo11n_forestai**: underperforms porque el modelo fue entrenado a 640px
4. Para bosque nativo sin infraestructura urbana: probar ExG+Watershed centroid=90, tile=1024
