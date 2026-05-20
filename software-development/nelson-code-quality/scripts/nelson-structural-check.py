#!/usr/bin/env python3
"""Sensores estructurales - Verifican arquitectura del proyecto.

Checks deterministicos, sin LLM. Baratos y rapidos.
"""

import argparse
import ast
import json
import sys
from pathlib import Path


class ArchitectureSensor:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.issues = []

    def log(self, severity: str, category: str, message: str, file: str = ""):
        self.issues.append({
            "severity": severity,
            "category": category,
            "file": str(file),
            "message": message,
        })

    # --- CHECKS ---

    def check_api_imports_models(self):
        """API no debe importar directamente de models."""
        api_dir = self.root / "app" / "api"
        if not api_dir.exists():
            return

        for pyfile in api_dir.rglob("*.py"):
            content = pyfile.read_text()
            if "from app.models" in content or "import app.models" in content:
                self.log("high", "architecture", 
                         f"API importa models directamente: {pyfile.name}", pyfile)

    def check_service_imports_api(self):
        """Services no debe importar de api (dependencia circular)."""
        svc_dir = self.root / "app" / "services"
        if not svc_dir.exists():
            return

        for pyfile in svc_dir.rglob("*.py"):
            content = pyfile.read_text()
            if "from app.api" in content or "import app.api" in content:
                self.log("high", "architecture",
                         f"Service importa API (circular): {pyfile.name}", pyfile)

    def check_no_bare_excepts(self):
        """No usar except: sin especificar excepcion."""
        app_dir = self.root / "app"
        if not app_dir.exists():
            return

        for pyfile in app_dir.rglob("*.py"):
            content = pyfile.read_text()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped == "except:" or stripped.startswith("except :"):
                    self.log("high", "error-handling",
                             f"Bare except en linea {i}", pyfile)

    def check_function_length(self, max_lines: int = 50):
        """Funciones no deben exceder max_lines."""
        app_dir = self.root / "app"
        if not app_dir.exists():
            return

        for pyfile in app_dir.rglob("*.py"):
            try:
                tree = ast.parse(pyfile.read_text())
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
                    if length > max_lines:
                        self.log("medium", "clean-code",
                                 f"Funcion '{node.name}' tiene {length} lineas (max {max_lines})", pyfile)

    def check_hardcoded_secrets(self):
        """Detectar strings que parecen secrets hardcodeados."""
        app_dir = self.root / "app"
        keywords = ["password", "secret", "token", "api_key", "apikey"]

        for pyfile in app_dir.rglob("*.py"):
            content = pyfile.read_text()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                lower = line.lower()
                if any(k in lower for k in keywords):
                    if "=" in line and any(c.isalnum() for c in line.split("=")[-1]):
                        val = line.split("=")[-1].strip().strip('"\'')
                        if val and val not in ("your-secret", "changeme", ""):
                            self.log("high", "security",
                                     f"Posible secret hardcodeado en linea {i}", pyfile)

    def check_todo_comments(self):
        """Detectar TODO/FIXME sin ticket/issue asociado."""
        app_dir = self.root / "app"
        for pyfile in app_dir.rglob("*.py"):
            content = pyfile.read_text()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                stripped = line.strip().lower()
                if "todo" in stripped or "fixme" in stripped or "hack" in stripped:
                    self.log("low", "maintenance",
                             f"TODO/FIXME en linea {i}: {line.strip()[:60]}", pyfile)

    def check_test_coverage(self):
        """Verificar que exista tests/ y no este vacio."""
        test_dir = self.root / "app" / "tests"
        if not test_dir.exists():
            self.log("high", "testing", "No existe directorio app/tests/")
            return

        py_files = list(test_dir.rglob("test_*.py"))
        if not py_files:
            self.log("high", "testing", "app/tests/ existe pero no tiene test_*.py")
        elif len(py_files) < 3:
            self.log("medium", "testing", f"Solo {len(py_files)} archivos de test")

    def run_all(self) -> dict:
        """Ejecutar todos los checks."""
        self.check_api_imports_models()
        self.check_service_imports_api()
        self.check_no_bare_excepts()
        self.check_function_length()
        self.check_hardcoded_secrets()
        self.check_todo_comments()
        self.check_test_coverage()

        high = sum(1 for i in self.issues if i["severity"] == "high")
        medium = sum(1 for i in self.issues if i["severity"] == "medium")
        low = sum(1 for i in self.issues if i["severity"] == "low")

        score = max(0, 100 - high * 15 - medium * 5 - low * 1)

        return {
            "score": score,
            "issues": self.issues,
            "summary": f"{high} high, {medium} medium, {low} low issues",
        }


def print_report(report: dict):
    print("\n" + "=" * 60)
    print("SENSORES ESTRUCTURALES - ARQUITECTURA")
    print("=" * 60)
    print(f"\nScore: {report['score']}/100")
    print(f"Summary: {report['summary']}")

    issues = report["issues"]
    if not issues:
        print("\n Todo OK. Arquitectura limpia.")
        return

    print(f"\nIssues: {len(issues)}")
    for issue in issues:
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")
        print(f"\n{icon} [{issue['severity'].upper()}] {issue['category']}")
        if issue.get("file"):
            print(f"   File: {issue['file']}")
        print(f"   {issue['message']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Raiz del proyecto")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    sensor = ArchitectureSensor(root)
    report = sensor.run_all()

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print_report(report)

    sys.exit(0 if report["score"] >= 80 else 1)


if __name__ == "__main__":
    main()
