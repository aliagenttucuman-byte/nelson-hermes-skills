# Estado del sistema en producción — 2026-05-26

## Servicios systemd activos

| Servicio | Puerto | Estado | Descripción |
|---|---|---|---|
| nelson-task-memory | :8742 | active (running) | SQLite task_graph.db, REST API |
| nelson-agent-router | :8743 | active (running) | Router de goals → agentes |
| nelson-meta-orchestrator | :8744 | active (running) | Loop GOAL→ROUTE→EXECUTE→VERIFY→NOTIFY |

Todos con `enabled` → levantan solos al reiniciar el servidor.

Orden de arranque garantizado por `After=` y `Wants=` en el .service:
- task-memory y router primero
- orchestrator después (depende de ambos)

## Pitfall del deploy de systemd

El orquestador corría como proceso uvicorn en background antes de instalar el servicio.
Cuando se instaló y arrancó el systemd, falló con `[Errno 98] address already in use`.

**Solución:**
```bash
fuser -k 8744/tcp   # matar proceso viejo
sudo systemctl restart nelson-meta-orchestrator
```

Regla: antes de instalar un systemd service para un proceso que ya corre en background,
matar el proceso existente primero.

## Next sprint (evoluciones pendientes)

1. **WebSocket broadcast desde dentro del loop** → el dashboard (:5174) se actualiza en tiempo real mientras el orquestador ejecuta una tarea (hoy el dashboard hace polling manual).
2. **Endpoint `/tasks/{id}/replay`** → re-correr una tarea cancelada o fallida sin tener que copiar el goal y crear una nueva. Útil para el flujo de operación diaria.

## Dashboard

- Puerto :5174 (Vite + Cloudflare tunnel)
- PIN: 741852
- Live feed via WebSocket /ws en :8744
- Presupuestación automática por tarea
