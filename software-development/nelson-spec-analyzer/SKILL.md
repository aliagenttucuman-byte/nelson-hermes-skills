---
name: nelson-spec-analyzer
description: "Fase 5 del flujo SDD Nelson. Analiza coherencia entre spec y plan. Detecta gaps y over-engineering antes de codear. Sin aprobacion del analyzer, no se implementa."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [spec-driven-development, analyzer, qa, validation, nelson, workflow]
    related_skills: [nelson-spec-driven-workflow, nelson-project-constitution, spec-driven-development, writing-plans, subagent-driven-development]
---

# Nelson Spec Analyzer

Fase 5 del flujo **Nelson Spec-Driven Development**.

Revisa la coherencia entre:
- **Spec** (QUÉ se pidió) y **Plan** (CÓMO se va a hacer)
- **Plan** y **Tasks** (¿todo está cubierto?)

**Regla de oro:** Si el analyzer encuentra gaps, NO se pasa a implementación. Se corrige primero.

## ¿Cuándo usar?

- Después de que Beto termina el plan técnico (Fase 4)
- Después de que JARVIS genera el breakdown de tareas (Fase 6)
- ANTES de que cualquier agente escriba código

## ¿Quién lo ejecuta?

**JARVIS** o **Alma** (agente QA). No lo ejecuta quien escribió el plan. Fresh eyes.

## Qué Revisa

### 1. Cobertura Completa

| Check | Descripción | Falla si... |
|---|---|---|
| **User Stories → Endpoints** | Cada user story tiene endpoints que la cubren | Una user story no tiene endpoint asociado |
| **User Stories → Data Model** | Cada entidad del spec existe en el data model | Falta una tabla/colección para una entidad |
| **Endpoints → Tasks** | Cada endpoint del OpenAPI tiene tarea de implementación | Un endpoint del spec no aparece en tasks.md |
| **Tasks → Plan** | Cada tarea está justificada en el plan | Hay tareas que no vienen del plan |

### 2. Over-Engineering Detection

| Check | Descripción | Ejemplo de over-engineering |
|---|---|---|
| **Scope extra** | El plan incluye cosas que NO pidió Tony | "Agregamos microservicios" cuando el spec dice monolito |
| **Tech innecesaria** | Stack más complejo de lo necesario | Usar Kafka cuando 10 requests/segundo con Celery alcanza |
| **Premature optimization** | Optimizar antes de medir | "Caching Redis para todo" sin evidencia de bottleneck |
| **Gold plating** | Features lindas pero no pedidas | "Dashboard de analytics" cuando el spec solo pide CRUD |

### 3. Consistencia de Nombres

- ¿Las entidades del spec se llaman igual en el data model? (ej: `User` vs `Usuario` vs `Account`)
- ¿Los endpoints usan los mismos nombres de campos que el spec? (ej: `email` vs `correo` vs `mail`)
- ¿Los tipos de datos coinciden? (ej: spec dice "fecha con hora" → plan usa `datetime`, no `date`)

### 4. Dependencias y Orden

- ¿Las tareas están en orden lógico? (models → repositories → services → endpoints → frontend)
- ¿Las tareas marcadas como paralelas `[P]` realmente no tienen dependencias entre sí?
- ¿Hay tareas bloqueantes sin alternativa? (single point of failure)

### 5. Estimaciones Realistas

- ¿La suma de estimaciones de tareas excede el deadline del CONSTITUTION?
- ¿Hay tareas estimadas en menos de 30 min? (demasiado granular, probable)
- ¿Hay tareas estimadas en más de 3 días? (demasiado grande, debe dividirse)

## Reporte de Análisis

### Si TODO OK

```markdown
# Spec Analyzer Report — [Proyecto]
**Fecha:** YYYY-MM-DD
**Analista:** JARVIS/Alma
**Resultado:** ✅ APROBADO

**Hallazgos:**
- Cobertura: 100% (12/12 user stories cubiertas)
- Over-engineering: Ninguno detectado
- Consistencia: 100% (nombres, tipos, endpoints alineados)
- Dependencias: Orden lógico, paralelizables correctamente marcadas
- Estimaciones: Total 15 días, dentro del deadline de 3 semanas

**Veredicto:** Apto para implementación. Proceder a Fase 6 (Tasks).
```

### Si HAY GAPS

```markdown
# Spec Analyzer Report — [Proyecto]
**Fecha:** YYYY-MM-DD
**Analista:** JARVIS/Alma
**Resultado:** ❌ RECHAZADO — Gaps encontrados

**Gaps Críticos (bloquean implementación):**
1. User Story #3 "Cancelar reserva" no tiene endpoint asociado en el plan
2. El data model no incluye entidad `ReservationStatus` (mencionada en el spec)
3. Over-engineering: Plan propone microservicios pero spec indica monolito (CONSTITUTION §2)

**Gaps Menores (deben corregirse pero no bloquean):**
4. Inconsistencia de nombres: spec usa `customer`, plan usa `client` → unificar
5. Task #12 estimada en 5 días → dividir en subtareas

**Acción requerida:**
- Beto debe agregar endpoint POST /reservations/{id}/cancel
- Beto debe agregar entidad `ReservationStatus` al data model
- Revisar arquitectura: monolito vs microservicios con Tony
- Corregir inconsistencias de naming
- Re-dividir task #12

**Próximo paso:** Corregir gaps y re-ejecutar analyzer.
```

## Flujo cuando hay gaps

```
Analyzer encuentra gaps
    ↓
Reporte enviado a Tony + Beto
    ↓
Beto corrige plan (y spec si es necesario)
    ↓
Re-ejecutar analyzer
    ↓
Si OK → pasar a Fase 6 (Tasks)
Si NO → repetir loop
```

**Regla:** Máximo 3 iteraciones. Si después de 3 iteraciones sigue fallando, escalar a Tony para decisión ejecutiva.

## Comandos Útiles

```bash
# Ejecutar análisis completo
cat specs/openapi.yaml specs/user-stories.md specs/data-model.md PLAN.md TASKS.md | analyze

# Verificar cobertura de endpoints por user story
python scripts/check_coverage.py specs/user-stories.md specs/openapi.yaml

# Detectar over-engineering comparando plan vs constitution
python scripts/check_overengineering.py PLAN.md CONSTITUTION.md
```

## Notas

- El analyzer es **objectivo**: no le importa quién escribió el plan. Si encuentra un gap, lo reporta.
- Tony puede decidir "ignorar este gap" pero debe documentar por qué (excepción justificada).
- Los gaps menores se pueden corregir en paralelo a la implementación si no afectan la arquitectura.
- Los gaps críticos SIEMPRE bloquean. No hay excepción.
- El reporte del analyzer se guarda en `~/brainstorming/YYYY-MM-DD-proyecto/analyzer-reports/`

## Ejemplo de Uso

```
Tony: "Beto terminó el plan. JARVIS, analizá antes de que codeen."

JARVIS:
  1. Lee CONSTITUTION.md (stack, reglas, restricciones)
  2. Lee specs/openapi.yaml + specs/user-stories.md + specs/data-model.md
  3. Lee PLAN.md + TASKS.md
  4. Ejecuta los 5 checks
  5. Genera reporte: ✅ APROBADO o ❌ RECHAZADO
  6. Si rechazado: lista de gaps + acciones concretas
  7. Envía reporte a Tony y Beto

Tony: "Dale, corregí los gaps y volvé a analizar"
(Beto corrige, JARVIS re-analiza, ahora ✅ APROBADO)
```

## Integración con el flujo SDD

| Fase | Skill | Output |
|---|---|---|
| 1. Constitución | `nelson-project-constitution` | `CONSTITUTION.md` |
| 2. Especificar | `spec-driven-development` | `specs/` |
| 3. Clarificar | (en spec-driven-development) | Spec actualizado |
| 4. Planear | `writing-plans` | `PLAN.md` |
| **5. Analizar** | **`nelson-spec-analyzer`** | **Analyzer Report** ← AQUÍ |
| 6. Tareas | `subagent-driven-development` | `TASKS.md` |
| 7. Checklist | `requesting-code-review` | Checklist OK |
| 8. Implementar | `subagent-driven-development` | Código funcionando |
