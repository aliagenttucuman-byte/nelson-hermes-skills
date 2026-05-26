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

## Casos de Uso del Equipo

### ForestAI (caso base)
```
Documentos ya generados:
✅ ESTIMACION.md
✅ BENCHMARKING-FORESTECH.md
✅ PARTICIPACION-SOCIETARIA.md
⬜ BUSINESS-PLAN.md ← pendiente
```

### Próximo proyecto
```
JARVIS carga esta skill y genera todos los documentos en orden.
Empezar siempre por ESTIMACION y BENCHMARKING antes del BUSINESS-PLAN.
```

---

## Notas

- **Pablo usa el BUSINESS-PLAN-EXEC.md** para reuniones. No el completo.
- **Tony aprueba todo** antes de que salga del equipo.
- **Nada se manda a inversores o socios sin OK explícito de Tony.**
- El documento es vivo — se actualiza con cada nueva información del mercado.
- Commitear siempre después de generar (ver flujo de brainstorming).
