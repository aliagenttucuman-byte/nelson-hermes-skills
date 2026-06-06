# NetFlora — Embrapa Acre (Referencia de integración)

## Qué es
Sistema de detección de especies forestales con YOLOv7 desarrollado por Embrapa Acre
(Brasil) con apoyo del Fondo JBS por la Amazonia. Open source bajo GPL 3.0.

GitHub: https://github.com/NetFlora/Netflora
Portal: https://www.embrapa.br/acre/netflora
Plugin QGIS: https://github.com/CarolinaGomesFerro/Netflora2

## Por qué importa para ForestAI
NetFlora resuelve el mismo problema que ForestAI (inventario forestal desde drones)
pero con un dataset de 100.000 hectares de Amazonia ya etiquetado y modelos entrenados.
Sus pesos y datos son reutilizables (GPL 3.0).

## Stack técnico
- Modelo: YOLOv7 (detect.py adaptado de WongKinYiu/yolov7)
- Input: ortomosaicos de drone (GeoTIFF)
- Pipeline: tiles.py → detect.py → results.py
- Output: CSV + Shapefile (.shp) con coordenadas georreferenciadas por árbol
- Dependencias: torch, torchvision, rasterio, geopandas, folium, opencv-python

## Especies detectadas (60+)
Organizadas en categorías:
- **Açaí**: Euterpe precatoria (açaí solteiro), açaí solteiro productivo
- **Castanheira**: Bertholletia excelsa (castaña de Brasil)
- **Palmeiras**: Paxiúba, Buritá, Jací, Ouricuri
- **Madeireras**: Cedro (Cedrela odorata), Pinho cuiabano, Caucho
- **No madeireras (PFNM)**: especies con valor extractivo no maderero
- **Ecológico**: árboles muertos, claros de bosque

## Modelo de datos (species_data.json)
```json
{
  "species_id": "ep01",
  "common_name": "Açaí solteiro",
  "scientific_name": "Euterpe precatoria Mart.",
  "category": "Açaí"
}
```

## Comando de detección
```bash
python detect.py --device 0 --weights model_weights.pt --img 1536
python results.py --graphics --conf 0.25
```

## Output generado (results.py)
- `results/csv/` — CSV con: class_id, common_name, lat, lon, confidence, bbox
- `results/shapefiles/` — Shapefile GIS con puntos georreferenciados
- Filtrable por algoritmo/categoría (Açaí, Palmeiras, Madeireras, etc.)

## Integración propuesta con ForestAI
1. Descargar model_weights.pt del repo de NetFlora
2. Importar catálogo de 60 especies (json/species_data.json + categories.json)
3. Conectar detect.py → results.py al backend de ForestAI como endpoint de procesamiento
4. Mostrar detecciones en mapa con filtro por categoría de especie
5. Diferencia visual entre "detección ForestAI" vs "detección NetFlora" con íconos distintos

## Plugin QGIS (Netflora2 — abril 2026)
Estructura: common/ + detection/ + flight_planner/
- Integra YOLO con PyTorch/ONNX directamente en QGIS
- Genera capas vectoriales + reporte HTML por análisis
- Útil para demostrar a clientes forestales sin UI web

## Recursos adicionales
- Ortofoto de ejemplo: https://drive.google.com/drive/folders/1OcRel7fJHALwm9ZAdU3rSlFwV_4iaZnp
- Curso EAD: https://ava.sede.embrapa.br/enrol/index.php?id=470
- COP30 (Belém, nov 2025): Embrapa presentó NetFlora como solución para Amazonia
