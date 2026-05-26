# Deployment nelson-task-memory (mayo 2026)

## Estado
- Implementado y corriendo en producción como servicio systemd
- URL: `http://localhost:8742`
- Repositorio: `https://github.com/aliagenttucuman-byte/nelson-task-memory`

## Archivos del proyecto
```
/home/server/nelson/task-memory/
├── db/tasks.db               # SQLite con WAL mode
├── task_memory/
│   ├── models.py             # Esquema + conexión
│   ├── crud.py               # CRUD completo
│   ├── api.py                # FastAPI router
│   ├── cli.py                # CLI Typer+Rich
│   └── integrations/         # kanban.py, hermes_search.py (stubs)
├── main.py                   # Entrypoint FastAPI
├── requirements.txt
└── README.md
```

## Systemd
```bash
sudo systemctl status nelson-task-memory   # ver estado
sudo systemctl restart nelson-task-memory  # reiniciar
sudo systemctl enable nelson-task-memory   # autostart al boot (ya habilitado)
```

## Comandos CLI
```bash
cd /home/server/nelson/task-memory
python3 -m task_memory.cli pending               # tareas pendientes
python3 -m task_memory.cli new "Goal" --assign hermes
python3 -m task_memory.cli show <task_id>
python3 -m task_memory.cli done <task_id> -s "Resumen"
python3 -m task_memory.cli history --limit 10
```

## Smoke test (8/8 endpoints OK)
Verificado 2026-05-26:
- POST /tasks/ — crear tarea
- POST /tasks/{id}/sessions/start — iniciar sesión (auto in_progress)
- GET /tasks/{id} — obtener tarea
- PATCH /tasks/{id}/status — actualizar estado
- POST /tasks/{id}/artifacts — agregar artefacto
- GET /tasks/pending — filtrar por agente
- GET /tasks/history — historial con filtros
- GET /health — health check

## Nota sobre uvicorn path
El uvicorn usado es el del venv de hermes-agent:
`/home/server/.hermes/hermes-agent/venv/bin/uvicorn`
Esto ya está en el `.service` file.
