# Tablas Alométricas INTA — ForestAI PoC

Coeficientes usados en `app/services/allometric.py`.
Modelo: `biomasa_kg = a * (height_m ^ b) * (crown_area_m2 ^ c)`
Edad: `age_years = height_m / growth_rate_per_year`

## Coeficientes por Especie (actualizado mayo 2026)

Fuentes:
- INTA EEA Bariloche: Gayoso et al. — Ecuaciones biomasa Patagonia
- INTA EEA Concordia: tablas Eucalyptus Mesopotamia
- INTA EEA Santiago del Estero: Prosopis spp. Chaco
- INTA EEA Anguil: Prosopis caldenia Espinal pampeano
- Proyecto REDD+ Argentina — MAyDS 2019
- FAO 2012 — Global Forest Resources Assessment

| Especie     | a     | b    | c    | Tasa (m/año) | Coef. biomasa (t/m³) | IMA (m³/ha/año) | Turno (años) | EEA INTA                  |
|-------------|-------|------|------|--------------|----------------------|-----------------|--------------|---------------------------|
| eucalipto   | 45.2  | 1.80 | 0.60 | 2.0          | 0.498                | 25.0            | 12           | Concordia — E. grandis    |
| pino        | 38.7  | 1.90 | 0.55 | 1.5          | 0.572                | 12.5            | 35           | Bariloche — P. ponderosa  |
| quebracho   | 62.1  | 1.60 | 0.70 | 0.6          | 0.780                | 2.8             | 60           | Santiago del Estero       |
| algarrobo   | 28.4  | 1.70 | 0.65 | 0.8          | 0.810                | 3.2             | 50           | Santiago del Estero       |
| araucaria   | 71.3  | 1.50 | 0.80 | 0.5          | 0.530                | 2.8             | —            | Bariloche (ESPECIE PROT.) |
| lenga       | 52.6  | 1.65 | 0.72 | 0.5          | 0.660                | 4.5             | 80           | Bariloche — N. pumilio    |
| caldén      | 34.8  | 1.55 | 0.68 | 0.4          | 0.790                | 2.1             | 60           | Anguil — P. caldenia      |
| desconocida | 40.0  | 1.70 | 0.60 | 1.0          | 0.600                | —               | —            | FAO 2012 genérico         |

## Ecorregiones Argentina por Especie

| Especie   | Ecorregión principal                                                |
|-----------|---------------------------------------------------------------------|
| eucalipto | Mesopotamia (Misiones, Entre Ríos, Corrientes)                      |
| pino      | Patagonia (Neuquén, Río Negro, Chubut)                              |
| quebracho | Gran Chaco (Santiago del Estero, Chaco, Formosa)                    |
| algarrobo | Gran Chaco / Espinal (Santiago del Estero, La Pampa)                |
| araucaria | Bosque Andino-Patagónico (Neuquén) — ESPECIE PROTEGIDA              |
| lenga     | Bosque Andino-Patagónico (Tierra del Fuego, Santa Cruz, Neuquén)    |
| caldén    | Espinal pampeano (La Pampa, San Luis, Córdoba sur)                  |

## Reglas de Clasificación RGB por Especie

Rangos amplios necesarios — colores varían por hora, estación, cámara:

| Especie   | R range   | G range   | B range   | G dominante | Textura (0-1) |
|-----------|-----------|-----------|-----------|-------------|---------------|
| eucalipto | 40–200    | 60–220    | 20–180    | sí          | 0.2–0.7       |
| pino      | 30–160    | 50–190    | 15–140    | sí          | 0.45–0.99     |
| quebracho | 60–220    | 50–200    | 20–150    | no          | 0.3–0.9       |
| algarrobo | 50–210    | 70–230    | 15–160    | sí          | 0.1–0.6       |
| araucaria | 20–150    | 40–180    | 10–130    | sí          | 0.55–0.99     |
| lenga     | 35–170    | 55–200    | 20–150    | sí          | 0.15–0.55     |
| caldén    | 55–200    | 65–210    | 20–140    | no          | 0.2–0.65      |

**Confianza:**
- score >= 0.8 → "alto"
- score >= 0.5 → "medio"
- score < 0.5  → "bajo" + especie = "desconocida"

**CRÍTICO:** Usar rangos AMPLIOS. Rangos estrechos → mayoría de árboles quedan como "desconocida".

## Estimación de Altura desde Área de Copa

Relación empírica usada en el pipeline (sin LiDAR):
```
radio_m = sqrt(area_m2 / pi)
height_m = 2.5 * radio_m
```

Válido para copas circulares medianas. Subestima árboles muy altos y esbeltos.

## Limitaciones Conocidas

- Los rangos RGB asumen imágenes tomadas al mediodía con luz solar directa
- Quebracho y algarrobo son difíciles de distinguir con RGB puro (necesitaría NIR o NDVI)
- Lenga y caldén son especies nuevas — clasificación experimental, validar con imágenes reales
- La estimación de altura sin LiDAR tiene error ±30% para árboles > 15m
- En plantaciones con filas regulares, el watershed funciona mejor que en bosque nativo
- Araucaria araucana es especie protegida — en producción agregar alerta en UI al detectarla
