#!/usr/bin/env python3
"""Self-correction loop - Intenta arreglar issues automaticamente.

Uso:
    nelson-self-fix --root . --dry-run   # Ver que haria sin tocar nada
    nelson-self-fix --root .             # Aplicar fixes
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


class SelfFixer:
    def __init__(self, root: Path, dry_run: bool = True):
        self.root = root
        self.dry_run = dry_run
        self.fixes = []

    def log(self, action: str, file: Path, detail: str):
        self.fixes.append({"action": action, "file": str(file), "detail": detail})
        prefix = "[DRY-RUN]" if self.dry_run else "[FIX]"
        print(f"{prefix} {action}: {file} - {detail}")

    def fix_bare_excepts(self):
        """Reemplazar 'except:' por 'except Exception:'."""
        app_dir = self.root / "app"
        if not app_dir.exists():
            return

        for pyfile in app_dir.rglob("*.py"):
            content = pyfile.read_text()
            original = content
            content = re.sub(r'except\s*:', 'except Exception:', content)
            if content != original:
                if not self.dry_run:
                    pyfile.write_text(content)
                self.log("fix_bare_except", pyfile, "Reemplazado except: por except Exception:")

    def add_type_hints_stub(self):
        """Agregar type hints basicos a funciones sin hints."""
        app_dir = self.root / "app"
        if not app_dir.exists():
            return

        for pyfile in app_dir.rglob("*.py"):
            content = pyfile.read_text()
            lines = content.split("\n")
            modified = False
            new_lines = []

            for i, line in enumerate(lines):
                new_lines.append(line)
                if line.strip().startswith("def ") and "->" not in line:
                    if "__init__" not in line and "_" not in line.split("def ")[1].split("(")[0]:
                        next_lines = lines[i+1:i+5]
                        has_return = any("return " in l and "return None" not in l for l in next_lines)
                        if not has_return:
                            new_lines[-1] = line.rstrip() + " -> None"
                            modified = True
                            self.log("add_type_hint", pyfile, f"Agregado -> None a {line.strip()[:40]}")

            if modified and not self.dry_run:
                pyfile.write_text("\n".join(new_lines))

    def sort_imports(self):
        """Ejecutar isort si esta disponible."""
        try:
            result = subprocess.run(
                ["isort", str(self.root / "app"), "--diff" if self.dry_run else "--atomic"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout:
                self.log("sort_imports", self.root, "Imports ordenados con isort")
        except FileNotFoundError:
            pass

    def run_all(self):
        self.fix_bare_excepts()
        self.add_type_hints_stub()
        self.sort_imports()
        return self.fixes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Raiz del proyecto")
    parser.add_argument("--dry-run", action="store_true", help="No modificar archivos")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    fixer = SelfFixer(root, dry_run=args.dry_run)
    fixes = fixer.run_all()

    print(f"\nTotal fixes: {len(fixes)}")
    if args.dry_run and fixes:
        print("Ejecutar sin --dry-run para aplicar.")


if __name__ == "__main__":
    main()
