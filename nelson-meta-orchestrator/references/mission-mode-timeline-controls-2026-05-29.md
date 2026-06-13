# Mission Mode + Timeline persistente + control de subtareas (2026-05-29)

## Contexto
Evolución aplicada al stack `meta-orchestrator + orchestrator-dashboard` para pasar de un flujo básico plan/confirm a operación más controlable.

## Patrón útil (durable)
Cuando mejoras el orquestador para uso operativo, aplicar en este orden:

1. **Persistencia backend primero**
   - Crear almacenamiento de eventos de orquestación (timeline)
   - Crear almacenamiento de estado de control por sub-tarea (active/paused/cancelled)
2. **Exponer endpoints de control/observabilidad**
   - Timeline por `master_id`
   - Subtareas por `master_id`
   - Acción sobre subtarea (`pause|resume|cancel|retry`)
3. **UI de misión**
   - Stepper Objetivo→Plan→Ejecución→Resultado
   - Timeline visible en panel
   - Botones de control/reintento conectados al backend

## Cambios backend implementados
Archivo: `nelson_orchestrator/orchestrator.py`

### Tablas SQLite agregadas
- `orchestration_events`
  - `master_id`, `event`, `detail`, `status`, `created_at`
- `subtask_control`
  - `subtask_id`, `master_id`, `control_state`, `updated_at`

### Helpers agregados
- `_log_event(master_id, event, detail, status)`
- `get_timeline(master_id, limit=100)`
- `get_subtasks(master_id)`
- `control_subtask(master_id, subtask_id, action)`

## Cambios UI implementados
Archivo: `orchestrator-dashboard/src/pages/Orchestrator.tsx`

- Modo Misión con stepper de 4 etapas
- Timeline local de eventos de ejecución
- Acción “Reintentar último goal”
- Conserva widgets de salud, stats y tareas recientes

## Convenciones de API/proxy observadas
- API orquestador en `127.0.0.1:8744`
- Frontend usa proxy `/api/orchestrate/*` hacia `:8744`

## Pitfalls
1. Hacer primero UI sin persistencia backend => timeline efíneo y sin auditabilidad real.
2. Implementar `pause/cancel/retry` solo en frontend => falsa sensación de control.
3. No loggear eventos por `master_id` => difícil depurar runs largos.

## Checklist de verificación recomendado
- [ ] Compila backend (`py_compile`) tras cambios de SQLite/helpers
- [ ] Build frontend (`npm run build`) sin errores
- [ ] `/health` y `/status` responden por API
- [ ] Un run genera eventos consultables por `master_id`
- [ ] `retry` restablece subtask a `pending` y limpia `result/error`
