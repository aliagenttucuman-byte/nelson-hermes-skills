---
title: High-Value Observations Convention
description: Convención para guardar observaciones puntuales de JARVIS durante evaluaciones de librerías/herramientas. NO tareas concretas — son ideas filtradas que merecen seguimiento futuro.
skill: nelson-skill-authoring
subsection: brainstorming-sidecar
---

# High-Value Observations — Convención (sidecar de brainstorming)

> **Contexto:** Esta convención es la versión destilada de la ex-skill `nelson-high-value-observations` (archivada en `~/.hermes/skills/.archive/`). Se mantiene acá como `references/` porque su dominio es **el flujo de archiving dentro del workflow de skill-authoring**, no un workflow paralelo. El skill-umbrella `nelson-skill-authoring` ya cubre el ciclo de vida de docs/skills/brainstorming; este archivo es el sub-protocolo del "qué guardar aparte" cuando aparece una observación filtrada.

## Qué es

Archivo sidecar en `~/brainstorming/HIGH-VALUE-OBSERVATIONS.md` para observaciones puntuales que JARVIS detecta durante la evaluación de librerías/herramientas, y que merecen seguimiento futuro pero NO son tareas inmediatas.

## Cuándo usarlo

Cuando en una evaluación aparece una **pieza específica** de un proyecto archivado/rechazado que igual vale la pena mirar más adelante. Ejemplo:

- Headroom completo → archivado (lean-ctx + FreeLLMAPI cubren 70%)
- PERO CacheAligner (~50-100 líneas) → anotado para port futuro

## Cuándo NO usarlo

- Si la lib/herramienta se integra directamente → ir al README de la skill
- Si es un TODO concreto → usar el proyecto
- Si es un bug → fix directo

## Schema de cada entrada

```markdown
## YYYY-MM-DD — [Nombre corto de la observación]

**Contexto:** De la eval de [link a README archivado].
[Narrativa breve de 1-2 líneas de dónde salió la observación]

**Observación destacada de JARVIS:**

[Descripción técnica de la pieza, por qué es interesante,
qué problema resuelve, qué tan aislable es del resto del proyecto]

**Por qué nos sirve:** [Aplicación directa al stack del equipo]

**Por qué no se hizo hoy:** [Razón — usualmente overkill instalar todo]

**Próximo paso natural (cuando haya bandwidth):**
1. [Paso 1 accionable]
2. [Paso 2]
3. [Medición/validación]

**Skills/skills relacionadas:**
- [skill1]
- [skill2]

**Status:** NO COMPROMETIDO. Anotado para futuro.
```

## Importante

- **NO borrar entradas** cuando se completa la observación — mover a sección "Completadas" abajo con fecha de cierre
- **Cada entrada referenciar el README archivado** que la originó
- **Mantener una entrada = 1 idea**, no agrupar
- **Si la observación se convierte en tarea real** → migrar a proyecto/skills y dejar el link acá

## Patrones de ejemplo

### Patrón 1: Pieza aislable de proyecto archivado
Headroom → CacheAligner (~50-100 líneas Python) → posible port a FreeLLMAPI

### Patrón 2: Patrón de diseño que no conocíamos
CCR reversible compression → mejorar `ctx_read` con `retrieve` formal

### Patrón 3: Métrica/benchmark que no teníamos
Cache hit rate real en Anthropic → medir antes/después de cualquier cambio de prefijo en FreeLLMAPI

## NO es para

- ❌ Decisiones diarias
- ❌ Bugs en el pipeline
- ❌ Lista de features pendientes
- ❌ Recordatorios personales

## Por qué este archivo está acá (no como skill aparte)

Esta convención era la skill `nelson-high-value-observations` (archivada en mayo 2026). Razón de la consolidación: su dominio — "qué guardar en brainstorming sidecars durante el workflow de skill authoring" — es un sub-protocolo del workflow cubierto por `nelson-skill-authoring`, no un workflow paralelo. El skill-umbrella ya referencia `nelson-brainstorming` como peer para archiving; este archivo es el detalle fino de UNO de los tipos de sidecar que ese workflow produce.
