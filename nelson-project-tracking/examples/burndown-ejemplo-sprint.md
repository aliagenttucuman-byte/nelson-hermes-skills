# Ejemplo: Burndown Sprint ForestAI v1 (2 semanas)

> **Este es un ejemplo completo con datos ficticios para mostrar el producto final a Gino/Luigi.**

## Datos del sprint

- **Proyecto:** ForestAI
- **Sprint:** Sprint 1 — MVP análisis NDVI
- **Fechas:** 2026-06-02 → 2026-06-13 (2 semanas, 10 días hábiles)
- **Capacity:** 80h (Nelson 30h, Gino 25h, Ricky 25h)
- **Planeado:** 56h en 8 tareas (18 puntos fibonacci)
- **Goal:** MVP funcional del análisis NDVI de ortofotos

## Las 8 tareas planeadas

| ID | Tarea | Estimate | Points | Asignado | Real h | Status |
|----|-------|----------|--------|----------|--------|--------|
| T-01 | Endpoint upload de ortofoto | M | 3 | Nelson | 4.0 | ✅ done día 2 |
| T-02 | Celery task para procesamiento | M | 3 | Ricky | 5.5 | ✅ done día 4 |
| T-03 | Integración con PostGIS | L | 5 | Ricky | 9.0 | ✅ done día 6 |
| T-04 | Frontend: componente de mapa | L | 5 | Nelson | 7.5 | ✅ done día 8 |
| T-05 | Cálculo NDVI con rasterio | M | 3 | Gino | 3.0 | ✅ done día 5 |
| T-06 | Tests e2e del flujo | M | 3 | Nelson | 4.5 | ✅ done día 9 |
| T-07 | Docs + deploy a staging | S | 2 | Gino | 2.0 | ✅ done día 10 |
| T-08 | Demo con Pablo | S | 2 | Nelson | 1.5 | ✅ done día 10 |

**Totales:** Planeado 18 puntos / 56h — Real 18 puntos / 37h — Accuracy 1.0 (mejor de lo esperado)

**Nota:** en este sprint "sueño" la estimación quedó pesimista (sumamos 56h, completamos 37h). La velocity real es 18 puntos, mejor que los 14 planeados originalmente en base al sprint anterior.

## Tabla de burndown día por día

| Día | Fecha | Ideal (h restantes) | Real (h restantes) | Comentario |
|-----|-------|---------------------|---------------------|------------|
| 1 | 06-02 (lun) | 50.4 | 52.0 | Empezamos tarde, ajustamos |
| 2 | 06-03 (mar) | 44.8 | 48.0 | T-01 done, T-02 en marcha |
| 3 | 06-04 (mié) | 39.2 | 42.0 | |
| 4 | 06-05 (jue) | 33.6 | 36.5 | T-02 done |
| 5 | 06-06 (vie) | 28.0 | 33.5 | T-05 done |
| 6 | 06-09 (lun) | 22.4 | 24.5 | T-03 done |
| 7 | 06-10 (mar) | 16.8 | 17.0 | En línea |
| 8 | 06-11 (mié) | 11.2 | 9.5 | T-04 done, **adelantados** |
| 9 | 06-12 (jue) | 5.6 | 5.0 | T-06 done |
| 10 | 06-13 (vie) | 0.0 | 0.0 | T-07, T-08 done — **cerrado** |

## Gráfico (ASCII)

```
Horas
restantes
60 ┤
   │ ●
55 ┤   ╲ ideal
   │     ╲
50 ┤  ●   ╲
   │        ╲
45 ┤    ●    ╲
   │          ╲
40 ┤      ●    ╲
   │            ╲
35 ┤        ●     ╲
   │              ╲
30 ┤          ●     ╲
   │                ╲
25 ┤            ●     ╲
   │                  ╲
20 ┤              ●     ╲
   │                    ╲
15 ┤                ●     ╲
   │                      ╲
10 ┤                  ●     ╲
   │                        ╲
 5 ┤                    ●     ╲
   │                          ●
 0 ┤________________________●_____●___
   1  2  3  4  5  6  7  8  9  10  día

   ● = real restante
   línea = ideal (decrece linealmente)
```

## Lectura del gráfico

1. **Días 1-3: atrasados** (entre 2-3h arriba de la ideal). Normal en sprints nuevos.
2. **Días 4-5: recuperación** porque T-02 y T-05 se completaron en menos tiempo del estimado.
3. **Días 6-7: en línea**, sprint estabilizado.
4. **Días 8-10: adelantados**, sprint cerrado antes con todo done.

## Resumen final

```
Sprint 1 — ForestAI MVP
═══════════════════════════════════════════
Goal:        MVP funcional del análisis NDVI ✅
Velocity:    18 puntos (planeado 14, +28% sobre plan)
Accuracy:    1.51 (real muy por debajo de estimado)
Horas:       37h reales / 56h estimadas (-34%)
Carry-over:  0
Estado:      🟢 Excelente
═══════════════════════════════════════════
```

## Aprendizajes

1. **Las estimaciones de T-03 (PostGIS) y T-04 (frontend) fueron pesimistas.** En el próximo sprint, tareas similares pueden ser M en lugar de L.
2. **Gino fue muy preciso** (3.0h real vs 3.0h estimado en T-05). Ricky se pasa 50% (5.5 vs 3.0 en T-02, 9.0 vs 5.0 en T-03). Revisar si las tareas de Ricky están bien scopeadas.
3. **Los agentes IA (Ricky) son más lentos que Nelson en tareas de integración**. Para el próximo sprint, considerar dar las tareas de integración a Nelson y dejar exploración/feature a Ricky.
4. **No hubo carry-over** → la planificación estuvo bien hecha. La capacity era 80h, solo usamos 37h. Subdimensionado: en el próximo sprint podríamos planear 25 puntos en vez de 18.
