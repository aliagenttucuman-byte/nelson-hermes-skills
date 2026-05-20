#!/usr/bin/env python3
"""Valida que un archivo sea seguro para commitear."""
import re
import sys
import os

SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{48}',
    r'ghp_[a-zA-Z0-9]{36}',
    r'AIza[0-9A-Za-z_-]{35}',
    r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    r'password\s*=\s*[\'"][^\'"]+[\'"]',
    r'token\s*=\s*[\'"][^\'"]{20,}[\'"]',
]

def check_file(path: str) -> list:
    issues = []
    try:
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return [f"No se pudo leer: {e}"]
    
    for pattern in SECRET_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line = content[:match.start()].count('\n') + 1
            issues.append(f"  Line {line}: posible secret ({pattern[:20]}...)")
    return issues

if __name__ == "__main__":
    errors = 0
    for path in sys.argv[1:]:
        if not os.path.isfile(path):
            continue
        issues = check_file(path)
        if issues:
            print(f"ISSUES in {path}:")
            for issue in issues:
                print(issue)
            errors += len(issues)
    if errors:
        print(f"\nFAILED: {errors} issue(s) found")
        sys.exit(1)
    print("SAFE TO COMMIT")
