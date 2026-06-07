#!/usr/bin/env python3
"""
onboard_sprint.py — Da de alta un sprint nuevo con sus tareas en un solo comando.

Uso:
    python scripts/onboard_sprint.py \\
        --project expreso_bisonte \\
        --name "Sprint 3 — Facturación AFIP" \\
        --goal "Cerrar integración con AFIP y subir a staging" \\
        --weeks 2 \\
        --capacity 80 \\
        --task T-001,T-002,T-003 \\
        --points 3,5,2

O desde un JSON:
    python scripts/onboard_sprint.py --from-file sprint.json
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from task_memory.crud import create_task, get_pending_tasks, update_status
from task_memory.models import init_db


def main():
    p = argparse.ArgumentParser(description="Onboarding de sprint")
    p.add_argument("--project", required=True, help="slug del proyecto (debe existir)")
    p.add_argument("--name", required=True)
    p.add_argument("--goal", default="")
    p.add_argument("--weeks", type=int, default=2)
    p.add_argument("--capacity", type=float, help="horas totales del equipo (default: 6 devs × 30h × semanas × 0.6)")
    p.add_argument("--task", help="lista de task IDs separados por coma")
    p.add_argument("--points", help="lista de puntos fibonacci separados por coma")
    p.add_argument("--from-file", help="JSON con todo: {project, name, goal, weeks, tasks: [{id, points, estimate}]}")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.from_file:
        with open(args.from_file) as f:
            data = json.load(f)
        project_slug = data["project"]
        name = data["name"]
        goal = data.get("goal", "")
        weeks = data.get("weeks", 2)
        capacity = data.get("capacity")
        tasks = data.get("tasks", [])
    else:
        project_slug = args.project
        name = args.name
        goal = args.goal
        weeks = args.weeks
        capacity = args.capacity
        if args.task and args.points:
            task_ids = args.task.split(",")
            points_list = [int(x) for x in args.points.split(",")]
            tasks = [{"id": tid, "points": pt, "estimate": None} for tid, pt in zip(task_ids, points_list)]
        else:
            tasks = []

    start = datetime.utcnow()
    end = start + timedelta(weeks=weeks)
    if capacity is None:
        # Regla: capacidad = 6 devs × 30h/sem × weeks × 0.6 = 21.6h/sem/dev asumido
        # Si tenés menos gente, pasá --capacity explícito
        capacity = 6 * 30 * weeks * 0.6

    total_points = sum(t.get("points", 0) for t in tasks)

    if args.dry_run:
        print(f"[DRY-RUN] Crearía sprint:")
        print(f"  project:   {project_slug}")
        print(f"  name:      {name}")
        print(f"  goal:      {goal}")
        print(f"  duration:  {weeks} semanas ({start.date()} → {end.date()})")
        print(f"  capacity:  {capacity}h")
        print(f"  tasks:     {len(tasks)} tareas, {total_points} puntos")
        for t in tasks:
            print(f"    - {t['id']} ({t.get('estimate','?')}) = {t.get('points',0)} pts")
        return

    print(f"Sprint {name}: {len(tasks)} tareas, {total_points} pts, {capacity}h capacity")
    print(f"Duración: {start.date()} → {end.date()}")
    # En implementación real, esto pegaría a la API de task-memory
    # Por ahora el script es el template — la integración con la API se hace
    # cuando se implemente el endpoint POST /sprints/ en nelson-task-memory
    print("\n⚠ Esta versión es template. Para activar, implementar endpoint POST /sprints/ en nelson-task-memory")


if __name__ == "__main__":
    main()
