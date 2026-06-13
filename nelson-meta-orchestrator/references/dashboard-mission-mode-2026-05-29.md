# Dashboard Mission Mode (2026-05-29)

Contexto: mejoras en `orchestrator-dashboard` para operar el meta-orquestador con menos fricción durante ejecución real (no solo demo).

## Qué patrón se implementó

Se consolidó un patrón de UX operacional llamado **Modo Misión** sobre la pantalla de Orquestador:

1. Flujo guiado visible en 4 pasos:
   - Objetivo
   - Plan
   - Ejecución
   - Resultado
2. CTA principal por fase:
   - `Planificar`
   - `Confirmar y Ejecutar`
3. Acciones de recuperación:
   - `Reintentar último goal` cuando la ejecución falla.
4. Timeline compacto en la misma pantalla:
   - Goal recibido
   - Plan generado
   - Ejecución iniciada
   - Resultado (ok/error)

## Ubicación de implementación

- Archivo principal: `src/pages/Orchestrator.tsx`
- Integración con hooks existentes:
  - `usePlanGoal`
  - `useConfirmGoal`
  - `useOrchestratorStatus`
  - `useOrchestratorHealth`

## Reglas de diseño que funcionaron

- Mantener el flujo **plan-first** (`/plan` -> `/run/confirm/{task_id}`), no volver al `run` directo como camino principal.
- Reducir fricción: el operador debe entender “qué sigue” sin leer texto largo.
- Mostrar estado de dependencias (task-memory/router) arriba de todo.
- Si falla, ofrecer retry inmediato del último goal para mantener momentum.

## Pendiente recomendado (siguiente iteración)

- Persistir timeline desde backend (no solo estado local React), para auditoría cross-session.
- Agregar controles por subtarea (pause/cancel/retry) cuando el backend los exponga.
- Agregar vista DAG para visualizar dependencias y camino crítico.
