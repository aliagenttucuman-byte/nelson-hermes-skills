# Systemd Deploy — Meta-Orquestador (2026-05-26)

## Estado final del stack

Todos los servicios del meta-orquestador corren como systemd services con restart automático:

| Puerto | Servicio                     | Estado   |
|--------|------------------------------|----------|
| :8742  | nelson-task-memory.service   | ✅ active |
| :8743  | nelson-agent-router.service  | ✅ active |
| :8744  | nelson-meta-orchestrator.service | ✅ active |

El dashboard (Vite + CF tunnel) corre aparte.

## Procedimiento de instalación

Script en `/home/server/nelson/meta-orchestrator/install-service.sh`

```bash
echo 'srv2026' | sudo -S bash /home/server/nelson/meta-orchestrator/install-service.sh
```

El script copia el `.service` a `/etc/systemd/system/`, hace `daemon-reload`, `enable` y `restart`.

## Pitfall: Address already in use al instalar

**Problema:** Al correr `install-service.sh`, el servicio falla con `[Errno 98] address already in use` porque el orquestador ya estaba corriendo en background (uvicorn lanzado manualmente en sesiones anteriores).

**Solución:**
```bash
# Matar el proceso que ocupa el puerto
fuser -k 8744/tcp 2>&1
# Esperar un momento y reiniciar el servicio
sleep 2
echo 'srv2026' | sudo -S systemctl restart nelson-meta-orchestrator
```

**Lección:** Antes de instalar el systemd service, siempre verificar si el puerto ya está en uso con `fuser 8744/tcp` o `ss -tlnp | grep 8744`.

## Limpieza de tareas obsoletas

No hay endpoint DELETE en task-memory. Para limpiar tareas de prueba, usar PATCH al endpoint de status:

```bash
curl -s -X PATCH http://localhost:8742/tasks/{task_id}/status \
  -H "Content-Type: application/json" \
  -d '{"status":"cancelled","result_summary":"Limpieza manual — tarea de prueba obsoleta"}'
```

Verificar que quedó limpio: `curl -s http://localhost:8742/tasks/pending` debe retornar `[]`.

## Evoluciones pendientes (next sprint)

1. **WebSocket broadcast desde dentro del loop del orquestador** → que el dashboard se actualice en tiempo real mientras el orquestador ejecuta batches (actualmente el WS en :8744 existe pero el loop no broadcastea eventos internos).

2. **Endpoint `/tasks/{id}/replay`** → re-correr una tarea cancelada o fallida sin tener que copiar el goal y crear una nueva. Muy útil para las tareas que fallan por contexto insuficiente y se quieren relanzar corregidas.
