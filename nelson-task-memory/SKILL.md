---
name: nelson-task-memory
description: Memoria persistente de tareas para el meta-orquestador de Nelson. Guarda estado, historial, artefactos y sesiones en SQLite para que el agente recuerde qué hizo, qué falló y qué sigue pendiente entre sesiones.
tags: [memory, tasks, persistence, sqlite, meta-agent, nelson]
related_skills: [nelson-meta-orchestrator, nelson-database, nelson-scheduled-jobs]
---

# Nelson Task Memory

Sistema de memoria persistente de tareas para el meta-orquestador de Nelson.
Permite que el agente retome trabajo entre sesiones sin perder contexto: qué se hizo, qué falló, qué sigue en curso, qué artefactos se generaron.

---

## Por qué existe esto

El meta-orquestador de Nelson puede correr en múltiples sesiones de Hermes/JARVIS a lo largo del tiempo. Sin persistencia, cada sesión arranca desde cero: no sabe si la tarea de ayer terminó, si hubo un error que requiere retry, ni qué archivos generó.

Task Memory resuelve eso con una base SQLite liviana que vive en el servidor y una API FastAPI para que cualquier agente o herramienta consulte o actualice el estado.

---

## Stack

- Python 3.11+
- SQLite (nativo, sin dependencias extra)
- FastAPI + Uvicorn (servicio HTTP)
- Typer (CLI)
- Opcionalmente: SQLAlchemy Core (sin ORM pesado)

---

## Estructura de archivos

```
/home/server/nelson/task-memory/
├── db/
│   └── tasks.db                  # Base SQLite principal
├── task_memory/
│   ├── __init__.py
│   ├── models.py                 # Esquema y conexión SQLite
│   ├── crud.py                   # Operaciones CRUD
│   ├── api.py                    # Endpoints FastAPI
│   ├── cli.py                    # CLI con Typer
│   └── integrations/
│       ├── kanban.py             # Sync con Nelson Kanban
│       └── hermes_search.py      # Integración session_search
├── main.py                       # Entrypoint FastAPI
├── requirements.txt
└── README.md
```

---

## Modelo de datos

### Tabla: tasks

| Campo          | Tipo    | Descripción                                      |
|----------------|---------|--------------------------------------------------|
| id             | TEXT PK | UUID v4                                          |
| goal           | TEXT    | Descripción del objetivo                         |
| status         | TEXT    | pending / in_progress / done / failed / cancelled|
| created_at     | TEXT    | ISO 8601                                         |
| updated_at     | TEXT    | ISO 8601                                         |
| assigned_to    | TEXT    | Agente o persona responsable (ej: "hermes", "tony") |
| result_summary | TEXT    | Resumen del resultado final (nullable)           |
| error          | TEXT    | Mensaje de error si falló (nullable)             |
| parent_task_id | TEXT FK | Para subtareas (nullable)                        |

### Tabla: sessions

| Campo      | Tipo | Descripción                              |
|------------|------|------------------------------------------|
| id         | TEXT PK | UUID v4                               |
| task_id    | TEXT FK | Referencia a tasks.id                 |
| session_id | TEXT    | ID de sesión Hermes/JARVIS             |
| started_at | TEXT    | ISO 8601                               |
| ended_at   | TEXT    | ISO 8601 (nullable si sigue activa)    |
| notes      | TEXT    | Notas libres del agente durante la sesión |

### Tabla: artifacts

| Campo       | Tipo | Descripción                                         |
|-------------|------|-----------------------------------------------------|
| id          | TEXT PK | UUID v4                                          |
| task_id     | TEXT FK | Referencia a tasks.id                            |
| type        | TEXT    | file / url / screenshot / report                 |
| path        | TEXT    | Ruta absoluta o URL del artefacto                |
| description | TEXT    | Descripción legible                              |
| created_at  | TEXT    | ISO 8601                                         |

---

## Implementación Python

### models.py — Esquema y conexión

```python
# task_memory/models.py
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("/home/server/nelson/task-memory/db/tasks.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # Lecturas concurrentes seguras
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Crea las tablas si no existen. Idempotente."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id             TEXT PRIMARY KEY,
                goal           TEXT NOT NULL,
                status         TEXT NOT NULL DEFAULT 'pending'
                               CHECK(status IN ('pending','in_progress','done','failed','cancelled')),
                created_at     TEXT NOT NULL,
                updated_at     TEXT NOT NULL,
                assigned_to    TEXT,
                result_summary TEXT,
                error          TEXT,
                parent_task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id         TEXT PRIMARY KEY,
                task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                session_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at   TEXT,
                notes      TEXT
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id          TEXT PRIMARY KEY,
                task_id     TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                type        TEXT NOT NULL
                            CHECK(type IN ('file','url','screenshot','report')),
                path        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status    ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_assigned  ON tasks(assigned_to);
            CREATE INDEX IF NOT EXISTS idx_sessions_task   ON sessions(task_id);
            CREATE INDEX IF NOT EXISTS idx_artifacts_task  ON artifacts(task_id);
        """)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())
```

### crud.py — Operaciones CRUD

```python
# task_memory/crud.py
from typing import Optional
from .models import get_connection, now_iso, new_id


# ── Tasks ──────────────────────────────────────────────────────────────────

def create_task(
    goal: str,
    assigned_to: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    status: str = "pending",
) -> dict:
    """Crea una tarea nueva. Retorna el dict completo."""
    task_id = new_id()
    ts = now_iso()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO tasks (id, goal, status, created_at, updated_at, assigned_to, parent_task_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (task_id, goal, status, ts, ts, assigned_to, parent_task_id),
        )
    return get_task(task_id)


def get_task(task_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def update_status(
    task_id: str,
    status: str,
    result_summary: Optional[str] = None,
    error: Optional[str] = None,
) -> Optional[dict]:
    """Actualiza el estado de una tarea. Válido: pending, in_progress, done, failed, cancelled."""
    valid = {"pending", "in_progress", "done", "failed", "cancelled"}
    if status not in valid:
        raise ValueError(f"Status inválido: {status}. Usar uno de {valid}")

    ts = now_iso()
    with get_connection() as conn:
        conn.execute(
            """UPDATE tasks
               SET status = ?, updated_at = ?, result_summary = COALESCE(?, result_summary),
                   error = COALESCE(?, error)
               WHERE id = ?""",
            (status, ts, result_summary, error, task_id),
        )
    return get_task(task_id)


def get_pending_tasks(assigned_to: Optional[str] = None) -> list[dict]:
    """Tareas pendientes o en curso. Filtrables por agente."""
    query = "SELECT * FROM tasks WHERE status IN ('pending', 'in_progress')"
    params: list = []
    if assigned_to:
        query += " AND assigned_to = ?"
        params.append(assigned_to)
    query += " ORDER BY created_at ASC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_task_history(
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Historial de tareas con filtros opcionales."""
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []
    if assigned_to:
        query += " AND assigned_to = ?"
        params.append(assigned_to)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_subtasks(parent_task_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at ASC",
            (parent_task_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Sessions ───────────────────────────────────────────────────────────────

def start_session(task_id: str, session_id: str, notes: Optional[str] = None) -> dict:
    sid = new_id()
    ts = now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (id, task_id, session_id, started_at, notes) VALUES (?, ?, ?, ?, ?)",
            (sid, task_id, session_id, ts, notes),
        )
        # Marcar tarea como in_progress automáticamente si estaba pending
        conn.execute(
            "UPDATE tasks SET status='in_progress', updated_at=? WHERE id=? AND status='pending'",
            (ts, task_id),
        )
    return {"id": sid, "task_id": task_id, "session_id": session_id, "started_at": ts}


def end_session(session_id: str, notes: Optional[str] = None) -> None:
    ts = now_iso()
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET ended_at=?, notes=COALESCE(?, notes) WHERE id=?",
            (ts, notes, session_id),
        )


def get_sessions(task_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE task_id=? ORDER BY started_at ASC",
            (task_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Artifacts ──────────────────────────────────────────────────────────────

def add_artifact(
    task_id: str,
    artifact_type: str,
    path: str,
    description: Optional[str] = None,
) -> dict:
    """Registra un artefacto (archivo, URL, screenshot, reporte)."""
    valid_types = {"file", "url", "screenshot", "report"}
    if artifact_type not in valid_types:
        raise ValueError(f"Tipo inválido: {artifact_type}. Usar uno de {valid_types}")
    aid = new_id()
    ts = now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO artifacts (id, task_id, type, path, description, created_at) VALUES (?,?,?,?,?,?)",
            (aid, task_id, artifact_type, path, description, ts),
        )
    return {"id": aid, "task_id": task_id, "type": artifact_type, "path": path, "description": description}


def get_artifacts(task_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE task_id=? ORDER BY created_at ASC",
            (task_id,),
        ).fetchall()
    return [dict(r) for r in rows]
```

---

## API FastAPI

```python
# task_memory/api.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from . import crud

router = APIRouter(prefix="/tasks", tags=["task-memory"])


# ── Schemas ────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    goal: str
    assigned_to: Optional[str] = None
    parent_task_id: Optional[str] = None
    status: str = "pending"


class StatusUpdate(BaseModel):
    status: str
    result_summary: Optional[str] = None
    error: Optional[str] = None


class ArtifactCreate(BaseModel):
    type: str
    path: str
    description: Optional[str] = None


class SessionStart(BaseModel):
    session_id: str
    notes: Optional[str] = None


class SessionEnd(BaseModel):
    notes: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_task(body: TaskCreate):
    return crud.create_task(
        goal=body.goal,
        assigned_to=body.assigned_to,
        parent_task_id=body.parent_task_id,
        status=body.status,
    )


@router.get("/pending")
def pending_tasks(assigned_to: Optional[str] = Query(None)):
    return crud.get_pending_tasks(assigned_to=assigned_to)


@router.get("/history")
def task_history(
    assigned_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    return crud.get_task_history(assigned_to=assigned_to, status=status, limit=limit)


@router.get("/{task_id}")
def get_task(task_id: str):
    task = crud.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Tarea {task_id} no encontrada")
    return task


@router.patch("/{task_id}/status")
def update_status(task_id: str, body: StatusUpdate):
    task = crud.update_status(
        task_id=task_id,
        status=body.status,
        result_summary=body.result_summary,
        error=body.error,
    )
    if not task:
        raise HTTPException(404, f"Tarea {task_id} no encontrada")
    return task


@router.get("/{task_id}/subtasks")
def get_subtasks(task_id: str):
    return crud.get_subtasks(task_id)


@router.post("/{task_id}/artifacts", status_code=201)
def add_artifact(task_id: str, body: ArtifactCreate):
    return crud.add_artifact(
        task_id=task_id,
        artifact_type=body.type,
        path=body.path,
        description=body.description,
    )


@router.get("/{task_id}/artifacts")
def get_artifacts(task_id: str):
    return crud.get_artifacts(task_id)


@router.post("/{task_id}/sessions/start", status_code=201)
def start_session(task_id: str, body: SessionStart):
    return crud.start_session(task_id=task_id, session_id=body.session_id, notes=body.notes)


@router.patch("/sessions/{session_id}/end")
def end_session(session_id: str, body: SessionEnd):
    crud.end_session(session_id=session_id, notes=body.notes)
    return {"ok": True}


@router.get("/{task_id}/sessions")
def get_sessions(task_id: str):
    return crud.get_sessions(task_id)
```

```python
# main.py
from fastapi import FastAPI
from task_memory.models import init_db
from task_memory.api import router

app = FastAPI(title="Nelson Task Memory", version="1.0.0")
app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "nelson-task-memory"}
```

Levantar el servicio:

```bash
cd /home/server/nelson/task-memory
uvicorn main:app --host 0.0.0.0 --port 8742 --reload
```

---

## CLI para Tony

```python
# task_memory/cli.py
import typer
from rich.table import Table
from rich.console import Console
from . import crud
from .models import init_db

app = typer.Typer(name="tasks", help="CLI de Task Memory — Nelson")
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    init_db()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("new")
def new_task(
    goal: str = typer.Argument(..., help="Descripción del objetivo"),
    assigned_to: str = typer.Option(None, "--assign", "-a", help="Agente o persona"),
):
    """Crea una nueva tarea."""
    task = crud.create_task(goal=goal, assigned_to=assigned_to)
    console.print(f"[green]✓ Tarea creada:[/green] {task['id']}")
    console.print(f"  Goal: {task['goal']}")
    console.print(f"  Status: {task['status']}")


@app.command("pending")
def list_pending(
    assigned_to: str = typer.Option(None, "--assign", "-a"),
):
    """Lista tareas pendientes o en curso."""
    tasks = crud.get_pending_tasks(assigned_to=assigned_to)
    if not tasks:
        console.print("[yellow]Sin tareas pendientes.[/yellow]")
        return
    _print_table(tasks)


@app.command("history")
def history(
    assigned_to: str = typer.Option(None, "--assign", "-a"),
    status: str = typer.Option(None, "--status", "-s"),
    limit: int = typer.Option(20, "--limit", "-n"),
):
    """Historial de tareas."""
    tasks = crud.get_task_history(assigned_to=assigned_to, status=status, limit=limit)
    _print_table(tasks)


@app.command("show")
def show_task(task_id: str = typer.Argument(...)):
    """Muestra el detalle de una tarea incluyendo artefactos y sesiones."""
    task = crud.get_task(task_id)
    if not task:
        console.print(f"[red]Tarea {task_id} no encontrada.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Tarea:[/bold] {task['id']}")
    console.print(f"  Goal:    {task['goal']}")
    console.print(f"  Status:  {task['status']}")
    console.print(f"  Assigned: {task['assigned_to'] or '-'}")
    console.print(f"  Created: {task['created_at']}")
    console.print(f"  Updated: {task['updated_at']}")
    if task['result_summary']:
        console.print(f"  Result:  {task['result_summary']}")
    if task['error']:
        console.print(f"  [red]Error:[/red]   {task['error']}")

    artifacts = crud.get_artifacts(task_id)
    if artifacts:
        console.print(f"\n  [bold]Artefactos ({len(artifacts)}):[/bold]")
        for a in artifacts:
            console.print(f"    [{a['type']}] {a['path']} — {a['description'] or ''}")

    sessions = crud.get_sessions(task_id)
    if sessions:
        console.print(f"\n  [bold]Sesiones ({len(sessions)}):[/bold]")
        for s in sessions:
            end = s['ended_at'] or 'activa'
            console.print(f"    {s['session_id'][:16]}… | {s['started_at']} → {end}")


@app.command("done")
def mark_done(
    task_id: str = typer.Argument(...),
    summary: str = typer.Option(None, "--summary", "-s"),
):
    """Marca una tarea como completada."""
    crud.update_status(task_id, "done", result_summary=summary)
    console.print(f"[green]✓ Tarea {task_id[:8]}… marcada como DONE[/green]")


@app.command("fail")
def mark_failed(
    task_id: str = typer.Argument(...),
    error: str = typer.Option(None, "--error", "-e"),
):
    """Marca una tarea como fallida."""
    crud.update_status(task_id, "failed", error=error)
    console.print(f"[red]✗ Tarea {task_id[:8]}… marcada como FAILED[/red]")


@app.command("artifact")
def add_artifact(
    task_id: str = typer.Argument(...),
    artifact_type: str = typer.Option(..., "--type", "-t", help="file|url|screenshot|report"),
    path: str = typer.Option(..., "--path", "-p"),
    description: str = typer.Option(None, "--desc", "-d"),
):
    """Agrega un artefacto a una tarea."""
    crud.add_artifact(task_id=task_id, artifact_type=artifact_type, path=path, description=description)
    console.print(f"[green]✓ Artefacto agregado a {task_id[:8]}…[/green]")


def _print_table(tasks: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", width=8)
    table.add_column("Status", width=12)
    table.add_column("Assigned", width=10)
    table.add_column("Goal")
    table.add_column("Updated", width=20)
    for t in tasks:
        color = {
            "done": "green", "failed": "red", "in_progress": "yellow",
            "cancelled": "dim", "pending": "white",
        }.get(t["status"], "white")
        table.add_row(
            t["id"][:8] + "…",
            f"[{color}]{t['status']}[/{color}]",
            t["assigned_to"] or "-",
            t["goal"][:60],
            t["updated_at"][:19],
        )
    console.print(table)


if __name__ == "__main__":
    app()
```

Uso del CLI:

```bash
# Agregar al PATH o alias
alias tasks="python -m task_memory.cli"

tasks new "Migrar base de datos de producción" --assign hermes
tasks pending
tasks pending --assign hermes
tasks history --status failed --limit 10
tasks show <task_id>
tasks done <task_id> --summary "Migración completada sin errores"
tasks fail <task_id> --error "Timeout en conexión a PostgreSQL"
tasks artifact <task_id> --type report --path /home/server/nelson/reports/migration.md --desc "Reporte de migración"
```

---

## Integración con Hermes session_search

Cuando un agente arranca y quiere retomar trabajo previo, puede buscar en el historial de sesiones de Hermes para cruzar con las tareas en memoria.

```python
# task_memory/integrations/hermes_search.py
"""
Integración con Hermes session_search para vincular sesiones del agente
con las tareas en Task Memory.
"""
import httpx
from typing import Optional
from task_memory import crud


HERMES_API = "http://localhost:8765"  # Ajustar según configuración local


def find_session_tasks(session_id: str) -> list[dict]:
    """Retorna todas las tareas asociadas a una sesión Hermes dada."""
    with crud.get_connection() as conn:
        rows = conn.execute(
            "SELECT t.* FROM tasks t JOIN sessions s ON t.id=s.task_id WHERE s.session_id=?",
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def search_related_sessions(query: str, limit: int = 5) -> list[dict]:
    """
    Usa session_search de Hermes para encontrar sesiones pasadas
    relacionadas con una query, y retorna las tareas vinculadas.
    """
    try:
        resp = httpx.get(
            f"{HERMES_API}/sessions/search",
            params={"q": query, "limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        sessions = resp.json()
    except Exception as e:
        print(f"[hermes_search] Error buscando sesiones: {e}")
        return []

    results = []
    for session in sessions:
        sid = session.get("session_id") or session.get("id")
        if sid:
            tasks = find_session_tasks(sid)
            results.extend(tasks)

    # Deduplicar por task id
    seen = set()
    unique = []
    for t in results:
        if t["id"] not in seen:
            seen.add(t["id"])
            unique.append(t)

    return unique


def resume_context(agent_name: str) -> dict:
    """
    Punto de entrada para que un agente recupere su contexto al iniciar sesión.
    Retorna: tareas pendientes propias + últimas tareas fallidas para retry.
    """
    pending = crud.get_pending_tasks(assigned_to=agent_name)
    failed = crud.get_task_history(assigned_to=agent_name, status="failed", limit=10)

    return {
        "pending_tasks": pending,
        "failed_tasks_for_retry": failed,
        "summary": (
            f"{len(pending)} tarea(s) pendiente(s), "
            f"{len(failed)} fallo(s) reciente(s) para revisar."
        ),
    }
```

Uso típico al inicio de sesión del meta-agente:

```python
from task_memory.integrations.hermes_search import resume_context

ctx = resume_context(agent_name="hermes")
print(ctx["summary"])
# → "3 tarea(s) pendiente(s), 1 fallo(s) reciente(s) para revisar."

for task in ctx["pending_tasks"]:
    print(f"- [{task['status']}] {task['goal']}")
```

---

## Integración con Nelson Kanban

La integración es bidireccional: cuando una tarea cambia de estado en Task Memory, se sincroniza con el tablero Kanban de Nelson (asumiendo que el Kanban expone una API REST o es una base propia).

```python
# task_memory/integrations/kanban.py
"""
Sync con el Kanban de Nelson.
Columnas Kanban mapeadas: Backlog -> In Progress -> Review -> Done / Blocked
"""
import httpx
from typing import Optional

KANBAN_API = "http://localhost:8743"  # Servicio Nelson Kanban

STATUS_TO_COLUMN = {
    "pending":     "Backlog",
    "in_progress": "In Progress",
    "done":        "Done",
    "failed":      "Blocked",
    "cancelled":   "Cancelled",
}


def sync_task_to_kanban(task: dict) -> bool:
    """
    Crea o actualiza la card en Kanban cuando cambia el estado de una tarea.
    Retorna True si fue exitoso.
    """
    column = STATUS_TO_COLUMN.get(task["status"], "Backlog")
    payload = {
        "external_id":  task["id"],
        "title":        task["goal"][:100],
        "column":       column,
        "assigned_to":  task.get("assigned_to"),
        "description":  task.get("result_summary") or task.get("error") or "",
        "updated_at":   task["updated_at"],
    }

    try:
        # Intentar actualizar primero, si no existe crear
        resp = httpx.put(
            f"{KANBAN_API}/cards/external/{task['id']}",
            json=payload,
            timeout=5,
        )
        if resp.status_code == 404:
            resp = httpx.post(f"{KANBAN_API}/cards", json=payload, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[kanban] Error sincronizando tarea {task['id'][:8]}: {e}")
        return False


def kanban_sync_middleware(task_id: str, new_status: str) -> None:
    """
    Hook para llamar después de update_status.
    Puede agregarse directamente en crud.update_status o en la API.
    """
    from task_memory import crud
    task = crud.get_task(task_id)
    if task:
        sync_task_to_kanban(task)
```

Para activar el sync automático, wrappear `update_status` en la API:

```python
# En task_memory/api.py — reemplazar el endpoint update_status

@router.patch("/{task_id}/status")
def update_status(task_id: str, body: StatusUpdate, sync_kanban: bool = Query(True)):
    task = crud.update_status(...)
    if task and sync_kanban:
        from .integrations.kanban import kanban_sync_middleware
        kanban_sync_middleware(task_id, body.status)
    return task
```

---

## Ciclo de vida completo — Ejemplo

El meta-agente de Nelson recibe la instrucción: "Generá un reporte de performance del mes pasado y mandalo a Slack".

### 1. Crear la tarea

```python
from task_memory.crud import create_task, start_session, update_status, add_artifact, end_session

task = create_task(
    goal="Generar reporte de performance mensual y enviar a Slack",
    assigned_to="hermes",
)
# → {"id": "a1b2c3d4-...", "status": "pending", ...}
```

### 2. Iniciar sesión de trabajo

```python
session = start_session(
    task_id=task["id"],
    session_id="hermes-session-20260526",
    notes="Iniciando generación de reporte. Query a prod DB."
)
# La tarea pasa a in_progress automáticamente
```

### 3. Subtarea: query de datos

```python
subtask_query = create_task(
    goal="Query de métricas de performance — mayo 2026",
    assigned_to="hermes",
    parent_task_id=task["id"],
)
# ... ejecutar query ...
update_status(subtask_query["id"], "done", result_summary="1842 filas obtenidas")
add_artifact(subtask_query["id"], "file", "/tmp/perf_may2026.csv", "CSV con métricas raw")
```

### 4. Subtarea: generar reporte

```python
subtask_report = create_task(
    goal="Generar PDF de reporte con visualizaciones",
    assigned_to="hermes",
    parent_task_id=task["id"],
)
# ... generar PDF ...
update_status(subtask_report["id"], "done", result_summary="PDF generado correctamente")
add_artifact(subtask_report["id"], "report", "/home/server/reports/perf_may2026.pdf", "Reporte PDF final")
```

### 5. Subtarea: enviar a Slack

```python
subtask_slack = create_task(
    goal="Enviar reporte a canal #performance en Slack",
    assigned_to="hermes",
    parent_task_id=task["id"],
)
# ... enviar ...
update_status(subtask_slack["id"], "done", result_summary="Mensaje enviado a #performance")
add_artifact(subtask_slack["id"], "url", "https://slack.com/archives/C01234/p1234", "Link al mensaje en Slack")
```

### 6. Cerrar sesión y completar tarea principal

```python
end_session(
    session_id=session["id"],
    notes="Todo completado: query, PDF y Slack. Sin errores."
)
update_status(
    task["id"],
    "done",
    result_summary="Reporte mensual generado y enviado a #performance en Slack."
)
```

### 7. Tony verifica desde CLI

```bash
tasks show a1b2c3d4

# Salida:
# Tarea: a1b2c3d4-...
#   Goal:    Generar reporte de performance mensual y enviar a Slack
#   Status:  done
#   Assigned: hermes
#   Result:  Reporte mensual generado y enviado a #performance en Slack.
#
#   Artefactos (3):
#     [file]    /tmp/perf_may2026.csv — CSV con métricas raw
#     [report]  /home/server/reports/perf_may2026.pdf — Reporte PDF final
#     [url]     https://slack.com/archives/... — Link al mensaje en Slack
#
#   Sesiones (1):
#     hermes-session-20260526 | 2026-05-26T18:00:00 → 2026-05-26T18:14:22
```

---

## Boards activos (setup 2026-06-19)

2 boards creados para los 2 frentes técnicos de Nelson:
- `alegent-ai` — proyectos propios AlegentAI (Bisonte, ForestAI, infra, demos)
- `lan-latam` — proyectos LAN/LATAM (finanzas, ML, GCP)
- YPF — gestión de equipo, NO tiene board en Hermes

Ver `references/kanban-proyectos-setup.md` para tareas iniciales y comandos.

PITFALL: `--board` va ANTES del subcomando:
✓ `hermes kanban --board alegent-ai list`
✗ `hermes kanban list --board alegent-ai`

## Pitfalls y consideraciones

### 1. Concurrencia sobre SQLite

SQLite soporta múltiples lectores concurrentes pero solo un escritor a la vez. Con WAL mode (`PRAGMA journal_mode=WAL`) esto es suficiente para el uso del meta-agente. Si en el futuro hay alta escritura concurrente, migrar a PostgreSQL usando la misma interfaz crud.

### 2. Borrado vs cancelación — cuándo usar cada uno

Para **tareas de trabajo real** preferir `cancelled` (preserva historial). Para **limpieza de historial** (tareas de prueba, experiments, runs que ya no interesan) hay endpoints DELETE que borran en cascada (subtareas + artefactos + sesiones).

**Endpoints DELETE disponibles (en producción desde 2026-05-26):**

```bash
# Borrar una tarea individual con todo su árbol
DELETE /tasks/{task_id}
# → { "deleted": "uuid" }

# Borrar todas las tareas de un estado en bloque
DELETE /tasks/bulk/{status}   # done | failed | cancelled | pending
# → { "deleted_count": N, "status": "done" }
```

```bash
# Ejemplos curl
curl -X DELETE http://localhost:8742/tasks/{task_id}
curl -X DELETE http://localhost:8742/tasks/bulk/done
curl -X DELETE http://localhost:8742/tasks/bulk/failed
```

```python
# Desde Python
import httpx
httpx.delete(f"http://localhost:8742/tasks/{task_id}")
httpx.delete("http://localhost:8742/tasks/bulk/failed")
```

**Regla de uso:**
- `bulk/done` + `bulk/failed` → limpieza periódica de historial viejo (safe, no hay recuperación)
- `bulk/pending` → usar con cuidado, borra tareas activas esperando ejecución
- Individual por ID → para limpiar una tarea específica con sus subtareas
- No exponer bulk/pending en el dashboard (demasiado destructivo por accidente)

**Implementación en crud.py** — borra en cascada:
```python
def delete_task(task_id):
    # 1. sub_ids = SELECT id WHERE parent_task_id = task_id
    # 2. Para cada sub: DELETE artifacts, sessions, task
    # 3. DELETE artifacts, sessions, task principal
    # Retorna bool (False si no existía)

def delete_tasks_by_status(status):
    # Solo borra tareas raíz (parent_task_id IS NULL) del status dado
    # Las subtareas se borran en cascada via delete_task()
    # Retorna count de tareas raíz borradas
```

### 3. IDs de sesión Hermes deben ser consistentes

Para que la integración con `session_search` funcione, el agente debe pasar siempre el mismo `session_id` que usa Hermes. Si el agente no lo conoce, puede usar `socket.gethostname() + timestamp` como fallback.

### 4. No confundir "sesión" con "tarea"

Una tarea puede tener múltiples sesiones (retries, continuaciones). Una sesión solo debería estar activa (sin `ended_at`) si el agente está corriendo en este momento. Al arrancar, cerrar sesiones huérfanas (sin `ended_at` de más de 1 hora).

```python
# cleanup de sesiones huérfanas al startup
def close_orphan_sessions(max_age_hours: int = 1) -> int:
    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()
    with get_connection() as conn:
        result = conn.execute(
            "UPDATE sessions SET ended_at=? WHERE ended_at IS NULL AND started_at < ?",
            (now_iso(), cutoff),
        )
    return result.rowcount
```

### 5. Sincronización con Kanban puede fallar silenciosamente

El sync con Kanban es best-effort. Si el servicio Kanban está caído, la tarea igual se actualiza en SQLite. Loggear los fallos pero no bloquear la operación principal.

### 6. El `result_summary` es para humanos, no para el agente

No guardar datos estructurados en `result_summary`. Para outputs que el agente necesita procesar, usar artefactos con tipo `file` o `report` y paths concretos.

### 7. Ruta del DB en múltiples entornos

Usar variable de entorno para la ruta del DB:

```python
import os
DB_PATH = Path(os.getenv("NELSON_TASKS_DB", "/home/server/nelson/task-memory/db/tasks.db"))
```

### 8. Migraciones del esquema

Agregar columnas nuevas siempre con `ALTER TABLE ... ADD COLUMN ... DEFAULT NULL`. Nunca recrear tablas con datos existentes sin migración explícita.

```python
def migrate_v2():
    """Ejemplo: agregar columna priority en v2."""
    with get_connection() as conn:
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 5")
        except Exception:
            pass  # Columna ya existe, ignorar
```

---

## requirements.txt

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
typer[all]>=0.12.0
rich>=13.7.0
httpx>=0.27.0
```

---

## Despliegue como servicio systemd

```ini
# /etc/systemd/system/nelson-task-memory.service
[Unit]
Description=Nelson Task Memory API
After=network.target

[Service]
User=server
WorkingDirectory=/home/server/nelson/task-memory
Environment=NELSON_TASKS_DB=/home/server/nelson/task-memory/db/tasks.db
ExecStart=/home/server/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8742
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nelson-task-memory
sudo systemctl start nelson-task-memory
sudo systemctl status nelson-task-memory
```

---

## Playbook operativo — "¿Qué nos quedó pendiente?"

Cuando Tony/Nelson pide un estado rápido de pendientes entre sesiones, no alcanza con una sola fuente. Usar este orden de chequeo para evitar falsos "todo limpio":

1. **Task Memory (fuente principal):**
   - Consultar `pending` + `in_progress` (+ opcional `failed` recientes).
   - Si está vacío, continuar igual con los pasos 2–4.
2. **TODO runtime del agente:**
   - Revisar la lista `todo` de la sesión actual.
3. **Historial de sesiones (session_search):**
   - Buscar términos de continuidad: `pendiente`, `TODO`, `falta`, `próximo`, nombres de proyectos (`ForestAI`, `Fleet`, `EduAI`) y `tunnel/cloudflare/deploy`.
   - Marcar como "posible pendiente histórico" cuando el indicio viene de transcript parcial.
4. **Backlog documental en brainstorming:**
   - Buscar en `~/brainstorming` headings tipo `## Próximos pasos` y archivos `ideas-pendientes-*`.
5. **Jobs programados:**
   - Listar cronjobs para detectar tareas pausadas/deshabilitadas que representen pendiente operativo.

### Formato de respuesta recomendado (WhatsApp, conciso)

- `Estado tareas formales`
- `Pendientes en docs`
- `Automatizaciones`
- `Posibles pendientes históricos`

Este formato prioriza legibilidad ejecutiva (rápido de leer en móvil) y separa pendientes confirmados vs indicios históricos.

Referencia ampliada: `references/pending-triage-checklist.md`.

## Resumen rápido — Qué hace cada componente

| Componente              | Función                                                   |
|-------------------------|-----------------------------------------------------------|
| `models.py`             | Esquema SQLite, conexión, WAL mode                        |
| `crud.py`               | Toda la lógica de datos, sin HTTP                         |
| `api.py`                | Endpoints REST para agentes y servicios                   |
| `cli.py`                | Interfaz para Tony desde terminal                         |
| `integrations/kanban`   | Sync con tablero visual Nelson                            |
| `integrations/hermes`   | Recuperación de contexto entre sesiones Hermes/JARVIS     |
