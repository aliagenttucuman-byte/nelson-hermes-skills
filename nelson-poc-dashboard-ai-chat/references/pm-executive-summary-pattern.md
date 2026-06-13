# Patrón PM Ejecutivo por proyecto seleccionado (Nelson)

## Objetivo
Convertir una vista PM estática en una vista ejecutiva operativa que se redibuja al seleccionar un proyecto real (proyectos locales, brainstorming, GitHub).

## Señales que disparan este patrón
- El usuario pide que PM sea operativo, no burocrático.
- El usuario pide que al seleccionar proyecto cambien los bloques de contexto.
- Se requiere evitar métricas artificiales cuando no hay evidencia suficiente.

## Implementación recomendada
1. Backend `/pm/instances` devuelve `projects` (y `instances` por compatibilidad) con:
   - `economic_weight` (`score`, `bucket`, `message`, `factors`)
   - `next_steps`
   - `project_kind`, `project_status`
2. Frontend PM usa `selectedProject` como fuente única para:
   - ficha ejecutiva superior
   - ponderación económica
   - próximas acciones
3. Si `economic_weight.score` no es numérico (`None/null`):
   - NO mostrar score
   - mostrar mensaje explícito de no-aplicabilidad
4. `next_steps`:
   - prioridad 1: extraídos de README/docs
   - fallback: pasos inferidos mínimos (README, deploy, smoke tests)

## Regla de UX (crítica)
No mostrar un número económico “porque sí”.
Si la evidencia es débil, el sistema debe decir claramente: “No aplica aún…”.

## Regla de lenguaje (Nelson)
En PM usar siempre “proyectos” (no “instancias”) en textos visibles.

## Checklist de verificación rápida
- Cambiar selector de proyecto y confirmar redibujo del bloque ejecutivo.
- Verificar un proyecto con score numérico y otro sin score.
- Verificar mensaje de no-aplicabilidad cuando no hay score.
- Verificar que la lista “Próximas acciones” provenga del proyecto seleccionado.
