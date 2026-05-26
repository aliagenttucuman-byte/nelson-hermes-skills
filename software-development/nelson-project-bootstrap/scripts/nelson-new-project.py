#!/usr/bin/env python3
"""Agente de bootstrap: crea nuevo proyecto desde template.

Uso:
    nelson-new-project "Nombre del Proyecto"
"""

import os
import subprocess
import sys
import argparse


def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Crear nuevo proyecto desde template")
    parser.add_argument("name", help="Nombre del proyecto (ej: 'Sistema de Inventario')")
    args = parser.parse_args()

    # Convertir a kebab-case
    project_slug = args.name.lower().replace(" ", "-").replace("_", "-")
    project_dir = os.path.expanduser(f"~/projects/{project_slug}")

    print(f"Creando proyecto: {args.name}")
    print(f"Directorio: {project_dir}")

    # Crear directorio
    os.makedirs(project_dir, exist_ok=True)

    # Clonar template
    run(f"git clone https://github.com/aliagenttucuman-byte/nelson-template.git {project_dir}")

    # Remover .git del template
    run(f"rm -rf {project_dir}/.git")

    # Inicializar nuevo repo
    run("git init", cwd=project_dir)
    run("git add -A", cwd=project_dir)
    run(f'git commit -m "chore: bootstrap desde nelson-template"', cwd=project_dir)

    print(f"\n Proyecto creado en {project_dir}")
    print("Para empezar:")
    print(f"  cd {project_dir}")
    print("  ./scripts/bootstrap.sh")


if __name__ == "__main__":
    main()
