# Template — Sección ROI para Propuestas Comerciales

Usar cuando el cliente menciona cuánto tiempo dedica al trabajo manual que se va a automatizar.

## Variables a completar antes de generar

```
HORAS_DIA = 3 o 5          # dato del cliente
DIAS_SEMANA = 7             # confirmar si trabajan fines de semana
COSTO_HORA_CONSERVADOR = 15 # USD/h — referencia mercado
COSTO_HORA_REAL = 25        # USD/h — valor oportunidad gerencial
INVERSION_A = 57_600        # Opción A propietario
MANTENIMIENTO_ANUAL = 7_200 # USD 600/mes × 12
SAAS_ANUAL = 54_000         # USD 4.500/mes × 12
```

## Cálculos base

```python
dias_anio = DIAS_SEMANA * 52  # 364

hs_anio_base = 3 * dias_anio   # 1.092 hs
hs_anio_real = 5 * dias_anio   # 1.820 hs

costo_anio_conservador_base = hs_anio_base * 15   # USD 16.380
costo_anio_real_real = hs_anio_real * 25           # USD 45.500

costo_3anios_base = costo_anio_conservador_base * 3  # USD 49.140
costo_3anios_real = costo_anio_real_real * 3          # USD 136.500

ahorro_mensual_real = (5 * 7 * 4.33) * 25  # USD 3.789/mes
breakeven_meses_real = INVERSION_A / ahorro_mensual_real  # ~15 meses

ganancia_neta_anio3 = costo_3anios_real - (INVERSION_A + MANTENIMIENTO_ANUAL * 2)
# USD 136.500 - (57.600 + 14.400) = USD 64.500
```

## Estructura de la sección (copiar y adaptar)

```markdown
## N. Análisis de Retorno sobre Inversi\u00f3n (ROI)

### El punto de partida real

[Nombre/rol] de [Empresa] dedica entre **X y Y horas [diarias/semanales], [N] días de la semana**,
al procesamiento manual de los [N] procesos que esta propuesta automatiza.
Esto representa entre **[hs_base] y [hs_real] horas anuales** de tiempo [operativo/gerencial].

### Supuestos del análisis

| Parámetro | Valor | Criterio |
|-----------|-------|----------|
| Horas [diarias/semanales] | X h (base) — Y h (real) | Dato provisto por [quien] |
| Días de trabajo por semana | N | |
| Horas anuales (base) | [hs_base] hs | |
| Horas anuales (real) | [hs_real] hs | |
| Costo hora (conservador) | USD 15/h | Mercado [sector] Argentina |
| Costo hora (real) | USD 25/h | Valor de oportunidad |
| Inversión sistema | USD [total] | Opción A |
| Mantenimiento año 2+ | USD [mant]/año | |

> Costo hora conservador. El valor de errores evitados, decisiones más rápidas,
> etc. no está cuantificado para mantener el análisis verificable.

### Tabla 1 — Costo del trabajo manual actual

| Escenario | Hs/año | USD/año (15/h) | USD/año (25/h) | 3 años (15/h) | 3 años (25/h) |
|-----------|:------:|:--------------:|:--------------:|:-------------:|:-------------:|
| Base ([X]hs/día) | [hs_base] | USD [val] | USD [val] | USD [val] | USD [val] |
| Real ([Y]hs/día) | [hs_real] | USD [val] | USD [val] | USD [val] | USD [val] |

### Tabla 2 — ROI acumulado

#### Escenario Real ([Y] hs/día — USD 25/h)

| Período | Sin sistema | Opción A (propietario) | Opción B (SaaS) |
|---------|:-----------:|:----------------------:|:---------------:|
| Año 1 | Costo: USD [val] | Inversión: USD [val] | Costo: USD [val] |
| Año 2 | Costo acum: USD [val] | Total: USD [val] | Acum: USD [val] |
| Año 3 | Costo acum: USD [val] | Total: USD [val] | Acum: USD [val] |
| **Balance año 3** | — | **✅ USD [ganancia] ganancia neta** | **❌ USD [diferencia] más caro** |

### Tabla 3 — Break-even Opción A

| Escenario | Ahorro mensual | Break-even |
|-----------|:--------------:|:----------:|
| Base / USD 15/h | USD [val]/mes | Mes [N] (año [N]) |
| Real / USD 25/h | USD [val]/mes | ✅ Mes [N] (año [N]) |

### Conclusión financiera

Sin el sistema: Bisonte gasta USD [X] en 3 años en trabajo manual repetitivo.
Con el sistema (Opción A): inversión USD [Y] total en 3 años.
En el escenario real, el sistema no es un gasto — **genera USD [Z] de retorno neto**.

> La automatización no es un gasto. Es la única decisión financieramente racional
> cuando el costo de no hacerla supera el costo de hacerla.
```

## Ejemplo real — Bisonte jun 2026

- Gerente general: 3-5 hs DIARIAS, 7 días/semana
- Costo real año: USD 45.500 (5hs × USD 25/h × 364 días)
- Inversión Opción A: USD 57.600
- Break-even: mes 15
- Ganancia neta año 3: USD 64.500
- Archivo: `/home/server/brainstorming/2026-06-13-bisonte-propuesta-comercial-v3/PROPUESTA-COMERCIAL-BISONTE-v3.md` sección 13
