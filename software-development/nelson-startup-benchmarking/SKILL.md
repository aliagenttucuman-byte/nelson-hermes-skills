---
name: nelson-startup-benchmarking
description: "Benchmarking de mercado, valuación de software y negociación de equity para startups donde el equipo Nelson aporta el software. Genera BENCHMARKING.md, ESTIMACION.md y PARTICIPACION-SOCIETARIA.md listos para negociar."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [benchmarking, equity, startup, valoracion, negociacion, consultora, pablo, forestai]
    related_skills: [nelson-pricing-model, nelson-project-constitution, nelson-spec-driven-workflow]
---

# Nelson Startup Benchmarking & Valuación

Skill para cuando el equipo Nelson entra como socio tecnológico en una startup nueva. Aplica cuando:
- **El equipo Nelson aporta el software** (PoC ya construida o desarrollo futuro)
- **El otro equipo aporta hardware / dominio / clientes** (drones, sensores, operación en campo, etc.)
- **Se negocia equity** — porcentaje de participación en la empresa
- **Se necesita justificar el valor del software** con números reales del mercado

**Regla de oro:** Nunca entrar a una negociación de equity sin benchmarking. Los números del mercado son el argumento más fuerte.

---

## Documentos que genera esta skill

```
brainstorming/YYYY-MM-DD-nombre-proyecto/
├── BENCHMARKING-[SECTOR].md      ← Empresas reales del mercado + proyección ingresos
├── ESTIMACION.md                 ← Costo del aporte software (ver nelson-pricing-model)
└── PARTICIPACION-SOCIETARIA.md  ← Análisis de equity + cláusulas de negociación
```

---

## Cuándo usar

- El equipo tiene una PoC lista y otra parte quiere unir fuerzas
- Pablo está negociando participación con un tercero
- Hay que justificar por qué el software vale X% de la empresa
- Se necesita proyección de ingresos para presentar a inversores o socios

---

## Flujo de Trabajo

### Paso 1 — JARVIS pide contexto mínimo a Tony

```
¿Cuál es el sector? (forestech, agritech, healthtech, energytech, etc.)
¿Qué aporta la otra parte? (hardware, clientes, operación, patentes, etc.)
¿Ya tenemos PoC? ¿Cuántas horas invertidas?
¿Hay revenue o clientes concretos de alguna de las dos partes?
¿Cuál es el modelo de negocio proyectado? (SaaS, por hectárea, por crédito, etc.)
```

### Paso 2 — Investigar empresas de referencia del sector

JARVIS busca 4-5 empresas reales del sector que combinen el mismo stack (hardware + software/AI). Datos a extraer por empresa:

| Campo | Qué buscar |
|-------|-----------|
| Nombre y país | — |
| Año de fundación | — |
| Tecnología | Qué hardware + qué software/AI |
| Modelo de negocio | SaaS, por unidad, marketplace, etc. |
| Pricing | Si es público — por ha, por análisis, suscripción anual |
| Funding total | Crunchbase / Tracxn |
| Revenue anual | Si disponible (Tracxn es buena fuente) |
| Valuación | Última ronda conocida |
| Inversores clave | Para mapear el ecosistema |

**Fuentes recomendadas para buscar:**
- Crunchbase (funding rounds, inversores)
- Tracxn (revenue estimado, valuación)
- TechCrunch (rondas recientes)
- LinkedIn (equipo, tamaño)
- El propio sitio web (pricing, modelo)

**Query de búsqueda tipo:**
```
"[sector] drone AI startup funding 2022 2023 2024 site:crunchbase.com OR site:tracxn.com"
"[sector] SaaS per hectare pricing revenue investors"
```

### Paso 3 — Generar BENCHMARKING.md

El archivo tiene esta estructura:

```markdown
# [Proyecto] · Benchmarking de Mercado + Proyección de Ingresos

## 1. Empresas de Referencia

### [Empresa más parecida a nosotros]
| Dato | Valor |
| País | |
| Fundada | |
| Tecnología | |
| Modelo | |
| Funding | |
| Revenue | |
| Valuación | |

[...repetir para cada empresa...]

## 2. Modelos de Precio del Mercado
[tabla con por hectárea / SaaS anual / por análisis / comisión]

## 3. Proyección de Ingresos para [Proyecto] Argentina
### Supuestos base
### Año 1 — conservador
### Año 2 — tracción
### Año 3 — escala regional

## 4. Distribución de Ingresos entre Partes (X%/Y%)
[tabla por año con ingresos brutos]
[tabla con utilidades estimadas y margen]

## 5. Upside adicional (carbono, data, licencias, etc.)

## 6. Valuación de la Empresa en el Tiempo
[múltiplo de revenue según comparable del mercado]

## 7. Conclusión para la Negociación
[argumento central en 3-4 líneas]
```

### Paso 4 — Generar PARTICIPACION-SOCIETARIA.md

```markdown
# [Proyecto] · Análisis de Participación Societaria

## 1. Contexto del Deal
[tabla: qué aporta cada parte]

## 2. Valuación del Aporte de Software
### 2a. PoC ya construida (horas × rate)
### 2b. Desarrollo futuro comprometido

## 3. Valuación del Aporte de la Otra Parte
[hardware, intangibles, red comercial]

## 4. Análisis de Equity — Rango Justo
| Escenario | Nelson | Otra Parte | Cuándo aplica |
| Mínimo aceptable | 30% | 70% | |
| Justo | 40% | 60% | |
| Favorable a Nelson | 45% | 55% | |
| No aceptar | <30% | >70% | |

## 5. Estructura Recomendada
### Distribución inicial (%)
### Vesting — OBLIGATORIO para todos
| Período | 24–36 meses |
| Cliff | 6 meses |
| Tipo | Mensual post-cliff |

### Cláusulas clave a incluir
- Tag-along
- Derecho de primera oferta
- Veto técnico del equipo Nelson
- Propiedad del código (de la sociedad)
- Dedicación mínima comprometida

## 6. Cómo Presentarlo en la Negociación
[argumento central]
[qué decir si ofrecen menos del mínimo]
[palanca: el software funciona solo]

## 7. División Interna del Equity de Nelson
[tabla: Tony / Pablo / equipo dev]

## 8. Próximos Pasos
[ ] Tony valida los números
[ ] Reunión con la otra parte
[ ] Acordar vesting ANTES de hablar de porcentajes
[ ] Consultar abogado comercial
```

---

## Rangos de Equity — Referencia General

| Aporte del equipo Nelson | Equity mínimo | Equity justo | Equity máximo |
|--------------------------|---------------|--------------|---------------|
| Solo desarrollo futuro (sin PoC) | 20% | 25-30% | 35% |
| PoC lista + desarrollo futuro | 30% | 35-40% | 45% |
| PoC lista + desarrollo + go-to-market | 40% | 45% | 50%+ |
| Solo mantenimiento post-launch | 10% | 15% | 20% |

**Reglas que no se rompen:**
- Nunca menos del 30% si somos los únicos desarrollando el producto
- Vesting de 24 meses mínimo para todos — sin excepción
- El código es de la sociedad, no de ningún socio individualmente
- El equipo Nelson tiene veto en decisiones de arquitectura

---

## Múltiplos de Valuación por Sector

| Sector | Múltiplo típico sobre revenue | Fuente |
|--------|------------------------------|--------|
| SaaS B2B (early stage) | 4x–8x ARR | Regla general VC |
| Forestech / agritech | 3x–6x revenue | Treemetrics ~3.2x |
| Healthtech | 6x–12x ARR | Mayor premium |
| Energytech (hardware+SW) | 3x–5x revenue | Conservador |
| Créditos de carbono (marketplace) | 10x–20x revenue | Pachama, Sylvera |

---

## Modelos de Negocio por Sector — Referencia

### Forestech / Agritech
| Modelo | Precio típico | Margen |
|--------|--------------|--------|
| SaaS anual | $10K–$200K/año | 70-80% |
| Por hectárea (inventario) | $5–$30/ha | 60-80% |
| Por hectárea (siembra+monitoreo) | $200–$500/ha | 40-60% |
| Créditos carbono (comisión) | 5-15% del deal | 95%+ |
| Por análisis/reporte | $15–$100/análisis | 80-95% |

### SaaS B2B General (referencia consultora Nelson)
| Plan | Usuarios | Precio/mes | Margen target |
|------|----------|-----------|---------------|
| Starter | ≤50 | $700–$1.000 | 60-70% |
| Business | ≤200 | $1.000–$1.500 | 65-75% |
| Enterprise | ≤1.000 | $2.000–$5.000 | 70-80% |

---

## Notas de Negociación

- **Empezar siempre por el vesting**, no por el porcentaje. Acordar la estructura primero.
- **El benchmark es el argumento técnico** — no opinión, son datos reales de mercado.
- **La PoC ya construida es equity diferido** — hay que valorizarla con horas × rate.
- **Si el deal no cierra:** el software funciona solo. Se puede buscar otro operador o vender directo al cliente final.
- **Pablo cierra el deal, Tony valida los números.** JARVIS genera los documentos. Nunca al revés.
- **Nada sale a terceros sin aprobación de Tony.**

---

## Archivos de Referencia (ForestAI — primer caso de uso)

- `~/brainstorming/2026-05-19-forestai-poc/ESTIMACION.md`
- `~/brainstorming/2026-05-19-forestai-poc/PARTICIPACION-SOCIETARIA.md`
- `~/brainstorming/2026-05-19-forestai-poc/BENCHMARKING-FORESTECH.md`

Estos archivos son la plantilla viva — se pueden usar como base para el próximo proyecto.
