---
name: nelson-high-value-observations
title: High-Value Observations — Brainstorming Sidecar
description: Convención para guardar observaciones puntuales de JARVIS durante evaluaciones de librerías/herramientas. NO tareas concretas — son ideas filtradas que merecen seguimiento futuro.
skill: nelson-high-value-observations
author: jarvis
version: 1.0.0
keywords: [brainstorming, observations, eval, followup]
---

# High-Value Observations — Convención

## Qué es

Archivo sidecar en `~/brainstorming/HIGH-VALUE-OBSERVATIONS.md` para
observaciones puntuales que JARVIS detecta durante la evaluación de
librerías/herramientas, y que merecen seguimiento futuro pero NO son
tareas inmediatas.

## Cuándo usarlo

Cuando en una evaluación aparece una **pieza específica** de un proyecto
archivado/rechazado que igual vale la pena mirar más adelante. Ejemplo:

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

- NO borrar entradas cuando se completa la observación — mover a sección
  "Completadas" abajo con fecha de cierre
- Cada entrada referenciar el README archivado que la originó
- Mantener una entrada = 1 idea, no agrupar
- Si la observación se convierte en tarea real → migrar a proyecto/skills
  y dejar el link acá

## Patrones de ejemplo

### Patrón 1: Pieza aislable de proyecto archivado
Headroom → CacheAligner (~50-100 líneas Python) → posible port a FreeLLMAPI

### Patrón 2: Patrón de diseño que no conocíamos
CCR reversible compression → mejorar `ctx_read` con `retrieve` formal

### Patrón 3: Métrica/benchmark que no teníamos
Cache hit rate real en Anthropic → medir antes/después de cualquier cambio
de prefijo en FreeLLMAPI

## NO es para

- ❌ Decisiones diarias
- ❌ Bugs en el pipeline
- ❌ Lista de features pendientes
- ❌ Recordatorios personales
