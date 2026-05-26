#!/usr/bin/env python3
"""Alma 2.0 - Revisor semantico de codigo con LLM local.

Uso:
    alma-reviewer <archivo.py> [--model llama3.1:8b]
    alma-reviewer --diff  # Revisa cambios no commiteados
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"

PROMPT_TEMPLATE = """Sos un senior software engineer con 20 anos de experiencia.
Revisa el siguiente codigo Python y detecta:

1. OVER-ENGINEERING: Codigo mas complejo de lo necesario, abstracciones innecesarias, patrones aplicados donde no corresponden.
2. CODIGO DUPLICADO SEMANTICO: Funciones o logica que hace lo mismo de forma diferente, no solo copy-paste exacto.
3. FEATURES INNECESARIAS: Funcionalidad que no aporta valor, edge cases que no son requeridos.
4. NOMBRES POBRES: Variables/funciones/clases con nombres confusos o genericos.
5. VIOLACIONES DE CLEAN CODE: Funciones muy largas, muchos parametros, responsabilidades mezcladas.
6. FALTA DE MANEJO DE ERRORES: Excepciones no manejadas, errores silenciados.
7. INEFICIENCIA: Algoritmos O(n^2) donde O(n) alcanza, queries N+1, etc.

Responde EXCLUSIVAMENTE en este formato JSON:
{
  "issues": [
    {
      "severity": "high|medium|low",
      "category": "over-engineering|duplication|unnecessary|naming|clean-code|error-handling|inefficiency",
      "line": numero o null,
      "description": "Descripcion corta del problema",
      "suggestion": "Como arreglarlo"
    }
  ],
  "score": 0-100,
  "summary": "Resumen ejecutivo de 2 oraciones"
}

Codigo a revisar:
```python
{code}
```
"""


def ollama_generate(prompt: str, model: str) -> str:
    """Llamar a Ollama API."""
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False})
    result = subprocess.run(
        ["curl", "-s", f"{OLLAMA_URL}/api/generate", "-d", payload],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ollama error: {result.stderr}")
    data = json.loads(result.stdout)
    return data.get("response", "")


def review_file(path: Path, model: str) -> dict:
    """Revisar un archivo con LLM."""
    code = path.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.format(code=code)
    response = ollama_generate(prompt, model)

    # Extraer JSON de la respuesta
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        else:
            json_str = response
        return json.loads(json_str.strip())
    except (json.JSONDecodeError, IndexError):
        return {
            "issues": [],
            "score": 0,
            "summary": f"Error parseando respuesta del LLM: {response[:200]}"
        }


def review_diff(model: str) -> dict:
    """Revisar cambios no commiteados."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True
    )
    files = [f for f in result.stdout.strip().split("\n") if f.endswith(".py")]

    all_issues = []
    total_score = 0
    summaries = []

    for f in files:
        path = Path(f)
        if not path.exists():
            continue
        report = review_file(path, model)
        all_issues.extend(report.get("issues", []))
        total_score += report.get("score", 0)
        summaries.append(report.get("summary", ""))

    count = len(files) or 1
    return {
        "files_reviewed": files,
        "issues": all_issues,
        "score": round(total_score / count, 1),
        "summary": " ".join(summaries)[:200]
    }


def print_report(report: dict):
    """Imprimir reporte en formato legible."""
    print("\n" + "=" * 60)
    print("ALMA 2.0 - REVISION SEMANTICA")
    print("=" * 60)

    if "files_reviewed" in report:
        print(f"\nArchivos revisados: {', '.join(report['files_reviewed'])}")

    print(f"\nScore: {report.get('score', 0)}/100")
    print(f"Summary: {report.get('summary', 'N/A')}")

    issues = report.get("issues", [])
    if not issues:
        print("\nNo se encontraron issues. Codigo limpio.")
        return

    print(f"\nIssues encontrados: {len(issues)}")
    for issue in issues:
        severity = issue.get("severity", "low").upper()
        icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
        print(f"\n{icon} [{severity}] {issue.get('category', 'general')}")
        if issue.get("line"):
            print(f"   Linea: {issue['line']}")
        print(f"   {issue.get('description', '')}")
        print(f"   → {issue.get('suggestion', '')}")

    high = sum(1 for i in issues if i.get("severity") == "high")
    medium = sum(1 for i in issues if i.get("severity") == "medium")
    low = sum(1 for i in issues if i.get("severity") == "low")
    print(f"\nResumen: {high} high, {medium} medium, {low} low")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Alma 2.0 - Revisor semantico")
    parser.add_argument("file", nargs="?", help="Archivo a revisar")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modelo Ollama")
    parser.add_argument("--diff", action="store_true", help="Revisar git diff")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    if args.diff:
        report = review_diff(args.model)
    elif args.file:
        report = review_file(Path(args.file), args.model)
    else:
        parser.print_help()
        sys.exit(1)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
