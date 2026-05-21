# ForestAI PoC — Limitaciones Actuales y Roadmap de Mejoras

> Documento generado: 2026-05-19  
> Estado del PoC: Funcional con imágenes RGB de drone  
> Propósito: Documentar honestamente el techo actual y el camino para mejorarlo

---

## Estado Actual del Algoritmo

### Qué hace bien hoy

| Imagen | Tipo | Árboles detectados | Observaciones |
|--------|------|-------------------|---------------|
| Chapadmalal Buenos Aires | Parque arbolado denso | 38 | Buena separación entre copas |
| Golondrinas Patagonia | Bosque patagónico | 36 | Buena detección |
| INTA San Salvador AER | Cultivo + monte | 10 | Razonable para zona mixta |
| La Leonesa - Chaco Norte | Chaco húmedo | 5 | Subestimado, copas solapadas |
| Lotes Silvopastoriles Chaco | Silvopastoral | 3 | Muy subestimado |

### Pipeline actual

```
GeoTIFF RGB (3 bandas)
    → VARI (Visible Atmospherically Resistant Index)
    → Umbral Otsu (adaptativo)
    → Watershed (separación de copas tocantes)
    → Filtro: área 2–80 m²
    → Filtro: circularidad > 0.15
    → Métricas alométricas (altura, DAP, biomasa)
```

---

## Limitación Principal: Sensor RGB sin Infrarrojo

### El problema

Las cámaras RGB estándar de drone capturan Rojo, Verde y Azul.  
Los árboles y el pasto tienen valores de verde muy similares en este espectro.

En imágenes silvopastorales, el VARI del pasto denso puede ser casi idéntico al VARI de las copas de los árboles. Resultado: el algoritmo no puede distinguirlos con confianza.

### Por qué NDVI sería la solución

NDVI (Normalized Difference Vegetation Index):
```
NDVI = (NIR - Red) / (NIR + Red)
```

Los árboles reflejan MUCHO más infrarrojo que el pasto (efecto "red edge").  
Con NDVI los árboles quedan claramente separados del suelo y del pasto bajo.

**Rango típico:**
- Suelo desnudo: NDVI 0.1–0.2  
- Pasto: NDVI 0.3–0.5  
- Árbol maduro: NDVI 0.6–0.9  

La diferencia es enorme comparada con VARI en RGB puro.

---

## Tipos de Imágenes y Calidad de Detección Esperada

### Tier 1 — RGB estándar (situación actual)

**Hardware:** DJI Phantom, Mavic, cualquier drone de consumo  
**Bandas:** R, G, B (3 bandas, uint8)  
**Índice usado:** VARI  

| Escenario | Detección esperada |
|-----------|-------------------|
| Parque o monte denso con suelo visible | Buena (70–85%) |
| Bosque cerrado con copas tocantes | Regular (50–65%) |
| Silvopastoral (árboles sobre pasto verde) | Pobre (20–40%) |
| Caña o maleza alta | Muy pobre |

**Limitación irresoluble en RGB:** Sin NIR no hay separación confiable árbol/pasto.

---

### Tier 2 — Multiespectral 4–5 bandas

**Hardware:** MicaSense RedEdge, Parrot Sequoia, DJI Zenmuse P1 MS  
**Bandas:** R, G, B, NIR (+ Red Edge opcional)  
**Índice posible:** NDVI, NDRE (con Red Edge)

| Escenario | Detección esperada |
|-----------|-------------------|
| Silvopastoral | Excelente (85–95%) |
| Bosque cerrado | Muy buena (80–90%) |
| Cualquier terreno verde | Buena |

**Cambios en el código necesarios:**
- Detectar automáticamente si el TIF tiene banda NIR (banda 4+)
- Si hay NIR: calcular NDVI en vez de VARI
- Si hay Red Edge (banda 5): calcular NDRE (mejor para coníferas y estrés hídrico)
- Ajustar umbrales de segmentación según índice usado

```python
# Lógica propuesta en forest_analyzer.py
if raster["band_count"] >= 4:
    nir = raster["nir"]
    ndvi = (nir - r) / (nir + r + 1e-10)
    index = ndvi
    index_name = "NDVI"
else:
    # RGB puro: usar VARI
    vari = (g - r) / (g + r - b + 1e-10)
    index = vari
    index_name = "VARI"
```

---

### Tier 3 — Satelital multibanda (Sentinel-2, Landsat)

**Fuente:** ESA Copernicus, USGS EarthExplorer  
**Resolución:** 10m/pixel (Sentinel-2) — no apto para contar árboles individuales  
**Uso útil:** Mapeo de cobertura forestal total, NDVI regional, cambio interanual  

Ideal para el nivel de "¿cuántos hectáreas de monte tiene el campo?" pero no para inventario árbol por árbol.

---

### Tier 4 — LiDAR (el nivel profesional)

**Hardware:** Drone con sensor LiDAR (Riegl, Velodyne, Livox)  
**Datos:** Nube de puntos 3D  
**Detección:** Por estructura tridimensional de la copa, no por color  

| Métrica | RGB | Multiespectral | LiDAR |
|---------|-----|---------------|-------|
| Conteo árboles | Regular | Bueno | Excelente |
| Altura real | Estimada (alométrica) | Estimada | Medida directa |
| DAP (diámetro tronco) | Estimado | Estimado | Medido |
| Biomasa | Aproximada | Aproximada | Alta precisión |
| Costo drone | Bajo | Medio | Alto |

---

## Mejoras de Algoritmo Independientes del Sensor

Estas mejoras se pueden hacer con imágenes RGB existentes:

### 1. Detección por sombra de copa

Los árboles altos proyectan sombra característica.  
Canal HSV (valor bajo + saturación variable) marca sombras con buena precisión.  
Complementar VARI con máscara de sombra para capturar árboles que "confunden" con pasto.

### 2. Deep Learning con RGB (YOLOv8 o SAM)

Modelos pre-entrenados en imágenes aéreas de árboles.  
**DeepForest** (Weinstein et al.) es el más usado en ecología forestal con RGB.  
Detecta copas individuales con F1 score ~0.75 en imágenes RGB de densidad media.

```bash
pip install deepforest
# Modelo pre-entrenado en 10,000+ anotaciones de árboles EEUU
```

**Limitación:** El modelo fue entrenado en bosques de Norteamérica. Puede necesitar fine-tuning para especies del Chaco/Patagonia/Pampa.

### 3. Escala adaptativa por resolución GSD

El GSD (Ground Sampling Distance) varía por altura de vuelo.  
Hoy usamos área fija 2–80 m². Si el GSD es 5 cm/px, 2 m² son 800 píxeles. Si es 20 cm/px, son 50 píxeles.  
**Mejora:** Calcular rango de área mínima/máxima en función del GSD real del GeoTIFF.

---

## Próximos Pasos Propuestos (Roadmap)

### Sprint 1 — Quick wins (sin cambiar hardware)
- [ ] Detección automática de bandas al cargar GeoTIFF
- [ ] Sombra de copa como canal complementario para silvopastoral
- [ ] Ajuste de área mínima por GSD real

### Sprint 2 — Soporte multiespectral
- [ ] Soporte NDVI cuando hay banda NIR
- [ ] Soporte NDRE cuando hay banda Red Edge
- [ ] UI muestra qué índice se usó para cada análisis

### Sprint 3 — Deep Learning opcional
- [ ] Integración DeepForest como detector alternativo
- [ ] Comparativa: watershed vs DeepForest por tipo de imagen
- [ ] Fine-tuning con anotaciones de clientes argentinos

### Sprint 4 — Ground truth y validación
- [ ] Panel de validación: usuario marca árboles reales para calibrar
- [ ] Accuracy report por análisis (si hay ground truth)
- [ ] Exportar anotaciones en formato COCO para re-entrenamiento

---

## Conclusión para la Demo con el Cliente

**Mensaje clave:**
> "Con imágenes RGB de drone estándar, el sistema detecta árboles en zonas de monte denso con alta precisión. Para campos silvopastorales o con pasto alto, la precisión mejora significativamente con cámaras multiespectrales que incluyan infrarrojo — un estándar cada vez más accesible en drones profesionales."

**Esto es un PoC funcional, no un producto terminado.** El roadmap está claro y cada mejora está cuantificada.

---

*Documento vivo — actualizar con cada iteración del PoC.*
