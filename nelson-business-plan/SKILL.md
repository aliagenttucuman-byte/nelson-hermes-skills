---
name: nelson-business-plan
description: "Genera el Business Plan maestro de proyectos/startups del equipo Nelson. Sigue la estructura Veigele (10 secciones) adaptada al contexto de la consultora. Se ejecuta después de BENCHMARKING y ESTIMACION, antes de presentar a inversores o socios."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [business-plan, startup, inversores, equity, consultora, pablo, plan-negocio, veigele]
    related_skills: [nelson-startup-benchmarking, nelson-pricing-model, nelson-project-constitution, nelson-spec-driven-workflow]
---

# Nelson Business Plan

Genera el **Business Plan maestro** de un proyecto o startup donde el equipo Nelson participa.
Sigue la estructura académica Veigele (Hochschule Biberach) adaptada al contexto de la consultora argentina.

**Cuándo usar:**
- Antes de presentar a inversores o socios estratégicos
- Cuando hay negociación de equity y se necesita un documento formal
- Cuando un proyecto pasa de PoC a MVP y necesita sustento comercial
- Cuando Pablo necesita un documento para llevar a una reunión

**Regla de oro:** El Business Plan NO es el primer paso. Primero CONSTITUTION → BENCHMARKING → ESTIMACION → recién entonces BUSINESS PLAN.

---

## Posición en el Flujo de la Consultora

```
FASE 1: CONSTITUTION        → nelson-project-constitution
FASE 2: SPEC / PLAN         → nelson-spec-driven-workflow
FASE 3: ESTIMAR             → nelson-pricing-model
FASE 4: BENCHMARKING        → nelson-startup-benchmarking (si hay equity)
FASE 5: BUSINESS PLAN  ★   → nelson-business-plan  ← AQUÍ
FASE 6: IMPLEMENTAR         → subagent-driven-development
```

---

## Estructura del Documento (10 secciones Veigele)

El Business Plan tiene máximo 35 páginas. JARVIS lo genera en Markdown.

### I. Executive Summary (2 páginas)
La primera sección que lee cualquier inversor. Debe poder leerse en 3 minutos.

Contenido obligatorio:
- Equipo (quiénes somos, qué nos distingue)
- Producto / servicio con USPs (Unique Selling Propositions)
- Ventaja competitiva concreta
- Mercado objetivo y tamaño
- Necesidad de inversión (si aplica)
- Roadmap con hitos y milestones
- Oportunidades y riesgos clave
- Objetivos de la empresa
- Retorno potencial

Checklist:
- [ ] ¿Quiénes son los miembros del equipo núcleo?
- [ ] ¿Cuál es la idea de negocio en una oración?
- [ ] ¿Cuál es el USP — qué la hace única?
- [ ] ¿Cuál es el mercado objetivo?
- [ ] ¿Cuál es el beneficio para el cliente?
- [ ] ¿Cómo es la situación de ingresos, costos y ganancias?
- [ ] ¿Qué canales de distribución se usarán?
- [ ] ¿Qué oportunidades y riesgos existen?
- [ ] ¿Cuánta inversión se requiere?

### II. La Empresa (1-2 páginas)
- Filosofía y misión
- Sistema de negocio (I+D, producción, marketing, ventas, servicio)
- Organización y organigrama
- Ubicación y forma jurídica
- Historia y objetivos de la empresa
- Estructura de socios (equity, vesting)

Checklist:
- [ ] ¿Cómo se ve el sistema de negocio para el producto/servicio?
- [ ] ¿Qué se hace internamente vs qué se terceriza?
- [ ] ¿Cuál es la forma jurídica adecuada?

### III. Equipo de Management y Personal (2 páginas)
Los inversores lo leen inmediatamente después del Executive Summary.

- Perfil de cada integrante del equipo (experiencia, logros, rol)
- Habilidades complementarias
- Qué habilidades faltan y cómo se cubren
- Asesores externos (abogados, contadores, mentores)
- Política de compensación (sueldos, participación)

Checklist:
- [ ] ¿Están los motivos y motivación del equipo explicados?
- [ ] ¿Qué experiencias tienen en común que sean relevantes?
- [ ] ¿Qué habilidades faltan? ¿Cómo se cubren?
- [ ] ¿Hay contactos en la industria?

### IV. El Producto / Servicio (2-5 páginas)
- Descripción clara y sin jerga técnica innecesaria
- USPs (qué lo hace único vs la competencia)
- Beneficio para el cliente (ahorro de tiempo, costos, calidad, unicidad)
- Estado de desarrollo actual
- Roadmap de desarrollo
- Proceso de producción / prestación del servicio
- Garantías y SLAs

Checklist:
- [ ] ¿Cuál es el problema de origen?
- [ ] ¿Qué innovación o ventaja competitiva ofrece?
- [ ] ¿Cuál es el beneficio concreto para el cliente?
- [ ] ¿Cuál es el ciclo de vida del producto?
- [ ] ¿Qué desarrollos futuros tiene?

### V. El Mercado (2-4 páginas)
Datos reales de mercado (ver nelson-startup-benchmarking para fuentes).

- Mercado total (TAM) con datos reales
- Segmentación del mercado
- Segmento objetivo (SAM y SOM)
- Análisis de competencia (SWOT o tabla comparativa)
- Potencial de mercado y proyección de crecimiento

Fuentes recomendadas: Crunchbase, Tracxn, TechCrunch, datos sectoriales de Argentina (INDEC, cámaras sectoriales).

Checklist:
- [ ] ¿Cuál es el TAM/SAM/SOM?
- [ ] ¿Cuáles son las barreras de entrada?
- [ ] ¿Quiénes son los 3-5 competidores principales?
- [ ] ¿Qué tendencias tecnológicas o regulatorias impactan?
- [ ] ¿Cuáles son los productos sustitutos?

### VI. Marketing y Ventas (2-4 páginas)
Las 4 P: Product / Price / Placement / Promotion.

- Estrategia de entrada al mercado
- Canales de distribución y ventas
- Política de precios (ver nelson-pricing-model para referencia)
- Estrategia de comunicación
- Plan de adquisición de clientes (primeros 3-5)

Checklist:
- [ ] ¿Están Product, Price, Canal y Comunicación alineados?
- [ ] ¿A qué precio vende la competencia?
- [ ] ¿Cuál es el margen de ganancia?
- [ ] ¿Cómo está organizado el equipo de ventas?

### VII. Planificación 3-5 Años (5 páginas)
Sección más importante para inversores. Datos numéricos, no narrativa.

Sub-secciones:
- **Planificación de personal:** headcount por área, costos
- **Planificación de inversiones:** capex, equipamiento
- **Planificación de liquidez:** cash flow mensual año 1, anual años 2-3
- **P&L proyectado:** ingresos, costos, EBIT por año
- **Balance proyectado:** activos y pasivos por año

Escenarios:
- Base Case: el caso más probable
- Best Case: si las oportunidades se materializan
- Worst Case: si los riesgos se materializan

Checklist:
- [ ] ¿Cuál es la visión a largo plazo?
- [ ] ¿Cuáles son los hitos clave y cuándo se alcanzan?
- [ ] ¿Qué inversiones están planeadas y cuándo?
- [ ] ¿Cuál es el break-even?

### VIII. Oportunidades y Riesgos (1-2 páginas)
- Top 3 oportunidades con probabilidad e impacto
- Top 3 riesgos con probabilidad e impacto y plan de mitigación
- Análisis de sensibilidad (qué pasa si el precio baja 20%, si tardan 6 meses más en adquirir clientes, etc.)

Checklist:
- [ ] ¿Cuáles son los 3 problemas principales en los próximos 3 años?
- [ ] ¿Cómo se mitigan?
- [ ] ¿Qué oportunidades adicionales existen?
- [ ] ¿Cómo impactan los escenarios en el capital y el retorno?

### IX. Necesidades Financieras (1-2 páginas)
Solo si se busca inversión externa.

- Capital necesario total y por fase
- Fuentes de financiamiento (equity, deuda, subsidios, créditos)
- Uso del capital (desarrollo, infra, equipo, operación)
- Retorno esperado para el inversor

### X. Anexos
- CV resumidos del equipo
- Capturas de la PoC / demo
- Documentos de benchmarking (BENCHMARKING.md)
- Estimación de costos (ESTIMACION.md)
- Análisis de participación (PARTICIPACION-SOCIETARIA.md)

---

## Template de Generación — Instrucciones para JARVIS

### Datos de entrada requeridos

Antes de generar, JARVIS pregunta a Tony:

| # | Dato | Fuente |
|---|------|--------|
| 1 | Nombre del proyecto / empresa | Tony |
| 2 | Descripción en una oración | Tony |
| 3 | ¿Ya hay CONSTITUTION.md? | JARVIS verifica |
| 4 | ¿Ya hay ESTIMACION.md? | JARVIS verifica |
| 5 | ¿Ya hay BENCHMARKING.md? | JARVIS verifica |
| 6 | ¿Se busca inversor externo, socio estratégico, o es solo interno? | Tony |
| 7 | ¿Hay clientes o usuarios existentes? | Tony |
| 8 | ¿Cuál es la forma jurídica planeada (SRL, SA, otra)? | Tony |
| 9 | ¿Hay necesidad de capital externo? ¿Cuánto? | Tony |

### Archivo de salida

```
brainstorming/YYYY-MM-DD-nombre-proyecto/
├── BUSINESS-PLAN.md          ← Este documento (versión completa)
├── BUSINESS-PLAN-EXEC.md     ← Solo Executive Summary (para compartir rápido)
├── ESTIMACION.md             ← Ya generado (nelson-pricing-model)
├── BENCHMARKING-[SECTOR].md  ← Ya generado (nelson-startup-benchmarking)
└── PARTICIPACION-SOCIETARIA.md ← Ya generado si hay equity
```

### Reglas de redacción

1. **Lenguaje:** Español neutro, sin jerga técnica en secciones ejecutivas. La sección IV puede tener términos técnicos.
2. **Longitud:** Máximo 35 páginas (equivalente Markdown). Executive Summary: 2 páginas.
3. **Datos:** Siempre citar fuente (Tracxn, Crunchbase, INDEC, etc.). Nunca inventar números.
4. **Tono:** Realista y honesto. Las debilidades se mencionan siempre con su plan de mitigación.
5. **Tablas:** Usar tablas Markdown para todos los datos numéricos.
6. **Aprobación:** Siempre terminar con tabla de aprobación: Tony (técnico) + Pablo (comercial).

---

## Diferencias con el Formato Veigele Original

| Aspecto | Veigele Original | Adaptación Nelson |
|---------|-----------------|-------------------|
| Idioma | Alemán | Español |
| Contexto | Empresas de construcción (HOCHTIEF) | Software / tech startup Argentina |
| Sección financiera | Muy detallada (balances GAAP/IAS) | Simplificada para early-stage |
| Benchmarking | No incluido | Incluido (nelson-startup-benchmarking) |
| Equity | No incluido | Incluido (PARTICIPACION-SOCIETARIA.md) |
| Escenarios | 3 (Base/Best/Worst) | 3 (conservador/realista/ambicioso) |
| Anexos | Documentos legales | Screenshots PoC + documentos técnicos |

---

## Patrón: Propuesta Comercial a medida (sin equity)

Cuando el cliente es una empresa que contrata desarrollo (no socio/inversor), el documento
**NO es un Business Plan Veigele completo** — es una Propuesta Comercial con:

1. Diagnóstico actual (el problema real, con datos propios del cliente)
2. Los N procesos/módulos a desarrollar (agrupados en bloques lógicos)
3. Stack tecnológico (con estado: PoC / a implementar)
4. Estimación por bloque (horas × USD 30/h)
5. Cronograma por fases con entregables verificables
6. **Dos opciones de pago** siempre:
   - Fee mensual SaaS (capex $0, pago recurrente, AlegentAI dueño del código)
   - Inversión inicial (30% adelantado + cuotas en N meses, cliente dueño del código)
7. Tabla comparativa A vs B con recomendación explícita
8. HU schema (CREEMOS QUE / RESULTARÁ EN / CRITERIOS DE ACEPTACIÓN)
9. Tabla de aprobación Nelson + Pablo

**Pricing estándar:**
- Desarrollo: USD 30/h
- Fee mensual Starter: USD 800/mes | Operativo: USD 1.400/mes | Completo: USD 2.000/mes
- Mantenimiento post-proyecto: Básico USD 400/mes | Evolutivo USD 800/mes | Full USD 1.200/mes
- Contrato mínimo fee mensual: 12 meses
- Anticipo inversión: 30% del total

**Pitfall:** el sweat equity de la PoC previa NO se vuelve a cobrar — se menciona como
antecedente de validación, no como ítem facturado.

**Pitfall crítico — no inventar scope (aprendido jun 2026):** NUNCA incluir módulos,
dashboards, o procesos que NO fueron mencionados explícitamente por el cliente.
Nelson corrigió una propuesta que incluía dashboards y procesos específicos que
la gerenta de Bisonte nunca pidió. Regla: si no lo mencionó el cliente, no va en
la propuesta. Para procesos desconocidos, comprometer la *metodología y capacidad*
(horas disponibles), no el contenido concreto. La frase correcta es:
"Los procesos se definen en el relevamiento, no antes."

**Líneas paralelas independientes:** cuando el cliente tiene múltiples áreas de
trabajo (ej: procesos Excel + flota), estructurar como Línea A / Línea B con
presupuesto y cronograma independientes y opción de contratar por separado.
Esto da flexibilidad al cliente para entrar de a poco.

**Patrón validado — 3 líneas de trabajo (Bisonte jun 2026):**
Cuando hay múltiples módulos de trabajo independientes, estructurar como Líneas numeradas:
- Línea 1 — Procesos Excel (~15 procesos, 1-2/mes, condicionado a referente del negocio)
- Línea 2 — Módulo independiente (ej: mantenimiento de flota)
- Línea 3 — Visualización / integración con sistema externo (ej: Sitrack GPS)

Cada línea tiene su propia tabla de inversión, cronograma y entregables verificables.
Las 3 líneas tienen resumen de inversión total + tabla comparativa A vs B al final.

**Patrón — disclaimer de fuentes de datos externas (Transoft/Sitrack):**
Cuando el cliente usa sistemas propietarios de terceros (ERP, GPS, etc.) sin API pública:
> "En esta primera instancia, las fuentes de datos deben estar disponibles como Excel
> descargado manualmente. La integración directa con [Sistema X] no está incluida en
> esta propuesta y requiere análisis técnico y comercial separado con el proveedor."
No comprometer integración con sistemas externos sin análisis previo.

**Sección de ROI obligatoria cuando el cliente hace trabajo manual cuantificable:**
Cuando el cliente menciona cuánto tiempo dedica a los procesos manuales, SIEMPRE
agregar una sección de ROI al final de la propuesta. Fórmula base:

```
Horas/año = horas_diarias × días_semana × 52 semanas
Costo_manual/año = horas/año × costo_hora_gerencia (USD 15-25/h)
Break-even = inversión_total / ahorro_mensual
Ganancia_neta_año3 = ahorro_3años - (inversión + mantenimiento_2años)
```

CRÍTICO — distinguir horas DIARIAS vs SEMANALES:
- 3-5 hs/semana → 1.092-1.820 hs/año (semanal)
- 3-5 hs/día × 7 días → 1.092-1.820 hs/año (diario — multiplica por 7 más)
- 3-5 hs DIARIAS × 7 días × 52 semanas = 1.092-1.820 hs/año (igual coinciden en este caso)
- PERO 5hs/día × USD 25/h × 364 días = USD 45.500/año — vs 5hs/semana = USD 2.080/año

Cuando el cliente sea la GERENTE GENERAL haciendo trabajo manual repetitivo:
usar USD 15/h como conservador y USD 25/h como valor real de oportunidad.
El argumento de cierre: "el sistema cuesta X una vez; no automatizar cuesta Y cada año".

Tablas a incluir en la sección ROI:
1. Costo trabajo manual actual (hs/año, USD/año, USD/3años) — base y real
2. ROI acumulado a 1, 2 y 3 años — Sin sistema / Opción A / Opción B
3. Break-even tabla (mes en que el ahorro supera la inversión)
4. Horas gerenciales liberadas (equivalente FTE)
5. Conclusión financiera: "la automatización no es un gasto, es la única decisión racional"

Referencia: `/home/server/brainstorming/2026-06-13-bisonte-propuesta-comercial-v3/PROPUESTA-COMERCIAL-BISONTE-v3.md` (sección 13)
Template con fórmulas y estructura copiable: `references/roi-seccion-template.md`

Referencia: `/home/server/brainstorming/2026-06-11-expreso-bisonte-propuesta-comercial/PROPUESTA-COMERCIAL-BISONTE.md`

---

## Casos de Uso del Equipo

### ForestAI (caso base)
```
Documentos ya generados:
✅ ESTIMACION.md
✅ BENCHMARKING-FORESTECH.md
✅ PARTICIPACION-SOCIETARIA.md
✅ ESTRATEGIA-COMERCIAL-REFOREST.md + PDF  ← generado jun 2026 para ReForest Latam
⬜ BUSINESS-PLAN.md ← pendiente
```

**Patrón validado — Estrategia Comercial para partner potencial:**
Cuando hay un partner concreto identificado (no un inversor genérico), generar un
`ESTRATEGIA-COMERCIAL-[PARTNER].md` en lugar del BUSINESS-PLAN completo. Es más
accionable para una primera reunión. Estructura mínima:
1. Activos de cada parte (tabla comparativa)
2. Integración técnica — qué gap cubre el producto
3. Ponderación (sweat equity, TRL, diferencial)
4. Opción A — Sociedad (equity sin capital)
5. Opción B — Inversión (capital a cambio de equity en el producto)
6. Comparativa A vs B (tabla rápida)
7. Roadmap conjunto con owners y plazos
8. Oportunidades y riesgos
9. Argumento de cierre (3-5 líneas, datos reales, sin adornos)
10. Próximos pasos con owner y fecha
11. Tabla de aprobación Tony + Pablo

Generado en PDF con WeasyPrint (ver nelson-startup-benchmarking `scripts/generar_pdf.py`).

### Expreso Bisonte (caso proyecto a medida — cliente existente)
```
Documentos generados jun 2026:
✅ PROPUESTA-COMERCIAL-BISONTE.md + PDF (propuesta inicial 10 procesos)
✅ PROPUESTA-ANUAL-BISONTE-2026-v2.md + PDF (plan anual Línea A + Línea B flota)
   /home/server/brainstorming/2026-06-13-bisonte-propuesta-automatizacion-anual/
✅ PROPUESTA-COMERCIAL-BISONTE-v3.md + PDF (sistema integral 3 líneas + ROI)
   /home/server/brainstorming/2026-06-13-bisonte-propuesta-comercial-v3/
```

**Propuesta v3 — Sistema Integral (jun 2026, 3 líneas):**
- Línea 1: ~15 procesos Excel, 1-2/mes, USD 30.000 total
- Línea 2: Auditoría mantenimiento de flota, USD 15.600
- Línea 3: Visualización tiempo real via Sitrack (Excel descargado del portal), USD 12.000
- Total sistema integral: 1.920 hs / USD 57.600
- Modalidad A propietario: anticipo 30% + 70% contra entrega
- Modalidad B SaaS: USD 4.500/mes, 12 meses mínimo
- ROI: gerente general dedica 3-5 hs DIARIAS (7 días/semana) = USD 45.500/año (5hs/USD 25h)
- Break-even Opción A escenario real: mes 15
- Ganancia neta año 3 (Opción A, real): USD 64.500

**Sitrack:** sistema GPS de flota sin API pública. Integración via Excel descargado manualmente del portal. Disclaimer obligatorio: no comprometer integración directa sin análisis previo con proveedor.

**Transoft:** sistema operativo de Bisonte. Sin API pública documentada. Mismo disclaimer que Sitrack.

**Lección clave (jun 2026):** La primera propuesta incluyó dashboards y procesos específicos que la gerenta nunca mencionó. Nelson corrigió: NO inventar scope. La v2 separa:
- **Línea A** — Procesos Excel (misma metodología CDO/PF, procesos se definen en relevamiento)
- **Línea B** — Control mantenimiento flota (módulo paralelo e independiente)

**Flota — módulos base para propuesta inicial:**
Registro por unidad, plan preventivo (km/fecha), alertas automáticas de vencimiento, historial de intervenciones, control de costos por unidad, exportación Excel/PDF. El diseño exacto surge del relevamiento con el área de flota.

**Patrón validado — Propuesta Comercial para proyecto a medida (no equity):**
Cuando el cliente es una empresa que contrata desarrollo (no un socio que entra con equity),
el documento cambia de estructura. No hay "opción A sociedad / opción B inversión" en sentido de equity,
sino dos modalidades de pago:

- **Opción A — Fee Mensual (SaaS):** sin inversión inicial, pago mensual por uso y mantenimiento.
  Estructura: Starter / Operativo / Completo con precio fijo/mes. Contrato mínimo 12 meses.
- **Opción B — Inversión inicial + cuotas:** 30% adelantado al inicio, resto en cuotas mensuales
  durante 12 meses. Al finalizar el cliente es dueño del código. Pago por hitos es la variante recomendada.

Siempre incluir tabla comparativa A vs B con: inversión inicial, costo mensual, costo total año 1 y año 3,
propiedad del sistema, riesgo de lock-in. La recomendación por defecto es Opción B si el cliente
puede hacer el anticipo — a 3 años sale 50% más barato que el fee mensual.

**Sweat equity ya invertido en PoC no se cobra nuevamente** — se menciona como antecedente de validación,
el proyecto nuevo parte de cero en facturación.

### Valorización AlegentAI para demo con prospecto (patrón Gino jun 2026)

Cuando Nelson diga "quiero mostrar la valorización de la consultora a [prospecto]":

1. Leer el documento existente en `/home/server/brainstorming/2026-06-07-valuacion-equipo-y-proyectos/README.md`
2. Generar PDF con WeasyPrint usando el CSS profesional con header AlegentAI + marca CONFIDENCIAL
3. Enviar por Telegram (NO WhatsApp — no soporta PDFs)

**Datos clave para citar en reunión:**
- Valorización total AlegentAI: USD 1.2M – 1.45M (escenario base jun 2026)
- Capacidad anual de desarrollo: USD 324K/año (4 personas × USD 30/h)
- ForestAI (45% AlegentAI): USD 337K – 1.08M según escenario
- 4 PoCs en producción como track record
- Equipo: Nelson (CEO/Tech Lead), Pablo (COO/Comercial), Julián (Backend IA), Mercedes (Frontend UX)

**Script PDF reutilizable:** `/tmp/generar_valorizacion_pdf.py`
**Fuente:** `/home/server/brainstorming/2026-06-07-valuacion-equipo-y-proyectos/README.md`
**Output:** `VALORIZACION-ALEGENTAI-2026.pdf` en la misma carpeta

### ⚠️ Pitfall crítico — WhatsApp NO entrega PDFs
WhatsApp no soporta entrega nativa de archivos PDF/MD vía el gateway de mensajes.
Solo imágenes y audios llegan nativamente con MEDIA:.
**Siempre** al final de generar documentos, indicar a Nelson:
1. La ruta exacta en el server donde quedaron los archivos
2. Ofrecerle enviarlo por Telegram (sí soporta archivos)
NO intentar MEDIA: con PDFs en WhatsApp — no llega y genera confusión.

### Próximo proyecto
```
JARVIS carga esta skill y genera todos los documentos en orden.
Empezar siempre por ESTIMACION y BENCHMARKING antes del BUSINESS-PLAN.
```

## Módulo ROI + Costo de Oportunidad (para propuestas a empresas operativas)

Cuando el cliente tiene procesos manuales repetitivos ejecutados por personal clave (gerente, coordinador), agregar siempre esta sección al final de la propuesta. Genera el argumento de cierre más poderoso.

### Variables a relevar antes de calcular

| Variable | Cómo obtenerla |
|---|---|
| Horas/día dedicadas al proceso | Pregunta directa al stakeholder: "¿cuánto tiempo le dedicás a esto por día?" |
| Días por semana | "¿Lo hacés solo días hábiles o también fines de semana?" |
| Costo del rol | Estimación de mercado. Para gerente general Tucumán: USD 15-25/h |
| Valor estratégico del rol | Cuánto vale esa persona haciendo trabajo de alto valor. Gerente general: USD 40-60/h |

### Fórmula

```
Horas/año = hs_diarias × días_semana × 52
Costo directo/año = horas_año × costo_operativo
Costo oportunidad/año = horas_año × valor_estratégico
ROI neto a N años = (costo_total_sin_sistema) - inversión_sistema
Break-even = inversión / ahorro_mensual_combinado
```

### Caso real Bisonte (jun 2026)

- 5 hs diarias, 7 días, gerente general → 1.820 hs/año
- Directo USD 45.500 + oportunidad USD 91.000 = **USD 136.500/año sin sistema**
- Inversión sistema: USD 57.600 → break-even mes 15 → ROI neto 3 años: **USD 351.900**

### Pitfalls al presentar ROI

- SIEMPRE usar el número de horas que el cliente dijo, sin inflarlo
- Si el cliente puede cuestionar el costo de oportunidad, solo mostrar costo directo
- Incluir siempre el disclaimer "basado en datos provistos por el cliente"
- La frase "estas son horas de su gerente general, la persona más estratégica de la empresa" cierra la conversación

---

## Notas

- **Pablo usa el BUSINESS-PLAN-EXEC.md** para reuniones. No el completo.
- **REGLA — sweat equity en presupuesto (aprendido jun 2026):** cuando el cliente contrata desarrollo a medida (no equity), el sweat equity acumulado VA como línea en el presupuesto total — no solo como argumento de validación. El cliente paga el retorno a la consultora. Ejemplo: PoC Bisonte 560 hs × USD 30 = USD 16.800 entra en el total junto al desarrollo nuevo.
- **Tipo de cambio:** incluir siempre precio en USD y ARS. Consultar `dolarapi.com/v1/dolares` para el oficial del día antes de generar el doc.
- **Tony aprueba todo** antes de que salga del equipo.
- **Nada se manda a inversores o socios sin OK explícito de Tony.**
- El documento es vivo — se actualiza con cada nueva información del mercado.
- Commitear siempre después de generar (ver flujo de brainstorming).
