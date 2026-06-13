# Timeline persistente + control de subtareas

Resumen del patrón implementado para operaciones del meta-orquestador desde UI.

## Objetivo

Dar visibilidad y control en tiempo real sin depender de logs de consola o intervención manual por shell.

## Modelo de datos (SQLite)

### orchestration_events
- id (autoincrement)
- master_id (task_id maestro)
- event (planned, execute_started, verify, completed, failed, subtask_control, etc.)
- detail
- status (info|warn|error)
- created_at

### subtask_control
- subtask_id (PK)
- master_id
- control_state (active|paused|cancelled)
- updated_at

## Endpoints

1. `GET /runs/{task_id}/timeline`
- Devuelve eventos persistidos para renderizar timeline en dashboard.

2. `GET /runs/{task_id}/subtasks`
- Devuelve subtareas y `control_state` actual para controles operativos.

3. `POST /runs/{task_id}/subtasks/{subtask_id}/control`
- Body: `{ "action": "pause|resume|cancel|retry" }`
- Efectos:
  - pause → control_state=paused
  - resume → control_state=active
  - cancel → control_state=cancelled + status='cancelled'
  - retry → control_state=active + status='pending' + limpia result/error

## Lógica de ejecución recomendada

Antes de cada iteración del loop EXECUTE:
1) leer subtasks + control_state,
2) marcar CANCELLED en memoria de estado,
3) filtrar ejecutables solo con control_state='active',
4) loggear evento si hay pausadas.

## Frontend coupling

El dashboard debe:
- mostrar timeline persistente cuando exista,
- mostrar tabla/lista de subtasks con acciones por fila,
- invalidar queries de timeline/subtasks después de control action.

## Verificación mínima

- plan crea run con al menos 1 evento en timeline,
- pause cambia estado a paused,
- cancel evita ejecución posterior,
- retry deja subtask en pending.

## Nota de despliegue

Si producción corre en service systemd, aplicar restart controlado para que la API nueva quede activa antes de validar desde tunnel/UI.
