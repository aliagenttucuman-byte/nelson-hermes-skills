---
name: nelson-react-doctor
description: "React Doctor v2: diagnóstico automático de errores en apps React. Detecta useState/useEffect innecesarios, prop drilling, problemas de accesibilidad y rendimiento. Integración con CI/CD del equipo Nelson."
category: software-development
tags: [react, frontend, code-quality, linting, performance, a11y]
related_skills: [nelson-frontend-stack, nelson-code-quality, nelson-frontend-testing]
---

# React Doctor v2 🤖⚕️

> **Trigger:** Cada vez que el equipo desarrolle o revise código React. También en CI/CD antes de mergear PRs.

## ¿Qué es?

Herramienta de código abierto que escanea apps React y detecta problemas comunes de manera automática:

- ✅ `useState` y `useEffect` innecesarios
- ✅ Errores de accesibilidad (a11y)
- ✅ Problemas de rendimiento
- ✅ Prop drilling evitable con Context
- ✅ Imports no usados
- ✅ Dependencias de efectos incorrectas

## Instalación

### One-shot (sin instalar globalmente)

```bash
npx react-doctor@latest
```

### Instalación local en proyecto

```bash
npm install --save-dev react-doctor@latest
```

### Verificar versión

```bash
npx react-doctor --version
```

## Uso básico

### Analizar todo el proyecto

```bash
npx react-doctor@latest
# o
npx react-doctor@latest --dir ./src
```

### Analizar un archivo específico

```bash
npx react-doctor@latest ./src/components/UserProfile.tsx
```

### Salida en formato JSON (para CI)

```bash
npx react-doctor@latest --format json --output report.json
```

### Solo errores críticos

```bash
npx react-doctor@latest --severity error
```

## Integración con CI/CD

### Pre-commit hook (husky)

```json
// .husky/pre-commit
npx react-doctor@latest --staged
```

### GitHub Actions

```yaml
# .github/workflows/react-doctor.yml
name: React Doctor Check
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx react-doctor@latest --format json
```

### Script del equipo

```bash
# scripts/check-react.sh
#!/bin/bash
set -e

echo "🤖⚕️ Corriendo React Doctor..."
npx react-doctor@latest --format json --output .reports/react-doctor.json

# Si hay errores críticos, falla el pipeline
if grep -q '"severity": "error"' .reports/react-doctor.json; then
  echo "❌ Errores críticos encontrados. Revisa .reports/react-doctor.json"
  exit 1
fi

echo "✅ React Doctor pasó sin errores críticos"
```

## Reglas principales detectadas

| Regla | Descripción | Severidad |
|---|---|---|
| `unnecessary-useState` | `useState` que podría ser una constante | warning |
| `unnecessary-useEffect` | `useEffect` que no maneja side effects | warning |
| `prop-drilling` | Props pasadas más de 3 niveles sin Context | warning |
| `missing-key-prop` | Elementos de lista sin `key` | error |
| `useEffect-missing-deps` | Dependencias faltantes en `useEffect` | error |
| `unused-imports` | Imports no utilizados | warning |
| `accessibility-missing-alt` | Imágenes sin `alt` | error |
| `performance-memo-missing` | Componentes que deberían usar `memo` | info |
| `context-over-prop-drilling` | Situación candidata para Context | suggestion |

## Configuración

### Archivo de config `react-doctor.config.js`

```javascript
module.exports = {
  extends: ['recommended'],
  rules: {
    'unnecessary-useState': 'warn',
    'unnecessary-useEffect': 'warn',
    'prop-drilling': 'warn',
    'missing-key-prop': 'error',
    'useEffect-missing-deps': 'error',
    'unused-imports': 'warn',
    'accessibility-missing-alt': 'error',
    'performance-memo-missing': 'info',
  },
  ignorePatterns: [
    '**/*.test.{js,jsx,ts,tsx}',
    '**/*.spec.{js,jsx,ts,tsx}',
    '**/node_modules/**',
    '**/dist/**',
  ],
};
```

## Flujo del equipo Nelson

```
1. Desarrollador escribe código React
2. Antes de commitear: npm run lint (incluye React Doctor)
3. Si hay errores: corrige antes de pushear
4. CI corre React Doctor automáticamente
5. PR bloqueada si hay errores críticos
6. Merge solo si pasa todas las validaciones
```

## Pitfalls

- **NO correr en `node_modules`** — React Doctor escanea todo el árbol por defecto. Usar `--ignore-pattern` o `react-doctor.config.js`.
- **No sustituye testing** — Detecta patrones de código, no bugs de lógica. Sigue usando jest/react-testing-library.
- **Revisar `suggestion` antes de aplicar** — Algunas sugerencias de "usar Context" pueden ser overkill para props simples.
- **Versión lock** — En CI, usar `react-doctor@latest` o versionar en `package.json` para consistencia.

## Comandos rápidos

```bash
# Diagnóstico completo
npx react-doctor@latest

# Solo archivos modificados (git staged)
npx react-doctor@latest --staged

# Reporte HTML
npx react-doctor@latest --format html --output report.html

# Ignorar archivos de test
npx react-doctor@latest --ignore-pattern "**/*.test.tsx"

# Con fix automático donde sea posible
npx react-doctor@latest --fix
```

## Links

- npm: `npx react-doctor@latest`
- Categoría: code-quality, frontend, react
