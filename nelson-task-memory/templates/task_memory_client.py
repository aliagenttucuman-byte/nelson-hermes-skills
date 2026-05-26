"""
Template: cliente Python para nelson-task-memory.
Copiar y adaptar en cualquier proyecto del equipo Nelson que quiera
registrar tareas en el orquestador.
"""
import httpx
from typing import Optional

TASK_MEMORY_URL = "http://localhost:8742"


def create_task(goal: str, assigned_to: Optional[str] = None, parent_task_id: Optional[str] = None) -> dict:
    r = httpx.post(f"{TASK_MEMORY_URL}/tasks/", json={
        "goal": goal,
        "assigned_to": assigned_to,
        "parent_task_id": parent_task_id,
    })
    r.raise_for_status()
    return r.json()


def start_session(task_id: str, session_id: str, notes: Optional[str] = None) -> dict:
    r = httpx.post(f"{TASK_MEMORY_URL}/tasks/{task_id}/sessions/start", json={
        "session_id": session_id,
        "notes": notes,
    })
    r.raise_for_status()
    return r.json()


def end_session(session_id: str, notes: Optional[str] = None) -> None:
    r = httpx.patch(f"{TASK_MEMORY_URL}/tasks/sessions/{session_id}/end", json={"notes": notes})
    r.raise_for_status()


def mark_done(task_id: str, summary: Optional[str] = None) -> dict:
    r = httpx.patch(f"{TASK_MEMORY_URL}/tasks/{task_id}/status", json={
        "status": "done",
        "result_summary": summary,
    })
    r.raise_for_status()
    return r.json()


def mark_failed(task_id: str, error: str) -> dict:
    r = httpx.patch(f"{TASK_MEMORY_URL}/tasks/{task_id}/status", json={
        "status": "failed",
        "error": error,
    })
    r.raise_for_status()
    return r.json()


def add_artifact(task_id: str, artifact_type: str, path: str, description: Optional[str] = None) -> dict:
    r = httpx.post(f"{TASK_MEMORY_URL}/tasks/{task_id}/artifacts", json={
        "type": artifact_type,
        "path": path,
        "description": description,
    })
    r.raise_for_status()
    return r.json()


def get_pending(assigned_to: Optional[str] = None) -> list:
    params = {}
    if assigned_to:
        params["assigned_to"] = assigned_to
    r = httpx.get(f"{TASK_MEMORY_URL}/tasks/pending", params=params)
    r.raise_for_status()
    return r.json()


# Ejemplo de uso en el loop del meta-agente:
if __name__ == "__main__":
    # 1. Crear tarea
    task = create_task("Implementar sistema de login", assigned_to="hermes")
    tid = task["id"]

    # 2. Iniciar sesión
    sess = start_session(tid, "hermes-session-001", notes="Arrancando implementación")

    try:
        # 3. Hacer el trabajo...
        # ... código del agente ...

        # 4. Registrar artefactos
        add_artifact(tid, "file", "/home/server/proyecto/auth.py", "Módulo de autenticación")

        # 5. Completar
        mark_done(tid, "Login implementado con JWT. Tests: 12/12 OK.")
    except Exception as e:
        mark_failed(tid, str(e))
    finally:
        end_session(sess["id"], notes="Sesión cerrada")
