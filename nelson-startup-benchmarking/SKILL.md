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

brainstorming/YYYY-MM-DD-valuacion-equipo-y-proyectos/  ← (nuevo, vista 360°)
└── README.md                     ← VALUACION-CONSOLIDADA.md: equipo + portfolio + riesgos + recomendaciones
```

## VALUACION-CONSOLIDADA (vista 360° del portfolio) — nuevo 2026-06-07

Cuándo generarla: cuando Nelson pide "valuación del equipo y de los proyectos", "cuánto vale todo esto", o un recap ejecutivo que cubra AlegentAI + todos los proyectos activos. Es el **documento para mostrar a Pablo o stakeholders** que necesitan ver el portafolio completo, no un proyecto puntual.

### Diferencia con los documentos por proyecto

| Documento | Pregunta que responde | Audiencia | Frecuencia |
|---|---|---|---|
| `BENCHMARKING.md` (por proyecto) | ¿Cuánto vale este proyecto puntual? | Inversor del proyecto | Cuando hay nuevo deal |
| `ESTIMACION.md` (por proyecto) | ¿Cuánto sweat equity tiene cada parte? | Socio estratégico | Al cerrar MVP |
| `PARTICIPACION-SOCIETARIA.md` (por proyecto) | ¿Qué % le toca a cada uno? | Abogado, socios | Al formalizar sociedad |
| **`VALUACION-CONSOLIDADA.md`** (nuevo) | **¿Cuánto vale el equipo + portfolio entero?** | **Pablo, stakeholders, recap interno** | **Trimestral o pre-reunión clave** |

### Estructura recomendada (8 secciones, ~15-20 KB)

1. **TL;DR** — 1 tabla con 5-7 líneas (equipo, 2-3 proyectos top, total conservador/base/optimista)
2. **Valuación del equipo (AlegentAI como consultora)** — capacidad anual de generación de valor (USD 30/h × horas), composición de intangibles (skills, PoCs, track record, dashboards)
3. **Valuación por proyecto** — subsección por cada proyecto activo, con:
   - Sweat equity ya invertido (horas × USD 30)
   - % ejecutado del charter original
   - Escenarios conservador/base/optimista con múltiplos del sector
   - Lo que le toca a AlegentAI en cada escenario
   - Activos diferenciales (NetFlora, multi-tenancy, integraciones)
4. **Valuación consolidada** — tabla 360° con todo sumado
5. **Riesgos de la valuación** — qué podría bajar el número, con mitigación
6. **Mejoras recientes y su impacto** — cuantificar lo que las skills nuevas cierran
7. **Recomendaciones 30 días** — 3-6 acciones priorizadas con esfuerzo + impacto
8. **Gaps de datos** — qué falta para mejorar la valuación (tarifas, revenue real, equity firmada, valuación independiente)

### Plantilla de cálculo (lo que el lector va a querer ver)

```markdown
## Capacidad anual del equipo
| Persona | Rol | Dedicación | USD/h | USD/año (2080h) |
| ... (5 personas típicas) | | | | |
| TOTAL | | X% | | USD X/año |

## Sweat equity invertido por proyecto (costo de reposición)
| Proyecto | Horas | USD (a 30/h) |
| ForestAI | 805 | 24.150 |
| Expreso Bisonte | 560 | 16.800 |
| Chat-docs | 200 | 6.000 |
| Fleet Optimizer | 280 | 8.400 |

## Valuación por sector (múltiplos de revenue)
| Sector | Múltiple | Fuente |
| Forestech / agritech | 3-5x | Treemetrics ~3.2x |
| SaaS B2B consultora | 3-5x | Regla general |
| ForestAI con upside carbono | 10-20x | Pachama, Sylvera |
```

### Cómo se ve el cierre (template de recap para WhatsApp)

```
[VALUACION-CONSOLIDADA] generada en ~/brainstorming/2026-06-07-.../README.md (17 KB)

TL;DR:
- AlegentAI consultora: USD 500-600K
- ForestAI (45% AlegentAI, base): USD 337K
- Expreso Bisonte (año 1): USD 48-72K
- Total conservador: USD 1.06M | Base: USD 1.30M | Optimista: USD 1.80M

Top 3 acciones 30 días:
1. Activar cron de backups (30 min, +10K valuación)
2. Onboarding ReforestLatam en ForestAI (1-2 sprints, +80-150K)
3. Cerrar contrato anual con Expreso Bisonte (1-2 reuniones, +50-70K)

Gaps para mejorar la valuación: [lista de 3-5]
```

### Referencia viva

El primer VALUACION-CONSOLIDADA generado está en `~/brainstorming/2026-06-07-valuacion-equipo-y-proyectos/README.md` (285 líneas, 17KB). Úsalo como template cuando Tony pida el siguiente snapshot.

### Anti-patrones del VALUACION-CONSOLIDADA

- ❌ Inventar revenue cuando no hay — si un proyecto está en PoC sin clientes, decirlo explícito y valuarlo solo por sweat equity
- ❌ Usar múltiplos optimistas sin justificación — los múltiplos forestech 3-5x están bien; 10-20x solo con upside de carbono explícito
- ❌ Omitir los gaps de datos — la honestidad sobre lo que falta sube la credibilidad del resto
- ❌ Tablas truncadas (Nelson odia esto, ver `nelson-external-communication`) — todas las columnas y filas visibles

## Scraping de sitios Next.js (client-side rendered)

Muchos sitios de startups usan Next.js con rendering en cliente. `curl` devuelve HTML vacío
con solo scripts. Técnica verificada:

1. `curl -sL URL -o /tmp/sitio.html` — si el HTML tiene `self.__next_f` es Next.js cliente
2. Buscar rutas internas con contenido real: `/nosotros`, `/impacto`, `/tecnologia`, `/premios`
3. Las páginas internas suelen tener más contenido renderizado en server que la home
4. Si todo falla: `curl -sL 'https://web.archive.org/web/2024/URL'` — Wayback Machine suele
   tener versiones con contenido textual accesible
5. Extraer texto: `re.sub('<[^>]+>', ' ', html)` + `re.sub('\s+', ' ', text)`

Páginas con contenido útil en ReForest Latam: /nosotros (85KB), /impacto (64KB), /tecnologia (78KB), /premios (58KB)

## Cuándo usar

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

---

## Estrategia comercial dual — Sociedad vs Inversión (patrón ForestAI 2026)

Cuando Nelson presenta a un co-fundador/inversor potencial (ej: Pablo, COO con dominio técnico),
plantear siempre DOS opciones claras — no más:

### Opción 1: Sociedad (co-fundadores activos)
- Equity: Nelson ~50% / Socio activo ~30% / Pool equipo 20%
- Vesting obligatorio: 36 meses, cliff 6 meses
- Responsabilidades específicas por socio (ventas, campo, tech)
- Valuación implícita: `sweat equity de Nelson / % de Nelson`
  Ejemplo: USD 30K sweat equity / 50% = valuación pre-money USD 60K
- Cláusulas mínimas: tag-along, drag-along, primera oferta, no-compete 24m, IP de la sociedad
- Cuándo: el socio se involucra operativamente (40%+ del tiempo)

### Opción 2: Inversión (capital pasivo)
- Capital semilla USD 20K–50K a cambio de 15–25% equity
- Valuación pre-money = múltiplo 3–5x del sweat equity invertido
- Tabla de retorno: conservador / base / optimista (18 meses)
- Uso del capital por destino con montos específicos
- Cuándo: el inversor quiere retorno sin involucrarse en el día a día

### Ponderación del proyecto (siempre incluir antes de las opciones)
| Componente | Horas | Valor (USD 30/h) | Estado |
|------------|:-----:|:----------------:|--------|
| [lista de activos construidos] | | | PoC / MVP / Prod |
- TRL actual (1–9)
- Diferencial competitivo real (qué no tiene ningún otro producto)
- Qué falta para el MVP comercial con esfuerzo estimado

### Argumento de cierre para la reunión
> "El [producto] funciona hoy sobre datos reales de [lugar/contexto].
> [Métrica técnica concreta]. No existe otra PoC así en [mercado].
> Lo que falta es [brecha puntual] — que es exactamente donde entra [nombre]."

**Output:** siempre PDF con `scripts/generar_pdf.py` mandado como MEDIA:.
**Recomendación por defecto:** plantear Opción 1 primero. Socio activo > capital pasivo en early-stage.
**Piso no negociable de Nelson:** Nelson ≥ 50%, vesting 36m para todos, IP = propiedad de la sociedad.

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
- **IMPORTANTE — socio dual:** Pablo puede estar en los dos lados del deal a la vez (COO de AlegentAI + referente del socio externo). En ese caso la sociedad es AlegentAI (equipo completo incluyendo Pablo) vs la otra empresa. No plantear a Pablo como "la otra parte" en documentos ni en RACI.

## Project Charter — cuándo generarlo

Cuando hay un deal de joint venture o sociedad con un tercero, generar un **Project Charter** formal además de los documentos de benchmarking/participación. El charter aplica la metodología PM de Pablo (PMI/ISO 21502/PRINCE2/Agile) y cubre:

- Mandato + hipótesis de valor (formato CREEMOS QUE / RESULTARÁ EN / CRITERIOS DE ACEPTACIÓN)
- Alcance incluido y excluido (MVP)
- Equipo + RACI (5 personas típico del equipo Nelson)
- Cronograma con hitos de gobierno H0–H6
- Presupuesto con costo de desarrollo a **USD 30/hora** (tasa estándar del equipo Nelson)
- Riesgos top 6
- Estructura societaria clara (quién es quién, % de cada parte)
- Proyección financiera en 3 escenarios (conservador / base / optimista)
- Próximos pasos con owner y plazo

**Tasa estándar de desarrollo del equipo Nelson: USD 30/hora.**
MVP típico (4 meses, 5 personas): ~2.400 horas, ~USD 73.000 en sweat equity.

Guardar en: `~/brainstorming/YYYY-MM-DD-nombre-proyecto/PROJECT-CHARTER-vN.md`
Exportar a PDF con WeasyPrint (ver scripts/generar_pdf.py — misma receta que para el benchmarking).

## Integración con Resumen PM (meta-orchestrator)

Cuando el dashboard PM pida "valoración real" (no heurística), usar el Project Charter/Estimación como fuente estructurada y mostrarlo por proyecto seleccionado.

Referencia técnica de extracción: `references/pm-valuation-extraction.md`.
Ejemplo completo sociedad vs inversión: `references/forestai-estrategia-comercial-2026.md`.

### Campos mínimos que debe exponer el backend por proyecto

```json
{
  "project_valuation": {
    "mvp_total_investment_usd": 73960,
    "development_cost_usd": 73440,
    "operational_cost_4m_usd": 520,
    "monthly_avg_usd": 18490,
    "revenue_scenarios": [
      {"name":"Conservador","clients_per_year":5,"price_per_year_usd":8000,"gross_revenue_usd":40000,"estimated_margin_usd":24000},
      {"name":"Base","clients_per_year":15,"price_per_year_usd":10000,"gross_revenue_usd":150000,"estimated_margin_usd":90000},
      {"name":"Optimista","clients_per_year":40,"price_per_year_usd":12000,"gross_revenue_usd":480000,"estimated_margin_usd":288000}
    ],
    "source_files": [".../PROJECT-CHARTER-v3.md"]
  }
}
```

### Reglas UX validadas con Nelson

1. Si hay `project_valuation`, priorizar esos números en "Resumen económico".
2. Si NO hay valuación estructurada, **no inventar valoración**: mostrar mensaje explícito de "faltan documentos financieros".
3. "Objetivos/KPIs", "Hitos", "Riesgos" y "Próximas acciones" deben re-renderizar según proyecto seleccionado; evitar bloques estáticos.
4. Mantener trazabilidad visual de fuentes (mostrar `source_files` resumido).

### Pitfall crítico (cache incremental)

Si existe endpoint con `force_refresh`, no reutilizar grupos locales cacheados en esa ruta. `force_refresh=true` debe recalcular verdaderamente datos locales + financieros, no solo GitHub.

---

## Exportar Análisis a PDF (para presentar a Pablo u otros)

Una vez generado el `analisis_mercado.md` o el `BENCHMARKING.md`, se puede exportar a PDF
profesional con WeasyPrint + markdown2 (sin pandoc, sin wkhtmltopdf):

```bash
pip3 install markdown2 weasyprint
```

Script reutilizable: `scripts/generar_pdf.py` (ver linked files)

**Notas:**
- WeasyPrint 68+ soporta tablas, headers/footers con `@page`, numeración de páginas.
- Usar CSS con `@top-center` y `@bottom-right` para header/footer en cada página.
- Paleta de colores del equipo Nelson: `#0f3460` (azul oscuro), `#e94560` (acento rojo), fondo blanco.
- Para proyectos forestales/verdes: usar `#1a7d4f` como acento en lugar de `#e94560`.
- El PDF se genera en el mismo directorio que el markdown.
- Nunca enviar PDF a Pablo sin aprobación explícita de Tony.

---

## Potenciales Partners Investigados

- `references/reforest-latam-profile.md` — ReForest Latam (Tucumán, Yerba Buena, 2021). Empresa B certificada, +10 premios internacionales (COP28, OEA, Land Innovation Fund, SER Global Partner). Stack: iSeeds™ biotecnología semillas + flota UAV 500ha/campaña + AI/GIS match especie-micrositio 94%. Proyecto real Bolivia Yungas 1.240 ha, 47 especies nativas validadas. Equipo 14 personas: Damián Rivadeneira CEO, Paula Gianserra COO, Ignacio Gasparri Science Director, Eugenio Lobo CTO UAV, Martina Ramirez CSO. Precio: USD 500-800/ha (80% menos que métodos tradicionales). MRV actual: emergencia 92%, supervivencia 85%, establecimiento 74%. **Gap identificado:** su stack AI/GIS hace análisis a nivel micrositio y satélite, pero NO tiene detección ni clasificación de especie individual árbol-por-árbol desde imágenes de drone post-siembra — exactamente lo que ForestAI+YOLO provee para MRV árbol-por-árbol y créditos de carbono premium. Contacto: +54 381 640 0542, info@reforest-latam.com, linkedin.com/company/reforest-latam. Estrategia comercial completa (opción sociedad + inversión) en `/home/server/brainstorming/2026-06-11-forestai-reforest-latam/ESTRATEGIA-COMERCIAL-REFOREST.md`.

---

## Archivos de Referencia (ForestAI — primer caso de uso)

- `~/brainstorming/2026-05-19-forestai-poc/ESTIMACION.md`
- `~/brainstorming/2026-05-19-forestai-poc/PARTICIPACION-SOCIETARIA.md`
- `~/brainstorming/2026-05-19-forestai-poc/BENCHMARKING-FORESTECH.md`
- `~/brainstorming/2026-06-11-forestai-reforest-latam/ESTRATEGIA-COMERCIAL-REFOREST.md` + PDF ← template de estrategia comercial para partner concreto

## Archivos de Referencia (Expreso Bisonte — proyecto a medida)

- `~/brainstorming/2026-06-11-expreso-bisonte-propuesta-comercial/PROPUESTA-COMERCIAL-BISONTE-v2.md` + PDF ← versión validada con sweat equity incluido
- Patrón de pricing validado jun 2026:
  - Opción A fee mensual: A1 pesos con ajuste IPC+10% semestral (~ARS 2.900.000/mes año 1), A2 dólares fijos (USD 2.000/mes año 1)
  - Opción B inversión: 30% adelantado (USD 12.240) + 12 cuotas USD 2.380/mes — cliente dueño del código
  - Mantenimiento post-proyecto: USD 400/800/1.200 por mes
- **REGLA CLAVE:** sweat equity VA INCLUIDO en el presupuesto total (no solo como argumento). Total Bisonte = USD 16.800 (PoC) + USD 24.000 (desarrollo) = USD 40.800
- Referencia cambiaria: consultar `dolarapi.com/v1/dolares` — usar dólar oficial para conversión ARS
- A 3 años la Opción B sale ~50% menos acumulado que el fee mensual
- Recomendación por defecto: **Opción B por hitos** (se paga cuando se entrega — más fácil de cerrar)

Estos archivos son la plantilla viva — se pueden usar como base para el próximo proyecto.

---

## ⚠️ Pitfall — Scraping de sitios Next.js (renderizado en cliente)

Sitios Next.js devuelven HTML vacío con curl estándar. El contenido real está en chunks JS.

**Fix probado (reforest-latam.com, expresobisonte.com):**
```bash
# Opción 1 — Web Archive (más rápido para contenido estático)
curl -sL 'https://web.archive.org/web/2024/https://sitio.com/' | python3 -c "
import sys, re; html=sys.stdin.read()
text=re.sub('<script[^>]*>.*?</script>','',html,flags=re.DOTALL)
text=re.sub('<style[^>]*>.*?</style>','',text,flags=re.DOTALL)
text=re.sub('<[^>]+>',' ',text); text=re.sub('\s+',' ',text).strip()
print(text[:5000])"

# Opción 2 — Páginas internas (algunas tienen contenido pre-renderizado)
# Probar /nosotros, /impacto, /tecnologia, /contacto — pueden devolver HTML completo
for page in nosotros impacto tecnologia contacto premios; do
    curl -sL "https://sitio.com/$page" -o /tmp/rf_$page.html 2>/dev/null
    wc -c /tmp/rf_$page.html
done
# Páginas >20KB generalmente tienen contenido pre-renderizado útil
```

**Truco clave:** en sitios Next.js algunas rutas tienen SSR (server-side rendering) y devuelven
HTML completo. Probar rutas internas una por una — las que devuelven >20KB tienen contenido.

# Opción 2 — Buscar páginas internas que SÍ tienen SSR
# Next.js a veces renderiza en servidor las rutas /nosotros, /contacto, etc.
# Probar: curl -sL https://sitio.com/nosotros -o /tmp/p.html && wc -c /tmp/p.html
# Si el tamaño > 30KB, tiene contenido real
```

Caso real: reforest-latam.com devolvía 7KB en la home (vacío) pero /nosotros devolvía 85KB (contenido completo SSR).
